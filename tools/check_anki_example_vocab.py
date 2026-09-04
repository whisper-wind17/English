#!/usr/bin/env python3
"""Check examples for vocabulary explicitly introduced in a later textbook.

The source XLSX vocabulary lists are not exhaustive: ordinary words such as
"yesterday" or "month" may appear in textbook sentences without being listed as
new vocabulary. Therefore this checker does NOT call every unlisted token
"out-of-grade". It flags only a stronger, auditable condition: an example uses a
content word whose first explicit vocabulary-list occurrence is in a later book.
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
    "please", "yes", "no", "let", "lets", "let's", "don't", "doesn't", "didn't",
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
    if len(token) >= 4 and token.endswith("es"):
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
        "met": "meet", "spent": "spend", "began": "begin", "became": "become",
    }
    if token in irregular:
        out.add(irregular[token])
    return out


def lexical_forms(text: str) -> set[str]:
    forms: set[str] = set()
    for token in tokens(text):
        forms.update(candidate_lemmas(token))
    return forms


def main() -> None:
    with MASTER.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    # Map every normalized lexical form found in a listed vocabulary item to
    # the earliest book in which that vocabulary item is explicitly introduced.
    first_index: dict[str, int] = {}
    first_book: dict[str, str] = {}
    for row in rows:
        idx = BOOK_INDEX[row["FirstBook"]]
        for form in lexical_forms(row["Word"]):
            if form not in first_index or idx < first_index[form]:
                first_index[form] = idx
                first_book[form] = row["FirstBook"]

    review = []
    for row in rows:
        current_idx = BOOK_INDEX[row["FirstBook"]]
        future: dict[str, str] = {}
        for token in tokens(row["ExampleSentence"]):
            if token in FUNCTION_WORDS:
                continue
            matches = [
                lemma for lemma in candidate_lemmas(token)
                if lemma in first_index
            ]
            if not matches:
                # The vocabulary spreadsheets are not exhaustive, so there is
                # no evidence that an unlisted ordinary word is a future word.
                continue
            earliest = min(first_index[lemma] for lemma in matches)
            if earliest > current_idx:
                lemma = min(
                    (x for x in matches if first_index[x] == earliest),
                    key=len,
                )
                future[token] = first_book[lemma]

        if future:
            review.append({
                "Word": row["Word"],
                "FirstBook": row["FirstBook"],
                "ExampleSentence": row["ExampleSentence"],
                "FutureVocabulary": " ".join(
                    f"{token}->{book}" for token, book in sorted(future.items())
                ),
            })

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Word", "FirstBook", "ExampleSentence", "FutureVocabulary"],
        )
        writer.writeheader()
        writer.writerows(review)

    print(f"Future-vocabulary example review items: {len(review)}")


if __name__ == "__main__":
    main()
