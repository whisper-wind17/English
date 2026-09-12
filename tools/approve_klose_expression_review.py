"""Record explicit per-expression review decisions after independent review."""
from __future__ import annotations

import argparse
import re

from klose_expression_review_fingerprint import VERSION, fingerprint
from klose_expression_review_state import BASE, APPROVALS, REVIEW_FIELDS, read_csv, write_csv, synchronize


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-file", required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--confirm-reviewed", action="store_true")
    args = parser.parse_args()
    if not args.confirm_reviewed or not re.fullmatch(r"[A-Za-z0-9_-]+", args.batch_id):
        raise SystemExit("Explicit reviewed confirmation and a safe batch-id are required")
    from pathlib import Path
    decisions = read_csv(Path(args.review_file))
    current = {r["ExpressionID"]: r for r in read_csv(BASE / "learner/current.csv")}
    reviews = read_csv(BASE / "learner/presentation_review_registry.csv")
    review_by = {(r["LearnerProfile"], r["LearnerLevel"], r["ExpressionID"]): r for r in reviews}
    seen, receipts = set(), []
    for row in decisions:
        eid = row.get("ExpressionID")
        if eid in seen or eid not in current:
            raise SystemExit(f"Duplicate/unknown reviewed Expression: {eid}")
        seen.add(eid)
        cur = current[eid]
        if row.get("Fingerprint") != fingerprint(cur) or row.get("FingerprintVersion") != VERSION:
            raise SystemExit(f"Stale explicit Expression review: {eid}")
        if row.get("LearnerProfile") != cur["LearnerProfile"] or row.get("LearnerLevel") != cur["LearnerLevel"]:
            raise SystemExit(f"Review profile/level mismatch: {eid}")
        if row.get("ReviewStatus") not in {"approved", "model-reviewed"} or row.get("ReviewerType") != ("human" if row["ReviewStatus"] == "approved" else "model"):
            raise SystemExit(f"Invalid reviewer/status: {eid}")
        if any(not row.get(f, "").strip() for f in ("ReviewBasis", "ReviewedAt", "Evidence")):
            raise SystemExit(f"Missing explicit review evidence: {eid}")
        key = (cur["LearnerProfile"], cur["LearnerLevel"], eid)
        if key not in review_by:
            raise SystemExit(f"Run review sync before approval: {eid}")
        review_by[key].update({f: row[f] for f in REVIEW_FIELDS})
        receipts.append(row)
    path = APPROVALS / f"{args.batch_id}.csv"
    if not receipts or path.exists():
        raise SystemExit("Empty or existing immutable approval batch")
    APPROVALS.mkdir(parents=True, exist_ok=True)
    write_csv(path, receipts, REVIEW_FIELDS + ["ReviewerType", "Evidence"])
    write_csv(BASE / "learner/presentation_review_registry.csv", reviews, REVIEW_FIELDS)
    synchronize()
    print(f"Approved {len(receipts)} independently reviewed Expressions: {path.name}")


if __name__ == "__main__":
    main()
