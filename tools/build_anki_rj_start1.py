#!/usr/bin/env python3
"""Build Anki-ready CSV files from 人教版一年级起点 XLSX sources.

Uses only Python standard library to parse the first worksheet of each XLSX.
The source XLSX files remain untouched.
"""

from __future__ import annotations

import csv
import re
import shutil
import zipfile
from collections import OrderedDict
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "1.全国各大教材版本中小学同步" / "人教版"
OUT_DIR = ROOT / "anki" / "人教版一年级起点"
MASTER_DIR = OUT_DIR / "master"
IMPORT_DIR = OUT_DIR / "import"

BOOKS = [
    ("人教版一年级起点一年级上.xlsx", 1, "上"),
    ("人教版一年级起点一年级下.xlsx", 1, "下"),
    ("人教版一年级起点二年级上.xlsx", 2, "上"),
    ("人教版一年级起点二年级下.xlsx", 2, "下"),
    ("人教版一年级起点三年级上.xlsx", 3, "上"),
    ("人教版一年级起点三年级下.xlsx", 3, "下"),
    ("人教版一年级起点四年级上.xlsx", 4, "上"),
    ("人教版一年级起点四年级下.xlsx", 4, "下"),
    ("人教版一年级起点五年级上.xlsx", 5, "上"),
    ("人教版一年级起点五年级下.xlsx", 5, "下"),
    ("人教版一年级起点六年级上.xlsx", 6, "上"),
    ("人教版一年级起点六年级下.xlsx", 6, "下"),
]

# Common function words for which a generic dictionary's first sense is often
# unsuitable for elementary-school flashcards. Everything else is extracted
# conservatively from the first Chinese gloss in MeaningRaw.
MEANING_OVERRIDES = {
    "i": "我",
    "a": "一个；一",
    "an": "一个；一",
    "the": "这/那（个）；定冠词",
    "have": "有；拥有",
    "has": "有；拥有",
    "had": "有；拥有",
    "am": "是",
    "is": "是",
    "are": "是",
    "was": "是",
    "were": "是",
    "be": "是；成为",
    "you": "你；你们",
    "he": "他",
    "she": "她",
    "it": "它；这件事",
    "we": "我们",
    "they": "他们；她们；它们",
    "my": "我的",
    "your": "你的；你们的",
    "his": "他的",
    "her": "她的",
    "our": "我们的",
    "their": "他们的；她们的；它们的",
    "this": "这；这个",
    "that": "那；那个",
    "these": "这些",
    "those": "那些",
    "and": "和；并且",
    "or": "或者",
    "but": "但是",
    "yes": "是；对",
    "no": "不；不是",
    "not": "不；没有",
    "can": "能；会；可以",
    "can't": "不能；不会",
    "cannot": "不能；不会",
    "do": "做；干",
    "does": "做；干",
    "did": "做；干",
    "what": "什么",
    "who": "谁",
    "where": "哪里",
    "when": "什么时候",
    "why": "为什么",
    "how": "怎样；如何",
    "in": "在……里面",
    "on": "在……上面",
    "at": "在；于",
    "to": "到；向",
    "from": "从；来自",
    "of": "……的",
    "for": "为了；给",
    "with": "和；跟；用",
}

EXPECTED_HEADERS = {"单词", "英音", "美音", "释义"}
NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def col_index(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref or "")
    if not letters:
        return 0
    value = 0
    for ch in letters.group(0):
        value = value * 26 + ord(ch) - ord("A") + 1
    return value - 1


def read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    name = "xl/sharedStrings.xml"
    if name not in zf.namelist():
        return []
    root = ET.fromstring(zf.read(name))
    values = []
    for si in root.findall(f"{NS_MAIN}si"):
        values.append("".join(t.text or "" for t in si.iter(f"{NS_MAIN}t")))
    return values


