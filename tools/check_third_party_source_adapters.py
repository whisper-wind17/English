#!/usr/bin/env python3
"""Validate closure of every enabled Third-party Vocabulary source adapter.

This is a source-layer gate only. It verifies the invariants shared by every
enabled adapter: standard occurrence schema, SourceID/key closure, dedicated
prepare/check implementations, and a single automated workflow owner.
Edition-specific source quality constraints remain owned by each adapter checker;
the generic gate must not invent stricter rules. It does not perform identity
matching or mutate Klose state.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "anki" / "klose" / "third_party_vocabulary" / "config" / "source_adapters.csv"
UNIFIED_WORKFLOW = ROOT / ".github" / "workflows" / "prepare-third-party-renjiao-start1.yml"
LEGACY_AUTO_WRITERS = [
    ROOT / ".github" / "workflows" / "prepare-klose-beijing-vocabulary.yml",
    ROOT / ".github" / "workflows" / "prepare-third-party-beishida-start1.yml",
    ROOT / ".github" / "workflows" / "prepare-third-party-jijiao-start3.yml",
]
EXPECTED_FIELDS = [
    "SourceOccurrenceKey", "SourceID", "SourceBook", "Grade", "Semester",
    "SourceRow", "Word", "MatchKey", "British", "American", "Definition", "SourceFile",
]
FORBIDDEN_FIELDS = {
    "CandidateNoteIDs", "CandidateSenses", "ProposedNoteID", "StageAClass",
    "AutoDecision", "NeedsSenseReview", "existing-in-klose", "third-party-new",
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise SystemExit(f"Missing required CSV: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def main() -> None:
    if not UNIFIED_WORKFLOW.exists():
        raise SystemExit("Missing unified Third-party Stage-A workflow owner")
    active_legacy = [path.relative_to(ROOT).as_posix() for path in LEGACY_AUTO_WRITERS if path.exists()]
    if active_legacy:
        raise SystemExit(
            "Duplicate source-adapter workflow writers are forbidden; retire: "
            + ", ".join(active_legacy)
        )

    fields, config = read_csv(CONFIG)
    if fields != ["SourceID", "OccurrencesPath", "Enabled"]:
        raise SystemExit(f"Unexpected source-adapter config schema: {fields}")

    enabled = [row for row in config if row.get("Enabled", "").strip().casefold() == "yes"]
    ids = [row.get("SourceID", "").strip() for row in enabled]
    if not ids or any(not source_id for source_id in ids) or len(ids) != len(set(ids)):
        raise SystemExit("Enabled SourceID set must be non-empty, unique, and non-blank")

    global_occurrence_keys: set[str] = set()
    total = 0
    blank_definition_total = 0
    counts: list[tuple[str, int, int]] = []
    missing_tools: list[str] = []

    for row in enabled:
        source_id = row["SourceID"].strip()
        rel = row.get("OccurrencesPath", "").strip()
        if not rel:
            raise SystemExit(f"Enabled adapter lacks OccurrencesPath: {source_id}")
        path = ROOT / rel
        occurrence_fields, occurrences = read_csv(path)
        if occurrence_fields != EXPECTED_FIELDS:
            raise SystemExit(f"Unexpected occurrence schema for {source_id}: {occurrence_fields}")
        if FORBIDDEN_FIELDS & set(occurrence_fields):
            raise SystemExit(f"Identity/reconciliation fields leaked into source adapter {source_id}")
        if not occurrences:
            raise SystemExit(f"Enabled adapter has no occurrences: {source_id}")
        if any(item.get("SourceID") != source_id for item in occurrences):
            raise SystemExit(f"SourceID drift inside adapter output: {source_id}")
        if any(not item.get("Word") or not item.get("MatchKey") for item in occurrences):
            raise SystemExit(f"Blank Word/MatchKey in adapter output: {source_id}")

        # Definition completeness is edition-specific. Some source workbooks have
        # legitimate blank gloss cells; their dedicated checker owns that contract.
        blank_definitions = sum(1 for item in occurrences if not item.get("Definition", "").strip())
        blank_definition_total += blank_definitions

        keys = [item.get("SourceOccurrenceKey", "") for item in occurrences]
        if any(not key for key in keys) or len(keys) != len(set(keys)):
            raise SystemExit(f"Blank/duplicate SourceOccurrenceKey inside adapter: {source_id}")
        overlap = global_occurrence_keys & set(keys)
        if overlap:
            raise SystemExit(f"Cross-adapter SourceOccurrenceKey collision: {source_id}: {sorted(overlap)[:10]}")
        global_occurrence_keys.update(keys)

        prepare = ROOT / "tools" / f"prepare_third_party_{source_id}.py"
        checker = ROOT / "tools" / f"check_third_party_{source_id}.py"
        if not prepare.exists() or not checker.exists():
            missing_tools.append(
                f"{source_id}: prepare={'yes' if prepare.exists() else 'no'} check={'yes' if checker.exists() else 'no'}"
            )
        total += len(occurrences)
        counts.append((source_id, len(occurrences), blank_definitions))

    if missing_tools:
        raise SystemExit("Enabled adapter lacks dedicated prepare/check contract: " + "; ".join(missing_tools))

    print("Third-party enabled Source Adapter closure = pass")
    print(f"enabled adapters = {len(enabled)}")
    for source_id, count, blank_definitions in counts:
        print(f"adapter {source_id} occurrences = {count}; blank definitions = {blank_definitions}")
    print(f"enabled source occurrences = {total}")
    print(f"blank definitions (edition-specific contract) = {blank_definition_total}")
    print("common occurrence schema = enforced")
    print("cross-adapter occurrence-key collision = no")
    print("dedicated prepare/check per enabled adapter = yes")
    print("single automated adapter workflow owner = yes")
    print("legacy duplicate workflow writers = no")
    print("identity/reconciliation fields in occurrence outputs = no")
    print("generic gate invents edition-specific Definition rule = no")
    print("Klose state mutated = no")


if __name__ == "__main__":
    main()
