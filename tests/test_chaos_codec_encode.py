"""Owner-absent chaos — codec-class + encode-pin (independent of #82).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the codec/encode layer:
no fabricated witness, no store write, no encoded bytes. HALT
stops STARTS only. One arm's timeout cannot mark another arm
SUSPECTED. Recovery is an inspect/replay and is still not a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.codec_class import (
    admit_codec,
    classify_timeout,
    encodes_bytes,
    grants_send as codec_grants_send,
    halt_blocks_inspect,
    ready_is_authorized as codec_ready_is_authorized,
    timeout_proves_concurrent as codec_timeout_proves,
)
from ofn.kernel.encode_pin import (
    EncodePin,
    grants_send as pin_grants_send,
    pin_allows_send,
    ready_is_authorized as pin_ready_is_authorized,
    timeout_proves_concurrent_write as pin_timeout_proves,
)
from ofn.kernel.errors import FailClosedError

_PAY_A = "arm-a-body"
_PAY_B = "arm-b-body"
_PAY_C = "arm-c-body"
_RUN_A = "run-1780000000-armaaaaaaa"
_RUN_B = "run-1780000000-armbbbbbbb"
_RUN_C = "run-1780000000-armccccccc"


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_codec_activity_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_codec(
                intended="encode", codec="utf8", payload=_PAY_A,
                activity="DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_codec_name_is_refused_not_false(self):
        d = admit_codec(intended="encode", codec="DEAD_SOURCE", payload=_PAY_A)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_codec")
        self.assertNotEqual(d.reason, "FALSE")


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_inspect(self):
        timed = admit_codec(
            intended="inspect", codec="utf8", payload=_PAY_A,
            timed_out=True)
        self.assertEqual(timed.status, "UNKNOWN")
        self.assertTrue(timed.allowed)
        sibling = admit_codec(
            intended="inspect", codec="utf8", payload=_PAY_B)
        self.assertTrue(sibling.allowed)
        self.assertEqual(sibling.status, "VERIFIED")
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(codec_timeout_proves())
        self.assertFalse(pin_timeout_proves())
        self.assertEqual(classify_timeout(), "UNKNOWN")
        d = admit_codec(
            intended="encode", codec="hex", payload="ab",
            activity="concurrent", timed_out=True)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_activity")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_inspect_and_pin_independently(self):
        inspects = [
            admit_codec(intended="inspect", codec="utf8", payload=p)
            for p in (_PAY_A, _PAY_B, _PAY_C)
        ]
        pin = EncodePin()
        pins = [
            pin.pin(rid, "utf8")
            for rid in (_RUN_A, _RUN_B, _RUN_C)
        ]
        self.assertEqual(len(inspects), 3)
        self.assertEqual(pins, ["pinned", "pinned", "pinned"])
        for d in inspects:
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)
        self.assertFalse(pin_grants_send())
        self.assertFalse(pin_allows_send())


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_admit_is_not_a_send(self):
        first = admit_codec(intended="replay", codec="ascii", payload=_PAY_A)
        second = admit_codec(intended="replay", codec="ascii", payload=_PAY_A)
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        self.assertFalse(codec_grants_send())
        pin = EncodePin()
        self.assertEqual(pin.pin(_RUN_A, "ascii"), "pinned")
        self.assertEqual(pin.pin(_RUN_A, "ascii"), "already_pinned")
        self.assertFalse(pin_grants_send())


class Scenario5SealedNameStopsThatRowOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_inspect_continues(self):
        sealed = admit_codec(
            intended="encode", codec="send_authorized", payload=_PAY_A)
        self.assertFalse(sealed.allowed)
        self.assertEqual(sealed.reason, "sealed_effect")
        sibling = admit_codec(
            intended="inspect", codec="utf8", payload=_PAY_B)
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsStartOnly(unittest.TestCase):
    def test_halt_refuses_encode_not_inspect(self):
        encoded = admit_codec(
            intended="encode", codec="utf8", payload=_PAY_A, halted=True)
        self.assertFalse(encoded.allowed)
        self.assertEqual(encoded.reason, "halt_active")
        inspect = admit_codec(
            intended="inspect", codec="utf8", payload=_PAY_B, halted=True)
        self.assertTrue(inspect.allowed)
        replay = admit_codec(
            intended="replay", codec="hex", payload="cd", halted=True)
        self.assertTrue(replay.allowed)
        self.assertFalse(halt_blocks_inspect())
        self.assertFalse(inspect.grants_send)
        self.assertFalse(replay.grants_send)
        self.assertFalse(encodes_bytes())

    def test_no_halt_knob_to_rearm_send(self):
        params = inspect.signature(admit_codec).parameters
        self.assertNotIn("halt_raw", params)
        self.assertNotIn("send_authorized", params)
        self.assertNotIn("resend", params)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_an_inspect_or_replay_and_not_a_send(self):
        blocked = admit_codec(
            intended="inspect", codec="quote_sent", payload=_PAY_A)
        self.assertFalse(blocked.allowed)
        resumed = admit_codec(
            intended="replay", codec="utf8", payload=_PAY_C)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(codec_grants_send())
        self.assertFalse(encodes_bytes())


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready = admit_codec(
            intended="inspect", codec="campaign_envelope_ready",
            payload=_PAY_A)
        sent = admit_codec(
            intended="inspect", codec="quote_sent", payload=_PAY_A)
        auth = admit_codec(
            intended="inspect", codec="send_authorized", payload=_PAY_A)
        for d in (ready, sent, auth):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(codec_ready_is_authorized())
        self.assertFalse(pin_ready_is_authorized())
        self.assertNotEqual(ready.codec, auth.codec)


if __name__ == "__main__":
    unittest.main()
