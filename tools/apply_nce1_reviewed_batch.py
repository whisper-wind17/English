"""One-time explicit NCE1 transaction. Not part of the build pipeline.

Appends reviewed identity/source/release inputs and deterministic presentation
adjustments. A sealed review receipt can subsequently be applied only to the
exact materialized content fingerprint; no approvals are generated here.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json
from pathlib import Path
from klose_nce1_state import BASE, SOURCE_ID, EDITION, read, reviewed_state
from klose_current_policy import unit_fingerprint

TARGETS=("master/note_registry_extensions.csv", "master/source_identity_extensions.csv",
         "master/release_registry_extensions.csv", "learner/prompt_hint_overrides.csv", "learner/presentation_adjustments.csv")

def appended_bytes(path, rows):
    old=path.read_bytes()
    fields=next(csv.reader(io.StringIO(old.decode('utf-8-sig'))))
    buffer=io.StringIO(newline='')
    csv.DictWriter(buffer,fieldnames=fields,extrasaction='ignore',lineterminator='\n').writerows(rows)
    if not old.endswith(b'\n'):raise SystemExit(f'Missing newline in append-only input: {path}')
    return old+buffer.getvalue().encode('utf-8')

def apply_inputs():
    manifest=json.loads((BASE/'nce1/batch_001.json').read_text())
    expected=manifest['BeforeSHA256']
    for name in TARGETS:
        if hashlib.sha256((BASE/name).read_bytes()).hexdigest()!=expected[name]:
            raise SystemExit(f'NCE1 transaction preimage changed; inspect before retry: {name}')
    _,decisions,proposed=reviewed_state(require_allocated=False)
    regs=read(BASE/'master/note_registry.csv')+read(BASE/'master/note_registry_extensions.csv')
    if set(proposed)&{r['NoteID'] for r in regs}:raise SystemExit('NCE1 new IDs are already occupied')
    maximum=max(int(r['NoteID'][2:]) for r in regs)
    if sorted(proposed)!=[f'KV{i:06d}' for i in range(maximum+1,maximum+len(proposed)+1)]:
        raise SystemExit('NCE1 reviewed allocation is stale/non-contiguous')
    mappings=[dict(SourceID=SOURCE_ID,SourceEdition=EDITION,SourceItemKey=k,NoteID=r['NoteID'],Decision=r['Decision'],Status='confirmed') for k,r in decisions.items()]
    releases=read(BASE/'master/release_registry.csv')+read(BASE/'master/release_registry_extensions.csv')
    released={r['NoteID'] for r in releases}
    new_release=sorted({r['NoteID'] for r in decisions.values()}-released)
    if len(new_release)!=manifest['NewReleaseCount']:
        raise SystemExit('NCE1 release transaction target set changed')
    additions={TARGETS[0]:list(proposed.values()),TARGETS[1]:mappings,TARGETS[2]:[
        dict(NoteID=n,ReleasedAt='2026-11-02',ReleaseReason='nce1-reviewed-batch001') for n in new_release]}
    adjustments=read(BASE/'nce1/learner/batch_001_adjustments.csv')
    registry={r['NoteID']:r for r in regs}
    for row in adjustments:
        if row['IdentityFingerprint']!=unit_fingerprint(registry[row['NoteID']]):
            raise SystemExit(f'Stale adjustment identity: {row["NoteID"]}')
    hints=[dict(NoteID=r['NoteID'],PromptHint=r['PromptHint'],Reason='nce1-batch001 explicit model-reviewed sense disambiguation') for r in [*proposed.values(),*adjustments] if r.get('PromptHint')]
    old_hints={r['NoteID'] for r in read(BASE/TARGETS[3])}
    if old_hints & {r['NoteID'] for r in hints}:raise SystemExit('NCE1 hint conflict requires explicit reconciliation')
    additions[TARGETS[3]]=hints
    additions[TARGETS[4]]=[dict(NoteID=r['NoteID'],Word='',MeaningPrimary=r['MeaningPrimary'],ExampleSentence=r['ExampleSentence'],ExampleTranslation=r['ExampleTranslation'],Reason=r['Reason']) for r in adjustments if r['MeaningPrimary'] or r['ExampleSentence']]
    old_adj={r['NoteID'] for r in read(BASE/TARGETS[4])}
    if old_adj & {r['NoteID'] for r in additions[TARGETS[4]]}:raise SystemExit('NCE1 presentation adjustment conflict')
    output={name:appended_bytes(BASE/name,rows) for name,rows in additions.items()}
    # All conflicts are checked before any write. Re-running after partial failure fails closed.
    for name,data in output.items():(BASE/name).write_bytes(data)
    reviewed_state()
    print(f'NCE1 inputs appended: new={len(proposed)} mappings={len(mappings)} release_added={len(new_release)} hints={len(hints)}')

def apply_receipt():
    from klose_review_fingerprint import fingerprint
    path=BASE/'nce1/review/batch_001_approval.csv'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=json.loads((BASE/'nce1/batch_001.json').read_text())['ReviewReceiptSHA256']:
        raise SystemExit('Sealed NCE1 review receipt digest changed')
    receipts=read(path)
    masters={r['NoteID']:r for r in read(BASE/'master/vocabulary_master.csv')}
    learners={r['NoteID']:r for r in read(BASE/'learner/current.csv')}
    ledger=read(BASE/'learner/presentation_review_registry.csv')
    by={r['NoteID']:r for r in ledger}
    expected=set(json.loads((BASE/'nce1/batch_001.json').read_text())['ReviewNoteIDs'])
    if len(receipts)!=len(expected) or {r['NoteID'] for r in receipts}!=expected:
        raise SystemExit('Sealed NCE1 review receipt scope drift')
    for r in receipts:
        nid=r['NoteID']
        if r['ContentFingerprint']!=fingerprint(masters[nid],learners[nid]) or r['ReviewStatus']!='model-reviewed' or r['ReviewerType']!='model':
            raise SystemExit(f'Sealed NCE1 review does not match current content: {nid}')
        if nid not in by:raise SystemExit(f'Build must create pending review first: {nid}')
    target=BASE/'learner/review_approvals'/path.name
    if target.exists() and target.read_bytes()!=path.read_bytes():raise SystemExit('Immutable NCE1 receipt conflict')
    for r in receipts:
        by[r['NoteID']].update({k:r[k] for k in by[r['NoteID']]})
    target.write_bytes(path.read_bytes())
    registry_path=BASE/'learner/presentation_review_registry.csv'
    with registry_path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(ledger[0]));w.writeheader();w.writerows(ledger)
    print(f'Applied {len(receipts)} explicitly sealed content-matching model review receipts; no approval decision generated')

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['inputs','receipt']);p.add_argument('--confirm-reviewed',action='store_true');a=p.parse_args()
    if not a.confirm_reviewed:raise SystemExit('Explicit reviewed-transaction confirmation required')
    (apply_inputs if a.action=='inputs' else apply_receipt)()
if __name__=='__main__':main()
