#!/usr/bin/env python3
"""Prepare NCE1 -> Stable Vocabulary identity reconciliation candidates.

This is analysis-only: it never allocates NoteIDs or confirms mappings.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from klose_nce1_source import read_xlsx_lexicon

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
SOURCE = BASE / "source_reference" / "new_concept_english_1_staging" / "vocabulary-smart-2022.csv"
LEGACY = BASE / "master" / "note_registry.csv"
EXT = BASE / "master" / "note_registry_extensions.csv"
OUT_DIR = BASE / "review" / "nce1_reconciliation"
OUT = OUT_DIR / "identity_candidates.csv"
STATUS = OUT_DIR / "status.json"

FIELDS = [
    "SourceItemKey", "CurriculumOrder", "LessonStart", "LessonEnd", "Entry",
    "PartOfSpeech", "Meaning", "SourceStatus", "LexiconWord", "British", "American",
    "DefinitionRaw", "ExactCandidateNoteIDs", "ExactCandidateSenses", "ResolutionLane",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", value.strip()).casefold()


def source_key(row: dict[str, str]) -> str:
    return f"nce1-o{int(row['CurriculumOrder']):04d}|{norm(row['Entry'])}"


def lexicon_candidates(entry: str) -> list[str]:
    key = norm(entry)
    candidates = [key]
    aliases = {
        "south korean": ["korean"],
        "sales rep": ["sales reps"],
        "instalment": ["installment"],
    }
    candidates.extend(aliases.get(key, []))
    if key.endswith("."):
        candidates.append(key[:-1])
    return list(dict.fromkeys(candidates))


def main() -> None:
    for path in (SOURCE, LEGACY, EXT):
        if not path.exists():
            raise SystemExit(f"Missing NCE1 reconciliation input: {path.relative_to(ROOT)}")

    source = read_csv(SOURCE)
    registry = [
        r for r in [*read_csv(LEGACY), *read_csv(EXT)]
        if r.get("Status", "").strip() == "active"
    ]
    by_surface: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in registry:
        by_surface[norm(row.get("CanonicalWord", ""))].append(row)

    lexicon = read_xlsx_lexicon()
    rows: list[dict[str, str]] = []
    lanes: Counter[str] = Counter()
    lexicon_missing: list[str] = []

    for src in source:
        entry = src["Entry"].strip()
        exact = by_surface.get(norm(entry), [])
        lex_rows: list[dict[str, str]] = []
        for candidate in lexicon_candidates(entry):
            if candidate in lexicon:
                lex_rows = lexicon[candidate]
                break
        if not lex_rows:
            lexicon_missing.append(entry)
        lex_word = " || ".join(dict.fromkeys(r["Word"] for r in lex_rows))
        british = " || ".join(dict.fromkeys(r["British"] for r in lex_rows if r["British"]))
        american = " || ".join(dict.fromkeys(r["American"] for r in lex_rows if r["American"]))
        definitions = " ||| ".join(dict.fromkeys(r["DefinitionRaw"].replace("\\r\\n", "\\n") for r in lex_rows if r["DefinitionRaw"]))

        actual = src.get("SourceStatus", "") == "verified-actual"
        if len(exact) == 0:
            lane = "actual-new-candidate" if actual else "baseline-new-candidate"
        elif len(exact) == 1:
            lane = "actual-exact-single-review" if actual else "baseline-exact-single-review"
        else:
            lane = "actual-multi-sense-review" if actual else "baseline-multi-sense-review"
        lanes[lane] += 1
        rows.append({
            "SourceItemKey": source_key(src),
            "CurriculumOrder": src["CurriculumOrder"],
            "LessonStart": src["LessonStart"],
            "LessonEnd": src["LessonEnd"],
            "Entry": entry,
            "PartOfSpeech": src.get("PartOfSpeech", ""),
            "Meaning": src.get("Meaning", ""),
            "SourceStatus": src.get("SourceStatus", ""),
            "LexiconWord": lex_word,
            "British": british,
            "American": american,
            "DefinitionRaw": definitions,
            "ExactCandidateNoteIDs": " || ".join(r["NoteID"].strip() for r in exact),
            "ExactCandidateSenses": " || ".join(r["SenseLabel"].strip() for r in exact),
            "ResolutionLane": lane,
        })

    write_csv(OUT, rows)
    status = {
        "schema_version": 1,
        "source_occurrences": len(source),
        "candidate_rows": len(rows),
        "unique_source_surfaces": len({norm(r["Entry"]) for r in source}),
        "lanes": dict(sorted(lanes.items())),
        "xlsx_lexicon_unique_surfaces": len(lexicon),
        "xlsx_lexicon_rows": sum(len(v) for v in lexicon.values()),
        "xlsx_lexicon_missing_occurrences": len(lexicon_missing),
        "xlsx_lexicon_missing_unique": sorted(set(lexicon_missing), key=norm),
        "decision_state": "prepared-not-allocated",
    }
    from klose_nce1_state import reviewed_state
    _, reviewed, new_notes = reviewed_state()
    status.update(decision_state="partially-reviewed-and-allocated", reviewed_occurrences=len(reviewed),
                  allocated_new_notes=len(new_notes), pending_occurrences=len(source)-len(reviewed))
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "NCE1 reconciliation prepared: "
        f"source={len(source)}, unique={status['unique_source_surfaces']}, "
        f"lexicon_rows={sum(len(v) for v in lexicon.values())}, lexicon_surfaces={len(lexicon)}, "
        f"missing_lexicon={len(set(lexicon_missing))}, lanes={dict(sorted(lanes.items()))}"
    )


if __name__ == "__main__":
    main()
