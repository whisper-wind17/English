#!/usr/bin/env python3
"""Overlay confirmed New Concept English 1 identities onto Klose derived Vocabulary state."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
SRC = BASE / "source_reference" / "new_concept_english_1_staging" / "vocabulary-smart-2022.csv"
DECISIONS = BASE / "review" / "nce1_reconciliation" / "identity_decisions.csv"
TARGETS = BASE / "review" / "nce1_reconciliation" / "target_sense_evidence.csv"
REG_EXT = BASE / "master" / "note_registry_extensions.csv"
SOURCE_EXT = BASE / "master" / "source_identity_extensions.csv"
MASTER = BASE / "master" / "vocabulary_master.csv"
OCC = BASE / "master" / "source_occurrences.csv"
LEARNER = BASE / "learner" / "current.csv"
LEARNER_REVIEW = BASE / "review" / "learner_review.csv"
STATS = BASE / "master" / "build_stats.csv"

SOURCE_ID = "new_concept_english_1"
SOURCE_EDITION = "2022-smart-isbn-9787521336702"
CREATED_SOURCE = "klose-nce1-current"
PROFILE = "klose"
LEVEL = "4"
EXPECTED_REASON = "nce1-current-new-note-needs-learner-content-and-lexical-facts"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing NCE1 overlay input: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def note_num(nid: str) -> int:
    return int(nid.removeprefix("KV"))


def add_pipe(value: str, item: str) -> str:
    parts = [x for x in (value or "").split("|") if x]
    if item not in parts:
        parts.append(item)
    return "|".join(parts)


def add_tags(value: str, *items: str) -> str:
    tags = {x for x in (value or "").split() if x}
    tags.update(x for x in items if x)
    return " ".join(sorted(tags))


def upsert_metric(rows: list[dict[str, str]], metric: str, value: int | str) -> None:
    for row in rows:
        if row.get("Metric") == metric:
            row["Value"] = str(value)
            return
    rows.append({"Metric": metric, "Value": str(value)})


def source_key(order: str, entry: str) -> str:
    clean = " ".join((entry or "").strip().replace("’", "'").replace("‘", "'").split()).casefold()
    return f"nce1-o{int(order):04d}|{clean}"


def main() -> None:
    for p in (SRC, DECISIONS, TARGETS, REG_EXT, SOURCE_EXT, MASTER, OCC, LEARNER, LEARNER_REVIEW, STATS):
        if not p.exists():
            raise SystemExit(f"Missing NCE1 overlay input: {p.relative_to(ROOT)}")

    source_rows = read_csv(SRC)
    source_by_order = {r["CurriculumOrder"].strip(): (i, r) for i, r in enumerate(source_rows, start=2)}
    if len(source_by_order) != 906:
        raise SystemExit(f"Unexpected NCE1 source order coverage: {len(source_by_order)}")

    decisions = read_csv(DECISIONS)
    targets = {r["CurriculumOrder"].strip(): r for r in read_csv(TARGETS)}
    reg_ext = read_csv(REG_EXT)
    reg_by_id = {r["NoteID"].strip(): r for r in reg_ext}
    group_to_id = {
        r["PrimaryOriginKey"].strip().removeprefix(CREATED_SOURCE + "|"): r["NoteID"].strip()
        for r in reg_ext
        if r.get("Status", "").strip() == "active"
        and r.get("CreatedSource", "").strip() == CREATED_SOURCE
        and r.get("PrimaryOriginKey", "").strip().startswith(CREATED_SOURCE + "|")
    }
    source_map = {
        (r.get("SourceID", "").strip(), r.get("SourceEdition", "").strip(), r.get("SourceItemKey", "").strip()): r
        for r in read_csv(SOURCE_EXT)
        if r.get("Status", "").strip() == "confirmed"
    }

    note_orders: dict[str, list[str]] = defaultdict(list)
    new_ids: set[str] = set()
    reused_ids: set[str] = set()
    morphology_orders: set[str] = set()
    for d in decisions:
        orders = [x.strip() for x in d.get("OccurrenceOrders", "").split(" || ") if x.strip()]
        decision = d.get("Decision", "").strip()
        if decision == "morphology-only":
            morphology_orders.update(orders)
            continue
        if decision == "reuse-existing":
            nid = d.get("DecisionNoteID", "").strip()
            reused_ids.add(nid)
        elif decision == "new-stable-identity":
            group = d.get("DecisionIdentityGroup", "").strip()
            nid = group_to_id.get(group, "")
            if not nid:
                raise SystemExit(f"Missing NCE1 allocation for {group}")
            new_ids.add(nid)
        else:
            raise SystemExit(f"Unexpected NCE1 decision: {decision!r}")
        for order in orders:
            _, src = source_by_order[order]
            key = source_key(order, src["Entry"])
            mapping = source_map.get((SOURCE_ID, SOURCE_EDITION, key))
            if mapping is None or mapping.get("NoteID", "").strip() != nid:
                raise SystemExit(f"Missing/drifted NCE1 source mapping: {order} {key} -> {nid}")
            note_orders[nid].append(order)

    mapped = sum(len(v) for v in note_orders.values())
    if mapped + len(morphology_orders) != 906:
        raise SystemExit(f"NCE1 occurrence decision closure mismatch: mapped={mapped} morphology={len(morphology_orders)}")

    master_rows = read_csv(MASTER)
    learner_rows = read_csv(LEARNER)
    occ_rows = read_csv(OCC)
    review_rows = read_csv(LEARNER_REVIEW)
    stats = read_csv(STATS)
    master_fields = list(master_rows[0].keys())
    learner_fields = list(learner_rows[0].keys())
    master_by = {r["NoteID"].strip(): r for r in master_rows}
    learner_by = {r["NoteID"].strip(): r for r in learner_rows}

    for nid in reused_ids:
        if nid not in master_by:
            raise SystemExit(f"Reused NCE1 Note absent from derived Master: {nid}")
        m = master_by[nid]
        m["Sources"] = add_pipe(m.get("Sources", ""), SOURCE_ID)
        for order in sorted(set(note_orders[nid]), key=int):
            _, src = source_by_order[order]
            book = f"{SOURCE_ID}::{SOURCE_EDITION}::Lesson{src['LessonStart']}-{src['LessonEnd']}"
            m["SourceBooks"] = add_pipe(m.get("SourceBooks", ""), book)
        m["Tags"] = add_tags(m.get("Tags", ""), f"source::{SOURCE_ID}", f"source::{SOURCE_ID}::edition::{SOURCE_EDITION}", "scope::klose::nce1-current")

    for nid in sorted(new_ids, key=note_num):
        if nid in master_by:
            raise SystemExit(f"New NCE1 Note unexpectedly already exists in derived Master: {nid}")
        reg = reg_by_id[nid]
        orders = sorted(set(note_orders[nid]), key=int)
        first_order = orders[0]
        _, first = source_by_order[first_order]
        meanings: list[str] = []
        books: list[str] = []
        for order in orders:
            _, src = source_by_order[order]
            target = targets[order]["TargetMeaning"].strip()
            if target and target not in meanings:
                meanings.append(target)
            book = f"{SOURCE_ID}::{SOURCE_EDITION}::Lesson{src['LessonStart']}-{src['LessonEnd']}"
            if book not in books:
                books.append(book)
        master = {
            "NoteID": nid,
            "CanonicalWord": reg["CanonicalWord"].strip(),
            "MatchKey": reg["MatchKey"].strip(),
            "SenseLabel": reg["SenseLabel"].strip(),
            "Word": reg["CanonicalWord"].strip(),
            "British": "",
            "American": "",
            "MeaningPrimary": reg["SenseLabel"].strip(),
            "MeaningRaw": " | ".join(meanings),
            "FirstSource": SOURCE_ID,
            "FirstSourceBook": f"{SOURCE_EDITION}::Lesson{first['LessonStart']}-{first['LessonEnd']}",
            "FirstGrade": "",
            "FirstSemester": "",
            "Sources": SOURCE_ID,
            "SourceBooks": "|".join(books),
            "Released": "no",
            "Tags": " ".join(sorted({f"source::{SOURCE_ID}", f"source::{SOURCE_ID}::edition::{SOURCE_EDITION}", "scope::klose::nce1-current", f"learner::klose::level::{LEVEL}"})),
        }
        master_rows.append(master); master_by[nid] = master
        learner = {field: "" for field in learner_fields}
        learner.update({
            "NoteID": nid, "LearnerProfile": PROFILE, "LearnerLevel": LEVEL, "PromptHint": "",
            "ExampleSentence": "", "ExampleTranslation": "",
            "PresentationStatus": "nce1-current-pending", "PresentationSource": "klose:nce1-current",
        })
        learner_rows.append(learner); learner_by[nid] = learner

    occ_fields = ["NoteID", "SourceID", "SourceEdition", "SourceBook", "Grade", "Semester", "Unit", "SourceWord", "SourceFile", "SourceRow", "Page"]
    for nid, orders in note_orders.items():
        for order in sorted(set(orders), key=int):
            row_no, src = source_by_order[order]
            occ_rows.append({
                "NoteID": nid, "SourceID": SOURCE_ID, "SourceEdition": SOURCE_EDITION,
                "SourceBook": "New Concept English 1", "Grade": "", "Semester": "",
                "Unit": f"Lesson{src['LessonStart']}-{src['LessonEnd']}", "SourceWord": src["Entry"].strip(),
                "SourceFile": SRC.name, "SourceRow": str(row_no), "Page": "",
            })

    existing_review = {r.get("NoteID", "").strip() for r in review_rows}
    for nid in sorted(new_ids, key=note_num):
        if nid not in existing_review:
            review_rows.append({
                "NoteID": nid, "Word": master_by[nid]["Word"], "FirstGrade": "", "ExampleSentence": "",
                "Reason": EXPECTED_REASON,
            })

    master_rows.sort(key=lambda r: note_num(r["NoteID"]))
    learner_rows.sort(key=lambda r: note_num(r["NoteID"]))
    occ_rows.sort(key=lambda r: (note_num(r["NoteID"]), r.get("SourceID", ""), r.get("SourceEdition", ""), r.get("Unit", ""), int(r.get("SourceRow", "0") or 0)))
    review_rows.sort(key=lambda r: note_num(r["NoteID"]))
    write_csv(MASTER, master_fields, master_rows)
    write_csv(LEARNER, learner_fields, learner_rows)
    write_csv(OCC, occ_fields, occ_rows)
    write_csv(LEARNER_REVIEW, ["NoteID", "Word", "FirstGrade", "ExampleSentence", "Reason"], review_rows)

    upsert_metric(stats, "nce1_source_occurrences_mapped", mapped)
    upsert_metric(stats, "nce1_morphology_only_occurrences", len(morphology_orders))
    upsert_metric(stats, "nce1_new_stable_notes", len(new_ids))
    upsert_metric(stats, "nce1_reused_notes", len(reused_ids))
    upsert_metric(stats, "nce1_unique_notes", len(note_orders))
    upsert_metric(stats, "master_notes", len(master_rows))
    upsert_metric(stats, "inventory_notes", len(master_rows))
    upsert_metric(stats, "source_occurrences", len(occ_rows))
    write_csv(STATS, ["Metric", "Value"], stats)
    print(f"Applied NCE1 overlay: new={len(new_ids)} reused={len(reused_ids)} unique={len(note_orders)} mapped={mapped} morphology={len(morphology_orders)}")


if __name__ == "__main__":
    main()
