"""Contract tests for scope_class (P1 complementary).

A bind records a supplied action + run_id shape. Missing is
UNKNOWN (None), not FALSE. Sealed send/ready names fail closed.
Timeout does not prove concurrent writing. HALT refuses start
and lets inspect / classify continue. Ready ≠ authorized.
Not wired into the run store.
"""

from __future__ import annotations

import inspect
import os
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.scope_class import (
    ACTIONS,
    CLASSIFY,
    INSPECT,
    START,
    ScopeBind,
    UNKNOWN,
    admit_scope,
    bind_scope,
    claims_immutable,
    classify_action,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_start,
    later_disarm_supersedes,
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


class ClassifyAction(unittest.TestCase):
    def test_known_actions(self):
        self.assertEqual(classify_action("inspect"), INSPECT)
        self.assertEqual(classify_action("classify"), CLASSIFY)
        self.assertEqual(classify_action("start"), START)
        self.assertEqual(ACTIONS, frozenset({INSPECT, CLASSIFY, START}))

    def test_case_and_hyphen_fold(self):
        self.assertEqual(classify_action("INSPECT"), INSPECT)
        self.assertEqual(classify_action("Classify"), CLASSIFY)
        self.assertEqual(classify_action("START"), START)

    def test_missing_is_unknown_not_false(self):
        self.assertEqual(classify_action(None), UNKNOWN)
        self.assertNotEqual(classify_action(None), "FALSE")
        self.assertFalse(unknown_is_false())

    def test_bool_int_float_fail_closed(self):
        for bad in (True, False, 1, 0, 1.0, b"inspect"):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    classify_action(bad)

    def test_empty_and_unknown_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_action("")
        with self.assertRaises(FailClosedError):
            classify_action("   ")
        with self.assertRaises(FailClosedError):
            classify_action("send")
        with self.assertRaises(FailClosedError):
            classify_action("create")

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
                    classify_action(name)

    def test_ready_is_not_authorized(self):
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertFalse(ready_is_authorized())


class BindScope(unittest.TestCase):
    def test_bind_records_pair(self):
        bound = bind_scope("inspect", _RUN)
        self.assertIsInstance(bound, ScopeBind)
        self.assertEqual(bound.action, INSPECT)
        self.assertEqual(bound.run_id, _RUN)
        self.assertEqual(bound.action_class, INSPECT)

    def test_frozen_cannot_retcon(self):
        bound = bind_scope("classify", _RUN)
        with self.assertRaises(Exception):
            bound.action = "start"  # type: ignore[misc]

    def test_malformed_run_id_fail_closed(self):
        with self.assertRaises(FailClosedError):
            bind_scope("inspect", "run-1-myrun")
        with self.assertRaises(FailClosedError):
            bind_scope("inspect", "not-a-run")
        with self.assertRaises(FailClosedError):
            bind_scope("inspect", "")

    def test_bool_run_id_fail_closed(self):
        with self.assertRaises(FailClosedError):
            bind_scope("inspect", True)
        with self.assertRaises(FailClosedError):
            bind_scope("inspect", 1780000000)

    def test_missing_action_on_explicit_bind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_scope(None, _RUN)

    def test_sealed_run_id_refused(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    bind_scope("inspect", name)


class TryBindUnknown(unittest.TestCase):
    def test_missing_action_is_none(self):
        self.assertIsNone(try_bind(None, _RUN))
        self.assertIsNone(try_bind("inspect", None))
        self.assertIsNone(try_bind(None, None))

    def test_present_malformed_still_fails_closed(self):
        with self.assertRaises(FailClosedError):
            try_bind(True, _RUN)
        with self.assertRaises(FailClosedError):
            try_bind("inspect", "run-1-x")
        with self.assertRaises(FailClosedError):
            try_bind("send_authorized", _RUN)

    def test_try_bind_success(self):
        bound = try_bind("start", _RUN)
        self.assertIsNotNone(bound)
        assert bound is not None
        self.assertEqual(bound.action, START)


class AdmitScope(unittest.TestCase):
    def test_inspect_and_classify_continue_under_halt(self):
        self.assertIs(admit_scope("inspect", halted=True), True)
        self.assertIs(admit_scope("classify", halted=True), True)
        self.assertIs(admit_scope("inspect", halted=False), True)

    def test_start_refused_when_halted(self):
        self.assertIs(admit_scope("start", halted=True), False)
        self.assertIs(admit_scope("start", halted=False), True)

    def test_missing_is_unknown_none(self):
        self.assertIsNone(admit_scope(None, halted=False))
        self.assertIsNone(admit_scope(None, halted=True))
        self.assertIsNot(admit_scope(None, halted=False), False)

    def test_non_bool_halted_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_scope("inspect", halted=None)  # type: ignore[arg-type]
        with self.assertRaises(FailClosedError):
            admit_scope("inspect", halted=1)  # type: ignore[arg-type]

    def test_sealed_never_admitted(self):
        with self.assertRaises(FailClosedError):
            admit_scope("send_authorized", halted=False)
        with self.assertRaises(FailClosedError):
            admit_scope("campaign_envelope_ready", halted=False)


class PairMatches(unittest.TestCase):
    def test_same_action_is_true(self):
        self.assertIs(pair_matches("inspect", _RUN, "inspect"), True)

    def test_different_action_is_false_not_unknown(self):
        self.assertIs(pair_matches("inspect", _RUN, "start"), False)

    def test_missing_is_unknown_none(self):
        self.assertIsNone(pair_matches(None, _RUN, "inspect"))
        self.assertIsNone(pair_matches("inspect", None, "inspect"))
        self.assertIsNone(pair_matches("inspect", _RUN, None))
        self.assertIsNot(pair_matches(None, _RUN, "inspect"), False)


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_blocks_only_start(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_inspect())
        self.assertTrue(halt_blocks_start())
        params = inspect.signature(classify_action).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)

    def test_timeout_is_unknown_not_writer(self):
        self.assertEqual(classify_timeout(), UNKNOWN)
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready(self):
        self.assertFalse(promotes_ready_to_send())
        self.assertTrue(later_disarm_supersedes())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())
        store = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ofn", "adapters", "run_store.py",
        )
        if os.path.isfile(store):
            text = open(store, encoding="utf-8").read()
            self.assertNotIn("scope_class", text)
            self.assertNotIn("limit_pin", text)

    def test_claims_immutable_is_false(self):
        self.assertFalse(claims_immutable())


if __name__ == "__main__":
    unittest.main()
