#!/usr/bin/env python3
"""Independently validate post-allocation third-party learner preparation."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
L = TP / "learner"
M = BASE / "master"
RECEIPT = TP / "allocation" / "execution_receipt.json"
STAGE_B = TP / "reconciliation" / "reconciliation_decisions.csv"
LEARNER_PREVIEW = L / "learner_vocabulary_preview.csv"
BINDINGS = TP / "provenance" / "stable_evidence_bindings.csv"
OCCURRENCES = TP / "staging" / "occurrences.csv"
REGISTRY = M / "note_registry.csv"
REGISTRY_EXT = M / "note_registry_extensions.csv"
CURRENT_LEARNER = BASE / "learner" / "current.csv"
CURRENT_ADMISSION = BASE / "learner" / "learning_admission.csv"
STABLE_SCOPE = L / "stable_learner_scope.csv"
PRESENTATION = L / "stable_presentation_candidates.csv"
ADMISSION_PLAN = L / "stable_learning_admission_plan.csv"
PLAN = L / "stable_learner_plan.json"


def rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def obj(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path.relative_to(ROOT)}")
    return value


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise SystemExit(msg)


def nnum(nid: str) -> int:
    req(bool(re.fullmatch(r"KV\d{6}", nid)), f"Invalid NoteID {nid!r}")
    return int(nid[2:])


def intval(value: str) -> int:
    req(value.isdigit(), f"Expected numeric value, got {value!r}")
    return int(value)


def pick(values: list[str]) -> tuple[str, str]:
    clean = [v.strip() for v in values if v.strip()]
    if not clean:
        return "", "missing"
    c = Counter(clean)
    value = sorted(c, key=lambda x: (-c[x], x.casefold(), x))[0]
    return value, "consistent" if len(c) == 1 else "conflicting-evidence"


def main() -> None:
    receipt = obj(RECEIPT)
    req(receipt.get("Status") == "executed-validated", "Allocation receipt is not executed-validated")
    req(receipt.get("AllocationCommitSHA") == "fe0d1f04c2eae1cf5d492673dd79aef302691d39", "Allocation commit drift")

    active = {
        r["NoteID"].strip(): r
        for path in (REGISTRY, REGISTRY_EXT)
        for r in rows(path)
        if r.get("Status", "").strip() == "active"
    }
    req(len(active) == 3010 and max(active, key=nnum) == "KV003015", "Current Stable truth drift")

    learner_pids = {r["ProvisionalIdentityKey"].strip() for r in rows(LEARNER_PREVIEW)}
    req(len(learner_pids) == 2794 and "" not in learner_pids, "Stage-A learner preview drift")

    decisions = {r["ProvisionalIdentityKey"].strip(): r for r in rows(STAGE_B)}
    req(len(decisions) == 2820 and "" not in decisions, "Stage-B closure drift")
    actions = Counter(r.get("Action", "").strip() for r in decisions.values())
    req(actions == Counter({"reuse-existing": 903, "new-stable-identity": 1821, "held": 96}), f"Stage-B action drift: {actions}")

    allocated = {}
    for nid, r in active.items():
        origin = r.get("PrimaryOriginKey", "").strip()
        if origin.startswith("third-party-vocabulary|candidate:"):
            pid = origin.removeprefix("third-party-vocabulary|")
            req(pid not in allocated, f"Duplicate allocated PID {pid}")
            allocated[pid] = nid
    req(len(allocated) == 1821, "Allocated third-party PID count drift")

    expected_pid_to_nid: dict[str, str] = {}
    held_in_learner = 0
    for pid, d in decisions.items():
        action = d.get("Action", "").strip()
        if action == "held":
            held_in_learner += pid in learner_pids
            continue
        req(pid in learner_pids, f"Resolved PID missing from learner preview: {pid}")
        nid = d.get("ExistingNoteID", "").strip() if action == "reuse-existing" else allocated.get(pid, "")
        req(nid in active, f"Resolved PID maps to non-active Stable Note: {pid}->{nid}")
        expected_pid_to_nid[pid] = nid
    req(len(expected_pid_to_nid) == 2724, "Resolved learner PID count must be 2724")
    req(held_in_learner == 70, "Learner-admitted held PID count must be 70")
    req(len(set(decisions) - learner_pids) == 26, "Learner-excluded PID count must be 26")

    binding_rows = rows(BINDINGS)
    req(len(binding_rows) == 15791, "Evidence binding count drift")
    by_pid: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_nid: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in binding_rows:
        pid, nid = r["ProvisionalIdentityKey"].strip(), r["NoteID"].strip()
        req(expected_pid_to_nid.get(pid) == nid, f"Binding mapping drift: {pid}->{nid}")
        by_pid[pid].append(r); by_nid[nid].append(r)

    occurrence_by_key = {r["SourceOccurrenceKey"].strip(): r for r in rows(OCCURRENCES)}
    req(len(occurrence_by_key) == 18887 and "" not in occurrence_by_key, "Occurrence truth drift")

    pids_by_nid: dict[str, list[str]] = defaultdict(list)
    for pid, nid in expected_pid_to_nid.items():
        pids_by_nid[nid].append(pid)
    expected_nids = set(pids_by_nid)

    scope = rows(STABLE_SCOPE)
    scope_by_nid = {r["NoteID"].strip(): r for r in scope}
    req(len(scope) == len(scope_by_nid) and set(scope_by_nid) == expected_nids, "Stable learner scope NoteID coverage drift")
    for nid, row in scope_by_nid.items():
        pids = sorted(pids_by_nid[nid])
        req(row["ProvisionalIdentityKeys"].split("|") == pids, f"Scope PID list drift: {nid}")
        req(intval(row["ThirdPartyIdentityCount"]) == len(pids), f"Scope PID count drift: {nid}")
        req(intval(row["SourceOccurrenceCount"]) == len(by_nid[nid]), f"Scope occurrence count drift: {nid}")
        req(intval(row["DistinctSourceIDs"]) == len({x["SourceID"] for x in by_nid[nid]}), f"Scope source count drift: {nid}")
        expected_action = "create-content-candidate" if all(decisions[p]["Action"] == "new-stable-identity" for p in pids) else "preserve-existing"
        req(row["PresentationAction"] == expected_action, f"Scope presentation action drift: {nid}")
        reg = active[nid]
        for f in ("CanonicalWord", "MatchKey", "SenseLabel"):
            req(row[f] == reg[f], f"Scope identity field drift {nid}:{f}")

    presentation = rows(PRESENTATION)
    pres_by_nid = {r["NoteID"].strip(): r for r in presentation}
    new_nids = set(allocated.values())
    req(len(presentation) == 1821 and len(pres_by_nid) == 1821 and set(pres_by_nid) == new_nids, "Presentation candidate coverage drift")
    for nid, r in pres_by_nid.items():
        pid = r["ProvisionalIdentityKey"].strip()
        req(allocated.get(pid) == nid, f"Presentation PID/NoteID drift {pid}->{nid}")
        reg = active[nid]
        req(r["CanonicalWord"] == reg["CanonicalWord"] and r["MatchKey"] == reg["MatchKey"] and r["SenseLabel"] == reg["SenseLabel"], f"Presentation identity drift: {nid}")
        req(r["MeaningPrimary"] == reg["SenseLabel"], f"Presentation MeaningPrimary must equal Stable SenseLabel: {nid}")
        occs = [occurrence_by_key[x["SourceOccurrenceKey"]] for x in by_pid[pid]]
        b, bs = pick([x.get("British", "") for x in occs]); a, ass = pick([x.get("American", "") for x in occs])
        req((r["BritishCandidate"], r["BritishEvidenceStatus"]) == (b, bs), f"British evidence drift: {nid}")
        req((r["AmericanCandidate"], r["AmericanEvidenceStatus"]) == (a, ass), f"American evidence drift: {nid}")
        req(r["ExampleSentence"] == "" and r["ExampleTranslation"] == "", f"Unreviewed example leaked into prep: {nid}")
        req(r["PresentationStatus"] == "third-party-content-pending", f"Presentation status drift: {nid}")

    current_learner_rows = rows(CURRENT_LEARNER)
    current_learner = {r["NoteID"].strip(): r for r in current_learner_rows}
    req(len(current_learner) == len(current_learner_rows), "Current learner duplicate")
    for nid, r in scope_by_nid.items():
        if r["PresentationAction"] == "preserve-existing":
            req(nid in current_learner, f"Reuse-existing Stable Note lacks current learner presentation: {nid}")
            req(r["ExistingLearnerPresentation"] == "yes", f"Reuse preservation flag drift: {nid}")
            req(r["ExistingPresentationStatus"] == current_learner[nid].get("PresentationStatus", ""), f"Existing presentation status drift: {nid}")

    current_admission_rows = rows(CURRENT_ADMISSION)
    current_admission = {r["NoteID"].strip(): r for r in current_admission_rows}
    req(len(current_admission) == len(current_admission_rows), "Current admission duplicate")
    allowed = {
        nid: r for nid, r in current_admission.items()
        if r.get("LearnerProfile") == "klose" and r.get("LearnerLevel") == "4" and r.get("Status") == "allowed"
    }
    allowed_orders = {nid: intval(r["LearningOrder"]) for nid, r in allowed.items()}
    req(set(allowed_orders.values()) == set(range(1, max(allowed_orders.values()) + 1)), "Current allowed LearningOrder drift")

    admission = rows(ADMISSION_PLAN)
    adm_by_nid = {r["NoteID"].strip(): r for r in admission}
    req(len(admission) == len(adm_by_nid) and set(adm_by_nid) == expected_nids, "Admission plan coverage drift")
    new_orders = []
    priority_rows = []
    for nid, r in adm_by_nid.items():
        req(r["LearnerProfile"] == "klose" and r["LearnerLevel"] == "4" and r["ProposedStatus"] == "allowed", f"Admission target drift: {nid}")
        req(r["OrderingPolicy"] == "preserve-existing-allowed-then-cross-source-prevalence-v1", f"Ordering policy drift: {nid}")
        if nid in allowed:
            req(r["AdmissionAction"] == "preserve-allowed", f"Existing allowed action drift: {nid}")
            req(intval(r["ProposedLearningOrder"]) == allowed_orders[nid], f"Existing order not preserved: {nid}")
        else:
            new_orders.append(intval(r["ProposedLearningOrder"]))
            priority_rows.append(r)
    start = max(allowed_orders.values()) + 1
    req(sorted(new_orders) == list(range(start, start + len(new_orders))), "Appended proposed LearningOrder is not continuous")
    expected_priority = sorted(priority_rows, key=lambda r: (
        -intval(r["PriorityDistinctSourceIDs"]), -intval(r["PrioritySourceOccurrences"]),
        intval(r["PriorityTokenCount"]), scope_by_nid[r["NoteID"]]["MatchKey"].casefold(), nnum(r["NoteID"]),
    ))
    req([intval(r["ProposedLearningOrder"]) for r in expected_priority] == list(range(start, start + len(expected_priority))), "New LearningOrder does not follow declared learner-evidence ranking")

    plan = obj(PLAN)
    req(plan.get("PlanVersion") == "third-party-stable-learner-prep-v1", "Stable learner plan version drift")
    req(plan.get("Status") == "prepared-pending-content-review-and-materialization", "Stable learner plan status drift")
    pp = plan.get("PresentationPolicy"); ap = plan.get("AdmissionPolicy"); scope_summary = plan.get("Scope")
    req(isinstance(pp, dict) and pp.get("OfficialLearnerCurrentMutated") is False, "Prep must not claim official learner mutation")
    req(isinstance(ap, dict) and ap.get("CanonicalLearningAdmissionMutated") is False and ap.get("SourceGradeUsedForAdmissionOrOrdering") is False, "Admission prep policy drift")
    req(isinstance(scope_summary, dict) and scope_summary.get("ResolvedLearnerProvisionalIdentities") == 2724 and scope_summary.get("NewStablePresentationCandidates") == 1821, "Plan scope summary drift")

    print("Third-party stable learner preparation check = PASS")
    print(f"Stage-A learner candidates = {len(learner_pids)}")
    print(f"resolved learner provisional identities = {len(expected_pid_to_nid)}")
    print(f"learner-admitted Stage-B held = {held_in_learner}")
    print(f"unique Stable learner NoteIDs = {len(expected_nids)}")
    print(f"new presentation candidates = {len(presentation)}")
    print(f"current allowed order preserved = {len(set(expected_nids) & set(allowed))}")
    print(f"new/promoted admission rows planned = {len(set(expected_nids) - set(allowed))}")
    print("Source Grade used for admission/order = no")
    print("official learner/admission/release/publish/Anki mutation = no")


if __name__ == "__main__":
    main()
