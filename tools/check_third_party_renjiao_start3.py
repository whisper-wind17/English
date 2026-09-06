#!/usr/bin/env python3
"""Validate the narrow Renjiao start-from-grade-3 source-adapter contract."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "anki" / "klose" / "source_reference" / "renjiao_start3_staging" / "occurrences.csv"
EXPECTED_FIELDS = [
    "SourceOccurrenceKey", "SourceID", "SourceBook", "Grade", "Semester",
    "SourceRow", "Word", "MatchKey", "British", "American", "Definition", "SourceFile",
]
SOURCE_FILE_RE = re.compile(r"人教版三年级起点[三四五六]年级[上下]\.xlsx$")


def main() -> None:
    if not PATH.exists():
        raise SystemExit(f"Missing source-adapter output: {PATH}")
    with PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != EXPECTED_FIELDS:
            raise SystemExit(f"Unexpected occurrence schema: {reader.fieldnames}")
        rows = list(reader)

    if not rows:
        raise SystemExit("Renjiao start3 adapter produced no source occurrences")
    if any(r.get("SourceID") != "renjiao_start3" for r in rows):
        raise SystemExit("SourceID drift in Renjiao start3 adapter")

    occ_keys = [r.get("SourceOccurrenceKey", "") for r in rows]
    if not all(occ_keys) or len(occ_keys) != len(set(occ_keys)):
        raise SystemExit("SourceOccurrenceKey must be non-empty and unique")
    if any(not r.get("Word") or not r.get("MatchKey") for r in rows):
        raise SystemExit("Word / MatchKey must be non-empty")
    if any(not SOURCE_FILE_RE.fullmatch(r.get("SourceFile", "")) for r in rows):
        raise SystemExit("Unexpected source file leaked into Renjiao start3 adapter")

    books = {(r.get("Grade", ""), r.get("Semester", "")) for r in rows}
    expected_books = {(str(g), s) for g in range(3, 7) for s in ("上", "下")}
    if books != expected_books:
        raise SystemExit(f"Expected 8 grade/semester books, got {sorted(books)}")

    distinct = len({r["MatchKey"] for r in rows})
    if distinct <= 0 or distinct > len(rows):
        raise SystemExit(f"Invalid normalized MatchKey count: {distinct}")

    forbidden = {"CandidateNoteIDs", "ProposedNoteID", "StageAClass", "existing-in-klose", "third-party-new"}
    if forbidden & set(EXPECTED_FIELDS):
        raise SystemExit("Source Adapter schema leaked matching/identity/final-diff state")

    print("Renjiao Start3 Source Adapter Recheck = pass")
    print(f"source occurrences = {len(rows)}")
    print(f"distinct MatchKeys = {distinct}")
    print("source books = 8")
    print("identity/matching state in adapter = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
