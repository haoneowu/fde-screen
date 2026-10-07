"""Owner: APU Workshop. Updated: 2026-10-07.
Change Log: 2026-10-07 Add offline ranking boundary and identity regression tests.
"""
import csv
import unittest
from school_lookup import REFERENCE, lookup, rank_bounds


class SchoolLookupTests(unittest.TestCase):
    def test_domestic_coverage(self):
        with (REFERENCE / "schools-2025-cn.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 589)
        self.assertEqual(len({r["name"] for r in rows}), 589)
        self.assertEqual(sum(rank_bounds(r["rank"])[1] <= 150 for r in rows), 150)

    def test_cutoff(self):
        self.assertEqual(lookup("domestic", "浙江农林大学")["ranking_status"], "within_top150")
        self.assertEqual(lookup("domestic", "南通大学")["ranking_status"], "outside_top150")
        self.assertEqual(lookup("domestic", "湖北工业大学")["ranking_status"], "within_top150")

    def test_no_parent_inheritance(self):
        for name in ["厦门大学嘉庚学院", "广东工业大学华立学院", "清华大学某独立学院", "北大"]:
            self.assertNotEqual(lookup("domestic", name)["ranking_status"], "within_top150")
        self.assertEqual(lookup("domestic", "厦门大学")["ranking_status"], "within_top150")

    def test_unlisted_and_campus_need_review(self):
        for name in ["不存在的大学", "哈尔滨工业大学（威海）", "中央财经大学", ""]:
            self.assertEqual(lookup("domestic", name)["g1"], "待核验")

    def test_english_and_whitespace(self):
        self.assertEqual(lookup("domestic", "  TSINGHUA   UNIVERSITY ")["ranking_status"], "within_top150")
        self.assertEqual(lookup("domestic", "清华大学")["g1"], "待核验")

    def test_qs_coverage_and_boundary(self):
        with (REFERENCE / "schools-2025-qs.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 200)
        self.assertEqual(len({r["name"] for r in rows}), 200)
        self.assertEqual(sum(rank_bounds(r["rank"])[1] <= 150 for r in rows), 151)
        for name in ["University of Bath", "Indian Institute of Technology Delhi (IITD)"]:
            result = lookup("overseas", name)
            self.assertEqual(result["ranking_status"], "within_top150")
            self.assertEqual(result["g1"], "待核验")
        self.assertEqual(lookup("overseas", "Michigan State University")["ranking_status"], "outside_top150")
        self.assertEqual(lookup("overseas", "Washington University in St. Louis")["match"]["rank"], "176")

    def test_qs_routing(self):
        self.assertEqual(lookup("overseas", "Tsinghua University")["ranking_status"], "wrong_scope")
        self.assertEqual(lookup("overseas", "The University of Hong Kong")["ranking_status"], "scope_review")
        self.assertEqual(lookup("overseas", "National Taiwan University (NTU)")["ranking_status"], "scope_review")
        self.assertEqual(lookup("overseas", "牛津大学")["ranking_status"], "unmatched")

    def test_rank_formats(self):
        self.assertEqual(rank_bounds("=150"), (150, 150))
        self.assertEqual(rank_bounds("151–200"), (151, 200))
        self.assertGreater(rank_bounds("500+")[0], 150)
        self.assertEqual(rank_bounds("N/A"), (None, None))


if __name__ == "__main__":
    unittest.main()
