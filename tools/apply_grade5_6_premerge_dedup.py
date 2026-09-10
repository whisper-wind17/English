#!/usr/bin/env python3
"""Apply reviewed Grade 5-6 premerge Vocabulary dedup migrations.

Allocated NoteIDs are never deleted or reused.  A deduplicated incoming identity is
retired with Status=merged, an explicit approved migration points to the older
survivor, reviewed reconciliation is rebound to reuse-existing, and Grade 5-6
source identity mappings are retargeted to that survivor.
"""
from __future__ import annotations

import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master"
REVIEW = BASE / "review"
DEDUP = REVIEW / "grade5_6_premerge_dedup"
REC = REVIEW / "grade5_6_reconciliation"

DEDUP_DECISIONS = DEDUP / "decisions.csv"
REGISTRY_EXT = MASTER / "note_registry_extensions.csv"
SOURCE_EXT = MASTER / "source_identity_extensions.csv"
MIGRATIONS = MASTER / "identity_migrations.csv"
VOCAB_DECISIONS = REC / "vocabulary_decisions.csv"
GRADE56_SOURCE = "klose-grade5-6-current"
ORIGIN_PREFIX = GRADE56_SOURCE + "|"

MIGRATION_FIELDS = ["MigrationID", "NoteID", "TargetNoteID", "MigrationType", "Reason", "Status"]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def main() -> None:
    subprocess.run(["python", "tools/check_grade5_6_premerge_dedup.py"], cwd=ROOT, check=True)

    _, review = read_csv(DEDUP_DECISIONS)
    merge_map = {
        r["NewNoteID"].strip(): r["MergeIntoNoteID"].strip()
        for r in review if r.get("Decision", "").strip() == "merge-new-into-existing"
    }
    if len(merge_map) != 5:
        raise SystemExit(f"Expected 5 reviewed dedup migrations, got {len(merge_map)}")

    reg_fields, reg = read_csv(REGISTRY_EXT)
    reg_by_id = {r["NoteID"].strip(): r for r in reg}
    all_ids = set(reg_by_id)
    legacy_ids = {
        r["NoteID"].strip()
        for r in read_csv(MASTER / "note_registry.csv")[1]
    }
    all_ids |= legacy_ids

    group_by_note: dict[str, str] = {}
    for nid, target in merge_map.items():
        row = reg_by_id.get(nid)
        if row is None or row.get("CreatedSource", "").strip() != GRADE56_SOURCE:
            raise SystemExit(f"Dedup source is not a Grade 5-6 allocated Note: {nid}")
        if target not in all_ids:
            raise SystemExit(f"Unknown dedup survivor: {nid}->{target}")
        origin = row.get("PrimaryOriginKey", "").strip()
        if not origin.startswith(ORIGIN_PREFIX + "new::"):
            raise SystemExit(f"Invalid Grade 5-6 allocation origin: {nid}->{origin!r}")
        group_by_note[nid] = origin[len(ORIGIN_PREFIX):]
        status = row.get("Status", "").strip()
        if status not in {"active", "merged"}:
            raise SystemExit(f"Unexpected source identity status before migration: {nid}->{status!r}")
        row["Status"] = "merged"

    # Rebind the original reconciliation groups to the older survivor.  Candidate
    # fingerprints remain valid because only the reviewed identity decision changes.
    vocab_fields, vocab = read_csv(VOCAB_DECISIONS)
    rebound_groups: set[str] = set()
    rationale_by_source = {
        r["NewNoteID"].strip(): r.get("Rationale", "").strip()
        for r in review if r.get("Decision", "").strip() == "merge-new-into-existing"
    }
    for row in vocab:
        if row.get("Decision", "").strip() != "new-stable-identity":
            continue
        group = row.get("DecisionIdentityGroup", "").strip()
        source_id = next((nid for nid, g in group_by_note.items() if g == group), "")
        if not source_id:
            continue
        target = merge_map[source_id]
        row["Decision"] = "reuse-existing"
        row["DecisionNoteID"] = target
        row["DecisionIdentityGroup"] = target
        row["DecisionBasis"] = "premerge-dedup-reviewed"
        row["Rationale"] = rationale_by_source[source_id]
        rebound_groups.add(group)
    if rebound_groups != set(group_by_note.values()):
        raise SystemExit(f"Not all retired allocation groups were rebound: {set(group_by_note.values()) - rebound_groups}")

    source_fields, source_rows = read_csv(SOURCE_EXT)
    rebound_source_rows = 0
    for row in source_rows:
        nid = row.get("NoteID", "").strip()
        if nid not in merge_map:
            continue
        row["NoteID"] = merge_map[nid]
        row["Decision"] = "reuse-existing"
        row["Status"] = "confirmed"
        rebound_source_rows += 1
    if rebound_source_rows < len(merge_map):
        raise SystemExit(f"Too few source mappings rebound: {rebound_source_rows}")

    mig_fields, migrations = read_csv(MIGRATIONS)
    if "TargetNoteID" not in mig_fields:
        mig_fields = MIGRATION_FIELDS
        migrations = [{f: r.get(f, "") for f in mig_fields} for r in migrations]
    elif mig_fields != MIGRATION_FIELDS:
        raise SystemExit(f"Unexpected migration schema: {mig_fields}")
    existing = {(r.get("NoteID", "").strip(), r.get("MigrationType", "").strip()): r for r in migrations}
    for nid, target in sorted(merge_map.items()):
        key = (nid, "identity-merge-dedup")
        row = existing.get(key)
        reason = f"Grade 5-6 premerge dedup: reviewed identity is equivalent to older Stable Note {target}."
        if row is None:
            migrations.append({
                "MigrationID": f"MIG-20260910-G56-DEDUP-{nid}",
                "NoteID": nid,
                "TargetNoteID": target,
                "MigrationType": "identity-merge-dedup",
                "Reason": reason,
                "Status": "approved",
            })
        elif row.get("TargetNoteID", "").strip() != target or row.get("Status", "").strip() != "approved":
            raise SystemExit(f"Existing dedup migration disagrees: {nid}")

    write_csv(REGISTRY_EXT, reg_fields, reg)
    write_csv(VOCAB_DECISIONS, vocab_fields, vocab)
    write_csv(SOURCE_EXT, source_fields, source_rows)
    write_csv(MIGRATIONS, mig_fields, migrations)
    print(
        "Grade 5-6 premerge dedup applied: "
        f"retired_allocated_ids={len(merge_map)}, active_grade56_new=288, "
        f"rebound_source_rows={rebound_source_rows}, stable_ids_deleted=0"
    )


if __name__ == "__main__":
    main()
