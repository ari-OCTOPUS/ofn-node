"""Subscribers, money, and ownership — the three numbers no tool gives.

Every figure the research document called "must be measured" is an assertion
here rather than a sentence, per CLAUDE.md §8-الف.

The load-bearing test in this file is cohort maturity. First-window
conversion counted over everybody falls every time a new subscriber arrives —
so a growing business reads as a failing one, and the number is at its worst
exactly when things are going best. A subscriber who joined yesterday has not
failed to convert in seven days; they have not had seven days.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from ofn.adapters.audience_store import AudienceError, AudienceStore
from ofn.kernel.audience import (
    DAY, FIRST_WINDOW_DAYS, Ownership, RevenueKind, Snapshot, Subscriber,
    first_window_conversion, gone_quiet, ownership_ratio, ownership_trend,
    revenue_mix, value_by_channel,
)

NOW = 1_785_000_000


def sub(sid="s1", *, joined_days_ago=30, channel="x", bought_after_days=None,
        contacted_days_ago=None, status="active", lifetime=0) -> Subscriber:
    first = NOW - joined_days_ago * DAY
    return Subscriber(
        sub_id=sid, first_seen_at=first, channel_source=channel, status=status,
        last_contact_at=(None if contacted_days_ago is None
                         else NOW - contacted_days_ago * DAY),
        first_purchase_at=(None if bought_after_days is None
                           else first + bought_after_days * DAY),
        lifetime_minor=lifetime)


class TestCohortMaturity(unittest.TestCase):
    """The trap: counting people who have not had a first week yet."""

    def test_somebody_who_joined_yesterday_is_not_a_failure(self):
        c = first_window_conversion([sub(joined_days_ago=1)], now_epoch_s=NOW)["x"]
        self.assertEqual(c.matured, 0)
        self.assertEqual(c.too_early, 1)
        self.assertIsNone(c.rate)

    def test_the_rate_does_not_fall_when_new_people_arrive(self):
        """A growing business must not read as a failing one."""
        mature = [sub(f"m{i}", joined_days_ago=30,
                      bought_after_days=(2 if i < 3 else None)) for i in range(6)]
        before = first_window_conversion(mature, now_epoch_s=NOW)["x"].rate
        after = first_window_conversion(
            mature + [sub(f"n{i}", joined_days_ago=1) for i in range(20)],
            now_epoch_s=NOW)["x"].rate
        self.assertEqual(before, after)
        self.assertAlmostEqual(before, 0.5)

    def test_no_matured_cohort_is_none_not_zero(self):
        """Zero is a measurement. None is the absence of one."""
        c = first_window_conversion([sub(joined_days_ago=2)], now_epoch_s=NOW)["x"]
        self.assertIsNone(c.rate)
        self.assertNotEqual(c.rate, 0.0)

    def test_the_boundary_day_counts_as_matured(self):
        c = first_window_conversion([sub(joined_days_ago=FIRST_WINDOW_DAYS)],
                                    now_epoch_s=NOW)["x"]
        self.assertEqual(c.matured, 1)

    def test_a_purchase_after_the_window_is_not_a_window_conversion(self):
        c = first_window_conversion(
            [sub(joined_days_ago=60, bought_after_days=20)], now_epoch_s=NOW)["x"]
        self.assertEqual(c.converted, 0)
        self.assertEqual(c.matured, 1)

    def test_it_is_reported_per_channel(self):
        """A blended rate cannot say which channel brings people who never
        buy."""
        out = first_window_conversion([
            sub("a", joined_days_ago=30, channel="reddit", bought_after_days=1),
            sub("b", joined_days_ago=30, channel="x"),
        ], now_epoch_s=NOW)
        self.assertEqual(out["reddit"].rate, 1.0)
        self.assertEqual(out["x"].rate, 0.0)


class TestWhoHasGoneQuiet(unittest.TestCase):
    """The highest-value, zero-risk output: a person sends the message."""

    def test_never_contacted_comes_first(self):
        out = gone_quiet([sub("old", contacted_days_ago=9),
                          sub("never", contacted_days_ago=None)],
                         now_epoch_s=NOW)
        self.assertEqual([q.sub_id for q in out], ["never", "old"])

    def test_never_contacted_is_none_not_a_big_number(self):
        """Never-written-to and written-to-long-ago are different situations,
        and collapsing them hides the one that is easiest to fix."""
        out = gone_quiet([sub("never")], now_epoch_s=NOW)
        self.assertIsNone(out[0].days_since_contact)

    def test_somebody_contacted_today_is_not_quiet(self):
        self.assertEqual(gone_quiet([sub(contacted_days_ago=0)],
                                    now_epoch_s=NOW), [])

    def test_longest_silence_first(self):
        out = gone_quiet([sub("a", contacted_days_ago=4),
                          sub("b", contacted_days_ago=30),
                          sub("c", contacted_days_ago=9)], now_epoch_s=NOW)
        self.assertEqual([q.sub_id for q in out], ["b", "c", "a"])

    def test_a_blocked_person_is_not_on_the_list(self):
        self.assertEqual(
            gone_quiet([sub(status="blocked")], now_epoch_s=NOW), [])


class TestOwnership(unittest.TestCase):
    def snaps(self, at, owned=0, semi=0, rented=0):
        return [Snapshot(at, "mail", Ownership.OWNED, owned),
                Snapshot(at, "tg", Ownership.SEMI_OWNED, semi),
                Snapshot(at, "x", Ownership.RENTED, rented)]

    def test_the_ratio(self):
        self.assertAlmostEqual(
            ownership_ratio(self.snaps(0, owned=10, semi=10, rented=80)), 0.2)

    def test_an_empty_audience_has_no_ratio(self):
        """A business with no audience does not have a bad ownership ratio."""
        self.assertIsNone(ownership_ratio([]))
        self.assertIsNone(ownership_ratio(self.snaps(0)))

    def test_growth_on_rented_ground_reads_as_down(self):
        """The failure that looks like success: every count rises while the
        share she owns falls."""
        series = self.snaps(100, owned=10, semi=10, rented=80) + \
            self.snaps(200, owned=12, semi=12, rented=400)
        trend = ownership_trend(series, split_at=200)
        self.assertEqual(trend.direction, "down")
        self.assertTrue(trend.worth_saying)

    def test_one_point_is_not_a_trend(self):
        """Reporting it as flat would be inventing the missing point."""
        trend = ownership_trend(self.snaps(200, owned=1, rented=1), split_at=200)
        self.assertEqual(trend.direction, "unknown")
        self.assertFalse(trend.worth_saying)

    def test_rising_ownership_is_not_worth_interrupting_for(self):
        series = self.snaps(100, owned=1, rented=99) + \
            self.snaps(200, owned=50, rented=50)
        self.assertEqual(ownership_trend(series, split_at=200).direction, "up")
        self.assertFalse(ownership_trend(series, split_at=200).worth_saying)


class TestValuePerChannel(unittest.TestCase):
    def test_lifetime_value_without_a_cost_is_none(self):
        """Zero cost makes every channel look infinitely profitable, and it
        is the most tempting default in the file."""
        v = value_by_channel([sub(channel="x", lifetime=5000)])["x"]
        self.assertEqual(v.average_lifetime_minor, 5000)
        self.assertIsNone(v.ratio)

    def test_with_a_cost_it_is_a_ratio(self):
        v = value_by_channel([sub("a", channel="x", lifetime=6000),
                              sub("b", channel="x", lifetime=4000)],
                             acquisition_cost_minor={"x": 1000})["x"]
        self.assertEqual(v.average_lifetime_minor, 5000)
        self.assertAlmostEqual(v.ratio, 5.0)

    def test_a_zero_cost_is_refused_not_divided_by(self):
        v = value_by_channel([sub(channel="x", lifetime=1)],
                             acquisition_cost_minor={"x": 0})["x"]
        self.assertIsNone(v.ratio)


class TestRevenueMix(unittest.TestCase):
    def test_nothing_earned_yet_is_none(self):
        """Somebody else's 50-70% is not hers."""
        self.assertIsNone(revenue_mix({k: 0 for k in RevenueKind}))

    def test_the_mix_is_her_own(self):
        mix = revenue_mix({RevenueKind.PPV: 7000,
                           RevenueKind.SUBSCRIPTION: 3000,
                           RevenueKind.TIP: 0, RevenueKind.CUSTOM: 0})
        self.assertAlmostEqual(mix["ppv"], 0.7)


