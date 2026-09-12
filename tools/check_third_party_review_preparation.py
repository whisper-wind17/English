#!/usr/bin/env python3
"""Independent validator for third-party learner/pronunciation review preparation."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
OUT = TP / "review_preparation"
REVIEW_DIR = OUT / "learner_review_packets"
PRON_DIR = OUT / "pronunciation_review_packets"
MANIFEST = OUT / "manifest.json"
MASTER = BASE / "master" / "vocabulary_master.csv"
ADMISSION = BASE / "learner" / "learning_admission.csv"
REVIEW = BASE / "learner" / "presentation_review_registry.csv"
RELEASE = BASE / "master" / "release_registry.csv"
RELEASE_EXT = BASE / "master" / "release_registry_extensions.csv"
PROFILE = "klose"
LEVEL = "4"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def packet_rows(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for p in sorted(path.glob("batch_*.csv")):
        rows.extend(read_csv(p))
    return rows


def fail(msg: str) -> None:
    raise SystemExit(msg)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    master = {r["NoteID"].strip(): r for r in read_csv(MASTER)}
    admission = {
        r["NoteID"].strip(): r for r in read_csv(ADMISSION)
        if r.get("LearnerProfile", "").strip() == PROFILE
        and r.get("LearnerLevel", "").strip() == LEVEL
    }
    review = {
        r["NoteID"].strip(): r for r in read_csv(REVIEW)
        if r.get("LearnerProfile", "").strip() == PROFILE
        and r.get("LearnerLevel", "").strip() == LEVEL
    }
    released = {r["NoteID"].strip() for r in read_csv(RELEASE) + read_csv(RELEASE_EXT)}
    allowed = {nid for nid, r in admission.items() if r.get("Status", "").strip() == "allowed"}
    expected_pending = {
        nid for nid in allowed
        if review.get(nid, {}).get("ReviewStatus", "").strip() == "pending"
    }
    expected_pron = {
        nid for nid in allowed
        if not master[nid].get("British", "").strip() or not master[nid].get("American", "").strip()
    }

    review_rows = packet_rows(REVIEW_DIR)
    pron_rows = packet_rows(PRON_DIR)
    review_ids = [r.get("NoteID", "").strip() for r in review_rows]
    pron_ids = [r.get("NoteID", "").strip() for r in pron_rows]

    if len(review_ids) != len(set(review_ids)) or set(review_ids) != expected_pending:
        fail(f"Pending review packet identity closure failed: packet={len(set(review_ids))} expected={len(expected_pending)}")
    if len(pron_ids) != len(set(pron_ids)) or set(pron_ids) != expected_pron:
        fail(f"Pronunciation debt packet identity closure failed: packet={len(set(pron_ids))} expected={len(expected_pron)}")

    for r in review_rows:
        if not r.get("ContentFingerprint", "").strip(): fail(f"Blank review fingerprint: {r.get('NoteID')}")
        if not r.get("MeaningPrimary", "").strip(): fail(f"Blank MeaningPrimary: {r.get('NoteID')}")
        if not r.get("ExampleSentence", "").strip() or not r.get("ExampleTranslation", "").strip():
            fail(f"Blank bilingual example: {r.get('NoteID')}")
        if r.get("AdmissionStage", "").strip() not in {"stage::third-party-primary", "stage::grade4-current", "stage::grade5-6-current"}:
            fail(f"Unexpected pending admission stage: {r.get('NoteID')}={r.get('AdmissionStage')}")

    for r in pron_rows:
        nid = r.get("NoteID", "").strip()
        if not r.get("CandidateBritish", "").strip() or not r.get("CandidateAmerican", "").strip():
            fail(f"Blank pronunciation candidate: {nid}")
        if r.get("CandidateEngine") != "espeak-ng": fail(f"Unexpected pronunciation engine: {nid}")
        expected_release = "released" if nid in released else "unreleased"
        if r.get("ReleaseState") != expected_release: fail(f"Release-state drift in pronunciation packet: {nid}")
        missing = set(r.get("MissingSides", "").split("+"))
        if "British" not in missing and r.get("ExistingBritish", "").strip() != r.get("CandidateBritish", "").strip():
            fail(f"Existing British pronunciation changed in candidate packet: {nid}")
        if "American" not in missing and r.get("ExistingAmerican", "").strip() != r.get("CandidateAmerican", "").strip():
            fail(f"Existing American pronunciation changed in candidate packet: {nid}")

    counts = {
        "PendingReviewRows": len(review_rows),
        "PendingNewThirdPartyStable": sum(r.get("OriginType") == "new-third-party-stable" for r in review_rows),
        "PendingReusedExistingStable": sum(r.get("OriginType") == "reused-existing-stable" for r in review_rows),
        "PronunciationDebtRows": len(pron_rows),
        "PronunciationDebtReleased": sum(r.get("ReleaseState") == "released" for r in pron_rows),
        "PronunciationDebtUnreleased": sum(r.get("ReleaseState") == "unreleased" for r in pron_rows),
        "PronunciationDebtNewThirdPartyStable": sum(r.get("OriginType") == "new-third-party-stable" for r in pron_rows),
        "PronunciationDebtReusedExistingStable": sum(r.get("OriginType") == "reused-existing-stable" for r in pron_rows),
    }
    for key, value in counts.items():
        if manifest.get(key) != value: fail(f"Manifest count drift: {key}={manifest.get(key)} expected={value}")

    if counts["PendingReviewRows"] != 1981: fail(f"Expected 1981 pending review rows, got {counts['PendingReviewRows']}")
    if counts["PendingNewThirdPartyStable"] != 1821 or counts["PendingReusedExistingStable"] != 160:
        fail(f"Pending origin split drift: {counts}")
    if counts["PronunciationDebtRows"] != 556:
        fail(f"Expected 556 allowed pronunciation debt rows, got {counts['PronunciationDebtRows']}")

    print(
        "Third-party review preparation = PASS: "
        f"pending={counts['PendingReviewRows']} new={counts['PendingNewThirdPartyStable']} reuse={counts['PendingReusedExistingStable']} "
        f"pron_debt={counts['PronunciationDebtRows']} released_debt={counts['PronunciationDebtReleased']} "
        f"unreleased_debt={counts['PronunciationDebtUnreleased']}"
    )


if __name__ == "__main__":
    main()
