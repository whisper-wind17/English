#!/usr/bin/env python3
"""Materialize reviewed pronunciation evidence into derived Vocabulary Master.

Only fills missing British/American IPA. Any disagreement with an existing non-empty
Master pronunciation fails closed. This keeps pronunciation review separate from
Source Fact and avoids overwriting previously established lexical facts.
"""
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


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def main() -> None:
    for path in (MASTER, ADMISSION, REVIEWED):
        if not path.exists():
            raise SystemExit(f"Missing pronunciation materialization input: {path.relative_to(ROOT)}")

    master = read_csv(MASTER)
    if not master:
        raise SystemExit("Vocabulary Master is empty")
    master_by = {r.get("NoteID", "").strip(): r for r in master}
    if "" in master_by or len(master_by) != len(master):
        raise SystemExit("Vocabulary Master has invalid/duplicate NoteID")

    allowed = {
        r.get("NoteID", "").strip()
        for r in read_csv(ADMISSION)
        if r.get("LearnerProfile", "").strip() == PROFILE
        and r.get("LearnerLevel", "").strip() == LEVEL
        and r.get("Status", "").strip() == "allowed"
    }
    reviewed = read_csv(REVIEWED)
    by_id = {r.get("NoteID", "").strip(): r for r in reviewed}
    if len(reviewed) != 616 or len(by_id) != 616:
        raise SystemExit(f"Expected 616 unique reviewed pronunciation rows, got rows={len(reviewed)} unique={len(by_id)}")

    filled_british = filled_american = already_matching = 0
    for nid, evidence in by_id.items():
        if nid not in allowed:
            raise SystemExit(f"Reviewed pronunciation is outside current allowed curriculum: {nid}")
        target = master_by.get(nid)
        if target is None:
            raise SystemExit(f"Reviewed pronunciation references missing Master row: {nid}")
        if evidence.get("CanonicalWord", "").strip() != target.get("CanonicalWord", "").strip():
            raise SystemExit(f"CanonicalWord drift in reviewed pronunciation: {nid}")
        if evidence.get("ReviewerType", "").strip() != "model":
            raise SystemExit(f"Reviewed pronunciation lacks explicit model review: {nid}")
        for side in ("British", "American"):
            value = evidence.get(side, "").strip()
            if not value:
                raise SystemExit(f"Reviewed pronunciation has blank {side}: {nid}")
            current = target.get(side, "").strip()
            if current:
                if current != value:
                    raise SystemExit(
                        f"Refusing to overwrite existing {side} pronunciation: {nid} current={current!r} reviewed={value!r}"
                    )
                already_matching += 1
                continue
            target[side] = value
            if side == "British":
                filled_british += 1
            else:
                filled_american += 1

    remaining = [
        nid for nid in sorted(allowed)
        if nid not in master_by
        or not master_by[nid].get("British", "").strip()
        or not master_by[nid].get("American", "").strip()
    ]
    if remaining:
        raise SystemExit(
            f"Allowed pronunciation debt remains after reviewed materialization: count={len(remaining)} examples={remaining[:20]}"
        )

    fields = list(master[0].keys())
    master.sort(key=lambda r: int(r["NoteID"][2:]))
    write_csv(MASTER, fields, master)
    print(
        "Reviewed pronunciation materialized: "
        f"rows=616 filled_british={filled_british} filled_american={filled_american} "
        f"already_matching_sides={already_matching} allowed_remaining_debt=0"
    )


if __name__ == "__main__":
    main()
