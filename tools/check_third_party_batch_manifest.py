#!/usr/bin/env python3
"""Require decision batches to close an execution-ready deterministic plan exactly.

v5 throughput mode supports three single-file submission contracts in decision_updates.csv:
1) full decision rows + plan/packet metadata;
2) delta-evidence approval rows;
3) mixed delta approvals plus a small number of explicit full-decision overrides.

Delta approvals are materialized here by copying the frozen durable identity content from
selected_review_packet.json and refreshing only evidence binding. Full overrides pay the
normal full-decision cost only for exceptional rows that fail delta semantic review.
Legacy batch_manifest.json + full decision rows remains supported.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
UPDATES = TP / "review" / "decision_updates.csv"
MANIFEST = TP / "review" / "batch_manifest.json"
PLAN = TP / "audit" / "next_batch.json"
PACKET = TP / "audit" / "selected_review_packet.json"

DECISION_FIELDS = [
    "DecisionKey", "MatchKey", "OccurrenceKeys", "Action", "CanonicalMatchKey",
    "ObjectType", "TargetSense", "Status", "Confidence", "DecisionBasis", "Rationale",
]
COMPACT_META = (
    "PlanVersion", "ReviewLane", "ReviewBundleFingerprint", "ReviewPacketFingerprint",
)
DELTA_APPROVAL_MODE = "delta-revalidate"
FULL_OVERRIDE_MODE = "full-decision"
COMPACT_MODES = {DELTA_APPROVAL_MODE, FULL_OVERRIDE_MODE}


def read_updates() -> list[dict[str, str]]:
    if not UPDATES.exists():
        return []
    with UPDATES.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_decisions(rows: list[dict[str, str]]) -> None:
    with UPDATES.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DECISION_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in DECISION_FIELDS} for row in rows)


def read_json(path: Path, label: str) -> dict[str, object]:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid {label} JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Invalid {label}: expected object")
    return value


def keys(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(x, str) and x for x in value):
        raise SystemExit(f"Invalid {label}: expected string list")
    if len(value) != len(set(value)):
        raise SystemExit(f"Invalid {label}: duplicate MatchKey")
    return value


def row_metadata(updates: list[dict[str, str]]) -> dict[str, str] | None:
    if not updates or not all(field in updates[0] for field in COMPACT_META):
        return None
    meta = {field: updates[0].get(field, "") for field in COMPACT_META}
    if not all(meta.values()):
        raise SystemExit("Compact decision_updates.csv has incomplete batch metadata")
    for row in updates[1:]:
        for field, expected in meta.items():
            if row.get(field, "") != expected:
                raise SystemExit(f"Compact decision_updates.csv has inconsistent {field}")
    return meta


def validate_meta(meta: dict[str, str], plan: dict[str, object]) -> None:
    if meta["PlanVersion"] != str(plan.get("PlanVersion", "")):
        raise SystemExit("Compact batch PlanVersion mismatch")
    if meta["ReviewLane"] != str(plan.get("ReviewLane", "")):
        raise SystemExit("Compact batch ReviewLane mismatch")
    if meta["ReviewBundleFingerprint"] != str(plan.get("ReviewBundleFingerprint", "")):
        raise SystemExit("Compact batch ReviewBundleFingerprint mismatch")
    if meta["ReviewPacketFingerprint"] != str(plan.get("ReviewPacketFingerprint", "")):
        raise SystemExit("Compact batch ReviewPacketFingerprint mismatch")


def packet_items(packet: dict[str, object]) -> dict[str, dict[str, object]]:
    items = packet.get("Items")
    if not isinstance(items, list):
        raise SystemExit("Selected review packet lacks Items")
    return {
        str(item.get("MatchKey", "")): item
        for item in items if isinstance(item, dict) and item.get("MatchKey")
    }


def materialize_one_delta(
    approval: dict[str, str],
    *,
    item_by_key: dict[str, dict[str, object]],
) -> dict[str, str]:
    key = approval.get("MatchKey", "")
    item = item_by_key.get(key)
    if not item or item.get("ReviewMode") != "delta-evidence":
        raise SystemExit(f"Delta approval lacks selected delta packet item: {key}")
    durable = item.get("DurableDecision")
    if not isinstance(durable, dict):
        raise SystemExit(f"Delta packet lacks DurableDecision: {key}")
    if durable.get("Action") != "keep-identity" or durable.get("Status") != "reviewed":
        raise SystemExit(f"Delta approval can only refresh reviewed keep identity: {key}")
    target = str(durable.get("TargetSense", "")).strip()
    if not target:
        raise SystemExit(f"Delta approval has empty frozen TargetSense: {key}")
    added = item.get("AddedEvidence")
    if not isinstance(added, list) or not added:
        raise SystemExit(f"Delta approval has no added evidence: {key}")
    sources = sorted({
        str(e.get("SourceID", "")) for e in added
        if isinstance(e, dict) and e.get("SourceID")
    })
    return {
        "DecisionKey": str(durable.get("DecisionKey", "")),
        "MatchKey": key,
        "OccurrenceKeys": "*",
        "Action": str(durable.get("Action", "")),
        "CanonicalMatchKey": str(durable.get("CanonicalMatchKey", "")),
        "ObjectType": str(durable.get("ObjectType", "")),
        "TargetSense": target,
        "Status": str(durable.get("Status", "")),
        "Confidence": str(durable.get("Confidence", "")),
        "DecisionBasis": "delta-evidence-revalidation-v5",
        "Rationale": (
            "Selected delta-evidence packet reviewed; added source evidence remains within the existing "
            f"learner-facing TargetSense. Identity content preserved; evidence binding refreshed. "
            f"AddedEvidence={len(added)}; AddedSources={','.join(sources) or 'unknown'}."
        ),
    }


def materialize_compact_rows(
    updates: list[dict[str, str]],
    *,
    plan: dict[str, object],
    packet: dict[str, object],
) -> tuple[list[dict[str, str]], int, int]:
    if MANIFEST.exists():
        raise SystemExit("Compact v5 submission must not be combined with batch_manifest.json")

    modes = {row.get("ApprovalMode", "") for row in updates}
    invalid = sorted(modes - COMPACT_MODES)
    if invalid:
        raise SystemExit(f"Invalid compact ApprovalMode: {invalid}")
    delta_count = sum(row.get("ApprovalMode") == DELTA_APPROVAL_MODE for row in updates)
    full_count = sum(row.get("ApprovalMode") == FULL_OVERRIDE_MODE for row in updates)

    if delta_count and (
        plan.get("ReviewLane") != "evidence-revalidation"
        or plan.get("ReviewMode") != "delta-evidence"
    ):
        raise SystemExit("delta-revalidate approvals are only valid for evidence-revalidation/delta-evidence plan")

    item_by_key = packet_items(packet)
    materialized: list[dict[str, str]] = []
    for row in updates:
        mode = row.get("ApprovalMode", "")
        if mode == DELTA_APPROVAL_MODE:
            materialized.append(materialize_one_delta(row, item_by_key=item_by_key))
            continue

        key = row.get("MatchKey", "")
        if key not in item_by_key:
            raise SystemExit(f"Full override lacks selected packet item: {key}")
        full = {field: row.get(field, "") for field in DECISION_FIELDS}
        if not full.get("DecisionKey") or not full.get("MatchKey"):
            raise SystemExit(f"Full override missing DecisionKey/MatchKey: {key}")
        if not full.get("OccurrenceKeys"):
            raise SystemExit(f"Full override missing OccurrenceKeys: {key}")
        if not full.get("Action") or not full.get("Status"):
            raise SystemExit(f"Full override missing Action/Status: {key}")
        materialized.append(full)

    write_decisions(materialized)
    return materialized, delta_count, full_count


def main() -> None:
    updates = read_updates()
    if not updates:
        if MANIFEST.exists():
            raise SystemExit("batch_manifest.json exists without decision_updates.csv rows")
        print("planned batch closure = not applicable (no decision batch)")
        return

    plan = read_json(PLAN, "next batch plan")
    packet = read_json(PACKET, "selected review packet")
    if plan.get("ExecutionReady") is not True:
        reason = str(plan.get("GateReason", "planned batch is not execution-ready"))
        raise SystemExit(f"Next review batch is gated and cannot be executed: {reason}")

    planned = keys(plan.get("SelectedMatchKeys"), "plan SelectedMatchKeys")
    packet_selected = keys(packet.get("SelectedMatchKeys"), "packet SelectedMatchKeys")
    if packet_selected != planned:
        raise SystemExit("Selected review packet no longer matches planned batch")
    if packet.get("ReviewBundleFingerprint") != plan.get("ReviewBundleFingerprint"):
        raise SystemExit("Selected review packet bundle fingerprint mismatch")
    if packet.get("ReviewPacketFingerprint") != plan.get("ReviewPacketFingerprint"):
        raise SystemExit("Selected review packet fingerprint mismatch")

    touched = list(dict.fromkeys(row.get("MatchKey", "") for row in updates if row.get("MatchKey", "")))
    if not planned:
        raise SystemExit("Execution-ready decision batch has empty SelectedMatchKeys")
    if set(touched) != set(planned):
        missing = sorted(set(planned) - set(touched))
        extra = sorted(set(touched) - set(planned))
        raise SystemExit(
            "Selected active batch closure failed: "
            f"missing={missing[:20]} extra={extra[:20]}"
        )

    meta = row_metadata(updates)
    is_compact = "ApprovalMode" in updates[0]
    delta_count = 0
    full_override_count = 0
    if is_compact:
        if not meta:
            raise SystemExit("Compact approval rows require batch metadata")
        validate_meta(meta, plan)
        updates, delta_count, full_override_count = materialize_compact_rows(
            updates, plan=plan, packet=packet
        )
        if delta_count and full_override_count:
            mode = "mixed-delta-full-single-file"
        elif delta_count:
            mode = "delta-approval-single-file"
        else:
            mode = "compact-full-decision-single-file"
    elif meta:
        if MANIFEST.exists():
            raise SystemExit("Compact decision_updates.csv must not be combined with batch_manifest.json")
        validate_meta(meta, plan)
        mode = "compact-full-decision-single-file"
    else:
        manifest = read_json(MANIFEST, "batch manifest")
        selected = keys(manifest.get("SelectedMatchKeys"), "manifest SelectedMatchKeys")
        if selected != planned:
            raise SystemExit(
                "Batch manifest does not match deterministic next-batch plan: "
                f"selected={selected[:20]} planned={planned[:20]}"
            )
        if int(manifest.get("SelectedCount", -1)) != len(selected):
            raise SystemExit("Batch manifest SelectedCount mismatch")
        if manifest.get("PlanVersion") != plan.get("PlanVersion"):
            raise SystemExit("Batch manifest PlanVersion mismatch")
        if manifest.get("ReviewLane") != plan.get("ReviewLane"):
            raise SystemExit("Batch manifest ReviewLane mismatch")
        if manifest.get("ReviewBundleFingerprint") != plan.get("ReviewBundleFingerprint"):
            raise SystemExit("Batch manifest ReviewBundleFingerprint mismatch")
        packet_fp = manifest.get("ReviewPacketFingerprint")
        if packet_fp and packet_fp != plan.get("ReviewPacketFingerprint"):
            raise SystemExit("Batch manifest ReviewPacketFingerprint mismatch")
        mode = "legacy-manifest"

    print(f"planned batch selected surfaces = {len(planned)}")
    print(f"planned batch touched MatchKeys = {len(set(touched))}")
    print(f"planned batch lane = {plan.get('ReviewLane', '')}")
    print(f"planned batch review mode = {plan.get('ReviewMode', '')}")
    print(f"planned batch submission mode = {mode}")
    if is_compact:
        print(f"delta approvals materialized = {delta_count}")
        print(f"full decision overrides materialized = {full_override_count}")
        if delta_count:
            print("delta approval preserves frozen identity content = yes")
        if full_override_count:
            print("exception rows pay full decision cost only = yes")
    print("planned batch execution ready = yes")
    print("selected active batch closure = 100%")
    print("selected review packet fingerprint bound = yes")


if __name__ == "__main__":
    main()
