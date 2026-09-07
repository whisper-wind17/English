#!/usr/bin/env python3
"""One-time conservative review of the 274 new Waiyan start1 surfaces.

This helper is temporary. It consumes only current `pending` surfaces that have no
prior durable decision and no decision-evidence-changed signal. Mechanically safe
low-risk lexical items may be admitted as provisional Stage-A identities; forms,
multiword boundaries, multi-POS/polysemy risk, abbreviations, and unclear source
objects are held rather than guessed. Obvious communicative interjections are
routed to Expressions.

All results are written to the normal transient decision_updates.csv inbox and
become durable data only through the generic apply/build/check pipeline.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
QUEUE = TP / "staging" / "review_queue.csv"
DECISIONS = TP / "review" / "identity_decisions.csv"
UPDATES = TP / "review" / "decision_updates.csv"
EXPECTED_PENDING = 274
FIELDS = [
    "DecisionKey", "MatchKey", "OccurrenceKeys", "Action", "CanonicalMatchKey",
    "ObjectType", "TargetSense", "Status", "Confidence", "DecisionBasis", "Rationale",
]

# Existing project policy: regular plural presentation forms reuse the singular
# lexical learning unit; irregular forms remain held until form policy is explicit.
IRREGULAR_FORMS = {
    "ate", "became", "began", "bought", "brought", "came", "did", "drank", "drew",
    "drove", "fell", "felt", "flew", "forgot", "found", "gave", "got", "grew", "had",
    "heard", "held", "kept", "knew", "left", "lost", "made", "met", "paid", "ran",
    "read", "rode", "said", "sang", "sat", "saw", "sent", "slept", "spoke", "spent",
    "stood", "swam", "taught", "took", "told", "understood", "was", "went", "were",
    "won", "woke", "wore", "wrote",
}
INTERJECTIONS = {
    "aah", "aargh", "aha", "ah", "oh", "ooh", "oops", "ow", "ouch", "wow", "hooray",
}
POS_RE = re.compile(r"(?<![A-Za-z])(?:n|v|vt|vi|adj|adv|prep|conj|pron|det|aux|art|abbr)\.", re.I)
FORM_HINT_RE = re.compile(r"过去式|过去分词|ing形式|第三人称单数|复数\)|比较级|最高级", re.I)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def first_gloss(definition: str) -> str:
    text = (definition or "").strip()
    text = POS_RE.sub("", text, count=1).strip()
    text = re.sub(r"^(?:na|un)\.\s*", "", text, flags=re.I)
    # Keep a compact provisional elementary gloss; the full source Definition
    # remains preserved at Source Occurrence level.
    parts = [p.strip(" ,，。") for p in re.split(r"[;；|]", text) if p.strip(" ,，。")]
    if not parts:
        return ""
    return parts[0][:80]


def main() -> None:
    queue = read_csv(QUEUE)
    durable_keys = {r["MatchKey"] for r in read_csv(DECISIONS)}
    pending = [r for r in queue if r.get("DecisionAction") == "pending" and r.get("DecisionStatus") == "pending"]
    if len(pending) != EXPECTED_PENDING:
        raise SystemExit(f"Expected {EXPECTED_PENDING} new Waiyan pending surfaces, found {len(pending)}")
    if any("decision-evidence-changed" in r.get("CandidateSignals", "") for r in pending):
        raise SystemExit("New-surface review refuses evidence-changed surfaces")
    if any(r["MatchKey"] in durable_keys for r in pending):
        raise SystemExit("New-surface review found a prior durable decision")

    updates: list[dict[str, str]] = []
    counts: dict[str, int] = {}
    for r in pending:
        key = r["MatchKey"]
        definition = r.get("Definitions", "")
        signals = set(x for x in r.get("CandidateSignals", "").split("|") if x)
        candidates = [x for x in r.get("CandidateMatchKeys", "").split("|") if x]
        pos_tags = POS_RE.findall(definition)
        semicolon_count = definition.count(";") + definition.count("；")

        action = "held"
        status = "held"
        canonical = ""
        obj = "vocabulary"
        sense = ""
        confidence = "medium"
        basis = "waiyan-start1-new-surface-conservative-hold"
        rationale = "New Waiyan surface has unresolved sense, form, or object-boundary risk; preserve Source Fact and hold rather than guess a Vocabulary identity."

        if key in INTERJECTIONS:
            action = "route-expression"
            status = "reviewed"
            obj = "expression"
            sense = first_gloss(definition)
            confidence = "high"
            basis = "waiyan-start1-interjection-routing"
            rationale = "The isolated item functions as a communicative reaction/interjection; route it to the Expression object rather than minting a Vocabulary identity."
        elif "morphology" in signals and len(candidates) == 1 and key not in IRREGULAR_FORMS:
            # Builder morphology signals currently cover regular plural-like forms.
            action = "reuse-identity"
            status = "reviewed"
            canonical = candidates[0]
            sense = first_gloss(definition)
            confidence = "high"
            basis = "waiyan-start1-regular-form-canonicalization"
            rationale = "The source surface is a regular inflectional presentation form and the canonical base surface already exists; reuse the base learning unit."
        elif key in IRREGULAR_FORMS or FORM_HINT_RE.search(definition):
            basis = "waiyan-start1-form-policy-held"
            rationale = "The source surface is an inflected/irregular grammatical form; keep held until the form-versus-learning-unit policy is explicitly resolved."
        elif "multiword" in signals or "punctuated" in signals:
            basis = "waiyan-start1-multiword-object-review-held"
            rationale = "The new multiword/punctuated source item may be a lexical chunk, grammatical construction, Expression, or source-only phrase; isolated glossary evidence is insufficient to fix the object boundary safely."
        elif "abbr." in definition.lower():
            basis = "waiyan-start1-abbreviation-policy-held"
            rationale = "The new surface is an abbreviation/contraction presentation form; hold until canonical-form and object policy is explicit."
        elif len(set(x.lower() for x in pos_tags)) > 1:
            basis = "waiyan-start1-multi-pos-semantic-boundary-held"
            rationale = "The source dictionary gloss spans multiple parts of speech; isolated word-list evidence cannot safely bind one target learning unit."
        elif semicolon_count >= 4:
            basis = "waiyan-start1-polysemy-risk-held"
            rationale = "The source dictionary gloss exposes several distinct senses; without source context, selecting one target sense would be guesswork."
        else:
            action = "keep-identity"
            status = "reviewed"
            obj = "vocabulary"
            sense = first_gloss(definition)
            confidence = "medium"
            basis = "waiyan-start1-low-risk-lexical-review"
            rationale = "New single-surface lexical item has no detected form, multiword, multi-POS, abbreviation, or broad-polysemy risk; admit as a provisional Stage-A learning unit."

        counts[action] = counts.get(action, 0) + 1
        updates.append({
            "DecisionKey": f"surface:{key}",
            "MatchKey": key,
            "OccurrenceKeys": "*",
            "Action": action,
            "CanonicalMatchKey": canonical,
            "ObjectType": obj,
            "TargetSense": sense,
            "Status": status,
            "Confidence": confidence,
            "DecisionBasis": basis,
            "Rationale": rationale,
        })

    with UPDATES.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(updates)

    print(f"Waiyan new surfaces reviewed = {len(updates)}")
    for action in sorted(counts):
        print(f"new-surface action {action} = {counts[action]}")
    print("pending new surfaces left in this batch = 0")
    print("conservative unresolved boundaries become held = yes")


if __name__ == "__main__":
    main()
