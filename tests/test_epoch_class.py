"""Kernel-pure epoch class — complementary to the run store.

A named window is classified. Only open is admitted. cut, rewrite,
and truncate refuse. HALT is not a parameter. A sealed send/ready
name refuses. Unknown state is UNKNOWN, not open. A run_id is not
an epoch. Ready is not authorized. This module is not wired into
the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.envelope import RUN_ID_RE
from ofn.kernel.epoch_class import (
    EPOCH_ID_RE,
    REFUSED_STATES,
    REFUSAL_REASONS,
    STATES,
    EpochDecision,
    admit_epoch,
    claims_immutable,
    classify_state,
    grants_send,
    halt_blocks_epoch,
    is_epoch_id,
    later_disarm_supersedes,
    proposal_is_execution,
    ready_is_authorized,
    unknown_is_false,
    unknown_state_is_open,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError

_E1 = "epoch-1756857600-abcdef0123"
_E2 = "epoch-1756857601-bbbbbbbbbb"
_RUN = "run-1756857600-abcdef0123"


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_epoch_classify(self):
        self.assertFalse(halt_blocks_epoch())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_state_is_not_open(self):
        self.assertFalse(unknown_state_is_open())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_later_disarm_supersedes_ready(self):
        self.assertTrue(later_disarm_supersedes())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(admit_epoch).parameters
        self.assertEqual(list(params), ["state", "epoch_id"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            EpochDecision(allowed=True, reason=None, state="open",
                          epoch_id=_E1, grants_send=True)
        with self.assertRaises(FailClosedError):
            EpochDecision(allowed=False, reason="cut", state="cut",
                          epoch_id=_E1, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            EpochDecision(allowed=True, reason="cut", state="open",
                          epoch_id=_E1)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            EpochDecision(allowed=False, reason=None, state="open",
                          epoch_id=_E1)
        with self.assertRaises(FailClosedError):
            EpochDecision(allowed=False, reason="send_authorized",
                          state="open", epoch_id=_E1)
        self.assertIn("cut", REFUSAL_REASONS)
        self.assertIn("rewrite", REFUSAL_REASONS)
        self.assertIn("truncate", REFUSAL_REASONS)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_allowed_decision_refuses_sealed_names(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    EpochDecision(allowed=True, reason=None,
                                  state=name, epoch_id=_E1)
                with self.assertRaises(FailClosedError):
                    EpochDecision(allowed=True, reason=None,
                                  state="open", epoch_id=name)

    def test_cut_refusal_cannot_carry_a_sealed_name(self):
        with self.assertRaises(FailClosedError):
            EpochDecision(allowed=False, reason="cut",
                          state="cut", epoch_id="send_authorized")

    def test_sealed_effect_refusal_names_the_subject(self):
        d = EpochDecision(allowed=False, reason="sealed_effect",
                          state="open", epoch_id="send_authorized")
        self.assertEqual(d.epoch_id, "send_authorized")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)

    def test_allowed_must_be_epoch_shaped(self):
        with self.assertRaises(FailClosedError):
            EpochDecision(allowed=True, reason=None, state="open",
                          epoch_id="not-an-epoch")
        with self.assertRaises(FailClosedError):
            EpochDecision(allowed=True, reason=None, state="open",
                          epoch_id=_RUN)


class Vocabulary(unittest.TestCase):
    def test_closed_state_vocabulary(self):
        self.assertEqual(STATES, frozenset({"open"}))

    def test_closed_refused_vocabulary(self):
        self.assertEqual(REFUSED_STATES,
                         frozenset({"cut", "rewrite", "truncate"}))

    def test_epoch_id_is_not_a_run_id(self):
        self.assertTrue(EPOCH_ID_RE.match(_E1))
        self.assertTrue(EPOCH_ID_RE.match(_E2))
        self.assertTrue(RUN_ID_RE.match(_RUN))
        self.assertFalse(EPOCH_ID_RE.match(_RUN))
        self.assertFalse(RUN_ID_RE.match(_E1))
        self.assertTrue(is_epoch_id(_E1))
        self.assertFalse(is_epoch_id(_RUN))
        self.assertFalse(is_epoch_id(None))
        self.assertFalse(is_epoch_id(True))
        self.assertFalse(is_epoch_id(""))


class ClassifyState(unittest.TestCase):
    def test_open_is_open(self):
        self.assertEqual(classify_state("open"), "open")
        self.assertEqual(classify_state("OPEN"), "open")

    def test_known_refusals_are_named(self):
        for name in ("cut", "rewrite", "truncate"):
            with self.subTest(name=name):
                self.assertEqual(classify_state(name), name)
                self.assertEqual(classify_state(name.upper()), name)

    def test_unknown_state_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_state("DEAD_STATE")
        self.assertIn("unknown", str(ctx.exception).lower())
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_missing_and_bool_fail_closed(self):
        for bad in (None, True, False, "", "   ", 1):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    classify_state(bad)


class OpenEpochAdmitted(unittest.TestCase):
    def test_open_valid_id(self):
        d = admit_epoch(state="open", epoch_id=_E1)
        self.assertTrue(d.allowed)
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)
        self.assertEqual(d.state, "open")
        self.assertEqual(d.epoch_id, _E1)

    def test_open_other_valid_id(self):
        d = admit_epoch(state="open", epoch_id=_E2)
        self.assertTrue(d.allowed)
        self.assertEqual(d.epoch_id, _E2)
        self.assertFalse(d.grants_send)


class KnownRefusals(unittest.TestCase):
    def test_cut_is_refused(self):
        d = admit_epoch(state="cut", epoch_id=_E1)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "cut")
        self.assertFalse(d.grants_send)

    def test_rewrite_is_refused(self):
        d = admit_epoch(state="rewrite", epoch_id=_E1)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "rewrite")
        self.assertFalse(d.grants_send)

    def test_truncate_is_refused(self):
        d = admit_epoch(state="truncate", epoch_id=_E1)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "truncate")
        self.assertFalse(d.grants_send)


class SealedNames(unittest.TestCase):
    def test_sealed_epoch_id_refuses(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "send-authorized"):
            with self.subTest(name=name):
                d = admit_epoch(state="open", epoch_id=name)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)

    def test_sealed_state_refuses(self):
        d = admit_epoch(state="send_authorized", epoch_id=_E1)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")


class ShapeAndUnknown(unittest.TestCase):
    def test_run_id_is_not_an_epoch(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_epoch(state="open", epoch_id=_RUN)
        self.assertIn("run_id", str(ctx.exception))

    def test_malformed_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_epoch(state="open", epoch_id="epoch-short")
        with self.assertRaises(FailClosedError):
            admit_epoch(state="open", epoch_id="window-1756857600-abcdef0123")

    def test_unknown_state_is_not_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_epoch(state="mystery", epoch_id=_E1)
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_missing_names_fail_closed(self):
        with self.assertRaises(FailClosedError):
            admit_epoch(state=None, epoch_id=_E1)
        with self.assertRaises(FailClosedError):
            admit_epoch(state="open", epoch_id=None)
        with self.assertRaises(FailClosedError):
            admit_epoch(state=True, epoch_id=_E1)
        with self.assertRaises(FailClosedError):
            admit_epoch(state="open", epoch_id="")


if __name__ == "__main__":
    unittest.main()
