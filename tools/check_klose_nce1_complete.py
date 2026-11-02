"""Whole-book closure and release checks, independent of candidate matching."""
from __future__ import annotations
import json
from collections import Counter
from klose_nce1_state import BASE, read, reviewed_state, SOURCE_ID

def main():
    certificate=json.loads((BASE/'nce1/full_book.json').read_text(encoding='utf-8'))
    source,decisions,proposed=reviewed_state()
    if len(decisions)!=len(source) or certificate['RemainingSourceOccurrences']!=0:
        raise SystemExit('Whole-book NCE1 coverage incomplete')
    targets={d['NoteID'] for d in decisions.values()}
    if len(targets)!=certificate['UniqueLearningTargets']:raise SystemExit('NCE1 target closure mismatch')
    master={r['NoteID']:r for r in read(BASE/'master/vocabulary_master.csv')}
    learner={r['NoteID']:r for r in read(BASE/'learner/current.csv')}
    admission={r['NoteID']:r for r in read(BASE/'learner/learning_admission.csv')}
    occurrences=[r for r in read(BASE/'master/source_occurrences.csv') if r['SourceID']==SOURCE_ID]
    if len(occurrences)!=len(source):raise SystemExit('NCE1 materialized occurrences incomplete')
    actual=Counter((r['NoteID'],r['SourceWord'],int(r['SourceRow'])-1) for r in occurrences)
    expected=Counter((r['NoteID'],r['Entry'],int(r['CurriculumOrder'])) for r in decisions.values())
    if actual!=expected:raise SystemExit('NCE1 source-to-identity provenance drift')
    for nid in targets:
        if nid not in master or master[nid]['Released']!='yes' or nid not in learner or admission.get(nid,{}).get('Status')!='allowed':
            raise SystemExit(f'NCE1 target not released/admitted: {nid}')
        for f in ('British','American','MeaningPrimary'):
            if not master[nid].get(f,'').strip('[] /'):raise SystemExit(f'NCE1 target missing content: {nid}:{f}')
        if not learner[nid]['ExampleSentence'] or not learner[nid]['ExampleTranslation'] or learner[nid]['LearnerLevel']!='4':
            raise SystemExit(f'NCE1 learner presentation missing: {nid}')
    if any(r['Grade'] or r['Semester'] for r in occurrences):raise SystemExit('NCE1 must not invent a Source Grade')
    from klose_release_curriculum import current_curriculum_ordered_note_ids
    ordered,states=current_curriculum_ordered_note_ids()
    g4=[i for i,n in enumerate(ordered) if states[n][0]=='stage::grade4-current']
    nce=[i for i,n in enumerate(ordered) if states[n][0]=='stage::nce1-current']
    later=[i for i,n in enumerate(ordered) if states[n][0] in {'stage::grade5-6-current','stage::third-party-primary'}]
    if not nce or not(max(g4)<min(nce) and max(nce)<min(later)):raise SystemExit('NCE1 segment ordering invalid')
    print(f'NCE1 complete: occurrences={len(source)} targets={len(targets)} source_new_identities={len(proposed)} pending=0')
if __name__=='__main__':main()
