#!/usr/bin/env python3
"""Allocate Stable Vocabulary identities for Klose's accepted Grade 5-6 learning scope.

Source provenance remains traceable but is not a learning-admission gate. This tool
only mutates persistent Vocabulary identity/source-mapping extension registries.
It does not release Notes, generate learner content, publish files, or touch Anki.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master"
SRC = BASE / "source_reference"
REVIEW = BASE / "review" / "grade5_6_reconciliation"
SCOPE = BASE / "learner" / "grade5_6_learning_scope.json"
SOURCE = SRC / "klose-actual-grade5-6-vocabulary.csv"
CANDIDATES = REVIEW / "vocabulary_candidates.csv"
DECISIONS = REVIEW / "vocabulary_decisions.csv"
REGISTRY = MASTER / "note_registry.csv"
REGISTRY_EXT = MASTER / "note_registry_extensions.csv"
SOURCE_EXT = MASTER / "source_identity_extensions.csv"
CREATED_SOURCE = "klose-grade5-6-current"
ORIGIN_PREFIX = CREATED_SOURCE + "|"
NOTE_RE = re.compile(r"^KV(\d{6})$")
SEM = {"上": "upper", "下": "lower"}
SEM_RANK = {"upper": 0, "lower": 1}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


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
    sem = SEM.get(row.get("Semester", "").strip())
    if sem is None:
        raise SystemExit(f"Invalid semester in Grade 5-6 source: {row}")
    return (
        f"grade{int(row['Grade'])}-{sem}-u{int(row['Unit']):02d}-"
        f"o{int(row['Order']):03d}|{norm(row['Entry'])}"
    )


def coord_from_key(key: str) -> tuple[int, int, int, int, str]:
    m = re.match(r"^grade([56])-(upper|lower)-u(\d+)-o(\d+)\|(.+)$", key)
    if m is None:
        raise SystemExit(f"Invalid Grade 5-6 occurrence key: {key!r}")
    grade, sem, unit, order, surface = m.groups()
    return int(grade), SEM_RANK[sem], int(unit), int(order), surface


def note_num(note_id: str) -> int:
    m = NOTE_RE.fullmatch(note_id)
    if m is None:
        raise SystemExit(f"Invalid NoteID: {note_id!r}")
    return int(m.group(1))


def split_occurrences(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(" || ") if x.strip()]


def main() -> None:
    required = (SCOPE, SOURCE, CANDIDATES, DECISIONS, REGISTRY, REGISTRY_EXT, SOURCE_EXT)
    for path in required:
        if not path.exists():
            raise SystemExit(f"Missing Grade 5-6 allocation input: {path.relative_to(ROOT)}")

    scope = json.loads(SCOPE.read_text(encoding="utf-8"))
    if scope.get("ScopeStatus") != "accepted" or scope.get("StableIdentityAllocationAuthorized") is not True:
        raise SystemExit("Grade 5-6 learning scope has not authorized Stable identity allocation")
    if scope.get("SourceProvenanceAffectsLearningAdmission") is not False:
        raise SystemExit("Grade 5-6 scope must keep source provenance independent from learning admission")
    books = scope.get("Books", {})
    if set(books) != {"5上", "5下", "6上", "6下"} or not all(v.get("Accepted") is True for v in books.values()):
        raise SystemExit("All four Grade 5-6 books must be explicitly accepted in current learning scope")

    _, source_rows = read_csv(SOURCE)
    if len(source_rows) != 509:
        raise SystemExit(f"Expected 509 Grade 5-6 source occurrences, got {len(source_rows)}")
    source_by_key: dict[str, dict[str, str]] = {}
    for row in source_rows:
        key = source_key(row)
        if key in source_by_key:
            raise SystemExit(f"Duplicate Grade 5-6 source key: {key}")
        source_by_key[key] = row

    _, candidates = read_csv(CANDIDATES)
    _, decisions = read_csv(DECISIONS)
    if len(candidates) != 504 or len(decisions) != 504:
        raise SystemExit(f"Reconciliation must be closed before allocation: candidates={len(candidates)} decisions={len(decisions)}")
    cand_by_id = {r["ProvisionalIdentityKey"].strip(): r for r in candidates}
    dec_by_id = {r["ProvisionalIdentityKey"].strip(): r for r in decisions}
    if set(cand_by_id) != set(dec_by_id):
        raise SystemExit("Grade 5-6 candidate/decision coverage mismatch")

    reg_fields, legacy = read_csv(REGISTRY)
    ext_fields, ext = read_csv(REGISTRY_EXT)
    if reg_fields != ext_fields:
        raise SystemExit("Legacy and extension registry schemas differ")
    all_registry = legacy + ext
    registry_ids = {r["NoteID"].strip() for r in all_registry}
    max_num = max(note_num(nid) for nid in registry_ids)

    group_candidates: dict[str, list[dict[str, str]]] = defaultdict(list)
    resolved_note_by_candidate: dict[str, str] = {}
    skipped_occurrences: set[str] = set()
    decision_counts: dict[str, int] = defaultdict(int)
    for key in sorted(cand_by_id):
        cand = cand_by_id[key]
        dec = dec_by_id[key]
        decision = dec.get("Decision", "").strip()
        decision_counts[decision] += 1
        occs = split_occurrences(cand.get("OccurrenceKeys", ""))
        if not occs or any(o not in source_by_key for o in occs):
            raise SystemExit(f"Candidate {key} has invalid occurrence coverage")
        if decision == "reuse-existing":
            nid = dec.get("DecisionNoteID", "").strip()
            if nid not in registry_ids:
                raise SystemExit(f"reuse-existing references unknown NoteID: {key}->{nid}")
            resolved_note_by_candidate[key] = nid
        elif decision == "new-stable-identity":
            group = dec.get("DecisionIdentityGroup", "").strip()
            if not group.startswith("new::"):
                raise SystemExit(f"new-stable-identity lacks new:: group: {key}")
            group_candidates[group].append(cand)
        elif decision in {"morphology-only", "held"}:
            skipped_occurrences.update(occs)
        else:
            raise SystemExit(f"Unexpected reconciliation decision: {key}->{decision!r}")

    if not group_candidates:
        raise SystemExit("No reviewed new identity groups remain for Grade 5-6 allocation")

    existing_group_alloc: dict[str, str] = {}
    for row in ext:
        origin = row.get("PrimaryOriginKey", "").strip()
        if not origin.startswith(ORIGIN_PREFIX):
            continue
        if row.get("Status", "").strip() != "active":
            continue
        group = origin[len(ORIGIN_PREFIX):]
        nid = row.get("NoteID", "").strip()
        if not group.startswith("new::") or group in existing_group_alloc:
            raise SystemExit(f"Invalid/duplicate Grade 5-6 allocated origin: {origin!r}")
        existing_group_alloc[group] = nid
    unknown_alloc = set(existing_group_alloc) - set(group_candidates)
    if unknown_alloc:
        raise SystemExit(f"Stale Grade 5-6 allocated groups: {sorted(unknown_alloc)[:10]}")

    def first_coord(group: str) -> tuple[int, int, int, int, str]:
        keys = [o for c in group_candidates[group] for o in split_occurrences(c["OccurrenceKeys"])]
        return min(coord_from_key(o) for o in keys)

    new_allocations = 0
    for group in sorted(group_candidates, key=lambda g: (first_coord(g), g)):
        if group in existing_group_alloc:
            continue
        max_num += 1
        nid = f"KV{max_num:06d}"
        if nid in registry_ids:
            raise SystemExit(f"Allocator produced existing NoteID: {nid}")
        group_rows = group_candidates[group]
        first = min(
            group_rows,
            key=lambda c: min(coord_from_key(o) for o in split_occurrences(c["OccurrenceKeys"])),
        )
        first_occ = min(split_occurrences(first["OccurrenceKeys"]), key=coord_from_key)
        grade, sem_rank, *_ = coord_from_key(first_occ)
        semester = "上" if sem_rank == 0 else "下"
        ext.append({
            "NoteID": nid,
            "CanonicalWord": first.get("Entry", "").strip(),
            "MatchKey": first.get("MatchKey", "").strip(),
            "SenseLabel": first.get("Meaning", "").strip(),
            "PrimaryOriginKey": ORIGIN_PREFIX + group,
            "CreatedSource": CREATED_SOURCE,
            "CreatedSourceBook": f"{grade}年级{semester}",
            "Status": "active",
        })
        registry_ids.add(nid)
        existing_group_alloc[group] = nid
        new_allocations += 1

    ext.sort(key=lambda r: note_num(r["NoteID"].strip()))
    write_csv(REGISTRY_EXT, ext_fields, ext)

    # Resolve every approved lexical source occurrence to a Stable NoteID.
    source_ext_fields, source_ext = read_csv(SOURCE_EXT)
    source_ext_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in source_ext:
        k = (row.get("SourceID", "").strip(), row.get("SourceEdition", "").strip(), row.get("SourceItemKey", "").strip())
        if k in source_ext_by_key:
            raise SystemExit(f"Duplicate existing source identity extension: {k}")
        source_ext_by_key[k] = row

    added_mappings = 0
    mapped_occurrences: set[str] = set()
    for cid, cand in cand_by_id.items():
        dec = dec_by_id[cid]
        decision = dec.get("Decision", "").strip()
        if decision in {"morphology-only", "held"}:
            continue
        nid = (
            dec.get("DecisionNoteID", "").strip()
            if decision == "reuse-existing"
            else existing_group_alloc[dec.get("DecisionIdentityGroup", "").strip()]
        )
        for occ in split_occurrences(cand["OccurrenceKeys"]):
            src = source_by_key[occ]
            k = (src["SourceID"].strip(), src["SourceEdition"].strip(), occ)
            current = source_ext_by_key.get(k)
            if current is not None:
                if current.get("NoteID", "").strip() != nid or current.get("Status", "").strip() != "confirmed":
                    raise SystemExit(f"Existing source mapping disagrees with reviewed Grade 5-6 decision: {k}")
            else:
                row = {
                    "SourceID": k[0],
                    "SourceEdition": k[1],
                    "SourceItemKey": occ,
                    "NoteID": nid,
                    "Decision": "reuse-existing" if decision == "reuse-existing" else "new-learning-unit",
                    "Status": "confirmed",
                }
                source_ext.append(row)
                source_ext_by_key[k] = row
                added_mappings += 1
            mapped_occurrences.add(occ)

    all_occurrences = set(source_by_key)
    if mapped_occurrences & skipped_occurrences:
        raise SystemExit("Mapped and skipped Grade 5-6 occurrence sets overlap")
    if mapped_occurrences | skipped_occurrences != all_occurrences:
        missing = sorted(all_occurrences - mapped_occurrences - skipped_occurrences)
        raise SystemExit(f"Grade 5-6 source coverage incomplete after allocation: {missing[:10]}")

    write_csv(SOURCE_EXT, source_ext_fields, source_ext)
    print(
        "Grade 5-6 Stable Vocabulary allocation OK: "
        f"groups={len(group_candidates)}, newly_allocated={new_allocations}, "
        f"registry_total={len(registry_ids)}, mapped_occurrences={len(mapped_occurrences)}, "
        f"skipped_occurrences={len(skipped_occurrences)}, added_source_mappings={added_mappings}, "
        f"decisions={dict(sorted(decision_counts.items()))}"
    )


if __name__ == "__main__":
    main()
