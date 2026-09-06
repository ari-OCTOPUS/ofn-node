"""Kernel-pure numeric claim — a number without a receipt is refused.

Every integer claim carries command, UTC Z stamp, full HEAD SHA,
exit code, and a receipt path. Small n is UNDERPOWERED, never
"improved". Ready is not authorized. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.numeric_claim import (
    POWER_LABELS,
    NumericClaim,
    claims_immutable,
    claims_improved,
    classify_sample_power,
    grants_send,
    halt_blocks_claim,
    mint_numeric_claim,
    ready_is_authorized,
    require_exact_int,
    require_head_sha,
    require_utc_z,
    unknown_is_false,
)

_SHA = "f0edc963f116feae9683f369b557643ffc5340af"
_UTC = "2026-09-02T15:56:43Z"
_CMD = "python3 -m unittest tests.test_numeric_claim -q"
_RCPT = "docs/octopus-surgery/architecture/2026-09-02/receipts/P1-EVIDENCE-WITNESS-20260902.json"


def _claim(**overrides):
    kwargs = dict(
        value=12, command=_CMD, utc_iso=_UTC, head_sha=_SHA,
        exit_code=0, receipt_path=_RCPT,
    )
    kwargs.update(overrides)
    return mint_numeric_claim(**kwargs)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_cannot_claim_improved(self):
        self.assertFalse(claims_improved())
        self.assertNotIn("improved", POWER_LABELS)
        self.assertEqual(POWER_LABELS, frozenset({"UNDERPOWERED", "AT_THRESHOLD"}))

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_halt_does_not_block_claims(self):
        self.assertFalse(halt_blocks_claim())

    def test_signature_has_no_send_or_improved_knob(self):
        params = inspect.signature(mint_numeric_claim).parameters
        self.assertEqual(
            list(params),
            ["value", "command", "utc_iso", "head_sha",
             "exit_code", "receipt_path"],
        )
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "improved",
                          "immutable"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            NumericClaim(
                value=1, command=_CMD, utc_iso=_UTC, head_sha=_SHA,
                exit_code=0, receipt_path=_RCPT, grants_send=True)


class RequiredSourceFields(unittest.TestCase):
    def test_mint_records_all_six_fields(self):
        c = _claim()
        self.assertEqual(c.value, 12)
        self.assertEqual(c.command, _CMD)
        self.assertEqual(c.utc_iso, _UTC)
        self.assertEqual(c.head_sha, _SHA)
        self.assertEqual(c.exit_code, 0)
        self.assertEqual(c.receipt_path, _RCPT)
        self.assertFalse(c.grants_send)

    def test_bool_value_refused(self):
        with self.assertRaises(FailClosedError):
            _claim(value=True)

    def test_float_value_refused(self):
        with self.assertRaises(FailClosedError):
            require_exact_int(1.0, what="value")

    def test_string_value_refused(self):
        with self.assertRaises(FailClosedError):
            _claim(value="12")

    def test_empty_command_refused(self):
        with self.assertRaises(FailClosedError):
            _claim(command="   ")

    def test_sealed_command_refused(self):
        with self.assertRaises(FailClosedError):
            _claim(command="send_authorized")

    def test_naive_utc_refused(self):
        with self.assertRaises(FailClosedError):
            require_utc_z("2026-09-02T15:56:43")
        with self.assertRaises(FailClosedError):
            _claim(utc_iso="2026-09-02T15:56:43+00:00")

    def test_short_head_sha_refused(self):
        with self.assertRaises(FailClosedError):
            require_head_sha("f0edc96")
        with self.assertRaises(FailClosedError):
            _claim(head_sha="f0edc963f116feae9683f369b557643ffc5340")

    def test_uppercase_head_sha_folded(self):
        c = _claim(head_sha=_SHA.upper())
        self.assertEqual(c.head_sha, _SHA)

    def test_bool_exit_code_refused(self):
        with self.assertRaises(FailClosedError):
            _claim(exit_code=True)

    def test_absolute_receipt_path_refused(self):
        with self.assertRaises(FailClosedError):
            _claim(receipt_path="/tmp/receipt.json")

    def test_sealed_receipt_component_refused(self):
        with self.assertRaises(FailClosedError):
            _claim(receipt_path="docs/quote_sent/r.json")


class SamplePower(unittest.TestCase):
    def test_below_threshold_is_underpowered(self):
        self.assertEqual(
            classify_sample_power(3, threshold=10), "UNDERPOWERED")

    def test_at_threshold_is_not_improved(self):
        label = classify_sample_power(10, threshold=10)
        self.assertEqual(label, "AT_THRESHOLD")
        self.assertNotEqual(label, "improved")

    def test_above_threshold_is_still_not_improved(self):
        label = classify_sample_power(100, threshold=10)
        self.assertEqual(label, "AT_THRESHOLD")
        self.assertNotIn(label.lower(), {"improved", "better"})

    def test_threshold_must_be_positive(self):
        with self.assertRaises(FailClosedError):
            classify_sample_power(0, threshold=0)
        with self.assertRaises(FailClosedError):
            classify_sample_power(1, threshold=-1)

    def test_negative_n_refused(self):
        with self.assertRaises(FailClosedError):
            classify_sample_power(-1, threshold=10)

    def test_bool_n_refused(self):
        with self.assertRaises(FailClosedError):
            classify_sample_power(True, threshold=10)


if __name__ == "__main__":
    unittest.main()
