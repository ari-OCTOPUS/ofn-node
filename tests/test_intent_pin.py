"""Contract tests for intent_pin (P1 complementary).

A pin records (run_id → intent) on a caller-owned table. Same pair
is already_pinned. A different intent on the same run_id fails
closed. peek never writes. Missing is UNKNOWN (None), not FALSE.
Ready ≠ authorized. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import os
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.intent_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    peek_pin,
    pin_allows_mint,
    pin_allows_send,
    pin_intent,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    wires_into_run_store,
)
from ofn.kernel.task_bind import TaskBind, bind_task


_RUN = "run-1780000000-abcdefghij"
_RUN_B = "run-1780000001-klmnopqrst"


class PinIntent(unittest.TestCase):
    def test_first_pin_records(self):
        table: dict[str, str] = {}
        bound = bind_task("mint", _RUN)
        self.assertEqual(pin_intent(table, bound), PINNED)
        self.assertEqual(table[_RUN], "mint")

    def test_same_pair_is_already_pinned(self):
        table: dict[str, str] = {}
        bound = bind_task("validate", _RUN)
        self.assertEqual(pin_intent(table, bound), PINNED)
        self.assertEqual(pin_intent(table, bound), ALREADY_PINNED)
        self.assertEqual(table[_RUN], "validate")

    def test_different_intent_is_collision(self):
        table: dict[str, str] = {}
        pin_intent(table, bind_task("mint", _RUN))
        with self.assertRaises(FailClosedError) as ctx:
            pin_intent(table, bind_task("replay", _RUN))
        self.assertIn("intent_collision", str(ctx.exception))
        self.assertEqual(table[_RUN], "mint")

    def test_distinct_run_ids_do_not_collide(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_intent(table, bind_task("mint", _RUN)), PINNED)
        self.assertEqual(pin_intent(table, bind_task("replay", _RUN_B)), PINNED)
        self.assertEqual(peek_pin(table, _RUN), "mint")
        self.assertEqual(peek_pin(table, _RUN_B), "replay")

    def test_missing_table_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_intent(None, bind_task("mint", _RUN))  # type: ignore[arg-type]

    def test_hand_built_bind_is_rechecked(self):
        table: dict[str, str] = {}
        with self.assertRaises(FailClosedError):
            pin_intent(
                table,
                TaskBind(
                    intent="send_authorized",
                    run_id=_RUN,
                    intent_class="send_authorized",
                ),
            )
        self.assertEqual(table, {})


class PeekNeverWrites(unittest.TestCase):
    def test_peek_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(peek_pin(table, _RUN))
        self.assertEqual(table, {})

    def test_peek_none_run_is_none(self):
        self.assertIsNone(peek_pin({}, None))

    def test_peek_does_not_insert(self):
        table: dict[str, str] = {}
        peek_pin(table, _RUN)
        self.assertNotIn(_RUN, table)

    def test_peek_sealed_run_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_pin({}, "send_authorized")

    def test_peek_bool_run_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_pin({}, True)


class RetconRefused(unittest.TestCase):
    def test_missing_pin_is_unknown_none(self):
        bound = bind_task("mint", _RUN)
        self.assertIsNone(retcon_refused({}, bound))

    def test_matching_pin_is_false(self):
        table: dict[str, str] = {}
        bound = bind_task("mint", _RUN)
        pin_intent(table, bound)
        self.assertIs(retcon_refused(table, bound), False)

    def test_disagreeing_pin_is_true(self):
        table: dict[str, str] = {}
        pin_intent(table, bind_task("mint", _RUN))
        other = bind_task("validate", _RUN)
        self.assertIs(retcon_refused(table, other), True)


class AllowPredicates(unittest.TestCase):
    def test_pin_allows_mint_only_for_mint(self):
        self.assertTrue(pin_allows_mint(bind_task("mint", _RUN)))
        self.assertFalse(pin_allows_mint(bind_task("validate", _RUN)))
        self.assertFalse(pin_allows_mint(bind_task("replay", _RUN)))

    def test_pin_allows_send_always_false(self):
        for intent in ("mint", "validate", "replay"):
            with self.subTest(intent=intent):
                self.assertFalse(pin_allows_send(bind_task(intent, _RUN)))

    def test_ready_stays_unsent(self):
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertFalse(ready_is_authorized())
        self.assertFalse(promotes_ready_to_send())


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())
        params = inspect.signature(pin_intent).parameters
        self.assertNotIn("halted", params)

    def test_timeout_does_not_prove_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_consume_nonce(self):
        self.assertFalse(consumes_nonce())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for rel in (
            os.path.join("ofn", "adapters", "run_store.py"),
            os.path.join("ofn", "kernel", "run_store.py"),
        ):
            path = os.path.join(root, rel)
            if os.path.isfile(path):
                text = open(path, encoding="utf-8").read()
                self.assertNotIn("intent_pin", text)
                self.assertNotIn("task_bind", text)

    def test_claims_immutable_is_false(self):
        self.assertFalse(claims_immutable())


if __name__ == "__main__":
    unittest.main()
