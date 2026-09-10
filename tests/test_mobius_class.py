"""Contract tests for mobius_class (P1 complementary).

A μ family is not a send. Missing is UNKNOWN, not FALSE
and not 0. Timeout does not prove a writer. Ready is not
authorized. Distinct from cube/cubic, square/root,
prime/composite, coprime/common, sign/magnitude.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.mobius_class import (
    CLASSIFY,
    FAMILIES,
    INSPECT,
    INTENTS,
    MINUS,
    OBSERVE,
    PLUS,
    SAMPLE,
    UNKNOWN,
    ZERO,
    MobiusBind,
    admit_mobius,
    bind_mobius,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_sample,
    later_disarm_supersedes,
    measured_one_is_unknown,
    measured_zero_is_unknown,
    minus_is_false,
    mints_run_id,
    missing_mu_is_zero,
    mu_of,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
    zero_is_false,
)

_SLOT = "env-mob-0001"


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("sample"), SAMPLE)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(classify_intent("inspect"), INSPECT)
        self.assertEqual(
            INTENTS, frozenset({SAMPLE, CLASSIFY, OBSERVE, INSPECT}))

    def test_hyphen_and_case_fold(self):
        self.assertEqual(classify_intent("SAMPLE"), SAMPLE)
        self.assertEqual(classify_intent(" Inspect "), INSPECT)

    def test_missing_is_unknown_not_false(self):
        self.assertEqual(classify_intent(None), UNKNOWN)
        self.assertNotEqual(classify_intent(None), "FALSE")
        self.assertIsNot(classify_intent(None), False)

    def test_empty_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_intent("")
        with self.assertRaises(FailClosedError):
            classify_intent("   ")

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_intent(True)
        with self.assertRaises(FailClosedError):
            classify_intent(False)

    def test_int_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_intent(1)

    def test_unknown_intent_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_intent("resend")
        with self.assertRaises(FailClosedError):
            classify_intent("send")
        with self.assertRaises(FailClosedError):
            classify_intent("consume")
        with self.assertRaises(FailClosedError):
            classify_intent("measure")

    def test_send_names_fail_closed(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "send-authorized",
            "Quote_Sent",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_intent(name)


class ClassifyFamily(unittest.TestCase):
    def test_closed_families(self):
        self.assertEqual(classify_family(1), PLUS)
        self.assertEqual(classify_family(2), MINUS)
        self.assertEqual(classify_family(4), ZERO)
        self.assertEqual(FAMILIES, frozenset({ZERO, PLUS, MINUS}))

    def test_unit_is_plus_never_unknown(self):
        self.assertEqual(classify_family(1), PLUS)
        self.assertEqual(mu_of(1), 1)
        self.assertFalse(measured_one_is_unknown())

    def test_square_factor_is_zero_never_unknown(self):
        self.assertEqual(classify_family(4), ZERO)
        self.assertEqual(mu_of(4), 0)
        self.assertEqual(classify_family(9), ZERO)
        self.assertEqual(mu_of(8), 0)
        self.assertFalse(measured_zero_is_unknown())
        self.assertFalse(zero_is_false())

    def test_single_prime_is_minus(self):
        self.assertEqual(classify_family(2), MINUS)
        self.assertEqual(mu_of(2), -1)
        self.assertEqual(classify_family(3), MINUS)
        self.assertEqual(classify_family(5), MINUS)
        self.assertFalse(minus_is_false())

    def test_two_distinct_primes_is_plus(self):
        self.assertEqual(classify_family(6), PLUS)
        self.assertEqual(mu_of(6), 1)
        self.assertEqual(classify_family(10), PLUS)
        self.assertEqual(mu_of(15), 1)

    def test_three_distinct_primes_is_minus(self):
        self.assertEqual(classify_family(30), MINUS)
        self.assertEqual(mu_of(30), -1)

    def test_n_less_than_one_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_family(0)
        self.assertIn("n < 1", str(ctx.exception))
        with self.assertRaises(FailClosedError):
            classify_family(-1)
        with self.assertRaises(FailClosedError):
            mu_of(0)

    def test_missing_is_none_not_false_or_zero(self):
        self.assertIsNone(classify_family(None))
        self.assertIsNone(mu_of(None))
        self.assertIsNot(classify_family(None), False)
        self.assertIsNot(mu_of(None), 0)
        self.assertFalse(missing_mu_is_zero())

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_family(6, timeout=True))
        self.assertIsNone(mu_of(6, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(6, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_family(6, timeout=1)

    def test_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(True)
        with self.assertRaises(FailClosedError):
            classify_family(False)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(6.0)
        with self.assertRaises(FailClosedError):
            classify_family(1.0)


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(admit_mobius("classify", 4, halted=True), True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(admit_mobius("observe", 4, halted=True), True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(admit_mobius("inspect", 6, halted=True), True)

    def test_admit_sample_refused_when_halted(self):
        self.assertIs(admit_mobius("sample", 6, halted=True), False)
        self.assertIs(admit_mobius("sample", 6, halted=False), True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(admit_mobius("sample", 6, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_mobius(None, 6))
        self.assertIsNone(admit_mobius("classify", None))

    def test_admit_zero_is_not_a_send_false(self):
        self.assertIs(admit_mobius("classify", 4), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_mobius("classify", 6, halted="yes")

    def test_bind_records_mu(self):
        bound = bind_mobius("classify", 6, slot=_SLOT)
        self.assertIsInstance(bound, MobiusBind)
        self.assertEqual(bound.family, PLUS)
        self.assertEqual(bound.mu, 1)
        self.assertEqual(bound.value, 6)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.slot, _SLOT)

    def test_bind_records_minus(self):
        bound = bind_mobius("observe", 30, slot=_SLOT)
        self.assertEqual(bound.family, MINUS)
        self.assertEqual(bound.mu, -1)

    def test_bind_records_zero(self):
        bound = bind_mobius("inspect", 4, slot=_SLOT)
        self.assertEqual(bound.family, ZERO)
        self.assertEqual(bound.mu, 0)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, 6, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, slot=_SLOT))
        self.assertIsNone(try_bind("classify", 6, slot=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_mobius(None, 6, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            bind_mobius("classify", None, slot=_SLOT)

    def test_bind_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_mobius(
                "classify", 6, slot="campaign_envelope_ready")

    def test_bind_empty_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_mobius("classify", 6, slot="")

    def test_bind_n_less_than_one_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_mobius("classify", 0, slot=_SLOT)


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertFalse(rearms_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertFalse(halt_blocks_inspect())
        self.assertTrue(halt_blocks_sample())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_timeout_does_not_prove_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_does_not_mint(self):
        self.assertFalse(mints_run_id())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_later_disarm_supersedes(self):
        self.assertTrue(later_disarm_supersedes())

    def test_missing_mu_is_not_zero(self):
        self.assertFalse(missing_mu_is_zero())

    def test_classify_family_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_family).parameters
        self.assertEqual(list(params), ["value", "timeout"])
        for forbidden in (
            "halted", "now", "resend", "send_authorized",
            "quote_sent", "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_mobius).parameters
        self.assertEqual(
            list(params),
            ["intent", "value", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
