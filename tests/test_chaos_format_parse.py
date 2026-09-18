"""Owner-absent chaos — format-class + parse-pin (independent of #82).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the format/parse layer:
no fabricated witness, no store write, no run_id mint. HALT
stops STARTS only. One arm's timeout cannot mark another arm
as a race. Recovery is inspect/peek and is still not a send.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.format_class import (
    admit_format,
    classify_timeout,
    grants_send as format_grants_send,
    halt_blocks_inspect,
    mints_run_id,
    ready_is_authorized as format_ready,
    timeout_proves_concurrent as format_timeout_proves,
)
from ofn.kernel.parse_pin import (
    grants_send as parse_grants_send,
    halt_blocks_peek,
    pin_parse,
    ready_is_authorized as parse_ready,
    timeout_proves_concurrent as parse_timeout_proves,
)

_RUN_A = "run-1780000000-armaaaaaaa"
_RUN_B = "run-1780000000-armbbbbbbb"
_RUN_C = "run-1780000000-armccccccc"


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_family_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_format(intended="inspect", family="DEAD_SOURCE", value=_RUN_A)
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_malformed_is_unknown_not_false(self):
        d = admit_format(intended="inspect", family="run_id", value="DEAD")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertIsNot(d.status, False)
        self.assertFalse(d.grants_send)


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_inspect(self):
        timed = admit_format(
            intended="inspect", family="run_id", value=_RUN_A, timed_out=True)
        self.assertEqual(timed.status, "UNKNOWN")
        self.assertTrue(timed.allowed)
        sibling = admit_format(
            intended="inspect", family="run_id", value=_RUN_B)
        self.assertTrue(sibling.allowed)
        self.assertEqual(sibling.status, "FORMAT_FIT")
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(format_timeout_proves())
        self.assertFalse(parse_timeout_proves())
        self.assertEqual(classify_timeout(), "UNKNOWN")
        d = pin_parse(
            intended="parse", family="run_id", value=_RUN_A, timed_out=True)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertNotEqual(d.reason, "already_parsed")
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_inspect_and_peek(self):
        formats = [
            admit_format(intended="inspect", family="run_id", value=rid)
            for rid in (_RUN_A, _RUN_B, _RUN_C)
        ]
        parses = [
            pin_parse(intended="peek", family="run_id", value=rid)
            for rid in (_RUN_A, _RUN_B, _RUN_C)
        ]
        self.assertEqual(len(formats), 3)
        self.assertEqual(len(parses), 3)
        for d in formats + parses:
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_inspect_is_not_a_send(self):
        first = admit_format(intended="inspect", family="run_id", value=_RUN_A)
        second = admit_format(intended="inspect", family="run_id", value=_RUN_A)
        self.assertEqual(first, second)
        self.assertFalse(first.grants_send)
        self.assertFalse(format_grants_send())

    def test_second_parse_is_not_a_send(self):
        first = pin_parse(intended="parse", family="run_id", value=_RUN_A)
        second = pin_parse(
            intended="parse", family="run_id", value=_RUN_A, prior_parsed=True)
        self.assertTrue(first.allowed)
        self.assertFalse(second.allowed)
        self.assertEqual(second.reason, "already_parsed")
        self.assertFalse(first.grants_send)
        self.assertFalse(second.grants_send)
        self.assertFalse(parse_grants_send())


class Scenario5HaltStopsStartsOnly(unittest.TestCase):
    def test_halt_refuses_classify_and_parse_not_inspect_peek(self):
        self.assertFalse(halt_blocks_inspect())
        self.assertFalse(halt_blocks_peek())
        classify = admit_format(
            intended="classify", family="run_id", value=_RUN_A, halted=True)
        parse = pin_parse(
            intended="parse", family="run_id", value=_RUN_A, halted=True)
        inspect = admit_format(
            intended="inspect", family="run_id", value=_RUN_A, halted=True)
        peek = pin_parse(
            intended="peek", family="run_id", value=_RUN_A, halted=True)
        self.assertFalse(classify.allowed)
        self.assertEqual(classify.reason, "halt_active")
        self.assertFalse(parse.allowed)
        self.assertEqual(parse.reason, "halt_active")
        self.assertTrue(inspect.allowed)
        self.assertTrue(peek.allowed)


class Scenario6RecoveryIsNotASend(unittest.TestCase):
    def test_inspect_and_peek_after_halt_are_not_send(self):
        d = admit_format(intended="inspect", family="run_id", value=_RUN_A)
        p = pin_parse(intended="peek", family="run_id", value=_RUN_A)
        self.assertTrue(d.allowed)
        self.assertTrue(p.allowed)
        self.assertFalse(d.grants_send)
        self.assertFalse(p.grants_send)
        self.assertFalse(format_ready())
        self.assertFalse(parse_ready())
        self.assertFalse(mints_run_id())


class Scenario7ReadyIsNotAuthorized(unittest.TestCase):
    def test_sealed_ready_and_send_stay_distinct(self):
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        for name in ("campaign_envelope_ready", "send_authorized", "quote_sent"):
            f = admit_format(intended="inspect", family="run_id", value=name)
            p = pin_parse(intended="peek", family="digest", value=name)
            self.assertFalse(f.allowed)
            self.assertEqual(f.reason, "sealed_effect")
            self.assertFalse(p.allowed)
            self.assertEqual(p.reason, "sealed_effect")
            self.assertFalse(f.grants_send)
            self.assertFalse(p.grants_send)


if __name__ == "__main__":
    unittest.main()
