#!/usr/bin/env python3
"""Protect persistent Klose Vocabulary identity/release state.

Checks current snapshot consistency and Git-baseline stability. Existing NoteIDs may
be appended to, but cannot disappear or silently change identity-defining fields.
Any intentional identity mutation requires an explicit approved migration record.

The legacy registry remains immutable baseline state. New actual-textbook learning
units are appended in note_registry_extensions.csv so schema evolution does not
rewrite the existing 802 identities.

CI should set KLOSE_BASE_COMMIT to the commit that existed before the current
change set (PR base SHA or push event.before). HEAD^ is only a local fallback.
"""
from __future__ import annotations

import csv
import io
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose" / "master"
REGISTRY = BASE / "note_registry.csv"
REGISTRY_EXTENSIONS = BASE / "note_registry_extensions.csv"
RELEASES = BASE / "release_registry.csv"
SOURCE_MAP = BASE / "source_identity_map.csv"
SOURCE_EXTENSIONS = BASE / "source_identity_extensions.csv"
MIGRATIONS = BASE / "identity_migrations.csv"
NOTE_RE = re.compile(r"KV(\d{6})$")
IDENTITY_FIELDS = ("CanonicalWord", "MatchKey", "SenseLabel", "PrimaryOriginKey")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_csv_text(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text.lstrip("\ufeff"))))


def baseline_ref() -> str:
    return os.environ.get("KLOSE_BASE_COMMIT", "").strip() or "HEAD^"


def git_csv_at(ref: str, path: Path, *, required: bool) -> list[dict[str, str]] | None:
    rel = path.relative_to(ROOT).as_posix()
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    if proc.returncode == 0:
        return read_csv_text(proc.stdout)
    if required:
        return None
    # An extension file may legitimately not exist in an older baseline.
    return []


def approved_migration_ids() -> set[str]:
    approved: set[str] = set()
    for row in read_csv(MIGRATIONS):
        if row.get("Status", "").strip() == "approved":
            nid = row.get("NoteID", "").strip()
            if nid:
                approved.add(nid)
    return approved


def check_git_stability(registry: list[dict[str, str]]) -> None:
    ref = baseline_ref()
    legacy = git_csv_at(ref, REGISTRY, required=True)
    if legacy is None:
        print(f"Persistent-state warning: Git baseline {ref!r} unavailable; historical identity check skipped")
        return
    extensions = git_csv_at(ref, REGISTRY_EXTENSIONS, required=False) or []
    baseline = legacy + extensions
    current = {r["NoteID"].strip(): r for r in registry}
    allowed = approved_migration_ids()
    removed: list[str] = []
    changed: list[str] = []
    for old in baseline:
        nid = old.get("NoteID", "").strip()
        if not nid:
            continue
        cur = current.get(nid)
        if cur is None:
            removed.append(nid)
            continue
        if any(old.get(f, "").strip() != cur.get(f, "").strip() for f in IDENTITY_FIELDS):
            if nid not in allowed:
                changed.append(nid)
    if removed or changed:
        raise SystemExit(
            "Historical NoteID stability violation against "
            f"{ref}: removed={removed[:10]} "
            f"changed_without_approved_migration={changed[:10]}"
        )


def main() -> None:
    required = (
        REGISTRY, REGISTRY_EXTENSIONS, RELEASES, SOURCE_MAP,
        SOURCE_EXTENSIONS, MIGRATIONS,
    )
    missing = [p for p in required if not p.exists()]
    if missing:
        raise SystemExit(
            "Persistent Klose state is missing; refusing to rebuild:\n- "
            + "\n- ".join(str(p.relative_to(ROOT)) for p in missing)
        )

    legacy_registry = read_csv(REGISTRY)
    extension_registry = read_csv(REGISTRY_EXTENSIONS)
    registry = legacy_registry + extension_registry
    releases = read_csv(RELEASES)
    if not legacy_registry:
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
        raise SystemExit("Combined registry NoteIDs are not in ascending order")
    if len(numbers) != len(set(numbers)):
        raise SystemExit("Combined registry contains repeated NoteID numbers")
    if extension_registry:
        legacy_max = max(int(NOTE_RE.fullmatch(r["NoteID"].strip()).group(1)) for r in legacy_registry)  # type: ignore[union-attr]
        ext_min = min(int(NOTE_RE.fullmatch(r["NoteID"].strip()).group(1)) for r in extension_registry)  # type: ignore[union-attr]
        if ext_min <= legacy_max:
            raise SystemExit("note_registry_extensions.csv must append after the legacy registry")

    registry_ids = set(ids)
    check_git_stability(registry)

    source_map = read_csv(SOURCE_MAP)
    map_keys: set[tuple[str, str]] = set()
    for row in source_map:
        source_id = row.get("SourceID", "").strip()
        item_key = row.get("SourceItemKey", "").strip()
        nid = row.get("NoteID", "").strip()
        status = row.get("Status", "").strip()
        key = (source_id, item_key)
        if not source_id or not item_key or key in map_keys:
            raise SystemExit(f"Invalid/duplicate legacy SourceIdentity key: {key}")
        if nid not in registry_ids:
            raise SystemExit(f"Source identity references unknown NoteID: {nid}")
        if status != "confirmed":
            raise SystemExit(f"Unconfirmed persistent SourceIdentity row: {key}")
        map_keys.add(key)
    if not source_map:
        raise SystemExit("source_identity_map.csv is empty")

    extension_keys: set[tuple[str, str, str]] = set()
    for row in read_csv(SOURCE_EXTENSIONS):
        source_id = row.get("SourceID", "").strip()
        edition = row.get("SourceEdition", "").strip()
        item_key = row.get("SourceItemKey", "").strip()
        nid = row.get("NoteID", "").strip()
        status = row.get("Status", "").strip()
        key = (source_id, edition, item_key)
        if not all(key) or key in extension_keys:
            raise SystemExit(f"Invalid/duplicate SourceIdentity extension key: {key}")
        if nid not in registry_ids:
            raise SystemExit(f"Source identity extension references unknown NoteID: {nid}")
        if status not in {"confirmed", "pending"}:
            raise SystemExit(f"Invalid SourceIdentity extension status: {key} -> {status!r}")
        extension_keys.add(key)

    release_ids: set[str] = set()
    for row in releases:
        nid = row.get("NoteID", "").strip()
        if nid in release_ids:
            raise SystemExit(f"Duplicate release NoteID: {nid}")
        if nid not in registry_ids:
            raise SystemExit(f"Release references unknown NoteID: {nid}")
        release_ids.add(nid)

    print(
        "Persistent state OK: "
        f"legacy_registry={len(legacy_registry)}, extensions={len(extension_registry)}, "
        f"total_registry={len(registry_ids)}, legacy_source_map={len(source_map)}, "
        f"source_identity_extensions={len(extension_keys)}, released={len(release_ids)}"
    )


if __name__ == "__main__":
    main()
