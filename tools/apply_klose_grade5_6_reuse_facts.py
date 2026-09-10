#!/usr/bin/env python3
"""Fill missing lexical facts for existing Stable Notes admitted by Grade 5-6 scope.

This overlay is deliberately narrow: it may only fill blank British/American IPA
on already-existing Notes. It must not change Word, Meaning, identity, release state,
or learner presentation.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master" / "vocabulary_master.csv"
OVERRIDES = BASE / "master" / "grade5_6_reuse_fact_overrides.csv"
DECISIONS = BASE / "review" / "grade5_6_reconciliation" / "vocabulary_decisions.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def main() -> None:
    for path in (MASTER, OVERRIDES, DECISIONS):
        if not path.exists():
            raise SystemExit(f"Missing Grade 5-6 reuse-fact input: {path.relative_to(ROOT)}")

    rows = read_csv(MASTER)
    fields = list(rows[0].keys())
    by_id = {r["NoteID"].strip(): r for r in rows}
    reused = {
        r.get("DecisionNoteID", "").strip()
        for r in read_csv(DECISIONS)
        if r.get("Decision", "").strip() == "reuse-existing"
    }

    overrides = read_csv(OVERRIDES)
    seen: set[str] = set()
    changed = 0
    for override in overrides:
        nid = override.get("NoteID", "").strip()
        if not nid or nid in seen:
            raise SystemExit(f"Invalid/duplicate Grade 5-6 reuse fact override: {nid!r}")
        seen.add(nid)
        if nid not in reused:
            raise SystemExit(f"Fact override is not a reviewed Grade 5-6 reuse Note: {nid}")
        target = by_id.get(nid)
        if target is None:
            raise SystemExit(f"Fact override references Note absent from derived Master: {nid}")
        if override.get("FactStatus", "").strip() != "model-curated":
            raise SystemExit(f"Unexpected FactStatus for {nid}")
        if override.get("FactSource", "").strip() != "klose-grade5-6-current":
            raise SystemExit(f"Unexpected FactSource for {nid}")
        british = override.get("British", "").strip()
        american = override.get("American", "").strip()
        if not british or not american:
            raise SystemExit(f"Incomplete IPA override for {nid}")
        for field, value in (("British", british), ("American", american)):
            current = target.get(field, "").strip()
            if current and current != value:
                raise SystemExit(
                    f"Refusing to overwrite nonblank {field} for {nid}: current={current!r} override={value!r}"
                )
            if not current:
                target[field] = value
                changed += 1

    write_csv(MASTER, fields, rows)
    print(f"Applied Grade 5-6 reused fact overrides: notes={len(seen)}, fields_filled={changed}")


if __name__ == "__main__":
    main()
