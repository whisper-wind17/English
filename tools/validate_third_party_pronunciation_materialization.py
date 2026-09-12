#!/usr/bin/env python3
"""Independent Completion Recheck for reviewed pronunciation materialization."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master" / "vocabulary_master.csv"
ADMISSION = BASE / "learner" / "learning_admission.csv"
REVIEWED = BASE / "third_party_vocabulary" / "pronunciation" / "reviewed_pronunciations.csv"
PROFILE = "klose"
LEVEL = "4"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    master_rows = read_csv(MASTER)
    master = {r.get("NoteID", "").strip(): r for r in master_rows}
    allowed = {
        r.get("NoteID", "").strip()
        for r in read_csv(ADMISSION)
        if r.get("LearnerProfile", "").strip() == PROFILE
        and r.get("LearnerLevel", "").strip() == LEVEL
        and r.get("Status", "").strip() == "allowed"
    }
    reviewed_rows = read_csv(REVIEWED)
    reviewed = {r.get("NoteID", "").strip(): r for r in reviewed_rows}
    errors: list[str] = []

    if not reviewed_rows or "" in reviewed or len(reviewed_rows) != len(reviewed):
        errors.append(f"reviewed pronunciation rows={len(reviewed_rows)} unique={len(reviewed)}")
    for nid, evidence in reviewed.items():
        m = master.get(nid)
        if m is None:
            errors.append(f"{nid}: missing Master row")
            continue
        if m.get("CanonicalWord", "").strip() != evidence.get("CanonicalWord", "").strip():
            errors.append(f"{nid}: CanonicalWord drift")
        for side in ("British", "American"):
            if not evidence.get(side, "").strip():
                errors.append(f"{nid}: reviewed {side} blank")
            elif m.get(side, "").strip() != evidence.get(side, "").strip():
                errors.append(f"{nid}: Master {side} != reviewed evidence")

    remaining = [
        nid for nid in sorted(allowed)
        if nid not in master
        or not master[nid].get("British", "").strip()
        or not master[nid].get("American", "").strip()
    ]
    if remaining:
        errors.append(f"allowed pronunciation debt remains={len(remaining)} examples={remaining[:20]}")

    if errors:
        print("\n".join(errors[:100]))
        raise SystemExit(f"Pronunciation materialization failed: {len(errors)} errors")
    print(
        f"Pronunciation materialization = PASS: reviewed={len(reviewed)} allowed={len(allowed)} "
        "allowed_pronunciation_debt=0"
    )


if __name__ == "__main__":
    main()
