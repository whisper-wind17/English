#!/usr/bin/env python3
"""Audit Renjiao start1 new surfaces before third-party Identity minting.

The 403 surfaces that do not match the Beijing seed are not assumed to be 403
new Vocabulary identities. This audit separates lexical single tokens from
multiword routing cases, ordinal/form aliases, and expression-like chunks, and
adds occurrence neighborhoods for later sense review.

Stage A only: no ThirdPartyID and no Klose diff.
"""
from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
RENJIAO = BASE / "source_reference" / "renjiao_start1_staging"
STAGING = BASE / "third_party_vocabulary" / "staging"
NEW_SURFACES = RENJIAO / "new_surface_candidates.csv"
OCCURRENCES = RENJIAO / "occurrences.csv"
OUT = STAGING / "renjiao_new_surface_type_audit.csv"
RISK_OUT = STAGING / "renjiao_new_surface_semantic_risk_queue.csv"

FIELDS = [
    "MatchKey", "DisplayForms", "Definitions", "Books", "OccurrenceCount",
    "Contexts", "TokenCount", "RiskSignals", "CandidateType", "CandidateRoute",
    "RelatedMatchKeys", "ReviewStatus", "Rationale", "KloseMergeAuthorized",
]

ORDINAL_WORDS = {
    "1st": "first", "2nd": "second", "3rd": "third", "4th": "fourth",
    "5th": "fifth", "6th": "sixth", "7th": "seventh", "8th": "eighth",
    "9th": "ninth", "10th": "tenth", "11th": "eleventh", "12th": "twelfth",
    "13th": "thirteenth", "14th": "fourteenth", "15th": "fifteenth",
    "20th": "twentieth", "21st": "twenty-first", "22nd": "twenty-second",
    "23rd": "twenty-third", "24th": "twenty-fourth", "25th": "twenty-fifth",
}

PAST_OR_PARTICIPLE_START = {
    "ate", "bought", "cleaned", "climbed", "felt", "got", "had", "learned",
    "left", "lost", "made", "played", "started", "studied", "took", "visited",
    "was", "were", "went", "won",
}
GERUND_START = {
    "cleaning", "collecting", "cooking", "drawing", "making", "playing",
    "reading", "riding", "running", "shopping", "singing", "swimming", "writing",
}
# Some -ing-headed forms are lexical compounds rather than event/gerund chunks.
# They must stay eligible for Vocabulary phrase identity review.
LEXICAL_GERUND_COMPOUNDS = {
    "shopping centre",
    "shopping list",
    "shopping mall",
}
FUNCTION_PHRASE_START = {
    "a", "an", "at", "across", "after", "be", "by", "for", "from", "how",
    "in", "look", "next", "on", "out", "the", "to", "what", "where", "with",
}
POS_MARKERS = (" n.", " vt.", " vi.", " adj.", " adv.", " prep.", " pron.", " conj.", " art.", " num.", " int.")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def multi_pos(definition: str) -> bool:
    text = " " + (definition or "").lower()
    found = sum(marker in text for marker in POS_MARKERS)
    return found >= 2


def build_contexts(occurrences: list[dict[str, str]]) -> dict[str, list[str]]:
    by_book: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in occurrences:
        by_book[row["SourceBook"]].append(row)
    for rows in by_book.values():
        rows.sort(key=lambda r: int(r["SourceRow"]))

    contexts: dict[str, list[str]] = defaultdict(list)
    for book, rows in by_book.items():
        for idx, row in enumerate(rows):
            lo = max(0, idx - 2)
            hi = min(len(rows), idx + 3)
            words = []
            for j in range(lo, hi):
                w = rows[j]["Word"]
                words.append(f"<{w}>" if j == idx else w)
            contexts[row["MatchKey"]].append(
                f"{book}@r{row['SourceRow']}: [" + " / ".join(words) + "]"
            )
    return contexts


