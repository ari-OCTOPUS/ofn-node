"""Contract tests for limit_pin (P1 complementary).

A pin records (run_id → action) on a caller-owned table. Same pair
is already_limited. A different action on the same run_id fails
closed. peek never writes. Missing is UNKNOWN (None), not FALSE.
Ready ≠ authorized. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import os
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.limit_pin import (
    ALREADY_LIMITED,
    LIMITED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_limit,
    pin_allows_send,
    pin_allows_start,
    pin_limit,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    wires_into_run_store,
)
from ofn.kernel.scope_class import ScopeBind, bind_scope


_RUN = "run-1780000000-abcdefghij"
_RUN_B = "run-1780000001-klmnopqrst"


class PinLimit(unittest.TestCase):
    def test_first_pin_records(self):
        table: dict[str, str] = {}
        bound = bind_scope("inspect", _RUN)
        self.assertEqual(pin_limit(table, bound), LIMITED)
        self.assertEqual(table[_RUN], "inspect")

    def test_same_pair_is_already_limited(self):
        table: dict[str, str] = {}
        bound = bind_scope("classify", _RUN)
        self.assertEqual(pin_limit(table, bound), LIMITED)
        self.assertEqual(pin_limit(table, bound), ALREADY_LIMITED)
        self.assertEqual(table[_RUN], "classify")

    def test_different_action_is_collision(self):
        table: dict[str, str] = {}
        pin_limit(table, bind_scope("inspect", _RUN))
        with self.assertRaises(FailClosedError) as ctx:
            pin_limit(table, bind_scope("start", _RUN))
        self.assertIn("action_collision", str(ctx.exception))
        self.assertEqual(table[_RUN], "inspect")

    def test_distinct_run_ids_do_not_collide(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_limit(table, bind_scope("inspect", _RUN)), LIMITED)
        self.assertEqual(pin_limit(table, bind_scope("start", _RUN_B)), LIMITED)
        self.assertEqual(peek_limit(table, _RUN), "inspect")
        self.assertEqual(peek_limit(table, _RUN_B), "start")

    def test_missing_table_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_limit(None, bind_scope("inspect", _RUN))  # type: ignore[arg-type]

    def test_hand_built_bind_is_rechecked(self):
        table: dict[str, str] = {}
        with self.assertRaises(FailClosedError):
            pin_limit(
                table,
                ScopeBind(
                    action="send_authorized",
                    run_id=_RUN,
                    action_class="send_authorized",
                ),
            )
        self.assertEqual(table, {})


class PeekNeverWrites(unittest.TestCase):
    def test_peek_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(peek_limit(table, _RUN))
        self.assertEqual(table, {})

    def test_peek_none_run_is_none(self):
        self.assertIsNone(peek_limit({}, None))

    def test_peek_does_not_insert(self):
        table: dict[str, str] = {}
        peek_limit(table, _RUN)
        self.assertNotIn(_RUN, table)

    def test_peek_sealed_run_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_limit({}, "send_authorized")

    def test_peek_bool_run_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_limit({}, True)


class RetconRefused(unittest.TestCase):
    def test_missing_pin_is_unknown_none(self):
        bound = bind_scope("inspect", _RUN)
        self.assertIsNone(retcon_refused({}, bound))

    def test_matching_pin_is_false(self):
        table: dict[str, str] = {}
        bound = bind_scope("inspect", _RUN)
        pin_limit(table, bound)
        self.assertIs(retcon_refused(table, bound), False)

    def test_disagreeing_pin_is_true(self):
        table: dict[str, str] = {}
        pin_limit(table, bind_scope("inspect", _RUN))
        other = bind_scope("classify", _RUN)
        self.assertIs(retcon_refused(table, other), True)


class AllowPredicates(unittest.TestCase):
    def test_pin_allows_start_only_for_start(self):
        self.assertTrue(pin_allows_start(bind_scope("start", _RUN)))
        self.assertFalse(pin_allows_start(bind_scope("inspect", _RUN)))
        self.assertFalse(pin_allows_start(bind_scope("classify", _RUN)))

    def test_pin_allows_send_always_false(self):
        for action in ("inspect", "classify", "start"):
            with self.subTest(action=action):
                self.assertFalse(pin_allows_send(bind_scope(action, _RUN)))

    def test_ready_stays_unsent(self):
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertFalse(ready_is_authorized())
        self.assertFalse(promotes_ready_to_send())
        self.assertTrue(later_disarm_supersedes())


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())
        params = inspect.signature(pin_limit).parameters
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
                self.assertNotIn("limit_pin", text)
                self.assertNotIn("scope_class", text)

    def test_claims_immutable_is_false(self):
        self.assertFalse(claims_immutable())


if __name__ == "__main__":
    unittest.main()
