#!/usr/bin/env python3
"""Protect persistent Klose Vocabulary state before any rebuild.

After the 2026-09-04 baseline, note_registry.csv and release_registry.csv are
committed state, not disposable generated caches. CI must fail before the build
if either disappears or becomes inconsistent, rather than silently bootstrap a
new identity history.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose" / "master"
REGISTRY = BASE / "note_registry.csv"
RELEASES = BASE / "release_registry.csv"
NOTE_RE = re.compile(r"KV(\d{6})$")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    missing = [p for p in (REGISTRY, RELEASES) if not p.exists()]
    if missing:
        raise SystemExit(
            "Persistent Klose state is missing; refusing to rebuild:\n- "
            + "\n- ".join(str(p.relative_to(ROOT)) for p in missing)
        )

    registry = read_csv(REGISTRY)
    releases = read_csv(RELEASES)
    if not registry:
        raise SystemExit("note_registry.csv is empty")

    ids: list[str] = []
    origins: set[str] = set()
    for row in registry:
        nid = row.get("NoteID", "").strip()
        origin = row.get("PrimaryOriginKey", "").strip()
        if not NOTE_RE.fullmatch(nid):
            raise SystemExit(f"Invalid registry NoteID: {nid!r}")
        if nid in ids:
            raise SystemExit(f"Duplicate registry NoteID: {nid}")
        if not origin:
            raise SystemExit(f"Missing PrimaryOriginKey: {nid}")
        if origin in origins:
            raise SystemExit(f"Duplicate PrimaryOriginKey: {origin}")
        ids.append(nid)
        origins.add(origin)

    numbers = [int(NOTE_RE.fullmatch(nid).group(1)) for nid in ids]  # type: ignore[union-attr]
    if numbers != sorted(numbers):
        raise SystemExit("Registry NoteIDs are not in ascending order")
    if len(numbers) != len(set(numbers)):
        raise SystemExit("Registry contains repeated NoteID numbers")

    registry_ids = set(ids)
    release_ids: set[str] = set()
    for row in releases:
        nid = row.get("NoteID", "").strip()
        if nid in release_ids:
            raise SystemExit(f"Duplicate release NoteID: {nid}")
        if nid not in registry_ids:
            raise SystemExit(f"Release references unknown NoteID: {nid}")
        release_ids.add(nid)

    print(f"Persistent state OK: registry={len(registry_ids)}, released={len(release_ids)}")


if __name__ == "__main__":
    main()
