#!/usr/bin/env python3
"""Verify the immutable historical release transaction, not today's admission."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'anki/klose'
MANIFEST = BASE / 'releases/history/2026-09-12-third-party.json'


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def main():
    manifest = json.loads(MANIFEST.read_text())
    historical = {}
    for path, digest in manifest['files'].items():
        result = subprocess.run(['git', 'show', f"{manifest['commit']}:{path}"], cwd=ROOT, capture_output=True)
        if result.returncode or hashlib.sha256(result.stdout).hexdigest() != digest:
            raise SystemExit(f'Historical release evidence unavailable/changed: {path}')
        historical[path] = list(csv.DictReader(io.StringIO(result.stdout.decode('utf-8-sig'))))
    def old(suffix):
        return next(rows for path, rows in historical.items() if path.endswith(suffix))
    plan = old('stable_learning_admission_plan.csv')
    candidates = old('stable_presentation_candidates.csv')
    if len(plan) != manifest['plan_count'] or len(candidates) != manifest['candidate_count']:
        raise SystemExit('Historical transaction manifest count mismatch')
    prior_releases = old('release_registry.csv') + old('release_registry_extensions.csv')
    expected = [r for r in prior_releases if r['ReleaseReason'] == manifest['reason']]
    other = {r['NoteID'] for r in prior_releases if r['ReleaseReason'] != manifest['reason']}
    if len(expected) != manifest['transaction_count'] or {r['NoteID'] for r in expected} != {r['NoteID'] for r in plan} - other:
        raise SystemExit('Historical transaction does not exactly cover its plan')
    current = read_csv(BASE / 'master/release_registry.csv') + read_csv(BASE / 'master/release_registry_extensions.csv')
    actual = [r for r in current if r['ReleaseReason'] == manifest['reason']]
    if actual != expected:
        raise SystemExit('Committed historical release transaction changed')
    ids = {r['NoteID'] for r in current}
    if len(ids) != len(current) or not {r['NoteID'] for r in prior_releases} <= ids:
        raise SystemExit('Historical released identities lost or duplicated')
    print(f'Historical third-party release PASS: transaction={len(expected)} current_release={len(ids)}; live admission/review checked separately')


if __name__ == '__main__':
    main()
