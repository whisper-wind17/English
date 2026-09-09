#!/usr/bin/env python3
"""Merge transient reviewed Stage-B reconciliation updates into durable decision truth.

The inbox `reconciliation/decision_updates.csv` is transient. Every update must bind
the current sealed Stage-A checkpoint and exact current premerge CandidateFingerprint.
This tool never mutates Klose Master/Learner/Release/Publish/Anki state and never
sets MutationAuthorized=yes.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
PREMERGE = TP / "premerge"
RECON = TP / "reconciliation"
CANDIDATES = PREMERGE / "identity_candidates.csv"
READINESS = PREMERGE / "readiness.json"
DECISIONS = RECON / "reconciliation_decisions.csv"
UPDATES = RECON / "decision_updates.csv"

FIELDS = [
    "DecisionKey", "ProvisionalIdentityKey", "StageACheckpointFingerprint",
    "CandidateFingerprint", "Action", "ExistingNoteID", "ProposedCanonicalWord",
    "ProposedMatchKey", "ProposedSense", "Status", "Confidence",
    "MutationAuthorized", "DecisionBasis", "Rationale",
]
CANDIDATE_FP_FIELDS = [
    "ProvisionalIdentityKey", "CanonicalMatchKey", "LookupMatchKey", "DisplayWord",
    "ThirdPartyTargetSense", "SourceMatchKeys", "SourceOccurrenceCount",
    "LearnerAdmitted", "KloseCandidateClass", "KloseCandidateCount",
    "KloseCandidateNoteIDs", "KloseCandidateSenses",
]
ACTIONS = {"reuse-existing", "new-stable-identity", "held"}
STATUSES = {"reviewed", "held"}


def rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return value


def candidate_fp(row: dict[str, str]) -> str:
    payload = {field: row.get(field, "") for field in CANDIDATE_FP_FIELDS}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def validate_update(
    row: dict[str, str], candidate_by_id: dict[str, dict[str, str]], checkpoint: str
) -> dict[str, str]:
    missing = [field for field in FIELDS if field not in row]
    if missing:
        raise SystemExit(f"decision update missing fields: {missing}")
    out = {field: row.get(field, "") for field in FIELDS}
    pid = out["ProvisionalIdentityKey"]
    if not pid or not out["DecisionKey"]:
        raise SystemExit("decision update has empty DecisionKey/ProvisionalIdentityKey")
    expected_dkey = "reconcile:" + pid.removeprefix("candidate:")
    if out["DecisionKey"] != expected_dkey:
        raise SystemExit(f"decision key is not canonical for {pid}: {out['DecisionKey']}")
    candidate = candidate_by_id.get(pid)
    if candidate is None:
        raise SystemExit(f"decision update references missing current candidate: {pid}")
    if out["StageACheckpointFingerprint"] != checkpoint:
        raise SystemExit(f"decision update Stage-A checkpoint drift: {pid}")
    if out["CandidateFingerprint"] != candidate_fp(candidate):
        raise SystemExit(f"decision update CandidateFingerprint drift: {pid}")
    if out["Action"] not in ACTIONS:
        raise SystemExit(f"invalid reconciliation action: {pid}: {out['Action']}")
    if out["Status"] not in STATUSES:
        raise SystemExit(f"invalid reconciliation status: {pid}: {out['Status']}")
    if out["MutationAuthorized"].casefold() != "no":
        raise SystemExit(f"Stage-B review update authorizes mutation: {pid}")
    if not out["DecisionBasis"].strip() or not out["Rationale"].strip():
        raise SystemExit(f"decision update lacks basis/rationale: {pid}")

    candidate_ids = [x for x in candidate.get("KloseCandidateNoteIDs", "").split("|") if x]
    if out["Action"] == "reuse-existing":
        if out["Status"] != "reviewed":
            raise SystemExit(f"reuse-existing must be reviewed: {pid}")
        if not out["ExistingNoteID"] or out["ExistingNoteID"] not in candidate_ids:
            raise SystemExit(f"reuse-existing NoteID not in current candidate set: {pid}")
        if any(out[field].strip() for field in ("ProposedCanonicalWord", "ProposedMatchKey", "ProposedSense")):
            raise SystemExit(f"reuse-existing unexpectedly proposes a new identity: {pid}")
    elif out["Action"] == "new-stable-identity":
        if out["Status"] != "reviewed" or out["ExistingNoteID"]:
            raise SystemExit(f"new-stable-identity status/existing NoteID invalid: {pid}")
        if not all(out[field].strip() for field in ("ProposedCanonicalWord", "ProposedMatchKey", "ProposedSense")):
            raise SystemExit(f"new-stable-identity lacks proposed identity fields: {pid}")
    else:
        if out["Status"] != "held" or out["ExistingNoteID"]:
            raise SystemExit(f"held decision status/existing NoteID invalid: {pid}")
        if any(out[field].strip() for field in ("ProposedCanonicalWord", "ProposedMatchKey", "ProposedSense")):
            raise SystemExit(f"held decision unexpectedly proposes identity fields: {pid}")
    return out


def main() -> None:
    readiness = read_json(READINESS)
    if readiness.get("ReadyForPremergeReview") is not True:
        raise SystemExit("Stage-B reconciliation updates require ReadyForPremergeReview=true")
    checkpoint = str(readiness.get("StageACheckpointFingerprint", "")).strip()
    if not checkpoint:
        raise SystemExit("Stage-B readiness lacks Stage-A checkpoint")

    candidates = rows(CANDIDATES)
    candidate_by_id = {r.get("ProvisionalIdentityKey", ""): r for r in candidates}
    if "" in candidate_by_id or len(candidate_by_id) != len(candidates):
        raise SystemExit("Premerge candidate identity is empty/duplicate")

    current = rows(DECISIONS)
    updates = rows(UPDATES) if UPDATES.exists() else []
    by_key: dict[str, dict[str, str]] = {}
    order: list[str] = []
    for row in current:
        dkey = row.get("DecisionKey", "")
        if not dkey or dkey in by_key:
            raise SystemExit(f"Durable reconciliation DecisionKey empty/duplicate: {dkey}")
        by_key[dkey] = {field: row.get(field, "") for field in FIELDS}
        order.append(dkey)

    seen: set[str] = set()
    replaced = 0
    appended = 0
    for raw in updates:
        row = validate_update(raw, candidate_by_id, checkpoint)
        dkey = row["DecisionKey"]
        if dkey in seen:
            raise SystemExit(f"Duplicate transient reconciliation DecisionKey: {dkey}")
        seen.add(dkey)
        if dkey in by_key:
            if by_key[dkey].get("ProvisionalIdentityKey") != row["ProvisionalIdentityKey"]:
                raise SystemExit(f"Reconciliation update changes identity binding: {dkey}")
            by_key[dkey] = row
            replaced += 1
        else:
            by_key[dkey] = row
            order.append(dkey)
            appended += 1

    if updates:
        with DECISIONS.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            for dkey in order:
                writer.writerow(by_key[dkey])
    if UPDATES.exists():
        UPDATES.unlink()

    print(f"Stage-B reconciliation updates applied = {len(updates)}")
    print(f"replaced = {replaced}")
    print(f"appended = {appended}")
    print(f"durable reconciliation decisions = {len(by_key)}")
    print("transient reconciliation inbox removed = yes")
    print("Stage-B mutation authorized = no")


if __name__ == "__main__":
    main()
