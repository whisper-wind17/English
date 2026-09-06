#!/usr/bin/env python3
"""One-time migration safety fix for simplified third-party identity decisions.

Only untouched Beijing seed carry-forward rows are affected. Multiword or
sentence-like surfaces were never object-routed, so they must return to the
single unified review queue instead of being assumed Vocabulary identities.
This script is temporary migration tooling and should be removed after the
corrected decision file is committed.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "anki" / "klose" / "third_party_vocabulary" / "review" / "identity_decisions.csv"


def main() -> None:
    with PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys()) if rows else []

    changed: list[str] = []
    for row in rows:
        if row.get("DecisionBasis") != "beijing-seed-carried-forward":
            continue
        key = row.get("MatchKey", "")
        if " " not in key and not re.search(r"[?!]|\.{2,}|…", key):
            continue
        row.update({
            "Action": "pending",
            "CanonicalMatchKey": "",
            "ObjectType": "vocabulary",
            "TargetSense": "",
            "Status": "pending",
            "Confidence": "",
            "DecisionBasis": "beijing-seed-object-review-required",
            "Rationale": (
                "Beijing seed multiword/sentence-like surface was not previously routed as Vocabulary vs Expression/source-only. "
                "Return it to the single unified review queue; do not infer object type from seed order."
            ),
        })
        changed.append(key)

    with PATH.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"Normalized Beijing carried-forward multiword decisions = {len(changed)}")
    print("keys = " + ("|".join(changed) if changed else "none"))


if __name__ == "__main__":
    main()
