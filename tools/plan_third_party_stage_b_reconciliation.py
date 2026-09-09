#!/usr/bin/env python3
"""Build a deterministic read-only Stage-B reconciliation review queue and next batch.

V2 separates safe executable proposals from semantic/manual review:
- learner-excluded -> explicit held (no allocation needed under current learner policy)
- exact/variant multiple -> manual high-risk review
- orthographic/spelling single -> manual equivalence review
- exact-single + exact learner-sense equality -> safe reuse proposal
- no-existing-match after exact/orthographic/spelling discovery -> safe new-identity proposal
- other exact-single -> semantic review

All actions remain reconciliation decisions only; MutationAuthorized is always no.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
PREMERGE = TP / "premerge"
CANDIDATES = PREMERGE / "identity_candidates.csv"
READINESS = PREMERGE / "readiness.json"
DECISIONS = TP / "reconciliation" / "reconciliation_decisions.csv"
QUEUE = PREMERGE / "reconciliation_review_queue.csv"
SELECTED = PREMERGE / "reconciliation_selected_view.csv"
NEXT = PREMERGE / "reconciliation_next_batch.json"

PLAN_VERSION = "stage-b-reconciliation-v2"
CANDIDATE_FP_FIELDS = [
    "ProvisionalIdentityKey", "CanonicalMatchKey", "LookupMatchKey", "DisplayWord",
    "ThirdPartyTargetSense", "SourceMatchKeys", "SourceOccurrenceCount",
    "LearnerAdmitted", "KloseCandidateClass", "KloseCandidateCount",
    "KloseCandidateNoteIDs", "KloseCandidateSenses",
]
QUEUE_FIELDS = [
    "ProvisionalIdentityKey", "CanonicalMatchKey", "LookupMatchKey", "DisplayWord",
    "ThirdPartyTargetSense", "LearnerAdmitted", "KloseCandidateClass",
    "KloseCandidateNoteIDs", "KloseCandidateSenses", "CandidateFingerprint",
    "ReviewLane", "ProposalAction", "ProposalExistingNoteID", "ProposalReason",
    "MutationAuthorized",
]
LANE_PRIORITY = {
    "learner-excluded": 0,
    "exact-multiple": 1,
    "variant-multiple": 2,
    "variant-single": 3,
    "exact-single-exact-sense": 4,
    "no-existing-match": 5,
    "exact-single-semantic-review": 6,
}
BATCH_CAPS = {
    "learner-excluded": 300,
    "exact-multiple": 20,
    "variant-multiple": 20,
    "variant-single": 40,
    "exact-single-exact-sense": 200,
    "no-existing-match": 300,
    "exact-single-semantic-review": 50,
}
SAFE_EXECUTABLE_LANES = {
    "learner-excluded",
    "exact-single-exact-sense",
    "no-existing-match",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return value


def candidate_fingerprint(row: dict[str, str]) -> str:
    payload = {field: row.get(field, "") for field in CANDIDATE_FP_FIELDS}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_decision_ids(
    candidates: dict[str, dict[str, str]], checkpoint: str
) -> set[str]:
    if not DECISIONS.exists():
        return set()
    valid: set[str] = set()
    for row in read_csv(DECISIONS):
        pid = row.get("ProvisionalIdentityKey", "")
        candidate = candidates.get(pid)
        if not candidate:
            continue
        if row.get("StageACheckpointFingerprint") != checkpoint:
            continue
        if row.get("CandidateFingerprint") != candidate_fingerprint(candidate):
            continue
        if row.get("Status") not in {"reviewed", "held"}:
            continue
        valid.add(pid)
    return valid


def classify(row: dict[str, str]) -> tuple[str, str, str, str]:
    if row.get("LearnerAdmitted", "").casefold() != "yes":
        return (
            "learner-excluded", "held", "",
            "identity is outside the current learner-admission policy; close as held without allocation",
        )

    cls = row.get("KloseCandidateClass", "")
    if cls == "exact-multiple":
        return "exact-multiple", "", "", "multiple current exact Klose candidates require explicit review"
    if cls in {"orthographic-multiple", "spelling-multiple"}:
        return "variant-multiple", "", "", "multiple orthographic/spelling-equivalent Klose candidates require review"
    if cls in {"orthographic-single", "spelling-single"}:
        return "variant-single", "", "", "single orthographic/spelling candidate requires sense-equivalence review"
    if cls == "exact-single":
        ids = [x for x in row.get("KloseCandidateNoteIDs", "").split("|") if x]
        if len(ids) != 1:
            raise SystemExit(f"exact-single candidate cardinality drift: {row.get('ProvisionalIdentityKey')}")
        third = row.get("ThirdPartyTargetSense", "").strip()
        klose = row.get("KloseCandidateSenses", "").strip()
        if third and third == klose:
            return (
                "exact-single-exact-sense", "reuse-existing", ids[0],
                "one exact MatchKey candidate plus byte-for-byte learner-sense equality",
            )
        return (
            "exact-single-semantic-review", "", "",
            "single exact MatchKey candidate but learner senses are not exactly equal",
        )
    if cls == "no-existing-match":
        return (
            "no-existing-match", "new-stable-identity", "",
            "validated premerge found no exact, space/hyphen-equivalent, or configured spelling-equivalent Klose identity",
        )
    raise SystemExit(f"Unknown KloseCandidateClass: {cls}: {row.get('ProvisionalIdentityKey')}")


def main() -> None:
    readiness = read_json(READINESS)
    if readiness.get("ReadyForPremergeReview") is not True:
        raise SystemExit("Stage-B reconciliation planning requires ReadyForPremergeReview=true")
    checkpoint = str(readiness.get("StageACheckpointFingerprint", "")).strip()
    if not checkpoint:
        raise SystemExit("Stage-B readiness lacks StageACheckpointFingerprint")

    candidate_rows = read_csv(CANDIDATES)
    by_id = {row.get("ProvisionalIdentityKey", ""): row for row in candidate_rows}
    if "" in by_id or len(by_id) != len(candidate_rows):
        raise SystemExit("Premerge candidate ProvisionalIdentityKey is empty/duplicate")
    decided = valid_decision_ids(by_id, checkpoint)

    queue_rows: list[dict[str, str]] = []
    lane_counts: Counter[str] = Counter()
    for pid, row in by_id.items():
        if pid in decided:
            continue
        lane, action, existing, reason = classify(row)
        lane_counts[lane] += 1
        queue_rows.append({
            "ProvisionalIdentityKey": pid,
            "CanonicalMatchKey": row.get("CanonicalMatchKey", ""),
            "LookupMatchKey": row.get("LookupMatchKey", ""),
            "DisplayWord": row.get("DisplayWord", ""),
            "ThirdPartyTargetSense": row.get("ThirdPartyTargetSense", ""),
            "LearnerAdmitted": row.get("LearnerAdmitted", ""),
            "KloseCandidateClass": row.get("KloseCandidateClass", ""),
            "KloseCandidateNoteIDs": row.get("KloseCandidateNoteIDs", ""),
            "KloseCandidateSenses": row.get("KloseCandidateSenses", ""),
            "CandidateFingerprint": candidate_fingerprint(row),
            "ReviewLane": lane,
            "ProposalAction": action,
            "ProposalExistingNoteID": existing,
            "ProposalReason": reason,
            "MutationAuthorized": "no",
        })

    queue_rows.sort(key=lambda r: (LANE_PRIORITY[r["ReviewLane"]], r["ProvisionalIdentityKey"]))
    write_csv(QUEUE, QUEUE_FIELDS, queue_rows)

    active_lane = ""
    for lane in sorted(LANE_PRIORITY, key=LANE_PRIORITY.get):
        if lane_counts[lane]:
            active_lane = lane
            break
    cap = BATCH_CAPS.get(active_lane, 0)
    selected_rows = [r for r in queue_rows if r["ReviewLane"] == active_lane][:cap]
    write_csv(SELECTED, QUEUE_FIELDS, selected_rows)

    next_state = {
        "PlanVersion": PLAN_VERSION,
        "StageACheckpointFingerprint": checkpoint,
        "CandidateCount": len(candidate_rows),
        "ValidDurableDecisionCount": len(decided),
        "ReviewQueueCount": len(queue_rows),
        "LaneCounts": dict(sorted(lane_counts.items())),
        "ReviewLane": active_lane,
        "BatchCap": cap,
        "SelectedCount": len(selected_rows),
        "SelectedProvisionalIdentityKeys": [r["ProvisionalIdentityKey"] for r in selected_rows],
        "ExecutionReady": bool(selected_rows),
        "AutoExecutable": active_lane in SAFE_EXECUTABLE_LANES and bool(selected_rows),
        "MutationAuthorized": False,
        "ReviewQueueFingerprint": sha256(QUEUE),
        "SelectedViewFingerprint": sha256(SELECTED),
    }
    NEXT.write_text(json.dumps(next_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Stage-B reconciliation plan = {PLAN_VERSION}")
    print(f"current candidates = {len(candidate_rows)}")
    print(f"valid durable decisions = {len(decided)}")
    print(f"review queue = {len(queue_rows)}")
    for lane in sorted(lane_counts, key=lambda x: LANE_PRIORITY[x]):
        print(f"review lane {lane} = {lane_counts[lane]}")
    print(f"next lane = {active_lane or 'none'}")
    print(f"selected = {len(selected_rows)}")
    print(f"auto executable = {'yes' if next_state['AutoExecutable'] else 'no'}")
    print("Stage-B mutation authorized = no")


if __name__ == "__main__":
    main()
