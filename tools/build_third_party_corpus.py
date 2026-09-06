#!/usr/bin/env python3
"""Build the simplified Third-party Vocabulary Stage-A workspace.

Long-term model:
  standardized source occurrences
  + one durable identity_decisions.csv
  -> candidate surfaces / review queue / unified vocabulary preview

Candidate signals are evidence only. All content decisions live in data, not in
source-specific Python passes. The first run can bootstrap identity_decisions.csv
from the previously reviewed Beijing + Renjiao staging outputs; after that the
file is durable review truth and is never regenerated automatically.

Stage A only: no stable ThirdPartyID minting and no Klose final diff.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
TP = BASE / "third_party_vocabulary"
OUT = TP / "staging"
DECISIONS = TP / "review" / "identity_decisions.csv"

ADAPTERS = [
    ("beijing_start1", BASE / "source_reference" / "beijing_start1_staging" / "occurrences.csv"),
    ("renjiao_start1", BASE / "source_reference" / "renjiao_start1_staging" / "occurrences.csv"),
]

# Legacy reviewed outputs are migration inputs only. They are ignored once
# identity_decisions.csv exists.
LEGACY_CROSS = OUT / "cross_source_identity_resolution.csv"
LEGACY_RENJIAO_ROUTE = OUT / "renjiao_new_surface_route_resolution.csv"
LEGACY_RENJIAO_FORM = OUT / "renjiao_single_token_form_audit.csv"
LEGACY_RENJIAO_MORPH = TP / "review" / "renjiao_start1_morphology_resolution.csv"
RENJIAO_SURFACE = BASE / "source_reference" / "renjiao_start1_staging" / "surface_inventory.csv"
BEIJING_SEMANTIC = BASE / "source_reference" / "beijing_start1_staging" / "semantic_resolution_review.csv"
BEIJING_IDENTITY = BASE / "source_reference" / "beijing_start1_staging" / "identity_resolution_review.csv"
BEIJING_VARIANT = BASE / "source_reference" / "beijing_start1_staging" / "source_variant_resolution_review.csv"

OCC_FIELDS = [
    "SourceOccurrenceKey", "SourceID", "SourceBook", "Grade", "Semester",
    "SourceRow", "Word", "MatchKey", "British", "American", "Definition", "SourceFile",
]
DECISION_FIELDS = [
    "DecisionKey", "MatchKey", "OccurrenceKeys", "Action", "CanonicalMatchKey",
    "ObjectType", "TargetSense", "Status", "Confidence", "DecisionBasis", "Rationale",
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

IRREGULAR = {
    "children": "child", "men": "man", "women": "woman", "feet": "foot",
    "teeth": "tooth", "mice": "mouse", "geese": "goose", "slept": "sleep",
    "swam": "swim", "won": "win", "were": "be",
}
NON_PLURAL_S_FORMS = {"its", "his", "this", "is", "was", "has", "does", "yes", "news"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: "" if row.get(k) is None else str(row.get(k, "")) for k in fields})


def norm_display(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("’", "'").replace("‘", "'")
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


def canonical_action_from_cross(value: str) -> str:
    if value == "reuse-learning-unit":
        return "keep-identity"
    if value in {"partial-overlap-split-required", "do-not-merge"}:
        return "split-required"
    if value.startswith("held-"):
        return "held"
    return "pending"


def canonical_action_from_route(value: str) -> tuple[str, str]:
    if value == "new-vocabulary-learning-unit-candidate":
        return "keep-identity", "vocabulary"
    if value == "canonical-form-alias-candidate":
        return "reuse-identity", "vocabulary"
    if value in {"held-identity-form-policy", "held-source-context-required"}:
        return "held", "vocabulary"
    if value == "within-source-split-required":
        return "split-required", "vocabulary"
    if value == "route-expression-candidate":
        return "route-expression", "expression"
    if value == "route-source-chunk-no-vocabulary-identity":
        return "source-only", "source-only"
    if value.startswith("pending-"):
        return "pending", "vocabulary"
    return "pending", "vocabulary"


def canonical_action_from_form(value: str) -> str:
    if value == "reuse-base-learning-unit-candidate":
        return "reuse-identity"
    if value == "keep-distinct-learning-unit-candidate":
        return "keep-identity"
    if value.startswith("held-"):
        return "held"
    if value == "pending-form-review":
        return "pending"
    return "pending"


def new_decision(key: str, action: str, *, canonical: str = "", object_type: str = "vocabulary",
                 sense: str = "", status: str = "reviewed", confidence: str = "medium",
                 basis: str = "", rationale: str = "") -> dict[str, str]:
    return {
        "DecisionKey": f"surface:{key}",
        "MatchKey": key,
        "OccurrenceKeys": "*",
        "Action": action,
        "CanonicalMatchKey": canonical,
        "ObjectType": object_type,
        "TargetSense": sense,
        "Status": status,
        "Confidence": confidence,
        "DecisionBasis": basis,
        "Rationale": rationale,
    }


def bootstrap_decisions(surface_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """One-time migration of already-reviewed legacy state into one decision table."""
    by_key: dict[str, dict[str, str]] = {}
    for row in surface_rows:
        key = row["MatchKey"]
        source_ids = set((row.get("SourceIDs") or "").split("|"))
        if source_ids == {"beijing_start1"}:
            by_key[key] = new_decision(
                key, "keep-identity", status="reviewed", confidence="medium",
                basis="beijing-seed-carried-forward",
                rationale="Beijing Stage-A seed surface carried forward into the simplified corpus model; specific reviewed risk overlays below take precedence.",
            )
        else:
            by_key[key] = new_decision(
                key, "pending", status="pending", confidence="",
                basis="migration-unresolved",
                rationale="No durable simplified decision was available before migration.",
            )

    # Beijing high-risk surface decisions. These are applied before cross-source
    # decisions because a later cross-source decision has the broader evidence scope.
    semantic_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(BEIJING_SEMANTIC):
        key = row.get("SourceOccurrenceKey", "").split("|")[-1] or match_key(row.get("Word", ""))
        semantic_by_key[key].append(row)
    for key, rows in semantic_by_key.items():
        if key not in by_key:
            continue
        decisions = {r.get("ProposedDecision", "") for r in rows}
        senses = unique_join([r.get("ProposedTargetSense", "") for r in rows])
        if "held" in decisions:
            action, status = "held", "held"
        elif len(rows) > 1 and "new-sense-candidate" in decisions:
            action, status = "split-required", "held"
        else:
            action, status = "keep-identity", "reviewed"
        by_key[key] = new_decision(
            key, action, sense=senses, status=status,
            confidence=min((r.get("Confidence") or "medium" for r in rows), default="medium"),
            basis="beijing-semantic-review-migration",
            rationale=unique_join([r.get("Evidence", "") for r in rows]),
        )

    for row in read_csv(BEIJING_IDENTITY):
        key = row.get("MatchKey", "")
        if key not in by_key:
            continue
        proposed = row.get("ProposedDecision", "")
        action = "held" if proposed == "held" else "keep-identity"
        status = "held" if proposed == "held" else "reviewed"
        by_key[key] = new_decision(
            key, action, status=status, confidence=row.get("Confidence", ""),
            basis="beijing-identity-review-migration", rationale=row.get("Evidence", ""),
        )

    # Beijing morphology/variant review: only overlay when the reviewed row
    # identifies a concrete form relation. Irregular policy blockers remain held.
    for row in read_csv(BEIJING_VARIANT):
        key = row.get("MatchKey", "")
        related = row.get("RelatedForm", "")
        proposed = row.get("ProposedDecision", "")
        if not key or not related:
            continue
        if proposed == "reuse" and related in by_key:
            by_key[related] = new_decision(
                related, "reuse-identity", canonical=key, status="reviewed",
                confidence=row.get("Confidence", ""), basis="beijing-variant-review-migration",
                rationale=row.get("Reason", ""),
            )
        elif proposed == "held":
            for target in (key, related):
                if target in by_key:
                    by_key[target] = new_decision(
                        target, "held", status="held", confidence=row.get("Confidence", ""),
                        basis="beijing-variant-review-migration", rationale=row.get("Reason", ""),
                    )
        elif proposed == "do-not-merge" and related in by_key:
            by_key[related] = new_decision(
                related, "keep-identity", status="reviewed", confidence=row.get("Confidence", ""),
                basis="beijing-variant-review-migration", rationale=row.get("Reason", ""),
            )

    # Renjiao new-surface routing and semantic decisions.
    for row in read_csv(LEGACY_RENJIAO_ROUTE):
        key = row.get("MatchKey", "")
        if key not in by_key:
            continue
        action, object_type = canonical_action_from_route(row.get("ProposedObjectDecision", ""))
        status_raw = row.get("ResolutionStatus", "")
        status = "pending" if status_raw == "pending" else ("held" if action == "held" else "reviewed")
        canonical = row.get("TargetReference", "") if action == "reuse-identity" else ""
        by_key[key] = new_decision(
            key, action, canonical=canonical, object_type=object_type,
            sense=row.get("TargetReference", "") if action == "keep-identity" else "",
            status=status, confidence=row.get("Confidence", ""),
            basis=row.get("ResolutionBasis", "renjiao-route-migration"),
            rationale=row.get("Rationale", ""),
        )

    # Renjiao morphology relations against the Beijing seed.
    for row in read_csv(LEGACY_RENJIAO_MORPH):
        key = row.get("RenjiaoMatchKey", "")
        canonical = row.get("BeijingMatchKey", "")
        if key not in by_key:
            continue
        proposed = row.get("ProposedDecision", "")
        if proposed == "reuse-learning-unit":
            action, status = "reuse-identity", "reviewed"
        elif proposed == "do-not-merge":
            action, status = "keep-identity", "reviewed"
        else:
            action, status = "held", "held"
        by_key[key] = new_decision(
            key, action, canonical=canonical if action == "reuse-identity" else "",
            status=status, confidence=row.get("Confidence", ""),
            basis="renjiao-morphology-review-migration", rationale=row.get("Rationale", ""),
        )

    # The one narrow format alias is still candidate-only under project rules.
    for row in read_csv(RENJIAO_SURFACE):
        if row.get("StageAClass") != "format-alias-overlap":
            continue
        key = row.get("MatchKey", "")
        if key in by_key and by_key[key]["Status"] == "pending":
            by_key[key] = new_decision(
                key, "pending", canonical=row.get("SeedMatchKeys", ""), status="pending",
                confidence="", basis="format-alias-candidate-migration",
                rationale="Presentation-only alias candidate remains reviewable; candidate matching is not identity truth.",
            )

    # Cross-source exact-overlap review is broader than source-local decisions.
    for row in read_csv(LEGACY_CROSS):
        key = row.get("MatchKey", "")
        if key not in by_key:
            continue
        action = canonical_action_from_cross(row.get("ProposedDecision", ""))
        status = "held" if action in {"held", "split-required"} else "reviewed"
        by_key[key] = new_decision(
            key, action, sense=row.get("ProposedSense", ""), status=status,
            confidence=row.get("Confidence", ""), basis=row.get("ResolutionBasis", "cross-source-migration"),
            rationale=row.get("Rationale", ""),
        )

    # Form audit is the most specific Renjiao source-local identity overlay.
    for row in read_csv(LEGACY_RENJIAO_FORM):
        key = row.get("MatchKey", "")
        if key not in by_key:
            continue
        action = canonical_action_from_form(row.get("ProposedFormDecision", ""))
        status = "pending" if action == "pending" else ("held" if action == "held" else "reviewed")
        by_key[key] = new_decision(
            key, action,
            canonical=row.get("BaseMatchKey", "") if action == "reuse-identity" else "",
            status=status, confidence=row.get("Confidence", ""),
            basis="renjiao-form-review-migration", rationale=row.get("Rationale", ""),
        )

    rows = [by_key[k] for k in sorted(by_key)]
    if len(rows) != len(surface_rows):
        raise SystemExit("Bootstrap decision count does not cover every current surface")
    return rows


def build_occurrences() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for source_id, path in ADAPTERS:
        source_rows = read_csv(path)
        if not source_rows:
            raise SystemExit(f"Missing/empty source adapter occurrences: {path}")
        for row in source_rows:
            if row.get("SourceID") != source_id:
                raise SystemExit(f"SourceID mismatch: {path}: {row.get('SourceID')} != {source_id}")
            occ_key = row.get("SourceOccurrenceKey", "")
            if not occ_key or occ_key in seen:
                raise SystemExit(f"Duplicate/empty SourceOccurrenceKey: {occ_key}")
            seen.add(occ_key)
            rows.append({f: row.get(f, "") for f in OCC_FIELDS})
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

    surfaces: list[dict[str, str]] = []
    for key in sorted(grouped):
        rows = grouped[key]
        signals: list[str] = []
        candidate_keys: list[str] = []
        source_ids = list(dict.fromkeys(r["SourceID"] for r in rows))
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
                    candidate_keys.append(other)
                    signals.append("format-alias")
        for mk in morphology_keys(key):
            if mk in all_keys:
                candidate_keys.append(mk)
                signals.append("morphology")
        # Reverse morphology relation.
        for other in all_keys:
            if key in morphology_keys(other):
                candidate_keys.append(other)
                signals.append("morphology")

        surfaces.append({
            "MatchKey": key,
            "DisplayForms": unique_join([r["Word"] for r in rows]),
            "Definitions": unique_join([r["Definition"] for r in rows]),
            "SourceIDs": "|".join(source_ids),
            "SourceBooks": unique_join([f"{r['SourceID']}:{r['SourceBook']}" for r in rows]),
            "OccurrenceCount": str(len(rows)),
            "CandidateSignals": unique_join(signals),
            "CandidateMatchKeys": unique_join(candidate_keys),
        })
    return surfaces


def main() -> None:
    occurrences = build_occurrences()
    surfaces = build_surfaces(occurrences)
    surface_by_key = {r["MatchKey"]: r for r in surfaces}

    if not DECISIONS.exists():
        decisions = bootstrap_decisions(surfaces)
        write_csv(DECISIONS, DECISION_FIELDS, decisions)
        print("identity_decisions bootstrap = created-from-reviewed-legacy-state")
    else:
        decisions = read_csv(DECISIONS)
        print("identity_decisions bootstrap = skipped-existing-durable-review-truth")

    decision_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    decision_keys: set[str] = set()
    for row in decisions:
        dkey = row.get("DecisionKey", "")
        key = row.get("MatchKey", "")
        if not dkey or dkey in decision_keys:
            raise SystemExit(f"Duplicate/empty DecisionKey: {dkey}")
        if key not in surface_by_key:
            raise SystemExit(f"Decision references missing current surface: {key}")
        if row.get("Action") not in ACTIONS:
            raise SystemExit(f"Invalid Action for {dkey}: {row.get('Action')}")
        decision_keys.add(dkey)
        decision_groups[key].append(row)

    # New source surfaces automatically become pending without mutating durable
    # decision truth. Reviewers later append/update identity_decisions.csv.
    candidate_rows: list[dict[str, str]] = []
    review_rows: list[dict[str, str]] = []
    for surface in surfaces:
        key = surface["MatchKey"]
        ds = decision_groups.get(key, [])
        if len(ds) == 1 and ds[0].get("OccurrenceKeys", "") == "*":
            d = ds[0]
            action = d["Action"]
            status = d["Status"]
            canonical = d.get("CanonicalMatchKey", "")
            sense = d.get("TargetSense", "")
        elif not ds:
            action, status, canonical, sense = "pending", "pending", "", ""
        else:
            # Explicit split parts are supported as durable decisions, but the
            # surface-level view remains split/multipart.
            action = "multipart-reviewed" if all(d.get("Status") == "reviewed" for d in ds) else "split-required"
            status = "reviewed" if action == "multipart-reviewed" else "held"
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

    # Build provisional identity groups. No ThirdPartyID is minted here.
    identity_groups: dict[str, dict[str, object]] = {}
    for surface in candidate_rows:
        key = surface["MatchKey"]
        ds = decision_groups.get(key, [])
        if len(ds) != 1 or ds[0].get("OccurrenceKeys", "") != "*":
            continue
        d = ds[0]
        action = d["Action"]
        if action not in {"keep-identity", "reuse-identity"} or d.get("Status") != "reviewed":
            continue
        canonical = d.get("CanonicalMatchKey", "") if action == "reuse-identity" else key
        canonical = canonical or key
        group = identity_groups.setdefault(canonical, {
            "matchkeys": [], "occ": 0, "display": "", "sense": "", "status": "reviewed",
        })
        group["matchkeys"].append(key)
        group["occ"] = int(group["occ"]) + int(surface["OccurrenceCount"])
        if not group["display"]:
            group["display"] = canonical if action == "reuse-identity" and canonical != key else surface["DisplayForms"].split("|")[0]
        if d.get("TargetSense") and not group["sense"]:
            group["sense"] = d["TargetSense"]

    preview_rows: list[dict[str, str]] = []
    for canonical in sorted(identity_groups):
        group = identity_groups[canonical]
        preview_rows.append({
            "ProvisionalIdentityKey": f"candidate:{canonical}",
            "CanonicalMatchKey": canonical,
            "DisplayWord": str(group["display"]),
            "TargetSense": str(group["sense"]),
            "SourceMatchKeys": unique_join(list(group["matchkeys"])),
            "SourceOccurrenceCount": str(group["occ"]),
            "DecisionStatus": "reviewed",
        })

    write_csv(OUT / "occurrences.csv", OCC_FIELDS, occurrences)
    write_csv(OUT / "surface_candidates.csv", SURFACE_FIELDS, candidate_rows)
    write_csv(OUT / "review_queue.csv", SURFACE_FIELDS, review_rows)
    write_csv(OUT / "unified_vocabulary_preview.csv", PREVIEW_FIELDS, preview_rows)

    action_counts = Counter(r["DecisionAction"] for r in candidate_rows)
    readme = f"""# Third-party Vocabulary — Simplified Stage A

