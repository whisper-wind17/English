#!/usr/bin/env python3
"""Independent closure check for reviewed third-party pronunciation evidence."""
from __future__ import annotations
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'anki'/'klose'; TP=BASE/'third_party_vocabulary'; PREP=TP/'review_preparation'
MASTER=BASE/'master'/'vocabulary_master.csv'; ADMISSION=BASE/'learner'/'learning_admission.csv'
OUT=TP/'pronunciation'/'reviewed_pronunciations.csv'; HIGH=PREP/'pronunciation_high_risk.csv'; OV=TP/'pronunciation'/'review_overrides.csv'

def read_csv(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def main():
    master={r['NoteID'].strip():r for r in read_csv(MASTER)}
    allowed={r['NoteID'].strip() for r in read_csv(ADMISSION) if r.get('LearnerProfile','').strip()=='klose' and r.get('LearnerLevel','').strip()=='4' and r.get('Status','').strip()=='allowed'}
    debt={nid for nid in allowed if not master[nid].get('British','').strip() or not master[nid].get('American','').strip()}
    rows=read_csv(OUT); by={r['NoteID'].strip():r for r in rows}; high={r['NoteID'].strip() for r in read_csv(HIGH)}; ov={r['NoteID'].strip():r for r in read_csv(OV)}
    if len(rows)!=616 or len(by)!=616 or set(by)!=debt: raise SystemExit(f'Reviewed pronunciation identity closure failed rows={len(rows)} unique={len(by)} debt={len(debt)}')
    if len(high)!=177 or len(ov)!=7: raise SystemExit(f'Risk/override closure drift high={len(high)} overrides={len(ov)}')
    errors=[]
    for nid,r in by.items():
        m=master[nid]
        if not r.get('British','').strip() or not r.get('American','').strip(): errors.append(f'{nid}: blank IPA')
        if r.get('ReviewerType')!='model': errors.append(f'{nid}: reviewer type')
        if nid in ov:
            o=ov[nid]
            if r.get('ReviewDecision')!='override-candidate' or r.get('British')!=o.get('British') or r.get('American')!=o.get('American'): errors.append(f'{nid}: override drift')
        elif nid in high and r.get('ReviewLane')!='high-risk-reviewed': errors.append(f'{nid}: high-risk lane drift')
        elif nid not in high and r.get('ReviewLane')!='low-risk-deterministic': errors.append(f'{nid}: low-risk lane drift')
        if m.get('British','').strip() and m.get('British','').strip()!=r.get('British','').strip(): errors.append(f'{nid}: would overwrite existing British')
        if m.get('American','').strip() and m.get('American','').strip()!=r.get('American','').strip(): errors.append(f'{nid}: would overwrite existing American')
    if errors:
        print('\n'.join(errors[:100])); raise SystemExit(f'Reviewed pronunciation failed: {len(errors)} errors')
    print(f'Reviewed pronunciation evidence = PASS: rows=616 high_risk=177 low_risk=439 overrides=7')
if __name__=='__main__':main()
