"""Redacted result storage and conservative Pareto selection."""

from __future__ import annotations

import csv
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


RESULT_COLUMNS = (
    "run_id",
    "candidate_id",
    "block_size",
    "baseline_auto",
    "diagnostic_only",
    "workload_id",
    "profile",
    "cache_phase",
    "repetition",
    "request_count",
    "success_count",
    "error_count",
    "oom_count",
    "crash_count",
    "restart_count",
    "thermal_abort",
    "identity_safety_gate_passed",
    "production_impact_detected",
    "host_memory_critical",
    "disk_critical",
    "metrics_available",
    "prompt_tokens_total",
    "generation_tokens_total",
    "ttft_p50_ms",
    "ttft_p95_ms",
    "ttft_p99_ms",
    "tpot_p50_ms",
    "tpot_p95_ms",
    "tpot_p99_ms",
    "itl_p50_ms",
    "itl_p95_ms",
    "itl_p99_ms",
    "e2e_p50_ms",
    "e2e_p95_ms",
    "e2e_p99_ms",
    "request_throughput_rps",
    "input_token_throughput_tps",
    "output_token_throughput_tps",
    "queue_time_p50_ms",
    "queue_time_p95_ms",
    "prefill_time_p50_ms",
    "prefill_time_p95_ms",
    "decode_time_p50_ms",
    "decode_time_p95_ms",
    "prefix_cache_queries",
    "prefix_cache_hits",
    "prefix_cache_hit_ratio",
    "kv_cache_usage_peak",
    "preemption_total",
    "num_requests_waiting_peak",
    "gpu_memory_peak_bytes",
    "gpu_utilization_mean",
    "gpu_temperature_peak_c",
    "estimated_tail_fragmentation",
    "resolved_num_gpu_blocks",
)

