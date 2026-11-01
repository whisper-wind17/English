#!/usr/bin/env python3
"""Diagnostic-only report of pending Klose Vocabulary learner-review fingerprints."""
from __future__ import annotations
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"anki"/"klose"/"learner"/"presentation_review_registry.csv"

def main():
    with REGISTRY.open("r",encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    pending=[
        r for r in rows
        if r.get("LearnerProfile","").strip()=="klose"
        and r.get("LearnerLevel","").strip()=="4"
        and r.get("ReviewStatus","").strip()=="pending"
    ]
    pending.sort(key=lambda r:int(r["NoteID"][2:]))
    print(f"PENDING_REVIEW_COUNT\t{len(pending)}")
    for r in pending:
        print(f"PENDING_REVIEW\t{r['NoteID']}\t{r['ContentFingerprint']}")

if __name__=="__main__": main()
