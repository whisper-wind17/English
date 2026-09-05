#!/usr/bin/env python3
"""One-time, idempotent migration for actual Grade-4 `speak` sense.

Actual Grade 4 teaches `speak = 说话；发言`, while the existing KV000705
identity is scoped to `说；讲（某种语言）`. Preserve KV000705 and append a new
learning-unit identity for the actual textbook occurrence.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master"
LEARNER = BASE / "learner"
LEGACY_REGISTRY = MASTER / "note_registry.csv"
REGISTRY_EXT = MASTER / "note_registry_extensions.csv"
SOURCE_EXT = MASTER / "source_identity_extensions.csv"
RELEASE_EXT = MASTER / "release_registry_extensions.csv"
FACTS = MASTER / "actual_grade4_fact_overrides.csv"
LEARNER_OVERRIDES = LEARNER / "actual_grade4_overrides.csv"
MIGRATIONS = MASTER / "identity_migrations.csv"

SOURCE_KEY = "grade4-upper-u05-o001|speak"
LEGACY_NOTE = "KV000705"
ORIGIN = "rj_start1|klose-current|grade4-upper-u05-o001|speak"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def note_num(nid: str) -> int:
    m = re.fullmatch(r"KV(\d{6})", nid)
    if not m:
        raise SystemExit(f"Invalid NoteID: {nid!r}")
    return int(m.group(1))


def main() -> None:
    required = (
        LEGACY_REGISTRY, REGISTRY_EXT, SOURCE_EXT, RELEASE_EXT,
        FACTS, LEARNER_OVERRIDES, MIGRATIONS,
    )
    for path in required:
        if not path.exists():
            raise SystemExit(f"Missing speak migration input: {path.relative_to(ROOT)}")

    legacy = read_csv(LEGACY_REGISTRY)
    ext = read_csv(REGISTRY_EXT)
    existing_by_origin = {r.get("PrimaryOriginKey", "").strip(): r for r in ext}
    existing = existing_by_origin.get(ORIGIN)

    mappings = read_csv(SOURCE_EXT)
    mapping = next(
        (r for r in mappings
         if r.get("SourceID", "").strip() == "rj_start1"
         and r.get("SourceEdition", "").strip() == "klose-current"
         and r.get("SourceItemKey", "").strip() == SOURCE_KEY),
        None,
    )
    if mapping is None:
        raise SystemExit(f"Missing actual Grade-4 speak source mapping: {SOURCE_KEY}")

    if existing is not None:
        new_nid = existing["NoteID"].strip()
        if mapping.get("NoteID", "").strip() != new_nid:
            raise SystemExit(
                f"Partial speak migration detected: identity={new_nid}, "
                f"mapping={mapping.get('NoteID', '')}"
            )
        print(f"Speak sense migration already applied: {new_nid}")
        return

    if mapping.get("NoteID", "").strip() != LEGACY_NOTE:
        raise SystemExit(
            f"Unexpected pre-migration speak mapping: {mapping.get('NoteID', '')}; "
            f"expected {LEGACY_NOTE}"
        )

    all_ids = [r["NoteID"].strip() for r in legacy + ext]
    new_nid = f"KV{max(note_num(nid) for nid in all_ids) + 1:06d}"

    ext.append({
        "NoteID": new_nid,
        "CanonicalWord": "speak",
        "MatchKey": "speak",
        "SenseLabel": "说话；发言",
        "PrimaryOriginKey": ORIGIN,
        "CreatedSource": "rj_start1",
        "CreatedSourceBook": "klose-current::4年级上",
        "Status": "active",
    })
    ext.sort(key=lambda r: note_num(r["NoteID"]))

    mapping["NoteID"] = new_nid
    mapping["Decision"] = "new-distinct-sense"
    mapping["Status"] = "confirmed"

    releases = read_csv(RELEASE_EXT)
    old_count = len(releases)
    releases = [r for r in releases if r.get("NoteID", "").strip() != LEGACY_NOTE]
    if any(r.get("NoteID", "").strip() == new_nid for r in releases):
        raise SystemExit(f"Unexpected duplicate release before speak migration: {new_nid}")
    releases.append({
        "NoteID": new_nid,
        "ReleasedAt": "2026-09-05",
        "ReleaseReason": "actual-grade4-klose-current",
    })
    releases.sort(key=lambda r: note_num(r["NoteID"]))
    if len(releases) != old_count:
        raise SystemExit(
            "Speak release migration must swap one extension NoteID without changing count"
        )

    facts = read_csv(FACTS)
    if any(r.get("NoteID", "").strip() == new_nid for r in facts):
        raise SystemExit(f"Duplicate speak fact override: {new_nid}")
    facts.append({
        "NoteID": new_nid,
        "Word": "speak",
        "British": "[spiːk]",
        "American": "[spiːk]",
        "MeaningPrimary": "说话；发言",
        "FactStatus": "model-curated",
        "FactSource": "klose-actual-grade4",
    })
    facts.sort(key=lambda r: note_num(r["NoteID"]))

    learner = read_csv(LEARNER_OVERRIDES)
    if any(r.get("NoteID", "").strip() == new_nid for r in learner):
        raise SystemExit(f"Duplicate speak learner override: {new_nid}")
    learner.append({
        "NoteID": new_nid,
        "ExampleSentence": "I want to speak in class.",
        "ExampleTranslation": "我想在课堂上发言。",
    })
    learner.sort(key=lambda r: note_num(r["NoteID"]))

    migrations = read_csv(MIGRATIONS)
    migration_id = "MIG-20260905-G4-SPEAK-SENSE"
    if not any(r.get("MigrationID", "").strip() == migration_id for r in migrations):
        migrations.append({
            "MigrationID": migration_id,
            "NoteID": new_nid,
            "MigrationType": "source-occurrence-sense-split",
            "Reason": "Actual Grade 4 speak=说话；发言 differs from legacy language-speaking sense KV000705",
            "Status": "approved",
        })

    write_csv(REGISTRY_EXT, list(ext[0].keys()), ext)
    write_csv(SOURCE_EXT, list(mappings[0].keys()), mappings)
    write_csv(RELEASE_EXT, list(releases[0].keys()), releases)
    write_csv(FACTS, list(facts[0].keys()), facts)
    write_csv(LEARNER_OVERRIDES, list(learner[0].keys()), learner)
    write_csv(MIGRATIONS, ["MigrationID", "NoteID", "MigrationType", "Reason", "Status"], migrations)

    print(f"Applied actual Grade-4 speak sense split: {LEGACY_NOTE} -> {new_nid}")


if __name__ == "__main__":
    main()
