#!/usr/bin/env python3
"""Merge one-time reviewed decision updates into the durable identity decision truth.

`review/decision_updates.csv` is a transient inbox, not a second state store. This
utility replaces/appends rows by DecisionKey, validates the decision schema, writes
`identity_decisions.csv`, then deletes the inbox so the long-term review directory
returns to containing only the durable truth file.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "anki" / "klose" / "third_party_vocabulary" / "review"
DECISIONS = REVIEW / "identity_decisions.csv"
UPDATES = REVIEW / "decision_updates.csv"

FIELDS = [
    "DecisionKey", "MatchKey", "OccurrenceKeys", "Action", "CanonicalMatchKey",
    "ObjectType", "TargetSense", "Status", "Confidence", "DecisionBasis", "Rationale",
]
ACTIONS = {
    "keep-identity", "reuse-identity", "split-required", "held",
    "route-expression", "source-only", "pending",
}
STATUSES = {"reviewed", "held", "pending"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def validate(row: dict[str, str], *, source: str) -> None:
    missing = [f for f in FIELDS if f not in row]
    if missing:
        raise SystemExit(f"{source}: missing fields {missing}")
    if not row["DecisionKey"] or not row["MatchKey"]:
        raise SystemExit(f"{source}: empty DecisionKey/MatchKey")
    if row["Action"] not in ACTIONS:
        raise SystemExit(f"{source}: invalid Action {row['Action']} for {row['DecisionKey']}")
    if row["Status"] not in STATUSES:
        raise SystemExit(f"{source}: invalid Status {row['Status']} for {row['DecisionKey']}")
    if row["Action"] == "reuse-identity" and not row["CanonicalMatchKey"]:
        raise SystemExit(f"{source}: reuse-identity lacks CanonicalMatchKey for {row['DecisionKey']}")
    if row["Action"] == "route-expression" and row["ObjectType"] != "expression":
        raise SystemExit(f"{source}: route-expression requires ObjectType=expression for {row['DecisionKey']}")
    if row["Action"] == "source-only" and row["ObjectType"] != "source-only":
        raise SystemExit(f"{source}: source-only requires ObjectType=source-only for {row['DecisionKey']}")


def main() -> None:
    if not UPDATES.exists():
        print("decision updates = none")
        return
    if not DECISIONS.exists():
        raise SystemExit(f"Missing durable decision truth: {DECISIONS}")

    current = read_csv(DECISIONS)
    updates = read_csv(UPDATES)
    if not updates:
        raise SystemExit("decision_updates.csv is empty")

    by_key: dict[str, dict[str, str]] = {}
    order: list[str] = []
    for row in current:
        validate(row, source="identity_decisions")
        key = row["DecisionKey"]
        if key in by_key:
            raise SystemExit(f"Duplicate durable DecisionKey: {key}")
        by_key[key] = {f: row.get(f, "") for f in FIELDS}
        order.append(key)

    seen_updates: set[str] = set()
    replaced = 0
    appended = 0
    for row in updates:
        validate(row, source="decision_updates")
        key = row["DecisionKey"]
        if key in seen_updates:
            raise SystemExit(f"Duplicate update DecisionKey: {key}")
        seen_updates.add(key)
        normalized = {f: row.get(f, "") for f in FIELDS}
        if key in by_key:
            if by_key[key]["MatchKey"] != normalized["MatchKey"]:
                raise SystemExit(f"Update changes MatchKey for existing DecisionKey: {key}")
            by_key[key] = normalized
            replaced += 1
        else:
            by_key[key] = normalized
            order.append(key)
            appended += 1

    with DECISIONS.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for key in order:
            w.writerow(by_key[key])

    UPDATES.unlink()
    print(f"decision updates applied = {len(updates)}")
    print(f"replaced = {replaced}")
    print(f"appended = {appended}")
    print("transient decision inbox removed = yes")


if __name__ == "__main__":
    main()
