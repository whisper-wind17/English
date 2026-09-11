#!/usr/bin/env python3
"""Validate the durable committed state after third-party Stable allocation.

This checker is for the post-execution lifecycle. It validates the recorded allocation
commit, exact two-path scope, append-only Stable identity result, evidence bindings,
and the Stage-B action closure that authorized that allocation. Later lifecycle
metadata refreshes may rewrite the current reconciliation artifact, so allocation
correspondence is bound to the decision snapshot at the allocation commit rather
than requiring that historical decision file to remain byte-identical forever.
"""
from __future__ import annotations

import csv
import io
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
RECEIPT = TP / "allocation" / "execution_receipt.json"
DECISIONS = TP / "reconciliation" / "reconciliation_decisions.csv"
REGISTRY = BASE / "master" / "note_registry.csv"
REGISTRY_EXT = BASE / "master" / "note_registry_extensions.csv"
EVIDENCE = TP / "provenance" / "stable_evidence_bindings.csv"
NOTE_RE = re.compile(r"^KV(\d{6})$")

REGISTRY_FIELDS = [
    "NoteID", "CanonicalWord", "MatchKey", "SenseLabel", "PrimaryOriginKey",
    "CreatedSource", "CreatedSourceBook", "Status",
]
BINDING_FIELDS = [
    "NoteID", "ProvisionalIdentityKey", "SourceOccurrenceKey", "SourceID",
    "SourceBook", "Grade", "Semester", "SourceRow", "SourceSnapshotFingerprint",
    "EvidenceStatus",
]
ALLOWED_PATHS = {
    "anki/klose/master/note_registry_extensions.csv",
    "anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def obj(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), f"Expected JSON object: {path.relative_to(ROOT)}")
    return value


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def read_csv_text(text: str) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    return list(reader.fieldnames or []), list(reader)


def git(*args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, encoding="utf-8")
    require(proc.returncode == 0, f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def git_show(ref: str, rel: str) -> str:
    proc = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=ROOT, text=True, capture_output=True, encoding="utf-8")
    require(proc.returncode == 0, f"Cannot read {ref}:{rel}: {proc.stderr.strip()}")
    return proc.stdout


def note_num(note_id: str) -> int:
    match = NOTE_RE.fullmatch(note_id)
    require(match is not None, f"Invalid NoteID: {note_id!r}")
    return int(match.group(1))


def main() -> None:
    receipt = obj(RECEIPT)
    require(receipt.get("ReceiptVersion") == "third-party-allocation-execution-receipt-v1", "Receipt version drift")
    require(receipt.get("Status") == "executed-validated", "Allocation receipt is not executed-validated")

    allocation_commit = str(receipt.get("AllocationCommitSHA", "")).strip()
    base_commit = str(receipt.get("AllocationBaseCommitSHA", "")).strip()
    require(allocation_commit and base_commit, "Allocation receipt commit boundary missing")
    require(git("rev-parse", f"{allocation_commit}^") == base_commit, "Allocation commit parent != recorded base")

    changed = {line for line in git("diff-tree", "--no-commit-id", "--name-only", "-r", allocation_commit).splitlines() if line}
    require(changed == ALLOWED_PATHS, f"Allocation commit path scope drift: {sorted(changed)}")
    require(set(receipt.get("AllowedAllocationCommitPaths", [])) == ALLOWED_PATHS, "Receipt allowed paths drift")

    ext_rel = REGISTRY_EXT.relative_to(ROOT).as_posix()
    legacy_rel = REGISTRY.relative_to(ROOT).as_posix()
    evidence_rel = EVIDENCE.relative_to(ROOT).as_posix()
    decisions_rel = DECISIONS.relative_to(ROOT).as_posix()

    base_ext_fields, base_ext = read_csv_text(git_show(base_commit, ext_rel))
    post_ext_fields, post_ext = read_csv_text(git_show(allocation_commit, ext_rel))
    require(base_ext_fields == REGISTRY_FIELDS and post_ext_fields == REGISTRY_FIELDS, "Registry extension schema drift")
    require(len(base_ext) == 392, f"Pre-allocation extension row count drift: {len(base_ext)}")
    require(len(post_ext) == 2213, f"Post-allocation extension row count drift: {len(post_ext)}")
    require(post_ext[:len(base_ext)] == base_ext, "Historical registry extension rows changed")
    appended = post_ext[len(base_ext):]
    require(len(appended) == 1821, "Allocated Stable row count drift")

    expected_ids = [f"KV{i:06d}" for i in range(1195, 3016)]
    require([r.get("NoteID", "") for r in appended] == expected_ids, "Allocated NoteID range is not exact/contiguous")
    require(all(r.get("Status") == "active" for r in appended), "Allocated Stable row is not active")
    require(all(r.get("CreatedSource") == "third-party-vocabulary" for r in appended), "Allocated CreatedSource drift")
    require(all(r.get("CreatedSourceBook") == "external-evidence-corpus" for r in appended), "Allocated CreatedSourceBook drift")
    origins = [r.get("PrimaryOriginKey", "") for r in appended]
    require(all(x.startswith("third-party-vocabulary|candidate:") for x in origins), "Allocated origin prefix drift")
    require(len(origins) == len(set(origins)), "Allocated origin duplicate")

    current_fields, current_ext = read_csv(REGISTRY_EXT)
    require(current_fields == REGISTRY_FIELDS, "Current registry extension schema drift")
    require(current_ext == post_ext, "Current registry extension no longer equals validated allocation state")

    legacy_fields, legacy = read_csv(REGISTRY)
    require(legacy_fields == REGISTRY_FIELDS, "Legacy registry schema drift")
    require(git("rev-parse", f"{base_commit}:{legacy_rel}") == git("rev-parse", f"{allocation_commit}:{legacy_rel}"), "Legacy registry changed in allocation commit")
    full = legacy + current_ext
    ids = [r.get("NoteID", "") for r in full]
    require(len(full) == 3015 and len(ids) == len(set(ids)), "Post-allocation persistent registry count/uniqueness drift")
    active = {r["NoteID"] for r in full if r.get("Status") == "active"}
    require(len(active) == 3010, f"Post-allocation active Stable count drift: {len(active)}")
    require(max(ids, key=note_num) == "KV003015", "Post-allocation max NoteID drift")

    evidence_fields, evidence = read_csv(EVIDENCE)
    require(evidence_fields == BINDING_FIELDS, "Evidence binding schema drift")
    commit_evidence_fields, commit_evidence = read_csv_text(git_show(allocation_commit, evidence_rel))
    require(commit_evidence_fields == BINDING_FIELDS, "Committed evidence schema drift")
    require(evidence == commit_evidence, "Current evidence bindings no longer equal allocation commit")
    require(len(evidence) == 15791, f"Evidence binding count drift: {len(evidence)}")
    binding_keys = [(r.get("ProvisionalIdentityKey", ""), r.get("SourceOccurrenceKey", "")) for r in evidence]
    require(len(binding_keys) == len(set(binding_keys)), "Evidence binding key duplicate")
    require(all(r.get("NoteID") in active for r in evidence), "Evidence binding references non-active/unknown NoteID")
    require(all(r.get("EvidenceStatus") == "external-unverified-edition" for r in evidence), "EvidenceStatus drift")

    # Allocation is bound to the Stage-B closure that existed when allocation was
    # committed. Current reconciliation metadata is validated by the Stage-B
    # lifecycle checker and may legitimately be resealed later without changing
    # the historical authorization basis.
    _, decisions = read_csv_text(git_show(allocation_commit, decisions_rel))
    by_pid = {r.get("ProvisionalIdentityKey", ""): r for r in decisions}
    require(len(by_pid) == 2820 and all(by_pid), "Historical Stage-B decision closure drift")
    reuse = {pid for pid, r in by_pid.items() if r.get("Action") == "reuse-existing"}
    new = {pid for pid, r in by_pid.items() if r.get("Action") == "new-stable-identity"}
    held = {pid for pid, r in by_pid.items() if r.get("Action") == "held"}
    require((len(reuse), len(new), len(held)) == (903, 1821, 96), "Historical Stage-B action distribution drift")

    appended_pids = {r["PrimaryOriginKey"].split("third-party-vocabulary|", 1)[1] for r in appended}
    require(appended_pids == new, "Allocated Stable origins do not exactly match historical Stage-B new identities")
    bound_pids = {r.get("ProvisionalIdentityKey", "") for r in evidence}
    require(held.isdisjoint(bound_pids), "Held historical Stage-B identity has evidence binding")
    require(bound_pids == reuse | new, "Evidence binding identity coverage drift")

    post_truth = receipt.get("PostAllocationTruth")
    require(isinstance(post_truth, dict), "Receipt post-allocation truth missing")
    require(post_truth.get("PersistentRegistryRows") == 3015, "Receipt persistent count drift")
    require(post_truth.get("ActiveStableNoteIDs") == 3010, "Receipt active count drift")
    require(post_truth.get("MaxNoteID") == "KV003015", "Receipt max NoteID drift")
    require(post_truth.get("StableEvidenceBindings") == 15791, "Receipt binding count drift")
    require(git("rev-parse", f"{allocation_commit}:{ext_rel}") == post_truth.get("NoteRegistryExtensionsBlobSHA"), "Receipt post registry blob drift")
    require(git("rev-parse", f"{allocation_commit}:{evidence_rel}") == post_truth.get("StableEvidenceBindingsBlobSHA"), "Receipt evidence blob drift")

    validation = receipt.get("Validation")
    require(isinstance(validation, dict), "Receipt validation block missing")
    for key in (
        "ClosedPreflight", "AuthorizedControlPlaneRecheck", "PersistentStatePreCommit",
        "PostMutationCompletionRecheck", "PersistentStatePostCommit",
        "PostCommitCompletionRecheck", "CompareAndSwapPush",
    ):
        require(validation.get(key) == "PASS", f"Receipt validation not PASS: {key}")
    require(validation.get("CommitPathScopeExact") is True, "Receipt path-scope validation missing")
    require(validation.get("HeldIdentitiesAllocated") is False, "Receipt held-allocation flag invalid")
    require(validation.get("MasterLearnerReleasePublishAnkiMutation") is False, "Receipt isolation flag invalid")

    print("Third-party committed allocation state = PASS")
    print(f"allocation commit = {allocation_commit}")
    print("allocation commit paths = exactly 2")
    print("historical Stage-B closure = reuse 903 / new 1821 / held 96")
    print("historical extension rows unchanged = 392")
    print("new Stable rows = 1821 / KV001195..KV003015")
    print("persistent Stable rows = 3015")
    print("active Stable NoteIDs = 3010")
    print("external evidence bindings = 15791")
    print("held identities allocated/bound = no")
    print("Master/Learner/Release/Publish/Anki allocation-commit mutation = no")


if __name__ == "__main__":
    main()
