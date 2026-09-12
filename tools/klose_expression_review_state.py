"""Expression approval receipts; generators cannot confer review approval."""
from __future__ import annotations

import csv
from pathlib import Path

from klose_expression_review_fingerprint import VERSION, fingerprint

BASE = Path(__file__).resolve().parents[1] / "anki/klose/expressions"
APPROVALS = BASE / "learner/review_approvals"
REVIEW_FIELDS = ["LearnerProfile", "LearnerLevel", "ExpressionID", "FingerprintVersion", "Fingerprint", "ReviewStatus", "ReviewBasis", "ReviewedAt"]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields=None):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]), lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def approval_keys():
    keys = set()
    for path in sorted(APPROVALS.glob("*.csv")):
        local = set()
        for row in read_csv(path):
            key = tuple(row.get(f, "") for f in REVIEW_FIELDS)
            if key in local or row.get("ReviewStatus") not in {"approved", "model-reviewed"}:
                raise SystemExit(f"Invalid/duplicate Expression approval: {path.name}")
            if row.get("ReviewerType") != ("human" if row["ReviewStatus"] == "approved" else "model"):
                raise SystemExit(f"Expression approval reviewer mismatch: {path.name}")
            if not row.get("Evidence", "").strip() or not row.get("ReviewBasis", "").strip() or not row.get("ReviewedAt", "").strip():
                raise SystemExit(f"Expression approval missing evidence: {path.name}")
            local.add(key)
            keys.add(key)
    return keys


def has_approval(row, keys=None):
    return tuple(row.get(f, "") for f in REVIEW_FIELDS) in (approval_keys() if keys is None else keys)


def synchronize():
    current = read_csv(BASE / "learner/current.csv")
    old = read_csv(BASE / "learner/presentation_review_registry.csv")
    by_key = {(r["LearnerProfile"], r["LearnerLevel"], r["ExpressionID"]): r for r in old}
    if len(by_key) != len(old):
        raise SystemExit("Duplicate Expression review key")
    receipts = approval_keys()
    release_path = BASE / "master/release_registry.csv"
    releases = read_csv(release_path)
    release = {r["ExpressionID"]: r for r in releases}
    admission = {r["ExpressionID"]: r for r in read_csv(BASE / "learner/learning_admission.csv")}
    for cur in current:
        key = (cur["LearnerProfile"], cur["LearnerLevel"], cur["ExpressionID"])
        fp = fingerprint(cur)
        row = by_key.get(key, {})
        valid = row.get("Fingerprint") == fp and row.get("FingerprintVersion") == VERSION and has_approval(row, receipts)
        if not valid:
            row = dict(zip(REVIEW_FIELDS, [*key, VERSION, fp, "pending", "content changed or no matching independent approval", ""]))
        by_key[key] = row
        eid = cur["ExpressionID"]
        if eid in release:
            allowed = admission[eid]["Status"] == "allowed"
            release[eid].update(PresentationStatus=row["ReviewStatus"], AdmissionStatus=admission[eid]["Status"], PublishStatus="generated" if valid and allowed else "blocked", ReleaseStatus="ready" if valid and allowed else "blocked")
    rows = [by_key[k] for k in sorted(by_key)]
    write_csv(BASE / "learner/presentation_review_registry.csv", rows, REVIEW_FIELDS)
    write_csv(release_path, releases)
    pending = sum(r["ReviewStatus"] == "pending" for r in rows)
    print(f"Expression review sync: rows={len(rows)} pending={pending}; approval is never inferred from generation")


if __name__ == "__main__":
    synchronize()
