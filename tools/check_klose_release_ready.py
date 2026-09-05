#!/usr/bin/env python3
"""Verify that the current released Klose vocabulary is safe to import into Anki.

Current learning Notes (`allowed`) must have every required release-visible field
complete. PromptHint is optional, but when present it is learner presentation and
must be derivable from upstream state and bound to review approval. LearningOrder
is admission metadata: allowed Notes must match exact textbook order, while held
Notes keep it blank. Held library Notes remain structurally valid and reviewed,
while legacy British/American IPA gaps are allowed until admission.
"""
from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path

from klose_learning_order import format_learning_order, is_valid_learning_order
from klose_review_fingerprint import fingerprint

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
    "NoteID", "CanonicalWord", "Word", "PromptHint", "British", "American", "MeaningPrimary",
    "ExampleSentence", "ExampleTranslation", "LearnerLevel", "LearningOrder", "Sources", "SourceBooks", "Tags",
]
DERIVED_FIELDS = [
    "NoteID", "CanonicalWord", "Word", "PromptHint", "British", "American", "MeaningPrimary",
    "ExampleSentence", "ExampleTranslation", "LearnerLevel", "Sources", "SourceBooks",
]
REQUIRED_FIELDS = tuple(field for field in PUBLISH_FIELDS if field != "PromptHint")
ALLOWED_REQUIRED_FIELDS = REQUIRED_FIELDS
HELD_REQUIRED_FIELDS = tuple(
    field for field in REQUIRED_FIELDS if field not in {"British", "American", "LearningOrder"}
)
CURRENT_LEARNING_TAG = "learning::klose::grade4"
CURRENT_STAGE = "stage::grade4-current"
HELD_STAGE = "stage::library"
GRADE4_KEY_RE = re.compile(r"^grade4-(upper|lower)-u(\d+)-o(\d+)\|")
SEMESTER_RANK = {"upper": 0, "lower": 1}


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
                f"Release blocked: Anki import row {index} has {len(values)} columns; expected {len(PUBLISH_FIELDS)}"
            )
        rows.append(dict(zip(PUBLISH_FIELDS, values)))
    return headers, rows


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


