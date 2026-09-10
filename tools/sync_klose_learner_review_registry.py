#!/usr/bin/env python3
"""Maintain persistent learner-presentation review state across learner levels.

Review truth is keyed by (LearnerProfile, LearnerLevel, NoteID) and bound to all
release-visible fact/presentation content. Any change invalidates prior approval.
Missing fingerprints are treated as unreviewed; schema migrations must be explicit
and must not silently preserve approval state.
"""
from __future__ import annotations

import csv
from pathlib import Path

from klose_review_fingerprint import fingerprint

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
LEARNER = BASE / "learner" / "current.csv"
MASTER = BASE / "master" / "vocabulary_master.csv"
REGISTRY = BASE / "learner" / "presentation_review_registry.csv"
ADMISSION = BASE / "learner" / "learning_admission.csv"
STATS = BASE / "master" / "build_stats.csv"

FIELDS = [
    "LearnerProfile", "LearnerLevel", "NoteID", "ContentFingerprint",
    "ReviewStatus", "ReviewedAt", "ReviewerType", "ReviewNote",
]
VALID_STATUSES = {"model-reviewed", "human-reviewed", "pending"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def upsert_metric(stats: list[dict[str, str]], metric: str, value: int | str) -> None:
    for row in stats:
        if row["Metric"] == metric:
            row["Value"] = str(value)
            return
    stats.append({"Metric": metric, "Value": str(value)})


def main() -> None:
    learner = read_csv(LEARNER)
    master = read_csv(MASTER)
    master_by_id = {r["NoteID"]: r for r in master}
    released = {r["NoteID"] for r in master if r.get("Released") == "yes"}
    learner_by_id = {r["NoteID"]: r for r in learner}
    if released - set(learner_by_id):
        raise SystemExit("Released notes are missing learner presentations")
    if not ADMISSION.exists():
        raise SystemExit("Learning admission is required before review-registry sync")

    review_keys: set[tuple[str, str, str]] = set()
    for nid in released:
        cur = learner_by_id[nid]
        review_keys.add((cur["LearnerProfile"], cur["LearnerLevel"], nid))

    allowed_count = 0
    for row in read_csv(ADMISSION):
        if row.get("Status", "").strip() != "allowed":
            continue
        allowed_count += 1
        nid = row.get("NoteID", "").strip()
        profile = row.get("LearnerProfile", "").strip()
        level = row.get("LearnerLevel", "").strip()
        if nid not in master_by_id or nid not in learner_by_id:
            raise SystemExit(f"Allowed learning admission lacks Master/Learner row: {nid}")
        cur = learner_by_id[nid]
        if cur.get("LearnerProfile", "").strip() != profile or cur.get("LearnerLevel", "").strip() != level:
            raise SystemExit(f"Allowed admission profile/level mismatch for {nid}")
        review_keys.add((profile, level, nid))

    existing = read_csv(REGISTRY) if REGISTRY.exists() else []
    by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in existing:
        key = (row["LearnerProfile"], row["LearnerLevel"], row["NoteID"])
        if key in by_key:
            raise SystemExit(f"Duplicate learner review registry key: {key}")
        if row.get("ReviewStatus", "") not in VALID_STATUSES:
            raise SystemExit(f"Invalid ReviewStatus in learner review registry: {row}")
        by_key[key] = row

    added = 0
    invalidated = 0
    missing_fingerprint_invalidated = 0
    for profile, level, nid in sorted(review_keys, key=lambda k: (k[0], int(k[1]), k[2])):
        cur = learner_by_id[nid]
        current_fp = fingerprint(master_by_id[nid], cur)
        key = (profile, level, nid)
        if key not in by_key:
            row = {
                "LearnerProfile": profile,
                "LearnerLevel": level,
                "NoteID": nid,
                "ContentFingerprint": current_fp,
                "ReviewStatus": "pending",
                "ReviewedAt": "",
                "ReviewerType": "",
                "ReviewNote": "awaiting explicit learner-level review before release",
            }
            existing.append(row)
            by_key[key] = row
            added += 1
            continue

        row = by_key[key]
        old_fp = row.get("ContentFingerprint", "").strip()
        if not old_fp:
            row["ContentFingerprint"] = current_fp
            row["ReviewStatus"] = "pending"
            row["ReviewedAt"] = ""
            row["ReviewerType"] = ""
            row["ReviewNote"] = "missing fingerprint is unreviewed; explicit approval required"
            missing_fingerprint_invalidated += 1
        elif old_fp != current_fp:
            row["ContentFingerprint"] = current_fp
            row["ReviewStatus"] = "pending"
            row["ReviewedAt"] = ""
            row["ReviewerType"] = ""
            row["ReviewNote"] = "release-visible content changed after previous review; explicit re-review required"
            invalidated += 1

    existing.sort(key=lambda r: (r["LearnerProfile"], int(r["LearnerLevel"]), r["NoteID"]))
    write_csv(REGISTRY, FIELDS, existing)

    required_rows = [by_key[k] for k in review_keys]
    model_reviewed = sum(r["ReviewStatus"] == "model-reviewed" for r in required_rows)
    human_reviewed = sum(r["ReviewStatus"] == "human-reviewed" for r in required_rows)
    pending = sum(r["ReviewStatus"] == "pending" for r in required_rows)

    stats = read_csv(STATS)
    upsert_metric(stats, "learner_review_registry_current", len(required_rows))
    upsert_metric(stats, "learner_model_reviewed_current", model_reviewed)
    upsert_metric(stats, "learner_human_reviewed_current", human_reviewed)
    upsert_metric(stats, "learner_review_pending_current", pending)
    write_csv(STATS, ["Metric", "Value"], stats)
    print(
        "Learner review registry: "
        f"required={len(required_rows)}, released={len(released)}, admitted_allowed={allowed_count}, "
        f"model={model_reviewed}, human={human_reviewed}, pending={pending}, added={added}, "
        f"invalidated={invalidated}, missing_fingerprint_invalidated={missing_fingerprint_invalidated}"
    )

if __name__ == "__main__":
    main()
