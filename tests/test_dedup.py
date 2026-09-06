"""Contract tests for kernel KindRefIndex (P1 complementary).

The store's (kind, ref) rule is owned by another open change. These
tests lock the kernel-pure second witness on main. Ready ≠ authorized.
HALT is not a parameter.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.dedup import (
    KindRefIndex, grants_send, halt_blocks_dedup,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import (
    BUDGET_DEBIT, EXECUTION_RECEIPT, TOOL_INVOKED,
)


class KindRefNegativeControls(unittest.TestCase):
    def setUp(self):
        self.idx = KindRefIndex()

    def test_unknown_kind_refused(self):
        with self.assertRaises(FailClosedError):
            self.idx.remember("NOT_A_KIND", "ref-1")

    def test_sealed_kind_refused(self):
        for kind in ("send_authorized", "quote_sent", "campaign_envelope_ready"):
            with self.subTest(kind=kind):
                with self.assertRaises(FailClosedError):
                    self.idx.remember(kind, "ref-1")

    def test_sealed_ref_refused(self):
        with self.assertRaises(FailClosedError):
            self.idx.remember(TOOL_INVOKED, "quote_sent")

    def test_blank_kind_refused(self):
        with self.assertRaises(FailClosedError):
            self.idx.remember("   ", "ref-1")


class DuplicateDeliveryOneEffect(unittest.TestCase):
    def setUp(self):
        self.idx = KindRefIndex()

    def test_first_remember_is_tracked(self):
        self.assertTrue(self.idx.remember(TOOL_INVOKED, "rcp-1"))
        self.assertTrue(self.idx.seen(TOOL_INVOKED, "rcp-1"))
        self.assertEqual(len(self.idx), 1)

    def test_second_delivery_of_same_pair_refused(self):
        self.idx.remember(TOOL_INVOKED, "rcp-1")
        with self.assertRaises(FailClosedError):
            self.idx.remember(TOOL_INVOKED, "rcp-1")
        self.assertEqual(len(self.idx), 1)

    def test_same_ref_different_kind_is_a_different_pair(self):
        self.idx.remember(EXECUTION_RECEIPT, "rcp-1")
        self.assertTrue(self.idx.remember(BUDGET_DEBIT, "rcp-1"))
        self.assertEqual(len(self.idx), 2)

    def test_empty_ref_is_not_tracked(self):
        self.assertFalse(self.idx.remember(TOOL_INVOKED, None))
        self.assertFalse(self.idx.remember(TOOL_INVOKED, ""))
        self.assertFalse(self.idx.remember(TOOL_INVOKED, "   "))
        self.assertFalse(self.idx.seen(TOOL_INVOKED, None))
        self.assertEqual(len(self.idx), 0)

    def test_replay_is_read_only_and_ordered(self):
        self.idx.remember(TOOL_INVOKED, "a")
        self.idx.remember(TOOL_INVOKED, "b")
        snap = self.idx.replay()
        self.assertEqual(snap, ((TOOL_INVOKED, "a"), (TOOL_INVOKED, "b")))
        # mutating the snapshot cannot rewrite the index
        try:
            snap[0]  # tuple — immutable
        except TypeError:
            self.fail("replay should return a tuple")
        self.assertEqual(self.idx.replay(), snap)


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_dedup(self):
        self.assertFalse(halt_blocks_dedup())

    def test_remember_has_no_halt_parameter(self):
        params = inspect.signature(KindRefIndex.remember).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("halt", params)
        self.assertEqual(list(params), ["self", "kind", "ref"])


if __name__ == "__main__":
    unittest.main()
