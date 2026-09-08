#!/usr/bin/env python3
"""Validate read-only Third-party → Klose Stage-B premerge readiness artifacts.

A premerge snapshot is valid in two states:
- ready: Stage A has no active review batch;
- gated: Stage A still has active review work.

Both states must describe the current sealed Stage-A checkpoint exactly. This avoids
leaving an older `ReadyForPremergeReview=true` artifact when Stage A changes later.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
PREMERGE = TP / "premerge"
PREVIEW = TP / "staging" / "unified_vocabulary_preview.csv"
LEARNER = TP / "learner" / "learner_vocabulary_preview.csv"
REVIEW = TP / "staging" / "review_queue.csv"
OCCURRENCES = TP / "staging" / "occurrences.csv"
DEFER = TP / "audit" / "defer_context.csv"
NEXT_BATCH = TP / "audit" / "next_batch.json"
STAGE_STATUS = TP / "audit" / "stage_a_status.json"
NOTE_REGISTRY = BASE / "master" / "note_registry.csv"
NOTE_EXTENSIONS = BASE / "master" / "note_registry_extensions.csv"
POLICY_VERSION = "v6-minimal-identity"
READINESS_VERSION = "third-party-stage-b-readiness-v2"
SEALED_STATUS_VERSION = "stage-a-status-v2"


def rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def json_obj(path: Path) -> dict[str, object]:
    if not path.exists():
        raise SystemExit(f"Missing required JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return value


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def main() -> None:
    candidates = rows(PREMERGE / "identity_candidates.csv")
    deferred = rows(PREMERGE / "audited_deferred.csv")
    preview = rows(PREVIEW)
    learner = rows(LEARNER)
    review = rows(REVIEW)
    occurrences = rows(OCCURRENCES)
    accepted = rows(DEFER)
    status = json_obj(PREMERGE / "readiness.json")
    plan = json_obj(NEXT_BATCH)
    stage_status = json_obj(STAGE_STATUS)

    require(status.get("StatusVersion") == READINESS_VERSION,
            f"Premerge readiness version drift: {status.get('StatusVersion', '')!r}")
    require(stage_status.get("StatusVersion") == SEALED_STATUS_VERSION,
            f"Stage-A status is not sealed {SEALED_STATUS_VERSION}")
    checkpoint = str(stage_status.get("CheckpointFingerprint", "")).strip()
    require(bool(checkpoint), "Stage-A checkpoint fingerprint missing")
    require(status.get("StageAStatusVersion") == SEALED_STATUS_VERSION,
            "Premerge StageAStatusVersion drift")
    require(status.get("StageACheckpointFingerprint") == checkpoint,
            "Premerge snapshot is not bound to current Stage-A checkpoint")
    require(int(stage_status.get("SourceOccurrences", -1)) == len(occurrences),
            "Sealed Stage-A source count drift")
    require(int(status.get("SourceOccurrences", -1)) == len(occurrences),
            "Premerge SourceOccurrences drift from current Stage-A source union")

    stable = rows(NOTE_REGISTRY) + rows(NOTE_EXTENSIONS)
    active = [r for r in stable if r.get("Status", "").casefold() == "active"]
    active_ids = {r.get("NoteID", "") for r in active}
    require(len(active_ids) == len(active) and "" not in active_ids,
            "Klose active NoteID registry is empty/duplicate")

    preview_ids = {r.get("ProvisionalIdentityKey", "") for r in preview}
    candidate_ids = {r.get("ProvisionalIdentityKey", "") for r in candidates}
    learner_ids = {r.get("ProvisionalIdentityKey", "") for r in learner}
    require(len(preview_ids) == len(preview) and "" not in preview_ids,
            "Stage-A Preview identity key is empty/duplicate")
    require(candidate_ids == preview_ids and len(candidates) == len(preview),
            "Premerge candidate map does not cover Stage-A Identity Preview exactly")
    require(learner_ids <= preview_ids, "Learner Preview is not subset of Identity Preview")

    allowed_classes = {"no-existing-match", "exact-single", "exact-multiple"}
    for row in candidates:
        cls = row.get("KloseCandidateClass", "")
        require(cls in allowed_classes, f"Invalid KloseCandidateClass: {cls}")
        ids = [x for x in row.get("KloseCandidateNoteIDs", "").split("|") if x]
        require(all(x in active_ids for x in ids),
                f"Premerge row references non-active/unknown Klose NoteID: {row.get('ProvisionalIdentityKey')}")
        require(int(row.get("KloseCandidateCount", "-1")) == len(ids),
                f"Candidate count mismatch: {row.get('ProvisionalIdentityKey')}")
        if cls == "no-existing-match":
            require(not ids, f"no-existing-match unexpectedly has Klose NoteID: {row.get('ProvisionalIdentityKey')}")
        elif cls == "exact-single":
            require(len(ids) == 1, f"exact-single must have one Klose NoteID: {row.get('ProvisionalIdentityKey')}")
        else:
            require(len(ids) >= 2, f"exact-multiple must have >=2 Klose NoteIDs: {row.get('ProvisionalIdentityKey')}")
        expected_admit = "yes" if row.get("ProvisionalIdentityKey", "") in learner_ids else "no"
        require(row.get("LearnerAdmitted") == expected_admit,
                f"LearnerAdmitted drift: {row.get('ProvisionalIdentityKey')}")
        require(row.get("MergeAuthorized", "").casefold() == "no",
                f"Premerge row unexpectedly authorizes merge: {row.get('ProvisionalIdentityKey')}")

    review_keys = {r.get("MatchKey", "") for r in review}
    deferred_keys = {r.get("MatchKey", "") for r in deferred}
    accepted_by_key = {r.get("MatchKey", ""): r for r in accepted}
    require(deferred_keys == review_keys and len(deferred) == len(review),
            "Audited-defer carry-forward does not cover current Stage-A review queue")
    for row in deferred:
        key = row.get("MatchKey", "")
        require(row.get("CarryForwardStatus") == "audited-defer",
                f"Stage-A unresolved surface is not accepted audited defer: {key}")
        require(row.get("AcceptedPolicyVersion") == POLICY_VERSION,
                f"Audited defer policy drift: {key}")
        require(accepted_by_key.get(key, {}).get("PolicyVersion") == POLICY_VERSION,
                f"Missing v6 defer registry record: {key}")
        require(row.get("MergeAuthorized", "").casefold() == "no",
                f"Deferred surface unexpectedly authorizes merge: {key}")

    selected = plan.get("SelectedMatchKeys", [])
    active_plan = bool(plan.get("ExecutionReady")) or bool(selected)
    expected_ready = not active_plan
    require(bool(status.get("ActiveReviewBatch")) == active_plan,
            "readiness ActiveReviewBatch drift")
    require(bool(status.get("ReadyForPremergeReview")) == expected_ready,
            "readiness ReadyForPremergeReview does not reflect current Stage-A review gate")
    require(status.get("StageBMutationAuthorized") is False,
            "Stage-B mutation was unexpectedly authorized")
    require(status.get("StableThirdPartyIDMinted") is False,
            "Premerge readiness must not mint Stable ThirdPartyID")
    require(int(status.get("MergeAuthorizedRows", -1)) == 0,
            "Premerge readiness contains authorized merge rows")
    require(int(status.get("StageAIdentityCandidates", -1)) == len(preview),
            "readiness identity count drift")
    require(int(status.get("StageALearnerCandidates", -1)) == len(learner),
            "readiness learner count drift")
    require(int(status.get("AuditedDeferredSurfaces", -1)) == len(review),
            "readiness defer count drift")
    require(int(status.get("KloseActiveNoteIDs", -1)) == len(active),
            "readiness Klose NoteID count drift")

    print("Third-party Stage-B premerge snapshot = pass")
    print(f"Stage-A checkpoint = {checkpoint}")
    print(f"Stage-A source occurrences = {len(occurrences)}")
    print(f"Stage-A identity candidates = {len(preview)}")
    print(f"Stage-A learner candidates = {len(learner)}")
    print(f"audited deferred carry-forward = {len(review)}")
    print(f"Klose active NoteIDs = {len(active)}")
    print(f"Stage A active review batch = {'yes' if active_plan else 'no'}")
    print(f"Premerge review ready = {'yes' if expected_ready else 'no (gated)'}")
    print("Premerge identity coverage = 100%")
    print("Deferred surface coverage = 100%")
    print("Unknown Klose NoteID references = no")
    print("Stage-B mutation authorized = no")
    print("Merge Authorized = no")
    print("Stable ThirdPartyID minted = no")


if __name__ == "__main__":
    main()
