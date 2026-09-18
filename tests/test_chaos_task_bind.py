"""Owner-absent chaos for task_bind / intent_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a concurrent writer, HALT does not block a bind,
and a recorded pair never becomes a send. Seven scenarios, same
shape as tests/test_chaos_owner_absent.py.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.intent_pin import (
    PINNED,
    grants_send as pin_grants_send,
    halt_blocks_pin,
    peek_pin,
    pin_allows_send,
    pin_intent,
    retcon_refused,
    timeout_proves_concurrent_write as pin_timeout_proves,
)
from ofn.kernel.task_bind import (
    UNKNOWN,
    bind_task,
    classify_intent,
    classify_timeout,
    grants_send,
    halt_blocks_bind,
    pair_matches,
    timeout_proves_concurrent_write,
    try_bind,
)


_RUN = "run-1780000000-abcdefghij"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_intent_is_unknown(self):
        self.assertEqual(classify_intent(None), UNKNOWN)
        self.assertNotEqual(classify_intent(None), "FALSE")

    def test_missing_bind_is_none(self):
        self.assertIsNone(try_bind(None, _RUN))
        self.assertIsNone(try_bind("mint", None))
        self.assertIsNone(peek_pin({}, _RUN))


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_predicate_is_structurally_false(self):
        self.assertEqual(classify_timeout(), UNKNOWN)
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertFalse(pin_timeout_proves())

    def test_a_timeout_error_is_not_a_bind(self):
        self.assertIsNone(try_bind(None, None))
        self.assertFalse(timeout_proves_concurrent_write())


class Scenario3HaltStopsStartsNotBind(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_bind_still_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_bind())
        self.assertFalse(halt_blocks_pin())
        bound = bind_task("mint", _RUN)
        self.assertEqual(bound.intent, "mint")
        params = inspect.signature(bind_task).parameters
        self.assertNotIn("halted", params)
        pin_params = inspect.signature(pin_intent).parameters
        self.assertNotIn("halted", pin_params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_failed_bind_does_not_grant_send(self):
        with self.assertRaises(FailClosedError):
            bind_task("mint", "run-1-x")
        self.assertFalse(grants_send())
        self.assertFalse(pin_grants_send())


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_sealed_names_cannot_be_intents(self):
        for name in (
            "campaign_envelope_ready",
            "send_authorized",
            "quote_sent",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    bind_task(name, _RUN)
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertFalse(pin_allows_send(bind_task("mint", _RUN)))


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_disagreeing_pair_is_false_missing_is_none(self):
        self.assertIs(pair_matches("mint", _RUN, "mint"), True)
        self.assertIs(pair_matches("mint", _RUN, "validate"), False)
        self.assertIsNone(pair_matches(None, _RUN, "mint"))
        table: dict[str, str] = {}
        pin_intent(table, bind_task("mint", _RUN))
        self.assertIs(retcon_refused(table, bind_task("validate", _RUN)), True)
        self.assertIsNone(retcon_refused({}, bind_task("mint", _RUN)))


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_rebind_and_repin_are_deterministic(self):
        a = bind_task("replay", _RUN)
        b = bind_task("replay", _RUN)
        self.assertEqual(a, b)
        table: dict[str, str] = {}
        self.assertEqual(pin_intent(table, a), PINNED)
        self.assertEqual(pin_intent(table, b), "already_pinned")
        self.assertEqual(peek_pin(table, _RUN), "replay")


if __name__ == "__main__":
    unittest.main()
