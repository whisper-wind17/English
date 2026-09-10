#!/usr/bin/env python3
"""Temporary branch-only helper for the 2026-09-10 Vocabulary release transition."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

# This helper exists only to materialize the guarded transition and is deleted before PR.
ROOT = Path(__file__).resolve().parents[1]
RELEASE_EXT = Path("anki/klose/master/release_registry_extensions.csv")


def baseline_bytes(path: str) -> bytes:
    proc = subprocess.run(
        ["git", "show", f"origin/main:{path}"], cwd=ROOT,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"Cannot read origin/main baseline for {path}")
    return proc.stdout


def patch_from_baseline(path: str, replacements: list[tuple[str, str, str]]) -> None:
    data = baseline_bytes(path)
    newline = "\r\n" if b"\r\n" in data else "\n"
    for old, new, label in replacements:
        old_b = old.replace("\n", newline).encode("utf-8")
        new_b = new.replace("\n", newline).encode("utf-8")
        count = data.count(old_b)
        if count != 1:
            raise SystemExit(f"{label} patch anchor drifted: count={count}")
        data = data.replace(old_b, new_b)
    (ROOT / path).write_bytes(data)


def main() -> None:
    # Restore exact historical bytes before applying the durable release transition.
    (ROOT / RELEASE_EXT).write_bytes(baseline_bytes(RELEASE_EXT.as_posix()))

    patch_from_baseline(
        "tools/apply_klose_actual_grade4.py",
        [(
            '    release_ext_rows = read_csv(RELEASE_EXTENSIONS)\n',
            '    release_ext_rows = [\n'
            '        r for r in read_csv(RELEASE_EXTENSIONS)\n'
            '        if r.get("ReleaseReason", "").strip() == "actual-grade4-klose-current"\n'
            '    ]\n',
            "Grade4 release-extension scope",
        )],
    )
    patch_from_baseline(
        "tools/check_klose_grade5_6_current_merge.py",
        [
            (
                '''    new_ids = set(allocations.values())
    for nid in new_ids:
        if master_by_id[nid].get("Released", "").strip() != "no":
            fail(f"new Grade 5-6 Note was prematurely released: {nid}")
        learner = learner_by_id[nid]
''',
                '''    new_ids = set(allocations.values())
    for nid in new_ids:
        learner = learner_by_id[nid]
''',
                "current-merge new-note release state",
            ),
            (
                '''    if len(release_ids) != 638:
        fail(f"unexpected existing released set: {len(release_ids)}")
    if new_ids & release_ids:
        fail("new Grade 5-6 Notes leaked into Release registry")
''',
                '''    if not release_ids <= registry_ids:
        fail("Release registry references Notes outside the active Stable registry")
''',
                "current-merge fixed release count",
            ),
            (
                '        f"learner_review_queue={len(review_ids)}, released_unchanged=638, publish_not_authorized"\n',
                '        f"learner_review_queue={len(review_ids)}, released={len(release_ids)}, release_state_separate"\n',
                "current-merge status output",
            ),
        ],
    )

    subprocess.run(
        [
            "python", "tools/release_klose_allowed_vocabulary.py",
            "--expected-count", "334",
            "--released-at", "2026-09-10",
            "--reason", "grade5-6-current-reviewed-v1",
            "--apply",
        ],
        cwd=ROOT,
        check=True,
        env=os.environ.copy(),
    )


if __name__ == "__main__":
    main()
