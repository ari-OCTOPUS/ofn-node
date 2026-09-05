"""Kernel-pure revoke class — complementary to send_fence / campaign_bind.

issue is a START. revoke / classify / observe continue under HALT.
Ready is not authorized. Withdrawn is not a send. Timeout is
UNKNOWN. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.revoke_class import (
    CLASSIFY,
    FAMILIES,
    HELD,
    INTENTS,
    ISSUE,
    OBSERVE,
    READY,
    REVOKE,
    RUN,
    SUBJECT_KINDS,
    UNKNOWN,
    WITHDRAWN,
    RevokeBind,
    admit_revoke,
    bind_revoke,
    claims_immutable,
    classify_family,
    classify_intent,
    classify_subject,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_issue,
    halt_blocks_observe,
    halt_blocks_revoke,
    later_disarm_supersedes,
    later_withdraw_supersedes,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
    withdrawn_is_authorized,
)

_RUN = "run-1780000000-armaaaaaaa"


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify_observe_revoke(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertFalse(halt_blocks_revoke())

    def test_halt_blocks_issue(self):
        self.assertTrue(halt_blocks_issue())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_withdrawn_is_not_authorized(self):
        self.assertFalse(withdrawn_is_authorized())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertEqual(classify_timeout(), UNKNOWN)

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_does_not_mint_run_id(self):
        self.assertFalse(mints_run_id())

    def test_later_withdraw_and_disarm_supersede(self):
        self.assertTrue(later_withdraw_supersedes())
        self.assertTrue(later_disarm_supersedes())

    def test_closed_vocabularies(self):
        self.assertEqual(INTENTS, frozenset({
            ISSUE, REVOKE, CLASSIFY, OBSERVE}))
        self.assertEqual(FAMILIES, frozenset({HELD, WITHDRAWN}))
        self.assertEqual(SUBJECT_KINDS, frozenset({READY, RUN}))

    def test_admit_signature_has_no_send_or_resend_knob(self):
        params = inspect.signature(admit_revoke).parameters
        self.assertEqual(
            list(params),
            ["intent", "subject", "withdrawn", "halted", "timeout"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt_raw",
            "now",
        ):
            self.assertNotIn(forbidden, params)

    def test_bind_signature_has_no_send_knob(self):
        params = inspect.signature(bind_revoke).parameters
        self.assertEqual(
            list(params),
            ["intent", "subject", "withdrawn", "slot"],
        )


class ClassifyIntent(unittest.TestCase):
    def test_none_is_unknown_not_false(self):
        self.assertEqual(classify_intent(None), UNKNOWN)
        self.assertNotEqual(classify_intent(None), "FALSE")

    def test_known_intents(self):
        for name in (ISSUE, REVOKE, CLASSIFY, OBSERVE):
            with self.subTest(name=name):
                self.assertEqual(classify_intent(name), name)

    def test_hyphen_and_case_fold(self):
        self.assertEqual(classify_intent("Revoke"), REVOKE)
        self.assertEqual(classify_intent("CLASSIFY"), CLASSIFY)

    def test_empty_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_intent("  ")

    def test_unknown_name_fails_closed_not_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_intent("GUESS")
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_bool_int_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_intent(True)
        with self.assertRaises(FailClosedError):
            classify_intent(1)

    def test_send_names_fail_closed(self):
        for name in ("send_authorized", "quote_sent", "send-authorized"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_intent(name)

    def test_ready_as_intent_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_intent("campaign_envelope_ready")
        with self.assertRaises(FailClosedError):
            classify_intent("ready")


class ClassifySubject(unittest.TestCase):
    def test_none_is_unknown_not_false(self):
        self.assertIsNone(classify_subject(None))
        self.assertIsNot(classify_subject(None), False)

    def test_ready_aliases(self):
        self.assertEqual(classify_subject("campaign_envelope_ready"), READY)
        self.assertEqual(classify_subject("campaign-envelope-ready"), READY)
        self.assertEqual(classify_subject("ready"), READY)

    def test_run_id(self):
        self.assertEqual(classify_subject(_RUN), RUN)

    def test_send_names_fail_closed(self):
        for name in ("send_authorized", "quote_sent", "Send_Authorized"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_subject(name)

    def test_malformed_run_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_subject("run-nope")
        with self.assertRaises(FailClosedError):
            classify_subject("not-a-subject")

    def test_empty_and_bool_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_subject("")
        with self.assertRaises(FailClosedError):
            classify_subject(True)


class ClassifyFamily(unittest.TestCase):
    def test_missing_is_unknown_not_false(self):
        self.assertIsNone(classify_family(None))
        self.assertIsNot(classify_family(None), False)

    def test_held_and_withdrawn(self):
        self.assertEqual(classify_family(False), HELD)
        self.assertEqual(classify_family(True), WITHDRAWN)

    def test_timeout_is_unknown_not_false(self):
        self.assertIsNone(classify_family(False, timeout=True))
        self.assertIsNone(classify_family(True, timeout=True))
        self.assertNotEqual(classify_family(False, timeout=True), "FALSE")

    def test_timeout_outranks_withdrawn(self):
        self.assertIsNone(classify_family(True, timeout=True))

    def test_bad_types_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_family(1)
        with self.assertRaises(FailClosedError):
            classify_family("true")
        with self.assertRaises(FailClosedError):
            classify_family(False, timeout="yes")


class BindRevoke(unittest.TestCase):
    def test_bind_ready_held(self):
        bind = bind_revoke(
            REVOKE, "campaign_envelope_ready",
            withdrawn=False, slot="slot-a")
        self.assertEqual(bind.intent, REVOKE)
        self.assertEqual(bind.family, HELD)
        self.assertEqual(bind.subject_kind, READY)
        self.assertEqual(bind.subject, READY)
        self.assertEqual(bind.slot, "slot-a")

    def test_bind_run_withdrawn(self):
        bind = bind_revoke(
            CLASSIFY, _RUN, withdrawn=True, slot="slot-b")
        self.assertEqual(bind.subject_kind, RUN)
        self.assertEqual(bind.subject, _RUN)
        self.assertEqual(bind.family, WITHDRAWN)

    def test_missing_sides_fail_closed(self):
        with self.assertRaises(FailClosedError):
            bind_revoke(None, _RUN, withdrawn=False, slot="s")
        with self.assertRaises(FailClosedError):
            bind_revoke(REVOKE, None, withdrawn=False, slot="s")
        with self.assertRaises(FailClosedError):
            bind_revoke(REVOKE, _RUN, withdrawn=None, slot="s")

    def test_send_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_revoke(
                REVOKE, _RUN, withdrawn=False, slot="send_authorized")

    def test_constructor_is_frozen(self):
        bind = bind_revoke(
            OBSERVE, READY, withdrawn=False, slot="s")
        with self.assertRaises(Exception):
            bind.family = WITHDRAWN  # type: ignore[misc]


class TryBind(unittest.TestCase):
    def test_missing_is_unknown_not_false(self):
        self.assertIsNone(
            try_bind(None, _RUN, withdrawn=False, slot="s"))
        self.assertIsNone(
            try_bind(REVOKE, None, withdrawn=False, slot="s"))
        self.assertIsNone(
            try_bind(REVOKE, _RUN, withdrawn=None, slot="s"))
        self.assertIsNone(
            try_bind(REVOKE, _RUN, withdrawn=False, slot=None))
        self.assertIsNot(
            try_bind(None, None, withdrawn=None, slot=None), False)

    def test_present_round_trip(self):
        bind = try_bind(ISSUE, _RUN, withdrawn=False, slot="s")
        self.assertIsInstance(bind, RevokeBind)
        self.assertEqual(bind.intent, ISSUE)


class AdmitRevoke(unittest.TestCase):
    def test_classify_and_observe_continue_under_halt(self):
        self.assertIs(
            admit_revoke(CLASSIFY, _RUN, withdrawn=False, halted=True),
            True)
        self.assertIs(
            admit_revoke(OBSERVE, READY, withdrawn=True, halted=True),
            True)

    def test_revoke_continues_under_halt_when_held(self):
        self.assertIs(
            admit_revoke(REVOKE, READY, withdrawn=False, halted=True),
            True)

    def test_issue_refused_when_halted(self):
        self.assertIs(
            admit_revoke(ISSUE, _RUN, withdrawn=False, halted=True),
            False)
        self.assertIs(
            admit_revoke(ISSUE, _RUN, withdrawn=False, halted=False),
            True)

    def test_revoke_of_already_withdrawn_is_false_not_unknown(self):
        self.assertIs(
            admit_revoke(REVOKE, READY, withdrawn=True),
            False)
        self.assertIsNot(
            admit_revoke(REVOKE, READY, withdrawn=True),
            None)

    def test_timeout_is_unknown_not_false(self):
        self.assertIsNone(
            admit_revoke(REVOKE, READY, withdrawn=False, timeout=True))
        self.assertIsNot(
            admit_revoke(ISSUE, _RUN, timeout=True),
            False)

    def test_missing_intent_or_subject_is_unknown(self):
        self.assertIsNone(admit_revoke(None, READY, withdrawn=False))
        self.assertIsNone(admit_revoke(REVOKE, None, withdrawn=False))

    def test_send_subject_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_revoke(REVOKE, "send_authorized", withdrawn=False)
        with self.assertRaises(FailClosedError):
            admit_revoke(CLASSIFY, "quote_sent", withdrawn=False)

    def test_halted_timeout_must_be_exact_bools(self):
        with self.assertRaises(FailClosedError):
            admit_revoke(REVOKE, READY, halted=1)
        with self.assertRaises(FailClosedError):
            admit_revoke(REVOKE, READY, timeout="yes")

    def test_admit_never_grants_send(self):
        self.assertFalse(grants_send())
        self.assertIs(
            admit_revoke(REVOKE, "campaign_envelope_ready", withdrawn=False),
            True)
        self.assertFalse(ready_is_authorized())


if __name__ == "__main__":
    unittest.main()
