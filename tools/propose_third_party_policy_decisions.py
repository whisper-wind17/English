#!/usr/bin/env python3
"""Generate conservative deterministic Stage-A policy proposals without applying decisions.

This is a derived review aid. It NEVER writes `identity_decisions.csv` or
`decision_updates.csv`. Proposals are emitted only when the frozen form policy,
directional form relation and current canonical evidence make a reuse candidate
mechanically checkable. Model/human review must still confirm the occurrence is the
same lexical sense before any durable content decision.

Before proposal generation, this tool also injects a small explicit set of
orthographic-identity audits into the derived review bundle. This closes a gap where
US/UK spelling variants could each be reviewed successfully as standalone identities
and therefore never enter the blocker queue. The audit is review-only: it never
merges identities automatically.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
BUNDLE = TP / "audit" / "review_bundle.csv"
OUT = TP / "audit" / "decision_proposals.csv"
DECISIONS = TP / "review" / "identity_decisions.csv"
OCCURRENCES = TP / "staging" / "occurrences.csv"

FIELDS = [
    "ProposalKey",
    "MatchKey",
    "OccurrenceKeys",
    "SuggestedAction",
    "SuggestedCanonicalMatchKey",
    "CanonicalRelation",
    "ObjectType",
    "TargetSense",
    "Status",
    "Confidence",
    "DecisionBasis",
    "Rationale",
    "ActionabilityScore",
    "ReviewLane",
    "ReviewMode",
    "AutoApply",
]

# Explicit review candidates, not automatic equivalence rules. Direction chooses the
# existing canonical spelling that should be reviewed for reuse if both independent
# identities are currently released.
ORTHOGRAPHIC_AUDIT_PAIRS = {
    "color": "colour",
    "favorite": "favourite",
    "neighbor": "neighbour",
    "program": "programme",
}

PEDAGOGICAL_FORM_EXCEPTIONS = {"women"}
SAFE_RELATIONS = {"irregular-form", "regular-past-form", "named-past-form", "contraction"}
GRAMMAR_CANONICALS_REQUIRING_MANUAL_REVIEW = {
    "am", "are", "be", "do", "have", "is", "was", "were",
}
POS_RE = re.compile(r"(?:^|[\s;,/])(?:n|v|vt|vi|adj|adv|prep|pron|conj|aux|int)\.", re.I)
UNSAFE_TEXT_MARKERS = (
    "lexicalized adjective",
    "independent adjective",
    "independent noun",
    "also a lexical",
    "also an independent",
    "semantic collision",
    "multiple target senses",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def decision_summary(rows: list[dict[str, str]]) -> tuple[str, str, str, str]:
    if len(rows) != 1:
        return "", "", "", ""
    row = rows[0]
    return (
        row.get("Action", ""),
        row.get("Status", ""),
        row.get("TargetSense", ""),
        row.get("CanonicalMatchKey", ""),
    )


def orthographic_evidence(
    key: str,
    occurrences_by_match: dict[str, list[dict[str, str]]],
    position: dict[str, tuple[list[dict[str, str]], int]],
) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []
    for occurrence in occurrences_by_match.get(key, []):
        rows, index = position[occurrence["SourceOccurrenceKey"]]
        evidence.append({
            "SourceOccurrenceKey": occurrence["SourceOccurrenceKey"],
            "SourceID": occurrence["SourceID"],
            "SourceBook": occurrence["SourceBook"],
            "Grade": occurrence.get("Grade", ""),
            "Semester": occurrence.get("Semester", ""),
            "SourceRow": occurrence.get("SourceRow", ""),
            "Word": occurrence.get("Word", ""),
            "Definition": occurrence.get("Definition", ""),
            "Before": [row["Word"] for row in rows[max(0, index - 8):index]],
            "After": [row["Word"] for row in rows[index + 1:index + 9]],
        })
    return evidence


def inject_orthographic_identity_audits() -> int:
    """Append review-only audits for independently released spelling variants."""
    bundle = read_csv(BUNDLE)
    with BUNDLE.open("r", encoding="utf-8-sig", newline="") as f:
        bundle_fields = csv.DictReader(f).fieldnames or []
    required_fields = {
        "AuditPriority", "ActionabilityScore", "ReviewLane", "RecommendedBatchSize",
        "BlockerClass", "MatchKey", "DisplayForms", "Definitions", "SourceIDs",
        "SourceBooks", "OccurrenceCount", "CandidateSignals", "CandidateCanonical",
        "CanonicalRelation", "CanonicalExists", "CanonicalAction", "CanonicalStatus",
        "CanonicalTargetSense", "CanonicalDefinitions", "CanonicalOccurrenceCount",
        "PolicyRecommendedAction", "DeferReason", "CurrentAction", "CurrentStatus",
        "CurrentConfidence", "CurrentDecisionBasis", "CurrentRationale",
        "OccurrenceEvidenceJSON",
    }
    if not required_fields <= set(bundle_fields):
        raise SystemExit("Orthographic audit: review bundle schema is incomplete")

    decisions = read_csv(DECISIONS)
    occurrences = read_csv(OCCURRENCES)
    decisions_by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decisions:
        decisions_by_match[row.get("MatchKey", "")].append(row)

    occurrences_by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    books: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in occurrences:
        occurrences_by_match[row.get("MatchKey", "")].append(row)
        books[(row.get("SourceID", ""), row.get("SourceBook", ""))].append(row)

    position: dict[str, tuple[list[dict[str, str]], int]] = {}
    for rows in books.values():
        for index, row in enumerate(rows):
            position[row["SourceOccurrenceKey"]] = (rows, index)

    existing_bundle_keys = {row.get("MatchKey", "") for row in bundle}
    injected: list[str] = []
    for alias, canonical in ORTHOGRAPHIC_AUDIT_PAIRS.items():
        if alias in existing_bundle_keys:
            continue
        alias_rows = decisions_by_match.get(alias, [])
        canonical_rows = decisions_by_match.get(canonical, [])
        alias_action, alias_status, alias_sense, alias_target = decision_summary(alias_rows)
        canonical_action, canonical_status, canonical_sense, _ = decision_summary(canonical_rows)
        if not alias_rows or not canonical_rows:
            continue
        if alias_action == "reuse-identity" and alias_target == canonical and alias_status == "reviewed":
            continue
        if not (
            alias_action == "keep-identity"
            and alias_status == "reviewed"
            and canonical_action == "keep-identity"
            and canonical_status == "reviewed"
            and alias_sense.strip()
            and canonical_sense.strip()
        ):
            continue

        evidence = orthographic_evidence(alias, occurrences_by_match, position)
        if not evidence:
            raise SystemExit(f"Orthographic audit lacks source evidence: {alias}")
        canonical_occ = occurrences_by_match.get(canonical, [])
        source_ids = sorted({row.get("SourceID", "") for row in occurrences_by_match[alias] if row.get("SourceID")})
        source_books = sorted({
            f'{row.get("SourceID", "")}:{row.get("SourceBook", "")}'
            for row in occurrences_by_match[alias]
            if row.get("SourceID") and row.get("SourceBook")
        })
        display_forms = list(dict.fromkeys(row.get("Word", "") for row in occurrences_by_match[alias] if row.get("Word")))
        definitions = list(dict.fromkeys(row.get("Definition", "") for row in occurrences_by_match[alias] if row.get("Definition")))
        canonical_defs = list(dict.fromkeys(row.get("Definition", "") for row in canonical_occ if row.get("Definition")))
        d = alias_rows[0]
        row = {field: "" for field in bundle_fields}
        row.update({
            "AuditPriority": "05",
            "ActionabilityScore": "95",
            "ReviewLane": "semantic-review",
            "RecommendedBatchSize": "30",
            "BlockerClass": "orthographic-identity-audit",
            "MatchKey": alias,
            "DisplayForms": "|".join(display_forms),
            "Definitions": "|".join(definitions),
            "SourceIDs": "|".join(source_ids),
            "SourceBooks": "|".join(source_books),
            "OccurrenceCount": str(len(occurrences_by_match[alias])),
            "CandidateSignals": "orthographic-variant|identity-dedup-audit",
            "CandidateCanonical": canonical,
            "CanonicalRelation": "orthographic-variant",
            "CanonicalExists": "yes",
            "CanonicalAction": canonical_action,
            "CanonicalStatus": canonical_status,
            "CanonicalTargetSense": canonical_sense,
            "CanonicalDefinitions": "|".join(canonical_defs),
            "CanonicalOccurrenceCount": str(len(canonical_occ)),
            "PolicyRecommendedAction": "review-orthographic-reuse",
            "CurrentAction": alias_action,
            "CurrentStatus": alias_status,
            "CurrentConfidence": d.get("Confidence", ""),
            "CurrentDecisionBasis": d.get("DecisionBasis", ""),
            "CurrentRationale": d.get("Rationale", ""),
            "OccurrenceEvidenceJSON": json.dumps(evidence, ensure_ascii=False, separators=(",", ":")),
        })
        bundle.append(row)
        existing_bundle_keys.add(alias)
        injected.append(alias)

    bundle.sort(key=lambda row: (
        1 if row.get("ReviewLane") == "deferred-high-ambiguity" else 0,
        -int(row.get("ActionabilityScore", "0") or 0),
        int(row.get("AuditPriority", "99") or 99),
        row.get("MatchKey", ""),
    ))
    with BUNDLE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=bundle_fields)
        writer.writeheader()
        writer.writerows(bundle)

    print(f"orthographic identity audits injected = {len(injected)}")
    print("orthographic audit MatchKeys = " + ("|".join(injected) if injected else "none"))
    print("orthographic audits auto-apply = no")
    return len(injected)


def occurrence_keys(raw: str, match_key: str) -> str:
    try:
        evidence = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid OccurrenceEvidenceJSON for {match_key}: {exc}") from exc
    keys = [item.get("SourceOccurrenceKey", "") for item in evidence]
    if not keys or not all(keys) or len(keys) != len(set(keys)):
        raise SystemExit(f"Invalid proposal evidence set for {match_key}")
    return json.dumps(keys, ensure_ascii=False, separators=(",", ":"))


def distinct_pos_count(definitions: str) -> int:
    return len({match.group(0).strip().casefold() for match in POS_RE.finditer(definitions or "")})


def safe_candidate(item: dict[str, str]) -> tuple[bool, str]:
    key = item.get("MatchKey", "").casefold()
    canonical = item.get("CandidateCanonical", "").casefold()
    relation = item.get("CanonicalRelation", "")
    text = " ".join([
        item.get("Definitions", ""),
        item.get("CurrentRationale", ""),
        item.get("CurrentDecisionBasis", ""),
    ]).casefold()

    if key in PEDAGOGICAL_FORM_EXCEPTIONS:
        return False, "pedagogical-exception"
    if relation not in SAFE_RELATIONS:
        return False, "unsafe-or-nondirectional-relation"
    if canonical in GRAMMAR_CANONICALS_REQUIRING_MANUAL_REVIEW:
        return False, "grammar-canonical-needs-manual-review"
    if distinct_pos_count(item.get("Definitions", "")) > 1:
        return False, "multi-pos-form-can-be-lexicalized"
    if any(marker in text for marker in UNSAFE_TEXT_MARKERS):
        return False, "known-lexical-or-semantic-boundary"
    return True, ""


def main() -> None:
    inject_orthographic_identity_audits()
    bundle = read_csv(BUNDLE)
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    skipped = Counter()
    executable_seen = 0

    for item in bundle:
        key = item.get("MatchKey", "")
        if not key or key in seen:
            raise SystemExit(f"Duplicate/empty MatchKey in Review Bundle: {key}")
        seen.add(key)

        if item.get("ReviewLane") != "policy-executable":
            continue
        executable_seen += 1
        if item.get("PolicyRecommendedAction") != "reuse-identity":
            raise SystemExit(f"Executable policy row is not reuse-identity: {key}")
        if item.get("BlockerClass") != "form-policy":
            raise SystemExit(f"Executable policy row is not form-policy: {key}")

        safe, reason = safe_candidate(item)
        if not safe:
            skipped[reason] += 1
            continue

        canonical = item.get("CandidateCanonical", "")
        relation = item.get("CanonicalRelation", "")
        if not canonical:
            raise SystemExit(f"Executable policy proposal lacks canonical: {key}")
        if item.get("CanonicalAction") != "keep-identity" or item.get("CanonicalStatus") != "reviewed":
            raise SystemExit(f"Executable proposal canonical is not reviewed keep-identity: {key} -> {canonical}")
        if not item.get("CanonicalTargetSense", "").strip():
            raise SystemExit(f"Executable proposal canonical lacks TargetSense: {key} -> {canonical}")

        score = int(item.get("ActionabilityScore", "0") or 0)
        if score < 60:
            raise SystemExit(f"Safe executable proposal has unexpectedly low actionability: {key} = {score}")

        occ_keys = occurrence_keys(item.get("OccurrenceEvidenceJSON", ""), key)
        rationale = (
            f"Frozen Stage-A form policy: directional {relation} evidence links {key} to reviewed "
            f"canonical {canonical} ({item.get('CanonicalTargetSense', '')}). Current occurrence evidence "
            "must still be confirmed as the same lexical sense before applying this proposal."
        )
        rows.append({
            "ProposalKey": f"proposal:{key}",
            "MatchKey": key,
            "OccurrenceKeys": occ_keys,
            "SuggestedAction": "reuse-identity",
            "SuggestedCanonicalMatchKey": canonical,
            "CanonicalRelation": relation,
            "ObjectType": "vocabulary",
            "TargetSense": "",
            "Status": "reviewed",
            "Confidence": "high",
            "DecisionBasis": "frozen-form-policy-directional-proposal",
            "Rationale": rationale,
            "ActionabilityScore": str(score),
            "ReviewLane": item.get("ReviewLane", ""),
            "ReviewMode": "confirm-or-reject",
            "AutoApply": "no",
        })

    rows.sort(key=lambda row: (-int(row["ActionabilityScore"]), row["MatchKey"]))
    write_csv(OUT, rows)

    if any(row["AutoApply"] != "no" for row in rows):
        raise SystemExit("Policy proposal engine must never auto-apply decisions")
    if any(row["CanonicalRelation"] not in SAFE_RELATIONS for row in rows):
        raise SystemExit("Unsafe canonical relation leaked into policy proposals")

    print(f"policy executable rows inspected = {executable_seen}")
    print(f"policy proposals = {len(rows)}")
    print("policy proposal action reuse-identity = " + str(len(rows)))
    for reason in sorted(skipped):
        print(f"policy proposal skipped {reason} = {skipped[reason]}")
    print("policy proposal confidence high = " + str(len(rows)))
    print("policy proposal canonical reviewed keep = yes")
    print("policy proposal directional relation = yes")
    print("policy proposal explicit OccurrenceKeys = yes")
    print("policy proposal review mode = confirm-or-reject")
    print("policy proposal auto-apply = no")
    print("policy proposal decision truth = derived-only")


if __name__ == "__main__":
    main()
