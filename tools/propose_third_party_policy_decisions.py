#!/usr/bin/env python3
"""Generate conservative deterministic Stage-A policy proposals without applying decisions.

This is a derived review aid. It NEVER writes `identity_decisions.csv` or
`decision_updates.csv`. Proposals are emitted only when the frozen form policy,
directional form relation and current canonical evidence make a reuse candidate
mechanically checkable. Model/human review must still confirm the occurrence is the
same lexical sense before any durable content decision.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
BUNDLE = TP / "audit" / "review_bundle.csv"
OUT = TP / "audit" / "decision_proposals.csv"

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
