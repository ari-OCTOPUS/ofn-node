"""Typed-event vocabulary — construction gates, ready ≠ authorized.

These tests lock the spine on main without editing ``events.py`` (owned
by open PR #82). Nested payload scan is out of scope here and is not
recorded as clean.
"""

from __future__ import annotations

import unittest

from ofn.kernel import events as ev
from ofn.kernel.errors import FailClosedError


class Vocabulary(unittest.TestCase):
    def test_spine_kinds_are_the_nine_named_constants(self):
        named = {
            ev.RUN_CREATED, ev.CLAIM_CREATED, ev.PROPOSAL_CREATED,
            ev.POLICY_DECISION, ev.TOOL_INVOKED, ev.EXECUTION_RECEIPT,
            ev.BUDGET_DEBIT, ev.RUN_CLOSED, ev.RUN_REJECTED,
        }
        self.assertEqual(ev.EVENT_KINDS, named)

    def test_ready_and_send_are_forbidden_and_not_kinds(self):
        sealed = {"send_authorized", "quote_sent", "campaign_envelope_ready"}
        self.assertEqual(ev.FORBIDDEN_EFFECT_KINDS, sealed)
        self.assertTrue(sealed.isdisjoint(ev.EVENT_KINDS))
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_proposal_is_not_execution(self):
        self.assertNotEqual(ev.PROPOSAL_CREATED, ev.EXECUTION_RECEIPT)
        self.assertIn(ev.PROPOSAL_CREATED, ev.EVENT_KINDS)
        self.assertIn(ev.EXECUTION_RECEIPT, ev.EVENT_KINDS)


class MakeEventGates(unittest.TestCase):
    def test_unknown_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            ev.make_event("NOT_A_KIND", "run-1", now_epoch_s=1)

    def test_forbidden_kind_fails_closed(self):
        for kind in ev.FORBIDDEN_EFFECT_KINDS:
            with self.subTest(kind=kind):
                with self.assertRaises(FailClosedError):
                    ev.make_event(kind, "run-1", now_epoch_s=1)

    def test_budget_debit_requires_ref(self):
        with self.assertRaises(FailClosedError):
            ev.make_event(ev.BUDGET_DEBIT, "run-1", now_epoch_s=1)
        rec = ev.make_event(
            ev.BUDGET_DEBIT, "run-1", now_epoch_s=1, ref="evt-receipt")
        self.assertEqual(rec["ref"], "evt-receipt")

    def test_blank_run_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            ev.make_event(ev.TOOL_INVOKED, "  ", now_epoch_s=1)

    def test_bool_timestamp_fails_closed(self):
        with self.assertRaises(FailClosedError):
            ev.make_event(ev.TOOL_INVOKED, "run-1", now_epoch_s=True)

    def test_payload_must_be_mapping(self):
        with self.assertRaises(FailClosedError):
            ev.make_event(
                ev.TOOL_INVOKED, "run-1", now_epoch_s=1,
                payload=["not", "a", "mapping"])


class PayloadSmuggleTopLevel(unittest.TestCase):
    def test_top_level_key_is_caught(self):
        self.assertEqual(
            ev.payload_forbidden_effect({"send_authorized": False}),
            "send_authorized")

    def test_top_level_value_is_caught(self):
        self.assertEqual(
            ev.payload_forbidden_effect({"next": "campaign_envelope_ready"}),
            "campaign_envelope_ready")

    def test_make_event_refuses_smuggled_ready(self):
        with self.assertRaises(FailClosedError):
            ev.make_event(
                ev.POLICY_DECISION, "run-1", now_epoch_s=1,
                payload={"next": "campaign_envelope_ready"})

    def test_none_payload_is_clean(self):
        self.assertIsNone(ev.payload_forbidden_effect(None))

    def test_nested_scan_is_out_of_scope_on_main_not_claimed_clean(self):
        # Main events.py walks top-level keys/values only. A nested
        # mapping is therefore not a verdict. This test records the
        # scope (UNKNOWN), not a claim that the nest is clean. PR #82
        # deepens the scan; when it merges this assertion must change.
        nested = {"inner": {"send_authorized": True}}
        self.assertIsNone(ev.payload_forbidden_effect(nested))


class NameHelper(unittest.TestCase):
    def test_unknown_name_is_not_forbidden(self):
        self.assertFalse(ev.is_forbidden_effect_name("score"))
        self.assertFalse(ev.is_forbidden_effect_name(None))
        self.assertFalse(ev.is_forbidden_effect_name(1))

    def test_exact_sealed_names_only(self):
        self.assertTrue(ev.is_forbidden_effect_name("send_authorized"))
        # Case-fold aliases are envelope-side (#83), not this helper.
        self.assertFalse(ev.is_forbidden_effect_name("Send_Authorized"))


if __name__ == "__main__":
    unittest.main()
