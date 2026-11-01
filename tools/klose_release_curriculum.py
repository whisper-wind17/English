#!/usr/bin/env python3
"""Derive Klose curriculum order across textbook, NCE1 and third-party stages.

Curriculum segment order is explicit in config/curriculum_segments.json.
A Stable Note that occurs in more than one source is scheduled at its earliest
curriculum coordinate. Third-party-only Notes preserve their established relative
order but are rebased after the source-backed curriculum.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
SOURCE_IDENTITY_EXTENSIONS = BASE / "master" / "source_identity_extensions.csv"
G56_SCOPE = BASE / "learner" / "grade5_6_learning_scope.json"
CURRICULUM = BASE / "config" / "curriculum_segments.json"
TP_PLAN = BASE / "third_party_vocabulary" / "learner" / "stable_learning_admission_plan.csv"

GRADE4_STAGE = "stage::grade4-current"
GRADE4_LEARNING_TAG = "learning::klose::grade4"
NCE_STAGE = "stage::nce1-current"
NCE_LEARNING_TAG = "learning::klose::nce1"
G56_STAGE = "stage::grade5-6-current"
G56_LEARNING_TAG = "learning::klose::grade5-6"
TP_STAGE = "stage::third-party-primary"
TP_LEARNING_TAG = "learning::klose::third-party-primary"

NCE_SOURCE_ID = "new_concept_english_1"
NCE_SOURCE_EDITION = "2022-smart-isbn-9787521336702"
GRADE4_KEY_RE = re.compile(r"^grade4-(upper|lower)-u(\d+)-o(\d+)\|")
NCE_KEY_RE = re.compile(r"^nce1-o(\d+)\|")
G56_KEY_RE = re.compile(r"^grade([56])-(upper|lower)-u(\d+)-o(\d+)\|")
SEMESTER_RANK = {"upper": 0, "lower": 1}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def order6(value: int) -> str:
    if value < 1 or value > 999999:
        raise SystemExit(f"Invalid curriculum order: {value}")
    return f"{value:06d}"


def curriculum_config() -> tuple[dict[str, int], bool]:
    cfg = json.loads(CURRICULUM.read_text(encoding="utf-8"))
    segments = cfg.get("Segments", {})
    required = {"grade4", "new_concept_english_1", "grade5", "grade6", "third_party"}
    if set(segments) != required:
        raise SystemExit(f"Release blocked: curriculum segments mismatch: {sorted(segments)}")
    ranks = {name: int(data["Rank"]) for name, data in segments.items()}
    if len(set(ranks.values())) != len(ranks):
        raise SystemExit("Release blocked: curriculum segment ranks must be unique")
    if not (
        ranks["grade4"] < ranks["new_concept_english_1"]
        < ranks["grade5"] < ranks["grade6"] < ranks["third_party"]
    ):
        raise SystemExit("Release blocked: curriculum segment order drift")
    nce = segments["new_concept_english_1"]
    if nce.get("SourceEdition") != NCE_SOURCE_EDITION:
        raise SystemExit("Release blocked: NCE1 SourceEdition drift")
    return ranks, nce.get("Status") == "active"


def source_backed_curriculum() -> tuple[list[str], dict[str, tuple[str, str]]]:
    scope = json.loads(G56_SCOPE.read_text(encoding="utf-8"))
    if scope.get("ScopeStatus") != "accepted" or scope.get("StableIdentityAllocationAuthorized") is not True:
        raise SystemExit("Release blocked: Grade 5-6 current learning scope is not accepted")
    accepted_books = {k for k, v in scope.get("Books", {}).items() if v.get("Accepted") is True}
    if accepted_books != {"5上", "5下", "6上", "6下"}:
        raise SystemExit(f"Release blocked: Grade 5-6 current scope is incomplete: {sorted(accepted_books)}")

    ranks, nce_active = curriculum_config()
    # Coordinate is (segment-rank, semester-rank, unit, source-order, NoteID).
    first: dict[str, tuple[tuple[int, int, int, int, int], tuple[str, str]]] = {}
    seen: set[tuple[int, int, int, int]] = set()

    def consider(nid: str, coordinate: tuple[int, int, int, int], state: tuple[str, str]) -> None:
        if coordinate in seen:
            raise SystemExit(f"Release blocked: duplicate current curriculum coordinate: {coordinate}")
        seen.add(coordinate)
        full = (*coordinate, int(nid[2:]))
        current = first.get(nid)
        if current is None or full < current[0]:
            first[nid] = (full, state)

    for row in read_csv(SOURCE_IDENTITY_EXTENSIONS):
        if row.get("Status", "").strip() != "confirmed":
            continue
        key = row.get("SourceItemKey", "").strip()
        nid = row.get("NoteID", "").strip()
        if not nid:
            raise SystemExit("Release blocked: confirmed source identity has blank NoteID")

        m4 = GRADE4_KEY_RE.match(key)
        if (
            m4 is not None
            and row.get("SourceID", "").strip() == "rj_start1"
            and row.get("SourceEdition", "").strip() == "klose-current"
        ):
            semester, unit_text, order_text = m4.groups()
            consider(
                nid,
                (ranks["grade4"], SEMESTER_RANK[semester], int(unit_text), int(order_text)),
                (GRADE4_STAGE, GRADE4_LEARNING_TAG),
            )
            continue

        mn = NCE_KEY_RE.match(key)
        if (
            nce_active
            and mn is not None
            and row.get("SourceID", "").strip() == NCE_SOURCE_ID
            and row.get("SourceEdition", "").strip() == NCE_SOURCE_EDITION
        ):
            consider(
                nid,
                (ranks["new_concept_english_1"], 0, 0, int(mn.group(1))),
                (NCE_STAGE, NCE_LEARNING_TAG),
            )
            continue

        m56 = G56_KEY_RE.match(key)
        if m56 is None:
            continue
        grade_text, semester, unit_text, order_text = m56.groups()
        book = grade_text + ("上" if semester == "upper" else "下")
        if book not in accepted_books:
            continue
        segment = "grade5" if grade_text == "5" else "grade6"
        consider(
            nid,
            (ranks[segment], SEMESTER_RANK[semester], int(unit_text), int(order_text)),
            (G56_STAGE, G56_LEARNING_TAG),
        )

    if not first:
        raise SystemExit("Release blocked: current source-backed curriculum is empty")
    ordered = [nid for nid, _ in sorted(first.items(), key=lambda item: item[1][0])]
    state = {nid: value[1] for nid, value in first.items()}
    return ordered, state


# Backward-compatible name used by existing checks.
def textbook_curriculum() -> tuple[list[str], dict[str, tuple[str, str]]]:
    return source_backed_curriculum()


def current_curriculum_ordered_note_ids() -> tuple[list[str], dict[str, tuple[str, str]]]:
    base_ordered, expected_state = source_backed_curriculum()
    base_set = set(base_ordered)

    plan = read_csv(TP_PLAN)
    if not plan:
        raise SystemExit("Release blocked: empty third-party admission plan")
    seen_ids: set[str] = set()
    third_party_only: list[dict[str, str]] = []
    for row in plan:
        nid = row.get("NoteID", "").strip()
        if not nid or nid in seen_ids:
            raise SystemExit(f"Release blocked: invalid/duplicate third-party admission NoteID: {nid!r}")
        seen_ids.add(nid)
        if row.get("LearnerProfile", "").strip() != "klose" or row.get("LearnerLevel", "").strip() != "4":
            raise SystemExit(f"Release blocked: third-party admission profile/level drift: {nid}")
        if row.get("ProposedStatus", "").strip() != "allowed":
            raise SystemExit(f"Release blocked: third-party admission status drift: {nid}")
        proposed_order = row.get("ProposedLearningOrder", "").strip()
        if not proposed_order.isdigit() or int(proposed_order) < 1:
            raise SystemExit(f"Release blocked: invalid third-party relative order: {nid}")
        # A Note newly exposed by NCE1 is source-backed now. Do not append it again
        # as third-party; its earliest source coordinate owns stage and position.
        if nid in base_set:
            continue
        if row.get("ProposedLearningTag", "").strip() != TP_LEARNING_TAG:
            raise SystemExit(f"Release blocked: third-party LearningTag drift: {nid}")
        third_party_only.append(row)

    # Historical ProposedLearningOrder is retained only as a stable *relative* order.
    # Inserting NCE1 rebases this block numerically after the source-backed curriculum.
    third_party_only.sort(
        key=lambda r: (int(r["ProposedLearningOrder"]), int(r["NoteID"][2:]))
    )
    appended_ids: list[str] = []
    for row in third_party_only:
        nid = row["NoteID"].strip()
        expected_state[nid] = (TP_STAGE, TP_LEARNING_TAG)
        appended_ids.append(nid)

    ordered = base_ordered + appended_ids
    if len(ordered) != len(set(ordered)):
        raise SystemExit("Release blocked: duplicate combined curriculum identity")
    from klose_current_policy import apply_decisions
    return apply_decisions(ordered, expected_state)


if __name__ == "__main__":
    ordered, state = current_curriculum_ordered_note_ids()
    source_ordered, _ = source_backed_curriculum()
    print(
        f"Klose release curriculum OK: source_backed={len(source_ordered)}, "
        f"nce1_stage={sum(1 for nid in ordered if state[nid][0] == NCE_STAGE)}, "
        f"third_party_appended={sum(1 for nid in ordered if state[nid][0] == TP_STAGE)}, total={len(ordered)}"
    )
