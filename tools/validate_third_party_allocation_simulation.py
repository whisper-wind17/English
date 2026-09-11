#!/usr/bin/env python3
"""Validate simulated post-allocation state without mutating repository truth."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
PLAN = TP / "allocation" / "plan.json"
REGISTRY = BASE / "master" / "note_registry.csv"
REGISTRY_EXT = BASE / "master" / "note_registry_extensions.csv"
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


def rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def obj(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def note_num(note_id: str) -> int:
    match = NOTE_RE.fullmatch(note_id)
    require(match is not None, f"Invalid NoteID: {note_id}")
    return int(match.group(1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run-dir", required=True)
    parser.add_argument("--simulation-dir", required=True)
    args = parser.parse_args()

    dry = Path(args.dry_run_dir).expanduser().resolve()
    sim = Path(args.simulation_dir).expanduser().resolve()
    plan = obj(PLAN)

    legacy_fields, legacy = rows(REGISTRY)
    ext_fields, current_ext = rows(REGISTRY_EXT)
    append_fields, append_rows = rows(dry / "registry_append.csv")
    dry_binding_fields, dry_bindings = rows(dry / "stable_evidence_bindings.csv")
    sim_ext_fields, sim_ext = rows(sim / "note_registry_extensions.csv")
    sim_binding_fields, sim_bindings = rows(sim / "stable_evidence_bindings.csv")
    require(legacy_fields == ext_fields == append_fields == sim_ext_fields == REGISTRY_FIELDS, "Simulated registry schema drift")
    require(dry_binding_fields == sim_binding_fields == BINDING_FIELDS, "Simulated evidence binding schema drift")

    expected_ext = list(current_ext) + list(append_rows)
    expected_ext.sort(key=lambda r: note_num(r["NoteID"]))
    require(sim_ext == expected_ext, "Simulated registry extension is not exact current + append set")

    legacy_ids = {r["NoteID"] for r in legacy}
    current_ext_ids = {r["NoteID"] for r in current_ext}
    require(not (legacy_ids & current_ext_ids), "Legacy and extension registry NoteID sets overlap")
    append_ids = [r["NoteID"] for r in append_rows]
    require(len(append_ids) == len(set(append_ids)), "Dry-run append NoteID duplicate")
    require(not ((legacy_ids | current_ext_ids) & set(append_ids)), "Dry-run append collides with current Stable NoteIDs")

    origin_rows = [r for r in append_rows if r["PrimaryOriginKey"].startswith("third-party-vocabulary|candidate:")]
    require(len(origin_rows) == len(append_rows), "Simulated append contains non-third-party origin")
    origins = [r["PrimaryOriginKey"] for r in append_rows]
    require(len(origins) == len(set(origins)), "Simulated append origin duplicate")

    range_plan = plan["HypotheticalAppendRange"]
    require(len(append_rows) == range_plan["Count"] == 1821, "Simulated append count drift")
    require(append_rows[0]["NoteID"] == range_plan["First"] == "KV001195", "Simulated first NoteID drift")
    require(append_rows[-1]["NoteID"] == range_plan["Last"] == "KV003015", "Simulated last NoteID drift")
    require(range_plan["Reserved"] is False, "Hypothetical NoteID range unexpectedly reserved")

    require(sim_bindings == dry_bindings, "Simulated evidence binding set differs from validated dry run")
    binding_keys = [(r["ProvisionalIdentityKey"], r["SourceOccurrenceKey"]) for r in sim_bindings]
    require(len(binding_keys) == len(set(binding_keys)), "Simulated evidence binding duplicate")
    require(len(sim_bindings) == 15791, "Simulated evidence binding count drift")
    require(all(r["EvidenceStatus"] == "external-unverified-edition" for r in sim_bindings), "Simulated evidence status drift")

    bound_note_ids = {r["NoteID"] for r in sim_bindings}
    simulated_full_ids = legacy_ids | {r["NoteID"] for r in sim_ext}
    require(bound_note_ids <= simulated_full_ids, "Evidence binding references NoteID outside simulated full Stable registry")

    print("Third-party allocation simulation validation = pass")
    print(f"simulated new Stable rows = {len(append_rows)}")
    print(f"simulated full Stable NoteIDs = {len(simulated_full_ids)}")
    print(f"simulated NoteID range = {range_plan['First']}..{range_plan['Last']} / NOT RESERVED")
    print(f"simulated external evidence bindings = {len(sim_bindings)}")
    print("Master textbook source mapping mutation = no")
    print("Learner/Release/Publish/Anki mutation = no")


if __name__ == "__main__":
    main()
