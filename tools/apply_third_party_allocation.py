#!/usr/bin/env python3
"""Apply or simulate the closed third-party Vocabulary allocation.

The default repository state is deliberately unauthorized. `--simulate` may only
write outside the repository. `--apply` may mutate exactly two paths and requires
both the durable authorization manifest and allocation plan mutation gates to be
explicitly enabled against the exact current truth boundary.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
PLAN = TP / "allocation" / "plan.json"
AUTH = TP / "allocation" / "authorization.json"
PROVENANCE = TP / "provenance" / "contract.json"
STAGE_B = TP / "reconciliation" / "reconciliation_decisions.csv"
REGISTRY = BASE / "master" / "note_registry.csv"
REGISTRY_EXT = BASE / "master" / "note_registry_extensions.csv"
EVIDENCE = TP / "provenance" / "stable_evidence_bindings.csv"
NOTE_RE = re.compile(r"^KV(\d{6})$")

REGISTRY_FIELDS = [
    "NoteID", "CanonicalWord", "MatchKey", "SenseLabel", "PrimaryOriginKey",
    "CreatedSource", "CreatedSourceBook", "Status",
]
BINDING_FIELDS = [
    "NoteID", "ProvisionalIdentityKey", "SourceOccurrenceKey", "SourceID",
    "SourceBook", "Grade", "Semester", "SourceRow", "SourceSnapshotFingerprint",
    "EvidenceStatus",
]


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def read_obj(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), f"Expected JSON object: {display_path(path)}")
    return value


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def note_num(note_id: str) -> int:
    match = NOTE_RE.fullmatch(note_id)
    require(match is not None, f"Invalid NoteID: {note_id!r}")
    return int(match.group(1))


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def outside_repo(raw: str) -> Path:
    path = Path(raw).expanduser().resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError:
        return path
    raise SystemExit("Simulation output must be outside the repository")


def load_dry_run(path: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    append_fields, append_rows = read_csv(path / "registry_append.csv")
    binding_fields, binding_rows = read_csv(path / "stable_evidence_bindings.csv")
    summary = read_obj(path / "summary.json")
    require(append_fields == REGISTRY_FIELDS, "Dry-run registry append schema drift")
    require(binding_fields == BINDING_FIELDS, "Dry-run evidence binding schema drift")
    require(summary.get("MutationAuthorized") is False, "Dry-run unexpectedly authorizes mutation")
    require(summary.get("HypotheticalRegistryAppends") == len(append_rows), "Dry-run append count mismatch")
    require(summary.get("ExternalEvidenceBindings") == len(binding_rows), "Dry-run binding count mismatch")
    return append_rows, binding_rows


def validate_truth_boundary(plan: dict[str, object], auth: dict[str, object]) -> None:
    truth = plan.get("TruthBoundary")
    auth_truth = auth.get("TruthBoundary")
    require(isinstance(truth, dict) and isinstance(auth_truth, dict), "Allocation truth boundary missing")
    current = {
        "StageBDecisionBlobSHA": git_blob_sha(STAGE_B),
        "NoteRegistryBlobSHA": git_blob_sha(REGISTRY),
        "NoteRegistryExtensionsBlobSHA": git_blob_sha(REGISTRY_EXT),
    }
    for key, sha in current.items():
        require(truth.get(key) == sha, f"Allocation plan stale at {key}: {truth.get(key)} != {sha}")
        require(auth_truth.get(key) == sha, f"Allocation authorization stale at {key}: {auth_truth.get(key)} != {sha}")
    require(
        auth.get("StageACheckpointFingerprint") == plan.get("StageACheckpointFingerprint"),
        "Authorization Stage-A checkpoint disagrees with allocation plan",
    )


def build_post_state(
    append_rows: list[dict[str, str]],
    binding_rows: list[dict[str, str]],
    *,
    base_extensions: list[dict[str, str]],
    existing_bindings: list[dict[str, str]] | None,
) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    _, legacy = read_csv(REGISTRY)
    all_current = legacy + base_extensions
    current_by_id = {r["NoteID"]: r for r in all_current}
    require(len(current_by_id) == len(all_current), "Current Stable NoteID duplicate")

    ext_by_origin = {
        r.get("PrimaryOriginKey", ""): r
        for r in base_extensions
        if r.get("PrimaryOriginKey", "").startswith("third-party-vocabulary|candidate:")
    }
    require(len(ext_by_origin) == sum(
        1 for r in base_extensions if r.get("PrimaryOriginKey", "").startswith("third-party-vocabulary|candidate:")
    ), "Duplicate existing third-party allocation origin")

    out_ext = list(base_extensions)
    added = 0
    for row in append_rows:
        note_id = row["NoteID"]
        origin = row["PrimaryOriginKey"]
        require(origin.startswith("third-party-vocabulary|candidate:"), f"Unexpected third-party origin key: {origin}")
        previous = ext_by_origin.get(origin)
        if previous is not None:
            require(previous == row, f"Existing third-party allocation disagrees with dry run: {origin}")
            continue
        require(note_id not in current_by_id, f"Allocation NoteID collides with current registry: {note_id}")
        out_ext.append(dict(row))
        ext_by_origin[origin] = row
        current_by_id[note_id] = row
        added += 1

    out_ext.sort(key=lambda r: note_num(r["NoteID"]))

    binding_key = lambda r: (r["ProvisionalIdentityKey"], r["SourceOccurrenceKey"])
    dry_by_key = {binding_key(r): r for r in binding_rows}
    require(len(dry_by_key) == len(binding_rows), "Dry-run evidence binding duplicate")
    if existing_bindings is None:
        out_bindings = list(binding_rows)
    else:
        existing_by_key = {binding_key(r): r for r in existing_bindings}
        require(len(existing_by_key) == len(existing_bindings), "Existing evidence binding duplicate")
        require(set(existing_by_key) <= set(dry_by_key), "Existing evidence binding contains rows outside current allocation truth")
        for key, row in existing_by_key.items():
            require(row == dry_by_key[key], f"Existing evidence binding disagrees with current truth: {key}")
        out_bindings = list(binding_rows)
    out_bindings.sort(key=binding_key)
    return out_ext, out_bindings, added


def authorization_enabled(plan: dict[str, object], auth: dict[str, object]) -> bool:
    gates = plan.get("MutationGates")
    return bool(
        auth.get("Authorized") is True
        and isinstance(gates, dict)
        and gates.get("ActualMutationAuthorized") is True
        and gates.get("StableNoteIDAllocationAuthorized") is True
        and gates.get("MasterSourceMappingMutationAuthorized") is False
        and gates.get("LearnerMutationAuthorized") is False
        and gates.get("ReleaseMutationAuthorized") is False
        and gates.get("PublishMutationAuthorized") is False
        and gates.get("AnkiMutationAuthorized") is False
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--simulate", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--expect-unauthorized", action="store_true")
    parser.add_argument("--dry-run-dir")
    parser.add_argument("--output-dir")
    args = parser.parse_args()

    plan = read_obj(PLAN)
    auth = read_obj(AUTH)
    provenance = read_obj(PROVENANCE)
    require(plan.get("PlanStatus") == "validated-checkpointed-plan-only", "Allocation plan is not checkpointed")
    require(provenance.get("ContractStatus") == "validated-checkpointed", "Provenance contract is not checkpointed")
    require(auth.get("AuthorizationVersion") == "third-party-allocation-authorization-v1", "Authorization contract version drift")
    validate_truth_boundary(plan, auth)

    enabled = authorization_enabled(plan, auth)
    if args.expect_unauthorized:
        require(not enabled, "Allocation unexpectedly authorized")
        print("Third-party allocation authorization gate = correctly closed")
        print("repository mutation = no")
        return

    require(args.dry_run_dir, "--dry-run-dir is required")
    dry_dir = Path(args.dry_run_dir).expanduser().resolve()
    append_rows, binding_rows = load_dry_run(dry_dir)
    ext_fields, current_ext = read_csv(REGISTRY_EXT)
    require(ext_fields == REGISTRY_FIELDS, "Registry extension schema drift")

    if args.simulate:
        require(args.output_dir, "--output-dir is required for --simulate")
        out = outside_repo(args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        simulated_ext = out / "note_registry_extensions.csv"
        simulated_bindings = out / "stable_evidence_bindings.csv"
        previous_bindings = None
        if simulated_bindings.exists():
            fields, previous_bindings = read_csv(simulated_bindings)
            require(fields == BINDING_FIELDS, "Previous simulated binding schema drift")
        base_ext = current_ext
        if simulated_ext.exists():
            fields, base_ext = read_csv(simulated_ext)
            require(fields == REGISTRY_FIELDS, "Previous simulated registry schema drift")
        post_ext, post_bindings, added = build_post_state(
            append_rows,
            binding_rows,
            base_extensions=base_ext,
            existing_bindings=previous_bindings,
        )
        write_csv(simulated_ext, REGISTRY_FIELDS, post_ext)
        write_csv(simulated_bindings, BINDING_FIELDS, post_bindings)
        print("Third-party allocation simulation = built")
        print(f"new registry rows added this simulation = {added}")
        print(f"simulated registry extension rows = {len(post_ext)}")
        print(f"simulated evidence bindings = {len(post_bindings)}")
        print("repository mutation = no")
        return

    require(args.apply, "Unsupported allocator mode")
    require(enabled, "Actual third-party allocation is not explicitly authorized")
    require(bool(str(auth.get("UserAuthorizationEvidence", "")).strip()), "Authorized allocation lacks user authorization evidence")
    require(bool(str(auth.get("AuthorizedAt", "")).strip()), "Authorized allocation lacks timestamp")

    existing_bindings = None
    if EVIDENCE.exists():
        fields, existing_bindings = read_csv(EVIDENCE)
        require(fields == BINDING_FIELDS, "Existing stable evidence binding schema drift")
    post_ext, post_bindings, added = build_post_state(
        append_rows,
        binding_rows,
        base_extensions=current_ext,
        existing_bindings=existing_bindings,
    )
    write_csv(REGISTRY_EXT, REGISTRY_FIELDS, post_ext)
    write_csv(EVIDENCE, BINDING_FIELDS, post_bindings)
    print("Third-party allocation apply = completed")
    print(f"new Stable registry rows added = {added}")
    print(f"external evidence bindings = {len(post_bindings)}")
    print("Master source identity mapping mutation = no")
    print("Learner/Release/Publish/Anki mutation = no")


if __name__ == "__main__":
    main()
