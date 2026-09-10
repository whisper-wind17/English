#!/usr/bin/env python3
"""Overlay accepted Grade 5-6 Vocabulary scope onto the Klose derived vocabulary state.

Persistent Stable identities/source mappings must already exist. New Grade 5-6 Notes
enter Master + Learner Presentation as unreleased/pending; reused Notes keep their
existing facts and review history. Learning admission is built separately.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER_DIR = BASE / "master"
LEARNER_DIR = BASE / "learner"
REVIEW_DIR = BASE / "review"
SRC = BASE / "source_reference"
REC = REVIEW_DIR / "grade5_6_reconciliation"
SOURCE = SRC / "klose-actual-grade5-6-vocabulary.csv"
CANDIDATES = REC / "vocabulary_candidates.csv"
DECISIONS = REC / "vocabulary_decisions.csv"
REGISTRY_EXT = MASTER_DIR / "note_registry_extensions.csv"
SOURCE_EXT = MASTER_DIR / "source_identity_extensions.csv"
MASTER = MASTER_DIR / "vocabulary_master.csv"
OCCURRENCES = MASTER_DIR / "source_occurrences.csv"
LEARNER = LEARNER_DIR / "current.csv"
LEARNER_REVIEW = REVIEW_DIR / "learner_review.csv"
STATS = MASTER_DIR / "build_stats.csv"
CREATED_SOURCE = "klose-grade5-6-current"
ORIGIN_PREFIX = CREATED_SOURCE + "|"
PROFILE = "klose"
LEVEL = "4"
SEM = {"上": "upper", "下": "lower"}
SEM_RANK = {"upper": 0, "lower": 1}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'")
    value = re.sub(r"\s+", " ", value.strip())
    return value.casefold()


def source_key(row: dict[str, str]) -> str:
    sem = SEM[row["Semester"].strip()]
    return f"grade{int(row['Grade'])}-{sem}-u{int(row['Unit']):02d}-o{int(row['Order']):03d}|{norm(row['Entry'])}"


def coord(key: str) -> tuple[int, int, int, int, str]:
    m = re.match(r"^grade([56])-(upper|lower)-u(\d+)-o(\d+)\|(.+)$", key)
    if m is None:
        raise SystemExit(f"Invalid Grade 5-6 source key: {key}")
    g, s, u, o, word = m.groups()
    return int(g), SEM_RANK[s], int(u), int(o), word


def split_occurrences(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(" || ") if x.strip()]


def note_num(note_id: str) -> int:
    return int(note_id.removeprefix("KV"))


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


def main() -> None:
    required = (SOURCE, CANDIDATES, DECISIONS, REGISTRY_EXT, SOURCE_EXT, MASTER, OCCURRENCES, LEARNER, LEARNER_REVIEW, STATS)
    for path in required:
        if not path.exists():
            raise SystemExit(f"Missing Grade 5-6 overlay input: {path.relative_to(ROOT)}")

    source_rows = read_csv(SOURCE)
    source_by_key: dict[str, tuple[int, dict[str, str]]] = {}
    for row_no, row in enumerate(source_rows, start=2):
        key = source_key(row)
        if key in source_by_key:
            raise SystemExit(f"Duplicate source key: {key}")
        source_by_key[key] = (row_no, row)

    candidates = read_csv(CANDIDATES)
    decisions = {r["ProvisionalIdentityKey"].strip(): r for r in read_csv(DECISIONS)}
    reg_ext = read_csv(REGISTRY_EXT)
    group_to_id: dict[str, str] = {}
    reg_by_id = {r["NoteID"].strip(): r for r in reg_ext}
    for row in reg_ext:
        origin = row.get("PrimaryOriginKey", "").strip()
        if origin.startswith(ORIGIN_PREFIX):
            group_to_id[origin[len(ORIGIN_PREFIX):]] = row["NoteID"].strip()
    if len(group_to_id) != 293:
        raise SystemExit(f"Expected 293 allocated Grade 5-6 groups before overlay, got {len(group_to_id)}")

    source_mappings = {
        (r.get("SourceID", "").strip(), r.get("SourceEdition", "").strip(), r.get("SourceItemKey", "").strip()): r
        for r in read_csv(SOURCE_EXT)
        if r.get("Status", "").strip() == "confirmed"
    }

    note_source_keys: dict[str, list[str]] = defaultdict(list)
    new_note_ids: set[str] = set()
    reused_note_ids: set[str] = set()
    approved_occurrences: set[str] = set()
    for cand in candidates:
        cid = cand["ProvisionalIdentityKey"].strip()
        dec = decisions.get(cid)
        if dec is None:
            raise SystemExit(f"Missing decision for {cid}")
        decision = dec.get("Decision", "").strip()
        if decision in {"morphology-only", "held"}:
            continue
        if decision == "reuse-existing":
            nid = dec.get("DecisionNoteID", "").strip()
            reused_note_ids.add(nid)
        elif decision == "new-stable-identity":
            group = dec.get("DecisionIdentityGroup", "").strip()
            nid = group_to_id.get(group, "")
            if not nid:
                raise SystemExit(f"Allocated NoteID missing for {group}")
            new_note_ids.add(nid)
        else:
            raise SystemExit(f"Unexpected decision for {cid}: {decision!r}")
        for key in split_occurrences(cand["OccurrenceKeys"]):
            _, src = source_by_key[key]
            mapping_key = (src["SourceID"].strip(), src["SourceEdition"].strip(), key)
            mapping = source_mappings.get(mapping_key)
            if mapping is None or mapping.get("NoteID", "").strip() != nid:
                raise SystemExit(f"Persistent source mapping missing/drifted for {key}->{nid}")
            note_source_keys[nid].append(key)
            approved_occurrences.add(key)

    if set(group_to_id.values()) != new_note_ids:
        raise SystemExit("Allocated Grade 5-6 identity set is not fully represented by reviewed source decisions")

    master_rows = read_csv(MASTER)
    learner_rows = read_csv(LEARNER)
    occurrence_rows = read_csv(OCCURRENCES)
    review_rows = read_csv(LEARNER_REVIEW)
    stats = read_csv(STATS)
    master_fields = list(master_rows[0].keys())
    learner_fields = list(learner_rows[0].keys())
    master_by_id = {r["NoteID"].strip(): r for r in master_rows}
    learner_by_id = {r["NoteID"].strip(): r for r in learner_rows}

    # Reused identities gain Grade 5-6 provenance only; their existing learning facts stay intact.
    for nid in reused_note_ids:
        if nid not in master_by_id:
            raise SystemExit(f"Reused Grade 5-6 NoteID missing from derived Master: {nid}")
        row = master_by_id[nid]
        for key in sorted(set(note_source_keys[nid]), key=coord):
            _, src = source_by_key[key]
            book = f"{src['SourceID'].strip()}::{src['SourceEdition'].strip()}::{src['Grade'].strip()}年级{src['Semester'].strip()}"
            row["Sources"] = add_pipe(row.get("Sources", ""), src["SourceID"].strip())
            row["SourceBooks"] = add_pipe(row.get("SourceBooks", ""), book)
            row["Tags"] = add_tags(
                row.get("Tags", ""),
                f"source::{src['SourceID'].strip()}",
                f"source::{src['SourceID'].strip()}::edition::{src['SourceEdition'].strip()}",
                f"source::{src['SourceID'].strip()}::grade::{src['Grade'].strip()}",
                f"source::{src['SourceID'].strip()}::grade::{src['Grade'].strip()}::{src['Semester'].strip()}",
                "scope::klose::grade5-6-current",
            )

    # Newly allocated identities enter the durable derived Master but remain unreleased
    # until learner presentation/fact enrichment passes its own review gates.
    appended = 0
    for nid in sorted(new_note_ids, key=note_num):
        if nid in master_by_id:
            raise SystemExit(f"New Grade 5-6 allocation unexpectedly already exists in derived Master: {nid}")
        reg = reg_by_id[nid]
        keys = sorted(set(note_source_keys[nid]), key=coord)
        first_key = keys[0]
        _, first = source_by_key[first_key]
        meanings: list[str] = []
        books: list[str] = []
        sources: list[str] = []
        tags = {"scope::klose::grade5-6-current", f"learner::klose::level::{LEVEL}"}
        for key in keys:
            _, src = source_by_key[key]
            meaning = src["Meaning"].strip()
            if meaning and meaning not in meanings:
                meanings.append(meaning)
            sid, sed = src["SourceID"].strip(), src["SourceEdition"].strip()
            if sid not in sources:
                sources.append(sid)
            book = f"{sid}::{sed}::{src['Grade'].strip()}年级{src['Semester'].strip()}"
            if book not in books:
                books.append(book)
            tags.update({
                f"source::{sid}",
                f"source::{sid}::edition::{sed}",
                f"source::{sid}::grade::{src['Grade'].strip()}",
                f"source::{sid}::grade::{src['Grade'].strip()}::{src['Semester'].strip()}",
            })
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
            "FirstSource": first["SourceID"].strip(),
            "FirstSourceBook": f"{first['SourceEdition'].strip()}::{first['Grade'].strip()}年级{first['Semester'].strip()}",
            "FirstGrade": first["Grade"].strip(),
            "FirstSemester": first["Semester"].strip(),
            "Sources": "|".join(sources),
            "SourceBooks": "|".join(books),
            "Released": "no",
            "Tags": " ".join(sorted(tags)),
        }
        master_rows.append(master)
        master_by_id[nid] = master
        learner = {field: "" for field in learner_fields}
        learner.update({
            "NoteID": nid,
            "LearnerProfile": PROFILE,
            "LearnerLevel": LEVEL,
            "PromptHint": "",
            "ExampleSentence": "",
            "ExampleTranslation": "",
            "PresentationStatus": "grade5-6-current-pending",
            "PresentationSource": "klose:grade5_6_current",
        })
        learner_rows.append(learner)
        learner_by_id[nid] = learner
        appended += 1

    # Source occurrences are rebuilt from the clean legacy+Grade4 derived state on every build.
    occurrence_fields = ["NoteID", "SourceID", "SourceEdition", "SourceBook", "Grade", "Semester", "Unit", "SourceWord", "SourceFile", "SourceRow", "Page"]
    for nid, keys in note_source_keys.items():
        for key in sorted(set(keys), key=coord):
            row_no, src = source_by_key[key]
            occurrence_rows.append({
                "NoteID": nid,
                "SourceID": src["SourceID"].strip(),
                "SourceEdition": src["SourceEdition"].strip(),
                "SourceBook": f"{src['Grade'].strip()}年级{src['Semester'].strip()}",
                "Grade": src["Grade"].strip(),
                "Semester": src["Semester"].strip(),
                "Unit": src["Unit"].strip(),
                "SourceWord": src["Entry"].strip(),
                "SourceFile": SOURCE.name,
                "SourceRow": str(row_no),
                "Page": src["Page"].strip(),
            })

    review_by_id = {r.get("NoteID", "").strip(): r for r in review_rows}
    for nid in sorted(new_note_ids, key=note_num):
        if nid not in review_by_id:
            master = master_by_id[nid]
            review_rows.append({
                "NoteID": nid,
                "Word": master["Word"],
                "FirstGrade": master["FirstGrade"],
                "ExampleSentence": "",
                "Reason": "grade5-6-current-new-note-needs-learner-content-and-lexical-facts",
            })

    master_rows.sort(key=lambda r: note_num(r["NoteID"]))
    learner_rows.sort(key=lambda r: note_num(r["NoteID"]))
    occurrence_rows.sort(key=lambda r: (note_num(r["NoteID"]), r.get("SourceID", ""), r.get("SourceEdition", ""), r.get("SourceBook", ""), int(r.get("SourceRow", "0") or 0)))
    review_rows.sort(key=lambda r: note_num(r["NoteID"]))
    write_csv(MASTER, master_fields, master_rows)
    write_csv(LEARNER, learner_fields, learner_rows)
    write_csv(OCCURRENCES, occurrence_fields, occurrence_rows)
    write_csv(LEARNER_REVIEW, ["NoteID", "Word", "FirstGrade", "ExampleSentence", "Reason"], review_rows)

    upsert_metric(stats, "grade5_6_current_source_occurrences", len(approved_occurrences))
    upsert_metric(stats, "grade5_6_current_new_stable_notes", len(new_note_ids))
    upsert_metric(stats, "grade5_6_current_reused_notes", len(reused_note_ids))
    upsert_metric(stats, "grade5_6_current_unique_notes", len(set(note_source_keys)))
    upsert_metric(stats, "master_notes", len(master_rows))
    upsert_metric(stats, "inventory_notes", len(master_rows))
    upsert_metric(stats, "source_occurrences", len(occurrence_rows))
    write_csv(STATS, ["Metric", "Value"], stats)

    print(
        "Applied Klose Grade 5-6 current Vocabulary overlay: "
        f"new={len(new_note_ids)}, reused_unique={len(reused_note_ids)}, "
        f"current_unique={len(set(note_source_keys))}, mapped_occurrences={len(approved_occurrences)}, "
        f"learner_pending_added={appended}"
    )


if __name__ == "__main__":
    main()
