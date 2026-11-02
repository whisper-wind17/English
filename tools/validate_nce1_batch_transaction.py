"""Independent, one-time before/after audit; never modifies scheduling or approves."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,subprocess
from pathlib import Path
from klose_nce1_state import BASE, read, reviewed_state
from klose_review_fingerprint import fingerprint
ROOT=BASE.parents[1]

def old_bytes(ref,path):
    return subprocess.check_output(['git','show',f'{ref}:{path}'],cwd=ROOT)
def old_csv(ref,path):
    return list(csv.DictReader(io.StringIO(old_bytes(ref,path).decode('utf-8-sig'))))

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    source,decisions,proposed=reviewed_state()
    baseline=a.baseline
    oldreg={r['NoteID']:r for name in ('note_registry.csv','note_registry_extensions.csv') for r in old_csv(baseline,'anki/klose/master/'+name)}
    newreg={r['NoteID']:r for name in ('note_registry.csv','note_registry_extensions.csv') for r in read(BASE/'master'/name)}
    if any(newreg.get(n)!=r for n,r in oldreg.items()) or set(newreg)-set(oldreg)!=set(proposed):raise SystemExit('Independent audit: historical identity changed/new allocation mismatch')
    oldmaster={r['NoteID']:r for r in old_csv(baseline,'anki/klose/master/vocabulary_master.csv')}
    oldlearner={r['NoteID']:r for r in old_csv(baseline,'anki/klose/learner/current.csv')}
    master={r['NoteID']:r for r in read(BASE/'master/vocabulary_master.csv')}
    learner={r['NoteID']:r for r in read(BASE/'learner/current.csv')}
    changed={n for n in oldmaster if fingerprint(oldmaster[n],oldlearner[n])!=fingerprint(master[n],learner[n])}
    expected={r['NoteID'] for r in read(BASE/'nce1/learner/batch_001_adjustments.csv')}
    if changed!=expected:raise SystemExit(f'Independent audit: unexpected old presentation changes {changed ^ expected}')
    old_release={r['NoteID'] for name in ('release_registry.csv','release_registry_extensions.csv') for r in old_csv(baseline,'anki/klose/master/'+name)}
    release={r['NoteID'] for name in ('release_registry.csv','release_registry_extensions.csv') for r in read(BASE/'master'/name)}
    if not old_release <= release or release-old_release!=set(proposed)|{'KV000746'}:raise SystemExit('Independent audit: release identity closure failed')
    old_adm={r['NoteID']:r for r in old_csv(baseline,'anki/klose/learner/learning_admission.csv')}
    adm={r['NoteID']:r for r in read(BASE/'learner/learning_admission.csv')}
    old_allowed={n for n,r in old_adm.items() if r['Status']=='allowed'}
    allowed={n for n,r in adm.items() if r['Status']=='allowed'}
    targets={r['NoteID'] for r in decisions.values()}
    if not old_allowed<=allowed or allowed-old_allowed!=targets-old_allowed:raise SystemExit('Independent audit: admission accidentally lost or added identities')
    g4=[n for n,r in old_adm.items() if r['Stage']=='stage::grade4-current' and r['Status']=='allowed']
    if any(adm[n]['LearningOrder']!=old_adm[n]['LearningOrder'] for n in g4):raise SystemExit('Independent audit: Grade 4 prefix moved')
    # Explicitly keep old library holds outside this reviewed source scope unchanged.
    held={n for n,r in old_adm.items() if r['Status']=='held'}-targets
    if any(adm[n]['Status']!='held' for n in held):raise SystemExit('Independent audit: unrelated held note was admitted')
    invariant_paths=['anki/klose/expressions/publish/anki-import.csv','anki/klose/expressions/publish/study.csv',
      'anki/klose/anki/card_front.html','anki/klose/anki/card_back.html','anki/klose/anki/styling.css',
      'anki/klose/source_reference/new_concept_english_1_staging/vocabulary.csv',
      'anki/klose/source_reference/new_concept_english_1_staging/vocabulary-smart-2022.csv']
    for path in invariant_paths:
        if old_bytes(baseline,path)!=(ROOT/path).read_bytes():raise SystemExit(f'Independent audit: invariant artifact changed {path}')
    report={'status':'passed','baseline':baseline,'source_occurrences_total':len(source),'reviewed_source_occurrences':len(decisions),
      'reused_existing_identities':len(targets-set(proposed)),'new_identities':len(proposed),
      'previously_released_reused':len(targets&old_release),'existing_inventory_newly_released':len((release-old_release)-set(proposed)),
      'released_before':len(old_release),'released_after':len(release),'allowed_before':len(old_allowed),'allowed_after':len(allowed),
      'existing_presentations_changed':sorted(changed),'grade4_prefix_unchanged':len(g4),
      'nce1_stage_notes':sum(r['Stage']=='stage::nce1-current' for r in adm.values()),
      'unreviewed_source_occurrences_remaining':len(source)-len(decisions),'existing_identity_rows_unchanged':len(oldreg),
      'expressions_and_templates_unchanged':True,'anki_device_updated':False,
      'import_sha256':hashlib.sha256((BASE/'publish/anki-import.csv').read_bytes()).hexdigest()}
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
