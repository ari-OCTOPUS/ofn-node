"""Contract tests for kernel SettlementIndex (P1 complementary).

One verdict → one budget effect, tested without opening a ledger.
The store's inline copy is owned by another open change. Ready ≠
authorized. HALT does not block in-flight settlement.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.settlement import (
    SettlementIndex, grants_send, halt_blocks_settlement,
)


class SettlementNegativeControls(unittest.TestCase):
    def setUp(self):
        self.idx = SettlementIndex()

    def test_blank_receipt_id_refused(self):
        with self.assertRaises(FailClosedError):
            self.idx.note_receipt("")
        with self.assertRaises(FailClosedError):
            self.idx.settle("   ")

    def test_sealed_receipt_id_refused(self):
        for name in ("send_authorized", "quote_sent", "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    self.idx.note_receipt(name)

    def test_settle_unknown_receipt_refused(self):
        with self.assertRaises(FailClosedError):
            self.idx.settle("rcp-never-noted")
        self.assertFalse(self.idx.known("rcp-never-noted"))


class OneVerdictOneBudgetEffect(unittest.TestCase):
    def setUp(self):
        self.idx = SettlementIndex()

    def test_note_then_settle_once(self):
        self.assertTrue(self.idx.note_receipt("rcp-1"))
        self.assertFalse(self.idx.is_settled("rcp-1"))
        self.idx.settle("rcp-1")
        self.assertTrue(self.idx.is_settled("rcp-1"))

    def test_second_settle_refused(self):
        self.idx.note_receipt("rcp-1")
        self.idx.settle("rcp-1")
        with self.assertRaises(FailClosedError):
            self.idx.settle("rcp-1")
        self.assertTrue(self.idx.is_settled("rcp-1"))

    def test_re_note_is_idempotent_and_does_not_unsettle(self):
        self.idx.note_receipt("rcp-1")
        self.idx.settle("rcp-1")
        self.assertFalse(self.idx.note_receipt("rcp-1"))
        self.assertTrue(self.idx.is_settled("rcp-1"))
        with self.assertRaises(FailClosedError):
            self.idx.settle("rcp-1")

    def test_two_receipts_settle_independently(self):
        self.idx.note_receipt("rcp-a")
        self.idx.note_receipt("rcp-b")
        self.idx.settle("rcp-a")
        self.assertTrue(self.idx.is_settled("rcp-a"))
        self.assertFalse(self.idx.is_settled("rcp-b"))
        self.idx.settle("rcp-b")
        self.assertEqual(len(self.idx), 2)

    def test_replay_is_read_only_and_ordered(self):
        self.idx.note_receipt("rcp-a")
        self.idx.note_receipt("rcp-b")
        self.idx.settle("rcp-a")
        snap = self.idx.replay()
        self.assertEqual(snap, (("rcp-a", True), ("rcp-b", False)))
        self.assertEqual(self.idx.replay(), snap)


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_settlement(self):
        self.assertFalse(halt_blocks_settlement())

    def test_settle_has_no_halt_parameter(self):
        params = inspect.signature(SettlementIndex.settle).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("halt", params)
        self.assertEqual(list(params), ["self", "receipt_id"])


if __name__ == "__main__":
    unittest.main()
