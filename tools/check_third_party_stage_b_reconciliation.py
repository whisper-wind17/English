#!/usr/bin/env python3
"""Validate durable Stage-B identity reconciliation decisions.

This checker is intentionally read-only. It binds each durable decision to both
the sealed Stage-A checkpoint and the exact current premerge candidate row, so a
change in either source identity state or Klose Stable NoteID context invalidates
old decisions instead of silently carrying them forward.
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
ALLOWED_STATUS = {"reviewed", "held", "pending"}
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
    require(all(decision_keys) and len(decision_keys) == len(set(decision_keys)),
            "Stage-B reconciliation DecisionKey is empty/duplicate")
    require(all(provisional_keys) and len(provisional_keys) == len(set(provisional_keys)),
            "Stage-B reconciliation ProvisionalIdentityKey is empty/duplicate")

    stable = rows(NOTE_REGISTRY) + rows(NOTE_EXTENSIONS)
    active = [r for r in stable if r.get("Status", "").casefold() == "active"]
    active_ids = {r.get("NoteID", "") for r in active}
    require(len(active_ids) == len(active) and "" not in active_ids,
            "Klose active NoteID registry is empty/duplicate")

    action_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    for decision in decisions:
        pid = decision["ProvisionalIdentityKey"]
        candidate = candidate_by_id.get(pid)
        require(candidate is not None, f"Reconciliation decision references missing candidate: {pid}")
        require(decision.get("StageACheckpointFingerprint") == checkpoint,
                f"Reconciliation decision Stage-A checkpoint drift: {pid}")
        current_candidate_fp = candidate_fingerprint(candidate)
        require(decision.get("CandidateFingerprint") == current_candidate_fp,
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
            require(all(decision.get(field, "").strip() for field in
                        ("ProposedCanonicalWord", "ProposedMatchKey", "ProposedSense")),
                    f"new-stable-identity lacks proposed identity fields: {pid}")
        else:
            require(status == "held", f"held action must have held status: {pid}")
            require(not existing, f"held decision must not bind existing NoteID: {pid}")
            require(not any(decision.get(field, "").strip() for field in
                            ("ProposedCanonicalWord", "ProposedMatchKey", "ProposedSense")),
                    f"held decision must not pre-authorize a proposed stable identity: {pid}")

        action_counts[action] += 1
        status_counts[status] += 1

    exact_multiple = {
        r["ProvisionalIdentityKey"] for r in candidates
        if r.get("KloseCandidateClass") == "exact-multiple"
    }
    decided = set(provisional_keys)
    require(exact_multiple <= decided,
            f"Exact-multiple reconciliation coverage incomplete: {sorted(exact_multiple - decided)}")
    high_risk_decisions = [r for r in decisions if r["ProvisionalIdentityKey"] in exact_multiple]
    require(len(high_risk_decisions) == len(exact_multiple),
            "Exact-multiple reconciliation decision cardinality drift")

    reviewed_or_held = sum(1 for r in decisions if r.get("Status") in {"reviewed", "held"})
    require(reviewed_or_held == len(decisions), "Pending reconciliation rows are not allowed in durable reviewed batch")

    print("Third-party Stage-B reconciliation decision check = pass")
    print(f"Stage-A checkpoint fingerprint = {checkpoint}")
    print(f"Premerge candidates = {len(candidates)}")
    print(f"Durable reconciliation decisions = {len(decisions)}")
    print(f"Exact-multiple candidates = {len(exact_multiple)}")
    print("Exact-multiple decision coverage = 100%")
    for action in sorted(action_counts):
        print(f"reconciliation action {action} = {action_counts[action]}")
    print(f"overall reconciliation closure = {len(decisions)} / {len(candidates)}")
    print("Stage-B mutation authorized = no")
    print("Stable NoteID minted = no")


if __name__ == "__main__":
    main()
