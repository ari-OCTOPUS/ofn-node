"""Kernel-pure append class — complementary to the run store.

A write mode is classified. Only append is admitted. rewrite and
truncate refuse. HALT is not a parameter. A sealed send/ready name
refuses. Unknown mode is UNKNOWN, not rewrite. Ready is not
authorized. This module is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import (
    BUDGET_DEBIT,
    EVENT_KINDS,
    EXECUTION_RECEIPT,
    RUN_CLOSED,
    RUN_CREATED,
    RUN_REJECTED,
    TOOL_INVOKED,
)
from ofn.kernel.append_class import (
    MODES,
    REFUSED_MODES,
    REFUSAL_REASONS,
    AppendDecision,
    admit_append,
    claims_immutable,
    classify_mode,
    grants_send,
    halt_blocks_append,
    proposal_is_execution,
    ready_is_authorized,
    unknown_is_false,
    unknown_mode_is_rewrite,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_appends(self):
        self.assertFalse(halt_blocks_append())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_mode_is_not_rewrite(self):
        self.assertFalse(unknown_mode_is_rewrite())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(admit_append).parameters
        self.assertEqual(list(params), ["mode", "kind"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            AppendDecision(allowed=True, reason=None, mode="append",
                           kind=RUN_CREATED, grants_send=True)
        with self.assertRaises(FailClosedError):
            AppendDecision(allowed=False, reason="rewrite",
                           mode="rewrite", kind=RUN_CREATED,
                           grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            AppendDecision(allowed=True, reason="rewrite",
                           mode="append", kind=RUN_CREATED)

    def test_allowed_cannot_be_rewrite(self):
        with self.assertRaises(FailClosedError):
            AppendDecision(allowed=True, reason=None,
                           mode="rewrite", kind=RUN_CREATED)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            AppendDecision(allowed=False, reason=None,
                           mode="append", kind=RUN_CREATED)
        with self.assertRaises(FailClosedError):
            AppendDecision(allowed=False, reason="send_authorized",
                           mode="append", kind=RUN_CREATED)
        self.assertIn("rewrite", REFUSAL_REASONS)
        self.assertIn("truncate", REFUSAL_REASONS)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_allowed_decision_refuses_sealed_names(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    AppendDecision(allowed=True, reason=None,
                                   mode=name, kind=RUN_CREATED)
                with self.assertRaises(FailClosedError):
                    AppendDecision(allowed=True, reason=None,
                                   mode="append", kind=name)

    def test_rewrite_refusal_cannot_carry_a_sealed_name(self):
        with self.assertRaises(FailClosedError):
            AppendDecision(allowed=False, reason="rewrite",
                           mode="rewrite", kind="send_authorized")

    def test_sealed_effect_refusal_names_the_subject(self):
        d = AppendDecision(allowed=False, reason="sealed_effect",
                           mode="append", kind="send_authorized")
        self.assertEqual(d.kind, "send_authorized")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)


class Vocabulary(unittest.TestCase):
    def test_closed_mode_vocabulary(self):
        self.assertEqual(MODES, frozenset({"append"}))

    def test_closed_refused_modes(self):
        self.assertEqual(REFUSED_MODES, frozenset({"rewrite", "truncate"}))


class ClassifyMode(unittest.TestCase):
    def test_append_classifies(self):
        self.assertEqual(classify_mode("append"), "append")
        self.assertEqual(classify_mode("APPEND"), "append")

    def test_rewrite_and_truncate_are_known(self):
        self.assertEqual(classify_mode("rewrite"), "rewrite")
        self.assertEqual(classify_mode("truncate"), "truncate")

    def test_unknown_mode_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_mode("upsert")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())
        self.assertFalse(unknown_mode_is_rewrite())

    def test_missing_mode_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_mode("")
        with self.assertRaises(FailClosedError):
            classify_mode(None)
        with self.assertRaises(FailClosedError):
            classify_mode(True)


class AppendAdmitsSpine(unittest.TestCase):
    def test_every_event_kind_is_admitted_on_append(self):
        for kind in sorted(EVENT_KINDS):
            with self.subTest(kind=kind):
                d = admit_append(mode="append", kind=kind)
                self.assertTrue(d.allowed)
                self.assertIsNone(d.reason)
                self.assertFalse(d.grants_send)
                self.assertEqual(d.mode, "append")
                self.assertEqual(d.kind, kind)

    def test_run_rejected_is_still_an_append(self):
        d = admit_append(mode="append", kind=RUN_REJECTED)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_replay_is_byte_identical(self):
        a = admit_append(mode="append", kind=TOOL_INVOKED)
        b = admit_append(mode="append", kind=TOOL_INVOKED)
        self.assertEqual(a, b)
        self.assertTrue(a.allowed)


class RewriteAndTruncateRefuse(unittest.TestCase):
    def test_rewrite_refused_for_spine_kinds(self):
        for kind in (RUN_CREATED, TOOL_INVOKED, EXECUTION_RECEIPT,
                     BUDGET_DEBIT, RUN_CLOSED):
            with self.subTest(kind=kind):
                d = admit_append(mode="rewrite", kind=kind)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "rewrite")
                self.assertFalse(d.grants_send)

    def test_truncate_refused(self):
        d = admit_append(mode="truncate", kind=RUN_CREATED)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "truncate")
        self.assertFalse(d.grants_send)

    def test_rewrite_is_not_a_send(self):
        d = admit_append(mode="REWRITE", kind=RUN_CREATED)
        self.assertEqual(d.reason, "rewrite")
        self.assertFalse(grants_send())


class SealedNameRefusesAppend(unittest.TestCase):
    def test_sealed_kind_aliases(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "SEND_AUTHORIZED",
                     "quote-sent", "campaign-envelope-ready"):
            with self.subTest(name=name):
                d = admit_append(mode="append", kind=name)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)

    def test_sealed_mode_aliases(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                d = admit_append(mode=name, kind=RUN_CREATED)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")

    def test_ready_and_authorized_stay_distinct(self):
        ready = admit_append(mode="append", kind="campaign_envelope_ready")
        auth = admit_append(mode="append", kind="send_authorized")
        sent = admit_append(mode="append", kind="quote_sent")
        for d in (ready, auth, sent):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
        self.assertNotEqual(ready.kind, auth.kind)
        self.assertFalse(ready_is_authorized())


class UnknownKindAndModeFailClosed(unittest.TestCase):
    def test_unknown_kind_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_append(mode="append", kind="DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_mode_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_append(mode="upsert", kind=RUN_CREATED)
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertFalse(unknown_mode_is_rewrite())

    def test_bool_mode_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_append(mode=True, kind=RUN_CREATED)

    def test_empty_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_append(mode="append", kind="  ")


if __name__ == "__main__":
    unittest.main()
