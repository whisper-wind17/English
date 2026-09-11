#!/usr/bin/env python3
"""Build post-allocation third-party learner preparation artifacts.

This is a preparation layer only. It maps the Stage-A learner view and closed
Stage-B decisions onto allocated Stable NoteIDs, prepares learner-presentation
candidates for newly allocated Notes, and proposes explicit long-term learning
admission/order. It never mutates Klose learner/current.csv, canonical admission,
release, publish, or Anki state.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
LEARNER_DIR = TP / "learner"
MASTER = BASE / "master"

RECEIPT = TP / "allocation" / "execution_receipt.json"
STAGE_B = TP / "reconciliation" / "reconciliation_decisions.csv"
LEARNER_PREVIEW = LEARNER_DIR / "learner_vocabulary_preview.csv"
OCCURRENCES = TP / "staging" / "occurrences.csv"
BINDINGS = TP / "provenance" / "stable_evidence_bindings.csv"
REGISTRY = MASTER / "note_registry.csv"
REGISTRY_EXT = MASTER / "note_registry_extensions.csv"
CURRENT_LEARNER = BASE / "learner" / "current.csv"
CURRENT_ADMISSION = BASE / "learner" / "learning_admission.csv"

STABLE_SCOPE = LEARNER_DIR / "stable_learner_scope.csv"
PRESENTATION = LEARNER_DIR / "stable_presentation_candidates.csv"
ADMISSION_PLAN = LEARNER_DIR / "stable_learning_admission_plan.csv"
PLAN = LEARNER_DIR / "stable_learner_plan.json"

SCOPE_FIELDS = [
    "NoteID", "ProvisionalIdentityKeys", "StageBActions", "CanonicalWord", "MatchKey",
    "SenseLabel", "ThirdPartyIdentityCount", "SourceOccurrenceCount", "DistinctSourceIDs",
    "ExistingLearnerPresentation", "ExistingPresentationStatus", "PresentationAction",
]
PRESENTATION_FIELDS = [
    "NoteID", "ProvisionalIdentityKey", "CanonicalWord", "MatchKey", "SenseLabel",
    "MeaningPrimary", "BritishCandidate", "AmericanCandidate", "BritishEvidenceStatus",
    "AmericanEvidenceStatus", "SourceOccurrenceCount", "DistinctSourceIDs",
    "DefinitionEvidence", "ExampleSentence", "ExampleTranslation", "PresentationStatus",
    "PresentationSource",
]
ADMISSION_FIELDS = [
    "LearnerProfile", "LearnerLevel", "NoteID", "CurrentStatus", "CurrentLearningOrder",
    "ProposedStatus", "ProposedLearningTag", "ProposedLearningOrder", "AdmissionAction",
    "PriorityDistinctSourceIDs", "PrioritySourceOccurrences", "PriorityTokenCount",
    "OrderingPolicy", "Reason",
]
NOTE_RE = re.compile(r"^KV\d{6}$")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required input: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: "" if row.get(k) is None else str(row.get(k, "")) for k in fields})


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path.relative_to(ROOT)}")
    return value


def note_num(nid: str) -> int:
    if not NOTE_RE.fullmatch(nid):
        raise SystemExit(f"Invalid NoteID: {nid!r}")
    return int(nid[2:])


def pick_pronunciation(values: list[str]) -> tuple[str, str]:
    clean = [v.strip() for v in values if v.strip()]
    if not clean:
        return "", "missing"
    counts = Counter(clean)
    # Stable choice: highest observed frequency, lexical tie-break.
    candidate = sorted(counts, key=lambda x: (-counts[x], x.casefold(), x))[0]
    return candidate, "consistent" if len(counts) == 1 else "conflicting-evidence"


def order_value(raw: str) -> int:
    raw = raw.strip()
    return int(raw) if raw.isdigit() else 0


def main() -> None:
    receipt = read_json(RECEIPT)
    if receipt.get("Status") != "executed-validated":
        raise SystemExit("Stable allocation is not executed-validated")
    post = receipt.get("PostAllocationTruth")
    if not isinstance(post, dict) or post.get("ActiveStableNoteIDs") != 3010 or post.get("MaxNoteID") != "KV003015":
        raise SystemExit("Unexpected post-allocation Stable truth")

    registry_rows = read_csv(REGISTRY) + read_csv(REGISTRY_EXT)
    active = {r["NoteID"].strip(): r for r in registry_rows if r.get("Status", "").strip() == "active"}
    if len(active) != 3010:
        raise SystemExit(f"Expected 3010 active Stable NoteIDs, got {len(active)}")

    learner_preview = {r["ProvisionalIdentityKey"].strip(): r for r in read_csv(LEARNER_PREVIEW)}
    if len(learner_preview) != 2794 or "" in learner_preview:
        raise SystemExit(f"Expected 2794 unique Stage-A learner candidates, got {len(learner_preview)}")

    decisions = read_csv(STAGE_B)
    decision_by_pid = {r["ProvisionalIdentityKey"].strip(): r for r in decisions}
    if len(decision_by_pid) != 2820 or "" in decision_by_pid:
        raise SystemExit("Stage-B decision closure drift")

    new_origin_to_id: dict[str, str] = {}
    for nid, row in active.items():
        origin = row.get("PrimaryOriginKey", "").strip()
        if origin.startswith("third-party-vocabulary|candidate:"):
            pid = origin.removeprefix("third-party-vocabulary|")
            if pid in new_origin_to_id:
                raise SystemExit(f"Duplicate allocated third-party origin: {pid}")
            new_origin_to_id[pid] = nid
    if len(new_origin_to_id) != 1821:
        raise SystemExit(f"Expected 1821 allocated third-party origins, got {len(new_origin_to_id)}")

    resolved_pid_to_id: dict[str, str] = {}
    action_by_pid: dict[str, str] = {}
    held_learner = 0
    for pid, dec in decision_by_pid.items():
        action = dec.get("Action", "").strip()
        action_by_pid[pid] = action
        admitted = pid in learner_preview
        if action == "held":
            if admitted:
                held_learner += 1
            continue
        if not admitted:
            raise SystemExit(f"Resolved Stage-B identity is unexpectedly absent from learner preview: {pid}")
        if action == "reuse-existing":
            nid = dec.get("ExistingNoteID", "").strip()
        elif action == "new-stable-identity":
            nid = new_origin_to_id.get(pid, "")
        else:
            raise SystemExit(f"Unexpected Stage-B action: {pid}->{action!r}")
        if nid not in active:
            raise SystemExit(f"Resolved learner identity lacks active Stable NoteID: {pid}->{nid}")
        resolved_pid_to_id[pid] = nid

    if len(resolved_pid_to_id) != 2724:
        raise SystemExit(f"Expected 2724 resolved learner identities, got {len(resolved_pid_to_id)}")
    if held_learner != 70:
        raise SystemExit(f"Expected 70 learner-admitted held identities, got {held_learner}")

    bindings = read_csv(BINDINGS)
    bindings_by_pid: dict[str, list[dict[str, str]]] = defaultdict(list)
    bindings_by_nid: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in bindings:
        pid = row.get("ProvisionalIdentityKey", "").strip()
        nid = row.get("NoteID", "").strip()
        if resolved_pid_to_id.get(pid) != nid:
            raise SystemExit(f"Evidence binding is outside resolved learner mapping: {pid}->{nid}")
        bindings_by_pid[pid].append(row)
        bindings_by_nid[nid].append(row)
    if len(bindings) != 15791:
        raise SystemExit(f"Expected 15791 stable evidence bindings, got {len(bindings)}")

    occurrences = {r["SourceOccurrenceKey"].strip(): r for r in read_csv(OCCURRENCES)}
    if len(occurrences) != 18887 or "" in occurrences:
        raise SystemExit("Unified occurrence truth drift")

    current_learner_rows = read_csv(CURRENT_LEARNER)
    current_learner = {r["NoteID"].strip(): r for r in current_learner_rows}
    if len(current_learner) != len(current_learner_rows):
        raise SystemExit("Current learner presentation NoteID duplicate")

    pids_by_nid: dict[str, list[str]] = defaultdict(list)
    for pid, nid in resolved_pid_to_id.items():
        pids_by_nid[nid].append(pid)

    scope_rows: list[dict[str, object]] = []
    for nid in sorted(pids_by_nid, key=note_num):
        pids = sorted(pids_by_nid[nid])
        actions = sorted({action_by_pid[pid] for pid in pids})
        reg = active[nid]
        learner = current_learner.get(nid)
        is_new = all(action_by_pid[pid] == "new-stable-identity" for pid in pids)
        if is_new and len(pids) != 1:
            raise SystemExit(f"Allocated new Stable Note unexpectedly maps multiple provisional identities: {nid}")
        if not is_new and any(action_by_pid[pid] != "reuse-existing" for pid in pids):
            raise SystemExit(f"Stable learner Note mixes new/reuse actions: {nid}")
        scope_rows.append({
            "NoteID": nid,
            "ProvisionalIdentityKeys": "|".join(pids),
            "StageBActions": "|".join(actions),
            "CanonicalWord": reg.get("CanonicalWord", ""),
            "MatchKey": reg.get("MatchKey", ""),
            "SenseLabel": reg.get("SenseLabel", ""),
            "ThirdPartyIdentityCount": len(pids),
            "SourceOccurrenceCount": len(bindings_by_nid[nid]),
            "DistinctSourceIDs": len({r.get("SourceID", "") for r in bindings_by_nid[nid]}),
            "ExistingLearnerPresentation": "yes" if learner is not None else "no",
            "ExistingPresentationStatus": "" if learner is None else learner.get("PresentationStatus", ""),
            "PresentationAction": "create-content-candidate" if is_new else "preserve-existing",
        })

    presentation_rows: list[dict[str, object]] = []
    for pid, nid in sorted(
        ((pid, nid) for pid, nid in resolved_pid_to_id.items() if action_by_pid[pid] == "new-stable-identity"),
        key=lambda x: note_num(x[1]),
    ):
        reg = active[nid]
        evidence = bindings_by_pid[pid]
        occurrence_rows = [occurrences[r["SourceOccurrenceKey"]] for r in evidence]
        british, british_status = pick_pronunciation([r.get("British", "") for r in occurrence_rows])
        american, american_status = pick_pronunciation([r.get("American", "") for r in occurrence_rows])
        definitions = sorted({r.get("Definition", "").strip() for r in occurrence_rows if r.get("Definition", "").strip()})
        presentation_rows.append({
            "NoteID": nid,
            "ProvisionalIdentityKey": pid,
            "CanonicalWord": reg.get("CanonicalWord", ""),
            "MatchKey": reg.get("MatchKey", ""),
            "SenseLabel": reg.get("SenseLabel", ""),
            "MeaningPrimary": reg.get("SenseLabel", ""),
            "BritishCandidate": british,
            "AmericanCandidate": american,
            "BritishEvidenceStatus": british_status,
            "AmericanEvidenceStatus": american_status,
            "SourceOccurrenceCount": len(evidence),
            "DistinctSourceIDs": len({r.get("SourceID", "") for r in evidence}),
            "DefinitionEvidence": " | ".join(definitions),
            "ExampleSentence": "",
            "ExampleTranslation": "",
            "PresentationStatus": "third-party-content-pending",
            "PresentationSource": "third-party-external-evidence-prep-v1",
        })
    if len(presentation_rows) != 1821:
        raise SystemExit(f"Expected 1821 new presentation candidates, got {len(presentation_rows)}")

    current_admission_rows = read_csv(CURRENT_ADMISSION)
    current_admission = {r["NoteID"].strip(): r for r in current_admission_rows}
    if len(current_admission) != len(current_admission_rows):
        raise SystemExit("Current learning admission NoteID duplicate")
    allowed = {
        nid: row for nid, row in current_admission.items()
        if row.get("LearnerProfile", "").strip() == "klose"
        and row.get("LearnerLevel", "").strip() == "4"
        and row.get("Status", "").strip() == "allowed"
    }
    existing_orders = {nid: order_value(row.get("LearningOrder", "")) for nid, row in allowed.items()}
    if not existing_orders or set(existing_orders.values()) != set(range(1, max(existing_orders.values()) + 1)):
        raise SystemExit("Existing allowed LearningOrder is not unique/continuous")
    next_order = max(existing_orders.values()) + 1

    scope_by_nid = {r["NoteID"]: r for r in scope_rows}
    new_to_order = [nid for nid in scope_by_nid if nid not in allowed]
    new_to_order.sort(key=lambda nid: (
        -int(scope_by_nid[nid]["DistinctSourceIDs"]),
        -int(scope_by_nid[nid]["SourceOccurrenceCount"]),
        len(re.findall(r"[A-Za-z0-9]+", str(scope_by_nid[nid]["CanonicalWord"]))),
        str(scope_by_nid[nid]["MatchKey"]).casefold(),
        note_num(nid),
    ))
    proposed_new_orders = {nid: next_order + i for i, nid in enumerate(new_to_order)}

    admission_rows: list[dict[str, object]] = []
    for nid in sorted(scope_by_nid, key=note_num):
        scope = scope_by_nid[nid]
        current = current_admission.get(nid, {})
        current_status = current.get("Status", "").strip()
        current_order = current.get("LearningOrder", "").strip()
        if nid in allowed:
            action = "preserve-allowed"
            proposed_order = existing_orders[nid]
            reason = "already-admitted-current-curriculum"
        else:
            action = "promote-held-to-allowed" if current_status == "held" else "add-allowed"
            proposed_order = proposed_new_orders[nid]
            reason = "resolved-third-party-learner-identity"
        admission_rows.append({
            "LearnerProfile": "klose",
            "LearnerLevel": "4",
            "NoteID": nid,
            "CurrentStatus": current_status,
            "CurrentLearningOrder": current_order,
            "ProposedStatus": "allowed",
            "ProposedLearningTag": "learning::klose::third-party-primary",
            "ProposedLearningOrder": f"{proposed_order:06d}",
            "AdmissionAction": action,
            "PriorityDistinctSourceIDs": scope["DistinctSourceIDs"],
            "PrioritySourceOccurrences": scope["SourceOccurrenceCount"],
            "PriorityTokenCount": len(re.findall(r"[A-Za-z0-9]+", str(scope["CanonicalWord"]))),
            "OrderingPolicy": "preserve-existing-allowed-then-cross-source-prevalence-v1",
            "Reason": reason,
        })

    write_csv(STABLE_SCOPE, SCOPE_FIELDS, scope_rows)
    write_csv(PRESENTATION, PRESENTATION_FIELDS, presentation_rows)
    write_csv(ADMISSION_PLAN, ADMISSION_FIELDS, admission_rows)

    duplicate_reuse = sum(max(0, len(pids) - 1) for nid, pids in pids_by_nid.items() if nid not in new_origin_to_id.values())
    plan = {
        "PlanVersion": "third-party-stable-learner-prep-v1",
        "Status": "prepared-pending-content-review-and-materialization",
        "LearnerProfile": "klose",
        "LearnerLevel": 4,
        "InputTruth": {
            "AllocationCommitSHA": receipt.get("AllocationCommitSHA"),
            "ActiveStableNoteIDs": len(active),
            "StageAIdentityCandidates": len(decision_by_pid),
            "StageALearnerCandidates": len(learner_preview),
            "StableEvidenceBindings": len(bindings),
        },
        "Scope": {
            "ResolvedLearnerProvisionalIdentities": len(resolved_pid_to_id),
            "LearnerAdmittedButStageBHeld": held_learner,
            "UniqueStableLearnerNotes": len(scope_rows),
            "NewStablePresentationCandidates": len(presentation_rows),
            "ReuseActions": sum(action_by_pid[pid] == "reuse-existing" for pid in resolved_pid_to_id),
            "DuplicateReuseContributions": duplicate_reuse,
        },
        "PresentationPolicy": {
            "ReuseExisting": "preserve-existing-learner-presentation",
            "NewStable": "prepare-content-candidate-only; examples remain pending",
            "MeaningPrimary": "Stable SenseLabel",
            "Pronunciation": "most-frequent external evidence candidate; conflicts explicitly flagged",
            "OfficialLearnerCurrentMutated": False,
        },
        "AdmissionPolicy": {
            "ProposedStatusForResolvedLearnerScope": "allowed",
            "ExistingAllowedOrder": "preserve-exactly",
            "NewOrder": "append after current allowed order; distinct-source count desc, occurrence count desc, token count asc, MatchKey lexical, NoteID",
            "SourceGradeUsedForAdmissionOrOrdering": False,
            "ImmediateAnkiSchedulingImplied": False,
            "CanonicalLearningAdmissionMutated": False,
        },
        "NextRequiredStep": "generate-and-review-learnerlevel4-content-then-materialize-presentation-and-admission",
    }
    PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"third-party stable learner provisional identities = {len(resolved_pid_to_id)}")
    print(f"third-party stable learner unique NoteIDs = {len(scope_rows)}")
    print(f"new presentation candidates = {len(presentation_rows)}")
    print(f"learner-admitted Stage-B held = {held_learner}")
    print(f"admission rows planned = {len(admission_rows)}")
    print(f"existing allowed preserved = {sum(r['AdmissionAction'] == 'preserve-allowed' for r in admission_rows)}")
    print(f"new/promoted allowed planned = {sum(r['AdmissionAction'] != 'preserve-allowed' for r in admission_rows)}")
    print("official learner/admission/release/publish/Anki mutation = no")


if __name__ == "__main__":
    main()
