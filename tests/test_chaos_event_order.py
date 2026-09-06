"""Owner-absent: backwards clocks and kind-renames are not clean ledgers.

Scenario 4 (duplicate delivery) already lives on the store. This file
covers the complementary holes: a later record with an earlier ts, a
BUDGET_DEBIT with no receipt, and a proposal treated as an execution.
Timeout is not used as evidence. HALT is not a parameter — in-flight
order checks must still run.

Independent of ``tests/test_chaos_owner_absent.py`` (owned by an open PR).
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import (
    BUDGET_DEBIT,
    EXECUTION_RECEIPT,
    PROPOSAL_CREATED,
    RUN_CLOSED,
    RUN_CREATED,
    TOOL_INVOKED,
)
from ofn.kernel.kind_graph import (
    KindGraph,
    classify_kind,
    proposal_is_execution,
)
from ofn.kernel.ts_order import (
    TsOrder,
    timeout_proves_concurrent_write,
    unknown_is_false,
)


class ScenarioBackwardsTsIsRefused(unittest.TestCase):
    def test_later_record_cannot_carry_earlier_clock(self):
        order = TsOrder()
        order.accept("run-a", 100)
        order.accept("run-a", 101)
        with self.assertRaises(FailClosedError):
            order.accept("run-a", 50)
        self.assertEqual(order.last("run-a"), 101)
        self.assertEqual(order.accepted_count("run-a"), 2)

    def test_missing_last_ts_is_unknown_not_a_writer(self):
        order = TsOrder()
        self.assertIsNone(order.last("run-absent"))
        self.assertFalse(unknown_is_false())
        self.assertFalse(timeout_proves_concurrent_write())


class ScenarioProposalIsNotExecution(unittest.TestCase):
    def test_rename_is_not_a_receipt(self):
        self.assertNotEqual(PROPOSAL_CREATED, EXECUTION_RECEIPT)
        self.assertNotEqual(
            classify_kind(PROPOSAL_CREATED), classify_kind(EXECUTION_RECEIPT))
        self.assertFalse(proposal_is_execution())

    def test_debit_without_receipt_is_refused(self):
        graph = KindGraph()
        graph.accept("run-a", RUN_CREATED)
        graph.accept("run-a", PROPOSAL_CREATED)
        with self.assertRaises(FailClosedError):
            graph.accept("run-a", BUDGET_DEBIT)
        self.assertFalse(graph.saw_receipt("run-a"))
        graph.accept("run-a", EXECUTION_RECEIPT)
        graph.accept("run-a", BUDGET_DEBIT)
        self.assertEqual(graph.last("run-a"), BUDGET_DEBIT)


class ScenarioCloseStopsFurtherKinds(unittest.TestCase):
    def test_recovery_closes_then_other_run_continues(self):
        graph = KindGraph()
        graph.accept("run-failed", RUN_CREATED)
        graph.accept("run-failed", TOOL_INVOKED)
        graph.accept("run-failed", RUN_CLOSED)
        with self.assertRaises(FailClosedError):
            graph.accept("run-failed", TOOL_INVOKED)
        graph.accept("run-sibling", RUN_CREATED)
        graph.accept("run-sibling", TOOL_INVOKED)
        self.assertTrue(graph.is_closed("run-failed"))
        self.assertFalse(graph.is_closed("run-sibling"))


class ScenarioInFlightOrderSurvivesHaltVocabulary(unittest.TestCase):
    def test_accept_has_no_halt_switch(self):
        order = TsOrder()
        order.accept("run-a", 1)
        order.accept("run-a", 2)
        graph = KindGraph()
        graph.accept("run-a", RUN_CREATED)
        graph.accept("run-a", TOOL_INVOKED)
        self.assertEqual(order.accepted_count("run-a"), 2)
        self.assertEqual(graph.accepted_count("run-a"), 2)


class ScenarioReadyAuthorizedSentStayDistinct(unittest.TestCase):
    def test_sealed_names_are_not_graph_nodes(self):
        graph = KindGraph()
        graph.accept("run-a", RUN_CREATED)
        for name in ("campaign_envelope_ready", "send_authorized", "quote_sent"):
            with self.subTest(name=name):
                self.assertEqual(classify_kind(name), "SEALED")
                with self.assertRaises(FailClosedError):
                    graph.accept("run-a", name)
        self.assertEqual(graph.last("run-a"), RUN_CREATED)


if __name__ == "__main__":
    unittest.main()
