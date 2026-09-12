#!/usr/bin/env python3
"""Build deterministic review packets for the current third-party release-preparation step.

This tool is preparation-only. It never mutates canonical Master/Learner/Admission/
Review/Release/Publish state. It materializes two auditable packet sets:

1. current fingerprint-bound pending learner presentations;
2. current allowed Notes with missing UK/US IPA, with deterministic espeak-ng
   pronunciation candidates for independent model review.

espeak-ng output is pronunciation evidence only. It is never Source Grade/Edition
or textbook provenance.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
OUT = TP / "review_preparation"
REVIEW_DIR = OUT / "learner_review_packets"
PRON_DIR = OUT / "pronunciation_review_packets"
MANIFEST = OUT / "manifest.json"

MASTER = BASE / "master" / "vocabulary_master.csv"
LEARNER = BASE / "learner" / "current.csv"
ADMISSION = BASE / "learner" / "learning_admission.csv"
REVIEW = BASE / "learner" / "presentation_review_registry.csv"
RELEASE = BASE / "master" / "release_registry.csv"
RELEASE_EXT = BASE / "master" / "release_registry_extensions.csv"
CANDIDATES = TP / "learner" / "stable_presentation_candidates.csv"

PROFILE = "klose"
LEVEL = "4"
PACKET_SIZE = 100
NEW_STABLE_MIN = 1195
NEW_STABLE_MAX = 3015
TOKEN_RE = re.compile(r"[A-Za-z]+")

REVIEW_FIELDS = [
    "NoteID", "OriginType", "CanonicalWord", "SenseLabel", "MeaningPrimary",
    "ExampleSentence", "ExampleTranslation", "PromptHint", "British", "American",
    "AdmissionStage", "LearningOrder", "ContentFingerprint", "PresentationStatus",
    "PresentationSource",
]
PRON_FIELDS = [
    "NoteID", "OriginType", "ReleaseState", "CanonicalWord", "Word", "SenseLabel",
    "MeaningPrimary", "ExistingBritish", "ExistingAmerican", "MissingSides",
    "OriginalBritishEvidenceStatus", "OriginalAmericanEvidenceStatus",
    "OriginalBritishCandidate", "OriginalAmericanCandidate",
    "CandidateBritish", "CandidateAmerican", "CandidateEngine", "CandidateEngineVersion",
    "CandidateBritishVoice", "CandidateAmericanVoice", "RiskFlags",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def reset_packet_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for old in path.glob("batch_*.csv"):
        old.unlink()


def batches(rows: list[dict[str, str]], size: int = PACKET_SIZE):
    for i in range(0, len(rows), size):
        yield i // size + 1, rows[i:i + size]


def note_num(note_id: str) -> int:
    return int(note_id.removeprefix("KV"))


def origin_type(note_id: str) -> str:
    n = note_num(note_id)
    return "new-third-party-stable" if NEW_STABLE_MIN <= n <= NEW_STABLE_MAX else "reused-existing-stable"


def espeak_version() -> str:
    proc = subprocess.run(["espeak-ng", "--version"], text=True, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(f"espeak-ng unavailable: {proc.stderr.strip()}")
    first = (proc.stdout or proc.stderr).strip().splitlines()[0]
    return first


def espeak_ipa(text: str, voice: str) -> str:
    proc = subprocess.run(
        ["espeak-ng", "-q", "--ipa=3", "-v", voice, text],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"espeak-ng failed for {text!r} / {voice}: {proc.stderr.strip()}")
    value = " ".join(proc.stdout.replace("\u200d", "").split())
    if not value:
        raise SystemExit(f"espeak-ng produced blank IPA for {text!r} / {voice}")
    return f"[{value}]"


def risk_flags(word: str) -> str:
    flags: list[str] = []
    if any(ch.isdigit() for ch in word): flags.append("digit")
    if len(word.split()) > 1: flags.append("multiword")
    if "-" in word: flags.append("hyphenated")
    alpha = "".join(TOKEN_RE.findall(word))
    if alpha and alpha.isupper() and len(alpha) > 1: flags.append("acronym")
    if any(tok[:1].isupper() for tok in word.split() if tok): flags.append("proper-case")
    if any(ch in word for ch in "'.&/()"):
        flags.append("punctuation")
    return " ".join(dict.fromkeys(flags))


def main() -> None:
    master = read_csv(MASTER)
    learner = read_csv(LEARNER)
    admission = read_csv(ADMISSION)
    review = read_csv(REVIEW)
    release_ids = {r["NoteID"].strip() for r in read_csv(RELEASE) + read_csv(RELEASE_EXT)}
    candidates = {r["NoteID"].strip(): r for r in read_csv(CANDIDATES)}

    mb = {r["NoteID"].strip(): r for r in master}
    lb = {r["NoteID"].strip(): r for r in learner}
    ab = {
        r["NoteID"].strip(): r for r in admission
        if r.get("LearnerProfile", "").strip() == PROFILE
        and r.get("LearnerLevel", "").strip() == LEVEL
    }
    rb = {
        r["NoteID"].strip(): r for r in review
        if r.get("LearnerProfile", "").strip() == PROFILE
        and r.get("LearnerLevel", "").strip() == LEVEL
    }

    allowed_ids = {
        nid for nid, r in ab.items() if r.get("Status", "").strip() == "allowed"
    }
    pending_ids = sorted(
        (nid for nid, r in rb.items()
         if nid in allowed_ids and r.get("ReviewStatus", "").strip() == "pending"),
        key=note_num,
    )

    review_rows: list[dict[str, str]] = []
    for nid in pending_ids:
        if nid not in mb or nid not in lb:
            raise SystemExit(f"Pending review row missing Master/Learner: {nid}")
        m, l, a, r = mb[nid], lb[nid], ab[nid], rb[nid]
        review_rows.append({
            "NoteID": nid,
            "OriginType": origin_type(nid),
            "CanonicalWord": m.get("CanonicalWord", "").strip(),
            "SenseLabel": m.get("SenseLabel", "").strip(),
            "MeaningPrimary": m.get("MeaningPrimary", "").strip(),
            "ExampleSentence": l.get("ExampleSentence", "").strip(),
            "ExampleTranslation": l.get("ExampleTranslation", "").strip(),
            "PromptHint": l.get("PromptHint", "").strip(),
            "British": m.get("British", "").strip(),
            "American": m.get("American", "").strip(),
            "AdmissionStage": a.get("Stage", "").strip(),
            "LearningOrder": a.get("LearningOrder", "").strip(),
            "ContentFingerprint": r.get("ContentFingerprint", "").strip(),
            "PresentationStatus": l.get("PresentationStatus", "").strip(),
            "PresentationSource": l.get("PresentationSource", "").strip(),
        })

    engine_version = espeak_version()
    pron_rows: list[dict[str, str]] = []
    for nid in sorted(allowed_ids, key=note_num):
        m = mb.get(nid)
        if m is None:
            raise SystemExit(f"Allowed Note missing Master: {nid}")
        british = m.get("British", "").strip()
        american = m.get("American", "").strip()
        if british and american:
            continue
        word = (m.get("Word", "") or m.get("CanonicalWord", "")).strip()
        c = candidates.get(nid, {})
        missing: list[str] = []
        if not british: missing.append("British")
        if not american: missing.append("American")
        pron_rows.append({
            "NoteID": nid,
            "OriginType": origin_type(nid),
            "ReleaseState": "released" if nid in release_ids else "unreleased",
            "CanonicalWord": m.get("CanonicalWord", "").strip(),
            "Word": word,
            "SenseLabel": m.get("SenseLabel", "").strip(),
            "MeaningPrimary": m.get("MeaningPrimary", "").strip(),
            "ExistingBritish": british,
            "ExistingAmerican": american,
            "MissingSides": "+".join(missing),
            "OriginalBritishEvidenceStatus": c.get("BritishEvidenceStatus", "").strip(),
            "OriginalAmericanEvidenceStatus": c.get("AmericanEvidenceStatus", "").strip(),
            "OriginalBritishCandidate": c.get("BritishCandidate", "").strip(),
            "OriginalAmericanCandidate": c.get("AmericanCandidate", "").strip(),
            "CandidateBritish": british or espeak_ipa(word, "en-gb"),
            "CandidateAmerican": american or espeak_ipa(word, "en-us"),
            "CandidateEngine": "espeak-ng",
            "CandidateEngineVersion": engine_version,
            "CandidateBritishVoice": "en-gb",
            "CandidateAmericanVoice": "en-us",
            "RiskFlags": risk_flags(word),
        })

    reset_packet_dir(REVIEW_DIR)
    reset_packet_dir(PRON_DIR)
    for idx, rows in batches(review_rows):
        write_csv(REVIEW_DIR / f"batch_{idx:02d}.csv", REVIEW_FIELDS, rows)
    for idx, rows in batches(pron_rows):
        write_csv(PRON_DIR / f"batch_{idx:02d}.csv", PRON_FIELDS, rows)

    manifest = {
        "Version": "third-party-review-preparation-v1",
        "LearnerProfile": PROFILE,
        "LearnerLevel": int(LEVEL),
        "PendingReviewRows": len(review_rows),
        "PendingNewThirdPartyStable": sum(r["OriginType"] == "new-third-party-stable" for r in review_rows),
        "PendingReusedExistingStable": sum(r["OriginType"] == "reused-existing-stable" for r in review_rows),
        "PronunciationDebtRows": len(pron_rows),
        "PronunciationDebtReleased": sum(r["ReleaseState"] == "released" for r in pron_rows),
        "PronunciationDebtUnreleased": sum(r["ReleaseState"] == "unreleased" for r in pron_rows),
        "PronunciationDebtNewThirdPartyStable": sum(r["OriginType"] == "new-third-party-stable" for r in pron_rows),
        "PronunciationDebtReusedExistingStable": sum(r["OriginType"] == "reused-existing-stable" for r in pron_rows),
        "LearnerReviewPacketCount": (len(review_rows) + PACKET_SIZE - 1) // PACKET_SIZE,
        "PronunciationReviewPacketCount": (len(pron_rows) + PACKET_SIZE - 1) // PACKET_SIZE,
        "PronunciationCandidateEngine": "espeak-ng",
        "PronunciationCandidateEngineVersion": engine_version,
        "PronunciationEvidenceSemantics": "deterministic pronunciation-reference candidate; not textbook source provenance",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
