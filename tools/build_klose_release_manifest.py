"""Generate one deterministic current-release snapshot for all documentation."""
from __future__ import annotations
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'anki/klose'


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result = {'schema_version': 1, 'device_state_source': 'anki/klose/releases/device_receipts.json', 'learning_effectiveness': 'see anki/klose/feedback; release validation does not prove learning outcomes'}
    for name, base, key in [('vocabulary', BASE, 'NoteID'), ('expressions', BASE / 'expressions', 'ExpressionID')]:
        study = rows(base / 'publish/study.csv')
        admission = rows(base / 'learner/learning_admission.csv')
        review = rows(base / 'learner/presentation_review_registry.csv')
        artifact = base / 'publish/anki-import.csv'
        ids = {r[key] for r in study}
        allowed = [r for r in admission if r['Status'] == 'allowed']
        result[name] = {
            'artifact': artifact.relative_to(ROOT).as_posix(), 'sha256': digest(artifact),
            'rows': len(study), 'allowed': len(allowed), 'held': sum(r['Status'] == 'held' for r in admission),
            'learning_order_max': max((r['LearningOrder'] for r in allowed), default=''),
            'review_counts': dict(sorted(Counter(r['ReviewStatus'] for r in review if r[key] in ids).items())),
            'prompt_hint_nonempty': sum(bool(r.get('PromptHint', '').strip()) for r in study),
            'note_type': 'Klose Vocabulary' if name == 'vocabulary' else 'Klose Expression',
            'deck': 'Klose-English::Vocabulary' if name == 'vocabulary' else 'Klose-English::Expressions',
            'columns': list(study[0]) if study else [],
            'template_sha256': {p.name: digest(p) for p in sorted((base / 'anki').glob('*')) if p.suffix in {'.html', '.css'}},
        }
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    result['release_id'] = hashlib.sha256(payload.encode()).hexdigest()
    path = BASE / 'releases/current.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(f"Release manifest: {result['release_id'][:16]} vocabulary={result['vocabulary']['rows']} expressions={result['expressions']['rows']}")


if __name__ == '__main__':
    main()
