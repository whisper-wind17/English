#!/usr/bin/env python3
"""Merge reviewed decision updates into durable third-party Identity truth.

Minimal Learner Identity contract:

- A singleton MatchKey decision owns learner Identity content. Its OccurrenceKeys are
  provenance/audit metadata, not a semantic-validity boundary. On every workflow run
  they are deterministically rebound to the current enabled SourceOccurrenceKey set.
  Adding/removing another textbook occurrence therefore does not re-open an already
  resolved singleton Identity.
- A multipart MatchKey uses multiple decision rows to represent distinct learner
  senses. For multipart rows OccurrenceKeys remain semantic partition truth and are
  never auto-expanded. Their subsets must stay explicit; source changes can therefore
  re-open the multipart surface until the partition is complete again.

`review/decision_updates.csv` is a transient inbox, never a second durable state store.
New inbox rows may use `*`, which is expanded before persistence, or an explicit JSON
array of occurrence keys.
"""
from __future__ import annotations

import csv
import json
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
                raise SystemExit(
                    f"SourceID mismatch in {path}: {row.get('SourceID')} != {source_id}"
                )
            occ_key = row.get("SourceOccurrenceKey", "")
            match_key = row.get("MatchKey", "")
            if not occ_key or occ_key in seen_occ or not match_key:
                raise SystemExit(f"Invalid/duplicate source occurrence: {occ_key}")
            seen_occ.add(occ_key)
            by_match[match_key].append(occ_key)
    return {k: sorted(v) for k, v in by_match.items()}


def encode_occurrence_keys(keys: list[str]) -> str:
    return json.dumps(sorted(keys), ensure_ascii=False, separators=(",", ":"))


def decode_occurrence_keys(raw: str, *, source: str, decision_key: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"{source}: OccurrenceKeys must be '*' or a JSON array for {decision_key}: {exc}"
        ) from exc
    if not isinstance(value, list) or not value or not all(
        isinstance(x, str) and x for x in value
    ):
        raise SystemExit(f"{source}: invalid OccurrenceKeys JSON array for {decision_key}")
    if len(value) != len(set(value)):
        raise SystemExit(f"{source}: duplicate OccurrenceKeys for {decision_key}")
    return value


def validate(row: dict[str, str], *, source: str) -> None:
    missing = [f for f in FIELDS if f not in row]
    if missing:
        raise SystemExit(f"{source}: missing fields {missing}")
    if not row["DecisionKey"] or not row["MatchKey"]:
        raise SystemExit(f"{source}: empty DecisionKey/MatchKey")
    if row["Action"] not in ACTIONS:
        raise SystemExit(
            f"{source}: invalid Action {row['Action']} for {row['DecisionKey']}"
        )
    if row["Status"] not in STATUSES:
        raise SystemExit(
            f"{source}: invalid Status {row['Status']} for {row['DecisionKey']}"
        )
    if not row.get("OccurrenceKeys"):
        raise SystemExit(f"{source}: empty OccurrenceKeys for {row['DecisionKey']}")
    if row["Action"] == "reuse-identity" and not row["CanonicalMatchKey"]:
        raise SystemExit(
            f"{source}: reuse-identity lacks CanonicalMatchKey for {row['DecisionKey']}"
        )
    if row["Action"] == "route-expression" and row["ObjectType"] != "expression":
        raise SystemExit(
            f"{source}: route-expression requires ObjectType=expression for {row['DecisionKey']}"
        )
    if row["Action"] == "source-only" and row["ObjectType"] != "source-only":
        raise SystemExit(
            f"{source}: source-only requires ObjectType=source-only for {row['DecisionKey']}"
        )


def normalize_row(
    row: dict[str, str],
    occurrence_map: dict[str, list[str]],
    *,
    source: str,
    allow_legacy_serialization: bool,
    require_current_subset: bool,
) -> tuple[dict[str, str], bool]:
    """Normalize serialization; semantic binding policy is applied after grouping."""
    normalized = {f: row.get(f, "") for f in FIELDS}
    validate(normalized, source=source)
    key = normalized["MatchKey"]
    current = occurrence_map.get(key, [])
    if not current:
        raise SystemExit(f"{source}: decision references missing current surface {key}")

    raw = normalized["OccurrenceKeys"]
    migrated_legacy = False
    if raw == "*":
        reviewed = current
        migrated_legacy = allow_legacy_serialization
    elif raw.lstrip().startswith("["):
        reviewed = decode_occurrence_keys(
            raw, source=source, decision_key=normalized["DecisionKey"]
        )
    elif allow_legacy_serialization:
        reviewed = current
        migrated_legacy = True
    else:
        raise SystemExit(
            f"{source}: OccurrenceKeys must be '*' or JSON for {normalized['DecisionKey']}"
        )

    if require_current_subset and not set(reviewed) <= set(current):
        raise SystemExit(
            f"{source}: OccurrenceKeys reference missing current evidence "
            f"for {normalized['DecisionKey']}"
        )
    normalized["OccurrenceKeys"] = encode_occurrence_keys(reviewed)
    return normalized, migrated_legacy


