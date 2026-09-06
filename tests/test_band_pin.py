"""Contract tests for band_pin (P1 complementary).

A caller-owned table records one latched band per run_id.
Missing peek is UNKNOWN, not FALSE. Collision fails closed.
send_authorized / quote_sent / campaign_envelope_ready refuse
as run_id or latched names. Ready ≠ authorized. Never grants
a send. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.band_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    grants_send,
    halt_blocks_pin,
    later_hold_supersedes_older,
    peek_pin,
    pin_allows_send,
    pin_band,
    pin_from_edge,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_latch,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.hysteresis_class import HIGH, LOW, pin_edge


_RUN = "run-1780000000-abcdefghij"


class PeekAndPin(unittest.TestCase):
    def test_missing_peek_is_none_not_false(self):
        self.assertIsNone(peek_pin({}, _RUN))
        self.assertIsNone(peek_pin({}, None))
        self.assertIsNot(peek_pin({}, _RUN), False)

    def test_first_pin_records(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_band(table, _RUN, HIGH), PINNED)
        self.assertEqual(peek_pin(table, _RUN), HIGH)

    def test_same_pair_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_band(table, _RUN, LOW)
        self.assertEqual(pin_band(table, _RUN, "low"), ALREADY_PINNED)
        self.assertEqual(peek_pin(table, _RUN), LOW)

    def test_collision_fails_closed(self):
        table: dict[str, str] = {}
        pin_band(table, _RUN, HIGH)
        with self.assertRaises(FailClosedError) as ctx:
            pin_band(table, _RUN, LOW)
        self.assertIn("band_collision", str(ctx.exception))
        self.assertEqual(peek_pin(table, _RUN), HIGH)

    def test_peek_never_writes(self):
        table: dict[str, str] = {}
        self.assertIsNone(peek_pin(table, _RUN))
        self.assertEqual(table, {})

    def test_missing_latched_on_pin_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_band({}, _RUN, None)

    def test_missing_table_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_band(None, _RUN, HIGH)  # type: ignore[arg-type]
        with self.assertRaises(FailClosedError):
            peek_pin(None, _RUN)  # type: ignore[arg-type]

    def test_malformed_run_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_band({}, "run-1-x", HIGH)

    def test_empty_run_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_band({}, "  ", HIGH)

    def test_sealed_run_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_band({}, "send_authorized", HIGH)
        with self.assertRaises(FailClosedError):
            peek_pin({}, "campaign_envelope_ready")

    def test_sealed_latched_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_band({}, _RUN, "quote_sent")

    def test_bool_run_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_band({}, True, HIGH)  # type: ignore[arg-type]


class PinFromEdgeAndRetcon(unittest.TestCase):
    def test_pin_from_rise_edge(self):
        table: dict[str, str] = {}
        edge = pin_edge(LOW, 10, 0, 10)
        self.assertEqual(pin_from_edge(table, _RUN, edge), PINNED)
        self.assertEqual(peek_pin(table, _RUN), HIGH)

    def test_pin_from_edge_rejects_hand_built(self):
        with self.assertRaises(FailClosedError):
            pin_from_edge({}, _RUN, "rise")  # type: ignore[arg-type]

    def test_retcon_missing_is_none(self):
        self.assertIsNone(retcon_refused({}, _RUN, HIGH))

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_band(table, _RUN, HIGH)
        self.assertIs(retcon_refused(table, _RUN, LOW), True)

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        pin_band(table, _RUN, HIGH)
        self.assertIs(retcon_refused(table, _RUN, HIGH), False)

    def test_try_latch_missing_is_none(self):
        self.assertIsNone(try_latch(None, 10, 0, 10))
        self.assertIsNone(try_latch(HIGH, None, 0, 10))

    def test_try_latch_success(self):
        self.assertEqual(try_latch(HIGH, 5, 0, 10), HIGH)
        self.assertEqual(try_latch(HIGH, 0, 0, 10), LOW)

    def test_try_latch_present_bad_still_fails(self):
        with self.assertRaises(FailClosedError):
            try_latch(HIGH, 5, 3, 3)
        with self.assertRaises(FailClosedError):
            try_latch("send_authorized", 5, 0, 10)


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertFalse(rearms_send())
        self.assertFalse(pin_allows_send(HIGH))
        self.assertFalse(pin_allows_send(LOW))
        self.assertFalse(pin_allows_send(None))

    def test_pin_allows_send_unknown_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_allows_send("maybe")

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertFalse(promotes_ready_to_send())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_later_hold_still_supersedes(self):
        self.assertTrue(later_hold_supersedes_older())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_timeout_does_not_prove_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_not_wired_flag(self):
        self.assertFalse(wires_into_run_store())

    def test_pin_has_no_halt_or_now_parameter(self):
        params = inspect.signature(pin_band).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)


class NotWiredIntoStore(unittest.TestCase):
    def test_run_store_does_not_import_band_pin(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("band_pin", source)
        self.assertNotIn("hysteresis_class", source)

    def test_send_fence_stays_distinct(self):
        import ofn.kernel.send_fence as send_fence
        source = inspect.getsource(send_fence)
        self.assertNotIn("pin_band", source)
        self.assertNotIn("latch_band", source)


if __name__ == "__main__":
    unittest.main()
