#!/usr/bin/env python3
"""Classify current pending learner review scope into semantic-risk lanes.

This is an audit aid, not an approval tool. It consumes current fingerprint-bound
review state and emits a compact high-risk view for explicit model adjudication.
"""
from __future__ import annotations

import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'anki'/'klose'
MASTER=BASE/'master'/'vocabulary_master.csv'
LEARNER=BASE/'learner'/'current.csv'
REGISTRY=BASE/'learner'/'presentation_review_registry.csv'
PRON=BASE/'third_party_vocabulary'/'pronunciation'/'reviewed_pronunciations.csv'
OUTDIR=BASE/'third_party_vocabulary'/'review_preparation'
OUT=OUTDIR/'learner_semantic_high_risk.csv'
SUMMARY=OUTDIR/'learner_semantic_review_summary.json'
PROFILE='klose'; LEVEL='4'
TOKEN_RE=re.compile(r"[A-Za-z0-9]+")
FIELDS=['NoteID','ReviewLane','RiskReasons','CanonicalWord','SenseLabel','MeaningPrimary','ExampleSentence','ExampleTranslation','PresentationStatus','PresentationSource']


def read_csv(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def main():
    master_rows=read_csv(MASTER); learner_rows=read_csv(LEARNER); registry_rows=read_csv(REGISTRY)
    mb={r['NoteID'].strip():r for r in master_rows}; lb={r['NoteID'].strip():r for r in learner_rows}
    pending={r['NoteID'].strip():r for r in registry_rows if r.get('LearnerProfile','').strip()==PROFILE and r.get('LearnerLevel','').strip()==LEVEL and r.get('ReviewStatus','').strip()=='pending'}
    pron={r['NoteID'].strip() for r in read_csv(PRON)}
    surfaces=defaultdict(list)
    for r in master_rows: surfaces[r.get('CanonicalWord','').strip().casefold()].append(r)
    high=[]; lane_counts=Counter(); reason_counts=Counter()
    for nid in sorted(pending,key=lambda x:int(x[2:])):
        m=mb[nid]; l=lb[nid]; word=m.get('CanonicalWord','').strip(); sense=m.get('SenseLabel','').strip(); meaning=l.get('MeaningPrimary','').strip(); sent=l.get('ExampleSentence','').strip()
        released=m.get('Released','').strip()=='yes'
        is_new=1195<=int(nid[2:])<=3015
        reasons=[]
        same=surfaces[word.casefold()]; senses={x.get('SenseLabel','').strip() for x in same}
        if len(same)>1 and len(senses)>1: reasons.append('duplicate-surface-multi-sense')
        if re.search(r'\d',word): reasons.append('digit-form')
        letters=''.join(ch for ch in word if ch.isalpha())
        if len(letters)>=2 and letters.isupper(): reasons.append('acronym-or-allcaps')
        if any(ch in sense+meaning for ch in '（）()'): reasons.append('sense-note-parenthetical')
        if len(TOKEN_RE.findall(sent))>10: reasons.append('long-example')
        if sense.count('；')+sense.count(';')>=2: reasons.append('multi-meaning-label')
        if not is_new and not released: lane='reuse-guardrail'
        elif released: lane='released-invalidated'
        elif reasons: lane='new-high-risk'
        else: lane='new-low-risk'
        lane_counts[lane]+=1; reason_counts.update(reasons)
        if lane in {'released-invalidated','reuse-guardrail','new-high-risk'}:
            item={'NoteID':nid,'ReviewLane':lane,'RiskReasons':' '.join(reasons),'CanonicalWord':word,'SenseLabel':sense,'MeaningPrimary':meaning,'ExampleSentence':sent,'ExampleTranslation':l.get('ExampleTranslation','').strip(),'PresentationStatus':l.get('PresentationStatus','').strip(),'PresentationSource':l.get('PresentationSource','').strip()}
            high.append(item)
    OUTDIR.mkdir(parents=True,exist_ok=True)
    with OUT.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator='\n');w.writeheader();w.writerows(high)
    summary={'PendingTotal':len(pending),'LaneCounts':dict(lane_counts),'RiskReasonCounts':dict(reason_counts),'ReviewedPronunciationPendingOverlap':len(set(pending)&pron),'ExplicitSemanticReviewRows':len(high)}
    SUMMARY.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if len(pending)!=2059: raise SystemExit(f'Expected 2059 current pending rows, got {len(pending)}')
    if lane_counts['released-invalidated']!=78 or lane_counts['reuse-guardrail']!=160: raise SystemExit(f'Known review lane drift: {dict(lane_counts)}')

if __name__=='__main__':main()
