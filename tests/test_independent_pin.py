"""Kernel-pure independent pin — complementary to approval_class.

UNKNOWN is not FALSE. Lowering required-approvals does not satisfy.
Ready is not authorized. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.independent_pin import (
    PIN_VERDICTS,
    PinDecision,
    author_self_satisfies,
    bot_satisfies,
    claims_immutable,
    grants_send,
    halt_blocks_pin,
    pin_independent,
    proposal_is_execution,
    ready_is_authorized,
    unknown_is_false,
    unknown_is_satisfied,
    unlisted_satisfies,
    zero_required_satisfies,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_unknown_is_not_satisfied(self):
        self.assertFalse(unknown_is_satisfied())

    def test_author_self_does_not_satisfy(self):
        self.assertFalse(author_self_satisfies())

    def test_bot_does_not_satisfy(self):
        self.assertFalse(bot_satisfies())

    def test_unlisted_does_not_satisfy(self):
        self.assertFalse(unlisted_satisfies())

    def test_zero_required_does_not_satisfy(self):
        self.assertFalse(zero_required_satisfies())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_closed_vocabulary(self):
        self.assertEqual(
            PIN_VERDICTS, {"satisfied", "unsatisfied", "unknown"})

    def test_pin_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(pin_independent).parameters
        self.assertEqual(list(params), ["verdicts", "required"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            PinDecision(
                verdict="unknown", required=1,
                independent_count=0, unknown_count=1,
                grants_send=True)

    def test_constructor_refuses_satisfied_below_required(self):
        with self.assertRaises(FailClosedError):
            PinDecision(
                verdict="satisfied", required=2,
                independent_count=1, unknown_count=0)

    def test_constructor_refuses_unsatisfied_with_unknown(self):
        with self.assertRaises(FailClosedError):
            PinDecision(
                verdict="unsatisfied", required=1,
                independent_count=0, unknown_count=1)

    def test_constructor_refuses_unsatisfied_when_count_meets(self):
        with self.assertRaises(FailClosedError):
            PinDecision(
                verdict="unsatisfied", required=1,
                independent_count=1, unknown_count=0)

    def test_constructor_refuses_required_zero(self):
        with self.assertRaises(FailClosedError):
            PinDecision(
                verdict="unknown", required=0,
                independent_count=0, unknown_count=0)

    def test_constructor_refuses_foreign_verdict(self):
        with self.assertRaises(FailClosedError):
            PinDecision(
                verdict="ok", required=1,
                independent_count=0, unknown_count=0)


class PinSatisfied(unittest.TestCase):
    def test_one_independent_satisfies_required_one(self):
        d = pin_independent(verdicts=("independent",), required=1)
        self.assertEqual(d.verdict, "satisfied")
        self.assertEqual(d.independent_count, 1)
        self.assertEqual(d.unknown_count, 0)
        self.assertFalse(d.grants_send)

    def test_independent_plus_noise_still_satisfies(self):
        d = pin_independent(
            verdicts=("bot", "author_self", "independent", "unlisted"),
            required=1)
        self.assertEqual(d.verdict, "satisfied")
        self.assertEqual(d.independent_count, 1)

    def test_two_independent_satisfies_required_two(self):
        d = pin_independent(
            verdicts=("independent", "independent"), required=2)
        self.assertEqual(d.verdict, "satisfied")
        self.assertEqual(d.required, 2)

    def test_empty_complete_set_is_unsatisfied_not_satisfied(self):
        d = pin_independent(verdicts=(), required=1)
        self.assertEqual(d.verdict, "unsatisfied")
        self.assertEqual(d.independent_count, 0)


class PinUnsatisfied(unittest.TestCase):
    def test_only_author_self_is_unsatisfied(self):
        d = pin_independent(verdicts=("author_self",), required=1)
        self.assertEqual(d.verdict, "unsatisfied")
        self.assertFalse(author_self_satisfies())
        self.assertFalse(d.grants_send)

    def test_only_bot_is_unsatisfied(self):
        d = pin_independent(verdicts=("bot",), required=1)
        self.assertEqual(d.verdict, "unsatisfied")
        self.assertFalse(bot_satisfies())

    def test_only_unlisted_is_unsatisfied(self):
        d = pin_independent(verdicts=("unlisted",), required=1)
        self.assertEqual(d.verdict, "unsatisfied")
        self.assertFalse(unlisted_satisfies())

    def test_author_self_and_bot_together_do_not_satisfy(self):
        d = pin_independent(
            verdicts=("author_self", "bot"), required=1)
        self.assertEqual(d.verdict, "unsatisfied")

    def test_one_independent_does_not_satisfy_required_two(self):
        d = pin_independent(
            verdicts=("independent", "bot"), required=2)
        self.assertEqual(d.verdict, "unsatisfied")
        self.assertEqual(d.independent_count, 1)


class PinUnknown(unittest.TestCase):
    def test_unknown_alone_is_unknown_not_unsatisfied(self):
        d = pin_independent(verdicts=("unknown",), required=1)
        self.assertEqual(d.verdict, "unknown")
        self.assertFalse(unknown_is_false())
        self.assertFalse(unknown_is_satisfied())
        self.assertFalse(d.grants_send)

    def test_unknown_plus_bot_stays_unknown(self):
        d = pin_independent(
            verdicts=("bot", "unknown"), required=1)
        self.assertEqual(d.verdict, "unknown")
        self.assertEqual(d.unknown_count, 1)

    def test_independent_wins_over_unknown(self):
        d = pin_independent(
            verdicts=("unknown", "independent"), required=1)
        self.assertEqual(d.verdict, "satisfied")
        self.assertEqual(d.unknown_count, 1)


class FailClosedInputs(unittest.TestCase):
    def test_missing_verdicts_is_unknown_not_empty(self):
        with self.assertRaises(FailClosedError):
            pin_independent(verdicts=None, required=1)

    def test_string_verdicts_is_not_a_list(self):
        with self.assertRaises(FailClosedError):
            pin_independent(verdicts="independent", required=1)

    def test_missing_required_is_unknown_not_one(self):
        with self.assertRaises(FailClosedError):
            pin_independent(verdicts=("independent",), required=None)

    def test_required_zero_does_not_satisfy(self):
        with self.assertRaises(FailClosedError):
            pin_independent(verdicts=(), required=0)
        self.assertFalse(zero_required_satisfies())

    def test_required_negative_refuses(self):
        with self.assertRaises(FailClosedError):
            pin_independent(verdicts=("independent",), required=-1)

    def test_bool_required_refuses(self):
        with self.assertRaises(FailClosedError):
            pin_independent(verdicts=("independent",), required=True)

    def test_sealed_verdict_refuses(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    pin_independent(verdicts=(name,), required=1)

    def test_foreign_verdict_refuses(self):
        with self.assertRaises(FailClosedError):
            pin_independent(verdicts=("ok",), required=1)


if __name__ == "__main__":
    unittest.main()
