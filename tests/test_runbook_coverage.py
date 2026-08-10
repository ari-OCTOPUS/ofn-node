"""Runbook coverage: the eight promised runbooks exist with the required
titles. A runbook that does not exist is a promise with no delivery — the
megaprompt (finding 41) names eight of them explicitly."""

from __future__ import annotations

import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNBOOKS = os.path.join(ROOT, "docs", "runbooks")

REQUIRED = {
    "NTP.md": "NTP",
    "TUNNEL.md": "تونل",
    "RESTORE.md": "بازیابی",
    "INBOX-HELD.md": "صندوق ورودی",
    "OUTBOX-HELD.md": "صف خروج",
    "WEBHOOK-SIGNATURE.md": "امضای وب‌هوک",
    "RATE-SPIKE.md": "موج درخواست",
    "SCHEMA-DRIFT.md": "انحراف اسکیما",
    "RETENTION.md": "retention",
}


class TestRunbookCoverage(unittest.TestCase):
    def test_all_eight_runbooks_exist(self):
        for name in REQUIRED:
            with self.subTest(runbook=name):
                path = os.path.join(RUNBOOKS, name)
                self.assertTrue(os.path.isfile(path),
                                f"{name} missing from docs/runbooks/")

    def test_each_runbook_has_its_title(self):
        for name, title in REQUIRED.items():
            with self.subTest(runbook=name):
                with open(os.path.join(RUNBOOKS, name),
                          encoding="utf-8") as fh:
                    first_line = fh.readline()
                self.assertIn(title, first_line,
                              f"{name} should open with its title")
