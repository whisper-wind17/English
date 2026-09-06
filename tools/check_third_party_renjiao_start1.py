#!/usr/bin/env python3
"""Validate Renjiao start1 third-party Stage A staging without touching Klose state."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "anki" / "klose" / "source_reference" / "renjiao_start1_staging"


def read_csv(name: str) -> list[dict[str, str]]:
    path = OUT / name
    if not path.exists():
        raise SystemExit(f"Missing staging file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    occ = read_csv("occurrences.csv")
    cmp_rows = read_csv("comparison_to_beijing_seed.csv")
    surfaces = read_csv("surface_inventory.csv")
    overlap = read_csv("overlap_candidates.csv")
    morph = read_csv("morphology_review_queue.csv")
    new = read_csv("new_surface_candidates.csv")

    if len(occ) != len(cmp_rows):
        raise SystemExit("Occurrence/comparison row count mismatch")

    keys = [r.get("SourceOccurrenceKey", "") for r in occ]
    if not all(keys) or len(keys) != len(set(keys)):
        raise SystemExit("SourceOccurrenceKey must be non-empty and unique")

    books = {(r.get("Grade", ""), r.get("Semester", "")) for r in occ}
    expected = {(str(g), s) for g in range(1, 7) for s in ("上", "下")}
    if books != expected:
        raise SystemExit(f"Expected 12 grade/semester books, got {sorted(books)}")

    surface_keys = [r.get("MatchKey", "") for r in surfaces]
    if not all(surface_keys) or len(surface_keys) != len(set(surface_keys)):
        raise SystemExit("Surface MatchKey must be non-empty and unique")

    allowed = {
        "exact-surface-overlap",
        "format-alias-overlap",
        "morphology-overlap",
        "new-surface-candidate",
    }
    classes = {r.get("StageAClass", "") for r in cmp_rows}
    if not classes <= allowed:
        raise SystemExit(f"Unexpected StageAClass: {sorted(classes - allowed)}")

    for row in cmp_rows:
        if row.get("NeedsSenseReview") != "yes":
            raise SystemExit("All Renjiao Stage A candidates must remain sense-review candidates")
        forbidden = {"CandidateNoteIDs", "ProposedNoteID", "existing-in-klose", "third-party-new"}
        if forbidden & set(row):
            raise SystemExit("Renjiao Stage A output must not encode final Klose-diff fields")

    if len(overlap) + len(morph) + len(new) != len(surfaces):
        raise SystemExit("Surface candidate partitions do not cover surface inventory exactly")

    print(f"Renjiao Stage A Valid = yes")
    print(f"Source occurrences = {len(occ)}")
    print(f"Distinct surfaces = {len(surfaces)}")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
