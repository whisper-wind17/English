#!/usr/bin/env python3
"""Report missing release-visible fields split by learning admission status."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
STUDY = BASE / "publish" / "study.csv"
ADMISSION = BASE / "learner" / "learning_admission.csv"
COMMON_REQUIRED = (
    "NoteID", "CanonicalWord", "Word", "British", "American", "MeaningPrimary",
    "ExampleSentence", "ExampleTranslation", "LearnerLevel", "Sources", "SourceBooks", "Tags",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    study = read_csv(STUDY)
    admission = {
        r["NoteID"].strip(): r["Status"].strip()
        for r in read_csv(ADMISSION)
        if r.get("LearnerProfile", "").strip() == "klose"
        and r.get("LearnerLevel", "").strip() == "4"
    }
    by_status = Counter()
    fields_by_status: dict[str, Counter[str]] = {"allowed": Counter(), "held": Counter()}
    examples: dict[str, list[str]] = {"allowed": [], "held": []}

    for row in study:
        nid = row["NoteID"].strip()
        status = admission.get(nid, "missing")
        required = list(COMMON_REQUIRED)
        if status == "allowed":
            required.append("LearningOrder")
        missing = [f for f in required if not row.get(f, "").strip()]
        if not missing:
            continue
        by_status[status] += 1
        if status in fields_by_status:
            fields_by_status[status].update(missing)
            if len(examples[status]) < 20:
                examples[status].append(f"{nid}:{','.join(missing)}")

    print(f"Release completeness missing rows by admission: {dict(by_status)}")
    for status in ("allowed", "held"):
        print(f"{status} missing fields: {dict(fields_by_status[status])}")
        print(f"{status} examples: {examples[status]}")

    if by_status.get("allowed", 0):
        raise SystemExit("Current allowed learning set has missing required release fields")


if __name__ == "__main__":
    main()
