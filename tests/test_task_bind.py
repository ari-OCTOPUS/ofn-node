"""Contract tests for task_bind (P1 complementary).

A bind records a supplied intent + run_id shape. The kernel does
not mint. Missing is UNKNOWN (None), not FALSE. Sealed send/ready
names fail closed. Timeout does not prove concurrent writing.
Ready ≠ authorized. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import os
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.task_bind import (
    INTENTS,
    MINT,
    REPLAY,
    TaskBind,
    UNKNOWN,
    VALIDATE,
    bind_task,
    claims_immutable,
    classify_intent,
    classify_timeout,
    grants_send,
    halt_blocks_bind,
    mints_run_id,
    pair_matches,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    unknown_is_false,
    wires_into_run_store,
)


_RUN = "run-1780000000-abcdefghij"


class ClassifyIntent(unittest.TestCase):
    def test_known_intents(self):
        self.assertEqual(classify_intent("mint"), MINT)
        self.assertEqual(classify_intent("validate"), VALIDATE)
        self.assertEqual(classify_intent("replay"), REPLAY)
        self.assertEqual(INTENTS, frozenset({MINT, VALIDATE, REPLAY}))

    def test_case_and_hyphen_fold(self):
        self.assertEqual(classify_intent("MINT"), MINT)
        self.assertEqual(classify_intent("Validate"), VALIDATE)

    def test_missing_is_unknown_not_false(self):
        self.assertEqual(classify_intent(None), UNKNOWN)
        self.assertNotEqual(classify_intent(None), "FALSE")
        self.assertFalse(unknown_is_false())

    def test_bool_int_float_fail_closed(self):
        for bad in (True, False, 1, 0, 1.0, b"mint"):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    classify_intent(bad)

    def test_empty_and_unknown_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_intent("")
        with self.assertRaises(FailClosedError):
            classify_intent("   ")
        with self.assertRaises(FailClosedError):
            classify_intent("send")
        with self.assertRaises(FailClosedError):
            classify_intent("create")

    def test_sealed_names_refused(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "send-authorized",
            "Send_Authorized",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_intent(name)

    def test_ready_is_not_authorized(self):
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertFalse(ready_is_authorized())


class BindTask(unittest.TestCase):
    def test_bind_records_pair(self):
        bound = bind_task("mint", _RUN)
        self.assertIsInstance(bound, TaskBind)
        self.assertEqual(bound.intent, MINT)
        self.assertEqual(bound.run_id, _RUN)
        self.assertEqual(bound.intent_class, MINT)

    def test_frozen_cannot_retcon(self):
        bound = bind_task("validate", _RUN)
        with self.assertRaises(Exception):
            bound.intent = "mint"  # type: ignore[misc]

    def test_malformed_run_id_fail_closed(self):
        with self.assertRaises(FailClosedError):
            bind_task("mint", "run-1-myrun")
        with self.assertRaises(FailClosedError):
            bind_task("mint", "not-a-run")
        with self.assertRaises(FailClosedError):
            bind_task("mint", "")

    def test_bool_run_id_fail_closed(self):
        with self.assertRaises(FailClosedError):
            bind_task("mint", True)
        with self.assertRaises(FailClosedError):
            bind_task("mint", 1780000000)

    def test_missing_intent_on_explicit_bind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_task(None, _RUN)

    def test_sealed_run_id_refused(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    bind_task("mint", name)


class TryBindUnknown(unittest.TestCase):
    def test_missing_intent_is_none(self):
        self.assertIsNone(try_bind(None, _RUN))
        self.assertIsNone(try_bind("mint", None))
        self.assertIsNone(try_bind(None, None))

    def test_present_malformed_still_fails_closed(self):
        with self.assertRaises(FailClosedError):
            try_bind(True, _RUN)
        with self.assertRaises(FailClosedError):
            try_bind("mint", "run-1-x")
        with self.assertRaises(FailClosedError):
            try_bind("send_authorized", _RUN)

    def test_try_bind_success(self):
        bound = try_bind("replay", _RUN)
        self.assertIsNotNone(bound)
        assert bound is not None
        self.assertEqual(bound.intent, REPLAY)


class PairMatches(unittest.TestCase):
    def test_same_intent_is_true(self):
        self.assertIs(pair_matches("mint", _RUN, "mint"), True)

    def test_different_intent_is_false_not_unknown(self):
        self.assertIs(pair_matches("mint", _RUN, "validate"), False)

    def test_missing_is_unknown_none(self):
        self.assertIsNone(pair_matches(None, _RUN, "mint"))
        self.assertIsNone(pair_matches("mint", None, "mint"))
        self.assertIsNone(pair_matches("mint", _RUN, None))
        self.assertIsNot(pair_matches(None, _RUN, "mint"), False)


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_bind(self):
        self.assertFalse(halt_blocks_bind())
        params = inspect.signature(bind_task).parameters
        self.assertNotIn("halted", params)

    def test_does_not_mint(self):
        self.assertFalse(mints_run_id())

    def test_timeout_is_unknown_not_writer(self):
        self.assertEqual(classify_timeout(), UNKNOWN)
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready(self):
        self.assertFalse(promotes_ready_to_send())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())
        store = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ofn", "adapters", "run_store.py",
        )
        if not os.path.isfile(store):
            store = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "ofn", "kernel", "run_store.py",
            )
        # run_store lives under adapters in this tree; either path may
        # be absent on a complementary checkout. Absence is UNKNOWN,
        # not proof the store imports this bind.
        if os.path.isfile(store):
            text = open(store, encoding="utf-8").read()
            self.assertNotIn("task_bind", text)
            self.assertNotIn("intent_pin", text)

    def test_claims_immutable_is_false(self):
        self.assertFalse(claims_immutable())


if __name__ == "__main__":
    unittest.main()
