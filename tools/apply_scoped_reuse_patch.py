#!/usr/bin/env python3
"""One-shot exact patch for explicit reuse of resolved multipart Stage-A subgroups."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"Patch anchor mismatch in {path}: expected exactly one occurrence")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


build = ROOT / "tools" / "build_third_party_corpus.py"
checker = ROOT / "tools" / "check_third_party_corpus.py"
policy = ROOT / "docs" / "THIRD_PARTY_VOCABULARY_REVIEW_POLICY.md"

replace_once(
    build,
    '''        elif len(ds) > 1 and multipart_resolved:\n            resolved_multipart[key] = ds\n\n    # Single-decision preview remains canonical-first.\n''',
    '''        elif len(ds) > 1 and multipart_resolved:\n            resolved_multipart[key] = ds\n\n    # Resolved multipart keep groups are addressable Stage-A canonical subgroups.\n    # A reuse alias may target one only by its explicit MatchKey#variant key; the\n    # subgroup remains the TargetSense/display authority.\n    multipart_keep_index: dict[str, tuple[str, dict[str, str]]] = {}\n    for base_key, ds in resolved_multipart.items():\n        for d in ds:\n            if d.get("Action") != "keep-identity":\n                continue\n            scoped = d.get("CanonicalMatchKey", "")\n            if scoped in multipart_keep_index:\n                raise SystemExit(f"Duplicate resolved multipart canonical subgroup: {scoped}")\n            multipart_keep_index[scoped] = (base_key, d)\n\n    # Single-decision preview remains canonical-first.\n''',
)

replace_once(
    build,
    '''    groups: dict[str, dict[str, object]] = {}\n    for surface in candidate_rows:\n''',
    '''    groups: dict[str, dict[str, object]] = {}\n    scoped_reuse_rows: list[tuple[dict[str, str], dict[str, str]]] = []\n    for surface in candidate_rows:\n''',
)

replace_once(
    build,
    '''        canonical = d.get("CanonicalMatchKey", "") if d["Action"] == "reuse-identity" else key\n        canonical = canonical or key\n        canonical_d = valid_decision.get(canonical) if canonical in surface_keys else None\n''',
    '''        canonical = d.get("CanonicalMatchKey", "") if d["Action"] == "reuse-identity" else key\n        canonical = canonical or key\n        if d["Action"] == "reuse-identity" and "#" in canonical:\n            target = multipart_keep_index.get(canonical)\n            if target is None:\n                raise SystemExit(f"Scoped reuse target is not a resolved multipart keep subgroup: {d['DecisionKey']} -> {canonical}")\n            target_sense = target[1].get("TargetSense", "")\n            alias_sense = d.get("TargetSense", "").strip()\n            if alias_sense and alias_sense != target_sense:\n                raise SystemExit(f"Scoped reuse TargetSense disagrees with canonical subgroup: {d['DecisionKey']} -> {canonical}")\n            scoped_reuse_rows.append((surface, d))\n            continue\n        canonical_d = valid_decision.get(canonical) if canonical in surface_keys else None\n''',
)

replace_once(
    build,
    '''                add_preview_group(\n                    groups, canonical,\n                    match_key_value=key,\n                    occurrence_count=part_count,\n                    display=target_display,\n                    sense=target_sense,\n                )\n\n    preview_rows = [{\n''',
    '''                add_preview_group(\n                    groups, canonical,\n                    match_key_value=key,\n                    occurrence_count=part_count,\n                    display=target_display,\n                    sense=target_sense,\n                )\n\n    # Single-surface aliases targeting an explicit resolved multipart subgroup are\n    # appended only after the subgroup itself has been materialized. This prevents\n    # an alias from minting an external-looking #variant identity or overriding\n    # the subgroup's learner-facing presentation.\n    for surface, d in scoped_reuse_rows:\n        canonical = d["CanonicalMatchKey"]\n        target = multipart_keep_index[canonical]\n        if canonical not in groups:\n            raise SystemExit(f"Scoped reuse canonical subgroup missing from Preview groups: {d['DecisionKey']} -> {canonical}")\n        add_preview_group(\n            groups, canonical,\n            match_key_value=surface["MatchKey"],\n            occurrence_count=int(surface["OccurrenceCount"]),\n            display="",\n            sense=target[1].get("TargetSense", ""),\n        )\n\n    preview_rows = [{\n''',
)

replace_once(
    checker,
    '''        else:\n            require(by_surface[key].get("DecisionAction") == "split-required"\n                    and by_surface[key].get("DecisionStatus") == "held",\n                    f"Incomplete/unresolved multipart must remain blocker: {key}")\n\n    expected_review = {\n''',
    '''        else:\n            require(by_surface[key].get("DecisionAction") == "split-required"\n                    and by_surface[key].get("DecisionStatus") == "held",\n                    f"Incomplete/unresolved multipart must remain blocker: {key}")\n\n    multipart_keep_index: dict[str, tuple[str, dict[str, str]]] = {}\n    for base_key, ds in resolved_multipart.items():\n        for d in ds:\n            if d.get("Action") != "keep-identity":\n                continue\n            scoped = d.get("CanonicalMatchKey", "")\n            require(scoped not in multipart_keep_index, f"Duplicate multipart canonical subgroup: {scoped}")\n            multipart_keep_index[scoped] = (base_key, d)\n\n    expected_review = {\n''',
)

replace_once(
    checker,
    '''        canonical = d.get("CanonicalMatchKey", "")\n        if canonical not in surface_keys:\n            continue\n        base = valid_decision.get(canonical)\n''',
    '''        canonical = d.get("CanonicalMatchKey", "")\n        if "#" in canonical:\n            target = multipart_keep_index.get(canonical)\n            require(target is not None,\n                    f"Scoped reuse target is not a resolved multipart keep subgroup: {key} -> {canonical}")\n            target_decision = target[1]\n            row = preview_by_key.get(canonical)\n            require(row is not None, f"Scoped reuse canonical missing from preview: {key} -> {canonical}")\n            require(key in row.get("SourceMatchKeys", "").split("|"),\n                    f"Scoped reuse provenance missing: {key} -> {canonical}")\n            require(row.get("TargetSense", "") == target_decision.get("TargetSense", ""),\n                    f"Scoped reuse changed canonical TargetSense: {key} -> {canonical}")\n            alias_sense = d.get("TargetSense", "").strip()\n            require(not alias_sense or alias_sense == target_decision.get("TargetSense", ""),\n                    f"Scoped reuse decision disagrees with canonical TargetSense: {key} -> {canonical}")\n            continue\n        if canonical not in surface_keys:\n            continue\n        base = valid_decision.get(canonical)\n''',
)

replace_once(
    checker,
    '''                require(int(row.get("SourceOccurrenceCount", "0")) == part_count,\n                        f"Multipart occurrence count drift: {d['DecisionKey']}")\n''',
    '''                scoped_alias_count = sum(\n                    len(decode_occurrence_keys(alias_d["OccurrenceKeys"], alias_d["DecisionKey"]))\n                    for alias_d in valid_decision.values()\n                    if alias_d.get("Status") == "reviewed"\n                    and alias_d.get("Action") == "reuse-identity"\n                    and alias_d.get("CanonicalMatchKey") == provisional\n                )\n                require(int(row.get("SourceOccurrenceCount", "0")) == part_count + scoped_alias_count,\n                        f"Multipart occurrence count drift: {d['DecisionKey']}")\n''',
)

policy_text = policy.read_text(encoding="utf-8")
section = '''\n\n## Resolved multipart subgroup reuse\n\n当 canonical surface 已通过 occurrence partition 形成多个 reviewed Stage-A learning units 时，\nform/alias 不得笼统 reuse 到原 surface；只有人工确认其 lexical sense 后，才允许显式指向\n已存在的 scoped provisional key（例如 `drank -> drink#verb`）。\n\n硬约束：\n\n- `#variant` target 必须是当前 complete + reviewed multipart partition 中的 `keep-identity` subgroup；\n- alias 自身必须绑定完整 current `OccurrenceKeys`，并为 `reviewed / reuse-identity`；\n- alias 不得创建新的 `#variant`，不得覆盖 subgroup 的 Display / TargetSense；\n- Preview provenance 与 occurrence count 必须合并 alias evidence；\n- source evidence 变化后仍按原 stale-evidence 规则 requeue；\n- `#variant` 仍只是 Stage-A provisional identity，不是 Stable ThirdPartyID。\n'''
if "## Resolved multipart subgroup reuse" not in policy_text:
    policy.write_text(policy_text.rstrip() + section + "\n", encoding="utf-8")
else:
    raise SystemExit("Policy already contains scoped reuse section; one-shot patch should not rerun")

print("Scoped multipart reuse patch applied")
