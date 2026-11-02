"""Apply pre-existing, sealed model review receipts; never decide approval in CI."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
from klose_nce1_state import BASE,read
from klose_review_fingerprint import fingerprint

def main():
    p=argparse.ArgumentParser();p.add_argument('--confirm-reviewed',action='store_true');a=p.parse_args()
    if not a.confirm_reviewed:raise SystemExit('Explicit reviewed receipt application required')
    manifest=json.loads((BASE/'nce1/batch_002.json').read_text(encoding='utf-8'))
    master={r['NoteID']:r for r in read(BASE/'master/vocabulary_master.csv')}
    learner={r['NoteID']:r for r in read(BASE/'learner/current.csv')}
    ledger=read(BASE/'learner/presentation_review_registry.csv');by={r['NoteID']:r for r in ledger}
    expected=set(manifest['ReviewNoteIDs']);all_ids=set();selected={};files=[]
    for name,digest in manifest['ReviewReceiptsSHA256'].items():
        if Path(name).name!=name or not name.endswith('.csv'):raise SystemExit('Invalid receipt path')
        path=BASE/'nce1/review/full_book'/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise SystemExit('Sealed review receipt digest mismatch')
        for r in read(path):
            n=r['NoteID'];all_ids.add(n)
            if n not in expected or r.get('ReviewerType')!='model' or r.get('ReviewStatus')!='model-reviewed' or not r.get('ReviewNote'):
                raise SystemExit('Invalid explicit full-book receipt')
            if r.get('LearnerProfile')!='klose' or r.get('LearnerLevel')!='4' or r.get('ReviewedAt')!='2026-11-02':
                raise SystemExit('Receipt review identity/date drift')
            if n in master and n in learner and r['ContentFingerprint']==fingerprint(master[n],learner[n]):
                selected[n]=r
        target=BASE/'learner/review_approvals'/name
        if target.exists() and target.read_bytes()!=path.read_bytes():raise SystemExit('Immutable receipt name conflict')
        files.append((path,target))
    if all_ids!=expected or set(selected)!=expected:raise SystemExit(f'Receipts do not exactly cover current content: {sorted(expected-set(selected))}')
    required={n for n,r in master.items() if r['Released']=='yes'}|{r['NoteID'] for r in read(BASE/'learner/learning_admission.csv') if r['Status']=='allowed'}
    pending={n for n in required if by[n]['ReviewStatus']=='pending'}
    if pending-expected:raise SystemExit(f'Unexpected unreviewed presentation drift: {sorted(pending-expected)}')
    # Superseded same-session receipts are preserved; only an exact final match
    # may populate current state. The generator never produces an approval.
    for n,r in selected.items():
        if n not in by:raise SystemExit('Build must establish review state first')
        by[n].update({k:r[k] for k in by[n]})
    for path,target in files:target.write_bytes(path.read_bytes())
    p=BASE/'learner/presentation_review_registry.csv'
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(ledger[0]),lineterminator='\n');w.writeheader();w.writerows(ledger)
    print(f'Applied {len(selected)} exact-current sealed model reviews; preserved {len(files)} receipts; no approval generated')
if __name__=='__main__':main()
