#!/usr/bin/env python3
"""One-shot deterministic source hardening for Grade 5-6 dedup-aware consumers.

This script intentionally uses exact guarded replacements.  It fails closed if the
expected pre-dedup source has drifted, preventing a partial textual rewrite.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one guarded source block in {path}, found {count}")
    p.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    # Allocator: reviewed group count is data-derived; only active historical
    # allocations satisfy current new-stable-identity decisions.
    replace_once(
        "tools/allocate_klose_grade5_6_vocabulary.py",
        '''    if len(group_candidates) != 293:\n        raise SystemExit(f"Expected 293 new identity groups, got {len(group_candidates)}")\n''',
        '''    if not group_candidates:\n        raise SystemExit("No reviewed new identity groups remain for Grade 5-6 allocation")\n''',
    )
    replace_once(
        "tools/allocate_klose_grade5_6_vocabulary.py",
        '''    for row in ext:\n        origin = row.get("PrimaryOriginKey", "").strip()\n        if not origin.startswith(ORIGIN_PREFIX):\n            continue\n        group = origin[len(ORIGIN_PREFIX):]\n''',
        '''    for row in ext:\n        origin = row.get("PrimaryOriginKey", "").strip()\n        if not origin.startswith(ORIGIN_PREFIX):\n            continue\n        if row.get("Status", "").strip() != "active":\n            continue\n        group = origin[len(ORIGIN_PREFIX):]\n''',
    )

    # Derived current overlay: retired merged allocations remain historical rows
    # but are not current active groups.
    replace_once(
        "tools/apply_klose_grade5_6_current.py",
        '''    for row in reg_ext:\n        origin = row.get("PrimaryOriginKey", "").strip()\n        if origin.startswith(ORIGIN_PREFIX):\n            group_to_id[origin[len(ORIGIN_PREFIX):]] = row["NoteID"].strip()\n    if len(group_to_id) != 293:\n        raise SystemExit(f"Expected 293 allocated Grade 5-6 groups before overlay, got {len(group_to_id)}")\n''',
        '''    for row in reg_ext:\n        origin = row.get("PrimaryOriginKey", "").strip()\n        if origin.startswith(ORIGIN_PREFIX) and row.get("Status", "").strip() == "active":\n            group = origin[len(ORIGIN_PREFIX):]\n            if group in group_to_id:\n                raise SystemExit(f"Duplicate active Grade 5-6 allocation group: {group}")\n            group_to_id[group] = row["NoteID"].strip()\n''',
    )

    # Audit remains reproducible after migration by including retired Grade 5-6
    # allocation rows in the historical incoming cohort.
    replace_once(
        "tools/audit_grade5_6_premerge_dedup.py",
        '''    active = [r for r in registry if r.get("Status", "").strip() == "active"]\n    incoming = [r for r in active if r.get("CreatedSource", "").strip() == GRADE56_SOURCE]\n    baseline = [r for r in active if r.get("CreatedSource", "").strip() != GRADE56_SOURCE]\n''',
        '''    active = [r for r in registry if r.get("Status", "").strip() == "active"]\n    incoming = [\n        r for r in registry\n        if r.get("CreatedSource", "").strip() == GRADE56_SOURCE\n        and r.get("Status", "").strip() in {"active", "merged"}\n    ]\n    baseline = [r for r in active if r.get("CreatedSource", "").strip() != GRADE56_SOURCE]\n''',
    )

    # Persistent state: explicitly model a merged Stable identity as historical,
    # require an approved target migration, and forbid source mappings to it.
    replace_once(
        "tools/check_klose_persistent_state.py",
        '''IDENTITY_FIELDS = ("CanonicalWord", "MatchKey", "SenseLabel", "PrimaryOriginKey")\n''',
        '''IDENTITY_FIELDS = ("CanonicalWord", "MatchKey", "SenseLabel", "PrimaryOriginKey")\nVALID_REGISTRY_STATUSES = {"active", "merged"}\n''',
    )
    replace_once(
        "tools/check_klose_persistent_state.py",
        '''        origin = row.get("PrimaryOriginKey", "").strip()\n        if not NOTE_RE.fullmatch(nid):\n''',
        '''        origin = row.get("PrimaryOriginKey", "").strip()\n        status = row.get("Status", "").strip()\n        if status not in VALID_REGISTRY_STATUSES:\n            raise SystemExit(f"Invalid registry status: {nid}->{status!r}")\n        if not NOTE_RE.fullmatch(nid):\n''',
    )
    replace_once(
        "tools/check_klose_persistent_state.py",
        '''    registry_ids = set(ids)\n    check_git_stability(registry)\n\n    source_map = read_csv(SOURCE_MAP)\n''',
        '''    registry_ids = set(ids)\n    registry_by_id = {r["NoteID"].strip(): r for r in registry}\n    check_git_stability(registry)\n\n    migration_rows = read_csv(MIGRATIONS)\n    merge_targets: dict[str, str] = {}\n    for row in migration_rows:\n        if row.get("MigrationType", "").strip() != "identity-merge-dedup" or row.get("Status", "").strip() != "approved":\n            continue\n        source = row.get("NoteID", "").strip()\n        target = row.get("TargetNoteID", "").strip()\n        if not source or not target or source == target or source in merge_targets:\n            raise SystemExit(f"Invalid/duplicate approved identity merge migration: {source}->{target}")\n        if source not in registry_ids or target not in registry_ids:\n            raise SystemExit(f"Identity merge migration references unknown NoteID: {source}->{target}")\n        if registry_by_id[target].get("Status", "").strip() != "active":\n            raise SystemExit(f"Identity merge survivor is not active: {source}->{target}")\n        merge_targets[source] = target\n    merged_ids = {nid for nid, row in registry_by_id.items() if row.get("Status", "").strip() == "merged"}\n    if merged_ids != set(merge_targets):\n        raise SystemExit(\n            f"Merged registry identities must equal approved dedup migrations: merged={sorted(merged_ids)} migrations={sorted(merge_targets)}"\n        )\n\n    source_map = read_csv(SOURCE_MAP)\n''',
    )
    replace_once(
        "tools/check_klose_persistent_state.py",
        '''        if nid not in registry_ids:\n            raise SystemExit(f"Source identity references unknown NoteID: {nid}")\n        if status != "confirmed":\n''',
        '''        if nid not in registry_ids:\n            raise SystemExit(f"Source identity references unknown NoteID: {nid}")\n        if registry_by_id[nid].get("Status", "").strip() != "active":\n            raise SystemExit(f"Legacy Source identity references non-active NoteID: {nid}")\n        if status != "confirmed":\n''',
    )
    replace_once(
        "tools/check_klose_persistent_state.py",
        '''        if nid not in registry_ids:\n            raise SystemExit(f"Source identity extension references unknown NoteID: {nid}")\n        if status not in {"confirmed", "pending"}:\n''',
        '''        if nid not in registry_ids:\n            raise SystemExit(f"Source identity extension references unknown NoteID: {nid}")\n        if registry_by_id[nid].get("Status", "").strip() != "active":\n            raise SystemExit(f"Source identity extension references non-active NoteID: {nid}")\n        if status not in {"confirmed", "pending"}:\n''',
    )

    # Independent current-merge checker: replace pre-dedup fixed cardinalities
    # with the reviewed post-dedup closure and derive downstream set sizes.
    replace_once(
        "tools/check_klose_grade5_6_current_merge.py",
        '''    expected_decisions = Counter({\n        "reuse-existing": 148,\n        "new-stable-identity": 301,\n        "morphology-only": 45,\n        "held": 10,\n    })\n''',
        '''    expected_decisions = Counter({\n        "reuse-existing": 153,\n        "new-stable-identity": 296,\n        "morphology-only": 45,\n        "held": 10,\n    })\n''',
    )
    replace_once(
        "tools/check_klose_grade5_6_current_merge.py",
        '''    if len(new_groups) != 293 or any(not g.startswith("new::") for g in new_groups):\n''',
        '''    if len(new_groups) != 288 or any(not g.startswith("new::") for g in new_groups):\n''',
    )
    replace_once(
        "tools/check_klose_grade5_6_current_merge.py",
        '''    if len(registry_rows) != len(registry_ids) or len(registry_ids) != 1194:\n''',
        '''    if len(registry_rows) != len(registry_ids) or len(registry_ids) != 1189:\n''',
    )
    replace_once(
        "tools/check_klose_grade5_6_current_merge.py",
        '''    for row in read_csv(REGISTRY_EXT):\n        origin = row.get("PrimaryOriginKey", "").strip()\n        if not origin.startswith(G56_ORIGIN_PREFIX):\n            continue\n        group = origin[len(G56_ORIGIN_PREFIX):]\n''',
        '''    for row in read_csv(REGISTRY_EXT):\n        origin = row.get("PrimaryOriginKey", "").strip()\n        if not origin.startswith(G56_ORIGIN_PREFIX):\n            continue\n        if row.get("Status", "").strip() != "active":\n            continue\n        group = origin[len(G56_ORIGIN_PREFIX):]\n''',
    )
    replace_once(
        "tools/check_klose_grade5_6_current_merge.py",
        '''    if set(allocations) != new_groups or len(set(allocations.values())) != 293:\n        fail("293 reviewed new groups are not in one-to-one Stable allocation")\n''',
        '''    if set(allocations) != new_groups or len(set(allocations.values())) != len(new_groups):\n        fail("reviewed new groups are not in one-to-one active Stable allocation")\n\n    expected_g56_note_ids: set[str] = set()\n    for cid, cand in cand_by_id.items():\n        dec = dec_by_id[cid]\n        decision = dec.get("Decision", "").strip()\n        if decision == "reuse-existing":\n            expected_g56_note_ids.add(dec.get("DecisionNoteID", "").strip())\n        elif decision == "new-stable-identity":\n            expected_g56_note_ids.add(allocations[dec.get("DecisionIdentityGroup", "").strip()])\n''',
    )
    replace_once(
        "tools/check_klose_grade5_6_current_merge.py",
        '''    if len(g56_coords) != 432:\n        fail(f"expected 432 unique Grade 5-6 current NoteIDs, got {len(g56_coords)}")\n''',
        '''    if set(g56_coords) != expected_g56_note_ids:\n        fail(\n            f"Grade 5-6 unique NoteID closure drifted: mapped={len(g56_coords)} expected={len(expected_g56_note_ids)}"\n        )\n''',
    )
    replace_once(
        "tools/check_klose_grade5_6_current_merge.py",
        '''    if len(master_by_id) != 1194 or len(master_by_id) != len(master_rows):\n        fail(f"derived Vocabulary Master is not 1194 unique Notes: {len(master_rows)}")\n''',
        '''    if len(master_by_id) != len(registry_ids) or len(master_by_id) != len(master_rows):\n        fail(f"derived Vocabulary Master does not match active Stable registry: {len(master_rows)}")\n''',
    )
    replace_once(
        "tools/check_klose_grade5_6_current_merge.py",
        '''    if review_ids != new_ids:\n        fail(f"learner review queue must equal the 293 new Grade 5-6 Notes: queue={len(review_ids)} new={len(new_ids)}")\n''',
        '''    if review_ids != new_ids:\n        fail(f"learner review queue must equal active new Grade 5-6 Notes: queue={len(review_ids)} new={len(new_ids)}")\n''',
    )
    replace_once(
        "tools/check_klose_grade5_6_current_merge.py",
        '''    if len(expected_current) != 627:\n        fail(f"unexpected total current curriculum size: {len(expected_current)}")\n''',
        '''    if not expected_current:\n        fail("derived current curriculum is empty")\n''',
    )
    replace_once(
        "tools/check_klose_grade5_6_current_merge.py",
        '''        "Klose Grade 5-6 current Vocabulary merge OK: "\n        "stable_registry=1194, new_stable=293, mapped_occurrences=454, skipped_occurrences=55, "\n        "grade5_6_unique=432, grade4_unique=221, current_curriculum=627, "\n        "learner_pending=293, released_unchanged=638, publish_not_authorized"\n''',
        '''        "Klose Grade 5-6 current Vocabulary merge OK: "\n        f"stable_registry={len(registry_ids)}, new_stable={len(new_ids)}, "\n        f"mapped_occurrences={len(g56_mapping_keys)}, skipped_occurrences={len(skipped)}, "\n        f"grade5_6_unique={len(g56_coords)}, grade4_unique={len(g4_coords)}, "\n        f"current_curriculum={len(expected_current)}, learner_pending={len(review_ids)}, "\n        "released_unchanged=638, publish_not_authorized"\n''',
    )

    print("Grade 5-6 dedup consumers hardened")


if __name__ == "__main__":
    main()
