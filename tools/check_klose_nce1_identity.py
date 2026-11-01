#!/usr/bin/env python3
"""Validate durable NCE1 identity, fact and learner-content closure."""
from __future__ import annotations
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"anki"/"klose"
SRC=BASE/"source_reference"/"new_concept_english_1_staging"/"vocabulary-smart-2022.csv"
DEC=BASE/"review"/"nce1_reconciliation"/"identity_decisions.csv"
REG=BASE/"master"/"note_registry_extensions.csv"
MAP=BASE/"master"/"source_identity_extensions.csv"
MIG=BASE/"master"/"identity_migrations.csv"
FACT=BASE/"master"/"nce1_new_fact_overrides.csv"
CONTENT=BASE/"learner"/"nce1_content.csv"
CREATED="klose-nce1-current"
SID="new_concept_english_1"; EDITION="2022-smart-isbn-9787521336702"


def read(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))


def main():
    for p in (SRC,DEC,REG,MAP,MIG,FACT,CONTENT):
        if not p.exists(): raise SystemExit(f"Missing NCE1 identity input: {p.relative_to(ROOT)}")
    src=read(SRC); dec=read(DEC); reg=read(REG); maps=read(MAP); mig=read(MIG)
    facts=read(FACT); content=read(CONTENT)
    if len(src)!=906: raise SystemExit(f"NCE1 source drift: {len(src)}")
    covered=[]; new_groups=set(); reused=set(); morph=[]
    for d in dec:
        orders=[x.strip() for x in d.get("OccurrenceOrders","").split(" || ") if x.strip()]
        if d["Decision"]=="new-stable-identity":
            if not d.get("DecisionIdentityGroup","").strip(): raise SystemExit(f"Missing new group: {d}")
            new_groups.add(d["DecisionIdentityGroup"].strip()); covered+=orders
        elif d["Decision"]=="reuse-existing":
            if not d.get("DecisionNoteID","").strip(): raise SystemExit(f"Missing reuse NoteID: {d}")
            reused.add(d["DecisionNoteID"].strip()); covered+=orders
        elif d["Decision"]=="morphology-only":
            morph+=orders; covered+=orders
        else: raise SystemExit(f"Unexpected NCE1 decision: {d.get('Decision')!r}")
    expected=[f"{i:04d}" for i in range(1,907)]
    if sorted(covered,key=int)!=expected or len(covered)!=906:
        raise SystemExit("NCE1 decision occurrence coverage is not exactly 0001..0906")

    active_new={
        r["NoteID"].strip():r for r in reg
        if r.get("CreatedSource","").strip()==CREATED and r.get("Status","").strip()=="active"
    }
    merged={
        r["NoteID"].strip():r for r in reg
        if r.get("CreatedSource","").strip()==CREATED and r.get("Status","").strip()=="merged"
    }
    group_to_id={
        r["PrimaryOriginKey"].strip().removeprefix(CREATED+"|"):nid
        for nid,r in active_new.items()
    }
    if set(group_to_id)!=new_groups:
        raise SystemExit(f"NCE1 active identity groups drift: registry={len(group_to_id)} decisions={len(new_groups)}")
    if len(active_new)!=249 or len(merged)!=6 or len(morph)!=4:
        raise SystemExit(f"NCE1 identity counts drift: active={len(active_new)} merged={len(merged)} morph={len(morph)}")
    approved_merges={
        r["NoteID"].strip():r["TargetNoteID"].strip() for r in mig
        if r.get("MigrationType","").strip()=="identity-merge-dedup"
        and r.get("Status","").strip()=="approved"
        and r.get("MigrationID","").startswith("MIG-20261101-NCE1-DEDUP-")
    }
    if set(approved_merges)!=set(merged):
        raise SystemExit(f"NCE1 merged IDs must equal approved pre-release migrations: {approved_merges} vs {set(merged)}")

    nce_maps=[
        r for r in maps if r.get("SourceID","").strip()==SID and r.get("SourceEdition","").strip()==EDITION
        and r.get("Status","").strip()=="confirmed"
    ]
    if len(nce_maps)!=902: raise SystemExit(f"NCE1 confirmed source mappings drift: {len(nce_maps)}")
    registry_active={r["NoteID"].strip() for r in reg if r.get("Status","").strip()=="active"}
    # Reused Notes may live in legacy registry; only reject provisional merged identities here.
    if any(r["NoteID"].strip() in merged for r in nce_maps):
        raise SystemExit("NCE1 source mapping references merged provisional identity")

    fact_ids=[r["NoteID"].strip() for r in facts]
    content_ids=[r["NoteID"].strip() for r in content]
    if len(fact_ids)!=249 or len(set(fact_ids))!=249 or set(fact_ids)!=set(active_new):
        raise SystemExit("NCE1 fact coverage must equal active new identities")
    if len(content_ids)!=249 or len(set(content_ids))!=249 or set(content_ids)!=set(active_new):
        raise SystemExit("NCE1 learner content coverage must equal active new identities")
    for r in facts:
        if r.get("FactStatus","").strip()!="model-reviewed" or not r.get("British","").strip() or not r.get("American","").strip():
            raise SystemExit(f"Invalid NCE1 fact row: {r}")
    for r in content:
        if r.get("ContentStatus","").strip()!="model-curated" or not r.get("ExampleSentence","").strip() or not r.get("ExampleTranslation","").strip():
            raise SystemExit(f"Invalid NCE1 learner content: {r}")

    print(f"NCE1 identity OK: decisions={len(dec)} source=906 mapped=902 morphology=4 new_active=249 merged=6 reused={len(reused)} content=249")


if __name__=="__main__": main()
