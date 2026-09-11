#!/usr/bin/env python3
"""Validate the third-party Vocabulary allocation/migration control plane.

The checker binds the plan and authorization manifest to the exact closed Stage-B
truth and current Klose Stable Vocabulary registry. It supports two explicit gate
states: closed (current default) and authorized-pending-apply. Validation never
performs allocation.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
PLAN = TP / "allocation" / "plan.json"
AUTH = TP / "allocation" / "authorization.json"
DECISIONS = TP / "reconciliation" / "reconciliation_decisions.csv"
CANDIDATES = TP / "premerge" / "identity_candidates.csv"
READINESS = TP / "premerge" / "readiness.json"
NEXT_BATCH = TP / "premerge" / "reconciliation_next_batch.json"
ADAPTERS = TP / "config" / "source_adapters.csv"
REGISTRY = BASE / "master" / "note_registry.csv"
REGISTRY_EXT = BASE / "master" / "note_registry_extensions.csv"
NOTE_RE = re.compile(r"^KV(\d{6})$")

EXPECTED_ALLOWED_PATHS = [
    "anki/klose/master/note_registry_extensions.csv",
    "anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv",
]
EXPECTED_FORBIDDEN_LAYERS = [
    "anki/klose/master/source_identity_extensions.csv",
    "anki/klose/learner",
    "anki/klose/publish",
    "anki/klose/anki",
    "anki/klose/expressions",
]
AUTHORIZED_GATES = {
    "ActualMutationAuthorized": True,
    "StableNoteIDAllocationAuthorized": True,
    "MasterSourceMappingMutationAuthorized": False,
    "LearnerMutationAuthorized": False,
    "ReleaseMutationAuthorized": False,
    "PublishMutationAuthorized": False,
    "AnkiMutationAuthorized": False,
}


def rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def obj(path: Path) -> dict[str, object]:
    if not path.exists():
        raise SystemExit(f"Missing required JSON: {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path.relative_to(ROOT)}")
    return value


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def note_num(note_id: str) -> int:
    m = NOTE_RE.fullmatch(note_id)
    if m is None:
        raise SystemExit(f"Invalid NoteID: {note_id!r}")
    return int(m.group(1))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    plan = obj(PLAN)
    auth = obj(AUTH)
    readiness = obj(READINESS)
    next_batch = obj(NEXT_BATCH)

    require(plan.get("PlanVersion") == "third-party-allocation-migration-plan-v1", "Unexpected allocation plan version")
    require(plan.get("PlanStatus") in {"checkpoint-candidate-plan-only", "validated-checkpointed-plan-only"}, "Unexpected allocation plan status")
    require(auth.get("AuthorizationVersion") == "third-party-allocation-authorization-v1", "Unexpected allocation authorization version")
    require(auth.get("Scope") == "stable-vocabulary-identity-and-external-evidence-binding-only", "Allocation authorization scope drift")
    require(auth.get("AllowedMutationPaths") == EXPECTED_ALLOWED_PATHS, "Allocation allowed mutation paths drift")
    require(auth.get("ForbiddenMutationLayers") == EXPECTED_FORBIDDEN_LAYERS, "Allocation forbidden mutation layers drift")

    reg_fields, legacy = rows(REGISTRY)
    ext_fields, ext = rows(REGISTRY_EXT)
    require(reg_fields == ext_fields, "Legacy/extension registry schema drift")
    registry = legacy + ext
    ids = [r.get("NoteID", "").strip() for r in registry]
    require(all(ids) and len(ids) == len(set(ids)), "Stable registry has empty/duplicate NoteID")
    active_ids = {r["NoteID"].strip() for r in registry if r.get("Status", "").strip() == "active"}
    max_id = max(ids, key=note_num)

    truth = plan.get("TruthBoundary")
    auth_truth = auth.get("TruthBoundary")
    require(isinstance(truth, dict), "Plan TruthBoundary missing")
    require(isinstance(auth_truth, dict), "Authorization TruthBoundary missing")
    expected_blobs = {
        "StageBDecisionBlobSHA": DECISIONS,
        "IdentityCandidateBlobSHA": CANDIDATES,
        "NoteRegistryBlobSHA": REGISTRY,
        "NoteRegistryExtensionsBlobSHA": REGISTRY_EXT,
    }
    for key, path in expected_blobs.items():
        actual = git_blob_sha(path)
        require(truth.get(key) == actual, f"Plan truth boundary stale: {key}: plan={truth.get(key)} current={actual}")
        if key != "IdentityCandidateBlobSHA":
            require(auth_truth.get(key) == actual, f"Authorization truth boundary stale: {key}: auth={auth_truth.get(key)} current={actual}")

    baseline = plan.get("RegistryBaseline")
    require(isinstance(baseline, dict), "RegistryBaseline missing")
    require(baseline.get("PersistentRows") == len(registry), "Persistent registry row baseline drift")
    require(baseline.get("ActiveNoteIDs") == len(active_ids), "Active NoteID baseline drift")
    require(baseline.get("MaxNoteID") == max_id, "Max NoteID baseline drift")

    checkpoint = str(readiness.get("StageACheckpointFingerprint", ""))
    require(checkpoint and plan.get("StageACheckpointFingerprint") == checkpoint, "Stage-A checkpoint drift")
    require(auth.get("StageACheckpointFingerprint") == checkpoint, "Authorization Stage-A checkpoint drift")
    require(readiness.get("KloseActiveNoteIDs") == len(active_ids), "Premerge readiness active-NoteID count is stale")
    require(readiness.get("StageBMutationAuthorized") is False, "Premerge unexpectedly authorizes Stage-B mutation")
    require(readiness.get("StableThirdPartyIDMinted") is False, "Premerge unexpectedly reports minted third-party identity")

    _, candidates = rows(CANDIDATES)
    _, decisions = rows(DECISIONS)
    cand_by = {r.get("ProvisionalIdentityKey", ""): r for r in candidates}
    dec_by = {r.get("ProvisionalIdentityKey", ""): r for r in decisions}
    require(len(candidates) == len(cand_by) and all(cand_by), "Candidate identities are empty/duplicate")
    require(len(decisions) == len(dec_by) and all(dec_by), "Reconciliation decisions are empty/duplicate")
    require(set(cand_by) == set(dec_by), "Candidate/decision identity coverage mismatch")

    require(next_batch.get("CandidateCount") == len(candidates), "Next-batch candidate count drift")
    require(next_batch.get("ValidDurableDecisionCount") == len(decisions), "Stage-B durable decision closure drift")
    require(next_batch.get("ReviewQueueCount") == 0 and next_batch.get("SelectedCount") == 0, "Stage-B is no longer closed")
    require(next_batch.get("MutationAuthorized") is False, "Stage-B next-batch unexpectedly authorizes mutation")

    action_counts: Counter[str] = Counter()
    learner_excluded = 0
    new_pairs: set[tuple[str, str]] = set()
    active_pairs = {
        (r.get("MatchKey", "").strip().casefold(), r.get("SenseLabel", "").strip())
        for r in registry if r.get("Status", "").strip() == "active"
    }

    for pid, dec in dec_by.items():
        cand = cand_by[pid]
        action = dec.get("Action", "").strip()
        action_counts[action] += 1
        require(dec.get("StageACheckpointFingerprint", "").strip() == checkpoint, f"Decision checkpoint drift: {pid}")
        require(dec.get("MutationAuthorized", "").strip().casefold() == "no", f"Decision pre-authorizes mutation: {pid}")
        admitted = cand.get("LearnerAdmitted", "").strip().casefold() == "yes"
        if not admitted:
            learner_excluded += 1
            require(action == "held", f"Learner-excluded identity is not held: {pid}")

        existing = dec.get("ExistingNoteID", "").strip()
        proposed_word = dec.get("ProposedCanonicalWord", "").strip()
        proposed_match = dec.get("ProposedMatchKey", "").strip()
        proposed_sense = dec.get("ProposedSense", "").strip()
        status = dec.get("Status", "").strip()

        if action == "reuse-existing":
            require(status == "reviewed", f"Reuse decision not reviewed: {pid}")
            require(existing in active_ids, f"Reuse decision references non-active NoteID: {pid}->{existing}")
            require(not (proposed_word or proposed_match or proposed_sense), f"Reuse decision proposes identity fields: {pid}")
        elif action == "new-stable-identity":
            require(status == "reviewed", f"New identity proposal not reviewed: {pid}")
            require(not existing and proposed_word and proposed_match and proposed_sense, f"New identity proposal fields invalid: {pid}")
            pair = (proposed_match.casefold(), proposed_sense)
            require(pair not in new_pairs, f"Duplicate proposed MatchKey+Sense pair: {pid}")
            require(pair not in active_pairs, f"Proposed new identity exactly duplicates active MatchKey+Sense: {pid}")
            new_pairs.add(pair)
        elif action == "held":
            require(status == "held", f"Held decision status drift: {pid}")
            require(not (existing or proposed_word or proposed_match or proposed_sense), f"Held decision preselects identity mutation: {pid}")
        else:
            raise SystemExit(f"Unexpected Stage-B action: {pid}->{action!r}")

    recon = plan.get("Reconciliation")
    require(isinstance(recon, dict), "Plan Reconciliation summary missing")
    require(recon.get("CandidateCount") == len(candidates), "Plan candidate count drift")
    for action in ("reuse-existing", "new-stable-identity", "held"):
        require(recon.get(action) == action_counts[action], f"Plan action count drift: {action}")
    require(recon.get("LearnerExcludedHeld") == learner_excluded, "Plan learner-excluded held count drift")
    require(recon.get("ReviewQueueCount") == 0 and recon.get("SelectedCount") == 0, "Plan does not represent closed Stage-B")

    new_count = action_counts["new-stable-identity"]
    append_range = plan.get("HypotheticalAppendRange")
    require(isinstance(append_range, dict), "HypotheticalAppendRange missing")
    first = f"KV{note_num(max_id) + 1:06d}"
    last = f"KV{note_num(max_id) + new_count:06d}"
    require(append_range.get("First") == first and append_range.get("Last") == last, "Hypothetical append range drift")
    require(append_range.get("Count") == new_count, "Hypothetical append count drift")
    require(append_range.get("Reserved") is False, "Plan must not reserve NoteIDs before actual mutation")

    contract = plan.get("AllocationContract")
    require(isinstance(contract, dict), "AllocationContract missing")
    require(contract.get("ReuseExistingMutation") == "no-registry-mutation", "Reuse mutation contract drift")
    require(contract.get("NewIdentityMutation") == "append-only-after-explicit-authorization", "New identity mutation contract drift")
    require(contract.get("HeldMutation") == "none", "Held mutation contract drift")
    require(contract.get("AllocationOrder") == "ProvisionalIdentityKey-lexical", "Allocation order must be deterministic")
    require(contract.get("LearnerAdmissionIndependent") is True, "Learner admission must remain independent")
    require(contract.get("ReleaseIndependent") is True and contract.get("AnkiIndependent") is True, "Release/Anki must remain independent")

    _, adapter_rows = rows(ADAPTERS)
    enabled = [r for r in adapter_rows if r.get("Enabled", "").strip().casefold() == "yes"]
    edition_present = False
    for adapter in enabled:
        rel = adapter.get("OccurrencesPath", "").strip()
        require(bool(rel), f"Enabled adapter lacks OccurrencesPath: {adapter}")
        path = ROOT / rel
        fields, _ = rows(path)
        if "SourceEdition" in fields:
            edition_present = True
    provenance = plan.get("SourceProvenance")
    require(isinstance(provenance, dict), "SourceProvenance plan missing")
    require(provenance.get("EnabledAdapters") == len(enabled), "Enabled adapter count drift")
    require(provenance.get("CurrentAdapterOccurrenceSchemaHasSourceEdition") is edition_present, "SourceEdition schema status drift")
    require(edition_present is False, "Third-party source adapters now carry SourceEdition; allocation provenance plan must be redesigned")
    require(provenance.get("MasterSourceMappingPromotionAuthorized") is False, "Master source mapping must remain blocked")

    gates = plan.get("MutationGates")
    require(isinstance(gates, dict) and gates, "MutationGates missing")
    authorized = auth.get("Authorized") is True
    user_evidence = str(auth.get("UserAuthorizationEvidence", "")).strip()
    authorized_at = str(auth.get("AuthorizedAt", "")).strip()
    if authorized:
        require(gates == AUTHORIZED_GATES, "Authorized allocation gate set is not exact")
        require(bool(user_evidence), "Authorized allocation lacks user authorization evidence")
        require(bool(authorized_at), "Authorized allocation lacks AuthorizedAt")
        gate_state = "authorized-pending-apply"
    else:
        require(all(value is False for value in gates.values()), "Closed allocation state must keep all mutation gates false")
        require(not user_evidence and not authorized_at, "Closed authorization state carries stale authorization evidence")
        gate_state = "closed"

    required = plan.get("RequiredBeforeMutation")
    require(isinstance(required, list) and len(required) >= 5, "RequiredBeforeMutation contract incomplete")

    print("Third-party allocation/migration plan check = pass")
    print(f"allocation gate state = {gate_state}")
    print(f"Stage-A checkpoint = {checkpoint}")
    print(f"registry persistent rows = {len(registry)}")
    print(f"registry active NoteIDs = {len(active_ids)}")
    print(f"registry max NoteID = {max_id}")
    print(f"Stage-B reconciliation closure = {len(decisions)} / {len(candidates)}")
    print(f"reuse-existing = {action_counts['reuse-existing']}")
    print(f"new-stable-identity proposals = {action_counts['new-stable-identity']}")
    print(f"held = {action_counts['held']}")
    print(f"learner-excluded held = {learner_excluded}")
    print(f"hypothetical append range = {first}..{last} (NOT RESERVED)")
    print(f"enabled third-party source adapters = {len(enabled)}")
    print("third-party SourceEdition field present = no")
    print("master provenance promotion authorized = no")
    print(f"Stable NoteID allocation authorized = {'yes' if authorized else 'no'}")
    print("Learner/release/publish/Anki mutation authorized = no")


if __name__ == "__main__":
    main()
