#!/usr/bin/env python3
"""Build the first-pass Beijing + Renjiao cross-source Identity Resolution table.

This remains Stage A only. It never mints ThirdPartyID and never performs the
final diff against Klose. Automatic resolution is deliberately narrow:
exact-overlap rows with no semantic risk signals may become provisional
reuse-learning-unit decisions. Known semantic collisions are explicitly
model-reviewed. Everything else stays pending.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "anki" / "klose" / "third_party_vocabulary" / "staging"
INPUT = STAGING / "cross_source_context_review.csv"
OUTPUT = STAGING / "cross_source_identity_resolution.csv"

FIELDS = [
    "MatchKey", "DisplayForms", "Definitions", "BeijingContexts", "RenjiaoContexts",
    "RiskSignals", "ProposedDecision", "ResolutionStatus", "Confidence",
    "ProposedSense", "ResolutionBasis", "Rationale", "KloseMergeAuthorized",
]

# Explicit model-reviewed cases where surface-level equality is known to be
# insufficient. These are intentionally conservative; held cases are not
# treated as resolved.
MODEL_DECISIONS: dict[str, tuple[str, str, str, str, str]] = {
    "can": (
        "reuse-learning-unit", "model-reviewed", "high", "modal can = 能；可以",
        "Both source neighborhoods indicate modal can; the dictionary noun sense 'can/container' is not the textbook target here.",
    ),
    "may": (
        "partial-overlap-split-required", "model-reviewed", "high",
        "Renjiao: May=五月; Beijing: May=五月 plus may=可以/可能",
        "Beijing contains both month and modal occurrences under one MatchKey; Renjiao is the month sequence. Occurrence-level identity split is required.",
    ),
    "like": (
        "partial-overlap-split-required", "model-reviewed", "high",
        "Renjiao: 喜欢; Beijing contains 喜欢 and 像/……怎么样 usage",
        "Renjiao 'do you like' is preference; Beijing includes weather-like context, so one surface cannot be one identity.",
    ),
    "square": (
        "do-not-merge", "model-reviewed", "high", "Beijing=正方形; Renjiao=广场",
        "Beijing is in a shape block; Renjiao is in a city/place block. Same surface, different target sense.",
    ),
    "left": (
        "do-not-merge", "model-reviewed", "high", "Beijing=左边/向左; Renjiao=leave 的过去式",
        "Beijing is directions/location context; Renjiao appears in a past-event context. Same surface, different learning unit.",
    ),
    "cook": (
        "do-not-merge", "model-reviewed", "high", "Beijing=烹饪/煮(verb); Renjiao=厨师(noun)",
        "Beijing is food/action context; Renjiao is an occupation list. Same surface, different target sense/POS.",
    ),
    "cold": (
        "partial-overlap-split-required", "model-reviewed", "high",
        "weather cold plus illness cold",
        "Beijing contains both weather and illness neighborhoods; Renjiao is clearly weather/temperature. Occurrence-level split is required.",
    ),
    "dress": (
        "partial-overlap-split-required", "model-reviewed", "medium",
        "noun 连衣裙 plus verb 穿衣/打扮",
        "Renjiao is a clothing-list noun; Beijing contexts plausibly include both noun and verb usage. Keep separate occurrence-level senses.",
    ),
    "study": (
        "partial-overlap-split-required", "model-reviewed", "high",
        "verb 学习 plus noun 书房",
        "Renjiao explicitly contains a room-list 'study' and a learning/education 'study'; one surface must split before identity minting.",
    ),
    "chicken": (
        "partial-overlap-split-required", "model-reviewed", "medium",
        "鸡/小鸡 plus 鸡肉",
        "Food-list and animal/pet neighborhoods coexist across the two sources; occurrence-level target-sense review is required.",
    ),
    "duck": (
        "partial-overlap-split-required", "model-reviewed", "medium",
        "鸭子 plus 鸭肉",
        "Animal and food neighborhoods coexist; do not collapse all occurrences into one identity without an explicit sense policy.",
    ),
    "fan": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "The neighborhoods do not establish whether the target is admirer, hand/electric fan, or another usage. Keep held.",
    ),
    "kind": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "The source may target noun 'type/kind' or adjective 'kind/friendly'; the current neighborhood is insufficient for a safe merge.",
    ),
    "light": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "The source may target lamp/light, illumination, or adjective 'light'; current list context is insufficient.",
    ),
    "speak": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "Renjiao is clearly 'speak French'; Beijing context is not sufficient to decide language-speaking vs general speaking.",
    ),
    "sound": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "Noun 'sound' and linking-verb 'sound' are both plausible from the current neighborhoods. Keep held.",
    ),
    "star": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "Celestial star, star shape, and person/star senses are all plausible across current occurrences. Keep held.",
    ),
    "plant": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "Noun plant and verb plant are both plausible; the source ordering is not enough to collapse them safely.",
    ),
    "live": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "Verb live and adjective live have distinct learning units; current neighborhoods do not source-confirm which one applies.",
    ),
    "tongue": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "Beijing neighborhood may indicate language/mother-tongue while Renjiao is physical tongue, but the Beijing source lacks sentence/unit evidence. Keep held rather than force a split.",
    ),
    "fish": (
        "held-identity-policy", "model-reviewed", "medium", "",
        "Animal and food usages coexist. Decide explicitly whether fish/鱼 and fish/鱼肉 are one pedagogical learning unit before collapsing occurrences.",
    ),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    source = read_csv(INPUT)
    if len(source) != 392:
        raise SystemExit(f"Expected 392 cross-source exact-overlap review rows, found {len(source)}")

    out: list[dict[str, str]] = []
    for row in source:
        key = row["MatchKey"]
        if key in MODEL_DECISIONS:
            decision, status, confidence, sense, rationale = MODEL_DECISIONS[key]
            basis = "model-review-of-source-neighborhoods"
        elif row["RiskSignals"] == "none-detected":
            decision = "reuse-learning-unit"
            status = "rule-reviewed"
            confidence = "high"
            sense = ""
            basis = "strict-exact-overlap-no-semantic-risk-signal"
            rationale = (
                "Exact MatchKey and no detected multi-POS, multi-occurrence, case/form, or known semantic-collision signal. "
                "This is a provisional Stage-A reuse decision, not a Klose merge authorization."
            )
        else:
            decision = "pending-semantic-review"
            status = "pending"
            confidence = ""
            sense = ""
            basis = "semantic-risk-signal-present"
            rationale = "Risk signal remains; do not collapse this surface until a later context-aware review pass."

        out.append({
            "MatchKey": key,
            "DisplayForms": row["DisplayForms"],
            "Definitions": row["Definitions"],
            "BeijingContexts": row["BeijingContexts"],
            "RenjiaoContexts": row["RenjiaoContexts"],
            "RiskSignals": row["RiskSignals"],
            "ProposedDecision": decision,
            "ResolutionStatus": status,
            "Confidence": confidence,
            "ProposedSense": sense,
            "ResolutionBasis": basis,
            "Rationale": rationale,
            "KloseMergeAuthorized": "no",
        })

    write_csv(OUTPUT, out)
    counts = Counter(r["ProposedDecision"] for r in out)
    status_counts = Counter(r["ResolutionStatus"] for r in out)
    print(f"Cross-source resolution rows = {len(out)}")
    for key in sorted(counts):
        print(f"decision {key} = {counts[key]}")
    for key in sorted(status_counts):
        print(f"status {key} = {status_counts[key]}")
    print("Stable ThirdPartyID minted = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
