#!/usr/bin/env python3
"""Materialize committed Vocabulary Release registry truth into the derived Master.

The combined legacy + extension release registries are authoritative for the
`Released` bit. Source overlays may construct Master rows, but they must not own
long-term release truth. This step runs after source/identity overlays and before
publish regeneration.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose" / "master"
MASTER = BASE / "vocabulary_master.csv"
RELEASE = BASE / "release_registry.csv"
RELEASE_EXT = BASE / "release_registry_extensions.csv"
STATS = BASE / "build_stats.csv"
ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}$")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing release materialization input: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def with_release_tag(tags: str, released: bool) -> str:
    parts = [x for x in (tags or "").split() if x != "learner::klose::released"]
    if released:
        parts.append("learner::klose::released")
    return " ".join(sorted(set(parts)))


def upsert_metric(rows: list[dict[str, str]], metric: str, value: int | str) -> None:
    for row in rows:
        if row.get("Metric") == metric:
            row["Value"] = str(value)
            return
    rows.append({"Metric": metric, "Value": str(value)})


def main() -> None:
    master_rows = read_csv(MASTER)
    release_rows = read_csv(RELEASE) + read_csv(RELEASE_EXT)
    stats = read_csv(STATS)
    if not master_rows:
        raise SystemExit("Vocabulary Master is empty")

    release_ids: set[str] = set()
    for row in release_rows:
        nid = row.get("NoteID", "").strip()
        if not nid or nid in release_ids:
            raise SystemExit(f"Invalid/duplicate release NoteID: {nid!r}")
        if not ISO_DATE_RE.fullmatch(row.get("ReleasedAt", "").strip()):
            raise SystemExit(f"Invalid release date for {nid}")
        if not row.get("ReleaseReason", "").strip():
            raise SystemExit(f"Missing release reason for {nid}")
        release_ids.add(nid)

    master_ids = {r.get("NoteID", "").strip() for r in master_rows}
    if "" in master_ids or len(master_ids) != len(master_rows):
        raise SystemExit("Vocabulary Master contains invalid/duplicate NoteID")
    missing = sorted(release_ids - master_ids)
    if missing:
        raise SystemExit(f"Release registry references Notes absent from active Master: {missing[:10]}")

    before = {r["NoteID"].strip() for r in master_rows if r.get("Released", "").strip() == "yes"}
    for row in master_rows:
        nid = row["NoteID"].strip()
        released = nid in release_ids
        row["Released"] = "yes" if released else "no"
        row["Tags"] = with_release_tag(row.get("Tags", ""), released)

    master_fields = list(master_rows[0].keys())
    write_csv(MASTER, master_fields, master_rows)
    upsert_metric(stats, "released_notes", len(release_ids))
    write_csv(STATS, ["Metric", "Value"], stats)
    print(
        f"Materialized Vocabulary Release truth: before={len(before)}, after={len(release_ids)}, "
        f"newly_visible={len(release_ids - before)}"
    )


if __name__ == "__main__":
    main()
