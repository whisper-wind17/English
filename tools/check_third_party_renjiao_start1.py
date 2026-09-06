#!/usr/bin/env python3
"""Validate the narrow Renjiao source-adapter contract."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "anki" / "klose" / "source_reference" / "renjiao_start1_staging" / "occurrences.csv"
EXPECTED_FIELDS = [
    "SourceOccurrenceKey", "SourceID", "SourceBook", "Grade", "Semester",
    "SourceRow", "Word", "MatchKey", "British", "American", "Definition", "SourceFile",
]


def main() -> None:
    if not PATH.exists():
        raise SystemExit(f"Missing source-adapter output: {PATH}")
    with PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != EXPECTED_FIELDS:
            raise SystemExit(f"Unexpected occurrence schema: {reader.fieldnames}")
        rows = list(reader)

    if len(rows) != 908:
        raise SystemExit(f"Expected 908 Renjiao occurrences, found {len(rows)}")
    if any(r.get("SourceID") != "renjiao_start1" for r in rows):
        raise SystemExit("SourceID drift in Renjiao adapter")

    occ_keys = [r.get("SourceOccurrenceKey", "") for r in rows]
    if not all(occ_keys) or len(occ_keys) != len(set(occ_keys)):
        raise SystemExit("SourceOccurrenceKey must be non-empty and unique")
    if any(not r.get("Word") or not r.get("MatchKey") for r in rows):
        raise SystemExit("Word / MatchKey must be non-empty")

    books = {(r.get("Grade", ""), r.get("Semester", "")) for r in rows}
    expected_books = {(str(g), s) for g in range(1, 7) for s in ("上", "下")}
    if books != expected_books:
        raise SystemExit(f"Expected 12 grade/semester books, got {sorted(books)}")

    distinct = len({r["MatchKey"] for r in rows})
    if distinct != 802:
        raise SystemExit(f"Expected 802 normalized MatchKeys, found {distinct}")

    forbidden = {"CandidateNoteIDs", "ProposedNoteID", "StageAClass", "existing-in-klose", "third-party-new"}
    if forbidden & set(EXPECTED_FIELDS):
        raise SystemExit("Source Adapter schema leaked matching/identity/final-diff state")

    print("Renjiao Source Adapter Recheck = pass")
    print(f"source occurrences = {len(rows)}")
    print(f"distinct MatchKeys = {distinct}")
    print("source books = 12")
    print("identity/matching state in adapter = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
