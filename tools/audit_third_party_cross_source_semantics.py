#!/usr/bin/env python3
"""Build context-rich semantic review queues for third-party Stage A exact overlaps.

The raw XLSX `Definition` field is dictionary-style and cannot prove textbook target
sense. For every Beijing/Renjiao exact surface overlap, this audit records local
source-order context from both adapters so sense-aware review can be performed.

No identities are merged by this tool.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
STAGE = BASE / "third_party_vocabulary" / "staging"
OCC_PATH = STAGE / "occurrences.csv"
SURFACE_PATH = STAGE / "cross_source_exact_overlap.csv"
BEIJING_SEMANTIC = BASE / "source_reference" / "beijing_start1_staging" / "semantic_resolution_review.csv"

FIELDS = [
    "MatchKey", "DisplayForms", "Definitions",
    "BeijingContexts", "RenjiaoContexts",
    "RiskSignals", "ReviewStatus", "ProposedDecision", "ProposedSense", "Rationale",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing input: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def row_num(row: dict[str, str]) -> int:
    try:
        return int(row.get("SourceRow", "0") or 0)
    except ValueError:
        return 0


def context_for(index: int, rows: list[dict[str, str]], radius: int = 2) -> str:
    lo = max(0, index - radius)
    hi = min(len(rows), index + radius + 1)
    parts: list[str] = []
    for i in range(lo, hi):
        word = rows[i].get("Word", "")
        parts.append(f"<{word}>" if i == index else word)
    r = rows[index]
    return f"{r.get('SourceBook','')}@r{r.get('SourceRow','')}:[" + " / ".join(parts) + "]"


def pos_count(definition: str) -> int:
    tags = set(re.findall(r"(?<![A-Za-z])(n|v|vt|vi|adj|adv|prep|conj|pron|int|art)\.", definition or "", flags=re.I))
    return len(tags)


def main() -> None:
    occurrences = read_csv(OCC_PATH)
    surfaces = read_csv(SURFACE_PATH)
    known_risk_keys: set[str] = set()
    if BEIJING_SEMANTIC.exists():
        for row in read_csv(BEIJING_SEMANTIC):
            key = row.get("MatchKey", "").strip()
            if key:
                known_risk_keys.add(key)

    by_book: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in occurrences:
        by_book[(row.get("SourceID", ""), row.get("SourceBook", ""))].append(row)
    for rows in by_book.values():
        rows.sort(key=row_num)

    contexts: dict[tuple[str, str], list[str]] = defaultdict(list)
    forms_by_key: dict[str, set[str]] = defaultdict(set)
    occurrences_by_source_key: dict[tuple[str, str], int] = defaultdict(int)
    for (source_id, _book), rows in by_book.items():
        for i, row in enumerate(rows):
            key = row.get("MatchKey", "")
            if not key:
                continue
            ctx = context_for(i, rows)
            if ctx not in contexts[(source_id, key)]:
                contexts[(source_id, key)].append(ctx)
            forms_by_key[key].add(row.get("Word", ""))
            occurrences_by_source_key[(source_id, key)] += 1

    review_rows: list[dict[str, str]] = []
    high_risk_rows: list[dict[str, str]] = []
    for surface in surfaces:
        key = surface.get("MatchKey", "")
        definition = surface.get("Definitions", "")
        signals: list[str] = []
        if key in known_risk_keys:
            signals.append("beijing-known-semantic-risk")
        if pos_count(definition) >= 2:
            signals.append("multi-pos-gloss")
        if len(forms_by_key.get(key, set())) > 1:
            signals.append("case-or-form-variant")
        if occurrences_by_source_key[("beijing_start1", key)] > 1 or occurrences_by_source_key[("renjiao_start1", key)] > 1:
            signals.append("multiple-occurrences")

        row = {
            "MatchKey": key,
            "DisplayForms": surface.get("DisplayForms", ""),
            "Definitions": definition,
            "BeijingContexts": " || ".join(contexts.get(("beijing_start1", key), [])),
            "RenjiaoContexts": " || ".join(contexts.get(("renjiao_start1", key), [])),
            "RiskSignals": "|".join(signals) if signals else "none-detected",
            "ReviewStatus": "pending",
            "ProposedDecision": "",
            "ProposedSense": "",
            "Rationale": "",
        }
        review_rows.append(row)
        if signals:
            high_risk_rows.append(row)

    write_csv(STAGE / "cross_source_context_review.csv", review_rows)
    write_csv(STAGE / "cross_source_semantic_risk_queue.csv", high_risk_rows)

    print(f"Cross-source exact-overlap review rows = {len(review_rows)}")
    print(f"Semantic-risk rows = {len(high_risk_rows)}")
    print("Identity merge executed = no")


if __name__ == "__main__":
    main()
