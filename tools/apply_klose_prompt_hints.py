#!/usr/bin/env python3
"""Apply optional front-side PromptHint values to Klose Vocabulary.

PromptHint is learner presentation, not source fact or vocabulary identity.
This overlay runs after all ordinary learner/example overlays so it can add the
field without changing Stable NoteID, canonical identity, or Anki card identity.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
LEARNER = BASE / "learner" / "current.csv"
OVERRIDES = BASE / "learner" / "prompt_hint_overrides.csv"
PROFILE = BASE / "config" / "profile.json"
PUBLISH = BASE / "publish"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def insert_after(fields: list[str], after: str, field: str) -> list[str]:
    fields = [f for f in fields if f != field]
    if after not in fields:
        raise SystemExit(f"Cannot insert {field}: missing anchor field {after}")
    index = fields.index(after) + 1
    return fields[:index] + [field] + fields[index:]


def main() -> None:
    for path in (LEARNER, OVERRIDES, PROFILE, PUBLISH / "study.csv"):
        if not path.exists():
            raise SystemExit(f"Missing PromptHint input: {path.relative_to(ROOT)}")

    learner_rows = read_csv(LEARNER)
    if not learner_rows:
        raise SystemExit("learner/current.csv is empty")
    learner_by_id = {r["NoteID"].strip(): r for r in learner_rows}

    overrides: dict[str, str] = {}
    for row in read_csv(OVERRIDES):
        nid = row.get("NoteID", "").strip()
        hint = row.get("PromptHint", "").strip()
        if not nid or nid in overrides:
            raise SystemExit(f"Invalid/duplicate PromptHint override: {nid!r}")
        if nid not in learner_by_id:
            raise SystemExit(f"PromptHint override references unknown NoteID: {nid}")
        if not hint:
            raise SystemExit(f"PromptHint override is blank: {nid}")
        overrides[nid] = hint

    # Deterministic overlay: every learner row has the field; only explicit
    # overrides are non-empty.
    for row in learner_rows:
        row["PromptHint"] = overrides.get(row["NoteID"].strip(), "")
    learner_fields = insert_after(list(learner_rows[0].keys()), "LearnerLevel", "PromptHint")
    learner_rows.sort(key=lambda r: int(r["NoteID"].removeprefix("KV")))
    write_csv(LEARNER, learner_fields, learner_rows)

    updated_views = 0
    for path in sorted(PUBLISH.rglob("*.csv")):
        if path.name == "anki-import.csv":
            continue
        rows = read_csv(path)
        if not rows:
            continue
        fields = list(rows[0].keys())
        if "NoteID" not in fields or "Word" not in fields:
            continue
        fields = insert_after(fields, "Word", "PromptHint")
        for row in rows:
            nid = row.get("NoteID", "").strip()
            row["PromptHint"] = learner_by_id.get(nid, {}).get("PromptHint", "")
        write_csv(path, fields, rows)
        updated_views += 1

    study = read_csv(PUBLISH / "study.csv")
    if not study:
        raise SystemExit("publish/study.csv is empty after PromptHint overlay")
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

    nonempty = sum(1 for row in learner_rows if row.get("PromptHint", "").strip())
    print(
        f"Applied PromptHint overlay: learner_rows={len(learner_rows)}, "
        f"nonempty={nonempty}, publish_views={updated_views}"
    )


if __name__ == "__main__":
    main()
