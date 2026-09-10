#!/usr/bin/env python3
from __future__ import annotations
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'anki'/'klose'
MASTER=BASE/'master'/'vocabulary_master.csv'
REGISTRY=BASE/'master'/'note_registry_extensions.csv'
LEARNER=BASE/'learner'/'current.csv'
ADMISSION=BASE/'learner'/'learning_admission.csv'
REVIEW=BASE/'learner'/'presentation_review_registry.csv'
OUT=BASE/'review'/'vocabulary_pending_focus_audit.csv'
FIELDS=['NoteID','Class','Released','Stage','LearningOrder','CanonicalWord','Word','MeaningPrimary','British','American','ExampleSentence','ExampleTranslation','PresentationStatus','ContentFingerprint','ReviewNote']

def read(path):
    with path.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def main():
    master={r['NoteID']:r for r in read(MASTER)}
    learner={r['NoteID']:r for r in read(LEARNER)}
    admission={r['NoteID']:r for r in read(ADMISSION) if r.get('LearnerProfile')=='klose' and r.get('LearnerLevel')=='4'}
    review={r['NoteID']:r for r in read(REVIEW) if r.get('LearnerProfile')=='klose' and r.get('LearnerLevel')=='4'}
    ext={r['NoteID']:r for r in read(REGISTRY)}
    pending={nid for nid,r in review.items() if r.get('ReviewStatus')=='pending'}
    rows=[]
    counts={}
    for nid in sorted(pending):
        m=master[nid]; l=learner[nid]; a=admission.get(nid,{})
        e=ext.get(nid,{})
        active_new=(e.get('CreatedSource')=='klose-grade5-6-current' and e.get('Status')=='active')
        if active_new:
            cls='grade5-6-new-active'
        elif m.get('Released')=='yes':
            cls='released-fingerprint-invalidated'
        else:
            cls='grade5-6-reused-unreleased'
        counts[cls]=counts.get(cls,0)+1
        if cls=='grade5-6-new-active':
            continue
        rows.append({
          'NoteID':nid,'Class':cls,'Released':m.get('Released',''),'Stage':a.get('Stage',''),'LearningOrder':a.get('LearningOrder',''),
          'CanonicalWord':m.get('CanonicalWord',''),'Word':m.get('Word',''),'MeaningPrimary':m.get('MeaningPrimary',''),'British':m.get('British',''),'American':m.get('American',''),
          'ExampleSentence':l.get('ExampleSentence',''),'ExampleTranslation':l.get('ExampleTranslation',''),'PresentationStatus':l.get('PresentationStatus',''),
          'ContentFingerprint':review[nid].get('ContentFingerprint',''),'ReviewNote':review[nid].get('ReviewNote','')})
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    print(f'pending_total={len(pending)} classes={counts} focus_rows={len(rows)}')
    if len(pending)!=343 or counts.get('grade5-6-new-active')!=288 or len(rows)!=55:
        raise SystemExit('Unexpected pending decomposition')
if __name__=='__main__':main()
