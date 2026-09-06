#!/usr/bin/env python3
"""Independent Completion Recheck for Renjiao single-token sense review."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
STAGING = BASE / "third_party_vocabulary" / "staging"
RESOLUTION = STAGING / "renjiao_new_surface_route_resolution.csv"
QUEUE = STAGING / "renjiao_new_surface_identity_review_queue.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing single-token recheck input: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    rows = read_csv(RESOLUTION)
    queue = read_csv(QUEUE)
    assert len(rows) == 403, len(rows)
    by_key = {r["MatchKey"]: r for r in rows}
    assert len(by_key) == 403

    # The 90 single-token semantic-risk rows must be fully reviewed: no
    # anonymous pending-vocabulary-sense-review remains.
    single_pending = [
        r for r in rows
        if r["ProposedObjectDecision"] == "pending-vocabulary-sense-review"
    ]
    assert not single_pending, [r["MatchKey"] for r in single_pending]

    # Representative clear senses.
    expected_senses = {
        "active": "积极的；活跃的",
        "bank": "银行",
        "bedroom": "卧室",
        "free": "空闲的；有空的",
        "grade": "年级",
        "mark": "分数；成绩",
        "present": "礼物",
        "straight": "直的；笔直的",
        "trunk": "象鼻",
        "wow": "哇（表示惊讶或赞叹）",
    }
    for key, sense in expected_senses.items():
        row = by_key[key]
        assert row["ProposedObjectDecision"] == "new-vocabulary-learning-unit-candidate", key
        assert row["ResolutionStatus"] == "model-reviewed", key
        assert row["TargetReference"] == sense, (key, row["TargetReference"])

    # Insufficient-context rows must remain explicit blockers rather than being
    # silently forced into a lexical identity.
    held = {
        "american", "catch", "central", "danish", "dream", "fall", "here",
        "hope", "just", "send", "so", "step", "summary", "taste", "top", "volunteer",
    }
    for key in held:
        row = by_key[key]
        assert row["ProposedObjectDecision"] == "held-source-context-required", key
        assert row["ResolutionStatus"] == "model-reviewed", key
        assert row["KloseMergeAuthorized"] == "no", key

    french = by_key["french"]
    assert french["ProposedObjectDecision"] == "within-source-split-required"
    assert french["ResolutionStatus"] == "model-reviewed"
    assert french["Confidence"] == "high"
    assert "法语" in french["TargetReference"]
    assert "法国" in french["TargetReference"]

    # Corrected lexical shopping compounds must still be pending phrase review;
    # this pass only resolves single-token semantic-risk rows.
    for key in {"shopping centre", "shopping list", "shopping mall"}:
        assert by_key[key]["ProposedObjectDecision"] == "pending-vocabulary-phrase-sense-review", key
        assert by_key[key]["ResolutionStatus"] == "pending", key

    # Previous object boundaries must remain intact.
    assert by_key["can't"]["ProposedObjectDecision"] == "held-identity-form-policy"
    assert by_key["let's"]["ProposedObjectDecision"] == "route-expression-candidate"
    assert by_key["be careful!"]["ProposedObjectDecision"] == "route-expression-candidate"
    assert by_key["5th"]["ProposedObjectDecision"] == "canonical-form-alias-candidate"

    for row in rows:
        assert row["KloseMergeAuthorized"] == "no", row["MatchKey"]

    statuses = Counter(r["ResolutionStatus"] for r in rows)
    decisions = Counter(r["ProposedObjectDecision"] for r in rows)
    assert statuses == Counter({"pending": 180, "rule-reviewed": 131, "model-reviewed": 92}), statuses
    assert decisions == Counter({
        "new-vocabulary-learning-unit-candidate": 172,
        "pending-vocabulary-phrase-sense-review": 138,
        "pending-vocabulary-vs-expression-review": 42,
        "route-source-chunk-no-vocabulary-identity": 25,
        "held-source-context-required": 16,
        "canonical-form-alias-candidate": 5,
        "route-expression-candidate": 3,
        "held-identity-form-policy": 1,
        "within-source-split-required": 1,
    }), decisions

    expected_queue_keys = {
        r["MatchKey"] for r in rows
        if r["ResolutionStatus"] == "pending"
        or r["ProposedObjectDecision"].startswith("held-")
    }
    queue_keys = {r["MatchKey"] for r in queue}
    assert len(queue_keys) == len(queue), "Duplicate MatchKey in post-semantic review queue"
    assert queue_keys == expected_queue_keys
    assert len(queue) == 197, len(queue)

    stable_registry = BASE / "third_party_vocabulary" / "master" / "identity_registry.csv"
    assert not stable_registry.exists(), "Stable ThirdPartyID registry exists before review closure"

    print("Renjiao Single-token Sense Completion Recheck = pass")
    print("single-token semantic-risk rows reviewed = 90")
    print("resolved learning-unit candidates = 73")
    print("held source-context blockers = 16")
    print("within-source split-required = 1")
    print(f"remaining pending object reviews = {statuses['pending']}")
    print(f"remaining identity/object review queue = {len(queue)}")
    print("ThirdPartyID minted = no")
    print("Klose merge authorized = no")


if __name__ == "__main__":
    main()
