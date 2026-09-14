"""Encode pin — complementary to codec_class / receipts / typed_event.

A pinned codec is not a send. Peek never writes. Missing is
UNKNOWN (None), not FALSE. Ready is not authorized.
"""

from __future__ import annotations

import unittest

from ofn.kernel.encode_pin import (
    EncodePin,
    admit_then_pin,
    claims_immutable,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    pin_allows_encode,
    pin_allows_send,
    pin_family,
    pin_ready_stays_ready,
    produces_encoded_bytes,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError

_RUN = "run-1780000000-abcdefghij"
_RUN_B = "run-1780000000-bbbbbbbbbb"


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())
        self.assertFalse(pin_allows_send())

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertTrue(pin_ready_stays_ready())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_timeout_does_not_prove_write(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_later_disarm_supersedes(self):
        self.assertTrue(later_disarm_supersedes())

    def test_does_not_produce_encoded_bytes(self):
        self.assertFalse(produces_encoded_bytes())


class FamilyAndAllow(unittest.TestCase):
    def test_known_families(self):
        self.assertEqual(pin_family("utf8"), "text")
        self.assertEqual(pin_family("hex"), "digest")
        self.assertEqual(pin_family("ascii"), "seven_bit")

    def test_unknown_codec_family_is_none_not_false(self):
        self.assertIsNone(pin_family("latin1"))
        self.assertIsNone(pin_family(None))
        self.assertIsNot(pin_family("latin1"), False)

    def test_sealed_name_is_not_a_family(self):
        with self.assertRaises(FailClosedError):
            pin_family("send_authorized")
        with self.assertRaises(FailClosedError):
            pin_family("campaign_envelope_ready")

    def test_pin_allows_encode_known_only(self):
        self.assertTrue(pin_allows_encode("utf8"))
        self.assertTrue(pin_allows_encode("hex"))
        self.assertTrue(pin_allows_encode("ascii"))
        self.assertFalse(pin_allows_encode("latin1"))
        self.assertFalse(pin_allows_encode(None))
        self.assertFalse(pin_allows_encode("send_authorized"))
        self.assertFalse(pin_allows_encode("campaign_envelope_ready"))


class PinMap(unittest.TestCase):
    def test_first_pin_and_peek(self):
        pin = EncodePin()
        self.assertIsNone(pin.peek(_RUN))
        self.assertEqual(pin.pin(_RUN, "utf8"), "pinned")
        self.assertEqual(pin.peek(_RUN), "utf8")
        self.assertFalse(grants_send())

    def test_same_pair_already_pinned(self):
        pin = EncodePin()
        self.assertEqual(pin.pin(_RUN, "hex"), "pinned")
        self.assertEqual(pin.pin(_RUN, "hex"), "already_pinned")
        self.assertEqual(pin.peek(_RUN), "hex")

    def test_codec_conflict(self):
        pin = EncodePin()
        pin.pin(_RUN, "utf8")
        with self.assertRaises(FailClosedError) as ctx:
            pin.pin(_RUN, "ascii")
        self.assertIn("codec_conflict", str(ctx.exception))
        self.assertEqual(pin.peek(_RUN), "utf8")

    def test_sibling_run_independent(self):
        pin = EncodePin()
        pin.pin(_RUN, "utf8")
        self.assertEqual(pin.pin(_RUN_B, "ascii"), "pinned")
        self.assertEqual(pin.peek(_RUN), "utf8")
        self.assertEqual(pin.peek(_RUN_B), "ascii")

    def test_timeout_is_unknown_not_a_pin(self):
        pin = EncodePin()
        with self.assertRaises(FailClosedError) as ctx:
            pin.pin(_RUN, "utf8", timeout=True)
        self.assertIn("UNKNOWN", str(ctx.exception))
        self.assertIsNone(pin.peek(_RUN))

    def test_try_pin_timeout_returns_none(self):
        pin = EncodePin()
        self.assertIsNone(pin.try_pin(_RUN, "utf8", timeout=True))
        self.assertIsNone(pin.peek(_RUN))

    def test_try_pin_missing_codec_is_none(self):
        pin = EncodePin()
        self.assertIsNone(pin.try_pin(_RUN, None))
        self.assertIsNone(pin.peek(_RUN))

    def test_bad_run_id_fails_closed(self):
        pin = EncodePin()
        with self.assertRaises(FailClosedError):
            pin.pin("not-a-run", "utf8")
        with self.assertRaises(FailClosedError):
            pin.pin("send_authorized", "utf8")

    def test_sealed_codec_fails_closed(self):
        pin = EncodePin()
        with self.assertRaises(FailClosedError):
            pin.pin(_RUN, "quote_sent")
        with self.assertRaises(FailClosedError):
            pin.pin(_RUN, "campaign_envelope_ready")

    def test_unknown_codec_fails_closed_not_false(self):
        pin = EncodePin()
        with self.assertRaises(FailClosedError) as ctx:
            pin.pin(_RUN, "latin1")
        self.assertNotIn("FALSE", str(ctx.exception))


class AdmitThenPin(unittest.TestCase):
    def test_granted_encode_pins(self):
        pin = EncodePin()
        result = admit_then_pin(
            run_id=_RUN, intended="encode", codec="utf8",
            payload="body", pin=pin)
        self.assertEqual(result, "pinned")
        self.assertEqual(pin.peek(_RUN), "utf8")

    def test_inspect_does_not_pin(self):
        pin = EncodePin()
        result = admit_then_pin(
            run_id=_RUN, intended="inspect", codec="utf8",
            payload="body", pin=pin)
        self.assertIsNone(result)
        self.assertIsNone(pin.peek(_RUN))

    def test_halted_encode_does_not_pin(self):
        pin = EncodePin()
        result = admit_then_pin(
            run_id=_RUN, intended="encode", codec="utf8",
            payload="body", pin=pin, halted=True)
        self.assertIsNone(result)
        self.assertIsNone(pin.peek(_RUN))

    def test_timeout_encode_does_not_pin(self):
        pin = EncodePin()
        result = admit_then_pin(
            run_id=_RUN, intended="encode", codec="utf8",
            payload="body", pin=pin, timed_out=True)
        self.assertIsNone(result)
        self.assertIsNone(pin.peek(_RUN))

    def test_sealed_name_fails_closed(self):
        pin = EncodePin()
        with self.assertRaises(FailClosedError):
            admit_then_pin(
                run_id=_RUN, intended="encode",
                codec="send_authorized", payload="body", pin=pin)
        self.assertIsNone(pin.peek(_RUN))


if __name__ == "__main__":
    unittest.main()
