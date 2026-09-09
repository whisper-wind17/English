#!/usr/bin/env python3
"""Plan the next deterministic high-throughput Stage-A review batch.

v6 uses semantic-complexity cost rather than raw occurrence count as the primary
review budget. Repeated source occurrences are provenance, not linear human/model
review cost under Minimal Learner Identity. A separate packet-byte budget keeps
full-evidence batches bounded without artificially shrinking surface throughput.

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
PLAN_VERSION = "v6-semantic-throughput"
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

# (surface cap, semantic-complexity budget)
LIMITS = {
    "source-reconciliation-needed": (12, 60),
    "policy-executable": (100, 160),
    "policy-review": (40, 100),
    "actionable-semantic": (50, 140),
    "evidence-revalidation": (80, 160),
    "semantic-review": (30, 120),
    "split-resolution": (18, 120),
    "object-boundary": (40, 120),
}

# Independent context-size guard. This prevents high-throughput packing from
# producing an unbounded selected_review_packet even when semantic cost is low.
PACKET_BYTE_LIMITS = {
    "source-reconciliation-needed": 180_000,
    "policy-executable": 240_000,
    "policy-review": 220_000,
    "actionable-semantic": 300_000,
    "evidence-revalidation": 220_000,
    "semantic-review": 300_000,
    "split-resolution": 300_000,
    "object-boundary": 260_000,
}

BLOCKER_COMPLEXITY = {
    "semantic-easy": 2,
    "semantic-cross-source": 3,
    "semantic-hard": 5,
    "functional-polysemy": 7,
    "split-resolution": 8,
    "multiword-object-boundary": 3,
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


def bounded_threshold_cost(value: int, thresholds: tuple[int, ...]) -> int:
    return sum(1 for threshold in thresholds if value >= threshold)


def evidence_weight(
    row: dict[str, str],
    *,
    lane: str,
    decisions_by_match: dict[str, list[dict[str, str]]],
    fast_info: dict[str, object] | None = None,
) -> int:
    """Estimate semantic decision cost, not raw provenance volume.

    Occurrence/source repetition contributes only bounded diversity cost. True
    polysemy, split state and canonical ambiguity remain expensive.
    """
    if lane == "evidence-revalidation" and fast_info:
        added = fast_info.get("AddedEvidence", [])
        if not isinstance(added, list):
            added = []
        added_sources = {
            str(item.get("SourceID", ""))
            for item in added if isinstance(item, dict) and item.get("SourceID")
        }
        payload_len = len(json.dumps(added, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        return (
            1
            + bounded_threshold_cost(len(added), (4, 12, 30))
            + bounded_threshold_cost(len(added_sources), (4, 8))
            + min(2, payload_len // 16_000)
        )

    blocker_class = row.get("BlockerClass", "")
    weight = BLOCKER_COMPLEXITY.get(blocker_class, 4)

    current_action = row.get("CurrentAction", "")
    durable_count = len(decisions_by_match.get(row.get("MatchKey", ""), []))
    if lane == "split-resolution" or current_action in {"split-required", "multipart-reviewed"}:
        weight += 4
    if durable_count > 1:
        weight += min(6, 2 + durable_count)
    if row.get("CandidateCanonical", ""):
        weight += 2

    occ = max(1, int(row.get("OccurrenceCount", "1") or 1))
    sources = max(1, len([x for x in row.get("SourceIDs", "").split("|") if x]))
    # Repeated evidence is useful, but under Minimal Learner Identity it is not
    # linear review work. Charge only bounded diversity/scale cost.
    weight += bounded_threshold_cost(occ, (8, 20, 50))
    weight += bounded_threshold_cost(sources, (4, 8, 16))

    evidence_bytes = len(row.get("OccurrenceEvidenceJSON", "").encode("utf-8"))
    weight += min(2, evidence_bytes // 16_000)
    return max(1, weight)


def review_payload_bytes(
    row: dict[str, str],
    *,
    lane: str,
    fast_info: dict[str, object] | None,
) -> int:
    if lane == "evidence-revalidation" and fast_info:
        raw = json.dumps(fast_info.get("AddedEvidence", []), ensure_ascii=False, separators=(",", ":"))
        return len(raw.encode("utf-8"))
    return len(row.get("OccurrenceEvidenceJSON", "").encode("utf-8"))


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
            "PacketBytes": plan.get("PacketBytes", 0),
            "PacketByteBudget": plan.get("PacketByteBudget", 0),
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
    total_packet_bytes = 0
    surface_cap = 0
    weight_budget = 0
    effective_budget = 0
    packet_byte_budget = 0
    effective_packet_byte_budget = 0
    skipped_for_packing: list[str] = []
    oversized_single = False
    if selected_lane:
        surface_cap, weight_budget = LIMITS[selected_lane]
        packet_byte_budget = PACKET_BYTE_LIMITS[selected_lane]
        effective_budget = weight_budget
        effective_packet_byte_budget = packet_byte_budget
        weighted: list[tuple[dict[str, str], int, int]] = []
        for row in lane_rows:
            info = fast_info_by_key.get(row.get("MatchKey", ""))
            weighted.append((
                row,
                evidence_weight(
                    row,
                    lane=selected_lane,
                    decisions_by_match=decisions_by_match,
                    fast_info=info,
                ),
                review_payload_bytes(row, lane=selected_lane, fast_info=info),
            ))

        for row, weight, packet_bytes in weighted:
            if len(selected) >= surface_cap:
                break
            if total_weight + weight > weight_budget or total_packet_bytes + packet_bytes > packet_byte_budget:
                skipped_for_packing.append(row.get("MatchKey", ""))
                continue
            selected.append(row)
            total_weight += weight
            total_packet_bytes += packet_bytes

        if not selected and weighted:
            row, weight, packet_bytes = min(
                weighted,
                key=lambda item: (item[1], item[2], item[0].get("MatchKey", "")),
            )
            selected = [row]
            total_weight = weight
            total_packet_bytes = packet_bytes
            effective_budget = max(weight_budget, weight)
            effective_packet_byte_budget = max(packet_byte_budget, packet_bytes)
            oversized_single = weight > weight_budget or packet_bytes > packet_byte_budget
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
        "PacketBytes": total_packet_bytes,
        "PacketByteBudget": effective_packet_byte_budget,
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
        "ReviewPacketVersion": "selected-review-packet-v3",
        "ReviewLane": selected_lane,
        "ReviewMode": plan["ReviewMode"],
        "SelectedMatchKeys": plan["SelectedMatchKeys"],
        "SelectedCount": plan["SelectedCount"],
        "EvidenceWeight": plan["EvidenceWeight"],
        "PacketBytes": plan["PacketBytes"],
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
    print(f"review batch semantic weight = {total_weight} / {effective_budget}")
    print(f"review batch packet bytes = {total_packet_bytes} / {effective_packet_byte_budget}")
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
