#!/usr/bin/env python3
"""Refine Grade 5-6 Expression learner presentation for LearnerLevel 4.

The identity/reconciliation layer is already frozen. This tool only improves the
learner-facing presentation: remove linguistic/meta jargon from prompts, prefer a
concrete textbook utterance as Target when it can be matched to the canonical
pattern, expose concrete slot cues, and re-bind the model-review fingerprint.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

from klose_expression_review_fingerprint import VERSION, fingerprint

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose" / "expressions"
MASTER = BASE / "master"
LEARNER = BASE / "learner"
ALLOCATION = MASTER / "grade5_6_identity_allocation.csv"
REGISTRY = MASTER / "expression_registry.csv"
OCCURRENCES = MASTER / "expression_occurrences.csv"
SOURCE_MAP = MASTER / "source_expression_map.csv"
CURRENT = LEARNER / "current.csv"
REVIEWS = LEARNER / "presentation_review_registry.csv"

CURRENT_FIELDS = [
    "LearnerProfile", "LearnerLevel", "ExpressionID", "FunctionLabel", "Prompt", "PromptHint",
    "Target", "Pattern", "MeaningUsage", "Examples", "ContextNote",
]
REVIEW_FIELDS = [
    "LearnerProfile", "LearnerLevel", "ExpressionID", "FingerprintVersion", "Fingerprint",
    "ReviewStatus", "ReviewBasis", "ReviewedAt",
]

SPECIAL: dict[str, tuple[str, str, str]] = {
    "No, I can't.": ("否定回答", "对方问你会不会做某事，你想回答“不会”", "用来否定回答自己是否会做某事。"),
    "Yes, [subject pronoun] does.": ("肯定回答", "对方问某人平时是否做某事，你想回答“是的”", "用来肯定回答某人的日常情况。"),
    "No, [subject pronoun] isn't.": ("否定回答", "对方问某人是否正在做某事，你想回答“没有”", "用来否定回答某人是否正在做某事。"),
    "No, [subject pronoun] didn't.": ("否定回答", "对方问某人过去是否做过某事，你想回答“没有”", "用来否定回答过去是否做过某事。"),
    "Yes, [subject pronoun] did.": ("肯定回答", "对方问某人过去是否做过某事，你想回答“做过”", "用来肯定回答过去是否做过某事。"),
    "Yes, there is.": ("肯定回答", "对方问某处有没有一个东西，你想回答“有”", "用来肯定回答单数事物是否存在。"),
    "Yes, there are.": ("肯定回答", "对方问某处有没有一些东西，你想回答“有”", "用来肯定回答复数事物是否存在。"),
    "Because [clause].": ("说明原因", "别人问“为什么”，你想说明原因", "用 Because 开头说明原因。"),
    "I [past verb phrase] [past time].": ("讲过去的事", "想说自己过去什么时候做了什么", "用来讲自己过去做过的事情。"),
    "We went to [verb phrase].": ("讲过去的事", "想说过去去做了什么", "用来讲过去去做某件事。"),
    "I'm going to [verb phrase].": ("说计划", "想说自己接下来打算做什么", "用来说明自己的近期计划。"),
    "How are you going to [verb phrase]?": ("询问计划", "想问对方打算怎样做一件事", "用来询问对方完成计划的方式。"),
    "I'm [height].": ("回答身高", "别人问你的身高，你想告诉他", "用来回答自己的身高。"),
    "I'm [weight].": ("回答体重", "别人问你的体重，你想告诉他", "用来回答自己的体重。"),
    "That's the [superlative adjective] [noun] [place phrase].": ("指出最突出的一个", "想指出一组事物中最突出的那个", "用来指出某个范围内最突出的对象。"),
    "[Subject] is/are [comparative adjective] than [target].": ("比较两个对象", "想比较两个对象在某方面的不同", "用来比较两个对象在某方面的差异。"),
    "Before, [clause]. Now, [clause].": ("对比过去和现在", "想说以前和现在有什么变化", "用来对比过去和现在的状态。"),
    "I was [adjective], so I couldn't [verb phrase].": ("解释过去原因", "想说明自己当时为什么做不到某事", "用过去的状态解释当时为什么做不到某事。"),
    "Now, I [verb phrase] [frequency].": ("说现在的新习惯", "想说自己现在形成了什么新习惯", "用来说明自己现在的新日常行为。"),
    "Sounds great!": ("积极回应", "听到一个不错的计划或经历，你想表示赞同", "用来积极回应一个听起来不错的计划或经历。"),
}

META_REPLACEMENTS = [
    ("高迁移", ""), ("可迁移", ""), ("高频", ""), ("教材核心", ""),
    ("基础主动产出", ""), ("基础", ""), ("通用", ""), ("常用", ""), ("简洁", ""),
    (" production frame", "表达"), ("production frame", "表达"),
    (" discourse frame", "表达"), ("discourse frame", "表达"),
    (" going-to frame", "表达"), ("going-to frame", "表达"),
    (" going-to 句型", "表达"), ("going-to 句型", "表达"),
    ("句型", "表达"), ("构式", "表达"), ("框架", "表达"),
]


def fail(msg: str) -> None:
    raise SystemExit(f"Grade 5-6 Expression presentation refinement failure: {msg}")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def friendly(text: str) -> str:
    out = " ".join((text or "").strip().split())
    out = re.split(r"[；。]", out, maxsplit=1)[0].strip()
    for old, new in META_REPLACEMENTS:
        out = out.replace(old, new)
    out = out.replace("一般现在时 Does 问句的肯定短答", "肯定回答日常情况")
    out = out.replace("现在进行时是非问句的否定短答", "否定回答正在发生的事情")
    out = out.replace("一般过去时是非问句的否定短答", "否定回答过去的事情")
    out = out.replace("一般过去时是非问句的肯定短答", "肯定回答过去的事情")
    out = out.replace("回答 Why 时给出原因", "回答“为什么”并说明原因")
    out = out.replace("频率副词位置", "经常做什么")
    out = out.replace("both...and 结构", "两个时间都发生")
    out = out.replace("最高级", "最突出的")
    out = out.replace("比较级", "比较")
    out = re.sub(r"\s+", " ", out).strip(" ，,;：:")
    return out


def make_prompt(usage: str) -> str:
    text = friendly(usage)
    if text.startswith(("询问", "追问", "表达", "说明", "描述", "提出", "提醒", "请求", "回答", "回应", "接受", "拒绝", "确认", "比较", "解释", "介绍", "评价", "告诉", "转述")):
        return "想" + text
    if text.startswith("对") and ("回答" in text or "回应" in text):
        return "想这样回应：" + text
    return "想表达这个意思：" + text


def make_label(usage: str) -> str:
    text = friendly(usage)
    if len(text) <= 14:
        return text
    for sep in ("的", "并", "；", "，"):
        if sep in text:
            head = text.split(sep, 1)[0]
            if 4 <= len(head) <= 14:
                return head
    return text[:14]


def canonical_regex(canonical: str) -> tuple[re.Pattern[str], list[str]]:
    names: list[str] = []
    chunks: list[str] = []
    for part in re.split(r"(\[[^\]]+\])", canonical):
        if not part:
            continue
        if part.startswith("[") and part.endswith("]"):
            names.append(part[1:-1].strip())
            chunks.append(r"(.+?)")
        else:
            escaped = re.escape(part)
            escaped = escaped.replace(r"\ ", r"\s+")
            escaped = escaped.replace("is/are", r"(?:is|are)")
            escaped = escaped.replace("a/an", r"(?:a|an)")
            chunks.append(escaped)
    return re.compile("".join(chunks), re.IGNORECASE), names


def concrete_target(canonical: str, slot_schema: str, raws: list[str]) -> tuple[str, str]:
    if "[" not in canonical:
        return canonical, ""
    pattern, names_from_pattern = canonical_regex(canonical)
    slot_names = [x.strip().replace("_", " ") for x in (slot_schema or "").split("|") if x.strip()]
    for raw in raws:
        normalized = raw.replace("’", "'")
        match = pattern.search(normalized)
        if not match:
            # common textbook contraction: canonical `What is ...` vs source `What's ...`
            contraction = canonical.replace("What is ", "What's ").replace("what is ", "what's ")
            if contraction != canonical:
                pattern2, names2 = canonical_regex(contraction)
                match = pattern2.search(normalized)
                if match:
                    names_from_pattern = names2
            if not match:
                continue
        target = match.group(0).strip().strip('"“”')
        values = [value.strip().strip('"“”') for value in match.groups()]
        names = slot_names if len(slot_names) == len(values) else [x.replace("_", " ") for x in names_from_pattern]
        if len(names) == len(values):
            hint = " · ".join(f"{name}: {value}" for name, value in zip(names, values))
        else:
            hint = ""
        return target, hint
    fallback_names = slot_names or [x.replace("_", " ") for x in names_from_pattern]
    return canonical, " · ".join(f"{name}: ___" for name in fallback_names)


def main() -> None:
    allocation_rows = read_csv(ALLOCATION)
    allocated_ids = {r.get("ExpressionID", "").strip() for r in allocation_rows}
    if len(allocated_ids) != 110:
        fail(f"expected 110 allocated Grade 5-6 identities, got {len(allocated_ids)}")

    registry = {r["ExpressionID"].strip(): r for r in read_csv(REGISTRY)}
    occurrences = {r["OccurrenceID"].strip(): r for r in read_csv(OCCURRENCES)}
    raws_by_eid: defaultdict[str, list[str]] = defaultdict(list)
    for row in read_csv(SOURCE_MAP):
        if row.get("MappingStatus", "").strip() != "confirmed":
            continue
        eid = row.get("ExpressionID", "").strip()
        oid = row.get("OccurrenceID", "").strip()
        if eid in allocated_ids and oid in occurrences:
            raw = occurrences[oid].get("RawExpression", "").strip()
            if raw and raw not in raws_by_eid[eid]:
                raws_by_eid[eid].append(raw)

    current_rows = read_csv(CURRENT)
    current_by_id = {r["ExpressionID"].strip(): r for r in current_rows}
    reviews = read_csv(REVIEWS)
    review_by_id = {r["ExpressionID"].strip(): r for r in reviews}

    concrete = 0
    fallback = 0
    for eid in sorted(allocated_ids):
        if eid not in registry or eid not in current_by_id or eid not in review_by_id:
            fail(f"missing registry/current/review row: {eid}")
        identity = registry[eid]
        cur = current_by_id[eid]
        canonical = identity.get("CanonicalForm", "").strip()
        if canonical in SPECIAL:
            label, prompt, usage = SPECIAL[canonical]
        else:
            usage = friendly(cur.get("MeaningUsage", ""))
            label = make_label(usage)
            prompt = make_prompt(usage)
        target, hint = concrete_target(canonical, identity.get("SlotSchema", ""), raws_by_eid[eid])
        if "[" in target:
            fallback += 1
        else:
            concrete += 1
        cur.update({
            "FunctionLabel": label,
            "Prompt": prompt,
            "PromptHint": hint,
            "Target": target,
            "Pattern": canonical,
            "MeaningUsage": usage,
            "ContextNote": "",
        })
        review = review_by_id[eid]
        review.update({
            "FingerprintVersion": VERSION,
            "Fingerprint": fingerprint(cur),
            "ReviewStatus": "model-reviewed",
            "ReviewBasis": "model-reviewed-grade5-6-learner-presentation-v2",
            "ReviewedAt": "2026-09-11",
        })

    write_csv(CURRENT, CURRENT_FIELDS, current_rows)
    write_csv(REVIEWS, REVIEW_FIELDS, reviews)

    banned = ("production frame", "discourse frame", "going-to frame", "高迁移", "教材核心", "构式")
    bad: list[str] = []
    for eid in sorted(allocated_ids):
        row = current_by_id[eid]
        front = (row.get("FunctionLabel", "") + " " + row.get("Prompt", "")).casefold()
        for token in banned:
            if token.casefold() in front:
                bad.append(f"{eid}:{token}")
    if bad:
        fail(f"learner-facing meta jargon remains: {bad[:20]}")

    print(
        "Refined Grade 5-6 Expression presentations: "
        f"rows=110 concrete_targets={concrete} pattern_targets={fallback} meta_jargon=0"
    )


if __name__ == "__main__":
    main()
