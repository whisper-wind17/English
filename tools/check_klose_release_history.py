#!/usr/bin/env python3
"""Protect byte- and row-level append-only Klose Vocabulary Release history."""
from __future__ import annotations

import csv
import io
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose" / "master"
RELEASE = BASE / "release_registry.csv"
RELEASE_EXT = BASE / "release_registry_extensions.csv"
FIELDS = ["NoteID", "ReleasedAt", "ReleaseReason"]
NOTE_RE = re.compile(r"KV\d{6}$")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}$")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_csv_bytes(data: bytes) -> list[dict[str, str]]:
    text = data.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text, newline="")))


def git_bytes(ref: str, path: Path) -> bytes | None:
    rel = path.relative_to(ROOT).as_posix()
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel}"], cwd=ROOT,
        capture_output=True,
    )
    return proc.stdout if proc.returncode == 0 else None


def normalized(rows: list[dict[str, str]]) -> list[tuple[str, str, str]]:
    result: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for row in rows:
        values = tuple(row.get(f, "").strip() for f in FIELDS)
        nid, released_at, reason = values
        if not NOTE_RE.fullmatch(nid) or nid in seen:
            raise SystemExit(f"Invalid/duplicate Release NoteID: {nid!r}")
        if not DATE_RE.fullmatch(released_at) or not reason:
            raise SystemExit(f"Invalid Release metadata: {values}")
        seen.add(nid)
        result.append(values)
    return result


def main() -> None:
    for path in (RELEASE, RELEASE_EXT):
        if not path.exists():
            raise SystemExit(f"Missing Release registry: {path.relative_to(ROOT)}")

    legacy_bytes = RELEASE.read_bytes()
    ext_bytes = RELEASE_EXT.read_bytes()
    legacy = normalized(read_csv(RELEASE))
    ext = normalized(read_csv(RELEASE_EXT))
    all_ids = [row[0] for row in legacy + ext]
    if len(all_ids) != len(set(all_ids)):
        raise SystemExit("Duplicate Release NoteID across legacy and extension registries")

    ref = os.environ.get("KLOSE_BASE_COMMIT", "").strip() or "HEAD^"
    old_legacy_bytes = git_bytes(ref, RELEASE)
    old_ext_bytes = git_bytes(ref, RELEASE_EXT)
    if old_legacy_bytes is None:
        print(f"Release-history warning: Git baseline {ref!r} unavailable; historical comparison skipped")
        return
    old_ext_bytes = old_ext_bytes or b""
    old_legacy = normalized(read_csv_bytes(old_legacy_bytes))
    old_ext = normalized(read_csv_bytes(old_ext_bytes)) if old_ext_bytes else []

    if legacy_bytes != old_legacy_bytes or legacy != old_legacy:
        raise SystemExit("Legacy release_registry.csv is byte-level immutable")
    if not ext_bytes.startswith(old_ext_bytes):
        raise SystemExit("release_registry_extensions.csv must preserve historical bytes exactly and append only")
    if len(ext) < len(old_ext) or ext[: len(old_ext)] != old_ext:
        raise SystemExit("release_registry_extensions.csv historical rows changed")

    appended = ext[len(old_ext):]
    old_ids = {row[0] for row in old_legacy + old_ext}
    duplicate_append = [row[0] for row in appended if row[0] in old_ids]
    if duplicate_append:
        raise SystemExit(f"New Release extension rows duplicate historical releases: {duplicate_append[:10]}")

    print(
        f"Vocabulary Release history OK: legacy={len(legacy)}, extension_before={len(old_ext)}, "
        f"extension_now={len(ext)}, appended={len(appended)}, total={len(all_ids)}, byte_prefix=exact"
    )


if __name__ == "__main__":
    main()
