#!/usr/bin/env python3
"""Normalize Stage-A review lanes for learner-first blocker finalization.

The review bundle and defer-context registry are derived-only. Stage-A source evidence
remains auditable, but lack of textbook sentence context is no longer a terminal reason
to hide a blocker. During the v4 finalization phase, every remaining held/split surface
is reactivated and must be resolved to an elementary learner-facing core sense, useful
phrase, explicit object route, or genuinely necessary semantic split.

Builder-level ``decision-evidence-changed`` signals remain mandatory re-review signals.
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
POLICY_VERSION = "v4-learner-first"

CONTEXT_FIELDS = [
    "MatchKey", "DecisionSignature", "ContextFingerprint", "DeferReasonCode",
    "DeferDependency", "PolicyVersion",
]


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
    if "reconciliation" in row.get("BlockerClass", ""):
        return "source-evidence"
    return f"policy:{POLICY_VERSION}"


def reactivation_lane(row: dict[str, str]) -> tuple[str, str]:
    if row.get("CurrentAction") == "split-required" or row.get("BlockerClass") == "split-resolution":
        return "split-resolution", "25"
    cls = row.get("BlockerClass", "")
    if cls in {"form-policy", "abbreviation-policy"}:
        return "policy-review", "30"
    if cls == "multiword-object-boundary":
        return "object-boundary", "25"
    if "reconciliation" in cls:
        return "semantic-review", "30"
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
    reactivated: list[str] = []
    evidence_reactivated: list[str] = []

    for row in rows:
        signals = {x for x in row.get("CandidateSignals", "").split("|") if x}
        if "decision-evidence-changed" not in signals:
            continue
        lane, batch = reactivation_lane(row)
        row["ReviewLane"] = lane
        row["RecommendedBatchSize"] = batch
        row["PolicyRecommendedAction"] = "re-review-evidence-changed"
        row["DeferReason"] = "source evidence changed; explicit re-review required"
        evidence_reactivated.append(row["MatchKey"])

    evidence_set = set(evidence_reactivated)
    for row in rows:
        key = row["MatchKey"]
        if key in evidence_set:
            continue
        if row.get("CurrentAction") not in {"held", "split-required"} and row.get("CurrentStatus") != "held":
            continue

        lane, batch = reactivation_lane(row)
        row["ReviewLane"] = lane
        row["RecommendedBatchSize"] = batch
        row["PolicyRecommendedAction"] = "learner-first-finalize"
        row["DeferReason"] = (
            "textbook sentence context unavailable/ambiguous; resolve with elementary "
            "learner-facing core sense, useful phrase, pedagogically salient form, or necessary split"
        )
        reactivated.append(key)

        basis = row.get("CurrentDecisionBasis", "").casefold()
        if "audited-defer" in basis:
            next_context.append({
                "MatchKey": key,
                "DecisionSignature": decision_signature(row),
                "ContextFingerprint": context_fingerprint(row),
                "DeferReasonCode": defer_reason_code(row),
                "DeferDependency": defer_dependency(row),
                "PolicyVersion": POLICY_VERSION,
            })

    rows.sort(key=lambda row: (
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

    hidden_changed = [
        row["MatchKey"] for row in rows
        if "decision-evidence-changed" in row.get("CandidateSignals", "").split("|")
        and row.get("ReviewLane") == "deferred-high-ambiguity"
    ]
    if hidden_changed:
        raise SystemExit("Changed source evidence remained hidden: " + ", ".join(hidden_changed[:20]))

    hidden_blockers = [
        row["MatchKey"] for row in rows
        if (row.get("CurrentAction") in {"held", "split-required"} or row.get("CurrentStatus") == "held")
        and row.get("ReviewLane") == "deferred-high-ambiguity"
    ]
    if hidden_blockers:
        raise SystemExit("Learner-first blocker remained hidden: " + ", ".join(hidden_blockers[:20]))

    counts = Counter(row["ReviewLane"] for row in rows)
    print(f"source-evidence-changed rows reactivated = {len(evidence_reactivated)}")
    print(f"learner-first blockers reactivated = {len(reactivated)}")
    print("reactivated MatchKeys = " + ("|".join(reactivated) if reactivated else "none"))
    for lane in sorted(counts):
        print(f"normalized review bundle lane {lane} = {counts[lane]}")
    print(f"defer context policy version = {POLICY_VERSION}")
    print("learner-first finalization = active")
    print("review lane normalization = pass")
    print("identity decision truth changed = no")


if __name__ == "__main__":
    main()