def read_first_sheet(path: Path) -> list[list[str]]:
    with zipfile.ZipFile(path) as zf:
        shared = read_shared_strings(zf)
        sheet_name = "xl/worksheets/sheet1.xml"
        if sheet_name not in zf.namelist():
            raise RuntimeError(f"Missing first worksheet: {path}")
        root = ET.fromstring(zf.read(sheet_name))
        rows: list[list[str]] = []
        for row in root.iter(f"{NS_MAIN}row"):
            values: dict[int, str] = {}
            max_col = -1
            for cell in row.findall(f"{NS_MAIN}c"):
                idx = col_index(cell.attrib.get("r", ""))
                max_col = max(max_col, idx)
                cell_type = cell.attrib.get("t")
                if cell_type == "inlineStr":
                    value = "".join(t.text or "" for t in cell.iter(f"{NS_MAIN}t"))
                else:
                    v = cell.find(f"{NS_MAIN}v")
                    raw = "" if v is None or v.text is None else v.text
                    if cell_type == "s" and raw:
                        value = shared[int(raw)]
                    else:
                        value = raw
                values[idx] = value.strip()
            if max_col >= 0:
                rows.append([values.get(i, "") for i in range(max_col + 1)])
        return rows


def normalize_word(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def primary_meaning(word: str, raw: str) -> tuple[str, str]:
    override = MEANING_OVERRIDES.get(normalize_word(word))
    if override:
        return override, "override"

    text = re.sub(r"\[[^\]]*\]", "", raw or "")
    # Remove common POS abbreviations while retaining the Chinese gloss.
    text = re.sub(
        r"(?i)(?:^|\s)(?:n|v|vt|vi|adj|adv|prep|pron|conj|aux|art|num|int)\.?\s*",
        "",
        text,
    )
    text = re.sub(r"(?i)(?:n|v|vt|vi|adj|adv|prep|pron|conj|aux|art|num|int)\.\s*", "", text)
    parts = [p.strip(" ，,。.；;:") for p in re.split(r"[；;]", text) if p.strip(" ，,。.；;:")]
    if not parts:
        return raw.strip(), "raw"

    first = parts[0]
    # A malformed dictionary entry can still contain an English POS marker in
    # the middle (e.g. "已经vt. 有"). Prefer the Chinese tail after it.
    first = re.sub(r"(?i)^.*?(?:n|v|vt|vi|adj|adv|prep|pron|conj|aux|art|num|int)\.\s*", "", first).strip()
    return first or raw.strip(), "auto"


def parse_book(path: Path, grade: int, semester: str) -> list[dict[str, str]]:
    rows = read_first_sheet(path)
    if not rows:
        raise RuntimeError(f"Empty workbook: {path}")

    header_idx = None
    header_map: dict[str, int] = {}
    for i, row in enumerate(rows[:10]):
        candidate = {v.strip(): j for j, v in enumerate(row) if v.strip()}
        if EXPECTED_HEADERS.issubset(candidate.keys()):
            header_idx = i
            header_map = candidate
            break
    if header_idx is None:
        raise RuntimeError(f"Expected headers not found in {path.name}")

    book = f"{grade}年级{semester}"
    result = []
    for source_row, row in enumerate(rows[header_idx + 1 :], start=header_idx + 2):
        def get(name: str) -> str:
            idx = header_map[name]
            return row[idx].strip() if idx < len(row) else ""

        word = get("单词")
        if not word:
            continue
        meaning_raw = get("释义")
        meaning_primary, meaning_status = primary_meaning(word, meaning_raw)
        result.append(
            {
                "Word": word,
                "British": get("英音"),
                "American": get("美音"),
                "MeaningPrimary": meaning_primary,
                "MeaningRaw": meaning_raw,
                "MeaningStatus": meaning_status,
                "Book": book,
                "Grade": str(grade),
                "Semester": semester,
                "SourceFile": path.name,
                "SourceRow": str(source_row),
            }
        )
    return result


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    missing = [name for name, _, _ in BOOKS if not (SOURCE_DIR / name).exists()]
    if missing:
        raise SystemExit("Missing source files:\n- " + "\n- ".join(missing))

    if OUT_DIR.exists():
        # Keep README (maintained manually); rebuild only generated data dirs.
        shutil.rmtree(MASTER_DIR, ignore_errors=True)
        shutil.rmtree(IMPORT_DIR, ignore_errors=True)

    occurrences: list[dict[str, str]] = []
    for filename, grade, semester in BOOKS:
        occurrences.extend(parse_book(SOURCE_DIR / filename, grade, semester))

    unique: OrderedDict[str, dict[str, object]] = OrderedDict()
    for item in occurrences:
        key = normalize_word(item["Word"])
        if key not in unique:
            unique[key] = {
                **item,
                "FirstBook": item["Book"],
                "BooksList": [item["Book"]],
                "SourceFilesList": [item["SourceFile"]],
            }
        else:
            target = unique[key]
            if item["Book"] not in target["BooksList"]:
                target["BooksList"].append(item["Book"])
            if item["SourceFile"] not in target["SourceFilesList"]:
                target["SourceFilesList"].append(item["SourceFile"])
            for field in ("British", "American", "MeaningRaw"):
                if not target.get(field) and item.get(field):
                    target[field] = item[field]
            if not target.get("MeaningPrimary") and item.get("MeaningPrimary"):
                target["MeaningPrimary"] = item["MeaningPrimary"]
                target["MeaningStatus"] = item["MeaningStatus"]

    master_rows: list[dict[str, str]] = []
    for obj in unique.values():
        books = list(obj["BooksList"])
        grade = str(obj["Grade"])
        semester = str(obj["Semester"])
        tags = ["rj_start1", f"grade::{grade}", f"semester::{semester}"]
        tags.extend("appears::" + b for b in books)
        master_rows.append(
            {
                "Word": str(obj["Word"]),
                "British": str(obj["British"]),
                "American": str(obj["American"]),
                "MeaningPrimary": str(obj["MeaningPrimary"]),
                "MeaningRaw": str(obj["MeaningRaw"]),
                "MeaningStatus": str(obj["MeaningStatus"]),
                "FirstBook": str(obj["FirstBook"]),
                "Grade": grade,
                "Semester": semester,
                "Books": "|".join(books),
                "SourceFiles": "|".join(obj["SourceFilesList"]),
                "Tags": " ".join(tags),
            }
        )

    master_fields = [
        "Word",
        "British",
        "American",
        "MeaningPrimary",
        "MeaningRaw",
        "MeaningStatus",
        "FirstBook",
        "Grade",
        "Semester",
        "Books",
        "SourceFiles",
        "Tags",
    ]
    write_csv(MASTER_DIR / "vocabulary_master.csv", master_fields, master_rows)

    occurrence_fields = [
        "Word",
        "British",
        "American",
        "MeaningPrimary",
        "MeaningRaw",
        "MeaningStatus",
        "Book",
        "Grade",
        "Semester",
        "SourceFile",
        "SourceRow",
    ]
    write_csv(MASTER_DIR / "vocabulary_occurrences.csv", occurrence_fields, occurrences)

    import_fields = [
        "Word",
        "British",
        "American",
        "MeaningPrimary",
        "MeaningRaw",
        "Books",
        "Tags",
    ]
    per_book_counts: dict[str, int] = {}
    for _, grade, semester in BOOKS:
        book = f"{grade}年级{semester}"
        rows = [row for row in master_rows if row["FirstBook"] == book]
        per_book_counts[book] = len(rows)
        write_csv(IMPORT_DIR / f"{book}.csv", import_fields, rows)

    repeated = sum(1 for row in master_rows if "|" in row["Books"])
    stats = [
        ("source_files", len(BOOKS)),
        ("source_occurrences", len(occurrences)),
        ("unique_notes", len(master_rows)),
        ("repeated_words", repeated),
    ]
    stats.extend((f"new_notes_{book}", count) for book, count in per_book_counts.items())
    write_csv(MASTER_DIR / "build_stats.csv", ["Metric", "Value"], [{"Metric": k, "Value": str(v)} for k, v in stats])

    print(f"Built {len(master_rows)} unique notes from {len(occurrences)} source occurrences.")
    print(f"Repeated across books: {repeated}")


if __name__ == "__main__":
    main()
