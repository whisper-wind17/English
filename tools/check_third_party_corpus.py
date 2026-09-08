#!/usr/bin/env python3
"""Independent Completion Recheck for the simplified third-party corpus Stage A."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
CONFIG = TP / "config" / "source_adapters.csv"
DECISIONS = TP / "review" / "identity_decisions.csv"
OUT = TP / "staging"
RENJIAO_ADAPTERS = {
    "renjiao_start1": BASE / "source_reference" / "renjiao_start1_staging",
    "renjiao_start3": BASE / "source_reference" / "renjiao_start3_staging",
}
EXPECTED_STAGING_FILES = {
    "README.md", "occurrences.csv", "surface_candidates.csv", "review_queue.csv",
    "unified_vocabulary_preview.csv",
}
EXPECTED_REVIEW_FILES = {"identity_decisions.csv"}
EXPECTED_NARROW_ADAPTER_FILES = {"README.md", "occurrences.csv"}
LEGACY_MULTI_PASS_TOOLS = {
    "build_third_party_vocabulary_stage_a.py",
    "audit_third_party_cross_source_semantics.py",
    "build_third_party_cross_source_resolution.py",
    "apply_third_party_cross_source_second_pass.py",
    "apply_third_party_cross_source_final_review.py",
    "recheck_third_party_beijing_renjiao_stage_a.py",
    "audit_third_party_renjiao_new_surfaces.py",
    "recheck_third_party_renjiao_new_surface_types.py",
    "resolve_third_party_renjiao_new_surface_routing.py",
    "recheck_third_party_renjiao_new_surface_routing.py",
    "apply_third_party_renjiao_single_token_sense_review.py",
    "recheck_third_party_renjiao_single_token_sense_review.py",
    "audit_third_party_renjiao_single_token_forms.py",
    "recheck_third_party_renjiao_single_token_forms.py",
    "sync_third_party_status_to_next.py",
}
EXPECTED_SOURCE_COUNTS = {
    "beijing_start1": 808,
    "renjiao_start1": 908,
    "renjiao_start3": 851,
    "hujiao_start3": 1111,
    "waiyan_start1": 1170,
    "waiyan_start3": 1157,
    "jijiao_start3": 605,
}
ACTIONS = {
    "keep-identity", "reuse-identity", "split-required", "held",
    "route-expression", "source-only", "pending",
}
RESOLVED_ACTIONS = {"keep-identity", "reuse-identity", "route-expression", "source-only"}
FORMER_SEMANTIC_COLLISIONS = {"may", "like", "square", "left", "cook", "cold", "study"}
LEARNER_FIRST_MARKER = "learner-first"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def decode_occurrence_keys(raw: str, decision_key: str) -> list[str]:
    require(bool(raw) and raw != "*", f"Durable wildcard/empty OccurrenceKeys: {decision_key}")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"OccurrenceKeys is not valid JSON for {decision_key}: {exc}") from exc
    require(
        isinstance(value, list) and bool(value) and all(isinstance(x, str) and x for x in value),
        f"OccurrenceKeys must be a non-empty JSON string array: {decision_key}",
    )
    require(len(value) == len(set(value)), f"Duplicate reviewed OccurrenceKeys: {decision_key}")
    return value


def partition_state(
    key: str,
    ds: list[dict[str, str]],
    current: set[str],
) -> tuple[set[str], bool, bool]:
    covered: set[str] = set()
    for d in ds:
        part = set(decode_occurrence_keys(d["OccurrenceKeys"], d["DecisionKey"]))
        require(part <= current, f"Decision occurrence evidence does not belong to its MatchKey: {d['DecisionKey']}")
        overlap = covered & part
        require(not overlap, f"Overlapping multipart OccurrenceKeys for {key}: {sorted(overlap)[:10]}")
        covered.update(part)
    complete = covered == current
    resolved = complete and all(
        d.get("Status") == "reviewed" and d.get("Action") in RESOLVED_ACTIONS for d in ds
    )
    return covered, complete, resolved


def learner_first_resolved(d: dict[str, str]) -> bool:
    return (
        d.get("Status") == "reviewed"
        and d.get("Action") == "keep-identity"
        and bool(d.get("TargetSense", "").strip())
        and LEARNER_FIRST_MARKER in d.get("DecisionBasis", "").casefold()
    )


def main() -> None:
    require({p.name for p in OUT.iterdir()} == EXPECTED_STAGING_FILES,
            f"Third-party staging contains unexpected/legacy files: {sorted(p.name for p in OUT.iterdir())}")
    require({p.name for p in (TP / "review").iterdir()} == EXPECTED_REVIEW_FILES,
            f"Third-party review directory must contain only identity_decisions.csv: {sorted(p.name for p in (TP / 'review').iterdir())}")
    for source_id, adapter_dir in RENJIAO_ADAPTERS.items():
        require(adapter_dir.exists(), f"Missing narrow Source Adapter directory: {source_id}")
        require({p.name for p in adapter_dir.iterdir()} == EXPECTED_NARROW_ADAPTER_FILES,
                f"{source_id} Source Adapter must contain only source facts: {sorted(p.name for p in adapter_dir.iterdir())}")
    present_legacy = sorted(name for name in LEGACY_MULTI_PASS_TOOLS if (ROOT / "tools" / name).exists())
    require(not present_legacy, f"Legacy multi-pass tools returned to active repo: {present_legacy}")

    config = [r for r in read_csv(CONFIG) if r.get("Enabled", "").lower() == "yes"]
    occ = read_csv(OUT / "occurrences.csv")
    surfaces = read_csv(OUT / "surface_candidates.csv")
    review = read_csv(OUT / "review_queue.csv")
    preview = read_csv(OUT / "unified_vocabulary_preview.csv")
    decisions = read_csv(DECISIONS)

    require(config, "No enabled third-party source adapters")
    configured_ids = [r.get("SourceID", "") for r in config]
    require(all(configured_ids) and len(configured_ids) == len(set(configured_ids)), "Source adapter config IDs invalid")

    expected_occ_keys: set[str] = set()
    expected_occ = 0
    for row in config:
        source_id = row["SourceID"]
        source_rows = read_csv(ROOT / row["OccurrencesPath"])
        require(all(r.get("SourceID") == source_id for r in source_rows), f"SourceID drift in adapter {source_id}")
        for source_row in source_rows:
            key = source_row.get("SourceOccurrenceKey", "")
            require(bool(key) and key not in expected_occ_keys, f"Duplicate/empty adapter SourceOccurrenceKey: {key}")
            expected_occ_keys.add(key)
        expected_occ += len(source_rows)

    actual_occ_keys = {r.get("SourceOccurrenceKey", "") for r in occ}
    require(len(occ) == expected_occ, f"Combined occurrence count drift: expected={expected_occ} actual={len(occ)}")
    require(actual_occ_keys == expected_occ_keys, "Combined occurrence set does not equal enabled adapter union")

    source_counts = Counter(r["SourceID"] for r in occ)
    for source_id in configured_ids:
        require(source_id in EXPECTED_SOURCE_COUNTS, f"Enabled adapter lacks frozen source baseline: {source_id}")
        require(source_counts[source_id] == EXPECTED_SOURCE_COUNTS[source_id],
                f"{source_id} occurrence baseline drift")

    current_by_match: dict[str, set[str]] = defaultdict(set)
    for row in occ:
        current_by_match[row["MatchKey"]].add(row["SourceOccurrenceKey"])
    surface_keys = {r["MatchKey"] for r in surfaces}
    require(len(surface_keys) == len(surfaces), "Surface MatchKey is not unique")
    require(surface_keys == set(current_by_match), "Surface set does not close over occurrence MatchKeys")

    decision_keys = [r.get("DecisionKey", "") for r in decisions]
    require(all(decision_keys) and len(decision_keys) == len(set(decision_keys)), "DecisionKey must be non-empty and unique")
    require(all(r.get("MatchKey") in surface_keys for r in decisions), "Decision references a missing enabled surface")
    require(all(r.get("Action") in ACTIONS for r in decisions), "Invalid Action in identity_decisions")
    require(all(r.get("Status") in {"reviewed", "held", "pending"} for r in decisions), "Invalid Status in identity_decisions")

    decisions_by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decisions:
        reviewed = decode_occurrence_keys(row.get("OccurrenceKeys", ""), row["DecisionKey"])
        require(set(reviewed) <= current_by_match[row["MatchKey"]],
                f"Decision occurrence evidence does not belong to its MatchKey: {row['DecisionKey']}")
        if row["Action"] == "reuse-identity":
            require(bool(row.get("CanonicalMatchKey")), f"reuse-identity lacks CanonicalMatchKey: {row['DecisionKey']}")
        if row["Action"] == "route-expression":
            require(row.get("ObjectType") == "expression", f"Expression object mismatch: {row['DecisionKey']}")
        if row["Action"] == "source-only":
            require(row.get("ObjectType") == "source-only", f"Source-only object mismatch: {row['DecisionKey']}")
        decisions_by_match[row["MatchKey"]].append(row)

    by_surface = {r["MatchKey"]: r for r in surfaces}
    stale_surfaces: set[str] = set()
    valid_decision: dict[str, dict[str, str]] = {}
    resolved_multipart: dict[str, list[dict[str, str]]] = {}
    for key in surface_keys:
        ds = decisions_by_match.get(key, [])
        if not ds:
            require(by_surface[key].get("DecisionAction") == "pending" and by_surface[key].get("DecisionStatus") == "pending",
                    f"Undecided new surface did not enter pending queue: {key}")
            continue

        _, complete, resolved = partition_state(key, ds, current_by_match[key])
        if not complete:
            stale_surfaces.add(key)
            require(by_surface[key].get("DecisionAction") == "pending" and by_surface[key].get("DecisionStatus") == "pending",
                    f"Changed/partial evidence did not requeue surface: {key}")
            require("decision-evidence-changed" in by_surface[key].get("CandidateSignals", ""),
                    f"Changed evidence signal missing: {key}")
        elif len(ds) == 1:
            valid_decision[key] = ds[0]
        elif resolved:
            resolved_multipart[key] = ds
            require(by_surface[key].get("DecisionAction") == "multipart-reviewed"
                    and by_surface[key].get("DecisionStatus") == "reviewed",
                    f"Complete reviewed split did not resolve surface: {key}")
            keep_keys: set[str] = set()
            for d in ds:
                if d.get("Action") != "keep-identity":
                    continue
                provisional = d.get("CanonicalMatchKey", "")
                require(provisional.startswith(key + "#"),
                        f"Multipart keep requires Stage-A key {key}#<variant>: {d['DecisionKey']}")
                require(provisional not in surface_keys,
                        f"Multipart provisional key collides with Source MatchKey: {provisional}")
                require(provisional not in keep_keys,
                        f"Duplicate multipart provisional key: {provisional}")
                require(bool(d.get("TargetSense", "").strip()),
                        f"Multipart keep lacks TargetSense: {d['DecisionKey']}")
                keep_keys.add(provisional)
        else:
            require(by_surface[key].get("DecisionAction") == "split-required"
                    and by_surface[key].get("DecisionStatus") == "held",
                    f"Incomplete/unresolved multipart must remain blocker: {key}")

    multipart_keep_index: dict[str, tuple[str, dict[str, str]]] = {}
    for base_key, ds in resolved_multipart.items():
        for d in ds:
            if d.get("Action") != "keep-identity":
                continue
            scoped = d.get("CanonicalMatchKey", "")
            require(scoped not in multipart_keep_index, f"Duplicate multipart canonical subgroup: {scoped}")
            multipart_keep_index[scoped] = (base_key, d)

    expected_review = {
        r["MatchKey"] for r in surfaces
        if r.get("DecisionAction") in {"pending", "held", "split-required"}
        or r.get("DecisionStatus") in {"pending", "held"}
    }
    review_keys = {r["MatchKey"] for r in review}
    require(review_keys == expected_review, "Review queue is not a pure derived blocker/pending view")
    require(not (set(resolved_multipart) & review_keys), "Resolved multipart surface remains in review queue")

    single_by_key = {k: ds[0] for k, ds in decisions_by_match.items() if len(ds) == 1}
    for key in FORMER_SEMANTIC_COLLISIONS:
        ds = decisions_by_match.get(key, [])
        require(ds, f"Known semantic collision missing decision: {key}")
        if key in stale_surfaces:
            continue
        if key in resolved_multipart:
            require(len(ds) >= 2, f"Known semantic collision resolved without partition: {key}")
        else:
            require(len(ds) == 1, f"Unexpected multipart state for former semantic collision: {key}")
            d = ds[0]
            require(
                d.get("Action") in {"split-required", "held"} or learner_first_resolved(d),
                f"Former semantic collision must remain blocked/split or use explicit learner-first narrow sense: {key}",
            )

    preview_keys = [r["CanonicalMatchKey"] for r in preview]
    require(all(preview_keys) and len(preview_keys) == len(set(preview_keys)), "Preview CanonicalMatchKey must be non-empty and unique")
    require(all(r.get("TargetSense", "").strip() for r in preview), "Preview TargetSense must be complete")

    print("Third-party simplified corpus Completion Recheck = pass")
    print(f"enabled adapters = {len(config)}")
    print(f"source occurrences = {len(occ)}")
    print(f"normalized surfaces = {len(surfaces)}")
    print(f"durable decisions = {len(decisions)}")
    print(f"review/blocker surfaces = {len(review)}")
    print(f"evidence-changed surfaces = {len(stale_surfaces)}")
    print(f"unified vocabulary preview = {len(preview)}")
    print(f"resolved multipart surfaces = {len(resolved_multipart)}")
    print("enabled adapter baselines frozen = yes")
    print("combined occurrence union closure = yes")
    print("decision occurrence evidence valid = yes")
    print("review queue derived closure = yes")
    print("multipart partition overlap = no")
    print("multipart partition completeness enforced = yes")
    print("preview canonical identity uniqueness = yes")
    print("preview TargetSense complete = yes")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
