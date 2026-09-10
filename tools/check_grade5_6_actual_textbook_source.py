#!/usr/bin/env python3
"""Validate Klose Grade 5–6 actual-textbook source materialization.

This gate validates Source-layer completeness only. It deliberately permits
SourceID/SourceEdition == pending-confirmation; that unresolved provenance must
remain explicit and must not be guessed. It never authorizes Stable ID allocation
or Klose learner/publish/Anki mutation.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "anki" / "klose" / "source_reference"

VOCAB = SRC / "klose-actual-grade5-6-vocabulary.csv"
EXPR = {
    (5, "上"): SRC / "klose-actual-grade5-upper-expressions.csv",
    (5, "下"): SRC / "klose-actual-grade5-lower-expressions.csv",
    (6, "上"): SRC / "klose-actual-grade6-upper-expressions.csv",
    (6, "下"): SRC / "klose-actual-grade6-lower-expressions.csv",
}
PROVERBS = SRC / "klose-actual-grade5-lower-proverbs.csv"
MORPH = SRC / "klose-actual-grade5-6-morphology.csv"
MANIFEST = SRC / "grade5_6_actual_textbook_manifest.csv"
SUPERSEDED_MORPH = SRC / "klose-grade6-morphology-pending-trace.csv"

EXPECTED_VOCAB = {
    (5, "上"): {1: 18, 2: 17, 3: 20, 4: 21, 5: 20, 6: 23},
    (5, "下"): {1: 36, 2: 24, 3: 35, 4: 21, 5: 16, 6: 24},
    (6, "上"): {1: 26, 2: 25, 3: 20, 4: 17, 5: 29, 6: 27},
    (6, "下"): {1: 21, 2: 24, 3: 23, 4: 22},
}
EXPECTED_EXPR = {
    (5, "上"): {1: 8, 2: 7, 3: 7, 4: 4, 5: 6, 6: 6},
    (5, "下"): {1: 4, 2: 4, 3: 4, 4: 4, 5: 6, 6: 6},
    (6, "上"): {1: 9, 2: 10, 3: 9, 4: 6, 5: 9, 6: 11},
    (6, "下"): {1: 8, 2: 9, 3: 10, 4: 6},
}
EXPECTED_MORPH_TYPES = {
    "verb_past": 36,
    "comparative": 14,
    "present_participle": 6,
    "plural": 2,
}
EXPECTED_TOTALS = {
    "Vocabulary": 509,
    "Useful Expressions": 153,
    "Proverbs": 6,
    "Morphology": 58,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required source artifact: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def require_columns(path: Path, rows: list[dict[str, str]], required: set[str]) -> None:
    if not rows:
        raise SystemExit(f"Empty source artifact: {path.relative_to(ROOT)}")
    missing = required - set(rows[0])
    if missing:
        raise SystemExit(f"{path.name}: missing columns {sorted(missing)}")
    forbidden = {"NoteID", "ExpressionID", "StableThirdPartyID"} & set(rows[0])
    if forbidden:
        raise SystemExit(f"{path.name}: Source artifact contains identity columns {sorted(forbidden)}")


def check_common(path: Path, rows: list[dict[str, str]]) -> None:
    for i, row in enumerate(rows, 2):
        if not row.get("EvidenceFileID", "").strip().startswith("file_"):
            raise SystemExit(f"{path.name}:{i}: missing/invalid EvidenceFileID")
        if row.get("SourceID", "").strip() != "pending-confirmation":
            raise SystemExit(f"{path.name}:{i}: SourceID must remain explicit pending-confirmation until verified")
        if row.get("SourceEdition", "").strip() != "pending-confirmation":
            raise SystemExit(f"{path.name}:{i}: SourceEdition must remain explicit pending-confirmation until verified")
        if "materialized-from-user-image" not in row.get("SourceStatus", ""):
            raise SystemExit(f"{path.name}:{i}: invalid SourceStatus")


def check_unit_orders(path: Path, rows: list[dict[str, str]], expected: dict[int, int]) -> None:
    grouped: dict[int, list[int]] = defaultdict(list)
    for row in rows:
        try:
            grouped[int(row["Unit"])].append(int(row["Order"]))
        except (KeyError, ValueError) as exc:
            raise SystemExit(f"{path.name}: invalid Unit/Order") from exc
    actual_counts = {u: len(v) for u, v in grouped.items()}
    if actual_counts != expected:
        raise SystemExit(f"{path.name}: Unit counts drift: actual={actual_counts}, expected={expected}")
    for unit, orders in grouped.items():
        want = list(range(1, len(orders) + 1))
        if sorted(orders) != want:
            raise SystemExit(f"{path.name}: non-contiguous/duplicate Order in Unit {unit}: {sorted(orders)}")


def check_vocab() -> list[dict[str, str]]:
    rows = read_csv(VOCAB)
    require_columns(VOCAB, rows, {
        "SourceID", "SourceEdition", "EvidenceFileID", "Grade", "Semester",
        "Unit", "Order", "Starred", "Entry", "Meaning", "Page", "SourceStatus",
    })
    check_common(VOCAB, rows)
    if len(rows) != EXPECTED_TOTALS["Vocabulary"]:
        raise SystemExit(f"Vocabulary row count drift: {len(rows)} != 509")
    buckets: dict[tuple[int, str], list[dict[str, str]]] = defaultdict(list)
    keys: set[tuple[int, str, int, int]] = set()
    for i, row in enumerate(rows, 2):
        try:
            grade = int(row["Grade"])
            unit = int(row["Unit"])
            order = int(row["Order"])
        except ValueError as exc:
            raise SystemExit(f"{VOCAB.name}:{i}: invalid numeric field") from exc
        sem = row["Semester"].strip()
        key = (grade, sem, unit, order)
        if key in keys:
            raise SystemExit(f"{VOCAB.name}:{i}: duplicate source occurrence key {key}")
        keys.add(key)
        if row["Starred"].strip() not in {"0", "1"}:
            raise SystemExit(f"{VOCAB.name}:{i}: Starred must be 0/1")
        if not row["Entry"].strip() or not row["Meaning"].strip() or not row["Page"].strip():
            raise SystemExit(f"{VOCAB.name}:{i}: Entry/Meaning/Page must be non-empty")
        buckets[(grade, sem)].append(row)
    if set(buckets) != set(EXPECTED_VOCAB):
        raise SystemExit(f"Vocabulary book coverage drift: {set(buckets)}")
    for book, expected in EXPECTED_VOCAB.items():
        check_unit_orders(VOCAB, buckets[book], expected)
    return rows


def check_expressions() -> list[dict[str, str]]:
    all_rows: list[dict[str, str]] = []
    for book, path in EXPR.items():
        rows = read_csv(path)
        require_columns(path, rows, {
            "SourceID", "SourceEdition", "EvidenceFileID", "Grade", "Semester",
            "Unit", "Order", "RawExpression", "Translation", "Page", "SourceStatus",
        })
        check_common(path, rows)
        grade, sem = book
        for i, row in enumerate(rows, 2):
            if row["Grade"].strip() != str(grade) or row["Semester"].strip() != sem:
                raise SystemExit(f"{path.name}:{i}: wrong Grade/Semester")
            if not row["RawExpression"].strip() or not row["Translation"].strip():
                raise SystemExit(f"{path.name}:{i}: RawExpression/Translation empty")
        check_unit_orders(path, rows, EXPECTED_EXPR[book])
        all_rows.extend(rows)
    if len(all_rows) != EXPECTED_TOTALS["Useful Expressions"]:
        raise SystemExit(f"Expression row count drift: {len(all_rows)} != 153")
    return all_rows


def check_proverbs() -> list[dict[str, str]]:
    rows = read_csv(PROVERBS)
    require_columns(PROVERBS, rows, {
        "SourceID", "SourceEdition", "EvidenceFileID", "Grade", "Semester",
        "ObjectType", "Order", "RawExpression", "Translation", "Page", "SourceStatus",
    })
    check_common(PROVERBS, rows)
    if len(rows) != 6:
        raise SystemExit(f"Proverb row count drift: {len(rows)} != 6")
    orders = sorted(int(r["Order"]) for r in rows)
    if orders != list(range(1, 7)):
        raise SystemExit(f"Proverb Order drift: {orders}")
    for i, row in enumerate(rows, 2):
        if row["Grade"] != "5" or row["Semester"] != "下" or row["ObjectType"] != "Proverb":
            raise SystemExit(f"{PROVERBS.name}:{i}: invalid proverb classification")
        if not row["RawExpression"].strip() or not row["Translation"].strip():
            raise SystemExit(f"{PROVERBS.name}:{i}: proverb text/translation empty")
    return rows


def check_morphology(vocab_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = read_csv(MORPH)
    require_columns(MORPH, rows, {
        "SourceID", "SourceEdition", "EvidenceFileID", "Lemma", "FormType",
        "InflectedForm", "IPA", "Grade", "Semester", "Unit", "Page",
        "SourceEntry", "SourceStatus",
    })
    check_common(MORPH, rows)
    if len(rows) != EXPECTED_TOTALS["Morphology"]:
        raise SystemExit(f"Morphology row count drift: {len(rows)} != 58")
    counts = Counter(r["FormType"].strip() for r in rows)
    if dict(counts) != EXPECTED_MORPH_TYPES:
        raise SystemExit(f"Morphology type counts drift: {dict(counts)} != {EXPECTED_MORPH_TYPES}")
    vocab_index: set[tuple[str, str, str, str, str]] = set()
    for row in vocab_rows:
        vocab_index.add((row["Grade"], row["Semester"], row["Unit"], row["Page"], row["Entry"].strip().casefold()))
    seen: set[tuple[str, ...]] = set()
    for i, row in enumerate(rows, 2):
        if not all(row[k].strip() for k in ("Lemma", "InflectedForm", "IPA", "Grade", "Semester", "Unit", "Page", "SourceEntry")):
            raise SystemExit(f"{MORPH.name}:{i}: incomplete morphology provenance")
        key = (row["Grade"], row["Semester"], row["Unit"], row["Page"], row["Lemma"], row["FormType"], row["InflectedForm"])
        if key in seen:
            raise SystemExit(f"{MORPH.name}:{i}: duplicate morphology occurrence {key}")
        seen.add(key)
        prefix = (row["Grade"], row["Semester"], row["Unit"], row["Page"])
        lemma_key = prefix + (row["Lemma"].strip().casefold(),)
        form_key = prefix + (row["InflectedForm"].strip().casefold(),)
        if lemma_key not in vocab_index and form_key not in vocab_index:
            raise SystemExit(f"{MORPH.name}:{i}: morphology row not traceable to a vocabulary source occurrence: {key}")
    if SUPERSEDED_MORPH.exists():
        raise SystemExit(f"Superseded morphology truth still exists: {SUPERSEDED_MORPH.relative_to(ROOT)}")
    return rows


def check_manifest() -> None:
    rows = read_csv(MANIFEST)
    expected = {
        ("5", "上", "Vocabulary"): 119,
        ("5", "上", "Useful Expressions"): 38,
        ("5", "下", "Vocabulary"): 156,
        ("5", "下", "Useful Expressions"): 28,
        ("5", "下", "Proverbs"): 6,
        ("6", "上", "Vocabulary"): 144,
        ("6", "上", "Useful Expressions"): 54,
        ("6", "下", "Vocabulary"): 90,
        ("6", "下", "Useful Expressions"): 33,
        ("5-6", "all", "Morphology"): 58,
    }
    actual: dict[tuple[str, str, str], int] = {}
    for i, row in enumerate(rows, 2):
        key = (row["Grade"].strip(), row["Semester"].strip(), row["ObjectType"].strip())
        if key in actual:
            raise SystemExit(f"{MANIFEST.name}:{i}: duplicate manifest key {key}")
        if row["MaterializationStatus"].strip() != "materialized-source-identity-pending":
            raise SystemExit(f"{MANIFEST.name}:{i}: unexpected MaterializationStatus")
        if row["SourceID"].strip() != "pending-confirmation" or row["SourceEdition"].strip() != "pending-confirmation":
            raise SystemExit(f"{MANIFEST.name}:{i}: source identity must remain explicit pending-confirmation")
        if row["ExpectedRows"].strip() != row["MaterializedRows"].strip():
            raise SystemExit(f"{MANIFEST.name}:{i}: expected/materialized mismatch")
        actual[key] = int(row["MaterializedRows"])
    if actual != expected:
        raise SystemExit(f"Manifest closure drift: actual={actual}, expected={expected}")


def main() -> None:
    vocab = check_vocab()
    expr = check_expressions()
    proverbs = check_proverbs()
    morph = check_morphology(vocab)
    check_manifest()
    print(
        "Grade 5–6 actual-textbook Source OK: "
        f"vocabulary={len(vocab)}, expressions={len(expr)}, proverbs={len(proverbs)}, "
        f"morphology_occurrences={len(morph)}, source_identity_pending=yes, "
        "StableID/allocation/publish/Anki authorization=no"
    )


if __name__ == "__main__":
    main()
