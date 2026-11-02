"""Completed migrations cannot regenerate durable review decisions on new intake."""
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RETIRED = (
    "grade5-6-vocabulary-reconciliation.yml",
    "third-party-stage-b-readiness.yml",
    "third-party-stage-b-reconciliation.yml",
    "third-party-allocation-plan.yml",
    "grade5-6-premerge-dedup-audit.yml",
)
ARCHIVE = Path("docs/archive/workflows/nce1-20261102")


def validate_lifecycle(root: Path) -> None:
    for name in RETIRED:
        if (root / ".github/workflows" / name).exists():
            raise ValueError(f"Completed migration workflow reactivated: {name}")
        if not (root / ARCHIVE / name).is_file():
            raise ValueError(f"Historical workflow evidence missing: {name}")
    canonical = (root / ".github/workflows/build-klose-vocabulary.yml").read_text(encoding="utf-8")
    for token in ("  push:", "  pull_request:", "klose_pipeline.py build", "klose_pipeline.py all", "unittest discover"):
        if token not in canonical:
            raise ValueError(f"Canonical validation entry removed: {token}")


class CompletedMigrationLifecycle(unittest.TestCase):
    def test_completed_migrations_are_archived_and_current_gates_stay_active(self):
        validate_lifecycle(ROOT)

    def test_accidental_reactivation_is_rejected_without_mutating_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".github/workflows").mkdir(parents=True)
            (root / ARCHIVE).mkdir(parents=True)
            for name in RETIRED:
                shutil.copyfile(ROOT / ARCHIVE / name, root / ARCHIVE / name)
            shutil.copyfile(ROOT / ".github/workflows/build-klose-vocabulary.yml", root / ".github/workflows/build-klose-vocabulary.yml")
            validate_lifecycle(root)
            (root / ".github/workflows" / RETIRED[0]).write_text("name: obsolete\non: push\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_lifecycle(root)


if __name__ == "__main__":
    unittest.main()
