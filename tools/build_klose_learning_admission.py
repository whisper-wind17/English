#!/usr/bin/env python3
"""Build the explicit Klose learning-state manifest from committed source/release truth.

Long-lived study and the current learning set are intentionally different:
- every released Note remains in study;
- confirmed Klose actual Grade-4 NoteIDs are `allowed` now;
- every other released Note is `held` in the library;
- allowed Notes receive deterministic curriculum order derived from actual Grade-4
  source item coordinates encoded in confirmed source identity mappings.

This manifest is deterministic. It does not infer learning scope from FirstGrade.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from klose_learning_order import format_learning_order

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master"
LEARNER = BASE / "learner"
LEGACY_RELEASES = MASTER / "release_registry.csv"
RELEASE_EXTENSIONS = MASTER / "release_registry_extensions.csv"
SOURCE_IDENTITIES = MASTER / "source_identity_extensions.csv"
OUT = LEARNER / "learning_admission.csv"

FIELDS = [
    "LearnerProfile", "LearnerLevel", "NoteID", "Stage", "Status",
    "LearningTag", "LearningOrder", "Reason",
]
PROFILE = "klose"
LEVEL = "4"
CURRENT_STAGE = "stage::grade4-current"
HELD_STAGE = "stage::library"
CURRENT_TAG = "learning::klose::grade4"
SOURCE_ID = "rj_start1"
SOURCE_EDITION = "klose-current"
GRADE4_KEY_RE = re.compile(r"^grade4-(upper|lower)-u(\d+)-o(\d+)\|")
SEMESTER_RANK = {"upper": 0, "lower": 1}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def note_num(note_id: str) -> int:
    if not note_id.startswith("KV") or not note_id[2:].isdigit():
        raise SystemExit(f"Invalid NoteID: {note_id!r}")
    return int(note_id[2:])


def ordered_current_note_ids() -> list[str]:
    items: list[tuple[tuple[int, int, int], str, str]] = []
    seen_coordinates: set[tuple[int, int, int]] = set()
    seen_note_ids: set[str] = set()

    for row in read_csv(SOURCE_IDENTITIES):
        if not (
            row.get("SourceID", "").strip() == SOURCE_ID
            and row.get("SourceEdition", "").strip() == SOURCE_EDITION
            and row.get("Status", "").strip() == "confirmed"
            and row.get("SourceItemKey", "").strip().startswith("grade4-")
        ):
            continue

        key = row.get("SourceItemKey", "").strip()
        match = GRADE4_KEY_RE.match(key)
        if match is None:
            raise SystemExit(f"Invalid actual Grade-4 SourceItemKey for ordering: {key!r}")
        semester, unit_text, order_text = match.groups()
        coordinate = (SEMESTER_RANK[semester], int(unit_text), int(order_text))
        if coordinate in seen_coordinates:
            raise SystemExit(f"Duplicate actual Grade-4 curriculum coordinate: {coordinate}")
        seen_coordinates.add(coordinate)

        nid = row.get("NoteID", "").strip()
        if not nid:
            raise SystemExit(f"Confirmed actual Grade-4 identity has no NoteID: {key}")
        if nid in seen_note_ids:
            raise SystemExit(
                "LearningOrder requires one active Note per textbook occurrence; "
                f"duplicate active NoteID={nid}"
            )
        seen_note_ids.add(nid)
        items.append((coordinate, nid, key))

    items.sort(key=lambda item: item[0])
    return [nid for _, nid, _ in items]


def main() -> None:
    for path in (LEGACY_RELEASES, RELEASE_EXTENSIONS, SOURCE_IDENTITIES):
        if not path.exists():
            raise SystemExit(f"Missing learning-admission input: {path.relative_to(ROOT)}")

    released: set[str] = set()
    for path in (LEGACY_RELEASES, RELEASE_EXTENSIONS):
        for row in read_csv(path):
            nid = row.get("NoteID", "").strip()
            if not nid:
                raise SystemExit(f"Missing NoteID in {path.relative_to(ROOT)}")
            if nid in released:
                raise SystemExit(f"Duplicate released NoteID across registries: {nid}")
            released.add(nid)

    ordered_current = ordered_current_note_ids()
    current = set(ordered_current)
    if not current:
        raise SystemExit("Actual Grade-4 current learning set is empty")
    if not current.issubset(released):
        missing = sorted(current - released, key=note_num)
        raise SystemExit(f"Current Grade-4 Notes are not released: {missing[:10]}")

    try:
        order_by_id = {
            nid: format_learning_order(index)
            for index, nid in enumerate(ordered_current, start=1)
        }
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    rows: list[dict[str, str]] = []
    for nid in sorted(released, key=note_num):
        allowed = nid in current
        rows.append({
            "LearnerProfile": PROFILE,
            "LearnerLevel": LEVEL,
            "NoteID": nid,
            "Stage": CURRENT_STAGE if allowed else HELD_STAGE,
            "Status": "allowed" if allowed else "held",
            "LearningTag": CURRENT_TAG if allowed else "",
            "LearningOrder": order_by_id.get(nid, ""),
            "Reason": "actual-grade4-current" if allowed else "released-library-held",
        })

    write_csv(OUT, rows)
    held = len(released) - len(current)
    print(
        f"Learning admission built: released={len(released)}, allowed={len(current)}, "
        f"held={held}, tag={CURRENT_TAG}, "
        f"learning_order={format_learning_order(1)}..{format_learning_order(len(current))}, "
        f"first8={ordered_current[:8]}"
    )


if __name__ == "__main__":
    main()
