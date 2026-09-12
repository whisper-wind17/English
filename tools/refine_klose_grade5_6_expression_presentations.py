#!/usr/bin/env python3
"""Refine Grade 5-6 Expression learner presentation for LearnerLevel 4.

Identity/reconciliation is already frozen. This tool changes only learner-facing
presentation. Changed fingerprints are invalidated by the independent review sync. It removes teaching/meta jargon,
uses a concrete textbook utterance as Target, and keeps the reusable canonical
form separately in Pattern.
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

CATEGORY_BY_PREFIX = {
    "ask_": "提问", "state_": "陈述", "respond_": "回应", "answer_": "回答",
    "suggest_": "建议", "request_": "请求", "warn_": "提醒", "remind_": "提醒",
    "express_": "表达", "accept_": "回应", "decline_": "回应", "refuse_": "回应",
    "apolog": "道歉", "comfort_": "安慰", "tell_": "请求", "compare_": "比较",
    "explain_": "解释", "invite_": "邀请", "confirm_": "确认", "describe_": "描述",
}

SPECIAL: dict[str, tuple[str, str, str]] = {
    "Can you [verb phrase]?": ("询问能力", "想问对方会不会做某事", "用来询问别人是否会做某事；这里不是请求许可。"),
    "No, I can't.": ("否定回答", "对方问你会不会做某事，你想回答“不会”", "用来否定回答自己是否会做某事。"),
    "What's your favourite [category]?": ("询问喜好", "想问对方某一类东西中最喜欢哪个", "用来询问对方最喜欢的对象。"),
    "What do you usually do [time phrase]?": ("询问日常活动", "想问对方某个时间通常做什么", "用来询问某个时间通常做什么。"),
    "Does [person] [verb phrase] on both [time 1] and [time 2]?": ("询问两个时间", "想问某人在两个时间是不是都做同一件事", "用来询问同一活动是否在两个时间都发生。"),
    "Yes, [subject pronoun] does.": ("肯定回答", "对方问某人平时是否做某事，你想回答“是的”", "用来肯定回答某人的日常情况。"),
    "Yes, there is.": ("肯定回答", "对方问某处有没有一个东西，你想回答“有”", "用来肯定回答单数事物是否存在。"),
    "Yes, there are.": ("肯定回答", "对方问某处有没有一些东西，你想回答“有”", "用来肯定回答复数事物是否存在。"),
    "Because [clause].": ("说明原因", "别人问“为什么”，你想说明原因", "用 Because 开头说明原因。"),
    "No, [subject pronoun] isn't.": ("否定回答", "对方问某人是否正在做某事，你想回答“没有”", "用来否定回答某人是否正在做某事。"),
    "I [past verb phrase] [past time].": ("讲过去的事", "想说自己过去什么时候做了什么", "用来讲自己过去做过的事情。"),
    "We went to [verb phrase].": ("讲过去的事", "想说过去去做了什么", "用来讲过去去做某件事。"),
    "Did you [verb phrase]?": ("询问过去的事", "想问对方过去有没有做过某事", "用来询问过去是否做过某事。"),
    "No, [subject pronoun] didn't.": ("否定回答", "对方问某人过去是否做过某事，你想回答“没有”", "用来否定回答过去是否做过某事。"),
    "Yes, [subject pronoun] did.": ("肯定回答", "对方问某人过去是否做过某事，你想回答“做过”", "用来肯定回答过去是否做过某事。"),
    "How are you going to [verb phrase]?": ("询问计划", "想问对方打算怎样做一件事", "用来询问对方完成计划的方式。"),
    "I'm going to [verb phrase].": ("说计划", "想说自己接下来打算做什么", "用来说明自己的近期计划。"),
    "That's the [superlative adjective] [noun] [place phrase].": ("指出最突出的一个", "想指出一组事物中最突出的那个", "用来指出某个范围内最突出的对象。"),
    "[Subject] is/are [comparative adjective] than [target].": ("比较两个对象", "想比较两个对象在某方面的不同", "用来比较两个对象在某方面的差异。"),
    "I'm [height].": ("回答身高", "别人问你的身高，你想告诉他", "用来回答自己的身高。"),
    "I'm [weight].": ("回答体重", "别人问你的体重，你想告诉他", "用来回答自己的体重。"),
    "Sounds great!": ("积极回应", "听到一个不错的计划或经历，你想表示赞同", "用来积极回应一个听起来不错的计划或经历。"),
    "Before, [clause]. Now, [clause].": ("对比过去和现在", "想说以前和现在有什么变化", "用来对比过去和现在的状态。"),
    "I was [adjective], so I couldn't [verb phrase].": ("解释过去原因", "想说明自己当时为什么做不到某事", "用过去的状态解释当时为什么做不到某事。"),
    "Now, I [verb phrase] [frequency].": ("说现在的新习惯", "想说自己现在形成了什么新习惯", "用来说明自己现在的新日常行为。"),
}

TARGET_OVERRIDES: dict[str, tuple[str, str]] = {
    "Can you [verb phrase]?": ("Can you make robots?", "verb phrase: make robots"),
    "What's your favourite [category]?": ("What's your favourite day at school?", "category: day at school"),
    "What do you usually do [time phrase]?": ("What do you usually do at the weekend?", "time phrase: at the weekend"),
    "Does [person] [verb phrase] on both [time 1] and [time 2]?": (
        "Does your mother work on both Saturdays and Sundays?",
        "person: your mother · verb phrase: work · time 1: Saturdays · time 2: Sundays",
    ),
    "Are there any [plural noun] [place phrase]?": (
        "Are there any famous mountains in the nature park?",
        "plural noun: famous mountains · place phrase: in the nature park",
    ),
    "There will be [noun phrase] [time/place].": (
        "There will be heavy rain in the afternoon too.",
        "noun phrase: heavy rain · time/place: in the afternoon too",
    ),
    "Which [category] do you like best?": ("Which season do you like best?", "category: season"),
    "Because [clause].": ("Because I like summer vacation!", "clause: I like summer vacation"),
    "[Subjects] are [verb-ing].": ("They're eating lunch.", "subjects: they · verb-ing: eating lunch"),
    "Keep [thing] [adjective].": ("Keep your desk clean.", "thing: your desk · adjective: clean"),
    "My [body part] hurts.": ("My head hurts.", "body part: head"),
    "I [past verb phrase] [past time].": (
        "I visited the Gingerbread House last Saturday.",
        "past verb phrase: visited the Gingerbread House · past time: last Saturday",
    ),
    "Where did you go [past time]?": (
        "Where did you go over the summer holidays?",
        "past time: over the summer holidays",
    ),
    "[Subject] went to [place/event] [past time].": (
        "My mother and I went to a marathon on Sunday.",
        "subject: My mother and I · place/event: a marathon · past time: on Sunday",
    ),
    "I'm [height].": ("I'm 1.65 metres.", "height: 1.65 metres"),
    "What size are your [items]?": ("What size are your shoes?", "items: shoes"),
    "[Items] are size [size].": ("My shoes are size 37.", "items: my shoes · size: 37"),
    "It looks like [thing].": ("It looks like a mule!", "thing: a mule"),
    "There were no [things] [place/time].": (
        "There were no computers or Internet in my time.",
        "things: computers or Internet · place/time: in my time",
    ),
    "Now, I [verb phrase] [frequency].": (
        "Now, I go cycling every day.",
        "verb phrase: go cycling · frequency: every day",
    ),
}

META_REPLACEMENTS = [
    ("高迁移", ""), ("可迁移", ""), ("高频", ""), ("教材核心", ""),
    ("基础主动产出", ""), ("基础", ""), ("通用", ""), ("常用", ""), ("简洁", ""),
    ("production frame", "表达"), ("discourse frame", "表达"),
    ("going-to frame", "表达"), ("going-to 句型", "表达"),
    ("固定实现", "表达"), ("固定表达", "表达"), ("核心问句", "问句"),
    ("社交表达", "表达"), ("感知表达", "表达"), ("句型", "表达"), ("构式", "表达"), ("框架", "表达"),
    ("本句", ""), ("语义核心", "关键意思"), ("承载", "表达"),
    ("一般过去时", "过去"), ("现在进行时", "正在发生的事情"), ("一般现在时", "日常情况"),
    ("是非问句", "问句"), ("否定祈使", "不要做某事"),
]
BANNED_FRONT = (
    "production frame", "discourse frame", "going-to frame", "高迁移", "教材核心", "构式",
    "本句", "承载", "语义核心", "一般过去时", "现在进行时", "一般现在时", "是非问句",
)


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


def category(function_key: str) -> str:
    key = (function_key or "").strip().casefold()
    for prefix, label in CATEGORY_BY_PREFIX.items():
        if key.startswith(prefix):
            return label
    return "表达"


def friendly(text: str) -> str:
    out = " ".join((text or "").strip().split())
    out = re.split(r"[；。]", out, maxsplit=1)[0].strip()
    for old, new in META_REPLACEMENTS:
        out = out.replace(old, new)
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
            escaped = re.escape(part).replace(r"\ ", r"\s+")
            escaped = escaped.replace("is/are", r"(?:is|are)")
            escaped = escaped.replace("a/an", r"(?:a|an)")
            chunks.append(escaped)
    return re.compile("".join(chunks), re.IGNORECASE), names


def source_variants(raw: str) -> list[str]:
    text = raw.replace("’", "'").strip()
    variants = [text]
    stripped = re.sub(r"^(?:And|But|Well),?\s+", "", text, flags=re.IGNORECASE)
    if stripped != text:
        variants.append(stripped[:1].upper() + stripped[1:])
    no_vocative = re.sub(r",\s*(?:[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)?|children|kids|class|everyone)([?!])$", r"\1", text, flags=re.IGNORECASE)
    if no_vocative != text:
        variants.append(no_vocative)
    return list(dict.fromkeys(variants))


def concrete_target(canonical: str, slot_schema: str, raws: list[str]) -> tuple[str, str]:
    if canonical in TARGET_OVERRIDES:
        return TARGET_OVERRIDES[canonical]
    if "[" not in canonical:
        return canonical, ""
    pattern, names_from_pattern = canonical_regex(canonical)
    slot_names = [x.strip().replace("_", " ") for x in (slot_schema or "").split("|") if x.strip()]
    for raw in raws:
        for normalized in source_variants(raw):
            match = pattern.search(normalized)
            active_names = names_from_pattern
            if not match:
                contraction = canonical.replace("What is ", "What's ").replace("what is ", "what's ")
                if contraction != canonical:
                    pattern2, names2 = canonical_regex(contraction)
                    match = pattern2.search(normalized)
                    if match:
                        active_names = names2
            if not match:
                continue
            target = match.group(0).strip().strip('"“”')
            target = target[:1].upper() + target[1:] if target else target
            values = [value.strip().strip('"“”') for value in match.groups()]
            names = slot_names if len(slot_names) == len(values) else [x.replace("_", " ") for x in active_names]
            hint = " · ".join(f"{name}: {value}" for name, value in zip(names, values)) if len(names) == len(values) else ""
            return target, hint
    fail(f"no concrete textbook target could be derived for pattern: {canonical}")


def main() -> None:
    allocation_rows = read_csv(ALLOCATION)
    allocated_ids = {r.get("ExpressionID", "").strip() for r in allocation_rows}
    if not allocated_ids or len(allocated_ids) != len(allocation_rows):
        fail("empty/duplicate Grade 5-6 allocation")

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
            label = category(identity.get("FunctionKey", ""))
            prompt = make_prompt(usage)
        target, hint = concrete_target(canonical, identity.get("SlotSchema", ""), raws_by_eid[eid])
        cur.update({
            "FunctionLabel": label,
            "Prompt": prompt,
            "PromptHint": hint,
            "Target": target,
            "Pattern": canonical,
            "MeaningUsage": usage,
            "ContextNote": "",
        })


    problems: list[str] = []
    targets: set[str] = set()
    for eid in sorted(allocated_ids):
        row = current_by_id[eid]
        front = f"{row.get('FunctionLabel','')} {row.get('Prompt','')} {row.get('PromptHint','')}"
        if any(token.casefold() in front.casefold() for token in BANNED_FRONT):
            problems.append(f"{eid}: learner-facing meta jargon")
        if "[" in row.get("Target", "") or "]" in row.get("Target", ""):
            problems.append(f"{eid}: Target still contains abstract slot")
        if "___" in row.get("PromptHint", ""):
            problems.append(f"{eid}: unresolved slot cue")
        if not row.get("Target", "").strip() or not row.get("Prompt", "").strip():
            problems.append(f"{eid}: blank target/prompt")
        target_key = row.get("Target", "").strip().casefold()
        if target_key in targets:
            problems.append(f"{eid}: duplicate concrete Target")
        targets.add(target_key)
    if problems:
        fail(f"learner-facing quality gate failed: {problems[:20]}")

    write_csv(CURRENT, CURRENT_FIELDS, current_rows)
    from klose_expression_review_state import synchronize
    synchronize()
    print(f"Refined Grade 5-6 Expression presentations: rows={len(allocated_ids)} concrete_targets={len(allocated_ids)} unresolved_slots=0 meta_jargon=0")


if __name__ == "__main__":
    main()
