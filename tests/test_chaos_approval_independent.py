"""Owner-absent chaos for approval class + independent pin.

Faults that must not flip UNKNOWN, author-self, or bot into an
independence grant. HALT is not a parameter. Send names stay sealed.
Ready ≠ authorized. Lowering required-approvals does not satisfy.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.approval_class import (
    classify_approval,
    grants_send as approval_grants_send,
    halt_blocks_approval,
    ready_is_authorized as approval_ready,
    unknown_is_false,
    unknown_is_independent,
    author_self_is_independent,
    bot_is_independent,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.independent_pin import (
    grants_send as pin_grants_send,
    halt_blocks_pin,
    pin_independent,
    ready_is_authorized as pin_ready,
    unknown_is_satisfied,
    zero_required_satisfies,
)

_VALID = frozenset({"rev-a", "rev-b"})


class ChaosUnknownStaysUnknown(unittest.TestCase):
    def test_missing_approver_under_pressure_to_call_it_independent(self):
        d = classify_approval(
            author="writer", approver=None,
            state="APPROVED", valid_reviewers=_VALID)
        self.assertEqual(d.verdict, "unknown")
        self.assertFalse(unknown_is_independent())
        self.assertFalse(unknown_is_false())
        self.assertFalse(d.grants_send)

    def test_unknown_pin_cannot_be_argued_satisfied(self):
        d = pin_independent(verdicts=("unknown", "bot"), required=1)
        self.assertEqual(d.verdict, "unknown")
        self.assertFalse(unknown_is_satisfied())
        self.assertFalse(d.grants_send)


class ChaosAuthorAndBot(unittest.TestCase):
    def test_author_self_under_pressure_to_count(self):
        d = classify_approval(
            author="writer", approver="writer",
            state="APPROVED", valid_reviewers=_VALID)
        pin = pin_independent(verdicts=(d.verdict,), required=1)
        self.assertEqual(d.verdict, "author_self")
        self.assertEqual(pin.verdict, "unsatisfied")
        self.assertFalse(author_self_is_independent())

    def test_bot_under_pressure_to_count(self):
        d = classify_approval(
            author="writer", approver="cursor[bot]",
            state="APPROVED", valid_reviewers=_VALID)
        pin = pin_independent(verdicts=(d.verdict,), required=1)
        self.assertEqual(d.verdict, "bot")
        self.assertEqual(pin.verdict, "unsatisfied")
        self.assertFalse(bot_is_independent())

    def test_author_plus_bot_still_unsatisfied(self):
        pin = pin_independent(
            verdicts=("author_self", "bot"), required=1)
        self.assertEqual(pin.verdict, "unsatisfied")
        self.assertFalse(pin.grants_send)


class ChaosHaltAndSend(unittest.TestCase):
    def test_halt_is_not_a_parameter_on_either_entry(self):
        self.assertFalse(halt_blocks_approval())
        self.assertFalse(halt_blocks_pin())
        for fn in (classify_approval, pin_independent):
            params = inspect.signature(fn).parameters
            self.assertNotIn("halt", params)
            self.assertNotIn("halt_raw", params)

    def test_neither_entry_grants_send(self):
        self.assertFalse(approval_grants_send())
        self.assertFalse(pin_grants_send())
        d = classify_approval(
            author="writer", approver="rev-a",
            state="APPROVED", valid_reviewers=_VALID)
        pin = pin_independent(verdicts=(d.verdict,), required=1)
        self.assertFalse(d.grants_send)
        self.assertFalse(pin.grants_send)

    def test_ready_is_not_authorized_on_either_module(self):
        self.assertFalse(approval_ready())
        self.assertFalse(pin_ready())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_sealed_names_stay_sealed_under_chaos(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_approval(
                        author=name, approver="rev-a",
                        state="APPROVED", valid_reviewers=_VALID)
                with self.assertRaises(FailClosedError):
                    classify_approval(
                        author="writer", approver=name,
                        state="APPROVED", valid_reviewers=_VALID)
                with self.assertRaises(FailClosedError):
                    pin_independent(verdicts=(name,), required=1)

    def test_lowering_required_cannot_be_argued_under_chaos(self):
        with self.assertRaises(FailClosedError):
            pin_independent(verdicts=("bot",), required=0)
        self.assertFalse(zero_required_satisfies())


if __name__ == "__main__":
    unittest.main()
