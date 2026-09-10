#!/usr/bin/env python3
"""Build review-only Grade 5–6 actual-textbook -> Klose Vocabulary candidates.

This planner is intentionally non-mutating with respect to Stable NoteID truth.
Exact MatchKey equality is candidate evidence only, never an automatic reuse decision.
Explicit textbook inflections are routed to morphology-only before lexical matching.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
SOURCE = BASE / "source_reference" / "klose-actual-grade5-6-vocabulary.csv"
MORPH = BASE / "source_reference" / "klose-actual-grade5-6-morphology.csv"
REGISTRIES = [
    BASE / "master" / "note_registry.csv",
    BASE / "master" / "note_registry_extensions.csv",
]
OUT_DIR = BASE / "review" / "grade5_6_reconciliation"
OUT = OUT_DIR / "vocabulary_candidates.csv"
SUMMARY = OUT_DIR / "vocabulary_status.json"

FIELDS = [
    "ProvisionalIdentityKey", "OccurrenceKeys", "OccurrenceCount",
    "GradeSemesters", "Units", "Pages", "Entry", "Meaning", "MatchKey",
    "SourceMeaningVariants", "SourceSurfaceMultiplicity",
    "CandidateClass", "ExistingNoteCount", "ExistingCandidates",
    "VariantCandidates", "MorphologyLemma", "MorphologyFormType",
    "ReviewStatus", "Decision", "DecisionNoteID", "Rationale",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'")
    value = re.sub(r"\s+", " ", value.strip())
    return value.casefold()


def variant_key(value: str) -> str:
    value = normalize(value)
    value = value.replace("-", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def meaning_key(value: str) -> str:
    value = normalize(value)
    value = value.replace("；", ";").replace("，", ",")
    return re.sub(r"\s+", "", value)


def occurrence_key(row: dict[str, str]) -> str:
    sem = {"上": "upper", "下": "lower"}[row["Semester"].strip()]
    return (
        f"grade{int(row['Grade'])}-{sem}-u{int(row['Unit']):02d}-"
        f"o{int(row['Order']):03d}|{normalize(row['Entry'])}"
    )


def candidate_text(rows: list[dict[str, str]]) -> str:
    return " || ".join(
        f"{r['NoteID']}::{r['CanonicalWord']}::{r['SenseLabel']}" for r in rows
    )


def main() -> None:
    for path in [SOURCE, MORPH, *REGISTRIES]:
        if not path.exists():
            raise SystemExit(f"Missing input: {path.relative_to(ROOT)}")

    source = read_csv(SOURCE)
    if len(source) != 509:
        raise SystemExit(f"Expected 509 source occurrences, got {len(source)}")
    registry = [r for p in REGISTRIES for r in read_csv(p)]
    by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_variant: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in registry:
        if row.get("Status", "").strip() != "active":
            continue
        by_match[normalize(row["MatchKey"])].append(row)
        by_variant[variant_key(row["MatchKey"])].append(row)

    # Explicit morphology is matched to the exact source occurrence dimensions.
    morph_index: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(MORPH):
        key = (
            row["Grade"].strip(), row["Semester"].strip(), row["Unit"].strip(),
            row["Page"].strip(), normalize(row["InflectedForm"]),
        )
        morph_index[key].append(row)

    source_meanings: dict[str, set[str]] = defaultdict(set)
    for row in source:
        source_meanings[normalize(row["Entry"])].add(meaning_key(row["Meaning"]))

    # Collapse byte-equivalent learning-unit occurrences, but keep all provenance keys.
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in source:
        groups[(normalize(row["Entry"]), meaning_key(row["Meaning"]))].append(row)

    output: list[dict[str, str]] = []
    counts: Counter[str] = Counter()
    covered_occurrences = 0
    for seq, ((match, _mkey), rows) in enumerate(sorted(groups.items()), 1):
        first = rows[0]
        covered_occurrences += len(rows)
        morph_rows: list[dict[str, str]] = []
        for r in rows:
            key = (
                r["Grade"].strip(), r["Semester"].strip(), r["Unit"].strip(),
                r["Page"].strip(), match,
            )
            morph_rows.extend(morph_index.get(key, []))

        exact = by_match.get(match, [])
        variants = [r for r in by_variant.get(variant_key(match), []) if normalize(r["MatchKey"]) != match]
        if morph_rows:
            cls = "morphology-only"
            lemmas = sorted({normalize(r["Lemma"]) for r in morph_rows})
            forms = sorted({r["FormType"].strip() for r in morph_rows})
        elif len(exact) == 1:
            cls = "exact-single"
            lemmas, forms = [], []
        elif len(exact) > 1:
            cls = "exact-multiple"
            lemmas, forms = [], []
        elif variants:
            cls = "orthographic-variant"
            lemmas, forms = [], []
        else:
            cls = "no-exact-match"
            lemmas, forms = [], []
        counts[cls] += 1

        occ_keys = [occurrence_key(r) for r in rows]
        output.append({
            "ProvisionalIdentityKey": f"G56V{seq:04d}",
            "OccurrenceKeys": " || ".join(occ_keys),
            "OccurrenceCount": str(len(rows)),
            "GradeSemesters": "|".join(sorted({r["Grade"].strip() + r["Semester"].strip() for r in rows})),
            "Units": "|".join(sorted({r["Grade"].strip() + r["Semester"].strip() + "-U" + r["Unit"].strip() for r in rows})),
            "Pages": "|".join(sorted({r["Grade"].strip() + r["Semester"].strip() + "-p" + r["Page"].strip() for r in rows})),
            "Entry": first["Entry"].strip(),
            "Meaning": first["Meaning"].strip(),
            "MatchKey": match,
            "SourceMeaningVariants": str(len(source_meanings[match])),
            "SourceSurfaceMultiplicity": "yes" if len(source_meanings[match]) > 1 else "no",
            "CandidateClass": cls,
            "ExistingNoteCount": str(len(exact)),
            "ExistingCandidates": candidate_text(exact),
            "VariantCandidates": candidate_text(variants),
            "MorphologyLemma": "|".join(lemmas),
            "MorphologyFormType": "|".join(forms),
            "ReviewStatus": "pending",
            "Decision": "",
            "DecisionNoteID": "",
            "Rationale": "",
        })

    if covered_occurrences != len(source):
        raise SystemExit("Source occurrence coverage mismatch")
    keys = [r["ProvisionalIdentityKey"] for r in output]
    if len(keys) != len(set(keys)):
        raise SystemExit("Duplicate ProvisionalIdentityKey")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader(); w.writerows(output)

    status = {
        "SourceOccurrences": len(source),
        "ProvisionalLearningUnits": len(output),
        "CandidateClasses": dict(sorted(counts.items())),
        "PendingReview": len(output),
        "StableNoteIDAllocated": False,
        "MasterLearnerReleasePublishMutationAuthorized": False,
        "SourceIdentityPending": True,
    }
    SUMMARY.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Grade 5–6 Vocabulary reconciliation plan:", json.dumps(status, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
