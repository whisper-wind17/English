#!/usr/bin/env python3
"""Validate Beijing Grade1-6 vocabulary pre-merge staging.

This gate proves that staging/review work is structurally complete while also
proving that no staging decision is authorized to mutate the Klose Vocabulary
identity/release state.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "anki" / "klose" / "source_reference" / "beijing_start1_staging"

REQUIRED_FILES = [
    "README.md",
    "occurrences.csv",
    "identity_candidates.csv",
    "surface_inventory.csv",
    "reuse_candidates.csv",
    "identity_review_queue.csv",
    "new_identity_candidates.csv",
    "identity_resolution_review.csv",
    "source_variant_review_queue.csv",
    "source_variant_resolution_review.csv",
    "source_variant_audit.md",
    "semantic_resolution_review.csv",
]


def rows(name: str) -> list[dict[str, str]]:
    path = STAGING / name
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def assert_no_merge_authorized(name: str) -> None:
    data = rows(name)
    if not data:
        return
    if "MergeAuthorized" not in data[0]:
        raise SystemExit(f"{name}: missing MergeAuthorized column")
    bad = [r for r in data if r.get("MergeAuthorized", "").strip().lower() not in {"", "no", "false", "0"}]
    if bad:
        raise SystemExit(f"{name}: staging unexpectedly authorizes merge for {len(bad)} rows")


def main() -> None:
    missing = [name for name in REQUIRED_FILES if not (STAGING / name).exists()]
    if missing:
        raise SystemExit(f"Missing Beijing pre-merge files: {missing}")

    occurrences = rows("occurrences.csv")
    surfaces = rows("surface_inventory.csv")
    high_risk = rows("identity_review_queue.csv")
    high_review = rows("identity_resolution_review.csv")
    variant_q = rows("source_variant_review_queue.csv")
    variant_review = rows("source_variant_resolution_review.csv")

    if len(occurrences) != 808:
        raise SystemExit(f"Expected 808 Beijing occurrences, got {len(occurrences)}")
    if len(surfaces) != 734:
        raise SystemExit(f"Expected 734 Beijing distinct MatchKeys, got {len(surfaces)}")

    books = {(r.get("Grade"), r.get("Semester")) for r in occurrences}
    expected = {(str(g), s) for g in range(1, 7) for s in ("上", "下")}
    if books != expected:
        raise SystemExit(f"Beijing book coverage mismatch: expected {sorted(expected)}, got {sorted(books)}")

    q_keys = {r.get("MatchKey", "") for r in high_risk}
    r_keys = {r.get("MatchKey", "") for r in high_review}
    if q_keys != r_keys:
        raise SystemExit(
            "High-risk identity review coverage mismatch: "
            f"missing={sorted(q_keys-r_keys)}, extra={sorted(r_keys-q_keys)}"
        )

    vq_keys = {r.get("MatchKey", "") for r in variant_q}
    vr_keys = {r.get("MatchKey", "") for r in variant_review}
    if vq_keys != vr_keys:
        raise SystemExit(
            "Source-variant review coverage mismatch: "
            f"missing={sorted(vq_keys-vr_keys)}, extra={sorted(vr_keys-vq_keys)}"
        )

    for name in (
        "identity_resolution_review.csv",
        "source_variant_resolution_review.csv",
        "semantic_resolution_review.csv",
    ):
        assert_no_merge_authorized(name)

    print("Beijing Premerge Valid = yes")
    print("Merge Authorized = no")
    print(f"Source occurrences = {len(occurrences)}")
    print(f"Distinct MatchKeys = {len(surfaces)}")
    print(f"High-risk identity reviews covered = {len(q_keys)}")
    print(f"Source-variant reviews covered = {len(vq_keys)}")


if __name__ == "__main__":
    main()
