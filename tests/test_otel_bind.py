"""Contract tests for otel_bind (P1 complementary).

Bind of a known spine kind is admitted only when VERIFIED.
Export and emit_send are refused. Unknown kinds fail closed.
Timeout is UNKNOWN, not a concurrent-write proof. Ready ≠
authorized. Distinct from otel_map.py (#77) and run_store.py.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import EVENT_KINDS
from ofn.kernel.otel_bind import (
    ACTIVITIES,
    INTENTS,
    REFUSAL_REASONS,
    SPAN_BY_KIND,
    STATUSES,
    OtelDecision,
    admit_otel,
    claims_immutable,
    classify_status,
    classify_timeout,
    exports_spans,
    grants_send,
    halt_blocks_otel,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    span_name,
    timeout_proves_concurrent,
    unknown_is_false,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_otel(self):
        self.assertFalse(halt_blocks_otel())

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
        self.assertNotEqual(classify_timeout(), "FALSE")

    def test_does_not_export(self):
        self.assertFalse(exports_spans())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(admit_otel).parameters
        self.assertEqual(
            list(params),
            ["kind", "intended", "activity", "timed_out"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "halt",
            "halted",
            "quote_sent",
        ):
            self.assertNotIn(forbidden, params)

    def test_vocabularies_are_closed(self):
        self.assertEqual(INTENTS, frozenset({"bind", "export", "emit_send"}))
        self.assertIn("idle", ACTIVITIES)
        self.assertEqual(STATUSES, frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"}))
        self.assertIn("export_forbidden", REFUSAL_REASONS)
        self.assertEqual(set(SPAN_BY_KIND), set(EVENT_KINDS))


class AdmitBind(unittest.TestCase):
    def test_bind_each_kind_when_verified(self):
        for kind in EVENT_KINDS:
            with self.subTest(kind=kind):
                d = admit_otel(kind=kind, intended="bind", activity="idle")
                self.assertTrue(d.allowed)
                self.assertEqual(d.span, span_name(kind))
                self.assertFalse(d.grants_send)

    def test_span_names_are_dotted(self):
        self.assertEqual(span_name("BUDGET_DEBIT"), "budget.debit")
        self.assertEqual(span_name("EXECUTION_RECEIPT"), "execution.receipt")
        self.assertNotIn("/", span_name("RUN_CREATED"))


class RefuseUnsafe(unittest.TestCase):
    def test_export_refused(self):
        d = admit_otel(
            kind="RUN_CREATED", intended="export", activity="idle")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "export_forbidden")
        self.assertIsNone(d.span)

    def test_emit_send_refused(self):
        d = admit_otel(
            kind="RUN_CREATED", intended="emit_send", activity="idle")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "emit_send_forbidden")

    def test_unknown_kind_is_refused_not_generic(self):
        d = admit_otel(kind="SPAN_GENERIC", intended="bind", activity="idle")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_kind")
        with self.assertRaises(FailClosedError):
            span_name("SPAN_GENERIC")


class TimeoutAndUnknown(unittest.TestCase):
    def test_timeout_outranks_concurrent(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=True),
            "UNKNOWN",
        )
        d = admit_otel(
            kind="RUN_CREATED",
            intended="bind",
            activity="concurrent",
            timed_out=True,
        )
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_activity")

    def test_unknown_activity_is_unknown_not_false(self):
        d = admit_otel(
            kind="RUN_CREATED", intended="bind", activity="unknown")
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertNotEqual(d.status, "FALSE")

    def test_suspected_concurrent_blocks_bind(self):
        d = admit_otel(
            kind="RUN_CREATED", intended="bind", activity="concurrent")
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "SUSPECTED")
        self.assertEqual(d.reason, "suspected_concurrent")

    def test_export_still_refused_when_unknown(self):
        d = admit_otel(
            kind="RUN_CREATED", intended="export", activity="unknown")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "export_forbidden")

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_otel(
                kind="RUN_CREATED",
                intended="bind",
                activity="idle",
                timed_out=1,
            )

    def test_bool_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_otel(kind=True, intended="bind", activity="idle")

    def test_empty_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_otel(kind="  ", intended="bind", activity="idle")


class SealedNames(unittest.TestCase):
    def test_sealed_kind_fails_closed(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "Send_Authorized",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    admit_otel(kind=name, intended="bind", activity="idle")

    def test_sealed_intent_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_otel(
                kind="RUN_CREATED",
                intended="send_authorized",
                activity="idle",
            )

    def test_decision_cannot_grant_send(self):
        with self.assertRaises(FailClosedError):
            OtelDecision(
                allowed=True,
                reason=None,
                status="VERIFIED",
                kind="RUN_CREATED",
                intended="bind",
                span="run.created",
                timed_out=False,
                grants_send=True,
            )


class DistinctFromMapAndStore(unittest.TestCase):
    def test_module_is_not_otel_map(self):
        import ofn.kernel.otel_bind as bind
        self.assertFalse(hasattr(bind, "is_exportable_state"))
        self.assertTrue(hasattr(bind, "admit_otel"))

    def test_run_store_does_not_import_otel_bind(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("otel_bind", source)
        self.assertNotIn("admit_otel", source)
