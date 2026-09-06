"""Contract tests for receipt_bind (P1 complementary).

A bind records a TYPED EXECUTION_RECEIPT + 64-hex digest.
Proposal cannot bind. Missing is UNKNOWN (None), not ''.
Forged digest fails closed. Ready ≠ authorized. Not wired
into the run store. Distinct from #87 receipts adapters.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import EXECUTION_RECEIPT, PROPOSAL_CREATED, RUN_CREATED
from ofn.kernel.receipt_bind import (
    ReceiptBind,
    bind_receipt,
    burns_idempotency_key,
    claims_immutable,
    digest_agrees,
    grants_send,
    halt_blocks_bind,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    try_bind,
    typed_is_receipt,
    unknown_digest_is_empty,
)


_TS = 1788405009
_RUN = "run-1788405009-rcptbind01"
_DIGEST = "a" * 64
_OTHER = "b" * 64


def _receipt(**extra):
    rec = {
        "kind": EXECUTION_RECEIPT,
        "run_id": _RUN,
        "ts": _TS,
    }
    rec.update(extra)
    return rec


class BindReceipt(unittest.TestCase):
    def test_bind_records_pair(self):
        bound = bind_receipt(_receipt(), _DIGEST)
        self.assertIsInstance(bound, ReceiptBind)
        self.assertEqual(bound.run_id, _RUN)
        self.assertEqual(bound.digest, _DIGEST)
        self.assertEqual(bound.kind, EXECUTION_RECEIPT)
        self.assertEqual(bound.ts, _TS)

    def test_frozen_cannot_retcon(self):
        bound = bind_receipt(_receipt(), _DIGEST)
        with self.assertRaises(Exception):
            bound.digest = _OTHER  # type: ignore[misc]

    def test_proposal_cannot_bind(self):
        with self.assertRaises(FailClosedError):
            bind_receipt(
                {"kind": PROPOSAL_CREATED, "run_id": _RUN, "ts": _TS},
                _DIGEST)
        self.assertFalse(proposal_is_execution())

    def test_run_created_cannot_bind(self):
        with self.assertRaises(FailClosedError):
            bind_receipt(
                {"kind": RUN_CREATED, "run_id": _RUN, "ts": _TS},
                _DIGEST)

    def test_uppercase_digest_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_receipt(_receipt(), "A" * 64)

    def test_short_digest_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_receipt(_receipt(), "a" * 63)

    def test_empty_digest_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_receipt(_receipt(), "")

    def test_non_hex_digest_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_receipt(_receipt(), "g" * 64)

    def test_bool_digest_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_receipt(_receipt(), True)

    def test_missing_record_on_explicit_bind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            bind_receipt(None, _DIGEST)

    def test_sealed_kind_refused(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    bind_receipt(
                        {"kind": name, "run_id": _RUN, "ts": _TS},
                        _DIGEST)


class TryBindUnknown(unittest.TestCase):
    def test_missing_digest_is_none_not_empty(self):
        self.assertIsNone(try_bind(_receipt(), None))
        self.assertFalse(unknown_digest_is_empty())

    def test_missing_record_is_none(self):
        self.assertIsNone(try_bind(None, _DIGEST))

    def test_missing_kind_is_none(self):
        self.assertIsNone(try_bind({"run_id": _RUN, "ts": _TS}, _DIGEST))

    def test_both_missing_is_none(self):
        self.assertIsNone(try_bind(None, None))

    def test_present_malformed_still_fails_closed(self):
        with self.assertRaises(FailClosedError):
            try_bind(_receipt(), "not-a-digest")
        with self.assertRaises(FailClosedError):
            try_bind(_receipt(kind=PROPOSAL_CREATED), _DIGEST)

    def test_try_bind_success(self):
        bound = try_bind(_receipt(), _DIGEST)
        self.assertIsNotNone(bound)
        assert bound is not None
        self.assertEqual(bound.digest, _DIGEST)


class DigestAgrees(unittest.TestCase):
    def test_same_digest_agrees(self):
        self.assertIs(digest_agrees(_receipt(), _DIGEST, _DIGEST), True)

    def test_different_digest_is_false_not_unknown(self):
        self.assertIs(digest_agrees(_receipt(), _DIGEST, _OTHER), False)

    def test_missing_expected_is_none(self):
        self.assertIsNone(digest_agrees(_receipt(), _DIGEST, None))

    def test_missing_record_is_none(self):
        self.assertIsNone(digest_agrees(None, _DIGEST, _DIGEST))

    def test_forged_expected_fails_closed(self):
        with self.assertRaises(FailClosedError):
            digest_agrees(_receipt(), _DIGEST, "Z" * 64)


class TypedIsReceipt(unittest.TestCase):
    def test_execution_is_true(self):
        self.assertIs(typed_is_receipt(_receipt()), True)

    def test_proposal_is_false(self):
        self.assertIs(
            typed_is_receipt(
                {"kind": PROPOSAL_CREATED, "run_id": _RUN, "ts": _TS}),
            False)

    def test_missing_is_none(self):
        self.assertIsNone(typed_is_receipt(None))
        self.assertIsNone(typed_is_receipt({"run_id": _RUN, "ts": _TS}))


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_bind(self):
        self.assertFalse(halt_blocks_bind())

    def test_timeout_does_not_prove_writer(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_burn_idempotency(self):
        self.assertFalse(burns_idempotency_key())

    def test_bind_has_no_halt_or_now_parameter(self):
        params = inspect.signature(bind_receipt).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("now", params)
        self.assertEqual(list(params), ["record", "digest"])


if __name__ == "__main__":
    unittest.main()
