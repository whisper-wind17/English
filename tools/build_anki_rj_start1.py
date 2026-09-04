#!/usr/bin/env python3
"""Build Anki CSVs for 人教版一年级起点 (Grades 1-6).

The raw XLSX files provide spelling, pronunciation, source glosses and book
occurrences. Final card meanings and examples MUST come from the manually
reviewed per-book CSV files in anki/人教版一年级起点/curation/.
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
CURATION_DIR = OUT_DIR / "curation"
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

EXPECTED_HEADERS = {"单词", "英音", "美音", "释义"}
CURATION_FIELDS = {"Word", "MeaningPrimary", "ExampleSentence", "ExampleTranslation"}
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
POS_NAMES = "abbr|aux|pron|prep|conj|adj|adv|num|int|art|det|modal|phrase|phr|vt|vi|n|v|un|na|vbl"
POS_RESIDUE_RE = re.compile(rf"(?:^|\s)(?:{POS_NAMES})\.\s*", re.I)
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
ENGLISH_RE = re.compile(r"[A-Za-z]")


def col_index(ref: str) -> int:
    m = re.match(r"[A-Z]+", ref or "")
    if not m:
        return 0
    n = 0
    for ch in m.group(0):
        n = n * 26 + ord(ch) - ord("A") + 1
    return n - 1


def read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in si.iter(f"{NS}t")) for si in root.findall(f"{NS}si")]


def read_first_sheet(path: Path) -> list[list[str]]:
    with zipfile.ZipFile(path) as zf:
        shared = read_shared_strings(zf)
        name = "xl/worksheets/sheet1.xml"
        if name not in zf.namelist():
            raise RuntimeError(f"Missing first worksheet: {path}")
        root = ET.fromstring(zf.read(name))
        result = []
        for row in root.iter(f"{NS}row"):
            cells: dict[int, str] = {}
            max_col = -1
            for cell in row.findall(f"{NS}c"):
                idx = col_index(cell.attrib.get("r", ""))
                max_col = max(max_col, idx)
                if cell.attrib.get("t") == "inlineStr":
                    value = "".join(t.text or "" for t in cell.iter(f"{NS}t"))
                else:
                    v = cell.find(f"{NS}v")
                    raw = "" if v is None or v.text is None else v.text
                    value = shared[int(raw)] if cell.attrib.get("t") == "s" and raw else raw
                cells[idx] = value.strip()
            if max_col >= 0:
                result.append([cells.get(i, "") for i in range(max_col + 1)])
        return result


def normalize_word(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def parse_book(path: Path, grade: int, semester: str) -> list[dict[str, str]]:
    rows = read_first_sheet(path)
    header_idx, header_map = None, {}
    for i, row in enumerate(rows[:10]):
        candidate = {v.strip(): j for j, v in enumerate(row) if v.strip()}
        if EXPECTED_HEADERS.issubset(candidate):
            header_idx, header_map = i, candidate
            break
    if header_idx is None:
        raise RuntimeError(f"Expected headers not found in {path.name}")

    book, output = f"{grade}年级{semester}", []
    for source_row, row in enumerate(rows[header_idx + 1:], start=header_idx + 2):
        def get(name: str) -> str:
            idx = header_map[name]
            return row[idx].strip() if idx < len(row) else ""

        word = get("单词")
        if not word:
            continue
        output.append({
            "Word": word,
            "British": get("英音"),
            "American": get("美音"),
            "MeaningRaw": get("释义"),
            "Book": book,
            "Grade": str(grade),
            "Semester": semester,
            "SourceFile": path.name,
            "SourceRow": str(source_row),
        })
    return output


def load_curation() -> dict[str, dict[str, str]]:
    curated: dict[str, dict[str, str]] = {}
    problems: list[str] = []
    for _, grade, semester in BOOKS:
        book = f"{grade}年级{semester}"
        path = CURATION_DIR / f"{book}.csv"
        if not path.exists():
            problems.append(f"missing curation file: {path.relative_to(ROOT)}")
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fields = set(reader.fieldnames or [])
            if not CURATION_FIELDS.issubset(fields):
                problems.append(f"bad curation headers: {path.relative_to(ROOT)}")
                continue
            for line_no, row in enumerate(reader, start=2):
                word = (row.get("Word") or "").strip()
                key = normalize_word(word)
                if not key:
                    problems.append(f"empty Word: {path.name}:{line_no}")
                    continue
                if key in curated:
                    problems.append(f"duplicate curated Word: {word} ({path.name}:{line_no})")
                    continue
                primary = (row.get("MeaningPrimary") or "").strip()
                example = (row.get("ExampleSentence") or "").strip()
                translation = (row.get("ExampleTranslation") or "").strip()
                if not primary or not example or not translation:
                    problems.append(f"incomplete curation: {word} ({path.name}:{line_no})")
                curated[key] = {
                    "Word": word,
                    "MeaningPrimary": primary,
                    "ExampleSentence": example,
                    "ExampleTranslation": translation,
                    "CuratedBook": book,
                }
    if problems:
        raise SystemExit("Curation file errors:\n- " + "\n- ".join(problems))
    return curated


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def example_review_reason(row: dict[str, str]) -> str:
    reasons: list[str] = []
    primary = row["MeaningPrimary"]
    example = row["ExampleSentence"]
    translation = row["ExampleTranslation"]
    if POS_RESIDUE_RE.search(primary):
        reasons.append("pos-residue")
    if not CHINESE_RE.search(primary):
        reasons.append("meaning-no-chinese")
    if not ENGLISH_RE.search(example):
        reasons.append("example-no-english")
    if not CHINESE_RE.search(translation):
        reasons.append("translation-no-chinese")
    word_count = len(re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*", example))
    if word_count > 12:
        reasons.append("example-too-long")
    if len(primary) > 32:
        reasons.append("meaning-too-long")
    return ";".join(reasons)


def main() -> None:
    missing = [name for name, _, _ in BOOKS if not (SOURCE_DIR / name).exists()]
    if missing:
        raise SystemExit("Missing source files:\n- " + "\n- ".join(missing))

    curated = load_curation()

    if OUT_DIR.exists():
        shutil.rmtree(MASTER_DIR, ignore_errors=True)
        shutil.rmtree(IMPORT_DIR, ignore_errors=True)

    occurrences: list[dict[str, str]] = []
    occurrence_counts: dict[str, int] = {}
    for filename, grade, semester in BOOKS:
        book = f"{grade}年级{semester}"
        rows = parse_book(SOURCE_DIR / filename, grade, semester)
        occurrence_counts[book] = len(rows)
        occurrences.extend(rows)

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
        books = target["BooksList"]
        files = target["SourceFilesList"]
        assert isinstance(books, list) and isinstance(files, list)
        if item["Book"] not in books:
            books.append(item["Book"])
        if item["SourceFile"] not in files:
            files.append(item["SourceFile"])
        for field in ("British", "American", "MeaningRaw"):
            if not target.get(field) and item.get(field):
                target[field] = item[field]

    source_keys = set(unique)
    curated_keys = set(curated)
    missing_curated = sorted(source_keys - curated_keys)
    extra_curated = sorted(curated_keys - source_keys)
    if missing_curated or extra_curated:
        lines = []
        if missing_curated:
            lines.append("Missing curated words: " + ", ".join(str(unique[k]["Word"]) for k in missing_curated))
        if extra_curated:
            lines.append("Unknown curated words: " + ", ".join(curated[k]["Word"] for k in extra_curated))
        raise SystemExit("Curation coverage mismatch:\n" + "\n".join(lines))

    master_rows: list[dict[str, str]] = []
    review_rows: list[dict[str, str]] = []
    for key, obj in unique.items():
        c = curated[key]
        first_book = str(obj["FirstBook"])
        if c["CuratedBook"] != first_book:
            raise SystemExit(
                f"Curation book mismatch for {obj['Word']}: source={first_book}, curated={c['CuratedBook']}"
            )
        books = list(obj["BooksList"])
        grade = str(obj["Grade"])
        semester = str(obj["Semester"])
        tags = ["rj_start1", f"grade::{grade}", f"semester::{semester}"]
        tags += ["appears::" + str(b) for b in books]
        row = {
            "Word": str(obj["Word"]),
            "British": str(obj["British"]),
            "American": str(obj["American"]),
            "MeaningPrimary": c["MeaningPrimary"],
            "ExampleSentence": c["ExampleSentence"],
            "ExampleTranslation": c["ExampleTranslation"],
            "MeaningRaw": str(obj["MeaningRaw"]),
            "MeaningStatus": "curated",
            "FirstBook": first_book,
            "Grade": grade,
            "Semester": semester,
            "Books": "|".join(str(b) for b in books),
            "SourceFiles": "|".join(str(x) for x in obj["SourceFilesList"]),
            "Tags": " ".join(tags),
        }
        master_rows.append(row)
        reason = example_review_reason(row)
        if reason:
            review_rows.append({
                "Word": row["Word"],
                "MeaningPrimary": row["MeaningPrimary"],
                "ExampleSentence": row["ExampleSentence"],
                "ExampleTranslation": row["ExampleTranslation"],
                "Reason": reason,
                "FirstBook": row["FirstBook"],
            })

    master_fields = [
        "Word", "British", "American", "MeaningPrimary", "ExampleSentence",
        "ExampleTranslation", "MeaningRaw", "MeaningStatus", "FirstBook",
        "Grade", "Semester", "Books", "SourceFiles", "Tags",
    ]
    write_csv(MASTER_DIR / "vocabulary_master.csv", master_fields, master_rows)

    occurrence_fields = [
        "Word", "British", "American", "MeaningRaw", "Book", "Grade",
        "Semester", "SourceFile", "SourceRow",
    ]
    write_csv(MASTER_DIR / "vocabulary_occurrences.csv", occurrence_fields, occurrences)

    review_fields = [
        "Word", "MeaningPrimary", "ExampleSentence", "ExampleTranslation",
        "Reason", "FirstBook",
    ]
    write_csv(MASTER_DIR / "curation_review.csv", review_fields, review_rows)

    import_fields = [
        "Word", "British", "American", "MeaningPrimary", "ExampleSentence",
        "ExampleTranslation", "MeaningRaw", "Books", "Tags",
    ]
    new_counts: dict[str, int] = {}
    for _, grade, semester in BOOKS:
        book = f"{grade}年级{semester}"
        rows = [r for r in master_rows if r["FirstBook"] == book]
        new_counts[book] = len(rows)
        write_csv(IMPORT_DIR / f"{book}.csv", import_fields, rows)

    repeated = sum(1 for r in master_rows if "|" in r["Books"])
    stats = [
        ("source_files", len(BOOKS)),
        ("source_occurrences", len(occurrences)),
        ("unique_notes", len(master_rows)),
        ("repeated_words", repeated),
        ("curated_notes", len(curated)),
        ("curation_review_items", len(review_rows)),
    ]
    stats += [(f"source_occurrences_{b}", occurrence_counts[b]) for _, g, s in BOOKS for b in [f"{g}年级{s}"]]
    stats += [(f"new_notes_{b}", new_counts[b]) for _, g, s in BOOKS for b in [f"{g}年级{s}"]]
    write_csv(
        MASTER_DIR / "build_stats.csv",
        ["Metric", "Value"],
        [{"Metric": k, "Value": str(v)} for k, v in stats],
    )

    print(f"Built {len(master_rows)} curated unique notes from {len(occurrences)} source occurrences.")
    print(f"Repeated across books: {repeated}; curation review queue: {len(review_rows)}")


if __name__ == "__main__":
    main()
