#!/usr/bin/env python3
"""Provenance-aware completion gate for Grade 5–6 actual textbook source."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "anki" / "klose" / "source_reference"
CONFIG = SRC / "grade5_6_source_provenance.json"
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
EXPECTED_TOTALS = {"Vocabulary": 509, "Useful Expressions": 153, "Proverbs": 6, "Morphology": 58}


def fail(msg: str) -> None:
    raise SystemExit(f"Grade 5–6 actual-source FAIL: {msg}")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"missing required source artifact: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_config() -> dict:
    if not CONFIG.exists():
        fail("missing grade5_6_source_provenance.json")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config.get("CanonicalSourceID") != "renjiao_start3":
        fail("unexpected CanonicalSourceID")
    if config.get("ResolutionState") not in {"planned", "applied"}:
        fail("invalid provenance ResolutionState")
    if config.get("StableIDAllocationAllowed") is not False:
        fail("provenance config must not authorize Stable ID allocation")
    books = config.get("Books", {})
    if set(books) != {"5上", "5下", "6上", "6下"}:
        fail("provenance config book coverage drift")
    if books["5上"].get("SourceEdition") != "2024-revision" or books["6上"].get("SourceEdition") != "2024-revision":
        fail("upper-volume revision lineage drift")
    if books["5下"].get("SourceEdition") != "pre-2024-revision" or books["6下"].get("SourceEdition") != "pre-2024-revision":
        fail("lower-volume legacy lineage drift")
    if books["5下"].get("StableIDAllocationEligible") is not False or books["6下"].get("StableIDAllocationEligible") is not False:
        fail("legacy lower volumes must remain allocation-held")
    return config


def book_key(row: dict[str, str]) -> str:
    key = row.get("Grade", "").strip() + row.get("Semester", "").strip()
    if key not in {"5上", "5下", "6上", "6下"}:
        fail(f"invalid Grade/Semester: {key!r}")
    return key


def require_columns(path: Path, rows: list[dict[str, str]], required: set[str]) -> None:
    if not rows:
        fail(f"empty source artifact: {path.relative_to(ROOT)}")
    missing = required - set(rows[0])
    if missing:
        fail(f"{path.name}: missing columns {sorted(missing)}")
    forbidden = {"NoteID", "ExpressionID", "StableThirdPartyID"} & set(rows[0])
    if forbidden:
        fail(f"{path.name}: Source artifact contains identity columns {sorted(forbidden)}")


def check_common(config: dict, path: Path, rows: list[dict[str, str]]) -> None:
    applied = config["ResolutionState"] == "applied"
    for i, row in enumerate(rows, 2):
        if not row.get("EvidenceFileID", "").strip().startswith("file_"):
            fail(f"{path.name}:{i}: missing/invalid EvidenceFileID")
        if "materialized-from-user-image" not in row.get("SourceStatus", ""):
            fail(f"{path.name}:{i}: invalid SourceStatus")
        if applied:
            key = book_key(row)
            book = config["Books"][key]
            if row.get("SourceID", "").strip() != config["CanonicalSourceID"]:
                fail(f"{path.name}:{i}: SourceID not resolved")
            if row.get("SourceEdition", "").strip() != book["SourceEdition"]:
                fail(f"{path.name}:{i}: SourceEdition not resolved for {key}")
            status = row.get("SourceStatus", "")
            if "source-provenance-resolved" not in status:
                fail(f"{path.name}:{i}: missing source-provenance-resolved marker")
            held = not book["StableIDAllocationEligible"]
            if held != ("source-provenance-held" in status):
                fail(f"{path.name}:{i}: held marker disagrees with provenance config")
            if "source-identity-pending-confirmation" in status:
                fail(f"{path.name}:{i}: stale pending provenance marker remains")
        else:
            if row.get("SourceID", "").strip() != "pending-confirmation" or row.get("SourceEdition", "").strip() != "pending-confirmation":
                fail(f"{path.name}:{i}: planned state requires explicit pending-confirmation")


def check_unit_orders(path: Path, rows: list[dict[str, str]], expected: dict[int, int]) -> None:
    grouped: dict[int, list[int]] = defaultdict(list)
    for row in rows:
        try:
            grouped[int(row["Unit"])].append(int(row["Order"]))
        except (KeyError, ValueError) as exc:
            fail(f"{path.name}: invalid Unit/Order: {exc}")
    actual_counts = {u: len(v) for u, v in grouped.items()}
    if actual_counts != expected:
        fail(f"{path.name}: Unit counts drift actual={actual_counts} expected={expected}")
    for unit, orders in grouped.items():
        if sorted(orders) != list(range(1, len(orders) + 1)):
            fail(f"{path.name}: non-contiguous/duplicate Order in Unit {unit}")


def check_vocab(config: dict) -> list[dict[str, str]]:
    rows = read_csv(VOCAB)
    require_columns(VOCAB, rows, {"SourceID", "SourceEdition", "EvidenceFileID", "Grade", "Semester", "Unit", "Order", "Starred", "Entry", "Meaning", "Page", "SourceStatus"})
    check_common(config, VOCAB, rows)
    if len(rows) != 509:
        fail(f"Vocabulary row count drift: {len(rows)} != 509")
    buckets: dict[tuple[int, str], list[dict[str, str]]] = defaultdict(list)
    seen: set[tuple[int, str, int, int]] = set()
    for i, row in enumerate(rows, 2):
        try:
            grade, unit, order = int(row["Grade"]), int(row["Unit"]), int(row["Order"])
        except ValueError as exc:
            fail(f"{VOCAB.name}:{i}: invalid numeric field: {exc}")
        sem = row["Semester"].strip()
        key = (grade, sem, unit, order)
        if key in seen:
            fail(f"{VOCAB.name}:{i}: duplicate occurrence {key}")
        seen.add(key)
        if row["Starred"].strip() not in {"0", "1"}:
            fail(f"{VOCAB.name}:{i}: Starred must be 0/1")
        if not row["Entry"].strip() or not row["Meaning"].strip() or not row["Page"].strip():
            fail(f"{VOCAB.name}:{i}: Entry/Meaning/Page must be non-empty")
        buckets[(grade, sem)].append(row)
    if set(buckets) != set(EXPECTED_VOCAB):
        fail(f"Vocabulary book coverage drift: {set(buckets)}")
    for book, expected in EXPECTED_VOCAB.items():
        check_unit_orders(VOCAB, buckets[book], expected)
    return rows


def check_expressions(config: dict) -> list[dict[str, str]]:
    all_rows: list[dict[str, str]] = []
    for book, path in EXPR.items():
        rows = read_csv(path)
        require_columns(path, rows, {"SourceID", "SourceEdition", "EvidenceFileID", "Grade", "Semester", "Unit", "Order", "RawExpression", "Translation", "Page", "SourceStatus"})
        check_common(config, path, rows)
        grade, sem = book
        for i, row in enumerate(rows, 2):
            if row["Grade"].strip() != str(grade) or row["Semester"].strip() != sem:
                fail(f"{path.name}:{i}: wrong Grade/Semester")
            if not row["RawExpression"].strip() or not row["Translation"].strip():
                fail(f"{path.name}:{i}: RawExpression/Translation empty")
        check_unit_orders(path, rows, EXPECTED_EXPR[book])
        all_rows.extend(rows)
    if len(all_rows) != 153:
        fail(f"Expression row count drift: {len(all_rows)} != 153")
    return all_rows


def check_proverbs(config: dict) -> list[dict[str, str]]:
    rows = read_csv(PROVERBS)
    require_columns(PROVERBS, rows, {"SourceID", "SourceEdition", "EvidenceFileID", "Grade", "Semester", "ObjectType", "Order", "RawExpression", "Translation", "Page", "SourceStatus"})
    check_common(config, PROVERBS, rows)
    if len(rows) != 6 or sorted(int(r["Order"]) for r in rows) != list(range(1, 7)):
        fail("Proverb count/order drift")
    for i, row in enumerate(rows, 2):
        if row["Grade"] != "5" or row["Semester"] != "下" or row["ObjectType"] != "Proverb":
            fail(f"{PROVERBS.name}:{i}: invalid proverb classification")
    return rows


def check_morphology(config: dict, vocab_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = read_csv(MORPH)
    require_columns(MORPH, rows, {"SourceID", "SourceEdition", "EvidenceFileID", "Lemma", "FormType", "InflectedForm", "IPA", "Grade", "Semester", "Unit", "Page", "SourceEntry", "SourceStatus"})
    check_common(config, MORPH, rows)
    if len(rows) != 58:
        fail(f"Morphology row count drift: {len(rows)} != 58")
    counts = Counter(r["FormType"].strip() for r in rows)
    if dict(counts) != EXPECTED_MORPH_TYPES:
        fail(f"Morphology type counts drift: {dict(counts)}")
    vocab_index = {(r["Grade"], r["Semester"], r["Unit"], r["Page"], r["Entry"].strip().casefold()) for r in vocab_rows}
    seen: set[tuple[str, ...]] = set()
    for i, row in enumerate(rows, 2):
        if not all(row[k].strip() for k in ("Lemma", "InflectedForm", "IPA", "Grade", "Semester", "Unit", "Page", "SourceEntry")):
            fail(f"{MORPH.name}:{i}: incomplete morphology provenance")
        key = (row["Grade"], row["Semester"], row["Unit"], row["Page"], row["Lemma"], row["FormType"], row["InflectedForm"])
        if key in seen:
            fail(f"{MORPH.name}:{i}: duplicate morphology occurrence")
        seen.add(key)
        prefix = (row["Grade"], row["Semester"], row["Unit"], row["Page"])
        if prefix + (row["Lemma"].strip().casefold(),) not in vocab_index and prefix + (row["InflectedForm"].strip().casefold(),) not in vocab_index:
            fail(f"{MORPH.name}:{i}: morphology not traceable to Vocabulary source")
    if SUPERSEDED_MORPH.exists():
        fail(f"superseded morphology truth still exists: {SUPERSEDED_MORPH.relative_to(ROOT)}")
    return rows


def check_manifest(config: dict) -> None:
    rows = read_csv(MANIFEST)
    expected = {
        ("5", "上", "Vocabulary"): 119, ("5", "上", "Useful Expressions"): 38,
        ("5", "下", "Vocabulary"): 156, ("5", "下", "Useful Expressions"): 28,
        ("5", "下", "Proverbs"): 6, ("6", "上", "Vocabulary"): 144,
        ("6", "上", "Useful Expressions"): 54, ("6", "下", "Vocabulary"): 90,
        ("6", "下", "Useful Expressions"): 33, ("5-6", "all", "Morphology"): 58,
    }
    actual: dict[tuple[str, str, str], int] = {}
    applied = config["ResolutionState"] == "applied"
    for i, row in enumerate(rows, 2):
        key = (row["Grade"].strip(), row["Semester"].strip(), row["ObjectType"].strip())
        if key in actual:
            fail(f"{MANIFEST.name}:{i}: duplicate manifest key {key}")
        if row["ExpectedRows"].strip() != row["MaterializedRows"].strip():
            fail(f"{MANIFEST.name}:{i}: expected/materialized mismatch")
        actual[key] = int(row["MaterializedRows"])
        if not applied:
            if row["SourceID"].strip() != "pending-confirmation" or row["SourceEdition"].strip() != "pending-confirmation":
                fail(f"{MANIFEST.name}:{i}: planned state must remain pending")
            if row["MaterializationStatus"].strip() != "materialized-source-identity-pending":
                fail(f"{MANIFEST.name}:{i}: unexpected planned MaterializationStatus")
        elif key == ("5-6", "all", "Morphology"):
            if row["SourceID"].strip() != config["CanonicalSourceID"] or row["SourceEdition"].strip() != "mixed-by-book":
                fail(f"{MANIFEST.name}:{i}: aggregate morphology provenance drift")
            if row["MaterializationStatus"].strip() != "materialized-source-provenance-resolved-mixed-held":
                fail(f"{MANIFEST.name}:{i}: aggregate morphology status drift")
        else:
            bkey = row["Grade"].strip() + row["Semester"].strip()
            book = config["Books"][bkey]
            if row["SourceID"].strip() != config["CanonicalSourceID"] or row["SourceEdition"].strip() != book["SourceEdition"]:
                fail(f"{MANIFEST.name}:{i}: resolved identity drift for {bkey}")
            want_status = "materialized-source-provenance-resolved" if book["StableIDAllocationEligible"] else "materialized-source-provenance-resolved-held"
            if row["MaterializationStatus"].strip() != want_status:
                fail(f"{MANIFEST.name}:{i}: MaterializationStatus drift for {bkey}")
    if actual != expected:
        fail(f"Manifest closure drift: actual={actual} expected={expected}")


def main() -> None:
    config = load_config()
    vocab = check_vocab(config)
    expr = check_expressions(config)
    proverbs = check_proverbs(config)
    morph = check_morphology(config, vocab)
    check_manifest(config)
    print(
        "Grade 5–6 actual-textbook Source OK: "
        f"vocabulary={len(vocab)}, expressions={len(expr)}, proverbs={len(proverbs)}, morphology={len(morph)}, "
        f"provenance_state={config['ResolutionState']}, source_id={config['CanonicalSourceID']}, "
        f"blockers={len(config.get('Blockers', []))}, StableIDAllocationAllowed=false"
    )


if __name__ == "__main__":
    main()
