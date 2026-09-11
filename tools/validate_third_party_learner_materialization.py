#!/usr/bin/env python3
"""Independent Completion Recheck for third-party learner/admission materialization."""
from __future__ import annotations
import csv, io
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
K=ROOT/'anki'/'klose'
TP=K/'third_party_vocabulary'/'learner'

def read_csv(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def reviewed_content():
    rows=[]
    for p in sorted((TP/'content_reviewed').glob('batch_*.csv')): rows.extend(read_csv(p))
    by={r['NoteID']:dict(r) for r in rows}
    for c in read_csv(TP/'content_corrections.csv'):
        by[c['NoteID']]['ExampleSentence']=c['ExampleSentence'].strip()
        by[c['NoteID']]['ExampleTranslation']=c['ExampleTranslation'].strip()
    return by

def anki_data_count(p):
    data=[]
    with p.open('r',encoding='utf-8',newline='') as f:
        for line in f:
            if line.startswith('#') or not line.strip(): continue
            data.append(line)
    return sum(1 for _ in csv.reader(io.StringIO(''.join(data))))

def main():
    candidates=read_csv(TP/'stable_presentation_candidates.csv')
    cand={r['NoteID']:r for r in candidates}
    new_ids=set(cand)
    expected_ids={f'KV{i:06d}' for i in range(1195,3016)}
    if new_ids!=expected_ids or len(candidates)!=1821: raise SystemExit('Third-party candidate Stable ID set drift')

    master=read_csv(K/'master'/'vocabulary_master.csv'); mb={r['NoteID']:r for r in master}
    learner=read_csv(K/'learner'/'current.csv'); lb={r['NoteID']:r for r in learner}
    admission=read_csv(K/'learner'/'learning_admission.csv'); ab={(r['LearnerProfile'],r['LearnerLevel'],r['NoteID']):r for r in admission}
    review=read_csv(K/'learner'/'presentation_review_registry.csv'); rb={(r['LearnerProfile'],r['LearnerLevel'],r['NoteID']):r for r in review}
    content=reviewed_content()
    errors=[]

    missing_master=sorted(new_ids-set(mb)); missing_learner=sorted(new_ids-set(lb))
    if missing_master: errors.append(f'new Stable Master rows missing={len(missing_master)}')
    if missing_learner: errors.append(f'new Stable learner rows missing={len(missing_learner)}')
    pronunciation_conflict=pronunciation_missing=ipa_debt=0
    for nid in sorted(new_ids):
        c=cand[nid]; m=mb.get(nid); l=lb.get(nid)
        if m is None or l is None: continue
        if m.get('FirstSource')!='third-party-vocabulary' or m.get('FirstSourceBook')!='external-evidence-corpus': errors.append(f'{nid}: bad external provenance inventory')
        if m.get('FirstGrade','').strip() or m.get('FirstSemester','').strip(): errors.append(f'{nid}: invented Source Grade/Semester')
        if m.get('Released')!='no': errors.append(f'{nid}: prematurely released')
        if 'provenance::external-unverified-edition' not in m.get('Tags','').split(): errors.append(f'{nid}: missing external provenance tag')
        debt=False
        for side,status_field,cand_field in [('British','BritishEvidenceStatus','BritishCandidate'),('American','AmericanEvidenceStatus','AmericanCandidate')]:
            status=c.get(status_field,'').strip(); candidate=c.get(cand_field,'').strip(); actual=m.get(side,'').strip()
            if status=='consistent':
                if actual!=candidate: errors.append(f'{nid}: {side} candidate drift')
            else:
                if actual: errors.append(f'{nid}: unsafe {side} pronunciation promoted from {status}')
                debt=True
        if 'conflicting-evidence' in {c.get('BritishEvidenceStatus'),c.get('AmericanEvidenceStatus')}: pronunciation_conflict+=1
        if not c.get('BritishCandidate','').strip() or not c.get('AmericanCandidate','').strip(): pronunciation_missing+=1
        if debt: ipa_debt+=1
        cr=content[nid]
        if l.get('LearnerProfile')!='klose' or l.get('LearnerLevel')!='4': errors.append(f'{nid}: learner profile/level drift')
        if l.get('ExampleSentence')!=cr.get('ExampleSentence') or l.get('ExampleTranslation')!=cr.get('ExampleTranslation'): errors.append(f'{nid}: reviewed content drift')
        if l.get('PresentationStatus')!='model-curated-pending-review' or l.get('PresentationSource')!='third-party-learner-content-v1': errors.append(f'{nid}: presentation lifecycle drift')
        rr=rb.get(('klose','4',nid))
        if rr is None or not rr.get('ContentFingerprint','').strip() or rr.get('ReviewStatus')!='pending': errors.append(f'{nid}: new presentation must be fingerprint-bound pending')

    plan=read_csv(TP/'stable_learning_admission_plan.csv')
    if len(plan)!=2720: errors.append(f'admission plan count={len(plan)}')
    preserve=mutated=0
    for p in plan:
        key=(p['LearnerProfile'].strip(),p['LearnerLevel'].strip(),p['NoteID'].strip()); a=ab.get(key)
        if a is None: errors.append(f'{key[2]}: canonical admission missing'); continue
        if a.get('Status')!='allowed' or a.get('LearningOrder')!=p.get('ProposedLearningOrder'): errors.append(f'{key[2]}: admission/order drift')
        if p.get('AdmissionAction')=='preserve-allowed':
            preserve+=1
            if a.get('LearningOrder')!=p.get('CurrentLearningOrder'): errors.append(f'{key[2]}: preserved order changed')
        else:
            mutated+=1
            if a.get('Stage')!='stage::third-party-primary' or a.get('LearningTag')!=p.get('ProposedLearningTag'): errors.append(f'{key[2]}: third-party admission metadata drift')
    allowed=[r for r in admission if r.get('LearnerProfile')=='klose' and r.get('LearnerLevel')=='4' and r.get('Status')=='allowed']
    orders=[r.get('LearningOrder','') for r in allowed]
    expected_orders=[f'{i:06d}' for i in range(1,len(allowed)+1)]
    if sorted(orders)!=expected_orders: errors.append(f'allowed LearningOrder is not unique/continuous 000001..{len(allowed):06d}')

    source_ext=read_csv(K/'master'/'source_identity_extensions.csv')
    leaked=sorted(new_ids & {r.get('NoteID','').strip() for r in source_ext})
    if leaked: errors.append(f'unverified third-party IDs leaked into textbook source map={len(leaked)}')
    if len(read_csv(K/'master'/'release_registry.csv'))+len(read_csv(K/'master'/'release_registry_extensions.csv'))!=972: errors.append('release registry count changed from 972')
    study_count=len(read_csv(K/'publish'/'study.csv'))
    anki_count=anki_data_count(K/'publish'/'anki-import.csv')
    if study_count!=972 or anki_count!=972: errors.append(f'publish changed prematurely study={study_count} anki={anki_count}')

    if errors:
        for e in errors[:100]: print(e)
        raise SystemExit(f'Third-party learner materialization failed: {len(errors)} errors')
    print(f'Third-party learner materialization OK: master_new=1821 learner_new=1821 plan=2720 preserve={preserve} new_or_promoted={mutated} allowed_total={len(allowed)} review_new_pending=1821 pronunciation_conflict_rows={pronunciation_conflict} pronunciation_missing_candidate_rows={pronunciation_missing} pronunciation_debt_rows={ipa_debt} release=972 publish=972 textbook_source_leak=0')

if __name__=='__main__': main()
