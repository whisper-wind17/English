#!/usr/bin/env python3
"""Plan the next deterministic high-throughput Stage-A review batch.

The planner now has a strict additive-evidence fast lane for previously reviewed,
single-row keep identities. It also emits a selected-only review packet and a
machine checkpoint so reviewers do not need to rescan large repository CSVs.
All emitted artifacts are derived-only; identity_decisions.csv remains content truth.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
BUNDLE = TP / "audit" / "review_bundle.csv"
PROPOSALS = TP / "audit" / "decision_proposals.csv"
DECISIONS = TP / "review" / "identity_decisions.csv"
OUT = TP / "audit" / "next_batch.json"
PACKET = TP / "audit" / "selected_review_packet.json"
STATUS = TP / "audit" / "stage_a_status.json"
REVIEW_VIEW = TP / "audit" / "selected_review_view.csv"
PLAN_VERSION = "v5-throughput-delta"
STATUS_VERSION = "stage-a-status-v1"

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
    "evidence-revalidation": (60, 120),
    "semantic-review": (30, 60),
    "split-resolution": (25, 70),
    "object-boundary": (25, 50),
}

FAST_ALLOWED_CLASSES = {"semantic-cross-source", "semantic-easy", "semantic-hard"}
FAST_ACTION = "keep-identity"

REVIEW_VIEW_FIELDS = [
    "MatchKey", "ReviewMode", "TargetSense", "AddedOccurrenceCount",
    "AddedSourceIDs", "AddedDefinitions", "AddedNeighborhoodJSON", "FullEvidenceJSON",
]


def read_csv(path: Path, *, required: bool = True) -> list[dict[str, str]]:
    if not path.exists():
        if required:
            raise SystemExit(f"Missing required file: {path}")
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def decode_json_list(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(value, list) or not all(isinstance(x, str) and x for x in value):
        return []
    return value


def evidence(row: dict[str, str]) -> list[dict[str, object]]:
    try:
        value = json.loads(row.get("OccurrenceEvidenceJSON", "[]"))
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def evidence_keys(items: list[dict[str, object]]) -> list[str]:
    return [
        str(item.get("SourceOccurrenceKey", ""))
        for item in items
        if isinstance(item, dict) and item.get("SourceOccurrenceKey")
    ]


def decision_map() -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(DECISIONS):
        out[row.get("MatchKey", "")].append(row)
    return out


def fast_revalidation_info(
    row: dict[str, str],
    decisions_by_match: dict[str, list[dict[str, str]]],
) -> dict[str, object] | None:
    signals = {x for x in row.get("CandidateSignals", "").split("|") if x}
    if "decision-evidence-changed" not in signals:
        return None
    if row.get("BlockerClass", "") not in FAST_ALLOWED_CLASSES:
        return None
    if row.get("CandidateCanonical", ""):
        return None

    decisions = decisions_by_match.get(row.get("MatchKey", ""), [])
    if len(decisions) != 1:
        return None
    decision = decisions[0]
    if decision.get("Action") != FAST_ACTION or decision.get("Status") != "reviewed":
        return None
    if not decision.get("TargetSense", "").strip():
        return None
    if "audited-defer" in decision.get("DecisionBasis", "").casefold():
        return None

    reviewed = decode_json_list(decision.get("OccurrenceKeys", ""))
    current_evidence = evidence(row)
    current = evidence_keys(current_evidence)
    reviewed_set = set(reviewed)
    current_set = set(current)
    if not reviewed or not current or not reviewed_set < current_set:
        return None
    if not reviewed_set <= current_set:
        return None

    added_set = current_set - reviewed_set
    added = [
        item for item in current_evidence
        if isinstance(item, dict) and str(item.get("SourceOccurrenceKey", "")) in added_set
    ]
    if not added:
        return None

    return {
        "Decision": decision,
        "ReviewedOccurrenceKeys": reviewed,
        "CurrentOccurrenceKeys": current,
        "AddedOccurrenceKeys": sorted(added_set),
        "AddedEvidence": added,
    }


def evidence_weight(
    row: dict[str, str],
    *,
    lane: str,
    fast_info: dict[str, object] | None = None,
) -> int:
    if lane == "evidence-revalidation" and fast_info:
        added = fast_info.get("AddedEvidence", [])
        if not isinstance(added, list):
            added = []
        added_sources = {
            str(item.get("SourceID", ""))
            for item in added if isinstance(item, dict) and item.get("SourceID")
        }
        payload_len = len(json.dumps(added, ensure_ascii=False, separators=(",", ":")))
        return max(1, len(added)) + max(0, len(added_sources) - 1) + max(0, math.ceil(payload_len / 4000) - 1)

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


def bundle_fingerprint(
    rows: list[dict[str, str]],
    decisions_by_match: dict[str, list[dict[str, str]]],
) -> str:
    payload = []
    for row in rows:
        durable = [
            {k: d.get(k, "") for k in (
                "DecisionKey", "OccurrenceKeys", "Action", "CanonicalMatchKey",
                "ObjectType", "TargetSense", "Status", "Confidence", "DecisionBasis", "Rationale",
            )}
            for d in decisions_by_match.get(row.get("MatchKey", ""), [])
        ]
        payload.append({
            "MatchKey": row.get("MatchKey", ""),
            "ReviewLane": row.get("ReviewLane", ""),
            "ActionabilityScore": row.get("ActionabilityScore", ""),
            "OccurrenceCount": row.get("OccurrenceCount", ""),
            "CandidateCanonical": row.get("CandidateCanonical", ""),
            "CurrentAction": row.get("CurrentAction", ""),
            "CurrentStatus": row.get("CurrentStatus", ""),
            "CurrentDecisionBasis": row.get("CurrentDecisionBasis", ""),
            "OccurrenceEvidenceJSON": row.get("OccurrenceEvidenceJSON", ""),
            "DurableDecisions": durable,
        })
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def packet_item(
    row: dict[str, str],
    *,
    lane: str,
    decisions_by_match: dict[str, list[dict[str, str]]],
    fast_info: dict[str, object] | None,
) -> dict[str, object]:
    if lane == "evidence-revalidation" and fast_info:
        decision = fast_info["Decision"]
        assert isinstance(decision, dict)
        return {
            "MatchKey": row.get("MatchKey", ""),
            "ReviewMode": "delta-evidence",
            "BlockerClass": row.get("BlockerClass", ""),
            "DurableDecision": {k: decision.get(k, "") for k in (
                "DecisionKey", "MatchKey", "Action", "CanonicalMatchKey", "ObjectType",
                "TargetSense", "Status", "Confidence",
            )},
            "ReviewedOccurrenceCount": len(fast_info["ReviewedOccurrenceKeys"]),
            "CurrentOccurrenceCount": len(fast_info["CurrentOccurrenceKeys"]),
            "AddedOccurrenceKeys": fast_info["AddedOccurrenceKeys"],
            "AddedEvidence": fast_info["AddedEvidence"],
        }

    full = evidence(row)
    return {
        "MatchKey": row.get("MatchKey", ""),
        "ReviewMode": "full-evidence",
        "DisplayForms": row.get("DisplayForms", ""),
        "Definitions": row.get("Definitions", ""),
        "SourceIDs": row.get("SourceIDs", ""),
        "SourceBooks": row.get("SourceBooks", ""),
        "CandidateSignals": row.get("CandidateSignals", ""),
        "CandidateCanonical": row.get("CandidateCanonical", ""),
        "CanonicalRelation": row.get("CanonicalRelation", ""),
        "CanonicalAction": row.get("CanonicalAction", ""),
        "CanonicalStatus": row.get("CanonicalStatus", ""),
        "CanonicalTargetSense": row.get("CanonicalTargetSense", ""),
        "BlockerClass": row.get("BlockerClass", ""),
        "PolicyRecommendedAction": row.get("PolicyRecommendedAction", ""),
        "DurableDecisions": decisions_by_match.get(row.get("MatchKey", ""), []),
        "CurrentOccurrenceKeys": evidence_keys(full),
        "FullEvidence": full,
    }


def write_review_view(items: list[dict[str, object]]) -> None:
    rows: list[dict[str, str]] = []
    for item in items:
        mode = str(item.get("ReviewMode", ""))
        if mode == "delta-evidence":
            durable = item.get("DurableDecision", {})
            if not isinstance(durable, dict):
                durable = {}
            added = item.get("AddedEvidence", [])
            if not isinstance(added, list):
                added = []
            sources = sorted({
                str(e.get("SourceID", "")) for e in added
                if isinstance(e, dict) and e.get("SourceID")
            })
            definitions = list(dict.fromkeys(
                str(e.get("Definition", "")) for e in added
                if isinstance(e, dict) and e.get("Definition")
            ))
            neighborhoods = [
                {
                    "SourceOccurrenceKey": e.get("SourceOccurrenceKey", ""),
                    "Before": e.get("Before", []),
                    "After": e.get("After", []),
                }
                for e in added if isinstance(e, dict)
            ]
            rows.append({
                "MatchKey": str(item.get("MatchKey", "")),
                "ReviewMode": mode,
                "TargetSense": str(durable.get("TargetSense", "")),
                "AddedOccurrenceCount": str(len(added)),
                "AddedSourceIDs": "|".join(sources),
                "AddedDefinitions": " | ".join(definitions),
                "AddedNeighborhoodJSON": json.dumps(neighborhoods, ensure_ascii=False, separators=(",", ":")),
                "FullEvidenceJSON": "",
            })
        else:
            rows.append({
                "MatchKey": str(item.get("MatchKey", "")),
                "ReviewMode": mode,
                "TargetSense": "",
                "AddedOccurrenceCount": "",
                "AddedSourceIDs": "",
                "AddedDefinitions": "",
                "AddedNeighborhoodJSON": "",
                "FullEvidenceJSON": json.dumps(item.get("FullEvidence", []), ensure_ascii=False, separators=(",", ":")),
            })
    with REVIEW_VIEW.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_VIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def packet_fingerprint(items: list[dict[str, object]]) -> str:
    raw = json.dumps(items, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def csv_count(path: Path) -> int:
    return len(read_csv(path, required=False))


def build_status(plan: dict[str, object], bundle_rows: list[dict[str, str]]) -> dict[str, object]:
    staging = TP / "staging"
    learner = TP / "learner"
    surface_rows = read_csv(staging / "surface_candidates.csv", required=False)
    multipart = sum(1 for row in surface_rows if row.get("DecisionAction") == "multipart-reviewed")
    evidence_changed = sum(
        1 for row in bundle_rows
        if "decision-evidence-changed" in row.get("CandidateSignals", "").split("|")
    )
    return {
        "StatusVersion": STATUS_VERSION,
        "CheckpointSemantics": "persisted only after downstream Completion Recheck and Klose isolation pass",
        "InputCommit": os.environ.get("GITHUB_SHA", ""),
        "WorkflowRunID": os.environ.get("GITHUB_RUN_ID", ""),
        "WorkflowRunNumber": os.environ.get("GITHUB_RUN_NUMBER", ""),
        "SourceOccurrences": csv_count(staging / "occurrences.csv"),
        "NormalizedSurfaces": len(surface_rows),
        "DurableIdentityDecisions": csv_count(DECISIONS),
        "IdentityVocabularyPreview": csv_count(staging / "unified_vocabulary_preview.csv"),
        "LearnerVocabularyPreview": csv_count(learner / "learner_vocabulary_preview.csv"),
        "ReviewBlockers": len(bundle_rows),
        "EvidenceChangedSurfaces": evidence_changed,
        "MultipartResolved": multipart,
        "GrammarFormQuarantineGates": csv_count(learner / "grammar_form_quarantine.csv"),
        "NextBatch": {
            "PlanVersion": plan.get("PlanVersion", ""),
            "ReviewLane": plan.get("ReviewLane", ""),
            "SelectedCount": plan.get("SelectedCount", 0),
            "SelectedMatchKeys": plan.get("SelectedMatchKeys", []),
            "EvidenceWeight": plan.get("EvidenceWeight", 0),
            "EffectiveWeightBudget": plan.get("EffectiveWeightBudget", 0),
            "ExecutionReady": plan.get("ExecutionReady", False),
            "ReviewBundleFingerprint": plan.get("ReviewBundleFingerprint", ""),
            "ReviewPacketFingerprint": plan.get("ReviewPacketFingerprint", ""),
        },
    }


def main() -> None:
    rows = read_csv(BUNDLE)
    decisions_by_match = decision_map()
    proposal_keys = {
        row.get("MatchKey", "")
        for row in read_csv(PROPOSALS, required=False)
        if row.get("MatchKey", "")
    }

    fast_info_by_key = {
        row["MatchKey"]: info
        for row in rows
        if (info := fast_revalidation_info(row, decisions_by_match)) is not None
    }

    selected_lane = ""
    lane_rows: list[dict[str, str]] = []
    skipped_guarded_policy = 0
    for lane in LANE_ORDER:
        candidates = [row for row in rows if row.get("ReviewLane") == lane]
        if lane == "policy-executable":
            guarded = [row for row in candidates if row.get("MatchKey") not in proposal_keys]
            skipped_guarded_policy += len(guarded)
            candidates = [row for row in candidates if row.get("MatchKey") in proposal_keys]
        if lane == "semantic-review":
            fast_candidates = [row for row in candidates if row.get("MatchKey") in fast_info_by_key]
            if fast_candidates:
                selected_lane = "evidence-revalidation"
                lane_rows = fast_candidates
                break
        if candidates:
            selected_lane = lane
            lane_rows = candidates
            break

    selected: list[dict[str, str]] = []
    total_weight = 0
    surface_cap = 0
    weight_budget = 0
    effective_budget = 0
    skipped_for_packing: list[str] = []
    oversized_single = False
    if selected_lane:
        surface_cap, weight_budget = LIMITS[selected_lane]
        effective_budget = weight_budget
        weighted: list[tuple[dict[str, str], int]] = []
        for row in lane_rows:
            info = fast_info_by_key.get(row.get("MatchKey", ""))
            weighted.append((row, evidence_weight(row, lane=selected_lane, fast_info=info)))

        for row, weight in weighted:
            if len(selected) >= surface_cap:
                break
            if total_weight + weight > weight_budget:
                skipped_for_packing.append(row.get("MatchKey", ""))
                continue
            selected.append(row)
            total_weight += weight

        if not selected and weighted:
            row, weight = min(weighted, key=lambda item: (item[1], item[0].get("MatchKey", "")))
            selected = [row]
            total_weight = weight
            effective_budget = weight
            oversized_single = weight > weight_budget
            skipped_for_packing = [
                item[0].get("MatchKey", "") for item in weighted if item[0] is not row
            ]

    execution_ready = bool(selected)
    gate_reason = "" if execution_ready else "no active review batch"
    selected_items = [
        packet_item(
            row,
            lane=selected_lane,
            decisions_by_match=decisions_by_match,
            fast_info=fast_info_by_key.get(row.get("MatchKey", "")),
        )
        for row in selected
    ]
    review_packet_fp = packet_fingerprint(selected_items)

    plan = {
        "PlanVersion": PLAN_VERSION,
        "ReviewLane": selected_lane,
        "ReviewMode": "delta-evidence" if selected_lane == "evidence-revalidation" else "full-evidence",
        "SelectedMatchKeys": [row["MatchKey"] for row in selected],
        "SelectedCount": len(selected),
        "EvidenceWeight": total_weight,
        "SurfaceCap": surface_cap,
        "WeightBudget": weight_budget,
        "EffectiveWeightBudget": effective_budget,
        "PackingSkippedMatchKeys": skipped_for_packing,
        "OversizedSingleSurface": oversized_single,
        "FastRevalidationCandidates": len(fast_info_by_key),
        "SkippedGuardedPolicyRows": skipped_guarded_policy,
        "ExecutionReady": execution_ready,
        "GateReason": gate_reason,
        "ReviewBundleFingerprint": bundle_fingerprint(rows, decisions_by_match),
        "ReviewPacketFingerprint": review_packet_fp,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    packet = {
        "PlanVersion": PLAN_VERSION,
        "ReviewPacketVersion": "selected-review-packet-v2",
        "ReviewLane": selected_lane,
        "ReviewMode": plan["ReviewMode"],
        "SelectedMatchKeys": plan["SelectedMatchKeys"],
        "SelectedCount": plan["SelectedCount"],
        "ReviewBundleFingerprint": plan["ReviewBundleFingerprint"],
        "ReviewPacketFingerprint": review_packet_fp,
        "Items": selected_items,
    }
    PACKET.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_review_view(selected_items)

    status = build_status(plan, rows)
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"review batch plan version = {PLAN_VERSION}")
    print(f"review batch lane = {selected_lane or 'none'}")
    print(f"review batch mode = {plan['ReviewMode']}")
    print(f"review batch selected surfaces = {len(selected)}")
    print(f"review batch evidence weight = {total_weight} / {effective_budget}")
    print(f"review batch surface cap = {surface_cap}")
    print(f"review batch fast revalidation candidates = {len(fast_info_by_key)}")
    print(f"review batch packing skipped = {len(skipped_for_packing)}")
    print(f"review batch oversized single = {'yes' if oversized_single else 'no'}")
    print(f"review batch guarded policy rows skipped = {skipped_guarded_policy}")
    print(f"review batch execution ready = {'yes' if execution_ready else 'no'}")
    if gate_reason:
        print(f"review batch gate reason = {gate_reason}")
    print("selected review packet = generated")
    print("selected review view = generated")
    print("Stage-A machine checkpoint = generated")
    print("review batch selection = deterministic")
    print("review batch decision truth = derived-only")


if __name__ == "__main__":
    main()
