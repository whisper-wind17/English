#!/usr/bin/env python3
"""Explain released learner-review invalidations against the pre-pronunciation checkpoint.

Analysis-only. Compares current fingerprint-bound fields with the learner-materialization
checkpoint and classifies whether each released pending Note is part of reviewed
pronunciation evidence. Never mutates Master/Learner/Review truth.
"""
from __future__ import annotations

import csv
import io
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master" / "vocabulary_master.csv"
LEARNER = BASE / "learner" / "current.csv"
REGISTRY = BASE / "learner" / "presentation_review_registry.csv"
PRON = BASE / "third_party_vocabulary" / "pronunciation" / "reviewed_pronunciations.csv"
OUT_DIR = BASE / "third_party_vocabulary" / "review_preparation"
OUT = OUT_DIR / "released_pending_after_pronunciation.csv"
SUMMARY = OUT_DIR / "released_pending_after_pronunciation.json"
BASE_REF = "d0dae5b0b3f9b218d1acb462cedf08031d8f70d8"
PROFILE = "klose"
LEVEL = "4"
FIELDS = [
    "NoteID", "CanonicalWord", "InReviewedPronunciation", "ChangedFields",
    "OldBritish", "British", "OldAmerican", "American",
    "OldMeaningPrimary", "MeaningPrimary", "OldExampleSentence", "ExampleSentence",
    "OldExampleTranslation", "ExampleTranslation", "OldPromptHint", "PromptHint",
    "ReviewNote",
]
FP_FIELDS = [
    "CanonicalWord", "SenseLabel", "Word", "British", "American", "MeaningPrimary",
    "ExampleSentence", "ExampleTranslation", "LearnerProfile", "LearnerLevel", "PromptHint",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def git_csv(ref: str, path: Path) -> list[dict[str, str]]:
    rel = path.relative_to(ROOT).as_posix()
    proc = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=ROOT, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(f"Cannot read {rel} at {ref}: {proc.stderr.decode('utf-8', 'replace')}")
    text = proc.stdout.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text, newline="")))


def merged(master: dict[str, str], learner: dict[str, str]) -> dict[str, str]:
    return {**master, **learner}


def main() -> None:
    current_master_rows = read_csv(MASTER)
    current_learner_rows = read_csv(LEARNER)
    registry_rows = read_csv(REGISTRY)
    old_master_rows = git_csv(BASE_REF, MASTER)
    old_learner_rows = git_csv(BASE_REF, LEARNER)
    pron_ids = {r.get("NoteID", "").strip() for r in read_csv(PRON)}

    cm = {r["NoteID"].strip(): r for r in current_master_rows}
    cl = {r["NoteID"].strip(): r for r in current_learner_rows}
    om = {r["NoteID"].strip(): r for r in old_master_rows}
    ol = {r["NoteID"].strip(): r for r in old_learner_rows}
    released = {r["NoteID"].strip() for r in current_master_rows if r.get("Released", "").strip() == "yes"}
    pending = {
        r["NoteID"].strip(): r for r in registry_rows
        if r.get("LearnerProfile", "").strip() == PROFILE
        and r.get("LearnerLevel", "").strip() == LEVEL
        and r.get("ReviewStatus", "").strip() == "pending"
        and r.get("NoteID", "").strip() in released
    }

    rows: list[dict[str, str]] = []
    for nid in sorted(pending, key=lambda x: int(x[2:])):
        if nid not in cm or nid not in cl or nid not in om or nid not in ol:
            raise SystemExit(f"Released pending Note missing from current/base comparison: {nid}")
        cur = merged(cm[nid], cl[nid])
        old = merged(om[nid], ol[nid])
        changed = [f for f in FP_FIELDS if cur.get(f, "").strip() != old.get(f, "").strip()]
        rows.append({
            "NoteID": nid,
            "CanonicalWord": cur.get("CanonicalWord", "").strip(),
            "InReviewedPronunciation": "yes" if nid in pron_ids else "no",
            "ChangedFields": "|".join(changed),
            "OldBritish": old.get("British", "").strip(), "British": cur.get("British", "").strip(),
            "OldAmerican": old.get("American", "").strip(), "American": cur.get("American", "").strip(),
            "OldMeaningPrimary": old.get("MeaningPrimary", "").strip(), "MeaningPrimary": cur.get("MeaningPrimary", "").strip(),
            "OldExampleSentence": old.get("ExampleSentence", "").strip(), "ExampleSentence": cur.get("ExampleSentence", "").strip(),
            "OldExampleTranslation": old.get("ExampleTranslation", "").strip(), "ExampleTranslation": cur.get("ExampleTranslation", "").strip(),
            "OldPromptHint": old.get("PromptHint", "").strip(), "PromptHint": cur.get("PromptHint", "").strip(),
            "ReviewNote": pending[nid].get("ReviewNote", "").strip(),
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader(); w.writerows(rows)

    pron_rows = [r for r in rows if r["InReviewedPronunciation"] == "yes"]
    extras = [r for r in rows if r["InReviewedPronunciation"] == "no"]
    changed_counts: dict[str, int] = {}
    for r in rows:
        key = r["ChangedFields"] or "none"
        changed_counts[key] = changed_counts.get(key, 0) + 1
    summary = {
        "BaselineCommit": BASE_REF,
        "ReleasedPending": len(rows),
        "InReviewedPronunciation": len(pron_rows),
        "ExtraReleasedInvalidations": len(extras),
        "ExtraNoteIDs": [r["NoteID"] for r in extras],
        "ChangedFieldPatterns": changed_counts,
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if len(rows) != 78 or len(pron_rows) != 72 or len(extras) != 6:
        raise SystemExit(
            f"Released-pending closure drift: total={len(rows)} pron={len(pron_rows)} extras={len(extras)}"
        )


if __name__ == "__main__":
    main()
