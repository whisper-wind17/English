#!/usr/bin/env python3
"""Build a compact, evidence-rich review bundle for third-party Stage-A blockers.

This file is a generated audit aid only. `identity_decisions.csv` remains the only
content-decision truth; `review_queue.csv` remains the blocker set. The bundle adds
triage class, priority and source-neighborhood evidence so 30-50 blockers can be
reviewed in one model pass without repeated repository lookups.
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
STAGING = TP / "staging"
DECISIONS = TP / "review" / "identity_decisions.csv"
OCCURRENCES = STAGING / "occurrences.csv"
REVIEW_QUEUE = STAGING / "review_queue.csv"
OUT = STAGING / "review_bundle.csv"

FIELDS = [
    "AuditPriority",
    "BlockerClass",
    "MatchKey",
    "DisplayForms",
    "Definitions",
    "SourceIDs",
    "SourceBooks",
    "OccurrenceCount",
    "CandidateSignals",
    "CurrentAction",
    "CurrentStatus",
    "CurrentConfidence",
    "CurrentDecisionBasis",
    "CurrentRationale",
    "OccurrenceEvidenceJSON",
]

FUNCTIONAL_POLYSEMY = {
    "a", "about", "after", "all", "as", "at", "back", "before", "by", "can",
    "could", "do", "for", "from", "have", "in", "like", "may", "of", "on",
    "one", "out", "over", "right", "so", "some", "that", "the", "to", "up",
    "with", "would",
}

ABBREVIATION_KEYS = {
    "a.m.", "am", "cd", "p.m.", "pm", "ps", "rsvp", "u.k.", "u.s.a.",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def classify(row: dict[str, str], decision_text: str) -> tuple[int, str]:
    key = row["MatchKey"].strip().casefold()
    action = row.get("DecisionAction", "")
    signals = {x for x in row.get("CandidateSignals", "").split("|") if x}
    definitions = row.get("Definitions", "").casefold()
    text = decision_text.casefold()

    if action == "split-required":
        return 30, "split-resolution"

    abbreviation = (
        key in ABBREVIATION_KEYS
        or "abbr." in definitions
        or "abbreviation" in text
        or "abbrev" in text
    )
    if abbreviation:
        return 70, "abbreviation-policy"

    form_markers = (
        "morphology" in signals
        or any(token in text for token in (
            "irregular-form", "form-policy", "inflected form", "past form",
            "past tense", "past participle", "plural-form", "contraction",
            "contracted grammatical form", "gerund-form", "form boundary",
        ))
    )
    if form_markers:
        return 60, "form-policy"

    if key in FUNCTIONAL_POLYSEMY:
        return 80, "functional-polysemy"

    if "multiword" in signals:
        return 45, "multiword-object-boundary"

    source_ids = [x for x in row.get("SourceIDs", "").split("|") if x]
    occ_count = int(row.get("OccurrenceCount", "0") or 0)
    if len(source_ids) == 1 and occ_count == 1:
        return 10, "semantic-easy"
    if len(source_ids) > 1:
        return 20, "semantic-cross-source"
    return 40, "semantic-hard"


def main() -> None:
    occ = read_csv(OCCURRENCES)
    review = read_csv(REVIEW_QUEUE)
    decisions = read_csv(DECISIONS)

    decisions_by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decisions:
        decisions_by_match[row["MatchKey"]].append(row)

    # Preserve adapter/source ordering from occurrences.csv. Neighborhoods are
    # constrained to the same SourceID + SourceBook so they never cross books.
    book_rows: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in occ:
        book_rows[(row["SourceID"], row["SourceBook"])].append(row)

    position: dict[str, tuple[list[dict[str, str]], int]] = {}
    for rows in book_rows.values():
        for i, row in enumerate(rows):
            position[row["SourceOccurrenceKey"]] = (rows, i)

    occ_by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in occ:
        occ_by_match[row["MatchKey"]].append(row)

    bundle: list[dict[str, str]] = []
    for blocker in review:
        key = blocker["MatchKey"]
        ds = decisions_by_match.get(key, [])
        basis = " || ".join(dict.fromkeys(d.get("DecisionBasis", "") for d in ds if d.get("DecisionBasis")))
        rationale = " || ".join(dict.fromkeys(d.get("Rationale", "") for d in ds if d.get("Rationale")))
        confidence = "|".join(dict.fromkeys(d.get("Confidence", "") for d in ds if d.get("Confidence")))
        decision_text = " ".join([basis, rationale])
        priority, blocker_class = classify(blocker, decision_text)

        evidence: list[dict[str, object]] = []
        for occurrence in occ_by_match.get(key, []):
            rows, idx = position[occurrence["SourceOccurrenceKey"]]
            before = [r["Word"] for r in rows[max(0, idx - 8):idx]]
            after = [r["Word"] for r in rows[idx + 1:idx + 9]]
            evidence.append({
                "SourceOccurrenceKey": occurrence["SourceOccurrenceKey"],
                "SourceID": occurrence["SourceID"],
                "SourceBook": occurrence["SourceBook"],
                "Grade": occurrence.get("Grade", ""),
                "Semester": occurrence.get("Semester", ""),
                "SourceRow": occurrence.get("SourceRow", ""),
                "Word": occurrence.get("Word", ""),
                "Definition": occurrence.get("Definition", ""),
                "Before": before,
                "After": after,
            })

        bundle.append({
            "AuditPriority": f"{priority:02d}",
            "BlockerClass": blocker_class,
            "MatchKey": key,
            "DisplayForms": blocker.get("DisplayForms", ""),
            "Definitions": blocker.get("Definitions", ""),
            "SourceIDs": blocker.get("SourceIDs", ""),
            "SourceBooks": blocker.get("SourceBooks", ""),
            "OccurrenceCount": blocker.get("OccurrenceCount", ""),
            "CandidateSignals": blocker.get("CandidateSignals", ""),
            "CurrentAction": blocker.get("DecisionAction", ""),
            "CurrentStatus": blocker.get("DecisionStatus", ""),
            "CurrentConfidence": confidence,
            "CurrentDecisionBasis": basis,
            "CurrentRationale": rationale,
            "OccurrenceEvidenceJSON": json.dumps(evidence, ensure_ascii=False, separators=(",", ":")),
        })

    bundle.sort(key=lambda r: (int(r["AuditPriority"]), r["MatchKey"]))
    write_csv(OUT, bundle)

    counts: dict[str, int] = defaultdict(int)
    for row in bundle:
        counts[row["BlockerClass"]] += 1
    print(f"review bundle blockers = {len(bundle)}")
    for name in sorted(counts):
        print(f"review bundle {name} = {counts[name]}")
    print("review bundle neighborhood radius = 8")
    print("review bundle decision truth = derived-only")


if __name__ == "__main__":
    main()
