#!/usr/bin/env python3
"""Check whether Anki examples introduce content words beyond the current book.

This is an approximate guardrail, not a grammar parser. Function words and a
small set of proper names are ignored; content words are checked against all
vocabulary introduced up to the note's FirstBook. Basic inflections are folded
back to known lemmas.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "人教版一年级起点"
MASTER = BASE / "master" / "vocabulary_master.csv"
REPORT = BASE / "master" / "example_vocab_review.csv"

BOOK_ORDER = [
    "1年级上", "1年级下", "2年级上", "2年级下",
    "3年级上", "3年级下", "4年级上", "4年级下",
    "5年级上", "5年级下", "6年级上", "6年级下",
]
BOOK_INDEX = {book: i for i, book in enumerate(BOOK_ORDER)}

# Grammar words are not exhaustively represented in the source vocabulary
# spreadsheets, so they are excluded from the content-vocabulary check.
FUNCTION_WORDS = {
    "a", "an", "the", "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them", "my", "your", "his", "our", "their",
    "this", "that", "these", "those", "who", "what", "where", "when", "why", "how",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "can", "could", "will", "would",
    "shall", "should", "may", "might", "must", "not", "don", "t", "s",
    "and", "or", "but", "so", "because", "if", "then", "than", "as",
    "in", "on", "at", "to", "from", "of", "for", "with", "by", "near", "under",
    "behind", "between", "before", "after", "into", "out", "around", "about", "over",
    "here", "there", "very", "too", "also", "only", "just", "more", "most", "less",
    "some", "any", "many", "much", "all", "every", "each", "one", "two", "three",
    "four", "five", "six", "seven", "eight", "nine", "ten", "first", "second", "third",
    "please", "yes", "no", "let", "lets", "let's", "don’t", "don't",
}

# Proper names/place names used only to make natural examples; they do not add
# a general lexical learning burden.
PROPER_WORDS = {
    "tom", "amy", "mum", "mom", "dad", "grandma", "beijing", "lhasa", "xi'an", "xian",
    "tibet", "sichuan", "shanghai", "guangzhou", "spring", "festival",
}

TOKEN_RE = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")


def tokens(text: str) -> list[str]:
    return [t.lower().replace("’", "'") for t in TOKEN_RE.findall(text)]


def candidate_lemmas(token: str) -> set[str]:
    out = {token}
    if token.endswith("'s"):
        out.add(token[:-2])
    if len(token) > 4 and token.endswith("ies"):
        out.add(token[:-3] + "y")
    if len(token) > 4 and token.endswith("ing"):
        stem = token[:-3]
        out.add(stem)
        out.add(stem + "e")
        if len(stem) > 2 and stem[-1] == stem[-2]:
            out.add(stem[:-1])
    if len(token) > 3 and token.endswith("ied"):
        out.add(token[:-3] + "y")
    if len(token) > 3 and token.endswith("ed"):
        stem = token[:-2]
        out.add(stem)
        out.add(stem + "e")
        if len(stem) > 2 and stem[-1] == stem[-2]:
            out.add(stem[:-1])
    if len(token) > 4 and token.endswith("es"):
        out.add(token[:-2])
        out.add(token[:-1])
    if len(token) > 3 and token.endswith("s"):
        out.add(token[:-1])
    irregular = {
        "went": "go", "gone": "go", "saw": "see", "seen": "see", "bought": "buy",
        "took": "take", "taken": "take", "ate": "eat", "eaten": "eat", "drank": "drink",
        "drunk": "drink", "swam": "swim", "swum": "swim", "wrote": "write", "written": "write",
        "made": "make", "came": "come", "got": "get", "gave": "give", "given": "give",
        "read": "read", "ran": "run", "won": "win", "felt": "feel", "left": "leave",
    }
    if token in irregular:
        out.add(irregular[token])
    return out


def main() -> None:
    with MASTER.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    words_by_book: dict[str, set[str]] = {b: set() for b in BOOK_ORDER}
    for row in rows:
        book = row["FirstBook"]
        words_by_book[book].update(tokens(row["Word"]))

    cumulative: dict[str, set[str]] = {}
    seen: set[str] = set()
    for book in BOOK_ORDER:
        seen = seen | words_by_book[book]
        cumulative[book] = set(seen)

    review = []
    for row in rows:
        book = row["FirstBook"]
        allowed = cumulative[book]
        unknown = []
        for token in tokens(row["ExampleSentence"]):
            if token in FUNCTION_WORDS or token in PROPER_WORDS:
                continue
            if any(lemma in allowed for lemma in candidate_lemmas(token)):
                continue
            unknown.append(token)
        unknown = sorted(set(unknown))
        if unknown:
            review.append({
                "Word": row["Word"],
                "FirstBook": book,
                "ExampleSentence": row["ExampleSentence"],
                "UnknownContentWords": " ".join(unknown),
            })

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Word", "FirstBook", "ExampleSentence", "UnknownContentWords"],
        )
        writer.writeheader()
        writer.writerows(review)

    print(f"Example vocabulary review items: {len(review)}")


if __name__ == "__main__":
    main()
