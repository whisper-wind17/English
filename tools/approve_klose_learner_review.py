#!/usr/bin/env python3
"""Explicitly approve the current learner presentation after real review.

This tool is deliberately NOT part of normal CI. It records an immutable approval
batch and updates presentation_review_registry.csv only when the current release-
visible fingerprints and quality reports are clean. Content changes later are
invalidated by sync_klose_learner_review_registry.py.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

from klose_review_fingerprint import fingerprint

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master" / "vocabulary_master.csv"
LEARNER = BASE / "learner" / "current.csv"
REGISTRY = BASE / "learner" / "presentation_review_registry.csv"
STATS = BASE / "master" / "build_stats.csv"
APPROVAL_DIR = BASE / "learner" / "review_approvals"
REPORTS = [
    BASE / "review" / "identity_review.csv",
    BASE / "review" / "learner_review.csv",
    BASE / "review" / "future_vocab_review.csv",
]
REGISTRY_FIELDS = [
    "LearnerProfile", "LearnerLevel", "NoteID", "ContentFingerprint",
    "ReviewStatus", "ReviewedAt", "ReviewerType", "ReviewNote",
]
APPROVAL_FIELDS = [
    "BatchID", "LearnerProfile", "LearnerLevel", "NoteID", "ContentFingerprint",
    "ReviewStatus", "ReviewedAt", "ReviewerType", "ReviewNote",
]


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
    p = argparse.ArgumentParser()
    p.add_argument("--batch-id", required=True)
    p.add_argument("--profile", required=True)
    p.add_argument("--level", type=int, required=True)
    p.add_argument("--expected-count", type=int, required=True)
    p.add_argument("--reviewer-type", choices=["model", "human"], required=True)
    p.add_argument("--review-note", required=True)
    p.add_argument("--confirm-all-current", action="store_true")
    args = p.parse_args()
    if not args.confirm_all_current:
        raise SystemExit("Refusing approval without --confirm-all-current")
    if not args.batch_id.replace("-", "").replace("_", "").isalnum():
        raise SystemExit("batch-id may contain only letters, digits, '-' and '_'")

    for path in (MASTER, LEARNER, REGISTRY, STATS, *REPORTS):
        if not path.exists():
            raise SystemExit(f"Missing input: {path.relative_to(ROOT)}")
    for report in REPORTS:
        rows = read_csv(report)
        if rows:
            raise SystemExit(f"Cannot approve while review report is non-empty: {report.relative_to(ROOT)} ({len(rows)} rows)")

    approval_path = APPROVAL_DIR / f"{args.batch_id}.csv"
    if approval_path.exists():
        raise SystemExit(f"Approval batch already exists and is immutable: {approval_path.relative_to(ROOT)}")

    master_rows = read_csv(MASTER)
    learner_rows = read_csv(LEARNER)
    registry_rows = read_csv(REGISTRY)
    master_by_id = {r["NoteID"]: r for r in master_rows}
    learner_by_id = {r["NoteID"]: r for r in learner_rows}
    registry_by_key = {
        (r["LearnerProfile"], r["LearnerLevel"], r["NoteID"]): r for r in registry_rows
    }

    current_ids = sorted(
        r["NoteID"] for r in master_rows
        if r.get("Released") == "yes"
        and r["NoteID"] in learner_by_id
        and learner_by_id[r["NoteID"]].get("LearnerProfile") == args.profile
        and learner_by_id[r["NoteID"]].get("LearnerLevel") == str(args.level)
    )
    if len(current_ids) != args.expected_count:
        raise SystemExit(f"Expected {args.expected_count} current notes, found {len(current_ids)}")

    reviewed_at = date.today().isoformat()
    status = "human-reviewed" if args.reviewer_type == "human" else "model-reviewed"
    approval_rows: list[dict[str, str]] = []
    for nid in current_ids:
        key = (args.profile, str(args.level), nid)
        if key not in registry_by_key:
            raise SystemExit(f"Missing registry row: {key}")
        row = registry_by_key[key]
        current_fp = fingerprint(master_by_id[nid], learner_by_id[nid])
        if row.get("ContentFingerprint", "") != current_fp:
            raise SystemExit(f"Registry fingerprint does not match current content: {nid}")
        row["ReviewStatus"] = status
        row["ReviewedAt"] = reviewed_at
        row["ReviewerType"] = args.reviewer_type
        row["ReviewNote"] = args.review_note
        approval_rows.append({
            "BatchID": args.batch_id,
            "LearnerProfile": args.profile,
            "LearnerLevel": str(args.level),
            "NoteID": nid,
            "ContentFingerprint": current_fp,
            "ReviewStatus": status,
            "ReviewedAt": reviewed_at,
            "ReviewerType": args.reviewer_type,
            "ReviewNote": args.review_note,
        })

    registry_rows.sort(key=lambda r: (r["LearnerProfile"], int(r["LearnerLevel"]), r["NoteID"]))
    write_csv(REGISTRY, REGISTRY_FIELDS, registry_rows)
    write_csv(approval_path, APPROVAL_FIELDS, approval_rows)

    stats = read_csv(STATS)
    current_rows = [registry_by_key[(args.profile, str(args.level), nid)] for nid in current_ids]
    model_count = sum(r["ReviewStatus"] == "model-reviewed" for r in current_rows)
    human_count = sum(r["ReviewStatus"] == "human-reviewed" for r in current_rows)
    pending_count = sum(r["ReviewStatus"] == "pending" for r in current_rows)
    upsert_metric(stats, "learner_review_registry_current", len(current_rows))
    upsert_metric(stats, "learner_model_reviewed_current", model_count)
    upsert_metric(stats, "learner_human_reviewed_current", human_count)
    upsert_metric(stats, "learner_review_pending_current", pending_count)
    write_csv(STATS, ["Metric", "Value"], stats)

    print(
        f"Approved learner review batch {args.batch_id}: count={len(current_ids)}, "
        f"status={status}, pending={pending_count}, manifest={approval_path.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
