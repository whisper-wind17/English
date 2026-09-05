#!/usr/bin/env python3
"""Apply actual Grade-4 release-visible facts to reused Vocabulary identities.

This is a presentation/fact overlay only. It deliberately does not mutate
CanonicalWord, MatchKey, SenseLabel, NoteID, or source identity mappings.
It is used when the actual textbook surface/gloss differs from the legacy
canonical form but still represents the same learning-unit identity, e.g.
`sock` reusing the historical `socks` NoteID.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master" / "vocabulary_master.csv"
ACTUAL = BASE / "source_reference" / "rj_start1-grade4-klose-actual.csv"
MAPPINGS = BASE / "master" / "source_identity_extensions.csv"
REGISTRY_EXT = BASE / "master" / "note_registry_extensions.csv"
OVERRIDES = BASE / "master" / "actual_grade4_reuse_fact_overrides.csv"
SOURCE_ID = "rj_start1"
SOURCE_EDITION = "klose-current"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", value.strip()).casefold()


def source_item_key(row: dict[str, str]) -> str:
    sem = {"上": "upper", "下": "lower"}[row["Semester"].strip()]
    return f"grade4-{sem}-u{int(row['Unit']):02d}-o{int(row['Order']):03d}|{norm(row['Entry'])}"


def main() -> None:
    for path in (MASTER, ACTUAL, MAPPINGS, REGISTRY_EXT, OVERRIDES):
        if not path.exists():
            raise SystemExit(f"Missing reused-fact input: {path.relative_to(ROOT)}")

    actual_by_key = {source_item_key(r): r for r in read_csv(ACTUAL)}
    actual_sources_by_note: dict[str, list[dict[str, str]]] = {}
    actual_ids: set[str] = set()
    for row in read_csv(MAPPINGS):
        if (
            row.get("SourceID", "").strip() != SOURCE_ID
            or row.get("SourceEdition", "").strip() != SOURCE_EDITION
            or row.get("Status", "").strip() != "confirmed"
            or not row.get("SourceItemKey", "").strip().startswith("grade4-")
        ):
            continue
        key = row["SourceItemKey"].strip()
        source = actual_by_key.get(key)
        if source is None:
            raise SystemExit(f"Grade-4 mapping has no actual source row: {key}")
        nid = row["NoteID"].strip()
        actual_ids.add(nid)
        actual_sources_by_note.setdefault(nid, []).append(source)

    new_ids = {r["NoteID"].strip() for r in read_csv(REGISTRY_EXT)}
    master_rows = read_csv(MASTER)
    if not master_rows:
        raise SystemExit("vocabulary_master.csv is empty")
    fields = list(master_rows[0].keys())
    master_by_id = {r["NoteID"].strip(): r for r in master_rows}

    seen: set[str] = set()
    applied = 0
    for row in read_csv(OVERRIDES):
        nid = row.get("NoteID", "").strip()
        if not nid or nid in seen:
            raise SystemExit(f"Invalid/duplicate reused fact override: {nid!r}")
        seen.add(nid)
        if nid not in actual_ids:
            raise SystemExit(f"Reused fact override is not in actual Grade 4: {nid}")
        if nid in new_ids:
            raise SystemExit(f"Reused fact override points to a new identity: {nid}")
        if nid not in master_by_id:
            raise SystemExit(f"Reused fact override references unknown Master NoteID: {nid}")
        for field in ("Word", "British", "American", "MeaningPrimary", "FactStatus", "FactSource"):
            if not row.get(field, "").strip():
                raise SystemExit(f"Incomplete reused fact override {nid}: missing {field}")

        sources = actual_sources_by_note[nid]
        if not any(norm(s["Entry"]) == norm(row["Word"]) for s in sources):
            raise SystemExit(
                f"Reused fact Word is not an actual textbook surface for {nid}: {row['Word']!r}"
            )
        if not any(s["Meaning"].strip() == row["MeaningPrimary"].strip() for s in sources):
            raise SystemExit(
                f"Reused fact MeaningPrimary is not the actual textbook gloss for {nid}: "
                f"{row['MeaningPrimary']!r}"
            )

        target = master_by_id[nid]
        target["Word"] = row["Word"].strip()
        target["British"] = row["British"].strip()
        target["American"] = row["American"].strip()
        target["MeaningPrimary"] = row["MeaningPrimary"].strip()
        applied += 1

    master_rows.sort(key=lambda r: int(r["NoteID"].removeprefix("KV")))
    write_csv(MASTER, fields, master_rows)
    print(f"Applied actual Grade-4 reused fact overlays: {applied}")


if __name__ == "__main__":
    main()