def actual_grade4_ordered_note_ids() -> list[str]:
    items: list[tuple[tuple[int, int, int], str]] = []
    seen_coordinates: set[tuple[int, int, int]] = set()
    seen_note_ids: set[str] = set()
    for row in read_csv(SOURCE_IDENTITY_EXTENSIONS):
        if not (
            row.get("SourceID", "").strip() == "rj_start1"
            and row.get("SourceEdition", "").strip() == "klose-current"
            and row.get("Status", "").strip() == "confirmed"
            and row.get("SourceItemKey", "").strip().startswith("grade4-")
        ):
            continue
        key = row.get("SourceItemKey", "").strip()
        match = GRADE4_KEY_RE.match(key)
        if match is None:
            raise SystemExit(f"Release blocked: invalid Grade-4 SourceItemKey for LearningOrder: {key!r}")
        semester, unit_text, order_text = match.groups()
        coordinate = (SEMESTER_RANK[semester], int(unit_text), int(order_text))
        if coordinate in seen_coordinates:
            raise SystemExit(f"Release blocked: duplicate Grade-4 curriculum coordinate: {coordinate}")
        seen_coordinates.add(coordinate)
        nid = row.get("NoteID", "").strip()
        if not nid or nid in seen_note_ids:
            raise SystemExit(f"Release blocked: invalid/duplicate active Grade-4 NoteID for ordering: {nid!r}")
        seen_note_ids.add(nid)
        items.append((coordinate, nid))
    items.sort(key=lambda item: item[0])
    return [nid for _, nid in items]


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
        learning_order = row.get("LearningOrder", "").strip()
        if not nid or nid in by_id:
            raise SystemExit(f"Release blocked: invalid/duplicate learning admission NoteID: {nid!r}")
        if status not in {"allowed", "held"}:
            raise SystemExit(f"Release blocked: invalid learning admission status: {nid}={status!r}")
        if status == "allowed":
            if stage != CURRENT_STAGE or tag != CURRENT_LEARNING_TAG:
                raise SystemExit(
                    f"Release blocked: current learning Note has wrong stage/tag: {nid} stage={stage!r} tag={tag!r}"
                )
            if not is_valid_learning_order(learning_order):
                raise SystemExit(
                    f"Release blocked: allowed Note has invalid six-digit LearningOrder: {nid}={learning_order!r}"
                )
        else:
            if stage != HELD_STAGE or tag:
                raise SystemExit(
                    f"Release blocked: held Note has wrong stage/tag: {nid} stage={stage!r} tag={tag!r}"
                )
            if learning_order:
                raise SystemExit(f"Release blocked: held Note must have blank LearningOrder: {nid}={learning_order!r}")
        by_id[nid] = row

    ids = set(by_id)
    missing = sorted(released_ids - ids)
    extra = sorted(ids - released_ids)
    if missing or extra:
        raise SystemExit(
            "Release blocked: explicit learning admission must cover exactly released study; "
            f"missing={missing[:10]} extra={extra[:10]}"
        )

    expected_ordered = actual_grade4_ordered_note_ids()
    expected_allowed = set(expected_ordered)
    allowed = {nid for nid, row in by_id.items() if row.get("Status", "").strip() == "allowed"}
    if allowed != expected_allowed:
        missing = sorted(expected_allowed - allowed)
        extra = sorted(allowed - expected_allowed)
        raise SystemExit(
            "Release blocked: allowed learning set does not equal confirmed actual Grade-4 identity set; "
            f"missing={missing[:10]} extra={extra[:10]}"
        )

    try:
        expected_order = {
            nid: format_learning_order(index)
            for index, nid in enumerate(expected_ordered, start=1)
        }
    except ValueError as exc:
        raise SystemExit(f"Release blocked: {exc}") from exc
    bad_order = [
        f"{nid}:{by_id[nid].get('LearningOrder', '')}->{expected}"
        for nid, expected in expected_order.items()
        if by_id[nid].get("LearningOrder", "").strip() != expected
    ]
    if bad_order:
        raise SystemExit(
            "Release blocked: LearningOrder does not match actual textbook order; "
            f"count={len(bad_order)} examples={bad_order[:10]}"
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
            f"Release blocked: study.csv mismatch released inventory; study={len(study_ids)} released={len(released_ids)}"
        )

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
            continue
        if row.get("LearningOrder", "") != admission_by_id[nid].get("LearningOrder", ""):
            drift.append(nid)
    if drift:
        raise SystemExit(
            "Release blocked: published content is not derivable from current upstream state; "
            f"count={len(drift)} examples={drift[:10]}"
        )

    missing_allowed: list[str] = []
    missing_held: list[str] = []
    bad_learning_state: list[str] = []
    for row in study_rows:
        nid = row["NoteID"]
        admission = admission_by_id[nid]
        status = admission["Status"].strip()
        required_fields = ALLOWED_REQUIRED_FIELDS if status == "allowed" else HELD_REQUIRED_FIELDS
        missing_fields = [field for field in required_fields if not row.get(field, "").strip()]
        if missing_fields:
            item = f"{nid}:{','.join(missing_fields)}"
            if status == "allowed":
                missing_allowed.append(item)
            else:
                missing_held.append(item)

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

    if missing_allowed:
        raise SystemExit(
            f"Release blocked: {len(missing_allowed)} current-learning rows have missing required fields; examples={missing_allowed[:10]}"
        )
    if missing_held:
        raise SystemExit(
            f"Release blocked: {len(missing_held)} held-library rows have missing structural fields; examples={missing_held[:10]}"
        )
    if bad_learning_state:
        raise SystemExit(
            f"Release blocked: {len(bad_learning_state)} study rows have invalid stage/learning tags; examples={bad_learning_state[:10]}"
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
            f"missing={len(missing)} pending={len(pending)} stale={len(stale)}; examples={(missing + pending + stale)[:10]}"
        )

    allowed_count = sum(1 for r in admission_by_id.values() if r.get("Status") == "allowed")
    held_count = sum(1 for r in admission_by_id.values() if r.get("Status") == "held")
    held_ipa_debt = sum(
        1 for row in study_rows
        if admission_by_id[row["NoteID"]]["Status"].strip() == "held"
        and (not row.get("British", "").strip() or not row.get("American", "").strip())
    )
    prompt_hint_count = sum(1 for row in study_rows if row.get("PromptHint", "").strip())
    print(
        f"Klose content release ready: profile={learner_profile}, level={learner_level}, "
        f"released={len(released_ids)}, current_learning={allowed_count}, held={held_count}, "
        f"study={len(study_ids)}, anki_import={len(anki_rows)}, prompt_hints={prompt_hint_count}, "
        f"learning_order={format_learning_order(1)}..{format_learning_order(allowed_count)}, "
        f"held_ipa_debt={held_ipa_debt}, "
        f"source_reconciliation=ready, unresolved_reports=0, pending_reviews=0"
    )


if __name__ == "__main__":
    main()
