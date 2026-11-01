import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import build_klose_learning_admission as admission


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["SourceID", "SourceEdition", "SourceItemKey", "NoteID", "Decision", "Status"],
            lineterminator="\n",
        )
        w.writeheader()
        w.writerows(rows)


class NCE1CurriculumOrderTest(unittest.TestCase):
    def fixture(self, root: Path, ranks=None):
        source = root / "source.csv"
        scope = root / "scope.json"
        curriculum = root / "curriculum.json"
        write_csv(source, [
            dict(SourceID="rj_start1", SourceEdition="klose-current",
                 SourceItemKey="grade4-upper-u01-o001|alpha", NoteID="KV000001",
                 Decision="reuse-existing", Status="confirmed"),
            dict(SourceID=admission.NCE_SOURCE_ID, SourceEdition=admission.NCE_SOURCE_EDITION,
                 SourceItemKey="nce1-o0001|beta", NoteID="KV000002",
                 Decision="reuse-existing", Status="confirmed"),
            # Same stable learning unit occurs later in Grade 5; NCE1 must win.
            dict(SourceID="renjiao_start3", SourceEdition="2024-revision",
                 SourceItemKey="grade5-upper-u01-o001|beta", NoteID="KV000002",
                 Decision="reuse-existing", Status="confirmed"),
            dict(SourceID="renjiao_start3", SourceEdition="2024-revision",
                 SourceItemKey="grade5-lower-u01-o001|gamma", NoteID="KV000003",
                 Decision="reuse-existing", Status="confirmed"),
            dict(SourceID="renjiao_start3", SourceEdition="2024-revision",
                 SourceItemKey="grade6-upper-u01-o001|delta", NoteID="KV000004",
                 Decision="reuse-existing", Status="confirmed"),
        ])
        scope.write_text(json.dumps({
            "ScopeStatus": "accepted",
            "StableIdentityAllocationAuthorized": True,
            "Books": {name: {"Accepted": True} for name in ("5上", "5下", "6上", "6下")},
        }), encoding="utf-8")
        ranks = ranks or {
            "grade4": 10, "new_concept_english_1": 20,
            "grade5": 30, "grade6": 40, "third_party": 90,
        }
        curriculum.write_text(json.dumps({
            "Segments": {
                name: ({
                    "Rank": rank,
                    "SourceEdition": admission.NCE_SOURCE_EDITION,
                } if name == "new_concept_english_1" else {"Rank": rank})
                for name, rank in ranks.items()
            }
        }), encoding="utf-8")
        return source, scope, curriculum

    def test_nce1_is_between_grade4_and_grade5_and_deduplicates_later_occurrence(self):
        with tempfile.TemporaryDirectory() as directory:
            source, scope, curriculum = self.fixture(Path(directory))
            with patch.object(admission, "SOURCE_IDENTITIES", source), \
                 patch.object(admission, "G56_SCOPE", scope), \
                 patch.object(admission, "CURRICULUM", curriculum):
                ordered, grade4, nce1, grade56 = admission.current_scope()
            self.assertEqual(ordered, ["KV000001", "KV000002", "KV000003", "KV000004"])
            self.assertEqual(grade4, {"KV000001"})
            self.assertEqual(nce1, {"KV000002"})
            self.assertEqual(grade56, {"KV000002", "KV000003", "KV000004"})

    def test_invalid_segment_order_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            bad = {
                "grade4": 10, "grade5": 20, "new_concept_english_1": 30,
                "grade6": 40, "third_party": 90,
            }
            source, scope, curriculum = self.fixture(Path(directory), ranks=bad)
            with patch.object(admission, "SOURCE_IDENTITIES", source), \
                 patch.object(admission, "G56_SCOPE", scope), \
                 patch.object(admission, "CURRICULUM", curriculum):
                with self.assertRaises(SystemExit):
                    admission.current_scope()


if __name__ == "__main__":
    unittest.main()