class Store(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "aud.sqlite")
        self.s = AudienceStore(self.path)
        self.addCleanup(self.s.close)


class TestMoneyIsIntegerMinorUnits(Store):
    def test_the_column_is_an_integer(self):
        cols = {r[1]: r[2] for r in self.s._conn.execute(
            "PRAGMA table_info(revenue_events)")}
        self.assertEqual(cols["amount_minor"], "INTEGER")

    def test_a_float_amount_is_refused(self):
        """`0.1 + 0.2 != 0.3`, and a year's total is where that shows."""
        self.s.add_subscriber("studio", "s1", first_seen_at=NOW)
        for bad in (10.5, "1000", True, None):
            with self.assertRaises(AudienceError):
                self.s.record_revenue("studio", f"e{bad}", kind="tip",
                                      amount_minor=bad, occurred_at=NOW)

    def test_a_negative_amount_is_refused(self):
        with self.assertRaises(AudienceError):
            self.s.record_revenue("studio", "e1", kind="tip",
                                  amount_minor=-1, occurred_at=NOW)

    def test_an_unknown_kind_is_refused(self):
        with self.assertRaises(AudienceError):
            self.s.record_revenue("studio", "e1", kind="mystery",
                                  amount_minor=1, occurred_at=NOW)


class TestFirstPurchaseIsStampedOnce(Store):
    def buy(self, eid, at, amount=1000):
        self.s.record_revenue("studio", eid, kind="ppv", amount_minor=amount,
                              occurred_at=at, sub_id="s1")

    def setUp(self):
        super().setUp()
        self.s.add_subscriber("studio", "s1", first_seen_at=NOW,
                              channel_source="reddit")

    def test_the_first_payment_stamps_it(self):
        self.buy("e1", NOW + 2 * DAY)
        self.assertEqual(self.s.subscriber("s1").first_purchase_at,
                         NOW + 2 * DAY)

    def test_a_later_payment_does_not_move_it(self):
        """It is what first-window conversion compares against; moving it
        would reclassify a conversion that already happened."""
        self.buy("e1", NOW + 2 * DAY)
        self.buy("e2", NOW + 40 * DAY)
        self.assertEqual(self.s.subscriber("s1").first_purchase_at,
                         NOW + 2 * DAY)

    def test_lifetime_value_is_summed_not_stored(self):
        """A stored total is a second copy of a fact, and the two disagree
        the first time a row is corrected."""
        self.buy("e1", NOW, amount=1500)
        self.buy("e2", NOW, amount=2500)
        self.assertEqual(self.s.subscriber("s1").lifetime_minor, 4000)

    def test_money_from_nobody_is_allowed(self):
        """A tip can arrive before anybody knows who sent it. Refusing it
        would lose the money to keep the schema tidy."""
        self.s.record_revenue("studio", "anon", kind="tip",
                              amount_minor=500, occurred_at=NOW)
        self.assertEqual(self.s.revenue_totals("studio")[RevenueKind.TIP], 500)

    def test_money_from_an_unknown_subscriber_is_refused(self):
        with self.assertRaises(AudienceError):
            self.s.record_revenue("studio", "e9", kind="ppv", amount_minor=1,
                                  occurred_at=NOW, sub_id="ghost")

    def test_the_same_event_twice_is_refused(self):
        self.buy("e1", NOW)
        with self.assertRaises(AudienceError):
            self.buy("e1", NOW)


