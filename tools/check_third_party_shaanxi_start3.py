#!/usr/bin/env python3
"""Validate the narrow Shaanxi grade-3-start primary source-adapter contract."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "anki" / "klose" / "source_reference" / "shaanxi_start3_staging" / "occurrences.csv"
EXPECTED_FIELDS = [
    "SourceOccurrenceKey", "SourceID", "SourceBook", "Grade", "Semester",
    "SourceRow", "Word", "MatchKey", "British", "American", "Definition", "SourceFile",
]
SOURCE_FILE_RE = re.compile(r"陕西版三年级起点([三四五六])年级([上下])\.xlsx$")
GRADE_CN = {"三": "3", "四": "4", "五": "5", "六": "6"}
SEM_EN = {"上": "upper", "下": "lower"}
EXPECTED_OCCURRENCES = 917
EXPECTED_MATCHKEYS = 880
EXPECTED_BLANK_DEFINITIONS = 1


def main() -> None:
    if not PATH.exists():
        raise SystemExit(f"Missing source-adapter output: {PATH}")
    with PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != EXPECTED_FIELDS:
            raise SystemExit(f"Unexpected occurrence schema: {reader.fieldnames}")
        rows = list(reader)

    if len(rows) != EXPECTED_OCCURRENCES:
        raise SystemExit(f"Expected {EXPECTED_OCCURRENCES} Shaanxi occurrences, found {len(rows)}")
    if any(r.get("SourceID") != "shaanxi_start3" for r in rows):
        raise SystemExit("SourceID drift in Shaanxi start3 adapter")

    occurrence_keys = [r.get("SourceOccurrenceKey", "") for r in rows]
    if not all(occurrence_keys) or len(occurrence_keys) != len(set(occurrence_keys)):
        raise SystemExit("SourceOccurrenceKey must be non-empty and unique")
    if any(not r.get("Word") or not r.get("MatchKey") for r in rows):
        raise SystemExit("Word / MatchKey must be non-empty")
    if any(r.get("British", "") or r.get("American", "") for r in rows):
        raise SystemExit("Shaanxi raw source has no pronunciation columns; British/American must remain empty")

    blank_defs = [r for r in rows if not r.get("Definition", "").strip()]
    if len(blank_defs) != EXPECTED_BLANK_DEFINITIONS:
        raise SystemExit(
            f"Expected {EXPECTED_BLANK_DEFINITIONS} source blank Definition, found {len(blank_defs)}"
        )

    seen_books: set[tuple[str, str]] = set()
    for r in rows:
        m = SOURCE_FILE_RE.fullmatch(r.get("SourceFile", ""))
        if not m:
            raise SystemExit(f"Unexpected Shaanxi source file: {r.get('SourceFile', '')}")
        grade, semester = GRADE_CN[m.group(1)], m.group(2)
        if r.get("Grade") != grade or r.get("Semester") != semester:
            raise SystemExit(f"Grade/Semester drift for {r.get('SourceFile')}")
        if r.get("SourceBook") != f"{grade}年级{semester}":
            raise SystemExit(f"SourceBook drift for {r.get('SourceFile')}: {r.get('SourceBook')}")
        try:
            row_no = int(r.get("SourceRow", ""))
        except ValueError as exc:
            raise SystemExit(f"Invalid SourceRow: {r.get('SourceRow')}") from exc
        if row_no <= 0:
            raise SystemExit(f"Invalid non-positive SourceRow: {row_no}")
        prefix = f"shaanxi_start3|g{grade}-{SEM_EN[semester]}|r{row_no:03d}|"
        if not r.get("SourceOccurrenceKey", "").startswith(prefix):
            raise SystemExit(f"SourceOccurrenceKey metadata drift: {r.get('SourceOccurrenceKey')}")
        seen_books.add((grade, semester))

    expected_books = {(str(g), s) for g in range(3, 7) for s in ("上", "下")}
    if seen_books != expected_books:
        raise SystemExit(f"Expected 8 Shaanxi books, got {sorted(seen_books)}")

    distinct = len({r["MatchKey"] for r in rows})
    if distinct != EXPECTED_MATCHKEYS:
        raise SystemExit(f"Expected {EXPECTED_MATCHKEYS} MatchKeys, found {distinct}")

    print("Shaanxi Start3 Source Adapter Recheck = pass")
    print(f"source occurrences = {len(rows)}")
    print(f"distinct MatchKeys = {distinct}")
    print("source books = 8")
    print(f"blank definitions = {len(blank_defs)}")
    print("source schema = headerless A=Word / B=Definition; pronunciation columns absent")
    print("exact source baseline frozen = yes")
    print("filename/grade/semester/book/key mapping = enforced")
    print("identity/matching state in adapter = no")
    print("Stable ThirdPartyID minted = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
