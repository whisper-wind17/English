#!/usr/bin/env python3
"""Prepare Renjiao Edition (start-from-grade-1) vocabulary as third-party Source Adapter #2.

This tool performs Stage A only:
- parse the 12 Renjiao Grade 1-6 XLSX books;
- preserve every source occurrence;
- compare Renjiao surfaces against the current Beijing third-party seed;
- emit candidate-only overlap / morphology / new-surface staging outputs.

It MUST NOT use the Klose Stable Vocabulary Registry as a deletion/filtering source and
MUST NOT modify Klose master, learner, release, publish, or Anki state.
"""
from __future__ import annotations

import csv
import re
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "1.全国各大教材版本中小学同步"
SOURCE_DIR = RAW_ROOT / "人教版"
BASE = ROOT / "anki" / "klose"
BEIJING_OCC = BASE / "source_reference" / "beijing_start1_staging" / "occurrences.csv"
OUT = BASE / "source_reference" / "renjiao_start1_staging"

EXPECTED_BOOKS = [(g, s) for g in range(1, 7) for s in ("上", "下")]
GRADE_CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}
BOOK_RE = re.compile(r"人教版一年级起点([一二三四五六])年级([上下])\.xlsx$")

OCC_FIELDS = [
    "SourceOccurrenceKey", "SourceID", "SourceBook", "Grade", "Semester",
    "SourceRow", "Word", "MatchKey", "British", "American", "Definition",
    "SourceFile",
]
CMP_FIELDS = OCC_FIELDS + [
    "StageAClass", "SeedMatchKeys", "SeedDisplayForms", "SeedDefinitions",
    "NeedsSenseReview", "ReviewReason",
]
SURFACE_FIELDS = [
    "MatchKey", "DisplayForms", "Definitions", "Books", "OccurrenceCount",
    "StageAClass", "SeedMatchKeys", "SeedDisplayForms", "SeedDefinitions",
    "NeedsSenseReview",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: "" if row.get(k) is None else str(row.get(k, "")) for k in fields})


