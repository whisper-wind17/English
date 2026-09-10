#!/usr/bin/env python3
"""Materialize reviewed/safe Stage-B reconciliation proposals into the transient inbox.

This is a review-truth helper, not a Klose mutation tool. Two inputs are supported:

1. `reconciliation/reviewed_batch.csv` — compact transient HUMAN/MODEL adjudication for
   the exact current selected batch. The tool binds every row to the current sealed
   Stage-A checkpoint and exact current CandidateFingerprint before materializing
   `decision_updates.csv`. The compact file is removed only in the workflow worktree;
   if downstream validation fails, the committed input remains available for retry.
2. Planner lanes explicitly marked AutoExecutable.

If a full explicit `decision_updates.csv` already exists, it is preserved for backward
compatibility. No path here allocates a Stable NoteID or authorizes Klose mutation.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
PREMERGE = TP / "premerge"
RECON = TP / "reconciliation"
NEXT = PREMERGE / "reconciliation_next_batch.json"
SELECTED = PREMERGE / "reconciliation_selected_view.csv"
UPDATES = RECON / "decision_updates.csv"
REVIEWED_BATCH = RECON / "reviewed_batch.csv"

FIELDS = [
    "DecisionKey", "ProvisionalIdentityKey", "StageACheckpointFingerprint",
    "CandidateFingerprint", "Action", "ExistingNoteID", "ProposedCanonicalWord",
    "ProposedMatchKey", "ProposedSense", "Status", "Confidence",
    "MutationAuthorized", "DecisionBasis", "Rationale",
]
REVIEW_FIELDS = [
    "ProvisionalIdentityKey", "Action", "ExistingNoteID", "ProposedCanonicalWord",
    "ProposedMatchKey", "ProposedSense", "Confidence", "DecisionBasis", "Rationale",
]
SAFE_LANES = {"learner-excluded", "exact-single-exact-sense", "no-existing-match"}
ACTIONS = {"reuse-existing", "new-stable-identity", "held"}
CONFIDENCE = {"high", "medium", "low"}


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


def write_updates(updates: list[dict[str, str]]) -> None:
    RECON.mkdir(parents=True, exist_ok=True)
    with UPDATES.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(updates)


def materialize_reviewed_batch(
    state: dict[str, object], selected: list[dict[str, str]], selected_ids: list[str]
) -> None:
    reviewed = rows(REVIEWED_BATCH)
    if not reviewed:
        raise SystemExit("Compact reviewed Stage-B batch is empty")
    if set(reviewed[0]) != set(REVIEW_FIELDS):
        missing = [x for x in REVIEW_FIELDS if x not in reviewed[0]]
        extra = [x for x in reviewed[0] if x not in REVIEW_FIELDS]
        raise SystemExit(f"Compact reviewed batch schema drift: missing={missing} extra={extra}")

    reviewed_ids = [r.get("ProvisionalIdentityKey", "") for r in reviewed]
    if reviewed_ids != selected_ids:
        raise SystemExit(
            "Compact reviewed Stage-B batch must exactly match current selected batch order/closure"
        )
    if len(reviewed_ids) != len(set(reviewed_ids)) or any(not x for x in reviewed_ids):
        raise SystemExit("Compact reviewed Stage-B batch has empty/duplicate identity key")

    checkpoint = str(state.get("StageACheckpointFingerprint", "")).strip()
    if not checkpoint:
        raise SystemExit("Stage-B next batch lacks checkpoint fingerprint")
    selected_by_id = {r["ProvisionalIdentityKey"]: r for r in selected}

    updates: list[dict[str, str]] = []
    for adjudication in reviewed:
        pid = adjudication["ProvisionalIdentityKey"]
        candidate = selected_by_id[pid]
        action = adjudication.get("Action", "")
        existing = adjudication.get("ExistingNoteID", "").strip()
        proposed_word = adjudication.get("ProposedCanonicalWord", "").strip()
        proposed_match = adjudication.get("ProposedMatchKey", "").strip()
        proposed_sense = adjudication.get("ProposedSense", "").strip()
        confidence = adjudication.get("Confidence", "").strip().casefold()
        basis = adjudication.get("DecisionBasis", "").strip()
        rationale = adjudication.get("Rationale", "").strip()
        candidate_ids = [x for x in candidate.get("KloseCandidateNoteIDs", "").split("|") if x]

        if action not in ACTIONS:
            raise SystemExit(f"Compact reviewed batch invalid Action: {pid}: {action}")
        if confidence not in CONFIDENCE:
            raise SystemExit(f"Compact reviewed batch invalid Confidence: {pid}: {confidence}")
        if not basis or not rationale:
            raise SystemExit(f"Compact reviewed batch lacks basis/rationale: {pid}")

        if action == "reuse-existing":
            if not existing or existing not in candidate_ids:
                raise SystemExit(f"Compact reuse NoteID not in current candidate context: {pid}")
            if proposed_word or proposed_match or proposed_sense:
                raise SystemExit(f"Compact reuse unexpectedly proposes identity fields: {pid}")
            status = "reviewed"
        elif action == "new-stable-identity":
            if existing or not (proposed_word and proposed_match and proposed_sense):
                raise SystemExit(f"Compact new identity fields invalid: {pid}")
            if candidate_ids and "no-equivalent" not in basis.casefold():
                raise SystemExit(
                    f"Compact new identity with existing candidates requires explicit no-equivalent review: {pid}"
                )
            status = "reviewed"
        else:
            if existing or proposed_word or proposed_match or proposed_sense:
                raise SystemExit(f"Compact held row pre-authorizes an identity: {pid}")
            status = "held"

        updates.append({
            "DecisionKey": "reconcile:" + pid.removeprefix("candidate:"),
            "ProvisionalIdentityKey": pid,
            "StageACheckpointFingerprint": checkpoint,
            "CandidateFingerprint": candidate["CandidateFingerprint"],
            "Action": action,
            "ExistingNoteID": existing,
            "ProposedCanonicalWord": proposed_word,
            "ProposedMatchKey": proposed_match,
            "ProposedSense": proposed_sense,
            "Status": status,
            "Confidence": confidence,
            "MutationAuthorized": "no",
            "DecisionBasis": basis,
            "Rationale": rationale,
        })

    write_updates(updates)
    REVIEWED_BATCH.unlink()
    print(f"compact reviewed Stage-B batch materialized = {len(updates)}")
    print("current CandidateFingerprint binding = yes")
    print("selected-batch closure = yes")
    print("MutationAuthorized = no")
    print("Stable NoteID allocated = no")


def main() -> None:
    state = obj(NEXT)
    selected = rows(SELECTED)
    selected_ids = [r.get("ProvisionalIdentityKey", "") for r in selected]
    if not all(selected_ids) or len(selected_ids) != len(set(selected_ids)):
        raise SystemExit("Selected Stage-B batch has empty/duplicate identity key")
    if selected_ids != state.get("SelectedProvisionalIdentityKeys", []):
        raise SystemExit("Selected Stage-B view/list drift")

    if UPDATES.exists():
        explicit = rows(UPDATES)
        print(f"explicit Stage-B reconciliation inbox preserved = {len(explicit)}")
        print("automatic proposal materialization = skipped")
        return

    if REVIEWED_BATCH.exists():
        materialize_reviewed_batch(state, selected, selected_ids)
        return

    lane = str(state.get("ReviewLane", ""))
    auto = state.get("AutoExecutable") is True
    if not selected:
        print("Stage-B selected batch empty = yes")
        return
    if not auto or lane not in SAFE_LANES:
        print(f"Stage-B selected lane requires explicit review = {lane}")
        return

    checkpoint = str(state.get("StageACheckpointFingerprint", "")).strip()
    if not checkpoint:
        raise SystemExit("Stage-B next batch lacks checkpoint fingerprint")

    updates: list[dict[str, str]] = []
    for row in selected:
        pid = row["ProvisionalIdentityKey"]
        action = row.get("ProposalAction", "")
        if lane == "learner-excluded":
            if action != "held" or row.get("LearnerAdmitted", "").casefold() == "yes":
                raise SystemExit(f"Unsafe learner-excluded proposal: {pid}")
            updates.append({
                "DecisionKey": "reconcile:" + pid.removeprefix("candidate:"),
                "ProvisionalIdentityKey": pid,
                "StageACheckpointFingerprint": checkpoint,
                "CandidateFingerprint": row["CandidateFingerprint"],
                "Action": "held",
                "ExistingNoteID": "",
                "ProposedCanonicalWord": "",
                "ProposedMatchKey": "",
                "ProposedSense": "",
                "Status": "held",
                "Confidence": "high",
                "MutationAuthorized": "no",
                "DecisionBasis": "current-learner-policy-exclusion",
                "Rationale": "Current learner admission excludes this identity. Retain Source/Identity evidence but do not allocate or merge it into the current Klose learning vocabulary; checkpoint changes force re-review if learner policy changes.",
            })
        elif lane == "exact-single-exact-sense":
            existing = row.get("ProposalExistingNoteID", "")
            if action != "reuse-existing" or not existing:
                raise SystemExit(f"Unsafe exact-sense reuse proposal: {pid}")
            updates.append({
                "DecisionKey": "reconcile:" + pid.removeprefix("candidate:"),
                "ProvisionalIdentityKey": pid,
                "StageACheckpointFingerprint": checkpoint,
                "CandidateFingerprint": row["CandidateFingerprint"],
                "Action": "reuse-existing",
                "ExistingNoteID": existing,
                "ProposedCanonicalWord": "",
                "ProposedMatchKey": "",
                "ProposedSense": "",
                "Status": "reviewed",
                "Confidence": "high",
                "MutationAuthorized": "no",
                "DecisionBasis": "exact-matchkey-and-exact-sense",
                "Rationale": "One current active Klose candidate has the exact MatchKey and byte-for-byte equal learner TargetSense. This records reconciliation equivalence only; no merge or mutation is authorized.",
            })
        elif lane == "no-existing-match":
            if action != "new-stable-identity" or row.get("KloseCandidateNoteIDs", ""):
                raise SystemExit(f"Unsafe no-existing-match proposal: {pid}")
            word = row.get("DisplayWord", "").strip()
            match_key = row.get("LookupMatchKey", "").strip()
            sense = row.get("ThirdPartyTargetSense", "").strip()
            if not word or not match_key or not sense:
                raise SystemExit(f"New-identity proposal lacks identity fields: {pid}")
            updates.append({
                "DecisionKey": "reconcile:" + pid.removeprefix("candidate:"),
                "ProvisionalIdentityKey": pid,
                "StageACheckpointFingerprint": checkpoint,
                "CandidateFingerprint": row["CandidateFingerprint"],
                "Action": "new-stable-identity",
                "ExistingNoteID": "",
                "ProposedCanonicalWord": word,
                "ProposedMatchKey": match_key,
                "ProposedSense": sense,
                "Status": "reviewed",
                "Confidence": "high",
                "MutationAuthorized": "no",
                "DecisionBasis": "no-current-equivalent-candidate-after-variant-scan",
                "Rationale": "Current premerge discovery found no exact MatchKey, conservative space/hyphen-equivalent, or configured spelling-equivalent active Klose identity. Record a proposed new stable identity only; no NoteID is allocated and no Klose state is mutated.",
            })
        else:
            raise SystemExit(f"Unexpected auto-executable Stage-B lane: {lane}")

    write_updates(updates)
    print(f"Stage-B auto proposal lane = {lane}")
    print(f"Stage-B auto proposals materialized = {len(updates)}")
    print("MutationAuthorized = no")
    print("Stable NoteID allocated = no")


if __name__ == "__main__":
    main()
