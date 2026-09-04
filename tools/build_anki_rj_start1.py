#!/usr/bin/env python3
"""Build curated Anki CSVs for 人教版一年级起点 (Grades 1-6).

Raw XLSX files provide source spelling, pronunciation, dictionary glosses and
book occurrences. Card meanings/examples come only from the explicit curation
CSVs. Known source spelling defects are corrected for the canonical Anki Word
while WordRaw remains available in master/audit data.
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

# Confirmed source-data spelling defects. The XLSX itself is left untouched so
# the fork remains traceable to upstream; generated Anki data uses the canonical
# form. The original source spelling is preserved in WordRaw.
WORD_CORRECTIONS = {
    "neat breakfast": "eat breakfast",
    "neat lunch": "eat lunch",
    "neat dinner": "eat dinner",
    "neat seafood": "eat seafood",
}

EXPECTED_HEADERS = {"单词", "英音", "美音", "释义"}
CURATION_FIELDS = {"Word", "MeaningPrimary", "ExampleSentence", "ExampleTranslation"}
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
POS_NAMES = "abbr|aux|pron|prep|conj|adj|adv|num|int|art|det|modal|phrase|phr|vt|vi|n|v|un|na|vbl"
POS_RESIDUE_RE = re.compile(rf"(?:^|\s)(?:{POS_NAMES})\.\s*", re.I)
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
ENGLISH_RE = re.compile(r"[A-Za-z]")


def normalize_word(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def canonical_word(value: str) -> str:
    raw = re.sub(r"\s+", " ", value.strip())
    return WORD_CORRECTIONS.get(normalize_word(raw), raw)


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
        sheet = "xl/worksheets/sheet1.xml"
        if sheet not in zf.namelist():
            raise RuntimeError(f"Missing first worksheet: {path}")
        root = ET.fromstring(zf.read(sheet))
        result: list[list[str]] = []
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


def parse_book(path: Path, grade: int, semester: str) -> list[dict[str, str]]:
    rows = read_first_sheet(path)
    header_idx = None
    header_map: dict[str, int] = {}
    for i, row in enumerate(rows[:10]):
        candidate = {v.strip(): j for j, v in enumerate(row) if v.strip()}
        if EXPECTED_HEADERS.issubset(candidate):
            header_idx, header_map = i, candidate
            break
    if header_idx is None:
        raise RuntimeError(f"Expected headers not found in {path.name}")

    book = f"{grade}年级{semester}"
    output: list[dict[str, str]] = []
    for source_row, row in enumerate(rows[header_idx + 1 :], start=header_idx + 2):
        def get(name: str) -> str:
            idx = header_map[name]
            return row[idx].strip() if idx < len(row) else ""

        word_raw = get("单词")
        if not word_raw:
            continue
        output.append({
            "Word": canonical_word(word_raw),
            "WordRaw": word_raw,
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
                curation_word_raw = (row.get("Word") or "").strip()
                word = canonical_word(curation_word_raw)
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
                    "CurationWordRaw": curation_word_raw,
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


def review_reason(row: dict[str, str]) -> str:
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
                "WordRawList": [item["WordRaw"]],
            }
            continue
        target = unique[key]
        books = target["BooksList"]
        files = target["SourceFilesList"]
        raw_words = target["WordRawList"]
        assert isinstance(books, list) and isinstance(files, list) and isinstance(raw_words, list)
        if item["Book"] not in books:
            books.append(item["Book"])
        if item["SourceFile"] not in files:
            files.append(item["SourceFile"])
        if item["WordRaw"] not in raw_words:
            raw_words.append(item["WordRaw"])
        for field in ("British", "American", "MeaningRaw"):
            if not target.get(field) and item.get(field):
                target[field] = item[field]

    source_keys, curated_keys = set(unique), set(curated)
    missing_curated = sorted(source_keys - curated_keys)
    extra_curated = sorted(curated_keys - source_keys)
    if missing_curated or extra_curated:
        lines: list[str] = []
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
        raw_words = list(obj["WordRawList"])
        grade, semester = str(obj["Grade"]), str(obj["Semester"])
        tags = ["rj_start1", f"grade::{grade}", f"semester::{semester}"]
        tags += ["appears::" + str(b) for b in books]
        row = {
            "Word": str(obj["Word"]),
            "WordRaw": "|".join(str(x) for x in raw_words),
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
        reason = review_reason(row)
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
        "Word", "WordRaw", "British", "American", "MeaningPrimary", "ExampleSentence",
        "ExampleTranslation", "MeaningRaw", "MeaningStatus", "FirstBook", "Grade",
        "Semester", "Books", "SourceFiles", "Tags",
    ]
    write_csv(MASTER_DIR / "vocabulary_master.csv", master_fields, master_rows)

    occurrence_fields = [
        "Word", "WordRaw", "British", "American", "MeaningRaw", "Book", "Grade",
        "Semester", "SourceFile", "SourceRow",
    ]
    write_csv(MASTER_DIR / "vocabulary_occurrences.csv", occurrence_fields, occurrences)

    review_fields = [
        "Word", "MeaningPrimary", "ExampleSentence", "ExampleTranslation", "Reason", "FirstBook",
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
    corrected_occurrences = sum(1 for r in occurrences if r["Word"] != r["WordRaw"])
    stats = [
        ("source_files", len(BOOKS)),
        ("source_occurrences", len(occurrences)),
        ("unique_notes", len(master_rows)),
        ("repeated_words", repeated),
        ("curated_notes", len(curated)),
        ("curation_review_items", len(review_rows)),
        ("source_word_corrections", corrected_occurrences),
    ]
    stats += [(f"source_occurrences_{g}年级{s}", occurrence_counts[f"{g}年级{s}"]) for _, g, s in BOOKS]
    stats += [(f"new_notes_{g}年级{s}", new_counts[f"{g}年级{s}"]) for _, g, s in BOOKS]
    write_csv(
        MASTER_DIR / "build_stats.csv",
        ["Metric", "Value"],
        [{"Metric": key, "Value": str(value)} for key, value in stats],
    )

    print(f"Built {len(master_rows)} curated notes from {len(occurrences)} source occurrences.")
    print(
        f"Repeated words: {repeated}; structural review: {len(review_rows)}; "
        f"source spelling corrections: {corrected_occurrences}"
    )


if __name__ == "__main__":
    main()
