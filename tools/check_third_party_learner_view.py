#!/usr/bin/env python3
"""Independent checks for the third-party learner-stage vocabulary view."""
from __future__ import annotations

import csv
import json
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

ALLOWED_FORM_TYPES = {"past-form", "past-or-past-participle", "modal-past-form"}
ALLOWED_SCOPES = {"matchkey", "decision"}
POLICY_VERSION = "klose-grammar-gate-v1"
PAST_MARKERS = (
    "过去式", "过去分词", "past tense", "past-tense", "past form", "past-form",
    "past participle", "past-participle", "past/participle", "past or past-participle",
)
LEXICALIZED_EXCEPTIONS = {"broken", "frightened", "lost", "worried", "tied", "surprised"}
NON_PAST_GUARDS = {"goes"}


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
    """Return true only for decision metadata that classifies *this* learning unit.

    Source definitions and free-form rationale are deliberately excluded. They can
    mention morphology of another surface (for example canonical `win` discussing
    `won`) or dictionary noise (for example noun `ground` mentioning grind forms).
    TargetSense and DecisionBasis are the narrow, decision-bound fields safe enough
    for a fail-closed coverage check.
    """
    if decision.get("Action") not in {"keep-identity", "reuse-identity"}:
        return False
    return has_past_marker(decision.get("TargetSense", "")) or has_past_marker(
        decision.get("DecisionBasis", "")
    )


def main() -> None:
    occurrences = read_csv(OCCURRENCES)
    decisions = read_csv(DECISIONS)
    identity_preview = read_csv(IDENTITY_PREVIEW)
    gates = read_csv(GATE)
    learner_preview = read_csv(LEARNER_PREVIEW)
    quarantine = read_csv(QUARANTINE_VIEW)

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

    # Fail closed only when durable decision metadata explicitly says that the
    # decision itself is a past/past-participle learning unit. Broad source glosses
    # are evidence, not a reliable machine grammar classifier; using them here caused
    # false positives such as go/hold/party/ground and would silently encode dictionary
    # noise as learner policy.
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

    identity_by_canonical = {r.get("CanonicalMatchKey", ""): r for r in identity_preview}
    learner_by_canonical = {r.get("CanonicalMatchKey", ""): r for r in learner_preview}
    require(len(identity_by_canonical) == len(identity_preview), "Identity Preview canonical key is not unique")
    require(len(learner_by_canonical) == len(learner_preview), "Learner Preview canonical key is not unique")
    require(set(learner_by_canonical) <= set(identity_by_canonical), "Learner Preview invented a new identity")
    require(all(r.get("TargetSense", "").strip() for r in learner_preview), "Learner Preview contains empty TargetSense")

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

    # Core identity truth must still retain resolved form relations. The learner gate
    # is a presentation/admission filter, not a rewrite of identity_decisions.csv.
    for gate in gates:
        d = decision_by_key[gate["DecisionKey"]]
        require(d.get("Action") in {"keep-identity", "reuse-identity", "source-only"},
                f"Grammar gate attached to unresolved/non-identity decision: {gate['GateKey']}")
        decode_occurrence_keys(d.get("OccurrenceKeys", ""), d["DecisionKey"])

    print("Third-party learner-stage grammar-form quarantine = pass")
    print(f"identity-level vocabulary preview = {len(identity_preview)}")
    print(f"learner-stage vocabulary preview = {len(learner_preview)}")
    print(f"grammar-form quarantine gates = {len(gates)}")
    print(f"explicit decision-bound past-form requirements = {len(explicit_past_decisions)}")
    print("past-form leak into learner preview = no")
    print("lexicalized participle/adjective over-gating = no")
    print("homograph decision-scope gate = enforced")
    print("source-definition heuristic used as identity truth = no")
    print("identity truth mutated by learner gate = no")


if __name__ == "__main__":
    main()
