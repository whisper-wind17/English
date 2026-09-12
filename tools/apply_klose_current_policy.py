"""Materialize current presentation corrections and curriculum decisions."""
from __future__ import annotations

import csv
from pathlib import Path

from klose_current_policy import admission_decisions, read_csv
from klose_release_curriculum import current_curriculum_ordered_note_ids
from klose_learning_order import format_learning_order

BASE = Path(__file__).resolve().parents[1] / "anki/klose"


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    master_path = BASE / "master/vocabulary_master.csv"
    master = read_csv(master_path)
    by_id = {r["NoteID"]: r for r in master}
    seen = set()
    for row in read_csv(BASE / "learner/presentation_adjustments.csv"):
        nid = row["NoteID"]
        if nid in seen or nid not in by_id or not row.get("Reason", "").strip():
            raise SystemExit(f"Invalid presentation adjustment: {nid}")
        seen.add(nid)
        for field in ("Word", "MeaningPrimary"):
            if row.get(field, "").strip():
                by_id[nid][field] = row[field].strip()
    write_csv(master_path, master)
    ordered, states = current_curriculum_ordered_note_ids()
    positions = {nid: format_learning_order(i) for i, nid in enumerate(ordered, 1)}
    decisions = admission_decisions()
    path = BASE / "learner/learning_admission.csv"
    rows = read_csv(path)
    if set(ordered) - {r["NoteID"] for r in rows}:
        raise SystemExit("Current curriculum has no materialized admission row")
    for row in rows:
        nid = row["NoteID"]
        if nid in positions:
            stage, tag = states[nid]
            row.update(Status="allowed", Stage=stage, LearningTag=tag, LearningOrder=positions[nid])
        else:
            row.update(Status="held", Stage="stage::library", LearningTag="", LearningOrder="")
        if nid in decisions:
            row["Reason"] = decisions[nid]["Reason"]
    write_csv(path, rows)
    print(f"Current policy: allowed={len(ordered)} held={len(rows)-len(ordered)} adjustments={len(seen)}")


if __name__ == "__main__":
    main()
