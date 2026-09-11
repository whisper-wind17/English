#!/usr/bin/env python3
from __future__ import annotations
import csv, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'anki'/'klose'/'third_party_vocabulary'/'learner'
CAND=BASE/'stable_presentation_candidates.csv'
REVIEWED=BASE/'content_reviewed'
TOKEN_RE=re.compile(r"[A-Za-z0-9]+")

def read_csv(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def toks(s): return TOKEN_RE.findall((s or '').casefold())

def contains_subseq(hay, needle):
    if not needle: return False
    return any(hay[i:i+len(needle)]==needle for i in range(0,len(hay)-len(needle)+1))

def main():
    candidates=read_csv(CAND)
    expected={r['NoteID']:r for r in candidates}
    rows=[]
    files=sorted(REVIEWED.glob('batch_*.csv'))
    if len(files)!=19: raise SystemExit(f'Expected 19 reviewed batches, got {len(files)}')
    for p in files: rows.extend(read_csv(p))
    by={}
    errors=[]
    duplicate_examples={}
    for r in rows:
        nid=r.get('NoteID','').strip()
        if not nid or nid in by: errors.append(f'{nid}: duplicate/blank NoteID'); continue
        by[nid]=r
        sent=r.get('ExampleSentence','').strip(); trans=r.get('ExampleTranslation','').strip()
        if not sent or not trans: errors.append(f'{nid}: blank bilingual example'); continue
        if r.get('ContentStatus','').strip()!='model-curated' or r.get('ContentSource','').strip()!='third-party-learner-content-v1':
            errors.append(f'{nid}: invalid content provenance')
        if len(toks(sent))>14: errors.append(f'{nid}: example too long ({len(toks(sent))} tokens)')
        key=' '.join(toks(sent))
        if key in duplicate_examples: errors.append(f'{nid}: duplicate example with {duplicate_examples[key]}')
        duplicate_examples[key]=nid
        cand=expected.get(nid)
        if cand is None: errors.append(f'{nid}: not a presentation candidate'); continue
        target=toks(cand.get('CanonicalWord',''))
        if not contains_subseq(toks(sent),target): errors.append(f'{nid}: target form missing from example: {cand.get("CanonicalWord")}')
    missing=sorted(set(expected)-set(by)); extra=sorted(set(by)-set(expected))
    if missing or extra: errors.append(f'coverage mismatch missing={len(missing)} extra={len(extra)} examples={(missing+extra)[:20]}')
    if len(rows)!=1821: errors.append(f'expected 1821 reviewed rows, got {len(rows)}')
    if errors:
        print('\n'.join(errors[:100])); raise SystemExit(f'Third-party learner content failed: {len(errors)} errors')
    conflicts=sum(r.get('BritishEvidenceStatus')=='conflicting-evidence' or r.get('AmericanEvidenceStatus')=='conflicting-evidence' for r in candidates)
    ipa_missing=sum(not r.get('BritishCandidate','').strip() or not r.get('AmericanCandidate','').strip() for r in candidates)
    print(f'Third-party learner content OK: rows={len(rows)} unique_examples={len(duplicate_examples)} pronunciation_conflict_rows={conflicts} pronunciation_missing_rows={ipa_missing}')

if __name__=='__main__': main()
