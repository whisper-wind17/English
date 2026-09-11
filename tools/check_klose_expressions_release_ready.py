#!/usr/bin/env python3
"""Release gate for the Klose Expressions bounded context.

The gate independently checks baseline identity resolution, Grade 5-6 downstream
allocation, source-only isolation, current-fingerprint learner review, admission
order, deterministic publish output, and exact Anki import derivation.
"""
from __future__ import annotations

import csv
import io
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
REVIEW = BASE / "review"
PUBLISH = BASE / "publish"
RECON = KLOSE / "review" / "grade5_6_reconciliation"
SRC = KLOSE / "source_reference"

REGISTRY = MASTER / "expression_registry.csv"
OCCURRENCES = MASTER / "expression_occurrences.csv"
SOURCE_MAP = MASTER / "source_expression_map.csv"
RELEASE = MASTER / "release_registry.csv"
ALLOCATION = MASTER / "grade5_6_identity_allocation.csv"
PROVENANCE = MASTER / "grade5_6_source_occurrence_provenance.csv"
CURRENT = LEARNER / "current.csv"
ADMISSION = LEARNER / "learning_admission.csv"
REVIEWS = LEARNER / "presentation_review_registry.csv"
SCOPE = LEARNER / "grade5_6_learning_scope.json"
CANDIDATES = REVIEW / "candidate_registry.csv"
IDENTITY_RESOLUTION = REVIEW / "identity_resolution.csv"
G56_GROUPS = RECON / "expression_identity_groups.csv"
G56_DECISIONS = RECON / "expression_source_decisions.csv"
STUDY = PUBLISH / "study.csv"
ANKI_IMPORT = PUBLISH / "anki-import.csv"
SOURCE_FILES = [
    SRC / "klose-actual-grade5-upper-expressions.csv",
    SRC / "klose-actual-grade5-lower-expressions.csv",
    SRC / "klose-actual-grade6-upper-expressions.csv",
    SRC / "klose-actual-grade6-lower-expressions.csv",
]

PUBLISH_FIELDS = [
    "ExpressionID", "FunctionLabel", "Prompt", "PromptHint", "Target", "Pattern",
    "MeaningUsage", "Examples", "LearnerLevel", "LearningOrder", "Sources", "SourceBooks",
]
NOTE_TYPE = "Klose Expression"
DECK = "Klose-English::Expressions"
ID_RE = re.compile(r"^KE\d{6}$")
OCC_RE = re.compile(r"^EO\d{6}$")
ORDER_RE = re.compile(r"^\d{6}$")
PUBLISHABLE_REVIEW_STATUSES = {"approved", "model-reviewed"}
STAGE_TAG = {
    "stage::grade4-expression": "expression::grade4",
    "stage::grade3-expression": "expression::grade3",
    "stage::grade5-6-expression": "expression::grade5-6",
}
STAGE_RANK = {
    "stage::grade4-expression": 0,
    "stage::grade3-expression": 1,
    "stage::grade5-6-expression": 2,
}


