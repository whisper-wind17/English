#!/usr/bin/env python3
"""Capture and independently verify one third-party Stage-A decision batch.

Usage in workflow:
  python tools/recheck_third_party_audit_batch.py capture
  python tools/recheck_third_party_audit_batch.py verify

The capture phase snapshots transient decision_updates.csv to /tmp before the apply
step deletes it. The verify phase checks that every intended decision is durable and
lands in the correct derived state. This complements, rather than replaces,
check_third_party_corpus.py.
"""
from __future__ import annotations

import csv
import json
import sys
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


def capture() -> None:
    rows = read_csv(UPDATES)
    payload = {
        "rows": [{field: row.get(field, "") for field in FIELDS_TO_MATCH} for row in rows],
        "count": len(rows),
    }
    BATCH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"captured audit decision batch = {len(rows)}")


def verify() -> None:
    payload = json.loads(BATCH.read_text(encoding="utf-8")) if BATCH.exists() else {"rows": [], "count": 0}
    expected = payload.get("rows", [])
    decisions = read_csv(DECISIONS)
    review = read_csv(REVIEW)
    preview = read_csv(PREVIEW)

    by_decision = {row["DecisionKey"]: row for row in decisions}
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

        action = actual["Action"]
        match_key = actual["MatchKey"]
        action_counts[action] = action_counts.get(action, 0) + 1

        if action == "keep-identity" and actual.get("Status") == "reviewed":
            if match_key not in preview_keys:
                fail(f"Batch recheck: keep-identity did not enter preview: {match_key}")
            if match_key in review_keys:
                fail(f"Batch recheck: keep-identity still in review queue: {match_key}")
        elif action in {"held", "split-required", "pending"}:
            if match_key not in review_keys:
                fail(f"Batch recheck: blocker missing from review queue: {match_key}")
            if match_key in preview_keys:
                fail(f"Batch recheck: blocker leaked into preview: {match_key}")
        elif action in {"route-expression", "source-only"}:
            if match_key in review_keys:
                fail(f"Batch recheck: routed/source-only item remains in review queue: {match_key}")
            if match_key in preview_keys or match_key in preview_source_keys:
                fail(f"Batch recheck: routed/source-only item leaked into preview: {match_key}")
        elif action == "reuse-identity" and actual.get("Status") == "reviewed":
            canonical = actual.get("CanonicalMatchKey", "")
            # A reuse alias is allowed to stay out of preview when its canonical is
            # intentionally blocked. If canonical is released, provenance must include it.
            if canonical in preview_keys and match_key not in preview_source_keys:
                fail(f"Batch recheck: released reuse alias missing from preview provenance: {match_key} -> {canonical}")

    print("Third-party audit batch recheck = pass")
    print(f"batch decisions = {len(expected)}")
    for action in sorted(action_counts):
        print(f"batch {action} = {action_counts[action]}")
    print(f"review/blocker surfaces = {len(review)}")
    print(f"unified vocabulary preview = {len(preview)}")
    print(f"preview TargetSense complete = {len(preview)} / {len(preview)}")
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
