#!/usr/bin/env python3
"""Canonical local/cloud pipeline. No approvals, identity allocation or Anki writes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTECT = ["check_klose_persistent_state.py", "check_klose_release_history.py", "check_klose_approval_history.py"]
VOCABULARY = [
    "check_grade5_6_premerge_dedup.py", "check_klose_actual_grade4_identity.py",
    "audit_klose_actual_grade4_reuse.py", "check_third_party_learner_content.py",
    "build_klose_vocabulary.py", "apply_klose_actual_grade4.py",
    "apply_klose_actual_grade4_reuse_facts.py", "apply_klose_grade5_6_current.py",
    "apply_klose_grade5_6_reuse_facts.py", "apply_klose_grade5_6_new_facts.py",
    "check_grade5_6_new_learner_content.py", "build_klose_learning_admission.py",
    "apply_klose_grade5_6_learner.py", "apply_third_party_stable_learner.py",
    "apply_klose_learner_overrides.py", "apply_klose_actual_grade4_reuse_learner.py",
    "apply_third_party_reviewed_pronunciations.py", "apply_klose_release_extensions.py",
    "apply_klose_current_policy.py", "apply_klose_learner_overrides.py",
    "validate_third_party_pronunciation_materialization.py", "apply_klose_prompt_hints.py",
    "sync_klose_learner_review_registry.py", "check_klose_learner.py",
    "validate_third_party_learner_materialization.py", "check_third_party_release_committed_state.py",
]
EXPRESSIONS = ["klose_expression_review_state.py", "build_klose_expressions.py"]
RELEASE = ["check_klose_release_ready.py", "check_klose_expressions_release_ready.py", "check_klose_feedback.py"]


def run(names):
    for name in names:
        result = subprocess.run([sys.executable, str(ROOT / "tools" / name)], cwd=ROOT, capture_output=True, text=True)
        print(f"{'PASS' if result.returncode == 0 else 'FAIL'} {name}", flush=True)
        if result.returncode:
            print(result.stdout + result.stderr, flush=True)
            raise SystemExit(result.returncode)


def data_snapshot():
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (ROOT / 'anki/klose').rglob('*') if path.is_file()}


def persist():
    """Never rebase a generated result onto unvalidated upstream inputs."""
    subprocess.run(["git", "fetch", "origin", "main"], cwd=ROOT, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    remote = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip()
    if head != remote:
        raise SystemExit("Remote main changed after checkout; rebuild from current main before persisting")
    names = sorted(set(subprocess.check_output(["git", "diff", "HEAD", "--name-only"], cwd=ROOT, text=True).splitlines()) |
                   set(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()))
    fixed = {
        "anki/klose/master/vocabulary_master.csv", "anki/klose/master/source_occurrences.csv", "anki/klose/master/build_stats.csv",
        "anki/klose/learner/current.csv", "anki/klose/learner/learning_admission.csv", "anki/klose/learner/presentation_review_registry.csv",
        "anki/klose/expressions/master/release_registry.csv", "anki/klose/expressions/learner/presentation_review_registry.csv",
        "anki/klose/releases/current.json",
    }
    prefixes = ("anki/klose/publish/", "anki/klose/expressions/publish/", "anki/klose/review/")
    if any(n not in fixed and not n.startswith(prefixes) for n in names):
        raise SystemExit(f"Unexpected generated diff scope: {names}")
    if not names:
        print("No generated changes")
        return
    subprocess.run(["git", "add", "--", *names], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "data: materialize validated Klose release"], cwd=ROOT, check=True)
    # Fast-forward only. A concurrent change causes push rejection, never a stale rebase.
    subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build", "verify", "all"])
    parser.add_argument("--baseline")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args()
    if args.baseline:
        os.environ["KLOSE_BASE_COMMIT"] = args.baseline
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    status = {"build_valid": False if args.command in {"build", "all"} else None, "release_ready": False if args.command in {"verify", "all"} else None}
    try:
        run(PROTECT)
        if args.command in {"build", "all"}:
            status["build_valid"] = False
            run(VOCABULARY + EXPRESSIONS)
            status["build_valid"] = True
        if args.command in {"verify", "all"}:
            status["release_ready"] = False
            run(RELEASE)
            run(["build_klose_release_manifest.py"])
            if args.command == "all":
                before = data_snapshot()
                run(VOCABULARY + EXPRESSIONS + RELEASE + ["build_klose_release_manifest.py"])
                after = data_snapshot()
                changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
                if changed:
                    raise SystemExit(f"Release blocked: repeated build changed data: {changed}")
                print("PASS deterministic rebuild: byte drift=0", flush=True)
            status["release_ready"] = True
        if args.persist:
            if args.command != "all":
                raise SystemExit("Persist requires a full build and release verification")
            persist()
    finally:
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(status, indent=2) + "\n")
        print(json.dumps(status), flush=True)


if __name__ == "__main__":
    main()
