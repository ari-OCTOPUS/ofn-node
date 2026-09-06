"""Receipt digest — second witness, independent of run_store inline stamp."""

from __future__ import annotations

import hashlib
import json
import unittest

from ofn.adapters.receipt import (
    DIGEST_KEY, grants_send, receipt_digest, stamp_receipt, verify_receipt,
)
from ofn.kernel.errors import FailClosedError


class StampAndVerify(unittest.TestCase):
    def test_stamp_adds_digest_of_body_without_self_hash(self):
        stamped = stamp_receipt({"tool": "score", "n": 1})
        self.assertIn(DIGEST_KEY, stamped)
        body = {k: v for k, v in stamped.items() if k != DIGEST_KEY}
        expected = hashlib.sha256(
            json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        self.assertEqual(stamped[DIGEST_KEY], expected)
        self.assertEqual(verify_receipt(stamped), expected)

    def test_none_payload_is_empty_object(self):
        stamped = stamp_receipt(None)
        self.assertEqual(
            stamped[DIGEST_KEY],
            receipt_digest({}),
        )
        verify_receipt(stamped)

    def test_matching_claimed_digest_is_accepted(self):
        body = {"tool": "draft"}
        digest = receipt_digest(body)
        stamped = stamp_receipt({"tool": "draft", DIGEST_KEY: digest})
        self.assertEqual(stamped[DIGEST_KEY], digest)

    def test_forged_digest_refused_and_returns_nothing(self):
        with self.assertRaises(FailClosedError):
            stamp_receipt({"tool": "draft", DIGEST_KEY: "0" * 64})

    def test_missing_digest_on_verify_fails_closed(self):
        with self.assertRaises(FailClosedError):
            verify_receipt({"tool": "draft"})

    def test_tampered_payload_fails_verify(self):
        stamped = stamp_receipt({"tool": "score"})
        stamped["tool"] = "smtp"
        with self.assertRaises(FailClosedError):
            verify_receipt(stamped)

    def test_digest_key_inside_body_is_not_self_hashable(self):
        with self.assertRaises(FailClosedError):
            receipt_digest({"tool": "score", DIGEST_KEY: "abc"})

    def test_non_mapping_fails_closed(self):
        with self.assertRaises(FailClosedError):
            stamp_receipt(["not", "a", "mapping"])  # type: ignore[arg-type]


class ReadyIsNotAReceipt(unittest.TestCase):
    def test_send_authorized_key_refused(self):
        with self.assertRaises(FailClosedError):
            stamp_receipt({"send_authorized": True})

    def test_quote_sent_value_refused(self):
        with self.assertRaises(FailClosedError):
            stamp_receipt({"next": "quote_sent"})

    def test_campaign_envelope_ready_refused(self):
        with self.assertRaises(FailClosedError):
            stamp_receipt({"next": "campaign_envelope_ready"})

    def test_stamp_never_grants_send(self):
        stamped = stamp_receipt({"tool": "score"})
        self.assertFalse(grants_send(stamped))
        self.assertFalse(grants_send(None))

    def test_grants_send_fails_closed_on_smuggled_ready(self):
        with self.assertRaises(FailClosedError):
            grants_send({"campaign_envelope_ready": True})


if __name__ == "__main__":
    unittest.main()
