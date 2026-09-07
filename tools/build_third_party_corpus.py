#!/usr/bin/env python3
"""Build the unified third-party Vocabulary Stage-A workspace.

Source adapters provide facts. `identity_decisions.csv` is the only content-decision
truth. Decisions are valid only for the exact SourceOccurrenceKey set they reviewed.
Candidate signals are evidence only. Stage A neither mints stable ThirdPartyID nor
performs the final Klose diff.

A MatchKey may have multiple reviewed decision rows when its Source Occurrences are
partitioned into distinct provisional learning units. Multipart partitions must be
non-overlapping and complete before the surface leaves the blocker queue.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
CONFIG = TP / "config" / "source_adapters.csv"
DECISIONS = TP / "review" / "identity_decisions.csv"
OUT = TP / "staging"

OCC_FIELDS = [
    "SourceOccurrenceKey", "SourceID", "SourceBook", "Grade", "Semester",
    "SourceRow", "Word", "MatchKey", "British", "American", "Definition", "SourceFile",
]
SURFACE_FIELDS = [
    "MatchKey", "DisplayForms", "Definitions", "SourceIDs", "SourceBooks",
    "OccurrenceCount", "CandidateSignals", "CandidateMatchKeys", "DecisionAction",
    "DecisionStatus", "CanonicalMatchKey", "TargetSense",
]
PREVIEW_FIELDS = [
    "ProvisionalIdentityKey", "CanonicalMatchKey", "DisplayWord", "TargetSense",
    "SourceMatchKeys", "SourceOccurrenceCount", "DecisionStatus",
]
ACTIONS = {
    "keep-identity", "reuse-identity", "split-required", "held",
    "route-expression", "source-only", "pending",
}
RESOLVED_ACTIONS = {"keep-identity", "reuse-identity", "route-expression", "source-only"}
IRREGULAR = {
    "children": "child", "men": "man", "women": "woman", "feet": "foot",
    "teeth": "tooth", "mice": "mouse", "geese": "goose", "slept": "sleep",
    "swam": "swim", "won": "win", "were": "be",
}
NON_PLURAL_S_FORMS = {"its", "his", "this", "is", "was", "has", "does", "yes", "news"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "" if row.get(k) is None else str(row.get(k, "")) for k in fields})


def norm_display(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", value.strip())


def match_key(value: str) -> str:
    return norm_display(value).casefold()


def format_alias_key(value: str) -> str:
    value = match_key(value)
    value = re.sub(r"(?:\.{2,}|…)+", " ", value)
    value = re.sub(r"[?!,;:]+$", "", value)
    return re.sub(r"\s+", " ", value).strip()


def morphology_keys(key: str) -> list[str]:
    if " " in key:
        return []
    out: list[str] = []
    if key in IRREGULAR:
        out.append(IRREGULAR[key])
    if key not in NON_PLURAL_S_FORMS:
        if key.endswith("ies") and len(key) > 4:
            out.append(key[:-3] + "y")
        if key.endswith("es") and len(key) > 3:
            out.append(key[:-2])
        if key.endswith("s") and len(key) > 2 and not key.endswith("ss"):
            out.append(key[:-1])
    return list(dict.fromkeys(x for x in out if x and x != key))


def unique_join(values: list[str]) -> str:
    return "|".join(dict.fromkeys(v for v in values if v))


def decode_occurrence_keys(raw: str, decision_key: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid OccurrenceKeys JSON for {decision_key}: {exc}") from exc
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
        raise SystemExit(f"Invalid OccurrenceKeys JSON array for {decision_key}")
    if len(value) != len(set(value)):
        raise SystemExit(f"Duplicate reviewed OccurrenceKeys for {decision_key}")
    return value


def enabled_adapters() -> list[tuple[str, Path]]:
    adapters: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for row in read_csv(CONFIG):
        if row.get("Enabled", "").lower() != "yes":
            continue
        source_id = row.get("SourceID", "").strip()
        rel = row.get("OccurrencesPath", "").strip()
        if not source_id or source_id in seen or not rel:
            raise SystemExit(f"Invalid source adapter config row: {row}")
        seen.add(source_id)
        adapters.append((source_id, ROOT / rel))
    if not adapters:
        raise SystemExit("No enabled third-party source adapters")
    return adapters


def build_occurrences(adapters: list[tuple[str, Path]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for source_id, path in adapters:
        for row in read_csv(path):
            if row.get("SourceID") != source_id:
                raise SystemExit(f"SourceID mismatch in {path}: {row.get('SourceID')} != {source_id}")
            key = row.get("SourceOccurrenceKey", "")
            if not key or key in seen:
                raise SystemExit(f"Duplicate/empty SourceOccurrenceKey: {key}")
            seen.add(key)
            rows.append({field: row.get(field, "") for field in OCC_FIELDS})
    return rows


def build_surfaces(occurrences: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in occurrences:
        key = row.get("MatchKey", "") or match_key(row.get("Word", ""))
        if not key:
            raise SystemExit(f"Empty MatchKey: {row.get('SourceOccurrenceKey')}")
        grouped[key].append(row)

    all_keys = set(grouped)
    alias_index: dict[str, set[str]] = defaultdict(set)
    for key, rows in grouped.items():
        for word in {r.get("Word", "") for r in rows}:
            alias = format_alias_key(word)
            if alias:
                alias_index[alias].add(key)

    morph_index: dict[str, set[str]] = defaultdict(set)
    for key in all_keys:
        for base in morphology_keys(key):
            if base in all_keys:
                morph_index[key].add(base)
                morph_index[base].add(key)

    surfaces: list[dict[str, str]] = []
    for key in sorted(grouped):
        rows = grouped[key]
        source_ids = list(dict.fromkeys(r["SourceID"] for r in rows))
        signals: list[str] = []
        candidates: list[str] = []
        if len(source_ids) > 1:
            signals.append("cross-source-exact")
        if len(rows) > 1:
            signals.append("multiple-occurrences")
        if " " in key:
            signals.append("multiword")
        if re.search(r"[?!]|\.{2,}|…", unique_join([r.get("Word", "") for r in rows])):
            signals.append("punctuated")
        for word in {r.get("Word", "") for r in rows}:
            alias = format_alias_key(word)
            for other in sorted(alias_index.get(alias, set())):
                if other != key:
                    signals.append("format-alias")
                    candidates.append(other)
        if morph_index.get(key):
            signals.append("morphology")
            candidates.extend(sorted(morph_index[key]))
        surfaces.append({
            "MatchKey": key,
            "DisplayForms": unique_join([r["Word"] for r in rows]),
            "Definitions": unique_join([r["Definition"] for r in rows]),
            "SourceIDs": "|".join(source_ids),
            "SourceBooks": unique_join([f"{r['SourceID']}:{r['SourceBook']}" for r in rows]),
            "OccurrenceCount": str(len(rows)),
            "CandidateSignals": unique_join(signals),
            "CandidateMatchKeys": unique_join(candidates),
        })
    return surfaces


def load_decisions(surface_keys: set[str], occurrence_keys: set[str]) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen: set[str] = set()
    for row in read_csv(DECISIONS):
        dkey = row.get("DecisionKey", "")
        key = row.get("MatchKey", "")
        if not dkey or dkey in seen:
            raise SystemExit(f"Duplicate/empty DecisionKey: {dkey}")
        if key not in surface_keys:
            raise SystemExit(f"Decision references missing enabled surface: {key}")
        if row.get("Action") not in ACTIONS:
            raise SystemExit(f"Invalid Action for {dkey}: {row.get('Action')}")
        if row.get("Status") not in {"reviewed", "held", "pending"}:
            raise SystemExit(f"Invalid Status for {dkey}: {row.get('Status')}")
        if row.get("Action") == "reuse-identity" and not row.get("CanonicalMatchKey"):
            raise SystemExit(f"reuse-identity lacks CanonicalMatchKey: {dkey}")
        raw = row.get("OccurrenceKeys", "")
        if not raw or raw == "*":
            raise SystemExit(f"Durable decision must bind explicit OccurrenceKeys: {dkey}")
        keys = decode_occurrence_keys(raw, dkey)
        if not set(keys) <= occurrence_keys:
            raise SystemExit(f"Invalid reviewed OccurrenceKeys for {dkey}")
        seen.add(dkey)
        groups[key].append(row)
    return groups


def partition_state(
    key: str,
    ds: list[dict[str, str]],
    current: set[str],
) -> tuple[set[str], bool, bool]:
    """Return (covered, complete, resolved); reject overlap immediately."""
    covered: set[str] = set()
    for d in ds:
        part = set(decode_occurrence_keys(d.get("OccurrenceKeys", ""), d.get("DecisionKey", "")))
        if not part <= current:
            raise SystemExit(f"Decision occurrence evidence does not belong to MatchKey {key}: {d.get('DecisionKey')}")
        overlap = covered & part
        if overlap:
            raise SystemExit(f"Overlapping multipart OccurrenceKeys for {key}: {sorted(overlap)[:10]}")
        covered.update(part)
    complete = covered == current
    resolved = complete and all(
        d.get("Status") == "reviewed" and d.get("Action") in RESOLVED_ACTIONS for d in ds
    )
    if len(ds) > 1 and resolved:
        split_keys: set[str] = set()
        for d in ds:
            if d.get("Action") != "keep-identity":
                continue
            provisional = d.get("CanonicalMatchKey", "")
            if not provisional or not provisional.startswith(key + "#"):
                raise SystemExit(
                    f"Multipart keep-identity requires CanonicalMatchKey={key}#<variant>: {d.get('DecisionKey')}"
                )
            if provisional in split_keys:
                raise SystemExit(f"Duplicate multipart provisional key for {key}: {provisional}")
            if not d.get("TargetSense", "").strip():
                raise SystemExit(f"Multipart keep-identity lacks TargetSense: {d.get('DecisionKey')}")
            split_keys.add(provisional)
    return covered, complete, resolved


def add_preview_group(
    groups: dict[str, dict[str, object]],
    canonical: str,
    *,
    match_key_value: str,
    occurrence_count: int,
    display: str,
    sense: str,
) -> None:
    group = groups.setdefault(canonical, {
        "matchkeys": [], "occ": 0, "display": "", "sense": "",
    })
    group["matchkeys"].append(match_key_value)
    group["occ"] = int(group["occ"]) + occurrence_count
    if display and not group["display"]:
        group["display"] = display
    if sense and not group["sense"]:
        group["sense"] = sense


def main() -> None:
    adapters = enabled_adapters()
    occurrences = build_occurrences(adapters)
    surfaces = build_surfaces(occurrences)
    surface_keys = {r["MatchKey"] for r in surfaces}
    all_occurrence_keys = {r["SourceOccurrenceKey"] for r in occurrences}
    current_by_match: dict[str, set[str]] = defaultdict(set)
    for row in occurrences:
        current_by_match[row["MatchKey"]].add(row["SourceOccurrenceKey"])
    decisions = load_decisions(surface_keys, all_occurrence_keys)

    states: dict[str, tuple[set[str], bool, bool]] = {}
    candidate_rows: list[dict[str, str]] = []
    review_rows: list[dict[str, str]] = []
    for surface in surfaces:
        key = surface["MatchKey"]
        ds = decisions.get(key, [])
        current = current_by_match[key]
        if ds:
            states[key] = partition_state(key, ds, current)
            _, complete, multipart_resolved = states[key]
        else:
            complete, multipart_resolved = False, False

        stale = bool(ds) and not complete
        if not ds:
            action, status, canonical, sense = "pending", "pending", "", ""
        elif stale:
            action, status, canonical, sense = "pending", "pending", "", ""
            surface["CandidateSignals"] = unique_join([surface["CandidateSignals"], "decision-evidence-changed"])
        elif len(ds) == 1:
            d = ds[0]
            action, status = d["Action"], d["Status"]
            canonical, sense = d.get("CanonicalMatchKey", ""), d.get("TargetSense", "")
        else:
            action = "multipart-reviewed" if multipart_resolved else "split-required"
            status = "reviewed" if multipart_resolved else "held"
            canonical, sense = "", ""

        row = dict(surface)
        row.update({
            "DecisionAction": action,
            "DecisionStatus": status,
            "CanonicalMatchKey": canonical,
            "TargetSense": sense,
        })
        candidate_rows.append(row)
        if action in {"pending", "held", "split-required"} or status in {"pending", "held"}:
            review_rows.append(row)

    surface_by_key = {r["MatchKey"]: r for r in candidate_rows}
    valid_decision: dict[str, dict[str, str]] = {}
    resolved_multipart: dict[str, list[dict[str, str]]] = {}
    for key in surface_keys:
        ds = decisions.get(key, [])
        if not ds:
            continue
        _, complete, multipart_resolved = states[key]
        if len(ds) == 1 and complete:
            valid_decision[key] = ds[0]
        elif len(ds) > 1 and multipart_resolved:
            resolved_multipart[key] = ds

    # Resolved multipart keep groups are addressable Stage-A canonical subgroups.
    # A reuse alias may target one only by its explicit MatchKey#variant key; the
    # subgroup remains the TargetSense/display authority.
    multipart_keep_index: dict[str, tuple[str, dict[str, str]]] = {}
    for base_key, ds in resolved_multipart.items():
        for d in ds:
            if d.get("Action") != "keep-identity":
                continue
            scoped = d.get("CanonicalMatchKey", "")
            if scoped in multipart_keep_index:
                raise SystemExit(f"Duplicate resolved multipart canonical subgroup: {scoped}")
            multipart_keep_index[scoped] = (base_key, d)

    # Single-decision preview remains canonical-first.
    groups: dict[str, dict[str, object]] = {}
    scoped_reuse_rows: list[tuple[dict[str, str], dict[str, str]]] = []
    for surface in candidate_rows:
        key = surface["MatchKey"]
        d = valid_decision.get(key)
        if not d or d.get("Status") != "reviewed" or d.get("Action") not in {"keep-identity", "reuse-identity"}:
            continue

        canonical = d.get("CanonicalMatchKey", "") if d["Action"] == "reuse-identity" else key
        canonical = canonical or key
        if d["Action"] == "reuse-identity" and "#" in canonical:
            target = multipart_keep_index.get(canonical)
            if target is None:
                raise SystemExit(f"Scoped reuse target is not a resolved multipart keep subgroup: {d['DecisionKey']} -> {canonical}")
            target_sense = target[1].get("TargetSense", "")
            alias_sense = d.get("TargetSense", "").strip()
            if alias_sense and alias_sense != target_sense:
                raise SystemExit(f"Scoped reuse TargetSense disagrees with canonical subgroup: {d['DecisionKey']} -> {canonical}")
            scoped_reuse_rows.append((surface, d))
            continue
        canonical_d = valid_decision.get(canonical) if canonical in surface_keys else None
        if d["Action"] == "reuse-identity" and canonical in surface_keys:
            if not canonical_d or canonical_d.get("Status") != "reviewed" or canonical_d.get("Action") != "keep-identity":
                continue

        display = ""
        sense = ""
        if canonical in surface_keys:
            if canonical_d and canonical_d.get("Status") == "reviewed" and canonical_d.get("Action") == "keep-identity":
                base_surface = surface_by_key[canonical]
                display = base_surface["DisplayForms"].split("|")[0]
                sense = canonical_d.get("TargetSense", "")
        else:
            display = canonical
            sense = d.get("TargetSense", "")
        add_preview_group(
            groups, canonical,
            match_key_value=key,
            occurrence_count=int(surface["OccurrenceCount"]),
            display=display,
            sense=sense,
        )

    # Multipart preview: every keep group gets its own explicit Stage-A provisional
    # CanonicalMatchKey (MatchKey#variant). Reuse groups join the reviewed canonical.
    for key, ds in resolved_multipart.items():
        surface = surface_by_key[key]
        display = surface["DisplayForms"].split("|")[0]
        for d in ds:
            action = d.get("Action")
            part_count = len(decode_occurrence_keys(d["OccurrenceKeys"], d["DecisionKey"]))
            if action == "keep-identity":
                canonical = d["CanonicalMatchKey"]
                if canonical in surface_keys:
                    raise SystemExit(f"Multipart provisional key collides with Source MatchKey: {canonical}")
                if canonical in groups:
                    raise SystemExit(f"Multipart provisional key collides with Preview identity: {canonical}")
                add_preview_group(
                    groups, canonical,
                    match_key_value=key,
                    occurrence_count=part_count,
                    display=display,
                    sense=d.get("TargetSense", ""),
                )
            elif action == "reuse-identity":
                canonical = d.get("CanonicalMatchKey", "")
                canonical_d = valid_decision.get(canonical) if canonical in surface_keys else None
                if canonical in surface_keys:
                    if not canonical_d or canonical_d.get("Status") != "reviewed" or canonical_d.get("Action") != "keep-identity":
                        raise SystemExit(f"Multipart reuse bypasses canonical blocker: {d['DecisionKey']} -> {canonical}")
                    base_surface = surface_by_key[canonical]
                    target_display = base_surface["DisplayForms"].split("|")[0]
                    target_sense = canonical_d.get("TargetSense", "")
                else:
                    target_display = canonical
                    target_sense = d.get("TargetSense", "")
                add_preview_group(
                    groups, canonical,
                    match_key_value=key,
                    occurrence_count=part_count,
                    display=target_display,
                    sense=target_sense,
                )

    # Single-surface aliases targeting an explicit resolved multipart subgroup are
    # appended only after the subgroup itself has been materialized. This prevents
    # an alias from minting an external-looking #variant identity or overriding
    # the subgroup's learner-facing presentation.
    for surface, d in scoped_reuse_rows:
        canonical = d["CanonicalMatchKey"]
        target = multipart_keep_index[canonical]
        if canonical not in groups:
            raise SystemExit(f"Scoped reuse canonical subgroup missing from Preview groups: {d['DecisionKey']} -> {canonical}")
        add_preview_group(
            groups, canonical,
            match_key_value=surface["MatchKey"],
            occurrence_count=int(surface["OccurrenceCount"]),
            display="",
            sense=target[1].get("TargetSense", ""),
        )

    preview_rows = [{
        "ProvisionalIdentityKey": f"candidate:{canonical}",
        "CanonicalMatchKey": canonical,
        "DisplayWord": str(group["display"]),
        "TargetSense": str(group["sense"]),
        "SourceMatchKeys": unique_join(list(group["matchkeys"])),
        "SourceOccurrenceCount": str(group["occ"]),
        "DecisionStatus": "reviewed",
    } for canonical, group in sorted(groups.items())]

    if len({r["CanonicalMatchKey"] for r in preview_rows}) != len(preview_rows):
        raise SystemExit("Preview CanonicalMatchKey is not unique")
    if len({r["ProvisionalIdentityKey"] for r in preview_rows}) != len(preview_rows):
        raise SystemExit("Preview ProvisionalIdentityKey is not unique")

    write_csv(OUT / "occurrences.csv", OCC_FIELDS, occurrences)
    write_csv(OUT / "surface_candidates.csv", SURFACE_FIELDS, candidate_rows)
    write_csv(OUT / "review_queue.csv", SURFACE_FIELDS, review_rows)
    write_csv(OUT / "unified_vocabulary_preview.csv", PREVIEW_FIELDS, preview_rows)

    action_counts = Counter(r["DecisionAction"] for r in candidate_rows)
    source_counts = Counter(r["SourceID"] for r in occurrences)
    stale_count = sum("decision-evidence-changed" in r.get("CandidateSignals", "") for r in candidate_rows)
    readme = f"""# Third-party Vocabulary — Simplified Stage A

