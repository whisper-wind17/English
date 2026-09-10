#!/usr/bin/env python3
"""Seed deterministic Grade 5–6 Vocabulary decisions and build the next review batch."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "anki" / "klose" / "review" / "grade5_6_reconciliation"
CANDIDATES = DIR / "vocabulary_candidates.csv"
DECISIONS = DIR / "vocabulary_decisions.csv"
BATCH = DIR / "vocabulary_next_batch.csv"
STATUS = DIR / "vocabulary_status.json"

DECISION_FIELDS = [
    "ProvisionalIdentityKey", "CandidateFingerprint", "Decision", "DecisionNoteID",
    "DecisionIdentityGroup", "DecisionBasis", "Rationale",
]
BATCH_FIELDS = [
    "ProvisionalIdentityKey", "CandidateFingerprint", "Entry", "Meaning", "MatchKey",
    "OccurrenceCount", "GradeSemesters", "Units", "Pages", "SourceMeaningVariants",
    "SourceSurfaceMultiplicity", "CandidateClass", "ExistingNoteCount",
    "ExistingCandidates", "VariantCandidates", "MorphologyLemma", "MorphologyFormType",
]
EVIDENCE_FIELDS = [
    "ProvisionalIdentityKey", "OccurrenceKeys", "OccurrenceCount", "GradeSemesters",
    "Units", "Pages", "Entry", "Meaning", "MatchKey", "SourceMeaningVariants",
    "SourceSurfaceMultiplicity", "CandidateClass", "ExistingNoteCount",
    "ExistingCandidates", "VariantCandidates", "MorphologyLemma", "MorphologyFormType",
]
VALID_DECISIONS = {"reuse-existing", "new-stable-identity", "morphology-only", "held"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'")
    value = value.replace("；", ";").replace("，", ",")
    value = re.sub(r"\s+", "", value.strip()).casefold()
    return value


def fingerprint(row: dict[str, str]) -> str:
    payload = {k: row.get(k, "") for k in EVIDENCE_FIELDS}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_single_existing(text: str) -> tuple[str, str] | None:
    if " || " in text or not text.strip():
        return None
    parts = text.split("::", 2)
    if len(parts) != 3:
        return None
    return parts[0].strip(), parts[2].strip()


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def validate_decision(row: dict[str, str], key: str) -> dict[str, str]:
    decision = row.get("Decision", "").strip()
    note_id = row.get("DecisionNoteID", "").strip()
    group = row.get("DecisionIdentityGroup", "").strip()
    if decision not in VALID_DECISIONS:
        raise SystemExit(f"Invalid decision for {key}")
    if decision == "reuse-existing":
        if not note_id:
            raise SystemExit(f"reuse-existing lacks NoteID: {key}")
        if group and group != note_id:
            raise SystemExit(f"reuse-existing identity group must equal NoteID: {key}")
        group = note_id
    elif decision == "new-stable-identity":
        if note_id:
            raise SystemExit(f"new-stable-identity cannot carry NoteID: {key}")
        if not group.startswith("new::"):
            raise SystemExit(f"new-stable-identity requires new:: identity group: {key}")
    else:
        if note_id or group:
            raise SystemExit(f"{decision} cannot carry NoteID/identity group: {key}")
    return {
        "ProvisionalIdentityKey": key,
        "CandidateFingerprint": row.get("CandidateFingerprint", "").strip(),
        "Decision": decision,
        "DecisionNoteID": note_id,
        "DecisionIdentityGroup": group,
        "DecisionBasis": row.get("DecisionBasis", "").strip(),
        "Rationale": row.get("Rationale", "").strip(),
    }


def main() -> None:
    candidates = read_csv(CANDIDATES)
    if not candidates:
        raise SystemExit("Missing vocabulary candidates")
    by_key = {r["ProvisionalIdentityKey"].strip(): r for r in candidates}
    if len(by_key) != len(candidates):
        raise SystemExit("Duplicate candidate key")

    existing: dict[str, dict[str, str]] = {}
    stale: list[str] = []
    for raw in read_csv(DECISIONS):
        key = raw.get("ProvisionalIdentityKey", "").strip()
        if key not in by_key:
            stale.append(key or "<blank>")
            continue
        if raw.get("CandidateFingerprint", "").strip() != fingerprint(by_key[key]):
            stale.append(key)
            continue
        if key in existing:
            raise SystemExit(f"Duplicate decision key: {key}")
        existing[key] = validate_decision(raw, key)

    seeded = Counter()
    for key, cand in by_key.items():
        if key in existing:
            continue
        fp = fingerprint(cand)
        if cand["CandidateClass"] == "morphology-only":
            existing[key] = {
                "ProvisionalIdentityKey": key,
                "CandidateFingerprint": fp,
                "Decision": "morphology-only",
                "DecisionNoteID": "",
                "DecisionIdentityGroup": "",
                "DecisionBasis": "policy-deterministic",
                "Rationale": "Textbook explicitly marks this source entry as an inflected form; keep the learning relation in Morphology Registry and do not mint a Vocabulary identity for the inflection alone.",
            }
            seeded["morphology-only"] += 1
            continue
        if cand["CandidateClass"] == "exact-single":
            parsed = parse_single_existing(cand.get("ExistingCandidates", ""))
            if parsed is not None:
                note_id, sense = parsed
                if norm(cand["Meaning"]) == norm(sense):
                    existing[key] = {
                        "ProvisionalIdentityKey": key,
                        "CandidateFingerprint": fp,
                        "Decision": "reuse-existing",
                        "DecisionNoteID": note_id,
                        "DecisionIdentityGroup": note_id,
                        "DecisionBasis": "policy-deterministic-exact-sense",
                        "Rationale": "Same MatchKey and normalized textbook target sense exactly equals the single current Stable Note sense.",
                    }
                    seeded["exact-sense-reuse"] += 1

    decision_rows = [existing[k] for k in sorted(existing)]
    write_csv(DECISIONS, DECISION_FIELDS, decision_rows)

    pending = [r for r in candidates if r["ProvisionalIdentityKey"].strip() not in existing]
    priority = {
        "exact-multiple": 0,
        "orthographic-variant": 1,
        "exact-single": 2,
        "no-exact-match": 3,
        "morphology-only": 4,
    }
    pending.sort(key=lambda r: (
        0 if r.get("SourceSurfaceMultiplicity") == "yes" else 1,
        priority.get(r["CandidateClass"], 9),
        r["MatchKey"], r["Meaning"],
    ))
    selected = pending[:50]
    batch_rows = []
    for r in selected:
        row = {f: r.get(f, "") for f in BATCH_FIELDS}
        row["CandidateFingerprint"] = fingerprint(r)
        batch_rows.append(row)
    write_csv(BATCH, BATCH_FIELDS, batch_rows)

    class_counts = Counter(r["CandidateClass"] for r in candidates)
    decision_counts = Counter(r["Decision"] for r in decision_rows)
    basis_counts = Counter(r["DecisionBasis"] for r in decision_rows)
    new_groups = {r["DecisionIdentityGroup"] for r in decision_rows if r["Decision"] == "new-stable-identity"}
    status = {
        "SourceOccurrences": 509,
        "ProvisionalLearningUnits": len(candidates),
        "CandidateClasses": dict(sorted(class_counts.items())),
        "ValidDecisionCount": len(decision_rows),
        "DecisionCounts": dict(sorted(decision_counts.items())),
        "DecisionBasisCounts": dict(sorted(basis_counts.items())),
        "ProposedNewIdentityGroups": len(new_groups),
        "PendingReview": len(pending),
        "NextBatchCount": len(selected),
        "NextBatchClasses": dict(sorted(Counter(r["CandidateClass"] for r in selected).items())),
        "StaleDecisionRowsIgnored": len(stale),
        "SeededThisRun": dict(sorted(seeded.items())),
        "StableNoteIDAllocated": False,
        "MasterLearnerReleasePublishMutationAuthorized": False,
        "SourceIdentityPending": True,
    }
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Grade 5–6 Vocabulary review status:", json.dumps(status, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
