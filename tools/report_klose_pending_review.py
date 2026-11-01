#!/usr/bin/env python3
"""Diagnostic-only report of pending Klose Vocabulary learner-review fingerprints."""
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "anki" / "klose" / "learner" / "presentation_review_registry.csv"


def main() -> None:
    with REGISTRY.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    pending = [
        row for row in rows
        if row.get("LearnerProfile", "").strip() == "klose"
        and row.get("LearnerLevel", "").strip() == "4"
        and row.get("ReviewStatus", "").strip() == "pending"
    ]
    pending.sort(key=lambda row: int(row["NoteID"][2:]))
    print(f"PENDING_REVIEW_COUNT\t{len(pending)}")
    for row in pending:
        print(f"PENDING_REVIEW\t{row['NoteID']}\t{row['ContentFingerprint']}")
    if pending:
        raise SystemExit(23)


if __name__ == "__main__":
    main()
