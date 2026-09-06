#!/usr/bin/env python3
"""Audit inflection-related Beijing staging candidates before any Klose merge.

This is a review aid only. It never modifies stable identity/master/release data.
It catches cases missed by exact MatchKey comparison, especially when the
Beijing source uses a singular form while Klose already stores a plural form,
or when two Beijing surfaces are inflectional variants of one likely learning
unit (e.g. tooth/teeth).
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master"
STAGING = BASE / "source_reference" / "beijing_start1_staging"
SURFACES = STAGING / "surface_inventory.csv"
OUT = STAGING / "source_variant_review_queue.csv"
SUMMARY = STAGING / "source_variant_audit.md"
REGISTRIES = [MASTER / "note_registry.csv", MASTER / "note_registry_extensions.csv"]

FIELDS = [
    "MatchKey", "DisplayForms", "Books", "CandidateType",
    "RelatedExistingNoteIDs", "RelatedExistingWords", "RelatedExistingSenses",
    "RelatedBeijingMatchKeys", "ReviewStatus", "ReviewReason",
]

IRREGULAR_SINGULAR_TO_PLURAL = {
    "child": "children", "man": "men", "woman": "women", "foot": "feet",
    "tooth": "teeth", "mouse": "mice", "goose": "geese",
}
IRREGULAR_PLURAL_TO_SINGULAR = {v: k for k, v in IRREGULAR_SINGULAR_TO_PLURAL.items()}
NON_PLURAL_S_FORMS = {
    "its", "his", "this", "is", "was", "has", "does", "yes", "news",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def variant_keys(key: str) -> set[str]:
    """Return conservative noun-like singular/plural neighbors.

    These are candidate links only, never automatic identity decisions.
    Multi-word phrases and verb conjugations are intentionally excluded.
    """
    if not key or " " in key:
        return set()
    out: set[str] = set()

    if key in IRREGULAR_SINGULAR_TO_PLURAL:
        out.add(IRREGULAR_SINGULAR_TO_PLURAL[key])
    if key in IRREGULAR_PLURAL_TO_SINGULAR:
        out.add(IRREGULAR_PLURAL_TO_SINGULAR[key])

    if key not in NON_PLURAL_S_FORMS:
        # plural -> likely singular
        if key.endswith("ies") and len(key) > 4:
            out.add(key[:-3] + "y")
        if key.endswith("es") and len(key) > 3:
            out.add(key[:-2])
            out.add(key[:-1])
        if key.endswith("s") and len(key) > 2 and not key.endswith("ss"):
            out.add(key[:-1])

        # singular -> likely plural
        if key.endswith("y") and len(key) > 2 and key[-2] not in "aeiou":
            out.add(key[:-1] + "ies")
        out.add(key + "s")
        out.add(key + "es")

    out.discard(key)
    return {x for x in out if x}


def main() -> None:
    if not SURFACES.exists():
        raise SystemExit(f"Missing staging surface inventory: {SURFACES}")

    surfaces = read_csv(SURFACES)
    surface_by_key = {r["MatchKey"]: r for r in surfaces}

    identities: list[dict[str, str]] = []
    for path in REGISTRIES:
        identities.extend(read_csv(path))
    identities_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in identities:
        key = (r.get("MatchKey") or r.get("CanonicalWord") or "").strip().casefold()
        if key:
            identities_by_key[key].append(r)

    rows: list[dict[str, str]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for surface in surfaces:
        if surface.get("AutoDecision") != "new-identity-candidate":
            continue
        key = surface["MatchKey"]
        neighbors = variant_keys(key)
        if not neighbors:
            continue

        existing: list[dict[str, str]] = []
        related_beijing: list[str] = []
        for nk in sorted(neighbors):
            existing.extend(identities_by_key.get(nk, []))
            if nk in surface_by_key:
                pair = tuple(sorted((key, nk)))
                if pair not in seen_pairs:
                    related_beijing.append(nk)
                    seen_pairs.add(pair)

        existing_unique = {r.get("NoteID", ""): r for r in existing if r.get("NoteID")}
        existing = list(existing_unique.values())
        if not existing and not related_beijing:
            continue

        if existing and related_beijing:
            ctype = "existing-and-beijing-inflection-candidate"
        elif existing:
            ctype = "existing-inflection-candidate"
        else:
            ctype = "beijing-inflection-cluster"

        rows.append({
            "MatchKey": key,
            "DisplayForms": surface.get("DisplayForms", ""),
            "Books": surface.get("Books", ""),
            "CandidateType": ctype,
            "RelatedExistingNoteIDs": "|".join(r.get("NoteID", "") for r in existing),
            "RelatedExistingWords": "|".join(r.get("CanonicalWord", "") for r in existing),
            "RelatedExistingSenses": "|".join(r.get("SenseLabel", "") for r in existing),
            "RelatedBeijingMatchKeys": "|".join(related_beijing),
            "ReviewStatus": "pending",
            "ReviewReason": "Inflection relationship is candidate-only; confirm learning-unit identity before merge.",
        })

    write_csv(OUT, rows)

    existing_count = sum(bool(r["RelatedExistingNoteIDs"]) for r in rows)
    source_count = sum(bool(r["RelatedBeijingMatchKeys"]) for r in rows)
    text = [
        "# Beijing staging — source variant audit",
        "",
        "> Review aid only. No identity merge is authorized by this file.",
        "",
        f"- reviewed unmatched surface candidates: {sum(1 for r in surfaces if r.get('AutoDecision') == 'new-identity-candidate')}",
        f"- rows with inflection-related candidates: {len(rows)}",
        f"- rows linked to an existing Klose identity by inflection: {existing_count}",
        f"- rows linked to another Beijing surface by inflection: {source_count}",
        "",
        "The audit is intentionally conservative: it handles single-word noun-like singular/plural relations and a small explicit irregular map. It does not merge verb conjugations, phrases, compounds, or semantic relatives.",
        "",
        "All rows remain `pending` until sense-aware review.",
    ]
    SUMMARY.write_text("\n".join(text) + "\n", encoding="utf-8")
    print(f"variant-review rows: {len(rows)}")


if __name__ == "__main__":
    main()
