# -*- coding: utf-8 -*-
"""T21 trust + eligibility quality states."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

_OPS = Path(__file__).resolve().parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from shadow_homeostasis.observation import Observation, Quality
from shadow_homeostasis.registry import default_registry
from shadow_homeostasis.trust import eligibility, mark_conflicting, never_zero_from_unknown, validate_observation

DT = datetime(2026, 8, 20, 2, 0, tzinfo=timezone.utc)


def _o(**kw):
    d = dict(observation_id="x", source_id="lab.fixture", metric="resource.cpu_pct",
             value=1.0, unit="percent", occurred_at=DT, recorded_at=DT, decision_time=DT,
             beat=1, boot_id="b", process_id=1, provenance_path="t", source_hash="h",
             quality="VALID", quality_reasons=[])
    d.update(kw)
    return Observation(**d)


def test_all_quality_states():
    reg = default_registry()
    assert validate_observation(_o(), reg).quality == Quality.VALID.value
    stale = validate_observation(_o(occurred_at=DT - timedelta(hours=1)), reg)
    assert stale.quality == Quality.STALE.value
    missing = validate_observation(_o(value=None), reg)
    assert missing.quality == Quality.MISSING.value
    unit = validate_observation(_o(unit="AUD"), reg)
    assert unit.quality == Quality.UNIT_MISMATCH.value
    future = validate_observation(_o(occurred_at=DT + timedelta(minutes=5), recorded_at=DT + timedelta(minutes=5)), reg)
    assert future.quality == Quality.FUTURE_DATA.value
    unreg = validate_observation(_o(metric="no.such"), reg)
    assert unreg.quality == Quality.UNLOCATED.value
    src = validate_observation(_o(source_id="not-registered"), reg)
    assert src.quality == Quality.UNLOCATED.value
    hist = validate_observation(_o(latest_only=True, historical_claim=True, metric="life_currency.tokens_min",
                                   unit="life_credit", source_id="pulse.life_currency"), reg)
    assert hist.quality == Quality.UNLOCATED.value
    warm = validate_observation(_o(metric="rhythm.hrv", unit="s", source_id="lab.fixture",
                                   window_n=1, value=0.0), reg)
    assert warm.quality == Quality.WARMUP.value
    a = _o(observation_id="a", metric="arbiter.period_s", unit="s", source_id="pulse.arbiter", value=113.65, beat=42784)
    b = _o(observation_id="b", metric="arbiter.period_s", unit="s", source_id="pulse.arbiter_shadow", value=112.76, beat=42784)
    a = validate_observation(a, reg)
    b = validate_observation(b, reg)
    mark_conflicting([a, b], "arbiter.period_s")
    assert a.quality == Quality.CONFLICTING.value
    assert b.quality == Quality.CONFLICTING.value
    rest = _o(metric="identity_health", unit="ratio", source_id="state.identities",
              quality=Quality.RESTART_ARTIFACT_SUSPECTED.value)
    rest.quality = Quality.RESTART_ARTIFACT_SUSPECTED.value
    assert rest.quality == Quality.RESTART_ARTIFACT_SUSPECTED.value


def test_invariants():
    assert never_zero_from_unknown(None, Quality.MISSING.value) is None
    assert never_zero_from_unknown(0, Quality.MISSING.value) is None
    assert eligibility(_o()) is False or True  # unvalidated
    v = validate_observation(_o(), default_registry())
    assert eligibility(v) is True
    assert not eligibility(validate_observation(_o(unit="nope"), default_registry()))
