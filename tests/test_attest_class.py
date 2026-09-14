"""Kernel-pure attest class — complementary to vault-witness adapter.

UNKNOWN is not FALSE. Missing-expected is not tamper. Ready is not
authorized. This module is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.attest_class import (
    FILE_LABELS,
    FILE_VERDICTS,
    AttestDecision,
    classify_file,
    classify_missing_expected,
    claims_immutable,
    grants_send,
    halt_blocks_attest,
    missing_expected_is_inconsistent,
    proposal_is_execution,
    ready_is_authorized,
    unknown_is_false,
    unknown_is_inconsistent,
    unmanifested_is_consistent,
    unreadable_is_skip,
)

_HEX_A = "a" * 64
_HEX_B = "b" * 64


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_attest(self):
        self.assertFalse(halt_blocks_attest())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_unknown_is_not_inconsistent(self):
        self.assertFalse(unknown_is_inconsistent())

    def test_missing_expected_is_not_inconsistent(self):
        self.assertFalse(missing_expected_is_inconsistent())

    def test_unmanifested_is_not_consistent(self):
        self.assertFalse(unmanifested_is_consistent())

    def test_unreadable_is_not_skip(self):
        self.assertFalse(unreadable_is_skip())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_closed_vocabularies(self):
        self.assertEqual(
            FILE_VERDICTS,
            {"consistent", "inconsistent", "incomplete", "unknown"})
        self.assertEqual(
            FILE_LABELS,
            {"match", "mismatch", "unmanifested",
             "missing-expected", "unreadable"})

    def test_classify_file_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(classify_file).parameters
        self.assertEqual(
            list(params),
            ["path", "readable", "observed_sha", "expected_sha"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw"):
            self.assertNotIn(forbidden, params)

    def test_missing_expected_signature_is_sealed(self):
        params = inspect.signature(classify_missing_expected).parameters
        self.assertEqual(list(params), ["path"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            AttestDecision(
                verdict="unknown", label="unreadable",
                path="a.md", grants_send=True)

    def test_constructor_refuses_mismatched_label_pairs(self):
        with self.assertRaises(FailClosedError):
            AttestDecision(verdict="unknown", label="match", path="a.md")
        with self.assertRaises(FailClosedError):
            AttestDecision(
                verdict="inconsistent", label="unreadable", path="a.md")
        with self.assertRaises(FailClosedError):
            AttestDecision(
                verdict="consistent", label="mismatch", path="a.md")
        with self.assertRaises(FailClosedError):
            AttestDecision(
                verdict="incomplete", label="match", path="a.md")

    def test_constructor_refuses_sealed_path(self):
        with self.assertRaises(FailClosedError):
            AttestDecision(
                verdict="unknown", label="unreadable",
                path="send_authorized")
        with self.assertRaises(FailClosedError):
            AttestDecision(
                verdict="unknown", label="unreadable",
                path="docs/campaign_envelope_ready/a.md")

    def test_foreign_verdict_refused(self):
        with self.assertRaises(FailClosedError):
            AttestDecision(verdict="ok", label="match", path="a.md")


class ClassifyMatchAndMismatch(unittest.TestCase):
    def test_matching_digests_are_consistent(self):
        d = classify_file(
            path="a.md", readable=True,
            observed_sha=_HEX_A, expected_sha=_HEX_A)
        self.assertEqual(d.verdict, "consistent")
        self.assertEqual(d.label, "match")
        self.assertEqual(d.path, "a.md")
        self.assertFalse(d.grants_send)

    def test_different_digests_are_inconsistent(self):
        d = classify_file(
            path="a.md", readable=True,
            observed_sha=_HEX_A, expected_sha=_HEX_B)
        self.assertEqual(d.verdict, "inconsistent")
        self.assertEqual(d.label, "mismatch")
        self.assertFalse(d.grants_send)

    def test_case_sensitive_hex_must_be_lowercase(self):
        with self.assertRaises(FailClosedError):
            classify_file(
                path="a.md", readable=True,
                observed_sha="A" * 64, expected_sha=_HEX_A)


class ClassifyIncomplete(unittest.TestCase):
    def test_unmanifested_is_incomplete_not_consistent(self):
        d = classify_file(
            path="extra.md", readable=True,
            observed_sha=_HEX_A, expected_sha=None)
        self.assertEqual(d.verdict, "incomplete")
        self.assertEqual(d.label, "unmanifested")
        self.assertFalse(unmanifested_is_consistent())
        self.assertFalse(d.grants_send)

    def test_missing_expected_is_incomplete_not_inconsistent(self):
        d = classify_missing_expected(path="SEASON-LOG.md")
        self.assertEqual(d.verdict, "incomplete")
        self.assertEqual(d.label, "missing-expected")
        self.assertFalse(missing_expected_is_inconsistent())
        self.assertNotEqual(d.verdict, "inconsistent")


class ClassifyUnknown(unittest.TestCase):
    def test_unreadable_is_unknown_and_not_skipped(self):
        d = classify_file(path="locked.md", readable=False)
        self.assertEqual(d.verdict, "unknown")
        self.assertEqual(d.label, "unreadable")
        self.assertFalse(unknown_is_false())
        self.assertFalse(unknown_is_inconsistent())
        self.assertFalse(unreadable_is_skip())

    def test_unreadable_ignores_supplied_digests(self):
        d = classify_file(
            path="locked.md", readable=False,
            observed_sha=_HEX_A, expected_sha=_HEX_A)
        self.assertEqual(d.verdict, "unknown")
        self.assertEqual(d.label, "unreadable")

    def test_unreadable_cannot_be_argued_into_mismatch(self):
        d = classify_file(
            path="locked.md", readable=False,
            observed_sha=_HEX_A, expected_sha=_HEX_B)
        self.assertEqual(d.verdict, "unknown")
        self.assertNotEqual(d.verdict, "inconsistent")


class FailClosedInputs(unittest.TestCase):
    def test_missing_readable_is_unknown_not_true(self):
        with self.assertRaises(FailClosedError):
            classify_file(path="a.md", readable=None, observed_sha=_HEX_A)

    def test_string_readable_is_not_a_claim(self):
        with self.assertRaises(FailClosedError):
            classify_file(path="a.md", readable="yes", observed_sha=_HEX_A)

    def test_readable_true_requires_observed_digest(self):
        with self.assertRaises(FailClosedError):
            classify_file(path="a.md", readable=True, expected_sha=_HEX_A)

    def test_blank_and_bool_path_refuse(self):
        with self.assertRaises(FailClosedError):
            classify_file(path="", readable=False)
        with self.assertRaises(FailClosedError):
            classify_file(path=True, readable=False)
        with self.assertRaises(FailClosedError):
            classify_missing_expected(path="")

    def test_short_or_non_hex_digest_refuses(self):
        with self.assertRaises(FailClosedError):
            classify_file(
                path="a.md", readable=True,
                observed_sha="abc", expected_sha=_HEX_A)
        with self.assertRaises(FailClosedError):
            classify_file(
                path="a.md", readable=True,
                observed_sha=_HEX_A, expected_sha="g" * 64)

    def test_sealed_path_refuses(self):
        with self.assertRaises(FailClosedError):
            classify_file(path="send_authorized", readable=False)
        with self.assertRaises(FailClosedError):
            classify_file(path="quote_sent", readable=False)
        with self.assertRaises(FailClosedError):
            classify_missing_expected(path="campaign_envelope_ready")
        with self.assertRaises(FailClosedError):
            classify_file(
                path="docs/send_authorized/a.md", readable=True,
                observed_sha=_HEX_A, expected_sha=_HEX_A)

    def test_sealed_digest_refuses(self):
        with self.assertRaises(FailClosedError):
            classify_file(
                path="a.md", readable=True,
                observed_sha="send_authorized", expected_sha=_HEX_A)


if __name__ == "__main__":
    unittest.main()
