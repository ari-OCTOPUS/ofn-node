"""Contract tests for clock_bind (P1 complementary).

A bind records a supplied epoch + UTC_Z stamp. The kernel reads no
clock. Missing is UNKNOWN (None), not 0. OFFSET is refused. Timeout
does not prove concurrent writing. Ready ≠ authorized. Not wired
into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.clock_bind import (
    ClockBind, bind_clock, claims_immutable, grants_send,
    halt_blocks_bind, pair_agrees, proposal_is_execution,
    ready_is_authorized, timeout_proves_concurrent_write, try_bind,
    unknown_epoch_is_zero,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.utc_class import UTC_Z


_STAMP = "2026-09-03T02:07:08Z"
# 2026-09-03T02:07:08Z = unix 1788401228 (civil math via deadline_epoch_s)
_EPOCH = 1788401228


class BindClock(unittest.TestCase):
    def test_bind_records_pair(self):
        bound = bind_clock(_EPOCH, _STAMP)
        self.assertIsInstance(bound, ClockBind)
        self.assertEqual(bound.epoch_s, _EPOCH)
        self.assertEqual(bound.stamp, _STAMP)
        self.assertEqual(bound.stamp_class, UTC_Z)

    def test_frozen_cannot_retcon(self):
        bound = bind_clock(_EPOCH, _STAMP)
        with self.assertRaises(Exception):
            bound.epoch_s = 0  # type: ignore[misc]

    def test_bool_float_str_epoch_fail_closed(self):
        with self.assertRaises(FailClosedError):
            bind_clock(True, _STAMP)
        with self.assertRaises(FailClosedError):
            bind_clock(1788401228.0, _STAMP)
        with self.assertRaises(FailClosedError):
            bind_clock("1788401228", _STAMP)

    def test_negative_epoch_fail_closed(self):
        with self.assertRaises(FailClosedError):
            bind_clock(-1, _STAMP)

    def test_offset_stamp_refused(self):
        with self.assertRaises(FailClosedError):
            bind_clock(_EPOCH, "2026-09-03T12:07:08+10:00")

    def test_naive_stamp_refused(self):
        with self.assertRaises(FailClosedError):
            bind_clock(_EPOCH, "2026-09-03T02:07:08")

    def test_missing_stamp_on_explicit_bind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_clock(_EPOCH, None)

    def test_sealed_stamp_refused(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    bind_clock(_EPOCH, name)


class TryBindUnknown(unittest.TestCase):
    def test_missing_epoch_is_none_not_zero(self):
        self.assertIsNone(try_bind(None, _STAMP))
        self.assertFalse(unknown_epoch_is_zero())

    def test_missing_stamp_is_none(self):
        self.assertIsNone(try_bind(_EPOCH, None))

    def test_both_missing_is_none(self):
        self.assertIsNone(try_bind(None, None))

    def test_present_malformed_still_fails_closed(self):
        with self.assertRaises(FailClosedError):
            try_bind(True, _STAMP)
        with self.assertRaises(FailClosedError):
            try_bind(_EPOCH, "not-a-stamp")

    def test_try_bind_success(self):
        bound = try_bind(_EPOCH, _STAMP)
        self.assertIsNotNone(bound)
        assert bound is not None
        self.assertEqual(bound.epoch_s, _EPOCH)


class PairAgrees(unittest.TestCase):
    def test_same_second_is_true(self):
        self.assertIs(pair_agrees(_EPOCH, _STAMP), True)

    def test_different_second_is_false_not_unknown(self):
        self.assertIs(pair_agrees(_EPOCH + 1, _STAMP), False)

    def test_missing_is_unknown_none(self):
        self.assertIsNone(pair_agrees(None, _STAMP))
        self.assertIsNone(pair_agrees(_EPOCH, None))
        self.assertIsNot(pair_agrees(None, _STAMP), False)


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_bind(self):
        self.assertFalse(halt_blocks_bind())

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_bind_has_no_halt_or_now_parameter(self):
        params = inspect.signature(bind_clock).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("halt", params)
        self.assertNotIn("now", params)
        self.assertEqual(list(params), ["epoch_s", "stamp"])


class NotWiredIntoStore(unittest.TestCase):
    def test_run_store_does_not_import_clock_bind(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("clock_bind", source)
        self.assertNotIn("utc_class", source)


if __name__ == "__main__":
    unittest.main()