class TestContactStampOnlyMovesForward(Store):
    def setUp(self):
        super().setUp()
        self.s.add_subscriber("studio", "s1", first_seen_at=NOW)

    def test_it_moves_forward(self):
        self.s.mark_contacted("s1", at=NOW + DAY)
        self.assertEqual(self.s.subscriber("s1").last_contact_at, NOW + DAY)

    def test_it_does_not_move_backwards(self):
        """An older message does not make a newer one less recent — and
        moving it back would put somebody on the quiet list who is not."""
        self.s.mark_contacted("s1", at=NOW + 5 * DAY)
        self.s.mark_contacted("s1", at=NOW + DAY)
        self.assertEqual(self.s.subscriber("s1").last_contact_at, NOW + 5 * DAY)


class TestSnapshots(Store):
    def test_a_snapshot_is_written_whole(self):
        self.s.take_snapshot("studio", taken_at=NOW, counts=[
            ("mail", "owned", 10), ("x", "rented", 90)])
        self.assertAlmostEqual(
            ownership_ratio(self.s.latest_snapshot("studio")), 0.1)

    def test_an_unknown_ownership_kind_is_refused_before_anything_is_written(self):
        """A half-written snapshot has an ownership ratio and it is wrong."""
        with self.assertRaises(AudienceError):
            self.s.take_snapshot("studio", taken_at=NOW, counts=[
                ("mail", "owned", 10), ("x", "borrowed", 90)])
        self.assertEqual(self.s.latest_snapshot("studio"), [])

    def test_the_database_refuses_a_fourth_kind_too(self):
        """Not only Python. A CHECK is the half that survives hand-written
        SQL."""
        with self.assertRaises(Exception):
            self.s._conn.execute(
                "INSERT INTO audience_snapshot (taken_at, tenant_id, channel, "
                "kind, count) VALUES (1, 'studio', 'x', 'borrowed', 1)")

    def test_snapshots_accumulate_as_a_series(self):
        for at in (NOW, NOW + 30 * DAY):
            self.s.take_snapshot("studio", taken_at=at, counts=[
                ("mail", "owned", 5), ("x", "rented", 95)])
        self.assertEqual(len(self.s.snapshots("studio")), 4)

    def test_taking_the_same_snapshot_twice_corrects_it(self):
        self.s.take_snapshot("studio", taken_at=NOW,
                             counts=[("mail", "owned", 5)])
        self.s.take_snapshot("studio", taken_at=NOW,
                             counts=[("mail", "owned", 7)])
        self.assertEqual(self.s.latest_snapshot("studio")[0].count, 7)


