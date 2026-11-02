"""Independent before/after audit of the full-book integration transaction."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'anki/klose'

def read_bytes(data):return list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
def read(path):return read_bytes(path.read_bytes())
def old(ref,relative):return subprocess.check_output(['git','show',f'{ref}:{relative}'],cwd=ROOT)
def digest(data):return hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    from klose_nce1_state import reviewed_state
    from klose_review_fingerprint import fingerprint
    source,decisions,proposed=reviewed_state()
    new_input=read(BASE/'nce1/learner/batch_002_new_notes.csv');newids={r['NoteID'] for r in new_input}
    adjustments=read(BASE/'nce1/learner/batch_002_adjustments.csv');adjusted={r['NoteID'] for r in adjustments}
    before_reg=[];after_reg=[]
    for name in ('note_registry.csv','note_registry_extensions.csv'):
        rel='anki/klose/master/'+name
        before_reg+=read_bytes(old(a.baseline,rel));after_reg+=read(ROOT/rel)
    old_by={r['NoteID']:r for r in before_reg};new_by={r['NoteID']:r for r in after_reg}
    assert all(new_by.get(n)==r for n,r in old_by.items()),'Existing identity fields changed'
    assert set(new_by)-set(old_by)==newids,'Unexpected identity addition'
    for rel in ('anki/klose/master/note_registry_extensions.csv','anki/klose/master/source_identity_extensions.csv','anki/klose/master/release_registry_extensions.csv'):
        assert (ROOT/rel).read_bytes().startswith(old(a.baseline,rel)),f'Append-only input rewritten: {rel}'
    protected=['anki/klose/source_reference/new_concept_english_1_staging/vocabulary.csv','anki/klose/source_reference/new_concept_english_1_staging/vocabulary-smart-2022.csv', 'anki/klose/learner/admission_decisions.csv']
    # Frozen first batch, all prior approvals, both card templates, Expressions and historical releases stay byte-identical.
    tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',a.baseline],cwd=ROOT,text=True).splitlines()
    prefixes=('anki/klose/expressions/','anki/klose/anki/','anki/klose/learner/review_approvals/','anki/klose/releases/history/')
    protected+= [n for n in tracked if n.startswith(prefixes) or n.startswith('anki/klose/nce1/') and ('batch_001' in n or n.endswith('/review_basis.md'))]
    for name in set(protected):assert (ROOT/name).read_bytes()==old(a.baseline,name),f'Historical/protected bytes changed: {name}'
    oldm={r['NoteID']:r for r in read_bytes(old(a.baseline,'anki/klose/master/vocabulary_master.csv'))}
    oldl={r['NoteID']:r for r in read_bytes(old(a.baseline,'anki/klose/learner/current.csv'))}
    newm={r['NoteID']:r for r in read(BASE/'master/vocabulary_master.csv')};newl={r['NoteID']:r for r in read(BASE/'learner/current.csv')}
    changed={n for n in oldm if fingerprint(oldm[n],oldl[n])!=fingerprint(newm[n],newl[n])}
    assert changed==adjusted,(changed-adjusted,adjusted-changed)
    olda=read_bytes(old(a.baseline,'anki/klose/learner/learning_admission.csv'));newa=read(BASE/'learner/learning_admission.csv')
    oldg4=[r['NoteID'] for r in sorted(olda,key=lambda x:x['LearningOrder']) if r['Stage']=='stage::grade4-current' and r['Status']=='allowed']
    allowed=sorted((r for r in newa if r['Status']=='allowed'),key=lambda x:x['LearningOrder'])
    assert [r['NoteID'] for r in allowed[:len(oldg4)]]==oldg4,'Grade 4 prefix changed'
    before_allowed={r['NoteID'] for r in olda if r['Status']=='allowed'};after_allowed={r['NoteID'] for r in allowed}
    assert before_allowed<=after_allowed,'Previously allowed targets removed'
    assert after_allowed-before_allowed<=newids|{r['NoteID'] for r in decisions.values()},'Unrelated target admitted'
    held_policy={r['NoteID'] for r in read(BASE/'learner/admission_decisions.csv') if r['Status']=='held'}
    assert not held_policy&after_allowed,'Explicit held duplicates resumed'
    before_released={n for n,r in oldm.items() if r['Released']=='yes'};after_released={n for n,r in newm.items() if r['Released']=='yes'}
    manifest=json.loads((BASE/'nce1/batch_002.json').read_text())
    assert before_released<=after_released and len(after_released-before_released)==manifest['NewReleaseCount']
    report=dict(status='passed',baseline=a.baseline,source_occurrences=len(source),mapped_occurrences=len(decisions),remaining_occurrences=len(source)-len(decisions),unique_nce1_targets=len({r['NoteID'] for r in decisions.values()}),historical_identities_unchanged=len(old_by),new_identities=len(newids),new_id_range=[min(newids),max(newids)],released_before=len(before_released),released_after=len(after_released),newly_released_existing=sorted((after_released-before_released)-newids),allowed_before=len(before_allowed),allowed_after=len(after_allowed),held_after=sum(r['Status']=='held' for r in newa),existing_presentation_changes=sorted(changed),grade4_prefix_unchanged=len(oldg4),nce1_stage_notes=sum(r['Stage']=='stage::nce1-current' for r in allowed),raw_source_and_prior_reviews_unchanged=True,expressions_and_templates_unchanged=True,anki_device_updated=False,import_sha256=digest((BASE/'publish/anki-import.csv').read_bytes()))
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
