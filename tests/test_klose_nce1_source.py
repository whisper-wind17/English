from pathlib import Path
import unittest

from tools.klose_nce1_source import DEFAULT_XLSX, read_first_sheet


class NCE1SourceAdapterTest(unittest.TestCase):
    def test_xlsx_is_readable_and_nontrivial(self):
        rows = read_first_sheet(DEFAULT_XLSX)
        print("NCE1_XLSX_SAMPLE", rows[:8])
        self.assertGreater(len(rows), 800)
        self.assertLess(len(rows), 1000)
        self.assertTrue(any("excuse" in " ".join(r).lower() for r in rows[:20]))


if __name__ == "__main__":
    unittest.main()