_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")
_SENSITIVE_VALUE_PATTERNS = (
    re.compile(
        r"(?i)\b(?:bearer|authorization|password|master[_ -]?secret|"
        r"api[_-]?key|cache[_-]?salt)\b\s*(?::|=)?\s*[^\s,;]+"
    ),
    re.compile(
        r"(?i)\b(?:bearer|authorization|password|master[_ -]?secret|"
        r"api[_-]?key|cache[_-]?salt)\b"
    ),
    re.compile(r"(?i)\btenant[_-]?(?:id|\d+)\b"),
    re.compile(r"(?i)\bhttps?://[^\s,'\"<>]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
)


@dataclass(frozen=True)
class BenchmarkResult:
    run_id: str
    candidate_id: str
    workload_id: str
    profile: str
    cache_phase: str
    repetition: int
    block_size: int | None = None
    baseline_auto: bool = False
    diagnostic_only: bool = False
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    oom_count: int = 0
    crash_count: int = 0
    restart_count: int = 0
    thermal_abort: bool = False
    identity_safety_gate_passed: bool = True
    production_impact_detected: bool = False
    host_memory_critical: bool = False
    disk_critical: bool = False
    metrics_available: bool = False
    prompt_tokens_total: int = 0
    generation_tokens_total: int = 0
    ttft_p50_ms: float | None = None
    ttft_p95_ms: float | None = None
    ttft_p99_ms: float | None = None
    tpot_p50_ms: float | None = None
    tpot_p95_ms: float | None = None
    tpot_p99_ms: float | None = None
    itl_p50_ms: float | None = None
    itl_p95_ms: float | None = None
    itl_p99_ms: float | None = None
    e2e_p50_ms: float | None = None
    e2e_p95_ms: float | None = None
    e2e_p99_ms: float | None = None
    request_throughput_rps: float | None = None
    input_token_throughput_tps: float | None = None
    output_token_throughput_tps: float | None = None
    queue_time_p50_ms: float | None = None
    queue_time_p95_ms: float | None = None
    prefill_time_p50_ms: float | None = None
    prefill_time_p95_ms: float | None = None
    decode_time_p50_ms: float | None = None
    decode_time_p95_ms: float | None = None
    prefix_cache_queries: int | None = None
    prefix_cache_hits: int | None = None
    prefix_cache_hit_ratio: float | None = None
    kv_cache_usage_peak: float | None = None
    preemption_total: int | None = None
    num_requests_waiting_peak: int | None = None
    gpu_memory_peak_bytes: int | None = None
    gpu_utilization_mean: float | None = None
    gpu_temperature_peak_c: float | None = None
    estimated_tail_fragmentation: float | None = None
    resolved_num_gpu_blocks: int | None = None

    def __post_init__(self) -> None:
        for identifier in (
            self.run_id,
            self.candidate_id,
            self.workload_id,
            self.profile,
            self.cache_phase,
        ):
            if not _SAFE_IDENTIFIER.fullmatch(identifier):
                raise ValueError("result identifiers must be non-sensitive slugs")
        if self.cache_phase not in {"cold", "warm"}:
            raise ValueError("cache_phase must be cold or warm")
        if self.repetition <= 0:
            raise ValueError("repetition must be positive")
        if self.block_size is not None and self.block_size <= 0:
            raise ValueError("block_size must be positive when explicit")
        integer_counts = (
            self.request_count,
            self.success_count,
            self.error_count,
            self.oom_count,
            self.crash_count,
            self.restart_count,
            self.prompt_tokens_total,
            self.generation_tokens_total,
        )
        if any(value < 0 for value in integer_counts):
            raise ValueError("result counts must be non-negative")
        if self.success_count + self.error_count > self.request_count:
            raise ValueError("success/error counts exceed request_count")


def contains_sensitive_text(value: str) -> bool:
    return any(pattern.search(value) for pattern in _SENSITIVE_VALUE_PATTERNS)


def redact_sensitive_text(value: str) -> str:
    """Redact common secret/endpoint patterns from diagnostic text."""

    redacted = value
    for pattern in _SENSITIVE_VALUE_PATTERNS:
        redacted = pattern.sub("<redacted>", redacted)
    return redacted


def _safe_row(result: BenchmarkResult) -> dict[str, Any]:
    row = asdict(result)
    if set(row) != set(RESULT_COLUMNS):
        raise AssertionError("result schema and CSV columns diverged")
    for value in row.values():
        if isinstance(value, str) and contains_sensitive_text(value):
            raise ValueError("sensitive text is forbidden in result records")
    return {column: row[column] for column in RESULT_COLUMNS}


class ResultStore:
    """Append-only CSV store with a fixed prompt-free schema."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def ensure_header(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            with self.path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle)
                existing = tuple(next(reader, ()))
            if existing != RESULT_COLUMNS:
                raise ValueError("existing result CSV has an unexpected schema")
            return
        with self.path.open("x", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerow(RESULT_COLUMNS)

    def append(self, result: BenchmarkResult) -> None:
        row = _safe_row(result)
        self.ensure_header()
        with self.path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS)
            writer.writerow(
                {
                    key: (
                        ""
                        if value is None
                        else str(value).lower()
                        if isinstance(value, bool)
                        else value
                    )
                    for key, value in row.items()
                }
            )

    def row_count(self) -> int:
        self.ensure_header()
        with self.path.open("r", encoding="utf-8", newline="") as handle:
            return max(0, sum(1 for _ in handle) - 1)


@dataclass(frozen=True)
class CandidateSummary:
    """A repeated, profile-level empirical summary used for selection."""

    candidate_id: str
    block_size: int | None
    baseline_auto: bool
    profile: str
    repeat_count: int
    ttft_p95_ms: float | None
    e2e_p95_ms: float | None
    throughput_rps: float | None
    prefix_cache_hit_ratio: float | None
    preemption_total: float | None
    fragmentation_ratio: float | None
    queue_p95_ms: float | None
    gpu_memory_peak_bytes: float | None
    ttft_p95_ci: tuple[float, float] | None = None
    e2e_p95_ci: tuple[float, float] | None = None
    throughput_ci: tuple[float, float] | None = None
    prefix_cache_hit_ci: tuple[float, float] | None = None
    preemption_ci: tuple[float, float] | None = None
    fragmentation_ci: tuple[float, float] | None = None
    queue_p95_ci: tuple[float, float] | None = None
    gpu_memory_ci: tuple[float, float] | None = None
    request_count: int = 0
    error_count: int = 0
    oom_count: int = 0
    crash_count: int = 0
    restart_count: int = 0
    thermal_abort: bool = False
    identity_safety_gate_passed: bool = True
    production_impact_detected: bool = False
    host_memory_critical: bool = False
    disk_critical: bool = False
    metrics_available: bool = True
    diagnostic_only: bool = False

    def __post_init__(self) -> None:
        if not _SAFE_IDENTIFIER.fullmatch(self.candidate_id):
            raise ValueError("candidate_id must be a non-sensitive slug")
        if not _SAFE_IDENTIFIER.fullmatch(self.profile):
            raise ValueError("profile must be a non-sensitive slug")
        if self.block_size is not None and self.block_size <= 0:
            raise ValueError("block_size must be positive")
        if self.block_size == 1 and not self.diagnostic_only:
            raise ValueError("block size 1 must remain diagnostic-only")
        if self.repeat_count < 0:
            raise ValueError("repeat_count must be non-negative")
        counts = (
            self.request_count,
            self.error_count,
            self.oom_count,
            self.crash_count,
            self.restart_count,
        )
        if any(value < 0 for value in counts):
            raise ValueError("candidate counts must be non-negative")
        objectives = self.objective_values()
        if any(
            value is not None and value < 0 for value in objectives.values()
        ):
            raise ValueError("objective values must be non-negative")
        for ratio in (
            self.prefix_cache_hit_ratio,
            self.fragmentation_ratio,
        ):
            if ratio is not None and not 0.0 <= ratio <= 1.0:
                raise ValueError("ratio objectives must be in [0, 1]")
        for interval in self.confidence_intervals().values():
            if interval is None:
                continue
            if (
                len(interval) != 2
                or not all(math.isfinite(value) for value in interval)
                or interval[0] > interval[1]
            ):
                raise ValueError("invalid confidence interval")

    def objective_values(self) -> dict[str, float | None]:
        return {
            "ttft_p95_ms": self.ttft_p95_ms,
            "e2e_p95_ms": self.e2e_p95_ms,
            "throughput_rps": self.throughput_rps,
            "prefix_cache_hit_ratio": self.prefix_cache_hit_ratio,
            "preemption_total": self.preemption_total,
            "fragmentation_ratio": self.fragmentation_ratio,
            "queue_p95_ms": self.queue_p95_ms,
            "gpu_memory_peak_bytes": self.gpu_memory_peak_bytes,
        }

    def confidence_intervals(
        self,
    ) -> dict[str, tuple[float, float] | None]:
        return {
            "ttft_p95_ms": self.ttft_p95_ci,
            "e2e_p95_ms": self.e2e_p95_ci,
            "throughput_rps": self.throughput_ci,
            "prefix_cache_hit_ratio": self.prefix_cache_hit_ci,
            "preemption_total": self.preemption_ci,
            "fragmentation_ratio": self.fragmentation_ci,
            "queue_p95_ms": self.queue_p95_ci,
            "gpu_memory_peak_bytes": self.gpu_memory_ci,
        }


@dataclass(frozen=True)
class SelectionPolicy:
    minimum_repeatable_improvement: float = 0.05
    minimum_repetitions: int = 3
    service_ttft_p95_limit_ms: float | None = None
    require_confidence_intervals: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= self.minimum_repeatable_improvement <= 1.0:
            raise ValueError("minimum improvement must be in [0, 1]")
        if self.minimum_repetitions <= 0:
            raise ValueError("minimum_repetitions must be positive")
        if (
            self.service_ttft_p95_limit_ms is not None
            and self.service_ttft_p95_limit_ms <= 0
        ):
            raise ValueError("service TTFT limit must be positive")


@dataclass(frozen=True)
class SelectionDecision:
    final_status: str
    selected_candidate_id: str | None
    selected_block_size: int | None
    pareto_frontier: tuple[str, ...]
    rejected: tuple[tuple[str, tuple[str, ...]], ...]
    reason: str


_MINIMIZE = frozenset(
    {
        "ttft_p95_ms",
        "e2e_p95_ms",
        "preemption_total",
        "fragmentation_ratio",
        "queue_p95_ms",
        "gpu_memory_peak_bytes",
    }
)
_MAXIMIZE = frozenset({"throughput_rps", "prefix_cache_hit_ratio"})
_THEORETICAL_ONLY = frozenset({"fragmentation_ratio"})


def _safety_reasons(item: CandidateSummary) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.error_count > 0:
        reasons.append("errors")
    if item.oom_count > 0:
        reasons.append("oom")
    if item.crash_count > 0:
        reasons.append("crash")
    if item.restart_count > 0:
        reasons.append("restart")
    if item.thermal_abort:
        reasons.append("thermal_abort")
    if not item.identity_safety_gate_passed:
        reasons.append("identity_or_safety_gate_failure")
    if item.production_impact_detected:
        reasons.append("production_impact")
    if item.host_memory_critical:
        reasons.append("host_memory_critical")
    if item.disk_critical:
        reasons.append("disk_critical")
    if not item.metrics_available:
        reasons.append("metrics_unavailable")
    if (
        item.request_count > 0
        and item.error_count / item.request_count > 0.01
        and "errors" not in reasons
    ):
        reasons.append("error_rate_above_one_percent")
    return tuple(reasons)


def _data_reasons(
    item: CandidateSummary, policy: SelectionPolicy
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.repeat_count < policy.minimum_repetitions:
        reasons.append("fewer_than_required_repetitions")
    if not item.baseline_auto and item.block_size is None:
        reasons.append("explicit_candidate_block_size_missing")
    values = item.objective_values()
    if any(value is None or not math.isfinite(value) for value in values.values()):
        reasons.append("incomplete_objectives")
    if (
        item.profile == "interactive"
        and policy.service_ttft_p95_limit_ms is None
        and not item.baseline_auto
    ):
        reasons.append("service_ttft_limit_missing")
    if (
        item.profile == "interactive"
        and policy.service_ttft_p95_limit_ms is not None
        and item.ttft_p95_ms is not None
        and item.ttft_p95_ms > policy.service_ttft_p95_limit_ms
    ):
        reasons.append("service_ttft_limit_violated")
    return tuple(reasons)


def _dominates(left: CandidateSummary, right: CandidateSummary) -> bool:
    left_values = left.objective_values()
    right_values = right.objective_values()
    all_no_worse = True
    any_better = False
    for key in _MINIMIZE | _MAXIMIZE:
        left_value = left_values[key]
        right_value = right_values[key]
        if left_value is None or right_value is None:
            return False
        if key in _MINIMIZE:
            all_no_worse &= left_value <= right_value
            any_better |= left_value < right_value
        else:
            all_no_worse &= left_value >= right_value
            any_better |= left_value > right_value
    return all_no_worse and any_better


def pareto_frontier(
    candidates: Iterable[CandidateSummary],
) -> tuple[CandidateSummary, ...]:
    """Return non-dominated candidates; callers must pre-filter invalid data."""

    values = tuple(candidates)
    return tuple(
        candidate
        for candidate in values
        if not any(
            other.candidate_id != candidate.candidate_id
            and _dominates(other, candidate)
            for other in values
        )
    )


def _percentage_improvement(
    baseline: float, candidate: float, *, minimize: bool
) -> float:
    if baseline == 0:
        return 0.0 if candidate == 0 else (-math.inf if minimize else math.inf)
    return (
        (baseline - candidate) / abs(baseline)
        if minimize
        else (candidate - baseline) / abs(baseline)
    )


def _intervals_overlap(
    left: tuple[float, float], right: tuple[float, float]
) -> bool:
    return max(left[0], right[0]) <= min(left[1], right[1])


def select_pareto_candidate(
    candidates: Iterable[CandidateSummary],
    *,
    baseline_candidate_id: str,
    policy: SelectionPolicy | None = None,
) -> SelectionDecision:
    """Select conservatively, never authorizing runtime mutation/deployment."""

    selection_policy = policy or SelectionPolicy()
    values = tuple(candidates)
    by_id = {item.candidate_id: item for item in values}
    if len(by_id) != len(values):
        raise ValueError("candidate IDs must be unique")
    baseline = by_id.get(baseline_candidate_id)
    if baseline is None or not baseline.baseline_auto:
        return SelectionDecision(
            final_status="BLOCKED_NO_CLEAR_WINNER",
            selected_candidate_id=None,
            selected_block_size=None,
            pareto_frontier=(),
            rejected=(),
            reason="platform auto baseline is missing",
        )

    rejected: dict[str, tuple[str, ...]] = {}
    baseline_safety = _safety_reasons(baseline)
    if baseline_safety:
        return SelectionDecision(
            final_status="BLOCKED_SAFETY",
            selected_candidate_id=None,
            selected_block_size=None,
            pareto_frontier=(),
            rejected=((baseline.candidate_id, baseline_safety),),
            reason="baseline failed a safety gate",
        )

    baseline_data = _data_reasons(baseline, selection_policy)
    if baseline_data:
        return SelectionDecision(
            final_status="BLOCKED_NO_CLEAR_WINNER",
            selected_candidate_id=None,
            selected_block_size=None,
            pareto_frontier=(),
            rejected=((baseline.candidate_id, baseline_data),),
            reason="baseline data is incomplete",
        )

    valid = [baseline]
    incomplete_candidate = False
    for item in values:
        if item.candidate_id == baseline_candidate_id:
            continue
        if item.diagnostic_only:
            rejected[item.candidate_id] = ("diagnostic_only",)
            continue
        safety = _safety_reasons(item)
        if safety:
            rejected[item.candidate_id] = safety
            continue
        data = _data_reasons(item, selection_policy)
        if data:
            rejected[item.candidate_id] = data
            if data != ("service_ttft_limit_violated",):
                incomplete_candidate = True
            continue
        valid.append(item)

    if incomplete_candidate:
        return SelectionDecision(
            final_status="BLOCKED_NO_CLEAR_WINNER",
            selected_candidate_id=None,
            selected_block_size=None,
            pareto_frontier=(),
            rejected=tuple(sorted(rejected.items())),
            reason="candidate data or service constraints are incomplete",
        )
    if len(valid) == 1:
        return SelectionDecision(
            final_status="KEEP_PLATFORM_DEFAULT",
            selected_candidate_id=baseline.candidate_id,
            selected_block_size=baseline.block_size,
            pareto_frontier=(baseline.candidate_id,),
            rejected=tuple(sorted(rejected.items())),
            reason="no valid explicit candidate displaced the baseline",
        )

    frontier = pareto_frontier(valid)
    frontier_ids = tuple(item.candidate_id for item in frontier)
    nonbaseline = [
        item for item in frontier if item.candidate_id != baseline_candidate_id
    ]
    if baseline in frontier or len(nonbaseline) != 1:
        return SelectionDecision(
            final_status="BLOCKED_NO_CLEAR_WINNER",
            selected_candidate_id=None,
            selected_block_size=None,
            pareto_frontier=frontier_ids,
            rejected=tuple(sorted(rejected.items())),
            reason="Pareto frontier does not contain one clear baseline replacement",
        )

    winner = nonbaseline[0]
    baseline_values = baseline.objective_values()
    winner_values = winner.objective_values()
    improvements = {
        key: _percentage_improvement(
            float(baseline_values[key]),
            float(winner_values[key]),
            minimize=key in _MINIMIZE,
        )
        for key in _MINIMIZE | _MAXIMIZE
    }
    improved_metrics = {
        key: gain for key, gain in improvements.items() if gain > 0
    }
    empirical_improved_metrics = {
        key: gain
        for key, gain in improved_metrics.items()
        if key not in _THEORETICAL_ONLY
    }
    maximum_gain = max(empirical_improved_metrics.values(), default=0.0)
    if maximum_gain < selection_policy.minimum_repeatable_improvement:
        return SelectionDecision(
            final_status="KEEP_PLATFORM_DEFAULT",
            selected_candidate_id=baseline.candidate_id,
            selected_block_size=baseline.block_size,
            pareto_frontier=frontier_ids,
            rejected=tuple(sorted(rejected.items())),
            reason=(
                "empirical repeatable improvement is below the five-percent "
                "policy; theoretical fragmentation cannot choose a winner"
            ),
        )

    if selection_policy.require_confidence_intervals:
        baseline_ci = baseline.confidence_intervals()
        winner_ci = winner.confidence_intervals()
        for key in empirical_improved_metrics:
            if baseline_ci[key] is None or winner_ci[key] is None:
                return SelectionDecision(
                    final_status="BLOCKED_NO_CLEAR_WINNER",
                    selected_candidate_id=None,
                    selected_block_size=None,
                    pareto_frontier=frontier_ids,
                    rejected=tuple(sorted(rejected.items())),
                    reason="confidence interval data is incomplete",
                )
            if _intervals_overlap(baseline_ci[key], winner_ci[key]):
                return SelectionDecision(
                    final_status="BLOCKED_NO_CLEAR_WINNER",
                    selected_candidate_id=None,
                    selected_block_size=None,
                    pareto_frontier=frontier_ids,
                    rejected=tuple(sorted(rejected.items())),
                    reason="confidence intervals overlap on an improved objective",
                )

    return SelectionDecision(
        final_status="READY_FOR_OWNER_APPROVED_CANARY",
        selected_candidate_id=winner.candidate_id,
        selected_block_size=winner.block_size,
        pareto_frontier=frontier_ids,
        rejected=tuple(sorted(rejected.items())),
        reason=(
            "one complete, non-overlapping Pareto candidate exceeds the "
            "repeatable-improvement threshold; owner approval is still required"
        ),
    )


select_candidate = select_pareto_candidate


def _redact_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return redact_mapping(value)
    if isinstance(value, (list, tuple)):
        return [_redact_value(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value


def redact_mapping(values: Mapping[str, Any]) -> dict[str, Any]:
    """Redact arbitrary diagnostic mappings before optional human display."""

    safe: dict[str, Any] = {}
    for key, value in values.items():
        normalized = key.lower()
        if any(
            marker in normalized
            for marker in (
                "prompt",
                "secret",
                "password",
                "authorization",
                "api_key",
                "api-key",
                "endpoint",
                "url",
                "cache_salt",
                "tenant",
                "user_id",
                "token_ids",
            )
        ):
            safe[key] = "<redacted>"
        else:
            safe[key] = _redact_value(value)
    return safe
