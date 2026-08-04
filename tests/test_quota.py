"""Token quota: ceilings, the invisible-spend multiplier, and fail-closed behaviour."""

from __future__ import annotations

import unittest

from ofn.kernel.domain import TenantId, TokenSpend
from ofn.kernel.errors import FailClosedError, UnknownTenantError
from ofn.kernel.quota import (
    DEFAULT_ORCHESTRATION_MULTIPLIER, NodeQuota, WEEK_SECONDS, week_index,
)

WEEK0 = 0
WEEK1 = WEEK_SECONDS + 10


def quota(capacity=1_000_000, utilisation=0.40, **kw) -> NodeQuota:
    shares = kw.pop("shares", {"alpha": 0.40, "bravo": 0.40, "charlie": 0.20})
    return NodeQuota(estimated_capacity_tokens=capacity, utilisation=utilisation,
                     shares=shares, **kw)


class TestConstruction(unittest.TestCase):
    def test_rejects_nonpositive_capacity(self):
        with self.assertRaises(FailClosedError):
            quota(capacity=0)

    def test_rejects_utilisation_out_of_range(self):
        with self.assertRaises(FailClosedError):
            quota(utilisation=0.0)
        with self.assertRaises(FailClosedError):
            quota(utilisation=1.5)

    def test_rejects_shares_over_one(self):
        with self.assertRaises(FailClosedError):
            quota(shares={"alpha": 0.7, "bravo": 0.7})

    def test_rejects_multiplier_below_one(self):
        """A multiplier under 1.0 would under-count billed spend by construction."""
        with self.assertRaises(FailClosedError):
            quota(orchestration_multiplier=0.5)

    def test_shares_may_sum_below_one(self):
        q = quota(shares={"alpha": 0.3})
        self.assertEqual(q.tenant_ceiling("alpha"), int(q.node_ceiling * 0.3))


class TestCeilings(unittest.TestCase):
    def test_node_ceiling_applies_utilisation(self):
        q = quota(capacity=1_000_000, utilisation=0.40)
        self.assertEqual(q.node_ceiling, 400_000)

    def test_tenant_ceiling_is_a_share_of_the_node_ceiling(self):
        q = quota(capacity=1_000_000, utilisation=0.40)
        self.assertEqual(q.tenant_ceiling("alpha"), 160_000)
        self.assertEqual(q.tenant_ceiling("charlie"), 80_000)

    def test_unknown_tenant_ceiling_raises(self):
        with self.assertRaises(UnknownTenantError):
            quota().tenant_ceiling("zulu")


class TestInvisibleSpend(unittest.TestCase):
    """The provider bills for orchestration it does not echo back."""

    def test_unreported_orchestration_is_multiplied_not_assumed_zero(self):
        q = quota()
        cost = q.effective_cost(TokenSpend(visible=1000))
        self.assertEqual(cost, int(round(1000 * DEFAULT_ORCHESTRATION_MULTIPLIER)))
        self.assertGreater(cost, 1000)

    def test_reported_orchestration_is_trusted_over_the_multiplier(self):
        q = quota()
        self.assertEqual(q.effective_cost(TokenSpend(visible=1000, orchestration=9000)),
                         10_000)

    def test_admission_and_accounting_use_the_same_number(self):
        """A call admitted at the visible figure but booked at the billed figure
        would silently overrun. Both paths must inflate identically."""
        q = quota(capacity=100_000, utilisation=1.0, shares={"alpha": 1.0})
        est = 30_000                       # billed as 30k x 2.6 = 78k
        self.assertTrue(q.check("alpha", est, WEEK0).allowed)
        booked = q.record("alpha", TokenSpend(visible=est), WEEK0)
        self.assertEqual(booked, 78_000)
        self.assertEqual(booked, q.effective_cost(TokenSpend(visible=est)))
        # A second identical call must now be refused: 2 x 78k > 100k, even
        # though 2 x 30k of *visible* tokens would have looked affordable.
        self.assertFalse(q.check("alpha", est, WEEK0).allowed)
        self.assertLess(2 * est, q.node_ceiling)   # the trap this guards against

    def test_negative_tokens_rejected(self):
        with self.assertRaises(ValueError):
            TokenSpend(visible=-1)


