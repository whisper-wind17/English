#!/usr/bin/env python3
"""Independent completion recheck for Grade 5–6 Vocabulary reconciliation.

This is read-only. It derives closure from candidates + durable decisions + current
Stable registries, cross-checks the generated status snapshot, and independently
binds that semantic closure to the current Source provenance fingerprint. It does not
allocate NoteIDs or mutate learner/release/publish/Anki state.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from grade5_6_source_state import source_provenance_state

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
DIR = BASE / "review" / "grade5_6_reconciliation"
CANDIDATES = DIR / "vocabulary_candidates.csv"
DECISIONS = DIR / "vocabulary_decisions.csv"
NEXT_BATCH = DIR / "vocabulary_next_batch.csv"
INBOX = DIR / "vocabulary_reviewed_batch.csv"
STATUS = DIR / "vocabulary_status.json"
REGISTRIES = [BASE / "master" / "note_registry.csv", BASE / "master" / "note_registry_extensions.csv"]

EVIDENCE_FIELDS = [
    "ProvisionalIdentityKey", "OccurrenceKeys", "OccurrenceCount", "GradeSemesters",
    "Units", "Pages", "Entry", "Meaning", "MatchKey", "SourceMeaningVariants",
    "SourceSurfaceMultiplicity", "CandidateClass", "ExistingNoteCount",
    "ExistingCandidates", "VariantCandidates", "MorphologyLemma", "MorphologyFormType",
]
VALID_DECISIONS = {"reuse-existing", "new-stable-identity", "morphology-only", "held"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing completion input: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fingerprint(row: dict[str, str]) -> str:
    payload = {k: row.get(k, "") for k in EVIDENCE_FIELDS}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"Grade 5–6 Vocabulary completion FAIL: {message}")


def main() -> None:
    candidates = read_csv(CANDIDATES)
    decisions = read_csv(DECISIONS)
    if INBOX.exists():
        fail("transient vocabulary_reviewed_batch.csv still exists")
    if read_csv(NEXT_BATCH):
        fail("vocabulary_next_batch.csv is not empty")

    by_key = {r.get("ProvisionalIdentityKey", "").strip(): r for r in candidates}
    if "" in by_key or len(by_key) != len(candidates):
        fail("candidate keys are blank or duplicated")
    decision_by_key = {r.get("ProvisionalIdentityKey", "").strip(): r for r in decisions}
    if "" in decision_by_key or len(decision_by_key) != len(decisions):
        fail("decision keys are blank or duplicated")
    if set(by_key) != set(decision_by_key):
        missing = sorted(set(by_key) - set(decision_by_key))
        extra = sorted(set(decision_by_key) - set(by_key))
        fail(f"candidate/decision coverage mismatch missing={missing[:10]} extra={extra[:10]}")

    stable_ids = {
        r.get("NoteID", "").strip()
        for path in REGISTRIES for r in read_csv(path)
        if r.get("Status", "").strip() == "active"
    }
    if len(stable_ids) != 901:
        fail(f"unexpected Stable Vocabulary registry size: {len(stable_ids)} != 901")

    counts: Counter[str] = Counter()
    new_groups: defaultdict[str, list[str]] = defaultdict(list)
    for key, cand in by_key.items():
        row = decision_by_key[key]
        if row.get("CandidateFingerprint", "").strip() != fingerprint(cand):
            fail(f"stale decision fingerprint: {key}")
        decision = row.get("Decision", "").strip()
        note_id = row.get("DecisionNoteID", "").strip()
        group = row.get("DecisionIdentityGroup", "").strip()
        if decision not in VALID_DECISIONS:
            fail(f"invalid decision: {key} -> {decision!r}")
        counts[decision] += 1

        if decision == "reuse-existing":
            if note_id not in stable_ids or group != note_id:
                fail(f"invalid reuse-existing contract: {key} -> note={note_id!r} group={group!r}")
        elif decision == "new-stable-identity":
            if note_id or not group.startswith("new::"):
                fail(f"invalid new-stable-identity contract: {key}")
            new_groups[group].append(key)
        elif decision == "morphology-only":
            if note_id or group or cand.get("CandidateClass", "").strip() != "morphology-only":
                fail(f"invalid morphology-only contract: {key}")
        elif decision == "held":
            if note_id or group:
                fail(f"held decision carries identity state: {key}")

    if len(candidates) != 504:
        fail(f"unexpected provisional learning units: {len(candidates)} != 504")
    expected_counts = {
        "reuse-existing": 148,
        "new-stable-identity": 301,
        "morphology-only": 45,
        "held": 10,
    }
    if dict(counts) != expected_counts:
        fail(f"decision counts changed: {dict(counts)} != {expected_counts}")
    if len(new_groups) != 293:
        fail(f"unexpected proposed new identity groups: {len(new_groups)} != 293")

    def find(entry: str, meaning: str) -> dict[str, str]:
        matches = [r for r in candidates if r.get("Entry") == entry and r.get("Meaning") == meaning]
        if len(matches) != 1:
            fail(f"representative candidate lookup not unique: {entry!r} / {meaning!r}")
        return decision_by_key[matches[0]["ProvisionalIdentityKey"]]

    expected_examples = [
        ("may", "也许；可能", "new-stable-identity", "", "new::may::possibility-modal"),
        ("run", "（使）运转", "new-stable-identity", "", "new::run::operate"),
        ("star", "歌唱（或表演）明星", "new-stable-identity", "", "new::star::performer-celebrity"),
        ("first (1st)", "第一（的）", "reuse-existing", "KV000279", "KV000279"),
        ("fifth (5th)", "第五（的）", "reuse-existing", "KV000602", "KV000602"),
        ("second (2nd)", "第二（的）", "reuse-existing", "KV000296", "KV000296"),
        ("third (3rd)", "第三（的）", "reuse-existing", "KV000297", "KV000297"),
        ("twelfth (12th)", "第十二（的）", "reuse-existing", "KV000606", "KV000606"),
        ("glass", "一杯（的量）；玻璃", "held", "", ""),
        ("heat", "加热；（使）变暖；热量", "held", "", ""),
        ("good job", "做得好", "held", "", ""),
        ("for example", "例如", "held", "", ""),
        ("have ... class", "上……课", "held", "", ""),
    ]
    for entry, meaning, decision, note_id, group in expected_examples:
        row = find(entry, meaning)
        got = (
            row.get("Decision", "").strip(),
            row.get("DecisionNoteID", "").strip(),
            row.get("DecisionIdentityGroup", "").strip(),
        )
        want = (decision, note_id, group)
        if got != want:
            fail(f"representative decision drift: {entry!r} got={got} want={want}")

    shared_expectations = [
        ("bamboo", "new::bamboo::plant"),
        ("do morning exercises", "new::do morning exercises::routine"),
    ]
    for entry, group in shared_expectations:
        matching_keys = [r["ProvisionalIdentityKey"] for r in candidates if r.get("Entry") == entry]
        if entry == "do morning exercises":
            matching_keys += [r["ProvisionalIdentityKey"] for r in candidates if r.get("Entry") == "doing morning exercises"]
        if not matching_keys or any(decision_by_key[k].get("DecisionIdentityGroup", "").strip() != group for k in matching_keys):
            fail(f"shared identity group drift: {entry!r} -> {group!r}")

    status = json.loads(STATUS.read_text(encoding="utf-8"))
    status_checks = {
        "ProvisionalLearningUnits": len(candidates),
        "ValidDecisionCount": len(decisions),
        "PendingReview": 0,
        "NextBatchCount": 0,
        "ProposedNewIdentityGroups": len(new_groups),
        "StableNoteIDAllocated": False,
        "MasterLearnerReleasePublishMutationAuthorized": False,
    }
    for field, expected in status_checks.items():
        if status.get(field) != expected:
            fail(f"status mismatch {field}: {status.get(field)!r} != {expected!r}")
    if status.get("DecisionCounts") != dict(sorted(counts.items())):
        fail("status DecisionCounts does not match independently derived counts")
    if status.get("StaleDecisionRowsIgnored") != 0:
        fail("status reports stale decision rows")

    provenance = source_provenance_state()
    if provenance["ResolutionState"] != "applied" or provenance["SourceIdentityPending"]:
        fail(f"Source provenance is not fully resolved: {provenance}")
    if not provenance["SourceProvenanceBlockers"]:
        fail("expected lower-volume provenance blockers are missing")
    if provenance["StableIDAllocationAllowed"]:
        fail("provenance unexpectedly authorizes Stable ID allocation")
    provenance_checks = {
        "SourceIdentityPending": False,
        "SourceProvenanceFingerprint": provenance["SourceProvenanceFingerprint"],
        "SourceProvenanceRows": provenance["SourceProvenanceRows"],
        "SourceProvenanceBlockers": provenance["SourceProvenanceBlockers"],
        "SourceProvenanceResolutionState": "applied",
        "CanonicalSourceID": "renjiao_start3",
        "StableIDAllocationAllowed": False,
    }
    for field, expected in provenance_checks.items():
        if status.get(field) != expected:
            fail(f"provenance status mismatch {field}: {status.get(field)!r} != {expected!r}")

    print(
        "Grade 5–6 Vocabulary reconciliation completion OK: "
        f"candidates={len(candidates)}, decisions={len(decisions)}, "
        f"counts={dict(sorted(counts.items()))}, new_groups={len(new_groups)}, "
        f"stable_registry={len(stable_ids)}, pending=0, stale=0, "
        f"provenance={provenance['SourceProvenanceFingerprint'][:12]}, allocation=blocked"
    )


if __name__ == "__main__":
    main()
