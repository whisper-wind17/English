#!/usr/bin/env python3
"""Validate and protect existing Klose Expressions persistent master state."""
from __future__ import annotations

import csv
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "anki" / "klose" / "expressions" / "master"
REGISTRY = MASTER / "expression_registry.csv"
OCCURRENCES = MASTER / "expression_occurrences.csv"
SOURCE_MAP = MASTER / "source_expression_map.csv"
RELEASE = MASTER / "release_registry.csv"
ID_RE = re.compile(r"^KE\d{6}$")
OCC_RE = re.compile(r"^EO\d{6}$")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def baseline_ref() -> str:
    return os.environ.get("KLOSE_BASE_COMMIT", "").strip() or "HEAD^"


def git_text(ref: str, path: Path) -> str | None:
    rel = path.relative_to(ROOT).as_posix()
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel}"], cwd=ROOT, text=True, capture_output=True, encoding="utf-8"
    )
    return proc.stdout if proc.returncode == 0 else None


def main() -> None:
    for path in (REGISTRY, OCCURRENCES, SOURCE_MAP, RELEASE):
        if not path.exists():
            raise SystemExit(f"Missing Klose Expression master state: {path.relative_to(ROOT)}")

    registry_rows = read_csv(REGISTRY)
    registry: dict[str, dict[str, str]] = {}
    for row in registry_rows:
        eid = row.get("ExpressionID", "").strip()
        if not ID_RE.fullmatch(eid) or eid in registry:
            raise SystemExit(f"Invalid/duplicate ExpressionID: {eid!r}")
        if not row.get("CanonicalForm", "").strip() or not row.get("FunctionKey", "").strip():
            raise SystemExit(f"Incomplete Expression identity: {eid}")
        registry[eid] = row

    if len(registry) != 66:
        raise SystemExit(f"Unexpected Stable Expression registry size: {len(registry)} != 66")

    occurrences: set[str] = set()
    for row in read_csv(OCCURRENCES):
        oid = row.get("OccurrenceID", "").strip()
        if not OCC_RE.fullmatch(oid) or oid in occurrences:
            raise SystemExit(f"Invalid/duplicate Expression OccurrenceID: {oid!r}")
        occurrences.add(oid)

    map_keys: set[tuple[str, str]] = set()
    for row in read_csv(SOURCE_MAP):
        oid = row.get("OccurrenceID", "").strip()
        eid = row.get("ExpressionID", "").strip()
        key = (oid, eid)
        if oid not in occurrences or eid not in registry or key in map_keys:
            raise SystemExit(f"Invalid/duplicate Expression source mapping: {key}")
        if row.get("MappingStatus", "").strip() != "confirmed":
            raise SystemExit(f"Unconfirmed persistent Expression source mapping: {key}")
        map_keys.add(key)

    release_ids: set[str] = set()
    for row in read_csv(RELEASE):
        eid = row.get("ExpressionID", "").strip()
        if eid not in registry or eid in release_ids:
            raise SystemExit(f"Invalid/duplicate Expression release identity: {eid!r}")
        release_ids.add(eid)

    ref = baseline_ref()
    changed: list[str] = []
    for path in (REGISTRY, OCCURRENCES, SOURCE_MAP, RELEASE):
        old = git_text(ref, path)
        if old is None:
            raise SystemExit(f"Expression persistent-state baseline unavailable: {ref}:{path.relative_to(ROOT)}")
        current = path.read_text(encoding="utf-8-sig")
        if old.lstrip("\ufeff") != current.lstrip("\ufeff"):
            changed.append(path.relative_to(ROOT).as_posix())
    if changed:
        raise SystemExit(f"Klose Expression persistent master mutation forbidden in reconciliation stage: {changed}")

    print(
        "Expression persistent state OK: "
        f"registry={len(registry)}, occurrences={len(occurrences)}, "
        f"source_mappings={len(map_keys)}, release={len(release_ids)}, baseline={ref}"
    )


if __name__ == "__main__":
    main()
