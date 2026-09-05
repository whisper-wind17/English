#!/usr/bin/env python3
"""Verify that the current released Klose vocabulary is safe to import into Anki.

This is a content-release gate, not merely a build-consistency check.
It verifies source reconciliation, explicit allowed/held learning state, publish
derivation, complete release-visible content, and current review approval.
"""
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
ADMISSION = BASE / "learner" / "learning_admission.csv"
RECONCILIATION = BASE / "master" / "source_reconciliation_registry.csv"
SOURCE_IDENTITY_EXTENSIONS = BASE / "master" / "source_identity_extensions.csv"
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
DERIVED_FIELDS = [
    "NoteID", "CanonicalWord", "Word", "British", "American", "MeaningPrimary",
    "ExampleSentence", "ExampleTranslation", "LearnerLevel", "Sources", "SourceBooks",
]
CURRENT_LEARNING_TAG = "learning::klose::grade4"
CURRENT_STAGE = "stage::grade4-current"
HELD_STAGE = "stage::library"


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
    """Bind approval to all release-visible facts plus learner presentation."""
    payload = "\x1f".join([
        "klose-presentation-v2",
        master.get("CanonicalWord", "").strip(),
        master.get("SenseLabel", "").strip(),
        master.get("Word", "").strip(),
        master.get("British", "").strip(),
        master.get("American", "").strip(),
        master.get("MeaningPrimary", "").strip(),
        learner.get("ExampleSentence", "").strip(),
        learner.get("ExampleTranslation", "").strip(),
        learner.get("LearnerProfile", "").strip(),
        learner.get("LearnerLevel", "").strip(),
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def assert_reconciliation_ready() -> None:
    rows = read_csv(RECONCILIATION)
    blocked = [
        r for r in rows
        if r.get("ReconciliationStatus", "").strip() != "reconciled"
        or r.get("IdentityStatus", "").strip() != "confirmed"
        or r.get("LearningAdmission", "").strip() != "allowed"
    ]
    if blocked:
        examples = [
            f"{r.get('SourceID')}:{r.get('SourceEdition')}:{r.get('SourceBook')}"
            f"[{r.get('ReconciliationStatus')}/{r.get('IdentityStatus')}/{r.get('LearningAdmission')}]"
            for r in blocked[:10]
        ]
        raise SystemExit(
            "Release blocked by source reconciliation state: "
            f"blocked={len(blocked)} examples={examples}"
        )


def actual_grade4_note_ids() -> set[str]:
    ids: set[str] = set()
    for row in read_csv(SOURCE_IDENTITY_EXTENSIONS):
        if (
            row.get("SourceID", "").strip() == "rj_start1"
            and row.get("SourceEdition", "").strip() == "klose-current"
            and row.get("Status", "").strip() == "confirmed"
            and row.get("SourceItemKey", "").strip().startswith("grade4-")
        ):
            nid = row.get("NoteID", "").strip()
            if nid:
                ids.add(nid)
    return ids


def load_and_validate_admission(
    learner_profile: str,
    learner_level: str,
    released_ids: set[str],
) -> dict[str, dict[str, str]]:
    rows = [
        r for r in read_csv(ADMISSION)
        if r.get("LearnerProfile", "").strip() == learner_profile
        and r.get("LearnerLevel", "").strip() == learner_level
    ]
    if not rows:
        raise SystemExit("Release blocked: explicit learning admission is empty")

    by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        nid = row.get("NoteID", "").strip()
        status = row.get("Status", "").strip()
        stage = row.get("Stage", "").strip()
        tag = row.get("LearningTag", "").strip()
        if not nid or nid in by_id:
            raise SystemExit(f"Release blocked: invalid/duplicate learning admission NoteID: {nid!r}")
        if status not in {"allowed", "held"}:
            raise SystemExit(f"Release blocked: invalid learning admission status: {nid}={status!r}")
        if status == "allowed":
            if stage != CURRENT_STAGE or tag != CURRENT_LEARNING_TAG:
                raise SystemExit(
                    f"Release blocked: current learning Note has wrong stage/tag: {nid} "
                    f"stage={stage!r} tag={tag!r}"
                )
        else:
            if stage != HELD_STAGE or tag:
                raise SystemExit(
                    f"Release blocked: held Note has wrong stage/tag: {nid} "
                    f"stage={stage!r} tag={tag!r}"
                )
        by_id[nid] = row

    ids = set(by_id)
    missing = sorted(released_ids - ids)
    extra = sorted(ids - released_ids)
    if missing or extra:
        raise SystemExit(
            "Release blocked: explicit learning admission must cover exactly released study; "
            f"missing={missing[:10]} extra={extra[:10]}"
        )

    expected_allowed = actual_grade4_note_ids()
    allowed = {nid for nid, row in by_id.items() if row.get("Status", "").strip() == "allowed"}
    if allowed != expected_allowed:
        missing = sorted(expected_allowed - allowed)
        extra = sorted(allowed - expected_allowed)
        raise SystemExit(
            "Release blocked: allowed learning set does not equal confirmed actual Grade-4 identity set; "
            f"missing={missing[:10]} extra={extra[:10]}"
        )
    return by_id


def main() -> None:
    required = (
        PROFILE, MASTER, LEARNER, REGISTRY, ADMISSION, RECONCILIATION,
        SOURCE_IDENTITY_EXTENSIONS, STUDY, ANKI_IMPORT, *REPORTS,
    )
    for path in required:
        if not path.exists():
            raise SystemExit(f"Missing release input: {path.relative_to(ROOT)}")

    assert_reconciliation_ready()

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
    admission_by_id = load_and_validate_admission(learner_profile, learner_level, released_ids)

    study_ids = [r["NoteID"] for r in study_rows]
    if len(study_ids) != len(set(study_ids)):
        raise SystemExit("Release blocked: duplicate NoteID in study.csv")
    if set(study_ids) != released_ids:
        raise SystemExit(
            f"Release blocked: study.csv mismatch released inventory; "
            f"study={len(study_ids)} released={len(released_ids)}"
        )

    # Generated release rows must be derivable from current upstream state. This
    # catches synchronized tampering with study.csv and anki-import.csv.
    drift: list[str] = []
    for row in study_rows:
        nid = row["NoteID"]
        master = master_by_id.get(nid)
        learner = learner_by_id.get(nid)
        if master is None or learner is None:
            drift.append(nid)
            continue
        expected = {**master, **learner}
        if any(row.get(field, "") != expected.get(field, "") for field in DERIVED_FIELDS):
            drift.append(nid)
    if drift:
        raise SystemExit(
            "Release blocked: published content is not derivable from current upstream state; "
            f"count={len(drift)} examples={drift[:10]}"
        )

    missing_required: list[str] = []
    bad_learning_state: list[str] = []
    for row in study_rows:
        if any(not row.get(field, "").strip() for field in (
            "NoteID", "CanonicalWord", "Word", "British", "American", "MeaningPrimary",
            "ExampleSentence", "ExampleTranslation", "LearnerLevel", "Sources", "SourceBooks", "Tags",
        )):
            missing_required.append(row["NoteID"])

        nid = row["NoteID"]
        admission = admission_by_id[nid]
        tags = row["Tags"].split()
        stage_tags = [tag for tag in tags if tag.startswith("stage::")]
        learning_tags = [tag for tag in tags if tag.startswith("learning::")]
        expected_stage = admission["Stage"].strip()
        expected_tag = admission.get("LearningTag", "").strip()
        if stage_tags != [expected_stage]:
            bad_learning_state.append(nid)
        elif expected_tag:
            if learning_tags != [expected_tag]:
                bad_learning_state.append(nid)
        elif learning_tags:
            bad_learning_state.append(nid)

    if missing_required:
        raise SystemExit(
            f"Release blocked: {len(missing_required)} study rows have missing required fields; "
            f"examples={missing_required[:10]}"
        )
    if bad_learning_state:
        raise SystemExit(
            f"Release blocked: {len(bad_learning_state)} study rows have invalid stage/learning tags; "
            f"examples={bad_learning_state[:10]}"
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

    allowed_count = sum(1 for r in admission_by_id.values() if r.get("Status") == "allowed")
    held_count = sum(1 for r in admission_by_id.values() if r.get("Status") == "held")
    print(
        f"Klose content release ready: profile={learner_profile}, level={learner_level}, "
        f"released={len(released_ids)}, current_learning={allowed_count}, held={held_count}, "
        f"study={len(study_ids)}, anki_import={len(anki_rows)}, "
        f"source_reconciliation=ready, unresolved_reports=0, pending_reviews=0"
    )


if __name__ == "__main__":
    main()
