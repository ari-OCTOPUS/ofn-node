"""Kernel-pure freeze-class — lock digest vs observed bytes.

LF-canonical match is LF_MATCH. A known CRLF checkout hash is
CRLF_CHECKOUT, not a source edit and not FALSE. Missing / timeout
is UNKNOWN, not FALSE. A content mismatch is MISMATCH.
Ready is not authorized. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.freeze_class import (
    CRLF_CHECKOUT,
    KINDS,
    LF_MATCH,
    MISMATCH,
    UNKNOWN,
    FreezeClass,
    claims_immutable,
    classify_digest,
    crlf_is_source_edit,
    grants_send,
    halt_blocks_classify,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    unknown_is_false,
    wires_into_run_store,
)

_LF = "5c0c16732b60b20f2bb8483955c770574e8d99c217ecc6e9d7a0536bca1be1d6"
_CRLF = "7e99cb35f8970a5069521f36f72855948b56f2a8d9182326edd2db61d4d9c901"
_OTHER = "a" * 64


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_crlf_is_not_a_source_edit(self):
        self.assertFalse(crlf_is_source_edit())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_does_not_wire_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_kinds_are_closed(self):
        self.assertEqual(
            KINDS, {LF_MATCH, CRLF_CHECKOUT, MISMATCH, UNKNOWN})

    def test_signature_has_no_send_halt_or_immutable_knob(self):
        params = inspect.signature(classify_digest).parameters
        self.assertEqual(
            list(params),
            ["observed", "lock", "known_crlf", "error", "intent"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt",
            "halt_raw",
            "immutable",
            "rewrite",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            FreezeClass(
                kind=LF_MATCH, observed=_LF, lock=_LF,
                known_crlf=_CRLF, grants_send=True)


class ClassifyDigest(unittest.TestCase):
    def test_lf_match(self):
        d = classify_digest(observed=_LF, lock=_LF, known_crlf=_CRLF)
        self.assertEqual(d.kind, LF_MATCH)
        self.assertEqual(d.observed, _LF)
        self.assertEqual(d.lock, _LF)
        self.assertFalse(d.grants_send)

    def test_crlf_checkout_is_known_artefact(self):
        d = classify_digest(observed=_CRLF, lock=_LF, known_crlf=_CRLF)
        self.assertEqual(d.kind, CRLF_CHECKOUT)
        self.assertNotEqual(d.kind, "FALSE")
        self.assertFalse(crlf_is_source_edit())
        self.assertFalse(d.grants_send)

    def test_crlf_without_known_hash_is_mismatch(self):
        d = classify_digest(observed=_CRLF, lock=_LF)
        self.assertEqual(d.kind, MISMATCH)

    def test_content_mismatch(self):
        d = classify_digest(observed=_OTHER, lock=_LF, known_crlf=_CRLF)
        self.assertEqual(d.kind, MISMATCH)
        self.assertFalse(d.grants_send)

    def test_missing_observed_is_unknown_not_false(self):
        d = classify_digest(observed=None, lock=_LF)
        self.assertEqual(d.kind, UNKNOWN)
        self.assertNotEqual(d.kind, "FALSE")
        self.assertIsNone(d.observed)

    def test_missing_lock_is_unknown_not_false(self):
        d = classify_digest(observed=_LF, lock=None)
        self.assertEqual(d.kind, UNKNOWN)
        self.assertIsNone(d.lock)

    def test_timeout_forces_unknown(self):
        d = classify_digest(
            observed=_LF, lock=_LF, error=TimeoutError("lock wait"))
        self.assertEqual(d.kind, UNKNOWN)
        self.assertIsNone(d.observed)
        self.assertFalse(timeout_proves_concurrent_write())

    def test_observe_intent_continues(self):
        d = classify_digest(
            observed=_LF, lock=_LF, intent="observe")
        self.assertEqual(d.kind, LF_MATCH)

    def test_hex_is_folded_lower(self):
        d = classify_digest(observed=_LF.upper(), lock=_LF)
        self.assertEqual(d.kind, LF_MATCH)
        self.assertEqual(d.observed, _LF)

    def test_short_digest_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_digest(observed="abc", lock=_LF)

    def test_bool_digest_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_digest(observed=True, lock=_LF)

    def test_empty_digest_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_digest(observed="", lock=_LF)

    def test_sealed_observed_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_digest(observed="send_authorized", lock=_LF)
        self.assertIn("sealed", str(ctx.exception).lower())

    def test_sealed_lock_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_digest(observed=_LF, lock="quote_sent")

    def test_ready_name_is_not_authorized(self):
        with self.assertRaises(FailClosedError):
            classify_digest(
                observed="campaign_envelope_ready", lock=_LF)
        self.assertFalse(ready_is_authorized())

    def test_unknown_intent_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_digest(observed=_LF, lock=_LF, intent="rewrite")
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_sealed_intent_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_digest(
                observed=_LF, lock=_LF, intent="send_authorized")
