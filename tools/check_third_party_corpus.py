#!/usr/bin/env python3
"""Independent Completion Recheck for the simplified third-party corpus Stage A."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
OUT = TP / "staging"
DECISIONS = TP / "review" / "identity_decisions.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def main() -> None:
    occ = read_csv(OUT / "occurrences.csv")
    surfaces = read_csv(OUT / "surface_candidates.csv")
    review = read_csv(OUT / "review_queue.csv")
    preview = read_csv(OUT / "unified_vocabulary_preview.csv")
    decisions = read_csv(DECISIONS)

    require(len(occ) == 1716, f"Expected 1716 source occurrences, found {len(occ)}")
    require(len({r['SourceOccurrenceKey'] for r in occ}) == len(occ), "SourceOccurrenceKey is not unique")
    require(len(surfaces) == 1144, f"Expected 1144 normalized surfaces, found {len(surfaces)}")
    require(len({r['MatchKey'] for r in surfaces}) == len(surfaces), "surface MatchKey is not unique")

    # Current migration should explicitly cover every existing surface. Future
    # source adapters may create new pending surfaces, but reviewed decisions may
    # never reference missing surfaces.
    surface_keys = {r["MatchKey"] for r in surfaces}
    decision_keys = [r["DecisionKey"] for r in decisions]
    require(len(decision_keys) == len(set(decision_keys)), "DecisionKey is not unique")
    require(all(r["MatchKey"] in surface_keys for r in decisions), "Decision references a missing surface")
    require({r["MatchKey"] for r in decisions} == surface_keys,
            "Initial simplified migration must cover all 1144 current surfaces")

    actions = Counter(r["Action"] for r in decisions)
    require(not actions.get("", 0), "Empty Action exists in identity_decisions")
    require(all(r.get("Status") in {"reviewed", "held", "pending"} for r in decisions),
            "Invalid decision Status")
    for row in decisions:
        if row["Action"] == "reuse-identity":
            require(bool(row.get("CanonicalMatchKey")), f"reuse-identity lacks CanonicalMatchKey: {row['DecisionKey']}")
        if row["Action"] == "route-expression":
            require(row.get("ObjectType") == "expression", f"Expression routing object mismatch: {row['DecisionKey']}")
        if row["Action"] == "source-only":
            require(row.get("ObjectType") == "source-only", f"Source-only object mismatch: {row['DecisionKey']}")

    # Review queue must be a pure derived view of unresolved/blocking surface state.
    expected_review = {
        r["MatchKey"] for r in surfaces
        if r.get("DecisionAction") in {"pending", "held", "split-required"}
        or r.get("DecisionStatus") in {"pending", "held"}
    }
    actual_review = {r["MatchKey"] for r in review}
    require(actual_review == expected_review,
            f"Review queue drift: expected={len(expected_review)} actual={len(actual_review)}")

    by_key = {r["MatchKey"]: r for r in decisions}

    # Known semantic collisions must remain blockers/splits after simplification.
    for key in ("may", "like", "square", "left", "cook", "cold", "study"):
        require(key in by_key, f"Missing known semantic-risk decision: {key}")
        require(by_key[key]["Action"] in {"split-required", "held"},
                f"Known semantic collision was flattened by simplification: {key} -> {by_key[key]['Action']}")

    # Known form cases verify that simplification preserves content decisions,
    # rather than merely preserving row counts.
    require(by_key["danced"]["Action"] == "reuse-identity" and by_key["danced"]["CanonicalMatchKey"] == "dance",
            "danced must canonicalize to dance")
    require(by_key["cartoons"]["Action"] == "reuse-identity" and by_key["cartoons"]["CanonicalMatchKey"] == "cartoon",
            "cartoons must canonicalize to cartoon")
    require(by_key["gloves"]["Action"] == "reuse-identity" and by_key["gloves"]["CanonicalMatchKey"] == "glove",
            "gloves must canonicalize to glove")
    require(by_key["scissors"]["Action"] == "keep-identity",
            "scissors must remain a lexicalized learning-unit candidate")
    require(by_key["crossroads"]["Action"] == "keep-identity",
            "crossroads must remain a lexicalized learning-unit candidate")
    for key in ("slept", "swam", "were", "won"):
        require(by_key[key]["Action"] == "held", f"Irregular form blocker lost: {key}")

    # Preview must contain only reviewed Vocabulary identity candidates.
    preview_keys = {r["CanonicalMatchKey"] for r in preview}
    require(len(preview_keys) == len(preview), "Unified preview canonical identity key is not unique")
    require(not (preview_keys & {"may", "like", "square", "left", "cook", "cold", "study"}),
            "Known unresolved semantic collision leaked into unified preview")

    source_counts = Counter(r["SourceID"] for r in occ)
    require(source_counts["beijing_start1"] == 808, "Beijing occurrence count drift")
    require(source_counts["renjiao_start1"] == 908, "Renjiao occurrence count drift")

    print("Third-party Simplified Completion Recheck = pass")
    print(f"source occurrences = {len(occ)}")
    print(f"normalized surfaces = {len(surfaces)}")
    print(f"durable decisions = {len(decisions)}")
    print(f"review/blocker surfaces = {len(review)}")
    print(f"unified vocabulary preview = {len(preview)}")
    for action in sorted(actions):
        print(f"decision {action} = {actions[action]}")
    print("Known semantic blockers preserved = yes")
    print("Known morphology decisions preserved = yes")
    print("Legacy multi-pass pipeline not required for active build = yes")
    print("Stable ThirdPartyID minted = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
