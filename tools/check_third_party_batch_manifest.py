#!/usr/bin/env python3
"""Require decision batches to close an execution-ready deterministic plan exactly."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
UPDATES = TP / "review" / "decision_updates.csv"
MANIFEST = TP / "review" / "batch_manifest.json"
PLAN = TP / "audit" / "next_batch.json"


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


def main() -> None:
    updates = read_updates()
    if not updates:
        if MANIFEST.exists():
            raise SystemExit("batch_manifest.json exists without decision_updates.csv rows")
        print("planned batch closure = not applicable (no decision batch)")
        return

    manifest = read_json(MANIFEST, "batch manifest")
    plan = read_json(PLAN, "next batch plan")

    if plan.get("ExecutionReady") is not True:
        reason = str(plan.get("GateReason", "planned batch is not execution-ready"))
        raise SystemExit(f"Next review batch is gated and cannot be executed: {reason}")

    selected = keys(manifest.get("SelectedMatchKeys"), "manifest SelectedMatchKeys")
    planned = keys(plan.get("SelectedMatchKeys"), "plan SelectedMatchKeys")
    touched = list(dict.fromkeys(row.get("MatchKey", "") for row in updates if row.get("MatchKey", "")))

    if not selected:
        raise SystemExit("Execution-ready decision batch has empty SelectedMatchKeys")
    if selected != planned:
        raise SystemExit(
            "Batch manifest does not match deterministic next-batch plan: "
            f"selected={selected[:20]} planned={planned[:20]}"
        )
    if set(touched) != set(selected):
        missing = sorted(set(selected) - set(touched))
        extra = sorted(set(touched) - set(selected))
        raise SystemExit(
            "Selected active batch closure failed: "
            f"missing={missing[:20]} extra={extra[:20]}"
        )
    if int(manifest.get("SelectedCount", -1)) != len(selected):
        raise SystemExit("Batch manifest SelectedCount mismatch")
    if manifest.get("PlanVersion") != plan.get("PlanVersion"):
        raise SystemExit("Batch manifest PlanVersion mismatch")
    if manifest.get("ReviewLane") != plan.get("ReviewLane"):
        raise SystemExit("Batch manifest ReviewLane mismatch")
    if manifest.get("ReviewBundleFingerprint") != plan.get("ReviewBundleFingerprint"):
        raise SystemExit("Batch manifest ReviewBundleFingerprint mismatch")

    print(f"planned batch selected surfaces = {len(selected)}")
    print(f"planned batch touched MatchKeys = {len(set(touched))}")
    print(f"planned batch lane = {plan.get('ReviewLane', '')}")
    print("planned batch execution ready = yes")
    print("selected active batch closure = 100%")


if __name__ == "__main__":
    main()
