#!/usr/bin/env python3
"""Resolve the final seven Beijing + Renjiao exact-overlap pending rows.

Six rows have aligned elementary target senses and are model-reviewed for
Stage-A reuse. `stay` remains explicitly held because the source neighborhoods
are insufficient to source-confirm one shared usage. This script never mints a
ThirdPartyID and never performs the final Klose diff.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "anki" / "klose" / "third_party_vocabulary" / "staging" / "cross_source_identity_resolution.csv"

FINAL_DECISIONS = {
    "farm": (
        "reuse-learning-unit", "high", "农场",
        "Both source neighborhoods use farm as the place/agricultural noun; broad verb glosses are dictionary noise for these occurrences.",
    ),
    "fast": (
        "reuse-learning-unit", "medium", "快的；快地",
        "Both neighborhoods are compatible with elementary speed usage. Adjective/adverb presentation does not justify separate learning identities here.",
    ),
    "hear": (
        "reuse-learning-unit", "medium", "听见；听到",
        "Both source neighborhoods support the elementary perception verb hear; no distinct target sense is evidenced.",
    ),
    "supermarket": (
        "reuse-learning-unit", "high", "超市",
        "Both sources clearly use supermarket as the place noun.",
    ),
    "yellow": (
        "reuse-learning-unit", "high", "黄色；黄色的",
        "Both neighborhoods are colour vocabulary; noun/adjective presentation is one elementary colour learning unit.",
    ),
    "yes": (
        "reuse-learning-unit", "high", "是；是的",
        "Both sources use yes as the affirmative response item.",
    ),
    "stay": (
        "held-source-context-required", "medium", "",
        "Both sources contain stay, but the adjacent word-list context does not source-confirm the same construction/target usage. Keep held rather than force reuse.",
    ),
}

FIELDS = [
    "MatchKey", "DisplayForms", "Definitions", "BeijingContexts", "RenjiaoContexts",
    "RiskSignals", "ProposedDecision", "ResolutionStatus", "Confidence",
    "ProposedSense", "ResolutionBasis", "Rationale", "KloseMergeAuthorized",
]


def main() -> None:
    with PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    by_key = {r["MatchKey"]: r for r in rows}
    pending = {r["MatchKey"] for r in rows if r["ResolutionStatus"] == "pending"}
    if pending != set(FINAL_DECISIONS):
        raise SystemExit(f"Unexpected final pending set: {sorted(pending)}")

    for key, (decision, confidence, sense, rationale) in FINAL_DECISIONS.items():
        row = by_key[key]
        row.update({
            "ProposedDecision": decision,
            "ResolutionStatus": "model-reviewed",
            "Confidence": confidence,
            "ProposedSense": sense,
            "ResolutionBasis": "model-final-pass-source-neighborhood-review",
            "Rationale": rationale,
            "KloseMergeAuthorized": "no",
        })

    with PATH.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    statuses = Counter(r["ResolutionStatus"] for r in rows)
    decisions = Counter(r["ProposedDecision"] for r in rows)
    print("Final cross-source pending reviewed = 7")
    print(f"Final-pass reuse = {sum(v[0] == 'reuse-learning-unit' for v in FINAL_DECISIONS.values())}")
    print(f"Final-pass held = {sum(v[0].startswith('held-') for v in FINAL_DECISIONS.values())}")
    for key in sorted(statuses):
        print(f"status {key} = {statuses[key]}")
    for key in sorted(decisions):
        print(f"decision {key} = {decisions[key]}")
    print("Stable ThirdPartyID minted = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
