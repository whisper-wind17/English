#!/usr/bin/env python3
"""Build explicit Klose learning admission from current curriculum identity truth.

Learning admission is intentionally independent from Release. A Stable Note can be
accepted into Klose's current curriculum before learner presentation/release is
complete. Released Notes outside current curriculum remain held in the library.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from klose_learning_order import format_learning_order

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master"
LEARNER = BASE / "learner"
LEGACY_RELEASES = MASTER / "release_registry.csv"
RELEASE_EXTENSIONS = MASTER / "release_registry_extensions.csv"
REGISTRY = MASTER / "note_registry.csv"
REGISTRY_EXTENSIONS = MASTER / "note_registry_extensions.csv"
SOURCE_IDENTITIES = MASTER / "source_identity_extensions.csv"
G56_SCOPE = LEARNER / "grade5_6_learning_scope.json"
CURRICULUM = BASE / "config" / "curriculum_segments.json"
OUT = LEARNER / "learning_admission.csv"

FIELDS = ["LearnerProfile", "LearnerLevel", "NoteID", "Stage", "Status", "LearningTag", "LearningOrder", "Reason"]
PROFILE = "klose"
LEVEL = "4"
HELD_STAGE = "stage::library"
GRADE4_STAGE = "stage::grade4-current"
GRADE4_TAG = "learning::klose::grade4"
G56_STAGE = "stage::grade5-6-current"
G56_TAG = "learning::klose::grade5-6"
NCE_STAGE = "stage::nce1-current"
NCE_TAG = "learning::klose::nce1"
NCE_SOURCE_ID = "new_concept_english_1"
NCE_SOURCE_EDITION = "2022-smart-isbn-9787521336702"
GRADE4_RE = re.compile(r"^grade4-(upper|lower)-u(\d+)-o(\d+)\|")
NCE_RE = re.compile(r"^nce1-o(\d+)\|")
G56_RE = re.compile(r"^grade([56])-(upper|lower)-u(\d+)-o(\d+)\|")
SEM_RANK = {"upper": 0, "lower": 1}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def note_num(note_id: str) -> int:
    if not note_id.startswith("KV") or not note_id[2:].isdigit():
        raise SystemExit(f"Invalid NoteID: {note_id!r}")
    return int(note_id[2:])


def current_scope() -> tuple[list[str], set[str], set[str], set[str]]:
    scope = json.loads(G56_SCOPE.read_text(encoding="utf-8"))
    if scope.get("ScopeStatus") != "accepted" or scope.get("StableIdentityAllocationAuthorized") is not True:
        raise SystemExit("Grade 5-6 current learning scope is not accepted")
    accepted_books = {k for k, v in scope.get("Books", {}).items() if v.get("Accepted") is True}
    if accepted_books != {"5上", "5下", "6上", "6下"}:
        raise SystemExit(f"Grade 5-6 current scope is incomplete: {sorted(accepted_books)}")

    curriculum = json.loads(CURRICULUM.read_text(encoding="utf-8"))
    segments = curriculum.get("Segments", {})
    required_segments = {"grade4", "new_concept_english_1", "grade5", "grade6", "third_party"}
    if set(segments) != required_segments:
        raise SystemExit(f"Curriculum segments mismatch: {sorted(segments)}")
    ranks = {name: int(data["Rank"]) for name, data in segments.items()}
    if len(set(ranks.values())) != len(ranks):
        raise SystemExit("Curriculum segment ranks must be unique")
    if not (ranks["grade4"] < ranks["new_concept_english_1"] < ranks["grade5"] < ranks["grade6"] < ranks["third_party"]):
        raise SystemExit("Curriculum order must be Grade4 -> NCE1 -> Grade5 -> Grade6 -> third-party")
    nce_cfg = segments["new_concept_english_1"]
    if nce_cfg.get("SourceEdition") != NCE_SOURCE_EDITION:
        raise SystemExit("NCE1 curriculum SourceEdition drift")
    nce_active = nce_cfg.get("Status") == "active"

    # One Note may recur in later sources. Its earliest curriculum coordinate wins,
    # so a Grade-4 word is not relearned in NCE1 and an NCE1 word is not repeated in Grade 5/6.
    first_coord: dict[str, tuple[int, int, int, int, int]] = {}
    grade4_ids: set[str] = set()
    nce_ids: set[str] = set()
    g56_ids: set[str] = set()
    for row in read_csv(SOURCE_IDENTITIES):
        if row.get("Status", "").strip() != "confirmed":
            continue
        key = row.get("SourceItemKey", "").strip()
        nid = row.get("NoteID", "").strip()

        m4 = GRADE4_RE.match(key)
        if (
            m4 is not None
            and row.get("SourceID", "").strip() == "rj_start1"
            and row.get("SourceEdition", "").strip() == "klose-current"
        ):
            sem, unit, order = m4.groups()
            grade4_ids.add(nid)
            c = (ranks["grade4"], SEM_RANK[sem], int(unit), int(order), note_num(nid))
            first_coord[nid] = min(first_coord.get(nid, c), c)
            continue

        mn = NCE_RE.match(key)
        if (
            nce_active
            and mn is not None
            and row.get("SourceID", "").strip() == NCE_SOURCE_ID
            and row.get("SourceEdition", "").strip() == NCE_SOURCE_EDITION
        ):
            order = int(mn.group(1))
            nce_ids.add(nid)
            c = (ranks["new_concept_english_1"], 0, 0, order, note_num(nid))
            first_coord[nid] = min(first_coord.get(nid, c), c)
            continue

        m56 = G56_RE.match(key)
        if m56 is not None:
            grade, sem, unit, order = m56.groups()
            book = grade + ("上" if sem == "upper" else "下")
            if book not in accepted_books:
                continue
            g56_ids.add(nid)
            segment = "grade5" if grade == "5" else "grade6"
            c = (ranks[segment], SEM_RANK[sem], int(unit), int(order), note_num(nid))
            first_coord[nid] = min(first_coord.get(nid, c), c)

    if not grade4_ids:
        raise SystemExit("Actual Grade-4 current identity set is empty")
    if not g56_ids:
        raise SystemExit("Accepted Grade 5-6 current identity set is empty")
    ordered = [nid for nid, _ in sorted(first_coord.items(), key=lambda item: item[1])]
    return ordered, grade4_ids, nce_ids, g56_ids


def main() -> None:
    for path in (LEGACY_RELEASES, RELEASE_EXTENSIONS, REGISTRY, REGISTRY_EXTENSIONS, SOURCE_IDENTITIES, G56_SCOPE, CURRICULUM):
        if not path.exists():
            raise SystemExit(f"Missing learning-admission input: {path.relative_to(ROOT)}")

    registry_ids = {
        r["NoteID"].strip()
        for path in (REGISTRY, REGISTRY_EXTENSIONS)
        for r in read_csv(path)
        if r.get("Status", "").strip() == "active"
    }
    released: set[str] = set()
    for path in (LEGACY_RELEASES, RELEASE_EXTENSIONS):
        for row in read_csv(path):
            nid = row.get("NoteID", "").strip()
            if not nid or nid in released:
                raise SystemExit(f"Invalid/duplicate released NoteID across registries: {nid!r}")
            released.add(nid)
    if not released.issubset(registry_ids):
        raise SystemExit("Release registries reference unknown Stable NoteIDs")

    ordered_current, grade4_ids, nce_ids, g56_ids = current_scope()
    current = set(ordered_current)
    if not current.issubset(registry_ids):
        missing = sorted(current - registry_ids, key=note_num)
        raise SystemExit(f"Current curriculum references unknown Stable NoteIDs: {missing[:10]}")

    order_by_id = {nid: format_learning_order(i) for i, nid in enumerate(ordered_current, start=1)}
    universe = released | current
    rows: list[dict[str, str]] = []
    for nid in sorted(universe, key=note_num):
        if nid in current:
            # Earliest curriculum segment wins for identities repeated by later sources.
            if nid in grade4_ids:
                stage, tag, reason = GRADE4_STAGE, GRADE4_TAG, "actual-grade4-current"
            elif nid in nce_ids:
                stage, tag, reason = NCE_STAGE, NCE_TAG, "accepted-nce1-current"
            else:
                stage, tag, reason = G56_STAGE, G56_TAG, "accepted-grade5-6-current"
            rows.append({
                "LearnerProfile": PROFILE,
                "LearnerLevel": LEVEL,
                "NoteID": nid,
                "Stage": stage,
                "Status": "allowed",
                "LearningTag": tag,
                "LearningOrder": order_by_id[nid],
                "Reason": reason,
            })
        else:
            rows.append({
                "LearnerProfile": PROFILE,
                "LearnerLevel": LEVEL,
                "NoteID": nid,
                "Stage": HELD_STAGE,
                "Status": "held",
                "LearningTag": "",
                "LearningOrder": "",
                "Reason": "released-library-held",
            })

    write_csv(OUT, rows)
    new_unreleased = current - released
    current_g56_only = g56_ids - grade4_ids - nce_ids
    print(
        "Learning admission built: "
        f"registry={len(registry_ids)}, released={len(released)}, current={len(current)}, "
        f"grade4={len(grade4_ids)}, nce1={len(nce_ids)}, grade5_6={len(g56_ids)}, grade5_6_only={len(current_g56_only)}, "
        f"current_unreleased={len(new_unreleased)}, library_held={len(released-current)}, "
        f"learning_order={format_learning_order(1)}..{format_learning_order(len(current))}"
    )


if __name__ == "__main__":
    main()
