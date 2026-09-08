#!/usr/bin/env python3
"""Normalize Stage-A review lanes with learner-first execution and audited-defer retirement.

The review bundle and defer-context registry are derived-only. Stage-A source evidence
remains auditable, but lack of textbook sentence context is no longer a terminal reason
to hide an unreviewed blocker.

A reviewed ``audited-defer`` is different: once its durable decision and review context
have been recorded, it must leave active throughput until source/canonical/policy context
changes. If that context changes while the durable decision is unchanged, the row stays
active across rebuilds until an explicit re-review changes the durable decision signature.

Builder-level ``decision-evidence-changed`` signals always take precedence and remain
mandatory re-review signals. This script never changes identity_decisions.csv, blocker
counts, or release state.
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
    """Fingerprint the durable decision metadata exposed by the review bundle.

    This intentionally excludes derived lane/scheduling fields. Explicit re-review
    batches must leave an auditable change in decision metadata (normally basis and/or
    rationale) when a held/split audited-defer is revalidated after context change.
    """
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


def is_audited_defer(row: dict[str, str]) -> bool:
    return "audited-defer" in row.get("CurrentDecisionBasis", "").casefold()


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


def context_record(row: dict[str, str]) -> dict[str, str]:
    return {
        "MatchKey": row["MatchKey"],
        "DecisionSignature": decision_signature(row),
        "ContextFingerprint": context_fingerprint(row),
        "DeferReasonCode": defer_reason_code(row),
        "DeferDependency": defer_dependency(row),
        "PolicyVersion": POLICY_VERSION,
    }


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


def activate(
    row: dict[str, str],
    *,
    action: str,
    reason: str,
) -> None:
    lane, batch = reactivation_lane(row)
    row["ReviewLane"] = lane
    row["RecommendedBatchSize"] = batch
    row["PolicyRecommendedAction"] = action
    row["DeferReason"] = reason


def retire_audited_defer(row: dict[str, str]) -> None:
    row["ReviewLane"] = "deferred-high-ambiguity"
    row["RecommendedBatchSize"] = "0"
    row["PolicyRecommendedAction"] = "audited-defer-valid"
    row["DeferReason"] = (
        "reviewed audited-defer remains valid; no rescan until source/canonical/policy context changes"
    )


def main() -> None:
    if not BUNDLE.exists():
        raise SystemExit(f"Missing review bundle: {BUNDLE}")

    with BUNDLE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        rows = list(reader)

    previous = {row["MatchKey"]: row for row in read_csv(CONTEXT) if row.get("MatchKey")}
    next_context: dict[str, dict[str, str]] = {}

    evidence_reactivated: list[str] = []
    context_reactivated: list[str] = []
    learner_first_reactivated: list[str] = []
    defer_stamped: list[str] = []
    defer_refreshed: list[str] = []
    defer_retired: list[str] = []

    # Highest-priority transition: changed source evidence can never remain hidden.
    for row in rows:
        signals = {x for x in row.get("CandidateSignals", "").split("|") if x}
        if "decision-evidence-changed" not in signals:
            continue

        activate(
            row,
            action="re-review-evidence-changed",
            reason="source evidence changed; explicit re-review required",
        )
        evidence_reactivated.append(row["MatchKey"])

        # Preserve the last accepted context rather than blessing the new context
        # before the durable decision is explicitly re-reviewed.
        prev = previous.get(row["MatchKey"])
        if prev and is_audited_defer(row):
            next_context[row["MatchKey"]] = prev

    evidence_set = set(evidence_reactivated)

    for row in rows:
        key = row["MatchKey"]
        if key in evidence_set:
            continue
        if row.get("CurrentAction") not in {"held", "split-required"} and row.get("CurrentStatus") != "held":
            continue

        if not is_audited_defer(row):
            activate(
                row,
                action="learner-first-finalize",
                reason=(
                    "textbook sentence context unavailable/ambiguous; resolve with elementary "
                    "learner-facing core sense, useful phrase, pedagogically salient form, or necessary split"
                ),
            )
            learner_first_reactivated.append(key)
            continue

        current = context_record(row)
        prev = previous.get(key)

        if prev is None:
            # First durable audited-defer under the current execution history:
            # the adjudication just happened, so stamp and retire immediately.
            retire_audited_defer(row)
            next_context[key] = current
            defer_stamped.append(key)
            continue

        same_decision = prev.get("DecisionSignature", "") == current["DecisionSignature"]
        same_context = (
            prev.get("ContextFingerprint", "") == current["ContextFingerprint"]
            and prev.get("PolicyVersion", "") == POLICY_VERSION
        )

        if same_decision and same_context:
            retire_audited_defer(row)
            next_context[key] = current
            defer_retired.append(key)
            continue

        if same_decision:
            # Context changed while durable decision did not. Keep the old accepted
            # fingerprint so repeated rebuilds stay active until explicit re-review.
            activate(
                row,
                action="re-review-context-changed",
                reason="audited-defer context changed; explicit re-review required",
            )
            next_context[key] = prev
            context_reactivated.append(key)
            continue

        # Durable decision metadata changed, which is the explicit re-review/refresh
        # transition. Accept the current context and retire the new audited-defer.
        retire_audited_defer(row)
        next_context[key] = current
        defer_refreshed.append(key)

    rows.sort(key=lambda row: (
        1 if row.get("ReviewLane") == "deferred-high-ambiguity" else 0,
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
        writer.writerows(next_context[key] for key in sorted(next_context))

    # Machine-enforced state-transition invariants.
    hidden_changed = [
        row["MatchKey"] for row in rows
        if "decision-evidence-changed" in row.get("CandidateSignals", "").split("|")
        and row.get("ReviewLane") == "deferred-high-ambiguity"
    ]
    if hidden_changed:
        raise SystemExit("Changed source evidence remained hidden: " + ", ".join(hidden_changed[:20]))

    invalid_deferred: list[str] = []
    for row in rows:
        if row.get("ReviewLane") != "deferred-high-ambiguity":
            continue
        key = row["MatchKey"]
        accepted = next_context.get(key)
        if not is_audited_defer(row) or not accepted:
            invalid_deferred.append(key)
            continue
        if (
            accepted.get("DecisionSignature") != decision_signature(row)
            or accepted.get("ContextFingerprint") != context_fingerprint(row)
            or accepted.get("PolicyVersion") != POLICY_VERSION
        ):
            invalid_deferred.append(key)
    if invalid_deferred:
        raise SystemExit(
            "Deferred lane contains unaccepted/stale audited-defer context: "
            + ", ".join(invalid_deferred[:20])
        )

    unchanged_not_retired: list[str] = []
    stale_hidden: list[str] = []
    for row in rows:
        key = row["MatchKey"]
        if not is_audited_defer(row) or key in evidence_set:
            continue
        prev = previous.get(key)
        if not prev:
            continue
        current_sig = decision_signature(row)
        current_fp = context_fingerprint(row)
        same_decision = prev.get("DecisionSignature", "") == current_sig
        same_context = (
            prev.get("ContextFingerprint", "") == current_fp
            and prev.get("PolicyVersion", "") == POLICY_VERSION
        )
        if same_decision and same_context and row.get("ReviewLane") != "deferred-high-ambiguity":
            unchanged_not_retired.append(key)
        if same_decision and not same_context and row.get("ReviewLane") == "deferred-high-ambiguity":
            stale_hidden.append(key)

    if unchanged_not_retired:
        raise SystemExit(
            "Unchanged audited-defer was reactivated: " + ", ".join(unchanged_not_retired[:20])
        )
    if stale_hidden:
        raise SystemExit(
            "Context-changed audited-defer was hidden: " + ", ".join(stale_hidden[:20])
        )

    counts = Counter(row["ReviewLane"] for row in rows)
    print(f"source-evidence-changed rows reactivated = {len(evidence_reactivated)}")
    print(f"context-changed audited-defer rows reactivated = {len(context_reactivated)}")
    print(f"learner-first non-defer blockers reactivated = {len(learner_first_reactivated)}")
    print(f"new audited-defer contexts stamped = {len(defer_stamped)}")
    print(f"explicit audited-defer refreshes accepted = {len(defer_refreshed)}")
    print(f"unchanged audited-defer rows retired = {len(defer_retired)}")
    print("context-reactivated MatchKeys = " + ("|".join(context_reactivated) if context_reactivated else "none"))
    print("retired audited-defer MatchKeys = " + (
        "|".join(sorted(set(defer_stamped + defer_refreshed + defer_retired)))
        if defer_stamped or defer_refreshed or defer_retired else "none"
    ))
    for lane in sorted(counts):
        print(f"normalized review bundle lane {lane} = {counts[lane]}")
    print(f"defer context policy version = {POLICY_VERSION}")
    print("audited-defer unchanged-context zero-scan = enforced")
    print("audited-defer stale-context requeue = enforced")
    print("review lane normalization = pass")
    print("identity decision truth changed = no")


if __name__ == "__main__":
    main()
