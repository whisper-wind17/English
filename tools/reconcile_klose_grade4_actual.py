#!/usr/bin/env python3
"""Batch reconcile Klose actual Grade-4 vocabulary against persistent NoteID registry.

This script is intentionally conservative. It never mutates identity/release state.
It produces a deterministic candidate report that separates:
- high-confidence exact-word/same-sense reuse
- exact-word but sense-review cases
- repeated actual homographs with different meanings
- genuine new surface candidates
- phrase/morphology candidates for review

Source Grade, LearnerLevel, and Learning Admission remain independent.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
ACTUAL = BASE / "source_reference" / "rj_start1-grade4-klose-actual.csv"
REGISTRY = BASE / "master" / "note_registry.csv"
OUT = BASE / "source_reference" / "rj_start1-grade4-identity-candidates.csv"

FIELDS = [
    "SourceEdition", "Semester", "Unit", "Order", "Entry", "Meaning",
    "MatchKey", "CandidateNoteID", "CandidateWord", "CandidateSense",
    "MatchType", "Decision", "ReviewReason",
]

STOP_CHARS = set("的了是在和或与及等用作表示某种一个一些；，。、（）()…… \t\r\n")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def norm_display(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", value.strip())


def match_key(value: str) -> str:
    return norm_display(value).casefold()


def meaning_tokens(text: str) -> set[str]:
    """Small deterministic token set for conservative Chinese gloss overlap."""
    text = norm_display(text)
    chunks = re.split(r"[；;，,、/（）()：:\s]+", text)
    tokens: set[str] = set()
    for chunk in chunks:
        chunk = "".join(ch for ch in chunk if ch not in STOP_CHARS)
        if not chunk:
            continue
        tokens.add(chunk)
        if len(chunk) >= 2:
            tokens.update(chunk[i:i+2] for i in range(len(chunk)-1))
    return {t for t in tokens if t}


def same_sense_likely(actual: str, candidate: str) -> bool:
    a = norm_display(actual)
    b = norm_display(candidate)
    if a == b or a in b or b in a:
        return True
    ta, tb = meaning_tokens(a), meaning_tokens(b)
    if not ta or not tb:
        return False
    common = ta & tb
    # Require at least one substantive 2+ char overlap, or strong token overlap.
    if any(len(x) >= 2 for x in common):
        return True
    return len(common) / min(len(ta), len(tb)) >= 0.5


def morphology_candidates(entry: str, registry_by_key: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    key = match_key(entry)
    candidates: list[dict[str, str]] = []
    variants: set[str] = set()
    if key.endswith("s") and len(key) > 3:
        variants.add(key[:-1])
    else:
        variants.add(key + "s")
    if key.endswith("es") and len(key) > 4:
        variants.add(key[:-2])
    if key.endswith("ies") and len(key) > 4:
        variants.add(key[:-3] + "y")
    for v in sorted(variants):
        candidates.extend(registry_by_key.get(v, []))
    return candidates


def phrase_candidates(entry: str, registry_by_key: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    words = [w for w in re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*", match_key(entry)) if len(w) > 2]
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for w in words:
        for row in registry_by_key.get(w, []):
            nid = row["NoteID"]
            if nid not in seen:
                seen.add(nid)
                out.append(row)
    return out


def main() -> None:
    for p in (ACTUAL, REGISTRY):
        if not p.exists():
            raise SystemExit(f"Missing input: {p.relative_to(ROOT)}")

    actual = read_csv(ACTUAL)
    registry = read_csv(REGISTRY)
    if len(actual) != 221:
        raise SystemExit(f"Expected confirmed Grade-4 actual baseline of 221 occurrences, found {len(actual)}")

    registry_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in registry:
        registry_by_key[r["MatchKey"].strip()].append(r)

    actual_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in actual:
        actual_by_key[match_key(r["Entry"])].append(r)

    rows: list[dict[str, str]] = []
    for src in actual:
        key = match_key(src["Entry"])
        base = {
            "SourceEdition": src["SourceEdition"],
            "Semester": src["Semester"],
            "Unit": src["Unit"],
            "Order": src["Order"],
            "Entry": src["Entry"],
            "Meaning": src["Meaning"],
            "MatchKey": key,
            "CandidateNoteID": "",
            "CandidateWord": "",
            "CandidateSense": "",
            "MatchType": "",
            "Decision": "",
            "ReviewReason": "",
        }

        same_surface_group = actual_by_key[key]
        distinct_actual_meanings = {norm_display(x["Meaning"]) for x in same_surface_group}
        exact = registry_by_key.get(key, [])

        if len(distinct_actual_meanings) > 1:
            # Homograph/duplicate surface in the confirmed textbook: never auto-collapse.
            if exact:
                c = exact[0]
                base.update({
                    "CandidateNoteID": c["NoteID"],
                    "CandidateWord": c["CanonicalWord"],
                    "CandidateSense": c["SenseLabel"],
                    "MatchType": "exact-surface-homograph",
                    "Decision": "review",
                    "ReviewReason": "same textbook surface has multiple target meanings",
                })
            else:
                base.update({
                    "MatchType": "new-surface-homograph",
                    "Decision": "review",
                    "ReviewReason": "same textbook surface has multiple target meanings; create separate identities",
                })
            rows.append(base)
            continue

        if len(exact) == 1:
            c = exact[0]
            likely = same_sense_likely(src["Meaning"], c["SenseLabel"])
            base.update({
                "CandidateNoteID": c["NoteID"],
                "CandidateWord": c["CanonicalWord"],
                "CandidateSense": c["SenseLabel"],
                "MatchType": "exact-surface",
                "Decision": "reuse" if likely else "review",
                "ReviewReason": "" if likely else "exact word but target sense/gloss overlap is insufficient",
            })
            rows.append(base)
            continue

        if len(exact) > 1:
            base.update({
                "MatchType": "multiple-existing-identities",
                "Decision": "review",
                "ReviewReason": f"{len(exact)} existing registry identities share this MatchKey",
            })
            rows.append(base)
            continue

        morph = morphology_candidates(src["Entry"], registry_by_key)
        phrase = phrase_candidates(src["Entry"], registry_by_key) if " " in key else []
        candidates = morph or phrase
        if candidates:
            c = candidates[0]
            base.update({
                "CandidateNoteID": c["NoteID"],
                "CandidateWord": c["CanonicalWord"],
                "CandidateSense": c["SenseLabel"],
                "MatchType": "morphology-candidate" if morph else "phrase-component-candidate",
                "Decision": "review",
                "ReviewReason": "surface is not exact; candidate must not be merged automatically",
            })
        else:
            base.update({
                "MatchType": "new-surface",
                "Decision": "new",
                "ReviewReason": "",
            })
        rows.append(base)

    rows.sort(key=lambda r: (0 if r["Semester"] == "上" else 1, int(r["Unit"]), int(r["Order"])))
    write_csv(OUT, rows)

    counts: dict[str, int] = defaultdict(int)
    for r in rows:
        counts[r["Decision"]] += 1
    print(
        "Grade-4 identity candidates: "
        f"occurrences={len(rows)} reuse={counts['reuse']} review={counts['review']} new={counts['new']} "
        f"output={OUT.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
