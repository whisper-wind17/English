#!/usr/bin/env python3
"""One-time Waiyan start1 exact-surface evidence revalidation.

This helper is intentionally temporary. It does NOT create semantic decisions for
new surfaces. It only takes durable Stage-A decisions that were explicitly
reviewed before waiyan_start1 was enabled and rebinds the same decision to the
current occurrence set when the only reason the surface is pending is added exact
MatchKey evidence.

The helper writes the normal transient decision_updates.csv inbox; the generic
apply/build/check pipeline remains authoritative. Remove this helper after the
Waiyan start1 revalidation migration is complete.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
CONFIG = TP / "config" / "source_adapters.csv"
DECISIONS = TP / "review" / "identity_decisions.csv"
UPDATES = TP / "review" / "decision_updates.csv"
EXPECTED = 797
FIELDS = [
    "DecisionKey", "MatchKey", "OccurrenceKeys", "Action", "CanonicalMatchKey",
    "ObjectType", "TargetSense", "Status", "Confidence", "DecisionBasis", "Rationale",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def decode(raw: str) -> set[str]:
    value = json.loads(raw)
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
        raise SystemExit("Invalid durable OccurrenceKeys")
    return set(value)


def current_occurrences() -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for cfg in read_csv(CONFIG):
        if cfg.get("Enabled", "").lower() != "yes":
            continue
        path = ROOT / cfg["OccurrencesPath"]
        source_id = cfg["SourceID"]
        for row in read_csv(path):
            if row.get("SourceID") != source_id:
                raise SystemExit(f"SourceID mismatch: {path}")
            result[row["MatchKey"]].add(row["SourceOccurrenceKey"])
    return result


def main() -> None:
    current = current_occurrences()
    decisions = read_csv(DECISIONS)
    by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decisions:
        by_match[row["MatchKey"]].append(row)

    updates: list[dict[str, str]] = []
    for match_key, rows in sorted(by_match.items()):
        if len(rows) != 1:
            continue
        row = rows[0]
        reviewed = decode(row["OccurrenceKeys"])
        now = current.get(match_key, set())
        if not now or reviewed == now:
            continue
        added = now - reviewed
        removed = reviewed - now
        if removed:
            raise SystemExit(f"Revalidation refuses removed evidence: {match_key}")
        # This migration is only for evidence added by waiyan_start1 exact MatchKey rows.
        if not added or not all(key.startswith("waiyan_start1|") for key in added):
            continue
        if row["Action"] == "pending" or row["Status"] == "pending":
            raise SystemExit(f"Cannot auto-revalidate previously pending decision: {match_key}")
        rationale = row.get("Rationale", "").strip()
        suffix = (
            " Waiyan start1 adds exact-MatchKey source occurrences; this previously explicit "
            "Stage-A decision is revalidated for the expanded five-adapter evidence set."
        )
        updates.append({
            "DecisionKey": row["DecisionKey"],
            "MatchKey": match_key,
            "OccurrenceKeys": "*",
            "Action": row["Action"],
            "CanonicalMatchKey": row.get("CanonicalMatchKey", ""),
            "ObjectType": row.get("ObjectType", ""),
            "TargetSense": row.get("TargetSense", ""),
            "Status": row["Status"],
            "Confidence": row.get("Confidence", ""),
            "DecisionBasis": "waiyan-start1-exact-surface-evidence-revalidation",
            "Rationale": (rationale + suffix).strip(),
        })

    if len(updates) != EXPECTED:
        raise SystemExit(f"Expected {EXPECTED} Waiyan evidence-changed decisions, found {len(updates)}")

    with UPDATES.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(updates)

    print(f"Waiyan existing-surface decisions revalidated = {len(updates)}")
    print("new Waiyan-only surfaces decided here = 0")
    print("semantic Action/TargetSense changed here = no")
    print("transient inbox written = yes")


if __name__ == "__main__":
    main()
