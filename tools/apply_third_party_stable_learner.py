#!/usr/bin/env python3
from __future__ import annotations
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
K=ROOT/'anki'/'klose'
TP=K/'third_party_vocabulary'/'learner'
MASTER=K/'master'/'vocabulary_master.csv'
LEARNER=K/'learner'/'current.csv'
ADMISSION=K/'learner'/'learning_admission.csv'
CAND=TP/'stable_presentation_candidates.csv'
PLAN=TP/'stable_learning_admission_plan.csv'
REVIEWED=TP/'content_reviewed'
CORRECTIONS=TP/'content_corrections.csv'

MASTER_FIELDS=['NoteID','CanonicalWord','MatchKey','SenseLabel','Word','British','American','MeaningPrimary','MeaningRaw','FirstSource','FirstSourceBook','FirstGrade','FirstSemester','Sources','SourceBooks','Released','Tags']
LEARNER_FIELDS=['NoteID','LearnerProfile','LearnerLevel','PromptHint','ExampleSentence','ExampleTranslation','PresentationStatus','PresentationSource']
ADMISSION_FIELDS=['LearnerProfile','LearnerLevel','NoteID','Stage','Status','LearningTag','LearningOrder','Reason']

def read_csv(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def write_csv(p, fields, rows):
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore',lineterminator='\n'); w.writeheader(); w.writerows(rows)

def main():
    candidates=read_csv(CAND)
    if len(candidates)!=1821: raise SystemExit(f'Expected 1821 candidates, got {len(candidates)}')
    reviewed=[]
    for p in sorted(REVIEWED.glob('batch_*.csv')): reviewed.extend(read_csv(p))
    content={r['NoteID']:dict(r) for r in reviewed}
    if len(content)!=1821: raise SystemExit(f'Expected 1821 reviewed content rows, got {len(content)}')
    corrections=read_csv(CORRECTIONS)
    if len(corrections)!=16 or len({r['NoteID'] for r in corrections})!=16: raise SystemExit('Expected 16 unique content corrections')
    for c in corrections:
        nid=c['NoteID'].strip()
        if nid not in content: raise SystemExit(f'Content correction outside reviewed scope: {nid}')
        content[nid]['ExampleSentence']=c['ExampleSentence'].strip()
        content[nid]['ExampleTranslation']=c['ExampleTranslation'].strip()

    master=read_csv(MASTER); master_by={r['NoteID']:r for r in master}
    learner=read_csv(LEARNER); learner_by={r['NoteID']:r for r in learner}
    admission=read_csv(ADMISSION); adm_by={(r['LearnerProfile'],r['LearnerLevel'],r['NoteID']):r for r in admission}

    added_master=added_learner=0
    for c in candidates:
        nid=c['NoteID'].strip()
        if nid in master_by: raise SystemExit(f'New third-party Stable Note already exists in derived Master: {nid}')
        british=c.get('BritishCandidate','').strip() if c.get('BritishEvidenceStatus','').strip()=='consistent' else ''
        american=c.get('AmericanCandidate','').strip() if c.get('AmericanEvidenceStatus','').strip()=='consistent' else ''
        m={
            'NoteID':nid,'CanonicalWord':c['CanonicalWord'].strip(),'MatchKey':c['MatchKey'].strip(),'SenseLabel':c['SenseLabel'].strip(),
            'Word':c['CanonicalWord'].strip(),'British':british,'American':american,'MeaningPrimary':c['MeaningPrimary'].strip(),
            'MeaningRaw':c.get('DefinitionEvidence','').strip(),'FirstSource':'third-party-vocabulary','FirstSourceBook':'external-evidence-corpus',
            'FirstGrade':'','FirstSemester':'','Sources':'third-party-vocabulary','SourceBooks':'third-party-vocabulary::external-evidence-corpus',
            'Released':'no','Tags':'learner::klose::level::4 source::third-party-vocabulary provenance::external-unverified-edition'
        }
        master.append(m); master_by[nid]=m; added_master+=1
        if nid in learner_by: raise SystemExit(f'New third-party Stable Note already exists in learner current: {nid}')
        cr=content[nid]
        l={'NoteID':nid,'LearnerProfile':'klose','LearnerLevel':'4','PromptHint':'','ExampleSentence':cr['ExampleSentence'].strip(),
           'ExampleTranslation':cr['ExampleTranslation'].strip(),'PresentationStatus':'model-curated-pending-review','PresentationSource':'third-party-learner-content-v1'}
        learner.append(l); learner_by[nid]=l; added_learner+=1

    plan=read_csv(PLAN)
    if len(plan)!=2720: raise SystemExit(f'Expected 2720 admission plan rows, got {len(plan)}')
    changed_adm=0; new_adm=0
    for p in plan:
        key=(p['LearnerProfile'].strip(),p['LearnerLevel'].strip(),p['NoteID'].strip())
        cur=adm_by.get(key)
        if p['CurrentStatus'].strip()=='allowed':
            if cur is None or cur.get('Status','').strip()!='allowed': raise SystemExit(f'Planned preserve-existing admission missing/drifted: {key}')
            if cur.get('LearningOrder','').strip()!=p['ProposedLearningOrder'].strip(): raise SystemExit(f'Existing LearningOrder drift: {key}')
            continue
        row={'LearnerProfile':key[0],'LearnerLevel':key[1],'NoteID':key[2],'Stage':'stage::third-party-primary','Status':'allowed',
             'LearningTag':p['ProposedLearningTag'].strip(),'LearningOrder':p['ProposedLearningOrder'].strip(),'Reason':'resolved-third-party-learner-identity'}
        if cur is None:
            admission.append(row); adm_by[key]=row; new_adm+=1
        else:
            cur.update(row); changed_adm+=1

    master.sort(key=lambda r:int(r['NoteID'][2:]))
    learner.sort(key=lambda r:int(r['NoteID'][2:]))
    admission.sort(key=lambda r:(r['LearnerProfile'],int(r['LearnerLevel']),int(r['NoteID'][2:])))
    write_csv(MASTER,MASTER_FIELDS,master); write_csv(LEARNER,LEARNER_FIELDS,learner); write_csv(ADMISSION,ADMISSION_FIELDS,admission)
    print(f'Third-party Stable learner materialized: master_added={added_master} learner_added={added_learner} corrections={len(corrections)} admission_new={new_adm} admission_promoted={changed_adm} plan={len(plan)}')

if __name__=='__main__': main()
