#!/usr/bin/env python3
"""Audit morphology/form risk among Renjiao single-token Vocabulary candidates.

A surface can be semantically unambiguous and still be the wrong Identity unit
(e.g. danced, slept, swam, were, won). This audit is intentionally downstream
of semantic review and upstream of ThirdPartyID minting.

Stage A only: no stable identity minting and no Klose final diff.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
STAGING = BASE / "third_party_vocabulary" / "staging"
ROUTING = STAGING / "renjiao_new_surface_route_resolution.csv"
SURFACE_INDEX = STAGING / "surface_index.csv"
OUTPUT = STAGING / "renjiao_single_token_form_audit.csv"

FIELDS = [
    "MatchKey", "DisplayForms", "Definitions", "Books", "Contexts",
    "CurrentDecision", "CurrentStatus", "FormClass", "BaseMatchKey",
    "BaseExistsInThirdParty", "ProposedFormDecision", "DecisionStatus",
    "Confidence", "Rationale", "KloseMergeAuthorized",
]

IRREGULAR_FORMS = {
    "slept": "sleep",
    "swam": "swim",
    "were": "be",
    "won": "win",
}

REGULAR_FORMS = {
    "danced": "dance",
    "does": "do",
    "cartoons": "cartoon",
    "gloves": "glove",
}

LEXICALIZED_DERIVED = {
    "broken": ("break", "adjective/participle lexical target ('broken' = damaged/broken) is plausible in the source neighborhood"),
    "amazing": ("amaze", "adjective target ('amazing' =令人惊异的) is lexicalized for elementary learning"),
    "boring": ("bore", "adjective target ('boring' =无聊的/令人厌烦的) is explicit in the source neighborhood"),
    "scared": ("scare", "adjective target ('scared' =害怕的) is explicit in the emotions/adjectives neighborhood"),
}

LEXICALIZED_FORM_SURFACES = {
    "crossroads": ("crossroad", "The directions/location context teaches lexical crossroads='十字路口'; treat the surface as a stable learning item rather than mechanically singularizing it."),
    "scissors": ("scissor", "Scissors is a pluralia-tantum lexical noun for the classroom object; do not collapse it to verb/noun 'scissor'."),
}

ACTIVITY_ING_FORMS = {
    "dancing": "dance",
    "reading": "read",
    "running": "run",
    "singing": "sing",
    "skateboarding": "skateboard",
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


def explicit_base_from_definition(definition: str) -> str:
    text = definition or ""
    patterns = [
        r"([A-Za-z][A-Za-z-]*)的过去式(?:和过去分词)?",
        r"([A-Za-z][A-Za-z-]*)的过去分词",
        r"([A-Za-z][A-Za-z-]*)的ing形式",
        r"([A-Za-z][A-Za-z-]*)的现在分词",
        r"([A-Za-z][A-Za-z-]*)的复数(?:形式)?",
        r"([A-Za-z][A-Za-z-]*)的第三人称单数(?:形式)?",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return m.group(1).lower()
    return ""


def main() -> None:
    routing = read_csv(ROUTING)
    surfaces = {r["MatchKey"] for r in read_csv(SURFACE_INDEX)}
    by_key = {r["MatchKey"]: r for r in routing}
    if len(routing) != 403 or len(by_key) != 403:
        raise SystemExit("Unexpected Renjiao routing baseline")

    candidates = [
        r for r in routing
        if r["CandidateType"] == "single-token-lexical-review"
        and r["ProposedObjectDecision"] == "new-vocabulary-learning-unit-candidate"
    ]

    out: list[dict[str, str]] = []
    for row in candidates:
        key = row["MatchKey"]
        explicit_base = explicit_base_from_definition(row["Definitions"])
        form_class = base = decision = status = confidence = rationale = ""

        if key in IRREGULAR_FORMS:
            form_class = "irregular-inflection"
            base = IRREGULAR_FORMS[key]
            decision = "held-irregular-form-policy"
            status = "model-reviewed"
            confidence = "high"
            rationale = "Irregular inflected form is pedagogically salient; link to its base but do not collapse identity until the third-party form policy is frozen."
        elif key in REGULAR_FORMS:
            form_class = "regular-inflection"
            base = REGULAR_FORMS[key]
            decision = "reuse-base-learning-unit-candidate"
            status = "model-reviewed"
            confidence = "high"
            rationale = "Regular inflection carries the same lexical target as the base; preserve the source form as provenance/presentation evidence instead of minting a second lexical identity."
        elif key in LEXICALIZED_DERIVED:
            base, why = LEXICALIZED_DERIVED[key]
            form_class = "derived-or-participial-lexical-target"
            decision = "keep-distinct-learning-unit-candidate"
            status = "model-reviewed"
            confidence = "high"
            rationale = why + "; morphology relation alone must not collapse the target learning unit."
        elif key in LEXICALIZED_FORM_SURFACES:
            base, why = LEXICALIZED_FORM_SURFACES[key]
            form_class = "lexicalized-form-surface"
            decision = "keep-distinct-learning-unit-candidate"
            status = "model-reviewed"
            confidence = "high"
            rationale = why
        elif key in ACTIVITY_ING_FORMS:
            form_class = "activity-gerund-or-noun"
            base = ACTIVITY_ING_FORMS[key]
            decision = "held-derived-form-identity-policy"
            status = "model-reviewed"
            confidence = "medium"
            rationale = "The source teaches this -ing form in an activity/hobby slot. It may be a lexical activity noun rather than a mere inflection; keep held until the form/learning-unit policy decides the boundary."
        elif explicit_base and explicit_base != key:
            form_class = "explicit-form-relation-unreviewed"
            base = explicit_base
            decision = "pending-form-review"
            status = "pending"
            rationale = "Dictionary gloss explicitly states a morphology relation to another base form. This candidate must not mint a stable identity until reviewed."
        else:
            continue

        out.append({
            "MatchKey": key,
            "DisplayForms": row["DisplayForms"],
            "Definitions": row["Definitions"],
            "Books": row["Books"],
            "Contexts": row["Contexts"],
            "CurrentDecision": row["ProposedObjectDecision"],
            "CurrentStatus": row["ResolutionStatus"],
            "FormClass": form_class,
            "BaseMatchKey": base,
            "BaseExistsInThirdParty": "yes" if base in surfaces else "no",
            "ProposedFormDecision": decision,
            "DecisionStatus": status,
            "Confidence": confidence,
            "Rationale": rationale,
            "KloseMergeAuthorized": "no",
        })

    out.sort(key=lambda r: r["MatchKey"])
    write_csv(OUTPUT, out)

    counts = Counter(r["ProposedFormDecision"] for r in out)
    print(f"Renjiao single-token form audit rows = {len(out)}")
    for key in sorted(counts):
        print(f"decision {key} = {counts[key]}")
    pending = [r["MatchKey"] for r in out if r["DecisionStatus"] == "pending"]
    print("pending form review keys = " + ("|".join(pending) if pending else "none"))
    print("ThirdPartyID minted = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
