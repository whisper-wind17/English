"""Protect published approval receipts and Expression identities against Git."""
from __future__ import annotations

import csv
import io
import subprocess
from pathlib import Path

from klose_git_history import baseline_commit

ROOT = Path(__file__).resolve().parents[1]


def historical(ref, path):
    result = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True)
    if result.returncode:
        raise SystemExit(f"Missing historical evidence: {ref}:{path}")
    return result.stdout


def main():
    ref = baseline_commit()
    paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", ref], cwd=ROOT, text=True).splitlines()
    receipts = [p for p in paths if ("/review_approvals/" in p or p.startswith("anki/klose/releases/history/")) and p.endswith((".csv", ".json"))]
    for name in receipts:
        path = ROOT / name
        if not path.exists() or path.read_bytes() != historical(ref, name):
            raise SystemExit(f"Immutable historical approval/manifest changed: {name}")
    migration_name = "anki/klose/master/identity_migrations.csv"
    old_migrations = list(csv.DictReader(io.StringIO(historical(ref, migration_name).decode("utf-8-sig"))))
    with (ROOT / migration_name).open(encoding="utf-8-sig", newline="") as handle:
        migration_rows = list(csv.DictReader(handle))
    migration_by = {r["MigrationID"]: r for r in migration_rows}
    if "" in migration_by or len(migration_by) != len(migration_rows):
        raise SystemExit("Invalid/duplicate MigrationID")
    for old in old_migrations:
        now = migration_by.get(old["MigrationID"], {})
        if any(now.get(key) != value for key, value in old.items()):
            raise SystemExit(f"Historical identity migration changed: {old['MigrationID']}")
    name = "anki/klose/expressions/master/expression_registry.csv"
    old = list(csv.DictReader(io.StringIO(historical(ref, name).decode("utf-8-sig"))))
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as handle:
        current_rows = list(csv.DictReader(handle))
    current = {r["ExpressionID"]: r for r in current_rows}
    if len(current) != len(current_rows):
        raise SystemExit("Duplicate current ExpressionID")
    fields = ("CanonicalForm", "FunctionKey", "ExpressionType", "SlotSchema", "Status", "CreatedFromCandidate", "CreatedFromOccurrence")
    for row in old:
        eid = row["ExpressionID"]
        if eid not in current or any(row.get(f, "") != current[eid].get(f, "") for f in fields):
            raise SystemExit(f"Historical Expression identity changed; explicit migration tooling required: {eid}")
    print(f"Approval/history protection OK: receipts={len(receipts)} expressions={len(old)} baseline={ref[:12]}")


if __name__ == "__main__":
    main()
