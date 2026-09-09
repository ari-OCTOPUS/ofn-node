"""Kernel-pure cut pin — complementary to epoch_class and the run store.

An open window may be pinned cut. An already-cut window refuses
(already_cut), not rewrite. Missing prior is UNKNOWN, not open.
HALT is not a parameter. A sealed send/ready name refuses. Cut is
not truncate and not rewrite. Ready is not authorized. This module
is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.cut_pin import (
    REFUSAL_REASONS,
    CutPin,
    claims_immutable,
    cut_is_rewrite,
    cut_is_truncate,
    grants_send,
    halt_blocks_cut,
    later_disarm_supersedes,
    pin_cut,
    proposal_is_execution,
    ready_is_authorized,
    unknown_is_false,
    unknown_prior_is_open,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError

_E1 = "epoch-1756857600-abcdef0123"
_E2 = "epoch-1756857601-bbbbbbbbbb"
_RUN = "run-1756857600-abcdef0123"


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_cut(self):
        self.assertFalse(halt_blocks_cut())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_prior_is_not_open(self):
        self.assertFalse(unknown_prior_is_open())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_cut_is_not_truncate(self):
        self.assertFalse(cut_is_truncate())

    def test_cut_is_not_rewrite(self):
        self.assertFalse(cut_is_rewrite())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_later_disarm_supersedes_ready(self):
        self.assertTrue(later_disarm_supersedes())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(pin_cut).parameters
        self.assertEqual(list(params), ["epoch_id", "prior_state"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            CutPin(allowed=True, reason=None, epoch_id=_E1,
                   prior_state="open", grants_send=True)
        with self.assertRaises(FailClosedError):
            CutPin(allowed=False, reason="already_cut", epoch_id=_E1,
                   prior_state="cut", grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            CutPin(allowed=True, reason="already_cut", epoch_id=_E1,
                   prior_state="open")

    def test_allowed_requires_open_prior(self):
        with self.assertRaises(FailClosedError):
            CutPin(allowed=True, reason=None, epoch_id=_E1,
                   prior_state="cut")

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            CutPin(allowed=False, reason=None, epoch_id=_E1,
                   prior_state="open")
        with self.assertRaises(FailClosedError):
            CutPin(allowed=False, reason="send_authorized", epoch_id=_E1,
                   prior_state="open")
        self.assertIn("already_cut", REFUSAL_REASONS)
        self.assertIn("rewrite", REFUSAL_REASONS)
        self.assertIn("truncate", REFUSAL_REASONS)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_allowed_decision_refuses_sealed_names(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    CutPin(allowed=True, reason=None, epoch_id=name,
                           prior_state="open")
                with self.assertRaises(FailClosedError):
                    CutPin(allowed=True, reason=None, epoch_id=_E1,
                           prior_state=name)

    def test_already_cut_cannot_carry_a_sealed_name(self):
        with self.assertRaises(FailClosedError):
            CutPin(allowed=False, reason="already_cut",
                   epoch_id="send_authorized", prior_state="cut")

    def test_sealed_effect_refusal_names_the_subject(self):
        d = CutPin(allowed=False, reason="sealed_effect",
                   epoch_id="send_authorized", prior_state="open")
        self.assertEqual(d.epoch_id, "send_authorized")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)

    def test_allowed_must_be_epoch_shaped(self):
        with self.assertRaises(FailClosedError):
            CutPin(allowed=True, reason=None, epoch_id="not-an-epoch",
                   prior_state="open")
        with self.assertRaises(FailClosedError):
            CutPin(allowed=True, reason=None, epoch_id=_RUN,
                   prior_state="open")


class OpenPriorAdmitsCut(unittest.TestCase):
    def test_open_valid_id(self):
        d = pin_cut(epoch_id=_E1, prior_state="open")
        self.assertTrue(d.allowed)
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)
        self.assertEqual(d.prior_state, "open")
        self.assertEqual(d.epoch_id, _E1)

    def test_open_other_valid_id(self):
        d = pin_cut(epoch_id=_E2, prior_state="OPEN")
        self.assertTrue(d.allowed)
        self.assertEqual(d.epoch_id, _E2)
        self.assertFalse(d.grants_send)


class KnownRefusals(unittest.TestCase):
    def test_already_cut_is_not_a_rewrite(self):
        d = pin_cut(epoch_id=_E1, prior_state="cut")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "already_cut")
        self.assertEqual(d.prior_state, "cut")
        self.assertFalse(d.grants_send)
        self.assertNotEqual(d.reason, "rewrite")

    def test_rewrite_prior_is_refused(self):
        d = pin_cut(epoch_id=_E1, prior_state="rewrite")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "rewrite")
        self.assertFalse(d.grants_send)

    def test_truncate_prior_is_refused(self):
        d = pin_cut(epoch_id=_E1, prior_state="truncate")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "truncate")
        self.assertFalse(d.grants_send)


class SealedNames(unittest.TestCase):
    def test_sealed_epoch_id_refuses(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "send-authorized"):
            with self.subTest(name=name):
                d = pin_cut(epoch_id=name, prior_state="open")
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)

    def test_sealed_prior_refuses(self):
        d = pin_cut(epoch_id=_E1, prior_state="send_authorized")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")


class ShapeAndUnknown(unittest.TestCase):
    def test_missing_prior_is_unknown_not_open(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_cut(epoch_id=_E1, prior_state=None)
        self.assertIn("UNKNOWN", str(ctx.exception))
        self.assertIn("not open", str(ctx.exception))

    def test_run_id_is_not_an_epoch(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_cut(epoch_id=_RUN, prior_state="open")
        self.assertIn("run_id", str(ctx.exception))

    def test_malformed_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_cut(epoch_id="epoch-short", prior_state="open")

    def test_unknown_prior_is_not_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_cut(epoch_id=_E1, prior_state="mystery")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_missing_names_fail_closed(self):
        with self.assertRaises(FailClosedError):
            pin_cut(epoch_id=None, prior_state="open")
        with self.assertRaises(FailClosedError):
            pin_cut(epoch_id=True, prior_state="open")
        with self.assertRaises(FailClosedError):
            pin_cut(epoch_id="", prior_state="open")
        with self.assertRaises(FailClosedError):
            pin_cut(epoch_id=_E1, prior_state=False)


if __name__ == "__main__":
    unittest.main()
