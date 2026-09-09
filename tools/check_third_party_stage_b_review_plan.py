#!/usr/bin/env python3
"""Validate the derived Stage-B reconciliation review queue and deterministic batch."""
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
QUEUE = PREMERGE / "reconciliation_review_queue.csv"
SELECTED = PREMERGE / "reconciliation_selected_view.csv"
NEXT = PREMERGE / "reconciliation_next_batch.json"
DECISIONS = TP / "reconciliation" / "reconciliation_decisions.csv"

PLAN_VERSION = "stage-b-reconciliation-v2"
CANDIDATE_FP_FIELDS = [
    "ProvisionalIdentityKey", "CanonicalMatchKey", "LookupMatchKey", "DisplayWord",
    "ThirdPartyTargetSense", "SourceMatchKeys", "SourceOccurrenceCount",
    "LearnerAdmitted", "KloseCandidateClass", "KloseCandidateCount",
    "KloseCandidateNoteIDs", "KloseCandidateSenses",
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
SAFE_EXECUTABLE_LANES = {"learner-excluded", "exact-single-exact-sense", "no-existing-match"}


def rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def obj(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return value


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def fp(row: dict[str, str]) -> str:
    payload = {field: row.get(field, "") for field in CANDIDATE_FP_FIELDS}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_decisions(candidate_by_id: dict[str, dict[str, str]], checkpoint: str) -> set[str]:
    if not DECISIONS.exists():
        return set()
    out: set[str] = set()
    for d in rows(DECISIONS):
        pid = d.get("ProvisionalIdentityKey", "")
        c = candidate_by_id.get(pid)
        if not c:
            continue
        if d.get("StageACheckpointFingerprint") != checkpoint:
            continue
        if d.get("CandidateFingerprint") != fp(c):
            continue
        if d.get("Status") not in {"reviewed", "held"}:
            continue
        out.add(pid)
    return out


def expected(row: dict[str, str]) -> tuple[str, str, str]:
    if row.get("LearnerAdmitted", "").casefold() != "yes":
        return "learner-excluded", "held", ""
    cls = row.get("KloseCandidateClass", "")
    if cls == "exact-multiple":
        return "exact-multiple", "", ""
    if cls in {"orthographic-multiple", "spelling-multiple"}:
        return "variant-multiple", "", ""
    if cls in {"orthographic-single", "spelling-single"}:
        return "variant-single", "", ""
    if cls == "exact-single":
        ids = [x for x in row.get("KloseCandidateNoteIDs", "").split("|") if x]
        require(len(ids) == 1, f"Exact-single cardinality drift: {row.get('ProvisionalIdentityKey')}")
        third = row.get("ThirdPartyTargetSense", "").strip()
        klose = row.get("KloseCandidateSenses", "").strip()
        if third and third == klose:
            return "exact-single-exact-sense", "reuse-existing", ids[0]
        return "exact-single-semantic-review", "", ""
    if cls == "no-existing-match":
        return "no-existing-match", "new-stable-identity", ""
    raise SystemExit(f"Unknown candidate class: {row.get('ProvisionalIdentityKey')}: {cls}")


def main() -> None:
    readiness = obj(READINESS)
    require(readiness.get("ReadyForPremergeReview") is True,
            "Stage-B review plan requires ReadyForPremergeReview=true")
    checkpoint = str(readiness.get("StageACheckpointFingerprint", "")).strip()
    require(bool(checkpoint), "Missing Stage-A checkpoint in readiness")

    candidates = rows(CANDIDATES)
    candidate_by_id = {r.get("ProvisionalIdentityKey", ""): r for r in candidates}
    require("" not in candidate_by_id and len(candidate_by_id) == len(candidates),
            "Candidate ProvisionalIdentityKey empty/duplicate")
    decided = valid_decisions(candidate_by_id, checkpoint)

    queue = rows(QUEUE)
    qids = [r.get("ProvisionalIdentityKey", "") for r in queue]
    require(all(qids) and len(qids) == len(set(qids)), "Review queue identity key empty/duplicate")
    require(set(qids) == set(candidate_by_id) - decided,
            "Review queue does not exactly equal current candidates minus valid durable decisions")

    counts: Counter[str] = Counter()
    for row in queue:
        pid = row["ProvisionalIdentityKey"]
        candidate = candidate_by_id[pid]
        require(row.get("CandidateFingerprint") == fp(candidate), f"Candidate fingerprint drift: {pid}")
        lane, action, existing = expected(candidate)
        require(row.get("ReviewLane") == lane,
                f"Review lane drift: {pid}: {row.get('ReviewLane')} != {lane}")
        require(row.get("MutationAuthorized") == "no", f"Review proposal authorizes mutation: {pid}")
        require(row.get("ProposalAction", "") == action,
                f"ProposalAction drift: {pid}: {row.get('ProposalAction')} != {action}")
        require(row.get("ProposalExistingNoteID", "") == existing,
                f"ProposalExistingNoteID drift: {pid}")
        if action == "reuse-existing":
            require(existing in candidate.get("KloseCandidateNoteIDs", "").split("|"),
                    f"Reuse proposal is outside candidate context: {pid}")
        if action == "new-stable-identity":
            require(candidate.get("KloseCandidateClass") == "no-existing-match",
                    f"New-identity proposal bypasses existing candidate: {pid}")
        if action == "held":
            require(candidate.get("LearnerAdmitted", "").casefold() != "yes",
                    f"Auto-held proposal is not learner-excluded: {pid}")
        counts[lane] += 1

    expected_order = sorted(queue, key=lambda r: (LANE_PRIORITY[r["ReviewLane"]], r["ProvisionalIdentityKey"]))
    require(qids == [r["ProvisionalIdentityKey"] for r in expected_order],
            "Review queue ordering is not deterministic")

    state = obj(NEXT)
    require(state.get("PlanVersion") == PLAN_VERSION, "Review plan version drift")
    require(state.get("StageACheckpointFingerprint") == checkpoint, "Review plan checkpoint drift")
    require(int(state.get("CandidateCount", -1)) == len(candidates), "Review plan candidate count drift")
    require(int(state.get("ValidDurableDecisionCount", -1)) == len(decided), "Valid decision count drift")
    require(int(state.get("ReviewQueueCount", -1)) == len(queue), "Review queue count drift")
    require(state.get("LaneCounts") == dict(sorted(counts.items())), "Review lane counts drift")
    require(state.get("ReviewQueueFingerprint") == file_sha(QUEUE), "Review queue fingerprint drift")
    require(state.get("SelectedViewFingerprint") == file_sha(SELECTED), "Selected view fingerprint drift")
    require(state.get("MutationAuthorized") is False, "Review plan authorizes mutation")

    active_lane = ""
    for lane in sorted(LANE_PRIORITY, key=LANE_PRIORITY.get):
        if counts[lane]:
            active_lane = lane
            break
    require(state.get("ReviewLane") == active_lane, "Next review lane drift")
    cap = BATCH_CAPS.get(active_lane, 0)
    require(int(state.get("BatchCap", -1)) == cap, "Next batch cap drift")
    expected_selected = [r for r in queue if r["ReviewLane"] == active_lane][:cap]
    selected = rows(SELECTED)
    require([r["ProvisionalIdentityKey"] for r in selected] ==
            [r["ProvisionalIdentityKey"] for r in expected_selected],
            "Selected reconciliation batch is not deterministic")
    require(state.get("SelectedProvisionalIdentityKeys") ==
            [r["ProvisionalIdentityKey"] for r in expected_selected],
            "Selected identity list drift")
    require(int(state.get("SelectedCount", -1)) == len(expected_selected), "Selected count drift")
    require(state.get("ExecutionReady") is bool(expected_selected), "ExecutionReady drift")
    expected_auto = active_lane in SAFE_EXECUTABLE_LANES and bool(expected_selected)
    require(state.get("AutoExecutable") is expected_auto, "AutoExecutable drift")

    print("Third-party Stage-B reconciliation review plan = pass")
    print(f"Stage-A checkpoint = {checkpoint}")
    print(f"candidates = {len(candidates)}")
    print(f"valid durable decisions = {len(decided)}")
    print(f"review queue = {len(queue)}")
    for lane in sorted(counts, key=lambda x: LANE_PRIORITY[x]):
        print(f"review lane {lane} = {counts[lane]}")
    print(f"selected lane = {active_lane or 'none'}")
    print(f"selected count = {len(expected_selected)}")
    print(f"auto executable = {'yes' if expected_auto else 'no'}")
    print("Exact MatchKey alone auto-authorizes reuse = no")
    print("No candidate match auto-authorizes Klose mutation = no")
    print("Stage-B mutation authorized = no")


if __name__ == "__main__":
    main()
