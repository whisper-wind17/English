#!/usr/bin/env python3
"""Normalize Stage-A review lanes and invalidate stale audited defers.

The review bundle and defer-context registry are derived-only. A held decision with
an explicit ``audited-defer`` marker is removed from active review only while the
context it was audited against remains unchanged. Context includes current source
evidence, directional canonical state, and the review-policy version.

This script never changes identity_decisions.csv, blocker counts, or release state.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
BUNDLE = TP / "audit" / "review_bundle.csv"
CONTEXT = TP / "audit" / "defer_context.csv"
POLICY_VERSION = "v3"

CONTEXT_FIELDS = [
    "MatchKey", "DecisionSignature", "ContextFingerprint", "DeferReasonCode",
    "DeferDependency", "PolicyVersion",
]

ACTIVE_REVIEW_LANES = {
    "policy-review",
    "object-boundary",
    "actionable-semantic",
    "semantic-review",
    "source-reconciliation-needed",
    "split-resolution",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha(payload: object) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def decision_signature(row: dict[str, str]) -> str:
    return sha({
        "Action": row.get("CurrentAction", ""),
        "Status": row.get("CurrentStatus", ""),
        "Confidence": row.get("CurrentConfidence", ""),
        "Basis": row.get("CurrentDecisionBasis", ""),
        "Rationale": row.get("CurrentRationale", ""),
    })


def context_fingerprint(row: dict[str, str]) -> str:
    return sha({
        "PolicyVersion": POLICY_VERSION,
        "OccurrenceEvidenceJSON": row.get("OccurrenceEvidenceJSON", ""),
        "CandidateCanonical": row.get("CandidateCanonical", ""),
        "CanonicalRelation": row.get("CanonicalRelation", ""),
        "CanonicalAction": row.get("CanonicalAction", ""),
        "CanonicalStatus": row.get("CanonicalStatus", ""),
        "CanonicalTargetSense": row.get("CanonicalTargetSense", ""),
        "CanonicalDefinitions": row.get("CanonicalDefinitions", ""),
        "CanonicalOccurrenceCount": row.get("CanonicalOccurrenceCount", ""),
    })


def defer_reason_code(row: dict[str, str]) -> str:
    text = f'{row.get("CurrentDecisionBasis", "")} {row.get("CurrentRationale", "")}'.casefold()
    if "canonical-blocked" in text:
        return "canonical-blocked"
    if "canonical-missing" in text:
        return "canonical-missing"
    if "object-boundary" in text:
        return "object-boundary"
    if "abbreviation" in text:
        return "abbreviation-evidence"
    if "source" in text or "evidence" in text:
        return "evidence-insufficient"
    if "policy" in text or "form" in text:
        return "policy-boundary"
    return "evidence-insufficient"


def defer_dependency(row: dict[str, str]) -> str:
    canonical = row.get("CandidateCanonical", "").strip()
    if canonical:
        return f"canonical:{canonical}"
    if row.get("BlockerClass") == "source-reconciliation":
        return "source-evidence"
    return f"policy:{POLICY_VERSION}"


def reactivation_lane(row: dict[str, str]) -> tuple[str, str]:
    cls = row.get("BlockerClass", "")
    if cls in {"form-policy", "abbreviation-policy"}:
        return "policy-review", "30"
    if cls == "multiword-object-boundary":
        return "object-boundary", "25"
    if cls == "split-resolution":
        return "split-resolution", "25"
    if "reconciliation" in cls:
        return "source-reconciliation-needed", "15"
    return "semantic-review", "30"


def main() -> None:
    if not BUNDLE.exists():
        raise SystemExit(f"Missing review bundle: {BUNDLE}")

    with BUNDLE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        rows = list(reader)

    previous = {row["MatchKey"]: row for row in read_csv(CONTEXT) if row.get("MatchKey")}
    next_context: list[dict[str, str]] = []
    retired: list[str] = []
    reactivated: list[str] = []

    for row in rows:
        if row.get("CurrentStatus") != "held":
            continue
        basis = row.get("CurrentDecisionBasis", "").casefold()
        if "audited-defer" not in basis:
            continue

        key = row["MatchKey"]
        signature = decision_signature(row)
        current_context = context_fingerprint(row)
        reason = defer_reason_code(row)
        dependency = defer_dependency(row)
        old = previous.get(key)

        # First v3 migration or an explicit re-review accepts the current context.
        accepted_context = old is None or old.get("DecisionSignature") != signature
        stale_context = (
            old is not None
            and old.get("DecisionSignature") == signature
            and old.get("ContextFingerprint") != current_context
        )

        if stale_context:
            lane, batch = reactivation_lane(row)
            row["ReviewLane"] = lane
            row["RecommendedBatchSize"] = batch
            row["PolicyRecommendedAction"] = "re-review-context-changed"
            row["DeferReason"] = "audited defer context changed; explicit re-review required"
            reactivated.append(key)
            # Keep the previously accepted fingerprint until the durable decision is re-reviewed.
            next_context.append({
                "MatchKey": key,
                "DecisionSignature": old.get("DecisionSignature", signature),
                "ContextFingerprint": old.get("ContextFingerprint", current_context),
                "DeferReasonCode": reason,
                "DeferDependency": dependency,
                "PolicyVersion": old.get("PolicyVersion", POLICY_VERSION),
            })
            continue

        row["ReviewLane"] = "deferred-high-ambiguity"
        row["RecommendedBatchSize"] = "0"
        row["PolicyRecommendedAction"] = "defer"
        row["DeferReason"] = "current audited context unchanged; do not rescan"
        retired.append(key)
        next_context.append({
            "MatchKey": key,
            "DecisionSignature": signature,
            "ContextFingerprint": current_context if accepted_context or old is None else old.get("ContextFingerprint", current_context),
            "DeferReasonCode": reason,
            "DeferDependency": dependency,
            "PolicyVersion": POLICY_VERSION,
        })

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

    CONTEXT.parent.mkdir(parents=True, exist_ok=True)
    with CONTEXT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CONTEXT_FIELDS)
        writer.writeheader()
        writer.writerows(sorted(next_context, key=lambda row: row["MatchKey"]))

    stale_hidden = [
        row["MatchKey"] for row in rows
        if row.get("CurrentStatus") == "held"
        and "audited-defer" in row.get("CurrentDecisionBasis", "").casefold()
        and row["MatchKey"] in set(reactivated)
        and row.get("ReviewLane") == "deferred-high-ambiguity"
    ]
    if stale_hidden:
        raise SystemExit("Stale audited defer remained hidden: " + ", ".join(stale_hidden[:20]))

    counts = Counter(row["ReviewLane"] for row in rows)
    print(f"audited defer rows retired from active lanes = {len(retired)}")
    print(f"audited defer rows reactivated by context change = {len(reactivated)}")
    print("reactivated MatchKeys = " + ("|".join(reactivated) if reactivated else "none"))
    for lane in sorted(counts):
        print(f"normalized review bundle lane {lane} = {counts[lane]}")
    print(f"defer context policy version = {POLICY_VERSION}")
    print("defer context fingerprint = source+canonical+policy")
    print("review lane normalization = pass")
    print("identity decision truth changed = no")


if __name__ == "__main__":
    main()
