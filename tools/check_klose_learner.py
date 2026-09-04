#!/usr/bin/env python3
"""Flag Grade-4 learner examples that use vocabulary explicitly introduced later.

The textbook vocabulary lists are not exhaustive. This checker only flags a
strong condition: a content token in an example maps to a listed vocabulary
item whose earliest explicit rj_start1 occurrence is after the learner level.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "klose"
MASTER = BASE / "master" / "vocabulary_master.csv"
OCCURRENCES = BASE / "master" / "source_occurrences.csv"
LEARNER = BASE / "learner" / "current.csv"
REPORT = BASE / "review" / "future_vocab_review.csv"
SOURCE_ID = "rj_start1"

FUNCTION_WORDS = {
    "a", "an", "the", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "our", "their", "this", "that", "these", "those", "who", "what", "where", "when", "why", "how",
    "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must", "not", "don't", "doesn't", "didn't",
    "and", "or", "but", "so", "because", "if", "then", "than", "as", "in", "on", "at", "to", "from", "of", "for", "with", "by",
    "near", "under", "behind", "between", "before", "after", "into", "out", "around", "about", "over", "here", "there",
    "very", "too", "also", "only", "just", "more", "most", "less", "some", "any", "many", "much", "all", "every", "each",
}
TOKEN_RE = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def tokens(text: str) -> list[str]:
    return [x.lower().replace("’", "'") for x in TOKEN_RE.findall(text)]


def lemmas(token: str) -> set[str]:
    out = {token}
    if token.endswith("'s"):
        out.add(token[:-2])
    if len(token) > 4 and token.endswith("ies"):
        out.add(token[:-3] + "y")
    if len(token) > 4 and token.endswith("ing"):
        stem = token[:-3]
        out.update({stem, stem + "e"})
        if len(stem) > 2 and stem[-1] == stem[-2]:
            out.add(stem[:-1])
    if len(token) > 3 and token.endswith("ied"):
        out.add(token[:-3] + "y")
    if len(token) > 3 and token.endswith("ed"):
        stem = token[:-2]
        out.update({stem, stem + "e"})
        if len(stem) > 2 and stem[-1] == stem[-2]:
            out.add(stem[:-1])
    if len(token) >= 4 and token.endswith("es"):
        out.update({token[:-2], token[:-1]})
    if len(token) > 3 and token.endswith("s"):
        out.add(token[:-1])
    irregular = {
        "went": "go", "gone": "go", "saw": "see", "seen": "see", "bought": "buy", "took": "take", "taken": "take",
        "ate": "eat", "eaten": "eat", "drank": "drink", "drunk": "drink", "swam": "swim", "swum": "swim",
        "wrote": "write", "written": "write", "made": "make", "came": "come", "got": "get", "gave": "give", "given": "give",
        "ran": "run", "won": "win", "felt": "feel", "left": "leave", "met": "meet", "spent": "spend", "began": "begin",
        "became": "become", "kept": "keep", "heard": "hear", "wore": "wear", "chosen": "choose", "chose": "choose",
    }
    if token in irregular:
        out.add(irregular[token])
    return out


def main() -> None:
    master = read_csv(MASTER)
    occ = read_csv(OCCURRENCES)
    learner = read_csv(LEARNER)
    learner_by_id = {r["NoteID"]: r for r in learner}

    first_grade_by_id: dict[str, int] = {}
    for row in occ:
        if row["SourceID"] != SOURCE_ID or not row["Grade"].isdigit():
            continue
        grade = int(row["Grade"])
        first_grade_by_id[row["NoteID"]] = min(grade, first_grade_by_id.get(row["NoteID"], grade))

    earliest: dict[str, int] = {}
    for row in master:
        grade = first_grade_by_id.get(row["NoteID"])
        if grade is None:
            continue
        for token in tokens(row["CanonicalWord"]):
            for lemma in lemmas(token):
                earliest[lemma] = min(grade, earliest.get(lemma, grade))

    review: list[dict[str, str]] = []
    for row in master:
        if row["Released"] != "yes":
            continue
        lr = learner_by_id[row["NoteID"]]
        level = int(lr["LearnerLevel"])
        future: dict[str, int] = {}
        for token in tokens(lr["ExampleSentence"]):
            if token in FUNCTION_WORDS:
                continue
            matched = [earliest[x] for x in lemmas(token) if x in earliest]
            if matched and min(matched) > level:
                future[token] = min(matched)
        if future:
            review.append({
                "NoteID": row["NoteID"],
                "Word": row["Word"],
                "LearnerLevel": lr["LearnerLevel"],
                "ExampleSentence": lr["ExampleSentence"],
                "FutureVocabulary": " ".join(f"{k}->G{v}" for k, v in sorted(future.items())),
            })

    write_csv(REPORT, ["NoteID", "Word", "LearnerLevel", "ExampleSentence", "FutureVocabulary"], review)
    print(f"Klose future-vocabulary review items: {len(review)}")
    for row in review:
        print(f"{row['NoteID']} | {row['Word']} | {row['FutureVocabulary']} | {row['ExampleSentence']}")
    if review:
        raise SystemExit("Learner examples contain vocabulary explicitly introduced after the learner level")


if __name__ == "__main__":
    main()
