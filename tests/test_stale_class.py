"""Contract tests for stale_class (P1 complementary).

Caller-supplied epochs + ttl classify FRESH / STALE / UNKNOWN.
Missing or timeout is UNKNOWN, not STALE and not FALSE.
Equal age stays FRESH. Inversion fail-closes. Refresh is a START.
Ready ≠ authorized. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.stale_class import (
    FRESH,
    KINDS,
    REFUSAL_REASONS,
    STALE,
    UNKNOWN,
    RefreshDecision,
    StaleClass,
    admit_refresh,
    claims_immutable,
    classify_age,
    equal_age_is_stale,
    grants_send,
    halt_blocks_classify,
    halt_blocks_refresh,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    unknown_is_false,
    unknown_is_stale,
    wires_into_run_store,
)

_OBS = 1_780_000_000
_TTL = 3600


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())

    def test_halt_does_block_refresh(self):
        self.assertTrue(halt_blocks_refresh())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_unknown_is_not_stale(self):
        self.assertFalse(unknown_is_stale())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_does_not_wire_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_equal_age_is_not_stale(self):
        self.assertFalse(equal_age_is_stale())

    def test_kinds_are_closed(self):
        self.assertEqual(KINDS, {FRESH, STALE, UNKNOWN})

    def test_classify_signature_has_no_send_halt_knob(self):
        params = inspect.signature(classify_age).parameters
        self.assertEqual(
            list(params),
            ["observed_epoch_s", "as_of_epoch_s", "ttl_s", "error", "intent"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready", "halt", "halt_raw", "now",
        ):
            self.assertNotIn(forbidden, params)

    def test_refresh_signature_has_no_send_knob(self):
        params = inspect.signature(admit_refresh).parameters
        self.assertEqual(list(params), ["classified", "halt"])
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            StaleClass(
                kind=FRESH, observed_epoch_s=_OBS, as_of_epoch_s=_OBS,
                ttl_s=_TTL, age_s=0, grants_send=True)
        with self.assertRaises(FailClosedError):
            RefreshDecision(
                allowed=True, reason=None, kind=STALE, halted=False,
                grants_send=True)


class ClassifyAge(unittest.TestCase):
    def test_fresh_when_age_below_ttl(self):
        got = classify_age(
            observed_epoch_s=_OBS, as_of_epoch_s=_OBS + 10, ttl_s=_TTL)
        self.assertEqual(got.kind, FRESH)
        self.assertEqual(got.age_s, 10)
        self.assertFalse(got.grants_send)

    def test_fresh_when_age_equals_ttl(self):
        got = classify_age(
            observed_epoch_s=_OBS, as_of_epoch_s=_OBS + _TTL, ttl_s=_TTL)
        self.assertEqual(got.kind, FRESH)
        self.assertEqual(got.age_s, _TTL)

    def test_stale_when_age_exceeds_ttl(self):
        got = classify_age(
            observed_epoch_s=_OBS, as_of_epoch_s=_OBS + _TTL + 1, ttl_s=_TTL)
        self.assertEqual(got.kind, STALE)
        self.assertEqual(got.age_s, _TTL + 1)

    def test_missing_observed_is_unknown(self):
        got = classify_age(as_of_epoch_s=_OBS, ttl_s=_TTL)
        self.assertEqual(got.kind, UNKNOWN)
        self.assertIsNone(got.age_s)
        self.assertNotEqual(got.kind, STALE)
        self.assertNotEqual(got.kind, "FALSE")

    def test_missing_as_of_is_unknown(self):
        got = classify_age(observed_epoch_s=_OBS, ttl_s=_TTL)
        self.assertEqual(got.kind, UNKNOWN)
        self.assertIsNone(got.age_s)

    def test_error_is_unknown_not_stale(self):
        got = classify_age(
            observed_epoch_s=_OBS, as_of_epoch_s=_OBS + 10_000,
            ttl_s=_TTL, error=TimeoutError("hung"))
        self.assertEqual(got.kind, UNKNOWN)
        self.assertIsNone(got.age_s)
        self.assertIsNone(got.observed_epoch_s)

    def test_observe_intent_same_as_classify(self):
        got = classify_age(
            observed_epoch_s=_OBS, as_of_epoch_s=_OBS + 1,
            ttl_s=_TTL, intent="observe")
        self.assertEqual(got.kind, FRESH)

    def test_unknown_intent_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_age(observed_epoch_s=_OBS, as_of_epoch_s=_OBS, ttl_s=_TTL,
                         intent="refresh")

    def test_bool_float_str_epoch_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_age(observed_epoch_s=True, as_of_epoch_s=_OBS, ttl_s=_TTL)
        with self.assertRaises(FailClosedError):
            classify_age(
                observed_epoch_s=float(_OBS), as_of_epoch_s=_OBS, ttl_s=_TTL)
        with self.assertRaises(FailClosedError):
            classify_age(
                observed_epoch_s=str(_OBS), as_of_epoch_s=_OBS, ttl_s=_TTL)

    def test_negative_epoch_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_age(observed_epoch_s=-1, as_of_epoch_s=_OBS, ttl_s=_TTL)

    def test_bool_ttl_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_age(observed_epoch_s=_OBS, as_of_epoch_s=_OBS, ttl_s=True)

    def test_negative_ttl_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_age(observed_epoch_s=_OBS, as_of_epoch_s=_OBS, ttl_s=-1)

    def test_inversion_fail_closed_not_stale(self):
        with self.assertRaises(FailClosedError):
            classify_age(
                observed_epoch_s=_OBS + 10, as_of_epoch_s=_OBS, ttl_s=_TTL)

    def test_sealed_intent_fail_closed(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_age(
                        observed_epoch_s=_OBS, as_of_epoch_s=_OBS,
                        ttl_s=_TTL, intent=name)

    def test_frozen_cannot_retcon(self):
        got = classify_age(
            observed_epoch_s=_OBS, as_of_epoch_s=_OBS, ttl_s=_TTL)
        with self.assertRaises(Exception):
            got.kind = STALE  # type: ignore[misc]


class AdmitRefresh(unittest.TestCase):
    def _stale(self) -> StaleClass:
        return classify_age(
            observed_epoch_s=_OBS, as_of_epoch_s=_OBS + _TTL + 5, ttl_s=_TTL)

    def _fresh(self) -> StaleClass:
        return classify_age(
            observed_epoch_s=_OBS, as_of_epoch_s=_OBS, ttl_s=_TTL)

    def test_stale_without_halt_is_allowed(self):
        got = admit_refresh(classified=self._stale(), halt=False)
        self.assertTrue(got.allowed)
        self.assertIsNone(got.reason)
        self.assertFalse(got.grants_send)

    def test_halt_refuses_stale_refresh(self):
        got = admit_refresh(classified=self._stale(), halt=True)
        self.assertFalse(got.allowed)
        self.assertEqual(got.reason, "halt_blocks_start")
        self.assertIn(got.reason, REFUSAL_REASONS)

    def test_corrupt_halt_refuses(self):
        got = admit_refresh(classified=self._stale(), halt="???")
        self.assertFalse(got.allowed)
        self.assertEqual(got.reason, "halt_blocks_start")

    def test_absent_halt_is_running(self):
        got = admit_refresh(classified=self._stale(), halt=None)
        self.assertTrue(got.allowed)

    def test_fresh_is_already_fresh(self):
        got = admit_refresh(classified=self._fresh(), halt=False)
        self.assertFalse(got.allowed)
        self.assertEqual(got.reason, "already_fresh")

    def test_unknown_is_not_admitted(self):
        unknown = classify_age(ttl_s=_TTL)
        got = admit_refresh(classified=unknown, halt=False)
        self.assertFalse(got.allowed)
        self.assertEqual(got.reason, "unknown_age")

    def test_unknown_under_halt_stays_unknown_age(self):
        unknown = classify_age(ttl_s=_TTL)
        got = admit_refresh(classified=unknown, halt=True)
        self.assertEqual(got.reason, "unknown_age")

    def test_non_class_fail_closed(self):
        with self.assertRaises(FailClosedError):
            admit_refresh(classified={"kind": STALE}, halt=False)

    def test_run_store_does_not_import(self):
        import ofn.adapters.run_store as store
        source = inspect.getsource(store)
        self.assertNotIn("stale_class", source)
        self.assertNotIn("fresh_pin", source)


if __name__ == "__main__":
    unittest.main()
