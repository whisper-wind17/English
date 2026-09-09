#!/usr/bin/env python3
"""Build the Klose learner-stage view of the third-party Stage-A corpus.

Identity resolution and learner admission are intentionally separate layers.
`staging/unified_vocabulary_preview.csv` remains the identity-level Stage-A view.
Learner-stage policy then removes two independent classes of contributions:

1. grammar-form quarantine: resolved forms that are outside Klose's current grammar stage;
2. content exclusion: learner identities intentionally below the learning threshold
   (currently a/an/the and elementary cardinal/ordinal number identities).

Neither gate mutates Source facts or durable Identity decisions.
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
STAGING = TP / "staging"
LEARNER = TP / "learner"
DECISIONS = TP / "review" / "identity_decisions.csv"
OCCURRENCES = STAGING / "occurrences.csv"
IDENTITY_PREVIEW = STAGING / "unified_vocabulary_preview.csv"
GATE = LEARNER / "grammar_form_quarantine.csv"
LEARNER_PREVIEW = LEARNER / "learner_vocabulary_preview.csv"
QUARANTINE_VIEW = LEARNER / "grammar_form_quarantine_view.csv"
CONTENT_POLICY = LEARNER / "content_exclusion_policy.csv"
CONTENT_VIEW = LEARNER / "content_exclusion_view.csv"

PREVIEW_FIELDS = [
    "ProvisionalIdentityKey", "CanonicalMatchKey", "DisplayWord", "TargetSense",
    "SourceMatchKeys", "SourceOccurrenceCount", "DecisionStatus",
]
GATE_FIELDS = [
    "GateKey", "MatchKey", "DecisionKey", "BaseForm", "FormType", "Scope",
    "PolicyVersion", "Rationale",
]
QUARANTINE_FIELDS = [
    "GateKey", "MatchKey", "DecisionKey", "BaseForm", "FormType", "Scope",
    "CurrentDecisionAction", "CurrentDecisionStatus", "CanonicalMatchKey",
    "CurrentOccurrenceCount", "ReviewedOccurrenceCount", "PreviewContributionRemoved",
    "PolicyVersion", "Rationale",
]
CONTENT_POLICY_FIELDS = [
    "RuleKey", "RuleType", "Value", "ReasonCode", "PolicyVersion", "Rationale",
]
CONTENT_VIEW_FIELDS = [
    "ProvisionalIdentityKey", "CanonicalMatchKey", "DisplayWord", "TargetSense",
    "MatchedRuleKey", "ReasonCode", "PolicyVersion", "Rationale",
    "LearnerIdentityRemoved",
]
CONTENT_POLICY_VERSION = "klose-content-exclusion-v1"

CARDINAL_WORDS = {
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty",
    "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "million", "billion",
}
ORDINAL_WORDS = {
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth",
    "tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth",
    "seventeenth", "eighteenth", "nineteenth", "twentieth", "thirtieth", "fortieth",
    "fiftieth", "sixtieth", "seventieth", "eightieth", "ninetieth", "hundredth",
    "thousandth", "millionth", "billionth",
}
NUMBER_WORDS = CARDINAL_WORDS | ORDINAL_WORDS
NUMBER_FILLERS = {"and", "a"}
NUMERIC_FORM_RE = re.compile(r"^\d[\d,]*(?:\.\d+)?(?:st|nd|rd|th)?$", re.IGNORECASE)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "" if row.get(k) is None else str(row.get(k, "")) for k in fields})


def decode_occurrence_keys(raw: str, decision_key: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid OccurrenceKeys JSON for {decision_key}: {exc}") from exc
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
        raise SystemExit(f"Invalid OccurrenceKeys for {decision_key}")
    if len(value) != len(set(value)):
        raise SystemExit(f"Duplicate OccurrenceKeys for {decision_key}")
    return value


def split_matchkeys(raw: str) -> list[str]:
    return [x for x in raw.split("|") if x]


def target_canonical(decision: dict[str, str]) -> str:
    action = decision.get("Action", "")
    if action == "reuse-identity":
        return decision.get("CanonicalMatchKey", "")
    if action == "keep-identity":
        return decision.get("CanonicalMatchKey", "") or decision.get("MatchKey", "")
    return ""


def is_elementary_number_identity(canonical: str) -> bool:
    text = canonical.casefold().strip()
    if not text or "#" in text:
        return False
    if NUMERIC_FORM_RE.fullmatch(text):
        return True
    tokens = [token for token in re.split(r"[\s-]+", text) if token]
    if not tokens:
        return False
    return (
        any(token in NUMBER_WORDS for token in tokens)
        and all(token in NUMBER_WORDS or token in NUMBER_FILLERS for token in tokens)
    )


def content_rule_for(
    row: dict[str, str], rules: list[dict[str, str]]
) -> dict[str, str] | None:
    canonical = row.get("CanonicalMatchKey", "").casefold().strip()
    matched: list[dict[str, str]] = []
    for rule in rules:
        rule_type = rule.get("RuleType", "")
        value = rule.get("Value", "").casefold().strip()
        if rule_type == "canonical-exact" and canonical == value:
            matched.append(rule)
        elif (
            rule_type == "number-lexeme-class"
            and value == "cardinal-or-ordinal"
            and is_elementary_number_identity(canonical)
        ):
            matched.append(rule)
    if len(matched) > 1:
        raise SystemExit(
            f"Learner content exclusion rules overlap for {row.get('ProvisionalIdentityKey', '')}: "
            f"{[r.get('RuleKey', '') for r in matched]}"
        )
    return matched[0] if matched else None


def main() -> None:
    preview = [dict(r) for r in read_csv(IDENTITY_PREVIEW)]
    occurrences = read_csv(OCCURRENCES)
    decisions = read_csv(DECISIONS)
    gates = read_csv(GATE)
    content_rules = read_csv(CONTENT_POLICY)

    if not gates:
        raise SystemExit("Learner-stage grammar-form quarantine is empty")
    if list(gates[0].keys()) != GATE_FIELDS:
        raise SystemExit(f"Unexpected grammar-form gate schema: {list(gates[0].keys())}")
    if not content_rules or list(content_rules[0].keys()) != CONTENT_POLICY_FIELDS:
        raise SystemExit("Learner content exclusion policy is missing or has unexpected schema")

    rule_keys: set[str] = set()
    for rule in content_rules:
        rkey = rule.get("RuleKey", "")
        if not rkey or rkey in rule_keys:
            raise SystemExit(f"Duplicate/empty learner content RuleKey: {rkey}")
        rule_keys.add(rkey)
        if rule.get("RuleType") not in {"canonical-exact", "number-lexeme-class"}:
            raise SystemExit(f"Unsupported learner content RuleType: {rkey}")
        if rule.get("PolicyVersion") != CONTENT_POLICY_VERSION:
            raise SystemExit(f"Learner content policy version drift: {rkey}")
        if not rule.get("ReasonCode", "").strip() or not rule.get("Rationale", "").strip():
            raise SystemExit(f"Learner content exclusion rule lacks audit metadata: {rkey}")

    occ_by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in occurrences:
        occ_by_match[row.get("MatchKey", "")].append(row)

    decision_by_key: dict[str, dict[str, str]] = {}
    decisions_by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decisions:
        dkey = row.get("DecisionKey", "")
        if not dkey or dkey in decision_by_key:
            raise SystemExit(f"Duplicate/empty DecisionKey: {dkey}")
        decision_by_key[dkey] = row
        decisions_by_match[row.get("MatchKey", "")].append(row)

    gate_keys: set[str] = set()
    for gate in gates:
        gkey = gate.get("GateKey", "")
        if not gkey or gkey in gate_keys:
            raise SystemExit(f"Duplicate/empty GateKey: {gkey}")
        gate_keys.add(gkey)
        key = gate.get("MatchKey", "")
        dkey = gate.get("DecisionKey", "")
        decision = decision_by_key.get(dkey)
        if key not in occ_by_match:
            raise SystemExit(f"Grammar-form gate references missing current MatchKey: {gkey} -> {key}")
        if decision is None or decision.get("MatchKey") != key:
            raise SystemExit(f"Grammar-form gate DecisionKey mismatch: {gkey} -> {dkey}")
        if gate.get("Scope") not in {"matchkey", "decision"}:
            raise SystemExit(f"Invalid grammar-form gate Scope: {gkey}")
        if gate.get("Scope") == "matchkey" and len(decisions_by_match[key]) != 1:
            raise SystemExit(
                f"MatchKey-scope grammar gate is unsafe for multipart/homograph surface: {gkey} -> {key}"
            )

    # Mutable learner copy keyed by canonical identity. Identity truth is untouched.
    rows_by_canonical: dict[str, dict[str, str]] = {
        row["CanonicalMatchKey"]: row for row in preview
    }
    if len(rows_by_canonical) != len(preview):
        raise SystemExit("Identity Preview CanonicalMatchKey is not unique")

    quarantine_rows: list[dict[str, object]] = []
    total_removed = 0

    for gate in gates:
        key = gate["MatchKey"]
        decision = decision_by_key[gate["DecisionKey"]]
        reviewed_keys = decode_occurrence_keys(decision.get("OccurrenceKeys", ""), decision["DecisionKey"])
        removed = 0

        if gate["Scope"] == "matchkey":
            hit_rows = [
                row for row in rows_by_canonical.values()
                if key in split_matchkeys(row.get("SourceMatchKeys", ""))
            ]
            if len(hit_rows) > 1:
                raise SystemExit(f"MatchKey-scope gate touches multiple learner identities: {gate['GateKey']}")
            if hit_rows:
                row = hit_rows[0]
                canonical = row["CanonicalMatchKey"]
                if decision.get("Action") == "keep-identity" and target_canonical(decision) == canonical:
                    removed = int(row.get("SourceOccurrenceCount", "0") or 0)
                    del rows_by_canonical[canonical]
                else:
                    matchkeys = split_matchkeys(row.get("SourceMatchKeys", ""))
                    matchkeys = [x for x in matchkeys if x != key]
                    contribution = len(occ_by_match[key])
                    new_count = int(row.get("SourceOccurrenceCount", "0") or 0) - contribution
                    if new_count < 0:
                        raise SystemExit(f"Negative learner occurrence count after gate: {gate['GateKey']}")
                    removed = contribution
                    if not matchkeys or new_count == 0:
                        del rows_by_canonical[canonical]
                    else:
                        row["SourceMatchKeys"] = "|".join(matchkeys)
                        row["SourceOccurrenceCount"] = str(new_count)
        else:
            canonical = target_canonical(decision)
            if canonical and canonical in rows_by_canonical:
                row = rows_by_canonical[canonical]
                matchkeys = split_matchkeys(row.get("SourceMatchKeys", ""))
                if key in matchkeys:
                    contribution = len(reviewed_keys)
                    if decision.get("Action") == "keep-identity" and canonical == row["CanonicalMatchKey"]:
                        removed = int(row.get("SourceOccurrenceCount", "0") or 0)
                        del rows_by_canonical[canonical]
                    else:
                        matchkeys = [x for x in matchkeys if x != key]
                        new_count = int(row.get("SourceOccurrenceCount", "0") or 0) - contribution
                        if new_count < 0:
                            raise SystemExit(f"Negative learner occurrence count after gate: {gate['GateKey']}")
                        removed = contribution
                        if not matchkeys or new_count == 0:
                            del rows_by_canonical[canonical]
                        else:
                            row["SourceMatchKeys"] = "|".join(matchkeys)
                            row["SourceOccurrenceCount"] = str(new_count)

        total_removed += removed
        quarantine_rows.append({
            "GateKey": gate["GateKey"],
            "MatchKey": key,
            "DecisionKey": gate["DecisionKey"],
            "BaseForm": gate["BaseForm"],
            "FormType": gate["FormType"],
            "Scope": gate["Scope"],
            "CurrentDecisionAction": decision.get("Action", ""),
            "CurrentDecisionStatus": decision.get("Status", ""),
            "CanonicalMatchKey": target_canonical(decision),
            "CurrentOccurrenceCount": len(occ_by_match[key]),
            "ReviewedOccurrenceCount": len(reviewed_keys),
            "PreviewContributionRemoved": removed,
            "PolicyVersion": gate["PolicyVersion"],
            "Rationale": gate["Rationale"],
        })

    # Apply content threshold policy at whole learner-identity scope. These identities
    # remain in the identity preview and remain available for Stage-B reconciliation.
    content_rows: list[dict[str, object]] = []
    for identity_row in preview:
        rule = content_rule_for(identity_row, content_rules)
        if rule is None:
            continue
        canonical = identity_row["CanonicalMatchKey"]
        removed = canonical in rows_by_canonical
        if removed:
            del rows_by_canonical[canonical]
        content_rows.append({
            "ProvisionalIdentityKey": identity_row.get("ProvisionalIdentityKey", ""),
            "CanonicalMatchKey": canonical,
            "DisplayWord": identity_row.get("DisplayWord", ""),
            "TargetSense": identity_row.get("TargetSense", ""),
            "MatchedRuleKey": rule.get("RuleKey", ""),
            "ReasonCode": rule.get("ReasonCode", ""),
            "PolicyVersion": rule.get("PolicyVersion", ""),
            "Rationale": rule.get("Rationale", ""),
            "LearnerIdentityRemoved": "yes" if removed else "already-removed-by-other-gate",
        })

    learner_rows = [rows_by_canonical[k] for k in sorted(rows_by_canonical)]
    write_csv(LEARNER_PREVIEW, PREVIEW_FIELDS, learner_rows)
    write_csv(QUARANTINE_VIEW, QUARANTINE_FIELDS, quarantine_rows)
    write_csv(CONTENT_VIEW, CONTENT_VIEW_FIELDS, content_rows)

    article_exclusions = sum(
        1 for row in content_rows if str(row.get("ReasonCode", "")) == "trivial-function-word"
    )
    number_exclusions = sum(
        1 for row in content_rows if str(row.get("ReasonCode", "")) == "trivial-number-word"
    )
    print(f"identity-level vocabulary preview = {len(preview)}")
    print(f"learner-stage vocabulary preview = {len(learner_rows)}")
    print(f"grammar-form quarantine gates = {len(gates)}")
    print(f"content-threshold exclusions = {len(content_rows)}")
    print(f"article exclusions = {article_exclusions}")
    print(f"number-identity exclusions = {number_exclusions}")
    print(f"identity rows suppressed by all learner gates = {len(preview) - len(learner_rows)}")
    print(f"grammar-gate occurrence contributions removed = {total_removed}")
    print("identity decisions mutated = no")
    print("source facts mutated = no")
    print("learner-stage gate separation = yes")


if __name__ == "__main__":
    main()
