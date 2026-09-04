#!/usr/bin/env python3
"""Build Anki CSVs for 人教版一年级起点 (Grades 1-6)."""
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

MEANING_OVERRIDES = {
    "i": "我", "a": "一个；一", "an": "一个；一", "the": "这/那（个）；定冠词",
    "have": "有；拥有", "has": "有；拥有", "had": "有；拥有",
    "am": "是", "is": "是", "are": "是", "was": "是", "were": "是", "be": "是；成为",
    "you": "你；你们", "he": "他", "she": "她", "it": "它；这件事", "we": "我们",
    "they": "他们；她们；它们", "my": "我的", "your": "你的；你们的", "his": "他的",
    "her": "她的", "our": "我们的", "their": "他们的；她们的；它们的",
    "this": "这；这个", "that": "那；那个", "these": "这些", "those": "那些",
    "and": "和；并且", "or": "或者", "but": "但是", "yes": "是；对", "no": "不；不是",
    "not": "不；没有", "can": "能；会；可以", "can't": "不能；不会", "cannot": "不能；不会",
    "do": "做；干", "does": "做；干", "did": "做；干", "what": "什么", "who": "谁",
    "where": "哪里", "when": "什么时候", "why": "为什么", "how": "怎样；如何",
    "in": "在……里面", "on": "在……上面", "at": "在；于", "to": "到；向",
    "from": "从；来自", "of": "……的", "for": "为了；给", "with": "和；跟；用",
    "zero": "零；0", "one": "一；一个", "two": "二；两个", "three": "三；三个",
    "four": "四；四个", "five": "五；五个", "six": "六；六个", "seven": "七；七个",
    "eight": "八；八个", "nine": "九；九个", "ten": "十；十个", "eleven": "十一；十一个",
    "twelve": "十二；十二个", "thirteen": "十三；十三个", "fourteen": "十四；十四个",
    "fifteen": "十五；十五个", "sixteen": "十六；十六个", "seventeen": "十七；十七个",
    "eighteen": "十八；十八个", "nineteen": "十九；十九个", "twenty": "二十；二十个",
    "big ben": "大本钟（英国伦敦）", "pen pal": "笔友",
}

EXPECTED_HEADERS = {"单词", "英音", "美音", "释义"}
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
POS_NAMES = "abbr|aux|pron|prep|conj|adj|adv|num|int|art|det|modal|phrase|phr|vt|vi|n|v"
POS_PREFIX_RE = re.compile(rf"^(?:{POS_NAMES})\.?(?:\s+|$)", re.I)
POS_RESIDUE_RE = re.compile(rf"\b(?:{POS_NAMES})\.", re.I)
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")


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
            cells, max_col = {}, -1
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


def clean_gloss_line(line: str) -> str:
    line = line.strip()
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
    for raw_line in text.splitlines():
        line = clean_gloss_line(raw_line)
        if not line:
            continue
        first = re.split(r"[；;]", line, maxsplit=1)[0].strip(" ，,。.；;:")
        if first:
            return first, "auto"
    return raw.strip(), "raw"


