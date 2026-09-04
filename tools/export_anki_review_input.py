#!/usr/bin/env python3
"""Export compact per-book review queues from the generated Anki master CSV."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "anki" / "人教版一年级起点"
MASTER = BASE / "master" / "vocabulary_master.csv"
OUT = BASE / "review_input"

BOOK_ORDER = [
    "1年级上", "1年级下", "2年级上", "2年级下",
    "3年级上", "3年级下", "4年级上", "4年级下",
    "5年级上", "5年级下", "6年级上", "6年级下",
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.csv"):
        old.unlink()

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    with MASTER.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            grouped[row["FirstBook"]].append(row)

    for book in BOOK_ORDER:
        path = OUT / f"{book}.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Word", "MeaningPrimary", "FirstBook"])
            for row in grouped.get(book, []):
                writer.writerow([row["Word"], row["MeaningPrimary"], row["FirstBook"]])
        print(f"{book}: {len(grouped.get(book, []))}")


if __name__ == "__main__":
    main()
