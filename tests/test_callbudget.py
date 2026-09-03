"""CallBudget clock + send pin — complementary to #82/#83/#87/#88/#93.

``day_index`` used to coerce with ``int()``. That treated True as day 0
and would have accepted a string timestamp. The clock is now exact-int,
matching the envelope/store rule, without touching those owned files.

HALT is not a parameter (stops STARTS, not in-flight counting).
Ready ≠ authorized. Docs/06-TOKEN-BUDGETS.yaml numbers are tests.
"""

from __future__ import annotations

import inspect
import os
import re
import unittest

from ofn.kernel.callbudget import (
    DAY,
    DEFAULT_CAPS,
    SEND_STATES,
    CallBudget,
    day_index,
    grants_send,
    require_epoch_s,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.routing import Rung

NOW = 1_785_000_000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUDGETS = os.path.join(ROOT, "docs", "octopus-os", "06-TOKEN-BUDGETS.yaml")
_CAP_LINE = re.compile(
    r"^\s+(RULES|LOCAL|REMOTE|REMOTE_DEEP):\s+(\d+)\b", re.M)


class ExactIntClock(unittest.TestCase):
    def test_require_epoch_s_accepts_non_negative_int(self):
        self.assertEqual(require_epoch_s(0), 0)
        self.assertEqual(require_epoch_s(NOW), NOW)

    def test_bool_float_str_negative_refused(self):
        for bad in (True, False, 1.5, "1785000000", -1, None, NOW + 0.0):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    require_epoch_s(bad)

    def test_day_index_refuses_coerced_clocks(self):
        self.assertEqual(day_index(NOW), NOW // DAY)
        for bad in (True, 1.9, "0", -DAY):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    day_index(bad)

    def test_allows_spent_record_report_share_the_clock_gate(self):
        b = CallBudget()
        for bad in (True, 1.5, "now"):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    b.allows(Rung.REMOTE, bad)
                with self.assertRaises(FailClosedError):
                    b.spent(Rung.REMOTE, bad)
                with self.assertRaises(FailClosedError):
                    b.record(Rung.REMOTE, bad)
                with self.assertRaises(FailClosedError):
                    b.report(bad)


class CapsAreCaps(unittest.TestCase):
    def test_yaml_daily_caps_match_default_caps(self):
        with open(BUDGETS, encoding="utf-8") as fh:
            text = fh.read()
        documented = {name: int(value) for name, value in _CAP_LINE.findall(text)}
        self.assertEqual(
            documented,
            {
                "RULES": DEFAULT_CAPS[Rung.RULES],
                "LOCAL": DEFAULT_CAPS[Rung.LOCAL],
                "REMOTE": DEFAULT_CAPS[Rung.REMOTE],
                "REMOTE_DEEP": DEFAULT_CAPS[Rung.REMOTE_DEEP],
            },
        )

    def test_remote_hundredth_is_last_allowed(self):
        b = CallBudget()
        for _ in range(100):
            self.assertTrue(b.allows(Rung.REMOTE, NOW))
            b.record(Rung.REMOTE, NOW)
        self.assertFalse(b.allows(Rung.REMOTE, NOW))
        self.assertEqual(b.spent(Rung.REMOTE, NOW), 100)
        self.assertEqual(b.remaining(Rung.REMOTE, NOW), 0)

    def test_rules_rung_stays_open_after_remote_exhausted(self):
        b = CallBudget()
        for _ in range(100):
            b.record(Rung.REMOTE, NOW)
        self.assertTrue(b.allows(Rung.RULES, NOW))
        self.assertIsNone(b.remaining(Rung.RULES, NOW))


class HaltIsNotAParameter(unittest.TestCase):
    def test_allows_and_record_have_no_halted_kwarg(self):
        for fn in (CallBudget.allows, CallBudget.record, CallBudget.spent,
                   CallBudget.remaining, CallBudget.report, day_index):
            params = inspect.signature(fn).parameters
            self.assertNotIn("halted", params)
            self.assertNotIn("halt", params)


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertFalse(CallBudget().grants_send())

    def test_send_and_ready_names_are_listed_but_not_granted(self):
        self.assertIn("send_authorized", SEND_STATES)
        self.assertIn("quote_sent", SEND_STATES)
        self.assertIn("campaign_envelope_ready", SEND_STATES)
        report = CallBudget().report(NOW)
        leaked = SEND_STATES.intersection(report)
        self.assertEqual(leaked, set())

    def test_report_rung_keys_only(self):
        report = CallBudget().report(NOW)
        self.assertEqual(set(report), {r.value for r in DEFAULT_CAPS})


if __name__ == "__main__":
    unittest.main()
