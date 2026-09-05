#!/usr/bin/env python3
"""Apply learner presentation overrides and rebuild publish views.

Identity/source facts remain untouched. Once learning_admission.csv contains
current-profile rows, every released Note must have an explicit learning state:
`allowed` means it belongs to the current learning set; `held` means it remains
in long-lived study but is not currently learned. Both states keep exactly one
stage tag. Only allowed Notes receive a `learning::...` tag and a deterministic
LearningOrder for curriculum sequencing in Anki.

The old Grade-4 staging logic remains only as a compatibility fallback while the
explicit admission registry is empty.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
PROFILE = BASE / "config" / "profile.json"
MASTER = BASE / "master" / "vocabulary_master.csv"
OCCURRENCES = BASE / "master" / "source_occurrences.csv"
STATS = BASE / "master" / "build_stats.csv"
LEARNER = BASE / "learner" / "current.csv"
ADMISSION = BASE / "learner" / "learning_admission.csv"
OVERRIDE_FILES = [
    BASE / "learner" / "grade4_overrides.csv",
    BASE / "learner" / "grade4_guardrail_overrides.csv",
    BASE / "learner" / "grade4_full_review_a.csv",
    BASE / "learner" / "grade4_full_review_b.csv",
    BASE / "learner" / "grade4_full_review_c.csv",
    BASE / "learner" / "actual_grade4_overrides.csv",
]
REVIEW = BASE / "review" / "learner_review.csv"
PUBLISH = BASE / "publish"
SOURCE_ID = "rj_start1"

LEGACY_STAGE_GRADE4_NEW = "stage::grade4-new"
LEGACY_STAGE_GRADE4_REVIEW = "stage::grade4-review"
LEGACY_STAGE_LOWER_BACKFILL = "stage::lower-grade-backfill"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_anki_import(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
    note_type: str,
    deck: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("#separator:Comma\n")
        f.write("#html:false\n")
        f.write(f"#notetype:{note_type}\n")
        f.write(f"#deck:{deck}\n")
        f.write(f"#tags column:{fields.index('Tags') + 1}\n")
        f.write("#columns:" + ",".join(fields) + "\n")
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writerows(rows)


def note_num(note_id: str) -> int:
    return int(note_id.removeprefix("KV"))


def source_grades(occurrence_rows: list[dict[str, str]]) -> dict[str, set[int]]:
    grades_by_id: dict[str, set[int]] = defaultdict(set)
    for occ in occurrence_rows:
        if occ["SourceID"] == SOURCE_ID and occ["Grade"].isdigit():
            grades_by_id[occ["NoteID"]].add(int(occ["Grade"]))
    return grades_by_id


def legacy_onboarding_stage(grades: set[int]) -> str:
    if not grades:
        return ""
    first_grade = min(grades)
    if first_grade == 4:
        return LEGACY_STAGE_GRADE4_NEW
    if 4 in grades and first_grade < 4:
        return LEGACY_STAGE_GRADE4_REVIEW
    if first_grade < 4:
        return LEGACY_STAGE_LOWER_BACKFILL
    return ""


def load_explicit_admission(
    profile: str,
    level: str,
    valid_ids: set[str],
) -> dict[str, dict[str, str]]:
    if not ADMISSION.exists():
        return {}
    result: dict[str, dict[str, str]] = {}
    allowed_orders: list[int] = []
    for row in read_csv(ADMISSION):
        if row.get("LearnerProfile", "").strip() != profile or row.get("LearnerLevel", "").strip() != level:
            continue
        nid = row.get("NoteID", "").strip()
        status = row.get("Status", "").strip()
        stage = row.get("Stage", "").strip()
        learning_tag = row.get("LearningTag", "").strip()
        learning_order = row.get("LearningOrder", "").strip()
        if nid not in valid_ids:
            raise SystemExit(f"Learning admission references unknown NoteID: {nid}")
        if status not in {"allowed", "held"}:
            raise SystemExit(f"Learning admission has invalid Status for {nid}: {status!r}")
        if not stage.startswith("stage::"):
            raise SystemExit(f"Learning admission has invalid Stage for {nid}: {stage!r}")
        if status == "allowed":
            if not learning_tag.startswith("learning::"):
                raise SystemExit(f"Allowed learning admission requires LearningTag for {nid}")
            if not learning_order.isdigit() or int(learning_order) <= 0:
                raise SystemExit(f"Allowed learning admission requires positive LearningOrder for {nid}")
            allowed_orders.append(int(learning_order))
        else:
            if learning_tag:
                raise SystemExit(f"Held learning admission must not have LearningTag for {nid}: {learning_tag!r}")
            if learning_order:
                raise SystemExit(f"Held learning admission must not have LearningOrder for {nid}: {learning_order!r}")
        if nid in result:
            raise SystemExit(f"Duplicate learning admission for {nid}")
        result[nid] = {
            "Status": status,
            "Stage": stage,
            "LearningTag": learning_tag,
            "LearningOrder": learning_order,
            "Reason": row.get("Reason", "").strip(),
        }
    if allowed_orders and sorted(allowed_orders) != list(range(1, len(allowed_orders) + 1)):
        raise SystemExit("Allowed LearningOrder values must be unique and contiguous from 1")
    return result


def with_stage(tags: str, stage: str) -> str:
    parts = [x for x in tags.split() if not x.startswith("stage::")]
    if stage:
        parts.append(stage)
    return " ".join(sorted(set(parts)))


def with_learning_tag(tags: str, learning_tag: str) -> str:
    parts = [x for x in tags.split() if not x.startswith("learning::")]
    if learning_tag:
        parts.append(learning_tag)
    return " ".join(sorted(set(parts)))


def upsert_metric(stats: list[dict[str, str]], metric: str, value: int | str) -> None:
    for row in stats:
        if row["Metric"] == metric:
            row["Value"] = str(value)
            return
    stats.append({"Metric": metric, "Value": str(value)})


def main() -> None:
    for path in (PROFILE, MASTER, OCCURRENCES, LEARNER, REVIEW, ADMISSION, *OVERRIDE_FILES):
        if not path.exists():
            raise SystemExit(f"Missing input: {path.relative_to(ROOT)}")

    with PROFILE.open("r", encoding="utf-8") as f:
        profile = json.load(f)
    note_type = str(profile["note_type"])
    main_deck = str(profile["main_deck"])
    learner_profile = str(profile["learner_profile"])
    learner_level = str(profile["learner_level"])

    master_rows = read_csv(MASTER)
    learner_rows = read_csv(LEARNER)
    occurrence_rows = read_csv(OCCURRENCES)
    review_rows = read_csv(REVIEW)

    learner_by_id = {r["NoteID"]: r for r in learner_rows}
    master_ids = {r["NoteID"] for r in master_rows}
    explicit_admission = load_explicit_admission(learner_profile, learner_level, master_ids)
    resolved_ids: set[str] = set()
    applied_rows = 0

    for override_path in OVERRIDE_FILES:
        local_seen: set[str] = set()
        for row in read_csv(override_path):
            nid = row["NoteID"].strip()
            if not nid:
                continue
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

    review_rows = [r for r in review_rows if r["NoteID"] not in resolved_ids]
    write_csv(REVIEW, ["NoteID", "Word", "FirstGrade", "ExampleSentence", "Reason"], review_rows)

    grades_by_id = source_grades(occurrence_rows)
    publish_fields = [
        "NoteID", "CanonicalWord", "Word", "British", "American", "MeaningPrimary",
        "ExampleSentence", "ExampleTranslation", "LearnerLevel", "LearningOrder",
        "Sources", "SourceBooks", "Tags",
    ]
    publish_rows: list[dict[str, str]] = []
    released_ids = {r["NoteID"] for r in master_rows if r["Released"] == "yes"}

    if explicit_admission:
        missing = sorted(released_ids - set(explicit_admission))
        extra = sorted(set(explicit_admission) - released_ids)
        if missing or extra:
            raise SystemExit(
                "Explicit learning admission must cover exactly the current released set with allowed/held states; "
                f"missing={missing[:10]} extra={extra[:10]}"
            )

    for master in master_rows:
        learner = learner_by_id[master["NoteID"]]
        row = {**master, **learner}
        row["LearningOrder"] = ""
        if master["Released"] == "yes":
            if explicit_admission:
                admission = explicit_admission[master["NoteID"]]
                row["Tags"] = with_stage(row.get("Tags", ""), admission["Stage"])
                row["Tags"] = with_learning_tag(row["Tags"], admission["LearningTag"])
                row["LearningOrder"] = admission["LearningOrder"]
            else:
                stage = legacy_onboarding_stage(grades_by_id.get(master["NoteID"], set()))
                row["Tags"] = with_stage(row.get("Tags", ""), stage)
                row["Tags"] = with_learning_tag(row["Tags"], "")
        else:
            row["Tags"] = with_stage(row.get("Tags", ""), "")
            row["Tags"] = with_learning_tag(row["Tags"], "")
        publish_rows.append(row)
    publish_rows.sort(key=lambda r: note_num(r["NoteID"]))

    write_csv(PUBLISH / "all.csv", publish_fields, publish_rows)
    study_rows = [r for r in publish_rows if r["Released"] == "yes"]
    write_csv(PUBLISH / "study.csv", publish_fields, study_rows)
    write_anki_import(
        PUBLISH / "anki-import.csv",
        publish_fields,
        study_rows,
        note_type=note_type,
        deck=main_deck,
    )

    migration_fields = ["Word"] + [f for f in publish_fields if f != "Word"]
    write_csv(PUBLISH / "migration" / "word-first-all.csv", migration_fields, publish_rows)
    write_csv(PUBLISH / "migration" / "word-first-study.csv", migration_fields, study_rows)

    for grade in range(1, 7):
        rows = [r for r in publish_rows if grade in grades_by_id.get(r["NoteID"], set())]
        write_csv(PUBLISH / "by-source" / SOURCE_ID / f"grade{grade}.csv", publish_fields, rows)

    stage_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in study_rows:
        stages = [tag for tag in row["Tags"].split() if tag.startswith("stage::")]
        if len(stages) != 1:
            raise SystemExit(f"Released note must have exactly one stage: {row['NoteID']}")
        stage_rows[stages[0]].append(row)

    # Keep legacy convenience files while the initial migration fallback exists.
    write_csv(PUBLISH / "onboarding" / "grade4-new.csv", publish_fields, stage_rows[LEGACY_STAGE_GRADE4_NEW])
    write_csv(PUBLISH / "onboarding" / "grade4-review.csv", publish_fields, stage_rows[LEGACY_STAGE_GRADE4_REVIEW])
    write_csv(PUBLISH / "onboarding" / "lower-grade-backfill.csv", publish_fields, stage_rows[LEGACY_STAGE_LOWER_BACKFILL])

    stats = read_csv(STATS)
    upsert_metric(stats, "learner_review_suggestions", len(review_rows))
    upsert_metric(stats, "learning_admission_mode", "explicit" if explicit_admission else "legacy-grade4-fallback")
    if explicit_admission:
        allowed = sum(1 for row in explicit_admission.values() if row["Status"] == "allowed")
        held = sum(1 for row in explicit_admission.values() if row["Status"] == "held")
        upsert_metric(stats, "learning_admission_allowed", allowed)
        upsert_metric(stats, "learning_admission_held", held)
        upsert_metric(stats, "learning_order_count", allowed)
        upsert_metric(stats, "learning_order_max", allowed)
    for stage, rows in sorted(stage_rows.items()):
        upsert_metric(stats, f"stage_{stage.removeprefix('stage::').replace('-', '_')}", len(rows))
    write_csv(STATS, ["Metric", "Value"], stats)

    print(f"Applied learner override rows: {applied_rows} across {len(OVERRIDE_FILES)} layers")
    print(f"Unique overridden notes: {len(resolved_ids)}")
    print(f"Remaining learner review suggestions: {len(review_rows)}")
    if explicit_admission:
        allowed = sum(1 for row in explicit_admission.values() if row["Status"] == "allowed")
        held = sum(1 for row in explicit_admission.values() if row["Status"] == "held")
        print(f"Learning admission mode: explicit; allowed={allowed}; held={held}; learning_order=001..{allowed:03d}")
    else:
        print("Learning admission mode: legacy-grade4-fallback")


if __name__ == "__main__":
    main()
