#!/usr/bin/env python3
"""Apply learner-presentation overrides for actual Grade-4 reused identities.

This runs after the ordinary learner override stack so actual textbook forms win
without changing Stable NoteID or canonical identity. Because the ordinary stack
also generates publish views, this final overlay updates those generated views in
place and regenerates `anki-import.csv` from the corrected `study.csv`.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
LEARNER = BASE / "learner" / "current.csv"
OVERRIDES = BASE / "learner" / "actual_grade4_reuse_overrides.csv"
PROFILE = BASE / "config" / "profile.json"
PUBLISH = BASE / "publish"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_anki_import(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
    note_type: str,
    deck: str,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("#separator:Comma\n")
        f.write("#html:false\n")
        f.write(f"#notetype:{note_type}\n")
        f.write(f"#deck:{deck}\n")
        f.write(f"#tags column:{fields.index('Tags') + 1}\n")
        f.write("#columns:" + ",".join(fields) + "\n")
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writerows(rows)


def main() -> None:
    for path in (LEARNER, OVERRIDES, PROFILE, PUBLISH / "study.csv"):
        if not path.exists():
            raise SystemExit(f"Missing learner reuse input: {path.relative_to(ROOT)}")

    override_rows = read_csv(OVERRIDES)
    override_by_id: dict[str, dict[str, str]] = {}
    for row in override_rows:
        nid = row.get("NoteID", "").strip()
        if not nid or nid in override_by_id:
            raise SystemExit(f"Invalid/duplicate Grade-4 reused learner override: {nid!r}")
        example = row.get("ExampleSentence", "").strip()
        translation = row.get("ExampleTranslation", "").strip()
        if not example or not translation:
            raise SystemExit(f"Incomplete reused learner override: {nid}")
        override_by_id[nid] = {
            "ExampleSentence": example,
            "ExampleTranslation": translation,
        }

    learner_rows = read_csv(LEARNER)
    if not learner_rows:
        raise SystemExit("learner/current.csv is empty")
    learner_fields = list(learner_rows[0].keys())
    learner_by_id = {r["NoteID"].strip(): r for r in learner_rows}
    for nid, override in override_by_id.items():
        if nid not in learner_by_id:
            raise SystemExit(f"Reused learner override references unknown NoteID: {nid}")
        target = learner_by_id[nid]
        target.update(override)
        target["PresentationStatus"] = "grade4-reviewed"
        target["PresentationSource"] = "klose:actual_grade4_reuse_overrides"

    learner_rows.sort(key=lambda r: int(r["NoteID"].removeprefix("KV")))
    write_csv(LEARNER, learner_fields, learner_rows)

    # Keep every generated CSV view aligned with the final learner presentation.
    updated_views = 0
    for path in sorted(PUBLISH.rglob("*.csv")):
        if path.name == "anki-import.csv":
            continue
        rows = read_csv(path)
        if not rows:
            continue
        fields = list(rows[0].keys())
        if not {"NoteID", "ExampleSentence", "ExampleTranslation"}.issubset(fields):
            continue
        changed = False
        for row in rows:
            override = override_by_id.get(row.get("NoteID", "").strip())
            if override is None:
                continue
            row.update(override)
            changed = True
        if changed:
            write_csv(path, fields, rows)
            updated_views += 1

    study = read_csv(PUBLISH / "study.csv")
    if not study:
        raise SystemExit("publish/study.csv is empty")
    publish_fields = list(study[0].keys())
    with PROFILE.open("r", encoding="utf-8") as f:
        profile = json.load(f)
    write_anki_import(
        PUBLISH / "anki-import.csv",
        publish_fields,
        study,
        note_type=str(profile["note_type"]),
        deck=str(profile["main_deck"]),
    )

    print(
        "Applied actual Grade-4 reused learner presentations: "
        f"notes={len(override_by_id)}, publish_views={updated_views}"
    )


if __name__ == "__main__":
    main()
