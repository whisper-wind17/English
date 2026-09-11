#!/usr/bin/env python3
"""Partition third-party Stable learner content candidates into compact review inputs."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose" / "third_party_vocabulary" / "learner"
CANDIDATES = BASE / "stable_presentation_candidates.csv"
OUT = BASE / "content_review_inputs"
MANIFEST = OUT / "manifest.json"
FIELDS = ["NoteID", "CanonicalWord", "SenseLabel"]
BATCH_SIZE = 96


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def main() -> None:
    rows = read_csv(CANDIDATES)
    if len(rows) != 1821:
        raise SystemExit(f"Expected 1821 third-party presentation candidates, got {len(rows)}")
    ids = [r.get("NoteID", "").strip() for r in rows]
    if not all(ids) or len(ids) != len(set(ids)):
        raise SystemExit("Third-party presentation candidates have empty/duplicate NoteID")
    expected = [f"KV{i:06d}" for i in range(1195, 3016)]
    if ids != expected:
        raise SystemExit("Third-party presentation candidate NoteID range/order drift")

    OUT.mkdir(parents=True, exist_ok=True)
    expected_files: set[str] = set()
    manifest_batches: list[dict[str, object]] = []
    for index, start in enumerate(range(0, len(rows), BATCH_SIZE), start=1):
        batch = rows[start:start + BATCH_SIZE]
        name = f"batch_{index:02d}.csv"
        expected_files.add(name)
        write_csv(OUT / name, [{k: r.get(k, "").strip() for k in FIELDS} for r in batch])
        manifest_batches.append({
            "Batch": index,
            "File": name,
            "Count": len(batch),
            "FirstNoteID": batch[0]["NoteID"],
            "LastNoteID": batch[-1]["NoteID"],
        })
    for path in OUT.glob("batch_*.csv"):
        if path.name not in expected_files:
            path.unlink()
    manifest = {
        "Version": "third-party-learner-content-review-input-v1",
        "CandidateCount": len(rows),
        "BatchSize": BATCH_SIZE,
        "BatchCount": len(manifest_batches),
        "Batches": manifest_batches,
        "ContentStatusRequiredAfterReview": "model-curated",
        "ContentSourceRequiredAfterReview": "third-party-learner-content-v1",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Third-party learner content review inputs: candidates={len(rows)} batches={len(manifest_batches)}")


if __name__ == "__main__":
    main()