def classify(row: dict[str, str]) -> tuple[str, str, str, str, list[str]]:
    key = row["MatchKey"].strip()
    display = row["DisplayForms"].strip()
    definition = row["Definitions"].strip()
    tokens = key.split()
    signals: list[str] = []
    related = ""

    if int(row["OccurrenceCount"]) > 1:
        signals.append("multiple-occurrences")
    if multi_pos(definition):
        signals.append("multi-pos-gloss")
    if not definition or definition == "无":
        signals.append("missing-or-empty-gloss")

    if re.fullmatch(r"\d+(?:st|nd|rd|th)", key):
        signals.append("numeric-ordinal-form")
        related = ORDINAL_WORDS.get(key, "")
        return (
            "ordinal-format-alias-review", "identity-alias-review", related,
            "Numeric ordinal spelling is a form/alias candidate, not automatically a new learning unit.", signals,
        )

    if len(tokens) == 1:
        if "'" in key or "’" in display:
            signals.append("contracted-form")
            return (
                "single-token-form-review", "identity-form-review", related,
                "Single-token contraction/form needs identity-policy review before treating it as a new Vocabulary identity.", signals,
            )
        return (
            "single-token-lexical-review", "vocabulary-identity-review", related,
            "Single-token lexical candidate; target sense still requires source-context review.", signals,
        )

    signals.append("multiword-surface")
    first = tokens[0]
    has_sentence_punct = any(ch in display for ch in "!?…")
    if first in PAST_OR_PARTICIPLE_START:
        signals.append("inflected-event-chunk")
        return (
            "expression-or-chunk-review", "expression-routing-review", related,
            "Past/participle-led multiword chunk is not presumed to be a Vocabulary identity.", signals,
        )
    if key in LEXICAL_GERUND_COMPOUNDS:
        return (
            "multiword-lexical-review", "vocabulary-vs-expression-review", related,
            "Known -ing-headed lexical compound; keep it in Vocabulary phrase identity review rather than treating it as an event chunk.", signals,
        )
    if first in GERUND_START:
        signals.append("gerund-chunk")
        return (
            "expression-or-chunk-review", "expression-routing-review", related,
            "Gerund-led multiword chunk requires Vocabulary-vs-Expression routing.", signals,
        )
    if has_sentence_punct:
        signals.append("sentence-punctuation")
        return (
            "expression-or-chunk-review", "expression-routing-review", related,
            "Punctuated multiword item is expression-like and must not auto-enter Vocabulary.", signals,
        )
    if first in FUNCTION_PHRASE_START:
        signals.append("function-or-construction-phrase")
        return (
            "multiword-routing-review", "vocabulary-vs-expression-review", related,
            "Function/construction-led phrase may be a lexical phrase or an Expression; route explicitly.", signals,
        )
    return (
        "multiword-lexical-review", "vocabulary-vs-expression-review", related,
        "Multiword item may be a legitimate lexical unit/proper name, but must be reviewed before Vocabulary identity minting.", signals,
    )


def main() -> None:
    surfaces = read_csv(NEW_SURFACES)
    occurrences = read_csv(OCCURRENCES)
    if len(surfaces) != 403:
        raise SystemExit(f"Expected 403 Renjiao new surfaces, found {len(surfaces)}")
    contexts = build_contexts(occurrences)

    out: list[dict[str, str]] = []
    for row in surfaces:
        ctype, route, related, rationale, signals = classify(row)
        key = row["MatchKey"]
        out.append({
            "MatchKey": key,
            "DisplayForms": row["DisplayForms"],
            "Definitions": row["Definitions"],
            "Books": row["Books"],
            "OccurrenceCount": row["OccurrenceCount"],
            "Contexts": " || ".join(contexts.get(key, [])),
            "TokenCount": str(len(key.split())),
            "RiskSignals": "|".join(signals) if signals else "none-detected",
            "CandidateType": ctype,
            "CandidateRoute": route,
            "RelatedMatchKeys": related,
            "ReviewStatus": "pending",
            "Rationale": rationale,
            "KloseMergeAuthorized": "no",
        })

    write_csv(OUT, out)
    risky = [r for r in out if r["RiskSignals"] != "none-detected" or r["CandidateType"] != "single-token-lexical-review"]
    write_csv(RISK_OUT, risky)

    type_counts = Counter(r["CandidateType"] for r in out)
    print(f"Renjiao new-surface audit rows = {len(out)}")
    for key in sorted(type_counts):
        print(f"type {key} = {type_counts[key]}")
    print(f"new-surface risk/routing queue = {len(risky)}")
    print("ThirdPartyID minted = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
