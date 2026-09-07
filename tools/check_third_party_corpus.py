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
}


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
        if source_id in EXPECTED_SOURCE_COUNTS:
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
    require(all(r.get("Action") in {
        "keep-identity", "reuse-identity", "split-required", "held",
        "route-expression", "source-only", "pending",
    } for r in decisions), "Invalid Action in identity_decisions")
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
    for key in surface_keys:
        ds = decisions_by_match.get(key, [])
        reviewed: set[str] = set()
        for d in ds:
            reviewed.update(decode_occurrence_keys(d["OccurrenceKeys"], d["DecisionKey"]))
        if not ds:
            require(by_surface[key].get("DecisionAction") == "pending" and by_surface[key].get("DecisionStatus") == "pending",
                    f"Undecided new surface did not enter pending queue: {key}")
        elif reviewed != current_by_match[key]:
            stale_surfaces.add(key)
            require(by_surface[key].get("DecisionAction") == "pending" and by_surface[key].get("DecisionStatus") == "pending",
                    f"Changed source evidence did not requeue reviewed surface: {key}")
            require("decision-evidence-changed" in by_surface[key].get("CandidateSignals", ""),
                    f"Changed evidence signal missing: {key}")
        elif len(ds) == 1:
            valid_decision[key] = ds[0]

    expected_review = {
        r["MatchKey"] for r in surfaces
        if r.get("DecisionAction") in {"pending", "held", "split-required"}
        or r.get("DecisionStatus") in {"pending", "held"}
    }
    require({r["MatchKey"] for r in review} == expected_review, "Review queue is not a pure derived blocker/pending view")

    by_key = {r["MatchKey"]: r for r in decisions}
    for key in ("may", "like", "square", "left", "cook", "cold", "study"):
        require(key in by_key and by_key[key]["Action"] in {"split-required", "held"},
                f"Known semantic collision flattened: {key}")
    require(by_key.get("danced", {}).get("Action") == "reuse-identity" and by_key["danced"]["CanonicalMatchKey"] == "dance",
            "danced canonicalization lost")
    require(by_key.get("cartoons", {}).get("Action") == "reuse-identity" and by_key["cartoons"]["CanonicalMatchKey"] == "cartoon",
            "cartoons canonicalization lost")
    require(by_key.get("gloves", {}).get("Action") == "reuse-identity" and by_key["gloves"]["CanonicalMatchKey"] == "glove",
            "gloves canonicalization lost")
    require(by_key.get("scissors", {}).get("Action") == "keep-identity", "scissors lexicalized decision lost")
    require(by_key.get("crossroads", {}).get("Action") == "keep-identity", "crossroads lexicalized decision lost")
    for key in ("slept", "swam", "were", "won"):
        require(by_key.get(key, {}).get("Action") == "held", f"Irregular-form blocker lost: {key}")

    for key in (
        "a few", "get well", "how many", "ice cream", "make use of", "pencil case",
        "sweet potato", "take part in", "the u.k.", "the u.s.a.", "the united states of america",
    ):
        row = by_key.get(key, {})
        require(row, f"Missing Beijing multiword migration guard: {key}")
        require(row.get("DecisionBasis") != "beijing-seed-carried-forward",
                f"Beijing multiword bypassed explicit object review: {key}")
        if row.get("DecisionBasis") == "beijing-seed-object-review-required":
            require(row.get("Action") == "pending" and row.get("Status") == "pending",
                    f"Unreviewed Beijing multiword must stay pending: {key}")

    preview_by_key = {r["CanonicalMatchKey"]: r for r in preview}
    preview_keys = set(preview_by_key)
    require(len(preview_keys) == len(preview), "Preview canonical key is not unique")
    require(not (preview_keys & {"may", "like", "square", "left", "cook", "cold", "study"}),
            "Known semantic blocker leaked into preview")

    preview_source_matchkeys: set[str] = set()
    for row in preview:
        preview_source_matchkeys.update(x for x in row.get("SourceMatchKeys", "").split("|") if x)
    require(not (stale_surfaces & preview_source_matchkeys),
            f"Evidence-stale source surfaces leaked into preview: {sorted(stale_surfaces & preview_source_matchkeys)[:10]}")

    # Generic canonical integrity: reuse cannot bypass a current canonical blocker;
    # when the canonical current surface is reviewed keep-identity, its TargetSense
    # is authoritative for learner-facing preview.
    blocked_canonical_targets: set[str] = set()
    for key, d in valid_decision.items():
        if d.get("Status") != "reviewed" or d.get("Action") != "reuse-identity":
            continue
        canonical = d.get("CanonicalMatchKey", "")
        if canonical not in surface_keys:
            continue
        base = valid_decision.get(canonical)
        if not base or base.get("Status") != "reviewed" or base.get("Action") != "keep-identity":
            blocked_canonical_targets.add(canonical)
            require(key not in preview_source_matchkeys,
                    f"Reuse alias bypassed canonical blocker in preview: {key} -> {canonical}")
        else:
            require(canonical in preview_by_key, f"Reviewed canonical missing from preview: {canonical}")
            require(preview_by_key[canonical].get("TargetSense", "") == base.get("TargetSense", ""),
                    f"Alias TargetSense overwrote canonical TargetSense: {key} -> {canonical}")
    require(not (blocked_canonical_targets & preview_keys),
            f"Blocked canonical targets leaked into preview: {sorted(blocked_canonical_targets & preview_keys)[:10]}")

    # Quality-audit regression guards.
    require(by_key.get("ice-cream", {}).get("Action") == "reuse-identity"
            and by_key["ice-cream"].get("CanonicalMatchKey") == "ice cream",
            "ice-cream orthographic alias regression")
    require(by_key.get("listening to music", {}).get("Action") == "reuse-identity"
            and by_key["listening to music"].get("CanonicalMatchKey") == "listen to music",
            "listen-to-music activity canonicalization regression")
    require(by_key.get("smart", {}).get("TargetSense") == "聪明的；机灵的",
            "smart canonical TargetSense regression")
    for key in ("old", "thin", "stay", "do", "watch"):
        require(key not in preview_keys, f"Blocked canonical leaked into preview via reuse alias: {key}")
    require(preview_by_key.get("candy", {}).get("TargetSense") == "糖果",
            "candy canonical TargetSense polluted by candies alias")
    require(preview_by_key.get("story", {}).get("TargetSense") == "故事",
            "story canonical TargetSense polluted by stories alias")
    require(preview_by_key.get("smart", {}).get("TargetSense") == "聪明的；机灵的",
            "smart preview TargetSense is not canonical")
    require("ice-cream" not in preview_keys and "ice cream" in preview_keys,
            "ice-cream duplicate identity remains in preview")
    require("listening to music" not in preview_keys and "listen to music" in preview_keys,
            "listen-to-music duplicate activity identity remains in preview")

    actions = Counter(r["Action"] for r in decisions)
    print("Third-party Simplified Completion Recheck = pass")
    print(f"enabled adapters = {len(config)}")
    print(f"source occurrences = {len(occ)}")
    print(f"normalized surfaces = {len(surfaces)}")
    print(f"durable decisions = {len(decisions)}")
    print(f"review/blocker surfaces = {len(review)}")
    print(f"unified vocabulary preview = {len(preview)}")
    print(f"evidence-changed surfaces = {len(stale_surfaces)}")
    for action in sorted(actions):
        print(f"decision {action} = {actions[action]}")
    print("Explicit reviewed OccurrenceKeys = yes")
    print("OccurrenceKeys serialization = JSON array")
    print("Changed source evidence requeues decision = yes")
    print("Stale source surface excluded from preview provenance = yes")
    print("Canonical blocker bypass = no")
    print("Canonical TargetSense precedence = yes")
    print("Simplified physical layout = yes")
    print("Legacy multi-pass tools absent = yes")
    print("Source occurrence closure = yes")
    print("Known semantic blockers preserved = yes")
    print("Known morphology decisions preserved = yes")
    print("Beijing multiword requires explicit review = yes")
    print("Stable ThirdPartyID minted = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
