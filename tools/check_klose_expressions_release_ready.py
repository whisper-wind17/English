#!/usr/bin/env python3
"""Release gate for the Klose Expressions bounded context."""
from __future__ import annotations

import csv
import io
import re
from collections import defaultdict
from pathlib import Path

from klose_expression_review_fingerprint import VERSION, fingerprint

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose" / "expressions"
MASTER = BASE / "master"
LEARNER = BASE / "learner"
REVIEW = BASE / "review"
PUBLISH = BASE / "publish"

REGISTRY = MASTER / "expression_registry.csv"
OCCURRENCES = MASTER / "expression_occurrences.csv"
SOURCE_MAP = MASTER / "source_expression_map.csv"
RELEASE = MASTER / "release_registry.csv"
CURRENT = LEARNER / "current.csv"
ADMISSION = LEARNER / "learning_admission.csv"
REVIEWS = LEARNER / "presentation_review_registry.csv"
CANDIDATES = REVIEW / "candidate_registry.csv"
STUDY = PUBLISH / "study.csv"
ANKI_IMPORT = PUBLISH / "anki-import.csv"

PUBLISH_FIELDS = [
    "ExpressionID", "FunctionLabel", "Prompt", "PromptHint", "Target", "Pattern",
    "MeaningUsage", "Examples", "LearnerLevel", "LearningOrder", "Sources", "SourceBooks",
]
NOTE_TYPE = "Klose Expression"
DECK = "Klose-English::Expressions"
ID_RE = re.compile(r"^KE\d{6}$")
ORDER_RE = re.compile(r"^\d{6}$")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def keyed(rows: list[dict[str, str]], field: str, label: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row.get(field, "").strip()
        if not key or key in result:
            raise SystemExit(f"Release blocked: invalid/duplicate {label}: {key!r}")
        result[key] = row
    return result


def read_anki_import(path: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    if path.read_bytes().startswith(b"\xef\xbb\xbf"):
        raise SystemExit("Release blocked: anki-import.csv must be UTF-8 without BOM")
    headers: dict[str, str] = {}
    data: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            if line.startswith("#"):
                if ":" not in line:
                    raise SystemExit(f"Release blocked: malformed Anki header: {line}")
                key, value = line[1:].split(":", 1)
                headers[key.strip().lower()] = value.strip()
            elif line:
                data.append(raw)
    rows: list[dict[str, str]] = []
    for index, values in enumerate(csv.reader(io.StringIO("".join(data))), start=1):
        if len(values) != len(PUBLISH_FIELDS):
            raise SystemExit(
                f"Release blocked: Anki row {index} has {len(values)} columns; expected {len(PUBLISH_FIELDS)}"
            )
        rows.append(dict(zip(PUBLISH_FIELDS, values)))
    return headers, rows


def source_metadata(
    eid: str,
    occurrence_by_id: dict[str, dict[str, str]],
    mapped_occurrences: dict[str, list[str]],
) -> tuple[str, str]:
    rows = [occurrence_by_id[oid] for oid in mapped_occurrences.get(eid, [])]
    if not rows:
        raise SystemExit(f"Release blocked: Expression has no confirmed source mapping: {eid}")
    sources = sorted({row["SourceID"].strip() for row in rows})
    books = sorted({
        f"{row['SourceID'].strip()}::grade{row['SourceGrade'].strip()}-{row['Semester'].strip()}"
        for row in rows
    })
    return "|".join(sources), "|".join(books)


def main() -> None:
    required = (
        REGISTRY, OCCURRENCES, SOURCE_MAP, RELEASE, CURRENT, ADMISSION,
        REVIEWS, CANDIDATES, STUDY, ANKI_IMPORT,
    )
    for path in required:
        if not path.exists():
            raise SystemExit(f"Release blocked: missing {path.relative_to(ROOT)}")

    registry = keyed(read_csv(REGISTRY), "ExpressionID", "ExpressionID")
    release = keyed(read_csv(RELEASE), "ExpressionID", "release ExpressionID")
    current = keyed(read_csv(CURRENT), "ExpressionID", "learner ExpressionID")
    admission = keyed(read_csv(ADMISSION), "ExpressionID", "admission ExpressionID")
    reviews = keyed(read_csv(REVIEWS), "ExpressionID", "review ExpressionID")
    candidates = keyed(read_csv(CANDIDATES), "CandidateKey", "CandidateKey")
    occurrences = keyed(read_csv(OCCURRENCES), "OccurrenceID", "OccurrenceID")

    ids = set(registry)
    if not ids or any(not ID_RE.fullmatch(eid) for eid in ids):
        raise SystemExit("Release blocked: invalid or empty Expression Registry")
    if set(release) != ids or set(current) != ids or set(admission) != ids or set(reviews) != ids:
        raise SystemExit("Release blocked: Registry/Release/Learner/Admission/Review identity coverage mismatch")

    mapped: dict[str, list[str]] = defaultdict(list)
    for row in read_csv(SOURCE_MAP):
        if row.get("MappingStatus", "").strip() != "confirmed":
            continue
        oid = row.get("OccurrenceID", "").strip()
        eid = row.get("ExpressionID", "").strip()
        if oid not in occurrences or eid not in registry:
            raise SystemExit(f"Release blocked: invalid source mapping {oid}->{eid}")
        mapped[eid].append(oid)

    allowed_orders: list[str] = []
    expected_publish: list[dict[str, str]] = []
    draft_count = 0
    for eid in sorted(ids):
        identity = registry[eid]
        rel = release[eid]
        cur = current[eid]
        adm = admission[eid]
        rev = reviews[eid]

        if identity.get("Status", "").strip() != "active":
            raise SystemExit(f"Release blocked: non-active pilot identity: {eid}")
        if rel.get("IdentityStatus", "").strip() != "active":
            raise SystemExit(f"Release blocked: release identity status drift: {eid}")

        candidate_key = identity.get("CreatedFromCandidate", "").strip()
        candidate = candidates.get(candidate_key)
        if candidate is None:
            raise SystemExit(f"Release blocked: identity references unknown CandidateKey: {eid}->{candidate_key}")
        if "4" not in candidate.get("SourceGrades", "").split("|"):
            raise SystemExit(f"Release blocked: current pilot contains non-Grade-4-priority identity: {eid}")

        if identity.get("CreatedFromOccurrence", "").strip() not in mapped.get(eid, []):
            raise SystemExit(f"Release blocked: CreatedFromOccurrence is not confirmed-mapped: {eid}")
        source_metadata(eid, occurrences, mapped)

        if adm.get("Status", "").strip() != "allowed":
            raise SystemExit(f"Release blocked: current pilot Expression not allowed: {eid}")
        order = adm.get("LearningOrder", "").strip()
        if not ORDER_RE.fullmatch(order):
            raise SystemExit(f"Release blocked: invalid LearningOrder: {eid}={order!r}")
        allowed_orders.append(order)

        if rev.get("FingerprintVersion", "").strip() != VERSION:
            raise SystemExit(f"Release blocked: unsupported fingerprint version: {eid}")
        if rev.get("Fingerprint", "").strip() != fingerprint(cur):
            raise SystemExit(f"Release blocked: stale learner presentation review: {eid}")

        if rev.get("ReviewStatus", "").strip() != "approved":
            draft_count += 1
            if rel.get("PresentationStatus", "").strip() != "model-reviewed":
                raise SystemExit(f"Release blocked: draft presentation status drift: {eid}")
            if rel.get("PublishStatus", "").strip() != "pending" or rel.get("ReleaseStatus", "").strip() != "pending":
                raise SystemExit(f"Release blocked: draft leaked into publish/release state: {eid}")
            continue

        if rel.get("PresentationStatus", "").strip() != "approved":
            raise SystemExit(f"Release blocked: approved presentation status drift: {eid}")
        if rel.get("AdmissionStatus", "").strip() != "allowed":
            raise SystemExit(f"Release blocked: admission status drift: {eid}")
        if rel.get("PublishStatus", "").strip() != "generated":
            raise SystemExit(f"Release blocked: approved Expression publish status is not generated: {eid}")
        if rel.get("ReleaseStatus", "").strip() != "ready":
            raise SystemExit(f"Release blocked: approved Expression release status is not ready: {eid}")

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
        raise SystemExit("Release blocked: duplicate LearningOrder")
    expected_orders = [f"{i:06d}" for i in range(1, len(allowed_orders) + 1)]
    if sorted(allowed_orders) != expected_orders:
        raise SystemExit(
            f"Release blocked: pilot LearningOrder must be continuous; actual={sorted(allowed_orders)} expected={expected_orders}"
        )

    expected_publish.sort(key=lambda row: row["LearningOrder"])
    study_rows = read_csv(STUDY)
    if study_rows != expected_publish:
        raise SystemExit("Release blocked: study.csv is not exactly derivable from approved upstream state")

    headers, anki_rows = read_anki_import(ANKI_IMPORT)
    expected_headers = {
        "separator": "Comma",
        "html": "false",
        "notetype": NOTE_TYPE,
        "deck": DECK,
        "columns": ",".join(PUBLISH_FIELDS),
    }
    if headers != expected_headers:
        raise SystemExit(f"Release blocked: Anki headers mismatch: {headers}")
    if anki_rows != study_rows:
        raise SystemExit("Release blocked: anki-import.csv data differs from study.csv")

    print(
        f"Expression Release Gate PASS: publishable={len(study_rows)} "
        f"model_reviewed_drafts={draft_count} admitted={len(allowed_orders)}"
    )


if __name__ == "__main__":
    main()
