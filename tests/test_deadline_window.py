"""Kernel-pure deadline window — second witness of the store's close rule.

Independent of ``run_store.py`` (owned by an open PR). HALT stops
STARTS, not in-flight windows. Equal means closed. Ready ≠ authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.deadline_window import (
    DeadlineIndex,
    grants_send,
    halt_blocks_deadline,
    refuse_past_deadline,
    refuse_sealed_deadline_label,
    window_open,
)
from ofn.kernel.errors import FailClosedError

_RUN_A = "run-1780000000-a1b2c3d4e5f6a7b8"
_RUN_B = "run-1780000000-b1b2c3d4e5f6a7b8"
_NOW = 1_780_000_000
_DEADLINE = 1_780_000_100


class EqualMeansClosed(unittest.TestCase):
    def test_strictly_before_is_open(self):
        self.assertTrue(window_open(_NOW, _DEADLINE))
        refuse_past_deadline(_NOW, _DEADLINE)  # must not raise

    def test_equal_is_closed(self):
        self.assertFalse(window_open(_DEADLINE, _DEADLINE))
        with self.assertRaises(FailClosedError):
            refuse_past_deadline(_DEADLINE, _DEADLINE)

    def test_after_is_closed(self):
        self.assertFalse(window_open(_DEADLINE + 1, _DEADLINE))
        with self.assertRaises(FailClosedError):
            refuse_past_deadline(_DEADLINE + 1, _DEADLINE)

    def test_one_second_before_is_still_open(self):
        self.assertTrue(window_open(_DEADLINE - 1, _DEADLINE))


class ExactIntClock(unittest.TestCase):
    def test_bool_is_not_an_int(self):
        for bad in (True, False):
            with self.subTest(value=bad):
                with self.assertRaises(FailClosedError):
                    window_open(bad, _DEADLINE)  # type: ignore[arg-type]
                with self.assertRaises(FailClosedError):
                    window_open(_NOW, bad)  # type: ignore[arg-type]

    def test_float_and_str_refused(self):
        for bad in (1.5, "1780000000", None, 1.0):
            with self.subTest(value=bad):
                with self.assertRaises(FailClosedError):
                    window_open(bad, _DEADLINE)  # type: ignore[arg-type]


class DeadlineIndexBind(unittest.TestCase):
    def test_bind_then_open_then_equal_closed(self):
        idx = DeadlineIndex()
        self.assertTrue(idx.bind(_RUN_A, _DEADLINE))
        self.assertTrue(idx.is_open(_RUN_A, _NOW))
        idx.refuse_if_closed(_RUN_A, _NOW)
        self.assertFalse(idx.is_open(_RUN_A, _DEADLINE))
        with self.assertRaises(FailClosedError):
            idx.refuse_if_closed(_RUN_A, _DEADLINE)

    def test_rebind_same_epoch_is_idempotent(self):
        idx = DeadlineIndex()
        self.assertTrue(idx.bind(_RUN_A, _DEADLINE))
        self.assertFalse(idx.bind(_RUN_A, _DEADLINE))
        self.assertEqual(len(idx), 1)
        self.assertEqual(idx.replay(), ((_RUN_A, _DEADLINE),))

    def test_rebind_different_epoch_refused(self):
        idx = DeadlineIndex()
        idx.bind(_RUN_A, _DEADLINE)
        with self.assertRaises(FailClosedError):
            idx.bind(_RUN_A, _DEADLINE + 10)
        self.assertEqual(idx.deadline_of(_RUN_A), _DEADLINE)

    def test_unbound_run_has_no_deadline(self):
        idx = DeadlineIndex()
        with self.assertRaises(FailClosedError):
            idx.deadline_of(_RUN_A)
        with self.assertRaises(FailClosedError):
            idx.refuse_if_closed(_RUN_A, _NOW)
        self.assertFalse(idx.known(_RUN_A))

    def test_sibling_run_unaffected(self):
        idx = DeadlineIndex()
        idx.bind(_RUN_A, _NOW)          # already closed at _NOW (equal)
        idx.bind(_RUN_B, _DEADLINE)     # still open
        with self.assertRaises(FailClosedError):
            idx.refuse_if_closed(_RUN_A, _NOW)
        idx.refuse_if_closed(_RUN_B, _NOW)
        self.assertTrue(idx.is_open(_RUN_B, _NOW))

    def test_malformed_run_id_refused(self):
        idx = DeadlineIndex()
        with self.assertRaises(FailClosedError):
            idx.bind("run-1-short", _DEADLINE)
        with self.assertRaises(FailClosedError):
            idx.bind("send_authorized", _DEADLINE)
        self.assertEqual(len(idx), 0)

    def test_replay_does_not_write(self):
        idx = DeadlineIndex()
        idx.bind(_RUN_A, _DEADLINE)
        snap = idx.replay()
        self.assertEqual(snap, ((_RUN_A, _DEADLINE),))
        self.assertEqual(len(idx), 1)
        # snapshot is a tuple — no mutation path back into the index
        self.assertIsInstance(snap, tuple)


class SealedLabelIsNotADeadline(unittest.TestCase):
    def test_send_name_refused_as_label(self):
        for name in ("send_authorized", "quote_sent", "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    refuse_sealed_deadline_label(name)


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertEqual(list(inspect.signature(grants_send).parameters), [])

    def test_halt_does_not_block_deadline(self):
        self.assertFalse(halt_blocks_deadline())
        params = inspect.signature(DeadlineIndex.refuse_if_closed).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("halt", params)
        idx = DeadlineIndex()
        idx.bind(_RUN_A, _DEADLINE)
        idx.refuse_if_closed(_RUN_A, _NOW)
        self.assertEqual(len(idx), 1)

    def test_no_resend_or_send_authorized_parameter(self):
        for fn in (window_open, refuse_past_deadline,
                   DeadlineIndex.bind, DeadlineIndex.refuse_if_closed):
            names = list(inspect.signature(fn).parameters)
            self.assertNotIn("resend", names)
            self.assertNotIn("send_authorized", names)


if __name__ == "__main__":
    unittest.main()
