"""Contract tests for the owner release switch.

The release switch is the only thing that may let real publishing out, so
its contract is the contract the whole "automated publishing" feature
stands or falls on. Every test here is a rule that must hold forever, not
a behaviour that may change: if any of these fails, automated publishing
is unsafe and must not ship.

The shape of every test is the same: build an all-green context, flip one
field to its bad value with dataclasses.replace, assert the switch refuses
and names the rule.
"""

import dataclasses
import itertools
import unittest

from ofn.kernel.release_switch import (
    OwnerRelease, ReleaseContext, RULE_KILL, RULE_OWNER_TWO_STEP,
    RULE_SECRET_ROTATION, RULE_PARTNER_PRECONDITION, RULE_RESTRICTED,
    RULE_CONSENT, RULE_PLATFORM, RULE_RATE_LIMIT, RULE_IDEMPOTENCY,
    RULE_LEDGER, RULE_OK,
)


def _green() -> ReleaseContext:
    """The all-green context: every field set to 'allowed'."""
    return ReleaseContext(
        owner_confirmed_step1=True,
        owner_confirmed_step2=True,
        secret_rotation_open=True,
        partner_precondition_open=True,
        kill_switch_active=False,
        sensitivity="general",
        consent_ok=True,
        platform_ok=True,
        rate_limit_ok=True,
        idempotency_unused=True,
        ledger_ready=True,
    )


def _bad(**changes) -> ReleaseContext:
    """All-green with the given fields flipped to their bad values."""
    return dataclasses.replace(_green(), **changes)


class TestOwnerRelease(unittest.TestCase):
    def setUp(self):
        self.sw = OwnerRelease()

    def test_all_green_allows_and_is_still_red(self):
        v = self.sw.may_publish(_green())
        self.assertTrue(v.ok)
        self.assertEqual(v.rule, RULE_OK)
        # Publishing is always RED; permission is not safety.
        self.assertEqual(v.risk, "RED")

    def test_kill_switch_wins_over_everything(self):
        v = self.sw.may_publish(_bad(kill_switch_active=True))
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, RULE_KILL)

    def test_one_step_is_not_enough(self):
        v = self.sw.may_publish(_bad(owner_confirmed_step2=False))
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, RULE_OWNER_TWO_STEP)

    def test_closed_secret_rotation_blocks(self):
        v = self.sw.may_publish(_bad(secret_rotation_open=False))
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, RULE_SECRET_ROTATION)

    def test_closed_partner_precondition_blocks(self):
        v = self.sw.may_publish(_bad(partner_precondition_open=False))
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, RULE_PARTNER_PRECONDITION)

    def test_restricted_never_leaves_even_when_owner_says_yes(self):
        v = self.sw.may_publish(_bad(sensitivity="restricted"))
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, RULE_RESTRICTED)

    def test_bad_consent_blocks(self):
        v = self.sw.may_publish(_bad(consent_ok=False))
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, RULE_CONSENT)

    def test_failed_platform_screen_blocks(self):
        v = self.sw.may_publish(_bad(platform_ok=False))
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, RULE_PLATFORM)

    def test_rate_limit_blocks(self):
        v = self.sw.may_publish(_bad(rate_limit_ok=False))
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, RULE_RATE_LIMIT)

    def test_used_idempotency_key_blocks(self):
        v = self.sw.may_publish(_bad(idempotency_unused=False))
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, RULE_IDEMPOTENCY)

    def test_ledger_not_ready_blocks(self):
        v = self.sw.may_publish(_bad(ledger_ready=False))
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, RULE_LEDGER)


class TestNoPathBypassesTwoStep(unittest.TestCase):
    """No field combination publishes with only one owner step."""

    def test_every_single_field_off_still_refuses(self):
        sw = OwnerRelease()
        bool_fields = ["secret_rotation_open", "partner_precondition_open",
                       "consent_ok", "platform_ok", "rate_limit_ok",
                       "idempotency_unused", "ledger_ready"]
        for combo in itertools.product([True, False], repeat=len(bool_fields)):
            kwargs = dict(zip(bool_fields, combo))
            ctx = ReleaseContext(
                owner_confirmed_step1=True,
                owner_confirmed_step2=False,
                kill_switch_active=False,
                sensitivity="general",
                **kwargs,
            )
            v = sw.may_publish(ctx)
            self.assertFalse(v.ok, f"published with one step off: {combo}")


if __name__ == "__main__":
    unittest.main()
