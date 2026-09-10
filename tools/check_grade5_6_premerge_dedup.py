#!/usr/bin/env python3
"""Independent gate for Grade 5-6 retrospective pre-merge Vocabulary dedup review."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
DIR = BASE / "review" / "grade5_6_premerge_dedup"
CANDIDATES = DIR / "candidates.csv"
DECISIONS = DIR / "decisions.csv"
REGISTRY = BASE / "master" / "note_registry.csv"
REGISTRY_EXT = BASE / "master" / "note_registry_extensions.csv"
GRADE56_SOURCE = "klose-grade5-6-current"

EVIDENCE_FIELDS = (
    "NewNoteID", "OtherNoteID", "NewMatchKey", "OtherMatchKey", "NewSense", "OtherSense"
)
VALID = {"merge-new-into-existing", "keep-distinct", "covered-by-other-merge"}


def fail(msg: str) -> None:
    raise SystemExit(f"Grade 5-6 premerge dedup FAIL: {msg}")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    candidates = read_csv(CANDIDATES)
    decisions = read_csv(DECISIONS)
    if len(candidates) != 38:
        fail(f"candidate count changed: {len(candidates)}")
    if len(decisions) != len(candidates):
        fail(f"decision coverage changed: decisions={len(decisions)} candidates={len(candidates)}")

    cand_by_id = {r.get("CandidateID", "").strip(): r for r in candidates}
    dec_by_id = {r.get("CandidateID", "").strip(): r for r in decisions}
    if "" in cand_by_id or len(cand_by_id) != len(candidates):
        fail("blank/duplicate candidate ID")
    if "" in dec_by_id or len(dec_by_id) != len(decisions) or set(cand_by_id) != set(dec_by_id):
        fail("decision IDs do not exactly cover candidate IDs")

    registry = [r for p in (REGISTRY, REGISTRY_EXT) for r in read_csv(p)]
    reg_by_id = {r.get("NoteID", "").strip(): r for r in registry}
    if len(reg_by_id) != len(registry):
        fail("duplicate Stable NoteID")

    merge_map: dict[str, str] = {}
    decision_counts: Counter[str] = Counter()
    for cid in sorted(cand_by_id):
        cand = cand_by_id[cid]
        dec = dec_by_id[cid]
        for field in EVIDENCE_FIELDS:
            if cand.get(field, "").strip() != dec.get(field, "").strip():
                fail(f"stale decision evidence: {cid} field={field}")
        decision = dec.get("Decision", "").strip()
        target = dec.get("MergeIntoNoteID", "").strip()
        if decision not in VALID:
            fail(f"invalid decision: {cid}->{decision!r}")
        decision_counts[decision] += 1

        new_id = cand["NewNoteID"].strip()
        other_id = cand["OtherNoteID"].strip()
        if new_id not in reg_by_id or other_id not in reg_by_id:
            fail(f"candidate references unknown Stable identity: {cid}")
        if reg_by_id[new_id].get("CreatedSource", "").strip() != GRADE56_SOURCE:
            fail(f"NewNoteID is not a Grade 5-6 allocated identity: {cid}->{new_id}")

        if decision == "merge-new-into-existing":
            if target != other_id:
                fail(f"merge target must equal reviewed OtherNoteID: {cid}")
            if reg_by_id[target].get("CreatedSource", "").strip() == GRADE56_SOURCE:
                fail(f"retrospective dedup merge must preserve older survivor: {cid}->{target}")
            previous = merge_map.setdefault(new_id, target)
            if previous != target:
                fail(f"one incoming identity has multiple merge targets: {new_id}")
        elif decision == "keep-distinct":
            if target:
                fail(f"keep-distinct cannot have merge target: {cid}")

    # covered-by-other-merge rows are secondary pair evidence for an incoming identity
    # that has exactly one canonical migration target elsewhere in this review.
    for cid, dec in dec_by_id.items():
        if dec.get("Decision", "").strip() != "covered-by-other-merge":
            continue
        new_id = dec["NewNoteID"].strip()
        target = dec.get("MergeIntoNoteID", "").strip()
        if not target or merge_map.get(new_id) != target:
            fail(f"covered row is not backed by the same incoming identity's merge: {cid}")

    expected_merge_map = {
        "KV000974": "KV000572",
        "KV001029": "KV000193",
        "KV001030": "KV000307",
        "KV001171": "KV000500",
        "KV001173": "KV000359",
    }
    if merge_map != expected_merge_map:
        fail(f"reviewed migration set drifted: {merge_map}")

    incoming = [r for r in registry if r.get("CreatedSource", "").strip() == GRADE56_SOURCE]
    if len(incoming) != 293:
        fail(f"historical Grade 5-6 allocation count changed: {len(incoming)}")

    print(
        "Grade 5-6 premerge dedup decisions OK: "
        f"candidates={len(candidates)}, decisions={len(decisions)}, "
        f"decision_counts={dict(sorted(decision_counts.items()))}, "
        f"merge_ids={len(merge_map)}, active_after_dedup={len(incoming)-len(merge_map)}"
    )


if __name__ == "__main__":
    main()
