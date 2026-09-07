#!/usr/bin/env python3
"""Retire already-audited Stage-A blockers from active review lanes.

The review bundle is derived-only. A held decision whose DecisionBasis explicitly
contains ``audited-defer`` has already completed its current evidence review and
must not be scheduled again until source evidence invalidates/requeues it.

This post-processing step does not change identity_decisions.csv, blocker counts,
or release state; it only keeps active-lane throughput honest.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "anki" / "klose" / "third_party_vocabulary" / "audit" / "review_bundle.csv"

ACTIVE_REVIEW_LANES = {
    "policy-review",
    "object-boundary",
    "actionable-semantic",
    "semantic-review",
}


def main() -> None:
    if not BUNDLE.exists():
        raise SystemExit(f"Missing review bundle: {BUNDLE}")

    with BUNDLE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        rows = list(reader)

    retired: list[str] = []
    for row in rows:
        if row.get("ReviewLane") not in ACTIVE_REVIEW_LANES:
            continue
        if row.get("CurrentStatus") != "held":
            continue
        basis = row.get("CurrentDecisionBasis", "").casefold()
        if "audited-defer" not in basis:
            continue
        row["ReviewLane"] = "deferred-high-ambiguity"
        row["RecommendedBatchSize"] = "0"
        row["PolicyRecommendedAction"] = "defer"
        row["DeferReason"] = (
            "current evidence already audited; do not rescan until source evidence requeues the decision"
        )
        retired.append(row["MatchKey"])

    rows.sort(key=lambda row: (
        1 if row["ReviewLane"] == "deferred-high-ambiguity" else 0,
        -int(row["ActionabilityScore"]),
        int(row["AuditPriority"]),
        row["MatchKey"],
    ))

    with BUNDLE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    stale = [
        row["MatchKey"] for row in rows
        if row["ReviewLane"] in ACTIVE_REVIEW_LANES
        and row.get("CurrentStatus") == "held"
        and "audited-defer" in row.get("CurrentDecisionBasis", "").casefold()
    ]
    if stale:
        raise SystemExit("Audited defer leaked into active review lanes: " + ", ".join(stale[:20]))

    counts = Counter(row["ReviewLane"] for row in rows)
    print(f"audited defer rows retired from active lanes = {len(retired)}")
    print("retired MatchKeys = " + ("|".join(retired) if retired else "none"))
    for lane in sorted(counts):
        print(f"normalized review bundle lane {lane} = {counts[lane]}")
    print("review lane normalization = pass")
    print("identity decision truth changed = no")


if __name__ == "__main__":
    main()
