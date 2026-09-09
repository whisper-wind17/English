#!/usr/bin/env python3
"""Parse JOIN Cambridge primary grade-3-start vocabulary into standardized occurrences."""
from __future__ import annotations

import csv
import re
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "1.全国各大教材版本中小学同步" / "剑桥版"
OUT = ROOT / "anki" / "klose" / "source_reference" / "cambridge_join_start3_staging"
EXPECTED_BOOKS = [(g, s) for g in range(3, 7) for s in ("上", "下")]
GRADE_CN = {"三": 3, "四": 4, "五": 5, "六": 6}
BOOK_RE = re.compile(r"JOIN版剑桥小学英语([三四五六])年级([上下])册\.xlsx$")
OCC_FIELDS = [
    "SourceOccurrenceKey", "SourceID", "SourceBook", "Grade", "Semester",
    "SourceRow", "Word", "MatchKey", "British", "American", "Definition", "SourceFile",
]


def norm_display(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", value.strip())


def match_key(value: str) -> str:
    return norm_display(value).casefold()


def shared_strings(zf: zipfile.ZipFile) -> list[str]:
    name = "xl/sharedStrings.xml"
    if name not in zf.namelist():
        return []
    root = ET.fromstring(zf.read(name))
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    return ["".join(t.text or "" for t in si.iter(f"{ns}t")) for si in root.findall(f"{ns}si")]


def cell_value(cell: ET.Element, strings: list[str]) -> str:
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    typ = cell.attrib.get("t", "")
    if typ == "inlineStr":
        node = cell.find(f"{ns}is")
        return "" if node is None else "".join(t.text or "" for t in node.iter(f"{ns}t"))
    node = cell.find(f"{ns}v")
    raw = "" if node is None else (node.text or "")
    return strings[int(raw)] if typ == "s" and raw else raw


def col_index(ref: str) -> int:
    letters = "".join(ch for ch in ref if ch.isalpha())
    n = 0
    for ch in letters.upper():
        n = n * 26 + ord(ch) - ord("A") + 1
    return n - 1


def read_xlsx_rows(path: Path) -> list[tuple[int, list[str]]]:
    with zipfile.ZipFile(path) as zf:
        strings = shared_strings(zf)
        sheet = "xl/worksheets/sheet1.xml"
        if sheet not in zf.namelist():
            raise SystemExit(f"Missing {sheet}: {path}")
        root = ET.fromstring(zf.read(sheet))
        ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        result: list[tuple[int, list[str]]] = []
        for row in root.iter(f"{ns}row"):
            row_no = int(row.attrib.get("r", "0") or 0)
            vals: dict[int, str] = {}
            for cell in row.findall(f"{ns}c"):
                vals[col_index(cell.attrib.get("r", "A1"))] = norm_display(cell_value(cell, strings))
            if vals:
                result.append((row_no, [vals.get(i, "") for i in range(max(vals) + 1)]))
        return result


def parse_source(path: Path, grade: int, semester: str) -> list[dict[str, str]]:
    rows = read_xlsx_rows(path)
    header_pos = next((i for i, (_, vals) in enumerate(rows[:10]) if "单词" in vals and "释义" in vals), None)
    if header_pos is None:
        raise SystemExit(f"Cannot find vocabulary header containing 单词/释义 in {path.name}")
    header = rows[header_pos][1]
    word_idx = header.index("单词")
    definition_idx = header.index("释义")
    british_idx = header.index("英音") if "英音" in header else None
    american_idx = header.index("美音") if "美音" in header else None
    sem_en = "upper" if semester == "上" else "lower"
    out: list[dict[str, str]] = []
    for row_no, vals in rows[header_pos + 1:]:
        def get(idx: int | None) -> str:
            return vals[idx] if idx is not None and idx < len(vals) else ""
        word = get(word_idx)
        if not word or word == "单词":
            continue
        key = match_key(word)
        out.append({
            "SourceOccurrenceKey": f"cambridge_join_start3|g{grade}-{sem_en}|r{row_no:03d}|{key}",
            "SourceID": "cambridge_join_start3", "SourceBook": f"{grade}年级{semester}",
            "Grade": str(grade), "Semester": semester, "SourceRow": str(row_no),
            "Word": word, "MatchKey": key, "British": get(british_idx),
            "American": get(american_idx), "Definition": get(definition_idx), "SourceFile": path.name,
        })
    if not out:
        raise SystemExit(f"No vocabulary occurrences parsed from {path.name}")
    return out


def main() -> None:
    source_files: dict[tuple[int, str], Path] = {}
    for path in SOURCE_DIR.glob("JOIN版剑桥小学英语*.xlsx"):
        m = BOOK_RE.fullmatch(path.name)
        if m:
            key = (GRADE_CN[m.group(1)], m.group(2))
            if key in source_files:
                raise SystemExit(f"Duplicate Cambridge JOIN source book: {key}")
            source_files[key] = path
    missing = [f"{g}年级{s}" for g, s in EXPECTED_BOOKS if (g, s) not in source_files]
    if missing or len(source_files) != 8:
        raise SystemExit(f"Cambridge JOIN source-book set invalid; missing={missing}; found={len(source_files)}")
    occurrences: list[dict[str, str]] = []
    for grade, semester in EXPECTED_BOOKS:
        occurrences.extend(parse_source(source_files[(grade, semester)], grade, semester))
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "occurrences.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OCC_FIELDS)
        writer.writeheader(); writer.writerows(occurrences)
    distinct = len({r["MatchKey"] for r in occurrences})
    blank_defs = sum(not r["Definition"].strip() for r in occurrences)
    (OUT / "README.md").write_text(
        f"# Cambridge JOIN Start3 — Third-party Source Adapter\n\n"
        f"Scope: JOIN版剑桥小学英语 3-6 年级上下册，共 8 册。\n\n"
        f"Source occurrences = {len(occurrences)}\n\nDistinct MatchKeys = {distinct}\n\n"
        f"Blank definitions = {blank_defs}\n\nSource facts only; no Identity or Klose mutation.\n",
        encoding="utf-8",
    )
    print("Cambridge JOIN start3 source adapter = parsed")
    print("source books = 8")
    print(f"source occurrences = {len(occurrences)}")
    print(f"distinct MatchKeys = {distinct}")
    print(f"blank definitions = {blank_defs}")
    print("cross-source identity logic executed here = no")
    print("Stable ThirdPartyID minted = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
