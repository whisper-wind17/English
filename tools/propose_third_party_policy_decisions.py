#!/usr/bin/env python3
"""Generate deterministic Stage-A policy proposals without applying decisions.

This is a derived review aid. It NEVER writes `identity_decisions.csv` or
`decision_updates.csv`. Proposals are emitted only when the frozen form policy and
current canonical evidence make a reuse candidate mechanically checkable. Model/human
review must still confirm or reject each proposal before any durable content decision.
"""
from __future__ import annotations

import csv
import json
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


def main() -> None:
    bundle = read_csv(BUNDLE)
    rows: list[dict[str, str]] = []
    seen: set[str] = set()

    for item in bundle:
        key = item.get("MatchKey", "")
        if not key or key in seen:
            raise SystemExit(f"Duplicate/empty MatchKey in Review Bundle: {key}")
        seen.add(key)

        if item.get("ReviewLane") != "policy-executable":
            continue
        if item.get("PolicyRecommendedAction") != "reuse-identity":
            continue
        if item.get("BlockerClass") != "form-policy":
            raise SystemExit(f"Executable policy proposal is not form-policy: {key}")
        if key.casefold() in PEDAGOGICAL_FORM_EXCEPTIONS:
            raise SystemExit(f"Pedagogical exception leaked into executable proposals: {key}")

        canonical = item.get("CandidateCanonical", "")
        if not canonical:
            raise SystemExit(f"Executable policy proposal lacks canonical: {key}")
        if item.get("CanonicalAction") != "keep-identity" or item.get("CanonicalStatus") != "reviewed":
            raise SystemExit(f"Executable proposal canonical is not reviewed keep-identity: {key} -> {canonical}")
        if not item.get("CanonicalTargetSense", "").strip():
            raise SystemExit(f"Executable proposal canonical lacks TargetSense: {key} -> {canonical}")

        score = int(item.get("ActionabilityScore", "0") or 0)
        if score < 60:
            raise SystemExit(f"Executable proposal has unexpectedly low actionability: {key} = {score}")

        occ_keys = occurrence_keys(item.get("OccurrenceEvidenceJSON", ""), key)
        rationale = (
            f"Frozen Stage-A form policy: {key} is treated as a form realization candidate of reviewed "
            f"canonical {canonical} ({item.get('CanonicalTargetSense', '')}). Current occurrence evidence "
            "must still be confirmed as the same lexical sense before applying this proposal."
        )
        rows.append({
            "ProposalKey": f"proposal:{key}",
            "MatchKey": key,
            "OccurrenceKeys": occ_keys,
            "SuggestedAction": "reuse-identity",
            "SuggestedCanonicalMatchKey": canonical,
            "ObjectType": "vocabulary",
            "TargetSense": "",
            "Status": "reviewed",
            "Confidence": "high",
            "DecisionBasis": "frozen-form-policy-proposal",
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

    print(f"policy proposals = {len(rows)}")
    print("policy proposal action reuse-identity = " + str(len(rows)))
    print("policy proposal canonical reviewed keep = yes")
    print("policy proposal explicit OccurrenceKeys = yes")
    print("policy proposal review mode = confirm-or-reject")
    print("policy proposal auto-apply = no")
    print("policy proposal decision truth = derived-only")


if __name__ == "__main__":
    main()
