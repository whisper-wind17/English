#!/usr/bin/env python3
"""Apply reviewed NCE1 lexical facts and LearnerLevel-4 presentation."""
from __future__ import annotations
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"anki"/"klose"
REG=BASE/"master"/"note_registry_extensions.csv"
FACT=BASE/"master"/"nce1_new_fact_overrides.csv"
CONTENT=BASE/"learner"/"nce1_content.csv"
MASTER=BASE/"master"/"vocabulary_master.csv"
LEARNER=BASE/"learner"/"current.csv"
REVIEW=BASE/"review"/"learner_review.csv"
CREATED="klose-nce1-current"
GAP_REASON="nce1-current-new-note-needs-learner-content-and-lexical-facts"


def read(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))


def write(path,fields,rows):
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n");w.writeheader();w.writerows(rows)


def num(nid): return int(nid[2:])


def main():
    active={r["NoteID"].strip() for r in read(REG) if r.get("CreatedSource","").strip()==CREATED and r.get("Status","").strip()=="active"}
    if len(active)!=249: raise SystemExit(f"Expected 249 active NCE1 new identities, got {len(active)}")
    facts=read(FACT); content=read(CONTENT)
    fact={r["NoteID"].strip():r for r in facts}; cont={r["NoteID"].strip():r for r in content}
    if len(facts)!=249 or set(fact)!=active or len(content)!=249 or set(cont)!=active:
        raise SystemExit("NCE1 facts/content do not exactly cover active new identities")

    master=read(MASTER); learner=read(LEARNER); review=read(REVIEW)
    mf=list(master[0]); lf=list(learner[0]); rf=list(review[0])
    mb={r["NoteID"].strip():r for r in master}; lb={r["NoteID"].strip():r for r in learner}
    if not active <= set(mb) or not active <= set(lb): raise SystemExit("NCE1 derived Master/Learner rows missing")
    for nid in active:
        fr=fact[nid]; cr=cont[nid]; m=mb[nid]; l=lb[nid]
        if fr.get("FactStatus","").strip()!="model-reviewed": raise SystemExit(f"Unreviewed NCE1 fact: {nid}")
        if cr.get("ContentStatus","").strip()!="model-curated": raise SystemExit(f"Uncurated NCE1 content: {nid}")
        m["British"]=fr["British"].strip();m["American"]=fr["American"].strip()
        l["ExampleSentence"]=cr["ExampleSentence"].strip();l["ExampleTranslation"]=cr["ExampleTranslation"].strip()
        l["PresentationStatus"]="nce1-content-ready";l["PresentationSource"]="klose:nce1-content-v1"
    master.sort(key=lambda r:num(r["NoteID"]));learner.sort(key=lambda r:num(r["NoteID"]))
    write(MASTER,mf,master);write(LEARNER,lf,learner)

    gap={r.get("NoteID","").strip() for r in review if r.get("Reason","").strip()==GAP_REASON}
    if gap!=active:
        raise SystemExit(f"NCE1 content gap queue mismatch before transition: gap={len(gap)} active={len(active)}")
    review=[r for r in review if r.get("NoteID","").strip() not in active]
    write(REVIEW,rf,review)
    print(f"Applied NCE1 learner presentation: facts={len(active)} content={len(active)} gaps_removed={len(gap)}")


if __name__=="__main__": main()
