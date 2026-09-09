"""Contract tests for stop_pin (P1 complementary).

A pinned isolated/cascade is not a send. Same triple is
already_pinned. A different family on the same stop fails closed.
peek never writes. Missing is UNKNOWN, not FALSE. Isolated
cannot be retconned into cascade.
"""

from __future__ import annotations

import unittest

from ofn.kernel.cascade_class import (
    CASCADE,
    ISOLATED,
    CascadeBind,
    bind_cascade,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.stop_pin import (
    ALREADY_PINNED,
    PINNED,
    cascade_is_authorized,
    children_do_not_promote,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_stop,
    pin_allows_record,
    pin_allows_send,
    pin_stop,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_STOP = "env-cst-0001"


def _bind(
    scope: str,
    child_count: int = 2,
    *,
    intent: str = "classify",
) -> CascadeBind:
    return bind_cascade(intent, scope, child_count, stop=_STOP)


class PinStops(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_stop(table, _bind("cascade")), PINNED)
        self.assertEqual(peek_stop(table, _STOP), "cascade:cascade:2")

    def test_same_triple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_stop(table, _bind("cascade"))
        self.assertEqual(pin_stop(table, _bind("cascade")), ALREADY_PINNED)

    def test_different_scope_fails_closed(self):
        table: dict[str, str] = {}
        pin_stop(table, _bind("isolated", 2))
        with self.assertRaises(FailClosedError) as ctx:
            pin_stop(table, _bind("cascade", 2))
        self.assertIn("stop_collision", str(ctx.exception))

    def test_isolated_with_children_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind("isolated", 3)
        self.assertEqual(bind.family, ISOLATED)
        self.assertEqual(pin_stop(table, bind), PINNED)
        self.assertEqual(peek_stop(table, _STOP), "isolated:isolated:3")
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_record(bind))
        self.assertTrue(children_do_not_promote())

    def test_cascade_record_allows_record_not_send(self):
        bind = _bind("cascade", 2, intent="record")
        self.assertEqual(bind.family, CASCADE)
        self.assertTrue(pin_allows_record(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_isolated_record_allows_record_not_send(self):
        bind = _bind("isolated", 0, intent="record")
        self.assertEqual(bind.family, ISOLATED)
        self.assertTrue(pin_allows_record(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_classify_cascade_does_not_allow_record(self):
        bind = _bind("cascade", 3, intent="classify")
        self.assertEqual(bind.family, CASCADE)
        self.assertFalse(pin_allows_record(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_stop({}, _STOP))
        self.assertIsNone(peek_stop({}, None))
        self.assertIsNot(peek_stop({}, _STOP), False)

    def test_peek_sealed_stop_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_stop({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(table, None, "cascade", 2, stop=_STOP))
        self.assertIsNone(try_pin(table, "classify", None, 2, stop=_STOP))
        self.assertIsNone(try_pin(table, "classify", "cascade", None, stop=_STOP))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", "cascade", 2, stop=_STOP, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", "cascade", 2, stop=_STOP), PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind("cascade")
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind("cascade")
        pin_stop(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_stop(table, _bind("isolated", 2))
        other = bind_cascade("classify", "cascade", 2, stop=_STOP)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = CascadeBind(
            intent="classify",
            family=CASCADE,
            scope=ISOLATED,
            child_count=2,
            stop=_STOP,
        )
        with self.assertRaises(FailClosedError):
            pin_stop(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_stop(None, _bind("cascade"))  # type: ignore[arg-type]


class StructuralRefusals(unittest.TestCase):
    def test_flags(self):
        self.assertFalse(grants_send())
        self.assertFalse(halt_blocks_pin())
        self.assertFalse(ready_is_authorized())
        self.assertFalse(claims_immutable())
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertFalse(proposal_is_execution())
        self.assertFalse(promotes_ready_to_send())
        self.assertFalse(wires_into_run_store())
        self.assertFalse(consumes_nonce())
        self.assertFalse(unknown_is_false())
        self.assertFalse(cascade_is_authorized())
        self.assertTrue(later_disarm_supersedes())
        self.assertTrue(children_do_not_promote())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
