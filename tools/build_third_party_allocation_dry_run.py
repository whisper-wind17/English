#!/usr/bin/env python3
"""Build a mutation-disabled third-party Vocabulary allocation dry run.

Outputs are allowed only outside the repository. The dry run resolves all closed
Stage-B decisions into existing or hypothetical NoteIDs and materializes the
future external-evidence binding shape without touching Klose persistent truth.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
PLAN = TP / "allocation" / "plan.json"
PROVENANCE = TP / "provenance" / "contract.json"
DECISIONS = TP / "reconciliation" / "reconciliation_decisions.csv"
STAGE_A_DECISIONS = TP / "review" / "identity_decisions.csv"
PREVIEW = TP / "staging" / "unified_vocabulary_preview.csv"
OCCURRENCES = TP / "staging" / "occurrences.csv"
REGISTRY = BASE / "master" / "note_registry.csv"
REGISTRY_EXT = BASE / "master" / "note_registry_extensions.csv"
NOTE_RE = re.compile(r"^KV(\d{6})$")
RESOLVED_STAGE_A_ACTIONS = {"keep-identity", "reuse-identity", "route-expression", "source-only"}

ACTION_FIELDS = [
    "ProvisionalIdentityKey", "StageBAction", "ResolvedNoteID", "NoteIDKind",
    "CanonicalWord", "MatchKey", "SenseLabel", "MutationAuthorized",
]
REGISTRY_FIELDS = [
    "NoteID", "CanonicalWord", "MatchKey", "SenseLabel", "PrimaryOriginKey",
    "CreatedSource", "CreatedSourceBook", "Status",
]
BINDING_FIELDS = [
    "NoteID", "ProvisionalIdentityKey", "SourceOccurrenceKey", "SourceID",
    "SourceBook", "Grade", "Semester", "SourceRow", "SourceSnapshotFingerprint",
    "EvidenceStatus",
]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_obj(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path.relative_to(ROOT)}")
    return value


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def note_num(note_id: str) -> int:
    match = NOTE_RE.fullmatch(note_id)
    if match is None:
        raise SystemExit(f"Invalid NoteID: {note_id!r}")
    return int(match.group(1))


def occurrence_keys(row: dict[str, str]) -> list[str]:
    raw = row.get("OccurrenceKeys", "")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid Stage-A OccurrenceKeys JSON: {row.get('DecisionKey')}: {exc}") from exc
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
        raise SystemExit(f"Invalid Stage-A OccurrenceKeys: {row.get('DecisionKey')}")
    if len(value) != len(set(value)):
        raise SystemExit(f"Duplicate Stage-A OccurrenceKeys: {row.get('DecisionKey')}")
    return value


def safe_output_dir(raw: str) -> Path:
    out = Path(raw).expanduser().resolve()
    root = ROOT.resolve()
    try:
        out.relative_to(root)
    except ValueError:
        return out
    raise SystemExit("Dry-run output directory must be outside the repository; persistent repo mutation is forbidden")


def stage_a_occurrence_map() -> tuple[dict[str, list[str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    """Reproduce Stage-A Preview eligibility, then bind each materialized identity to exact occurrences."""
    _, occurrence_rows = read_csv(OCCURRENCES)
    occ_by_key = {r.get("SourceOccurrenceKey", ""): r for r in occurrence_rows}
    require(len(occ_by_key) == len(occurrence_rows) and all(occ_by_key), "Unified occurrence keys are empty/duplicate")
    current_by_match: dict[str, set[str]] = defaultdict(set)
    for row in occurrence_rows:
        current_by_match[row.get("MatchKey", "")].add(row["SourceOccurrenceKey"])

    _, decision_rows = read_csv(STAGE_A_DECISIONS)
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decision_rows:
        groups[row.get("MatchKey", "")].append(row)

    valid_decision: dict[str, dict[str, str]] = {}
    resolved_multipart: dict[str, list[dict[str, str]]] = {}
    for match_key, rows in groups.items():
        current = current_by_match.get(match_key, set())
        if not current:
            continue
        covered: set[str] = set()
        overlap = False
        for row in rows:
            keys = occurrence_keys(row)
            if not set(keys) <= current:
                raise SystemExit(f"Stage-A decision evidence outside current MatchKey: {row.get('DecisionKey')}")
            if covered & set(keys):
                overlap = True
            covered.update(keys)
        resolved = (
            not overlap
            and covered == current
            and all(r.get("Status") == "reviewed" and r.get("Action") in RESOLVED_STAGE_A_ACTIONS for r in rows)
        )
        if not resolved:
            continue
        if len(rows) == 1:
            valid_decision[match_key] = rows[0]
        else:
            resolved_multipart[match_key] = rows

    multipart_keep_index: dict[str, tuple[str, dict[str, str]]] = {}
    for base_key, rows in resolved_multipart.items():
        for row in rows:
            if row.get("Action") != "keep-identity":
                continue
            canonical = row.get("CanonicalMatchKey", "").strip()
            require(bool(canonical) and canonical.startswith(base_key + "#"), f"Invalid multipart keep canonical: {row.get('DecisionKey')}")
            require(canonical not in multipart_keep_index, f"Duplicate multipart keep canonical: {canonical}")
            multipart_keep_index[canonical] = (base_key, row)

    mapping: dict[str, set[str]] = defaultdict(set)
    assigned_occurrence: dict[str, str] = {}

    def assign(pid: str, keys: list[str], decision_key: str) -> None:
        for key in keys:
            previous = assigned_occurrence.get(key)
            require(previous in {None, pid}, f"Source occurrence maps to multiple provisional identities: {key}: {previous} vs {pid} ({decision_key})")
            assigned_occurrence[key] = pid
            mapping[pid].add(key)

    # Mirror build_third_party_corpus.py single-decision canonical eligibility.
    for match_key, row in valid_decision.items():
        action = row.get("Action")
        if action not in {"keep-identity", "reuse-identity"}:
            continue
        keys = occurrence_keys(row)
        if action == "keep-identity":
            assign(f"candidate:{match_key}", keys, row.get("DecisionKey", ""))
            continue

        canonical = row.get("CanonicalMatchKey", "").strip()
        require(bool(canonical), f"reuse-identity lacks CanonicalMatchKey: {row.get('DecisionKey')}")
        if "#" in canonical:
            target = multipart_keep_index.get(canonical)
            if target is None:
                base_key = canonical.split("#", 1)[0]
                if base_key in current_by_match and base_key not in resolved_multipart:
                    # Current Stage-A Preview deliberately suppresses aliases whose
                    # canonical multipart target is blocked or no longer resolved.
                    continue
                raise SystemExit(f"Scoped reuse target is not a resolved multipart keep subgroup: {row.get('DecisionKey')} -> {canonical}")
            assign(f"candidate:{canonical}", keys, row.get("DecisionKey", ""))
            continue

        if canonical in current_by_match:
            canonical_d = valid_decision.get(canonical)
            if not canonical_d or canonical_d.get("Status") != "reviewed" or canonical_d.get("Action") != "keep-identity":
                # Canonical blocker precedence: reviewed alias is not materialized
                # until the canonical surface itself is a valid keep identity.
                continue
        assign(f"candidate:{canonical}", keys, row.get("DecisionKey", ""))

    # Mirror resolved multipart materialization.
    for base_key, rows in resolved_multipart.items():
        for row in rows:
            action = row.get("Action")
            if action not in {"keep-identity", "reuse-identity"}:
                continue
            keys = occurrence_keys(row)
            if action == "keep-identity":
                canonical = row.get("CanonicalMatchKey", "").strip()
                require(bool(canonical), f"Multipart keep lacks canonical: {row.get('DecisionKey')}")
                assign(f"candidate:{canonical}", keys, row.get("DecisionKey", ""))
                continue

            canonical = row.get("CanonicalMatchKey", "").strip()
            require(bool(canonical), f"Multipart reuse lacks canonical: {row.get('DecisionKey')}")
            if canonical in current_by_match:
                canonical_d = valid_decision.get(canonical)
                require(
                    bool(canonical_d)
                    and canonical_d.get("Status") == "reviewed"
                    and canonical_d.get("Action") == "keep-identity",
                    f"Multipart reuse bypasses canonical blocker: {row.get('DecisionKey')} -> {canonical}",
                )
            assign(f"candidate:{canonical}", keys, row.get("DecisionKey", ""))

    _, preview_rows = read_csv(PREVIEW)
    preview_by_pid = {r.get("ProvisionalIdentityKey", ""): r for r in preview_rows}
    require(len(preview_by_pid) == len(preview_rows) and all(preview_by_pid), "Stage-A preview identities are empty/duplicate")
    mapping_keys = set(mapping)
    preview_keys = set(preview_by_pid)
    if mapping_keys != preview_keys:
        missing = sorted(preview_keys - mapping_keys)
        extra = sorted(mapping_keys - preview_keys)
        print(f"Stage-A mapping identities = {len(mapping_keys)}")
        print(f"Stage-A preview identities = {len(preview_keys)}")
        print(f"Stage-A mapping missing identities ({len(missing)}) = {missing[:50]}")
        print(f"Stage-A mapping extra identities ({len(extra)}) = {extra[:50]}")
        raise SystemExit("Stage-A exact occurrence mapping does not close current Vocabulary Preview")
    count_mismatches = [
        (pid, len(mapping[pid]), int(row.get("SourceOccurrenceCount", "0")))
        for pid, row in preview_by_pid.items()
        if len(mapping[pid]) != int(row.get("SourceOccurrenceCount", "0"))
    ]
    if count_mismatches:
        print(f"Stage-A occurrence count mismatches ({len(count_mismatches)}) = {count_mismatches[:50]}")
        raise SystemExit("Stage-A occurrence counts do not close current Vocabulary Preview")
    return {pid: sorted(keys) for pid, keys in mapping.items()}, occ_by_key, preview_by_pid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    out = safe_output_dir(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    plan = read_obj(PLAN)
    provenance = read_obj(PROVENANCE)
    require(plan.get("PlanStatus") == "validated-checkpointed-plan-only", "Allocation plan is not checkpointed")
    require(provenance.get("ContractStatus") == "validated-checkpointed", "Provenance contract is not checkpointed")
    gates = plan.get("MutationGates")
    require(isinstance(gates, dict) and all(value is False for value in gates.values()), "Dry run refuses to run from a mutation-authorized plan")

    reg_fields, legacy = read_csv(REGISTRY)
    ext_fields, extensions = read_csv(REGISTRY_EXT)
    require(reg_fields == REGISTRY_FIELDS and ext_fields == REGISTRY_FIELDS, "Stable registry schema drift")
    registry = legacy + extensions
    registry_by_id = {r["NoteID"]: r for r in registry}
    require(len(registry_by_id) == len(registry), "Stable registry NoteID duplicate")
    active_by_id = {nid: row for nid, row in registry_by_id.items() if row.get("Status") == "active"}
    max_id = max(registry_by_id, key=note_num)

    _, stage_b_rows = read_csv(DECISIONS)
    stage_b = {r.get("ProvisionalIdentityKey", ""): r for r in stage_b_rows}
    require(len(stage_b) == len(stage_b_rows) and all(stage_b), "Stage-B decision identities are empty/duplicate")
    occurrence_map, occ_by_key, preview_by_pid = stage_a_occurrence_map()
    require(set(stage_b) == set(preview_by_pid), "Stage-B decisions do not close Stage-A preview")

    new_pids = sorted(pid for pid, row in stage_b.items() if row.get("Action") == "new-stable-identity")
    first_num = note_num(max_id) + 1
    hypothetical_ids = {pid: f"KV{first_num + i:06d}" for i, pid in enumerate(new_pids)}
    append_range = plan.get("HypotheticalAppendRange")
    require(isinstance(append_range, dict), "Plan HypotheticalAppendRange missing")
    if new_pids:
        require(hypothetical_ids[new_pids[0]] == append_range.get("First"), "Dry-run first NoteID drift")
        require(hypothetical_ids[new_pids[-1]] == append_range.get("Last"), "Dry-run last NoteID drift")
    require(len(new_pids) == append_range.get("Count"), "Dry-run new identity count drift")

    stable_policy = provenance.get("StableIdentityPolicy")
    binding_policy = provenance.get("FutureEvidenceBinding")
    source_freeze = provenance.get("SourceFreeze")
    require(isinstance(stable_policy, dict) and isinstance(binding_policy, dict) and isinstance(source_freeze, dict), "Provenance policy incomplete")
    created_source = str(stable_policy.get("PlannedCreatedSource", ""))
    created_book = str(stable_policy.get("PlannedCreatedSourceBook", ""))
    snapshot = str(source_freeze.get("UnifiedOccurrencesFingerprint", ""))
    evidence_status = str(binding_policy.get("EvidenceStatusValue", ""))

    actions: list[dict[str, str]] = []
    appends: list[dict[str, str]] = []
    bindings: list[dict[str, str]] = []
    held_occurrences = 0

    for pid in sorted(stage_b):
        decision = stage_b[pid]
        action = decision.get("Action", "")
        if action == "reuse-existing":
            note_id = decision.get("ExistingNoteID", "")
            require(note_id in active_by_id, f"Dry-run reuse NoteID is not active: {pid}->{note_id}")
            identity = active_by_id[note_id]
            kind = "existing"
        elif action == "new-stable-identity":
            note_id = hypothetical_ids[pid]
            require(note_id not in registry_by_id, f"Hypothetical NoteID collides with registry: {note_id}")
            identity = {
                "CanonicalWord": decision.get("ProposedCanonicalWord", ""),
                "MatchKey": decision.get("ProposedMatchKey", ""),
                "SenseLabel": decision.get("ProposedSense", ""),
            }
            require(all(identity.values()), f"Dry-run new identity fields incomplete: {pid}")
            kind = "hypothetical-new"
            appends.append({
                "NoteID": note_id,
                "CanonicalWord": identity["CanonicalWord"],
                "MatchKey": identity["MatchKey"],
                "SenseLabel": identity["SenseLabel"],
                "PrimaryOriginKey": f"third-party-vocabulary|{pid}",
                "CreatedSource": created_source,
                "CreatedSourceBook": created_book,
                "Status": "active",
            })
        elif action == "held":
            note_id = ""
            identity = {"CanonicalWord": "", "MatchKey": "", "SenseLabel": ""}
            kind = "held"
            held_occurrences += len(occurrence_map[pid])
        else:
            raise SystemExit(f"Unexpected Stage-B action in dry run: {pid}->{action!r}")

        actions.append({
            "ProvisionalIdentityKey": pid,
            "StageBAction": action,
            "ResolvedNoteID": note_id,
            "NoteIDKind": kind,
            "CanonicalWord": identity["CanonicalWord"],
            "MatchKey": identity["MatchKey"],
            "SenseLabel": identity["SenseLabel"],
            "MutationAuthorized": "no",
        })

        if action == "held":
            continue
        for occurrence_key in occurrence_map[pid]:
            occurrence = occ_by_key[occurrence_key]
            bindings.append({
                "NoteID": note_id,
                "ProvisionalIdentityKey": pid,
                "SourceOccurrenceKey": occurrence_key,
                "SourceID": occurrence.get("SourceID", ""),
                "SourceBook": occurrence.get("SourceBook", ""),
                "Grade": occurrence.get("Grade", ""),
                "Semester": occurrence.get("Semester", ""),
                "SourceRow": occurrence.get("SourceRow", ""),
                "SourceSnapshotFingerprint": snapshot,
                "EvidenceStatus": evidence_status,
            })

    bindings.sort(key=lambda r: (r["ProvisionalIdentityKey"], r["SourceOccurrenceKey"]))
    write_csv(out / "identity_actions.csv", ACTION_FIELDS, actions)
    write_csv(out / "registry_append.csv", REGISTRY_FIELDS, appends)
    write_csv(out / "stable_evidence_bindings.csv", BINDING_FIELDS, bindings)

    counts = {action: sum(r["StageBAction"] == action for r in actions) for action in ("reuse-existing", "new-stable-identity", "held")}
    summary = {
        "DryRunVersion": "third-party-allocation-dry-run-v1",
        "MutationAuthorized": False,
        "RegistryBaselineRows": len(registry),
        "RegistryActiveNoteIDs": len(active_by_id),
        "RegistryMaxNoteID": max_id,
        "IdentityActions": len(actions),
        "ActionCounts": counts,
        "HypotheticalRegistryAppends": len(appends),
        "HypotheticalFirstNoteID": appends[0]["NoteID"] if appends else "",
        "HypotheticalLastNoteID": appends[-1]["NoteID"] if appends else "",
        "ExternalEvidenceBindings": len(bindings),
        "HeldSourceOccurrences": held_occurrences,
        "SourceSnapshotFingerprint": snapshot,
        "OutputDirectory": str(out),
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Third-party allocation dry run = built")
    print(f"identity actions = {len(actions)}")
    print(f"reuse-existing = {counts['reuse-existing']}")
    print(f"hypothetical new identities = {counts['new-stable-identity']}")
    print(f"held = {counts['held']}")
    print(f"hypothetical registry append = {len(appends)}")
    print(f"hypothetical NoteID range = {summary['HypotheticalFirstNoteID']}..{summary['HypotheticalLastNoteID']}")
    print(f"external evidence bindings = {len(bindings)}")
    print(f"held source occurrences = {held_occurrences}")
    print("repository mutation = no")
    print("Stable NoteID allocation authorized = no")


if __name__ == "__main__":
    main()
