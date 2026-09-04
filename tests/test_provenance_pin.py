"""Kernel-pure provenance pin — complementary to lineage_class.

Genesis+mint and contained+succeed may pin. Orphan is unbound.
Unknown stays unknown. Ready is not authorized. Not wired into
the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.provenance_pin import (
    FAMILIES,
    REFUSAL_REASONS,
    ProvenancePin,
    claims_immutable,
    grants_send,
    halt_blocks_pin,
    orphan_is_contained,
    pin_allows,
    pin_family,
    pin_provenance,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    unknown_is_contained,
    unknown_is_false,
    wires_into_run_store,
)

_ROOT = "run-1780000000-rootaaaaaa"
_CHILD = "run-1780000000-childbbbbb"


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_unknown_is_not_contained(self):
        self.assertFalse(unknown_is_contained())

    def test_orphan_is_not_contained(self):
        self.assertFalse(orphan_is_contained())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_signature_has_no_send_halt_or_immutable_knob(self):
        params = inspect.signature(pin_provenance).parameters
        self.assertEqual(
            list(params),
            ["role", "intended", "node_id", "parent_id"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt",
            "halt_raw",
            "immutable",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            ProvenancePin(
                allowed=True, reason=None, family="genesis",
                role="root", intended="mint", node_id=_ROOT,
                parent_id=None, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            ProvenancePin(
                allowed=True, reason="unbound_orphan", family="genesis",
                role="root", intended="mint", node_id=_ROOT,
                parent_id=None)

    def test_cannot_allow_unbound_or_unknown(self):
        with self.assertRaises(FailClosedError):
            ProvenancePin(
                allowed=True, reason=None, family="unbound",
                role="orphan", intended="succeed", node_id=_CHILD,
                parent_id=_ROOT)
        with self.assertRaises(FailClosedError):
            ProvenancePin(
                allowed=True, reason=None, family="unknown",
                role="unknown", intended="observe", node_id=_ROOT,
                parent_id=None)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            ProvenancePin(
                allowed=False, reason=None, family="unknown",
                role="unknown", intended="observe", node_id=_ROOT,
                parent_id=None)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("unbound_orphan", REFUSAL_REASONS)
        self.assertIn("unknown_role", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)


class ClosedVocabularies(unittest.TestCase):
    def test_families(self):
        self.assertEqual(
            FAMILIES,
            frozenset({"genesis", "contained", "unbound", "unknown"}))


class FamilyMap(unittest.TestCase):
    def test_root_is_genesis(self):
        self.assertEqual(pin_family("root"), "genesis")

    def test_successor_is_contained(self):
        self.assertEqual(pin_family("successor"), "contained")

    def test_orphan_is_unbound(self):
        self.assertEqual(pin_family("orphan"), "unbound")

    def test_unknown_role_is_unknown_family(self):
        self.assertEqual(pin_family("unknown"), "unknown")

    def test_unknown_role_token_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_family("ancestor")
        self.assertNotIn("FALSE", str(ctx.exception))


class PinAllows(unittest.TestCase):
    def test_genesis_mint_allows(self):
        self.assertTrue(pin_allows("root", intended="mint"))

    def test_contained_succeed_allows(self):
        self.assertTrue(pin_allows("successor", intended="succeed"))

    def test_genesis_succeed_does_not_allow(self):
        self.assertFalse(pin_allows("root", intended="succeed"))

    def test_contained_mint_does_not_allow(self):
        self.assertFalse(pin_allows("successor", intended="mint"))

    def test_observe_never_allows(self):
        for role in ("root", "successor", "orphan", "unknown"):
            with self.subTest(role=role):
                self.assertFalse(pin_allows(role, intended="observe"))

    def test_orphan_never_allows(self):
        for intent in ("mint", "succeed", "observe"):
            with self.subTest(intended=intent):
                self.assertFalse(pin_allows("orphan", intended=intent))

    def test_unknown_never_allows(self):
        for intent in ("mint", "succeed", "observe"):
            with self.subTest(intended=intent):
                self.assertFalse(pin_allows("unknown", intended=intent))


class PinMint(unittest.TestCase):
    def test_pin_root_mint(self):
        pin = pin_provenance(
            role="root", intended="mint", node_id=_ROOT)
        self.assertTrue(pin.allowed)
        self.assertEqual(pin.family, "genesis")
        self.assertIsNone(pin.reason)
        self.assertFalse(pin.grants_send)

    def test_pin_successor_succeed(self):
        pin = pin_provenance(
            role="successor", intended="succeed",
            node_id=_CHILD, parent_id=_ROOT)
        self.assertTrue(pin.allowed)
        self.assertEqual(pin.family, "contained")
        self.assertEqual(pin.parent_id, _ROOT)
        self.assertFalse(pin.grants_send)

    def test_pin_orphan_is_unbound(self):
        pin = pin_provenance(
            role="orphan", intended="succeed",
            node_id=_CHILD, parent_id=_ROOT)
        self.assertFalse(pin.allowed)
        self.assertEqual(pin.reason, "unbound_orphan")
        self.assertEqual(pin.family, "unbound")
        self.assertFalse(orphan_is_contained())
        self.assertFalse(pin.grants_send)

    def test_pin_unknown_role_is_unknown(self):
        pin = pin_provenance(
            role="unknown", intended="observe", node_id=_ROOT)
        self.assertFalse(pin.allowed)
        self.assertEqual(pin.reason, "unknown_role")
        self.assertEqual(pin.family, "unknown")
        self.assertFalse(unknown_is_contained())
        self.assertFalse(unknown_is_false())
        self.assertFalse(pin.grants_send)

    def test_role_intent_mismatch(self):
        pin = pin_provenance(
            role="root", intended="succeed", node_id=_ROOT)
        self.assertFalse(pin.allowed)
        self.assertEqual(pin.reason, "role_intent_mismatch")
        self.assertFalse(pin.grants_send)

    def test_self_parent_is_refused(self):
        pin = pin_provenance(
            role="successor", intended="succeed",
            node_id=_CHILD, parent_id=_CHILD)
        self.assertFalse(pin.allowed)
        self.assertEqual(pin.reason, "self_parent")
        self.assertFalse(pin.grants_send)

    def test_pin_is_byte_identical(self):
        a = pin_provenance(role="root", intended="mint", node_id=_ROOT)
        b = pin_provenance(role="root", intended="mint", node_id=_ROOT)
        self.assertEqual(a, b)


class SealedAndShape(unittest.TestCase):
    def test_sealed_node_id_aliases(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "quote-sent",
            "campaign-envelope-ready",
        ):
            with self.subTest(name=name):
                pin = pin_provenance(
                    role="root", intended="mint", node_id=name)
                self.assertFalse(pin.allowed)
                self.assertEqual(pin.reason, "sealed_effect")
                self.assertFalse(pin.grants_send)

    def test_sealed_parent_id_is_refused(self):
        pin = pin_provenance(
            role="successor", intended="succeed",
            node_id=_CHILD, parent_id="send_authorized")
        self.assertFalse(pin.allowed)
        self.assertEqual(pin.reason, "sealed_effect")
        self.assertFalse(pin.grants_send)

    def test_ready_and_authorized_stay_distinct_subjects(self):
        ready = pin_provenance(
            role="root", intended="mint",
            node_id="campaign_envelope_ready")
        auth = pin_provenance(
            role="root", intended="mint", node_id="send_authorized")
        self.assertNotEqual(ready.node_id, auth.node_id)
        self.assertFalse(ready.allowed)
        self.assertFalse(auth.allowed)
        self.assertFalse(ready_is_authorized())

    def test_unknown_role_token_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_provenance(
                role="ancestor", intended="mint", node_id=_ROOT)
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_unknown_intended_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_provenance(role="root", intended="send", node_id=_ROOT)
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_empty_node_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_provenance(role="root", intended="mint", node_id="  ")

    def test_bool_node_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_provenance(role="root", intended="mint", node_id=True)


if __name__ == "__main__":
    unittest.main()
