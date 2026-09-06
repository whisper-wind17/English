#!/usr/bin/env python3
"""Resolve object routing for Renjiao start1 new surfaces.

This is still Stage A and intentionally stops before ThirdPartyID minting.
It converts the 403 mixed new surfaces into explicit provisional object
routing: Vocabulary candidate, canonical-form alias, Expression candidate,
non-identity source chunk, or a held/pending review queue.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
STAGING = BASE / "third_party_vocabulary" / "staging"
INPUT = STAGING / "renjiao_new_surface_type_audit.csv"
OUTPUT = STAGING / "renjiao_new_surface_route_resolution.csv"
REVIEW_QUEUE = STAGING / "renjiao_new_surface_identity_review_queue.csv"

FIELDS = [
    "MatchKey", "DisplayForms", "Definitions", "Books", "OccurrenceCount",
    "Contexts", "RiskSignals", "CandidateType", "CandidateRoute",
    "ProposedObjectDecision", "ResolutionStatus", "Confidence",
    "TargetReference", "ResolutionBasis", "Rationale", "KloseMergeAuthorized",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def resolve(row: dict[str, str]) -> tuple[str, str, str, str, str, str]:
    key = row["MatchKey"]
    ctype = row["CandidateType"]
    signals = set(filter(None, row["RiskSignals"].split("|")))

    if ctype == "ordinal-format-alias-review":
        return (
            "canonical-form-alias-candidate", "rule-reviewed", "high",
            row["RelatedMatchKeys"], "numeric-ordinal-alias",
            "Numeric ordinal and written ordinal represent the same ordinal concept; keep one identity candidate and preserve the numeric form as source/presentation evidence.",
        )

    if ctype == "single-token-form-review":
        if key == "let's":
            return (
                "route-expression-candidate", "model-reviewed", "high", "",
                "communicative-contraction-routing",
                "Let's is primarily a communicative proposal frame ('Let's ...'), so it should not mint an isolated Vocabulary identity in this corpus pass.",
            )
        return (
            "held-identity-form-policy", "model-reviewed", "medium", "",
            "contracted-form-policy-blocker",
            "The contracted form carries grammatical/negation information beyond a simple spelling alias; keep held until the Vocabulary form policy is explicit.",
        )

    if ctype == "expression-or-chunk-review":
        if "sentence-punctuation" in signals:
            return (
                "route-expression-candidate", "rule-reviewed", "high", "",
                "punctuated-communicative-item",
                "Punctuated communicative item belongs in Expression candidate routing rather than isolated Vocabulary identity minting.",
            )
        return (
            "route-source-chunk-no-vocabulary-identity", "rule-reviewed", "high", "",
            "inflected-or-gerund-source-chunk",
            "Inflected/event chunk remains preserved as Source Fact but is not treated as a standalone Vocabulary learning unit.",
        )

    if ctype == "single-token-lexical-review":
        if row["RiskSignals"] == "none-detected":
            return (
                "new-vocabulary-learning-unit-candidate", "rule-reviewed", "high", "",
                "single-token-no-detected-sense-risk",
                "Unique single-token lexical surface with no detected within-source repetition, multi-POS, form, or missing-gloss risk. This is provisional Stage-A candidacy, not stable identity minting.",
            )
        return (
            "pending-vocabulary-sense-review", "pending", "", "",
            "single-token-semantic-risk",
            "Single-token surface has repeated-occurrence and/or broad semantic/POS signals; review target sense before identity minting.",
        )

    if ctype == "multiword-lexical-review":
        return (
            "pending-vocabulary-phrase-sense-review", "pending", "", "",
            "multiword-lexical-unit-review",
            "Potential lexical phrase/proper-name learning unit; confirm that it is a stable Vocabulary unit rather than a compositional/source-only chunk.",
        )

    if ctype == "multiword-routing-review":
        return (
            "pending-vocabulary-vs-expression-review", "pending", "", "",
            "multiword-object-type-review",
            "Phrase can be lexical Vocabulary or a communicative/grammatical Expression; route by learning objective before identity minting.",
        )

    raise SystemExit(f"Unhandled CandidateType for {key}: {ctype}")


def main() -> None:
    source = read_csv(INPUT)
    if len(source) != 403:
        raise SystemExit(f"Expected 403 type-audit rows, found {len(source)}")

    out: list[dict[str, str]] = []
    for row in source:
        decision, status, confidence, target, basis, rationale = resolve(row)
        out.append({
            "MatchKey": row["MatchKey"],
            "DisplayForms": row["DisplayForms"],
            "Definitions": row["Definitions"],
            "Books": row["Books"],
            "OccurrenceCount": row["OccurrenceCount"],
            "Contexts": row["Contexts"],
            "RiskSignals": row["RiskSignals"],
            "CandidateType": row["CandidateType"],
            "CandidateRoute": row["CandidateRoute"],
            "ProposedObjectDecision": decision,
            "ResolutionStatus": status,
            "Confidence": confidence,
            "TargetReference": target,
            "ResolutionBasis": basis,
            "Rationale": rationale,
            "KloseMergeAuthorized": "no",
        })

    write_csv(OUTPUT, out)
    queue = [r for r in out if r["ResolutionStatus"] == "pending" or r["ProposedObjectDecision"].startswith("held-")]
    write_csv(REVIEW_QUEUE, queue)

    statuses = Counter(r["ResolutionStatus"] for r in out)
    decisions = Counter(r["ProposedObjectDecision"] for r in out)
    print(f"Renjiao new-surface route rows = {len(out)}")
    for key in sorted(statuses):
        print(f"status {key} = {statuses[key]}")
    for key in sorted(decisions):
        print(f"decision {key} = {decisions[key]}")
    print(f"identity/object review queue = {len(queue)}")
    print("ThirdPartyID minted = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