class TestItWorksWithNobodyAtAll(Store):
    """All three tables exist before there is a single subscriber, and that
    is the reason to build them now: the month a business starts is the month
    churn is decided, and a table added afterwards cannot describe it."""

    def test_an_empty_business_answers_without_inventing(self):
        self.assertEqual(self.s.subscribers("studio"), [])
        self.assertIsNone(revenue_mix(self.s.revenue_totals("studio")))
        self.assertIsNone(ownership_ratio(self.s.latest_snapshot("studio")))
        self.assertEqual(gone_quiet(self.s.subscribers("studio"),
                                    now_epoch_s=NOW), [])

    def test_durability(self):
        mode = self.s._conn.execute("PRAGMA journal_mode").fetchone()[0]
        self.assertEqual(str(mode).lower(), "wal")
        self.assertEqual(
            self.s._conn.execute("PRAGMA synchronous").fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()


class TestDistributionNotAverage(unittest.TestCase):
    """The cohort trap, moved onto money.

    A handful of people are most of the income in this business. "Average
    subscriber value is $40" describes nobody when three people are half the
    month — and it is exactly the number that gets used to decide what a
    subscriber is worth acquiring.
    """

    def test_a_skewed_month_refuses_to_offer_a_mean(self):
        """A number that is available gets used."""
        from ofn.kernel.audience import concentration
        subs = [sub("whale", lifetime=100_000)] + \
            [sub(f"s{i}", lifetime=1_000) for i in range(10)]
        c = concentration(subs)
        self.assertTrue(c.is_skewed)
        self.assertIsNone(c.mean_minor)

    def test_an_even_month_does_offer_one(self):
        from ofn.kernel.audience import concentration
        c = concentration([sub(f"s{i}", lifetime=1_000) for i in range(20)])
        self.assertFalse(c.is_skewed)
        self.assertEqual(c.mean_minor, 1_000)

    def test_the_top_share_is_the_number_worth_saying(self):
        from ofn.kernel.audience import concentration
        subs = [sub("a", lifetime=5_000), sub("b", lifetime=4_000),
                sub("c", lifetime=1_000)] + \
            [sub(f"s{i}", lifetime=100) for i in range(10)]
        c = concentration(subs, top_n=3)
        self.assertAlmostEqual(c.top_share, 10_000 / 11_000, places=4)

    def test_people_who_never_paid_are_counted_not_averaged_away(self):
        """"Forty people have never bought anything" is an action. Averaging
        them into the value of a subscriber is how that action disappears."""
        from ofn.kernel.audience import concentration
        c = concentration([sub("a", lifetime=1_000)] +
                          [sub(f"s{i}") for i in range(40)])
        self.assertEqual(c.payers, 1)
        self.assertEqual(c.silent, 40)

    def test_nobody_paying_has_no_share(self):
        from ofn.kernel.audience import concentration
        c = concentration([sub(f"s{i}") for i in range(5)])
        self.assertIsNone(c.top_share)
        self.assertIsNone(c.mean_minor)
        self.assertFalse(c.is_skewed)

    def test_fewer_payers_than_the_top_n_is_reported_honestly(self):
        """`top_n` of 3 with two payers is a share of two, and says so."""
        from ofn.kernel.audience import concentration
        c = concentration([sub("a", lifetime=10), sub("b", lifetime=10)],
                          top_n=3)
        self.assertEqual(c.top_n, 2)
        self.assertEqual(c.top_share, 1.0)
