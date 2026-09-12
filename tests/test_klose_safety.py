"""Regression checks for real failure modes; all mutation tests use isolated copies."""
import contextlib
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from klose_git_history import baseline_commit, identity_fingerprint, permits_identity_change
from check_klose_fronts import validate_fronts
import klose_pipeline


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def write(path, rows):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def copy_bytes(source, destination):
    # Explicit byte copies also work on managed filesystems without fast-copy support.
    Path(destination).write_bytes(Path(source).read_bytes())
    return destination


class IdentityAndFronts(unittest.TestCase):
    def test_migration_is_one_exact_transaction(self):
        fields = ('CanonicalWord', 'SenseLabel', 'Status')
        old = dict(CanonicalWord='speak', SenseLabel='language', Status='active')
        new = dict(old, SenseLabel='speech')
        row = dict(MigrationID='new', NoteID='KV000901', Status='approved',
                   BaselineCommit='base', BeforeFingerprint=identity_fingerprint(old, fields),
                   AfterFingerprint=identity_fingerprint(new, fields), Reason='explicit sense split')
        check = lambda change, records, prior: permits_identity_change('KV000901', old, change, fields, records, 'base', prior)
        self.assertTrue(check(new, [row], []))
        self.assertFalse(check(new, [row], [row]))  # Already consumed approval.
        self.assertFalse(check(dict(new, SenseLabel='unrelated'), [row], []))
        self.assertFalse(check(new, [dict(row, BaselineCommit='other')], []))
        self.assertFalse(check(new, [dict(row, BeforeFingerprint='wrong')], []))
        self.assertFalse(check(new, [dict(MigrationID='legacy', NoteID='KV000901', Status='approved')], []))

    def test_missing_baseline_fails_closed(self):
        with patch.dict(os.environ, {'KLOSE_BASE_COMMIT': 'missing-klose-test-baseline'}):
            with self.assertRaises(SystemExit):
                baseline_commit()

    def test_build_valid_and_release_blocked_are_reported_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'status.json'
            def run(names):
                if names == klose_pipeline.RELEASE:
                    raise SystemExit(1)
            with patch.object(sys, 'argv', ['pipeline', 'all', '--report', str(report)]), patch.object(klose_pipeline, 'run', side_effect=run):
                with self.assertRaises(SystemExit):
                    klose_pipeline.main()
            self.assertEqual(json.loads(report.read_text()), {'build_valid': True, 'release_ready': False})

    def test_remote_race_blocks_persist_without_rebase_or_commit(self):
        with patch.object(klose_pipeline.subprocess, 'run') as execute, patch.object(klose_pipeline.subprocess, 'check_output', side_effect=['old\n', 'new\n']):
            with self.assertRaises(SystemExit):
                klose_pipeline.persist()
            self.assertEqual([call.args[0] for call in execute.call_args_list], [['git', 'fetch', 'origin', 'main']])

    def test_fronts_reject_case_and_missing_cues_but_allow_held_duplicate(self):
        master = [dict(NoteID='a', Word='May'), dict(NoteID='b', Word='may')]
        learner = [dict(NoteID='a', PromptHint=''), dict(NoteID='b', PromptHint='')]
        admission = [dict(NoteID='a', Status='allowed'), dict(NoteID='b', Status='allowed')]
        with self.assertRaises(SystemExit):
            validate_fronts(master, learner, admission)
        learner[0]['PromptHint'] = '月份'
        with self.assertRaises(SystemExit):
            validate_fronts(master, learner, admission)
        learner[1]['PromptHint'] = '情态动词'
        validate_fronts(master, learner, admission)
        learner[0]['PromptHint'] = learner[1]['PromptHint'] = ''
        admission[1]['Status'] = 'held'
        validate_fronts(master, learner, admission)


