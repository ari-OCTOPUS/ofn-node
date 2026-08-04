"""The two time questions are gone, everywhere.

Removed by the owner on 2026-08-04 after watching the first real session:
"چند ساعت وقت برد؟" and "ساعتی چند؟". A piece now costs what was bought for
it — materials and packaging.

This reverses a decision the pack argued for in a comment, and the comment
was right: a piece priced against materials alone looks profitable at exactly
the price that loses money. That trade is the owner's to make. What these
tests protect is that it was made *once and completely* — a half-removed
question is worse than either answer, because the field survives somewhere
nobody is looking and starts collecting zeroes that later get averaged.

So: gone from the form, gone from the pack, gone from the API, and gone from
the formula. The two columns stay in the database file — dropping a column
rewrites the table, and an unread column costs nothing — but nothing writes
them again.
"""

from __future__ import annotations

import os
import re
import unittest

from ofn.adapters.packloader import load_pack
from ofn.adapters.products import EDITABLE, cogs_for
from ofn.node import _PRODUCT_NUMERIC

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "web")
PACK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "packs", "ziman.yaml")
GONE = ("labour_hours", "hourly_rate_aud")


class TestTheFormNoLongerAsks(unittest.TestCase):
    def setUp(self):
        src = open(os.path.join(WEB, "ziman.html"), encoding="utf-8").read()
        self.js = re.sub(r"/\*.*?\*/|<!--.*?-->", "", src, flags=re.S)

    def test_neither_question_is_a_step(self):
        steps = re.search(r"const STEPS = \[(.*?)\n\];", self.js, re.S)
        self.assertIsNotNone(steps)
        for key in GONE:
            self.assertNotIn(key, steps.group(1))

    def test_the_wording_is_gone_from_the_page(self):
        for phrase in ("چند ساعت وقت برد", "ساعتی چند"):
            self.assertNotIn(phrase, self.js)

    def test_the_running_cost_is_materials_plus_packaging(self):
        body = re.search(r"function costNow\(\) \{(.*?)\n\}", self.js, re.S)
        self.assertIsNotNone(body)
        self.assertIn("materials_cost_aud", body.group(1))
        self.assertIn("packaging_cost_aud", body.group(1))
        for key in GONE:
            self.assertNotIn(key, body.group(1))

    def test_the_summary_does_not_bill_for_time(self):
        summary = re.search(r"function drawSummary\(\) \{(.*?)\n\}", self.js, re.S)
        self.assertIsNotNone(summary)
        self.assertNotIn("وقت شما", summary.group(1))

    def test_the_shell_no_longer_reads_the_hourly_fact(self):
        self.assertNotIn("time.hourly_floor", self.js)
        self.assertNotIn("hourlyDefault", self.js)


class TestThePackNoLongerDeclaresIt(unittest.TestCase):
    def setUp(self):
        self.pack = load_pack(PACK)

    def test_the_formula_has_no_labour_term(self):
        self.assertEqual(self.pack.labour_hours_field, "")
        self.assertEqual(self.pack.labour_rate_field, "")

    def test_cost_is_still_materials_and_packaging(self):
        self.assertEqual(self.pack.cost_fields,
                         ("materials_cost_aud", "packaging_cost_aud"))

    def test_the_hourly_fact_is_neither_required_nor_worded(self):
        self.assertNotIn("time.hourly_floor", self.pack.required_facts)
        self.assertNotIn("time.hourly_floor", self.pack.question_meta)

    def test_the_pack_file_mentions_time_only_to_explain_its_absence(self):
        """The reversal is written down. If the loss warning never fires,
        the answer should be findable rather than rediscovered."""
        raw = open(PACK, encoding="utf-8").read()
        for key in GONE:
            for line in raw.splitlines():
                if key in line:
                    self.assertTrue(line.lstrip().startswith("#"),
                                    f"{key} is still live config: {line}")

    def test_the_required_facts_have_no_duplicate_keys(self):
        """They did. The same fact appeared twice — once with a label and
        once bare — and YAML silently kept the last one, so those labels were
        never read by anything."""
        raw = open(PACK, encoding="utf-8").read()
        block = re.search(r"\nrequired_facts:\n(.*?)\n\S", raw, re.S)
        self.assertIsNotNone(block)
        keys = re.findall(r"^  ([\w.]+):", block.group(1), re.M)
        self.assertEqual(sorted(keys), sorted(set(keys)))


class TestTheApiRefusesThem(unittest.TestCase):
    def test_neither_field_is_editable(self):
        for key in GONE:
            self.assertNotIn(key, EDITABLE)

    def test_neither_field_is_accepted_as_a_number(self):
        for key in GONE:
            self.assertNotIn(key, _PRODUCT_NUMERIC)


class TestTheFormulaIgnoresThem(unittest.TestCase):
    FORMULA = dict(cost_fields=("materials_cost_aud", "packaging_cost_aud"),
                   labour_hours_field="", labour_rate_field="")

    def test_time_in_the_input_changes_nothing(self):
        """A row still carrying yesterday's hours must not have them
        resurface in a cost computed today."""
        with_time = cogs_for({"materials_cost_aud": 40.0,
                              "packaging_cost_aud": 3.0,
                              "labour_hours": 24.0,
                              "hourly_rate_aud": 30.0}, **self.FORMULA)
        self.assertAlmostEqual(with_time, 43.0)

    def test_an_empty_field_name_does_not_match_an_empty_key(self):
        """`labour_hours_field=""` must mean "no labour term", not "look up
        the field called empty string"."""
        self.assertAlmostEqual(
            cogs_for({"materials_cost_aud": 10.0, "": 999.0}, **self.FORMULA),
            10.0)


if __name__ == "__main__":
    unittest.main()
