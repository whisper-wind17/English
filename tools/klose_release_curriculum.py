#!/usr/bin/env python3
"""Derive the expected Klose release curriculum across textbook and third-party stages.

Source-backed Grade 4/5/6 identities keep their textbook stage/tag. The reviewed
third-party admission plan may append additional Stable NoteIDs under the explicit
`stage::third-party-primary` curriculum without inventing Source Grade/Edition.
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
TP_PLAN = BASE / "third_party_vocabulary" / "learner" / "stable_learning_admission_plan.csv"

GRADE4_STAGE = "stage::grade4-current"
GRADE4_LEARNING_TAG = "learning::klose::grade4"
G56_STAGE = "stage::grade5-6-current"
G56_LEARNING_TAG = "learning::klose::grade5-6"
TP_STAGE = "stage::third-party-primary"
TP_LEARNING_TAG = "learning::klose::third-party-primary"
GRADE4_KEY_RE = re.compile(r"^grade4-(upper|lower)-u(\d+)-o(\d+)\|")
G56_KEY_RE = re.compile(r"^grade([56])-(upper|lower)-u(\d+)-o(\d+)\|")
SEMESTER_RANK = {"upper": 0, "lower": 1}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def order6(value: int) -> str:
    if value < 1 or value > 999999:
        raise SystemExit(f"Invalid curriculum order: {value}")
    return f"{value:06d}"


def textbook_curriculum() -> tuple[list[str], dict[str, tuple[str, str]]]:
    scope = json.loads(G56_SCOPE.read_text(encoding="utf-8"))
    if scope.get("ScopeStatus") != "accepted" or scope.get("StableIdentityAllocationAuthorized") is not True:
        raise SystemExit("Release blocked: Grade 5-6 current learning scope is not accepted")
    accepted_books = {k for k, v in scope.get("Books", {}).items() if v.get("Accepted") is True}
    if accepted_books != {"5上", "5下", "6上", "6下"}:
        raise SystemExit(f"Release blocked: Grade 5-6 current scope is incomplete: {sorted(accepted_books)}")

    first_coord: dict[str, tuple[int, int, int, int, int]] = {}
    expected_state: dict[str, tuple[str, str]] = {}
    seen_coordinates: set[tuple[int, int, int, int]] = set()
    for row in read_csv(SOURCE_IDENTITY_EXTENSIONS):
        if row.get("Status", "").strip() != "confirmed":
            continue
        key = row.get("SourceItemKey", "").strip()
        nid = row.get("NoteID", "").strip()
        if not nid:
            raise SystemExit("Release blocked: confirmed source identity has blank NoteID")

        m4 = GRADE4_KEY_RE.match(key)
        if m4 is not None and row.get("SourceID", "").strip() == "rj_start1" and row.get("SourceEdition", "").strip() == "klose-current":
            semester, unit_text, order_text = m4.groups()
            coordinate = (4, SEMESTER_RANK[semester], int(unit_text), int(order_text))
            if coordinate in seen_coordinates:
                raise SystemExit(f"Release blocked: duplicate current curriculum coordinate: {coordinate}")
            seen_coordinates.add(coordinate)
            full_coord = (*coordinate, int(nid[2:]))
            first_coord[nid] = min(first_coord.get(nid, full_coord), full_coord)
            expected_state[nid] = (GRADE4_STAGE, GRADE4_LEARNING_TAG)
            continue

        m56 = G56_KEY_RE.match(key)
        if m56 is None:
            continue
        grade_text, semester, unit_text, order_text = m56.groups()
        book = grade_text + ("上" if semester == "upper" else "下")
        if book not in accepted_books:
            continue
        coordinate = (int(grade_text), SEMESTER_RANK[semester], int(unit_text), int(order_text))
        if coordinate in seen_coordinates:
            raise SystemExit(f"Release blocked: duplicate current curriculum coordinate: {coordinate}")
        seen_coordinates.add(coordinate)
        full_coord = (*coordinate, int(nid[2:]))
        first_coord[nid] = min(first_coord.get(nid, full_coord), full_coord)
        expected_state.setdefault(nid, (G56_STAGE, G56_LEARNING_TAG))

    if not first_coord:
        raise SystemExit("Release blocked: current textbook curriculum identity set is empty")
    ordered = [nid for nid, _ in sorted(first_coord.items(), key=lambda item: item[1])]
    return ordered, expected_state


def current_curriculum_ordered_note_ids() -> tuple[list[str], dict[str, tuple[str, str]]]:
    base_ordered, expected_state = textbook_curriculum()
    base_pos = {nid: order6(i) for i, nid in enumerate(base_ordered, start=1)}

    plan = read_csv(TP_PLAN)
    if not plan:
        raise SystemExit("Release blocked: empty third-party admission plan")
    by_id: dict[str, dict[str, str]] = {}
    for row in plan:
        nid = row.get("NoteID", "").strip()
        if not nid or nid in by_id:
            raise SystemExit(f"Release blocked: invalid/duplicate third-party admission NoteID: {nid!r}")
        if row.get("LearnerProfile", "").strip() != "klose" or row.get("LearnerLevel", "").strip() != "4":
            raise SystemExit(f"Release blocked: third-party admission profile/level drift: {nid}")
        if row.get("ProposedStatus", "").strip() != "allowed":
            raise SystemExit(f"Release blocked: third-party admission status drift: {nid}")
        by_id[nid] = row

    preserve = [r for r in plan if r.get("AdmissionAction", "").strip() == "preserve-allowed"]
    appended = [r for r in plan if r.get("AdmissionAction", "").strip() != "preserve-allowed"]

    for row in preserve:
        nid = row["NoteID"].strip()
        if nid not in base_pos:
            raise SystemExit(f"Release blocked: preserve-allowed Note is outside textbook curriculum: {nid}")
        if row.get("ProposedLearningOrder", "").strip() != base_pos[nid]:
            raise SystemExit(f"Release blocked: preserved textbook LearningOrder drift: {nid}")

    appended.sort(key=lambda r: (int(r.get("ProposedLearningOrder", "0") or 0), int(r["NoteID"][2:])))
    expected_appended_orders = [order6(i) for i in range(len(base_ordered) + 1, len(base_ordered) + len(appended) + 1)]
    actual_appended_orders = [r.get("ProposedLearningOrder", "").strip() for r in appended]
    if actual_appended_orders != expected_appended_orders:
        raise SystemExit("Release blocked: appended third-party LearningOrder is not exact/continuous after textbook curriculum")

    appended_ids: list[str] = []
    for row in appended:
        nid = row["NoteID"].strip()
        if nid in expected_state:
            raise SystemExit(f"Release blocked: appended third-party Note overlaps textbook curriculum: {nid}")
        if row.get("ProposedLearningTag", "").strip() != TP_LEARNING_TAG:
            raise SystemExit(f"Release blocked: third-party LearningTag drift: {nid}")
        expected_state[nid] = (TP_STAGE, TP_LEARNING_TAG)
        appended_ids.append(nid)

    ordered = base_ordered + appended_ids
    if len(ordered) != len(set(ordered)):
        raise SystemExit("Release blocked: duplicate combined curriculum identity")
    from klose_current_policy import apply_decisions
    return apply_decisions(ordered, expected_state)


if __name__ == "__main__":
    ordered, state = current_curriculum_ordered_note_ids()
    print(
        f"Klose release curriculum OK: textbook={len(textbook_curriculum()[0])}, "
        f"third_party_appended={sum(1 for nid in ordered if state[nid][0] == TP_STAGE)}, total={len(ordered)}"
    )
