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
OVERRIDE_FILES = [
    BASE / "learner" / "grade4_overrides.csv",
    BASE / "learner" / "grade4_guardrail_overrides.csv",
    BASE / "learner" / "grade4_full_review_a.csv",
    BASE / "learner" / "grade4_full_review_b.csv",
    BASE / "learner" / "grade4_full_review_c.csv",
]
REVIEW = BASE / "review" / "learner_review.csv"
PUBLISH = BASE / "publish"
SOURCE_ID = "rj_start1"

STAGE_GRADE4_NEW = "stage::grade4-new"
STAGE_GRADE4_REVIEW = "stage::grade4-review"
STAGE_LOWER_BACKFILL = "stage::lower-grade-backfill"
STAGE_TAGS = {STAGE_GRADE4_NEW, STAGE_GRADE4_REVIEW, STAGE_LOWER_BACKFILL}


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


def source_grades(occurrence_rows: list[dict[str, str]]) -> dict[str, set[int]]:
    grades_by_id: dict[str, set[int]] = defaultdict(set)
    for occ in occurrence_rows:
        if occ["SourceID"] == SOURCE_ID and occ["Grade"].isdigit():
            grades_by_id[occ["NoteID"]].add(int(occ["Grade"]))
    return grades_by_id


def onboarding_stage(grades: set[int]) -> str:
    if not grades:
        return ""
    first_grade = min(grades)
    if first_grade == 4:
        return STAGE_GRADE4_NEW
    if 4 in grades and first_grade < 4:
        return STAGE_GRADE4_REVIEW
    if first_grade < 4:
        return STAGE_LOWER_BACKFILL
    return ""


def with_stage(tags: str, stage: str) -> str:
    parts = [x for x in tags.split() if x not in STAGE_TAGS]
    if stage:
        parts.append(stage)
    return " ".join(sorted(set(parts)))


def upsert_metric(stats: list[dict[str, str]], metric: str, value: int | str) -> None:
    for row in stats:
        if row["Metric"] == metric:
            row["Value"] = str(value)
            return
    stats.append({"Metric": metric, "Value": str(value)})


