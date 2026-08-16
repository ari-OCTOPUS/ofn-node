"""Fleet health and the trial-and-error search over earning methods.

The question behind every test here: when the owner is asleep and a hundred
and sixty machines are running unattended, does this code tell the truth about
what it does and does not know?
"""

from __future__ import annotations

import unittest

from ofn.kernel.allocation import (
    DEFAULT_MIN_SHARE,
    DEFAULT_MIN_DWELL_S, Arm, Assignment, Feasibility, Placement, Trial,
    coverage, plan,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.fleet import (
    MIN_BASELINE_SAMPLES, Baseline, Reading, UnitClass, UnitHealth, UnitId,
    class_is_dark, judge, judge_all, summarise,
)

NOW = 1_785_000_000
OPI = "opi5pro"
ESP = "esp32"


def reading(**kw) -> Reading:
    base = dict(unit="opi-01", at_epoch_s=NOW, hashrate=1000.0,
                accepted=50, arm_id="a1")
    base.update(kw)
    return Reading(**base)


def baseline(**kw) -> Baseline:
    base = dict(unit="opi-01", arm_id="a1", samples=100, median_hashrate=1000.0)
    base.update(kw)
    return Baseline(**base)


class TestIds(unittest.TestCase):
    def test_unit_id_rejects_path_traversal(self):
        for bad in ["../etc", "opi/01", "OPI-01", "", "opi_01"]:
            with self.subTest(bad=bad), self.assertRaises(FailClosedError):
                UnitId(bad)

    def test_unit_class_is_validated_too(self):
        UnitClass("opi5pro"); UnitClass("zero3"); UnitClass("rpi4")
        with self.assertRaises(FailClosedError):
            UnitClass("../x")

    def test_negative_counters_refused(self):
        with self.assertRaises(FailClosedError):
            Reading(unit="u", at_epoch_s=NOW, accepted=-1)


class TestUnknownIsNotHealthy(unittest.TestCase):
    """The rule this module exists for: 162 units, zero ever benchmarked."""

    def test_never_seen_is_unknown_not_offline(self):
        v = judge(UnitId("opi-01"), None, None, now_epoch_s=NOW)
        self.assertIs(v.health, UnitHealth.UNKNOWN)

    def test_no_baseline_means_unknown_not_healthy(self):
        v = judge(UnitId("opi-01"), reading(), None, now_epoch_s=NOW)
        self.assertIs(v.health, UnitHealth.UNKNOWN)
        self.assertIn("baseline", v.reason)

    def test_thin_baseline_is_not_a_baseline(self):
        b = baseline(samples=MIN_BASELINE_SAMPLES - 1)
        v = judge(UnitId("opi-01"), reading(hashrate=10.0), b, now_epoch_s=NOW)
        self.assertIs(v.health, UnitHealth.UNKNOWN,
                      "one lucky minute must not become the reference number")

    def test_cannot_be_called_slow_against_another_arm(self):
        """A board running a different algorithm is not a slower board."""
        v = judge(UnitId("opi-01"), reading(arm_id="a2", hashrate=1.0),
                  baseline(arm_id="a1"), now_epoch_s=NOW)
        self.assertIs(v.health, UnitHealth.UNKNOWN)
        self.assertIn("not comparable", v.reason)

    def test_unknown_does_not_summon_a_human(self):
        self.assertFalse(UnitHealth.UNKNOWN.needs_a_human())
        self.assertTrue(UnitHealth.OFFLINE.needs_a_human())


class TestHealthJudgements(unittest.TestCase):
    def test_silence_beats_a_stale_good_reading(self):
        v = judge(UnitId("opi-01"), reading(at_epoch_s=NOW - 9999),
                  baseline(), now_epoch_s=NOW)
        self.assertIs(v.health, UnitHealth.OFFLINE)

    def test_hashrate_without_accepted_shares_is_broken(self):
        """The failure a liveness check calls healthy."""
        v = judge(UnitId("opi-01"), reading(accepted=0, hashrate=999.0),
                  baseline(), now_epoch_s=NOW)
        self.assertIs(v.health, UnitHealth.BROKEN)

    def test_below_its_own_baseline_is_degraded(self):
        v = judge(UnitId("opi-01"), reading(hashrate=500.0), baseline(),
                  now_epoch_s=NOW)
        self.assertIs(v.health, UnitHealth.DEGRADED)
        self.assertIn("50%", v.reason)

    def test_healthy_needs_both_shares_and_rate(self):
        v = judge(UnitId("opi-01"), reading(), baseline(), now_epoch_s=NOW)
        self.assertIs(v.health, UnitHealth.HEALTHY)

    def test_registry_is_iterated_not_the_readings(self):
        """A unit dead on a shelf sends nothing, so it must be found via the
        registry — the readings map cannot contain it."""
        units = [("opi-01", OPI), ("opi-02", OPI), ("opi-03", OPI)]
        vs = judge_all({"opi-01": reading()}, {}, units, now_epoch_s=NOW)
        self.assertEqual(len(vs), 3)
        self.assertEqual(summarise(vs)["unknown"], 3)


class TestClassGoingDark(unittest.TestCase):
    def test_whole_class_dark_is_detected(self):
        units = [("esp-1", ESP), ("esp-2", ESP), ("opi-01", OPI)]
        vs = judge_all({"opi-01": reading()}, {}, units, now_epoch_s=NOW)
        self.assertTrue(class_is_dark(vs, units, UnitClass(ESP)))

    def test_one_live_member_means_not_dark(self):
        units = [("esp-1", ESP), ("esp-2", ESP)]
        latest = {"esp-1": reading(unit="esp-1", accepted=0, hashrate=1.0)}
        vs = judge_all(latest, {}, units, now_epoch_s=NOW)
        self.assertFalse(class_is_dark(vs, units, UnitClass(ESP)),
                         "broken still means powered and talking")

    def test_empty_class_is_not_dark(self):
        self.assertFalse(class_is_dark([], [], UnitClass("fpga")))


class TestFeasibility(unittest.TestCase):
    def test_unproven_until_shares_confirm(self):
        self.assertIs(Trial("a1", OPI, seconds=60).feasibility(),
                      Feasibility.UNPROVEN)

    def test_accepted_shares_prove_it_works(self):
        self.assertIs(Trial("a1", OPI, seconds=60, accepted=10).feasibility(),
                      Feasibility.WORKING)

    def test_long_run_with_nothing_is_broken_not_unproven(self):
        t = Trial("a1", OPI, seconds=DEFAULT_MIN_DWELL_S * 2, accepted=0)
        self.assertIs(t.feasibility(), Feasibility.BROKEN)

    def test_proof_on_one_class_does_not_vouch_for_another(self):
        trials = {("a1", OPI): Trial("a1", OPI, seconds=99999, accepted=500)}
        self.assertIs(
            trials.get(("a1", ESP), Trial("a1", ESP)).feasibility(),
            Feasibility.UNPROVEN)


class TestArmValidation(unittest.TestCase):
    def test_arm_with_no_class_is_refused(self):
        with self.assertRaises(FailClosedError):
            Arm("a1", ())

    def test_arm_id_is_a_safe_slug(self):
        Arm("xmr.p2pool", (OPI,))
        with self.assertRaises(FailClosedError):
            Arm("../evil", (OPI,))


class TestPlan(unittest.TestCase):
    def units(self, n, cls=OPI, arm="", since=0):
        return [Placement(f"u{i:02d}", cls, arm, since) for i in range(n)]

    def test_idle_units_get_assigned(self):
        arms = [Arm("a1", (OPI,))]
        moves = plan(self.units(4), arms, {}, now_epoch_s=NOW)
        self.assertEqual(len(moves), 4)
        self.assertTrue(all(m.arm_id == "a1" for m in moves))

    def test_dwell_time_stops_thrashing(self):
        """Without this the fleet measures nothing but warm-ups."""
        arms = [Arm("a1", (OPI,)), Arm("a2", (OPI,))]
        placed = self.units(4, arm="a1", since=NOW - 60)
        self.assertEqual(plan(placed, arms, {}, now_epoch_s=NOW), ())

    def test_broken_arm_overrides_dwell(self):
        arms = [Arm("a1", (OPI,)), Arm("a2", (OPI,))]
        trials = {("a1", OPI): Trial("a1", OPI,
                                     seconds=DEFAULT_MIN_DWELL_S * 3, accepted=0)}
        placed = self.units(2, arm="a1", since=NOW - 10)
        moves = plan(placed, arms, trials, now_epoch_s=NOW)
        self.assertEqual(len(moves), 2)
        self.assertTrue(all(m.arm_id == "a2" for m in moves))

    def test_a_broken_arm_is_never_a_destination(self):
        arms = [Arm("a1", (OPI,)), Arm("dead", (OPI,))]
        trials = {("dead", OPI): Trial("dead", OPI,
                                       seconds=DEFAULT_MIN_DWELL_S * 5, accepted=0)}
        moves = plan(self.units(6), arms, trials, now_epoch_s=NOW)
        self.assertTrue(all(m.arm_id != "dead" for m in moves))

    def test_exploration_is_bounded(self):
        """Sixteen boards may prove new arms without the whole fleet leaving
        what already works."""
        arms = [Arm("proven", (OPI,))] + [Arm(f"new{i}", (OPI,)) for i in range(9)]
        trials = {("proven", OPI): Trial("proven", OPI, seconds=99999, accepted=999)}
        placed = self.units(16, arm="proven", since=NOW - DEFAULT_MIN_DWELL_S * 2)
        moves = plan(placed, arms, trials, now_epoch_s=NOW, explore_fraction=0.25)
        explorers = [m for m in moves if m.rule == "alloc:explore"]
        self.assertLessEqual(len(explorers), 4)
        self.assertGreater(len(explorers), 0)

    def test_zero_explore_budget_still_exploits(self):
        arms = [Arm("proven", (OPI,)), Arm("new", (OPI,))]
        trials = {("proven", OPI): Trial("proven", OPI, seconds=99999, accepted=999)}
        moves = plan(self.units(4), arms, trials, now_epoch_s=NOW,
                     explore_fraction=0.0)
        self.assertTrue(all(m.arm_id == "proven" for m in moves))

    def test_class_restrictions_are_honoured(self):
        """An algorithm that is pointless on a microcontroller stays off it."""
        arms = [Arm("heavy", (OPI,)), Arm("light", (ESP,))]
        placed = [Placement("e1", ESP), Placement("o1", OPI)]
        moves = plan(placed, arms, {}, now_epoch_s=NOW)
        by_unit = {m.unit: m.arm_id for m in moves}
        self.assertEqual(by_unit["e1"], "light")
        self.assertEqual(by_unit["o1"], "heavy")

    def test_a_class_with_no_arm_is_left_alone_not_crashed(self):
        moves = plan([Placement("f1", "fpga")], [Arm("a1", (OPI,))], {},
                     now_epoch_s=NOW)
        self.assertEqual(moves, ())

    def test_load_spreads_across_proven_arms(self):
        arms = [Arm("p1", (OPI,)), Arm("p2", (OPI,))]
        trials = {("p1", OPI): Trial("p1", OPI, seconds=99999, accepted=999),
                  ("p2", OPI): Trial("p2", OPI, seconds=99999, accepted=999)}
        moves = plan(self.units(8), arms, trials, now_epoch_s=NOW,
                     explore_fraction=0.0)
        counts = {}
        for m in moves:
            counts[m.arm_id] = counts.get(m.arm_id, 0) + 1
        self.assertEqual(counts, {"p1": 4, "p2": 4})

    def test_unit_on_a_deleted_arm_is_rescued(self):
        """Ari removes a row from the pinned file; the unit must not sit
        pointed at something that no longer exists."""
        placed = [Placement("u1", OPI, "gone", NOW - 10)]
        moves = plan(placed, [Arm("a1", (OPI,))], {}, now_epoch_s=NOW)
        self.assertEqual(moves[0].arm_id, "a1")

    def test_plan_is_deterministic(self):
        arms = [Arm("a1", (OPI,)), Arm("a2", (OPI,)), Arm("a3", (OPI,))]
        args = (self.units(9), arms, {})
        first = plan(*args, now_epoch_s=NOW)
        for _ in range(5):
            self.assertEqual(plan(*args, now_epoch_s=NOW), first)

    def test_bad_explore_fraction_is_refused(self):
        with self.assertRaises(FailClosedError):
            plan([], [], {}, now_epoch_s=NOW, explore_fraction=1.5)

    def test_every_move_carries_a_rule(self):
        moves = plan(self.units(3), [Arm("a1", (OPI,))], {}, now_epoch_s=NOW)
        for m in moves:
            self.assertTrue(m.rule.startswith("alloc:"))
            self.assertTrue(m.reason)


class TestCoverage(unittest.TestCase):
    def test_reports_what_is_still_untried(self):
        arms = [Arm("a1", (OPI, ESP)), Arm("a2", (OPI,))]
        trials = {("a1", OPI): Trial("a1", OPI, seconds=9999, accepted=99)}
        c = coverage([], arms, trials)
        self.assertEqual(c["arm_class_pairs"], 3)
        self.assertEqual(c["working"], 1)
        self.assertEqual(c["unproven"], 2)

    def test_idle_units_are_counted(self):
        c = coverage([Placement("u1", OPI), Placement("u2", OPI, "a1")], [], {})
        self.assertEqual(c["units_idle"], 1)
        self.assertEqual(c["units_assigned"], 1)


if __name__ == "__main__":
    unittest.main()


class TestEmissionShare(unittest.TestCase):
    """The owner's correction, as code: a coin that hands a 16-board fleet a
    rounding error of its emission is not accumulation, however well it runs."""

    def test_unknown_share_is_not_a_bad_share(self):
        """Day one, nobody has looked up what the chain emits. That must not
        condemn the arm."""
        t = Trial("a1", OPI, seconds=9999, accepted=50)
        self.assertIsNone(t.share)
        self.assertIs(t.feasibility(), Feasibility.WORKING)

    def test_a_real_share_is_working(self):
        t = Trial("new", OPI, seconds=9999, accepted=50,
                  units_earned=1200.0, network_emitted=20_000.0)   # 6%
        self.assertAlmostEqual(t.share, 0.06)
        self.assertIs(t.feasibility(), Feasibility.WORKING)

    def test_a_rounding_error_is_marginal_not_working(self):
        """The established-chain case the owner rejected by name."""
        t = Trial("big", OPI, seconds=9999, accepted=50,
                  units_earned=3.0, network_emitted=5_000_000.0)
        self.assertIs(t.feasibility(), Feasibility.MARGINAL)

    def test_marginal_still_beats_idle(self):
        arms = [Arm("big", (OPI,))]
        trials = {("big", OPI): Trial("big", OPI, seconds=9999, accepted=50,
                                      units_earned=1.0, network_emitted=1e9)}
        moves = plan([Placement("u1", OPI)], arms, trials, now_epoch_s=NOW,
                     explore_fraction=0.0)
        self.assertEqual(moves[0].arm_id, "big")
        self.assertEqual(moves[0].rule, "alloc:marginal")

    def test_a_real_arm_wins_over_a_marginal_one(self):
        arms = [Arm("big", (OPI,)), Arm("new", (OPI,))]
        trials = {
            ("big", OPI): Trial("big", OPI, seconds=9999, accepted=50,
                                units_earned=1.0, network_emitted=1e9),
            ("new", OPI): Trial("new", OPI, seconds=9999, accepted=50,
                                units_earned=900.0, network_emitted=10_000.0),
        }
        moves = plan([Placement("u1", OPI)], arms, trials, now_epoch_s=NOW,
                     explore_fraction=0.0)
        self.assertEqual(moves[0].arm_id, "new")
        self.assertEqual(moves[0].rule, "alloc:exploit")

    def test_diversity_survives_a_high_share_arm(self):
        """Share breaks ties; it does not collapse the fleet onto one coin.
        Many coins accumulating at once is the point."""
        arms = [Arm("a", (OPI,)), Arm("b", (OPI,))]
        trials = {
            ("a", OPI): Trial("a", OPI, seconds=9999, accepted=50,
                              units_earned=9000.0, network_emitted=10_000.0),
            ("b", OPI): Trial("b", OPI, seconds=9999, accepted=50,
                              units_earned=500.0, network_emitted=10_000.0),
        }
        moves = plan([Placement(f"u{i}", OPI) for i in range(8)], arms, trials,
                     now_epoch_s=NOW, explore_fraction=0.0)
        counts = {}
        for m in moves:
            counts[m.arm_id] = counts.get(m.arm_id, 0) + 1
        self.assertEqual(counts, {"a": 4, "b": 4})

    def test_raw_units_are_reported_even_though_ignored(self):
        arms = [Arm("a", (OPI,))]
        trials = {("a", OPI): Trial("a", OPI, seconds=99, accepted=1,
                                    units_earned=1234.5)}
        self.assertAlmostEqual(coverage([], arms, trials)["units_earned_total"],
                               1234.5)

    def test_negative_emission_is_refused(self):
        with self.assertRaises(FailClosedError):
            Trial("a", OPI, units_earned=-1.0)
