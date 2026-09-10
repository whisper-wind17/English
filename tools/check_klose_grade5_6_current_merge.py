#!/usr/bin/env python3
"""Independent completion check for Klose Grade 5-6 current Vocabulary merge.

This checker derives the accepted current-learning set from committed reconciliation,
Stable identity/source mappings, Grade-4 current mappings and Learning Admission.
Source provenance remains audit metadata and is intentionally not a learning gate.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master"
LEARNER = BASE / "learner"
REVIEW = BASE / "review"
REC = REVIEW / "grade5_6_reconciliation"

SCOPE = LEARNER / "grade5_6_learning_scope.json"
CANDIDATES = REC / "vocabulary_candidates.csv"
DECISIONS = REC / "vocabulary_decisions.csv"
REGISTRY = MASTER / "note_registry.csv"
REGISTRY_EXT = MASTER / "note_registry_extensions.csv"
SOURCE_EXT = MASTER / "source_identity_extensions.csv"
VOCAB_MASTER = MASTER / "vocabulary_master.csv"
LEARNER_CURRENT = LEARNER / "current.csv"
ADMISSION = LEARNER / "learning_admission.csv"
LEARNER_REVIEW = REVIEW / "learner_review.csv"
RELEASE = MASTER / "release_registry.csv"
RELEASE_EXT = MASTER / "release_registry_extensions.csv"
REUSE_FACTS = MASTER / "grade5_6_reuse_fact_overrides.csv"

G4_RE = re.compile(r"^grade4-(upper|lower)-u(\d+)-o(\d+)\|")
G56_RE = re.compile(r"^grade([56])-(upper|lower)-u(\d+)-o(\d+)\|")
SEM_RANK = {"upper": 0, "lower": 1}
G56_ORIGIN_PREFIX = "klose-grade5-6-current|"


def fail(msg: str) -> None:
    raise SystemExit(f"Grade 5-6 current merge FAIL: {msg}")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def note_num(nid: str) -> int:
    m = re.fullmatch(r"KV(\d{6})", nid)
    if m is None:
        fail(f"invalid NoteID: {nid!r}")
    return int(m.group(1))


def split_occ(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(" || ") if x.strip()]


def main() -> None:
    scope = json.loads(SCOPE.read_text(encoding="utf-8"))
    if scope.get("ScopeStatus") != "accepted":
        fail("Grade 5-6 learning scope is not accepted")
    if scope.get("SourceProvenanceAffectsLearningAdmission") is not False:
        fail("source provenance has incorrectly become a learning-admission gate")
    if scope.get("StableIdentityAllocationAuthorized") is not True:
        fail("Stable identity allocation is not authorized by current learning scope")
    books = scope.get("Books", {})
    if set(books) != {"5上", "5下", "6上", "6下"} or not all(v.get("Accepted") is True for v in books.values()):
        fail("all four Grade 5-6 books are not explicitly accepted")

    candidates = read_csv(CANDIDATES)
    decisions = read_csv(DECISIONS)
    if len(candidates) != 504 or len(decisions) != 504:
        fail(f"reconciliation coverage changed: candidates={len(candidates)} decisions={len(decisions)}")
    cand_by_id = {r.get("ProvisionalIdentityKey", "").strip(): r for r in candidates}
    dec_by_id = {r.get("ProvisionalIdentityKey", "").strip(): r for r in decisions}
    if "" in cand_by_id or len(cand_by_id) != len(candidates) or set(cand_by_id) != set(dec_by_id):
        fail("candidate/decision key closure failed")
    decision_counts = Counter(r.get("Decision", "").strip() for r in decisions)
    expected_decisions = Counter({
        "reuse-existing": 153,
        "new-stable-identity": 296,
        "morphology-only": 45,
        "held": 10,
    })
    if decision_counts != expected_decisions:
        fail(f"reconciliation decision counts drifted: {dict(decision_counts)}")

    new_groups = {
        r.get("DecisionIdentityGroup", "").strip()
        for r in decisions if r.get("Decision", "").strip() == "new-stable-identity"
    }
    if len(new_groups) != 288 or any(not g.startswith("new::") for g in new_groups):
        fail(f"unexpected new identity-group closure: {len(new_groups)}")

    registry_rows = [
        r for p in (REGISTRY, REGISTRY_EXT) for r in read_csv(p)
        if r.get("Status", "").strip() == "active"
    ]
    registry_ids = {r.get("NoteID", "").strip() for r in registry_rows}
    if len(registry_rows) != len(registry_ids) or len(registry_ids) != 1189:
        fail(f"unexpected Stable registry state: rows={len(registry_rows)} unique={len(registry_ids)}")

    allocations: dict[str, str] = {}
    for row in read_csv(REGISTRY_EXT):
        origin = row.get("PrimaryOriginKey", "").strip()
        if not origin.startswith(G56_ORIGIN_PREFIX):
            continue
        if row.get("Status", "").strip() != "active":
            continue
        group = origin[len(G56_ORIGIN_PREFIX):]
        nid = row.get("NoteID", "").strip()
        if group in allocations or nid not in registry_ids:
            fail(f"invalid/duplicate Grade 5-6 Stable allocation: {origin}")
        allocations[group] = nid
    if set(allocations) != new_groups or len(set(allocations.values())) != len(new_groups):
        fail("reviewed new groups are not in one-to-one active Stable allocation")

    expected_g56_note_ids: set[str] = set()
    for cid, cand in cand_by_id.items():
        dec = dec_by_id[cid]
        decision = dec.get("Decision", "").strip()
        if decision == "reuse-existing":
            expected_g56_note_ids.add(dec.get("DecisionNoteID", "").strip())
        elif decision == "new-stable-identity":
            expected_g56_note_ids.add(allocations[dec.get("DecisionIdentityGroup", "").strip()])

    # Source identity mappings are the authoritative admitted lexical occurrence set.
    g4_coords: dict[str, tuple[int, int, int, int, int]] = {}
    g56_coords: dict[str, tuple[int, int, int, int, int]] = {}
    g56_mapping_keys: set[str] = set()
    for row in read_csv(SOURCE_EXT):
        if row.get("Status", "").strip() != "confirmed":
            continue
        key = row.get("SourceItemKey", "").strip()
        nid = row.get("NoteID", "").strip()
        m4 = G4_RE.match(key)
        if (
            m4 is not None
            and row.get("SourceID", "").strip() == "rj_start1"
            and row.get("SourceEdition", "").strip() == "klose-current"
        ):
            sem, unit, order = m4.groups()
            c = (4, SEM_RANK[sem], int(unit), int(order), note_num(nid))
            g4_coords[nid] = min(g4_coords.get(nid, c), c)
            continue
        m56 = G56_RE.match(key)
        if m56 is not None:
            if key in g56_mapping_keys:
                fail(f"duplicate Grade 5-6 source mapping key: {key}")
            g56_mapping_keys.add(key)
            grade, sem, unit, order = m56.groups()
            c = (int(grade), SEM_RANK[sem], int(unit), int(order), note_num(nid))
            g56_coords[nid] = min(g56_coords.get(nid, c), c)

    if len(g56_mapping_keys) != 454:
        fail(f"expected 454 mapped Grade 5-6 lexical occurrences, got {len(g56_mapping_keys)}")
    if set(g56_coords) != expected_g56_note_ids:
        fail(
            f"Grade 5-6 unique NoteID closure drifted: mapped={len(g56_coords)} expected={len(expected_g56_note_ids)}"
        )
    if len(g4_coords) != 221:
        fail(f"expected 221 actual Grade-4 current NoteIDs, got {len(g4_coords)}")

    # Independently derive skipped occurrence keys from reconciliation.
    mapped_from_decisions: set[str] = set()
    skipped: set[str] = set()
    for cid, cand in cand_by_id.items():
        d = dec_by_id[cid].get("Decision", "").strip()
        occs = set(split_occ(cand.get("OccurrenceKeys", "")))
        if d in {"reuse-existing", "new-stable-identity"}:
            mapped_from_decisions |= occs
        else:
            skipped |= occs
    if len(mapped_from_decisions) != 454 or len(skipped) != 55 or mapped_from_decisions & skipped:
        fail(
            f"reconciliation occurrence partition invalid: mapped={len(mapped_from_decisions)} "
            f"skipped={len(skipped)} overlap={len(mapped_from_decisions & skipped)}"
        )
    if mapped_from_decisions != g56_mapping_keys:
        fail("persistent Grade 5-6 source mappings do not equal reviewed lexical occurrence set")

    master_rows = read_csv(VOCAB_MASTER)
    learner_rows = read_csv(LEARNER_CURRENT)
    master_by_id = {r.get("NoteID", "").strip(): r for r in master_rows}
    learner_by_id = {r.get("NoteID", "").strip(): r for r in learner_rows}
    if len(master_by_id) != len(registry_ids) or len(master_by_id) != len(master_rows):
        fail(f"derived Vocabulary Master does not match active Stable registry: {len(master_rows)}")
    if set(master_by_id) != registry_ids:
        fail("derived Vocabulary Master does not cover the current Stable registry exactly")
    if set(learner_by_id) != registry_ids:
        fail("learner/current does not cover the current Stable registry exactly")

    new_ids = set(allocations.values())
    for nid in new_ids:
        if master_by_id[nid].get("Released", "").strip() != "no":
            fail(f"new Grade 5-6 Note was prematurely released: {nid}")
        if learner_by_id[nid].get("PresentationStatus", "").strip() != "grade5-6-current-pending":
            fail(f"new Grade 5-6 Note lacks pending learner presentation state: {nid}")

    review_ids = {r.get("NoteID", "").strip() for r in read_csv(LEARNER_REVIEW)}
    if review_ids != new_ids:
        fail(f"learner review queue must equal active new Grade 5-6 Notes: queue={len(review_ids)} new={len(new_ids)}")

    release_ids: set[str] = set()
    for path in (RELEASE, RELEASE_EXT):
        for row in read_csv(path):
            nid = row.get("NoteID", "").strip()
            if not nid or nid in release_ids:
                fail(f"invalid/duplicate release registry NoteID: {nid!r}")
            release_ids.add(nid)
    if len(release_ids) != 638:
        fail(f"unexpected existing released set: {len(release_ids)}")
    if new_ids & release_ids:
        fail("new Grade 5-6 Notes leaked into Release registry")

    # Admission must equal Grade4-current UNION accepted Grade5-6 current, ordered by
    # earliest curriculum coordinate; release state must not alter this curriculum set.
    earliest = dict(g4_coords)
    for nid, c in g56_coords.items():
        earliest[nid] = min(earliest.get(nid, c), c)
    expected_current = set(earliest)
    if not expected_current:
        fail("derived current curriculum is empty")
    expected_order = {
        nid: f"{index:06d}"
        for index, (nid, _) in enumerate(sorted(earliest.items(), key=lambda item: item[1]), start=1)
    }

    admission_rows = [
        r for r in read_csv(ADMISSION)
        if r.get("LearnerProfile", "").strip() == "klose" and r.get("LearnerLevel", "").strip() == "4"
    ]
    admission_by_id = {r.get("NoteID", "").strip(): r for r in admission_rows}
    if len(admission_by_id) != len(admission_rows):
        fail("duplicate Learning Admission NoteID")
    allowed = {nid for nid, r in admission_by_id.items() if r.get("Status", "").strip() == "allowed"}
    held = {nid for nid, r in admission_by_id.items() if r.get("Status", "").strip() == "held"}
    if allowed != expected_current:
        fail(f"Learning Admission allowed set drifted: got={len(allowed)} want={len(expected_current)}")
    if held != release_ids - expected_current:
        fail(f"Learning Admission held set drifted: got={len(held)} want={len(release_ids-expected_current)}")
    if set(admission_by_id) != release_ids | expected_current:
        fail("Learning Admission universe must equal released UNION current curriculum")
    for nid in allowed:
        row = admission_by_id[nid]
        if row.get("LearningOrder", "").strip() != expected_order[nid]:
            fail(f"LearningOrder drift: {nid} got={row.get('LearningOrder')} want={expected_order[nid]}")
        if nid in g4_coords:
            if row.get("Stage", "").strip() != "stage::grade4-current":
                fail(f"Grade-4 current Note has wrong stage: {nid}")
        elif row.get("Stage", "").strip() != "stage::grade5-6-current":
            fail(f"Grade 5-6 current Note has wrong stage: {nid}")

    # Narrow IPA facts for reused/current released Notes, including reviewed dedup
    # survivors, must be present without requiring identity or learner-content rewrite.
    reuse_fact_ids = {r.get("NoteID", "").strip() for r in read_csv(REUSE_FACTS)}
    expected_reuse_fact_ids = {
        "KV000158", "KV000193", "KV000195", "KV000303", "KV000307",
        "KV000327", "KV000359", "KV000483", "KV000500",
    }
    if reuse_fact_ids != expected_reuse_fact_ids:
        fail(f"unexpected Grade 5-6 reuse fact override set: {sorted(reuse_fact_ids)}")
    for nid in reuse_fact_ids:
        if not master_by_id[nid].get("British", "").strip() or not master_by_id[nid].get("American", "").strip():
            fail(f"Grade 5-6 reused/current Note still lacks IPA: {nid}")

    print(
        "Klose Grade 5-6 current Vocabulary merge OK: "
        f"stable_registry={len(registry_ids)}, new_stable={len(new_ids)}, "
        f"mapped_occurrences={len(g56_mapping_keys)}, skipped_occurrences={len(skipped)}, "
        f"grade5_6_unique={len(g56_coords)}, grade4_unique={len(g4_coords)}, "
        f"current_curriculum={len(expected_current)}, learner_pending={len(review_ids)}, "
        "released_unchanged=638, publish_not_authorized"
    )


if __name__ == "__main__":
    main()
