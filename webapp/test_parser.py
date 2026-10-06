#!/usr/bin/env python3
"""Unit tests for the QA test plan parser."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plan_parser import build_plan  # noqa: E402

PLAN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_plan():
    return build_plan(
        os.path.join(PLAN_DIR, "QA-TESTPLAN.md"),
        os.path.join(PLAN_DIR, "QA-TESTPLAN.de.md"),
    )


class PlanParserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load_plan()
        cls.cases = {case["id"]: case for case in cls.plan["cases"]}

    def test_case_count(self):
        self.assertEqual(len(self.plan["cases"]), 63)

    def test_ids_unique(self):
        ids = [case["id"] for case in self.plan["cases"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_expected_ids_present(self):
        for case_id in ("ENV-01", "BASE-16", "JAVA-16", "WEB-16", "MOB-07", "REG-04"):
            self.assertIn(case_id, self.cases)

    def test_groups(self):
        prefixes = [group["prefix"] for group in self.plan["groups"]]
        self.assertEqual(prefixes, ["ENV", "BASE", "JAVA", "WEB", "MOB", "REG"])

    def test_tier_distribution(self):
        tiers = {}
        for case in self.plan["cases"]:
            tiers.setdefault(case["tier"], 0)
            tiers[case["tier"]] += 1
        self.assertEqual(tiers, {0: 4, 1: 33, 2: 26})

    def test_language_merge(self):
        env01 = self.cases["ENV-01"]
        self.assertIn("Record versions", env01["title"]["en"])
        self.assertIn("Versionen erfassen", env01["title"]["de"])
        self.assertNotEqual(env01["title"]["en"], env01["title"]["de"])

    def test_template_not_parsed(self):
        self.assertNotIn("ID", self.cases)

    def test_steps_are_lists(self):
        for case in self.plan["cases"]:
            self.assertIsInstance(case["steps"]["en"], list)
            self.assertIsInstance(case["steps"]["de"], list)
            self.assertTrue(case["steps"]["en"], case["id"])
            self.assertTrue(case["steps"]["de"], case["id"])

    def test_all_cases_have_expected(self):
        for case in self.plan["cases"]:
            self.assertTrue(case["expected"]["en"], case["id"])
            self.assertTrue(case["expected"]["de"], case["id"])

    def test_metadata(self):
        base01 = self.cases["BASE-01"]
        self.assertEqual(base01["tier"], 1)
        self.assertEqual(base01["package"], "cranix-base")
        self.assertEqual(base01["priority"], "H")
        env01 = self.cases["ENV-01"]
        self.assertEqual(env01["packages"], ["all"])

    def test_env_fields(self):
        self.assertEqual(len(self.plan["envFields"]), 7)
        first = self.plan["envFields"][0]
        self.assertEqual(first["label"]["en"], "Server hostname / IP")
        self.assertEqual(first["label"]["de"], "Server-Hostname / IP")


if __name__ == "__main__":
    unittest.main()
