#!/usr/bin/env python3
"""Build a read-only Third-party Stage-B premerge candidate map.

This tool never mutates Klose identity/release state and never authorizes a merge.
It deterministically compares reviewed Stage-A provisional identities with the current
Klose stable Note registry by MatchKey only. Exact MatchKey equality is a candidate
signal, not a same-sense decision.

Audited Stage-A defers are carried forward explicitly rather than silently dropped.
The readiness snapshot is always bound to the current sealed Stage-A checkpoint.
When Stage A still has an active review batch, the snapshot is persisted as current
but gated (`ReadyForPremergeReview=false`) instead of leaving an older ready snapshot.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
PREVIEW = TP / "staging" / "unified_vocabulary_preview.csv"
LEARNER = TP / "learner" / "learner_vocabulary_preview.csv"
REVIEW = TP / "staging" / "review_queue.csv"
OCCURRENCES = TP / "staging" / "occurrences.csv"
DEFER = TP / "audit" / "defer_context.csv"
NEXT_BATCH = TP / "audit" / "next_batch.json"
STAGE_STATUS = TP / "audit" / "stage_a_status.json"
NOTE_REGISTRY = BASE / "master" / "note_registry.csv"
NOTE_EXTENSIONS = BASE / "master" / "note_registry_extensions.csv"
OUT = TP / "premerge"
CANDIDATES = OUT / "identity_candidates.csv"
DEFERRED = OUT / "audited_deferred.csv"
STATUS = OUT / "readiness.json"
POLICY_VERSION = "v6-minimal-identity"
SEALED_STATUS_VERSION = "stage-a-status-v2"

CANDIDATE_FIELDS = [
    "ProvisionalIdentityKey", "CanonicalMatchKey", "LookupMatchKey", "DisplayWord",
    "ThirdPartyTargetSense", "SourceMatchKeys", "SourceOccurrenceCount",
    "LearnerAdmitted", "KloseCandidateClass", "KloseCandidateCount",
    "KloseCandidateNoteIDs", "KloseCandidateSenses", "PremergeStatus", "MergeAuthorized",
]
DEFER_FIELDS = [
    "MatchKey", "DecisionAction", "DecisionStatus", "CandidateSignals",
    "AcceptedPolicyVersion", "DeferReasonCode", "DeferDependency",
    "CarryForwardStatus", "MergeAuthorized",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "" if row.get(k) is None else str(row.get(k, "")) for k in fields})


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return value


def lookup_key(canonical: str) -> str:
    # Stage-A multipart provisional keys are MatchKey#variant. Klose does not know
    # that provisional suffix yet, so premerge candidate discovery uses the source
    # surface key while preserving the full provisional identity in output.
    return canonical.split("#", 1)[0].casefold().strip()


def main() -> None:
    preview = read_csv(PREVIEW)
    learner = read_csv(LEARNER)
    review = read_csv(REVIEW)
    occurrences = read_csv(OCCURRENCES)
    defer = read_csv(DEFER)
    plan = read_json(NEXT_BATCH)
    stage_status = read_json(STAGE_STATUS)

    if stage_status.get("StatusVersion") != SEALED_STATUS_VERSION:
        raise SystemExit(
            f"Premerge requires sealed {SEALED_STATUS_VERSION}; "
            f"actual={stage_status.get('StatusVersion', '')!r}"
        )
    checkpoint = str(stage_status.get("CheckpointFingerprint", "")).strip()
    if not checkpoint:
        raise SystemExit("Sealed Stage-A checkpoint lacks CheckpointFingerprint")
    try:
        sealed_source_count = int(stage_status.get("SourceOccurrences", -1))
    except (TypeError, ValueError):
        raise SystemExit("Sealed Stage-A SourceOccurrences is not an integer")
    if sealed_source_count != len(occurrences):
        raise SystemExit(
            "Stage-A source occurrence count drift before premerge build: "
            f"sealed={sealed_source_count} actual={len(occurrences)}"
        )

    stable_rows = read_csv(NOTE_REGISTRY) + read_csv(NOTE_EXTENSIONS)
    active = [r for r in stable_rows if r.get("Status", "").strip().casefold() == "active"]
    note_ids = [r.get("NoteID", "") for r in active]
    if not all(note_ids) or len(note_ids) != len(set(note_ids)):
        raise SystemExit("Klose active NoteID registry is empty/duplicate across baseline + extensions")

    by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in active:
        key = row.get("MatchKey", "").strip().casefold()
        if not key:
            raise SystemExit(f"Klose active NoteID lacks MatchKey: {row.get('NoteID', '')}")
        by_match[key].append(row)

    learner_ids = {r.get("ProvisionalIdentityKey", "") for r in learner}
    preview_ids = [r.get("ProvisionalIdentityKey", "") for r in preview]
    if not all(preview_ids) or len(preview_ids) != len(set(preview_ids)):
        raise SystemExit("Stage-A Preview ProvisionalIdentityKey is empty/duplicate")
    if not learner_ids <= set(preview_ids):
        raise SystemExit("Learner Preview is not a subset of Identity Preview")

    candidate_rows: list[dict[str, object]] = []
    classes: Counter[str] = Counter()
    for row in preview:
        canonical = row.get("CanonicalMatchKey", "").strip()
        lookup = lookup_key(canonical)
        matches = sorted(by_match.get(lookup, []), key=lambda r: r["NoteID"])
        if not matches:
            cls = "no-existing-match"
            status = "pending-new-identity-review"
        elif len(matches) == 1:
            cls = "exact-single"
            status = "pending-sense-confirmation"
        else:
            cls = "exact-multiple"
            status = "pending-multi-candidate-review"
        classes[cls] += 1
        candidate_rows.append({
            "ProvisionalIdentityKey": row.get("ProvisionalIdentityKey", ""),
            "CanonicalMatchKey": canonical,
            "LookupMatchKey": lookup,
            "DisplayWord": row.get("DisplayWord", ""),
            "ThirdPartyTargetSense": row.get("TargetSense", ""),
            "SourceMatchKeys": row.get("SourceMatchKeys", ""),
            "SourceOccurrenceCount": row.get("SourceOccurrenceCount", ""),
            "LearnerAdmitted": "yes" if row.get("ProvisionalIdentityKey", "") in learner_ids else "no",
            "KloseCandidateClass": cls,
            "KloseCandidateCount": len(matches),
            "KloseCandidateNoteIDs": "|".join(r["NoteID"] for r in matches),
            "KloseCandidateSenses": "|".join(r.get("SenseLabel", "") for r in matches),
            "PremergeStatus": status,
            "MergeAuthorized": "no",
        })

    defer_by_key = {r.get("MatchKey", ""): r for r in defer if r.get("MatchKey", "")}
    review_keys = [r.get("MatchKey", "") for r in review]
    deferred_rows: list[dict[str, object]] = []
    invalid_defer: list[str] = []
    for row in review:
        key = row.get("MatchKey", "")
        accepted = defer_by_key.get(key)
        policy = accepted.get("PolicyVersion", "") if accepted else ""
        if not accepted or policy != POLICY_VERSION:
            invalid_defer.append(key)
        deferred_rows.append({
            "MatchKey": key,
            "DecisionAction": row.get("DecisionAction", ""),
            "DecisionStatus": row.get("DecisionStatus", ""),
            "CandidateSignals": row.get("CandidateSignals", ""),
            "AcceptedPolicyVersion": policy,
            "DeferReasonCode": accepted.get("DeferReasonCode", "") if accepted else "",
            "DeferDependency": accepted.get("DeferDependency", "") if accepted else "",
            "CarryForwardStatus": "audited-defer" if accepted and policy == POLICY_VERSION else "active-blocker",
            "MergeAuthorized": "no",
        })

    selected = plan.get("SelectedMatchKeys", [])
    active_plan = bool(plan.get("ExecutionReady")) or bool(selected)
    ready = not active_plan and not invalid_defer and set(review_keys) == set(defer_by_key)

    write_csv(CANDIDATES, CANDIDATE_FIELDS, candidate_rows)
    write_csv(DEFERRED, DEFER_FIELDS, deferred_rows)
    status = {
        "StatusVersion": "third-party-stage-b-readiness-v2",
        "PolicyVersion": POLICY_VERSION,
        "StageAStatusVersion": SEALED_STATUS_VERSION,
        "StageACheckpointFingerprint": checkpoint,
        "SourceOccurrences": len(occurrences),
        "StageAIdentityCandidates": len(candidate_rows),
        "StageALearnerCandidates": len(learner_ids),
        "AuditedDeferredSurfaces": len(deferred_rows),
        "ActiveReviewBatch": active_plan,
        "KloseActiveNoteIDs": len(active),
        "CandidateClassCounts": dict(sorted(classes.items())),
        "ReadyForPremergeReview": ready,
        "StageBMutationAuthorized": False,
        "StableThirdPartyIDMinted": False,
        "MergeAuthorizedRows": 0,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Stage-A checkpoint = {checkpoint}")
    print(f"Stage-A source occurrences = {len(occurrences)}")
    print(f"Stage-A identity candidates = {len(candidate_rows)}")
    print(f"Stage-A learner candidates = {len(learner_ids)}")
    print(f"audited deferred surfaces carried forward = {len(deferred_rows)}")
    print(f"Klose active NoteIDs = {len(active)}")
    for cls in sorted(classes):
        print(f"premerge candidate {cls} = {classes[cls]}")
    print(f"Stage A active review batch = {'yes' if active_plan else 'no'}")
    print(f"Ready for premerge review = {'yes' if ready else 'no'}")
    print("Stage-B mutation authorized = no")
    print("Stable ThirdPartyID minted = no")
    print("Merge Authorized = no")


if __name__ == "__main__":
    main()
