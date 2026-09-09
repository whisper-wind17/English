#!/usr/bin/env python3
"""Validate the narrow Kepu start-from-grade-3 primary source-adapter contract."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "anki" / "klose" / "source_reference" / "kepu_start3_staging" / "occurrences.csv"
EXPECTED_FIELDS = [
    "SourceOccurrenceKey", "SourceID", "SourceBook", "Grade", "Semester",
    "SourceRow", "Word", "MatchKey", "British", "American", "Definition", "SourceFile",
]
SOURCE_FILE_RE = re.compile(r"科普版三年级起点([三四五六])年级([上下])(?:册)?\.xlsx$")
GRADE_CN = {"三": "3", "四": "4", "五": "5", "六": "6"}
SEM_EN = {"上": "upper", "下": "lower"}
EXPECTED_OCCURRENCES = 772
EXPECTED_MATCHKEYS = 771
EXPECTED_BLANK_DEFINITIONS = 0


def main() -> None:
    if not PATH.exists():
        raise SystemExit(f"Missing source-adapter output: {PATH}")
    with PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != EXPECTED_FIELDS:
            raise SystemExit(f"Unexpected occurrence schema: {reader.fieldnames}")
        rows = list(reader)

    if len(rows) != EXPECTED_OCCURRENCES:
        raise SystemExit(f"Expected {EXPECTED_OCCURRENCES} Kepu start3 occurrences, found {len(rows)}")
    if any(row.get("SourceID") != "kepu_start3" for row in rows):
        raise SystemExit("SourceID drift in Kepu start3 adapter")

    occ_keys = [row.get("SourceOccurrenceKey", "") for row in rows]
    if not all(occ_keys) or len(occ_keys) != len(set(occ_keys)):
        raise SystemExit("SourceOccurrenceKey must be non-empty and unique")
    if any(not row.get("Word") or not row.get("MatchKey") for row in rows):
        raise SystemExit("Word / MatchKey must be non-empty")

    blank_defs = [row for row in rows if not row.get("Definition", "").strip()]
    if len(blank_defs) != EXPECTED_BLANK_DEFINITIONS:
        raise SystemExit(
            f"Expected {EXPECTED_BLANK_DEFINITIONS} source blank Definition, found {len(blank_defs)}"
        )

    seen_books: set[tuple[str, str]] = set()
    for row in rows:
        m = SOURCE_FILE_RE.fullmatch(row.get("SourceFile", ""))
        if not m:
            raise SystemExit(f"Unexpected source file leaked into Kepu start3 adapter: {row.get('SourceFile', '')}")
        grade = GRADE_CN[m.group(1)]
        semester = m.group(2)
        if row.get("Grade") != grade or row.get("Semester") != semester:
            raise SystemExit(
                f"Grade/Semester drift for {row.get('SourceFile')}: "
                f"row={row.get('Grade')}/{row.get('Semester')} expected={grade}/{semester}"
            )
        if row.get("SourceBook") != f"{grade}年级{semester}":
            raise SystemExit(f"SourceBook drift for {row.get('SourceFile')}: {row.get('SourceBook')}")
        try:
            row_no = int(row.get("SourceRow", ""))
        except ValueError as exc:
            raise SystemExit(f"Invalid SourceRow: {row.get('SourceRow')}") from exc
        if row_no <= 0:
            raise SystemExit(f"Invalid non-positive SourceRow: {row_no}")
        expected_prefix = f"kepu_start3|g{grade}-{SEM_EN[semester]}|r{row_no:03d}|"
        if not row.get("SourceOccurrenceKey", "").startswith(expected_prefix):
            raise SystemExit(
                f"SourceOccurrenceKey metadata drift: {row.get('SourceOccurrenceKey')} expected prefix {expected_prefix}"
            )
        seen_books.add((grade, semester))

    expected_books = {(str(g), s) for g in range(3, 7) for s in ("上", "下")}
    if seen_books != expected_books:
        raise SystemExit(f"Expected 8 grade/semester books, got {sorted(seen_books)}")

    distinct = len({row["MatchKey"] for row in rows})
    if distinct != EXPECTED_MATCHKEYS:
        raise SystemExit(f"Expected {EXPECTED_MATCHKEYS} normalized MatchKeys, found {distinct}")

    print("Kepu Start3 Source Adapter Recheck = pass")
    print(f"source occurrences = {len(rows)}")
    print(f"distinct MatchKeys = {distinct}")
    print("source books = 8")
    print(f"blank definitions = {len(blank_defs)}")
    print("exact source baseline frozen = yes")
    print("filename/grade/semester/book/key mapping = enforced")
    print("identity/matching state in adapter = no")
    print("Stable ThirdPartyID minted = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
