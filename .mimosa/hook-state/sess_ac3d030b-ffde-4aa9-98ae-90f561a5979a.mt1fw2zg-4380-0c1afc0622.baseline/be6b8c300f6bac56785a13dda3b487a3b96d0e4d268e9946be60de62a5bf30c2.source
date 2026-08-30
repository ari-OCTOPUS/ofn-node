import pytest

pytestmark = pytest.mark.l0

from nbb_cp.kernel.events import EventKind, next_event
from nbb_cp.kernel.fitness import compute_fitness
from nbb_cp.kernel.pulse import MAX_FACTOR, MIN_FACTOR, epoch_length_seconds
from nbb_cp.kernel.sigma import branching_ratio, sigma_allows_spawn, sigma_from_events


def chain(payloads):
    events, prev = [], None
    for kind, payload in payloads:
        prev = next_event(prev, "2026-01-01T00:00:00+00:00", kind, payload)
        events.append(prev)
    return events


class TestSigma:
    def test_zero_agents_zero_sigma(self):
        assert branching_ratio(0, 0) == 0.0

    def test_ratio(self):
        assert branching_ratio(2, 4) == 0.5

    def test_negative_counts_rejected(self):
        with pytest.raises(ValueError):
            branching_ratio(-1, 1)

    def test_limit_inclusive(self):
        assert sigma_allows_spawn(1.0)
        assert not sigma_allows_spawn(1.0001)

    def test_sigma_from_events_counts_only_executed_in_window(self):
        events = chain([
            (EventKind.SPAWN, {"executed": True, "epoch": 0}),   # outside window
            (EventKind.SPAWN, {"executed": True, "epoch": 8}),
            (EventKind.SPAWN, {"executed": False, "epoch": 9}),  # proposal only
            (EventKind.SPAWN, {"executed": True, "epoch": 10}),
        ])
        sigma = sigma_from_events(events, active_agents=2, window_epochs=5, current_epoch=10)
        assert sigma == pytest.approx(1.0)  # 2 executed spawns / 2 agents


class TestFitness:
    def test_only_confirmed_and_attributed_count(self):
        events = chain([
            (EventKind.REVENUE, {"organ_id": "a", "state": "reported", "amount_cents": 9999}),
            (EventKind.REVENUE, {"organ_id": "a", "state": "approved", "amount_cents": 500}),
            (EventKind.REVENUE, {"organ_id": "a", "state": "settled", "amount_cents": 500}),
            (EventKind.REVENUE, {"organ_id": "a", "state": "confirmed", "amount_cents": 300}),
            (EventKind.REVENUE, {"organ_id": "a", "state": "attributed", "amount_cents": 200}),
        ])
        assert compute_fitness(events, "a").confirmed_value_cents == 500

    def test_other_organ_revenue_ignored(self):
        events = chain([
            (EventKind.REVENUE, {"organ_id": "b", "state": "confirmed", "amount_cents": 100}),
        ])
        assert compute_fitness(events, "a").confirmed_value_cents == 0

    def test_three_bucket_spend_all_counted(self):
        events = chain([
            (EventKind.SPEND, {"organ_id": "a", "input_cents": 10, "output_cents": 20, "orchestration_cents": 70}),
        ])
        report = compute_fitness(events, "a")
        assert report.spend_cents == 100  # orchestration bucket must not vanish

    def test_net_and_efficiency(self):
        events = chain([
            (EventKind.REVENUE, {"organ_id": "a", "state": "confirmed", "amount_cents": 300}),
            (EventKind.SPEND, {"organ_id": "a", "input_cents": 100}),
        ])
        report = compute_fitness(events, "a")
        assert report.net_cents == 200
        assert report.efficiency == pytest.approx(3.0)

    def test_zero_spend_zero_value_efficiency_zero(self):
        assert compute_fitness([], "a").efficiency == 0.0


class TestPulse:
    def test_calm_system_beats_slow(self):
        assert epoch_length_seconds(100) == pytest.approx(200.0)

    def test_pressure_shortens_epoch(self):
        calm = epoch_length_seconds(100, spend_velocity=0.1)
        stressed = epoch_length_seconds(100, spend_velocity=0.9, deadline_proximity=0.8)
        assert stressed < calm

    def test_clamped_between_min_and_max(self):
        assert epoch_length_seconds(100, spend_velocity=99) == 100 * MIN_FACTOR
        assert epoch_length_seconds(100) <= 100 * MAX_FACTOR

    def test_inputs_modulate_rhythm_not_phase(self):
        # Pure function of pressure: same inputs, same length — no hidden clock state.
        a = epoch_length_seconds(60, 0.2, 0.3, 0.1)
        b = epoch_length_seconds(60, 0.2, 0.3, 0.1)
        assert a == b

    def test_nonpositive_base_rejected(self):
        with pytest.raises(ValueError):
            epoch_length_seconds(0)
