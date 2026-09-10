#!/usr/bin/env python3
"""Compile reviewed Grade 5-6 IPA evidence into the durable new-note fact layer."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
REG = BASE / "master" / "note_registry_extensions.csv"
REVIEW = BASE / "review" / "grade5_6_lexical_facts"
AUTO = REVIEW / "ipa_candidates.csv"
UNRESOLVED = REVIEW / "ipa_unresolved.csv"
MANUAL = REVIEW / "ipa_manual_review.csv"
OUT = BASE / "master" / "grade5_6_new_fact_overrides.csv"
CREATED_SOURCE = "klose-grade5-6-current"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing input: {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def note_num(nid: str) -> int:
    return int(nid.removeprefix("KV"))


def main() -> None:
    active_rows = [
        r for r in read_csv(REG)
        if r.get("CreatedSource", "").strip() == CREATED_SOURCE
        and r.get("Status", "").strip() == "active"
    ]
    active = {r["NoteID"].strip(): r for r in active_rows}
    if len(active) != 288:
        raise SystemExit(f"Expected 288 active Grade 5-6 new identities, got {len(active)}")

    auto_rows = read_csv(AUTO)
    unresolved_rows = read_csv(UNRESOLVED)
    manual_rows = read_csv(MANUAL)
    auto = {r["NoteID"].strip(): r for r in auto_rows}
    unresolved = {r["NoteID"].strip(): r for r in unresolved_rows}
    manual = {r["NoteID"].strip(): r for r in manual_rows}
    if len(auto) != len(auto_rows) or len(unresolved) != len(unresolved_rows) or len(manual) != len(manual_rows):
        raise SystemExit("Duplicate NoteID in Grade 5-6 IPA review inputs")
    if len(auto) != 213 or len(unresolved) != 75 or len(manual) != 75:
        raise SystemExit(f"Unexpected IPA review counts: auto={len(auto)} unresolved={len(unresolved)} manual={len(manual)}")
    if set(manual) != set(unresolved):
        raise SystemExit("Manual IPA review must exactly cover unresolved IPA set")
    if set(auto) & set(manual):
        raise SystemExit("Auto and manual IPA sets overlap")
    if set(auto) | set(manual) != set(active):
        missing = sorted(set(active) - (set(auto) | set(manual)), key=note_num)
        extra = sorted((set(auto) | set(manual)) - set(active), key=note_num)
        raise SystemExit(f"IPA coverage does not equal active Grade 5-6 new IDs: missing={missing[:10]} extra={extra[:10]}")

    out: list[dict[str, str]] = []
    for nid in sorted(active, key=note_num):
        reg = active[nid]
        if nid in auto:
            src = auto[nid]
            status = "repo-exact-unanimous"
            fact_source = "grade5_6_lexical_facts:auto|" + src.get("EvidenceSources", "").strip()
        else:
            src = manual[nid]
            if src.get("ReviewStatus", "").strip() != "model-reviewed" or src.get("ReviewerType", "").strip() != "model":
                raise SystemExit(f"Unreviewed manual IPA row: {nid}")
            status = "model-curated"
            fact_source = "grade5_6_lexical_facts:manual-model-review"
        if src.get("CanonicalWord", "").strip() != reg.get("CanonicalWord", "").strip():
            raise SystemExit(f"CanonicalWord drift for {nid}: {src.get('CanonicalWord')!r} != {reg.get('CanonicalWord')!r}")
        uk, us = src.get("British", "").strip(), src.get("American", "").strip()
        if not uk or not us or not (uk.startswith("[") and uk.endswith("]") and us.startswith("[") and us.endswith("]")):
            raise SystemExit(f"Invalid IPA pair for {nid}: {uk!r} / {us!r}")
        out.append({
            "NoteID": nid,
            "British": uk,
            "American": us,
            "FactStatus": status,
            "FactSource": fact_source,
        })

    write_csv(OUT, ["NoteID", "British", "American", "FactStatus", "FactSource"], out)
    print(f"Compiled Grade 5-6 new-note lexical facts: total={len(out)}, repo_exact={len(auto)}, model_curated={len(manual)}")


if __name__ == "__main__":
    main()
