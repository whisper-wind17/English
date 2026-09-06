#!/usr/bin/env python3
"""Apply a second-pass model review to Beijing + Renjiao exact-overlap rows.

This remains Stage A only. It upgrades clearly aligned elementary target senses
from pending to model-reviewed reuse, and explicitly preserves newly identified
semantic blockers. It never mints ThirdPartyID and never performs the Klose
final diff.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "anki" / "klose" / "third_party_vocabulary" / "staging" / "cross_source_identity_resolution.csv"

SAFE_REUSE = set("""
all also apple are arm around art at august autumn bad ball banana bear bed before behind between big bird birthday black blackboard blue boat body book box bread brother busy but buy
cake cap car card cat chair china chinese city class clock coat colour come country cow crayon cry
dance day desk dirty do doctor dog door drink
ear early east egg eight elephant eleven english evening excited eye face family father favourite fifth fifty film find first five floor flower foot for forest forget forty friday friend friendly fruit fun
garden gate girl go grandfather grandmother grass great green hair hand head he home horse hospital hot hotel house how hurt i ill in is jacket job juice king know lake late long look lost love lovely
man many map meet milk monday monkey mother mouth much my name near new nine no nose nurse ok old on one only orange panda paper park pen pencil people phone pig plane please quiet rabbit race red rice room ruler run sad safe saturday say school schoolbag season second seven she shirt shop short shorts sister ski skirt small snake snow sorry soup spring stamp station story street subject summer sure swim talk tall tea teach teacher thank that the thin thirty this three thursday tiger time tired to today together toilet tomorrow too toy travel tree tuesday twelfth twelve twenty two under use vacation vegetable want warm water weather wednesday west what when where why winter young your zoo
""".split())

EXPLICIT = {
    "cool": (
        "partial-overlap-split-required", "model-reviewed", "high",
        "temperature cool plus evaluative cool",
        "Beijing is temperature/weather; Renjiao contains both weather cool and evaluative 'cool/fantastic'. Occurrence-level split is required.",
    ),
    "call": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "The neighborhoods may target telephone/call or the verb call/name; current source ordering is insufficient for a safe single learning unit.",
    ),
    "dear": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "Dear as address term and adjective/sense variants are plausible; current list context is insufficient to collapse safely.",
    ),
    "earth": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "Earth as the planet and earth/ground are distinct learning units; current neighborhoods do not source-confirm one shared target sense.",
    ),
    "exercise": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "Exercise may be physical exercise or an exercise/task; current neighborhoods do not establish one target sense across occurrences.",
    ),
    "get": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "The verb get has multiple elementary constructions and senses; current source ordering is too weak to collapse them into one learning unit.",
    ),
    "stop": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "Stop as verb and stop as station/stop are both plausible; keep held until occurrence-level evidence is sufficient.",
    ),
    "there": (
        "held-identity-policy", "model-reviewed", "medium", "",
        "Locative there and existential there are pedagogically distinct usages; identity policy must decide whether to split before reuse.",
    ),
    "welcome": (
        "held-source-context-required", "model-reviewed", "medium", "",
        "Welcome as greeting/interjection and verb/adjective usage are both plausible from the current neighborhoods. Keep held.",
    ),
}

FIELDS = [
    "MatchKey", "DisplayForms", "Definitions", "BeijingContexts", "RenjiaoContexts",
    "RiskSignals", "ProposedDecision", "ResolutionStatus", "Confidence",
    "ProposedSense", "ResolutionBasis", "Rationale", "KloseMergeAuthorized",
]


def read_csv() -> list[dict[str, str]]:
    with PATH.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(rows: list[dict[str, str]]) -> None:
    with PATH.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    rows = read_csv()
    by_key = {r["MatchKey"]: r for r in rows}
    if len(rows) != 392 or len(by_key) != 392:
        raise SystemExit("Unexpected first-pass resolution baseline")

    missing = sorted((SAFE_REUSE | set(EXPLICIT)) - set(by_key))
    if missing:
        raise SystemExit(f"Second-pass keys missing from resolution: {missing}")

    for key in sorted(SAFE_REUSE):
        row = by_key[key]
        if row["ResolutionStatus"] != "pending" or row["ProposedDecision"] != "pending-semantic-review":
            raise SystemExit(
                f"Second-pass SAFE_REUSE expected pending row: {key} -> "
                f"{row['ResolutionStatus']} / {row['ProposedDecision']}"
            )
        row.update({
            "ProposedDecision": "reuse-learning-unit",
            "ResolutionStatus": "model-reviewed",
            "Confidence": "medium",
            "ProposedSense": "",
            "ResolutionBasis": "model-second-pass-source-neighborhood-review",
            "Rationale": (
                "Beijing and Renjiao neighborhoods align on the same elementary target sense; "
                "the earlier risk flag comes from broad dictionary gloss and/or repeated occurrences. "
                "This is Stage-A third-party reuse only, not a Klose merge authorization."
            ),
            "KloseMergeAuthorized": "no",
        })

    for key, (decision, status, confidence, sense, rationale) in EXPLICIT.items():
        row = by_key[key]
        if row["ResolutionStatus"] != "pending" or row["ProposedDecision"] != "pending-semantic-review":
            raise SystemExit(
                f"Second-pass EXPLICIT expected pending row: {key} -> "
                f"{row['ResolutionStatus']} / {row['ProposedDecision']}"
            )
        row.update({
            "ProposedDecision": decision,
            "ResolutionStatus": status,
            "Confidence": confidence,
            "ProposedSense": sense,
            "ResolutionBasis": "model-second-pass-source-neighborhood-review",
            "Rationale": rationale,
            "KloseMergeAuthorized": "no",
        })

    for row in rows:
        if row["KloseMergeAuthorized"] != "no":
            raise SystemExit(f"Unexpected Klose merge authorization: {row['MatchKey']}")

    write_csv(rows)
    statuses = Counter(r["ResolutionStatus"] for r in rows)
    decisions = Counter(r["ProposedDecision"] for r in rows)
    print(f"Second-pass safe reuse reviewed = {len(SAFE_REUSE)}")
    print(f"Second-pass explicit blockers = {len(EXPLICIT)}")
    for key in sorted(statuses):
        print(f"status {key} = {statuses[key]}")
    for key in sorted(decisions):
        print(f"decision {key} = {decisions[key]}")
    print("Stable ThirdPartyID minted = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
