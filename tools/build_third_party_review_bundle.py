#!/usr/bin/env python3
"""Build an evidence-rich, high-throughput review bundle for Stage-A blockers.

`identity_decisions.csv` remains the only content-decision truth. This generated
bundle adds triage class, actionability, execution lane, canonical evidence and
source neighborhoods so model review can focus on the most actionable blockers
without repeated repository lookups.
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "anki" / "klose" / "third_party_vocabulary"
STAGING = TP / "staging"
DECISIONS = TP / "review" / "identity_decisions.csv"
OCCURRENCES = STAGING / "occurrences.csv"
REVIEW_QUEUE = STAGING / "review_queue.csv"
OUT = TP / "audit" / "review_bundle.csv"

FIELDS = [
    "AuditPriority",
    "ActionabilityScore",
    "ReviewLane",
    "RecommendedBatchSize",
    "BlockerClass",
    "MatchKey",
    "DisplayForms",
    "Definitions",
    "SourceIDs",
    "SourceBooks",
    "OccurrenceCount",
    "CandidateSignals",
    "CandidateCanonical",
    "CanonicalExists",
    "CanonicalAction",
    "CanonicalStatus",
    "CanonicalTargetSense",
    "CanonicalDefinitions",
    "CanonicalOccurrenceCount",
    "PolicyRecommendedAction",
    "DeferReason",
    "CurrentAction",
    "CurrentStatus",
    "CurrentConfidence",
    "CurrentDecisionBasis",
    "CurrentRationale",
    "OccurrenceEvidenceJSON",
]

FUNCTIONAL_POLYSEMY = {
    "a", "about", "after", "all", "as", "at", "back", "before", "by", "can",
    "could", "do", "for", "from", "have", "in", "like", "may", "of", "on",
    "one", "out", "over", "right", "so", "some", "that", "the", "to", "up",
    "with", "would",
}

ABBREVIATION_KEYS = {
    "a.m.", "am", "cd", "p.m.", "pm", "ps", "rsvp", "u.k.", "u.s.a.",
}

PEDAGOGICAL_FORM_EXCEPTIONS = {"women"}

IRREGULAR_BASE = {
    "ate": "eat", "became": "become", "bought": "buy", "broke": "break",
    "broken": "break", "brought": "bring", "came": "come", "did": "do",
    "drank": "drink", "drove": "drive", "fell": "fall", "felt": "feel",
    "flew": "fly", "gave": "give", "got": "get", "had": "have",
    "heard": "hear", "knew": "know", "learnt": "learn", "left": "leave",
    "lost": "lose", "made": "make", "met": "meet", "ran": "run",
    "rode": "ride", "said": "say", "saw": "see", "sent": "send",
    "slept": "sleep", "spoke": "speak", "spent": "spend", "stood": "stand",
    "swam": "swim", "told": "tell", "took": "take", "went": "go",
    "won": "win", "wore": "wear", "wrote": "write",
}

CONTRACTION_BASE = {
    "can't": "cannot", "couldn't": "could not", "don't": "do not",
    "isn't": "is not", "they're": "they are", "wasn't": "was not",
    "weren't": "were not", "won't": "will not", "wouldn't": "would not",
    "you'll": "you will", "you're": "you are",
}

POS_RE = re.compile(r"(?:^|[\s;,/])(?:n|v|vt|vi|adj|adv|prep|pron|conj|aux)\.", re.I)
LOW_EVIDENCE_MARKERS = (
    "insufficient", "does not bind", "cannot safely", "do not safely", "ambig",
    "multiple", "several", "polysem", "boundary", "without source context",
    "source fact alone", "word-list evidence", "isolated glossary",
)
RECONCILIATION_MARKERS = (
    "reconciliation", "dictionary gloss", "bad dictionary", "source conflict",
    "gloss gives", "gloss conflicts",
)
ACTIVITY_ANCHORS = {
    "activity", "activities", "hobby", "sport", "sports", "game", "games",
    "running", "reading", "singing", "dancing", "cycling", "hiking",
    "skateboarding", "swimming", "boating",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def decision_summary(rows: list[dict[str, str]]) -> tuple[str, str, str, str]:
    if not rows:
        return "", "", "", ""
    if len(rows) == 1:
        row = rows[0]
        return (
            row.get("Action", ""), row.get("Status", ""),
            row.get("TargetSense", ""), row.get("CanonicalMatchKey", ""),
        )
    reviewed = all(r.get("Status") == "reviewed" for r in rows)
    return "multipart-reviewed" if reviewed else "split-required", "reviewed" if reviewed else "held", "", ""


def candidate_bases(key: str, explicit_candidates: list[str], all_keys: set[str]) -> list[str]:
    candidates: list[str] = []
    candidates.extend(explicit_candidates)
    if key in IRREGULAR_BASE:
        candidates.append(IRREGULAR_BASE[key])
    if key in CONTRACTION_BASE:
        candidates.append(CONTRACTION_BASE[key])

    if " " not in key and key not in PEDAGOGICAL_FORM_EXCEPTIONS:
        if key.endswith("ied") and len(key) > 4:
            candidates.append(key[:-3] + "y")
        if key.endswith("ed") and len(key) > 3:
            candidates.extend([key[:-2], key[:-1]])
            if len(key) > 4 and key[-3] == key[-4]:
                candidates.append(key[:-3])
        if key.endswith("ing") and len(key) > 4:
            stem = key[:-3]
            candidates.extend([stem, stem + "e"])
            if len(stem) > 2 and stem[-1] == stem[-2]:
                candidates.append(stem[:-1])

    return list(dict.fromkeys(c for c in candidates if c in all_keys and c != key))


def evidence_words(evidence: list[dict[str, object]]) -> set[str]:
    words: set[str] = set()
    for item in evidence:
        for field in ("Before", "After"):
            for value in item.get(field, []):
                words.add(str(value).casefold())
    return words


def classify(
    blocker: dict[str, str],
    decision_text: str,
    candidate_canonical: str,
    canonical_action: str,
    canonical_status: str,
) -> tuple[int, str]:
    key = blocker["MatchKey"].strip().casefold()
    action = blocker.get("DecisionAction", "")
    signals = {x for x in blocker.get("CandidateSignals", "").split("|") if x}
    definitions = blocker.get("Definitions", "").casefold()
    text = decision_text.casefold()

    if action == "split-required":
        return 30, "split-resolution"

    abbreviation = (
        key in ABBREVIATION_KEYS
        or "abbr." in definitions
        or "abbreviation" in text
        or "abbrev" in text
    )
    if abbreviation:
        return 70, "abbreviation-policy"

    form_markers = (
        "morphology" in signals
        or key in IRREGULAR_BASE
        or key in CONTRACTION_BASE
        or any(token in text for token in (
            "irregular-form", "form-policy", "inflected form", "past form",
            "past tense", "past participle", "plural-form", "contraction",
            "contracted grammatical form", "gerund-form", "form boundary",
        ))
    )
    if form_markers:
        return 60, "form-policy"

    if key in FUNCTIONAL_POLYSEMY:
        return 80, "functional-polysemy"

    if "multiword" in signals:
        return 45, "multiword-object-boundary"

    source_ids = [x for x in blocker.get("SourceIDs", "").split("|") if x]
    occ_count = int(blocker.get("OccurrenceCount", "0") or 0)
    if len(source_ids) == 1 and occ_count == 1:
        return 10, "semantic-easy"
    if len(source_ids) > 1:
        return 20, "semantic-cross-source"
    if candidate_canonical and canonical_action == "keep-identity" and canonical_status == "reviewed":
        return 20, "semantic-cross-source"
    return 40, "semantic-hard"


def score_actionability(
    blocker: dict[str, str],
    blocker_class: str,
    decision_text: str,
    evidence: list[dict[str, object]],
    candidate_canonical: str,
    canonical_action: str,
    canonical_status: str,
) -> int:
    score = 50
    key = blocker["MatchKey"].casefold()
    definitions = blocker.get("Definitions", "")
    text = decision_text.casefold()
    source_ids = [x for x in blocker.get("SourceIDs", "").split("|") if x]
    occ_count = int(blocker.get("OccurrenceCount", "0") or 0)
    pos_count = len(set(m.group(0).strip().casefold() for m in POS_RE.finditer(definitions)))

    if len(source_ids) == 1 and occ_count == 1:
        score += 10
    if len(source_ids) > 1:
        score += 5
    if pos_count <= 1:
        score += 10
    elif pos_count >= 2:
        score -= 20
    if any(marker in text for marker in LOW_EVIDENCE_MARKERS):
        score -= 20
    if any(marker in text for marker in RECONCILIATION_MARKERS):
        score -= 20
    if blocker_class == "functional-polysemy":
        score -= 30
    if blocker_class == "split-resolution":
        score += 5
    if blocker_class == "semantic-hard":
        score -= 10
    if blocker_class == "multiword-object-boundary":
        score -= 10
    if blocker_class == "abbreviation-policy":
        score -= 10

    canonical_ready = candidate_canonical and canonical_action == "keep-identity" and canonical_status == "reviewed"
    if blocker_class == "form-policy":
        score += 25 if canonical_ready else -15
        if key.endswith("ing") and evidence_words(evidence) & ACTIVITY_ANCHORS:
            score -= 10

    return max(0, min(100, score))


def lane_for(
    key: str,
    blocker_class: str,
    score: int,
    decision_text: str,
    candidate_canonical: str,
    canonical_action: str,
    canonical_status: str,
    evidence: list[dict[str, object]],
) -> tuple[str, int, str, str]:
    text = decision_text.casefold()
    canonical_ready = candidate_canonical and canonical_action == "keep-identity" and canonical_status == "reviewed"

    if any(marker in text for marker in RECONCILIATION_MARKERS):
        return "source-reconciliation-needed", 15, "source-reconciliation", "source/gloss conflict"
    if blocker_class == "split-resolution":
        return "split-resolution", 25, "resolve-occurrence-split", ""
    if blocker_class == "form-policy":
        if key in PEDAGOGICAL_FORM_EXCEPTIONS:
            return "policy-review", 30, "preserve-pedagogical-exception", "explicit form exception"
        if key.endswith("ing") and evidence_words(evidence) & ACTIVITY_ANCHORS:
            return "policy-review", 30, "review-lexicalized-activity", "activity-noun boundary needs evidence confirmation"
        if canonical_ready:
            return "policy-executable", 80, "reuse-identity", ""
        return "policy-review", 30, "hold-canonical-unresolved", "canonical not reviewed keep-identity"
    if blocker_class == "abbreviation-policy":
        return "policy-review", 30, "manual-abbreviation-review", "abbreviation expansion/object boundary needs confirmation"
    if blocker_class == "multiword-object-boundary":
        return "object-boundary", 25, "review-object-boundary", ""
    if blocker_class == "functional-polysemy":
        return "deferred-high-ambiguity", 0, "defer", "functional/polysemy evidence cost is high"
    if score >= 65:
        return "actionable-semantic", 50, "review-semantic-release", ""
    if score >= 45:
        return "semantic-review", 30, "review-semantic", ""
    return "deferred-high-ambiguity", 0, "defer", "low actionability without stronger source evidence"


def main() -> None:
    occurrences = read_csv(OCCURRENCES)
    review = read_csv(REVIEW_QUEUE)
    decisions = read_csv(DECISIONS)

    decisions_by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decisions:
        decisions_by_match[row["MatchKey"]].append(row)
    all_keys = set(decisions_by_match)

    book_rows: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in occurrences:
        book_rows[(row["SourceID"], row["SourceBook"])].append(row)

    position: dict[str, tuple[list[dict[str, str]], int]] = {}
    for rows in book_rows.values():
        for index, row in enumerate(rows):
            position[row["SourceOccurrenceKey"]] = (rows, index)

    occurrences_by_match: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in occurrences:
        occurrences_by_match[row["MatchKey"]].append(row)

    review_keys = [row["MatchKey"] for row in review]
    if len(review_keys) != len(set(review_keys)):
        raise SystemExit("Review Bundle: duplicate MatchKey in review_queue.csv")

    bundle: list[dict[str, str]] = []
    for blocker in review:
        key = blocker["MatchKey"]
        current_decisions = decisions_by_match.get(key, [])
        basis = " || ".join(dict.fromkeys(d.get("DecisionBasis", "") for d in current_decisions if d.get("DecisionBasis")))
        rationale = " || ".join(dict.fromkeys(d.get("Rationale", "") for d in current_decisions if d.get("Rationale")))
        confidence = "|".join(dict.fromkeys(d.get("Confidence", "") for d in current_decisions if d.get("Confidence")))
        decision_text = " ".join([basis, rationale])

        evidence: list[dict[str, object]] = []
        for occurrence in occurrences_by_match.get(key, []):
            rows, index = position[occurrence["SourceOccurrenceKey"]]
            before = [r["Word"] for r in rows[max(0, index - 8):index]]
            after = [r["Word"] for r in rows[index + 1:index + 9]]
            evidence.append({
                "SourceOccurrenceKey": occurrence["SourceOccurrenceKey"],
                "SourceID": occurrence["SourceID"],
                "SourceBook": occurrence["SourceBook"],
                "Grade": occurrence.get("Grade", ""),
                "Semester": occurrence.get("Semester", ""),
                "SourceRow": occurrence.get("SourceRow", ""),
                "Word": occurrence.get("Word", ""),
                "Definition": occurrence.get("Definition", ""),
                "Before": before,
                "After": after,
            })

        explicit_candidates = [x for x in blocker.get("CandidateMatchKeys", "").split("|") if x]
        bases = candidate_bases(key.casefold(), explicit_candidates, all_keys)
        candidate_canonical = bases[0] if len(bases) == 1 else ""
        canonical_rows = decisions_by_match.get(candidate_canonical, []) if candidate_canonical else []
        canonical_action, canonical_status, canonical_sense, _ = decision_summary(canonical_rows)
        canonical_defs = "|".join(dict.fromkeys(
            occurrence.get("Definition", "")
            for occurrence in occurrences_by_match.get(candidate_canonical, [])
            if occurrence.get("Definition", "")
        )) if candidate_canonical else ""
        canonical_occ_count = len(occurrences_by_match.get(candidate_canonical, [])) if candidate_canonical else 0

        priority, blocker_class = classify(
            blocker, decision_text, candidate_canonical, canonical_action, canonical_status
        )
        score = score_actionability(
            blocker, blocker_class, decision_text, evidence,
            candidate_canonical, canonical_action, canonical_status,
        )
        lane, batch_size, recommended_action, defer_reason = lane_for(
            key.casefold(), blocker_class, score, decision_text,
            candidate_canonical, canonical_action, canonical_status, evidence,
        )

        bundle.append({
            "AuditPriority": f"{priority:02d}",
            "ActionabilityScore": str(score),
            "ReviewLane": lane,
            "RecommendedBatchSize": str(batch_size),
            "BlockerClass": blocker_class,
            "MatchKey": key,
            "DisplayForms": blocker.get("DisplayForms", ""),
            "Definitions": blocker.get("Definitions", ""),
            "SourceIDs": blocker.get("SourceIDs", ""),
            "SourceBooks": blocker.get("SourceBooks", ""),
            "OccurrenceCount": blocker.get("OccurrenceCount", ""),
            "CandidateSignals": blocker.get("CandidateSignals", ""),
            "CandidateCanonical": candidate_canonical,
            "CanonicalExists": "yes" if candidate_canonical else "no",
            "CanonicalAction": canonical_action,
            "CanonicalStatus": canonical_status,
            "CanonicalTargetSense": canonical_sense,
            "CanonicalDefinitions": canonical_defs,
            "CanonicalOccurrenceCount": str(canonical_occ_count) if candidate_canonical else "",
            "PolicyRecommendedAction": recommended_action,
            "DeferReason": defer_reason,
            "CurrentAction": blocker.get("DecisionAction", ""),
            "CurrentStatus": blocker.get("DecisionStatus", ""),
            "CurrentConfidence": confidence,
            "CurrentDecisionBasis": basis,
            "CurrentRationale": rationale,
            "OccurrenceEvidenceJSON": json.dumps(evidence, ensure_ascii=False, separators=(",", ":")),
        })

    bundle.sort(key=lambda row: (
        1 if row["ReviewLane"] == "deferred-high-ambiguity" else 0,
        -int(row["ActionabilityScore"]),
        int(row["AuditPriority"]),
        row["MatchKey"],
    ))
    write_csv(OUT, bundle)

    if {row["MatchKey"] for row in bundle} != set(review_keys):
        raise SystemExit("Review Bundle closure mismatch with review_queue.csv")

    class_counts: dict[str, int] = defaultdict(int)
    lane_counts: dict[str, int] = defaultdict(int)
    score_bands: dict[str, int] = defaultdict(int)
    for row in bundle:
        class_counts[row["BlockerClass"]] += 1
        lane_counts[row["ReviewLane"]] += 1
        score = int(row["ActionabilityScore"])
        band = "80-100" if score >= 80 else "65-79" if score >= 65 else "45-64" if score >= 45 else "0-44"
        score_bands[band] += 1

    print(f"review bundle blockers = {len(bundle)}")
    for name in sorted(class_counts):
        print(f"review bundle class {name} = {class_counts[name]}")
    for name in sorted(lane_counts):
        print(f"review bundle lane {name} = {lane_counts[name]}")
    for name in ("80-100", "65-79", "45-64", "0-44"):
        print(f"review bundle actionability {name} = {score_bands[name]}")
    print("review bundle neighborhood radius = 8")
    print("review bundle canonical evidence = yes")
    print("review bundle closure = pass")
    print("review bundle decision truth = derived-only")


if __name__ == "__main__":
    main()