def norm_display(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", value.strip())


def match_key(value: str) -> str:
    return norm_display(value).casefold()


def format_alias_key(value: str) -> str:
    value = match_key(value)
    value = re.sub(r"(?:\.{2,}|…)+", " ", value)
    value = re.sub(r"[?!,;:]+$", "", value)
    return re.sub(r"\s+", " ", value).strip()


def shared_strings(zf: zipfile.ZipFile) -> list[str]:
    name = "xl/sharedStrings.xml"
    if name not in zf.namelist():
        return []
    root = ET.fromstring(zf.read(name))
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    out: list[str] = []
    for si in root.findall(f"{ns}si"):
        out.append("".join(t.text or "" for t in si.iter(f"{ns}t")))
    return out


def cell_value(cell: ET.Element, strings: list[str]) -> str:
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    typ = cell.attrib.get("t", "")
    if typ == "inlineStr":
        isel = cell.find(f"{ns}is")
        if isel is None:
            return ""
        return "".join(t.text or "" for t in isel.iter(f"{ns}t"))
    v = cell.find(f"{ns}v")
    raw = "" if v is None else (v.text or "")
    if typ == "s" and raw:
        return strings[int(raw)]
    return raw


def col_index(ref: str) -> int:
    letters = "".join(ch for ch in ref if ch.isalpha())
    n = 0
    for ch in letters.upper():
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n - 1


def read_xlsx_rows(path: Path) -> list[tuple[int, list[str]]]:
    with zipfile.ZipFile(path) as zf:
        strings = shared_strings(zf)
        sheet_name = "xl/worksheets/sheet1.xml"
        if sheet_name not in zf.namelist():
            raise SystemExit(f"Missing {sheet_name}: {path}")
        root = ET.fromstring(zf.read(sheet_name))
        ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        result: list[tuple[int, list[str]]] = []
        for row in root.iter(f"{ns}row"):
            row_no = int(row.attrib.get("r", "0") or 0)
            vals: dict[int, str] = {}
            for c in row.findall(f"{ns}c"):
                idx = col_index(c.attrib.get("r", "A1"))
                vals[idx] = norm_display(cell_value(c, strings))
            if not vals:
                continue
            width = max(vals) + 1
            result.append((row_no, [vals.get(i, "") for i in range(width)]))
        return result


def parse_source(path: Path, grade: int, semester: str) -> list[dict[str, str]]:
    rows = read_xlsx_rows(path)
    header_pos = None
    for i, (_, vals) in enumerate(rows[:10]):
        joined = "|".join(vals)
        if "单词" in joined and "释义" in joined:
            header_pos = i
            break
    if header_pos is None:
        raise SystemExit(f"Cannot find vocabulary header in {path.name}")

    book = f"{grade}年级{semester}"
    sem_en = "upper" if semester == "上" else "lower"
    out: list[dict[str, str]] = []
    for row_no, vals in rows[header_pos + 1:]:
        vals = vals + [""] * (4 - len(vals))
        word, british, american, definition = vals[:4]
        if not word or word == "单词":
            continue
        key = match_key(word)
        out.append({
            "SourceOccurrenceKey": f"renjiao_start1|g{grade}-{sem_en}|r{row_no:03d}|{key}",
            "SourceID": "renjiao_start1",
            "SourceBook": book,
            "Grade": str(grade),
            "Semester": semester,
            "SourceRow": str(row_no),
            "Word": word,
            "MatchKey": key,
            "British": british,
            "American": american,
            "Definition": definition,
            "SourceFile": path.name,
        })
    return out


IRREGULAR = {
    "children": "child", "men": "man", "women": "woman", "feet": "foot",
    "teeth": "tooth", "mice": "mouse", "geese": "goose",
}
NON_PLURAL_S_FORMS = {"its", "his", "this", "is", "was", "has", "does", "yes", "news"}


def morphology_keys(key: str) -> list[str]:
    if " " in key:
        return []
    out: list[str] = []
    if key in IRREGULAR:
        out.append(IRREGULAR[key])
    if key not in NON_PLURAL_S_FORMS:
        if key.endswith("ies") and len(key) > 4:
            out.append(key[:-3] + "y")
        if key.endswith("es") and len(key) > 3:
            out.append(key[:-2])
        if key.endswith("s") and len(key) > 2 and not key.endswith("ss"):
            out.append(key[:-1])
    return list(dict.fromkeys(x for x in out if x and x != key))


def unique_join(values: list[str]) -> str:
    return "|".join(dict.fromkeys(v for v in values if v))


def main() -> None:
    if not BEIJING_OCC.exists():
        raise SystemExit(f"Missing Beijing seed occurrences: {BEIJING_OCC}")

    source_files: dict[tuple[int, str], Path] = {}
    for path in SOURCE_DIR.glob("人教版一年级起点*年级*.xlsx"):
        m = BOOK_RE.fullmatch(path.name)
        if not m:
            continue
        source_files[(GRADE_CN[m.group(1)], m.group(2))] = path

    missing = [f"{g}年级{s}" for g, s in EXPECTED_BOOKS if (g, s) not in source_files]
    if missing:
        raise SystemExit(f"Missing Renjiao start1 source books: {missing}")
    if len(source_files) != 12:
        raise SystemExit(f"Expected exactly 12 Renjiao start1 Grade1-6 books, found {len(source_files)}")

    occurrences: list[dict[str, str]] = []
    per_book: Counter[str] = Counter()
    for grade, sem in EXPECTED_BOOKS:
        rows = parse_source(source_files[(grade, sem)], grade, sem)
        occurrences.extend(rows)
        per_book[f"{grade}年级{sem}"] += len(rows)

    seed_rows = read_csv(BEIJING_OCC)
    seed_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    seed_by_alias: dict[str, list[dict[str, str]]] = defaultdict(list)
    seed_morph_reverse: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in seed_rows:
        key = row.get("MatchKey", "").strip() or match_key(row.get("Word", ""))
        seed_by_key[key].append(row)
        alias = format_alias_key(row.get("Word", ""))
        if alias:
            seed_by_alias[alias].append(row)
        for mk in morphology_keys(key):
            seed_morph_reverse[mk].append(row)

    compared: list[dict[str, str]] = []
    for occ in occurrences:
        key = occ["MatchKey"]
        seed_match: list[dict[str, str]] = []
        cls: str
        reason: str

        if seed_by_key.get(key):
            seed_match = seed_by_key[key]
            cls = "exact-surface-overlap"
            reason = "Same MatchKey exists in Beijing seed; target sense must be resolved before third-party identity reuse."
        else:
            alias = format_alias_key(occ["Word"])
            if alias and seed_by_alias.get(alias):
                seed_match = seed_by_alias[alias]
                cls = "format-alias-overlap"
                reason = "Presentation-only punctuation/ellipsis candidate exists in Beijing seed."
            else:
                morph_rows: list[dict[str, str]] = []
                for mk in morphology_keys(key):
                    morph_rows.extend(seed_by_key.get(mk, []))
                morph_rows.extend(seed_morph_reverse.get(key, []))
                uniq: dict[str, dict[str, str]] = {}
                for row in morph_rows:
                    uniq[row.get("SourceOccurrenceKey", "") or f"{row.get('MatchKey','')}|{row.get('Word','')}"] = row
                seed_match = list(uniq.values())
                if seed_match:
                    cls = "morphology-overlap"
                    reason = "Inflection-related Beijing seed candidate; candidate-only, never auto-merge."
                else:
                    cls = "new-surface-candidate"
                    reason = "No Beijing seed surface/format/morphology candidate; still requires identity review for homographs and within-source sense splits."

        row = dict(occ)
        row.update({
            "StageAClass": cls,
            "SeedMatchKeys": unique_join([r.get("MatchKey", "") for r in seed_match]),
            "SeedDisplayForms": unique_join([r.get("Word", "") for r in seed_match]),
            "SeedDefinitions": unique_join([r.get("Definition", "") for r in seed_match]),
            "NeedsSenseReview": "yes",
            "ReviewReason": reason,
        })
        compared.append(row)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in compared:
        grouped[row["MatchKey"]].append(row)

    surfaces: list[dict[str, str]] = []
    for key in sorted(grouped):
        rows = grouped[key]
        first = rows[0]
        surfaces.append({
            "MatchKey": key,
            "DisplayForms": unique_join([r["Word"] for r in rows]),
            "Definitions": unique_join([r["Definition"] for r in rows]),
            "Books": unique_join([r["SourceBook"] for r in rows]),
            "OccurrenceCount": str(len(rows)),
            "StageAClass": first["StageAClass"],
            "SeedMatchKeys": first["SeedMatchKeys"],
            "SeedDisplayForms": first["SeedDisplayForms"],
            "SeedDefinitions": first["SeedDefinitions"],
            "NeedsSenseReview": "yes",
        })

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "occurrences.csv", OCC_FIELDS, occurrences)
    write_csv(OUT / "comparison_to_beijing_seed.csv", CMP_FIELDS, compared)
    write_csv(OUT / "surface_inventory.csv", SURFACE_FIELDS, surfaces)
    write_csv(OUT / "overlap_candidates.csv", SURFACE_FIELDS,
              [r for r in surfaces if r["StageAClass"] in {"exact-surface-overlap", "format-alias-overlap"}])
    write_csv(OUT / "morphology_review_queue.csv", SURFACE_FIELDS,
              [r for r in surfaces if r["StageAClass"] == "morphology-overlap"])
    write_csv(OUT / "new_surface_candidates.csv", SURFACE_FIELDS,
              [r for r in surfaces if r["StageAClass"] == "new-surface-candidate"])

    occ_counts = Counter(r["StageAClass"] for r in compared)
    surface_counts = Counter(r["StageAClass"] for r in surfaces)
    readme = f"""# Renjiao Start1 Grade 1-6 — Third-party Source Adapter #2 Staging

Generated by `tools/prepare_third_party_renjiao_start1.py`.

This is **Stage A only**. It compares Renjiao start1 against the Beijing third-party seed.
It does not perform the final Klose diff and does not remove anything because Klose already knows it.

## Scope

```text
Source books              = 12
Source occurrences        = {len(occurrences)}
Distinct MatchKeys        = {len(surfaces)}
Beijing seed occurrences  = {len(seed_rows)}
```

## Occurrence-level candidate classes

```text
exact-surface-overlap = {occ_counts['exact-surface-overlap']}
format-alias-overlap  = {occ_counts['format-alias-overlap']}
morphology-overlap    = {occ_counts['morphology-overlap']}
new-surface-candidate = {occ_counts['new-surface-candidate']}
```

## Surface-level candidate classes

```text
exact-surface-overlap = {surface_counts['exact-surface-overlap']}
format-alias-overlap  = {surface_counts['format-alias-overlap']}
morphology-overlap    = {surface_counts['morphology-overlap']}
new-surface-candidate = {surface_counts['new-surface-candidate']}
```

## Boundary

- Exact surface overlap is a candidate, not an automatic identity merge.
- Morphology is candidate-only.
- Same surface may still contain multiple target senses.
- New surface may still need within-source sense split.
- No Klose Master / Learner / Release / Publish / Anki state is modified.
- Final `existing-in-klose / third-party-new` classification is deferred until all planned third-party sources are complete.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    print(f"Renjiao start1 books = {len(source_files)}")
    print(f"Renjiao start1 occurrences = {len(occurrences)}")
    print(f"Renjiao start1 surfaces = {len(surfaces)}")
    print("Stage A only = yes")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
