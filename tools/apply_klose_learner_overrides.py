#!/usr/bin/env python3
"""Apply Klose Grade-4 learner presentation overrides and rebuild publish views.

This runs after build_klose_vocabulary.py. Identity/source facts remain untouched;
only learner presentation and derived publish files are changed.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master" / "vocabulary_master.csv"
OCCURRENCES = BASE / "master" / "source_occurrences.csv"
STATS = BASE / "master" / "build_stats.csv"
LEARNER = BASE / "learner" / "current.csv"
OVERRIDES = BASE / "learner" / "grade4_overrides.csv"
REVIEW = BASE / "review" / "learner_review.csv"
PUBLISH = BASE / "publish"
SOURCE_ID = "rj_start1"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def note_num(note_id: str) -> int:
    return int(note_id.removeprefix("KV"))


def main() -> None:
    for path in (MASTER, OCCURRENCES, LEARNER, OVERRIDES, REVIEW):
        if not path.exists():
            raise SystemExit(f"Missing input: {path.relative_to(ROOT)}")

    master_rows = read_csv(MASTER)
    learner_rows = read_csv(LEARNER)
    occurrence_rows = read_csv(OCCURRENCES)
    review_rows = read_csv(REVIEW)
    override_rows = read_csv(OVERRIDES)

    learner_by_id = {r["NoteID"]: r for r in learner_rows}
    master_ids = {r["NoteID"] for r in master_rows}
    seen: set[str] = set()
    for row in override_rows:
        nid = row["NoteID"].strip()
        if nid in seen:
            raise SystemExit(f"Duplicate learner override: {nid}")
        seen.add(nid)
        if nid not in master_ids:
            raise SystemExit(f"Unknown learner override NoteID: {nid}")
        if not row["ExampleSentence"].strip() or not row["ExampleTranslation"].strip():
            raise SystemExit(f"Incomplete learner override: {nid}")
        target = learner_by_id[nid]
        target["ExampleSentence"] = row["ExampleSentence"].strip()
        target["ExampleTranslation"] = row["ExampleTranslation"].strip()
        target["PresentationStatus"] = "grade4-reviewed"
        target["PresentationSource"] = "klose:grade4_overrides"

    learner_rows.sort(key=lambda r: note_num(r["NoteID"]))
    learner_fields = [
        "NoteID", "LearnerProfile", "LearnerLevel", "ExampleSentence",
        "ExampleTranslation", "PresentationStatus", "PresentationSource",
    ]
    write_csv(LEARNER, learner_fields, learner_rows)

    # Remove resolved heuristic suggestions. Remaining rows stay explicit.
    review_rows = [r for r in review_rows if r["NoteID"] not in seen]
    write_csv(REVIEW, ["NoteID", "Word", "FirstGrade", "ExampleSentence", "Reason"], review_rows)

    publish_fields = [
        "NoteID", "CanonicalWord", "Word", "British", "American", "MeaningPrimary",
        "ExampleSentence", "ExampleTranslation", "LearnerLevel", "Sources", "SourceBooks", "Tags",
    ]
    publish_rows: list[dict[str, str]] = []
    for master in master_rows:
        learner = learner_by_id[master["NoteID"]]
        publish_rows.append({**master, **learner})
    publish_rows.sort(key=lambda r: note_num(r["NoteID"]))

    write_csv(PUBLISH / "all.csv", publish_fields, publish_rows)
    study_rows = [r for r in publish_rows if r["Released"] == "yes"]
    write_csv(PUBLISH / "study.csv", publish_fields, study_rows)

    migration_fields = ["Word"] + [f for f in publish_fields if f != "Word"]
    write_csv(PUBLISH / "migration" / "word-first-all.csv", migration_fields, publish_rows)
    write_csv(PUBLISH / "migration" / "word-first-study.csv", migration_fields, study_rows)

    grades_by_id: dict[str, set[int]] = defaultdict(set)
    for occ in occurrence_rows:
        if occ["SourceID"] == SOURCE_ID and occ["Grade"].isdigit():
            grades_by_id[occ["NoteID"]].add(int(occ["Grade"]))
    for grade in range(1, 7):
        rows = [r for r in publish_rows if grade in grades_by_id[r["NoteID"]]]
        write_csv(PUBLISH / "by-source" / SOURCE_ID / f"grade{grade}.csv", publish_fields, rows)

    # Keep build stats aligned with the final learner layer.
    stats = read_csv(STATS)
    for row in stats:
        if row["Metric"] == "learner_review_suggestions":
            row["Value"] = str(len(review_rows))
    write_csv(STATS, ["Metric", "Value"], stats)

    print(f"Applied Grade-4 overrides: {len(override_rows)}")
    print(f"Remaining learner review suggestions: {len(review_rows)}")


if __name__ == "__main__":
    main()
