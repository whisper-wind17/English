#!/usr/bin/env python3
"""Apply a transient reviewed Grade 5–6 Vocabulary batch to durable review decisions.

This mutates only reconciliation review truth. It never writes Stable NoteID registries.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
DIR = BASE / "review" / "grade5_6_reconciliation"
CANDIDATES = DIR / "vocabulary_candidates.csv"
BATCH = DIR / "vocabulary_next_batch.csv"
INBOX = DIR / "vocabulary_reviewed_batch.csv"
DECISIONS = DIR / "vocabulary_decisions.csv"
REGISTRIES = [BASE / "master" / "note_registry.csv", BASE / "master" / "note_registry_extensions.csv"]

EVIDENCE_FIELDS = [
    "ProvisionalIdentityKey", "OccurrenceKeys", "OccurrenceCount", "GradeSemesters",
    "Units", "Pages", "Entry", "Meaning", "MatchKey", "SourceMeaningVariants",
    "SourceSurfaceMultiplicity", "CandidateClass", "ExistingNoteCount",
    "ExistingCandidates", "VariantCandidates", "MorphologyLemma", "MorphologyFormType",
]
DECISION_FIELDS = [
    "ProvisionalIdentityKey", "CandidateFingerprint", "Decision", "DecisionNoteID",
    "DecisionIdentityGroup", "DecisionBasis", "Rationale",
]
VALID_MANUAL = {"reuse-existing", "new-stable-identity", "held"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fingerprint(row: dict[str, str]) -> str:
    payload = {k: row.get(k, "") for k in EVIDENCE_FIELDS}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main() -> None:
    if not INBOX.exists():
        print("No reviewed Grade 5–6 Vocabulary batch to apply.")
        return
    candidates = read_csv(CANDIDATES)
    by_key = {r["ProvisionalIdentityKey"].strip(): r for r in candidates}
    current_batch = {r["ProvisionalIdentityKey"].strip() for r in read_csv(BATCH)}
    stable_ids = {
        r["NoteID"].strip()
        for path in REGISTRIES for r in read_csv(path)
        if r.get("Status", "").strip() == "active"
    }
    inbox = read_csv(INBOX)
    if not inbox:
        raise SystemExit("Reviewed batch exists but is empty")
    seen: set[str] = set()
    reviewed: dict[str, dict[str, str]] = {}
    for row in inbox:
        key = row.get("ProvisionalIdentityKey", "").strip()
        if key in seen:
            raise SystemExit(f"Duplicate reviewed key: {key}")
        seen.add(key)
        if key not in by_key:
            raise SystemExit(f"Unknown reviewed key: {key}")
        if key not in current_batch:
            raise SystemExit(f"Reviewed key is not in current selected batch: {key}")
        fp = row.get("CandidateFingerprint", "").strip()
        if fp != fingerprint(by_key[key]):
            raise SystemExit(f"Candidate fingerprint mismatch: {key}")
        decision = row.get("Decision", "").strip()
        note_id = row.get("DecisionNoteID", "").strip()
        group = row.get("DecisionIdentityGroup", "").strip()
        rationale = row.get("Rationale", "").strip()
        if decision not in VALID_MANUAL:
            raise SystemExit(f"Invalid manual decision: {key} -> {decision!r}")
        if not rationale:
            raise SystemExit(f"Reviewed decision lacks rationale: {key}")
        if decision == "reuse-existing":
            if note_id not in stable_ids:
                raise SystemExit(f"reuse-existing references unknown active NoteID: {key} -> {note_id}")
            if group and group != note_id:
                raise SystemExit(f"reuse-existing group must equal NoteID: {key}")
            group = note_id
        elif decision == "new-stable-identity":
            if note_id:
                raise SystemExit(f"new-stable-identity cannot carry NoteID: {key}")
            if not group.startswith("new::"):
                raise SystemExit(f"new-stable-identity requires a shared new:: identity group: {key}")
        else:
            if note_id or group:
                raise SystemExit(f"held cannot carry NoteID/identity group: {key}")
        reviewed[key] = {
            "ProvisionalIdentityKey": key,
            "CandidateFingerprint": fp,
            "Decision": decision,
            "DecisionNoteID": note_id,
            "DecisionIdentityGroup": group,
            "DecisionBasis": "model-reviewed-current-evidence",
            "Rationale": rationale,
        }

    durable = {r.get("ProvisionalIdentityKey", "").strip(): r for r in read_csv(DECISIONS)}
    overlap = sorted(set(reviewed) & set(durable))
    if overlap:
        raise SystemExit(f"Refusing to overwrite existing durable decisions: {overlap[:10]}")
    durable.update(reviewed)
    with DECISIONS.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=DECISION_FIELDS, lineterminator="\n")
        w.writeheader()
        for key in sorted(durable):
            w.writerow({field: durable[key].get(field, "") for field in DECISION_FIELDS})
    INBOX.unlink()
    print(f"Applied reviewed Grade 5–6 Vocabulary batch: {len(reviewed)} decisions")


if __name__ == "__main__":
    main()
