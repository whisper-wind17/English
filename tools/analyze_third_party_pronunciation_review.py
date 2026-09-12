#!/usr/bin/env python3
"""Classify pronunciation debt into deterministic low-risk and explicit high-risk review lanes.

This is analysis-only. It never writes Master or review approval. High-risk includes
proper/digit/acronym forms, known heteronyms, duplicate-surface learning units, and
narrow allophones that should not be silently normalized into project IPA style.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'anki' / 'klose'
PREP = BASE / 'third_party_vocabulary' / 'review_preparation'
PACKETS = PREP / 'pronunciation_review_packets'
OUT = PREP / 'pronunciation_high_risk.csv'
BATCH_DIR = PREP / 'pronunciation_high_risk_batches'
MASTER = BASE / 'master' / 'vocabulary_master.csv'

FIELDS = [
    'NoteID','OriginType','ReleaseState','CanonicalWord','SenseLabel','MeaningPrimary',
    'CandidateBritish','CandidateAmerican','RiskFlags','ReviewRiskReasons'
]
KNOWN_HETERONYMS = {
    'bow','close','conduct','content','contract','desert','digest','does','entrance','invalid',
    'lead','live','minute','object','present','produce','project','read','record','refuse',
    'subject','survey','suspect','tear','use','wind','wound'
}
NARROW_MARKERS = {'ɾ':'flap-allophone','ʔ':'glottal-allophone'}
BATCH_SIZE=50


def read_csv(path: Path):
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore',lineterminator='\n'); w.writeheader(); w.writerows(rows)


def main():
    rows=[]
    for p in sorted(PACKETS.glob('batch_*.csv')): rows.extend(read_csv(p))
    master=read_csv(MASTER)
    surfaces=defaultdict(list)
    for r in master:
        surfaces[(r.get('CanonicalWord','').strip().casefold())].append(r)

    high=[]; reasons_count=Counter()
    for r in rows:
        reasons=[]
        flags=set(r.get('RiskFlags','').split())
        if 'digit' in flags: reasons.append('digit')
        if 'proper-case' in flags: reasons.append('proper-case')
        if 'acronym' in flags: reasons.append('acronym')
        word=r.get('CanonicalWord','').strip()
        key=word.casefold()
        if key in KNOWN_HETERONYMS: reasons.append('known-heteronym')
        same=surfaces.get(key,[])
        senses={x.get('SenseLabel','').strip() for x in same}
        if len(same)>1 and len(senses)>1: reasons.append('duplicate-surface-multi-sense')
        candidate=(r.get('CandidateBritish','')+' '+r.get('CandidateAmerican',''))
        for marker,label in NARROW_MARKERS.items():
            if marker in candidate: reasons.append(label)
        if reasons:
            reasons=list(dict.fromkeys(reasons))
            item=dict(r); item['ReviewRiskReasons']=' '.join(reasons); high.append(item)
            reasons_count.update(reasons)

    high.sort(key=lambda r:int(r['NoteID'][2:]))
    write_csv(OUT,high)
    BATCH_DIR.mkdir(parents=True,exist_ok=True)
    for old in BATCH_DIR.glob('batch_*.csv'): old.unlink()
    for i in range(0,len(high),BATCH_SIZE):
        write_csv(BATCH_DIR/f'batch_{i//BATCH_SIZE+1:02d}.csv',high[i:i+BATCH_SIZE])
    print(f'Pronunciation review classification: total={len(rows)} high_risk={len(high)} low_risk={len(rows)-len(high)} high_risk_batches={(len(high)+BATCH_SIZE-1)//BATCH_SIZE}')
    print('High-risk reasons:', dict(reasons_count))
    print('High-risk released=',sum(r.get('ReleaseState')=='released' for r in high),'unreleased=',sum(r.get('ReleaseState')=='unreleased' for r in high))

if __name__=='__main__': main()
