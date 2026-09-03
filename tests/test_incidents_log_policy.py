"""Incidents-log policy — mechanically checked (evidence-hardening round).

The log must stay an append-only operational record: entries in date
order, no verbatim document mirrors (YAML frontmatter of external docs
was the giveaway last time), and the pointer+hash policy line present.
"""

from __future__ import annotations

import os
import re
import unittest

LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "docs", "octopus-os", "07-INCIDENTS.md")

DATE_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})", re.M)


class AppendOnlyPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(LOG, encoding="utf-8") as f:
            cls.text = f.read()

    def test_file_exists_and_nonempty(self):
        self.assertTrue(os.path.exists(LOG))
        self.assertGreater(len(self.text), 200)

    def test_entries_are_in_ascending_date_order(self):
        dates = DATE_RE.findall(self.text)
        self.assertTrue(dates, "no dated entries found")
        self.assertEqual(dates, sorted(dates),
                         "log entries out of order — append-only violated")

    def test_no_verbatim_document_mirrors(self):
        # External docs carried YAML frontmatter (`---\ntitle:`); the log
        # itself must never embed one.
        self.assertNotRegex(self.text, re.compile(r"^---\s*$\n^title:", re.M))

    def test_pointer_policy_line_present(self):
        self.assertIn("pointer", self.text)
        self.assertIn("SHA-256", self.text)


if __name__ == "__main__":
    unittest.main()
