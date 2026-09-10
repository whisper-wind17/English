#!/usr/bin/env python3
"""Append the current reviewed-but-unreleased Klose Vocabulary admission set to Release truth.

Release is deliberately separate from Learning Admission. This tool performs one
explicit transition: `allowed ∩ unreleased -> released`, guarded by the current
learner-presentation fingerprint and an expected-count assertion. Existing release
rows are never rewritten or reordered.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from klose_review_fingerprint import fingerprint

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
PROFILE = BASE / "config" / "profile.json"
MASTER = BASE / "master" / "vocabulary_master.csv"
LEARNER = BASE / "learner" / "current.csv"
ADMISSION = BASE / "learner" / "learning_admission.csv"
REVIEW_REGISTRY = BASE / "learner" / "presentation_review_registry.csv"
RELEASE = BASE / "master" / "release_registry.csv"
RELEASE_EXT = BASE / "master" / "release_registry_extensions.csv"
REPORTS = [
    BASE / "review" / "identity_review.csv",
    BASE / "review" / "learner_review.csv",
    BASE / "review" / "future_vocab_review.csv",
]
RELEASE_FIELDS = ["NoteID", "ReleasedAt", "ReleaseReason"]
ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}$")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing release input: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=RELEASE_FIELDS, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--expected-count", type=int, required=True)
    p.add_argument("--released-at", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()

    if args.expected_count < 0:
        raise SystemExit("expected-count must be >= 0")
    if not ISO_DATE_RE.fullmatch(args.released_at):
        raise SystemExit("released-at must be YYYY-MM-DD")
    if not args.reason.strip():
        raise SystemExit("release reason must be non-empty")

    for report in REPORTS:
        rows = read_csv(report)
        if rows:
            raise SystemExit(f"Release allocation blocked: {report.relative_to(ROOT)} has {len(rows)} unresolved rows")

    with PROFILE.open("r", encoding="utf-8") as f:
        profile = json.load(f)
    learner_profile = str(profile["learner_profile"])
    learner_level = str(profile["learner_level"])

    master_rows = read_csv(MASTER)
    learner_rows = read_csv(LEARNER)
    admission_rows = read_csv(ADMISSION)
    review_rows = read_csv(REVIEW_REGISTRY)
    legacy_release_rows = read_csv(RELEASE)
    extension_release_rows = read_csv(RELEASE_EXT)

    master_by_id = {r.get("NoteID", "").strip(): r for r in master_rows}
    learner_by_id = {r.get("NoteID", "").strip(): r for r in learner_rows}
    if "" in master_by_id or len(master_by_id) != len(master_rows):
        raise SystemExit("Vocabulary Master contains invalid/duplicate NoteID")
    if "" in learner_by_id or len(learner_by_id) != len(learner_rows):
        raise SystemExit("Learner current contains invalid/duplicate NoteID")

    release_ids: set[str] = set()
    for row in legacy_release_rows + extension_release_rows:
        nid = row.get("NoteID", "").strip()
        if not nid or nid in release_ids:
            raise SystemExit(f"Invalid/duplicate release NoteID: {nid!r}")
        if not ISO_DATE_RE.fullmatch(row.get("ReleasedAt", "").strip()) or not row.get("ReleaseReason", "").strip():
            raise SystemExit(f"Invalid release metadata: {nid}")
        release_ids.add(nid)

    admission = {
        r.get("NoteID", "").strip(): r
        for r in admission_rows
        if r.get("LearnerProfile", "").strip() == learner_profile
        and r.get("LearnerLevel", "").strip() == learner_level
    }
    if "" in admission or len(admission) != sum(
        1 for r in admission_rows
        if r.get("LearnerProfile", "").strip() == learner_profile
        and r.get("LearnerLevel", "").strip() == learner_level
    ):
        raise SystemExit("Learning Admission contains invalid/duplicate current-scope NoteID")

    allowed = {
        nid for nid, row in admission.items()
        if row.get("Status", "").strip() == "allowed"
    }
    target = allowed - release_ids
    target_ordered = sorted(
        target,
        key=lambda nid: (
            int(admission[nid].get("LearningOrder", "0") or 0),
            int(nid.removeprefix("KV")),
        ),
    )
    if len(target_ordered) != args.expected_count:
        raise SystemExit(
            f"Expected {args.expected_count} allowed-unreleased Notes, found {len(target_ordered)}"
        )

    review_by_key = {
        (r.get("LearnerProfile", "").strip(), r.get("LearnerLevel", "").strip(), r.get("NoteID", "").strip()): r
        for r in review_rows
    }
    for nid in target_ordered:
        if nid not in master_by_id or nid not in learner_by_id:
            raise SystemExit(f"Release target missing Master/Learner presentation: {nid}")
        key = (learner_profile, learner_level, nid)
        review = review_by_key.get(key)
        if review is None:
            raise SystemExit(f"Release target missing review registry row: {nid}")
        if review.get("ReviewStatus", "").strip() not in {"model-reviewed", "human-reviewed"}:
            raise SystemExit(f"Release target is not reviewed: {nid}")
        current_fp = fingerprint(master_by_id[nid], learner_by_id[nid])
        if review.get("ContentFingerprint", "").strip() != current_fp:
            raise SystemExit(f"Release target review fingerprint is stale: {nid}")
        if not admission[nid].get("LearningOrder", "").strip():
            raise SystemExit(f"Release target lacks LearningOrder: {nid}")

    print(
        f"Klose Vocabulary release delta: allowed={len(allowed)}, already_released={len(release_ids)}, "
        f"allowed_unreleased={len(target_ordered)}, apply={args.apply}"
    )
    if target_ordered:
        print(f"Release target range: {target_ordered[0]} .. {target_ordered[-1]}")

    if not args.apply:
        return
    if not target_ordered:
        print("No release rows appended.")
        return

    appended = [
        {"NoteID": nid, "ReleasedAt": args.released_at, "ReleaseReason": args.reason.strip()}
        for nid in target_ordered
    ]
    write_csv(RELEASE_EXT, extension_release_rows + appended)
    print(f"Appended {len(appended)} immutable release-extension rows to {RELEASE_EXT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
