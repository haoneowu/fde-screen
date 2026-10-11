"""Owner: APU Workshop. Updated: 2026-10-11.
Change Log: 2026-10-07 Add offline ranking boundary and identity regression tests.
"""
import csv
import unittest
from unittest.mock import patch
from school_lookup import REFERENCE, lookup, lookup_either, rank_bounds


class SchoolLookupTests(unittest.TestCase):
    def test_cn100_boundary_and_derived_list(self):
        self.assertEqual(lookup('domestic', '华南农业大学')['ranking_status'], 'within_cutoff')
        self.assertEqual(lookup('domestic', '山西大学')['ranking_status'], 'outside_cutoff')
        self.assertEqual(lookup('domestic', '华侨大学')['ranking_status'], 'outside_cutoff')
        self.assertEqual(lookup('domestic', '华南农业大学')['cutoff'], 100)
        self.assertEqual(lookup('overseas', 'University of Bath')['cutoff'], 150)
        with (REFERENCE / 'schools-2025-cn.csv').open(encoding='utf-8', newline='') as f:
            expected = [r for r in csv.DictReader(f) if rank_bounds(r['rank'])[1] <= 100]
        with (REFERENCE / 'schools-2025-cn-top100.csv').open(encoding='utf-8', newline='') as f:
            self.assertEqual(list(csv.DictReader(f)), expected)
        self.assertEqual(len(expected), 100)

    def test_domestic_coverage(self):
        with (REFERENCE / "schools-2025-cn.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 589)
        self.assertEqual(len({r["name"] for r in rows}), 589)
        self.assertEqual(sum(rank_bounds(r["rank"])[1] <= 150 for r in rows), 150)

    def test_cutoff(self):
        self.assertEqual(lookup("domestic", "湖南师范大学")["ranking_status"], "within_cutoff")
        self.assertEqual(lookup("domestic", "南通大学")["ranking_status"], "outside_cutoff")
        self.assertEqual(lookup("domestic", "湖北工业大学")["ranking_status"], "outside_cutoff")

    def test_no_parent_inheritance(self):
        for name in ["厦门大学嘉庚学院", "广东工业大学华立学院", "清华大学某独立学院", "北大"]:
            self.assertNotEqual(lookup("domestic", name)["ranking_status"], "within_cutoff")
        self.assertEqual(lookup("domestic", "厦门大学")["ranking_status"], "within_cutoff")

    def test_unlisted_and_campus_need_review(self):
        for name in ["不存在的大学", "哈尔滨工业大学（威海）", "中央财经大学", ""]:
            self.assertEqual(lookup("domestic", name)["g1"], "待核验")

    def test_english_and_whitespace(self):
        self.assertEqual(lookup("domestic", "  TSINGHUA   UNIVERSITY ")["ranking_status"], "within_cutoff")
        self.assertEqual(lookup("domestic", "清华大学")["g1"], "待核验")

    def test_qs_coverage_and_boundary(self):
        with (REFERENCE / "schools-2025-qs.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 200)
        self.assertEqual(len({r["name"] for r in rows}), 200)
        self.assertEqual(sum(rank_bounds(r["rank"])[1] <= 150 for r in rows), 151)
        for name in ["University of Bath", "Indian Institute of Technology Delhi (IITD)"]:
            result = lookup("overseas", name)
            self.assertEqual(result["ranking_status"], "within_cutoff")
            self.assertEqual(result["g1"], "待核验")
        self.assertEqual(lookup("overseas", "Michigan State University")["ranking_status"], "outside_cutoff")
        self.assertEqual(lookup("overseas", "Washington University in St. Louis")["match"]["rank"], "176")

    def test_qs_routing(self):
        for name in ["Tsinghua University", "The University of Hong Kong", "National Taiwan University (NTU)"]:
            self.assertEqual(lookup_either(name)["ranking_status"], "within_cutoff")
        self.assertEqual(lookup("overseas", "牛津大学")["ranking_status"], "unmatched")

    def test_either_and_entity(self):
        for name in ["清华大学", "湖南师范大学", "University of Bath"]:
            self.assertEqual(lookup_either(name)["ranking_status"], "within_cutoff")
        for name in ["宁波诺丁汉大学", "University of Nottingham Ningbo China", "厦门大学嘉庚学院", "南通大学", ""]:
            self.assertEqual(lookup_either(name)["g1"], "待核验")
            self.assertNotEqual(lookup_either(name)["ranking_status"], "within_cutoff")
        self.assertEqual(lookup("domestic", "南通大学")["g1"], "待核验")
        self.assertEqual(lookup_either("University of Nottingham")["ranking_status"], "within_cutoff")

    def test_rank_formats(self):
        self.assertEqual(rank_bounds("=150"), (150, 150))
        self.assertEqual(rank_bounds("151–200"), (151, 200))
        self.assertGreater(rank_bounds("500+")[0], 150)
        self.assertEqual(rank_bounds("N/A"), (None, None))

    def test_or_truth_table(self):
        cases = [
            ("outside_cutoff", "within_cutoff", "within_cutoff"),
            ("within_cutoff", "outside_cutoff", "within_cutoff"),
            ("outside_cutoff", "outside_cutoff", "outside_both_cutoffs"),
            ("outside_cutoff", "unmatched", "pending_verification"),
            ("unmatched", "unmatched", "pending_verification"),
            ("data_unavailable", "within_cutoff", "within_cutoff"),
        ]
        for cn, qs, expected in cases:
            with self.subTest(cn=cn, qs=qs):
                def fake(scope, school):
                    return {"ranking_status": cn if scope == "domestic" else qs}
                with patch("school_lookup.lookup", side_effect=fake):
                    result = lookup_either("Test institution")
                self.assertEqual(result["ranking_status"], expected)
                if expected != "outside_both_cutoffs":
                    self.assertEqual(result["g1"], "待核验")


if __name__ == "__main__":
    unittest.main()
