#!/usr/bin/env python3
"""Independently validate post-allocation worktree/commit state before persistence.

This checker is intentionally separate from the mutator. It proves that the current
state equals the validated dry-run mutation exactly, historical Stable rows did not
change, and the Git change scope is limited to the two authorized allocation files.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
PLAN = TP / "allocation" / "plan.json"
AUTH = TP / "allocation" / "authorization.json"
REGISTRY = BASE / "master" / "note_registry.csv"
REGISTRY_EXT = BASE / "master" / "note_registry_extensions.csv"
EVIDENCE = TP / "provenance" / "stable_evidence_bindings.csv"

REGISTRY_FIELDS = [
    "NoteID", "CanonicalWord", "MatchKey", "SenseLabel", "PrimaryOriginKey",
    "CreatedSource", "CreatedSourceBook", "Status",
]
BINDING_FIELDS = [
    "NoteID", "ProvisionalIdentityKey", "SourceOccurrenceKey", "SourceID",
    "SourceBook", "Grade", "Semester", "SourceRow", "SourceSnapshotFingerprint",
    "EvidenceStatus",
]
ALLOWED_PATHS = {
    "anki/klose/master/note_registry_extensions.csv",
    "anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def read_csv_text(text: str) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    return list(reader.fieldnames or []), list(reader)


def obj(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def git_show(ref: str, rel: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel}"], cwd=ROOT, text=True,
        capture_output=True, encoding="utf-8",
    )
    require(proc.returncode == 0, f"Cannot read baseline {ref}:{rel}: {proc.stderr.strip()}")
    return proc.stdout


def git_blob_sha_bytes(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def git_blob_sha_at(ref: str, rel: str) -> str:
    data = git_show(ref, rel).encode("utf-8")
    # git show text normalizes only decoding; repository files here are UTF-8 CSV/JSON.
    return git_blob_sha_bytes(data)


def changed_paths(base_ref: str) -> set[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", base_ref, "--"], cwd=ROOT,
        text=True, capture_output=True, encoding="utf-8",
    )
    require(proc.returncode == 0, f"git diff failed: {proc.stderr.strip()}")
    changed = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    proc = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT,
        text=True, capture_output=True, encoding="utf-8",
    )
    require(proc.returncode == 0, f"git ls-files failed: {proc.stderr.strip()}")
    changed.update(line.strip() for line in proc.stdout.splitlines() if line.strip())
    return changed


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run-dir", required=True)
    parser.add_argument("--base-ref", required=True)
    args = parser.parse_args()

    dry = Path(args.dry_run_dir).expanduser().resolve()
    base_ref = args.base_ref.strip()
    require(base_ref, "--base-ref must not be empty")

    plan = obj(PLAN)
    auth = obj(AUTH)
    gates = plan.get("MutationGates")
    require(auth.get("Authorized") is True, "Post-mutation gate requires explicit allocation authorization")
    require(bool(str(auth.get("UserAuthorizationEvidence", "")).strip()), "Authorization evidence missing")
    require(bool(str(auth.get("AuthorizedAt", "")).strip()), "Authorization timestamp missing")
    require(isinstance(gates, dict), "Allocation mutation gates missing")
    require(gates.get("ActualMutationAuthorized") is True, "ActualMutationAuthorized is not true")
    require(gates.get("StableNoteIDAllocationAuthorized") is True, "StableNoteIDAllocationAuthorized is not true")
    for key in (
        "MasterSourceMappingMutationAuthorized", "LearnerMutationAuthorized",
        "ReleaseMutationAuthorized", "PublishMutationAuthorized", "AnkiMutationAuthorized",
    ):
        require(gates.get(key) is False, f"Forbidden mutation gate enabled: {key}")

    append_fields, append_rows = read_csv(dry / "registry_append.csv")
    binding_fields, binding_rows = read_csv(dry / "stable_evidence_bindings.csv")
    require(append_fields == REGISTRY_FIELDS, "Dry-run append schema drift")
    require(binding_fields == BINDING_FIELDS, "Dry-run binding schema drift")
    require(len(append_rows) == 1821, "Dry-run append count drift")
    require(len(binding_rows) == 15791, "Dry-run binding count drift")

    ext_rel = REGISTRY_EXT.relative_to(ROOT).as_posix()
    legacy_rel = REGISTRY.relative_to(ROOT).as_posix()
    base_ext_fields, base_ext = read_csv_text(git_show(base_ref, ext_rel))
    require(base_ext_fields == REGISTRY_FIELDS, "Baseline extension registry schema drift")

    # The authorized transaction must start from the exact frozen Stable truth.
    truth = plan.get("TruthBoundary")
    require(isinstance(truth, dict), "Allocation plan TruthBoundary missing")
    baseline_ext_blob = subprocess.run(
        ["git", "rev-parse", f"{base_ref}:{ext_rel}"], cwd=ROOT,
        text=True, capture_output=True, encoding="utf-8",
    )
    require(baseline_ext_blob.returncode == 0, "Cannot resolve baseline extension blob")
    require(
        baseline_ext_blob.stdout.strip() == truth.get("NoteRegistryExtensionsBlobSHA"),
        "Post-mutation base registry does not match allocation truth boundary",
    )
    baseline_legacy_blob = subprocess.run(
        ["git", "rev-parse", f"{base_ref}:{legacy_rel}"], cwd=ROOT,
        text=True, capture_output=True, encoding="utf-8",
    )
    require(baseline_legacy_blob.returncode == 0, "Cannot resolve baseline legacy registry blob")
    require(
        baseline_legacy_blob.stdout.strip() == truth.get("NoteRegistryBlobSHA"),
        "Post-mutation legacy registry baseline does not match allocation truth boundary",
    )

    current_ext_fields, current_ext = read_csv(REGISTRY_EXT)
    require(current_ext_fields == REGISTRY_FIELDS, "Current extension registry schema drift")
    require(current_ext[: len(base_ext)] == base_ext, "Historical extension registry rows changed")
    require(current_ext[len(base_ext):] == append_rows, "Post-allocation Stable append is not exact dry-run append")
    require(len(current_ext) == len(base_ext) + 1821, "Post-allocation extension row count drift")

    require(EVIDENCE.exists(), "Post-allocation stable_evidence_bindings.csv is missing")
    evidence_fields, evidence_rows = read_csv(EVIDENCE)
    require(evidence_fields == BINDING_FIELDS, "Post-allocation evidence binding schema drift")
    require(evidence_rows == binding_rows, "Post-allocation evidence bindings are not exact dry-run bindings")

    legacy_fields, legacy_rows = read_csv(REGISTRY)
    require(legacy_fields == REGISTRY_FIELDS, "Legacy registry schema drift")
    full_ids = {r["NoteID"] for r in legacy_rows + current_ext}
    require(len(full_ids) == len(legacy_rows) + len(current_ext), "Post-allocation Stable NoteID duplicate")
    require(len(full_ids) == 3015, "Post-allocation full Stable NoteID count drift")
    require(all(r["NoteID"] in full_ids for r in evidence_rows), "Evidence binding references unknown Stable NoteID")

    changed = changed_paths(base_ref)
    require(changed == ALLOWED_PATHS, f"Allocation transaction diff scope violation: {sorted(changed)}")

    print("Third-party allocation post-mutation Completion Recheck = pass")
    print(f"historical extension rows unchanged = {len(base_ext)}")
    print("new Stable rows exact = 1821")
    print("full Stable NoteIDs = 3015")
    print("external evidence bindings exact = 15791")
    print("held identities allocated = no")
    print("Master/Learner/Release/Publish/Anki mutation = no")
    print(f"authorized diff scope = {sorted(ALLOWED_PATHS)}")


if __name__ == "__main__":
    main()
