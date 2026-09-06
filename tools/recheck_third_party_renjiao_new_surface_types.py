#!/usr/bin/env python3
"""Independent Completion Recheck for Renjiao start1 new-surface type audit.

This check is deliberately separate from the audit generator. It verifies
403-row closure, routing boundaries, representative high-risk examples, and the
Stage-A no-merge/no-ThirdPartyID boundary.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
RENJIAO = BASE / "source_reference" / "renjiao_start1_staging"
STAGING = BASE / "third_party_vocabulary" / "staging"
SOURCE = RENJIAO / "new_surface_candidates.csv"
AUDIT = STAGING / "renjiao_new_surface_type_audit.csv"
RISK = STAGING / "renjiao_new_surface_semantic_risk_queue.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing type-audit input: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    source = read_csv(SOURCE)
    audit = read_csv(AUDIT)
    risk = read_csv(RISK)

    assert len(source) == 403, len(source)
    assert len(audit) == 403, len(audit)

    source_keys = {r["MatchKey"] for r in source}
    audit_keys = {r["MatchKey"] for r in audit}
    assert len(source_keys) == 403, len(source_keys)
    assert source_keys == audit_keys

    by_key = {r["MatchKey"]: r for r in audit}
    assert len(by_key) == 403

    allowed_types = {
        "ordinal-format-alias-review",
        "single-token-form-review",
        "single-token-lexical-review",
        "expression-or-chunk-review",
        "multiword-routing-review",
        "multiword-lexical-review",
    }
    allowed_routes = {
        "identity-alias-review",
        "identity-form-review",
        "vocabulary-identity-review",
        "expression-routing-review",
        "vocabulary-vs-expression-review",
    }

    for row in audit:
        assert row["CandidateType"] in allowed_types, (row["MatchKey"], row["CandidateType"])
        assert row["CandidateRoute"] in allowed_routes, (row["MatchKey"], row["CandidateRoute"])
        assert row["ReviewStatus"] == "pending", row["MatchKey"]
        assert row["KloseMergeAuthorized"] == "no", row["MatchKey"]
        assert int(row["TokenCount"]) >= 1, row["MatchKey"]
        assert row["Contexts"].strip(), row["MatchKey"]

    # Known ordinal/form aliases must not be minted as new lexical identities.
    for key, related in {
        "5th": "fifth",
        "10th": "tenth",
        "12th": "twelfth",
        "15th": "fifteenth",
        "25th": "twenty-fifth",
    }.items():
        row = by_key[key]
        assert row["CandidateType"] == "ordinal-format-alias-review", key
        assert row["CandidateRoute"] == "identity-alias-review", key
        assert row["RelatedMatchKeys"] == related, (key, row["RelatedMatchKeys"])

    # Representative multiword cases must be routed away from automatic
    # single-token Vocabulary identity creation.
    for key in {"a lot of", "by bike", "across from"}:
        assert by_key[key]["CandidateType"] == "multiword-routing-review", key
        assert by_key[key]["CandidateRoute"] == "vocabulary-vs-expression-review", key

    for key in {"ate ice-cream", "bought some gifts", "cleaned the window"}:
        assert by_key[key]["CandidateType"] == "expression-or-chunk-review", key
        assert by_key[key]["CandidateRoute"] == "expression-routing-review", key

    # Legitimate multiword lexical/proper-name candidates remain reviewable as
    # Vocabulary rather than being silently routed to Expressions.
    for key in {"art gallery", "big ben", "bus driver"}:
        assert by_key[key]["CandidateType"] == "multiword-lexical-review", key
        assert by_key[key]["CandidateRoute"] == "vocabulary-vs-expression-review", key

    for key in {"active", "airport", "bank"}:
        assert by_key[key]["CandidateType"] == "single-token-lexical-review", key
        assert by_key[key]["CandidateRoute"] == "vocabulary-identity-review", key

    # Risk queue must be an exact filtered subset of the audit output.
    expected_risk_keys = {
        r["MatchKey"]
        for r in audit
        if r["RiskSignals"] != "none-detected"
        or r["CandidateType"] != "single-token-lexical-review"
    }
    risk_keys = {r["MatchKey"] for r in risk}
    assert len(risk_keys) == len(risk), "Duplicate MatchKey in new-surface risk queue"
    assert risk_keys == expected_risk_keys

    # No stable third-party identity registry may appear during this stage.
    stable_registry = BASE / "third_party_vocabulary" / "master" / "identity_registry.csv"
    assert not stable_registry.exists(), "Stable ThirdPartyID registry exists before new-surface resolution"

    type_counts: dict[str, int] = {}
    for row in audit:
        type_counts[row["CandidateType"]] = type_counts.get(row["CandidateType"], 0) + 1

    print("Renjiao New-surface Type Completion Recheck = pass")
    print(f"audit rows = {len(audit)}")
    for key in sorted(type_counts):
        print(f"type {key} = {type_counts[key]}")
    print(f"risk/routing queue = {len(risk)}")
    print("403 surfaces are not assumed to equal 403 Vocabulary identities = yes")
    print("ThirdPartyID minted = no")
    print("Klose merge authorized = no")


if __name__ == "__main__":
    main()
