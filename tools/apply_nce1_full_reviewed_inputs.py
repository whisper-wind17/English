"""Explicit one-time whole-book input transaction; never run by daily CI.

The model-reviewed decisions and presentations must already exist. This command
checks preimages and only materializes their append/update operations. No matcher
or automatic approval is used. A retry after any successful write fails closed.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json
from pathlib import Path
from klose_nce1_state import BASE,SOURCE_ID,EDITION,read,reviewed_state
from klose_current_policy import unit_fingerprint

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def append(path,rows):
    old=path.read_bytes();fields=next(csv.reader(io.StringIO(old.decode('utf-8-sig'))))
    if not old.endswith(b'\n'):raise SystemExit('Append target missing newline')
    out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore',lineterminator='\n');w.writerows(rows)
    return old+out.getvalue().encode('utf-8')
def encode(rows,fields):
    out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(rows)
    return b'\xef\xbb\xbf'+out.getvalue().encode('utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('--confirm-reviewed',action='store_true');a=p.parse_args()
    if not a.confirm_reviewed:raise SystemExit('Explicit reviewed transaction confirmation required')
    manifest=json.loads((BASE/'nce1/batch_002.json').read_text(encoding='utf-8'))
    for name,expected in manifest['BeforeSHA256'].items():
        if digest(BASE/name)!=expected:raise SystemExit(f'Stale full-book transaction preimage: {name}')
    reviewed_state(require_allocated=False)
    new=read(BASE/'nce1/learner/batch_002_new_notes.csv');decisions=read(BASE/'nce1/identity_decisions/batch_002.csv');adjust=read(BASE/'nce1/learner/batch_002_adjustments.csv')
    regs={r['NoteID']:r for name in ('note_registry.csv','note_registry_extensions.csv') for r in read(BASE/'master'/name)}
    maximum=max(int(n[2:]) for n in regs)
    if [r['NoteID'] for r in new]!=[f'KV{n:06d}' for n in range(maximum+1,maximum+len(new)+1)]:raise SystemExit('Full-book ID allocation stale/non-contiguous')
    releases={r['NoteID'] for name in ('release_registry.csv','release_registry_extensions.csv') for r in read(BASE/'master'/name)}
    added_release=sorted({r['NoteID'] for r in decisions}-releases)
    if len(added_release)!=manifest['NewReleaseCount']:raise SystemExit('Full-book release scope changed')
    hints_path=BASE/'learner/prompt_hint_overrides.csv';hints=read(hints_path);hb={r['NoteID']:r for r in hints}
    adjust_path=BASE/'learner/presentation_adjustments.csv';old_adjust=read(adjust_path);ab={r['NoteID']:r for r in old_adjust}
    for row in adjust:
        if row['NoteID'] not in regs or row.get('IdentityFingerprint')!=unit_fingerprint(regs[row['NoteID']]):raise SystemExit('Stale full-book presentation identity')
    for row in new+adjust:
        nid=row['NoteID'];hint=row.get('PromptHint','')
        if hint:
            if nid in hb:raise SystemExit(f'Unexpected existing front override: {nid}')
            r=dict(NoteID=nid,PromptHint=hint,Reason='nce1-full-book explicit sense disambiguation');hints.append(r);hb[nid]=r
    for row in adjust:
        changes={k:row[k] for k in ('MeaningPrimary','ExampleSentence','ExampleTranslation') if row.get(k)}
        if not changes:continue
        nid=row['NoteID']
        if nid not in ab:
            r=dict.fromkeys(list(old_adjust[0]),'');r['NoteID']=nid;old_adjust.append(r);ab[nid]=r
        ab[nid].update(changes)
        ab[nid]['Reason']=(ab[nid].get('Reason','')+'; '+row['Reason']).strip('; ')
    mapping=[dict(SourceID=SOURCE_ID,SourceEdition=EDITION,SourceItemKey=r['SourceItemKey'],NoteID=r['NoteID'],Decision=r['Decision'],Status='confirmed') for r in decisions]
    output={
        'master/note_registry_extensions.csv':append(BASE/'master/note_registry_extensions.csv',new),
        'master/source_identity_extensions.csv':append(BASE/'master/source_identity_extensions.csv',mapping),
        'master/release_registry_extensions.csv':append(BASE/'master/release_registry_extensions.csv',[dict(NoteID=n,ReleasedAt='2026-11-02',ReleaseReason='nce1-full-book-explicit-review') for n in added_release]),
        'learner/prompt_hint_overrides.csv':encode(hints,list(hints[0])),
        'learner/presentation_adjustments.csv':encode(old_adjust,list(old_adjust[0]))}
    # Scope, conflicts, and every preimage checked before touching durable state.
    for name,data in output.items():(BASE/name).write_bytes(data)
    reviewed_state()
    print(f'NCE1 full inputs: source_mappings={len(mapping)} new_identities={len(new)} newly_released={len(added_release)}')
if __name__=='__main__':main()
