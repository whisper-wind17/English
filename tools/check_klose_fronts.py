"""Check current-learning question identity independently of content generation."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from klose_current_policy import read_csv

BASE = Path(__file__).resolve().parents[1] / "anki/klose"


def validate_fronts(master, learner, admission):
    allowed = {r["NoteID"] for r in admission if r.get("Status") == "allowed"}
    current = {r["NoteID"]: r for r in learner}
    words, fronts = defaultdict(list), defaultdict(list)
    for row in master:
        nid = row["NoteID"]
        if nid not in allowed:
            continue
        word = " ".join(row.get("Word", "").casefold().split())
        hint = " ".join(current[nid].get("PromptHint", "").casefold().split())
        words[word].append((nid, hint))
        fronts[(word, hint)].append(nid)
    conflicts = [ids for ids in fronts.values() if len(ids) > 1]
    uncued = [nid for rows in words.values() if len(rows) > 1 for nid, hint in rows if not hint]
    if conflicts or uncued:
        raise SystemExit(f"Release blocked: ambiguous vocabulary fronts: collisions={conflicts[:12]} uncued={uncued[:12]}")
    print(f"Vocabulary fronts OK: allowed={len(allowed)} ambiguous=0")


def main():
    validate_fronts(read_csv(BASE / "master/vocabulary_master.csv"), read_csv(BASE / "learner/current.csv"), read_csv(BASE / "learner/learning_admission.csv"))


if __name__ == "__main__":
    main()
