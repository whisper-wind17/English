"""Negative tests use isolated data; no real learner state is mutated."""
import contextlib
import csv
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import klose_nce1_state as nce
import klose_release_curriculum as curriculum


def write(path, rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


class ReviewedNCE1Batch(unittest.TestCase):
    @contextlib.contextmanager
    def isolated(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)/'klose'
            for name in ('nce1','source_reference/new_concept_english_1_staging','master'):
                shutil.copytree(nce.BASE/name,base/name)
            with patch.object(nce,'BASE',base):
                yield base

    def test_frozen_first_batch_stays_closed_with_later_batches(self):
        sources, decisions, proposed=nce.reviewed_state()
        first={k:r for k,r in decisions.items() if int(r['CurriculumOrder'])<=150}
        first_new={n:r for n,r in proposed.items() if int(r['Order'])<=150}
        self.assertEqual(len(first),150)
        self.assertEqual(len(first_new),41)
        self.assertEqual(len({r['NoteID'] for r in first.values()}),150)
        self.assertEqual({r['NoteID'] for r in first.values() if r['Decision'].startswith('new-')},set(first_new))

    def test_semantic_distinction_and_title_variant_are_explicit(self):
        _,decisions,_=nce.reviewed_state()
        self.assertEqual(decisions['nce1-o0015|watch']['NoteID'],'KV003020')
        self.assertEqual(decisions['nce1-o0015|watch']['Decision'],'new-distinct-sense')
        self.assertEqual(decisions['nce1-o0037|mr.']['NoteID'],'KV002159')
        self.assertEqual(decisions['nce1-o0040|miss']['NoteID'],'KV002131')
        self.assertEqual(decisions['nce1-o0099|cold']['NoteID'],'KV000176')

    def test_mapping_to_other_existing_sense_is_rejected(self):
        with self.isolated() as base:
            p=base/'master/source_identity_extensions.csv';rows=nce.read(p)
            row=next(r for r in rows if r['SourceItemKey']=='nce1-o0015|watch')
            row['NoteID']='KV000851';write(p,rows)
            with self.assertRaises(SystemExit):nce.reviewed_state()

    def test_source_text_change_invalidates_prior_identity_review(self):
        with self.isolated() as base:
            p=base/'source_reference/new_concept_english_1_staging/vocabulary-smart-2022.csv'
            rows=nce.read(p);rows[14]['Meaning']='观看';write(p,rows)
            with self.assertRaises(SystemExit):nce.reviewed_state()

    def test_extra_mapping_cannot_claim_an_unreviewed_target(self):
        with self.isolated() as base:
            p=base/'master/source_identity_extensions.csv';rows=nce.read(p)
            rows.append(dict(SourceID=nce.SOURCE_ID,SourceEdition=nce.EDITION,SourceItemKey='nce1-o0907|unreviewed',NoteID='KV002101',Decision='reuse-existing',Status='confirmed'))
            write(p,rows)
            with self.assertRaises(SystemExit):nce.reviewed_state()

    def test_current_order_preserves_grade4_prefix_and_reuses_promoted_tp(self):
        from klose_current_policy import read_csv
        ordered,states=curriculum.current_curriculum_ordered_note_ids()
        old,old_state=curriculum.textbook_curriculum(include_nce1=False)
        g4=[n for n in old if old_state[n][0]=='stage::grade4-current']
        self.assertEqual(ordered[:len(g4)],g4)
        nce_pos=[i for i,n in enumerate(ordered) if states[n][0]=='stage::nce1-current']
        g56_pos=[i for i,n in enumerate(ordered) if states[n][0]=='stage::grade5-6-current']
        _,reviewed,_=nce.reviewed_state()
        first_ids={r['NoteID'] for r in reviewed.values() if int(r['CurriculumOrder'])<=150}
        self.assertEqual(sum(states.get(n,('',''))[0]=='stage::nce1-current' for n in first_ids),136)
        self.assertLess(max(nce_pos),min(g56_pos))
        self.assertEqual(len(ordered),len(set(ordered)))
        self.assertEqual(states['KV002159'][0],'stage::nce1-current')
        self.assertEqual(ordered.count('KV002159'),1)
        self.assertNotIn('KV002569',ordered)  # historical held duplicate stays held

    def test_approval_remains_separate_from_generation(self):
        source=(ROOT/'tools/apply_klose_nce1.py').read_text()
        self.assertNotIn('approve_klose_learner_review',source)
        self.assertNotIn('review_approvals',source)
        _, decisions, _=nce.reviewed_state()
        self.assertTrue(all(r['ReviewerType']=='model' for r in decisions.values()))

if __name__=='__main__':unittest.main()
