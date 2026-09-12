#!/usr/bin/env python3
"""Report observed support blockers and unassessed example vocabulary.

Admission describes curriculum eligibility, never observed mastery. Unknown support
is advisory until actual learning evidence establishes a difficulty. Function words
are a presentation scaffold, not a claim that the learner has mastered them.
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
ADMISSION = BASE / "learner" / "learning_admission.csv"
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
        "brought": "bring", "said": "say", "slept": "sleep", "born": "bear",
    }
    if token in irregular:
        out.add(irregular[token])
    return out


def main() -> None:
    master = read_csv(MASTER)
    learner = {r["NoteID"]: r for r in read_csv(LEARNER)}
    admitted = {r["NoteID"] for r in read_csv(ADMISSION) if r.get("Status") == "allowed"}
    scope = admitted | {r["NoteID"] for r in master if r.get("Released") == "yes"}
    decisions = read_csv(BASE / "feedback" / "learning_support.csv")
    support = {}
    for row in decisions:
        token = row.get("Token", "").strip().casefold()
        if not token or token in support or row.get("Status") not in {"supported", "needs-support"}:
            raise SystemExit(f"Invalid/duplicate learning-support decision: {token!r}")
        if not row.get("Evidence", "").strip() or not row.get("ObservedAt", "").strip():
            raise SystemExit(f"Learning-support decision needs actual evidence: {token}")
        support[token] = row["Status"]
    supported = set().union(*(lemmas(t) for t, status in support.items() if status == "supported")) if support else set()
    needs_support = {t for t, status in support.items() if status == "needs-support"}
    blockers, unassessed = [], []
    for row in master:
        nid = row["NoteID"]
        if nid not in scope:
            continue
        cur = learner[nid]
        target = set().union(*(lemmas(t) for t in tokens(row["Word"])))
        unknown, difficult = set(), set()
        for token in tokens(cur["ExampleSentence"]):
            forms = lemmas(token)
            if forms & target:
                continue
            # Explicit observed difficulties override generic function-word scaffolding.
            if forms & needs_support:
                difficult.add(token)
            elif token not in FUNCTION_WORDS and not forms & supported:
                unknown.add(token)
        if difficult and nid in admitted:
            blockers.append({"NoteID": nid, "Word": row["Word"], "LearnerLevel": cur["LearnerLevel"], "ExampleSentence": cur["ExampleSentence"], "FutureVocabulary": " ".join(sorted(difficult))})
        if unknown:
            unassessed.append({"NoteID": nid, "Word": row["Word"], "UnassessedVocabulary": " ".join(sorted(unknown)), "SupportStatus": "unassessed", "AdmissionIsMastery": "false"})
    write_csv(REPORT, ["NoteID", "Word", "LearnerLevel", "ExampleSentence", "FutureVocabulary"], blockers)
    write_csv(BASE / "review" / "example_support_review.csv", ["NoteID", "Word", "UnassessedVocabulary", "SupportStatus", "AdmissionIsMastery"], unassessed)
    print(f"Example support: scope={len(scope)} observed_decisions={len(support)} blockers={len(blockers)} unassessed_examples={len(unassessed)}; allowed does not imply mastered")
    # Release gate consumes the blocker report; generating a review queue is build-valid.


if __name__ == "__main__":
    main()
