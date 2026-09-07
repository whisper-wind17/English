#!/usr/bin/env python3
"""Capture and independently verify one third-party Stage-A decision batch.

The transient inbox is snapshotted before apply deletes it. Verification checks
both decision content and explicit occurrence evidence. Multipart MatchKeys are
verified as one partition-aware unit so a resolved split may legitimately emit
multiple Preview identities while the Source MatchKey itself leaves review.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
UPDATES = TP / "review" / "decision_updates.csv"
DECISIONS = TP / "review" / "identity_decisions.csv"
REVIEW = TP / "staging" / "review_queue.csv"
PREVIEW = TP / "staging" / "unified_vocabulary_preview.csv"
BATCH = Path("/tmp/third_party_audit_batch.json")

FIELDS_TO_MATCH = [
    "DecisionKey", "MatchKey", "Action", "CanonicalMatchKey", "ObjectType",
    "TargetSense", "Status", "Confidence", "DecisionBasis", "Rationale",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fail(message: str) -> None:
    raise SystemExit(message)


def decode_keys(raw: str, label: str) -> set[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"Batch recheck: invalid OccurrenceKeys JSON for {label}: {exc}")
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
        fail(f"Batch recheck: invalid OccurrenceKeys array for {label}")
    if len(value) != len(set(value)):
        fail(f"Batch recheck: duplicate OccurrenceKeys for {label}")
    return set(value)


def capture() -> None:
    rows = read_csv(UPDATES)
    payload_rows = []
    for row in rows:
        item = {field: row.get(field, "") for field in FIELDS_TO_MATCH}
        item["OccurrenceKeys"] = row.get("OccurrenceKeys", "")
        payload_rows.append(item)
    payload = {"rows": payload_rows, "count": len(payload_rows)}
    BATCH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"captured audit decision batch = {len(rows)}")


def verify() -> None:
    payload = json.loads(BATCH.read_text(encoding="utf-8")) if BATCH.exists() else {"rows": [], "count": 0}
    expected = payload.get("rows", [])
    decisions = read_csv(DECISIONS)
    review = read_csv(REVIEW)
    preview = read_csv(PREVIEW)

    by_decision = {row["DecisionKey"]: row for row in decisions}
    decisions_by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decisions:
        decisions_by_match[row["MatchKey"]].append(row)

    review_keys = {row["MatchKey"] for row in review}
    preview_keys = {row["CanonicalMatchKey"] for row in preview}
    preview_source_keys: set[str] = set()
    missing_target_sense = []
    for row in preview:
        if not row.get("TargetSense", "").strip():
            missing_target_sense.append(row.get("CanonicalMatchKey", ""))
        preview_source_keys.update(x for x in row.get("SourceMatchKeys", "").split("|") if x)

    if missing_target_sense:
        fail(f"Batch recheck: preview has empty TargetSense: {missing_target_sense[:20]}")
    if UPDATES.exists():
        fail("Batch recheck: transient decision_updates.csv still exists")

    action_counts: dict[str, int] = {}
    touched_matches: set[str] = set()
    for wanted in expected:
        key = wanted["DecisionKey"]
        actual = by_decision.get(key)
        if actual is None:
            fail(f"Batch recheck: durable decision missing: {key}")
        for field in FIELDS_TO_MATCH:
            if actual.get(field, "") != wanted.get(field, ""):
                fail(
                    f"Batch recheck: field mismatch for {key}: {field}: "
                    f"expected={wanted.get(field, '')!r} actual={actual.get(field, '')!r}"
                )

        expected_occ = wanted.get("OccurrenceKeys", "")
        if expected_occ and expected_occ != "*":
            if decode_keys(actual.get("OccurrenceKeys", ""), key) != decode_keys(expected_occ, f"expected {key}"):
                fail(f"Batch recheck: OccurrenceKeys mismatch for {key}")
        elif not actual.get("OccurrenceKeys", "") or actual.get("OccurrenceKeys") == "*":
            fail(f"Batch recheck: wildcard/empty OccurrenceKeys persisted for {key}")

        action = actual["Action"]
        action_counts[action] = action_counts.get(action, 0) + 1
        touched_matches.add(actual["MatchKey"])

    # Verify derived state per MatchKey. This is essential for multipart decisions:
    # subgroup actions cannot be judged as if each row owned the whole surface.
    for match_key in touched_matches:
        ds = decisions_by_match[match_key]
        multipart = len(ds) > 1
        in_review = match_key in review_keys

        if multipart:
            all_reviewed_resolved = all(
                d.get("Status") == "reviewed"
                and d.get("Action") in {"keep-identity", "reuse-identity", "route-expression", "source-only"}
                for d in ds
            )
            if all_reviewed_resolved and not in_review:
                for d in ds:
                    if d["Action"] == "keep-identity":
                        provisional = d.get("CanonicalMatchKey", "")
                        if not provisional or provisional not in preview_keys:
                            fail(f"Batch recheck: multipart keep missing from preview: {d['DecisionKey']} -> {provisional}")
                        if match_key not in preview_source_keys:
                            fail(f"Batch recheck: multipart provenance missing: {d['DecisionKey']}")
                    elif d["Action"] == "reuse-identity":
                        canonical = d.get("CanonicalMatchKey", "")
                        if canonical in preview_keys and match_key not in preview_source_keys:
                            fail(f"Batch recheck: multipart reuse provenance missing: {d['DecisionKey']} -> {canonical}")
            elif not in_review:
                fail(f"Batch recheck: unresolved multipart surface escaped review: {match_key}")
            continue

        actual = ds[0]
        action = actual["Action"]
        if action == "keep-identity" and actual.get("Status") == "reviewed":
            if match_key not in preview_keys:
                fail(f"Batch recheck: keep-identity did not enter preview: {match_key}")
            if in_review:
                fail(f"Batch recheck: keep-identity still in review queue: {match_key}")
        elif action in {"held", "split-required", "pending"}:
            if not in_review:
                fail(f"Batch recheck: blocker missing from review queue: {match_key}")
            if match_key in preview_keys:
                fail(f"Batch recheck: blocker leaked into preview: {match_key}")
        elif action in {"route-expression", "source-only"}:
            if in_review:
                fail(f"Batch recheck: routed/source-only item remains in review queue: {match_key}")
            if match_key in preview_keys or match_key in preview_source_keys:
                fail(f"Batch recheck: routed/source-only item leaked into preview: {match_key}")
        elif action == "reuse-identity" and actual.get("Status") == "reviewed":
            canonical = actual.get("CanonicalMatchKey", "")
            if canonical in preview_keys and match_key not in preview_source_keys:
                fail(f"Batch recheck: released reuse alias missing from preview provenance: {match_key} -> {canonical}")

    print("Third-party audit batch recheck = pass")
    print(f"batch decisions = {len(expected)}")
    for action in sorted(action_counts):
        print(f"batch {action} = {action_counts[action]}")
    print(f"touched MatchKeys = {len(touched_matches)}")
    print(f"review/blocker surfaces = {len(review)}")
    print(f"unified vocabulary preview = {len(preview)}")
    print(f"preview TargetSense complete = {len(preview)} / {len(preview)}")
    print("explicit split OccurrenceKeys verified = yes")
    print("multipart derived-state verification = yes")
    print("transient decision inbox removed = yes")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"capture", "verify"}:
        fail("Usage: recheck_third_party_audit_batch.py [capture|verify]")
    if sys.argv[1] == "capture":
        capture()
    else:
        verify()


if __name__ == "__main__":
    main()
