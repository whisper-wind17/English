#!/usr/bin/env python3
"""Verify that the current released Klose vocabulary is safe to import into Anki."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
PROFILE = BASE / "config" / "profile.json"
MASTER = BASE / "master" / "vocabulary_master.csv"
LEARNER = BASE / "learner" / "current.csv"
REGISTRY = BASE / "learner" / "presentation_review_registry.csv"
STUDY = BASE / "publish" / "study.csv"
REPORTS = [
    BASE / "review" / "identity_review.csv",
    BASE / "review" / "learner_review.csv",
    BASE / "review" / "future_vocab_review.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fingerprint(master: dict[str, str], learner: dict[str, str]) -> str:
    payload = "\x1f".join([
        "klose-presentation-v1",
        master.get("MeaningPrimary", "").strip(),
        learner.get("ExampleSentence", "").strip(),
        learner.get("ExampleTranslation", "").strip(),
        learner.get("LearnerProfile", "").strip(),
        learner.get("LearnerLevel", "").strip(),
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> None:
    for path in (PROFILE, MASTER, LEARNER, REGISTRY, STUDY, *REPORTS):
        if not path.exists():
            raise SystemExit(f"Missing release input: {path.relative_to(ROOT)}")

    with PROFILE.open("r", encoding="utf-8") as f:
        profile = json.load(f)
    learner_profile = str(profile["learner_profile"])
    learner_level = str(profile["learner_level"])

    for report in REPORTS:
        rows = read_csv(report)
        if rows:
            raise SystemExit(f"Release blocked: {report.relative_to(ROOT)} has {len(rows)} unresolved rows")

    master_rows = read_csv(MASTER)
    learner_rows = read_csv(LEARNER)
    registry_rows = read_csv(REGISTRY)
    study_rows = read_csv(STUDY)
    master_by_id = {r["NoteID"]: r for r in master_rows}
    learner_by_id = {r["NoteID"]: r for r in learner_rows}
    registry_by_key = {
        (r["LearnerProfile"], r["LearnerLevel"], r["NoteID"]): r for r in registry_rows
    }

    released_ids = {
        r["NoteID"] for r in master_rows
        if r.get("Released") == "yes"
        and r["NoteID"] in learner_by_id
        and learner_by_id[r["NoteID"]].get("LearnerProfile") == learner_profile
        and learner_by_id[r["NoteID"]].get("LearnerLevel") == learner_level
    }
    study_ids = [r["NoteID"] for r in study_rows]
    if len(study_ids) != len(set(study_ids)):
        raise SystemExit("Release blocked: duplicate NoteID in study.csv")
    if set(study_ids) != released_ids:
        raise SystemExit(
            f"Release blocked: study.csv mismatch released inventory; "
            f"study={len(study_ids)} released={len(released_ids)}"
        )

    pending: list[str] = []
    stale: list[str] = []
    missing: list[str] = []
    for nid in sorted(released_ids):
        key = (learner_profile, learner_level, nid)
        row = registry_by_key.get(key)
        if row is None:
            missing.append(nid)
            continue
        if row.get("ReviewStatus") not in {"model-reviewed", "human-reviewed"}:
            pending.append(nid)
        expected_fp = fingerprint(master_by_id[nid], learner_by_id[nid])
        if row.get("ContentFingerprint") != expected_fp:
            stale.append(nid)

    if missing or pending or stale:
        raise SystemExit(
            "Release blocked by learner review state: "
            f"missing={len(missing)} pending={len(pending)} stale={len(stale)}; "
            f"examples={(missing + pending + stale)[:10]}"
        )

    print(
        f"Klose release ready: profile={learner_profile}, level={learner_level}, "
        f"released={len(released_ids)}, study={len(study_ids)}, unresolved_reports=0, pending_reviews=0"
    )


if __name__ == "__main__":
    main()
