#!/usr/bin/env python3
"""Resolve Renjiao start1 single-token semantic-risk candidates.

This pass operates only on the 90 rows currently classified as
pending-vocabulary-sense-review. Clear elementary target senses become
model-reviewed Vocabulary learning-unit candidates. Insufficient source context
stays held, and explicit within-source semantic collisions become split-required.

Stage A only: no ThirdPartyID minting and no Klose final diff.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
STAGING = BASE / "third_party_vocabulary" / "staging"
PATH = STAGING / "renjiao_new_surface_route_resolution.csv"
QUEUE = STAGING / "renjiao_new_surface_identity_review_queue.csv"

FIELDS = [
    "MatchKey", "DisplayForms", "Definitions", "Books", "OccurrenceCount",
    "Contexts", "RiskSignals", "CandidateType", "CandidateRoute",
    "ProposedObjectDecision", "ResolutionStatus", "Confidence",
    "TargetReference", "ResolutionBasis", "Rationale", "KloseMergeAuthorized",
]

# Explicit target senses inferred from the Renjiao source neighborhoods.
# These are model-reviewed Stage-A decisions, not source-confirmed Klose merges.
RESOLVED: dict[str, tuple[str, str]] = {
    "active": ("积极的；活跃的", "high"),
    "age": ("年龄", "high"),
    "always": ("总是；一直", "high"),
    "bank": ("银行", "high"),
    "bark": ("吠叫；狗叫", "medium"),
    "bedroom": ("卧室", "high"),
    "bite": ("咬", "high"),
    "blind": ("失明的；瞎的", "high"),
    "bookshop": ("书店", "high"),
    "boring": ("无聊的；令人厌烦的", "high"),
    "candy": ("糖果", "high"),
    "celebrate": ("庆祝", "high"),
    "cute": ("可爱的", "high"),
    "delicious": ("美味的；可口的", "high"),
    "doll": ("洋娃娃；玩偶", "high"),
    "downtown": ("市中心；在市中心", "medium"),
    "everyone": ("每个人；人人", "high"),
    "everywhere": ("到处；处处", "high"),
    "fantastic": ("极好的；非常棒的", "high"),
    "fifteen": ("十五", "high"),
    "fourteen": ("十四", "high"),
    "free": ("空闲的；有空的", "high"),
    "frog": ("青蛙", "high"),
    "grade": ("年级", "high"),
    "guess": ("猜；猜测", "medium"),
    "habit": ("习惯", "high"),
    "handsome": ("英俊的；帅气的", "high"),
    "happy": ("高兴的；开心的", "high"),
    "help": ("帮助；帮忙", "high"),
    "kick": ("踢", "high"),
    "knife": ("刀", "high"),
    "leave": ("离开；出发", "high"),
    "less": ("更少；较少", "high"),
    "mark": ("分数；成绩", "high"),
    "merry": ("愉快的；快乐的", "medium"),
    "more": ("更多；更多的", "high"),
    "north": ("北；北方", "high"),
    "paint": ("画；涂；上色", "medium"),
    "party": ("聚会；派对", "high"),
    "pet": ("宠物", "high"),
    "pity": ("遗憾；可惜", "medium"),
    "place": ("地方；地点", "high"),
    "present": ("礼物", "high"),
    "pretty": ("漂亮的；好看的", "high"),
    "prize": ("奖品；奖赏", "high"),
    "reading": ("阅读；读书", "high"),
    "reptile": ("爬行动物", "high"),
    "running": ("跑步", "high"),
    "sandwich": ("三明治", "high"),
    "scarf": ("围巾", "high"),
    "shark": ("鲨鱼", "high"),
    "sick": ("生病的；不舒服的", "high"),
    "silk": ("丝绸；蚕丝", "high"),
    "singing": ("唱歌；歌唱", "high"),
    "six": ("六", "high"),
    "slim": ("苗条的；修长的", "high"),
    "south": ("南；南方", "high"),
    "special": ("特别的；特殊的", "medium"),
    "spend": ("花费；度过（时间）", "medium"),
    "squirrel": ("松鼠", "high"),
    "stone": ("石头；石块", "high"),
    "straight": ("直的；笔直的", "high"),
    "swan": ("天鹅", "high"),
    "t-shirt": ("T恤衫", "high"),
    "tail": ("尾巴", "high"),
    "test": ("测试；考试", "medium"),
    "thirteen": ("十三", "high"),
    "trunk": ("象鼻", "high"),
    "tusk": ("长牙；象牙", "high"),
    "wet": ("湿的；潮湿的", "high"),
    "whale": ("鲸；鲸鱼", "high"),
    "win": ("赢；获胜", "high"),
    "wow": ("哇（表示惊讶或赞叹）", "high"),
}

HELD: dict[str, str] = {
    "american": "The neighborhood identifies a nationality word but does not establish noun 'American' versus adjective 'American' as the intended learning unit.",
    "catch": "The hobby neighborhood does not identify what is being caught or whether the target is the general verb, a sport/hobby collocation, or another elementary sense.",
    "central": "The nearby place/travel items do not establish whether central is an adjective, a named-place fragment, or another target use.",
    "danish": "The nationality/language neighborhood does not establish whether the target is Danish as adjective, person/nationality, or language.",
    "dream": "The travel/activity neighborhood is compatible with noun 'dream' and verb 'dream'; the source list has no sentence/unit evidence to choose one learning unit.",
    "fall": "The neighborhood is not sufficient to distinguish fall='落下/摔倒' from fall='秋天' or another elementary use.",
    "here": "The list neighborhood is too weak to determine the exact deictic/interjection use of here.",
    "hope": "The neighborhood does not establish noun 'hope' versus verb 'hope'.",
    "just": "The source neighborhood is insufficient to choose among elementary adverb senses such as 'just/only', 'just now', or 'exactly'.",
    "send": "The neighborhood lacks an object or sentence, so the intended communication/transfer construction cannot be source-confirmed.",
    "so": "The neighborhood does not distinguish conjunction 'so=所以' from adverbial 'so=如此/这么'.",
    "step": "The neighborhood does not establish noun 'step/步骤/脚步' versus verb '迈步'.",
    "summary": "This may be a lexical target or a source/review-section artifact; the current word-list context is insufficient to mint a learning unit safely.",
    "taste": "The geography/travel neighborhood does not establish noun '味道' versus verb '品尝/尝起来'.",
    "top": "The neighborhood does not establish noun/adjective/prepositional use of top as one clear target sense.",
    "volunteer": "The neighborhood does not establish noun '志愿者' versus verb/adjective volunteer usage as the intended learning unit.",
}

SPLIT: dict[str, tuple[str, str]] = {
    "french": (
        "法语 | 法国的/法国人（国籍用法）",
        "Renjiao has one occurrence in 'speak French' and another in an American/French/Danish nationality block; one surface therefore carries at least two pedagogically distinct target uses.",
    ),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    rows = read_csv(PATH)
    by_key = {r["MatchKey"]: r for r in rows}
    if len(rows) != 403 or len(by_key) != 403:
        raise SystemExit("Unexpected Renjiao routing baseline")

    pending_keys = {
        r["MatchKey"] for r in rows
        if r["ProposedObjectDecision"] == "pending-vocabulary-sense-review"
        and r["ResolutionStatus"] == "pending"
    }
    expected = set(RESOLVED) | set(HELD) | set(SPLIT)
    if len(expected) != 90:
        raise SystemExit(f"Single-token review decision table must contain 90 keys, found {len(expected)}")
    if pending_keys != expected:
        missing = sorted(pending_keys - expected)
        extra = sorted(expected - pending_keys)
        raise SystemExit(f"Single-token review set drift: undecided={missing}; stale-decisions={extra}")

    for key, (sense, confidence) in RESOLVED.items():
        row = by_key[key]
        row.update({
            "ProposedObjectDecision": "new-vocabulary-learning-unit-candidate",
            "ResolutionStatus": "model-reviewed",
            "Confidence": confidence,
            "TargetReference": sense,
            "ResolutionBasis": "model-single-token-source-neighborhood-review",
            "Rationale": (
                "The Renjiao neighborhood supports one elementary target sense despite broad dictionary POS/gloss noise. "
                "This remains a provisional Stage-A learning-unit decision, not stable ThirdPartyID minting."
            ),
            "KloseMergeAuthorized": "no",
        })

    for key, rationale in HELD.items():
        row = by_key[key]
        row.update({
            "ProposedObjectDecision": "held-source-context-required",
            "ResolutionStatus": "model-reviewed",
            "Confidence": "medium",
            "TargetReference": "",
            "ResolutionBasis": "model-single-token-insufficient-source-context",
            "Rationale": rationale,
            "KloseMergeAuthorized": "no",
        })

    for key, (senses, rationale) in SPLIT.items():
        row = by_key[key]
        row.update({
            "ProposedObjectDecision": "within-source-split-required",
            "ResolutionStatus": "model-reviewed",
            "Confidence": "high",
            "TargetReference": senses,
            "ResolutionBasis": "model-single-token-within-source-semantic-collision",
            "Rationale": rationale,
            "KloseMergeAuthorized": "no",
        })

    write_csv(PATH, rows)
    queue = [
        r for r in rows
        if r["ResolutionStatus"] == "pending"
        or r["ProposedObjectDecision"].startswith("held-")
    ]
    write_csv(QUEUE, queue)

    statuses = Counter(r["ResolutionStatus"] for r in rows)
    decisions = Counter(r["ProposedObjectDecision"] for r in rows)
    print(f"Single-token semantic review rows = {len(expected)}")
    print(f"single-token resolved learning units = {len(RESOLVED)}")
    print(f"single-token held = {len(HELD)}")
    print(f"single-token split-required = {len(SPLIT)}")
    for key in sorted(statuses):
        print(f"status {key} = {statuses[key]}")
    for key in sorted(decisions):
        print(f"decision {key} = {decisions[key]}")
    print(f"remaining identity/object review queue = {len(queue)}")
    print("ThirdPartyID minted = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
