#!/usr/bin/env python3
"""Maintain persistent learner-presentation review state across learner levels.

A review decision is keyed by (LearnerProfile, LearnerLevel, NoteID). Existing
rows are never silently overwritten. New released notes/levels are appended as
pending unless the current presentation already has an explicit model-reviewed
status.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
LEARNER = BASE / "learner" / "current.csv"
MASTER = BASE / "master" / "vocabulary_master.csv"
REGISTRY = BASE / "learner" / "presentation_review_registry.csv"
STATS = BASE / "master" / "build_stats.csv"

FIELDS = [
    "LearnerProfile", "LearnerLevel", "NoteID", "ReviewStatus",
    "ReviewedAt", "ReviewerType", "ReviewNote",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def main() -> None:
    learner = read_csv(LEARNER)
    master = read_csv(MASTER)
    released = {r["NoteID"] for r in master if r.get("Released") == "yes"}
    learner_by_id = {r["NoteID"]: r for r in learner}
    if released - set(learner_by_id):
        raise SystemExit("Released notes are missing learner presentations")

    existing = read_csv(REGISTRY) if REGISTRY.exists() else []
    by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in existing:
        key = (row["LearnerProfile"], row["LearnerLevel"], row["NoteID"])
        if key in by_key:
            raise SystemExit(f"Duplicate learner review registry key: {key}")
        by_key[key] = row

    added = 0
    for nid in sorted(released):
        cur = learner_by_id[nid]
        profile = cur["LearnerProfile"]
        level = cur["LearnerLevel"]
        key = (profile, level, nid)
        if key in by_key:
            continue
        explicit = cur.get("PresentationStatus", "") == f"grade{level}-reviewed"
        row = {
            "LearnerProfile": profile,
            "LearnerLevel": level,
            "NoteID": nid,
            "ReviewStatus": "model-reviewed" if explicit else "pending",
            "ReviewedAt": date.today().isoformat() if explicit else "",
            "ReviewerType": "model" if explicit else "",
            "ReviewNote": "baseline explicit learner override" if explicit else "awaiting explicit learner-level review",
        }
        existing.append(row)
        by_key[key] = row
        added += 1

    existing.sort(key=lambda r: (r["LearnerProfile"], int(r["LearnerLevel"]), r["NoteID"]))
    write_csv(REGISTRY, FIELDS, existing)

    current_keys = {
        (learner_by_id[nid]["LearnerProfile"], learner_by_id[nid]["LearnerLevel"], nid)
        for nid in released
    }
    current_rows = [by_key[k] for k in current_keys]
    reviewed = sum(r["ReviewStatus"] == "model-reviewed" for r in current_rows)
    pending = sum(r["ReviewStatus"] == "pending" for r in current_rows)
    invalid = [r for r in current_rows if r["ReviewStatus"] not in {"model-reviewed", "human-reviewed", "pending"}]
    if invalid:
        raise SystemExit("Invalid ReviewStatus in learner review registry")

    stats = read_csv(STATS)
    metrics = {r["Metric"]: r for r in stats}
    values = {
        "learner_review_registry_current": str(len(current_rows)),
        "learner_model_reviewed_current": str(reviewed),
        "learner_review_pending_current": str(pending),
    }
    for metric, value in values.items():
        if metric in metrics:
            metrics[metric]["Value"] = value
        else:
            row = {"Metric": metric, "Value": value}
            stats.append(row); metrics[metric] = row
    write_csv(STATS, ["Metric", "Value"], stats)
    print(f"Learner review registry: current={len(current_rows)}, reviewed={reviewed}, pending={pending}, added={added}")


if __name__ == "__main__":
    main()