class TestFailClosed(unittest.TestCase):
    def test_node_exhaustion_stops_every_tenant(self):
        """Not just the heaviest consumer — all of them.

        Both legs spend their full share, so the node total is exhausted while
        neither has individually misbehaved. Everyone stops.
        """
        q = quota(capacity=100_000, utilisation=1.0,
                  shares={"alpha": 0.5, "bravo": 0.5}, orchestration_multiplier=1.0)
        q.record("alpha", TokenSpend(visible=50_000), WEEK0)
        q.record("bravo", TokenSpend(visible=50_000), WEEK0)
        for tenant in ("alpha", "bravo"):
            with self.subTest(tenant=tenant):
                d = q.check(tenant, 1, WEEK0)
                self.assertFalse(d.allowed)
                self.assertEqual(d.rule, "quota:node-ceiling")

    def test_tenant_share_exhaustion_does_not_stop_others(self):
        q = quota(capacity=100_000, utilisation=1.0,
                  shares={"alpha": 0.5, "bravo": 0.5}, orchestration_multiplier=1.0)
        q.record("alpha", TokenSpend(visible=50_000), WEEK0)
        self.assertFalse(q.check("alpha", 1, WEEK0).allowed)
        self.assertTrue(q.check("bravo", 1, WEEK0).allowed)

    def test_unknown_tenant_is_denied_not_defaulted(self):
        d = quota().check("zulu", 10, WEEK0)
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule, "quota:unknown-tenant")

    def test_negative_estimate_denied(self):
        d = quota().check("alpha", -5, WEEK0)
        self.assertFalse(d.allowed)

    def test_recording_an_overrun_still_books_it(self):
        """Pretending an overrun did not happen would corrupt the next check."""
        q = quota(capacity=1000, utilisation=1.0, shares={"alpha": 1.0},
                  orchestration_multiplier=1.0)
        q.record("alpha", TokenSpend(visible=5000), WEEK0)
        self.assertEqual(q.spent(WEEK0, "alpha"), 5000)
        self.assertFalse(q.check("alpha", 1, WEEK0).allowed)

    def test_record_for_unknown_tenant_raises(self):
        with self.assertRaises(UnknownTenantError):
            quota().record("zulu", TokenSpend(visible=1), WEEK0)


class TestWeeklyWindows(unittest.TestCase):
    def test_week_index_buckets(self):
        self.assertEqual(week_index(0), 0)
        self.assertEqual(week_index(WEEK_SECONDS - 1), 0)
        self.assertEqual(week_index(WEEK_SECONDS), 1)

    def test_negative_time_fails_closed(self):
        with self.assertRaises(FailClosedError):
            week_index(-1)

    def test_spend_resets_next_week(self):
        q = quota(capacity=100_000, utilisation=1.0, shares={"alpha": 1.0},
                  orchestration_multiplier=1.0)
        q.record("alpha", TokenSpend(visible=100_000), WEEK0)
        self.assertFalse(q.check("alpha", 1, WEEK0).allowed)
        self.assertTrue(q.check("alpha", 1, WEEK1).allowed)
        self.assertEqual(q.spent(WEEK1, "alpha"), 0)

    def test_remaining_is_the_smaller_of_both_ceilings(self):
        q = quota(capacity=100_000, utilisation=1.0,
                  shares={"alpha": 0.9, "bravo": 0.1}, orchestration_multiplier=1.0)
        q.record("bravo", TokenSpend(visible=95_000), WEEK0)
        # alpha's own ceiling is 90k, but only 5k of node headroom is left.
        self.assertEqual(q.remaining(WEEK0, "alpha"), 5_000)

    def test_remaining_never_negative(self):
        q = quota(capacity=1000, utilisation=1.0, shares={"alpha": 1.0},
                  orchestration_multiplier=1.0)
        q.record("alpha", TokenSpend(visible=9999), WEEK0)
        self.assertEqual(q.remaining(WEEK0, "alpha"), 0)


class TestCalibration(unittest.TestCase):
    def test_starts_flagged_as_an_estimate(self):
        self.assertTrue(quota().capacity_is_estimate)

    def test_calibration_reapplies_the_fraction_to_reality(self):
        q = quota(capacity=1_000_000, utilisation=0.40)
        self.assertEqual(q.node_ceiling, 400_000)
        q.calibrate(2_000_000)          # the plan was twice what we guessed
        self.assertEqual(q.node_ceiling, 800_000)
        self.assertFalse(q.capacity_is_estimate)

    def test_calibration_downward_tightens_immediately(self):
        q = quota(capacity=1_000_000, utilisation=0.40)
        q.calibrate(500_000)
        self.assertEqual(q.node_ceiling, 200_000)

    def test_calibration_rejects_nonsense(self):
        with self.assertRaises(FailClosedError):
            quota().calibrate(0)


class TestSnapshot(unittest.TestCase):
    def test_snapshot_reports_estimate_flag_and_totals(self):
        q = quota(capacity=1_000_000, utilisation=0.40)
        q.record("alpha", TokenSpend(visible=1000, orchestration=1600), WEEK0)
        snap = q.snapshot(WEEK0)
        self.assertTrue(snap["capacity_is_estimate"])
        self.assertEqual(snap["node_ceiling"], 400_000)
        self.assertEqual(snap["node_spent"], 2600)
        self.assertEqual(snap["calls"], 1)
        self.assertEqual(snap["tenants"]["alpha"]["spent"], 2600)
        self.assertEqual(sorted(snap["tenants"]), ["alpha", "bravo", "charlie"])


if __name__ == "__main__":
    unittest.main()
