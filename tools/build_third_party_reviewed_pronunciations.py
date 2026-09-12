#!/usr/bin/env python3
"""Materialize the reviewed pronunciation sidecar from prepared debt packets.

All 616 currently allowed Notes with missing UK/US IPA are covered. Low-risk and
accepted high-risk rows preserve the deterministic eSpeak-ng candidate; explicitly
reviewed exceptions are taken from review_overrides.csv. This writes evidence only,
not Vocabulary Master.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'anki'/'klose'
TP=BASE/'third_party_vocabulary'
PREP=TP/'review_preparation'
PACKETS=PREP/'pronunciation_review_packets'
HIGH=PREP/'pronunciation_high_risk.csv'
OVERRIDES=TP/'pronunciation'/'review_overrides.csv'
OUT=TP/'pronunciation'/'reviewed_pronunciations.csv'
FIELDS=['NoteID','CanonicalWord','British','American','ReviewLane','ReviewDecision','ReviewerType','EvidenceSource','EvidenceDetail','EvidenceVersion','ReviewNote']


def read_csv(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write_csv(p,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(rows)

def main():
    packet=[]
    for p in sorted(PACKETS.glob('batch_*.csv')): packet.extend(read_csv(p))
    if len(packet)!=616: raise SystemExit(f'Expected 616 pronunciation debt packets, got {len(packet)}')
    high={r['NoteID'].strip():r for r in read_csv(HIGH)}
    if len(high)!=177: raise SystemExit(f'Expected 177 high-risk rows, got {len(high)}')
    overrides={r['NoteID'].strip():r for r in read_csv(OVERRIDES)}
    if len(overrides)!=7: raise SystemExit(f'Expected 7 explicit pronunciation overrides, got {len(overrides)}')
    packet_by={r['NoteID'].strip():r for r in packet}
    unknown=set(overrides)-set(packet_by)
    if unknown: raise SystemExit(f'Pronunciation override outside debt scope: {sorted(unknown)}')
    if not set(overrides).issubset(set(high)):
        raise SystemExit('Every explicit override must belong to high-risk lane')

    rows=[]
    for p in sorted(packet,key=lambda r:int(r['NoteID'][2:])):
        nid=p['NoteID'].strip(); ov=overrides.get(nid); is_high=nid in high
        if ov:
            british=ov['British'].strip(); american=ov['American'].strip()
            lane='high-risk-explicit'
            decision='override-candidate'
            source=ov['EvidenceSource'].strip(); detail=ov['EvidenceDetail'].strip(); note=ov['ReviewRationale'].strip()
        else:
            british=p['CandidateBritish'].strip(); american=p['CandidateAmerican'].strip()
            lane='high-risk-reviewed' if is_high else 'low-risk-deterministic'
            decision='accept-candidate'
            source='espeak-ng-reviewed'
            detail=(p.get('CandidateEngineVersion','').strip()+'; '+p.get('CandidateBritishVoice','').strip()+'/'+p.get('CandidateAmericanVoice','').strip()).strip('; ')
            note=('Independent model review found no sense/pronunciation conflict in flagged lane.' if is_high
                  else 'Deterministic candidate passed structural and low-risk pronunciation gates.')
        if not british or not american: raise SystemExit(f'Blank reviewed pronunciation: {nid}')
        rows.append({'NoteID':nid,'CanonicalWord':p['CanonicalWord'].strip(),'British':british,'American':american,
                     'ReviewLane':lane,'ReviewDecision':decision,'ReviewerType':'model','EvidenceSource':source,
                     'EvidenceDetail':detail,'EvidenceVersion':p.get('CandidateEngineVersion','').strip(),'ReviewNote':note})
    write_csv(OUT,rows)
    print(f'Reviewed pronunciation evidence built: rows={len(rows)} low_risk={sum(r["ReviewLane"]=="low-risk-deterministic" for r in rows)} high_risk={sum(r["ReviewLane"]!="low-risk-deterministic" for r in rows)} overrides={sum(r["ReviewDecision"]=="override-candidate" for r in rows)}')

if __name__=='__main__':main()
