"""Kernel-pure per-run timestamp order — second witness of clock succession.

Independent of ``run_store.py`` (owned by an open PR) and of ``seq.py``
(owned by another). HALT stops STARTS, not in-flight ordering.
Ready ≠ authorized. A missing last-ts is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.ts_order import (
    TsOrder,
    compare_ts,
    grants_send,
    halt_blocks_ts_order,
    promotes_ready_to_send,
    timeout_proves_concurrent_write,
    unknown_is_false,
)


class FirstAcceptRecords(unittest.TestCase):
    def test_empty_cursor_last_is_none_not_zero(self):
        order = TsOrder()
        self.assertIsNone(order.last("run-a"))
        self.assertEqual(order.accepted_count("run-a"), 0)
        self.assertTrue(order.peek_would_accept("run-a", 10))

    def test_first_accept_records_ts(self):
        order = TsOrder()
        self.assertEqual(order.accept("run-a", 10), 10)
        self.assertEqual(order.last("run-a"), 10)
        self.assertEqual(order.accepted_count("run-a"), 1)


class MonotonicWithinRun(unittest.TestCase):
    def test_equal_ts_allowed(self):
        order = TsOrder()
        order.accept("run-a", 10)
        order.accept("run-a", 10)
        self.assertEqual(order.last("run-a"), 10)
        self.assertEqual(order.accepted_count("run-a"), 2)

    def test_later_ts_accepted(self):
        order = TsOrder()
        order.accept("run-a", 10)
        order.accept("run-a", 11)
        self.assertEqual(order.last("run-a"), 11)

    def test_backwards_refused_and_cursor_unchanged(self):
        order = TsOrder()
        order.accept("run-a", 10)
        with self.assertRaises(FailClosedError):
            order.accept("run-a", 9)
        self.assertEqual(order.last("run-a"), 10)
        self.assertEqual(order.accepted_count("run-a"), 1)

    def test_runs_are_independent(self):
        order = TsOrder()
        order.accept("run-a", 50)
        order.accept("run-b", 1)
        self.assertEqual(order.last("run-a"), 50)
        self.assertEqual(order.last("run-b"), 1)


class MalformedInputFailsClosed(unittest.TestCase):
    def test_bool_is_not_int(self):
        order = TsOrder()
        with self.assertRaises(FailClosedError):
            order.accept("run-a", True)  # type: ignore[arg-type]
        with self.assertRaises(FailClosedError):
            order.accept("run-a", False)  # type: ignore[arg-type]
        self.assertIsNone(order.last("run-a"))

    def test_float_and_str_refused(self):
        order = TsOrder()
        with self.assertRaises(FailClosedError):
            order.accept("run-a", 1.5)  # type: ignore[arg-type]
        with self.assertRaises(FailClosedError):
            order.accept("run-a", "10")  # type: ignore[arg-type]

    def test_empty_run_id_refused(self):
        order = TsOrder()
        with self.assertRaises(FailClosedError):
            order.accept("", 1)
        with self.assertRaises(FailClosedError):
            order.accept("   ", 1)

    def test_sealed_run_id_refused(self):
        order = TsOrder()
        for name in ("send_authorized", "quote_sent", "campaign_envelope_ready",
                     "send-authorized"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    order.accept(name, 1)


class PeekDoesNotWrite(unittest.TestCase):
    def test_peek_true_does_not_advance(self):
        order = TsOrder()
        self.assertTrue(order.peek_would_accept("run-a", 10))
        self.assertIsNone(order.last("run-a"))
        self.assertEqual(order.accepted_count("run-a"), 0)

    def test_peek_invalid_is_false_not_raise(self):
        order = TsOrder()
        self.assertFalse(order.peek_would_accept("run-a", True))
        self.assertFalse(order.peek_would_accept("run-a", "10"))
        self.assertFalse(order.peek_would_accept("", 1))
        self.assertFalse(order.peek_would_accept("send_authorized", 1))
        order.accept("run-a", 10)
        self.assertFalse(order.peek_would_accept("run-a", 9))
        self.assertEqual(order.last("run-a"), 10)


class CompareTsIsReadOnly(unittest.TestCase):
    def test_ok_and_backwards(self):
        self.assertEqual(compare_ts(10, 10), "ok")
        self.assertEqual(compare_ts(10, 11), "ok")
        self.assertEqual(compare_ts(10, 9), "backwards")

    def test_malformed_fails_closed(self):
        with self.assertRaises(FailClosedError):
            compare_ts(None, 1)
        with self.assertRaises(FailClosedError):
            compare_ts(1, True)


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertEqual(list(inspect.signature(grants_send).parameters), [])

    def test_halt_does_not_block_order(self):
        self.assertFalse(halt_blocks_ts_order())
        params = inspect.signature(TsOrder.accept).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("halt", params)
        order = TsOrder()
        order.accept("run-a", 1)
        self.assertEqual(order.accepted_count("run-a"), 1)

    def test_timeout_is_not_a_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertFalse(unknown_is_false())
        self.assertFalse(promotes_ready_to_send())
        self.assertEqual(
            list(inspect.signature(timeout_proves_concurrent_write).parameters),
            [])


if __name__ == "__main__":
    unittest.main()
