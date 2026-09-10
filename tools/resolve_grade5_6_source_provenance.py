#!/usr/bin/env python3
"""Resolve Grade 5–6 actual-textbook SourceID / SourceEdition in-place.

This script mutates Source-layer provenance only. It is intentionally idempotent and
must not allocate Stable NoteID / ExpressionID or touch learner/release/publish/Anki.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "anki" / "klose" / "source_reference"
CONFIG = SRC / "grade5_6_source_provenance.json"
MANIFEST = SRC / "grade5_6_actual_textbook_manifest.csv"
FILES = [
    SRC / "klose-actual-grade5-6-vocabulary.csv",
    SRC / "klose-actual-grade5-upper-expressions.csv",
    SRC / "klose-actual-grade5-lower-expressions.csv",
    SRC / "klose-actual-grade6-upper-expressions.csv",
    SRC / "klose-actual-grade6-lower-expressions.csv",
    SRC / "klose-actual-grade5-lower-proverbs.csv",
    SRC / "klose-actual-grade5-6-morphology.csv",
]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def book_key(row: dict[str, str]) -> str:
    grade = row.get("Grade", "").strip()
    semester = row.get("Semester", "").strip()
    key = grade + semester
    if key not in {"5上", "5下", "6上", "6下"}:
        raise SystemExit(f"Unexpected Grade/Semester while resolving provenance: {grade!r}/{semester!r}")
    return key


def add_status(status: str, marker: str) -> str:
    parts = [p.strip() for p in (status or "").split(";") if p.strip()]
    parts = [p for p in parts if p != "source-identity-pending-confirmation"]
    if marker not in parts:
        parts.append(marker)
    return ";".join(parts)


def resolve_source_file(path: Path, config: dict) -> tuple[int, int]:
    fields, rows = read_csv(path)
    if not rows:
        raise SystemExit(f"Refusing to resolve empty source file: {path.relative_to(ROOT)}")
    for required in ("SourceID", "SourceEdition", "Grade", "Semester", "SourceStatus"):
        if required not in fields:
            raise SystemExit(f"{path.name}: missing required column {required}")
    before = len(rows)
    changed = 0
    canonical_source = config["CanonicalSourceID"]
    for row in rows:
        key = book_key(row)
        book = config["Books"][key]
        expected_edition = book["SourceEdition"]
        current_source = row.get("SourceID", "").strip()
        current_edition = row.get("SourceEdition", "").strip()
        if current_source not in {"pending-confirmation", canonical_source}:
            raise SystemExit(f"{path.name}: unexpected pre-existing SourceID {current_source!r}")
        if current_edition not in {"pending-confirmation", expected_edition}:
            raise SystemExit(
                f"{path.name}: unexpected pre-existing SourceEdition {current_edition!r}; "
                f"expected pending-confirmation or {expected_edition!r}"
            )
        old = dict(row)
        row["SourceID"] = canonical_source
        row["SourceEdition"] = expected_edition
        row["SourceStatus"] = add_status(row.get("SourceStatus", ""), "source-provenance-resolved")
        if not book["StableIDAllocationEligible"]:
            row["SourceStatus"] = add_status(row["SourceStatus"], "source-provenance-held")
        if row != old:
            changed += 1
    if len(rows) != before:
        raise SystemExit(f"{path.name}: row count changed during provenance resolution")
    write_csv(path, fields, rows)
    return before, changed


def resolve_manifest(config: dict) -> tuple[int, int]:
    fields, rows = read_csv(MANIFEST)
    changed = 0
    canonical_source = config["CanonicalSourceID"]
    for row in rows:
        old = dict(row)
        if row.get("ObjectType", "").strip() == "Morphology" and row.get("Grade", "").strip() == "5-6":
            row["SourceID"] = canonical_source
            row["SourceEdition"] = "mixed-by-book"
            row["MaterializationStatus"] = "materialized-source-provenance-resolved-mixed-held"
            row["Notes"] = (
                "58 source occurrences; provenance resolved per Grade/Semester; "
                "5上/6上=2024-revision, 5下/6下=pre-2024-revision; lower-volume allocation held"
            )
        else:
            key = row.get("Grade", "").strip() + row.get("Semester", "").strip()
            if key not in config["Books"]:
                raise SystemExit(f"{MANIFEST.name}: unexpected book key {key!r}")
            book = config["Books"][key]
            row["SourceID"] = canonical_source
            row["SourceEdition"] = book["SourceEdition"]
            row["MaterializationStatus"] = (
                "materialized-source-provenance-resolved"
                if book["StableIDAllocationEligible"]
                else "materialized-source-provenance-resolved-held"
            )
            prior = row.get("Notes", "").strip()
            marker = f"provenance={book['ProvenanceStatus']}"
            if marker not in prior:
                row["Notes"] = (prior + "; " + marker).strip("; ")
        if row != old:
            changed += 1
    write_csv(MANIFEST, fields, rows)
    return len(rows), changed


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config.get("CanonicalSourceID") != "renjiao_start3":
        raise SystemExit("Unexpected canonical SourceID")
    if config.get("ResolutionState") not in {"planned", "applied"}:
        raise SystemExit("Unexpected provenance ResolutionState")
    if config.get("StableIDAllocationAllowed") is not False:
        raise SystemExit("Provenance resolution must not authorize Stable ID allocation")

    total_rows = 0
    total_changed = 0
    for path in FILES:
        rows, changed = resolve_source_file(path, config)
        total_rows += rows
        total_changed += changed
    manifest_rows, manifest_changed = resolve_manifest(config)

    if config.get("ResolutionState") != "applied":
        config["ResolutionState"] = "applied"
        CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        "Grade 5–6 provenance resolved: "
        f"source_rows={total_rows}, changed_rows={total_changed}, "
        f"manifest_rows={manifest_rows}, manifest_changed={manifest_changed}, "
        "StableIDAllocationAllowed=false"
    )


if __name__ == "__main__":
    main()
