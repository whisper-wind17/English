#!/usr/bin/env python3
"""Audit actual Grade-4 items that reuse legacy vocabulary identities.

The original batch match intentionally preferred reuse where possible. This
second-pass audit is stricter: it surfaces likely sense drift and every morphology
reuse for semantic review. It does not mutate identity state.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
ACTUAL = BASE / "source_reference" / "rj_start1-grade4-klose-actual.csv"
LEGACY = BASE / "master" / "note_registry.csv"
EXT = BASE / "master" / "note_registry_extensions.csv"
MAPPINGS = BASE / "master" / "source_identity_extensions.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", value.strip()).casefold()


def source_item_key(row: dict[str, str]) -> str:
    sem = {"上": "upper", "下": "lower"}[row["Semester"].strip()]
    return f"grade4-{sem}-u{int(row['Unit']):02d}-o{int(row['Order']):03d}|{norm(row['Entry'])}"


def chinese_chars(text: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fff]", text))


def meaning_overlap(a: str, b: str) -> bool:
    a = chinese_chars(a)
    b = chinese_chars(b)
    if not a or not b:
        return True
    if a in b or b in a:
        return True
    a2 = {a[i:i+2] for i in range(len(a)-1)}
    b2 = {b[i:i+2] for i in range(len(b)-1)}
    if a2 & b2:
        return True
    # single-character overlap is accepted only when one gloss is one character,
    # e.g. `马` / `马`; otherwise it is too weak for identity confirmation.
    return len(a) == 1 and len(b) == 1 and a == b


def main() -> None:
    actual_by_key = {source_item_key(r): r for r in read_csv(ACTUAL)}
    registry = {r["NoteID"].strip(): r for r in [*read_csv(LEGACY), *read_csv(EXT)]}
    mappings = [
        r for r in read_csv(MAPPINGS)
        if r.get("SourceID", "").strip() == "rj_start1"
        and r.get("SourceEdition", "").strip() == "klose-current"
        and r.get("Status", "").strip() == "confirmed"
        and r.get("SourceItemKey", "").strip().startswith("grade4-")
        and r.get("Decision", "").strip().startswith("reuse")
    ]

    flagged: list[tuple[str, str, str, str, str, str]] = []
    for m in mappings:
        key = m["SourceItemKey"].strip()
        source = actual_by_key[key]
        nid = m["NoteID"].strip()
        reg = registry[nid]
        actual_word = source["Entry"].strip()
        actual_meaning = source["Meaning"].strip()
        canonical = reg["CanonicalWord"].strip()
        sense = reg["SenseLabel"].strip()
        decision = m["Decision"].strip()
        reasons: list[str] = []
        if norm(actual_word) != norm(canonical):
            reasons.append("surface-mismatch")
        if not meaning_overlap(actual_meaning, sense):
            reasons.append("meaning-overlap-low")
        if decision == "reuse-morphology":
            reasons.append("morphology-reuse")
        if reasons:
            flagged.append((key, nid, actual_word, actual_meaning, canonical, sense, "+".join(reasons)))

    print(f"Actual Grade-4 reuse audit: reused={len(mappings)}, flagged={len(flagged)}")
    for key, nid, word, meaning, canonical, sense, reason in flagged:
        print(f"REVIEW | {key} | {nid} | actual={word}:{meaning} | existing={canonical}:{sense} | {reason}")


if __name__ == "__main__":
    main()
