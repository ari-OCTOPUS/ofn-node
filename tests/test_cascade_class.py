"""Contract tests for cascade_class (P1 complementary).

A cascade family is not a send. Missing is UNKNOWN, not
FALSE. Timeout does not prove a writer. Ready is not authorized.
Children do not promote isolated into cascade. Zero children
cannot cascade. This is a propagation witness, not is_halted
and not which operation may proceed.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.cascade_class import (
    CASCADE,
    CLASSIFY,
    FAMILIES,
    INSPECT,
    INTENTS,
    ISOLATED,
    OBSERVE,
    RECORD,
    SCOPES,
    UNKNOWN,
    CascadeBind,
    admit_cascade,
    bind_cascade,
    cascade_is_authorized,
    children_do_not_promote,
    claims_immutable,
    classify_intent,
    classify_propagation,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_observe,
    halt_blocks_record,
    isolated_is_false,
    later_disarm_supersedes,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
    zero_children_cannot_cascade,
)
from ofn.kernel.errors import FailClosedError

_STOP = "env-cst-0001"


class ClassifyIntent(unittest.TestCase):
    def test_closed_intents(self):
        self.assertEqual(classify_intent("record"), RECORD)
        self.assertEqual(classify_intent("classify"), CLASSIFY)
        self.assertEqual(classify_intent("observe"), OBSERVE)
        self.assertEqual(classify_intent("inspect"), INSPECT)
        self.assertEqual(
            INTENTS, frozenset({RECORD, CLASSIFY, OBSERVE, INSPECT}))

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

    def test_unknown_intent_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_intent("consume")
        with self.assertRaises(FailClosedError):
            classify_intent("send")
        with self.assertRaises(FailClosedError):
            classify_intent("reserve")

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


class ClassifyPropagation(unittest.TestCase):
    def test_closed_families(self):
        self.assertEqual(classify_propagation("isolated", 0), ISOLATED)
        self.assertEqual(classify_propagation("isolated", 3), ISOLATED)
        self.assertEqual(classify_propagation("cascade", 1), CASCADE)
        self.assertEqual(classify_propagation("cascade", 4), CASCADE)
        self.assertEqual(classify_propagation("cascade", 0), ISOLATED)
        self.assertEqual(FAMILIES, frozenset({ISOLATED, CASCADE}))
        self.assertEqual(SCOPES, frozenset({ISOLATED, CASCADE}))

    def test_children_do_not_promote_isolated(self):
        self.assertEqual(classify_propagation("isolated", 5), ISOLATED)
        self.assertNotEqual(classify_propagation("isolated", 5), CASCADE)
        self.assertTrue(children_do_not_promote())

    def test_zero_children_cannot_cascade(self):
        self.assertEqual(classify_propagation("cascade", 0), ISOLATED)
        self.assertTrue(zero_children_cannot_cascade())

    def test_missing_is_none_not_false(self):
        self.assertIsNone(classify_propagation(None, 3))
        self.assertIsNone(classify_propagation("cascade", None))
        self.assertIsNone(classify_propagation(None, None))
        self.assertIsNot(classify_propagation(None, 3), False)
        self.assertIsNot(classify_propagation(None, 3), CASCADE)
        self.assertIsNot(classify_propagation(None, 3), ISOLATED)

    def test_timeout_is_none_not_false(self):
        self.assertIsNone(classify_propagation("cascade", 2, timeout=True))
        self.assertIsNone(classify_propagation("isolated", 0, timeout=True))
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_timeout_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_propagation("cascade", 2, timeout="yes")
        with self.assertRaises(FailClosedError):
            classify_propagation("cascade", 2, timeout=1)

    def test_bool_child_count_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_propagation("cascade", True)
        with self.assertRaises(FailClosedError):
            classify_propagation("isolated", False)

    def test_negative_child_count_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_propagation("cascade", -1)

    def test_float_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_propagation("cascade", 1.0)  # type: ignore[arg-type]

    def test_unknown_scope_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_propagation("fanout", 1)
        with self.assertRaises(FailClosedError):
            classify_propagation("local", 1)

    def test_empty_scope_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_propagation("", 1)

    def test_sealed_scope_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_propagation("send_authorized", 1)
        with self.assertRaises(FailClosedError):
            classify_propagation("campaign_envelope_ready", 1)

    def test_case_fold(self):
        self.assertEqual(classify_propagation("ISOLATED", 2), ISOLATED)
        self.assertEqual(classify_propagation("CASCADE", 2), CASCADE)
        self.assertEqual(classify_propagation("Isolated", 2), ISOLATED)

    def test_cascade_is_not_authorized(self):
        self.assertEqual(classify_propagation("cascade", 2), CASCADE)
        self.assertFalse(cascade_is_authorized())

    def test_isolated_is_not_false(self):
        self.assertEqual(classify_propagation("isolated", 0), ISOLATED)
        self.assertFalse(isolated_is_false())

    def test_not_halt_predicate_or_op(self):
        self.assertNotEqual(classify_propagation("cascade", 2), "halted")
        self.assertNotEqual(classify_propagation("isolated", 2), "start_run")
        self.assertNotEqual(classify_propagation("cascade", 2), "quorum")


class AdmitAndBind(unittest.TestCase):
    def test_admit_classify_continues_under_halt(self):
        self.assertIs(admit_cascade("classify", "isolated", 3, halted=True), True)

    def test_admit_observe_continues_under_halt(self):
        self.assertIs(admit_cascade("observe", "cascade", 2, halted=True), True)

    def test_admit_inspect_continues_under_halt(self):
        self.assertIs(admit_cascade("inspect", "cascade", 0, halted=True), True)

    def test_admit_record_refused_when_halted(self):
        self.assertIs(admit_cascade("record", "cascade", 2, halted=True), False)
        self.assertIs(admit_cascade("record", "cascade", 2, halted=False), True)

    def test_admit_timeout_is_none(self):
        self.assertIsNone(admit_cascade("record", "cascade", 2, timeout=True))

    def test_admit_missing_is_none(self):
        self.assertIsNone(admit_cascade(None, "cascade", 2))
        self.assertIsNone(admit_cascade("classify", None, 2))
        self.assertIsNone(admit_cascade("classify", "cascade", None))

    def test_admit_isolated_is_not_a_send_false(self):
        self.assertIs(admit_cascade("classify", "isolated", 3), True)

    def test_admit_halted_non_bool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_cascade("classify", "cascade", 2, halted="yes")

    def test_bind_records_cascade(self):
        bound = bind_cascade("classify", "cascade", 2, stop=_STOP)
        self.assertIsInstance(bound, CascadeBind)
        self.assertEqual(bound.family, CASCADE)
        self.assertEqual(bound.scope, CASCADE)
        self.assertEqual(bound.child_count, 2)
        self.assertEqual(bound.intent, CLASSIFY)
        self.assertEqual(bound.stop, _STOP)

    def test_bind_records_isolated_with_children(self):
        bound = bind_cascade("classify", "isolated", 4, stop=_STOP)
        self.assertEqual(bound.family, ISOLATED)
        self.assertEqual(bound.scope, ISOLATED)
        self.assertEqual(bound.child_count, 4)

    def test_bind_cascade_zero_children_is_isolated_family(self):
        bound = bind_cascade("classify", "cascade", 0, stop=_STOP)
        self.assertEqual(bound.family, ISOLATED)
        self.assertEqual(bound.scope, CASCADE)
        self.assertEqual(bound.child_count, 0)

    def test_try_bind_missing_is_none(self):
        self.assertIsNone(try_bind(None, "cascade", 2, stop=_STOP))
        self.assertIsNone(try_bind("classify", None, 2, stop=_STOP))
        self.assertIsNone(try_bind("classify", "cascade", None, stop=_STOP))
        self.assertIsNone(try_bind("classify", "cascade", 2, stop=None))

    def test_bind_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_cascade(None, "cascade", 2, stop=_STOP)
        with self.assertRaises(FailClosedError):
            bind_cascade("classify", None, 2, stop=_STOP)
        with self.assertRaises(FailClosedError):
            bind_cascade("classify", "cascade", None, stop=_STOP)

    def test_bind_sealed_stop_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_cascade("classify", "cascade", 2, stop="campaign_envelope_ready")

    def test_bind_empty_stop_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_cascade("classify", "cascade", 2, stop="")


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertFalse(rearms_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertFalse(halt_blocks_inspect())
        self.assertTrue(halt_blocks_record())

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

    def test_classify_propagation_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_propagation).parameters
        self.assertEqual(list(params), ["scope", "child_count", "timeout"])
        for forbidden in (
            "halted", "now", "resend",
            "send_authorized", "quote_sent", "campaign_envelope_ready",
            "votes", "required",
        ):
            self.assertNotIn(forbidden, params)

    def test_admit_has_no_send_knob(self):
        params = inspect.signature(admit_cascade).parameters
        self.assertEqual(
            list(params),
            ["intent", "scope", "child_count", "halted", "timeout"],
        )
        for forbidden in (
            "resend", "send_authorized", "quote_sent",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)


if __name__ == "__main__":
    unittest.main()
