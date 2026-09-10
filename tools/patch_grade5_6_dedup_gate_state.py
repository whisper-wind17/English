#!/usr/bin/env python3
"""One-shot fail-closed patch for Grade 5-6 post-dedup completion gates.

This script is intentionally deterministic. It updates stale pre-dedup assertions
and the reconciliation status snapshot after the reviewed 5-identity dedup
migration. It does not alter Vocabulary identity decisions, source mappings,
Learner presentation, Release, Publish, or Anki data.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOCAB_CHECK = ROOT / "tools" / "check_grade5_6_vocabulary_reconciliation_completion.py"
MERGE_CHECK = ROOT / "tools" / "check_klose_grade5_6_current_merge.py"
DECISIONS = ROOT / "anki" / "klose" / "review" / "grade5_6_reconciliation" / "vocabulary_decisions.csv"
STATUS = ROOT / "anki" / "klose" / "review" / "grade5_6_reconciliation" / "vocabulary_status.json"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected one guarded block in {path.relative_to(ROOT)}, got {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def read_decisions() -> list[dict[str, str]]:
    with DECISIONS.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    replace_once(
        VOCAB_CHECK,
        '''Reconciliation truth remains immutable after Stable-ID allocation: decisions keep\nnew:: proposal groups and never embed newly allocated NoteIDs. Post-reconciliation\nallocation is verified separately against the accepted Klose Grade 5-6 learning\nscope. Source provenance is audit metadata and does not gate that learning scope.\n''',
        '''Reconciliation truth remains fingerprint-bound to source evidence. A later reviewed\npre-merge dedup may rebind a proposed new identity to an older Stable NoteID without\nchanging source evidence. Remaining new:: groups stay proposal-only; active Stable\nallocation is verified separately against the accepted Klose Grade 5-6 learning scope.\n''',
    )
    replace_once(
        VOCAB_CHECK,
        '''    expected_counts = {\n        "reuse-existing": 148,\n        "new-stable-identity": 301,\n        "morphology-only": 45,\n        "held": 10,\n    }\n''',
        '''    expected_counts = {\n        "reuse-existing": 153,\n        "new-stable-identity": 296,\n        "morphology-only": 45,\n        "held": 10,\n    }\n''',
    )
    replace_once(
        VOCAB_CHECK,
        '''    if len(new_groups) != 293:\n        fail(f"unexpected proposed new identity groups: {len(new_groups)} != 293")\n''',
        '''    if len(new_groups) != 288:\n        fail(f"unexpected proposed new identity groups after reviewed dedup: {len(new_groups)} != 288")\n''',
    )
    replace_once(
        VOCAB_CHECK,
        '''        if not origin.startswith(G56_ORIGIN_PREFIX):\n            continue\n        group = origin[len(G56_ORIGIN_PREFIX):]\n''',
        '''        if not origin.startswith(G56_ORIGIN_PREFIX):\n            continue\n        if row.get("Status", "").strip() != "active":\n            continue\n        group = origin[len(G56_ORIGIN_PREFIX):]\n''',
    )
    replace_once(
        VOCAB_CHECK,
        '''    if set(allocations) != set(new_groups) or len(set(allocations.values())) != 293:\n        fail("post-reconciliation Stable allocation does not match the 293 reviewed new groups")\n''',
        '''    if set(allocations) != set(new_groups) or len(set(allocations.values())) != len(new_groups):\n        fail("post-reconciliation active Stable allocation does not match reviewed post-dedup new groups")\n''',
    )

    replace_once(
        MERGE_CHECK,
        '''    # Narrow IPA facts added for five reused/current released Notes must be present,\n    # without requiring any identity or learner-content rewrite.\n    reuse_fact_ids = {r.get("NoteID", "").strip() for r in read_csv(REUSE_FACTS)}\n    if reuse_fact_ids != {"KV000158", "KV000195", "KV000303", "KV000327", "KV000483"}:\n        fail(f"unexpected Grade 5-6 reuse fact override set: {sorted(reuse_fact_ids)}")\n''',
        '''    # Narrow IPA facts for reused/current released Notes, including reviewed dedup\n    # survivors, must be present without requiring identity or learner-content rewrite.\n    reuse_fact_ids = {r.get("NoteID", "").strip() for r in read_csv(REUSE_FACTS)}\n    expected_reuse_fact_ids = {\n        "KV000158", "KV000193", "KV000195", "KV000303", "KV000307",\n        "KV000327", "KV000359", "KV000483", "KV000500",\n    }\n    if reuse_fact_ids != expected_reuse_fact_ids:\n        fail(f"unexpected Grade 5-6 reuse fact override set: {sorted(reuse_fact_ids)}")\n''',
    )

    decisions = read_decisions()
    counts = Counter(r.get("Decision", "").strip() for r in decisions)
    bases = Counter(r.get("DecisionBasis", "").strip() for r in decisions)
    groups = {
        r.get("DecisionIdentityGroup", "").strip()
        for r in decisions
        if r.get("Decision", "").strip() == "new-stable-identity"
    }
    expected_counts = Counter({
        "reuse-existing": 153,
        "new-stable-identity": 296,
        "morphology-only": 45,
        "held": 10,
    })
    if counts != expected_counts or len(groups) != 288:
        raise SystemExit(f"Unexpected post-dedup decision closure: counts={counts}, groups={len(groups)}")
    if bases.get("premerge-dedup-reviewed") != 5:
        raise SystemExit(f"Expected five dedup-reviewed decisions, got {bases.get('premerge-dedup-reviewed')}")

    status = json.loads(STATUS.read_text(encoding="utf-8"))
    status["DecisionCounts"] = dict(sorted(counts.items()))
    status["DecisionBasisCounts"] = dict(sorted(bases.items()))
    status["ProposedNewIdentityGroups"] = len(groups)
    status["PendingReview"] = 0
    status["NextBatchCount"] = 0
    status["StaleDecisionRowsIgnored"] = 0
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        "Grade 5-6 dedup gate state patched: "
        f"decisions={len(decisions)}, counts={dict(sorted(counts.items()))}, "
        f"new_groups={len(groups)}, dedup_reviewed={bases['premerge-dedup-reviewed']}"
    )


if __name__ == "__main__":
    main()
