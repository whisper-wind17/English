#!/usr/bin/env python3
"""Independently validate mutation-disabled third-party allocation dry-run outputs."""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
PLAN = TP / "allocation" / "plan.json"
PROVENANCE = TP / "provenance" / "contract.json"
STAGE_B = TP / "reconciliation" / "reconciliation_decisions.csv"
STAGE_A = TP / "review" / "identity_decisions.csv"
PREVIEW = TP / "staging" / "unified_vocabulary_preview.csv"
OCCURRENCES = TP / "staging" / "occurrences.csv"
REGISTRY = BASE / "master" / "note_registry.csv"
REGISTRY_EXT = BASE / "master" / "note_registry_extensions.csv"
NOTE_RE = re.compile(r"^KV(\d{6})$")
RESOLVED_STAGE_A = {"keep-identity", "reuse-identity", "route-expression", "source-only"}

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


def rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def obj(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return value


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def note_num(note_id: str) -> int:
    match = NOTE_RE.fullmatch(note_id)
    if match is None:
        raise SystemExit(f"Invalid NoteID: {note_id!r}")
    return int(match.group(1))


def decode_keys(row: dict[str, str]) -> list[str]:
    try:
        value = json.loads(row.get("OccurrenceKeys", ""))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid OccurrenceKeys JSON: {row.get('DecisionKey')}") from exc
    require(isinstance(value, list) and value and all(isinstance(x, str) and x for x in value), f"Invalid OccurrenceKeys: {row.get('DecisionKey')}")
    require(len(value) == len(set(value)), f"Duplicate OccurrenceKeys: {row.get('DecisionKey')}")
    return value


def safe_output_dir(raw: str) -> Path:
    out = Path(raw).expanduser().resolve()
    try:
        out.relative_to(ROOT.resolve())
    except ValueError:
        return out
    raise SystemExit("Dry-run validation refuses repo-local output directory")


def expected_occurrence_map() -> tuple[dict[str, list[str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    _, occ_rows = rows(OCCURRENCES)
    occ_by = {r["SourceOccurrenceKey"]: r for r in occ_rows}
    require(len(occ_by) == len(occ_rows), "Current source occurrence keys are not unique")
    current_by_match: dict[str, set[str]] = defaultdict(set)
    for row in occ_rows:
        current_by_match[row["MatchKey"]].add(row["SourceOccurrenceKey"])

    _, decision_rows = rows(STAGE_A)
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decision_rows:
        groups[row["MatchKey"]].append(row)

    mapping: dict[str, set[str]] = defaultdict(set)
    assigned: dict[str, str] = {}
    for match_key, group in groups.items():
        current = current_by_match.get(match_key, set())
        if not current:
            continue
        covered: set[str] = set()
        parts: list[tuple[dict[str, str], list[str]]] = []
        valid = True
        for row in group:
            keys = decode_keys(row)
            keyset = set(keys)
            if not keyset <= current or covered & keyset:
                valid = False
            covered.update(keyset)
            parts.append((row, keys))
        valid = valid and covered == current and all(
            row.get("Status") == "reviewed" and row.get("Action") in RESOLVED_STAGE_A
            for row, _ in parts
        )
        if not valid:
            continue
        multipart = len(parts) > 1
        for row, keys in parts:
            action = row.get("Action")
            if action not in {"keep-identity", "reuse-identity"}:
                continue
            if action == "reuse-identity" or multipart:
                canonical = row.get("CanonicalMatchKey", "").strip()
            else:
                canonical = match_key
            require(bool(canonical), f"Current Stage-A resolved decision lacks canonical key: {row.get('DecisionKey')}")
            pid = f"candidate:{canonical}"
            for key in keys:
                previous = assigned.get(key)
                require(previous in {None, pid}, f"Occurrence assigned to multiple identities: {key}")
                assigned[key] = pid
                mapping[pid].add(key)

    _, preview_rows = rows(PREVIEW)
    preview = {r["ProvisionalIdentityKey"]: r for r in preview_rows}
    require(set(mapping) == set(preview), "Independent Stage-A occurrence mapping does not close Preview")
    for pid, row in preview.items():
        require(len(mapping[pid]) == int(row["SourceOccurrenceCount"]), f"Preview occurrence count drift: {pid}")
    return {pid: sorted(keys) for pid, keys in mapping.items()}, occ_by, preview


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    out = safe_output_dir(args.output_dir)

    plan = obj(PLAN)
    provenance = obj(PROVENANCE)
    summary = obj(out / "summary.json")
    action_fields, action_rows = rows(out / "identity_actions.csv")
    append_fields, append_rows = rows(out / "registry_append.csv")
    binding_fields, binding_rows = rows(out / "stable_evidence_bindings.csv")
    require(action_fields == ACTION_FIELDS, "Dry-run identity action schema drift")
    require(append_fields == REGISTRY_FIELDS, "Dry-run registry append schema drift")
    require(binding_fields == BINDING_FIELDS, "Dry-run evidence binding schema drift")

    reg_fields, legacy = rows(REGISTRY)
    ext_fields, extensions = rows(REGISTRY_EXT)
    require(reg_fields == REGISTRY_FIELDS and ext_fields == REGISTRY_FIELDS, "Current stable registry schema drift")
    registry = legacy + extensions
    registry_by = {r["NoteID"]: r for r in registry}
    active = {nid: r for nid, r in registry_by.items() if r["Status"] == "active"}
    max_id = max(registry_by, key=note_num)

    _, stage_b_rows = rows(STAGE_B)
    stage_b = {r["ProvisionalIdentityKey"]: r for r in stage_b_rows}
    occurrence_map, occ_by, preview = expected_occurrence_map()
    require(set(stage_b) == set(preview), "Current Stage-B / Stage-A identity set drift")

    action_by = {r["ProvisionalIdentityKey"]: r for r in action_rows}
    require(len(action_by) == len(action_rows) and set(action_by) == set(stage_b), "Dry-run identity actions do not close Stage-B")
    new_pids = sorted(pid for pid, d in stage_b.items() if d["Action"] == "new-stable-identity")
    first_num = note_num(max_id) + 1
    expected_new_id = {pid: f"KV{first_num + i:06d}" for i, pid in enumerate(new_pids)}

    expected_appends: dict[str, dict[str, str]] = {}
    expected_bindings: set[tuple[str, ...]] = set()
    stable_policy = provenance["StableIdentityPolicy"]
    binding_policy = provenance["FutureEvidenceBinding"]
    snapshot = provenance["SourceFreeze"]["UnifiedOccurrencesFingerprint"]
    evidence_status = binding_policy["EvidenceStatusValue"]
    held_occurrences = 0

    counts: Counter[str] = Counter()
    for pid, decision in stage_b.items():
        action = decision["Action"]
        counts[action] += 1
        actual = action_by[pid]
        require(actual["StageBAction"] == action and actual["MutationAuthorized"] == "no", f"Dry-run action drift: {pid}")
        if action == "reuse-existing":
            note_id = decision["ExistingNoteID"]
            require(note_id in active, f"Current reuse target no longer active: {pid}->{note_id}")
            current = active[note_id]
            require(actual["ResolvedNoteID"] == note_id and actual["NoteIDKind"] == "existing", f"Dry-run reuse NoteID drift: {pid}")
            for field in ("CanonicalWord", "MatchKey", "SenseLabel"):
                require(actual[field] == current[field], f"Dry-run reuse identity rewrite: {pid}:{field}")
        elif action == "new-stable-identity":
            note_id = expected_new_id[pid]
            require(actual["ResolvedNoteID"] == note_id and actual["NoteIDKind"] == "hypothetical-new", f"Dry-run hypothetical NoteID drift: {pid}")
            require(actual["CanonicalWord"] == decision["ProposedCanonicalWord"], f"Dry-run new CanonicalWord drift: {pid}")
            require(actual["MatchKey"] == decision["ProposedMatchKey"], f"Dry-run new MatchKey drift: {pid}")
            require(actual["SenseLabel"] == decision["ProposedSense"], f"Dry-run new SenseLabel drift: {pid}")
            expected_appends[note_id] = {
                "NoteID": note_id,
                "CanonicalWord": decision["ProposedCanonicalWord"],
                "MatchKey": decision["ProposedMatchKey"],
                "SenseLabel": decision["ProposedSense"],
                "PrimaryOriginKey": f"third-party-vocabulary|{pid}",
                "CreatedSource": stable_policy["PlannedCreatedSource"],
                "CreatedSourceBook": stable_policy["PlannedCreatedSourceBook"],
                "Status": "active",
            }
        elif action == "held":
            note_id = ""
            require(actual["ResolvedNoteID"] == "" and actual["NoteIDKind"] == "held", f"Dry-run held identity pre-resolved: {pid}")
            require(not any(actual[x] for x in ("CanonicalWord", "MatchKey", "SenseLabel")), f"Dry-run held identity fields populated: {pid}")
            held_occurrences += len(occurrence_map[pid])
        else:
            raise SystemExit(f"Unexpected current Stage-B action: {pid}->{action}")

        if action == "held":
            continue
        for key in occurrence_map[pid]:
            occ = occ_by[key]
            expected_bindings.add((
                note_id, pid, key, occ["SourceID"], occ["SourceBook"], occ["Grade"],
                occ["Semester"], occ["SourceRow"], snapshot, evidence_status,
            ))

    append_by = {r["NoteID"]: r for r in append_rows}
    require(len(append_by) == len(append_rows) and append_by == expected_appends, "Dry-run registry append is not exact")
    require(not (set(append_by) & set(registry_by)), "Dry-run registry append collides with current Stable NoteIDs")
    if append_rows:
        ordered_ids = [r["NoteID"] for r in append_rows]
        require(ordered_ids == [expected_new_id[pid] for pid in new_pids], "Dry-run new NoteID ordering is not deterministic")

    actual_bindings = {
        tuple(row[field] for field in BINDING_FIELDS)
        for row in binding_rows
    }
    require(len(actual_bindings) == len(binding_rows), "Dry-run external evidence bindings duplicate")
    require(actual_bindings == expected_bindings, "Dry-run external evidence bindings are not exact")

    plan_range = plan["HypotheticalAppendRange"]
    require(plan_range["Reserved"] is False, "Allocation plan unexpectedly reserves NoteIDs")
    require(len(append_rows) == plan_range["Count"], "Dry-run append count disagrees with plan")
    require((append_rows[0]["NoteID"] if append_rows else "") == plan_range["First"], "Dry-run first NoteID disagrees with plan")
    require((append_rows[-1]["NoteID"] if append_rows else "") == plan_range["Last"], "Dry-run last NoteID disagrees with plan")

    require(summary.get("DryRunVersion") == "third-party-allocation-dry-run-v1", "Dry-run summary version drift")
    require(summary.get("MutationAuthorized") is False, "Dry-run summary authorizes mutation")
    require(summary.get("IdentityActions") == len(stage_b), "Dry-run summary identity count drift")
    require(summary.get("ActionCounts") == dict(counts), "Dry-run summary action counts drift")
    require(summary.get("HypotheticalRegistryAppends") == len(append_rows), "Dry-run summary append count drift")
    require(summary.get("ExternalEvidenceBindings") == len(binding_rows), "Dry-run summary binding count drift")
    require(summary.get("HeldSourceOccurrences") == held_occurrences, "Dry-run summary held occurrence count drift")
    require(summary.get("SourceSnapshotFingerprint") == snapshot, "Dry-run summary source snapshot drift")

    print("Third-party allocation dry-run validation = pass")
    print(f"identity actions = {len(action_rows)}")
    print(f"reuse-existing = {counts['reuse-existing']}")
    print(f"hypothetical new identities = {counts['new-stable-identity']}")
    print(f"held = {counts['held']}")
    print(f"hypothetical registry append = {len(append_rows)}")
    print(f"hypothetical NoteID range = {plan_range['First']}..{plan_range['Last']} / NOT RESERVED")
    print(f"external evidence bindings = {len(binding_rows)}")
    print(f"held source occurrences = {held_occurrences}")
    print("current Stable registry mutation = no")
    print("current Master source mapping mutation = no")
    print("current Learner/Release/Publish/Anki mutation = no")


if __name__ == "__main__":
    main()
