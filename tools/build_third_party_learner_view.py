#!/usr/bin/env python3
"""Build the Klose learner-stage view of the third-party Stage-A corpus.

Identity resolution and learner admission are intentionally separate layers.
`staging/unified_vocabulary_preview.csv` remains the identity-level Stage-A view.
`learner/grammar_form_quarantine.csv` is the durable learner-stage gate for forms
that are correctly resolved at the identity layer but are not appropriate for
Klose's current grammar stage (currently past/past-participle forms).

The derived learner view removes only gated contributions. Decision-scoped gates
allow a homographic surface such as `left` or `saw` to quarantine only the past-form
partition while preserving other lexical identities of the same surface.
"""
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


def main() -> None:
    preview = [dict(r) for r in read_csv(IDENTITY_PREVIEW)]
    occurrences = read_csv(OCCURRENCES)
    decisions = read_csv(DECISIONS)
    gates = read_csv(GATE)

    if not gates:
        raise SystemExit("Learner-stage grammar-form quarantine is empty")
    if list(gates[0].keys()) != GATE_FIELDS:
        raise SystemExit(f"Unexpected grammar-form gate schema: {list(gates[0].keys())}")

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

    # Mutable learner copy keyed by canonical identity. The identity-level preview
    # remains untouched; only this derived learner view is changed.
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
            # A pure single-decision form may appear in at most one identity row.
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
                    # The canonical identity itself is a grammar-form learning unit.
                    # Suppress the whole learner identity, including aliases that may
                    # have been attached to it at the identity layer.
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
            # source-only / expression decisions already contribute nothing to the
            # identity preview; they may still be retained in the quarantine audit.
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

    learner_rows = [rows_by_canonical[k] for k in sorted(rows_by_canonical)]
    write_csv(LEARNER_PREVIEW, PREVIEW_FIELDS, learner_rows)
    write_csv(QUARANTINE_VIEW, QUARANTINE_FIELDS, quarantine_rows)

    print(f"identity-level vocabulary preview = {len(preview)}")
    print(f"learner-stage vocabulary preview = {len(learner_rows)}")
    print(f"grammar-form quarantine gates = {len(gates)}")
    print(f"identity rows suppressed by learner gate = {len(preview) - len(learner_rows)}")
    print(f"preview occurrence contributions removed = {total_removed}")
    print("identity decisions mutated = no")
    print("learner-stage gate separation = yes")


if __name__ == "__main__":
    main()
