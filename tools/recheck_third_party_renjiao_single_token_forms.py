#!/usr/bin/env python3
"""Independent Completion Recheck for Renjiao single-token form audit."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
STAGING = BASE / "third_party_vocabulary" / "staging"
ROUTING = STAGING / "renjiao_new_surface_route_resolution.csv"
AUDIT = STAGING / "renjiao_single_token_form_audit.csv"

FORM_PATTERNS = [
    r"([A-Za-z][A-Za-z-]*)的过去式(?:和过去分词)?",
    r"([A-Za-z][A-Za-z-]*)的过去分词",
    r"([A-Za-z][A-Za-z-]*)的ing形式",
    r"([A-Za-z][A-Za-z-]*)的现在分词",
    r"([A-Za-z][A-Za-z-]*)的复数(?:形式)?",
    r"([A-Za-z][A-Za-z-]*)的第三人称单数(?:形式)?",
]

MANUAL_FORM_KEYS = {
    "slept", "swam", "were", "won", "danced", "does",
    "broken", "amazing", "dancing", "reading", "running", "singing", "skateboarding",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing form-audit input: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def has_explicit_form_relation(definition: str) -> bool:
    return any(re.search(p, definition or "", flags=re.I) for p in FORM_PATTERNS)


def main() -> None:
    routing = read_csv(ROUTING)
    audit = read_csv(AUDIT)
    assert len(routing) == 403, len(routing)
    by_key = {r["MatchKey"]: r for r in routing}
    audit_by_key = {r["MatchKey"]: r for r in audit}
    assert len(audit_by_key) == len(audit), "Duplicate form-audit MatchKey"

    lexical_candidates = [
        r for r in routing
        if r["CandidateType"] == "single-token-lexical-review"
        and r["ProposedObjectDecision"] == "new-vocabulary-learning-unit-candidate"
    ]
    expected_signal_keys = {
        r["MatchKey"] for r in lexical_candidates
        if has_explicit_form_relation(r["Definitions"])
    } | (MANUAL_FORM_KEYS & {r["MatchKey"] for r in lexical_candidates})
    assert set(audit_by_key) == expected_signal_keys, (
        sorted(expected_signal_keys - set(audit_by_key)),
        sorted(set(audit_by_key) - expected_signal_keys),
    )

    expected = {
        "danced": ("regular-inflection", "dance", "reuse-base-learning-unit-candidate"),
        "does": ("regular-inflection", "do", "reuse-base-learning-unit-candidate"),
        "slept": ("irregular-inflection", "sleep", "held-irregular-form-policy"),
        "swam": ("irregular-inflection", "swim", "held-irregular-form-policy"),
        "were": ("irregular-inflection", "be", "held-irregular-form-policy"),
        "won": ("irregular-inflection", "win", "held-irregular-form-policy"),
        "broken": ("derived-or-participial-lexical-target", "break", "keep-distinct-learning-unit-candidate"),
        "amazing": ("derived-or-participial-lexical-target", "amaze", "keep-distinct-learning-unit-candidate"),
    }
    for key, (form_class, base, decision) in expected.items():
        row = audit_by_key[key]
        assert row["FormClass"] == form_class, (key, row["FormClass"])
        assert row["BaseMatchKey"] == base, (key, row["BaseMatchKey"])
        assert row["ProposedFormDecision"] == decision, (key, row["ProposedFormDecision"])
        assert row["KloseMergeAuthorized"] == "no", key

    for key in {"dancing", "reading", "running", "singing", "skateboarding"}:
        row = audit_by_key[key]
        assert row["FormClass"] == "activity-gerund-or-noun", key
        assert row["ProposedFormDecision"] == "held-derived-form-identity-policy", key
        assert row["DecisionStatus"] == "model-reviewed", key

    # Any remaining explicit form relation not covered by the reviewed map must
    # stay pending rather than silently minting a stable identity.
    for row in audit:
        assert row["KloseMergeAuthorized"] == "no", row["MatchKey"]
        if row["FormClass"] == "explicit-form-relation-unreviewed":
            assert row["ProposedFormDecision"] == "pending-form-review", row["MatchKey"]
            assert row["DecisionStatus"] == "pending", row["MatchKey"]

    stable_registry = BASE / "third_party_vocabulary" / "master" / "identity_registry.csv"
    assert not stable_registry.exists(), "Stable ThirdPartyID registry exists before form review closure"

    pending = [r["MatchKey"] for r in audit if r["DecisionStatus"] == "pending"]
    print("Renjiao Single-token Form Completion Recheck = pass")
    print(f"form audit rows = {len(audit)}")
    print("known regular/irregular/derived cases protected = yes")
    print("pending explicit form keys = " + ("|".join(sorted(pending)) if pending else "none"))
    print("ThirdPartyID minted = no")
    print("Klose merge authorized = no")


if __name__ == "__main__":
    main()
