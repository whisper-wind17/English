#!/usr/bin/env python3
"""Require decision batches to close an execution-ready deterministic plan exactly.

v5 throughput mode allows one compact transient artifact: decision_updates.csv can
carry PlanVersion/ReviewLane/ReviewBundleFingerprint/ReviewPacketFingerprint columns,
so batch_manifest.json is optional. Legacy two-file batches remain supported.
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

COMPACT_META = (
    "PlanVersion", "ReviewLane", "ReviewBundleFingerprint", "ReviewPacketFingerprint",
)


def read_updates() -> list[dict[str, str]]:
    if not UPDATES.exists():
        return []
    with UPDATES.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


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


def compact_metadata(updates: list[dict[str, str]]) -> dict[str, str] | None:
    if not updates:
        return None
    if not all(field in updates[0] for field in COMPACT_META):
        return None
    meta = {field: updates[0].get(field, "") for field in COMPACT_META}
    if not all(meta.values()):
        raise SystemExit("Compact decision_updates.csv has incomplete batch metadata")
    for row in updates[1:]:
        for field, expected in meta.items():
            if row.get(field, "") != expected:
                raise SystemExit(f"Compact decision_updates.csv has inconsistent {field}")
    return meta


def main() -> None:
    updates = read_updates()
    if not updates:
        if MANIFEST.exists():
            raise SystemExit("batch_manifest.json exists without decision_updates.csv rows")
        print("planned batch closure = not applicable (no decision batch)")
        return

    plan = read_json(PLAN, "next batch plan")
    packet = read_json(PACKET, "selected review packet") if PACKET.exists() else {}
    if plan.get("ExecutionReady") is not True:
        reason = str(plan.get("GateReason", "planned batch is not execution-ready"))
        raise SystemExit(f"Next review batch is gated and cannot be executed: {reason}")

    planned = keys(plan.get("SelectedMatchKeys"), "plan SelectedMatchKeys")
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

    compact = compact_metadata(updates)
    mode = "compact-single-file" if compact else "legacy-manifest"
    if compact:
        if MANIFEST.exists():
            raise SystemExit("Compact decision_updates.csv must not be combined with batch_manifest.json")
        if compact["PlanVersion"] != str(plan.get("PlanVersion", "")):
            raise SystemExit("Compact batch PlanVersion mismatch")
        if compact["ReviewLane"] != str(plan.get("ReviewLane", "")):
            raise SystemExit("Compact batch ReviewLane mismatch")
        if compact["ReviewBundleFingerprint"] != str(plan.get("ReviewBundleFingerprint", "")):
            raise SystemExit("Compact batch ReviewBundleFingerprint mismatch")
        if compact["ReviewPacketFingerprint"] != str(plan.get("ReviewPacketFingerprint", "")):
            raise SystemExit("Compact batch ReviewPacketFingerprint mismatch")
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

    if packet:
        packet_selected = keys(packet.get("SelectedMatchKeys"), "packet SelectedMatchKeys")
        if packet_selected != planned:
            raise SystemExit("Selected review packet no longer matches planned batch")
        if packet.get("ReviewBundleFingerprint") != plan.get("ReviewBundleFingerprint"):
            raise SystemExit("Selected review packet bundle fingerprint mismatch")
        if packet.get("ReviewPacketFingerprint") != plan.get("ReviewPacketFingerprint"):
            raise SystemExit("Selected review packet fingerprint mismatch")

    print(f"planned batch selected surfaces = {len(planned)}")
    print(f"planned batch touched MatchKeys = {len(set(touched))}")
    print(f"planned batch lane = {plan.get('ReviewLane', '')}")
    print(f"planned batch review mode = {plan.get('ReviewMode', '')}")
    print(f"planned batch submission mode = {mode}")
    print("planned batch execution ready = yes")
    print("selected active batch closure = 100%")
    print("selected review packet fingerprint bound = yes")


if __name__ == "__main__":
    main()
