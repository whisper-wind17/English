#!/usr/bin/env python3
"""Build reviewable Grade 5-6 lexical-fact (IPA) backfill candidates.

This is deliberately conservative. Identity and meaning come from Klose's actual-
textbook reconciliation. We only reuse UK/US IPA from already-ingested repo sources
when an English form matches exactly after Unicode/case/whitespace normalization.
Conflicting IPA pairs remain unresolved instead of being guessed.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KLOSE = ROOT / "anki" / "klose"
REG_EXT = KLOSE / "master" / "note_registry_extensions.csv"
SOURCE_ROOT = KLOSE / "source_reference"
LEGACY_MASTER = ROOT / "anki" / "人教版一年级起点" / "master" / "vocabulary_master.csv"
OUT = KLOSE / "review" / "grade5_6_lexical_facts"
CANDIDATES = OUT / "ipa_candidates.csv"
MISSING = OUT / "ipa_unresolved.csv"
STATUS = OUT / "status.json"
CREATED_SOURCE = "klose-grade5-6-current"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'")
    value = re.sub(r"\s+", " ", value.strip()).casefold()
    return value


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def clean_ipa(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def main() -> None:
    active = [
        r for r in read_csv(REG_EXT)
        if r.get("CreatedSource", "").strip() == CREATED_SOURCE
        and r.get("Status", "").strip() == "active"
    ]
    if len(active) != 288:
        raise SystemExit(f"Expected 288 active Grade 5-6 new identities, got {len(active)}")

    # form -> {(British, American): {source labels}}
    facts: dict[str, dict[tuple[str, str], set[str]]] = defaultdict(lambda: defaultdict(set))

    if LEGACY_MASTER.exists():
        for row in read_csv(LEGACY_MASTER):
            key = norm(row.get("Word", ""))
            uk, us = clean_ipa(row.get("British", "")), clean_ipa(row.get("American", ""))
            if key and uk and us:
                facts[key][(uk, us)].add("legacy:rj_start1-master")

    source_files = sorted(SOURCE_ROOT.glob("*_staging/occurrences.csv"))
    for path in source_files:
        label = f"staging:{path.parent.name}"
        for row in read_csv(path):
            key = norm(row.get("MatchKey") or row.get("Word", ""))
            uk, us = clean_ipa(row.get("British", "")), clean_ipa(row.get("American", ""))
            if key and uk and us:
                facts[key][(uk, us)].add(label)

    candidates: list[dict[str, str]] = []
    unresolved: list[dict[str, str]] = []
    resolved = conflicts = missing = 0

    for row in sorted(active, key=lambda r: int(r["NoteID"].removeprefix("KV"))):
        nid = row["NoteID"].strip()
        canonical = row.get("CanonicalWord", "").strip()
        match_key = row.get("MatchKey", "").strip()
        sense = row.get("SenseLabel", "").strip()
        keys = []
        for value in (match_key, canonical):
            k = norm(value)
            if k and k not in keys:
                keys.append(k)
        # Conservative alias for ordinal display forms such as "fourth (4th)".
        simple = re.sub(r"\s*\([^)]*\)\s*$", "", canonical).strip()
        simple_key = norm(simple)
        if simple_key and simple_key not in keys:
            keys.append(simple_key)

        merged: dict[tuple[str, str], set[str]] = defaultdict(set)
        matched_keys: set[str] = set()
        for key in keys:
            for pair, sources in facts.get(key, {}).items():
                merged[pair].update(sources)
                matched_keys.add(key)

        if len(merged) == 1:
            (uk, us), sources = next(iter(merged.items()))
            candidates.append({
                "NoteID": nid,
                "CanonicalWord": canonical,
                "SenseLabel": sense,
                "British": uk,
                "American": us,
                "MatchBasis": "|".join(sorted(matched_keys)),
                "EvidenceSources": "|".join(sorted(sources)),
                "Resolution": "auto-exact-unanimous",
            })
            resolved += 1
        else:
            if merged:
                conflicts += 1
                detail = " || ".join(
                    f"{uk} / {us} <= {'|'.join(sorted(srcs))}"
                    for (uk, us), srcs in sorted(merged.items())
                )
                reason = "conflicting-exact-ipa"
            else:
                missing += 1
                detail = ""
                reason = "no-exact-ipa-in-repo"
            unresolved.append({
                "NoteID": nid,
                "CanonicalWord": canonical,
                "SenseLabel": sense,
                "LookupKeys": "|".join(keys),
                "Reason": reason,
                "Evidence": detail,
            })

    if resolved + conflicts + missing != len(active):
        raise SystemExit("IPA coverage partition does not close")

    write_csv(
        CANDIDATES,
        ["NoteID", "CanonicalWord", "SenseLabel", "British", "American", "MatchBasis", "EvidenceSources", "Resolution"],
        candidates,
    )
    write_csv(
        MISSING,
        ["NoteID", "CanonicalWord", "SenseLabel", "LookupKeys", "Reason", "Evidence"],
        unresolved,
    )
    status = {
        "ActiveGrade56NewIdentities": len(active),
        "RepoIPASourceFiles": 1 + len(source_files),
        "AutoResolvedExactUnanimous": resolved,
        "ConflictingExactIPA": conflicts,
        "NoExactIPAInRepo": missing,
        "Unresolved": len(unresolved),
        "MasterMutation": False,
        "LearnerMutation": False,
        "ReleaseMutation": False,
        "AnkiMutation": False,
    }
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
