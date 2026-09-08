"""MetricRegistry — units, staleness, warmup, restart sensitivity."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MetricSpec:
    name: str
    canonical_unit: str
    source_priority: tuple[str, ...]
    max_age_s: float
    expected_cadence_s: float
    warmup_window: int
    restart_sensitive: bool
    aggregation: str
    unknown_is_not_zero: bool = True


@dataclass
class MetricRegistry:
    metrics: dict[str, MetricSpec] = field(default_factory=dict)
    sources: dict[str, dict[str, Any]] = field(default_factory=dict)

    def register_metric(self, spec: MetricSpec) -> None:
        self.metrics[spec.name] = spec

    def register_source(self, source_id: str, kind: str, path: str) -> None:
        self.sources[source_id] = {"kind": kind, "path": path}

    def get(self, name: str) -> MetricSpec | None:
        return self.metrics.get(name)

    def source_ok(self, source_id: str) -> bool:
        return source_id in self.sources


def default_registry() -> MetricRegistry:
    r = MetricRegistry()
    r.register_source("pulse.arbiter", "overwrite_json", "_ops/state/pulse/arbiter-latest.json")
    r.register_source("pulse.arbiter_shadow", "append_jsonl", "_ops/state/pulse/arbiter-shadow.jsonl")
    r.register_source("pulse.life_currency", "overwrite_json", "_ops/state/pulse/life-currency-latest.json")
    r.register_source("state.organism", "overwrite_json", "_ops/state/ORGANISM-STATE.json")
    r.register_source("state.identities", "overwrite_json", "_ops/state/identities-latest.json")
    r.register_source("lab.fixture", "fixture", "_ops/shadow_homeostasis/fixtures")
    r.register_source("lab.store", "append_jsonl", "_ops/shadow_homeostasis/lab")
    specs = [
        MetricSpec("arbiter.period_s", "s", ("pulse.arbiter_shadow", "pulse.arbiter"), 180, 113, 0, False, "last"),
        MetricSpec("arbiter.color", "enum", ("pulse.arbiter_shadow", "pulse.arbiter"), 180, 113, 0, True, "last"),
        MetricSpec("rhythm.hrv", "s", ("lab.fixture",), 180, 113, 2, True, "last"),
        MetricSpec("rhythm.window_n", "count", ("lab.fixture",), 180, 113, 2, True, "last"),
        MetricSpec("identity_health", "ratio", ("state.identities", "state.organism"), 3600, 113, 1, True, "last"),
        MetricSpec("identity.learner", "ratio", ("state.identities",), 3600, 113, 1, True, "last"),
        MetricSpec("life_currency.daily_cap", "life_credit", ("pulse.life_currency",), 180, 113, 0, False, "last"),
        MetricSpec("life_currency.tokens_min", "life_credit", ("pulse.life_currency",), 180, 113, 0, False, "min"),
        MetricSpec("life_currency.unit", "enum", ("pulse.life_currency",), 180, 113, 0, False, "last"),
        MetricSpec("judge.rs_ba", "ratio", ("lab.fixture",), 86400, 86400, 0, False, "last"),
        MetricSpec("resource.cpu_pct", "percent", ("lab.fixture",), 120, 30, 0, False, "last"),
        MetricSpec("telemetry.integrity", "enum", ("lab.fixture",), 180, 113, 0, False, "last"),
    ]
    for s in specs:
        r.register_metric(s)
    return r
