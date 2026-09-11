#!/usr/bin/env python3
"""Deterministically build Klose Expressions study.csv and anki-import.csv.

Publishable learner presentations must be current-fingerprint reviewed and explicitly
release-ready. `approved` preserves the user-confirmed baseline; `model-reviewed`
is a distinct review state used by the current Grade 5-6 release. Draft/pending
presentations remain upstream and never leak into Anki.
"""
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
PUBLISH = BASE / "publish"

REGISTRY = MASTER / "expression_registry.csv"
OCCURRENCES = MASTER / "expression_occurrences.csv"
SOURCE_MAP = MASTER / "source_expression_map.csv"
RELEASE = MASTER / "release_registry.csv"
CURRENT = LEARNER / "current.csv"
ADMISSION = LEARNER / "learning_admission.csv"
REVIEWS = LEARNER / "presentation_review_registry.csv"

STUDY = PUBLISH / "study.csv"
ANKI_IMPORT = PUBLISH / "anki-import.csv"

PUBLISH_FIELDS = [
    "ExpressionID", "FunctionLabel", "Prompt", "PromptHint", "Target", "Pattern",
    "MeaningUsage", "Examples", "LearnerLevel", "LearningOrder", "Sources", "SourceBooks",
]
REQUIRED_PRESENTATION = [
    "FunctionLabel", "Prompt", "Target", "Pattern", "MeaningUsage", "Examples", "LearnerLevel",
]
NOTE_TYPE = "Klose Expression"
DECK = "Klose-English::Expressions"
ID_RE = re.compile(r"^KE\d{6}$")
ORDER_RE = re.compile(r"^\d{6}$")
PUBLISHABLE_REVIEW_STATUSES = {"approved", "model-reviewed"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def keyed(rows: list[dict[str, str]], field: str, label: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row.get(field, "").strip()
        if not key or key in result:
            raise SystemExit(f"Invalid/duplicate {label}: {key!r}")
        result[key] = row
    return result


def source_metadata(
    expression_id: str,
    occurrence_by_id: dict[str, dict[str, str]],
    mapped_occurrences: dict[str, list[str]],
) -> tuple[str, str]:
    rows = [occurrence_by_id[oid] for oid in mapped_occurrences.get(expression_id, [])]
    if not rows:
        raise SystemExit(f"Expression has no confirmed Source Occurrence: {expression_id}")
    sources = sorted({row["SourceID"].strip() for row in rows})
    books = sorted({
        f"{row['SourceID'].strip()}::grade{row['SourceGrade'].strip()}-{row['Semester'].strip()}"
        for row in rows
    })
    return "|".join(sources), "|".join(books)


def main() -> None:
    for path in (REGISTRY, OCCURRENCES, SOURCE_MAP, RELEASE, CURRENT, ADMISSION, REVIEWS):
        if not path.exists():
            raise SystemExit(f"Missing input: {path.relative_to(ROOT)}")

    registry = keyed(read_csv(REGISTRY), "ExpressionID", "ExpressionID")
    release = keyed(read_csv(RELEASE), "ExpressionID", "release ExpressionID")
    current = keyed(read_csv(CURRENT), "ExpressionID", "learner ExpressionID")
    admission = keyed(read_csv(ADMISSION), "ExpressionID", "admission ExpressionID")
    reviews = keyed(read_csv(REVIEWS), "ExpressionID", "review ExpressionID")
    occurrences = keyed(read_csv(OCCURRENCES), "OccurrenceID", "OccurrenceID")

    mapped: dict[str, list[str]] = defaultdict(list)
    for row in read_csv(SOURCE_MAP):
        if row.get("MappingStatus", "").strip() != "confirmed":
            continue
        oid = row.get("OccurrenceID", "").strip()
        eid = row.get("ExpressionID", "").strip()
        if oid not in occurrences:
            raise SystemExit(f"Source map references unknown OccurrenceID: {oid}")
        if eid not in registry:
            raise SystemExit(f"Source map references unknown ExpressionID: {eid}")
        mapped[eid].append(oid)

    publish_rows: list[dict[str, str]] = []
    for eid, identity in registry.items():
        if not ID_RE.fullmatch(eid):
            raise SystemExit(f"Invalid ExpressionID: {eid}")
        if identity.get("Status", "").strip() != "active":
            continue

        rel = release.get(eid)
        cur = current.get(eid)
        adm = admission.get(eid)
        rev = reviews.get(eid)
        if not all((rel, cur, adm, rev)):
            raise SystemExit(f"Active Expression missing upstream state: {eid}")

        if rel.get("IdentityStatus", "").strip() != "active":
            raise SystemExit(f"Release registry identity drift: {eid}")
        if adm.get("Status", "").strip() != "allowed":
            continue
        order = adm.get("LearningOrder", "").strip()
        if not ORDER_RE.fullmatch(order):
            raise SystemExit(f"Allowed Expression has invalid LearningOrder: {eid}={order!r}")

        review_status = rev.get("ReviewStatus", "").strip()
        if review_status not in PUBLISHABLE_REVIEW_STATUSES:
            continue
        if rev.get("FingerprintVersion", "").strip() != VERSION:
            raise SystemExit(f"Unsupported fingerprint version: {eid}")
        if rev.get("Fingerprint", "").strip() != fingerprint(cur):
            raise SystemExit(f"Reviewed learner presentation fingerprint is stale: {eid}")
        if rel.get("PresentationStatus", "").strip() != review_status:
            raise SystemExit(
                f"Release registry presentation status drift: {eid}: "
                f"release={rel.get('PresentationStatus','')!r} review={review_status!r}"
            )
        if rel.get("AdmissionStatus", "").strip() != "allowed":
            raise SystemExit(f"Release registry admission status drift: {eid}")
        if rel.get("PublishStatus", "").strip() != "generated" or rel.get("ReleaseStatus", "").strip() != "ready":
            raise SystemExit(f"Reviewed Expression is not explicitly release-ready: {eid}")

        missing = [field for field in REQUIRED_PRESENTATION if not cur.get(field, "").strip()]
        if missing:
            raise SystemExit(f"Reviewed Expression missing learner fields: {eid}:{','.join(missing)}")

        sources, source_books = source_metadata(eid, occurrences, mapped)
        publish_rows.append({
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
            "SourceBooks": source_books,
        })

    publish_rows.sort(key=lambda row: row["LearningOrder"])
    orders = [row["LearningOrder"] for row in publish_rows]
    if len(orders) != len(set(orders)):
        raise SystemExit("Duplicate LearningOrder in publishable Expressions")

    write_csv(STUDY, PUBLISH_FIELDS, publish_rows)

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    for row in publish_rows:
        writer.writerow([row[field] for field in PUBLISH_FIELDS])
    headers = [
        "#separator:Comma",
        "#html:false",
        f"#notetype:{NOTE_TYPE}",
        f"#deck:{DECK}",
        f"#columns:{','.join(PUBLISH_FIELDS)}",
    ]
    ANKI_IMPORT.parent.mkdir(parents=True, exist_ok=True)
    ANKI_IMPORT.write_text("\n".join(headers) + "\n" + buffer.getvalue(), encoding="utf-8")

    drafts = sum(
        1 for row in reviews.values()
        if row.get("ReviewStatus", "").strip() not in PUBLISHABLE_REVIEW_STATUSES
    )
    print(f"Built Klose Expressions: publishable={len(publish_rows)} drafts={drafts}")


if __name__ == "__main__":
    main()