Active pipeline:

```text
standardized source occurrences
+ review/identity_decisions.csv
→ tools/build_third_party_corpus.py
→ surface_candidates.csv
→ review_queue.csv
→ unified_vocabulary_preview.csv
→ tools/check_third_party_corpus.py
```

Current facts:

```text
Source occurrences       = {len(occurrences)}
Normalized surfaces      = {len(surfaces)}
Reviewed identity preview = {len(preview_rows)}
Review/blocker surfaces  = {len(review_rows)}
```

Candidate signals (exact / morphology / format / multiword / punctuation) are
only evidence. They do not create extra processing stages and never equal
Identity truth.

`identity_decisions.csv` is the single durable content-decision truth for this
third-party corpus. Legacy audit/resolution CSVs remain only as migration/audit
history and are no longer part of the active long-term pipeline.

Stable ThirdPartyID is not minted yet. Final Klose diff is not executed in Stage A.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    print(f"Third-party source occurrences = {len(occurrences)}")
    print(f"Third-party surfaces = {len(surfaces)}")
    print(f"Unified vocabulary preview = {len(preview_rows)}")
    print(f"Review/blocker surfaces = {len(review_rows)}")
    for action in sorted(action_counts):
        print(f"action {action} = {action_counts[action]}")
    print("Stable ThirdPartyID minted = no")
    print("Final Klose diff executed = no")


if __name__ == "__main__":
    main()
