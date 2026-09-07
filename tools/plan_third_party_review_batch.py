#!/usr/bin/env python3
"""Plan the next deterministic high-throughput Stage-A review batch.

The normalized review bundle remains derived-only. This planner selects one active
lane at a time, preserving bundle order while enforcing both a surface-count cap
and an evidence-weight budget. The resulting next_batch.json is a review plan, not
content-decision truth.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
BUNDLE = TP / "audit" / "review_bundle.csv"
OUT = TP / "audit" / "next_batch.json"
PLAN_VERSION = "v3"

LANE_ORDER = [
    "source-reconciliation-needed",
    "policy-executable",
    "policy-review",
    "actionable-semantic",
    "semantic-review",
    "split-resolution",
    "object-boundary",
]

LIMITS = {
    "source-reconciliation-needed": (15, 40),
    "policy-executable": (80, 120),
    "policy-review": (30, 60),
    "actionable-semantic": (50, 90),
    "semantic-review": (30, 60),
    "split-resolution": (25, 70),
    "object-boundary": (25, 50),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing review bundle: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def evidence_weight(row: dict[str, str]) -> int:
    occ = max(1, int(row.get("OccurrenceCount", "1") or 1))
    sources = max(1, len([x for x in row.get("SourceIDs", "").split("|") if x]))
    weight = 1 + max(0, occ - 1) + max(0, sources - 1)
    if row.get("ReviewLane") == "split-resolution":
        weight += 2
    if row.get("CandidateCanonical", ""):
        weight += 1
    evidence_len = len(row.get("OccurrenceEvidenceJSON", ""))
    weight += max(0, math.ceil(evidence_len / 4000) - 1)
    return weight


def bundle_fingerprint(rows: list[dict[str, str]]) -> str:
    payload = [
        {
            "MatchKey": row.get("MatchKey", ""),
            "ReviewLane": row.get("ReviewLane", ""),
            "ActionabilityScore": row.get("ActionabilityScore", ""),
            "OccurrenceCount": row.get("OccurrenceCount", ""),
            "CandidateCanonical": row.get("CandidateCanonical", ""),
            "CurrentAction": row.get("CurrentAction", ""),
            "CurrentStatus": row.get("CurrentStatus", ""),
            "CurrentDecisionBasis": row.get("CurrentDecisionBasis", ""),
            "OccurrenceEvidenceJSON": row.get("OccurrenceEvidenceJSON", ""),
        }
        for row in rows
    ]
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main() -> None:
    rows = read_csv(BUNDLE)
    selected_lane = ""
    lane_rows: list[dict[str, str]] = []
    for lane in LANE_ORDER:
        candidates = [row for row in rows if row.get("ReviewLane") == lane]
        if candidates:
            selected_lane = lane
            lane_rows = candidates
            break

    selected: list[dict[str, str]] = []
    total_weight = 0
    surface_cap = 0
    weight_budget = 0
    if selected_lane:
        surface_cap, weight_budget = LIMITS[selected_lane]
        for row in lane_rows:
            weight = evidence_weight(row)
            if selected and (len(selected) >= surface_cap or total_weight + weight > weight_budget):
                break
            selected.append(row)
            total_weight += weight
            if len(selected) >= surface_cap:
                break

    plan = {
        "PlanVersion": PLAN_VERSION,
        "ReviewLane": selected_lane,
        "SelectedMatchKeys": [row["MatchKey"] for row in selected],
        "SelectedCount": len(selected),
        "EvidenceWeight": total_weight,
        "SurfaceCap": surface_cap,
        "WeightBudget": weight_budget,
        "ReviewBundleFingerprint": bundle_fingerprint(rows),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"review batch plan version = {PLAN_VERSION}")
    print(f"review batch lane = {selected_lane or 'none'}")
    print(f"review batch selected surfaces = {len(selected)}")
    print(f"review batch evidence weight = {total_weight} / {weight_budget}")
    print(f"review batch surface cap = {surface_cap}")
    print("review batch selection = deterministic")
    print("review batch decision truth = derived-only")


if __name__ == "__main__":
    main()
