#!/usr/bin/env python3
"""Independent completion recheck for Grade 5–6 actual-textbook Expressions reconciliation.

This checker rebuilds source occurrence keys/fingerprints from the four source files
instead of trusting expression_status.json or the planner output. It validates full
coverage, decision/group contracts, representative semantic boundaries, transient
cleanup, and absence of Stable ExpressionID allocation.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
SRC = BASE / "source_reference"
DIR = BASE / "review" / "grade5_6_reconciliation"
STABLE = BASE / "expressions" / "master" / "expression_registry.csv"
SOURCES = [
    SRC / "klose-actual-grade5-upper-expressions.csv",
    SRC / "klose-actual-grade5-lower-expressions.csv",
    SRC / "klose-actual-grade6-upper-expressions.csv",
    SRC / "klose-actual-grade6-lower-expressions.csv",
]
CANDIDATES = DIR / "expression_source_candidates.csv"
DECISIONS = DIR / "expression_source_decisions.csv"
GROUPS = DIR / "expression_identity_groups.csv"
NEXT_BATCH = DIR / "expression_next_batch.csv"
STATUS = DIR / "expression_status.json"
SOURCE_INBOX = DIR / "expression_source_reviewed_batch.csv"
GROUP_INBOX = DIR / "expression_group_reviewed_batch.csv"

FINGERPRINT_FIELDS = [
    "SourceOccurrenceKey", "Grade", "Semester", "Unit", "Order",
    "RawExpression", "Translation", "Page",
]
VALID_DISPOSITIONS = {"mapped", "source-only", "held"}
VALID_TYPES = {"fixed", "slot_frame", "discourse_frame"}


def fail(msg: str) -> None:
    raise SystemExit(f"Expression reconciliation completion failure: {msg}")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def source_key(row: dict[str, str]) -> str:
    sem = {"上": "upper", "下": "lower"}.get(row.get("Semester", "").strip())
    if not sem:
        fail(f"invalid semester in source row: {row}")
    return f"grade{int(row['Grade'])}-{sem}-u{int(row['Unit']):02d}-o{int(row['Order']):03d}"


def fingerprint(row: dict[str, str]) -> str:
    payload = {k: row.get(k, "") for k in FINGERPRINT_FIELDS}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def split_groups(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split("|") if x.strip()]


def main() -> None:
    # Rebuild source truth independently from the four actual-textbook files.
    expected: dict[str, dict[str, str]] = {}
    for path in SOURCES:
        for src in read_csv(path):
            key = source_key(src)
            if key in expected:
                fail(f"duplicate source occurrence key rebuilt from source: {key}")
            row = {
                "SourceOccurrenceKey": key,
                "Grade": src.get("Grade", "").strip(),
                "Semester": src.get("Semester", "").strip(),
                "Unit": src.get("Unit", "").strip(),
                "Order": src.get("Order", "").strip(),
                "RawExpression": src.get("RawExpression", "").strip(),
                "Translation": src.get("Translation", "").strip(),
                "Page": src.get("Page", "").strip(),
            }
            row["CandidateFingerprint"] = fingerprint(row)
            expected[key] = row
    if len(expected) != 153:
        fail(f"rebuilt actual-textbook source count {len(expected)} != 153")

    candidates = read_csv(CANDIDATES)
    candidate_by_key: dict[str, dict[str, str]] = {}
    for row in candidates:
        key = row.get("SourceOccurrenceKey", "").strip()
        if not key or key in candidate_by_key:
            fail(f"blank/duplicate candidate key: {key!r}")
        candidate_by_key[key] = row
    if set(candidate_by_key) != set(expected):
        missing = sorted(set(expected) - set(candidate_by_key))
        extra = sorted(set(candidate_by_key) - set(expected))
        fail(f"candidate/source key mismatch missing={missing[:5]} extra={extra[:5]}")
    for key, src in expected.items():
        cand = candidate_by_key[key]
        for field in ("Grade", "Semester", "Unit", "Order", "RawExpression", "Translation", "Page"):
            if cand.get(field, "").strip() != src[field]:
                fail(f"candidate/source field drift: {key}:{field}")
        if cand.get("CandidateFingerprint", "").strip() != src["CandidateFingerprint"]:
            fail(f"candidate fingerprint drift: {key}")

    stable_rows = [r for r in read_csv(STABLE) if r.get("Status", "").strip() == "active"]
    stable_ids = {r.get("ExpressionID", "").strip() for r in stable_rows}
    if len(stable_ids) != 66 or len(stable_ids) != len(stable_rows):
        fail(f"unexpected Stable Expression registry: rows={len(stable_rows)} unique={len(stable_ids)}")

    group_rows = read_csv(GROUPS)
    group_by_key: dict[str, dict[str, str]] = {}
    canonical_function_pairs: set[tuple[str, str]] = set()
    for row in group_rows:
        group = row.get("IdentityGroup", "").strip()
        if not group or group in group_by_key or not group.startswith("new::"):
            fail(f"invalid/duplicate new group key: {group!r}")
        if row.get("Decision", "").strip() != "new-stable-identity":
            fail(f"invalid new-group decision: {group}")
        if row.get("ExpressionID", "").strip():
            fail(f"Stable ExpressionID allocated during reconciliation: {group}")
        canonical = row.get("CanonicalForm", "").strip()
        function = row.get("FunctionKey", "").strip()
        etype = row.get("ExpressionType", "").strip()
        slots = row.get("SlotSchema", "").strip()
        if not canonical or not function or etype not in VALID_TYPES:
            fail(f"incomplete new-group metadata: {group}")
        if etype == "fixed" and slots:
            fail(f"fixed group carries slots: {group}")
        if etype != "fixed" and not slots:
            fail(f"non-fixed group lacks SlotSchema: {group}")
        if row.get("DecisionBasis", "").strip() != "model-reviewed-current-evidence":
            fail(f"unexpected group DecisionBasis: {group}")
        if not row.get("Rationale", "").strip():
            fail(f"new group lacks rationale: {group}")
        pair = (canonical.casefold(), function)
        if pair in canonical_function_pairs:
            fail(f"duplicate CanonicalForm+FunctionKey group: {canonical!r}/{function}")
        canonical_function_pairs.add(pair)
        group_by_key[group] = row

    decision_rows = read_csv(DECISIONS)
    decision_by_key: dict[str, dict[str, str]] = {}
    disposition_counts: Counter[str] = Counter()
    referenced: set[str] = set()
    for row in decision_rows:
        key = row.get("SourceOccurrenceKey", "").strip()
        if not key or key in decision_by_key or key not in expected:
            fail(f"invalid/duplicate/unknown source decision key: {key!r}")
        if row.get("CandidateFingerprint", "").strip() != expected[key]["CandidateFingerprint"]:
            fail(f"durable decision fingerprint mismatch: {key}")
        disposition = row.get("Disposition", "").strip()
        if disposition not in VALID_DISPOSITIONS:
            fail(f"invalid source disposition: {key} -> {disposition!r}")
        groups = split_groups(row.get("IdentityGroups", ""))
        if len(groups) != len(set(groups)):
            fail(f"duplicate group reference within source decision: {key}")
        if disposition == "mapped" and not groups:
            fail(f"mapped source lacks identity group: {key}")
        if disposition != "mapped" and groups:
            fail(f"non-mapped source carries identity groups: {key}")
        for group in groups:
            if group not in stable_ids and group not in group_by_key:
                fail(f"source references unknown group: {key} -> {group}")
            referenced.add(group)
        if row.get("DecisionBasis", "").strip() != "model-reviewed-current-evidence":
            fail(f"unexpected source DecisionBasis: {key}")
        if not row.get("Rationale", "").strip():
            fail(f"source decision lacks rationale: {key}")
        decision_by_key[key] = row
        disposition_counts[disposition] += 1

    if set(decision_by_key) != set(expected):
        missing = sorted(set(expected) - set(decision_by_key))
        fail(f"source decisions do not cover all 153 occurrences; missing={missing[:10]}")

    expected_dispositions = {"mapped": 138, "source-only": 15}
    if dict(sorted(disposition_counts.items())) != expected_dispositions:
        fail(f"unexpected source disposition counts: {dict(disposition_counts)} != {expected_dispositions}")

    referenced_new = {g for g in referenced if g.startswith("new::")}
    referenced_stable = referenced & stable_ids
    if referenced_new != set(group_by_key):
        orphan = sorted(set(group_by_key) - referenced_new)
        missing = sorted(referenced_new - set(group_by_key))
        fail(f"new-group reference closure failed orphan={orphan[:5]} missing={missing[:5]}")
    if len(referenced_new) != 110:
        fail(f"unexpected new future identity groups: {len(referenced_new)} != 110")
    if len(referenced_stable) != 8:
        fail(f"unexpected reused Stable Expression groups: {len(referenced_stable)} != 8")
    if len(referenced) != 118:
        fail(f"unexpected total referenced identity groups: {len(referenced)} != 118")

    if read_csv(NEXT_BATCH):
        fail("next batch is not empty after claimed closure")
    if SOURCE_INBOX.exists() or GROUP_INBOX.exists():
        fail("transient Expression review inbox still exists")

    # High-risk semantic/boundary regressions.
    expected_examples = {
        "grade5-upper-u01-o001": ("mapped", {"new::ask-person-description"}),
        "grade5-upper-u01-o002": ("mapped", {"KE000027"}),
        "grade5-upper-u02-o001": ("mapped", {"new::describe-look", "new::ask-problem-whats-matter"}),
        "grade5-upper-u03-o003": ("source-only", set()),
        "grade5-upper-u04-o003": ("mapped", {"KE000006"}),
        "grade5-upper-u05-o003": ("mapped", {"KE000009"}),
        "grade5-lower-u05-o004": ("mapped", {"KE000018"}),
        "grade6-upper-u05-o008": ("source-only", set()),
        "grade6-upper-u06-o002": ("source-only", set()),
        "grade6-upper-u06-o009": ("mapped", {"KE000029"}),
        "grade6-lower-u04-o005": ("mapped", {"new::contrast-before-now"}),
        "grade6-lower-u04-o006": ("mapped", {"new::explain-past-inability", "new::state-now-routine"}),
    }
    for key, (want_disposition, want_groups) in expected_examples.items():
        row = decision_by_key[key]
        got_disposition = row.get("Disposition", "").strip()
        got_groups = set(split_groups(row.get("IdentityGroups", "")))
        if (got_disposition, got_groups) != (want_disposition, want_groups):
            fail(
                f"representative decision drift: {key} got={(got_disposition, got_groups)} "
                f"want={(want_disposition, want_groups)}"
            )

    # Shared future groups must actually accumulate cross-occurrence evidence.
    for group, minimum in {
        "new::ask-event-time": 4,
        "new::ask-past-activity": 4,
        "new::ask-past-yesno": 4,
        "new::ask-method-how-can": 3,
        "new::state-future-going-to": 2,
        "new::ask-origin-thing": 2,
    }.items():
        uses = sum(group in split_groups(r.get("IdentityGroups", "")) for r in decision_rows)
        if uses < minimum:
            fail(f"shared future identity unexpectedly under-linked: {group} uses={uses} < {minimum}")

    status = json.loads(STATUS.read_text(encoding="utf-8"))
    checks = {
        "SourceOccurrences": 153,
        "ReviewedSourceOccurrences": 153,
        "SourceDispositionCounts": expected_dispositions,
        "ReferencedIdentityGroups": 118,
        "ReuseExistingExpressionGroups": 8,
        "NewStableIdentityProposalGroups": 110,
        "DefinedNewIdentityGroups": 110,
        "PendingSourceReview": 0,
        "NextBatchCount": 0,
        "StaleSourceDecisionRowsIgnored": 0,
        "StableExpressionRegistry": 66,
        "StableExpressionIDAllocated": False,
        "MasterLearnerReleasePublishMutationAuthorized": False,
        "SourceIdentityPending": True,
    }
    for field, want in checks.items():
        if status.get(field) != want:
            fail(f"status cross-check mismatch {field}: {status.get(field)!r} != {want!r}")

    print(
        "Grade 5–6 Expression reconciliation completion OK: "
        f"source=153, decisions=153, mapped={disposition_counts['mapped']}, "
        f"source_only={disposition_counts['source-only']}, new_groups={len(referenced_new)}, "
        f"reused_stable_groups={len(referenced_stable)}, stable_registry={len(stable_ids)}, "
        "pending=0, transient_inbox=absent, stable_id_allocation=0"
    )


if __name__ == "__main__":
    main()
