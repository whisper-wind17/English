import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_klose_learning_admission as admission
import klose_release_curriculum as release_curriculum


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
                    "Status": "active",
                } if name == "new_concept_english_1" else {"Rank": rank, "Status": "active"})
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


    def test_identity_gated_nce1_does_not_enter_admission(self):
        with tempfile.TemporaryDirectory() as directory:
            source, scope, curriculum = self.fixture(Path(directory))
            cfg = json.loads(curriculum.read_text(encoding="utf-8"))
            cfg["Segments"]["new_concept_english_1"]["Status"] = "identity-gated"
            curriculum.write_text(json.dumps(cfg), encoding="utf-8")
            with patch.object(admission, "SOURCE_IDENTITIES", source), \
                 patch.object(admission, "G56_SCOPE", scope), \
                 patch.object(admission, "CURRICULUM", curriculum):
                ordered, grade4, nce1, grade56 = admission.current_scope()
            self.assertEqual(ordered, ["KV000001", "KV000002", "KV000003", "KV000004"])
            # KV000002 remains present through Grade 5, not through the gated NCE segment.
            self.assertEqual(nce1, set())
            self.assertEqual(grade4, {"KV000001"})
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


class NCE1ReleaseCurriculumTest(unittest.TestCase):
    def fixture(self, root: Path):
        source = root / "source.csv"
        scope = root / "scope.json"
        curriculum = root / "curriculum.json"
        tp = root / "third_party.csv"
        write_csv(source, [
            dict(SourceID="rj_start1", SourceEdition="klose-current",
                 SourceItemKey="grade4-upper-u01-o001|alpha", NoteID="KV000001",
                 Decision="reuse-existing", Status="confirmed"),
            dict(SourceID=release_curriculum.NCE_SOURCE_ID, SourceEdition=release_curriculum.NCE_SOURCE_EDITION,
                 SourceItemKey="nce1-o0001|beta", NoteID="KV000002",
                 Decision="reuse-existing", Status="confirmed"),
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
        curriculum.write_text(json.dumps({
            "Segments": {
                "grade4": {"Rank": 10, "Status": "active"},
                "new_concept_english_1": {
                    "Rank": 20, "Status": "active",
                    "SourceEdition": release_curriculum.NCE_SOURCE_EDITION,
                },
                "grade5": {"Rank": 30, "Status": "active"},
                "grade6": {"Rank": 40, "Status": "active"},
                "third_party": {"Rank": 90, "Status": "active"},
            }
        }), encoding="utf-8")
        fields = [
            "LearnerProfile", "LearnerLevel", "NoteID", "CurrentStatus", "CurrentLearningOrder",
            "ProposedStatus", "ProposedLearningTag", "ProposedLearningOrder", "AdmissionAction",
        ]
        with tp.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows([
                dict(LearnerProfile="klose", LearnerLevel="4", NoteID="KV000001",
                     CurrentStatus="allowed", CurrentLearningOrder="000001", ProposedStatus="allowed",
                     ProposedLearningTag=release_curriculum.TP_LEARNING_TAG,
                     ProposedLearningOrder="000001", AdmissionAction="preserve-allowed"),
                # Was previously third-party; NCE1 now owns the earlier coordinate.
                dict(LearnerProfile="klose", LearnerLevel="4", NoteID="KV000002",
                     CurrentStatus="allowed", CurrentLearningOrder="000900", ProposedStatus="allowed",
                     ProposedLearningTag=release_curriculum.TP_LEARNING_TAG,
                     ProposedLearningOrder="000900", AdmissionAction="preserve-allowed"),
                dict(LearnerProfile="klose", LearnerLevel="4", NoteID="KV000005",
                     CurrentStatus="allowed", CurrentLearningOrder="001000", ProposedStatus="allowed",
                     ProposedLearningTag=release_curriculum.TP_LEARNING_TAG,
                     ProposedLearningOrder="001000", AdmissionAction="preserve-allowed"),
                dict(LearnerProfile="klose", LearnerLevel="4", NoteID="KV000006",
                     CurrentStatus="allowed", CurrentLearningOrder="001200", ProposedStatus="allowed",
                     ProposedLearningTag=release_curriculum.TP_LEARNING_TAG,
                     ProposedLearningOrder="001200", AdmissionAction="preserve-allowed"),
            ])
        return source, scope, curriculum, tp

    def test_release_order_inserts_nce_and_rebases_third_party(self):
        with tempfile.TemporaryDirectory() as directory:
            source, scope, curriculum, tp = self.fixture(Path(directory))
            with patch.object(release_curriculum, "SOURCE_IDENTITY_EXTENSIONS", source), \
                 patch.object(release_curriculum, "G56_SCOPE", scope), \
                 patch.object(release_curriculum, "CURRICULUM", curriculum), \
                 patch.object(release_curriculum, "TP_PLAN", tp), \
                 patch("klose_current_policy.apply_decisions", side_effect=lambda ordered, state: (ordered, state)):
                ordered, state = release_curriculum.current_curriculum_ordered_note_ids()
            self.assertEqual(
                ordered,
                ["KV000001", "KV000002", "KV000003", "KV000004", "KV000005", "KV000006"],
            )
            self.assertEqual(state["KV000002"][0], release_curriculum.NCE_STAGE)
            self.assertEqual(state["KV000005"][0], release_curriculum.TP_STAGE)


if __name__ == "__main__":
    unittest.main()
