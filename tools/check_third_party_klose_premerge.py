#!/usr/bin/env python3
"""Validate read-only Third-party → Klose Stage-B premerge readiness artifacts."""
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
DEFER = TP / "audit" / "defer_context.csv"
NEXT_BATCH = TP / "audit" / "next_batch.json"
NOTE_REGISTRY = BASE / "master" / "note_registry.csv"
NOTE_EXTENSIONS = BASE / "master" / "note_registry_extensions.csv"
POLICY_VERSION = "v6-minimal-identity"


def rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def main() -> None:
    candidates = rows(PREMERGE / "identity_candidates.csv")
    deferred = rows(PREMERGE / "audited_deferred.csv")
    preview = rows(PREVIEW)
    learner = rows(LEARNER)
    review = rows(REVIEW)
    accepted = rows(DEFER)
    status = json.loads((PREMERGE / "readiness.json").read_text(encoding="utf-8"))
    plan = json.loads(NEXT_BATCH.read_text(encoding="utf-8-sig"))

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

    require(plan.get("ExecutionReady") is False and not plan.get("SelectedMatchKeys", []),
            "Stage A still has an active review batch; premerge readiness must remain gated")
    require(status.get("ReadyForPremergeReview") is True,
            "readiness.json did not mark premerge review ready")
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

    print("Third-party Stage-B premerge readiness = pass")
    print(f"Stage-A identity candidates = {len(preview)}")
    print(f"Stage-A learner candidates = {len(learner)}")
    print(f"audited deferred carry-forward = {len(review)}")
    print(f"Klose active NoteIDs = {len(active)}")
    print("Stage A active review batch = no")
    print("Premerge identity coverage = 100%")
    print("Deferred surface coverage = 100%")
    print("Unknown Klose NoteID references = no")
    print("Stage-B mutation authorized = no")
    print("Merge Authorized = no")
    print("Stable ThirdPartyID minted = no")


if __name__ == "__main__":
    main()