def main() -> None:
    for path in (MASTER, OCCURRENCES, LEARNER, REVIEW, *OVERRIDE_FILES):
        if not path.exists():
            raise SystemExit(f"Missing input: {path.relative_to(ROOT)}")

    master_rows = read_csv(MASTER)
    learner_rows = read_csv(LEARNER)
    occurrence_rows = read_csv(OCCURRENCES)
    review_rows = read_csv(REVIEW)

    learner_by_id = {r["NoteID"]: r for r in learner_rows}
    master_ids = {r["NoteID"] for r in master_rows}
    resolved_ids: set[str] = set()
    applied_rows = 0

    # Ordered explicit layers. Later files intentionally override earlier rows.
    for override_path in OVERRIDE_FILES:
        local_seen: set[str] = set()
        for row in read_csv(override_path):
            nid = row["NoteID"].strip()
            if nid in local_seen:
                raise SystemExit(f"Duplicate learner override in {override_path.name}: {nid}")
            local_seen.add(nid)
            if nid not in master_ids:
                raise SystemExit(f"Unknown learner override NoteID: {nid}")
            if not row["ExampleSentence"].strip() or not row["ExampleTranslation"].strip():
                raise SystemExit(f"Incomplete learner override: {nid}")
            target = learner_by_id[nid]
            target["ExampleSentence"] = row["ExampleSentence"].strip()
            target["ExampleTranslation"] = row["ExampleTranslation"].strip()
            target["PresentationStatus"] = "grade4-reviewed"
            target["PresentationSource"] = f"klose:{override_path.stem}"
            resolved_ids.add(nid)
            applied_rows += 1

    learner_rows.sort(key=lambda r: note_num(r["NoteID"]))
    learner_fields = [
        "NoteID", "LearnerProfile", "LearnerLevel", "ExampleSentence",
        "ExampleTranslation", "PresentationStatus", "PresentationSource",
    ]
    write_csv(LEARNER, learner_fields, learner_rows)

    # Remove resolved heuristic suggestions. Remaining rows stay explicit.
    review_rows = [r for r in review_rows if r["NoteID"] not in resolved_ids]
    write_csv(REVIEW, ["NoteID", "Word", "FirstGrade", "ExampleSentence", "Reason"], review_rows)

    grades_by_id = source_grades(occurrence_rows)
    publish_fields = [
        "NoteID", "CanonicalWord", "Word", "British", "American", "MeaningPrimary",
        "ExampleSentence", "ExampleTranslation", "LearnerLevel", "Sources", "SourceBooks", "Tags",
    ]
    publish_rows: list[dict[str, str]] = []
    for master in master_rows:
        learner = learner_by_id[master["NoteID"]]
        row = {**master, **learner}
        if master["Released"] == "yes":
            row["Tags"] = with_stage(row.get("Tags", ""), onboarding_stage(grades_by_id.get(master["NoteID"], set())))
        publish_rows.append(row)
    publish_rows.sort(key=lambda r: note_num(r["NoteID"]))

    write_csv(PUBLISH / "all.csv", publish_fields, publish_rows)
    study_rows = [r for r in publish_rows if r["Released"] == "yes"]
    write_csv(PUBLISH / "study.csv", publish_fields, study_rows)

    migration_fields = ["Word"] + [f for f in publish_fields if f != "Word"]
    write_csv(PUBLISH / "migration" / "word-first-all.csv", migration_fields, publish_rows)
    write_csv(PUBLISH / "migration" / "word-first-study.csv", migration_fields, study_rows)

    for grade in range(1, 7):
        rows = [r for r in publish_rows if grade in grades_by_id.get(r["NoteID"], set())]
        write_csv(PUBLISH / "by-source" / SOURCE_ID / f"grade{grade}.csv", publish_fields, rows)

    # Convenience views only. They all belong to the same Anki main deck.
    stage_rows = {
        STAGE_GRADE4_NEW: [r for r in study_rows if STAGE_GRADE4_NEW in r["Tags"].split()],
        STAGE_GRADE4_REVIEW: [r for r in study_rows if STAGE_GRADE4_REVIEW in r["Tags"].split()],
        STAGE_LOWER_BACKFILL: [r for r in study_rows if STAGE_LOWER_BACKFILL in r["Tags"].split()],
    }
    write_csv(PUBLISH / "onboarding" / "grade4-new.csv", publish_fields, stage_rows[STAGE_GRADE4_NEW])
    write_csv(PUBLISH / "onboarding" / "grade4-review.csv", publish_fields, stage_rows[STAGE_GRADE4_REVIEW])
    write_csv(PUBLISH / "onboarding" / "lower-grade-backfill.csv", publish_fields, stage_rows[STAGE_LOWER_BACKFILL])

    staged_ids = [r["NoteID"] for rows in stage_rows.values() for r in rows]
    if len(staged_ids) != len(set(staged_ids)) or set(staged_ids) != {r["NoteID"] for r in study_rows}:
        raise SystemExit("Each released Grade-4 baseline note must belong to exactly one onboarding stage")

    stats = read_csv(STATS)
    upsert_metric(stats, "learner_review_suggestions", len(review_rows))
    upsert_metric(stats, "stage_grade4_new", len(stage_rows[STAGE_GRADE4_NEW]))
    upsert_metric(stats, "stage_grade4_review", len(stage_rows[STAGE_GRADE4_REVIEW]))
    upsert_metric(stats, "stage_lower_grade_backfill", len(stage_rows[STAGE_LOWER_BACKFILL]))
    write_csv(STATS, ["Metric", "Value"], stats)

    print(f"Applied Grade-4 override rows: {applied_rows} across {len(OVERRIDE_FILES)} layers")
    print(f"Unique Grade-4 overridden notes: {len(resolved_ids)}")
    print(f"Remaining learner review suggestions: {len(review_rows)}")
    print(
        "Onboarding stages: "
        f"grade4-new={len(stage_rows[STAGE_GRADE4_NEW])}, "
        f"grade4-review={len(stage_rows[STAGE_GRADE4_REVIEW])}, "
        f"lower-grade-backfill={len(stage_rows[STAGE_LOWER_BACKFILL])}"
    )


if __name__ == "__main__":
    main()
