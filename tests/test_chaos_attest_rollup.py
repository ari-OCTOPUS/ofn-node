"""Owner-absent chaos for attest class + rollup pin.

Faults that must not flip UNKNOWN into a permission or a tamper
verdict. HALT is not a parameter. Send names stay sealed.
Ready ≠ authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.attest_class import (
    classify_file,
    classify_missing_expected,
    grants_send as attest_grants_send,
    halt_blocks_attest,
    ready_is_authorized as attest_ready,
    unknown_is_false,
    unknown_is_inconsistent,
    missing_expected_is_inconsistent,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.rollup_pin import (
    grants_send as rollup_grants_send,
    halt_blocks_rollup,
    ready_is_authorized as rollup_ready,
    rollup,
    truncated_is_consistent,
    unknown_file_is_inconsistent,
)

_HEX_A = "a" * 64
_HEX_B = "b" * 64


class ChaosUnknownStaysUnknown(unittest.TestCase):
    def test_unreadable_under_pressure_to_call_it_tamper(self):
        d = classify_file(
            path="locked.md", readable=False,
            observed_sha=_HEX_A, expected_sha=_HEX_B)
        self.assertEqual(d.verdict, "unknown")
        self.assertFalse(unknown_is_inconsistent())
        self.assertFalse(unknown_is_false())
        self.assertFalse(d.grants_send)

    def test_missing_expected_under_pressure_to_call_it_tamper(self):
        d = classify_missing_expected(path="SEASON-LOG.md")
        self.assertEqual(d.verdict, "incomplete")
        self.assertFalse(missing_expected_is_inconsistent())

    def test_unknown_file_cannot_be_rolled_into_tamper_or_grant(self):
        d = rollup(file_verdicts=("unknown",), truncated=False)
        self.assertEqual(d.verdict, "incomplete")
        self.assertFalse(unknown_file_is_inconsistent())
        self.assertFalse(d.grants_send)


class ChaosHaltAndSend(unittest.TestCase):
    def test_halt_is_not_a_parameter_on_either_entry(self):
        self.assertFalse(halt_blocks_attest())
        self.assertFalse(halt_blocks_rollup())
        for fn in (classify_file, classify_missing_expected, rollup):
            params = inspect.signature(fn).parameters
            self.assertNotIn("halt", params)
            self.assertNotIn("halt_raw", params)

    def test_neither_entry_grants_send(self):
        self.assertFalse(attest_grants_send())
        self.assertFalse(rollup_grants_send())
        match = classify_file(
            path="a.md", readable=True,
            observed_sha=_HEX_A, expected_sha=_HEX_A)
        tree = rollup(file_verdicts=("consistent",), truncated=False)
        self.assertFalse(match.grants_send)
        self.assertFalse(tree.grants_send)

    def test_ready_is_not_authorized_on_either_module(self):
        self.assertFalse(attest_ready())
        self.assertFalse(rollup_ready())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_sealed_names_stay_sealed_under_chaos(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_file(path=name, readable=False)
                with self.assertRaises(FailClosedError):
                    classify_missing_expected(path=name)
                with self.assertRaises(FailClosedError):
                    rollup(file_verdicts=(name,), truncated=False)

    def test_truncated_walk_cannot_be_argued_consistent(self):
        d = rollup(
            file_verdicts=("consistent",) * 8, truncated=True)
        self.assertEqual(d.verdict, "incomplete")
        self.assertFalse(truncated_is_consistent())

    def test_inconsistent_still_wins_when_halt_would_be_tempting(self):
        d = rollup(
            file_verdicts=("unknown", "inconsistent", "incomplete"),
            truncated=True)
        self.assertEqual(d.verdict, "inconsistent")
        self.assertFalse(d.grants_send)


if __name__ == "__main__":
    unittest.main()
