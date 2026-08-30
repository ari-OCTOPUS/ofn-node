from mining_preexec_mvp.death_watch import evaluate_death_watch
from mining_preexec_mvp.models import DeathWatch


def test_death_watch_abandon_for_dead_dev():
    result = evaluate_death_watch(DeathWatch(coin="ABC", dev_dead_weeks=9, chain_stalled=False, community_dead=False))
    assert not result.passed
    assert result.risk.value == "red"


def test_death_watch_passes_when_no_death_criteria():
    result = evaluate_death_watch(DeathWatch(coin="ABC", dev_dead_weeks=2, chain_stalled=False, community_dead=False))
    assert result.passed


def test_death_watch_incomplete_is_orange():
    result = evaluate_death_watch(DeathWatch(coin="ABC"))
    assert not result.passed
    assert result.risk.value == "orange"
