#!/usr/bin/env python3
"""Prepare Beijing Edition Grade 1-6 vocabulary staging for Klose.

This tool is intentionally non-publishing. It reads the 12 Beijing Edition
(one-year-start) XLSX source files already in the repository, preserves every
source occurrence, and compares them against the committed Klose Vocabulary
identity registries.

It MUST NOT modify note_registry*, source_occurrences.csv, release registries,
publish outputs, learner state, or Anki state.
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
SOURCE_DIR = ROOT / "1.全国各大教材版本中小学同步" / "北京版"
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master"
OUT = BASE / "source_reference" / "beijing_start1_staging"

REGISTRY_FILES = [
    MASTER / "note_registry.csv",
    MASTER / "note_registry_extensions.csv",
]

EXPECTED_BOOKS = [(g, s) for g in range(1, 7) for s in ("上", "下")]
GRADE_CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}
BOOK_RE = re.compile(r"北京版一年级起点([一二三四五六])年级([上下])\.xlsx$")

OCC_FIELDS = [
    "SourceOccurrenceKey", "SourceID", "SourceBook", "Grade", "Semester",
    "SourceRow", "Word", "MatchKey", "British", "American", "Definition",
    "SourceFile",
]
CAND_FIELDS = OCC_FIELDS + [
    "CandidateClass", "CandidateNoteIDs", "CandidateWords", "CandidateSenses",
    "AutoDecision", "NeedsSenseReview", "ReviewReason",
]
SURFACE_FIELDS = [
    "MatchKey", "DisplayForms", "Definitions", "OccurrenceCount", "Books",
    "CandidateClass", "CandidateNoteIDs", "CandidateWords", "CandidateSenses",
    "AutoDecision", "NeedsSenseReview",
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
    if not rows:
        raise SystemExit(f"Empty XLSX: {path}")

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
        if not word:
            continue
        if word == "单词":
            continue
        key = match_key(word)
        occ_key = f"beijing_start1|g{grade}-{sem_en}|r{row_no:03d}|{key}"
        out.append({
            "SourceOccurrenceKey": occ_key,
            "SourceID": "beijing_start1",
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


def load_identities() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for path in REGISTRY_FILES:
        if not path.exists():
            raise SystemExit(f"Missing identity registry: {path}")
        for row in read_csv(path):
            nid = row.get("NoteID", "").strip()
            if not nid:
                continue
            if nid in seen:
                raise SystemExit(f"Duplicate NoteID across registries: {nid}")
            seen.add(nid)
            rows.append(row)
    return rows


IRREGULAR = {
    "children": "child", "men": "man", "women": "woman", "feet": "foot",
    "teeth": "tooth", "mice": "mouse", "geese": "goose",
}


def morphology_keys(key: str) -> list[str]:
    out: list[str] = []
    if key in IRREGULAR:
        out.append(IRREGULAR[key])
    if key.endswith("ies") and len(key) > 4:
        out.append(key[:-3] + "y")
    if key.endswith("es") and len(key) > 3:
        out.append(key[:-2])
    if key.endswith("s") and len(key) > 2 and not key.endswith("ss"):
        out.append(key[:-1])
    return list(dict.fromkeys(x for x in out if x and x != key))


def classify(occ: dict[str, str], by_key: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    key = occ["MatchKey"]
    exact = by_key.get(key, [])
    if len(exact) == 1:
        cands = exact
        cls = "exact-single"
        decision = "reuse-candidate"
        review = "yes"
        reason = "Exact MatchKey; target sense must still be confirmed before merge."
    elif len(exact) > 1:
        cands = exact
        cls = "exact-multiple"
        decision = "identity-review"
        review = "yes"
        reason = "Multiple existing identities share this MatchKey; select target sense explicitly."
    else:
        morph: list[dict[str, str]] = []
        for mk in morphology_keys(key):
            morph.extend(by_key.get(mk, []))
        if not morph and " " in key:
            for existing_key, rows in by_key.items():
                if existing_key and (existing_key in key or key in existing_key):
                    if existing_key != key:
                        morph.extend(rows)
        unique = {r.get("NoteID", ""): r for r in morph if r.get("NoteID")}
        cands = list(unique.values())
        if cands:
            cls = "morphology-or-phrase"
            decision = "identity-review"
            review = "yes"
            reason = "Only morphology/phrase-related candidates found; never auto-merge."
        else:
            cls = "no-existing-match"
            decision = "new-identity-candidate"
            review = "yes"
            reason = "No existing MatchKey candidate; confirm this is a genuine new learning unit."

    return {
        "CandidateClass": cls,
        "CandidateNoteIDs": "|".join(r.get("NoteID", "") for r in cands),
        "CandidateWords": "|".join(r.get("CanonicalWord", "") for r in cands),
        "CandidateSenses": "|".join(r.get("SenseLabel", "") for r in cands),
        "AutoDecision": decision,
        "NeedsSenseReview": review,
        "ReviewReason": reason,
    }


def main() -> None:
    source_files: dict[tuple[int, str], Path] = {}
    for path in SOURCE_DIR.glob("北京版一年级起点*年级*.xlsx"):
        m = BOOK_RE.fullmatch(path.name)
        if not m:
            continue
        source_files[(GRADE_CN[m.group(1)], m.group(2))] = path

    missing = [f"{g}年级{s}" for g, s in EXPECTED_BOOKS if (g, s) not in source_files]
    if missing:
        raise SystemExit(f"Missing Beijing source books: {missing}")
    if len(source_files) != 12:
        raise SystemExit(f"Expected exactly 12 Beijing Grade1-6 books, found {len(source_files)}")

    occurrences: list[dict[str, str]] = []
    per_book: Counter[str] = Counter()
    for grade, sem in EXPECTED_BOOKS:
        rows = parse_source(source_files[(grade, sem)], grade, sem)
        occurrences.extend(rows)
        per_book[f"{grade}年级{sem}"] += len(rows)

    identities = load_identities()
    by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in identities:
        key = row.get("MatchKey", "").strip() or match_key(row.get("CanonicalWord", ""))
        by_key[key].append(row)

    candidates: list[dict[str, str]] = []
    for occ in occurrences:
        row = dict(occ)
        row.update(classify(occ, by_key))
        candidates.append(row)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        grouped[row["MatchKey"]].append(row)
    surfaces: list[dict[str, str]] = []
    for key in sorted(grouped):
        rows = grouped[key]
        first = rows[0]
        surfaces.append({
            "MatchKey": key,
            "DisplayForms": "|".join(dict.fromkeys(r["Word"] for r in rows)),
            "Definitions": "|".join(dict.fromkeys(r["Definition"] for r in rows if r["Definition"])),
            "OccurrenceCount": str(len(rows)),
            "Books": "|".join(dict.fromkeys(r["SourceBook"] for r in rows)),
            "CandidateClass": first["CandidateClass"],
            "CandidateNoteIDs": first["CandidateNoteIDs"],
            "CandidateWords": first["CandidateWords"],
            "CandidateSenses": first["CandidateSenses"],
            "AutoDecision": first["AutoDecision"],
            "NeedsSenseReview": "yes" if any(r["NeedsSenseReview"] == "yes" for r in rows) else "no",
        })

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "occurrences.csv", OCC_FIELDS, occurrences)
    write_csv(OUT / "identity_candidates.csv", CAND_FIELDS, candidates)
    write_csv(OUT / "surface_inventory.csv", SURFACE_FIELDS, surfaces)

    class_counts = Counter(r["CandidateClass"] for r in candidates)
    decision_counts = Counter(r["AutoDecision"] for r in candidates)
    summary = [
        "# Beijing Edition Grade 1–6 Vocabulary — Pre-merge Staging",
        "",
        "> Status: **staging / non-authoritative / not merged into Klose Vocabulary**",
        "",
        "This directory is generated by `tools/prepare_klose_beijing_vocabulary.py`.",
        "It intentionally does not modify stable Vocabulary identities, source occurrences, release state, learner state, publish files, or Anki state.",
        "",
        "## Source scope",
        "",
        "- Source: repository `北京版/北京版一年级起点*.xlsx`",
        "- Grades: 1–6",
        "- Semesters: upper + lower",
        "- Books required: 12",
        f"- Parsed source occurrences: {len(occurrences)}",
        f"- Distinct MatchKeys: {len(surfaces)}",
        f"- Existing Klose identities compared: {len(identities)}",
        "",
        "## Per-book occurrence counts",
        "",
        "| Book | Occurrences |",
        "|---|---:|",
    ]
    for grade, sem in EXPECTED_BOOKS:
        book = f"{grade}年级{sem}"
        summary.append(f"| {book} | {per_book[book]} |")
    summary += [
        "",
        "## Candidate classification",
        "",
        "| Class | Occurrences | Meaning |",
        "|---|---:|---|",
        f"| exact-single | {class_counts['exact-single']} | one exact MatchKey candidate; still requires target-sense confirmation |",
        f"| exact-multiple | {class_counts['exact-multiple']} | multiple stable identities share MatchKey |",
        f"| morphology-or-phrase | {class_counts['morphology-or-phrase']} | only morphology/phrase-related candidates; never auto-merge |",
        f"| no-existing-match | {class_counts['no-existing-match']} | possible genuinely new learning unit |",
        "",
        "## Pre-merge decision buckets",
        "",
        f"- reuse-candidate: {decision_counts['reuse-candidate']}",
        f"- identity-review: {decision_counts['identity-review']}",
        f"- new-identity-candidate: {decision_counts['new-identity-candidate']}",
        "",
        "## Merge boundary",
        "",
        "No row in this staging directory is authorized to create/modify a NoteID by itself.",
        "Before merge, every candidate must receive a sense-aware decision. Existing NoteIDs must be reused where the learning unit is the same; new NoteIDs are append-only and only for genuinely new learning units.",
        "",
        "Generated files:",
        "- `occurrences.csv`: full Beijing source occurrences, preserving book and source row",
        "- `identity_candidates.csv`: occurrence-level comparison against current stable Klose identities",
        "- `surface_inventory.csv`: cross-book surface index for review; not an identity table",
        "",
    ]
    (OUT / "README.md").write_text("\n".join(summary), encoding="utf-8")

    print(f"Beijing books: {len(source_files)}")
    print(f"Occurrences: {len(occurrences)}")
    print(f"Distinct MatchKeys: {len(surfaces)}")
    print(f"Existing identities: {len(identities)}")
    for key in ("exact-single", "exact-multiple", "morphology-or-phrase", "no-existing-match"):
        print(f"{key}: {class_counts[key]}")


if __name__ == "__main__":
    main()
