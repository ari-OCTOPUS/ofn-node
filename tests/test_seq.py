"""Kernel-pure monotonic seq — second witness of the store's seq gate.

Independent of ``run_store.py`` (owned by an open PR). HALT stops
STARTS, not in-flight sequencing. Ready ≠ authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.seq import (
    SeqCursor, grants_send, halt_blocks_seq, refuse_sealed_seq_label,
)


class FirstAcceptIsOne(unittest.TestCase):
    def test_empty_cursor_expects_one(self):
        cur = SeqCursor()
        self.assertEqual(cur.next_expected, 1)
        self.assertEqual(len(cur), 0)
        self.assertTrue(cur.peek_would_accept(1))
        self.assertFalse(cur.peek_would_accept(2))

    def test_accept_one_then_two(self):
        cur = SeqCursor()
        self.assertEqual(cur.accept(1), 1)
        self.assertEqual(cur.accept(2), 2)
        self.assertEqual(cur.replay(), (1, 2))
        self.assertEqual(cur.next_expected, 3)


class GapAndReplayFailClosed(unittest.TestCase):
    def test_gap_refused_and_cursor_unchanged(self):
        cur = SeqCursor()
        cur.accept(1)
        with self.assertRaises(FailClosedError):
            cur.accept(3)
        self.assertEqual(len(cur), 1)
        self.assertEqual(cur.next_expected, 2)

    def test_replay_of_same_seq_refused(self):
        cur = SeqCursor()
        cur.accept(1)
        with self.assertRaises(FailClosedError):
            cur.accept(1)
        self.assertEqual(cur.replay(), (1,))

    def test_zero_and_negative_refused(self):
        cur = SeqCursor()
        for bad in (0, -1, -99):
            with self.subTest(seq=bad):
                with self.assertRaises(FailClosedError):
                    cur.accept(bad)
        self.assertEqual(len(cur), 0)

    def test_bool_is_not_an_int(self):
        cur = SeqCursor()
        with self.assertRaises(FailClosedError):
            cur.accept(True)  # type: ignore[arg-type]
        with self.assertRaises(FailClosedError):
            cur.accept(False)  # type: ignore[arg-type]

    def test_string_seq_refused(self):
        cur = SeqCursor()
        with self.assertRaises(FailClosedError):
            cur.accept("1")  # type: ignore[arg-type]


class PeekDoesNotWrite(unittest.TestCase):
    def test_peek_true_does_not_advance(self):
        cur = SeqCursor()
        self.assertTrue(cur.peek_would_accept(1))
        self.assertEqual(cur.next_expected, 1)
        self.assertEqual(len(cur), 0)

    def test_peek_invalid_is_false_not_raise(self):
        cur = SeqCursor()
        self.assertFalse(cur.peek_would_accept(True))  # type: ignore[arg-type]
        self.assertFalse(cur.peek_would_accept(0))
        self.assertFalse(cur.peek_would_accept("1"))  # type: ignore[arg-type]


class SealedLabelIsNotASeq(unittest.TestCase):
    def test_send_name_refused_as_label(self):
        for name in ("send_authorized", "quote_sent", "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    refuse_sealed_seq_label(name)


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertEqual(list(inspect.signature(grants_send).parameters), [])

    def test_halt_does_not_block_seq(self):
        self.assertFalse(halt_blocks_seq())
        params = inspect.signature(SeqCursor.accept).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("halt", params)
        cur = SeqCursor()
        cur.accept(1)
        self.assertEqual(len(cur), 1)


if __name__ == "__main__":
    unittest.main()
