#!/usr/bin/env python3
"""Validate third-party external-evidence provenance without mutating Klose truth.

Third-party adapters are external evidence. They do not become verified textbook
Source Facts merely because an identity is later allocated. Promotion to the Klose
Master Source Identity Map requires independently verified SourceEdition/Revision.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
CONTRACT = TP / "provenance" / "contract.json"
FREEZE = TP / "config" / "source_freeze.json"
ADAPTERS = TP / "config" / "source_adapters.csv"
UNIFIED = TP / "staging" / "occurrences.csv"
MASTER_MAP = BASE / "master" / "source_identity_extensions.csv"

REQUIRED_OCC_FIELDS = [
    "SourceOccurrenceKey", "SourceID", "SourceBook", "Grade", "Semester",
    "SourceRow", "Word", "MatchKey", "British", "American", "Definition", "SourceFile",
]
FUTURE_BINDING_FIELDS = [
    "NoteID", "ProvisionalIdentityKey", "SourceOccurrenceKey", "SourceID",
    "SourceBook", "Grade", "Semester", "SourceRow", "SourceSnapshotFingerprint",
    "EvidenceStatus",
]


def obj(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object: {path.relative_to(ROOT)}")
    return value


def rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def main() -> None:
    contract = obj(CONTRACT)
    freeze = obj(FREEZE)
    require(contract.get("ContractVersion") == "third-party-source-provenance-v1", "Unexpected provenance contract version")
    require(contract.get("ContractStatus") in {"checkpoint-candidate", "validated-checkpointed"}, "Unexpected provenance contract status")

    classification = contract.get("SourceClassification")
    require(isinstance(classification, dict), "SourceClassification missing")
    require(classification.get("ThirdPartyAdapters") == "external-evidence-provenance", "Third-party adapters must remain external evidence")
    require(classification.get("MasterSourceIdentityMap") == "verified-textbook-source-fact-only", "Master Source Identity Map boundary drift")

    contract_freeze = contract.get("SourceFreeze")
    require(isinstance(contract_freeze, dict), "SourceFreeze contract missing")
    for key in ("FreezeVersion", "SourceAdaptersFingerprint", "UnifiedOccurrencesFingerprint"):
        require(contract_freeze.get(key) == freeze.get(key), f"Source freeze contract drift: {key}")
    require(contract_freeze.get("EnabledAdapters") == len(freeze.get("ExpectedEnabledAdapters", [])), "Enabled adapter freeze count drift")
    require(contract_freeze.get("SourceOccurrences") == freeze.get("ExpectedSourceOccurrences"), "Source occurrence freeze count drift")
    require(sha256(ADAPTERS) == freeze.get("SourceAdaptersFingerprint"), "source_adapters.csv raw fingerprint drift")
    require(sha256(UNIFIED) == freeze.get("UnifiedOccurrencesFingerprint"), "Unified occurrence raw fingerprint drift")

    adapter_fields, adapter_rows = rows(ADAPTERS)
    require(adapter_fields == ["SourceID", "OccurrencesPath", "Enabled"], "Adapter config schema drift")
    enabled = [r for r in adapter_rows if r.get("Enabled", "").strip().casefold() == "yes"]
    require(len(enabled) == contract_freeze.get("EnabledAdapters"), "Enabled adapter count drift")
    require({r["SourceID"] for r in enabled} == set(freeze.get("ExpectedEnabledAdapters", [])), "Enabled adapter identity set drift")

    occurrence_keys: set[str] = set()
    occurrence_total = 0
    for adapter in enabled:
        path = ROOT / adapter["OccurrencesPath"]
        fields, source_rows = rows(path)
        require(fields == REQUIRED_OCC_FIELDS, f"Occurrence schema drift: {path.relative_to(ROOT)}")
        require("SourceEdition" not in fields, f"Unexpected SourceEdition in current adapter schema: {path.relative_to(ROOT)}")
        for row in source_rows:
            require(row.get("SourceID") == adapter["SourceID"], f"SourceID mismatch in {path.relative_to(ROOT)}")
            key = row.get("SourceOccurrenceKey", "")
            require(bool(key) and key not in occurrence_keys, f"Empty/duplicate third-party SourceOccurrenceKey: {key!r}")
            occurrence_keys.add(key)
        occurrence_total += len(source_rows)
    require(occurrence_total == contract_freeze.get("SourceOccurrences"), "Adapter occurrence closure drift")

    evidence = contract.get("EvidenceIdentity")
    require(isinstance(evidence, dict), "EvidenceIdentity missing")
    require(evidence.get("OccurrencePrimaryKey") == "SourceOccurrenceKey", "Evidence occurrence key drift")
    require(evidence.get("SnapshotBinding") == "UnifiedOccurrencesFingerprint", "Evidence snapshot binding drift")
    require(evidence.get("EditionStatus") == "unverified" and evidence.get("EditionFactPresent") is False, "Current edition epistemic status drift")

    edition = contract.get("EditionPolicy")
    require(isinstance(edition, dict), "EditionPolicy missing")
    for key in (
        "SyntheticSourceEditionAllowed", "UnknownEditionSentinelAllowedInMaster",
        "InferEditionFromFilename", "InferEditionFromGrade", "InferEditionFromThirdPartyLabel",
    ):
        require(edition.get(key) is False, f"Unsafe edition inference enabled: {key}")
    require(edition.get("MasterPromotionRequiresVerifiedEditionEvidence") is True, "Master promotion must require verified edition evidence")

    identity = contract.get("StableIdentityPolicy")
    require(isinstance(identity, dict), "StableIdentityPolicy missing")
    require(identity.get("ExternalEvidenceMaySupportStableIdentityAllocation") is True, "External evidence allocation support contract drift")
    require(identity.get("StableIdentityAllocationImpliesTextbookProvenance") is False, "Stable allocation must not imply textbook provenance")
    require(identity.get("PlannedPrimaryOriginKey") == "third-party-vocabulary|<ProvisionalIdentityKey>", "Stable origin key contract drift")
    require(identity.get("PlannedCreatedSource") == "third-party-vocabulary", "CreatedSource contract drift")
    require(identity.get("PlannedCreatedSourceBook") == "external-evidence-corpus", "CreatedSourceBook must not pretend to be a textbook edition")

    binding = contract.get("FutureEvidenceBinding")
    require(isinstance(binding, dict), "FutureEvidenceBinding missing")
    require(binding.get("GeneratedOnlyAfterAuthorizedAllocation") is True, "Evidence binding must not pre-authorize allocation")
    require(binding.get("Fields") == FUTURE_BINDING_FIELDS, "Future evidence binding schema drift")
    require(binding.get("EvidenceStatusValue") == "external-unverified-edition", "Evidence status contract drift")
    require(not (ROOT / str(binding.get("Path", ""))).exists(), "Future stable evidence binding unexpectedly exists before allocation")

    promotion = contract.get("MasterPromotion")
    require(isinstance(promotion, dict), "MasterPromotion missing")
    require(promotion.get("CurrentAuthorized") is False, "Master textbook provenance promotion unexpectedly authorized")
    require(promotion.get("TargetPath") == "anki/klose/master/source_identity_extensions.csv", "Master promotion target drift")
    require(promotion.get("PreserveExternalEvidenceAfterPromotion") is True, "External evidence must remain auditable after promotion")

    master_fields, master_rows = rows(MASTER_MAP)
    require(master_fields == ["SourceID", "SourceEdition", "SourceItemKey", "NoteID", "Decision", "Status"], "Master source identity schema drift")
    leaked = [r for r in master_rows if r.get("SourceItemKey", "") in occurrence_keys]
    require(not leaked, f"Unverified third-party occurrence promoted into Master source mapping: {leaked[:3]}")

    gates = contract.get("CurrentMutationGates")
    require(isinstance(gates, dict), "CurrentMutationGates missing")
    require(gates.get("MasterSourceMappingMutationAuthorized") is False, "Master mapping mutation unexpectedly authorized")
    require(gates.get("StableNoteIDAllocationAuthorized") is False, "Stable allocation unexpectedly authorized")
    require(gates.get("AnkiMutationAuthorized") is False, "Anki mutation unexpectedly authorized")

    print("Third-party source provenance contract = pass")
    print(f"external-evidence adapters = {len(enabled)}")
    print(f"external-evidence occurrences = {occurrence_total}")
    print("SourceEdition fact in current adapters = no")
    print("synthetic/unknown SourceEdition in Master = forbidden")
    print("external evidence may support Stable identity = yes")
    print("Stable identity implies textbook provenance = no")
    print("unverified occurrence promoted to Master mapping = no")
    print("Master source mapping mutation authorized = no")
    print("Stable NoteID allocation authorized = no")
    print("Anki mutation authorized = no")


if __name__ == "__main__":
    main()