class IsolatedStateTransitions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='klose-regression-')
        cls.root = Path(cls.temp.name)
        cls.source_digests = {p: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (ROOT / 'anki/klose').rglob('*') if p.is_file()}
        shutil.copytree(ROOT / 'tools', cls.root / 'tools', ignore=shutil.ignore_patterns('__pycache__'), copy_function=copy_bytes)
        shutil.copytree(ROOT / 'anki/klose', cls.root / 'anki/klose', copy_function=copy_bytes)
        cls.base = cls.root / 'anki/klose'
        cls.expr = cls.base / 'expressions'
        subprocess.run(['git', 'init', '-q'], cwd=cls.root, check=True)
        protected = ['anki/klose/master', 'anki/klose/learner/review_approvals',
                     'anki/klose/expressions/master', 'anki/klose/expressions/learner/review_approvals',
                     'anki/klose/releases/history']
        subprocess.run(['git', 'add', '--', *protected], cwd=cls.root, check=True)
        subprocess.run(['git', '-c', 'user.name=Klose Test', '-c', 'user.email=test@example.invalid',
                        'commit', '-qm', 'isolated test baseline'], cwd=cls.root, check=True)
        cls.baseline = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=cls.root, text=True).strip()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()
        changed = [str(p) for p, digest in cls.source_digests.items()
                   if hashlib.sha256(p.read_bytes()).hexdigest() != digest]
        if changed:
            raise AssertionError(f'Isolated tests changed source repository: {changed}')

    @contextlib.contextmanager
    def preserve(self, *paths):
        snapshots = {p: p.read_bytes() if p.exists() else None for p in paths}
        try:
            yield
        finally:
            for p, data in snapshots.items():
                if data is None:
                    p.unlink(missing_ok=True)
                else:
                    p.write_bytes(data)

    def command(self, name, success=True, *args):
        result = subprocess.run([sys.executable, str(self.root / 'tools' / name), *args],
                                cwd=self.root, capture_output=True, text=True,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', KLOSE_BASE_COMMIT=self.baseline))
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def expression_files(self):
        return [self.expr / p for p in ('learner/current.csv', 'learner/presentation_review_registry.csv',
                'learner/learning_admission.csv', 'master/release_registry.csv',
                'publish/study.csv', 'publish/anki-import.csv')]

    def test_changed_expression_requeues_and_generator_cannot_approve(self):
        with self.preserve(*self.expression_files()):
            p = self.expr / 'learner/current.csv'
            rows = read(p)
            rows[-1]['Prompt'] = '故意错误的提问：你昨天买了什么？'
            write(p, rows)
            self.command('klose_expression_review_state.py')
            reviews = read(self.expr / 'learner/presentation_review_registry.csv')
            self.assertEqual(reviews[-1]['ReviewStatus'], 'pending')
            self.assertEqual(reviews[-1]['ReviewedAt'], '')
            self.command('build_klose_expressions.py')
            self.assertNotIn(rows[-1]['ExpressionID'], {r['ExpressionID'] for r in read(self.expr / 'publish/study.csv')})
            self.command('check_klose_expressions_release_ready.py', False)
            # Writing a new hash/status into a registry does not create an approval receipt.
            reviews[-1].update(ReviewStatus='model-reviewed', ReviewedAt='2026-09-12')
            write(self.expr / 'learner/presentation_review_registry.csv', reviews)
            self.command('check_klose_expressions_release_ready.py', False)
            self.command('klose_expression_review_state.py')
            self.assertEqual(read(self.expr / 'learner/presentation_review_registry.csv')[-1]['ReviewStatus'], 'pending')
        self.command('check_klose_expressions_release_ready.py')  # Restored state remains releasable.

    def test_model_to_human_upgrade_does_not_require_fixed_model_count(self):
        receipt = self.expr / 'learner/review_approvals/test-human.csv'
        with self.preserve(*self.expression_files(), receipt):
            path = self.expr / 'learner/presentation_review_registry.csv'
            rows = read(path)
            rows[-1].update(ReviewStatus='approved', ReviewBasis='isolated test human receipt', ReviewedAt='2026-09-12')
            write(path, rows)
            write(receipt, [dict(rows[-1], ReviewerType='human', Evidence='Test fixture only; never a real learner confirmation')])
            self.command('klose_expression_review_state.py')
            self.command('build_klose_expressions.py')
            self.command('check_klose_expressions_release_ready.py')

    def test_historical_generators_cannot_restore_automatic_approval(self):
        # Historical utility rewrites several derived files; preserve the entire domain.
        paths = [p for p in self.expr.rglob('*') if p.is_file()]
        with self.preserve(*paths):
            self.command('materialize_klose_grade5_6_expressions.py')
            self.command('refine_klose_grade5_6_expression_presentations.py')
            reviews = read(self.expr / 'learner/presentation_review_registry.csv')
            self.assertTrue(any(r['ReviewStatus'] == 'pending' for r in reviews))
            self.command('build_klose_expressions.py')
            self.command('check_klose_expressions_release_ready.py', False)

    def test_expression_hold_exit_and_retry(self):
        with self.preserve(*self.expression_files()):
            path = self.expr / 'learner/learning_admission.csv'
            rows = read(path)
            last = max(rows, key=lambda r: r['LearningOrder'])
            old_order = last['LearningOrder']
            last.update(Status='held', LearningOrder='', Reason='isolated workload hold')
            write(path, rows)
            self.command('klose_expression_review_state.py')
            self.command('build_klose_expressions.py')
            self.command('check_klose_expressions_release_ready.py')
            self.assertEqual(len(read(self.expr / 'publish/study.csv')), len(rows) - 1)
            last.update(Status='allowed', LearningOrder=old_order)
            write(path, rows)
            self.command('klose_expression_review_state.py')
            self.command('build_klose_expressions.py')
            self.command('check_klose_expressions_release_ready.py')
            self.assertEqual(len(read(self.expr / 'publish/study.csv')), len(rows))

    def test_vocabulary_review_requires_matching_receipt(self):
        path = self.base / 'learner/presentation_review_registry.csv'
        with self.preserve(path):
            rows = read(path)
            rows[0]['ReviewNote'] = 'forged evidence with otherwise current fingerprint'
            write(path, rows)
            output = self.command('check_klose_release_ready.py', False)
            self.assertIn('review state', output)

    def test_historical_approval_edit_and_identity_waiver_are_rejected(self):
        receipt = next((self.expr / 'learner/review_approvals').glob('*.csv'))
        with self.preserve(receipt):
            receipt.write_bytes(receipt.read_bytes() + b'\n')
            self.assertIn('Immutable historical', self.command('check_klose_approval_history.py', False))
        self.command('check_klose_approval_history.py')
        path = self.base / 'master/note_registry_extensions.csv'
        with self.preserve(path):
            rows = read(path)
            row = next(r for r in rows if r['NoteID'] == 'KV000901')
            row['SenseLabel'] = 'unrelated mutation despite historical approval'
            write(path, rows)
            self.assertIn('Historical NoteID stability violation', self.command('check_klose_persistent_state.py', False))
        self.command('check_klose_persistent_state.py')

    def test_held_vocabulary_keeps_reviewed_pronunciation(self):
        self.command('validate_third_party_pronunciation_materialization.py')
        admission = {r['NoteID']: r for r in read(self.base / 'learner/learning_admission.csv')}
        for nid in ('KV001808', 'KV002569', 'KV002636'):
            self.assertEqual(admission[nid]['Status'], 'held')

    def test_seventeenth_content_correction_is_valid(self):
        self.command('check_third_party_learner_content.py')
        self.assertGreater(len(read(self.base / 'third_party_vocabulary/learner/content_corrections.csv')), 16)

    def test_textbook_check_accepts_later_third_party_scope(self):
        self.command('check_klose_grade5_6_current_merge.py')

    def test_admission_does_not_prove_support_and_observed_difficulty_blocks(self):
        support = self.base / 'feedback/learning_support.csv'
        report = self.base / 'review/future_vocab_review.csv'
        advisory = self.base / 'review/example_support_review.csv'
        with self.preserve(support, report, advisory):
            self.command('check_klose_learner.py')
            self.assertTrue(read(advisory))
            write(support, [dict(Token='homework', Status='needs-support', ObservedAt='2026-09-12', Evidence='isolated test observation')])
            self.command('check_klose_learner.py')
            self.assertTrue(read(report))
            self.command('check_klose_release_ready.py', False)
            write(support, [dict(Token='homework', Status='supported', ObservedAt='2026-09-12', Evidence='isolated test recovery')])
            self.command('check_klose_learner.py')
            self.assertFalse(read(report))
            self.command('check_klose_release_ready.py')

    def test_feedback_rejects_nonfinite_measurements(self):
        path = self.base / 'feedback/observations.csv'
        with self.preserve(path):
            with path.open() as handle:
                fields = next(csv.reader(handle))
            row = dict.fromkeys(fields, '')
            row.update(PeriodStart='2026-09-01', PeriodEnd='2026-09-07', Source='test', Observation='test only', AgainRatio='NaN')
            write(path, [row])
            self.command('check_klose_feedback.py', False)


if __name__ == '__main__':
    unittest.main()
