"""Owner-absent chaos for scope_class / limit_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a concurrent writer, HALT stops start and lets
inspect / classify continue, and a recorded pair never becomes a
send. Seven scenarios, same shape as tests/test_chaos_owner_absent.py.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.limit_pin import (
    LIMITED,
    grants_send as pin_grants_send,
    halt_blocks_pin,
    later_disarm_supersedes as pin_later_disarm,
    peek_limit,
    pin_allows_send,
    pin_limit,
    retcon_refused,
    timeout_proves_concurrent_write as pin_timeout_proves,
)
from ofn.kernel.scope_class import (
    UNKNOWN,
    admit_scope,
    bind_scope,
    classify_action,
    classify_timeout,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inspect,
    halt_blocks_start,
    later_disarm_supersedes,
    pair_matches,
    timeout_proves_concurrent_write,
    try_bind,
)


_RUN = "run-1780000000-abcdefghij"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_action_is_unknown(self):
        self.assertEqual(classify_action(None), UNKNOWN)
        self.assertNotEqual(classify_action(None), "FALSE")

    def test_missing_bind_is_none(self):
        self.assertIsNone(try_bind(None, _RUN))
        self.assertIsNone(try_bind("inspect", None))
        self.assertIsNone(peek_limit({}, _RUN))
        self.assertIsNone(admit_scope(None, halted=False))


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_predicate_is_structurally_false(self):
        self.assertEqual(classify_timeout(), UNKNOWN)
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertFalse(pin_timeout_proves())

    def test_a_timeout_error_is_not_a_bind(self):
        self.assertIsNone(try_bind(None, None))
        self.assertFalse(timeout_proves_concurrent_write())


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_inspect())
        self.assertTrue(halt_blocks_start())
        self.assertFalse(halt_blocks_pin())
        self.assertIs(admit_scope("inspect", halted=True), True)
        self.assertIs(admit_scope("start", halted=True), False)
        params = inspect.signature(classify_action).parameters
        self.assertNotIn("halted", params)
        pin_params = inspect.signature(pin_limit).parameters
        self.assertNotIn("halted", pin_params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_failed_bind_does_not_grant_send(self):
        with self.assertRaises(FailClosedError):
            bind_scope("inspect", "run-1-x")
        self.assertFalse(grants_send())
        self.assertFalse(pin_grants_send())


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_sealed_names_cannot_be_actions(self):
        for name in (
            "campaign_envelope_ready",
            "send_authorized",
            "quote_sent",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    bind_scope(name, _RUN)
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertFalse(pin_allows_send(bind_scope("start", _RUN)))


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_disagreeing_pair_is_false_missing_is_none(self):
        self.assertIs(pair_matches("inspect", _RUN, "inspect"), True)
        self.assertIs(pair_matches("inspect", _RUN, "start"), False)
        self.assertIsNone(pair_matches(None, _RUN, "inspect"))
        table: dict[str, str] = {}
        pin_limit(table, bind_scope("inspect", _RUN))
        self.assertIs(retcon_refused(table, bind_scope("classify", _RUN)), True)
        self.assertIsNone(retcon_refused({}, bind_scope("inspect", _RUN)))


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_rebind_and_repin_are_deterministic(self):
        a = bind_scope("classify", _RUN)
        b = bind_scope("classify", _RUN)
        self.assertEqual(a, b)
        table: dict[str, str] = {}
        self.assertEqual(pin_limit(table, a), LIMITED)
        self.assertEqual(pin_limit(table, b), "already_limited")
        self.assertEqual(peek_limit(table, _RUN), "classify")
        self.assertTrue(later_disarm_supersedes())
        self.assertTrue(pin_later_disarm())


if __name__ == "__main__":
    unittest.main()
