#!/usr/bin/env python3
"""Build the explicit Klose learning-state manifest from committed source/release truth.

Long-lived study and the current learning set are intentionally different:
- every released Note remains in study;
- confirmed Klose actual Grade-4 NoteIDs are `allowed` now;
- every other released Note is `held` in the library.

This manifest is deterministic. It does not infer learning scope from FirstGrade.
"""
from __future__ import annotations

import csv
from pathlib import Path

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
    "LearningTag", "Reason",
]
PROFILE = "klose"
LEVEL = "4"
CURRENT_STAGE = "stage::grade4-current"
HELD_STAGE = "stage::library"
CURRENT_TAG = "learning::klose::grade4"


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

    current: set[str] = set()
    for row in read_csv(SOURCE_IDENTITIES):
        if (
            row.get("SourceID", "").strip() == "rj_start1"
            and row.get("SourceEdition", "").strip() == "klose-current"
            and row.get("Status", "").strip() == "confirmed"
            and row.get("SourceItemKey", "").strip().startswith("grade4-")
        ):
            nid = row.get("NoteID", "").strip()
            if not nid:
                raise SystemExit("Confirmed actual Grade-4 identity has no NoteID")
            current.add(nid)

    if not current:
        raise SystemExit("Actual Grade-4 current learning set is empty")
    if not current.issubset(released):
        missing = sorted(current - released, key=note_num)
        raise SystemExit(f"Current Grade-4 Notes are not released: {missing[:10]}")

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
            "Reason": "actual-grade4-current" if allowed else "released-library-held",
        })

    write_csv(OUT, rows)
    held = len(released) - len(current)
    print(
        f"Learning admission built: released={len(released)}, "
        f"allowed={len(current)}, held={held}, tag={CURRENT_TAG}"
    )


if __name__ == "__main__":
    main()
