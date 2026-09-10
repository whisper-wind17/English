#!/usr/bin/env python3
"""Apply a transient reviewed Grade 5–6 Expression batch to durable reconciliation truth.

This mutates only Grade 5–6 reconciliation review state. It never allocates Stable
ExpressionID and never mutates Klose Expressions master / learner / release / publish.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
DIR = BASE / "review" / "grade5_6_reconciliation"
CANDIDATES = DIR / "expression_source_candidates.csv"
BATCH = DIR / "expression_next_batch.csv"
SOURCE_INBOX = DIR / "expression_source_reviewed_batch.csv"
GROUP_INBOX = DIR / "expression_group_reviewed_batch.csv"
SOURCE_DECISIONS = DIR / "expression_source_decisions.csv"
GROUPS = DIR / "expression_identity_groups.csv"
STABLE_REGISTRY = BASE / "expressions" / "master" / "expression_registry.csv"

SOURCE_FIELDS = [
    "SourceOccurrenceKey", "CandidateFingerprint", "Disposition", "IdentityGroups",
    "DecisionBasis", "Rationale",
]
GROUP_FIELDS = [
    "IdentityGroup", "Decision", "ExpressionID", "CanonicalForm", "FunctionKey",
    "ExpressionType", "SlotSchema", "DecisionBasis", "Rationale",
]
VALID_DISPOSITIONS = {"mapped", "source-only", "held"}
VALID_TYPES = {"fixed", "slot_frame", "discourse_frame"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def split_groups(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split("|") if x.strip()]


def main() -> None:
    if not SOURCE_INBOX.exists():
        if GROUP_INBOX.exists():
            raise SystemExit("Expression group reviewed batch exists without source reviewed batch")
        print("No reviewed Grade 5–6 Expression batch to apply.")
        return

    candidates = {r["SourceOccurrenceKey"].strip(): r for r in read_csv(CANDIDATES)}
    current_batch = {r["SourceOccurrenceKey"].strip() for r in read_csv(BATCH)}
    stable_ids = {
        r["ExpressionID"].strip()
        for r in read_csv(STABLE_REGISTRY)
        if r.get("Status", "").strip() == "active"
    }
    if not candidates or not current_batch:
        raise SystemExit("Expression candidates/current batch missing before apply")

    durable_sources = {r["SourceOccurrenceKey"].strip(): r for r in read_csv(SOURCE_DECISIONS)}
    durable_groups = {r["IdentityGroup"].strip(): r for r in read_csv(GROUPS)}

    batch_groups: dict[str, dict[str, str]] = {}
    for row in read_csv(GROUP_INBOX):
        group = row.get("IdentityGroup", "").strip()
        if not group or group in batch_groups:
            raise SystemExit(f"Blank/duplicate reviewed Expression group: {group!r}")
        if group in durable_groups:
            raise SystemExit(f"Refusing to overwrite durable Expression group: {group}")
        if not group.startswith("new::"):
            raise SystemExit(f"New Expression group must start new::: {group}")
        if row.get("Decision", "").strip() != "new-stable-identity":
            raise SystemExit(f"Invalid Expression group decision: {group}")
        if row.get("ExpressionID", "").strip():
            raise SystemExit(f"Reviewed new Expression group cannot allocate ExpressionID: {group}")
        etype = row.get("ExpressionType", "").strip()
        if etype not in VALID_TYPES:
            raise SystemExit(f"Invalid ExpressionType: {group} -> {etype!r}")
        if not row.get("CanonicalForm", "").strip() or not row.get("FunctionKey", "").strip():
            raise SystemExit(f"Incomplete reviewed Expression group metadata: {group}")
        if etype == "fixed" and row.get("SlotSchema", "").strip():
            raise SystemExit(f"Fixed Expression group cannot carry SlotSchema: {group}")
        if not row.get("Rationale", "").strip():
            raise SystemExit(f"Reviewed Expression group lacks rationale: {group}")
        batch_groups[group] = {field: row.get(field, "").strip() for field in GROUP_FIELDS}
        batch_groups[group]["DecisionBasis"] = "model-reviewed-current-evidence"

    reviewed_sources: dict[str, dict[str, str]] = {}
    referenced_in_batch: set[str] = set()
    for row in read_csv(SOURCE_INBOX):
        key = row.get("SourceOccurrenceKey", "").strip()
        if not key or key in reviewed_sources:
            raise SystemExit(f"Blank/duplicate reviewed Expression source key: {key!r}")
        if key not in candidates:
            raise SystemExit(f"Unknown reviewed Expression source key: {key}")
        if key not in current_batch:
            raise SystemExit(f"Reviewed Expression source key is not in current batch: {key}")
        if key in durable_sources:
            raise SystemExit(f"Refusing to overwrite durable Expression source decision: {key}")
        fp = row.get("CandidateFingerprint", "").strip()
        if fp != candidates[key].get("CandidateFingerprint", "").strip():
            raise SystemExit(f"Expression candidate fingerprint mismatch: {key}")
        disposition = row.get("Disposition", "").strip()
        if disposition not in VALID_DISPOSITIONS:
            raise SystemExit(f"Invalid Expression source disposition: {key} -> {disposition!r}")
        groups = split_groups(row.get("IdentityGroups", ""))
        if disposition == "mapped" and not groups:
            raise SystemExit(f"Mapped Expression source lacks identity groups: {key}")
        if disposition != "mapped" and groups:
            raise SystemExit(f"Non-mapped Expression source carries identity groups: {key}")
        for group in groups:
            if group not in stable_ids and group not in durable_groups and group not in batch_groups:
                raise SystemExit(f"Expression source references unknown identity group: {key} -> {group}")
            referenced_in_batch.add(group)
        if not row.get("Rationale", "").strip():
            raise SystemExit(f"Reviewed Expression source lacks rationale: {key}")
        reviewed_sources[key] = {
            "SourceOccurrenceKey": key,
            "CandidateFingerprint": fp,
            "Disposition": disposition,
            "IdentityGroups": "|".join(groups),
            "DecisionBasis": "model-reviewed-current-evidence",
            "Rationale": row.get("Rationale", "").strip(),
        }

    if not reviewed_sources:
        raise SystemExit("Reviewed Expression source batch exists but is empty")
    orphan_new = sorted(set(batch_groups) - referenced_in_batch)
    if orphan_new:
        raise SystemExit(f"Reviewed new Expression groups are not referenced by this batch: {orphan_new[:10]}")

    durable_sources.update(reviewed_sources)
    durable_groups.update(batch_groups)
    write_csv(SOURCE_DECISIONS, SOURCE_FIELDS, [durable_sources[k] for k in sorted(durable_sources)])
    write_csv(GROUPS, GROUP_FIELDS, [durable_groups[k] for k in sorted(durable_groups)])
    SOURCE_INBOX.unlink()
    if GROUP_INBOX.exists():
        GROUP_INBOX.unlink()
    print(
        f"Applied reviewed Grade 5–6 Expression batch: sources={len(reviewed_sources)}, "
        f"new_groups={len(batch_groups)}"
    )


if __name__ == "__main__":
    main()
