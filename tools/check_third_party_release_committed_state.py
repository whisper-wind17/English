#!/usr/bin/env python3
"""Protect the committed third-party Vocabulary release checkpoint.

This checker is intentionally about durable release truth, not about creating a
release. It proves that the 2026-09-12 third-party release transaction remains an
append-only, plan-consistent subset of current Vocabulary state.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
PLAN = BASE / "third_party_vocabulary" / "learner" / "stable_learning_admission_plan.csv"
CANDIDATES = BASE / "third_party_vocabulary" / "learner" / "stable_presentation_candidates.csv"
MASTER = BASE / "master" / "vocabulary_master.csv"
ADMISSION = BASE / "learner" / "learning_admission.csv"
REVIEW = BASE / "learner" / "presentation_review_registry.csv"
LEGACY_RELEASE = BASE / "master" / "release_registry.csv"
RELEASE_EXT = BASE / "master" / "release_registry_extensions.csv"

PROFILE = "klose"
LEVEL = "4"
TX_DATE = "2026-09-12"
TX_REASON = "third-party-primary-reviewed-v1"
EXPECTED_PLAN = 2720
EXPECTED_NEW_STABLE = 1821
EXPECTED_TX = 1981
THIRD_PARTY_STAGE = "stage::third-party-primary"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing committed-state input: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fail(message: str) -> None:
    raise SystemExit(f"Third-party committed release invalid: {message}")


def main() -> None:
    plan = read_csv(PLAN)
    candidates = read_csv(CANDIDATES)
    master = read_csv(MASTER)
    admission = read_csv(ADMISSION)
    review = read_csv(REVIEW)
    legacy_release = read_csv(LEGACY_RELEASE)
    release_ext = read_csv(RELEASE_EXT)

    if len(plan) != EXPECTED_PLAN or len({r["NoteID"].strip() for r in plan}) != EXPECTED_PLAN:
        fail(f"learner plan must contain exactly {EXPECTED_PLAN} unique NoteIDs")
    if len(candidates) != EXPECTED_NEW_STABLE or len({r["NoteID"].strip() for r in candidates}) != EXPECTED_NEW_STABLE:
        fail(f"presentation candidates must contain exactly {EXPECTED_NEW_STABLE} unique NoteIDs")

    plan_by_id = {r["NoteID"].strip(): r for r in plan}
    candidate_ids = {r["NoteID"].strip() for r in candidates}
    master_by_id = {r["NoteID"].strip(): r for r in master}
    admission_by_id = {
        r["NoteID"].strip(): r
        for r in admission
        if r.get("LearnerProfile", "").strip() == PROFILE
        and r.get("LearnerLevel", "").strip() == LEVEL
    }
    review_by_id = {
        r["NoteID"].strip(): r
        for r in review
        if r.get("LearnerProfile", "").strip() == PROFILE
        and r.get("LearnerLevel", "").strip() == LEVEL
    }

    release_rows = legacy_release + release_ext
    release_ids: set[str] = set()
    transaction_ids: set[str] = set()
    other_release_ids: set[str] = set()
    for row in release_rows:
        nid = row.get("NoteID", "").strip()
        if not nid or nid in release_ids:
            fail(f"invalid/duplicate release NoteID {nid!r}")
        release_ids.add(nid)
        reason = row.get("ReleaseReason", "").strip()
        released_at = row.get("ReleasedAt", "").strip()
        if reason == TX_REASON:
            if released_at != TX_DATE:
                fail(f"transaction row has wrong date: {nid}={released_at!r}")
            transaction_ids.add(nid)
        else:
            other_release_ids.add(nid)

    plan_ids = set(plan_by_id)
    expected_transaction_ids = plan_ids - other_release_ids
    if transaction_ids != expected_transaction_ids:
        missing = sorted(expected_transaction_ids - transaction_ids)[:10]
        extra = sorted(transaction_ids - expected_transaction_ids)[:10]
        fail(f"transaction set drift: missing={missing} extra={extra}")
    if len(transaction_ids) != EXPECTED_TX:
        fail(f"expected {EXPECTED_TX} transaction rows, got {len(transaction_ids)}")
    if not plan_ids.issubset(release_ids):
        fail(f"learner plan has unreleased NoteIDs: {sorted(plan_ids - release_ids)[:10]}")
    if not candidate_ids.issubset(release_ids):
        fail(f"new Stable candidates have unreleased NoteIDs: {sorted(candidate_ids - release_ids)[:10]}")

    missing_master = sorted(candidate_ids - set(master_by_id))
    if missing_master:
        fail(f"new Stable candidates missing from derived Master: {missing_master[:10]}")
    not_materialized_released = sorted(
        nid for nid in candidate_ids if master_by_id[nid].get("Released", "").strip() != "yes"
    )
    if not_materialized_released:
        fail(f"new Stable candidates are not materialized Released=yes: {not_materialized_released[:10]}")

    bad_admission: list[str] = []
    bad_review: list[str] = []
    for nid, planned in plan_by_id.items():
        current = admission_by_id.get(nid)
        if current is None or current.get("Status", "").strip() != "allowed":
            bad_admission.append(f"{nid}:missing/not-allowed")
            continue
        expected_order = planned.get("ProposedLearningOrder", "").strip()
        if current.get("LearningOrder", "").strip() != expected_order:
            bad_admission.append(f"{nid}:order")
        if planned.get("CurrentStatus", "").strip() != "allowed":
            if current.get("Stage", "").strip() != THIRD_PARTY_STAGE:
                bad_admission.append(f"{nid}:stage")
            expected_tag = planned.get("ProposedLearningTag", "").strip()
            if current.get("LearningTag", "").strip() != expected_tag:
                bad_admission.append(f"{nid}:tag")

        review_row = review_by_id.get(nid)
        if review_row is None or review_row.get("ReviewStatus", "").strip() not in {"model-reviewed", "human-reviewed"}:
            bad_review.append(nid)

    if bad_admission:
        fail(f"admission drift count={len(bad_admission)} examples={bad_admission[:10]}")
    if bad_review:
        fail(f"review approval drift count={len(bad_review)} examples={bad_review[:10]}")

    print(
        "Third-party committed release = PASS: "
        f"plan={len(plan_ids)} new_stable={len(candidate_ids)} transaction={len(transaction_ids)} "
        f"released_total={len(release_ids)} admission_plan_allowed={len(plan_ids)} review_plan_approved={len(plan_ids)}"
    )


if __name__ == "__main__":
    main()
