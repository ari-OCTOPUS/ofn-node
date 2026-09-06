"""Contract tests for utc_class (P1 complementary).

A supplied stamp is UTC_Z, OFFSET, or UNKNOWN. Missing is not FALSE
and not 0. Naive local fails closed. OFFSET is not UTC_Z. Sealed
send/ready names are not timestamps. Ready ≠ authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.utc_class import (
    OFFSET, UNKNOWN, UTC_Z, classify_stamp, claims_immutable,
    grants_send, halt_blocks_utc, is_utc_z, ready_is_authorized,
    unknown_is_false,
)


class ClassifyStamp(unittest.TestCase):
    def test_none_is_unknown_not_false(self):
        self.assertEqual(classify_stamp(None), UNKNOWN)
        self.assertNotEqual(classify_stamp(None), "FALSE")
        self.assertNotEqual(classify_stamp(None), UTC_Z)
        self.assertIsNone(None)

    def test_utc_z_accepted(self):
        self.assertEqual(classify_stamp("2026-09-03T02:07:08Z"), UTC_Z)
        self.assertTrue(is_utc_z("2026-09-03T02:07:08.123Z"))

    def test_offset_is_not_utc_z(self):
        self.assertEqual(
            classify_stamp("2026-09-03T12:07:08+10:00"), OFFSET)
        self.assertFalse(is_utc_z("2026-09-03T12:07:08+10:00"))
        self.assertNotEqual(
            classify_stamp("2026-09-03T02:07:08-00:00"), UTC_Z)

    def test_naive_local_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_stamp("2026-09-03T02:07:08")
        with self.assertRaises(FailClosedError):
            classify_stamp("2026-09-03 02:07:08")

    def test_empty_and_whitespace_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_stamp("")
        with self.assertRaises(FailClosedError):
            classify_stamp("   ")

    def test_bool_int_float_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_stamp(True)
        with self.assertRaises(FailClosedError):
            classify_stamp(1780000000)
        with self.assertRaises(FailClosedError):
            classify_stamp(1780000000.5)

    def test_impossible_civil_date_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_stamp("2026-02-30T00:00:00Z")
        with self.assertRaises(FailClosedError):
            classify_stamp("2026-13-01T00:00:00Z")
        with self.assertRaises(FailClosedError):
            classify_stamp("2026-04-31T00:00:00+10:00")

    def test_sealed_names_refused(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "Send_Authorized",
            "send-authorized",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify_stamp(name)

    def test_ready_and_authorized_stay_distinct(self):
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertFalse(ready_is_authorized())


class StructuralRefusals(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classification(self):
        self.assertFalse(halt_blocks_utc())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_classify_has_no_halt_or_now_parameter(self):
        params = inspect.signature(classify_stamp).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("halt", params)
        self.assertNotIn("now", params)
        self.assertEqual(list(params), ["value"])


if __name__ == "__main__":
    unittest.main()
