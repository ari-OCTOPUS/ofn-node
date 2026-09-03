"""Kernel-pure architecture-contract bind — complementary to otel_map.

A contract is bound to a closed surface. Observe is read-only.
Bind is admitted for known names. Mutate is never admitted.
Timeout is UNKNOWN, not a concurrent-write proof.
Ready is not authorized. This module is not wired into the
run store. Distinct from #77 otel_map and from census_class.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.arch_bind import (
    CONTRACTS,
    INTENTS,
    REFUSAL_REASONS,
    SURFACES,
    BindDecision,
    bind_arch,
    claims_immutable,
    classify_timeout,
    copies_canonical,
    grants_send,
    halt_blocks_bind,
    mutates_contract,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    unknown_is_false,
)
from ofn.kernel.errors import FailClosedError


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_bind(self):
        self.assertFalse(halt_blocks_bind())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(classify_timeout(), "UNKNOWN")

    def test_does_not_mutate(self):
        self.assertFalse(mutates_contract())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_does_not_copy_canonical(self):
        self.assertFalse(copies_canonical())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(bind_arch).parameters
        self.assertEqual(
            list(params),
            ["contract", "surface", "intended", "timed_out"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt",
            "halt_raw",
            "mutate",
            "body",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            BindDecision(
                allowed=True, reason=None, contract="task_envelope",
                surface="kernel", intended="bind", timed_out=False,
                grants_send=True)
        with self.assertRaises(FailClosedError):
            BindDecision(
                allowed=False, reason="sealed_effect",
                contract="send_authorized", surface="kernel",
                intended="bind", timed_out=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            BindDecision(
                allowed=True, reason="mutate_forbidden",
                contract="task_envelope", surface="kernel",
                intended="bind", timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            BindDecision(
                allowed=False, reason=None, contract="task_envelope",
                surface="kernel", intended="mutate", timed_out=False)
        with self.assertRaises(FailClosedError):
            BindDecision(
                allowed=False, reason="send_authorized",
                contract="task_envelope", surface="kernel",
                intended="mutate", timed_out=False)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("mutate_forbidden", REFUSAL_REASONS)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            BindDecision(
                allowed=True, reason=None, contract="task_envelope",
                surface="kernel", intended="bind", timed_out=1)
        with self.assertRaises(FailClosedError):
            bind_arch(
                contract="task_envelope", surface="kernel",
                intended="observe", timed_out=1)
        with self.assertRaises(FailClosedError):
            bind_arch(
                contract="task_envelope", surface="kernel",
                intended="observe", timed_out="true")


class ClosedVocabularies(unittest.TestCase):
    def test_contracts_are_the_nine_priority_names(self):
        self.assertEqual(
            CONTRACTS,
            frozenset({
                "task_envelope",
                "typed_event",
                "run_store",
                "dedup",
                "receipt",
                "halt",
                "otel_map",
                "token_budget",
                "worktree_inventory",
            }),
        )

    def test_surfaces_and_intents(self):
        self.assertEqual(SURFACES, frozenset({"kernel", "adapter", "test", "doc"}))
        self.assertEqual(INTENTS, frozenset({"bind", "observe", "mutate"}))

    def test_sealed_names_are_not_contracts(self):
        for sealed in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(sealed, CONTRACTS)
            self.assertNotIn(sealed, SURFACES)
            self.assertNotIn(sealed, INTENTS)


class AdmitBind(unittest.TestCase):
    def test_bind_known_contract_to_kernel(self):
        d = bind_arch(
            contract="task_envelope", surface="kernel", intended="bind")
        self.assertTrue(d.allowed)
        self.assertIsNone(d.reason)
        self.assertEqual(d.contract, "task_envelope")
        self.assertEqual(d.surface, "kernel")
        self.assertFalse(d.grants_send)
        self.assertFalse(d.timed_out)

    def test_observe_every_contract_on_every_surface(self):
        for contract in CONTRACTS:
            for surface in SURFACES:
                d = bind_arch(
                    contract=contract, surface=surface, intended="observe")
                self.assertTrue(d.allowed, msg=f"{contract}/{surface}")
                self.assertFalse(d.grants_send)

    def test_bind_every_known_pair(self):
        for contract in CONTRACTS:
            d = bind_arch(
                contract=contract, surface="test", intended="bind")
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)

    def test_mutate_is_always_refused(self):
        d = bind_arch(
            contract="receipt", surface="doc", intended="mutate")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "mutate_forbidden")
        self.assertFalse(d.grants_send)
        self.assertFalse(mutates_contract())

    def test_timeout_records_unknown_and_still_admits_observe(self):
        d = bind_arch(
            contract="dedup", surface="adapter", intended="observe",
            timed_out=True)
        self.assertTrue(d.allowed)
        self.assertTrue(d.timed_out)
        self.assertEqual(classify_timeout(), "UNKNOWN")
        self.assertFalse(timeout_proves_concurrent())
        self.assertFalse(d.grants_send)

    def test_timeout_does_not_refuse_a_valid_bind(self):
        d = bind_arch(
            contract="halt", surface="kernel", intended="bind",
            timed_out=True)
        self.assertTrue(d.allowed)
        self.assertTrue(d.timed_out)
        self.assertFalse(d.grants_send)


class FailClosedUnknown(unittest.TestCase):
    def test_unknown_contract_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            bind_arch(
                contract="DEAD_SOURCE", surface="kernel", intended="observe")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_surface_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            bind_arch(
                contract="task_envelope", surface="network", intended="bind")
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_unknown_intent_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            bind_arch(
                contract="task_envelope", surface="kernel", intended="send")
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_empty_and_bool_names_fail_closed(self):
        with self.assertRaises(FailClosedError):
            bind_arch(contract="", surface="kernel", intended="observe")
        with self.assertRaises(FailClosedError):
            bind_arch(contract=True, surface="kernel", intended="observe")
        with self.assertRaises(FailClosedError):
            bind_arch(contract="task_envelope", surface="", intended="observe")
        with self.assertRaises(FailClosedError):
            bind_arch(
                contract="task_envelope", surface="kernel", intended="")


class SealedNames(unittest.TestCase):
    def test_sealed_contract_refuses(self):
        for sealed in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "send-authorized",
            "Send_Authorized",
        ):
            d = bind_arch(
                contract=sealed, surface="kernel", intended="bind")
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)

    def test_sealed_surface_refuses(self):
        d = bind_arch(
            contract="task_envelope", surface="quote_sent",
            intended="observe")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")

    def test_ready_is_not_authorized_as_a_contract(self):
        ready = bind_arch(
            contract="campaign_envelope_ready", surface="kernel",
            intended="bind")
        auth = bind_arch(
            contract="send_authorized", surface="kernel", intended="bind")
        self.assertNotEqual(ready.contract, auth.contract)
        self.assertFalse(ready.allowed)
        self.assertFalse(auth.allowed)
        self.assertFalse(ready_is_authorized())


class DualRecord(unittest.TestCase):
    def test_allowed_and_grants_send_are_both_recorded(self):
        d = bind_arch(
            contract="otel_map", surface="kernel", intended="bind")
        self.assertTrue(hasattr(d, "allowed"))
        self.assertTrue(hasattr(d, "grants_send"))
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_refused_and_grants_send_are_both_recorded(self):
        d = bind_arch(
            contract="token_budget", surface="doc", intended="mutate")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)


if __name__ == "__main__":
    unittest.main()
