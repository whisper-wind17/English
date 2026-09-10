#!/usr/bin/env python3
"""Build Grade 5–6 actual-textbook Expression review state.

The source occurrence is the coverage unit. A reviewed occurrence may map to 0..N
Stable/future expression identity groups. New groups carry canonical form +
communicative function metadata, but no Stable ExpressionID is allocated here.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
SRC = BASE / "source_reference"
DIR = BASE / "review" / "grade5_6_reconciliation"
STABLE_REGISTRY = BASE / "expressions" / "master" / "expression_registry.csv"
SOURCES = [
    SRC / "klose-actual-grade5-upper-expressions.csv",
    SRC / "klose-actual-grade5-lower-expressions.csv",
    SRC / "klose-actual-grade6-upper-expressions.csv",
    SRC / "klose-actual-grade6-lower-expressions.csv",
]
CANDIDATES = DIR / "expression_source_candidates.csv"
SOURCE_DECISIONS = DIR / "expression_source_decisions.csv"
GROUPS = DIR / "expression_identity_groups.csv"
NEXT_BATCH = DIR / "expression_next_batch.csv"
STATUS = DIR / "expression_status.json"

CANDIDATE_FIELDS = [
    "SourceOccurrenceKey", "CandidateFingerprint", "Grade", "Semester", "Unit", "Order",
    "RawExpression", "Translation", "Page", "StablePatternMatches",
]
FINGERPRINT_FIELDS = [
    "SourceOccurrenceKey", "Grade", "Semester", "Unit", "Order",
    "RawExpression", "Translation", "Page",
]
SOURCE_DECISION_FIELDS = [
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


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    value = re.sub(r"\s+", " ", value.strip()).casefold()
    return value


def source_key(row: dict[str, str]) -> str:
    sem = {"上": "upper", "下": "lower"}.get(row.get("Semester", "").strip())
    if not sem:
        raise SystemExit(f"Invalid semester: {row}")
    return f"grade{int(row['Grade'])}-{sem}-u{int(row['Unit']):02d}-o{int(row['Order']):03d}"


def fingerprint(row: dict[str, str]) -> str:
    payload = {k: row.get(k, "") for k in FINGERPRINT_FIELDS}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def stable_regex(canonical: str) -> re.Pattern[str]:
    text = norm(canonical)
    pieces: list[str] = []
    pos = 0
    for m in re.finditer(r"\[[^\]]+\]", text):
        pieces.append(re.escape(text[pos:m.start()]))
        pieces.append(r".+?")
        pos = m.end()
    pieces.append(re.escape(text[pos:]))
    pattern = "".join(pieces)
    return re.compile(r"^" + pattern + r"$", re.IGNORECASE)


def split_groups(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split("|") if x.strip()]


def main() -> None:
    stable = [r for r in read_csv(STABLE_REGISTRY) if r.get("Status", "").strip() == "active"]
    if len(stable) != 66:
        raise SystemExit(f"Unexpected Stable Expression registry size: {len(stable)} != 66")
    stable_ids = {r["ExpressionID"].strip() for r in stable}
    patterns = [(r["ExpressionID"].strip(), stable_regex(r["CanonicalForm"])) for r in stable]

    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    source_count = 0
    for path in SOURCES:
        rows = read_csv(path)
        if not rows:
            raise SystemExit(f"Missing/empty actual Expression source: {path.relative_to(ROOT)}")
        for src in rows:
            source_count += 1
            key = source_key(src)
            if key in seen:
                raise SystemExit(f"Duplicate Grade 5–6 Expression source key: {key}")
            seen.add(key)
            core = {
                "SourceOccurrenceKey": key,
                "Grade": src.get("Grade", "").strip(),
                "Semester": src.get("Semester", "").strip(),
                "Unit": src.get("Unit", "").strip(),
                "Order": src.get("Order", "").strip(),
                "RawExpression": src.get("RawExpression", "").strip(),
                "Translation": src.get("Translation", "").strip(),
                "Page": src.get("Page", "").strip(),
            }
            raw_norm = norm(core["RawExpression"])
            matches = [eid for eid, rx in patterns if rx.fullmatch(raw_norm)]
            row = dict(core)
            row["CandidateFingerprint"] = fingerprint(core)
            row["StablePatternMatches"] = " | ".join(matches)
            candidates.append({f: row.get(f, "") for f in CANDIDATE_FIELDS})

    if source_count != 153:
        raise SystemExit(f"Unexpected Grade 5–6 Useful Expression source count: {source_count} != 153")
    write_csv(CANDIDATES, CANDIDATE_FIELDS, candidates)
    by_key = {r["SourceOccurrenceKey"]: r for r in candidates}

    durable_source = read_csv(SOURCE_DECISIONS)
    valid_source: dict[str, dict[str, str]] = {}
    stale = 0
    for row in durable_source:
        key = row.get("SourceOccurrenceKey", "").strip()
        if key not in by_key or row.get("CandidateFingerprint", "").strip() != by_key.get(key, {}).get("CandidateFingerprint", ""):
            stale += 1
            continue
        if key in valid_source:
            raise SystemExit(f"Duplicate durable Expression source decision: {key}")
        disposition = row.get("Disposition", "").strip()
        groups = split_groups(row.get("IdentityGroups", ""))
        if disposition not in VALID_DISPOSITIONS:
            raise SystemExit(f"Invalid Expression source disposition: {key} -> {disposition!r}")
        if disposition == "mapped" and not groups:
            raise SystemExit(f"Mapped Expression source lacks groups: {key}")
        if disposition != "mapped" and groups:
            raise SystemExit(f"Non-mapped Expression source carries groups: {key}")
        valid_source[key] = row

    durable_groups = read_csv(GROUPS)
    group_by_key: dict[str, dict[str, str]] = {}
    for row in durable_groups:
        group = row.get("IdentityGroup", "").strip()
        if not group or group in group_by_key:
            raise SystemExit(f"Blank/duplicate future Expression group: {group!r}")
        if row.get("Decision", "").strip() != "new-stable-identity":
            raise SystemExit(f"Only new-stable-identity belongs in Expression group registry: {group}")
        if row.get("ExpressionID", "").strip():
            raise SystemExit(f"Future Expression group must not allocate ExpressionID: {group}")
        if not group.startswith("new::"):
            raise SystemExit(f"Future Expression group key must start new::: {group}")
        etype = row.get("ExpressionType", "").strip()
        if etype not in VALID_TYPES:
            raise SystemExit(f"Invalid ExpressionType: {group} -> {etype!r}")
        if not row.get("CanonicalForm", "").strip() or not row.get("FunctionKey", "").strip():
            raise SystemExit(f"Incomplete future Expression group metadata: {group}")
        if etype == "fixed" and row.get("SlotSchema", "").strip():
            raise SystemExit(f"Fixed Expression group must not carry SlotSchema: {group}")
        group_by_key[group] = row

    referenced: set[str] = set()
    for row in valid_source.values():
        for group in split_groups(row.get("IdentityGroups", "")):
            if group not in stable_ids and group not in group_by_key:
                raise SystemExit(f"Expression source references unknown group: {group}")
            referenced.add(group)

    pending = [r for r in candidates if r["SourceOccurrenceKey"] not in valid_source]
    selected = pending[:40]
    write_csv(NEXT_BATCH, CANDIDATE_FIELDS, selected)

    dispositions = Counter(r.get("Disposition", "").strip() for r in valid_source.values())
    reuse_groups = {g for g in referenced if g in stable_ids}
    new_groups = {g for g in referenced if g.startswith("new::")}
    status = {
        "SourceOccurrences": len(candidates),
        "ReviewedSourceOccurrences": len(valid_source),
        "SourceDispositionCounts": dict(sorted(dispositions.items())),
        "ReferencedIdentityGroups": len(referenced),
        "ReuseExistingExpressionGroups": len(reuse_groups),
        "NewStableIdentityProposalGroups": len(new_groups),
        "DefinedNewIdentityGroups": len(group_by_key),
        "PendingSourceReview": len(pending),
        "NextBatchCount": len(selected),
        "StaleSourceDecisionRowsIgnored": stale,
        "StableExpressionRegistry": len(stable_ids),
        "StableExpressionIDAllocated": False,
        "MasterLearnerReleasePublishMutationAuthorized": False,
        "SourceIdentityPending": True,
    }
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Grade 5–6 Expression reconciliation status:", json.dumps(status, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
