"""Offline Prometheus parsing and version-aware vLLM metric discovery.

The adapter accepts caller-supplied text.  It intentionally has no HTTP client
and therefore cannot contact production or canary endpoints by itself.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable, Mapping


class PrometheusParseError(ValueError):
    """Raised when an input cannot be parsed within safety limits."""


_METRIC_NAME = r"[A-Za-z_:][A-Za-z0-9_:]*"
_METRIC_RE = re.compile(
    rf"^(?P<name>{_METRIC_NAME})(?:\{{(?P<labels>.*)\}})?"
    r"\s+(?P<value>[^\s]+)(?:\s+(?P<timestamp>[0-9]+))?$"
)
_TYPE_RE = re.compile(
    rf"^#\s*TYPE\s+(?P<name>{_METRIC_NAME})\s+"
    r"(?P<type>counter|gauge|histogram|gaugehistogram|summary|info|stateset|unknown)$"
)
_LABEL_RE = re.compile(
    r'\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*'
    r'"(?P<value>(?:\\.|[^"\\])*)"\s*(?P<separator>,|$)'
)
_SAFE_LABEL_NAMES = frozenset(
    {
        "le",
        "quantile",
        "method",
        "status",
        "reason",
        "engine",
        "worker",
        "finished_reason",
        "cache_type",
        "request_type",
        "version",
    }
)
_SENSITIVE_LABEL_FRAGMENTS = (
    "prompt",
    "tenant",
    "user",
    "request_id",
    "api",
    "authorization",
    "secret",
    "salt",
    "endpoint",
    "url",
    "path",
    "token_id",
)
_SAFE_LABEL_VALUE_RE = re.compile(r"^[A-Za-z0-9_.+-]{0,64}$")
_MAX_INPUT_BYTES = 5_000_000
_MAX_LINE_LENGTH = 65_536
_MAX_SAMPLES = 250_000
_MAX_LABELS_PER_SAMPLE = 64
REDACTED = "<redacted>"


@dataclass(frozen=True)
class MetricSample:
    name: str
    labels: tuple[tuple[str, str], ...]
    value: float
    timestamp_ms: int | None = None

    def label_dict(self) -> dict[str, str]:
        return dict(self.labels)


@dataclass(frozen=True)
class MetricFamily:
    name: str
    metric_type: str | None
    samples: tuple[MetricSample, ...]


@dataclass(frozen=True)
class ParsedPrometheus:
    families: tuple[MetricFamily, ...]
    issues: tuple[str, ...]
    redacted_label_count: int

    @property
    def samples(self) -> tuple[MetricSample, ...]:
        return tuple(
            sample for family in self.families for sample in family.samples
        )

    @property
    def sample_names(self) -> frozenset[str]:
        return frozenset(sample.name for sample in self.samples)


def _unescape_label(value: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char != "\\":
            result.append(char)
            index += 1
            continue
        index += 1
        if index >= len(value):
            raise PrometheusParseError("trailing label escape")
        escaped = value[index]
        if escaped == "n":
            result.append("\n")
        elif escaped in {'"', "\\"}:
            result.append(escaped)
        else:
            raise PrometheusParseError("unsupported label escape")
        index += 1
    return "".join(result)


def _redact_label(name: str, value: str) -> tuple[str, bool]:
    normalized = name.lower()
    sensitive = any(
        fragment in normalized for fragment in _SENSITIVE_LABEL_FRAGMENTS
    )
    if (
        sensitive
        or name not in _SAFE_LABEL_NAMES
        or not _SAFE_LABEL_VALUE_RE.fullmatch(value)
    ):
        return REDACTED, True
    return value, False


def _parse_labels(raw: str) -> tuple[tuple[tuple[str, str], ...], int]:
    if not raw.strip():
        return (), 0
    labels: list[tuple[str, str]] = []
    redacted = 0
    position = 0
    while position < len(raw):
        match = _LABEL_RE.match(raw, position)
        if match is None:
            raise PrometheusParseError("malformed metric labels")
        value = _unescape_label(match.group("value"))
        safe_value, was_redacted = _redact_label(match.group("name"), value)
        labels.append((match.group("name"), safe_value))
        redacted += int(was_redacted)
        if len(labels) > _MAX_LABELS_PER_SAMPLE:
            raise PrometheusParseError("too many labels in sample")
        position = match.end()
        if match.group("separator") == "":
            break
        if position >= len(raw):
            raise PrometheusParseError("trailing metric label separator")
    if position != len(raw):
        raise PrometheusParseError("trailing metric label content")
    names = [name for name, _ in labels]
    if len(names) != len(set(names)):
        raise PrometheusParseError("duplicate metric label")
    return tuple(sorted(labels)), redacted


def _parse_value(raw: str) -> float:
    normalized = raw
    if raw == "+Inf":
        normalized = "inf"
    elif raw == "-Inf":
        normalized = "-inf"
    elif raw == "NaN":
        normalized = "nan"
    try:
        value = float(normalized)
    except ValueError as exc:
        raise PrometheusParseError("invalid metric value") from exc
    return value


def _family_name(
    sample_name: str, declared_types: Mapping[str, str]
) -> str:
    if sample_name in declared_types:
        return sample_name
    for suffix in ("_bucket", "_sum", "_count", "_created", "_info"):
        if sample_name.endswith(suffix):
            base = sample_name[: -len(suffix)]
            if base in declared_types:
                return base
    return sample_name


def parse_prometheus_text(
    text: str, *, strict: bool = True
) -> ParsedPrometheus:
    """Parse bounded Prometheus/OpenMetrics text and sanitize every label."""

    if not isinstance(text, str):
        raise TypeError("Prometheus input must be text")
    if len(text.encode("utf-8")) > _MAX_INPUT_BYTES:
        raise PrometheusParseError("Prometheus input exceeds size limit")

    declared_types: dict[str, str] = {}
    raw_samples: list[MetricSample] = []
    issues: list[str] = []
    redacted_count = 0
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if len(raw_line) > _MAX_LINE_LENGTH:
            raise PrometheusParseError("Prometheus line exceeds size limit")
        line = raw_line.strip()
        if not line or line == "# EOF" or line.startswith("# HELP"):
            continue
        type_match = _TYPE_RE.fullmatch(line)
        if type_match:
            declared_types[type_match.group("name")] = type_match.group("type")
            continue
        if line.startswith("#"):
            continue
        try:
            match = _METRIC_RE.fullmatch(line)
            if match is None:
                raise PrometheusParseError("malformed metric sample")
            labels, redacted = _parse_labels(match.group("labels") or "")
            timestamp_raw = match.group("timestamp")
            raw_samples.append(
                MetricSample(
                    name=match.group("name"),
                    labels=labels,
                    value=_parse_value(match.group("value")),
                    timestamp_ms=(
                        int(timestamp_raw) if timestamp_raw is not None else None
                    ),
                )
            )
            redacted_count += redacted
            if len(raw_samples) > _MAX_SAMPLES:
                raise PrometheusParseError("too many metric samples")
        except PrometheusParseError as exc:
            if strict:
                raise PrometheusParseError(
                    f"metric parse error at line {line_number}: {exc}"
                ) from exc
            issues.append(f"line_{line_number}:{exc}")

    grouped: dict[str, list[MetricSample]] = {}
    for sample in raw_samples:
        grouped.setdefault(
            _family_name(sample.name, declared_types), []
        ).append(sample)
    families = tuple(
        MetricFamily(
            name=name,
            metric_type=declared_types.get(name),
            samples=tuple(grouped[name]),
        )
        for name in sorted(grouped)
    )
    return ParsedPrometheus(
        families=families,
        issues=tuple(issues),
        redacted_label_count=redacted_count,
    )


@dataclass(frozen=True)
class MetricMapProfile:
    name: str
    minimum_version: tuple[int, int, int] | None
    maximum_version: tuple[int, int, int] | None
    aliases: Mapping[str, tuple[str, ...]]


_LEGACY_ALIASES: dict[str, tuple[str, ...]] = {
    "request_success_total": ("vllm:request_success_total",),
    "prompt_tokens_total": ("vllm:prompt_tokens_total",),
    "generation_tokens_total": ("vllm:generation_tokens_total",),
    "ttft_seconds": ("vllm:time_to_first_token_seconds",),
    "tpot_seconds": ("vllm:time_per_output_token_seconds",),
    "itl_seconds": ("vllm:inter_token_latency_seconds",),
    "e2e_seconds": ("vllm:e2e_request_latency_seconds",),
    "queue_seconds": ("vllm:request_queue_time_seconds",),
    "prefill_seconds": ("vllm:request_prefill_time_seconds",),
    "decode_seconds": ("vllm:request_decode_time_seconds",),
    "kv_cache_usage": ("vllm:gpu_cache_usage_perc",),
    "preemption_total": ("vllm:num_preemptions_total",),
    "requests_waiting": ("vllm:num_requests_waiting",),
    "prefix_cache_queries": ("vllm:prefix_cache_queries",),
    "prefix_cache_hits": ("vllm:prefix_cache_hits",),
}

_CURRENT_ALIASES: dict[str, tuple[str, ...]] = {
    **_LEGACY_ALIASES,
    "kv_cache_usage": (
        "vllm:kv_cache_usage_perc",
        "vllm:gpu_cache_usage_perc",
    ),
    "prefix_cache_queries": (
        "vllm:prefix_cache_queries_total",
        "vllm:prefix_cache_queries",
        "vllm:gpu_prefix_cache_queries",
    ),
    "prefix_cache_hits": (
        "vllm:prefix_cache_hits_total",
        "vllm:prefix_cache_hits",
        "vllm:gpu_prefix_cache_hits",
    ),
}

_PROFILES = (
    MetricMapProfile(
        name="vllm_pre_0_11",
        minimum_version=None,
        maximum_version=(0, 10, 99),
        aliases=_LEGACY_ALIASES,
    ),
    MetricMapProfile(
        name="vllm_0_11_plus",
        minimum_version=(0, 11, 0),
        maximum_version=None,
        aliases=_CURRENT_ALIASES,
    ),
)

REQUIRED_SEMANTICS = frozenset(
    {
        "request_success_total",
        "prompt_tokens_total",
        "generation_tokens_total",
        "ttft_seconds",
        "tpot_seconds",
        "itl_seconds",
        "e2e_seconds",
        "queue_seconds",
        "prefill_seconds",
        "decode_seconds",
        "kv_cache_usage",
        "preemption_total",
        "requests_waiting",
        "prefix_cache_queries",
        "prefix_cache_hits",
    }
)


def _parse_version(version: str | None) -> tuple[int, int, int] | None:
    if not version:
        return None
    match = re.search(r"(?<!\d)(\d+)\.(\d+)(?:\.(\d+))?", version)
    if match is None:
        return None
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3) or 0),
    )


def _profile_for_version(
    version: str | None,
) -> tuple[str, Mapping[str, tuple[str, ...]], tuple[str, ...]]:
    parsed = _parse_version(version)
    if parsed is not None:
        for profile in _PROFILES:
            if (
                profile.minimum_version is not None
                and parsed < profile.minimum_version
            ):
                continue
            if (
                profile.maximum_version is not None
                and parsed > profile.maximum_version
            ):
                continue
            return profile.name, profile.aliases, ()

    merged: dict[str, list[str]] = {}
    for profile in _PROFILES:
        for semantic, aliases in profile.aliases.items():
            bucket = merged.setdefault(semantic, [])
            for alias in aliases:
                if alias not in bucket:
                    bucket.append(alias)
    return (
        "unknown_version_discovery_only",
        {key: tuple(value) for key, value in merged.items()},
        ("vLLM version is unknown; aliases are discovered but not assumed",),
    )


@dataclass(frozen=True)
class MetricDiscovery:
    profile: str
    vllm_version: str | None
    mapping: tuple[tuple[str, str], ...]
    missing_required: tuple[str, ...]
    available_families: tuple[str, ...]
    parse_issues: tuple[str, ...]
    warnings: tuple[str, ...]
    redacted_label_count: int

    @property
    def required_metrics_available(self) -> bool:
        return not self.missing_required and not self.parse_issues

    def mapping_dict(self) -> dict[str, str]:
        return dict(self.mapping)


def discover_vllm_metrics(
    metrics: str | ParsedPrometheus,
    *,
    vllm_version: str | None,
    strict: bool = True,
) -> MetricDiscovery:
    """Map observed families using a version-selected alias profile."""

    parsed = (
        parse_prometheus_text(metrics, strict=strict)
        if isinstance(metrics, str)
        else metrics
    )
    profile_name, aliases, warnings = _profile_for_version(vllm_version)
    available_samples = {
        sample.name for sample in parsed.samples if math.isfinite(sample.value)
    }
    available_families = {
        family.name
        for family in parsed.families
        if any(math.isfinite(sample.value) for sample in family.samples)
    }
    available = frozenset(available_samples | available_families)
    mapping: dict[str, str] = {}
    for semantic, candidates in aliases.items():
        for candidate in candidates:
            if candidate in available:
                mapping[semantic] = candidate
                break
    missing = tuple(sorted(REQUIRED_SEMANTICS - set(mapping)))
    return MetricDiscovery(
        profile=profile_name,
        vllm_version=vllm_version,
        mapping=tuple(sorted(mapping.items())),
        missing_required=missing,
        available_families=tuple(
            sorted(family.name for family in parsed.families)
        ),
        parse_issues=parsed.issues,
        warnings=warnings,
        redacted_label_count=parsed.redacted_label_count,
    )


def finite_sample_values(
    parsed: ParsedPrometheus, metric_name: str
) -> tuple[float, ...]:
    """Return finite values for one discovered sample/family name."""

    values = tuple(
        sample.value
        for sample in parsed.samples
        if sample.name == metric_name and math.isfinite(sample.value)
    )
    return values
