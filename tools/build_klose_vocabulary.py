#!/usr/bin/env python3
"""Build the long-lived Klose Vocabulary System from source-specific curated data.

Current source adapter: 人教版一年级起点 (`rj_start1`).

Important invariants:
- NoteID comes from a committed registry and is append-only.
- Source provenance remains source-scoped.
- Learner presentation is separate from FirstGrade.
- `study.csv` contains released notes; `all.csv` is inventory.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
CONFIG = BASE / "config" / "profile.json"
MASTER_DIR = BASE / "master"
LEARNER_DIR = BASE / "learner"
PUBLISH_DIR = BASE / "publish"
REVIEW_DIR = BASE / "review"

SOURCE_ID = "rj_start1"
SOURCE_BASE = ROOT / "anki" / "人教版一年级起点" / "master"
SOURCE_MASTER = SOURCE_BASE / "vocabulary_master.csv"
SOURCE_OCCURRENCES = SOURCE_BASE / "vocabulary_occurrences.csv"

REGISTRY = MASTER_DIR / "note_registry.csv"
RELEASE_REGISTRY = MASTER_DIR / "release_registry.csv"
GLOBAL_MASTER = MASTER_DIR / "vocabulary_master.csv"
GLOBAL_OCCURRENCES = MASTER_DIR / "source_occurrences.csv"
LEARNER_CURRENT = LEARNER_DIR / "current.csv"
IDENTITY_REVIEW = REVIEW_DIR / "identity_review.csv"
LEARNER_REVIEW = REVIEW_DIR / "learner_review.csv"
BUILD_STATS = MASTER_DIR / "build_stats.csv"

REGISTRY_FIELDS = [
    "NoteID", "CanonicalWord", "MatchKey", "SenseLabel", "PrimaryOriginKey",
    "CreatedSource", "CreatedSourceBook", "Status",
]
RELEASE_FIELDS = ["NoteID", "ReleasedAt", "ReleaseReason"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "" if row.get(k) is None else str(row.get(k, "")) for k in fields})


def normalize_display(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'")
    value = re.sub(r"\s+", " ", value.strip())
    return value


def match_key(value: str) -> str:
    return normalize_display(value).casefold()


def note_num(note_id: str) -> int:
    m = re.fullmatch(r"KV(\d{6})", note_id)
    if not m:
        raise ValueError(f"Invalid NoteID: {note_id}")
    return int(m.group(1))


def origin_key(word: str) -> str:
    return f"{SOURCE_ID}|{match_key(word)}"


def parse_book(book: str) -> tuple[int | None, str]:
    m = re.fullmatch(r"(\d+)年级([上下])", book.strip())
    if not m:
        return None, ""
    return int(m.group(1)), m.group(2)


def load_config() -> dict[str, object]:
    with CONFIG.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_or_bootstrap_registry(source_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], bool]:
    created = False
    if REGISTRY.exists():
        registry = read_csv(REGISTRY)
    else:
        created = True
        registry = []
        for idx, row in enumerate(source_rows, start=1):
            word = normalize_display(row["Word"])
            registry.append({
                "NoteID": f"KV{idx:06d}",
                "CanonicalWord": word,
                "MatchKey": match_key(word),
                "SenseLabel": row["MeaningPrimary"].strip(),
                "PrimaryOriginKey": origin_key(word),
                "CreatedSource": SOURCE_ID,
                "CreatedSourceBook": row["FirstBook"].strip(),
                "Status": "active",
            })

    # Registry is append-only. Current source rows must map to an existing origin,
    # or receive a new ID appended after the current maximum.
    seen_ids: set[str] = set()
    seen_origins: set[str] = set()
    for row in registry:
        nid = row["NoteID"].strip()
        org = row["PrimaryOriginKey"].strip()
        if nid in seen_ids:
            raise SystemExit(f"Duplicate NoteID in registry: {nid}")
        if org in seen_origins:
            raise SystemExit(f"Duplicate PrimaryOriginKey in registry: {org}")
        note_num(nid)
        seen_ids.add(nid)
        seen_origins.add(org)

    by_origin = {r["PrimaryOriginKey"]: r for r in registry}
    next_id = max((note_num(r["NoteID"]) for r in registry), default=0) + 1
    changed = created
    for row in source_rows:
        word = normalize_display(row["Word"])
        org = origin_key(word)
        if org in by_origin:
            continue
        new = {
            "NoteID": f"KV{next_id:06d}",
            "CanonicalWord": word,
            "MatchKey": match_key(word),
            "SenseLabel": row["MeaningPrimary"].strip(),
            "PrimaryOriginKey": org,
            "CreatedSource": SOURCE_ID,
            "CreatedSourceBook": row["FirstBook"].strip(),
            "Status": "active",
        }
        registry.append(new)
        by_origin[org] = new
        next_id += 1
        changed = True

    registry.sort(key=lambda r: note_num(r["NoteID"]))
    if changed:
        write_csv(REGISTRY, REGISTRY_FIELDS, registry)
    return registry, changed


def source_grade_membership(source_rows: list[dict[str, str]]) -> dict[str, set[int]]:
    result: dict[str, set[int]] = {}
    for row in source_rows:
        grades: set[int] = set()
        for book in row["Books"].split("|"):
            grade, _ = parse_book(book)
            if grade is not None:
                grades.add(grade)
        result[origin_key(row["Word"])] = grades
    return result


def load_or_extend_releases(
    config: dict[str, object],
    registry: list[dict[str, str]],
    source_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], bool]:
    releases = read_csv(RELEASE_REGISTRY) if RELEASE_REGISTRY.exists() else []
    released = {r["NoteID"] for r in releases}

    scopes = config.get("released_scopes", [])
    allowed_grades: set[int] = set()
    for scope in scopes if isinstance(scopes, list) else []:
        if not isinstance(scope, dict) or scope.get("source_id") != SOURCE_ID:
            continue
        grades = scope.get("grades", [])
        if isinstance(grades, list):
            allowed_grades.update(int(x) for x in grades)

    grade_membership = source_grade_membership(source_rows)
    by_origin = {r["PrimaryOriginKey"]: r for r in registry}
    release_date = str(config.get("initial_release_date", ""))
    reason = f"scope:{SOURCE_ID}:grades={','.join(str(x) for x in sorted(allowed_grades))}"
    changed = not RELEASE_REGISTRY.exists()

    for org, grades in grade_membership.items():
        if not (grades & allowed_grades):
            continue
        nid = by_origin[org]["NoteID"]
        if nid in released:
            continue
        releases.append({"NoteID": nid, "ReleasedAt": release_date, "ReleaseReason": reason})
        released.add(nid)
        changed = True

    releases.sort(key=lambda r: note_num(r["NoteID"]))
    if changed:
        write_csv(RELEASE_REGISTRY, RELEASE_FIELDS, releases)
    return releases, changed


def trivial_grade4_reason(example: str, first_grade: int) -> str:
    """Heuristic review only; never treats simple = automatically wrong."""
    if first_grade >= 4:
        return ""
    text = normalize_display(example)
    words = re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*", text)
    if len(words) > 5:
        return ""
    patterns = [
        r"^(This|That|It) is (a |an |the |my |your )?.+\.$",
        r"^I (like|have|can) .+\.$",
        r"^Today is .+\.$",
        r"^It is .+ today\.$",
    ]
    return "grade4-upgrade-candidate" if any(re.match(p, text, re.I) for p in patterns) else ""


def main() -> None:
    for required in (CONFIG, SOURCE_MASTER, SOURCE_OCCURRENCES):
        if not required.exists():
            raise SystemExit(f"Missing input: {required.relative_to(ROOT)}")

    config = load_config()
    source_rows = read_csv(SOURCE_MASTER)
    source_occ = read_csv(SOURCE_OCCURRENCES)
    if not source_rows:
        raise SystemExit("Source master is empty")

    # Current source-specific master must be unique by current origin key.
    source_by_origin: dict[str, dict[str, str]] = {}
    for row in source_rows:
        org = origin_key(row["Word"])
        if org in source_by_origin:
            raise SystemExit(f"Duplicate source master origin: {org}")
        source_by_origin[org] = row

    registry, registry_changed = load_or_bootstrap_registry(source_rows)
    registry_by_origin = {r["PrimaryOriginKey"]: r for r in registry}
    releases, releases_changed = load_or_extend_releases(config, registry, source_rows)
    released_ids = {r["NoteID"] for r in releases}

    # Identity review: case/display collisions in raw occurrences after match-key folding.
    variants: dict[str, set[str]] = defaultdict(set)
    for row in source_occ:
        variants[match_key(row["Word"])].add(normalize_display(row["Word"]))
    identity_review_rows: list[dict[str, object]] = []
    for key, names in sorted(variants.items()):
        if len(names) > 1:
            identity_review_rows.append({
                "MatchKey": key,
                "Variants": "|".join(sorted(names)),
                "Reason": "case-or-display-collision",
                "Status": "needs-review",
            })

    master_rows: list[dict[str, object]] = []
    learner_rows: list[dict[str, object]] = []
    learner_review_rows: list[dict[str, object]] = []

    for src in source_rows:
        org = origin_key(src["Word"])
        reg = registry_by_origin[org]
        nid = reg["NoteID"]
        books = [b for b in src["Books"].split("|") if b]
        source_books = [f"{SOURCE_ID}::{b}" for b in books]
        first_grade = int(src["Grade"]) if src["Grade"].isdigit() else 0
        source_tags = {f"source::{SOURCE_ID}"}
        for book in books:
            grade, semester = parse_book(book)
            if grade is None:
                continue
            source_tags.add(f"source::{SOURCE_ID}::grade::{grade}")
            source_tags.add(f"source::{SOURCE_ID}::grade::{grade}::{semester}")

        released = nid in released_ids
        if released:
            source_tags.add("learner::klose::released")
        source_tags.add(f"learner::klose::level::{int(config['learner_level'])}")

        master_rows.append({
            "NoteID": nid,
            "CanonicalWord": reg["CanonicalWord"],
            "MatchKey": reg["MatchKey"],
            "SenseLabel": reg["SenseLabel"],
            "Word": src["Word"],
            "British": src["British"],
            "American": src["American"],
            "MeaningPrimary": src["MeaningPrimary"],
            "MeaningRaw": src["MeaningRaw"],
            "FirstSource": SOURCE_ID,
            "FirstSourceBook": src["FirstBook"],
            "FirstGrade": src["Grade"],
            "FirstSemester": src["Semester"],
            "Sources": SOURCE_ID,
            "SourceBooks": "|".join(source_books),
            "Released": "yes" if released else "no",
            "Tags": " ".join(sorted(source_tags)),
        })

        status = "migrated-curated"
        reason = trivial_grade4_reason(src["ExampleSentence"], first_grade)
        if released and reason:
            status = "review-suggested"
            learner_review_rows.append({
                "NoteID": nid,
                "Word": src["Word"],
                "FirstGrade": src["Grade"],
                "ExampleSentence": src["ExampleSentence"],
                "Reason": reason,
            })

        learner_rows.append({
            "NoteID": nid,
            "LearnerProfile": str(config["learner_profile"]),
            "LearnerLevel": str(config["learner_level"]),
            "ExampleSentence": src["ExampleSentence"],
            "ExampleTranslation": src["ExampleTranslation"],
            "PresentationStatus": status,
            "PresentationSource": f"{SOURCE_ID}:curation",
        })

    master_rows.sort(key=lambda r: note_num(str(r["NoteID"])))
    learner_rows.sort(key=lambda r: note_num(str(r["NoteID"])))
    learner_by_id = {str(r["NoteID"]): r for r in learner_rows}

    # Full source occurrence audit, now attached to stable NoteID.
    occurrence_rows: list[dict[str, object]] = []
    for occ in source_occ:
        org = origin_key(occ["Word"])
        if org not in registry_by_origin:
            raise SystemExit(f"Occurrence without registry identity: {occ['Word']}")
        nid = registry_by_origin[org]["NoteID"]
        occurrence_rows.append({
            "NoteID": nid,
            "SourceID": SOURCE_ID,
            "SourceBook": occ["Book"],
            "Grade": occ["Grade"],
            "Semester": occ["Semester"],
            "Unit": "",
            "SourceWord": occ["Word"],
            "SourceFile": occ["SourceFile"],
            "SourceRow": occ["SourceRow"],
        })
    occurrence_rows.sort(key=lambda r: (note_num(str(r["NoteID"])), str(r["SourceBook"]), int(str(r["SourceRow"]))))

    master_fields = [
        "NoteID", "CanonicalWord", "MatchKey", "SenseLabel", "Word", "British", "American",
        "MeaningPrimary", "MeaningRaw", "FirstSource", "FirstSourceBook", "FirstGrade",
        "FirstSemester", "Sources", "SourceBooks", "Released", "Tags",
    ]
    learner_fields = [
        "NoteID", "LearnerProfile", "LearnerLevel", "ExampleSentence", "ExampleTranslation",
        "PresentationStatus", "PresentationSource",
    ]
    occurrence_fields = [
        "NoteID", "SourceID", "SourceBook", "Grade", "Semester", "Unit", "SourceWord",
        "SourceFile", "SourceRow",
    ]
    write_csv(GLOBAL_MASTER, master_fields, master_rows)
    write_csv(LEARNER_CURRENT, learner_fields, learner_rows)
    write_csv(GLOBAL_OCCURRENCES, occurrence_fields, occurrence_rows)
    write_csv(IDENTITY_REVIEW, ["MatchKey", "Variants", "Reason", "Status"], identity_review_rows)
    write_csv(LEARNER_REVIEW, ["NoteID", "Word", "FirstGrade", "ExampleSentence", "Reason"], learner_review_rows)

    publish_fields = [
        "NoteID", "CanonicalWord", "Word", "British", "American", "MeaningPrimary",
        "ExampleSentence", "ExampleTranslation", "LearnerLevel", "Sources", "SourceBooks", "Tags",
    ]
    publish_rows: list[dict[str, object]] = []
    for row in master_rows:
        learner = learner_by_id[str(row["NoteID"])]
        publish_rows.append({**row, **learner})
    write_csv(PUBLISH_DIR / "all.csv", publish_fields, publish_rows)
    study_rows = [r for r in publish_rows if str(r["NoteID"]) in released_ids]
    write_csv(PUBLISH_DIR / "study.csv", publish_fields, study_rows)

    # One-time migration files keep Word as field #1 to match the legacy Note Type.
    migration_fields = ["Word"] + [x for x in publish_fields if x != "Word"]
    write_csv(PUBLISH_DIR / "migration" / "word-first-all.csv", migration_fields, publish_rows)
    write_csv(PUBLISH_DIR / "migration" / "word-first-study.csv", migration_fields, study_rows)

    # Per-source grade views merge upper/lower semesters and include every Note
    # that appears in that grade. They are views only, not independent truth.
    occurrence_grades: dict[str, set[int]] = defaultdict(set)
    for occ in occurrence_rows:
        if str(occ["Grade"]).isdigit():
            occurrence_grades[str(occ["NoteID"])].add(int(str(occ["Grade"])))
    for grade in range(1, 7):
        rows = [r for r in publish_rows if grade in occurrence_grades[str(r["NoteID"])]]
        write_csv(PUBLISH_DIR / "by-source" / SOURCE_ID / f"grade{grade}.csv", publish_fields, rows)

    # Hard invariants.
    all_ids = [str(r["NoteID"]) for r in publish_rows]
    if len(all_ids) != len(set(all_ids)):
        raise SystemExit("Duplicate NoteID in all.csv")
    study_ids = {str(r["NoteID"]) for r in study_rows}
    if not study_ids.issubset(set(all_ids)):
        raise SystemExit("study.csv is not a subset of all.csv")
    if len(master_rows) != len(learner_rows):
        raise SystemExit("Learner coverage mismatch")

    stats = [
        {"Metric": "source_id", "Value": SOURCE_ID},
        {"Metric": "source_occurrences", "Value": len(occurrence_rows)},
        {"Metric": "master_notes", "Value": len(master_rows)},
        {"Metric": "released_notes", "Value": len(study_rows)},
        {"Metric": "inventory_notes", "Value": len(publish_rows)},
        {"Metric": "identity_review_items", "Value": len(identity_review_rows)},
        {"Metric": "learner_review_suggestions", "Value": len(learner_review_rows)},
        {"Metric": "registry_rows", "Value": len(registry)},
        {"Metric": "registry_changed", "Value": str(registry_changed).lower()},
        {"Metric": "release_registry_changed", "Value": str(releases_changed).lower()},
    ]
    for grade in range(1, 7):
        count = sum(1 for r in publish_rows if grade in occurrence_grades[str(r["NoteID"])])
        stats.append({"Metric": f"{SOURCE_ID}_grade{grade}_view", "Value": count})
    write_csv(BUILD_STATS, ["Metric", "Value"], stats)

    print(f"Klose Vocabulary: inventory={len(publish_rows)}, released={len(study_rows)}")
    print(f"Registry={len(registry)}; identity review={len(identity_review_rows)}; learner suggestions={len(learner_review_rows)}")


if __name__ == "__main__":
    main()
