"""Kernel-pure mint fence — complementary to envelope.create_envelope.

A proposed run_id is admitted only at trusted_boundary against a
known registry. HALT is not a parameter. A sealed send/ready name
refuses. A missing registry is UNKNOWN, not empty. Ready is not
authorized. This module is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.envelope import RUN_ID_RE
from ofn.kernel.errors import FailClosedError
from ofn.kernel.mint_fence import (
    BOUNDARIES,
    REFUSAL_REASONS,
    UNTRUSTED_BOUNDARIES,
    MintDecision,
    admit_mint,
    claims_immutable,
    grants_send,
    halt_blocks_mint,
    proposal_is_execution,
    ready_is_authorized,
    unknown_is_false,
    unknown_registry_is_empty,
)

_FRESH = "run-1756857600-abcdef0123"
_OTHER = "run-1756857601-bbbbbbbbbb"


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_mint_lookup(self):
        self.assertFalse(halt_blocks_mint())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_registry_is_not_empty(self):
        self.assertFalse(unknown_registry_is_empty())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(admit_mint).parameters
        self.assertEqual(list(params), ["boundary", "proposed_id", "existing_ids"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            MintDecision(allowed=True, reason=None,
                         boundary="trusted_boundary",
                         proposed_id=_FRESH, grants_send=True)
        with self.assertRaises(FailClosedError):
            MintDecision(allowed=False, reason="id_collision",
                         boundary="trusted_boundary",
                         proposed_id=_FRESH, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            MintDecision(allowed=True, reason="id_collision",
                         boundary="trusted_boundary", proposed_id=_FRESH)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            MintDecision(allowed=False, reason=None,
                         boundary="trusted_boundary", proposed_id=_FRESH)
        with self.assertRaises(FailClosedError):
            MintDecision(allowed=False, reason="send_authorized",
                         boundary="trusted_boundary", proposed_id=_FRESH)
        self.assertIn("id_collision", REFUSAL_REASONS)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("untrusted_boundary", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_allowed_decision_refuses_sealed_names(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    MintDecision(allowed=True, reason=None,
                                 boundary=name, proposed_id=_FRESH)
                with self.assertRaises(FailClosedError):
                    MintDecision(allowed=True, reason=None,
                                 boundary="trusted_boundary",
                                 proposed_id=name)

    def test_collision_refusal_cannot_carry_a_sealed_name(self):
        with self.assertRaises(FailClosedError):
            MintDecision(allowed=False, reason="id_collision",
                         boundary="trusted_boundary",
                         proposed_id="send_authorized")

    def test_sealed_effect_refusal_names_the_subject(self):
        d = MintDecision(allowed=False, reason="sealed_effect",
                         boundary="trusted_boundary",
                         proposed_id="send_authorized")
        self.assertEqual(d.proposed_id, "send_authorized")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)

    def test_allowed_must_be_boundary_shaped(self):
        with self.assertRaises(FailClosedError):
            MintDecision(allowed=True, reason=None,
                         boundary="trusted_boundary",
                         proposed_id="not-a-run-id")


class Vocabulary(unittest.TestCase):
    def test_closed_boundary_vocabulary(self):
        self.assertEqual(BOUNDARIES, frozenset({"trusted_boundary"}))

    def test_closed_untrusted_vocabulary(self):
        self.assertEqual(UNTRUSTED_BOUNDARIES, frozenset({"arm", "pack", "model"}))

    def test_fresh_id_matches_envelope_regex(self):
        self.assertTrue(RUN_ID_RE.match(_FRESH))
        self.assertTrue(RUN_ID_RE.match(_OTHER))


class TrustedBoundaryAdmitsFresh(unittest.TestCase):
    def test_fresh_id_against_empty_registry(self):
        d = admit_mint(boundary="trusted_boundary",
                       proposed_id=_FRESH, existing_ids=set())
        self.assertTrue(d.allowed)
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)
        self.assertEqual(d.boundary, "trusted_boundary")
        self.assertEqual(d.proposed_id, _FRESH)

    def test_fresh_id_against_other_ids(self):
        d = admit_mint(boundary="trusted_boundary",
                       proposed_id=_FRESH, existing_ids={_OTHER})
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_list_registry_is_accepted(self):
        d = admit_mint(boundary="trusted_boundary",
                       proposed_id=_FRESH, existing_ids=[_OTHER])
        self.assertTrue(d.allowed)

    def test_replay_is_byte_identical(self):
        a = admit_mint(boundary="trusted_boundary",
                       proposed_id=_FRESH, existing_ids={_OTHER})
        b = admit_mint(boundary="trusted_boundary",
                       proposed_id=_FRESH, existing_ids={_OTHER})
        self.assertEqual(a, b)
        self.assertTrue(a.allowed)


class CollisionRefuses(unittest.TestCase):
    def test_same_id_is_collision(self):
        d = admit_mint(boundary="trusted_boundary",
                       proposed_id=_FRESH, existing_ids={_FRESH})
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "id_collision")
        self.assertFalse(d.grants_send)

    def test_collision_is_not_a_send(self):
        d = admit_mint(boundary="trusted_boundary",
                       proposed_id=_FRESH, existing_ids={_FRESH, _OTHER})
        self.assertEqual(d.reason, "id_collision")
        self.assertFalse(d.grants_send)
        self.assertFalse(grants_send())


class UntrustedBoundaryRefuses(unittest.TestCase):
    def test_arm_pack_model_refused(self):
        for name in ("arm", "pack", "model"):
            with self.subTest(name=name):
                d = admit_mint(boundary=name, proposed_id=_FRESH,
                               existing_ids=set())
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "untrusted_boundary")
                self.assertFalse(d.grants_send)

    def test_unknown_boundary_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_mint(boundary="adapter_guess", proposed_id=_FRESH,
                       existing_ids=set())
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())


class SealedNameRefusesMint(unittest.TestCase):
    def test_sealed_proposed_id_aliases(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "SEND_AUTHORIZED",
                     "quote-sent", "campaign-envelope-ready"):
            with self.subTest(name=name):
                d = admit_mint(boundary="trusted_boundary",
                               proposed_id=name, existing_ids=set())
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)

    def test_sealed_boundary_aliases(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                d = admit_mint(boundary=name, proposed_id=_FRESH,
                               existing_ids=set())
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")

    def test_ready_and_authorized_stay_distinct(self):
        ready = admit_mint(boundary="trusted_boundary",
                           proposed_id="campaign_envelope_ready",
                           existing_ids=set())
        auth = admit_mint(boundary="trusted_boundary",
                          proposed_id="send_authorized",
                          existing_ids=set())
        self.assertEqual(ready.reason, "sealed_effect")
        self.assertEqual(auth.reason, "sealed_effect")
        self.assertNotEqual(ready.proposed_id, auth.proposed_id)
        self.assertFalse(ready_is_authorized())


class UnknownAndMalformedFailClosed(unittest.TestCase):
    def test_none_registry_is_unknown_not_empty(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_mint(boundary="trusted_boundary",
                       proposed_id=_FRESH, existing_ids=None)
        self.assertIn("UNKNOWN", str(ctx.exception))
        self.assertFalse(unknown_registry_is_empty())

    def test_string_registry_is_not_a_set(self):
        with self.assertRaises(FailClosedError):
            admit_mint(boundary="trusted_boundary",
                       proposed_id=_FRESH, existing_ids=_FRESH)

    def test_bool_registry_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_mint(boundary="trusted_boundary",
                       proposed_id=_FRESH, existing_ids=True)
        with self.assertRaises(FailClosedError):
            admit_mint(boundary="trusted_boundary",
                       proposed_id=_FRESH, existing_ids=False)

    def test_bool_boundary_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_mint(boundary=True, proposed_id=_FRESH, existing_ids=set())

    def test_empty_proposed_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_mint(boundary="trusted_boundary",
                       proposed_id="  ", existing_ids=set())

    def test_malformed_run_id_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_mint(boundary="trusted_boundary",
                       proposed_id="run-nope", existing_ids=set())
        self.assertIn("boundary", str(ctx.exception).lower())

    def test_uppercase_rand_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_mint(boundary="trusted_boundary",
                       proposed_id="run-1756857600-ABCDEF0123",
                       existing_ids=set())

    def test_sealed_name_in_registry_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_mint(boundary="trusted_boundary",
                       proposed_id=_FRESH,
                       existing_ids={_OTHER, "quote_sent"})

    def test_blank_registry_entry_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_mint(boundary="trusted_boundary",
                       proposed_id=_FRESH, existing_ids={"  "})


if __name__ == "__main__":
    unittest.main()
