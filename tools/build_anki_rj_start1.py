#!/usr/bin/env python3
"""Build Anki-ready CSV files for 人教版一年级起点 (Grade 1-6).

The source XLSX files remain untouched.  This script uses only the Python
standard library and parses the first worksheet directly from OOXML.

Data model:
- one normalized English word = one Anki note;
- the note belongs to the first book in which the word appears;
- later appearances are preserved in Books/Tags metadata;
- MeaningRaw preserves the source dictionary text;
- MeaningPrimary is a conservative elementary-school display gloss.
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

# Generic dictionary entries are often too broad for a child-facing card.
# These overrides cover high-frequency function words/numerals where simply
# choosing the first dictionary gloss is especially error-prone.
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
    "zero": "零；0",
    "one": "一；一个",
    "two": "二；两个",
    "three": "三；三个",
    "four": "四；四个",
    "five": "五；五个",
    "six": "六；六个",
    "seven": "七；七个",
    "eight": "八；八个",
    "nine": "九；九个",
    "ten": "十；十个",
    "eleven": "十一；十一个",
    "twelve": "十二；十二个",
    "thirteen": "十三；十三个",
    "fourteen": "十四；十四个",
    "fifteen": "十五；十五个",
    "sixteen": "十六；十六个",
    "seventeen": "十七；十七个",
    "eighteen": "十八；十八个",
    "nineteen": "十九；十九个",
    "twenty": "二十；二十个",
}

EXPECTED_HEADERS = {"单词", "英音", "美音", "释义"}
NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

# Longest tokens first: otherwise "num." can be partially consumed as "n".
POS_NAMES = (
    "abbr|aux|pron|prep|conj|adj|adv|num|int|art|det|modal|"
    "phrase|phr|vt|vi|n|v"
)
POS_PREFIX_RE = re.compile(rf"^(?:{POS_NAMES})\.?(?:\s+|$)", re.IGNORECASE)
POS_RESIDUE_RE = re.compile(rf"\b(?:{POS_NAMES})\.", re.IGNORECASE)
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")


def col_index(cell_ref: str) -> int:
    match = re.match(r"[A-Z]+", cell_ref or "")
    if not match:
        return 0
    value = 0
    for ch in match.group(0):
        value = value * 26 + ord(ch) - ord("A") + 1
    return value - 1


def read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    name = "xl/sharedStrings.xml"
    if name not in zf.namelist():
        return []
    root = ET.fromstring(zf.read(name))
    values: list[str] = []
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


def clean_gloss_line(line: str) -> str:
    """Remove only a leading POS marker; never globally delete POS-like text."""
    line = line.strip()
    # Some entries start with more than one marker, e.g. "aux. vt. ...".
    for _ in range(3):
        cleaned = POS_PREFIX_RE.sub("", line, count=1).strip()
        if cleaned == line:
            break
        line = cleaned
    return line


def primary_meaning(word: str, raw: str) -> tuple[str, str]:
    override = MEANING_OVERRIDES.get(normalize_word(word))
    if override:
        return override, "override"

    text = re.sub(r"\[[^\]]*\]", "", raw or "").strip()
    if not text:
        return "", "raw"

    # Dictionary exports often store each part of speech / sense on a new line.
    # For elementary cards, take the first non-empty cleaned line and its first
    # semicolon-delimited sense.  MeaningRaw remains available for inspection.
    for raw_line in text.splitlines():
        line = clean_gloss_line(raw_line)
        if not line:
            continue
        first = re.split(r"[；;]", line, maxsplit=1)[0].strip(" ，,。.；;:")
        if first:
            return first, "auto"

    return raw.strip(), "raw"


def review_reason(primary: str, raw: str, status: str) -> str:
    reasons: list[str] = []
    if not primary:
        reasons.append("empty")
    if "\n" in primary or "\r" in primary:
        reasons.append("multiline")
    if POS_RESIDUE_RE.search(primary):
        reasons.append("pos-residue")
    if status == "raw":
        reasons.append("fallback-raw")
    if primary and not CHINESE_RE.search(primary) and re.search(r"[A-Za-z]", primary):
        reasons.append("no-chinese-gloss")
    if len(primary) > 36:
        reasons.append("too-long")
    return ";".join(reasons)


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
    result: list[dict[str, str]] = []
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
    # utf-8-sig keeps Chinese readable when opened directly in Excel and is
    # accepted by Anki's text importer.
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    missing = [name for name, _, _ in BOOKS if not (SOURCE_DIR / name).exists()]
    if missing:
        raise SystemExit("Missing source files:\n- " + "\n- ".join(missing))

    if OUT_DIR.exists():
        # README is maintained manually; only generated directories are rebuilt.
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
            continue

        target = unique[key]
        books_list = target["BooksList"]
        source_files_list = target["SourceFilesList"]
        assert isinstance(books_list, list)
        assert isinstance(source_files_list, list)
        if item["Book"] not in books_list:
            books_list.append(item["Book"])
        if item["SourceFile"] not in source_files_list:
            source_files_list.append(item["SourceFile"])
        for field in ("British", "American", "MeaningRaw"):
            if not target.get(field) and item.get(field):
                target[field] = item[field]
        if not target.get("MeaningPrimary") and item.get("MeaningPrimary"):
            target["MeaningPrimary"] = item["MeaningPrimary"]
            target["MeaningStatus"] = item["MeaningStatus"]

    master_rows: list[dict[str, str]] = []
    review_rows: list[dict[str, str]] = []
    for obj in unique.values():
        books = list(obj["BooksList"])
        grade = str(obj["Grade"])
        semester = str(obj["Semester"])
        tags = ["rj_start1", f"grade::{grade}", f"semester::{semester}"]
        tags.extend("appears::" + str(book) for book in books)
        row = {
            "Word": str(obj["Word"]),
            "British": str(obj["British"]),
            "American": str(obj["American"]),
            "MeaningPrimary": str(obj["MeaningPrimary"]),
            "MeaningRaw": str(obj["MeaningRaw"]),
            "MeaningStatus": str(obj["MeaningStatus"]),
            "FirstBook": str(obj["FirstBook"]),
            "Grade": grade,
            "Semester": semester,
            "Books": "|".join(str(book) for book in books),
            "SourceFiles": "|".join(str(x) for x in obj["SourceFilesList"]),
            "Tags": " ".join(tags),
        }
        master_rows.append(row)

        reason = review_reason(row["MeaningPrimary"], row["MeaningRaw"], row["MeaningStatus"])
        if reason:
            review_rows.append(
                {
                    "Word": row["Word"],
                    "MeaningPrimary": row["MeaningPrimary"],
                    "MeaningRaw": row["MeaningRaw"],
                    "Reason": reason,
                    "FirstBook": row["FirstBook"],
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
    write_csv(
        MASTER_DIR / "meaning_review.csv",
        ["Word", "MeaningPrimary", "MeaningRaw", "Reason", "FirstBook"],
        review_rows,
    )

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
        ("meaning_review_items", len(review_rows)),
    ]
    stats.extend((f"new_notes_{book}", count) for book, count in per_book_counts.items())
    write_csv(
        MASTER_DIR / "build_stats.csv",
        ["Metric", "Value"],
        [{"Metric": key, "Value": str(value)} for key, value in stats],
    )

    print(f"Built {len(master_rows)} unique notes from {len(occurrences)} source occurrences.")
    print(f"Repeated across books: {repeated}")
    print(f"Meaning review queue: {len(review_rows)}")


if __name__ == "__main__":
    main()
