"""Full-book closure and adversarial evidence checks; all mutations isolated."""
import contextlib,csv,json,hashlib,shutil,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import klose_nce1_state as nce

def write(p,rows):
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

class WholeBook(unittest.TestCase):
    @contextlib.contextmanager
    def isolated(self):
        with tempfile.TemporaryDirectory() as temp:
            b=Path(temp)/'klose'
            for name in ('nce1','master','source_reference/new_concept_english_1_staging'):
                shutil.copytree(nce.BASE/name,b/name)
            with patch.object(nce,'BASE',b):yield b
    def test_every_source_occurrence_has_one_reviewed_target(self):
        src,dec,new=nce.reviewed_state()
        self.assertEqual(len(src),len(dec));self.assertEqual(len(src),906)
        self.assertEqual([int(r['CurriculumOrder']) for r in dec.values()],list(range(1,len(src)+1)))
        self.assertEqual(len({r['NoteID'] for r in dec.values()}),889)
    def test_surface_aliases_reuse_survivors(self):
        _,d,_=nce.reviewed_state()
        for k,n in [('0159|ice cream','KV000236'),('0167|shoe','KV000256'),('0203|mrs.','KV000948'),('0500|stomach ache','KV000585'),('0903|tyre','KV002837')]:
            self.assertEqual(d['nce1-o'+k]['NoteID'],n)
    def test_distinct_senses_and_same_sense_repetitions(self):
        _,d,_=nce.reviewed_state()
        for key,other in [('0174|full','KV001775'),('0228|open','KV001021'),('0293|bank','KV000445'),('0684|miss','KV002132'),('0862|pool','KV002373')]:
            self.assertNotEqual(d['nce1-o'+key]['NoteID'],other)
        self.assertEqual(d['nce1-o0741|low']['NoteID'],d['nce1-o0725|low']['NoteID'])
        self.assertEqual(d['nce1-o0394|rain']['NoteID'],'KV000829')
    def test_changed_sense_review_fails_closed(self):
        with self.isolated() as b:
            p=b/'nce1/source_senses/batch_002.csv';r=nce.read(p);r[0]['TargetMeaning']='无关的新释义';write(p,r)
            with self.assertRaises(SystemExit):nce.reviewed_state()
    def test_changed_decision_fails_even_when_target_exists(self):
        with self.isolated() as b:
            p=b/'nce1/identity_decisions/batch_002.csv';r=nce.read(p);r[0]['NoteID']='KV002101';write(p,r)
            with self.assertRaises(SystemExit):nce.reviewed_state()
    def test_removing_full_batch_does_not_fake_completion(self):
        with self.isolated() as b:
            (b/'nce1/batch_002.json').unlink()
            with self.assertRaises(SystemExit):nce.reviewed_state()
    def test_later_raw_source_change_invalidates_review(self):
        with self.isolated() as b:
            p=b/'source_reference/new_concept_english_1_staging/vocabulary-smart-2022.csv';r=nce.read(p);r[-1]['Entry']='changed';write(p,r)
            with self.assertRaises(SystemExit):nce.reviewed_state()
    def test_daily_build_never_runs_explicit_transactions_or_approval(self):
        import klose_pipeline as pipe
        names=pipe.PROTECT+pipe.VOCABULARY+pipe.EXPRESSIONS+pipe.RELEASE
        self.assertNotIn('apply_nce1_full_reviewed_inputs.py',names)
        self.assertFalse(any('approve_' in x for x in names))
        self.assertIn('check_klose_nce1_complete.py',names)
if __name__=='__main__':unittest.main()
