"""Kernel-pure dual record — complementary to numeric_claim and arbiter_claim.

A pair is witnessed only when two independent sources agree.
HALT is not a parameter. A sealed send/ready name refuses.
Ready is not authorized. This module is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.dual_record import (
    DualVerdict,
    EVIDENCE_LEVELS,
    PAIR_REASONS,
    RecordRef,
    STATUSES,
    VANTAGES,
    classify_timeout,
    claims_immutable,
    grants_send,
    halt_blocks_pair,
    pair_records,
    picks_winner,
    proposal_is_execution,
    raises_grade,
    ready_is_authorized,
    timeout_proves_concurrent,
    unknown_is_false,
    unknown_is_true,
)
from ofn.kernel.errors import FailClosedError


def _rec(
    source: str,
    value: str = "pass",
    *,
    vantage: str = "this_host_only",
    level: str = "E2",
) -> RecordRef:
    return RecordRef(
        source_path=source,
        vantage=vantage,
        value=value,
        evidence_level=level,
    )


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_pairing(self):
        self.assertFalse(halt_blocks_pair())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false_and_not_true(self):
        self.assertFalse(unknown_is_false())
        self.assertFalse(unknown_is_true())

    def test_does_not_pick_a_winner(self):
        self.assertFalse(picks_winner())

    def test_does_not_raise_grade(self):
        self.assertFalse(raises_grade())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(classify_timeout(), "UNKNOWN")

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(pair_records).parameters
        self.assertEqual(list(params), ["topic", "record_a", "record_b"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            DualVerdict(status="WITNESSED", reason=None,
                        topic="head_sha", grants_send=True)
        with self.assertRaises(FailClosedError):
            DualVerdict(status="UNWITNESSED", reason="missing_second",
                        topic="head_sha", grants_send=True)

    def test_witnessed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            DualVerdict(status="WITNESSED", reason="missing_second",
                        topic="head_sha")

    def test_unwitnessed_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            DualVerdict(status="UNWITNESSED", reason=None, topic="head_sha")
        with self.assertRaises(FailClosedError):
            DualVerdict(status="UNWITNESSED", reason="send_authorized",
                        topic="head_sha")
        self.assertIn("missing_second", PAIR_REASONS)
        self.assertIn("same_source", PAIR_REASONS)
        self.assertIn("sealed_effect", PAIR_REASONS)
        self.assertIn("contradicted", PAIR_REASONS)
        self.assertNotIn("send_authorized", PAIR_REASONS)

    def test_unknown_status_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            DualVerdict(status="TRUE", reason=None, topic="head_sha")
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_witnessed_decision_refuses_sealed_names(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    DualVerdict(status="WITNESSED", reason=None, topic=name)

    def test_mismatch_refusal_cannot_carry_a_sealed_name(self):
        with self.assertRaises(FailClosedError):
            DualVerdict(status="UNWITNESSED", reason="same_source",
                        topic="send_authorized")

    def test_sealed_effect_refusal_names_the_subject(self):
        d = DualVerdict(status="UNWITNESSED", reason="sealed_effect",
                        topic="send_authorized")
        self.assertEqual(d.topic, "send_authorized")
        self.assertEqual(d.status, "UNWITNESSED")
        self.assertFalse(d.grants_send)


class ClosedVocabularies(unittest.TestCase):
    def test_statuses(self):
        self.assertEqual(
            STATUSES, frozenset({"WITNESSED", "UNWITNESSED", "CONTRADICTED"}))
        self.assertNotIn("TRUE", STATUSES)
        self.assertNotIn("FALSE", STATUSES)
        self.assertNotIn("UNKNOWN", STATUSES)

    def test_vantages(self):
        self.assertEqual(
            VANTAGES,
            frozenset({"this_host_only", "loopback", "lan", "remote"}))

    def test_evidence_levels(self):
        self.assertEqual(
            EVIDENCE_LEVELS,
            frozenset({"E0", "E1", "E2", "E3", "E4", "E5"}))


class RecordRefBounds(unittest.TestCase):
    def test_empty_and_bool_names_fail_closed(self):
        for bad in ("", "  ", True, False, None, 0):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    RecordRef(source_path=bad, vantage="this_host_only",
                              value="pass", evidence_level="E2")
                with self.assertRaises(FailClosedError):
                    RecordRef(source_path="a.txt", vantage=bad,
                              value="pass", evidence_level="E2")
                with self.assertRaises(FailClosedError):
                    RecordRef(source_path="a.txt", vantage="this_host_only",
                              value=bad, evidence_level="E2")
                with self.assertRaises(FailClosedError):
                    RecordRef(source_path="a.txt", vantage="this_host_only",
                              value="pass", evidence_level=bad)

    def test_unknown_vantage_is_not_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            RecordRef(source_path="a.txt", vantage="system_wide",
                      value="pass", evidence_level="E2")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_level_is_not_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            RecordRef(source_path="a.txt", vantage="this_host_only",
                      value="pass", evidence_level="improved")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertNotIn("improved", RecordRef(
            source_path="a.txt", vantage="this_host_only",
            value="pass", evidence_level="E2").evidence_level)

    def test_sealed_value_refused_on_construction(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "quote-sent"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    RecordRef(source_path="a.txt", vantage="this_host_only",
                              value=name, evidence_level="E2")

    def test_strips_source_and_value(self):
        r = RecordRef(source_path="  a.txt  ", vantage="this_host_only",
                      value="  pass  ", evidence_level="E2")
        self.assertEqual(r.source_path, "a.txt")
        self.assertEqual(r.value, "pass")


class PairingHappyPath(unittest.TestCase):
    def test_two_sources_agreeing_are_witnessed(self):
        d = pair_records(
            topic="head_sha",
            record_a=_rec("git-rev-parse", "58e8777"),
            record_b=_rec("receipt.json", "58e8777", vantage="loopback"),
        )
        self.assertEqual(d.status, "WITNESSED")
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)
        self.assertEqual(d.topic, "head_sha")

    def test_same_vantage_different_source_is_still_a_pair(self):
        d = pair_records(
            topic="exit_code",
            record_a=_rec("cmd-a", "0"),
            record_b=_rec("cmd-b", "0"),
        )
        self.assertEqual(d.status, "WITNESSED")
        self.assertFalse(d.grants_send)

    def test_replay_is_byte_identical(self):
        a = pair_records(
            topic="exit_code",
            record_a=_rec("cmd-a", "0"),
            record_b=_rec("cmd-b", "0"),
        )
        b = pair_records(
            topic="exit_code",
            record_a=_rec("cmd-a", "0"),
            record_b=_rec("cmd-b", "0"),
        )
        self.assertEqual(a, b)
        self.assertEqual(a.status, b.status)


class MissingAndSameSource(unittest.TestCase):
    def test_missing_second_is_unwitnessed_not_true(self):
        d = pair_records(topic="head_sha", record_a=_rec("only.txt"))
        self.assertEqual(d.status, "UNWITNESSED")
        self.assertEqual(d.reason, "missing_second")
        self.assertFalse(d.grants_send)
        self.assertFalse(unknown_is_true())

    def test_explicit_none_second_is_unwitnessed(self):
        d = pair_records(
            topic="head_sha", record_a=_rec("only.txt"), record_b=None)
        self.assertEqual(d.status, "UNWITNESSED")
        self.assertEqual(d.reason, "missing_second")

    def test_same_source_is_not_a_second_record(self):
        d = pair_records(
            topic="head_sha",
            record_a=_rec("same.txt", "abc"),
            record_b=_rec("same.txt", "abc"),
        )
        self.assertEqual(d.status, "UNWITNESSED")
        self.assertEqual(d.reason, "same_source")
        self.assertFalse(d.grants_send)

    def test_same_source_after_strip_is_not_independent(self):
        d = pair_records(
            topic="head_sha",
            record_a=_rec("  same.txt", "abc"),
            record_b=_rec("same.txt  ", "abc"),
        )
        self.assertEqual(d.status, "UNWITNESSED")
        self.assertEqual(d.reason, "same_source")


class ContradictionDoesNotResolve(unittest.TestCase):
    def test_disagreement_is_contradicted(self):
        d = pair_records(
            topic="head_sha",
            record_a=_rec("git", "aaa"),
            record_b=_rec("receipt", "bbb"),
        )
        self.assertEqual(d.status, "CONTRADICTED")
        self.assertEqual(d.reason, "contradicted")
        self.assertFalse(d.grants_send)
        self.assertFalse(picks_winner())

    def test_contradiction_does_not_pick_first_or_second(self):
        d = pair_records(
            topic="count",
            record_a=_rec("a", "16"),
            record_b=_rec("b", "19"),
        )
        self.assertNotEqual(d.status, "WITNESSED")
        self.assertNotIn(d.reason, (None, "missing_second"))


class SealedNameRefusesPair(unittest.TestCase):
    def test_sealed_topic_aliases(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "SEND_AUTHORIZED",
                     "quote-sent", "campaign-envelope-ready"):
            with self.subTest(name=name):
                d = pair_records(
                    topic=name,
                    record_a=_rec("a.txt"),
                    record_b=_rec("b.txt"),
                )
                self.assertEqual(d.status, "UNWITNESSED")
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)

    def test_ready_and_authorized_are_both_sealed_and_distinct(self):
        ready = pair_records(
            topic="campaign_envelope_ready",
            record_a=_rec("a.txt"),
            record_b=_rec("b.txt"),
        )
        auth = pair_records(
            topic="send_authorized",
            record_a=_rec("a.txt"),
            record_b=_rec("b.txt"),
        )
        self.assertEqual(ready.reason, "sealed_effect")
        self.assertEqual(auth.reason, "sealed_effect")
        self.assertNotEqual(ready.topic, auth.topic)
        self.assertFalse(ready_is_authorized())


class FailClosedInputs(unittest.TestCase):
    def test_missing_first_record_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pair_records(topic="head_sha", record_a=None, record_b=_rec("b"))

    def test_wrong_type_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            pair_records(topic="head_sha", record_a={"source": "a"})
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_wrong_type_second_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pair_records(
                topic="head_sha", record_a=_rec("a"), record_b="timeout")

    def test_empty_topic_fails_closed(self):
        for bad in ("", "  ", True, False, None):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    pair_records(topic=bad, record_a=_rec("a"),
                                 record_b=_rec("b"))


if __name__ == "__main__":
    unittest.main()
