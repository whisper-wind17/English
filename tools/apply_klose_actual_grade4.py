#!/usr/bin/env python3
"""Overlay the authoritative Klose Grade-4 textbook edition onto the legacy build.

The legacy rj_start1 adapter remains historical inventory. This script adds the
confirmed `klose-current` Grade-4 provenance, appends genuinely new NoteIDs, and
extends the long-lived released set without rewriting the legacy registries.

It intentionally does not fabricate learner examples for new notes. New learning
units enter learner_review.csv and remain release-blocked until presentation
content is curated and approved.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER_DIR = BASE / "master"
LEARNER_DIR = BASE / "learner"
REVIEW_DIR = BASE / "review"

ACTUAL = BASE / "source_reference" / "rj_start1-grade4-klose-actual.csv"
REGISTRY_EXTENSIONS = MASTER_DIR / "note_registry_extensions.csv"
SOURCE_IDENTITY_EXTENSIONS = MASTER_DIR / "source_identity_extensions.csv"
RELEASE_EXTENSIONS = MASTER_DIR / "release_registry_extensions.csv"
MASTER = MASTER_DIR / "vocabulary_master.csv"
OCCURRENCES = MASTER_DIR / "source_occurrences.csv"
LEARNER = LEARNER_DIR / "current.csv"
LEARNER_REVIEW = REVIEW_DIR / "learner_review.csv"
STATS = MASTER_DIR / "build_stats.csv"

SOURCE_ID = "rj_start1"
SOURCE_EDITION = "klose-current"
LEARNER_PROFILE = "klose"
LEARNER_LEVEL = "4"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'")
    value = re.sub(r"\s+", " ", value.strip())
    return value.casefold()


def note_num(note_id: str) -> int:
    m = re.fullmatch(r"KV(\d{6})", note_id)
    if not m:
        raise SystemExit(f"Invalid NoteID: {note_id!r}")
    return int(m.group(1))


def source_item_key(row: dict[str, str]) -> str:
    semester = {"上": "upper", "下": "lower"}.get(row.get("Semester", "").strip())
    if semester is None:
        raise SystemExit(f"Invalid Grade-4 semester: {row}")
    return (
        f"grade4-{semester}-u{int(row['Unit']):02d}-o{int(row['Order']):03d}"
        f"|{normalize(row['Entry'])}"
    )


def add_pipe_value(value: str, item: str) -> str:
    parts = [x for x in value.split("|") if x]
    if item not in parts:
        parts.append(item)
    return "|".join(parts)


def add_tags(value: str, *items: str) -> str:
    tags = {x for x in value.split() if x}
    tags.update(x for x in items if x)
    return " ".join(sorted(tags))


def upsert_metric(rows: list[dict[str, str]], metric: str, value: int | str) -> None:
    for row in rows:
        if row.get("Metric") == metric:
            row["Value"] = str(value)
            return
    rows.append({"Metric": metric, "Value": str(value)})


def main() -> None:
    required = (
        ACTUAL, REGISTRY_EXTENSIONS, SOURCE_IDENTITY_EXTENSIONS,
        RELEASE_EXTENSIONS, MASTER, OCCURRENCES, LEARNER, LEARNER_REVIEW, STATS,
    )
    for path in required:
        if not path.exists():
            raise SystemExit(f"Missing actual Grade-4 overlay input: {path.relative_to(ROOT)}")

    actual = read_csv(ACTUAL)
    registry_ext = read_csv(REGISTRY_EXTENSIONS)
    registry_ext_by_id = {r["NoteID"].strip(): r for r in registry_ext}
    source_mappings = {
        r["SourceItemKey"].strip(): r
        for r in read_csv(SOURCE_IDENTITY_EXTENSIONS)
        if r.get("SourceID", "").strip() == SOURCE_ID
        and r.get("SourceEdition", "").strip() == SOURCE_EDITION
        and r.get("Status", "").strip() == "confirmed"
        and r.get("SourceItemKey", "").strip().startswith("grade4-")
    }

    actual_by_key: dict[str, tuple[int, dict[str, str]]] = {}
    note_sources: dict[str, list[tuple[int, dict[str, str]]]] = defaultdict(list)
    for index, row in enumerate(actual, start=2):
        key = source_item_key(row)
        if key in actual_by_key:
            raise SystemExit(f"Duplicate actual Grade-4 source item: {key}")
        mapping = source_mappings.get(key)
        if mapping is None:
            raise SystemExit(f"Actual Grade-4 source item has no confirmed identity mapping: {key}")
        nid = mapping["NoteID"].strip()
        actual_by_key[key] = (index, row)
        note_sources[nid].append((index, row))

    extra_mappings = sorted(set(source_mappings) - set(actual_by_key))
    if extra_mappings:
        raise SystemExit(f"Actual Grade-4 identity map has extra items: {extra_mappings[:10]}")

    master_rows = read_csv(MASTER)
    learner_rows = read_csv(LEARNER)
    occurrence_rows = read_csv(OCCURRENCES)
    review_rows = read_csv(LEARNER_REVIEW)
    stats = read_csv(STATS)

    master_fields = list(master_rows[0].keys())
    learner_fields = list(learner_rows[0].keys())
    master_by_id = {r["NoteID"].strip(): r for r in master_rows}
    learner_by_id = {r["NoteID"].strip(): r for r in learner_rows}

    released_before = {nid for nid, row in master_by_id.items() if row.get("Released") == "yes"}
    actual_note_ids = set(note_sources)
    release_ext_rows = read_csv(RELEASE_EXTENSIONS)
    release_ext_ids = {r["NoteID"].strip() for r in release_ext_rows}
    expected_release_extensions = actual_note_ids - released_before
    if release_ext_ids != expected_release_extensions:
        missing = sorted(expected_release_extensions - release_ext_ids)
        extra = sorted(release_ext_ids - expected_release_extensions)
        raise SystemExit(
            "Actual Grade-4 release extension mismatch: "
            f"missing={missing[:10]} extra={extra[:10]}"
        )

    new_notes = sorted(actual_note_ids - set(master_by_id), key=note_num)
    if set(new_notes) != set(registry_ext_by_id):
        missing = sorted(set(new_notes) - set(registry_ext_by_id))
        extra = sorted(set(registry_ext_by_id) - set(new_notes))
        raise SystemExit(
            "Actual Grade-4 NoteID extension mismatch: "
            f"missing_registry={missing[:10]} extra_registry={extra[:10]}"
        )

    # Add actual-textbook provenance to reused Notes and mark release extensions.
    for nid, sources in note_sources.items():
        if nid not in master_by_id:
            continue
        master = master_by_id[nid]
        for _, source in sources:
            semester = source["Semester"].strip()
            book = f"{SOURCE_ID}::{SOURCE_EDITION}::4年级{semester}"
            master["SourceBooks"] = add_pipe_value(master.get("SourceBooks", ""), book)
            master["Tags"] = add_tags(
                master.get("Tags", ""),
                f"source::{SOURCE_ID}",
                f"source::{SOURCE_ID}::edition::{SOURCE_EDITION}",
                f"source::{SOURCE_ID}::edition::{SOURCE_EDITION}::grade::4",
                f"source::{SOURCE_ID}::edition::{SOURCE_EDITION}::grade::4::{semester}",
            )
        if nid in release_ext_ids:
            master["Released"] = "yes"
            master["Tags"] = add_tags(master.get("Tags", ""), "learner::klose::released")

    # Append genuinely new identity/fact rows. IPA and learner examples are left
    # blank deliberately; review gates must keep them from being considered ready.
    for nid in new_notes:
        reg = registry_ext_by_id[nid]
        _, source = note_sources[nid][0]
        semester = source["Semester"].strip()
        source_book = f"{SOURCE_ID}::{SOURCE_EDITION}::4年级{semester}"
        tags = add_tags(
            "",
            f"source::{SOURCE_ID}",
            f"source::{SOURCE_ID}::edition::{SOURCE_EDITION}",
            f"source::{SOURCE_ID}::edition::{SOURCE_EDITION}::grade::4",
            f"source::{SOURCE_ID}::edition::{SOURCE_EDITION}::grade::4::{semester}",
            "learner::klose::released",
            f"learner::klose::level::{LEARNER_LEVEL}",
        )
        master = {
            "NoteID": nid,
            "CanonicalWord": reg["CanonicalWord"].strip(),
            "MatchKey": reg["MatchKey"].strip(),
            "SenseLabel": reg["SenseLabel"].strip(),
            "Word": source["Entry"].strip(),
            "British": "",
            "American": "",
            "MeaningPrimary": source["Meaning"].strip(),
            "MeaningRaw": source["Meaning"].strip(),
            "FirstSource": SOURCE_ID,
            "FirstSourceBook": f"{SOURCE_EDITION}::4年级{semester}",
            "FirstGrade": "4",
            "FirstSemester": semester,
            "Sources": SOURCE_ID,
            "SourceBooks": source_book,
            "Released": "yes",
            "Tags": tags,
        }
        master_rows.append(master)
        master_by_id[nid] = master
        learner = {
            "NoteID": nid,
            "LearnerProfile": LEARNER_PROFILE,
            "LearnerLevel": LEARNER_LEVEL,
            "ExampleSentence": "",
            "ExampleTranslation": "",
            "PresentationStatus": "actual-grade4-pending",
            "PresentationSource": f"{SOURCE_ID}:{SOURCE_EDITION}:actual-grade4",
        }
        learner_rows.append(learner)
        learner_by_id[nid] = learner

    # Actual source occurrences are first-class provenance. Extend the physical
    # occurrence schema with Edition/Page while keeping legacy rows compatible.
    occurrence_fields = [
        "NoteID", "SourceID", "SourceEdition", "SourceBook", "Grade", "Semester",
        "Unit", "SourceWord", "SourceFile", "SourceRow", "Page",
    ]
    for index, source in enumerate(actual, start=2):
        key = source_item_key(source)
        nid = source_mappings[key]["NoteID"].strip()
        occurrence_rows.append({
            "NoteID": nid,
            "SourceID": SOURCE_ID,
            "SourceEdition": SOURCE_EDITION,
            "SourceBook": f"4年级{source['Semester'].strip()}",
            "Grade": "4",
            "Semester": source["Semester"].strip(),
            "Unit": source["Unit"].strip(),
            "SourceWord": source["Entry"].strip(),
            "SourceFile": ACTUAL.name,
            "SourceRow": str(index),
            "Page": source["Page"].strip(),
        })

    # New Notes require learner content before release readiness. Keep this queue
    # explicit rather than inventing generic examples during source reconciliation.
    review_by_id = {r.get("NoteID", "").strip(): r for r in review_rows}
    for nid in new_notes:
        if nid in review_by_id:
            continue
        source = note_sources[nid][0][1]
        review_rows.append({
            "NoteID": nid,
            "Word": source["Entry"].strip(),
            "FirstGrade": "4",
            "ExampleSentence": "",
            "Reason": "actual-grade4-new-note-needs-learner-content",
        })

    master_rows.sort(key=lambda r: note_num(r["NoteID"]))
    learner_rows.sort(key=lambda r: note_num(r["NoteID"]))
    occurrence_rows.sort(
        key=lambda r: (
            note_num(r["NoteID"]),
            r.get("SourceID", ""),
            r.get("SourceEdition", ""),
            r.get("SourceBook", ""),
            int(r.get("SourceRow", "0") or 0),
        )
    )
    review_rows.sort(key=lambda r: note_num(r["NoteID"]))

    write_csv(MASTER, master_fields, master_rows)
    write_csv(LEARNER, learner_fields, learner_rows)
    write_csv(OCCURRENCES, occurrence_fields, occurrence_rows)
    write_csv(
        LEARNER_REVIEW,
        ["NoteID", "Word", "FirstGrade", "ExampleSentence", "Reason"],
        review_rows,
    )

    released_after = {r["NoteID"] for r in master_rows if r.get("Released") == "yes"}
    upsert_metric(stats, "actual_grade4_occurrences", len(actual))
    upsert_metric(stats, "actual_grade4_notes", len(actual_note_ids))
    upsert_metric(stats, "actual_grade4_new_notes", len(new_notes))
    upsert_metric(stats, "actual_grade4_release_extensions", len(release_ext_ids))
    upsert_metric(stats, "master_notes", len(master_rows))
    upsert_metric(stats, "inventory_notes", len(master_rows))
    upsert_metric(stats, "released_notes", len(released_after))
    upsert_metric(stats, "source_occurrences", len(occurrence_rows))
    write_csv(STATS, ["Metric", "Value"], stats)

    print(
        "Applied actual Grade-4 overlay: "
        f"occurrences={len(actual)}, learning_units={len(actual_note_ids)}, "
        f"new_notes={len(new_notes)}, release_extensions={len(release_ext_ids)}, "
        f"inventory={len(master_rows)}, released={len(released_after)}, "
        f"new_content_pending={len(new_notes)}"
    )


if __name__ == "__main__":
    main()
