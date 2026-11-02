"""Validate explicit, fingerprint-bound NCE1 review batches; never approve content.

Raw source facts stay immutable. Schema 1 binds photographed source meanings.
Schema 2 additionally binds a separate, explicitly reviewed lesson-sense record
for the legacy-reference suffix. Neither a string match nor a source name grants
identity or release approval.
"""
from __future__ import annotations
import csv
import hashlib
import json
import re
from pathlib import Path
from klose_current_policy import unit_fingerprint

BASE = Path(__file__).resolve().parents[1] / 'anki/klose'
SOURCE_ID = 'new_concept_english_1'
EDITION = '2022-smart-isbn-9787521336702'
IDENTITY_FIELDS = ('CanonicalWord','MatchKey','SenseLabel','PrimaryOriginKey','CreatedSource','CreatedSourceBook','Status')

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))

def source_fingerprint(row):
    return hashlib.sha256(json.dumps(row,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _check_digest(path, expected):
    if not isinstance(expected,str) or len(expected)!=64 or _digest(path)!=expected:
        raise SystemExit(f'NCE1 sealed review input changed: {path.name}')

def review_batches():
    paths=sorted(p for p in (BASE/'nce1').glob('batch_*.json') if re.fullmatch(r'batch_\d{3}\.json',p.name))
    if not paths:raise SystemExit('NCE1 has no explicit reviewed batch')
    return [(p,json.loads(p.read_text(encoding='utf-8'))) for p in paths]

def reviewed_state(*, require_allocated=True):
    source_path=BASE/'source_reference/new_concept_english_1_staging/vocabulary-smart-2022.csv'
    source=read(source_path)
    sources={f"nce1-o{int(r['CurriculumOrder']):04d}|{r['Entry'].casefold()}":r for r in source}
    if len(sources)!=len(source):raise SystemExit('Duplicate NCE1 source coordinates')
    registry={r['NoteID']:r for name in ('note_registry.csv','note_registry_extensions.csv') for r in read(BASE/'master'/name)}
    proposed_all={};mapped={};next_order=1
    for path,manifest in review_batches():
        stem=path.stem
        if manifest.get('Status')!='identity-reviewed' or manifest.get('SourceID')!=SOURCE_ID or manifest.get('SourceEdition')!=EDITION:
            raise SystemExit('NCE1 reviewed batch identity/status is invalid')
        schema=manifest.get('SchemaVersion')
        if schema not in (1,2):raise SystemExit('Unsupported NCE1 review schema')
        note_path=BASE/f'nce1/learner/{stem}_new_notes.csv'
        decision_path=BASE/f'nce1/identity_decisions/{stem}.csv'
        new_rows=read(note_path);decisions=read(decision_path)
        proposed={r['NoteID']:r for r in new_rows}
        if len(new_rows)!=len(proposed) or set(proposed)&set(proposed_all):
            raise SystemExit('Duplicate NCE1 proposed stable identity')
        senses={}
        if schema==2:
            _check_digest(note_path,manifest.get('NewNotesSHA256'))
            _check_digest(decision_path,manifest.get('DecisionSHA256'))
            sense_rel=manifest.get('SourceSenseFile','')
            if sense_rel!=f'source_senses/{stem}.csv':raise SystemExit('Invalid NCE1 sense-review path')
            sense_path=BASE/'nce1'/sense_rel
            _check_digest(sense_path,manifest.get('SourceSenseSHA256'))
            _check_digest(BASE/f'nce1/learner/{stem}_adjustments.csv',manifest.get('AdjustmentSHA256'))
            sense_rows=read(sense_path);senses={r['SourceItemKey']:r for r in sense_rows}
            if len(senses)!=len(sense_rows):raise SystemExit('Duplicate NCE1 lesson-sense review')
        for nid,row in proposed.items():
            if row.get('CreatedSource')!=SOURCE_ID or row.get('Status')!='active' or row.get('LearnerProfile')!='klose' or row.get('LearnerLevel')!='4':
                raise SystemExit(f'NCE1 new identity/profile drift: {nid}')
            if require_allocated and nid not in registry:raise SystemExit(f'NCE1 identity not allocated: {nid}')
            if nid in registry:
                for field in IDENTITY_FIELDS:
                    if row.get(field)!=registry[nid].get(field):raise SystemExit(f'NCE1 allocated identity conflict: {nid}:{field}')
        effective=dict(registry)
        if not require_allocated:
            effective.update(proposed_all);effective.update(proposed)
        batch_map={};new_targets=set();reused=set()
        for row in decisions:
            key,nid=row['SourceItemKey'],row['NoteID']
            if key in mapped or key in batch_map or key not in sources or nid not in effective:
                raise SystemExit(f'NCE1 decision key/target invalid: {key}')
            src=sources[key];target=effective[nid]
            if target.get('Status')!='active':raise SystemExit(f'NCE1 target is not active: {nid}')
            if row.get('ReviewerType') not in {'model','human'} or not row.get('ReviewedAt') or not row.get('Reason'):
                raise SystemExit(f'NCE1 decision lacks explicit review evidence: {key}')
            if row.get('SourceFingerprint')!=source_fingerprint(src) or row.get('IdentityFingerprint')!=unit_fingerprint(target):
                raise SystemExit(f'NCE1 source/identity fingerprint mismatch: {key}')
            if any(row.get(k)!=src.get(k) for k in ('CurriculumOrder','Entry','PartOfSpeech')) or row.get('SourceMeaning')!=src.get('Meaning') or row.get('TargetSense')!=target.get('SenseLabel'):
                raise SystemExit(f'NCE1 reviewed meaning/coordinate drift: {key}')
            if schema==1:
                if not src.get('Meaning') or src.get('SourceStatus')!='verified-actual':
                    raise SystemExit(f'Photo batch cannot authorize unverified target senses: {key}')
            else:
                sense=senses.get(key)
                if not sense or row.get('SourceSenseFingerprint')!=source_fingerprint(sense):
                    raise SystemExit(f'NCE1 lesson-sense review fingerprint mismatch: {key}')
                if sense.get('SourceFingerprint')!=source_fingerprint(src) or any(sense.get(k)!=src.get(k) for k in ('CurriculumOrder','Entry')):
                    raise SystemExit(f'NCE1 lesson-sense review source drift: {key}')
                if src.get('SourceStatus')!='baseline-reconciled':raise SystemExit('Suffix review cannot relabel raw evidence')
                required=('TargetPartOfSpeech','TargetMeaning','ReferenceURL','ReviewBasis','ReviewedAt')
                if any(not sense.get(f,'').strip() for f in required) or sense.get('ReviewerType') not in {'model','human'}:
                    raise SystemExit(f'NCE1 lesson-sense review lacks evidence: {key}')
                if sense.get('EvidenceBasis') not in {'secondary-lesson-reference-model-reviewed','baseline-context-model-reviewed','edition-preview-crosschecked'}:
                    raise SystemExit(f'Unsupported NCE1 evidence level: {key}')
            decision=row['Decision']
            if decision in {'new-learning-unit','new-distinct-sense'}:
                if nid not in proposed or nid in new_targets:raise SystemExit(f'Invalid/repeated NCE1 new allocation decision: {key}')
                new_targets.add(nid)
            elif decision=='reuse-current-batch':
                if schema!=2 or nid not in new_targets:raise SystemExit(f'NCE1 repeat lacks an earlier reviewed target: {key}')
            elif decision in {'reuse-existing','reuse-spelling-variant','reuse-form-variant'}:
                if nid in proposed:raise SystemExit(f'NCE1 reuse points to newly allocated identity: {key}')
                reused.add(nid)
            else:raise SystemExit(f'Unsupported NCE1 decision: {key}')
            batch_map[key]=row
        scope=manifest['Scope'];orders=[int(r['CurriculumOrder']) for r in decisions]
        if scope['FirstCurriculumOrder']!=next_order or orders!=list(range(next_order,scope['LastCurriculumOrder']+1)):
            raise SystemExit('NCE1 reviewed batch coverage is not ordered/closed')
        next_order=scope['LastCurriculumOrder']+1
        if len(decisions)!=scope['SourceOccurrences'] or len(new_targets)!=scope['NewStableNotes'] or len(reused)!=scope['ReusedStableNotes'] or new_targets!=set(proposed):
            raise SystemExit('NCE1 frozen batch counts/sets drift')
        if schema==2 and set(senses)!=set(batch_map):raise SystemExit('NCE1 lesson-sense review coverage incomplete')
        mapped.update(batch_map);proposed_all.update(proposed)
    completion_path=BASE/'nce1/full_book.json'
    if completion_path.exists():
        complete=json.loads(completion_path.read_text(encoding='utf-8'))
        if complete.get('Status')!='identity-complete' or complete.get('SourceSHA256')!=_digest(source_path) or complete.get('SourceOccurrences')!=len(source) or complete.get('RemainingSourceOccurrences')!=0 or set(mapped)!=set(sources):
            raise SystemExit('NCE1 whole-book completion assertion is not closed')
        actual_manifests={p.name:_digest(p) for p,_ in review_batches()}
        if complete.get('BatchManifestSHA256')!=actual_manifests:raise SystemExit('NCE1 whole-book batch manifest changed')
    if require_allocated:
        mappings=[r for r in read(BASE/'master/source_identity_extensions.csv') if r.get('SourceID')==SOURCE_ID]
        actual={}
        for row in mappings:
            key=row.get('SourceItemKey')
            if key in actual or key not in mapped or row.get('SourceEdition')!=EDITION or row.get('Status')!='confirmed' or row.get('NoteID')!=mapped[key]['NoteID'] or row.get('Decision')!=mapped[key]['Decision']:
                raise SystemExit(f'Unreviewed/drifted NCE1 source mapping: {key}')
            actual[key]=row
        if set(actual)!=set(mapped):raise SystemExit('NCE1 source mapping coverage incomplete')
    return source,mapped,proposed_all

def validated_mapping_tuples():
    _,decisions,_=reviewed_state()
    return {(SOURCE_ID,EDITION,k,r['NoteID']) for k,r in decisions.items()}

if __name__=='__main__':
    sources,decisions,new=reviewed_state()
    print(f'NCE1 reviewed identity gate PASS: reviewed={len(decisions)} new={len(new)} remaining={len(sources)-len(decisions)}')
