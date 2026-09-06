#!/usr/bin/env python3
"""Consolidate Beijing staging candidates/reviews into one occurrence-level map.

The output is a merge planning artifact only. It never writes Klose master,
learner, release, publish, or Anki state, and every output row remains
MergeAuthorized=no.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "anki" / "klose" / "source_reference" / "beijing_start1_staging"
INPUT = STAGING / "identity_candidates.csv"
HIGH = STAGING / "identity_resolution_review.csv"
VARIANT = STAGING / "source_variant_resolution_review.csv"
SEMANTIC = STAGING / "semantic_resolution_review.csv"
OUT = STAGING / "proposed_occurrence_identity_map.csv"

FIELDS = [
    "SourceOccurrenceKey", "SourceBook", "Grade", "Semester", "SourceRow",
    "Word", "MatchKey", "Definition",
    "BaselineCandidateClass", "BaselineCandidateNoteIDs", "BaselineCandidateSenses",
    "ProposedDecision", "ProposedNoteID", "ProposedTargetSense",
    "ResolutionStatus", "Confidence", "ResolutionBasis", "MergeAuthorized",
]


def read(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    base = read(INPUT)
    high = {r["MatchKey"].casefold(): r for r in read(HIGH)}
    variant = {r["MatchKey"].casefold(): r for r in read(VARIANT)}
    semantic = {r["SourceOccurrenceKey"]: r for r in read(SEMANTIC)}

    rows: list[dict[str, str]] = []
    for b in base:
        proposed_decision = b.get("AutoDecision", "")
        proposed_note = ""
        proposed_sense = ""
        status = "pending-sense-confirmation"
        confidence = ""
        basis = "baseline-candidate-only"

        if b.get("CandidateClass") == "exact-single":
            proposed_decision = "reuse-candidate"
            proposed_note = b.get("CandidateNoteIDs", "")
            proposed_sense = b.get("CandidateSenses", "")
        elif b.get("CandidateClass") == "no-existing-match":
            proposed_decision = "new-identity-candidate"
            status = "pending-new-identity-review"

        # MatchKey-level high-risk review (exact-multiple / format alias /
        # morphology from the primary matcher).
        hr = high.get(b.get("MatchKey", "").casefold())
        if hr:
            proposed_decision = hr.get("ProposedDecision", proposed_decision)
            proposed_note = hr.get("ProposedNoteID", "")
            proposed_sense = ""
            status = hr.get("ReviewStatus", "")
            confidence = hr.get("Confidence", "")
            basis = hr.get("ReviewBasis", "high-risk-review")

        # Inflection review can redirect a baseline new candidate to an
        # existing identity, hold it for form policy, or explicitly prevent a
        # morphology merge.
        vr = variant.get(b.get("MatchKey", "").casefold())
        if vr:
            proposed_decision = vr.get("ProposedDecision", proposed_decision)
            proposed_note = vr.get("ProposedNoteID", "")
            status = vr.get("ReviewStatus", "")
            confidence = vr.get("Confidence", "")
            basis = vr.get("ReviewBasis", "source-variant-review")

        # Occurrence-level semantic decisions must win over all surface-level
        # decisions because one MatchKey can represent different senses in
        # different books/contexts (e.g. May/month vs may/modal).
        sr = semantic.get(b.get("SourceOccurrenceKey", ""))
        if sr:
            proposed_decision = sr.get("ProposedDecision", proposed_decision)
            proposed_note = sr.get("ProposedNoteID", "")
            proposed_sense = sr.get("ProposedTargetSense", "")
            status = sr.get("ReviewStatus", "")
            confidence = sr.get("Confidence", "")
            basis = sr.get("ReviewBasis", "occurrence-semantic-review")

        rows.append({
            "SourceOccurrenceKey": b.get("SourceOccurrenceKey", ""),
            "SourceBook": b.get("SourceBook", ""),
            "Grade": b.get("Grade", ""),
            "Semester": b.get("Semester", ""),
            "SourceRow": b.get("SourceRow", ""),
            "Word": b.get("Word", ""),
            "MatchKey": b.get("MatchKey", ""),
            "Definition": b.get("Definition", ""),
            "BaselineCandidateClass": b.get("CandidateClass", ""),
            "BaselineCandidateNoteIDs": b.get("CandidateNoteIDs", ""),
            "BaselineCandidateSenses": b.get("CandidateSenses", ""),
            "ProposedDecision": proposed_decision,
            "ProposedNoteID": proposed_note,
            "ProposedTargetSense": proposed_sense,
            "ResolutionStatus": status,
            "Confidence": confidence,
            "ResolutionBasis": basis,
            "MergeAuthorized": "no",
        })

    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    if len(rows) != 808:
        raise SystemExit(f"Expected 808 occurrence decisions, got {len(rows)}")
    if any(r["MergeAuthorized"] != "no" for r in rows):
        raise SystemExit("Pre-merge map must never authorize merge")

    print(f"proposed occurrence identity rows = {len(rows)}")
    print("Merge Authorized = no")


if __name__ == "__main__":
    main()
