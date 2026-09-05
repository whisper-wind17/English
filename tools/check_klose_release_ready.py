#!/usr/bin/env python3
"""Verify that the current released Klose vocabulary is safe to import into Anki."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
PROFILE = BASE / "config" / "profile.json"
MASTER = BASE / "master" / "vocabulary_master.csv"
LEARNER = BASE / "learner" / "current.csv"
REGISTRY = BASE / "learner" / "presentation_review_registry.csv"
STUDY = BASE / "publish" / "study.csv"
ANKI_IMPORT = BASE / "publish" / "anki-import.csv"
REPORTS = [
    BASE / "review" / "identity_review.csv",
    BASE / "review" / "learner_review.csv",
    BASE / "review" / "future_vocab_review.csv",
]
PUBLISH_FIELDS = [
    "NoteID", "CanonicalWord", "Word", "British", "American", "MeaningPrimary",
    "ExampleSentence", "ExampleTranslation", "LearnerLevel", "Sources", "SourceBooks", "Tags",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_anki_import(path: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    headers: dict[str, str] = {}
    data_lines: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            if line.startswith("#"):
                if ":" not in line:
                    raise SystemExit(f"Release blocked: malformed Anki header: {line}")
                key, value = line[1:].split(":", 1)
                headers[key.strip().lower()] = value.strip()
            elif line:
                data_lines.append(raw)
    reader = csv.reader(io.StringIO("".join(data_lines)))
    rows: list[dict[str, str]] = []
    for index, values in enumerate(reader, start=1):
        if len(values) != len(PUBLISH_FIELDS):
            raise SystemExit(
                f"Release blocked: Anki import row {index} has {len(values)} columns; "
                f"expected {len(PUBLISH_FIELDS)}"
            )
        rows.append(dict(zip(PUBLISH_FIELDS, values)))
    return headers, rows


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
    for path in (PROFILE, MASTER, LEARNER, REGISTRY, STUDY, ANKI_IMPORT, *REPORTS):
        if not path.exists():
            raise SystemExit(f"Missing release input: {path.relative_to(ROOT)}")

    if ANKI_IMPORT.read_bytes().startswith(b"\xef\xbb\xbf"):
        raise SystemExit("Release blocked: anki-import.csv must be UTF-8 without BOM so #file headers start at byte 0")

    with PROFILE.open("r", encoding="utf-8") as f:
        profile = json.load(f)
    learner_profile = str(profile["learner_profile"])
    learner_level = str(profile["learner_level"])
    note_type = str(profile["note_type"])
    main_deck = str(profile["main_deck"])

    for report in REPORTS:
        rows = read_csv(report)
        if rows:
            raise SystemExit(f"Release blocked: {report.relative_to(ROOT)} has {len(rows)} unresolved rows")

    master_rows = read_csv(MASTER)
    learner_rows = read_csv(LEARNER)
    registry_rows = read_csv(REGISTRY)
    study_rows = read_csv(STUDY)
    anki_headers, anki_rows = read_anki_import(ANKI_IMPORT)

    expected_headers = {
        "separator": "Comma",
        "html": "false",
        "notetype": note_type,
        "deck": main_deck,
        "tags column": str(PUBLISH_FIELDS.index("Tags") + 1),
        "columns": ",".join(PUBLISH_FIELDS),
    }
    for key, expected in expected_headers.items():
        if anki_headers.get(key) != expected:
            raise SystemExit(
                f"Release blocked: Anki import header {key!r}={anki_headers.get(key)!r}; expected {expected!r}"
            )

    if anki_rows != study_rows:
        raise SystemExit("Release blocked: anki-import.csv data does not exactly match study.csv")

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

    missing_required: list[str] = []
    bad_stage: list[str] = []
    for row in study_rows:
        if any(not row.get(field, "").strip() for field in (
            "NoteID", "CanonicalWord", "Word", "MeaningPrimary",
            "ExampleSentence", "ExampleTranslation", "LearnerLevel", "Sources", "SourceBooks", "Tags",
        )):
            missing_required.append(row["NoteID"])
        stage_tags = [tag for tag in row["Tags"].split() if tag.startswith("stage::")]
        if len(stage_tags) != 1:
            bad_stage.append(row["NoteID"])
    if missing_required:
        raise SystemExit(
            f"Release blocked: {len(missing_required)} study rows have missing required fields; "
            f"examples={missing_required[:10]}"
        )
    if bad_stage:
        raise SystemExit(
            f"Release blocked: {len(bad_stage)} study rows do not have exactly one stage tag; "
            f"examples={bad_stage[:10]}"
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
        f"released={len(released_ids)}, study={len(study_ids)}, anki_import={len(anki_rows)}, "
        f"unresolved_reports=0, pending_reviews=0"
    )


if __name__ == "__main__":
    main()
