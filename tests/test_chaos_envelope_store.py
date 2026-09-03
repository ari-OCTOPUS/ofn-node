"""Owner-absent chaos — envelope-class + store-class (independent of #82).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the envelope/store layer:
no fabricated witness, no store write, no run_id mint. HALT
stops STARTS only. One arm's timeout cannot mark another arm
SUSPECTED. Recovery is a validate/replay and is still not a send.
"""

from __future__ import annotations

import unittest

from ofn.kernel.envelope_class import (
    admit_envelope,
    classify_timeout,
    grants_send as envelope_grants_send,
    halt_blocks_validate,
    mints_run_id,
    ready_is_authorized as envelope_ready_is_authorized,
    timeout_proves_concurrent as envelope_timeout_proves,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import EXECUTION_RECEIPT, RUN_CREATED
from ofn.kernel.store_class import (
    admit_store,
    grants_send as store_grants_send,
    halt_blocks_inflight_append,
    ready_is_authorized as store_ready_is_authorized,
    rewrites_ledger,
    timeout_proves_concurrent as store_timeout_proves,
)

_RUN_A = "run-1780000000-armaaaaaaa"
_RUN_B = "run-1780000000-armbbbbbbb"
_RUN_C = "run-1780000000-armccccccc"


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_envelope_activity_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_envelope(
                intended="mint", version=1, run_id=_RUN_A,
                activity="DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_store_kind_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_store(intended="append", kind="DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_validate(self):
        timed = admit_envelope(
            intended="validate", version=1, run_id=_RUN_A, timed_out=True)
        self.assertEqual(timed.status, "UNKNOWN")
        self.assertTrue(timed.allowed)
        sibling = admit_envelope(
            intended="validate", version=1, run_id=_RUN_B)
        self.assertTrue(sibling.allowed)
        self.assertEqual(sibling.status, "VERIFIED")
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(envelope_timeout_proves())
        self.assertFalse(store_timeout_proves())
        self.assertEqual(classify_timeout(), "UNKNOWN")
        d = admit_store(
            intended="append", kind=EXECUTION_RECEIPT,
            activity="concurrent", timed_out=True)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_activity")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_validate_and_inflight_append(self):
        envelopes = [
            admit_envelope(intended="validate", version=1, run_id=rid)
            for rid in (_RUN_A, _RUN_B, _RUN_C)
        ]
        stores = [
            admit_store(intended="append", kind=EXECUTION_RECEIPT)
            for _ in range(3)
        ]
        self.assertEqual(len(envelopes), 3)
        self.assertEqual(len(stores), 3)
        for d in envelopes + stores:
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_admit_is_not_a_send(self):
        first = admit_envelope(intended="replay", version=1, run_id=_RUN_A)
        second = admit_envelope(intended="replay", version=1, run_id=_RUN_A)
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        self.assertFalse(envelope_grants_send())
        self.assertFalse(store_grants_send())


class Scenario5SealedNameStopsThatRowOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_validate_continues(self):
        sealed = admit_envelope(
            intended="mint", version=1, run_id="send_authorized")
        self.assertFalse(sealed.allowed)
        self.assertEqual(sealed.reason, "sealed_effect")
        sibling = admit_envelope(
            intended="validate", version=1, run_id=_RUN_B)
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsStartOnly(unittest.TestCase):
    def test_halt_refuses_mint_and_run_created_not_validate(self):
        mint = admit_envelope(
            intended="mint", version=1, run_id=_RUN_A, halted=True)
        self.assertFalse(mint.allowed)
        self.assertEqual(mint.reason, "halt_active")
        created = admit_store(
            intended="append", kind=RUN_CREATED, halted=True)
        self.assertFalse(created.allowed)
        self.assertEqual(created.reason, "halt_start")
        validate = admit_envelope(
            intended="validate", version=1, run_id=_RUN_B, halted=True)
        self.assertTrue(validate.allowed)
        receipt = admit_store(
            intended="append", kind=EXECUTION_RECEIPT, halted=True)
        self.assertTrue(receipt.allowed)
        self.assertFalse(halt_blocks_validate())
        self.assertFalse(halt_blocks_inflight_append())
        self.assertFalse(validate.grants_send)
        self.assertFalse(receipt.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        import inspect
        for fn in (admit_envelope, admit_store):
            params = inspect.signature(fn).parameters
            self.assertNotIn("halt_raw", params)
            self.assertNotIn("send_authorized", params)
            self.assertNotIn("resend", params)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_validate_or_replay_and_not_a_send(self):
        blocked = admit_envelope(
            intended="validate", version=1, run_id="quote_sent")
        self.assertFalse(blocked.allowed)
        resumed = admit_envelope(
            intended="replay", version=1, run_id=_RUN_C)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(envelope_grants_send())
        self.assertFalse(mints_run_id())

    def test_rewrite_is_never_recovery(self):
        d = admit_store(intended="rewrite", kind=RUN_CREATED)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "rewrite_forbidden")
        self.assertFalse(rewrites_ledger())


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready_e = admit_envelope(
            intended="validate", version=1,
            run_id="campaign_envelope_ready")
        sent_e = admit_envelope(
            intended="validate", version=1, run_id="quote_sent")
        auth_e = admit_envelope(
            intended="validate", version=1, run_id="send_authorized")
        ready_s = admit_store(
            intended="append", kind="campaign_envelope_ready")
        sent_s = admit_store(intended="append", kind="quote_sent")
        auth_s = admit_store(intended="append", kind="send_authorized")
        for d in (ready_e, sent_e, auth_e, ready_s, sent_s, auth_s):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(envelope_ready_is_authorized())
        self.assertFalse(store_ready_is_authorized())
        self.assertNotEqual(ready_e.run_id, auth_e.run_id)
        self.assertNotEqual(ready_s.kind, auth_s.kind)


if __name__ == "__main__":
    unittest.main()
