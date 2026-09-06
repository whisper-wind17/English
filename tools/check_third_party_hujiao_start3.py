#!/usr/bin/env python3
"""Validate the narrow Hujiao start-from-grade-3 primary source-adapter contract."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "anki" / "klose" / "source_reference" / "hujiao_start3_staging" / "occurrences.csv"
EXPECTED_FIELDS = [
    "SourceOccurrenceKey", "SourceID", "SourceBook", "Grade", "Semester",
    "SourceRow", "Word", "MatchKey", "British", "American", "Definition", "SourceFile",
]
SOURCE_FILE_RE = re.compile(r"沪教版三年级起点[三四五六]年级[上下]\.xlsx$")
EXPECTED_OCCURRENCES = 1111
EXPECTED_MATCHKEYS = 1067


def main() -> None:
    if not PATH.exists():
        raise SystemExit(f"Missing source-adapter output: {PATH}")
    with PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != EXPECTED_FIELDS:
            raise SystemExit(f"Unexpected occurrence schema: {reader.fieldnames}")
        rows = list(reader)

    if len(rows) != EXPECTED_OCCURRENCES:
        raise SystemExit(f"Expected {EXPECTED_OCCURRENCES} Hujiao start3 occurrences, found {len(rows)}")
    if any(r.get("SourceID") != "hujiao_start3" for r in rows):
        raise SystemExit("SourceID drift in Hujiao start3 adapter")

    occ_keys = [r.get("SourceOccurrenceKey", "") for r in rows]
    if not all(occ_keys) or len(occ_keys) != len(set(occ_keys)):
        raise SystemExit("SourceOccurrenceKey must be non-empty and unique")
    if any(not r.get("Word") or not r.get("MatchKey") for r in rows):
        raise SystemExit("Word / MatchKey must be non-empty")
    if any(not SOURCE_FILE_RE.fullmatch(r.get("SourceFile", "")) for r in rows):
        raise SystemExit("Unexpected source file leaked into Hujiao start3 primary adapter")

    books = {(r.get("Grade", ""), r.get("Semester", "")) for r in rows}
    expected_books = {(str(g), s) for g in range(3, 7) for s in ("上", "下")}
    if books != expected_books:
        raise SystemExit(f"Expected 8 grade/semester books, got {sorted(books)}")

    distinct = len({r["MatchKey"] for r in rows})
    if distinct != EXPECTED_MATCHKEYS:
        raise SystemExit(f"Expected {EXPECTED_MATCHKEYS} normalized MatchKeys, found {distinct}")

    forbidden = {"CandidateNoteIDs", "ProposedNoteID", "StageAClass", "existing-in-klose", "third-party-new"}
    if forbidden & set(EXPECTED_FIELDS):
        raise SystemExit("Source Adapter schema leaked matching/identity/final-diff state")

    print("Hujiao Start3 Source Adapter Recheck = pass")
    print(f"source occurrences = {len(rows)}")
    print(f"distinct MatchKeys = {distinct}")
    print("source books = 8")
    print("exact source baseline frozen = yes")
    print("identity/matching state in adapter = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
