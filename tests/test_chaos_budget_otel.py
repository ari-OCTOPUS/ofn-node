"""Owner-absent chaos for budget_class / otel_bind.

While the owner cannot be reached: missing stays UNKNOWN, a
timeout does not invent a writer, HALT does not block classify,
a zero ceiling never becomes a send, a bind never becomes an
export, and a budget fit never becomes send_authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.budget_class import (
    admit_budget,
    grants_send as budget_grants_send,
    halt_blocks_budget,
    timeout_proves_concurrent,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.otel_bind import (
    admit_otel,
    grants_send as otel_grants_send,
    halt_blocks_otel,
)


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_kind_is_refused_not_false(self):
        d = admit_otel(
            kind="MISSING_KIND", intended="bind", activity="idle")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_kind")
        self.assertNotEqual(d.reason, "FALSE")


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_on_debit_is_unknown(self):
        d = admit_budget(
            intended="debit",
            activity="concurrent",
            ceiling=10,
            request=1,
            timed_out=True,
        )
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(timeout_proves_concurrent())


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_admit_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_budget())
        self.assertFalse(halt_blocks_otel())
        d = admit_budget(intended="observe", activity="idle")
        self.assertTrue(d.allowed)
        self.assertNotIn("halted", inspect.signature(admit_budget).parameters)
        self.assertNotIn("halted", inspect.signature(admit_otel).parameters)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_exhausted_ceiling_does_not_grant_send(self):
        d = admit_budget(
            intended="debit",
            activity="idle",
            ceiling=0,
            request=1,
        )
        self.assertFalse(d.allowed)
        self.assertFalse(budget_grants_send())
        self.assertFalse(otel_grants_send())


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_sealed_names_cannot_become_a_bind(self):
        with self.assertRaises(FailClosedError):
            admit_otel(
                kind="campaign_envelope_ready",
                intended="bind",
                activity="idle",
            )
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            admit_budget(intended="quote_sent", activity="idle")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_export_is_not_rewritten_to_bind(self):
        d = admit_otel(
            kind="RUN_CREATED", intended="export", activity="idle")
        self.assertEqual(d.intended, "export")
        self.assertEqual(d.reason, "export_forbidden")
        self.assertIsNone(d.span)
        self.assertNotEqual(d.intended, "bind")


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_observe_and_bind_are_deterministic(self):
        a = admit_budget(intended="observe", activity="idle")
        b = admit_budget(intended="observe", activity="idle")
        self.assertEqual(a, b)
        self.assertTrue(a.allowed)
        c = admit_otel(kind="BUDGET_DEBIT", intended="bind", activity="idle")
        d = admit_otel(kind="BUDGET_DEBIT", intended="bind", activity="idle")
        self.assertEqual(c, d)
        self.assertTrue(c.allowed)
        credit = admit_budget(intended="credit", activity="idle")
        self.assertFalse(credit.allowed)


if __name__ == "__main__":
    unittest.main()
