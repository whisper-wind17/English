#!/usr/bin/env python3
"""Merge reviewed decision updates into the durable third-party identity truth.

`review/decision_updates.csv` is a transient inbox, never a second state store.
`OccurrenceKeys` is also the review-evidence boundary: a surface decision records
exactly which Source Occurrences were covered when it was reviewed. An inbox row
may use `*`; before persistence this tool expands it to the current occurrence set
for that MatchKey. Durable `*` values from the pre-evidence migration are likewise
stamped once against the currently enabled adapters.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
CONFIG = TP / "config" / "source_adapters.csv"
REVIEW = TP / "review"
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


def current_occurrence_keys() -> dict[str, list[str]]:
    by_match: dict[str, list[str]] = defaultdict(list)
    seen_occ: set[str] = set()
    for cfg in read_csv(CONFIG):
        if cfg.get("Enabled", "").lower() != "yes":
            continue
        source_id = cfg.get("SourceID", "").strip()
        path = ROOT / cfg.get("OccurrencesPath", "").strip()
        if not source_id or not path.exists():
            raise SystemExit(f"Invalid enabled adapter config: {cfg}")
        for row in read_csv(path):
            if row.get("SourceID") != source_id:
                raise SystemExit(f"SourceID mismatch in {path}: {row.get('SourceID')} != {source_id}")
            occ_key = row.get("SourceOccurrenceKey", "")
            match_key = row.get("MatchKey", "")
            if not occ_key or occ_key in seen_occ or not match_key:
                raise SystemExit(f"Invalid/duplicate source occurrence: {occ_key}")
            seen_occ.add(occ_key)
            by_match[match_key].append(occ_key)
    return {k: sorted(v) for k, v in by_match.items()}


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
    if not row.get("OccurrenceKeys"):
        raise SystemExit(f"{source}: empty OccurrenceKeys for {row['DecisionKey']}")
    if row["Action"] == "reuse-identity" and not row["CanonicalMatchKey"]:
        raise SystemExit(f"{source}: reuse-identity lacks CanonicalMatchKey for {row['DecisionKey']}")
    if row["Action"] == "route-expression" and row["ObjectType"] != "expression":
        raise SystemExit(f"{source}: route-expression requires ObjectType=expression for {row['DecisionKey']}")
    if row["Action"] == "source-only" and row["ObjectType"] != "source-only":
        raise SystemExit(f"{source}: source-only requires ObjectType=source-only for {row['DecisionKey']}")


def stamp(row: dict[str, str], occurrence_map: dict[str, list[str]], *, source: str) -> dict[str, str]:
    normalized = {f: row.get(f, "") for f in FIELDS}
    validate(normalized, source=source)
    key = normalized["MatchKey"]
    current = occurrence_map.get(key, [])
    if not current:
        raise SystemExit(f"{source}: decision references missing current surface {key}")
    if normalized["OccurrenceKeys"] == "*":
        normalized["OccurrenceKeys"] = "|".join(current)
    else:
        reviewed = normalized["OccurrenceKeys"].split("|")
        if len(reviewed) != len(set(reviewed)):
            raise SystemExit(f"{source}: duplicate OccurrenceKeys for {normalized['DecisionKey']}")
        if not set(reviewed) <= set(current):
            raise SystemExit(f"{source}: OccurrenceKeys reference missing current evidence for {normalized['DecisionKey']}")
    return normalized


def main() -> None:
    if not DECISIONS.exists():
        raise SystemExit(f"Missing durable decision truth: {DECISIONS}")

    occurrence_map = current_occurrence_keys()
    current = read_csv(DECISIONS)
    updates = read_csv(UPDATES) if UPDATES.exists() else []

    by_key: dict[str, dict[str, str]] = {}
    order: list[str] = []
    stamped_legacy = 0
    for raw in current:
        had_star = raw.get("OccurrenceKeys") == "*"
        row = stamp(raw, occurrence_map, source="identity_decisions")
        key = row["DecisionKey"]
        if key in by_key:
            raise SystemExit(f"Duplicate durable DecisionKey: {key}")
        by_key[key] = row
        order.append(key)
        stamped_legacy += int(had_star)

    seen_updates: set[str] = set()
    replaced = 0
    appended = 0
    for raw in updates:
        row = stamp(raw, occurrence_map, source="decision_updates")
        key = row["DecisionKey"]
        if key in seen_updates:
            raise SystemExit(f"Duplicate update DecisionKey: {key}")
        seen_updates.add(key)
        if key in by_key:
            if by_key[key]["MatchKey"] != row["MatchKey"]:
                raise SystemExit(f"Update changes MatchKey for existing DecisionKey: {key}")
            by_key[key] = row
            replaced += 1
        else:
            by_key[key] = row
            order.append(key)
            appended += 1

    changed = bool(stamped_legacy or updates)
    if changed:
        with DECISIONS.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            for key in order:
                w.writerow(by_key[key])

    if UPDATES.exists():
        UPDATES.unlink()

    print(f"legacy wildcard decisions stamped = {stamped_legacy}")
    print(f"decision updates applied = {len(updates)}")
    print(f"replaced = {replaced}")
    print(f"appended = {appended}")
    print(f"durable decisions = {len(by_key)}")
    print("durable wildcard OccurrenceKeys = no")
    print("transient decision inbox removed = yes")


if __name__ == "__main__":
    main()
