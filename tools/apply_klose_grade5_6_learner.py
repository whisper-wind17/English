#!/usr/bin/env python3
"""Apply validated Grade 5-6 learner presentation to active new Vocabulary Notes.

This is a learner-layer transition only. It updates bilingual examples and removes
resolved content-gap queue rows. It does not change identity, source mapping,
learning admission, release registries, generated publish files, or Anki state.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
REG = BASE / "master" / "note_registry_extensions.csv"
LEARNER = BASE / "learner" / "current.csv"
REVIEW = BASE / "review" / "learner_review.csv"
BATCHES = [
    BASE / "learner" / "grade5_6_content_batch_a.csv",
    BASE / "learner" / "grade5_6_content_batch_b.csv",
    BASE / "learner" / "grade5_6_content_batch_c.csv",
]
CREATED_SOURCE = "klose-grade5-6-current"
EXPECTED_REASON = "grade5-6-current-new-note-needs-learner-content-and-lexical-facts"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing input: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def note_num(nid: str) -> int:
    return int(nid.removeprefix("KV"))


def main() -> None:
    active_rows = [
        r for r in read_csv(REG)
        if r.get("CreatedSource", "").strip() == CREATED_SOURCE
        and r.get("Status", "").strip() == "active"
    ]
    active = {r["NoteID"].strip() for r in active_rows}
    if len(active) != 288:
        raise SystemExit(f"Expected 288 active Grade 5-6 new identities, got {len(active)}")

    content_rows = [r for p in BATCHES for r in read_csv(p)]
    content = {r["NoteID"].strip(): r for r in content_rows}
    if len(content_rows) != 288 or len(content) != 288 or set(content) != active:
        raise SystemExit(
            f"Learner content must exactly cover active Grade 5-6 new IDs: "
            f"rows={len(content_rows)} unique={len(content)} active={len(active)}"
        )

    learner_rows = read_csv(LEARNER)
    learner_fields = list(learner_rows[0].keys())
    learner_by_id = {r["NoteID"].strip(): r for r in learner_rows}
    if len(learner_by_id) != len(learner_rows) or not active <= set(learner_by_id):
        raise SystemExit("Learner current state does not uniquely cover all active Grade 5-6 new IDs")

    for nid in active:
        target = learner_by_id[nid]
        src = content[nid]
        if target.get("LearnerProfile", "").strip() != "klose" or target.get("LearnerLevel", "").strip() != "4":
            raise SystemExit(f"Unexpected learner profile/level for {nid}")
        if target.get("PresentationStatus", "").strip() not in {"grade5-6-current-pending", "grade5-6-content-ready"}:
            raise SystemExit(f"Unexpected pre-apply presentation status for {nid}: {target.get('PresentationStatus')!r}")
        if src.get("ContentStatus", "").strip() != "model-curated" or src.get("ContentSource", "").strip() != "grade5-6-learner-content-v1":
            raise SystemExit(f"Invalid content provenance for {nid}")
        sentence = src.get("ExampleSentence", "").strip()
        translation = src.get("ExampleTranslation", "").strip()
        if not sentence or not translation:
            raise SystemExit(f"Incomplete bilingual learner content for {nid}")
        target["ExampleSentence"] = sentence
        target["ExampleTranslation"] = translation
        target["PresentationStatus"] = "grade5-6-content-ready"
        target["PresentationSource"] = "klose:grade5-6-learner-content-v1"

    learner_rows.sort(key=lambda r: note_num(r["NoteID"]))
    write_csv(LEARNER, learner_fields, learner_rows)

    review_rows = read_csv(REVIEW)
    review_fields = list(review_rows[0].keys())
    gap_ids = {
        r.get("NoteID", "").strip()
        for r in review_rows
        if r.get("Reason", "").strip() == EXPECTED_REASON
    }
    if gap_ids != active:
        missing = sorted(active - gap_ids, key=note_num)
        extra = sorted(gap_ids - active, key=note_num)
        raise SystemExit(
            f"Grade 5-6 content-gap queue does not equal active set before transition: "
            f"missing={missing[:10]} extra={extra[:10]}"
        )
    remaining = [r for r in review_rows if r.get("NoteID", "").strip() not in active]
    write_csv(REVIEW, review_fields, remaining)
    print(f"Applied Grade 5-6 learner presentation: content_ready={len(active)}, content_gap_removed={len(gap_ids)}")


if __name__ == "__main__":
    main()
