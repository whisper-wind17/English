#!/usr/bin/env python3
"""Enforce the post-Phase-A1 Third-party Vocabulary SOURCE FREEZE contract.

This gate is intentionally source-only. It binds the final enabled adapter set,
source-union counts, book count, edition-specific blank-gloss total, config bytes,
and the rebuilt unified occurrence bytes. Identity/Learner/Stage-B state is out of
scope; Klose isolation remains enforced by the workflow's independent git diff.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose" / "third_party_vocabulary"
CONTRACT = BASE / "config" / "source_freeze.json"
CONFIG = BASE / "config" / "source_adapters.csv"
UNIFIED = BASE / "staging" / "occurrences.csv"


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.exists(), f"Missing required file: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    require(CONTRACT.exists(), "SOURCE FREEZE contract is missing")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract.get("FreezeVersion") == "source-freeze-v1", "Unexpected SOURCE FREEZE version")
    require(contract.get("Status") == "frozen", "SOURCE FREEZE status is not frozen")

    expected_ids = contract.get("ExpectedEnabledAdapters")
    require(isinstance(expected_ids, list) and expected_ids, "Frozen adapter set is missing")
    require(len(expected_ids) == len(set(expected_ids)), "Frozen adapter set contains duplicates")

    config_rows = read_csv(CONFIG)
    enabled = [r for r in config_rows if r.get("Enabled", "").strip().casefold() == "yes"]
    enabled_ids = [r.get("SourceID", "").strip() for r in enabled]
    require(enabled_ids == expected_ids, f"Enabled adapter set/order drift: expected={expected_ids} actual={enabled_ids}")
    require(
        sha256(CONFIG) == contract.get("SourceAdaptersFingerprint"),
        "Frozen source_adapters.csv fingerprint drift",
    )

    union_keys: set[str] = set()
    total = 0
    blank_definitions = 0
    books: set[tuple[str, str]] = set()
    for row in enabled:
        source_id = row["SourceID"].strip()
        occurrence_path = ROOT / row["OccurrencesPath"].strip()
        source_rows = read_csv(occurrence_path)
        require(source_rows, f"Frozen adapter has no occurrences: {source_id}")
        require(all(r.get("SourceID") == source_id for r in source_rows), f"SourceID drift: {source_id}")

        keys = [r.get("SourceOccurrenceKey", "") for r in source_rows]
        require(all(keys) and len(keys) == len(set(keys)), f"Blank/duplicate key inside frozen adapter: {source_id}")
        overlap = union_keys & set(keys)
        require(not overlap, f"Cross-adapter occurrence collision after freeze: {source_id}: {sorted(overlap)[:10]}")
        union_keys.update(keys)

        prepare = ROOT / "tools" / f"prepare_third_party_{source_id}.py"
        checker = ROOT / "tools" / f"check_third_party_{source_id}.py"
        require(prepare.exists() and checker.exists(), f"Frozen adapter lost prepare/check contract: {source_id}")

        total += len(source_rows)
        blank_definitions += sum(not r.get("Definition", "").strip() for r in source_rows)
        books.update((source_id, r.get("SourceFile", "")) for r in source_rows if r.get("SourceFile", ""))

    require(total == contract.get("ExpectedSourceOccurrences"), f"Frozen source occurrence drift: {total}")
    require(len(books) == contract.get("ExpectedBooks"), f"Frozen source book-count drift: {len(books)}")
    require(
        blank_definitions == contract.get("ExpectedBlankDefinitions"),
        f"Frozen edition-specific blank Definition drift: {blank_definitions}",
    )

    unified_rows = read_csv(UNIFIED)
    unified_keys = [r.get("SourceOccurrenceKey", "") for r in unified_rows]
    require(len(unified_rows) == total, "Rebuilt unified source occurrence count does not match frozen adapter union")
    require(set(unified_keys) == union_keys and len(unified_keys) == len(set(unified_keys)),
            "Rebuilt unified source occurrence set does not equal frozen adapter union")
    require(
        sha256(UNIFIED) == contract.get("UnifiedOccurrencesFingerprint"),
        "Frozen unified source occurrence fingerprint drift",
    )

    boundaries = contract.get("TerminalScopeBoundaries")
    require(isinstance(boundaries, list) and boundaries, "SOURCE FREEZE lacks reviewed terminal scope boundaries")
    require(all(x.get("Source") and x.get("Disposition") and x.get("Reason") for x in boundaries),
            "SOURCE FREEZE terminal scope boundary is incomplete")

    print("Third-party SOURCE FREEZE = pass")
    print(f"frozen enabled adapters = {len(enabled_ids)}")
    print(f"frozen source occurrences = {total}")
    print(f"frozen source books = {len(books)}")
    print(f"frozen blank definitions = {blank_definitions}")
    print("all planned adapters terminal = yes")
    print("source-adapter union deterministic = yes")
    print("dedicated prepare/check per enabled adapter = yes")
    print("cross-adapter occurrence collision = no")
    print("unexpected Source Fact drift = no")
    print("source config fingerprint frozen = yes")
    print("unified occurrence fingerprint frozen = yes")
    print("Klose mutation checked independently by workflow = yes")


if __name__ == "__main__":
    main()
