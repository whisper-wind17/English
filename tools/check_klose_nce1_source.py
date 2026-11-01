#!/usr/bin/env python3
"""Validate the reconciled Klose NCE1 Smart Edition source reference."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose" / "source_reference" / "new_concept_english_1_staging"
SOURCE = BASE / "vocabulary-smart-2022.csv"
ACTUAL = BASE / "vocabulary.csv"
PROVENANCE = BASE / "source_provenance.json"
SOURCE_ID = "new_concept_english_1"
EDITION = "2022-smart-isbn-9787521336702"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    for path in (SOURCE, ACTUAL, PROVENANCE):
        if not path.exists():
            raise SystemExit(f"Missing NCE1 source input: {path.relative_to(ROOT)}")

    rows = read_csv(SOURCE)
    actual = read_csv(ACTUAL)
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))

    if len(rows) != 906:
        raise SystemExit(f"NCE1 source occurrence count drift: expected=906 got={len(rows)}")
    if len(actual) != 150:
        raise SystemExit(f"NCE1 photographed prefix count drift: expected=150 got={len(actual)}")
    expected_orders = [f"{i:04d}" for i in range(1, len(rows) + 1)]
    if [r["CurriculumOrder"] for r in rows] != expected_orders:
        raise SystemExit("NCE1 CurriculumOrder must be unique and contiguous 0001..0906")

    for row in rows:
        if row.get("SourceID") != SOURCE_ID or row.get("SourceEdition") != EDITION:
            raise SystemExit(f"NCE1 source identity drift: {row}")

    prefix = rows[: len(actual)]
    for index, (source, photo) in enumerate(zip(prefix, actual), start=1):
        expected = (
            photo["Entry"].strip(), photo["PartOfSpeech"].strip(), photo["Meaning"].strip(),
            photo["Lesson"].strip(),
        )
        got = (
            source["Entry"].strip(), source["PartOfSpeech"].strip(), source["Meaning"].strip(),
            source["LessonStart"].strip(),
        )
        if got != expected or source["LessonStart"] != source["LessonEnd"]:
            raise SystemExit(f"NCE1 photographed prefix mismatch at {index}: expected={expected} got={got}")
        if source["EvidenceBasis"] != "klose-actual-textbook-photo" or source["SourceStatus"] != "verified-actual":
            raise SystemExit(f"NCE1 photographed evidence status drift at {index}")

    suffix = rows[len(actual):]
    if any(r["SourceStatus"] != "baseline-reconciled" for r in suffix):
        raise SystemExit("NCE1 reconstructed suffix must remain explicitly baseline-reconciled")
    if any(int(r["LessonStart"]) < 19 for r in suffix):
        raise SystemExit("NCE1 reconstructed suffix unexpectedly overlaps photographed prefix")

    early_words = [r["Entry"] for r in prefix]
    if "South Korean" not in early_words:
        raise SystemExit("Smart Edition delta lost: South Korean missing")
    for legacy_only in ("Korean", "Daewoo", "Fiat"):
        if legacy_only in early_words:
            raise SystemExit(f"Legacy-only Smart Edition delta leaked into verified prefix: {legacy_only}")

    if provenance.get("SourceID") != SOURCE_ID or provenance.get("SourceEdition") != EDITION:
        raise SystemExit("NCE1 provenance identity drift")
    rec = provenance.get("Reconciliation", {})
    if rec.get("ActualPhotoRows") != 150 or rec.get("TotalOccurrenceRows") != 906:
        raise SystemExit("NCE1 provenance counts drift")
    if provenance.get("Status") != "accepted-with-explicit-baseline-provenance":
        raise SystemExit("NCE1 provenance status is not accepted")

    print(
        "NCE1 source OK: "
        f"occurrences={len(rows)}, photographed={len(actual)}, baseline_reconciled={len(suffix)}, "
        f"edition={EDITION}"
    )


if __name__ == "__main__":
    main()