def main() -> None:
    if not DECISIONS.exists():
        raise SystemExit(f"Missing durable decision truth: {DECISIONS}")

    occurrence_map = current_occurrence_keys()
    current = read_csv(DECISIONS)
    updates = read_csv(UPDATES) if UPDATES.exists() else []

    by_key: dict[str, dict[str, str]] = {}
    order: list[str] = []
    migrated_legacy = 0

    for raw in current:
        row, migrated = normalize_row(
            raw,
            occurrence_map,
            source="identity_decisions",
            allow_legacy_serialization=True,
            require_current_subset=False,
        )
        dkey = row["DecisionKey"]
        if dkey in by_key:
            raise SystemExit(f"Duplicate durable DecisionKey: {dkey}")
        by_key[dkey] = row
        order.append(dkey)
        migrated_legacy += int(migrated)

    seen_updates: set[str] = set()
    replaced = 0
    appended = 0
    for raw in updates:
        row, _ = normalize_row(
            raw,
            occurrence_map,
            source="decision_updates",
            allow_legacy_serialization=False,
            require_current_subset=True,
        )
        dkey = row["DecisionKey"]
        if dkey in seen_updates:
            raise SystemExit(f"Duplicate update DecisionKey: {dkey}")
        seen_updates.add(dkey)
        if dkey in by_key:
            if by_key[dkey]["MatchKey"] != row["MatchKey"]:
                raise SystemExit(
                    f"Update changes MatchKey for existing DecisionKey: {dkey}"
                )
            by_key[dkey] = row
            replaced += 1
        else:
            by_key[dkey] = row
            order.append(dkey)
            appended += 1

    decision_keys_by_match: dict[str, list[str]] = defaultdict(list)
    for dkey in order:
        decision_keys_by_match[by_key[dkey]["MatchKey"]].append(dkey)

    singleton_rebound = 0
    multipart_rows_checked = 0
    for match_key, dkeys in decision_keys_by_match.items():
        current_keys = occurrence_map.get(match_key, [])
        if not current_keys:
            raise SystemExit(f"Decision references missing current surface: {match_key}")

        if len(dkeys) == 1:
            dkey = dkeys[0]
            desired = encode_occurrence_keys(current_keys)
            if by_key[dkey]["OccurrenceKeys"] != desired:
                by_key[dkey]["OccurrenceKeys"] = desired
                singleton_rebound += 1
            continue

        current_set = set(current_keys)
        for dkey in dkeys:
            reviewed = decode_occurrence_keys(
                by_key[dkey]["OccurrenceKeys"],
                source="identity_decisions",
                decision_key=dkey,
            )
            if not set(reviewed) <= current_set:
                raise SystemExit(
                    f"Multipart decision references removed current evidence: {dkey}"
                )
            multipart_rows_checked += 1

    changed = bool(migrated_legacy or updates or singleton_rebound)
    if changed:
        with DECISIONS.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            for dkey in order:
                writer.writerow(by_key[dkey])

    if UPDATES.exists():
        UPDATES.unlink()

    print(f"legacy decision evidence migrated = {migrated_legacy}")
    print(f"decision updates applied = {len(updates)}")
    print(f"replaced = {replaced}")
    print(f"appended = {appended}")
    print(f"singleton occurrence snapshots auto-rebound = {singleton_rebound}")
    print(f"multipart decision rows preserved/checked = {multipart_rows_checked}")
    print(f"durable decisions = {len(by_key)}")
    print("Singleton Identity validity independent of occurrence expansion = yes")
    print("Multipart OccurrenceKeys remain semantic partition truth = yes")
    print("OccurrenceKeys serialization = JSON array")
    print("durable wildcard/legacy OccurrenceKeys = no")
    print("transient decision inbox removed = yes")


if __name__ == "__main__":
    main()
