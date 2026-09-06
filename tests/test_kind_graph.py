"""Kernel-pure event-kind succession — second witness of the typed spine.

Independent of ``run_store.py`` (owned by an open PR) and of
``settlement.py`` (owned by another). HALT stops STARTS, not
in-flight succession. Ready ≠ authorized. Proposal ≠ execution.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import (
    BUDGET_DEBIT,
    CLAIM_CREATED,
    EXECUTION_RECEIPT,
    POLICY_DECISION,
    PROPOSAL_CREATED,
    RUN_CLOSED,
    RUN_CREATED,
    RUN_REJECTED,
    TOOL_INVOKED,
)
from ofn.kernel.kind_graph import (
    EXECUTION,
    PROPOSAL,
    REFUSAL,
    SEALED,
    START,
    TERMINAL,
    UNKNOWN,
    KindGraph,
    classify_kind,
    grants_send,
    halt_blocks_kind_graph,
    may_follow,
    promotes_ready_to_send,
    proposal_is_execution,
    unknown_is_false,
)


class ClassifyKind(unittest.TestCase):
    def test_closed_vocabulary(self):
        self.assertEqual(classify_kind(RUN_CREATED), START)
        self.assertEqual(classify_kind(PROPOSAL_CREATED), PROPOSAL)
        self.assertEqual(classify_kind(EXECUTION_RECEIPT), EXECUTION)
        self.assertEqual(classify_kind(RUN_CLOSED), TERMINAL)
        self.assertEqual(classify_kind(RUN_REJECTED), REFUSAL)
        self.assertEqual(classify_kind(CLAIM_CREATED), "PROGRESS")
        self.assertEqual(classify_kind(BUDGET_DEBIT), "SETTLEMENT")

    def test_proposal_is_not_execution(self):
        self.assertNotEqual(
            classify_kind(PROPOSAL_CREATED), classify_kind(EXECUTION_RECEIPT))
        self.assertFalse(proposal_is_execution())

    def test_sealed_ready_authorized_sent_are_distinct(self):
        self.assertEqual(classify_kind("campaign_envelope_ready"), SEALED)
        self.assertEqual(classify_kind("send_authorized"), SEALED)
        self.assertEqual(classify_kind("quote_sent"), SEALED)
        # Same class (not a ledger node) but the names stay distinct.
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertNotEqual("send_authorized", "quote_sent")

    def test_unknown_kind_is_unknown_not_false(self):
        self.assertEqual(classify_kind("not-a-spine-kind"), UNKNOWN)
        self.assertNotEqual(classify_kind("not-a-spine-kind"), "FALSE")
        self.assertFalse(unknown_is_false())

    def test_empty_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_kind("")
        with self.assertRaises(FailClosedError):
            classify_kind(None)


class MayFollow(unittest.TestCase):
    def test_only_run_created_starts(self):
        self.assertTrue(may_follow(None, RUN_CREATED))
        self.assertFalse(may_follow(None, TOOL_INVOKED))
        self.assertFalse(may_follow(None, RUN_CLOSED))
        self.assertFalse(may_follow(None, RUN_REJECTED))

    def test_second_run_created_refused(self):
        self.assertFalse(may_follow(RUN_CREATED, RUN_CREATED))

    def test_progress_after_start(self):
        for kind in (CLAIM_CREATED, PROPOSAL_CREATED, POLICY_DECISION,
                     TOOL_INVOKED, EXECUTION_RECEIPT, BUDGET_DEBIT, RUN_CLOSED):
            with self.subTest(kind=kind):
                self.assertTrue(may_follow(RUN_CREATED, kind))

    def test_nothing_after_close(self):
        for kind in (TOOL_INVOKED, RUN_CREATED, RUN_CLOSED, EXECUTION_RECEIPT):
            with self.subTest(kind=kind):
                self.assertFalse(may_follow(RUN_CLOSED, kind))

    def test_refusal_and_sealed_are_not_nodes(self):
        self.assertFalse(may_follow(RUN_CREATED, RUN_REJECTED))
        self.assertFalse(may_follow(RUN_CREATED, "send_authorized"))
        self.assertFalse(may_follow(RUN_CREATED, "campaign_envelope_ready"))
        self.assertFalse(may_follow(RUN_CREATED, "quote_sent"))


class KindGraphCursor(unittest.TestCase):
    def test_must_start_with_run_created(self):
        graph = KindGraph()
        self.assertIsNone(graph.last("run-a"))
        with self.assertRaises(FailClosedError):
            graph.accept("run-a", TOOL_INVOKED)
        self.assertEqual(graph.accepted_count("run-a"), 0)
        graph.accept("run-a", RUN_CREATED)
        self.assertEqual(graph.last("run-a"), RUN_CREATED)

    def test_debit_requires_prior_receipt(self):
        graph = KindGraph()
        graph.accept("run-a", RUN_CREATED)
        self.assertFalse(graph.saw_receipt("run-a"))
        with self.assertRaises(FailClosedError):
            graph.accept("run-a", BUDGET_DEBIT)
        self.assertEqual(graph.last("run-a"), RUN_CREATED)
        graph.accept("run-a", EXECUTION_RECEIPT)
        self.assertTrue(graph.saw_receipt("run-a"))
        graph.accept("run-a", BUDGET_DEBIT)
        self.assertEqual(graph.last("run-a"), BUDGET_DEBIT)

    def test_close_is_terminal(self):
        graph = KindGraph()
        graph.accept("run-a", RUN_CREATED)
        graph.accept("run-a", RUN_CLOSED)
        self.assertTrue(graph.is_closed("run-a"))
        with self.assertRaises(FailClosedError):
            graph.accept("run-a", TOOL_INVOKED)
        self.assertEqual(graph.last("run-a"), RUN_CLOSED)

    def test_proposal_then_execution_are_distinct_nodes(self):
        graph = KindGraph()
        graph.accept("run-a", RUN_CREATED)
        graph.accept("run-a", PROPOSAL_CREATED)
        graph.accept("run-a", EXECUTION_RECEIPT)
        self.assertEqual(graph.last("run-a"), EXECUTION_RECEIPT)
        self.assertNotEqual(PROPOSAL_CREATED, EXECUTION_RECEIPT)

    def test_runs_are_independent(self):
        graph = KindGraph()
        graph.accept("run-a", RUN_CREATED)
        graph.accept("run-a", RUN_CLOSED)
        graph.accept("run-b", RUN_CREATED)
        graph.accept("run-b", TOOL_INVOKED)
        self.assertTrue(graph.is_closed("run-a"))
        self.assertFalse(graph.is_closed("run-b"))

    def test_sealed_kind_refused(self):
        graph = KindGraph()
        graph.accept("run-a", RUN_CREATED)
        for name in ("send_authorized", "quote_sent", "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    graph.accept("run-a", name)
        self.assertEqual(graph.last("run-a"), RUN_CREATED)

    def test_refusal_kind_refused(self):
        graph = KindGraph()
        graph.accept("run-a", RUN_CREATED)
        with self.assertRaises(FailClosedError):
            graph.accept("run-a", RUN_REJECTED)

    def test_unknown_kind_refused(self):
        graph = KindGraph()
        graph.accept("run-a", RUN_CREATED)
        with self.assertRaises(FailClosedError):
            graph.accept("run-a", "not-a-spine-kind")


class PeekDoesNotWrite(unittest.TestCase):
    def test_peek_true_does_not_advance(self):
        graph = KindGraph()
        self.assertTrue(graph.peek_would_accept("run-a", RUN_CREATED))
        self.assertIsNone(graph.last("run-a"))
        self.assertEqual(graph.accepted_count("run-a"), 0)

    def test_peek_invalid_is_false_not_raise(self):
        graph = KindGraph()
        self.assertFalse(graph.peek_would_accept("run-a", TOOL_INVOKED))
        self.assertFalse(graph.peek_would_accept("run-a", True))
        self.assertFalse(graph.peek_would_accept("", RUN_CREATED))
        self.assertFalse(graph.peek_would_accept("send_authorized", RUN_CREATED))
        graph.accept("run-a", RUN_CREATED)
        self.assertFalse(graph.peek_would_accept("run-a", BUDGET_DEBIT))
        self.assertEqual(graph.last("run-a"), RUN_CREATED)


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertEqual(list(inspect.signature(grants_send).parameters), [])
        self.assertFalse(promotes_ready_to_send())

    def test_halt_does_not_block_graph(self):
        self.assertFalse(halt_blocks_kind_graph())
        params = inspect.signature(KindGraph.accept).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("halt", params)
        graph = KindGraph()
        graph.accept("run-a", RUN_CREATED)
        graph.accept("run-a", TOOL_INVOKED)
        self.assertEqual(graph.accepted_count("run-a"), 2)


if __name__ == "__main__":
    unittest.main()
