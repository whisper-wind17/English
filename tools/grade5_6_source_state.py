#!/usr/bin/env python3
"""Shared read-only helpers for Grade 5–6 Source provenance state.

Semantic candidate fingerprints intentionally live elsewhere. This module hashes only
the Source provenance binding so a SourceID/Edition correction does not masquerade as
a target-sense or communicative-function change.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "anki" / "klose" / "source_reference"
CONFIG = SRC / "grade5_6_source_provenance.json"
SOURCES = [
    ("vocabulary", SRC / "klose-actual-grade5-6-vocabulary.csv"),
    ("expression", SRC / "klose-actual-grade5-upper-expressions.csv"),
    ("expression", SRC / "klose-actual-grade5-lower-expressions.csv"),
    ("expression", SRC / "klose-actual-grade6-upper-expressions.csv"),
    ("expression", SRC / "klose-actual-grade6-lower-expressions.csv"),
    ("proverb", SRC / "klose-actual-grade5-lower-proverbs.csv"),
    ("morphology", SRC / "klose-actual-grade5-6-morphology.csv"),
]


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _locator(kind: str, row: dict[str, str]) -> str:
    base = f"g{row.get('Grade','').strip()}-{row.get('Semester','').strip()}-u{row.get('Unit','').strip()}-p{row.get('Page','').strip()}"
    if kind in {"vocabulary", "expression"}:
        return base + f"-o{row.get('Order','').strip()}"
    if kind == "proverb":
        return f"g5-下-proverb-o{row.get('Order','').strip()}"
    return base + "-" + "|".join(
        row.get(k, "").strip() for k in ("Lemma", "FormType", "InflectedForm")
    )


def source_provenance_state() -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    payload: list[dict[str, str]] = []
    pending = False
    rows_by_book: dict[str, int] = {}
    for kind, path in SOURCES:
        for row in _rows(path):
            source_id = row.get("SourceID", "").strip()
            edition = row.get("SourceEdition", "").strip()
            if source_id == "pending-confirmation" or edition == "pending-confirmation":
                pending = True
            key = row.get("Grade", "").strip() + row.get("Semester", "").strip()
            rows_by_book[key] = rows_by_book.get(key, 0) + 1
            payload.append({
                "ObjectType": kind,
                "Locator": _locator(kind, row),
                "SourceID": source_id,
                "SourceEdition": edition,
                "EvidenceFileID": row.get("EvidenceFileID", "").strip(),
            })
    payload.sort(key=lambda x: (x["ObjectType"], x["Locator"], x["EvidenceFileID"], x["SourceID"], x["SourceEdition"]))
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    blockers = list(config.get("Blockers", []))
    return {
        "SourceProvenanceFingerprint": fingerprint,
        "SourceProvenanceRows": len(payload),
        "SourceRowsByBook": dict(sorted(rows_by_book.items())),
        "SourceIdentityPending": pending,
        "SourceProvenanceBlockers": blockers,
        "StableIDAllocationAllowed": bool(config.get("StableIDAllocationAllowed", False)) and not pending and not blockers,
        "ResolutionState": config.get("ResolutionState"),
        "CanonicalSourceID": config.get("CanonicalSourceID"),
    }
