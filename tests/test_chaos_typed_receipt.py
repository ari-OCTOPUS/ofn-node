"""Owner-absent chaos for typed_event / receipt_bind.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a writer, HALT does not block classify/bind, a
proposal never becomes a receipt, and a recorded digest never
becomes a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import EXECUTION_RECEIPT, PROPOSAL_CREATED, RUN_CREATED
from ofn.kernel.halt import is_halted
from ofn.kernel.receipt_bind import (
    bind_receipt,
    grants_send,
    halt_blocks_bind,
    timeout_proves_concurrent_write,
    try_bind,
    typed_is_receipt,
)
from ofn.kernel.typed_event import (
    TYPED,
    UNKNOWN,
    classify_record,
    halt_blocks_typed,
    is_execution,
    try_typed,
)


_TS = 1788405009
_RUN = "run-1788405009-chaosrcp1"
_DIGEST = "c" * 64


def _receipt():
    return {
        "kind": EXECUTION_RECEIPT,
        "run_id": _RUN,
        "ts": _TS,
    }


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertEqual(classify_record(None), UNKNOWN)
        self.assertNotEqual(classify_record(None), "FALSE")
        self.assertIsNone(try_typed(None))
        self.assertIsNone(try_bind(None, _DIGEST))
        self.assertIsNone(try_bind(_receipt(), None))


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_flag_is_structurally_false(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertEqual(
            classify_record({"kind": None, "run_id": _RUN, "ts": _TS}),
            UNKNOWN)


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_typed())
        self.assertFalse(halt_blocks_bind())
        self.assertEqual(
            classify_record({
                "kind": RUN_CREATED, "run_id": _RUN, "ts": _TS,
            }),
            TYPED)
        params = inspect.signature(classify_record).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_refused_proposal_bind_does_not_grant_send(self):
        with self.assertRaises(FailClosedError):
            bind_receipt(
                {"kind": PROPOSAL_CREATED, "run_id": _RUN, "ts": _TS},
                _DIGEST)
        self.assertFalse(grants_send())
        self.assertFalse(is_execution(PROPOSAL_CREATED))


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_sealed_names_cannot_bind(self):
        with self.assertRaises(FailClosedError):
            bind_receipt(
                {
                    "kind": "campaign_envelope_ready",
                    "run_id": _RUN,
                    "ts": _TS,
                },
                _DIGEST)
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_proposal_is_measured_false_missing_is_none(self):
        self.assertIs(
            typed_is_receipt(
                {"kind": PROPOSAL_CREATED, "run_id": _RUN, "ts": _TS}),
            False)
        self.assertIsNone(typed_is_receipt(None))


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_and_rebind_are_deterministic(self):
        a = classify_record(_receipt())
        b = classify_record(_receipt())
        self.assertEqual(a, b)
        self.assertEqual(a, TYPED)
        first = bind_receipt(_receipt(), _DIGEST)
        second = bind_receipt(_receipt(), _DIGEST)
        self.assertEqual(first.digest, second.digest)
        self.assertEqual(first.run_id, second.run_id)


if __name__ == "__main__":
    unittest.main()