def review_reason(primary: str, status: str) -> str:
    reasons = []
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
        raw = get("释义")
        primary, status = primary_meaning(word, raw)
        output.append({
            "Word": word, "British": get("英音"), "American": get("美音"),
            "MeaningPrimary": primary, "MeaningRaw": raw, "MeaningStatus": status,
            "Book": book, "Grade": str(grade), "Semester": semester,
            "SourceFile": path.name, "SourceRow": str(source_row),
        })
    return output


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    missing = [name for name, _, _ in BOOKS if not (SOURCE_DIR / name).exists()]
    if missing:
        raise SystemExit("Missing source files:\n- " + "\n- ".join(missing))
    if OUT_DIR.exists():
        shutil.rmtree(MASTER_DIR, ignore_errors=True)
        shutil.rmtree(IMPORT_DIR, ignore_errors=True)

    occurrences = []
    occurrence_counts = {}
    for filename, grade, semester in BOOKS:
        book = f"{grade}年级{semester}"
        rows = parse_book(SOURCE_DIR / filename, grade, semester)
        occurrence_counts[book] = len(rows)
        occurrences.extend(rows)

    unique: OrderedDict[str, dict[str, object]] = OrderedDict()
    for item in occurrences:
        key = normalize_word(item["Word"])
        if key not in unique:
            unique[key] = {**item, "FirstBook": item["Book"], "BooksList": [item["Book"]], "SourceFilesList": [item["SourceFile"]]}
            continue
        target = unique[key]
        books, files = target["BooksList"], target["SourceFilesList"]
        assert isinstance(books, list) and isinstance(files, list)
        if item["Book"] not in books:
            books.append(item["Book"])
        if item["SourceFile"] not in files:
            files.append(item["SourceFile"])
        for field in ("British", "American", "MeaningRaw"):
            if not target.get(field) and item.get(field):
                target[field] = item[field]
        if not target.get("MeaningPrimary") and item.get("MeaningPrimary"):
            target["MeaningPrimary"], target["MeaningStatus"] = item["MeaningPrimary"], item["MeaningStatus"]

    master_rows, review_rows = [], []
    for obj in unique.values():
        books = list(obj["BooksList"])
        grade, semester = str(obj["Grade"]), str(obj["Semester"])
        tags = ["rj_start1", f"grade::{grade}", f"semester::{semester}"] + ["appears::" + str(b) for b in books]
        row = {
            "Word": str(obj["Word"]), "British": str(obj["British"]), "American": str(obj["American"]),
            "MeaningPrimary": str(obj["MeaningPrimary"]), "MeaningRaw": str(obj["MeaningRaw"]),
            "MeaningStatus": str(obj["MeaningStatus"]), "FirstBook": str(obj["FirstBook"]),
            "Grade": grade, "Semester": semester, "Books": "|".join(str(b) for b in books),
            "SourceFiles": "|".join(str(x) for x in obj["SourceFilesList"]), "Tags": " ".join(tags),
        }
        master_rows.append(row)
        reason = review_reason(row["MeaningPrimary"], row["MeaningStatus"])
        if reason:
            review_rows.append({"Word": row["Word"], "MeaningPrimary": row["MeaningPrimary"], "MeaningRaw": row["MeaningRaw"], "Reason": reason, "FirstBook": row["FirstBook"]})

    master_fields = ["Word", "British", "American", "MeaningPrimary", "MeaningRaw", "MeaningStatus", "FirstBook", "Grade", "Semester", "Books", "SourceFiles", "Tags"]
    write_csv(MASTER_DIR / "vocabulary_master.csv", master_fields, master_rows)
    occurrence_fields = ["Word", "British", "American", "MeaningPrimary", "MeaningRaw", "MeaningStatus", "Book", "Grade", "Semester", "SourceFile", "SourceRow"]
    write_csv(MASTER_DIR / "vocabulary_occurrences.csv", occurrence_fields, occurrences)
    write_csv(MASTER_DIR / "meaning_review.csv", ["Word", "MeaningPrimary", "MeaningRaw", "Reason", "FirstBook"], review_rows)

    import_fields = ["Word", "British", "American", "MeaningPrimary", "MeaningRaw", "Books", "Tags"]
    new_counts = {}
    for _, grade, semester in BOOKS:
        book = f"{grade}年级{semester}"
        rows = [r for r in master_rows if r["FirstBook"] == book]
        new_counts[book] = len(rows)
        write_csv(IMPORT_DIR / f"{book}.csv", import_fields, rows)

    repeated = sum(1 for r in master_rows if "|" in r["Books"])
    stats = [
        ("source_files", len(BOOKS)), ("source_occurrences", len(occurrences)),
        ("unique_notes", len(master_rows)), ("repeated_words", repeated),
        ("meaning_review_items", len(review_rows)),
    ]
    stats += [(f"source_occurrences_{b}", occurrence_counts[b]) for _, g, s in BOOKS for b in [f"{g}年级{s}"]]
    stats += [(f"new_notes_{b}", new_counts[b]) for _, g, s in BOOKS for b in [f"{g}年级{s}"]]
    write_csv(MASTER_DIR / "build_stats.csv", ["Metric", "Value"], [{"Metric": k, "Value": str(v)} for k, v in stats])

    print(f"Built {len(master_rows)} unique notes from {len(occurrences)} source occurrences.")
    print(f"Repeated across books: {repeated}; meaning review queue: {len(review_rows)}")


if __name__ == "__main__":
    main()
