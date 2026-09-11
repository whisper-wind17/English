#!/usr/bin/env python3
"""Materialize the accepted Grade 5-6 Expression learning scope.

This is the downstream boundary after the closed reconciliation lane. It preserves
all existing KE/EO identities, allocates stable IDs only for the 110 reviewed
`new::` groups, keeps the 8 reviewed KE reuses, preserves all 15 source-only
occurrences without cards, and builds LearnerLevel-4 model-reviewed presentations.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from klose_expression_review_fingerprint import VERSION, fingerprint

ROOT = Path(__file__).resolve().parents[1]
KLOSE = ROOT / "anki" / "klose"
BASE = KLOSE / "expressions"
MASTER = BASE / "master"
LEARNER = BASE / "learner"
RECON = KLOSE / "review" / "grade5_6_reconciliation"
SRC = KLOSE / "source_reference"

SCOPE = LEARNER / "grade5_6_learning_scope.json"
GROUPS = RECON / "expression_identity_groups.csv"
DECISIONS = RECON / "expression_source_decisions.csv"
SOURCES = [
    SRC / "klose-actual-grade5-upper-expressions.csv",
    SRC / "klose-actual-grade5-lower-expressions.csv",
    SRC / "klose-actual-grade6-upper-expressions.csv",
    SRC / "klose-actual-grade6-lower-expressions.csv",
]
REGISTRY = MASTER / "expression_registry.csv"
OCCURRENCES = MASTER / "expression_occurrences.csv"
SOURCE_MAP = MASTER / "source_expression_map.csv"
RELEASE = MASTER / "release_registry.csv"
CURRENT = LEARNER / "current.csv"
ADMISSION = LEARNER / "learning_admission.csv"
REVIEWS = LEARNER / "presentation_review_registry.csv"
ALLOCATION = MASTER / "grade5_6_identity_allocation.csv"
PROVENANCE = MASTER / "grade5_6_source_occurrence_provenance.csv"

GROUP_FIELDS = [
    "IdentityGroup", "ExpressionID", "CanonicalForm", "FunctionKey", "ExpressionType",
    "SlotSchema", "AllocatedFromOccurrence", "AllocationBasis", "Status",
]
PROVENANCE_FIELDS = [
    "SourceOccurrenceKey", "OccurrenceID", "CandidateFingerprint", "SourceID", "SourceEdition",
    "EvidenceFileID", "Grade", "Semester", "Unit", "Order", "Page", "ProvenanceStatus",
]
REGISTRY_FIELDS = [
    "ExpressionID", "CanonicalForm", "FunctionKey", "ExpressionType", "SlotSchema",
    "Status", "CreatedFromCandidate", "CreatedFromOccurrence",
]
OCCURRENCE_FIELDS = [
    "OccurrenceID", "SourceID", "SourceGrade", "Semester", "Unit", "Order",
    "RawExpression", "RawTranslation", "SourceStatus",
]
MAP_FIELDS = ["OccurrenceID", "ExpressionID", "MappingStatus", "Notes"]
CURRENT_FIELDS = [
    "LearnerProfile", "LearnerLevel", "ExpressionID", "FunctionLabel", "Prompt", "PromptHint",
    "Target", "Pattern", "MeaningUsage", "Examples", "ContextNote",
]
ADMISSION_FIELDS = [
    "LearnerProfile", "LearnerLevel", "ExpressionID", "Stage", "Status", "LearningTag",
    "LearningOrder", "Reason",
]
REVIEW_FIELDS = [
    "LearnerProfile", "LearnerLevel", "ExpressionID", "FingerprintVersion", "Fingerprint",
    "ReviewStatus", "ReviewBasis", "ReviewedAt",
]
RELEASE_FIELDS = [
    "ExpressionID", "IdentityStatus", "PresentationStatus", "AdmissionStatus", "PublishStatus",
    "ReleaseStatus", "Notes",
]
FINGERPRINT_FIELDS = [
    "SourceOccurrenceKey", "Grade", "Semester", "Unit", "Order",
    "RawExpression", "Translation", "Page",
]
ID_RE = re.compile(r"^KE(\d{6})$")
OCC_RE = re.compile(r"^EO(\d{6})$")
SEM_RANK = {"上": 0, "下": 1, "upper": 0, "lower": 1}
INTENT_WORDS = (
    "询问", "追问", "表达", "说明", "描述", "建议", "提醒", "回答", "回应", "请求",
    "确认", "陈述", "转述", "安慰", "接受", "拒绝", "祝愿", "告知", "提出", "要求",
    "表示", "介绍", "比较", "解释", "劝告", "评价", "判断", "邀请", "许可", "道歉",
)
CATEGORY_BY_PREFIX = {
    "ask_": "提问", "state_": "陈述", "respond_": "回应", "answer_": "回应",
    "suggest_": "建议", "request_": "请求", "warn_": "提醒", "remind_": "提醒",
    "express_": "表达", "accept_": "接受", "decline_": "拒绝", "refuse_": "拒绝",
    "apolog": "道歉", "comfort_": "安慰", "tell_": "告知", "compare_": "比较",
    "explain_": "解释", "invite_": "邀请", "confirm_": "确认", "describe_": "描述",
}


def fail(msg: str) -> None:
    raise SystemExit(f"Grade 5-6 Expression materialization failure: {msg}")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def split_groups(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split("|") if x.strip()]


def source_key(row: dict[str, str]) -> str:
    sem = {"上": "upper", "下": "lower"}.get(row.get("Semester", "").strip())
    if not sem:
        fail(f"invalid source semester: {row.get('Semester')!r}")
    return f"grade{int(row['Grade'])}-{sem}-u{int(row['Unit']):02d}-o{int(row['Order']):03d}"


def source_fingerprint(row: dict[str, str]) -> str:
    payload = {field: row.get(field, "") for field in FINGERPRINT_FIELDS}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def coordinate(row: dict[str, str]) -> tuple[int, int, int, int]:
    sem = SEM_RANK.get(row.get("Semester", "").strip())
    if sem is None:
        fail(f"unknown semester for coordinate: {row}")
    return (int(row["Grade"]), sem, int(row["Unit"]), int(row["Order"]))


def intent_text(rationale: str) -> str:
    text = " ".join((rationale or "").strip().split())
    if not text:
        return "表达当前交际意图"
    chinese_start = re.search(r"[\u4e00-\u9fff]", text)
    if chinese_start:
        text = text[chinese_start.start():]
    best = None
    for word in INTENT_WORDS:
        pos = text.find(word)
        if pos >= 0 and (best is None or pos < best[0]):
            best = (pos, word)
    if best is not None:
        text = text[best[0]:]
    text = re.split(r"[；。]", text, maxsplit=1)[0].strip(" ，,;：:")
    text = re.sub(r"\s+", " ", text)
    if len(text) > 42:
        text = text[:42].rstrip() + "…"
    return text or "表达当前交际意图"


def category(function_key: str) -> str:
    key = (function_key or "").strip().casefold()
    for prefix, label in CATEGORY_BY_PREFIX.items():
        if key.startswith(prefix):
            return label
    return "表达"


def prompt_for(rationale: str) -> str:
    intent = intent_text(rationale)
    if intent.startswith(("询问", "追问", "表达", "说明", "描述", "建议", "提醒", "请求", "确认", "陈述", "转述", "安慰", "接受", "拒绝", "祝愿", "告知", "提出", "要求", "表示", "介绍", "比较", "解释", "劝告", "评价", "判断", "邀请", "许可", "道歉")):
        return "想" + intent
    return "想表达这个意思：" + intent


def scope_check() -> None:
    scope = json.loads(SCOPE.read_text(encoding="utf-8"))
    if scope.get("ScopeStatus") != "accepted" or scope.get("StableIdentityAllocationAuthorized") is not True:
        fail("Grade 5-6 Expression learning scope is not accepted/authorized")
    if str(scope.get("LearnerLevel")) != "4" or scope.get("LearnerProfile") != "klose":
        fail("Grade 5-6 Expression learning scope profile/level drift")
    books = scope.get("Books", {})
    if {k for k, v in books.items() if isinstance(v, dict) and v.get("Accepted") is True} != {"5上", "5下", "6上", "6下"}:
        fail("Grade 5-6 Expression learning scope does not accept all four captured books")


def main() -> None:
    scope_check()

    source_by_key: dict[str, dict[str, str]] = {}
    for path in SOURCES:
        for src in read_csv(path):
            key = source_key(src)
            if key in source_by_key:
                fail(f"duplicate source occurrence key: {key}")
            row = dict(src)
            row["SourceOccurrenceKey"] = key
            row["CandidateFingerprint"] = source_fingerprint({
                "SourceOccurrenceKey": key,
                "Grade": src.get("Grade", "").strip(),
                "Semester": src.get("Semester", "").strip(),
                "Unit": src.get("Unit", "").strip(),
                "Order": src.get("Order", "").strip(),
                "RawExpression": src.get("RawExpression", "").strip(),
                "Translation": src.get("Translation", "").strip(),
                "Page": src.get("Page", "").strip(),
            })
            source_by_key[key] = row
    if len(source_by_key) != 153:
        fail(f"expected 153 source occurrences, got {len(source_by_key)}")

    decisions = read_csv(DECISIONS)
    decision_by_key = {row.get("SourceOccurrenceKey", "").strip(): row for row in decisions}
    if len(decision_by_key) != 153 or set(decision_by_key) != set(source_by_key):
        fail("reconciliation decisions do not exactly cover 153 current source occurrences")
    dispositions: defaultdict[str, int] = defaultdict(int)
    for key, row in decision_by_key.items():
        if row.get("CandidateFingerprint", "").strip() != source_by_key[key]["CandidateFingerprint"]:
            fail(f"stale reconciliation decision: {key}")
        dispositions[row.get("Disposition", "").strip()] += 1
    if dict(dispositions) != {"mapped": 138, "source-only": 15}:
        fail(f"unexpected disposition counts: {dict(dispositions)}")

    groups = read_csv(GROUPS)
    group_by_key = {row.get("IdentityGroup", "").strip(): row for row in groups}
    if len(group_by_key) != 110 or any(not key.startswith("new::") for key in group_by_key):
        fail(f"expected 110 unique new identity groups, got {len(group_by_key)}")
    for key, row in group_by_key.items():
        if row.get("Decision", "").strip() != "new-stable-identity" or row.get("ExpressionID", "").strip():
            fail(f"reconciliation group is not an unallocated new identity proposal: {key}")

    referenced_new: set[str] = set()
    reused: set[str] = set()
    occurrence_keys_by_group: defaultdict[str, list[str]] = defaultdict(list)
    for source_key_value, row in decision_by_key.items():
        if row.get("Disposition", "").strip() != "mapped":
            if split_groups(row.get("IdentityGroups", "")):
                fail(f"source-only row unexpectedly references identity: {source_key_value}")
            continue
        for token in split_groups(row.get("IdentityGroups", "")):
            if token.startswith("new::"):
                if token not in group_by_key:
                    fail(f"source references unknown new group: {source_key_value}->{token}")
                referenced_new.add(token)
                occurrence_keys_by_group[token].append(source_key_value)
            elif ID_RE.fullmatch(token):
                reused.add(token)
            else:
                fail(f"source references invalid identity token: {source_key_value}->{token}")
    if referenced_new != set(group_by_key) or len(reused) != 8:
        fail(f"identity closure drift: new={len(referenced_new)} reused={len(reused)}")

    registry_rows = read_csv(REGISTRY)
    registry_by_id = {row.get("ExpressionID", "").strip(): row for row in registry_rows}
    if len(registry_by_id) != len(registry_rows) or any(not ID_RE.fullmatch(x) for x in registry_by_id):
        fail("invalid current Stable Expression registry")
    for eid in reused:
        if eid not in registry_by_id or registry_by_id[eid].get("Status", "").strip() != "active":
            fail(f"reused ExpressionID is not active: {eid}")

    # Stable source occurrence allocation is stored separately so reruns never renumber EO IDs.
    if PROVENANCE.exists():
        provenance_rows = read_csv(PROVENANCE)
        provenance_by_key = {row.get("SourceOccurrenceKey", "").strip(): row for row in provenance_rows}
        if len(provenance_by_key) != 153 or set(provenance_by_key) != set(source_by_key):
            fail("existing Grade 5-6 occurrence provenance does not exactly cover current source")
        for key, row in provenance_by_key.items():
            if row.get("CandidateFingerprint", "").strip() != source_by_key[key]["CandidateFingerprint"]:
                fail(f"source changed after stable EO allocation: {key}")
            if not OCC_RE.fullmatch(row.get("OccurrenceID", "").strip()):
                fail(f"invalid allocated OccurrenceID: {key}")
    else:
        existing_occ = read_csv(OCCURRENCES)
        max_occ = max(int(OCC_RE.fullmatch(r["OccurrenceID"].strip()).group(1)) for r in existing_occ)
        provenance_by_key = {}
        for offset, key in enumerate(sorted(source_by_key, key=lambda x: coordinate(source_by_key[x])), start=1):
            src = source_by_key[key]
            provenance_by_key[key] = {
                "SourceOccurrenceKey": key,
                "OccurrenceID": f"EO{max_occ + offset:06d}",
                "CandidateFingerprint": src["CandidateFingerprint"],
                "SourceID": src.get("SourceID", "").strip(),
                "SourceEdition": src.get("SourceEdition", "").strip(),
                "EvidenceFileID": src.get("EvidenceFileID", "").strip(),
                "Grade": src.get("Grade", "").strip(),
                "Semester": src.get("Semester", "").strip(),
                "Unit": src.get("Unit", "").strip(),
                "Order": src.get("Order", "").strip(),
                "Page": src.get("Page", "").strip(),
                "ProvenanceStatus": src.get("SourceStatus", "").strip(),
            }
        provenance_rows = [provenance_by_key[k] for k in sorted(provenance_by_key, key=lambda x: coordinate(source_by_key[x]))]
        write_csv(PROVENANCE, PROVENANCE_FIELDS, provenance_rows)

    for key, src in source_by_key.items():
        row = provenance_by_key[key]
        for field in ("SourceID", "SourceEdition", "EvidenceFileID", "Grade", "Unit", "Order"):
            if row.get(field, "").strip() != src.get(field, "").strip():
                fail(f"occurrence provenance drift: {key}:{field}")

    # Stable ExpressionID allocation is a durable registry. Never recompute IDs after first allocation.
    if ALLOCATION.exists():
        allocation_rows = read_csv(ALLOCATION)
        allocation_by_group = {row.get("IdentityGroup", "").strip(): row for row in allocation_rows}
        if len(allocation_by_group) != 110 or set(allocation_by_group) != set(group_by_key):
            fail("existing Grade 5-6 allocation registry does not exactly cover reviewed groups")
        for key, row in allocation_by_group.items():
            group = group_by_key[key]
            for field in ("CanonicalForm", "FunctionKey", "ExpressionType", "SlotSchema"):
                if row.get(field, "").strip() != group.get(field, "").strip():
                    fail(f"stable allocation metadata drift: {key}:{field}")
            if not ID_RE.fullmatch(row.get("ExpressionID", "").strip()) or row.get("Status", "").strip() != "active":
                fail(f"invalid stable allocation row: {key}")
    else:
        if any(row.get("CreatedFromCandidate", "").strip().startswith("new::") for row in registry_rows):
            fail("new Grade 5-6 identities exist without durable allocation registry")
        max_id = max(int(ID_RE.fullmatch(eid).group(1)) for eid in registry_by_id)
        group_order = sorted(
            group_by_key,
            key=lambda group: (
                min(coordinate(source_by_key[k]) for k in occurrence_keys_by_group[group]),
                group,
            ),
        )
        allocation_by_group = {}
        allocation_rows = []
        for offset, group_key in enumerate(group_order, start=1):
            group = group_by_key[group_key]
            first_source_key = min(occurrence_keys_by_group[group_key], key=lambda k: coordinate(source_by_key[k]))
            row = {
                "IdentityGroup": group_key,
                "ExpressionID": f"KE{max_id + offset:06d}",
                "CanonicalForm": group.get("CanonicalForm", "").strip(),
                "FunctionKey": group.get("FunctionKey", "").strip(),
                "ExpressionType": group.get("ExpressionType", "").strip(),
                "SlotSchema": group.get("SlotSchema", "").strip(),
                "AllocatedFromOccurrence": provenance_by_key[first_source_key]["OccurrenceID"],
                "AllocationBasis": "closed-grade5-6-reconciliation+explicit-user-learning-scope",
                "Status": "active",
            }
            allocation_rows.append(row)
            allocation_by_group[group_key] = row
        write_csv(ALLOCATION, GROUP_FIELDS, allocation_rows)

    allocated_ids = {row["ExpressionID"] for row in allocation_by_group.values()}
    if len(allocated_ids) != 110 or allocated_ids & (set(registry_by_id) - allocated_ids):
        fail("allocated ExpressionID set is duplicate/colliding")

    new_occurrence_ids = {row["OccurrenceID"] for row in provenance_by_key.values()}
    baseline_occurrences = [r for r in read_csv(OCCURRENCES) if r.get("OccurrenceID", "").strip() not in new_occurrence_ids]
    generated_occurrences: list[dict[str, str]] = []
    for key in sorted(source_by_key, key=lambda x: coordinate(source_by_key[x])):
        src = source_by_key[key]
        generated_occurrences.append({
            "OccurrenceID": provenance_by_key[key]["OccurrenceID"],
            "SourceID": src.get("SourceID", "").strip(),
            "SourceGrade": src.get("Grade", "").strip(),
            "Semester": "upper" if src.get("Semester", "").strip() == "上" else "lower",
            "Unit": src.get("Unit", "").strip(),
            "Order": src.get("Order", "").strip(),
            "RawExpression": src.get("RawExpression", "").strip(),
            "RawTranslation": src.get("Translation", "").strip(),
            "SourceStatus": src.get("SourceStatus", "").strip(),
        })
    write_csv(OCCURRENCES, OCCURRENCE_FIELDS, baseline_occurrences + generated_occurrences)

    baseline_maps = [r for r in read_csv(SOURCE_MAP) if r.get("OccurrenceID", "").strip() not in new_occurrence_ids]
    generated_maps: list[dict[str, str]] = []
    examples_by_group: defaultdict[str, list[str]] = defaultdict(list)
    for key in sorted(source_by_key, key=lambda x: coordinate(source_by_key[x])):
        decision = decision_by_key[key]
        if decision.get("Disposition", "").strip() != "mapped":
            continue
        oid = provenance_by_key[key]["OccurrenceID"]
        raw = source_by_key[key].get("RawExpression", "").strip()
        for token in split_groups(decision.get("IdentityGroups", "")):
            eid = allocation_by_group[token]["ExpressionID"] if token.startswith("new::") else token
            generated_maps.append({
                "OccurrenceID": oid,
                "ExpressionID": eid,
                "MappingStatus": "confirmed",
                "Notes": "Grade 5-6 closed reconciliation: " + decision.get("Rationale", "").strip(),
            })
            if token.startswith("new::") and raw and raw not in examples_by_group[token]:
                examples_by_group[token].append(raw)
    generated_maps.sort(key=lambda r: (int(OCC_RE.fullmatch(r["OccurrenceID"]).group(1)), r["ExpressionID"]))
    write_csv(SOURCE_MAP, MAP_FIELDS, baseline_maps + generated_maps)

    baseline_registry = [r for r in read_csv(REGISTRY) if r.get("ExpressionID", "").strip() not in allocated_ids]
    generated_registry: list[dict[str, str]] = []
    for group_key, alloc in sorted(allocation_by_group.items(), key=lambda item: item[1]["ExpressionID"]):
        generated_registry.append({
            "ExpressionID": alloc["ExpressionID"],
            "CanonicalForm": alloc["CanonicalForm"],
            "FunctionKey": alloc["FunctionKey"],
            "ExpressionType": alloc["ExpressionType"],
            "SlotSchema": alloc["SlotSchema"],
            "Status": "active",
            "CreatedFromCandidate": group_key,
            "CreatedFromOccurrence": alloc["AllocatedFromOccurrence"],
        })
    write_csv(REGISTRY, REGISTRY_FIELDS, baseline_registry + generated_registry)

    # Preserve all existing learner/release state. New Grade 5-6 material is appended after the 66-card baseline.
    baseline_admission = [r for r in read_csv(ADMISSION) if r.get("ExpressionID", "").strip() not in allocated_ids]
    max_order = max(int(r.get("LearningOrder", "0") or 0) for r in baseline_admission if r.get("Status", "").strip() == "allowed")

    generated_current: list[dict[str, str]] = []
    generated_admission: list[dict[str, str]] = []
    generated_reviews: list[dict[str, str]] = []
    generated_release: list[dict[str, str]] = []
    for index, (group_key, alloc) in enumerate(
        sorted(allocation_by_group.items(), key=lambda item: item[1]["ExpressionID"]), start=1
    ):
        group = group_by_key[group_key]
        rationale = group.get("Rationale", "").strip()
        slots = group.get("SlotSchema", "").strip()
        examples = examples_by_group[group_key][:2]
        if not examples:
            fail(f"allocated group has no concrete textbook example: {group_key}")
        cur = {
            "LearnerProfile": "klose",
            "LearnerLevel": "4",
            "ExpressionID": alloc["ExpressionID"],
            "FunctionLabel": category(group.get("FunctionKey", "")),
            "Prompt": prompt_for(rationale),
            "PromptHint": ("slots: " + slots.replace("|", " · ")) if slots else "",
            "Target": group.get("CanonicalForm", "").strip(),
            "Pattern": group.get("CanonicalForm", "").strip(),
            "MeaningUsage": rationale,
            "Examples": " | ".join(examples),
            "ContextNote": "Grade 5-6 current scope; Stage A intent prompt; canonical pattern is the retrieval target.",
        }
        if not all(cur[field] for field in ("FunctionLabel", "Prompt", "Target", "Pattern", "MeaningUsage", "Examples")):
            fail(f"incomplete generated learner presentation: {group_key}")
        generated_current.append(cur)
        generated_admission.append({
            "LearnerProfile": "klose",
            "LearnerLevel": "4",
            "ExpressionID": alloc["ExpressionID"],
            "Stage": "stage::grade5-6-expression",
            "Status": "allowed",
            "LearningTag": "expression::grade5-6",
            "LearningOrder": f"{max_order + index:06d}",
            "Reason": "explicit-user-current-learning-scope;grade5-6-after-existing-expression-baseline",
        })
        generated_reviews.append({
            "LearnerProfile": "klose",
            "LearnerLevel": "4",
            "ExpressionID": alloc["ExpressionID"],
            "FingerprintVersion": VERSION,
            "Fingerprint": fingerprint(cur),
            "ReviewStatus": "model-reviewed",
            "ReviewBasis": "model-reviewed-grade5-6-current-learning-scope-v1",
            "ReviewedAt": "2026-09-11",
        })
        generated_release.append({
            "ExpressionID": alloc["ExpressionID"],
            "IdentityStatus": "active",
            "PresentationStatus": "model-reviewed",
            "AdmissionStatus": "allowed",
            "PublishStatus": "generated",
            "ReleaseStatus": "ready",
            "Notes": "Grade 5-6 current scope; model-reviewed learner presentation; append after existing Expression baseline",
        })

    baseline_current = [r for r in read_csv(CURRENT) if r.get("ExpressionID", "").strip() not in allocated_ids]
    baseline_reviews = [r for r in read_csv(REVIEWS) if r.get("ExpressionID", "").strip() not in allocated_ids]
    baseline_release = [r for r in read_csv(RELEASE) if r.get("ExpressionID", "").strip() not in allocated_ids]
    write_csv(CURRENT, CURRENT_FIELDS, baseline_current + generated_current)
    write_csv(ADMISSION, ADMISSION_FIELDS, baseline_admission + generated_admission)
    write_csv(REVIEWS, REVIEW_FIELDS, baseline_reviews + generated_reviews)
    write_csv(RELEASE, RELEASE_FIELDS, baseline_release + generated_release)

    print(
        "Materialized Grade 5-6 Expressions: "
        f"source=153 mapped=138 source_only=15 reused={len(reused)} new={len(allocated_ids)} "
        f"registry={len(baseline_registry) + len(generated_registry)} learning_order={max_order + 1:06d}..{max_order + len(generated_admission):06d}"
    )


if __name__ == "__main__":
    main()
