#!/usr/bin/env python3
"""Independent Completion Recheck for Renjiao new-surface object routing."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
STAGING = BASE / "third_party_vocabulary" / "staging"
AUDIT = STAGING / "renjiao_new_surface_type_audit.csv"
RESOLUTION = STAGING / "renjiao_new_surface_route_resolution.csv"
QUEUE = STAGING / "renjiao_new_surface_identity_review_queue.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing routing recheck input: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    audit = read_csv(AUDIT)
    resolution = read_csv(RESOLUTION)
    queue = read_csv(QUEUE)

    assert len(audit) == 403, len(audit)
    assert len(resolution) == 403, len(resolution)
    audit_keys = {r["MatchKey"] for r in audit}
    resolution_keys = {r["MatchKey"] for r in resolution}
    assert len(audit_keys) == 403
    assert audit_keys == resolution_keys

    by_key = {r["MatchKey"]: r for r in resolution}
    assert len(by_key) == 403

    for row in resolution:
        assert row["KloseMergeAuthorized"] == "no", row["MatchKey"]
        assert row["ResolutionStatus"] in {"rule-reviewed", "model-reviewed", "pending"}, row["MatchKey"]
        assert row["ProposedObjectDecision"], row["MatchKey"]

    for key, target in {
        "5th": "fifth",
        "10th": "tenth",
        "12th": "twelfth",
        "15th": "fifteenth",
        "25th": "twenty-fifth",
    }.items():
        row = by_key[key]
        assert row["ProposedObjectDecision"] == "canonical-form-alias-candidate", key
        assert row["TargetReference"] == target, key
        assert row["ResolutionStatus"] == "rule-reviewed", key

    assert by_key["can't"]["ProposedObjectDecision"] == "held-identity-form-policy"
    assert by_key["let's"]["ProposedObjectDecision"] == "route-expression-candidate"
    assert by_key["be careful!"]["ProposedObjectDecision"] == "route-expression-candidate"

    for key in {"ate ice-cream", "bought some gifts", "cleaned the window"}:
        assert by_key[key]["ProposedObjectDecision"] == "route-source-chunk-no-vocabulary-identity", key

    for key in {"advice", "africa", "airport", "artist"}:
        assert by_key[key]["ProposedObjectDecision"] == "new-vocabulary-learning-unit-candidate", key
        assert by_key[key]["ResolutionStatus"] == "rule-reviewed", key

    for key in {"active", "age", "bank", "bark"}:
        assert by_key[key]["ProposedObjectDecision"] == "pending-vocabulary-sense-review", key
        assert by_key[key]["ResolutionStatus"] == "pending", key

    # These are lexical compounds even though they begin with "shopping".
    # They must remain eligible for Vocabulary phrase identity review.
    for key in {"shopping centre", "shopping list", "shopping mall"}:
        assert by_key[key]["ProposedObjectDecision"] == "pending-vocabulary-phrase-sense-review", key
        assert by_key[key]["ResolutionStatus"] == "pending", key

    for key in {"art gallery", "big ben", "living room"}:
        assert by_key[key]["ProposedObjectDecision"] == "pending-vocabulary-phrase-sense-review", key
        assert by_key[key]["ResolutionStatus"] == "pending", key

    for key in {"a lot of", "across from", "be good at", "look forward to"}:
        assert by_key[key]["ProposedObjectDecision"] == "pending-vocabulary-vs-expression-review", key
        assert by_key[key]["ResolutionStatus"] == "pending", key

    expected_queue_keys = {
        r["MatchKey"]
        for r in resolution
        if r["ResolutionStatus"] == "pending" or r["ProposedObjectDecision"].startswith("held-")
    }
    queue_keys = {r["MatchKey"] for r in queue}
    assert len(queue_keys) == len(queue), "Duplicate MatchKey in identity/object review queue"
    assert queue_keys == expected_queue_keys

    lexical_safe = [
        r for r in audit
        if r["CandidateType"] == "single-token-lexical-review"
        and r["RiskSignals"] == "none-detected"
    ]
    assert len(lexical_safe) == 99, len(lexical_safe)
    for row in lexical_safe:
        resolved = by_key[row["MatchKey"]]
        assert resolved["ProposedObjectDecision"] == "new-vocabulary-learning-unit-candidate", row["MatchKey"]

    stable_registry = BASE / "third_party_vocabulary" / "master" / "identity_registry.csv"
    assert not stable_registry.exists(), "Stable ThirdPartyID registry exists before routing review closure"

    statuses = Counter(r["ResolutionStatus"] for r in resolution)
    decisions = Counter(r["ProposedObjectDecision"] for r in resolution)
    print("Renjiao New-surface Routing Completion Recheck = pass")
    print(f"routing rows = {len(resolution)}")
    for key in sorted(statuses):
        print(f"status {key} = {statuses[key]}")
    for key in sorted(decisions):
        print(f"decision {key} = {decisions[key]}")
    print(f"identity/object review queue = {len(queue)}")
    print("Lexical shopping compounds preserved for Vocabulary review = yes")
    print("No source occurrence deleted = yes")
    print("ThirdPartyID minted = no")
    print("Klose merge authorized = no")


if __name__ == "__main__":
    main()
