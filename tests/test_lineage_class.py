"""Kernel-pure lineage class — complementary to envelope_class / hash_chain.

Root mint is a START. Succeed/observe continue under HALT.
Missing prior is UNKNOWN, not empty. Orphan is a known refusal.
Ready is not authorized. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.lineage_class import (
    ACTIVITIES,
    INTENTS,
    REFUSAL_REASONS,
    ROLES,
    STATUSES,
    LineageDecision,
    admit_lineage,
    claims_immutable,
    classify_status,
    classify_timeout,
    grants_send,
    halt_blocks_succeed,
    missing_prior_is_empty,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    unknown_is_false,
    wires_into_run_store,
)

_ROOT = "run-1780000000-rootaaaaaa"
_CHILD = "run-1780000000-childbbbbb"
_OTHER = "run-1780000000-otherccccc"


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_succeed(self):
        self.assertFalse(halt_blocks_succeed())

    def test_does_not_mint_run_id(self):
        self.assertFalse(mints_run_id())

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

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_missing_prior_is_not_empty(self):
        self.assertFalse(missing_prior_is_empty())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_signature_has_no_send_or_resend_knob(self):
        params = inspect.signature(admit_lineage).parameters
        self.assertEqual(
            list(params),
            [
                "intended",
                "node_id",
                "parent_id",
                "prior",
                "activity",
                "halted",
                "timed_out",
            ],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt_raw",
            "immutable",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            LineageDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="observe", role="unknown", node_id=_ROOT,
                parent_id=None, timed_out=False, grants_send=True)
        with self.assertRaises(FailClosedError):
            LineageDecision(
                allowed=False, reason="sealed_effect", status="UNKNOWN",
                intended="observe", role="unknown",
                node_id="send_authorized", parent_id=None,
                timed_out=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            LineageDecision(
                allowed=True, reason="halt_start", status="VERIFIED",
                intended="mint", role="root", node_id=_ROOT,
                parent_id=None, timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            LineageDecision(
                allowed=False, reason=None, status="UNKNOWN",
                intended="mint", role="root", node_id=_ROOT,
                parent_id=None, timed_out=False)
        with self.assertRaises(FailClosedError):
            LineageDecision(
                allowed=False, reason="send_authorized", status="UNKNOWN",
                intended="mint", role="root", node_id=_ROOT,
                parent_id=None, timed_out=False)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("halt_start", REFUSAL_REASONS)
        self.assertIn("orphan_parent", REFUSAL_REASONS)
        self.assertIn("missing_parent", REFUSAL_REASONS)
        self.assertIn("unknown_prior", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_allowed_mint_requires_verified(self):
        for status in ("SUSPECTED", "UNKNOWN"):
            with self.subTest(status=status):
                with self.assertRaises(FailClosedError):
                    LineageDecision(
                        allowed=True, reason=None, status=status,
                        intended="mint", role="root", node_id=_ROOT,
                        parent_id=None, timed_out=False)

    def test_allowed_succeed_requires_successor_role(self):
        with self.assertRaises(FailClosedError):
            LineageDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="succeed", role="orphan", node_id=_CHILD,
                parent_id=_ROOT, timed_out=False)

    def test_cannot_allow_orphan(self):
        with self.assertRaises(FailClosedError):
            LineageDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="observe", role="orphan", node_id=_CHILD,
                parent_id=_OTHER, timed_out=False)

    def test_allowed_decision_refuses_sealed_node(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    LineageDecision(
                        allowed=True, reason=None, status="VERIFIED",
                        intended="observe", role="unknown",
                        node_id=name, parent_id=None, timed_out=False)

    def test_non_sealed_refusal_cannot_carry_a_sealed_node(self):
        with self.assertRaises(FailClosedError):
            LineageDecision(
                allowed=False, reason="unknown_activity", status="UNKNOWN",
                intended="mint", role="root",
                node_id="send_authorized", parent_id=None, timed_out=True)

    def test_sealed_effect_refusal_names_the_subject(self):
        d = LineageDecision(
            allowed=False, reason="sealed_effect", status="UNKNOWN",
            intended="observe", role="unknown",
            node_id="send_authorized", parent_id=None, timed_out=False)
        self.assertEqual(d.node_id, "send_authorized")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            LineageDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="observe", role="unknown", node_id=_ROOT,
                parent_id=None, timed_out="false")  # type: ignore[arg-type]


class ClosedVocabularies(unittest.TestCase):
    def test_statuses(self):
        self.assertEqual(STATUSES, frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"}))

    def test_activities(self):
        self.assertEqual(ACTIVITIES, frozenset({"idle", "concurrent", "unknown"}))

    def test_intents(self):
        self.assertEqual(INTENTS, frozenset({"mint", "succeed", "observe"}))

    def test_roles(self):
        self.assertEqual(ROLES, frozenset({"root", "successor", "orphan", "unknown"}))


class StatusDerivation(unittest.TestCase):
    def test_idle_is_verified(self):
        self.assertEqual(
            classify_status(activity="idle", timed_out=False), "VERIFIED")

    def test_concurrent_is_suspected(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=False),
            "SUSPECTED")

    def test_unknown_activity_is_unknown(self):
        self.assertEqual(
            classify_status(activity="unknown", timed_out=False), "UNKNOWN")

    def test_timeout_outranks_concurrent(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=True), "UNKNOWN")

    def test_timeout_outranks_idle(self):
        self.assertEqual(
            classify_status(activity="idle", timed_out=True), "UNKNOWN")

    def test_unknown_activity_token_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_status(activity="racing", timed_out=False)
        self.assertNotIn("FALSE", str(ctx.exception))


class MintIsAStart(unittest.TestCase):
    def test_mint_idle_verified_is_admitted_as_root(self):
        d = admit_lineage(intended="mint", node_id=_ROOT)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "VERIFIED")
        self.assertEqual(d.role, "root")
        self.assertIsNone(d.parent_id)
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)

    def test_mint_halted_is_refused(self):
        d = admit_lineage(intended="mint", node_id=_ROOT, halted=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "halt_start")
        self.assertEqual(d.role, "root")
        self.assertFalse(d.grants_send)

    def test_mint_unknown_is_refused(self):
        d = admit_lineage(
            intended="mint", node_id=_ROOT, activity="unknown")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_activity")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(d.grants_send)

    def test_mint_concurrent_is_refused(self):
        d = admit_lineage(
            intended="mint", node_id=_ROOT, activity="concurrent")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "suspected_concurrent")
        self.assertEqual(d.status, "SUSPECTED")
        self.assertFalse(d.grants_send)

    def test_mint_timeout_is_unknown_not_suspected(self):
        d = admit_lineage(
            intended="mint", node_id=_ROOT,
            activity="concurrent", timed_out=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_activity")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)

    def test_mint_with_parent_is_a_shape_error(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_lineage(intended="mint", node_id=_CHILD, parent_id=_ROOT)
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("root", str(ctx.exception).lower())


class SucceedNeedsAPriorParent(unittest.TestCase):
    def test_succeed_with_prior_parent_is_admitted(self):
        d = admit_lineage(
            intended="succeed", node_id=_CHILD, parent_id=_ROOT,
            prior=frozenset({_ROOT}))
        self.assertTrue(d.allowed)
        self.assertEqual(d.role, "successor")
        self.assertEqual(d.parent_id, _ROOT)
        self.assertFalse(d.grants_send)

    def test_succeed_continues_under_halt(self):
        d = admit_lineage(
            intended="succeed", node_id=_CHILD, parent_id=_ROOT,
            prior=frozenset({_ROOT}), halted=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.role, "successor")
        self.assertFalse(halt_blocks_succeed())
        self.assertFalse(d.grants_send)

    def test_missing_parent_is_unknown_not_false(self):
        d = admit_lineage(intended="succeed", node_id=_CHILD)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "missing_parent")
        self.assertEqual(d.role, "unknown")
        self.assertFalse(d.grants_send)
        self.assertFalse(unknown_is_false())

    def test_missing_prior_is_unknown_not_empty(self):
        d = admit_lineage(
            intended="succeed", node_id=_CHILD, parent_id=_ROOT)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_prior")
        self.assertEqual(d.role, "unknown")
        self.assertFalse(missing_prior_is_empty())
        self.assertFalse(d.grants_send)

    def test_empty_prior_is_orphan_not_unknown(self):
        d = admit_lineage(
            intended="succeed", node_id=_CHILD, parent_id=_ROOT,
            prior=frozenset())
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "orphan_parent")
        self.assertEqual(d.role, "orphan")
        self.assertFalse(d.grants_send)

    def test_parent_absent_from_prior_is_orphan(self):
        d = admit_lineage(
            intended="succeed", node_id=_CHILD, parent_id=_OTHER,
            prior=frozenset({_ROOT}))
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "orphan_parent")
        self.assertEqual(d.role, "orphan")
        self.assertFalse(d.grants_send)

    def test_self_parent_is_refused(self):
        d = admit_lineage(
            intended="succeed", node_id=_CHILD, parent_id=_CHILD,
            prior=frozenset({_CHILD}))
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "self_parent")
        self.assertEqual(d.role, "unknown")
        self.assertFalse(d.grants_send)

    def test_succeed_timeout_is_unknown_not_suspected(self):
        d = admit_lineage(
            intended="succeed", node_id=_CHILD, parent_id=_ROOT,
            prior=frozenset({_ROOT}), activity="concurrent",
            timed_out=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_activity")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)

    def test_succeed_concurrent_is_refused(self):
        d = admit_lineage(
            intended="succeed", node_id=_CHILD, parent_id=_ROOT,
            prior=frozenset({_ROOT}), activity="concurrent")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "suspected_concurrent")
        self.assertEqual(d.status, "SUSPECTED")
        self.assertFalse(d.grants_send)


class ObserveIsNotAStart(unittest.TestCase):
    def test_observe_continues_under_halt(self):
        d = admit_lineage(intended="observe", node_id=_ROOT, halted=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.role, "unknown")
        self.assertFalse(d.grants_send)

    def test_observe_timeout_is_unknown_and_still_admitted(self):
        d = admit_lineage(intended="observe", node_id=_ROOT, timed_out=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(d.grants_send)

    def test_observe_is_byte_identical(self):
        a = admit_lineage(intended="observe", node_id=_ROOT)
        b = admit_lineage(intended="observe", node_id=_ROOT)
        self.assertEqual(a, b)
        self.assertTrue(a.allowed)
        self.assertFalse(a.grants_send)

    def test_observe_does_not_claim_successor_without_prior(self):
        d = admit_lineage(
            intended="observe", node_id=_CHILD, parent_id=_ROOT)
        self.assertTrue(d.allowed)
        self.assertEqual(d.role, "unknown")
        self.assertFalse(d.grants_send)


class ShapeAndUnknown(unittest.TestCase):
    def test_malformed_node_id_is_refused(self):
        d = admit_lineage(intended="mint", node_id="not-a-run")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "malformed_id")
        self.assertFalse(d.grants_send)

    def test_malformed_parent_id_is_refused(self):
        d = admit_lineage(
            intended="succeed", node_id=_CHILD, parent_id="not-a-run",
            prior=frozenset({_ROOT}))
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "malformed_id")
        self.assertFalse(d.grants_send)

    def test_unknown_activity_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_lineage(
                intended="mint", node_id=_ROOT, activity="racing")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_intended_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_lineage(intended="send", node_id=_ROOT)
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_empty_node_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_lineage(intended="mint", node_id="  ")

    def test_bool_node_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_lineage(intended="mint", node_id=True)

    def test_string_prior_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_lineage(
                intended="succeed", node_id=_CHILD, parent_id=_ROOT,
                prior=_ROOT)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_lineage(intended="mint", node_id=_ROOT, timed_out=1)
        with self.assertRaises(FailClosedError):
            admit_lineage(intended="mint", node_id=_ROOT, timed_out="true")

    def test_halted_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_lineage(intended="mint", node_id=_ROOT, halted=1)


class SealedNameRefusesLineage(unittest.TestCase):
    def test_sealed_node_id_aliases(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "SEND_AUTHORIZED",
            "quote-sent",
            "campaign-envelope-ready",
        ):
            with self.subTest(name=name):
                d = admit_lineage(intended="observe", node_id=name)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)

    def test_sealed_parent_id_is_refused(self):
        d = admit_lineage(
            intended="succeed", node_id=_CHILD,
            parent_id="send_authorized", prior=frozenset({_ROOT}))
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")
        self.assertFalse(d.grants_send)

    def test_ready_and_authorized_stay_distinct_subjects(self):
        ready = admit_lineage(
            intended="observe", node_id="campaign_envelope_ready")
        auth = admit_lineage(intended="observe", node_id="send_authorized")
        self.assertNotEqual(ready.node_id, auth.node_id)
        self.assertFalse(ready.allowed)
        self.assertFalse(auth.allowed)
        self.assertFalse(ready_is_authorized())


if __name__ == "__main__":
    unittest.main()
