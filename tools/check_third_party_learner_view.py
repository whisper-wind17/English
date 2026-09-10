#!/usr/bin/env python3
"""Independent checks for the third-party learner-stage vocabulary view."""
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

ALLOWED_FORM_TYPES = {"past-form", "past-or-past-participle", "modal-past-form"}
ALLOWED_SCOPES = {"matchkey", "decision"}
POLICY_VERSION = "klose-grammar-gate-v1"
CONTENT_POLICY_VERSION = "klose-content-exclusion-v1"
CONTENT_POLICY_FIELDS = [
    "RuleKey", "RuleType", "Value", "ReasonCode", "PolicyVersion", "Rationale",
]
CONTENT_VIEW_FIELDS = [
    "ProvisionalIdentityKey", "CanonicalMatchKey", "DisplayWord", "TargetSense",
    "MatchedRuleKey", "ReasonCode", "PolicyVersion", "Rationale",
    "LearnerIdentityRemoved",
]
PAST_MARKERS = (
    "过去式", "过去分词", "past tense", "past-tense", "past form", "past-form",
    "past participle", "past-participle", "past/participle", "past or past-participle",
)
LEXICALIZED_EXCEPTIONS = {"broken", "frightened", "lost", "worried", "tied", "surprised"}
NON_PAST_GUARDS = {"goes"}

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


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def decode_occurrence_keys(raw: str, decision_key: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid OccurrenceKeys JSON for {decision_key}: {exc}") from exc
    require(
        isinstance(value, list) and bool(value) and all(isinstance(x, str) and x for x in value),
        f"Invalid OccurrenceKeys for {decision_key}",
    )
    return value


def split_matchkeys(raw: str) -> list[str]:
    return [x for x in raw.split("|") if x]


def has_past_marker(text: str) -> bool:
    folded = text.casefold()
    return any(marker in folded for marker in PAST_MARKERS)


def decision_explicitly_self_identifies_past_form(decision: dict[str, str]) -> bool:
    if decision.get("Action") not in {"keep-identity", "reuse-identity"}:
        return False
    return has_past_marker(decision.get("TargetSense", "")) or has_past_marker(
        decision.get("DecisionBasis", "")
    )


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


def match_content_rule(
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
    require(
        len(matched) <= 1,
        f"Overlapping content exclusion rules: {row.get('ProvisionalIdentityKey', '')}: "
        f"{[r.get('RuleKey', '') for r in matched]}",
    )
    return matched[0] if matched else None


def main() -> None:
    occurrences = read_csv(OCCURRENCES)
    decisions = read_csv(DECISIONS)
    identity_preview = read_csv(IDENTITY_PREVIEW)
    gates = read_csv(GATE)
    learner_preview = read_csv(LEARNER_PREVIEW)
    quarantine = read_csv(QUARANTINE_VIEW)
    content_policy = read_csv(CONTENT_POLICY)
    content_view = read_csv(CONTENT_VIEW)

    occ_by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in occurrences:
        occ_by_match[row.get("MatchKey", "")].append(row)

    decisions_by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    decision_by_key: dict[str, dict[str, str]] = {}
    for row in decisions:
        dkey = row.get("DecisionKey", "")
        require(bool(dkey) and dkey not in decision_by_key, f"Duplicate/empty DecisionKey: {dkey}")
        decision_by_key[dkey] = row
        decisions_by_match[row.get("MatchKey", "")].append(row)

    gate_keys = [r.get("GateKey", "") for r in gates]
    require(all(gate_keys) and len(gate_keys) == len(set(gate_keys)), "Grammar-form GateKey must be unique")
    gate_by_decision: dict[str, dict[str, str]] = {}
    gated_matchkeys: set[str] = set()
    for gate in gates:
        gkey = gate["GateKey"]
        key = gate.get("MatchKey", "")
        dkey = gate.get("DecisionKey", "")
        require(key in occ_by_match, f"Gate references missing current MatchKey: {gkey} -> {key}")
        require(dkey in decision_by_key, f"Gate references missing DecisionKey: {gkey} -> {dkey}")
        require(decision_by_key[dkey].get("MatchKey") == key, f"Gate DecisionKey/MatchKey mismatch: {gkey}")
        require(gate.get("FormType") in ALLOWED_FORM_TYPES, f"Invalid FormType: {gkey}")
        require(gate.get("Scope") in ALLOWED_SCOPES, f"Invalid Scope: {gkey}")
        require(gate.get("PolicyVersion") == POLICY_VERSION, f"Grammar gate policy version drift: {gkey}")
        require(bool(gate.get("BaseForm", "").strip()), f"Grammar gate lacks BaseForm: {gkey}")
        require(dkey not in gate_by_decision, f"DecisionKey has multiple grammar gates: {dkey}")
        if gate["Scope"] == "matchkey":
            require(len(decisions_by_match[key]) == 1,
                    f"Multipart/homograph MatchKey must use decision-scoped gate: {gkey} -> {key}")
        else:
            require(len(decisions_by_match[key]) > 1,
                    f"Decision-scoped gate should be reserved for multipart/homograph surface: {gkey}")
        gate_by_decision[dkey] = gate
        gated_matchkeys.add(key)

    explicit_past_decisions = {
        dkey
        for dkey, decision in decision_by_key.items()
        if " " not in decision.get("MatchKey", "")
        and decision_explicitly_self_identifies_past_form(decision)
    }
    missing_decision_gates = sorted(explicit_past_decisions - set(gate_by_decision))
    require(
        not missing_decision_gates,
        f"Reviewed one-word past-form decisions lack learner-stage gate: {missing_decision_gates[:30]}",
    )

    require(not (LEXICALIZED_EXCEPTIONS & gated_matchkeys),
            f"Lexicalized adjective/noun exception was incorrectly grammar-gated: {sorted(LEXICALIZED_EXCEPTIONS & gated_matchkeys)}")
    require(not (NON_PAST_GUARDS & gated_matchkeys),
            f"Non-past form was incorrectly grammar-gated: {sorted(NON_PAST_GUARDS & gated_matchkeys)}")

    quarantine_keys = [r.get("GateKey", "") for r in quarantine]
    require(quarantine_keys == gate_keys, "Generated grammar quarantine view does not exactly match gate registry order/set")

    # Independent content-threshold policy validation.
    require(bool(content_policy), "Learner content exclusion policy is empty")
    require(list(content_policy[0].keys()) == CONTENT_POLICY_FIELDS, "Content exclusion policy schema drift")
    policy_keys = [r.get("RuleKey", "") for r in content_policy]
    require(all(policy_keys) and len(policy_keys) == len(set(policy_keys)), "Content exclusion RuleKey must be unique")
    require(
        set(policy_keys) == {"article:a", "article:an", "article:the"},
        f"Content exclusion policy set drift: {policy_keys}",
    )
    for rule in content_policy:
        require(rule.get("RuleType") in {"canonical-exact", "number-lexeme-class"},
                f"Unsupported content exclusion RuleType: {rule.get('RuleKey')}")
        require(rule.get("PolicyVersion") == CONTENT_POLICY_VERSION,
                f"Content exclusion policy version drift: {rule.get('RuleKey')}")
        require(bool(rule.get("ReasonCode", "").strip()) and bool(rule.get("Rationale", "").strip()),
                f"Content exclusion policy lacks audit metadata: {rule.get('RuleKey')}")

    require(
        not content_view or list(content_view[0].keys()) == CONTENT_VIEW_FIELDS,
        "Content exclusion view schema drift",
    )
    identity_by_pid = {r.get("ProvisionalIdentityKey", ""): r for r in identity_preview}
    require(len(identity_by_pid) == len(identity_preview) and "" not in identity_by_pid,
            "Identity Preview ProvisionalIdentityKey is empty/duplicate")
    expected_content: dict[str, dict[str, str]] = {}
    for row in identity_preview:
        rule = match_content_rule(row, content_policy)
        if rule is not None:
            expected_content[row["ProvisionalIdentityKey"]] = rule

    content_pids = [r.get("ProvisionalIdentityKey", "") for r in content_view]
    require(all(content_pids) and len(content_pids) == len(set(content_pids)),
            "Content exclusion view ProvisionalIdentityKey is empty/duplicate")
    require(set(content_pids) == set(expected_content),
            "Content exclusion view does not exactly close over current policy matches")
    for row in content_view:
        pid = row["ProvisionalIdentityKey"]
        identity = identity_by_pid[pid]
        rule = expected_content[pid]
        require(row.get("CanonicalMatchKey") == identity.get("CanonicalMatchKey"),
                f"Content exclusion canonical drift: {pid}")
        require(row.get("MatchedRuleKey") == rule.get("RuleKey"),
                f"Content exclusion rule drift: {pid}")
        require(row.get("ReasonCode") == rule.get("ReasonCode"),
                f"Content exclusion reason drift: {pid}")
        require(row.get("PolicyVersion") == CONTENT_POLICY_VERSION,
                f"Content exclusion view policy version drift: {pid}")
        require(row.get("LearnerIdentityRemoved") in {"yes", "already-removed-by-other-gate"},
                f"Invalid content exclusion removal state: {pid}")

    identity_by_canonical = {r.get("CanonicalMatchKey", ""): r for r in identity_preview}
    learner_by_canonical = {r.get("CanonicalMatchKey", ""): r for r in learner_preview}
    require(len(identity_by_canonical) == len(identity_preview), "Identity Preview canonical key is not unique")
    require(len(learner_by_canonical) == len(learner_preview), "Learner Preview canonical key is not unique")
    require(set(learner_by_canonical) <= set(identity_by_canonical), "Learner Preview invented a new identity")
    require(all(r.get("TargetSense", "").strip() for r in learner_preview), "Learner Preview contains empty TargetSense")

    excluded_canonicals = {identity_by_pid[pid]["CanonicalMatchKey"] for pid in expected_content}
    require(not (excluded_canonicals & set(learner_by_canonical)),
            f"Content-excluded identity leaked into learner preview: {sorted(excluded_canonicals & set(learner_by_canonical))[:20]}")
    require({"a", "an", "the"} <= excluded_canonicals,
            "Required article exclusions a/an/the are not all present at identity level")

    # Current learner policy admits elementary cardinal/ordinal identities. The classifier is
    # retained only as an independent adversarial detector, not as an exclusion rule.
    number_identity_canonicals = {
        canonical for canonical in identity_by_canonical if is_elementary_number_identity(canonical)
    }
    require(not (number_identity_canonicals & excluded_canonicals),
            f"Admitted number identity was content-excluded: {sorted(number_identity_canonicals & excluded_canonicals)[:20]}")
    missing_number_admissions = sorted(number_identity_canonicals - set(learner_by_canonical))
    require(not missing_number_admissions,
            f"Elementary number identities missing from learner preview: {missing_number_admissions[:20]}")

    # Adversarial guards: ordinary concepts/phrases containing number-like tokens stay distinct.
    for guard in ("number", "phone number", "one day"):
        if guard in identity_by_canonical:
            require(guard not in excluded_canonicals,
                    f"Non-number-learning-unit was over-excluded: {guard}")

    for canonical, learner_row in learner_by_canonical.items():
        identity_row = identity_by_canonical[canonical]
        require(learner_row.get("DisplayWord") == identity_row.get("DisplayWord"),
                f"Learner gate changed DisplayWord: {canonical}")
        require(learner_row.get("TargetSense") == identity_row.get("TargetSense"),
                f"Learner gate changed TargetSense: {canonical}")
        require(int(learner_row.get("SourceOccurrenceCount", "0") or 0)
                <= int(identity_row.get("SourceOccurrenceCount", "0") or 0),
                f"Learner gate increased provenance count: {canonical}")

    learner_rows_containing: dict[str, list[str]] = defaultdict(list)
    for row in learner_preview:
        for key in split_matchkeys(row.get("SourceMatchKeys", "")):
            learner_rows_containing[key].append(row["CanonicalMatchKey"])

    for gate in gates:
        key = gate["MatchKey"]
        decision = decision_by_key[gate["DecisionKey"]]
        if gate["Scope"] == "matchkey":
            require(not learner_rows_containing.get(key),
                    f"Grammar-gated MatchKey leaked into learner preview: {gate['GateKey']} -> {learner_rows_containing.get(key)}")
        else:
            action = decision.get("Action", "")
            if action == "reuse-identity":
                canonical = decision.get("CanonicalMatchKey", "")
            elif action == "keep-identity":
                canonical = decision.get("CanonicalMatchKey", "") or key
            else:
                canonical = ""
            if canonical in learner_by_canonical:
                require(key not in split_matchkeys(learner_by_canonical[canonical].get("SourceMatchKeys", "")),
                        f"Decision-scoped past partition leaked into target learner identity: {gate['GateKey']} -> {canonical}")

    for gate in gates:
        d = decision_by_key[gate["DecisionKey"]]
        require(d.get("Action") in {"keep-identity", "reuse-identity", "source-only"},
                f"Grammar gate attached to unresolved/non-identity decision: {gate['GateKey']}")
        decode_occurrence_keys(d.get("OccurrenceKeys", ""), d["DecisionKey"])

    article_count = sum(1 for r in content_view if r.get("ReasonCode") == "trivial-function-word")
    number_count = sum(1 for r in content_view if r.get("ReasonCode") == "trivial-number-word")
    require(article_count == 3, f"Expected exactly 3 article exclusions, got {article_count}")
    require(number_count == 0, f"Elementary number identities must be admitted, but {number_count} remain excluded")

    print("Third-party learner-stage gates = pass")
    print(f"identity-level vocabulary preview = {len(identity_preview)}")
    print(f"learner-stage vocabulary preview = {len(learner_preview)}")
    print(f"grammar-form quarantine gates = {len(gates)}")
    print(f"explicit decision-bound past-form requirements = {len(explicit_past_decisions)}")
    print(f"content-threshold exclusions = {len(content_view)}")
    print(f"article exclusions = {article_count}")
    print(f"number-identity exclusions = {number_count}")
    print(f"number identities admitted = {len(number_identity_canonicals)}")
    print("past-form leak into learner preview = no")
    print("content-exclusion leak into learner preview = no")
    print("number learner admission = pass")
    print("identity truth mutated by learner gates = no")
    print("source truth mutated by learner gates = no")


if __name__ == "__main__":
    main()
