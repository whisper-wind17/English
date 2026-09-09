#!/usr/bin/env python3
"""Validate current durable Stage-B identity reconciliation decisions.

This checker is incremental: every durable row must be valid against the current
sealed Stage-A checkpoint and current premerge candidate, but full candidate coverage
is enforced separately by the Stage-B Completion Recheck. No row authorizes mutation.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
PREMERGE = TP / "premerge"
RECON = TP / "reconciliation"
DECISIONS = RECON / "reconciliation_decisions.csv"
STATUS = TP / "audit" / "stage_a_status.json"
NOTE_REGISTRY = BASE / "master" / "note_registry.csv"
NOTE_EXTENSIONS = BASE / "master" / "note_registry_extensions.csv"

ALLOWED_ACTIONS = {"reuse-existing", "new-stable-identity", "held"}
ALLOWED_STATUS = {"reviewed", "held"}
CANDIDATE_FINGERPRINT_FIELDS = [
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


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def candidate_fingerprint(row: dict[str, str]) -> str:
    payload = {field: row.get(field, "") for field in CANDIDATE_FINGERPRINT_FIELDS}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main() -> None:
    candidates = rows(PREMERGE / "identity_candidates.csv")
    decisions = rows(DECISIONS)
    stage_status = json.loads(STATUS.read_text(encoding="utf-8-sig"))
    checkpoint = stage_status.get("CheckpointFingerprint", "")
    require(stage_status.get("StatusVersion") == "stage-a-status-v2" and bool(checkpoint),
            "Stage-B reconciliation requires a sealed stage-a-status-v2 checkpoint")

    candidate_by_id = {r.get("ProvisionalIdentityKey", ""): r for r in candidates}
    require(len(candidate_by_id) == len(candidates) and "" not in candidate_by_id,
            "Premerge candidate ProvisionalIdentityKey is empty/duplicate")

    decision_keys = [r.get("DecisionKey", "") for r in decisions]
    provisional_keys = [r.get("ProvisionalIdentityKey", "") for r in decisions]
    require(all(decision_keys) and len(decision_keys) == len(set(decision_keys)) if decisions else True,
            "Stage-B reconciliation DecisionKey is empty/duplicate")
    require(all(provisional_keys) and len(provisional_keys) == len(set(provisional_keys)) if decisions else True,
            "Stage-B reconciliation ProvisionalIdentityKey is empty/duplicate")

    stable = rows(NOTE_REGISTRY) + rows(NOTE_EXTENSIONS)
    active = [r for r in stable if r.get("Status", "").casefold() == "active"]
    active_ids = {r.get("NoteID", "") for r in active}
    require(len(active_ids) == len(active) and "" not in active_ids,
            "Klose active NoteID registry is empty/duplicate")

    action_counts: Counter[str] = Counter()
    high_risk_total = sum(
        1 for r in candidates if r.get("KloseCandidateClass", "").endswith("-multiple")
    )
    high_risk_decided = 0

    for decision in decisions:
        pid = decision["ProvisionalIdentityKey"]
        candidate = candidate_by_id.get(pid)
        require(candidate is not None, f"Reconciliation decision references missing candidate: {pid}")
        require(decision.get("StageACheckpointFingerprint") == checkpoint,
                f"Reconciliation decision Stage-A checkpoint drift: {pid}")
        require(decision.get("CandidateFingerprint") == candidate_fingerprint(candidate),
                f"Reconciliation candidate context drift: {pid}")

        action = decision.get("Action", "")
        status = decision.get("Status", "")
        require(action in ALLOWED_ACTIONS, f"Invalid reconciliation Action: {pid}: {action}")
        require(status in ALLOWED_STATUS, f"Invalid reconciliation Status: {pid}: {status}")
        require(decision.get("MutationAuthorized", "").casefold() == "no",
                f"Reconciliation decision unexpectedly authorizes mutation: {pid}")
        require(bool(decision.get("DecisionBasis", "").strip()) and bool(decision.get("Rationale", "").strip()),
                f"Reconciliation decision lacks audit rationale: {pid}")

        candidate_ids = [x for x in candidate.get("KloseCandidateNoteIDs", "").split("|") if x]
        existing = decision.get("ExistingNoteID", "")
        if action == "reuse-existing":
            require(status == "reviewed", f"reuse-existing must be reviewed: {pid}")
            require(bool(existing) and existing in active_ids,
                    f"reuse-existing references non-active/empty NoteID: {pid}: {existing}")
            require(existing in candidate_ids,
                    f"reuse-existing NoteID is not in current candidate context: {pid}: {existing}")
            require(not any(decision.get(field, "").strip() for field in
                            ("ProposedCanonicalWord", "ProposedMatchKey", "ProposedSense")),
                    f"reuse-existing must not propose a new identity: {pid}")
        elif action == "new-stable-identity":
            require(status == "reviewed", f"new-stable-identity must be reviewed: {pid}")
            require(not existing, f"new-stable-identity must not bind existing NoteID: {pid}")
            if candidate_ids:
                require("no-equivalent" in decision.get("DecisionBasis", "").casefold(),
                        f"new-stable-identity with current candidates lacks explicit no-equivalent review: {pid}")
            else:
                require(candidate.get("KloseCandidateClass") == "no-existing-match",
                        f"candidate-free new-stable-identity is not no-existing-match: {pid}")
            require(all(decision.get(field, "").strip() for field in
                        ("ProposedCanonicalWord", "ProposedMatchKey", "ProposedSense")),
                    f"new-stable-identity lacks proposed identity fields: {pid}")
        else:
            require(status == "held", f"held action must have held status: {pid}")
            require(not existing, f"held decision must not bind existing NoteID: {pid}")
            require(not any(decision.get(field, "").strip() for field in
                            ("ProposedCanonicalWord", "ProposedMatchKey", "ProposedSense")),
                    f"held decision must not pre-authorize a proposed stable identity: {pid}")
            if decision.get("DecisionBasis") == "current-learner-policy-exclusion":
                require(candidate.get("LearnerAdmitted", "").casefold() != "yes",
                        f"Learner-policy held row is currently admitted: {pid}")

        if candidate.get("KloseCandidateClass", "").endswith("-multiple"):
            high_risk_decided += 1
        action_counts[action] += 1

    print("Third-party Stage-B incremental reconciliation check = pass")
    print(f"Stage-A checkpoint fingerprint = {checkpoint}")
    print(f"Premerge candidates = {len(candidates)}")
    print(f"Durable current reconciliation decisions = {len(decisions)}")
    print(f"High-risk multiple candidates decided = {high_risk_decided} / {high_risk_total}")
    for action in sorted(action_counts):
        print(f"reconciliation action {action} = {action_counts[action]}")
    print(f"overall reconciliation closure = {len(decisions)} / {len(candidates)}")
    print("All durable decisions current-fingerprint bound = yes")
    print("Stage-B mutation authorized = no")
    print("Stable NoteID minted = no")


if __name__ == "__main__":
    main()
