#!/usr/bin/env python3
"""Seal or verify the validated Third-party Vocabulary Stage-A checkpoint.

The Stage-A planner writes a provisional machine status before the final downstream
Completion Recheck and Klose isolation steps.  This tool upgrades that status only
after those steps have passed and binds it to the exact durable/derived Stage-A
content that Stage B is allowed to consume.

Usage:
    python tools/seal_third_party_stage_a_checkpoint.py seal
    python tools/seal_third_party_stage_a_checkpoint.py verify
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
STATUS = TP / "audit" / "stage_a_status.json"
STATUS_VERSION = "stage-a-status-v2"

# These files are the Stage-A content/truth boundary that Stage-B premerge may
# depend on. stage_a_status.json itself is intentionally excluded to avoid a
# recursive fingerprint.
CHECKPOINT_FILES = [
    TP / "config" / "source_adapters.csv",
    TP / "review" / "identity_decisions.csv",
    TP / "learner" / "grammar_form_quarantine.csv",
    TP / "staging" / "occurrences.csv",
    TP / "staging" / "surface_candidates.csv",
    TP / "staging" / "review_queue.csv",
    TP / "staging" / "unified_vocabulary_preview.csv",
    TP / "learner" / "learner_vocabulary_preview.csv",
    TP / "audit" / "defer_context.csv",
    TP / "audit" / "next_batch.json",
]


def fail(message: str) -> None:
    raise SystemExit(message)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"Missing Stage-A checkpoint input: {rel(path)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        fail(f"Missing Stage-A checkpoint JSON: {rel(path)}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        fail(f"Expected JSON object: {rel(path)}")
    return value


def sha256_file(path: Path) -> str:
    if not path.exists():
        fail(f"Missing Stage-A checkpoint input: {rel(path)}")
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def content_fingerprints() -> dict[str, str]:
    return {rel(path): sha256_file(path) for path in CHECKPOINT_FILES}


def checkpoint_fingerprint(fingerprints: dict[str, str]) -> str:
    raw = json.dumps(fingerprints, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def current_metrics() -> dict[str, int]:
    surfaces = read_csv(TP / "staging" / "surface_candidates.csv")
    review = read_csv(TP / "staging" / "review_queue.csv")
    return {
        "SourceOccurrences": len(read_csv(TP / "staging" / "occurrences.csv")),
        "NormalizedSurfaces": len(surfaces),
        "DurableIdentityDecisions": len(read_csv(TP / "review" / "identity_decisions.csv")),
        "IdentityVocabularyPreview": len(read_csv(TP / "staging" / "unified_vocabulary_preview.csv")),
        "LearnerVocabularyPreview": len(read_csv(TP / "learner" / "learner_vocabulary_preview.csv")),
        "ReviewBlockers": len(review),
        "EvidenceChangedSurfaces": sum(
            1 for row in review
            if "decision-evidence-changed" in row.get("CandidateSignals", "").split("|")
        ),
        "MultipartResolved": sum(
            1 for row in surfaces if row.get("DecisionAction") == "multipart-reviewed"
        ),
        "GrammarFormQuarantineGates": len(read_csv(TP / "learner" / "grammar_form_quarantine.csv")),
    }


def validate_status_against_current(status: dict[str, object]) -> None:
    metrics = current_metrics()
    for key, actual in metrics.items():
        try:
            recorded = int(status.get(key, -1))
        except (TypeError, ValueError):
            fail(f"Stage-A checkpoint metric is not an integer: {key}")
        if recorded != actual:
            fail(f"Stage-A checkpoint metric drift: {key}: recorded={recorded} actual={actual}")

    plan = read_json(TP / "audit" / "next_batch.json")
    recorded_plan = status.get("NextBatch", {})
    if not isinstance(recorded_plan, dict):
        fail("Stage-A checkpoint NextBatch is not an object")
    for key in (
        "PlanVersion", "ReviewLane", "SelectedCount", "SelectedMatchKeys",
        "EvidenceWeight", "EffectiveWeightBudget", "ExecutionReady",
        "ReviewBundleFingerprint", "ReviewPacketFingerprint",
    ):
        if recorded_plan.get(key) != plan.get(key):
            fail(
                f"Stage-A checkpoint next-batch drift: {key}: "
                f"recorded={recorded_plan.get(key)!r} actual={plan.get(key)!r}"
            )


def seal() -> None:
    status = read_json(STATUS)
    validate_status_against_current(status)
    fingerprints = content_fingerprints()
    sealed = dict(status)
    sealed["StatusVersion"] = STATUS_VERSION
    sealed["CheckpointSemantics"] = (
        "sealed only after Stage-A Completion Recheck, learner gate check, "
        "audit-batch recheck, and Klose isolation pass"
    )
    sealed["SealedInputCommit"] = os.environ.get("GITHUB_SHA", status.get("InputCommit", ""))
    sealed["SealedWorkflowRunID"] = os.environ.get("GITHUB_RUN_ID", status.get("WorkflowRunID", ""))
    sealed["SealedWorkflowRunNumber"] = os.environ.get("GITHUB_RUN_NUMBER", status.get("WorkflowRunNumber", ""))
    sealed["ContentFingerprintAlgorithm"] = "sha256-raw-bytes-v1"
    sealed["ContentFingerprints"] = fingerprints
    sealed["CheckpointFingerprint"] = checkpoint_fingerprint(fingerprints)
    STATUS.write_text(json.dumps(sealed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verify()
    print("Stage-A validated checkpoint sealed = yes")


def verify() -> None:
    status = read_json(STATUS)
    if status.get("StatusVersion") != STATUS_VERSION:
        fail(
            f"Stage-A checkpoint is not sealed with {STATUS_VERSION}: "
            f"actual={status.get('StatusVersion', '')!r}"
        )
    if status.get("ContentFingerprintAlgorithm") != "sha256-raw-bytes-v1":
        fail("Stage-A checkpoint fingerprint algorithm drift")

    validate_status_against_current(status)
    expected = status.get("ContentFingerprints")
    if not isinstance(expected, dict):
        fail("Stage-A checkpoint ContentFingerprints missing/not an object")
    actual = content_fingerprints()
    if expected != actual:
        changed = sorted(
            key for key in set(expected) | set(actual)
            if expected.get(key) != actual.get(key)
        )
        fail(f"Stage-A sealed content drift: {changed}")
    aggregate = checkpoint_fingerprint(actual)
    if status.get("CheckpointFingerprint") != aggregate:
        fail("Stage-A aggregate checkpoint fingerprint drift")

    review = read_csv(TP / "staging" / "review_queue.csv")
    defer = read_csv(TP / "audit" / "defer_context.csv")
    review_keys = [row.get("MatchKey", "") for row in review]
    defer_keys = [row.get("MatchKey", "") for row in defer]
    if any(not key for key in review_keys) or len(review_keys) != len(set(review_keys)):
        fail("Stage-A review queue MatchKey is empty/duplicate")
    if any(not key for key in defer_keys) or len(defer_keys) != len(set(defer_keys)):
        fail("Stage-A defer registry MatchKey is empty/duplicate")

    print(f"Stage-A sealed checkpoint version = {STATUS_VERSION}")
    print(f"Stage-A checkpoint files = {len(actual)}")
    print(f"Stage-A checkpoint fingerprint = {aggregate}")
    print("Stage-A sealed content drift = no")
    print("Stage-A review/defer duplicate MatchKey = no")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"seal", "verify"}:
        fail("Usage: seal_third_party_stage_a_checkpoint.py [seal|verify]")
    if sys.argv[1] == "seal":
        seal()
    else:
        verify()


if __name__ == "__main__":
    main()
