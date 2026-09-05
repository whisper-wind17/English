#!/usr/bin/env python3
"""Audit actual Grade-4 items that reuse legacy vocabulary identities.

The batch matcher may reuse an existing identity when the actual textbook has a
wording or morphology difference. Every risky reuse must either be genuinely
same-sense or be explicitly reconciled by the committed actual-textbook fact
overlay. Unresolved reuse is a build error; this script never mutates identity.
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
RESOLVED_OVERRIDES = BASE / "master" / "actual_grade4_reuse_fact_overrides.csv"


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
    return len(a) == 1 and len(b) == 1 and a == b


def main() -> None:
    for path in (ACTUAL, LEGACY, EXT, MAPPINGS, RESOLVED_OVERRIDES):
        if not path.exists():
            raise SystemExit(f"Missing Grade-4 reuse audit input: {path.relative_to(ROOT)}")

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

    resolved: dict[str, dict[str, str]] = {}
    for row in read_csv(RESOLVED_OVERRIDES):
        nid = row.get("NoteID", "").strip()
        if not nid or nid in resolved:
            raise SystemExit(f"Invalid/duplicate resolved reuse override: {nid!r}")
        resolved[nid] = row

    flagged: list[tuple[str, str, str, str, str, str, str]] = []
    resolved_count = 0
    reuse_ids = {m["NoteID"].strip() for m in mappings}
    extra_resolutions = sorted(set(resolved) - reuse_ids)
    if extra_resolutions:
        raise SystemExit(f"Reuse resolution references non-reused NoteID(s): {extra_resolutions}")

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

        if reasons and nid in resolved:
            override = resolved[nid]
            if (
                norm(override.get("Word", "")) == norm(actual_word)
                and override.get("MeaningPrimary", "").strip() == actual_meaning
            ):
                resolved_count += 1
                continue
            reasons.append("resolution-does-not-match-source")

        if reasons:
            flagged.append((key, nid, actual_word, actual_meaning, canonical, sense, "+".join(reasons)))

    print(
        f"Actual Grade-4 reuse audit: reused={len(mappings)}, "
        f"explicitly_resolved={resolved_count}, unresolved={len(flagged)}"
    )
    for key, nid, word, meaning, canonical, sense, reason in flagged:
        print(f"REVIEW | {key} | {nid} | actual={word}:{meaning} | existing={canonical}:{sense} | {reason}")
    if flagged:
        raise SystemExit(f"Unresolved actual Grade-4 reused identities: {len(flagged)}")


if __name__ == "__main__":
    main()
