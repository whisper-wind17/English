#!/usr/bin/env python3
"""Independent Completion Recheck for Beijing + Renjiao start1 Stage A.

This is intentionally separate from the generation scripts. It checks count
closure, cross-source resolution coverage, known semantic edge cases,
morphology decisions, and the current no-merge boundary.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
BEIJING = BASE / "source_reference" / "beijing_start1_staging" / "occurrences.csv"
RENJIAO = BASE / "source_reference" / "renjiao_start1_staging" / "occurrences.csv"
STAGING = BASE / "third_party_vocabulary" / "staging"
COMBINED = STAGING / "occurrences.csv"
CONTEXT = STAGING / "cross_source_context_review.csv"
RESOLUTION = STAGING / "cross_source_identity_resolution.csv"
MORPH = BASE / "third_party_vocabulary" / "review" / "renjiao_start1_morphology_resolution.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing recheck input: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def unique_keys(rows: list[dict[str, str]], field: str) -> set[str]:
    return {r[field] for r in rows}


def main() -> None:
    bj = read_csv(BEIJING)
    rj = read_csv(RENJIAO)
    combined = read_csv(COMBINED)
    context = read_csv(CONTEXT)
    resolution = read_csv(RESOLUTION)
    morph = read_csv(MORPH)

    # Count / set closure for the current two-adapter baseline.
    assert len(bj) == 808, len(bj)
    assert len(rj) == 908, len(rj)
    assert len(combined) == 1716, len(combined)
    assert len(unique_keys(combined, "SourceOccurrenceKey")) == 1716
    assert len(unique_keys(combined, "MatchKey")) == 1144
    assert len(context) == 392, len(context)
    assert len(resolution) == 392, len(resolution)
    assert len(unique_keys(context, "MatchKey")) == 392
    assert unique_keys(context, "MatchKey") == unique_keys(resolution, "MatchKey")

    by_key = {r["MatchKey"]: r for r in resolution}

    expected_nonmerge = {
        "square": "do-not-merge",
        "left": "do-not-merge",
        "cook": "do-not-merge",
        "may": "partial-overlap-split-required",
        "like": "partial-overlap-split-required",
        "cold": "partial-overlap-split-required",
        "dress": "partial-overlap-split-required",
        "study": "partial-overlap-split-required",
        "chicken": "partial-overlap-split-required",
        "duck": "partial-overlap-split-required",
    }
    for key, decision in expected_nonmerge.items():
        assert by_key[key]["ProposedDecision"] == decision, (key, by_key[key]["ProposedDecision"])
        assert by_key[key]["ResolutionStatus"] == "model-reviewed"

    expected_held = {"fan", "kind", "light", "speak", "sound", "star", "plant", "live", "tongue", "fish"}
    for key in expected_held:
        assert by_key[key]["ProposedDecision"].startswith("held-"), (key, by_key[key]["ProposedDecision"])
        assert by_key[key]["ResolutionStatus"] == "model-reviewed"

    assert by_key["can"]["ProposedDecision"] == "reuse-learning-unit"
    assert by_key["can"]["ResolutionStatus"] == "model-reviewed"

    # Strict-rule reuse is allowed only for rows that had no risk signal.
    for row in resolution:
        if row["ResolutionStatus"] == "rule-reviewed":
            assert row["RiskSignals"] == "none-detected", row["MatchKey"]
            assert row["ProposedDecision"] == "reuse-learning-unit", row["MatchKey"]
        assert row["KloseMergeAuthorized"] == "no", row["MatchKey"]

    # Morphology decisions are separate and must preserve the held irregular case.
    assert len(morph) == 6, len(morph)
    morph_map = {r["RenjiaoMatchKey"]: r for r in morph}
    expected_morph = {
        "feet": "held-irregular-form-policy",
        "noodles": "reuse-learning-unit",
        "shoes": "reuse-learning-unit",
        "socks": "reuse-learning-unit",
        "thanks": "do-not-merge",
        "vegetables": "reuse-learning-unit",
    }
    assert set(morph_map) == set(expected_morph)
    for key, decision in expected_morph.items():
        assert morph_map[key]["ProposedDecision"] == decision, (key, morph_map[key]["ProposedDecision"])
        assert morph_map[key]["KloseMergeAuthorized"] == "no", key

    # The stable third-party registry must not exist yet in this phase.
    stable_registry = BASE / "third_party_vocabulary" / "master" / "identity_registry.csv"
    assert not stable_registry.exists(), "Stable ThirdPartyID registry exists before Identity Resolution is ready"

    pending = sum(r["ResolutionStatus"] == "pending" for r in resolution)
    rule_reviewed = sum(r["ResolutionStatus"] == "rule-reviewed" for r in resolution)
    model_reviewed = sum(r["ResolutionStatus"] == "model-reviewed" for r in resolution)

    print("Completion Recheck = pass")
    print(f"Beijing occurrences = {len(bj)}")
    print(f"Renjiao occurrences = {len(rj)}")
    print(f"Combined occurrences = {len(combined)}")
    print(f"Combined MatchKeys = {len(unique_keys(combined, 'MatchKey'))}")
    print(f"Cross-source resolution rows = {len(resolution)}")
    print(f"rule-reviewed = {rule_reviewed}")
    print(f"model-reviewed = {model_reviewed}")
    print(f"pending = {pending}")
    print("Known semantic blockers preserved = yes")
    print("Klose merge authorized = no")


if __name__ == "__main__":
    main()
