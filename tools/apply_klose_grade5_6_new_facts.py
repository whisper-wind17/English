#!/usr/bin/env python3
"""Apply reviewed lexical facts to active Grade 5-6 new Vocabulary Notes.

This layer mutates only derived Master British/American fields. Identity, source
mapping, learner presentation, release state and Anki state remain untouched.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
REG = BASE / "master" / "note_registry_extensions.csv"
FACTS = BASE / "master" / "grade5_6_new_fact_overrides.csv"
MASTER = BASE / "master" / "vocabulary_master.csv"
CREATED_SOURCE = "klose-grade5-6-current"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing input: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def main() -> None:
    active = {
        r["NoteID"].strip()
        for r in read_csv(REG)
        if r.get("CreatedSource", "").strip() == CREATED_SOURCE
        and r.get("Status", "").strip() == "active"
    }
    facts_rows = read_csv(FACTS)
    facts = {r["NoteID"].strip(): r for r in facts_rows}
    if len(active) != 288 or len(facts) != 288 or len(facts) != len(facts_rows):
        raise SystemExit(f"Invalid Grade 5-6 fact coverage: active={len(active)} facts={len(facts)} rows={len(facts_rows)}")
    if set(facts) != active:
        raise SystemExit("Grade 5-6 new fact override set must exactly equal active new identities")

    master_rows = read_csv(MASTER)
    fields = list(master_rows[0].keys())
    by_id = {r["NoteID"].strip(): r for r in master_rows}
    if not active <= set(by_id):
        raise SystemExit("Derived Master is missing active Grade 5-6 new identities")

    for nid in active:
        row = by_id[nid]
        fact = facts[nid]
        if row.get("Released", "").strip() != "no":
            raise SystemExit(f"Grade 5-6 new Note unexpectedly released before fact application: {nid}")
        row["British"] = fact["British"].strip()
        row["American"] = fact["American"].strip()

    write_csv(MASTER, fields, master_rows)
    print(f"Applied Grade 5-6 new-note lexical facts: {len(active)}")


if __name__ == "__main__":
    main()