Active data flow:

```text
config/source_adapters.csv
+ standardized adapter occurrences
+ review/identity_decisions.csv
→ tools/build_third_party_corpus.py
→ surface_candidates.csv
→ review_queue.csv
→ unified_vocabulary_preview.csv
→ tools/check_third_party_corpus.py
```

```text
Enabled adapters          = {len(adapters)}
Source occurrences        = {len(occurrences)}
Normalized surfaces       = {len(surfaces)}
Vocabulary preview        = {len(preview_rows)}
Review/blocker surfaces   = {len(review_rows)}
Evidence-changed surfaces = {stale_count}
Multipart resolved        = {len(resolved_multipart)}
```

Each durable decision is bound to the exact Source Occurrences it reviewed via an
unambiguous JSON array in `OccurrenceKeys`. Additional source evidence automatically
re-queues that MatchKey. Multipart split decisions must form a disjoint, complete
occurrence partition before leaving review. Candidate signals are evidence only.
Canonical blockers cannot be bypassed by reuse aliases. Stable ThirdPartyID is not
minted and Stage-B Klose diff is not executed here.
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    print(f"enabled adapters = {len(adapters)}")
    for source_id in sorted(source_counts):
        print(f"source {source_id} occurrences = {source_counts[source_id]}")
    print(f"third-party source occurrences = {len(occurrences)}")
    print(f"third-party surfaces = {len(surfaces)}")
    print(f"unified vocabulary preview = {len(preview_rows)}")
    print(f"review/blocker surfaces = {len(review_rows)}")
    print(f"evidence-changed surfaces = {stale_count}")
    print(f"multipart resolved = {len(resolved_multipart)}")
    for action in sorted(action_counts):
        print(f"action {action} = {action_counts[action]}")
    print("Split occurrence partition overlap = no")
    print("Split occurrence partition completeness = enforced")
    print("Canonical blocker bypass = no")
    print("Canonical TargetSense precedence = yes")
    print("Stable ThirdPartyID minted = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
