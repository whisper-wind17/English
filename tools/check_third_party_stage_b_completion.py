#!/usr/bin/env python3
"""Independent Completion Recheck for Third-party Stage-B reconciliation.

With --allow-incomplete the checker validates the current partial closure and exits 0.
When ReviewQueueCount reaches zero it automatically applies the stronger final gate:
every current Stage-A identity candidate must have exactly one current fingerprint-bound
reconciliation decision. This checker never authorizes or performs Klose mutation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
PREMERGE = TP / "premerge"
RECON = TP / "reconciliation"
CANDIDATES = PREMERGE / "identity_candidates.csv"
READINESS = PREMERGE / "readiness.json"
QUEUE = PREMERGE / "reconciliation_review_queue.csv"
SELECTED = PREMERGE / "reconciliation_selected_view.csv"
NEXT = PREMERGE / "reconciliation_next_batch.json"
DECISIONS = RECON / "reconciliation_decisions.csv"
STATUS = TP / "audit" / "stage_a_status.json"

CANDIDATE_FP_FIELDS = [
    "ProvisionalIdentityKey", "CanonicalMatchKey", "LookupMatchKey", "DisplayWord",
    "ThirdPartyTargetSense", "SourceMatchKeys", "SourceOccurrenceCount",
    "LearnerAdmitted", "KloseCandidateClass", "KloseCandidateCount",
    "KloseCandidateNoteIDs", "KloseCandidateSenses",
]


def rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def obj(path: Path) -> dict[str, object]:
    if not path.exists():
        raise SystemExit(f"Missing required JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return value


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def candidate_fp(row: dict[str, str]) -> str:
    payload = {field: row.get(field, "") for field in CANDIDATE_FP_FIELDS}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    readiness = obj(READINESS)
    status = obj(STATUS)
    plan = obj(NEXT)
    candidates = rows(CANDIDATES)
    decisions = rows(DECISIONS)
    queue = rows(QUEUE)
    selected = rows(SELECTED)

    checkpoint = str(status.get("CheckpointFingerprint", "")).strip()
    require(status.get("StatusVersion") == "stage-a-status-v2" and bool(checkpoint),
            "Stage-B completion requires current sealed Stage A")
    require(readiness.get("StageACheckpointFingerprint") == checkpoint,
            "Stage-B readiness checkpoint drift")
    require(readiness.get("ReadyForPremergeReview") is True,
            "Stage-B completion requires ReadyForPremergeReview=true")
    require(readiness.get("StageBMutationAuthorized") is False,
            "Stage-B readiness unexpectedly authorizes mutation")
    require(readiness.get("StableThirdPartyIDMinted") is False,
            "Stage-B premerge unexpectedly minted StableThirdPartyID")
    require(int(readiness.get("MergeAuthorizedRows", -1)) == 0,
            "Stage-B premerge unexpectedly authorizes merge")

    candidate_by_id = {r.get("ProvisionalIdentityKey", ""): r for r in candidates}
    require("" not in candidate_by_id and len(candidate_by_id) == len(candidates),
            "Stage-B candidates have empty/duplicate identity keys")
    decision_by_id = {r.get("ProvisionalIdentityKey", ""): r for r in decisions}
    require("" not in decision_by_id and len(decision_by_id) == len(decisions),
            "Stage-B decisions have empty/duplicate identity keys")
    require(set(decision_by_id) <= set(candidate_by_id),
            "Stage-B durable decision references missing candidate")

    for pid, decision in decision_by_id.items():
        candidate = candidate_by_id[pid]
        require(decision.get("StageACheckpointFingerprint") == checkpoint,
                f"Stage-B decision checkpoint drift: {pid}")
        require(decision.get("CandidateFingerprint") == candidate_fp(candidate),
                f"Stage-B decision candidate fingerprint drift: {pid}")
        require(decision.get("MutationAuthorized", "").casefold() == "no",
                f"Stage-B decision authorizes mutation: {pid}")

    queue_ids = [r.get("ProvisionalIdentityKey", "") for r in queue]
    require(all(queue_ids) and len(queue_ids) == len(set(queue_ids)) if queue else True,
            "Stage-B review queue has empty/duplicate identities")
    expected_unresolved = set(candidate_by_id) - set(decision_by_id)
    require(set(queue_ids) == expected_unresolved,
            "Stage-B review queue does not equal candidates minus current decisions")
    require(int(plan.get("CandidateCount", -1)) == len(candidates),
            "Stage-B completion plan candidate count drift")
    require(int(plan.get("ValidDurableDecisionCount", -1)) == len(decisions),
            "Stage-B completion plan durable decision count drift")
    require(int(plan.get("ReviewQueueCount", -1)) == len(queue),
            "Stage-B completion plan review queue count drift")
    require(plan.get("MutationAuthorized") is False,
            "Stage-B review plan unexpectedly authorizes mutation")

    complete = not queue
    if not complete:
        require(bool(plan.get("ExecutionReady")) and int(plan.get("SelectedCount", 0)) > 0,
                "Incomplete Stage-B queue has no executable/explicit review batch")
        require(selected, "Incomplete Stage-B queue has empty selected view")
        if not args.allow_incomplete:
            raise SystemExit(f"Stage-B reconciliation incomplete: {len(decisions)} / {len(candidates)}")
        print("Third-party Stage-B Completion Recheck = incomplete-valid")
        print(f"current reconciliation closure = {len(decisions)} / {len(candidates)}")
        print(f"remaining review queue = {len(queue)}")
        print(f"next lane = {plan.get('ReviewLane', '')}")
        print("Stage-B mutation authorized = no")
        return

    require(set(decision_by_id) == set(candidate_by_id),
            "Stage-B final decision coverage is not exactly 100%")
    require(not selected, "Stage-B final selected view is not empty")
    require(int(plan.get("SelectedCount", -1)) == 0,
            "Stage-B final SelectedCount is not zero")
    require(plan.get("SelectedProvisionalIdentityKeys") == [],
            "Stage-B final selected identity list is not empty")
    require(plan.get("ExecutionReady") is False,
            "Stage-B final plan remains execution-ready")
    require(plan.get("AutoExecutable") is False,
            "Stage-B final plan remains auto-executable")
    require(plan.get("ReviewLane", "") == "",
            "Stage-B final plan still has a review lane")

    learner_excluded = {
        pid for pid, candidate in candidate_by_id.items()
        if candidate.get("LearnerAdmitted", "").casefold() != "yes"
    }
    for pid in learner_excluded:
        decision = decision_by_id[pid]
        require(decision.get("Action") == "held" and decision.get("Status") == "held",
                f"Learner-excluded identity is not held at final Stage B: {pid}")
        require(not decision.get("ExistingNoteID", "").strip(),
                f"Learner-excluded identity binds ExistingNoteID: {pid}")
        require(not any(decision.get(field, "").strip() for field in
                        ("ProposedCanonicalWord", "ProposedMatchKey", "ProposedSense")),
                f"Learner-excluded identity proposes allocation: {pid}")

    counts = Counter(r.get("Action", "") for r in decisions)
    print("Third-party Stage-B Completion Recheck = pass")
    print(f"Stage-A checkpoint = {checkpoint}")
    print(f"reconciliation closure = {len(decisions)} / {len(candidates)}")
    print(f"learner-excluded held = {len(learner_excluded)}")
    for action in sorted(counts):
        print(f"reconciliation action {action} = {counts[action]}")
    print("review queue = 0")
    print("selected review batch = 0")
    print("Stable NoteID minted = no")
    print("Stage-B mutation authorized = no")
    print("Merge authorized = no")


if __name__ == "__main__":
    main()
