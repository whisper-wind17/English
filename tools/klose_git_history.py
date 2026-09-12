"""Fail-closed Git baselines and narrowly scoped identity migrations."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def baseline_commit() -> str:
    ref = os.environ.get("KLOSE_BASE_COMMIT", "").strip() or "HEAD^"
    result = subprocess.run(["git", "rev-parse", "--verify", f"{ref}^{{commit}}"], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(f"Historical validation blocked: Git baseline unavailable: {ref!r}")
    return result.stdout.strip()


def identity_fingerprint(row: dict[str, str], fields: tuple[str, ...]) -> str:
    payload = {field: row.get(field, "").strip() for field in fields}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def permits_identity_change(note_id, old, current, fields, migrations, baseline, historical_migrations):
    """A historical approval is evidence of its own transaction, never a waiver."""
    old_ids = {row.get("MigrationID") for row in historical_migrations}
    return any(
        row.get("MigrationID") and row.get("MigrationID") not in old_ids
        and row.get("NoteID") == note_id
        and row.get("Status") == "approved"
        and row.get("BaselineCommit") == baseline
        and row.get("BeforeFingerprint") == identity_fingerprint(old, fields)
        and row.get("AfterFingerprint") == identity_fingerprint(current, fields)
        and row.get("Reason", "").strip()
        for row in migrations
    )