def fail(msg: str) -> None:
    raise SystemExit(f"Release blocked: {msg}")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def keyed(rows: list[dict[str, str]], field: str, label: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row.get(field, "").strip()
        if not key or key in result:
            fail(f"invalid/duplicate {label}: {key!r}")
        result[key] = row
    return result


def split_groups(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split("|") if x.strip()]


def source_occurrence_key(row: dict[str, str]) -> str:
    sem = {"上": "upper", "下": "lower"}.get(row.get("Semester", "").strip())
    if not sem:
        fail(f"invalid Grade 5-6 source semester: {row.get('Semester')!r}")
    return f"grade{int(row['Grade'])}-{sem}-u{int(row['Unit']):02d}-o{int(row['Order']):03d}"


def read_anki_import(path: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    if path.read_bytes().startswith(b"\xef\xbb\xbf"):
        fail("anki-import.csv must be UTF-8 without BOM")
    headers: dict[str, str] = {}
    data: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            if line.startswith("#"):
                if ":" not in line:
                    fail(f"malformed Anki header: {line}")
                key, value = line[1:].split(":", 1)
                headers[key.strip().lower()] = value.strip()
            elif line:
                data.append(raw)
    rows: list[dict[str, str]] = []
    for index, values in enumerate(csv.reader(io.StringIO("".join(data))), start=1):
        if len(values) != len(PUBLISH_FIELDS):
            fail(f"Anki row {index} has {len(values)} columns; expected {len(PUBLISH_FIELDS)}")
        rows.append(dict(zip(PUBLISH_FIELDS, values)))
    return headers, rows


def source_rows(eid: str, occurrences: dict[str, dict[str, str]], mapped: dict[str, list[str]]) -> list[dict[str, str]]:
    rows = [occurrences[oid] for oid in mapped.get(eid, [])]
    if not rows:
        fail(f"Expression has no confirmed source mapping: {eid}")
    return rows


def source_metadata(eid: str, occurrences: dict[str, dict[str, str]], mapped: dict[str, list[str]]) -> tuple[str, str]:
    rows = source_rows(eid, occurrences, mapped)
    sources = sorted({row["SourceID"].strip() for row in rows})
    books = sorted({
        f"{row['SourceID'].strip()}::grade{row['SourceGrade'].strip()}-{row['Semester'].strip()}"
        for row in rows
    })
    return "|".join(sources), "|".join(books)


def main() -> None:
    required = (
        REGISTRY, OCCURRENCES, SOURCE_MAP, RELEASE, CURRENT, ADMISSION, REVIEWS,
        CANDIDATES, IDENTITY_RESOLUTION, ALLOCATION, PROVENANCE, SCOPE,
        G56_GROUPS, G56_DECISIONS, STUDY, ANKI_IMPORT, *SOURCE_FILES,
    )
    for path in required:
        if not path.exists():
            fail(f"missing {path.relative_to(ROOT)}")

    scope = json.loads(SCOPE.read_text(encoding="utf-8"))
    if scope.get("ScopeStatus") != "accepted" or scope.get("StableIdentityAllocationAuthorized") is not True:
        fail("Grade 5-6 Expression learning scope is not accepted/authorized")
    if scope.get("LearnerProfile") != "klose" or str(scope.get("LearnerLevel")) != "4":
        fail("Grade 5-6 Expression learning scope profile/level drift")

    registry = keyed(read_csv(REGISTRY), "ExpressionID", "ExpressionID")
    release = keyed(read_csv(RELEASE), "ExpressionID", "release ExpressionID")
    current = keyed(read_csv(CURRENT), "ExpressionID", "learner ExpressionID")
    admission = keyed(read_csv(ADMISSION), "ExpressionID", "admission ExpressionID")
    reviews = keyed(read_csv(REVIEWS), "ExpressionID", "review ExpressionID")
    candidates = keyed(read_csv(CANDIDATES), "CandidateKey", "CandidateKey")
    occurrences = keyed(read_csv(OCCURRENCES), "OccurrenceID", "OccurrenceID")
    allocation = keyed(read_csv(ALLOCATION), "IdentityGroup", "Grade 5-6 IdentityGroup allocation")
    provenance = keyed(read_csv(PROVENANCE), "SourceOccurrenceKey", "Grade 5-6 source occurrence key")
    groups = keyed(read_csv(G56_GROUPS), "IdentityGroup", "Grade 5-6 identity group")

    ids = set(registry)
    if not ids or any(not ID_RE.fullmatch(eid) for eid in ids):
        fail("invalid or empty Expression Registry")
    if set(release) != ids or set(current) != ids or set(admission) != ids or set(reviews) != ids:
        fail("Registry/Release/Learner/Admission/Review identity coverage mismatch")
    if len(ids) != 176:
        fail(f"expected 176 active Expression identities after Grade 5-6 release, got {len(ids)}")

    # Baseline candidates remain resolved exactly as before.
    resolution_pairs: set[tuple[str, str]] = set()
    resolved_candidates: set[str] = set()
    for row in read_csv(IDENTITY_RESOLUTION):
        ck = row.get("CandidateKey", "").strip()
        eid = row.get("ExpressionID", "").strip()
        if ck not in candidates or eid not in registry or not row.get("Decision", "").strip():
            fail(f"invalid baseline identity resolution row: {ck}->{eid}")
        if (ck, eid) in resolution_pairs:
            fail(f"duplicate baseline identity resolution: {ck}->{eid}")
        resolution_pairs.add((ck, eid))
        resolved_candidates.add(ck)
    if resolved_candidates != set(candidates):
        fail("baseline candidate identity resolution coverage mismatch")

    if set(allocation) != set(groups) or len(allocation) != 110:
        fail(f"Grade 5-6 stable allocation coverage mismatch: allocation={len(allocation)} groups={len(groups)}")
    allocated_ids: set[str] = set()
    for group_key, alloc in allocation.items():
        group = groups[group_key]
        if group.get("Decision", "").strip() != "new-stable-identity" or group.get("ExpressionID", "").strip():
            fail(f"Grade 5-6 reconciliation group was mutated/invalid: {group_key}")
        eid = alloc.get("ExpressionID", "").strip()
        if not ID_RE.fullmatch(eid) or eid in allocated_ids or eid not in registry:
            fail(f"invalid/colliding Grade 5-6 ExpressionID allocation: {group_key}->{eid}")
        allocated_ids.add(eid)
        identity = registry[eid]
        for field in ("CanonicalForm", "FunctionKey", "ExpressionType", "SlotSchema"):
            if identity.get(field, "").strip() != group.get(field, "").strip() or alloc.get(field, "").strip() != group.get(field, "").strip():
                fail(f"allocated identity metadata drift: {group_key}:{field}")
        if identity.get("CreatedFromCandidate", "").strip() != group_key:
            fail(f"allocated identity provenance drift: {group_key}->{eid}")
        if identity.get("CreatedFromOccurrence", "").strip() != alloc.get("AllocatedFromOccurrence", "").strip():
            fail(f"allocated identity first occurrence drift: {group_key}->{eid}")
    if len(allocated_ids) != 110:
        fail("Grade 5-6 allocated identity count is not 110")
    expected_new_ids = {f"KE{i:06d}" for i in range(67, 177)}
    if allocated_ids != expected_new_ids:
        fail(f"Grade 5-6 IDs must append KE000067..KE000176; actual range={min(allocated_ids)}..{max(allocated_ids)}")

    # Exact source-provenance and reconciliation mapping check for all 153 source rows.
    current_source: dict[str, dict[str, str]] = {}
    for path in SOURCE_FILES:
        for row in read_csv(path):
            key = source_occurrence_key(row)
            if key in current_source:
                fail(f"duplicate current Grade 5-6 source key: {key}")
            current_source[key] = row
    if len(current_source) != 153 or set(provenance) != set(current_source):
        fail("Grade 5-6 occurrence provenance does not exactly cover 153 current source rows")
    occurrence_key_by_id: dict[str, str] = {}
    for key, prov in provenance.items():
        oid = prov.get("OccurrenceID", "").strip()
        if not OCC_RE.fullmatch(oid) or oid not in occurrences or oid in occurrence_key_by_id:
            fail(f"invalid Grade 5-6 occurrence allocation: {key}->{oid}")
        occurrence_key_by_id[oid] = key
        src = current_source[key]
        for pfield, sfield in (
            ("SourceID", "SourceID"), ("SourceEdition", "SourceEdition"),
            ("EvidenceFileID", "EvidenceFileID"), ("Grade", "Grade"),
            ("Unit", "Unit"), ("Order", "Order"), ("Page", "Page"),
        ):
            if prov.get(pfield, "").strip() != src.get(sfield, "").strip():
                fail(f"Grade 5-6 provenance drift: {key}:{pfield}")
        occ = occurrences[oid]
        want_semester = "upper" if src.get("Semester", "").strip() == "上" else "lower"
        if (
            occ.get("SourceID", "").strip() != src.get("SourceID", "").strip()
            or occ.get("SourceGrade", "").strip() != src.get("Grade", "").strip()
            or occ.get("Semester", "").strip() != want_semester
            or occ.get("Unit", "").strip() != src.get("Unit", "").strip()
            or occ.get("Order", "").strip() != src.get("Order", "").strip()
            or occ.get("RawExpression", "").strip() != src.get("RawExpression", "").strip()
            or occ.get("RawTranslation", "").strip() != src.get("Translation", "").strip()
        ):
            fail(f"materialized source occurrence drift: {key}->{oid}")

    mapped: dict[str, list[str]] = defaultdict(list)
    mapping_by_occurrence: defaultdict[str, set[str]] = defaultdict(set)
    for row in read_csv(SOURCE_MAP):
        if row.get("MappingStatus", "").strip() != "confirmed":
            fail(f"unconfirmed persistent source mapping: {row}")
        oid = row.get("OccurrenceID", "").strip()
        eid = row.get("ExpressionID", "").strip()
        if oid not in occurrences or eid not in registry:
            fail(f"invalid source mapping {oid}->{eid}")
        if eid in mapping_by_occurrence[oid]:
            fail(f"duplicate source mapping {oid}->{eid}")
        mapping_by_occurrence[oid].add(eid)
        mapped[eid].append(oid)

    decisions = keyed(read_csv(G56_DECISIONS), "SourceOccurrenceKey", "Grade 5-6 source decision")
    if set(decisions) != set(current_source):
        fail("Grade 5-6 source decisions do not cover current source exactly")
    mapped_count = 0
    source_only_count = 0
    reused_ids: set[str] = set()
    for key, decision in decisions.items():
        oid = provenance[key]["OccurrenceID"].strip()
        disposition = decision.get("Disposition", "").strip()
        tokens = split_groups(decision.get("IdentityGroups", ""))
        if disposition == "source-only":
            source_only_count += 1
            if tokens or mapping_by_occurrence.get(oid):
                fail(f"source-only occurrence leaked into card mapping: {key}->{oid}")
            continue
        if disposition != "mapped" or not tokens:
            fail(f"invalid Grade 5-6 source decision: {key}")
        mapped_count += 1
        expected: set[str] = set()
        for token in tokens:
            if token.startswith("new::"):
                if token not in allocation:
                    fail(f"decision references unallocated group: {key}->{token}")
                expected.add(allocation[token]["ExpressionID"].strip())
            elif ID_RE.fullmatch(token):
                if token not in registry:
                    fail(f"decision reuses unknown Stable ExpressionID: {key}->{token}")
                reused_ids.add(token)
                expected.add(token)
            else:
                fail(f"invalid decision identity token: {key}->{token}")
        if mapping_by_occurrence.get(oid, set()) != expected:
            fail(
                f"materialized source mapping differs from reviewed decision: {key} "
                f"actual={sorted(mapping_by_occurrence.get(oid,set()))} expected={sorted(expected)}"
            )
    if (mapped_count, source_only_count, len(reused_ids)) != (138, 15, 8):
        fail(f"Grade 5-6 source closure drift: mapped={mapped_count} source_only={source_only_count} reused={len(reused_ids)}")

    allowed_orders: list[str] = []
    ordered_stages: list[tuple[str, str]] = []
    expected_publish: list[dict[str, str]] = []
    review_counts: defaultdict[str, int] = defaultdict(int)
    stage_counts: defaultdict[str, int] = defaultdict(int)

    for eid in sorted(ids):
        identity = registry[eid]
        rel = release[eid]
        cur = current[eid]
        adm = admission[eid]
        rev = reviews[eid]
        if identity.get("Status", "").strip() != "active" or rel.get("IdentityStatus", "").strip() != "active":
            fail(f"non-active released identity: {eid}")

        candidate_key = identity.get("CreatedFromCandidate", "").strip()
        if candidate_key.startswith("new::"):
            if candidate_key not in allocation or allocation[candidate_key]["ExpressionID"].strip() != eid:
                fail(f"new identity missing durable allocation: {candidate_key}->{eid}")
        else:
            if candidate_key not in candidates or (candidate_key, eid) not in resolution_pairs:
                fail(f"baseline identity missing explicit resolution: {candidate_key}->{eid}")
        if identity.get("CreatedFromOccurrence", "").strip() not in mapped.get(eid, []):
            fail(f"CreatedFromOccurrence is not confirmed-mapped: {eid}")

        if adm.get("Status", "").strip() != "allowed":
            fail(f"current Expression is not admitted: {eid}")
        if cur.get("LearnerProfile", "").strip() != "klose" or cur.get("LearnerLevel", "").strip() != "4":
            fail(f"learner profile/level drift: {eid}")
        stage = adm.get("Stage", "").strip()
        tag = adm.get("LearningTag", "").strip()
        if stage not in STAGE_TAG or tag != STAGE_TAG[stage]:
            fail(f"invalid stage/tag: {eid} stage={stage!r} tag={tag!r}")
        stage_counts[stage] += 1
        grades = {r.get("SourceGrade", "").strip() for r in source_rows(eid, occurrences, mapped)}
        if stage == "stage::grade4-expression" and "4" not in grades:
            fail(f"Grade-4 baseline Expression lost Grade-4 source: {eid}")
        if stage == "stage::grade3-expression" and "3" not in grades:
            fail(f"Grade-3 baseline Expression lost Grade-3 source: {eid}")
        if stage == "stage::grade5-6-expression":
            if eid not in allocated_ids or not (grades & {"5", "6"}):
                fail(f"Grade 5-6 stage is not a newly allocated Grade 5-6 identity: {eid}")

        order = adm.get("LearningOrder", "").strip()
        if not ORDER_RE.fullmatch(order):
            fail(f"invalid LearningOrder: {eid}={order!r}")
        allowed_orders.append(order)
        ordered_stages.append((order, stage))

        if rev.get("FingerprintVersion", "").strip() != VERSION or rev.get("Fingerprint", "").strip() != fingerprint(cur):
            fail(f"stale/unsupported learner presentation review: {eid}")
        review_status = rev.get("ReviewStatus", "").strip()
        review_counts[review_status] += 1
        if review_status not in PUBLISHABLE_REVIEW_STATUSES:
            fail(f"current admitted Expression is not release-reviewed: {eid}={review_status!r}")
        if rel.get("PresentationStatus", "").strip() != review_status:
            fail(f"release presentation/review status mismatch: {eid}")
        if rel.get("AdmissionStatus", "").strip() != "allowed":
            fail(f"release admission status drift: {eid}")
        if rel.get("PublishStatus", "").strip() != "generated" or rel.get("ReleaseStatus", "").strip() != "ready":
            fail(f"reviewed Expression is not release-ready: {eid}")
        for field in ("FunctionLabel", "Prompt", "Target", "Pattern", "MeaningUsage", "Examples"):
            if not cur.get(field, "").strip():
                fail(f"reviewed Expression missing learner field: {eid}:{field}")

        sources, books = source_metadata(eid, occurrences, mapped)
        expected_publish.append({
            "ExpressionID": eid,
            "FunctionLabel": cur["FunctionLabel"].strip(),
            "Prompt": cur["Prompt"].strip(),
            "PromptHint": cur.get("PromptHint", "").strip(),
            "Target": cur["Target"].strip(),
            "Pattern": cur["Pattern"].strip(),
            "MeaningUsage": cur["MeaningUsage"].strip(),
            "Examples": cur["Examples"].strip(),
            "LearnerLevel": cur["LearnerLevel"].strip(),
            "LearningOrder": order,
            "Sources": sources,
            "SourceBooks": books,
        })

    if len(allowed_orders) != len(set(allowed_orders)):
        fail("duplicate LearningOrder")
    expected_orders = [f"{i:06d}" for i in range(1, len(ids) + 1)]
    if sorted(allowed_orders) != expected_orders:
        fail("LearningOrder must remain continuous 000001..000176")
    ranks = [STAGE_RANK[stage] for _, stage in sorted(ordered_stages)]
    if ranks != sorted(ranks):
        fail("LearningOrder stage blocks must remain Grade4 -> Grade3 -> Grade5-6")
    if stage_counts["stage::grade5-6-expression"] != 110:
        fail(f"Grade 5-6 admission count is not 110: {stage_counts['stage::grade5-6-expression']}")
    if review_counts["model-reviewed"] != 110:
        fail(f"Grade 5-6 model-reviewed count is not 110: {review_counts['model-reviewed']}")

    expected_publish.sort(key=lambda row: row["LearningOrder"])
    study_rows = read_csv(STUDY)
    if study_rows != expected_publish:
        fail("study.csv is not exactly derivable from current reviewed upstream state")
    if len(study_rows) != 176:
        fail(f"expected 176 publishable Expressions, got {len(study_rows)}")

    headers, anki_rows = read_anki_import(ANKI_IMPORT)
    expected_headers = {
        "separator": "Comma",
        "html": "false",
        "notetype": NOTE_TYPE,
        "deck": DECK,
        "columns": ",".join(PUBLISH_FIELDS),
    }
    if headers != expected_headers:
        fail(f"Anki headers mismatch: {headers}")
    if anki_rows != study_rows:
        fail("anki-import.csv data differs from study.csv")

    print(
        "Expression Release Gate PASS: "
        f"publishable={len(study_rows)} baseline=66 grade5_6_new=110 reused={len(reused_ids)} "
        f"source_only={source_only_count} review_counts={dict(sorted(review_counts.items()))} "
        f"learning_order=000001..{len(ids):06d}"
    )


if __name__ == "__main__":
    main()
