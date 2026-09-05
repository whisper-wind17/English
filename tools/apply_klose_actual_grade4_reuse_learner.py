#!/usr/bin/env python3
"""Apply learner-presentation overrides for actual Grade-4 reused identities.

This runs after the ordinary learner override stack so actual textbook forms win
without changing Stable NoteID or canonical identity.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
LEARNER = BASE / "learner" / "current.csv"
OVERRIDES = BASE / "learner" / "actual_grade4_reuse_overrides.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    for path in (LEARNER, OVERRIDES):
        if not path.exists():
            raise SystemExit(f"Missing learner reuse input: {path.relative_to(ROOT)}")

    rows = read_csv(LEARNER)
    if not rows:
        raise SystemExit("learner/current.csv is empty")
    fields = list(rows[0].keys())
    by_id = {r["NoteID"].strip(): r for r in rows}
    seen: set[str] = set()
    applied = 0

    for row in read_csv(OVERRIDES):
        nid = row.get("NoteID", "").strip()
        if not nid or nid in seen:
            raise SystemExit(f"Invalid/duplicate Grade-4 reused learner override: {nid!r}")
        seen.add(nid)
        if nid not in by_id:
            raise SystemExit(f"Reused learner override references unknown NoteID: {nid}")
        example = row.get("ExampleSentence", "").strip()
        translation = row.get("ExampleTranslation", "").strip()
        if not example or not translation:
            raise SystemExit(f"Incomplete reused learner override: {nid}")
        target = by_id[nid]
        target["ExampleSentence"] = example
        target["ExampleTranslation"] = translation
        target["PresentationStatus"] = "grade4-reviewed"
        target["PresentationSource"] = "klose:actual_grade4_reuse_overrides"
        applied += 1

    rows.sort(key=lambda r: int(r["NoteID"].removeprefix("KV")))
    write_csv(LEARNER, fields, rows)
    print(f"Applied actual Grade-4 reused learner presentations: {applied}")


if __name__ == "__main__":
    main()
