#!/usr/bin/env python3
"""Validate the authoritative Klose Grade-4 textbook -> stable NoteID mapping."""
from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
ACTUAL = BASE / "source_reference" / "rj_start1-grade4-klose-actual.csv"
LEGACY_REGISTRY = BASE / "master" / "note_registry.csv"
REGISTRY_EXTENSIONS = BASE / "master" / "note_registry_extensions.csv"
SOURCE_IDENTITY_EXTENSIONS = BASE / "master" / "source_identity_extensions.csv"
SOURCE_ID = "rj_start1"
SOURCE_EDITION = "klose-current"
VALID_DECISIONS = {
    "reuse-existing",
    "reuse-existing-noun",
    "reuse-morphology",
    "new-learning-unit",
    "new-distinct-sense",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'")
    value = re.sub(r"\s+", " ", value.strip())
    return value.casefold()


def source_item_key(row: dict[str, str]) -> str:
    semester = {"上": "upper", "下": "lower"}.get(row.get("Semester", "").strip())
    if semester is None:
        raise SystemExit(f"Invalid Grade-4 semester: {row}")
    try:
        unit = int(row["Unit"])
        order = int(row["Order"])
    except ValueError as exc:
        raise SystemExit(f"Invalid Unit/Order in actual Grade-4 source: {row}") from exc
    return f"grade4-{semester}-u{unit:02d}-o{order:03d}|{normalize(row['Entry'])}"


def main() -> None:
    for path in (ACTUAL, LEGACY_REGISTRY, REGISTRY_EXTENSIONS, SOURCE_IDENTITY_EXTENSIONS):
        if not path.exists():
            raise SystemExit(f"Missing Grade-4 identity input: {path.relative_to(ROOT)}")

    actual = read_csv(ACTUAL)
    registry = read_csv(LEGACY_REGISTRY) + read_csv(REGISTRY_EXTENSIONS)
    mappings = [
        r for r in read_csv(SOURCE_IDENTITY_EXTENSIONS)
        if r.get("SourceID", "").strip() == SOURCE_ID
        and r.get("SourceEdition", "").strip() == SOURCE_EDITION
        and r.get("SourceItemKey", "").strip().startswith("grade4-")
    ]

    registry_ids = {r["NoteID"].strip() for r in registry}
    expected: dict[str, dict[str, str]] = {}
    for row in actual:
        if row.get("SourceID", "").strip() != SOURCE_ID:
            raise SystemExit(f"Unexpected SourceID in actual Grade-4 source: {row}")
        if row.get("SourceEdition", "").strip() != SOURCE_EDITION:
            raise SystemExit(f"Unexpected SourceEdition in actual Grade-4 source: {row}")
        if row.get("Grade", "").strip() != "4":
            raise SystemExit(f"Unexpected Grade in actual Grade-4 source: {row}")
        key = source_item_key(row)
        if key in expected:
            raise SystemExit(f"Duplicate actual Grade-4 source item key: {key}")
        expected[key] = row

    mapped: dict[str, dict[str, str]] = {}
    for row in mappings:
        key = row.get("SourceItemKey", "").strip()
        if key in mapped:
            raise SystemExit(f"Duplicate actual Grade-4 identity mapping: {key}")
        if row.get("Status", "").strip() != "confirmed":
            raise SystemExit(f"Unconfirmed actual Grade-4 identity mapping: {key}")
        if row.get("Decision", "").strip() not in VALID_DECISIONS:
            raise SystemExit(f"Invalid actual Grade-4 identity decision: {key} -> {row.get('Decision')!r}")
        nid = row.get("NoteID", "").strip()
        if nid not in registry_ids:
            raise SystemExit(f"Actual Grade-4 mapping references unknown NoteID: {key} -> {nid}")
        mapped[key] = row

    missing = sorted(set(expected) - set(mapped))
    extra = sorted(set(mapped) - set(expected))
    if missing or extra:
        raise SystemExit(
            "Actual Grade-4 identity coverage mismatch: "
            f"missing={missing[:10]} extra={extra[:10]}"
        )

    surface_notes: dict[str, set[str]] = defaultdict(set)
    surface_meanings: dict[str, set[str]] = defaultdict(set)
    for key, source in expected.items():
        surface = normalize(source["Entry"])
        surface_notes[surface].add(mapped[key]["NoteID"].strip())
        surface_meanings[surface].add(normalize(source["Meaning"]))
    bad_duplicate_identity = sorted(
        surface for surface, note_ids in surface_notes.items()
        if len(note_ids) > 1 and len(surface_meanings[surface]) == 1
    )
    if bad_duplicate_identity:
        raise SystemExit(
            "Same surface + same textbook meaning was split into multiple NoteIDs: "
            f"{bad_duplicate_identity[:10]}"
        )

    note_ids = [mapped[k]["NoteID"].strip() for k in expected]
    duplicate_note_use = len(note_ids) - len(set(note_ids))
    decisions = Counter(mapped[k]["Decision"].strip() for k in expected)
    multi_sense_surfaces = sorted(s for s, ids in surface_notes.items() if len(ids) > 1)

    print(
        "Actual Grade-4 identity OK: "
        f"occurrences={len(actual)}, unique_note_ids={len(set(note_ids))}, "
        f"shared_note_occurrences={duplicate_note_use}, decisions={dict(sorted(decisions.items()))}, "
        f"multi_sense_surfaces={multi_sense_surfaces}"
    )


if __name__ == "__main__":
    main()
