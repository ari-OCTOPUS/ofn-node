"""Planning and safety primitives for vLLM KV-cache block-size experiments.

This module is deliberately offline-only.  It does not import vLLM, contact an
endpoint, inspect process command lines, or start/stop a process.  A block-size
estimate is theoretical evidence only; it is never a deployment decision.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import math
import os
import platform
import random
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlsplit


FINAL_STATUSES = frozenset(
    {
        "READY_FOR_OWNER_APPROVED_CANARY",
        "READY_FOR_OWNER_APPROVED_DEPLOYMENT",
        "KEEP_PLATFORM_DEFAULT",
        "BLOCKED_NO_GPU",
        "BLOCKED_VERSION",
        "BLOCKED_METRICS",
        "BLOCKED_SAFETY",
        "BLOCKED_NO_CLEAR_WINNER",
    }
)


class PlanningError(RuntimeError):
    """Raised when version-resolved candidate planning is impossible."""


class SafetyValidationError(ValueError):
    """Raised when a proposed canary violates a WAVE0 safety invariant."""


@dataclass(frozen=True)
class FragmentationEstimate:
    block_size: int
    request_count: int
    logical_tokens: int
    allocated_tokens: int
    wasted_tokens: int
    fragmentation_ratio: float
    mean_waste_per_request: float


def estimate_fragmentation(
    lengths: Iterable[int], block_size: int
) -> FragmentationEstimate:
    """Estimate theoretical per-request tail allocation waste.

    The estimate excludes allocator metadata, hybrid-attention grouping,
    replication, physical-page padding, and external cache-transfer chunking.
    Resolved vLLM profiling remains the source of truth.
    """

    if (
        not isinstance(block_size, int)
        or isinstance(block_size, bool)
        or block_size <= 0
    ):
        raise ValueError("block_size must be positive")
    values = tuple(lengths)
    if not values or any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
        for value in values
    ):
        raise ValueError(
            "lengths must be non-empty non-negative integer token counts"
        )

    allocated = tuple(
        ((value + block_size - 1) // block_size) * block_size
        for value in values
    )
    waste = tuple(
        allocated_value - logical_value
        for allocated_value, logical_value in zip(allocated, values)
    )
    total_allocated = sum(allocated)
    total_waste = sum(waste)
    return FragmentationEstimate(
        block_size=block_size,
        request_count=len(values),
        logical_tokens=sum(values),
        allocated_tokens=total_allocated,
        wasted_tokens=total_waste,
        fragmentation_ratio=(
            total_waste / total_allocated if total_allocated else 0.0
        ),
        mean_waste_per_request=mean(waste),
    )


def tail_waste_tokens(length: int, block_size: int) -> int:
    """Return ``(block_size - length % block_size) % block_size``."""

    if length < 0:
        raise ValueError("length must be non-negative")
    if block_size <= 0:
        raise ValueError("block_size must be positive")
    return (block_size - (length % block_size)) % block_size


def divisible_block_tail_waste_property(
    length: int, smaller_block_size: int, larger_block_size: int
) -> bool:
    """Check the correctly scoped tail-waste monotonicity property.

    A smaller block does *not* universally have less tail waste than every
    larger block.  The property is guaranteed when the smaller block size
    divides the larger one.  For example, 8 divides 16, so 8-versus-16 is
    inside this restricted guarantee; a genuine inversion is 6 versus 8 at
    length 7 (waste 5 versus 1).
    """

    if smaller_block_size <= 0 or larger_block_size <= 0:
        raise ValueError("block sizes must be positive")
    if smaller_block_size > larger_block_size:
        raise ValueError("smaller_block_size must be <= larger_block_size")
    if larger_block_size % smaller_block_size:
        raise ValueError("smaller_block_size must divide larger_block_size")
    return tail_waste_tokens(
        length, smaller_block_size
    ) <= tail_waste_tokens(length, larger_block_size)


def apc_unreused_suffix_tokens(prefix_length: int, block_size: int) -> int:
    """Return the suffix APC cannot reuse because APC reuses full blocks only."""

    if prefix_length < 0:
        raise ValueError("prefix_length must be non-negative")
    if block_size <= 0:
        raise ValueError("block_size must be positive")
    return prefix_length % block_size


@dataclass(frozen=True)
class FullAttentionKvEstimate:
    bytes_per_token: float
    bytes_per_block: float
    block_size: int
    limitations: tuple[str, ...]


def estimate_full_attention_kv_bytes(
    *,
    num_layers: int,
    num_kv_heads: int,
    head_dim: int,
    bytes_per_element: int,
    tensor_parallel_sharding: int,
    block_size: int,
) -> FullAttentionKvEstimate:
    """Apply the documented full-attention approximation.

    This is intentionally not used by candidate selection.
    """

    values = (
        num_layers,
        num_kv_heads,
        head_dim,
        bytes_per_element,
        tensor_parallel_sharding,
        block_size,
    )
    if any(value <= 0 for value in values):
        raise ValueError("KV geometry inputs must be positive")
    bytes_per_token = (
        2
        * num_layers
        * num_kv_heads
        * head_dim
        * bytes_per_element
        / tensor_parallel_sharding
    )
    return FullAttentionKvEstimate(
        bytes_per_token=bytes_per_token,
        bytes_per_block=block_size * bytes_per_token,
        block_size=block_size,
        limitations=(
            "full-attention approximation only",
            "resolved vLLM cache profiling is authoritative",
            "replication, hybrid groups, page padding, and metadata excluded",
            "LMCache/external transfer chunks are a separate setting",
        ),
    )


@dataclass(frozen=True)
class BlockSizePlan:
    """Version/capability-resolved logical vLLM block-size plan."""

    baseline_auto: bool
    candidates: tuple[int, ...]
    diagnostic_candidates: tuple[int, ...] = ()
    backend: str = "UNKNOWN"
    vllm_version: str | None = None
    capability_source: str | None = None

    def __post_init__(self) -> None:
        if not self.baseline_auto:
            raise ValueError("platform-selected baseline_auto must be represented")
        if len(set(self.candidates)) != len(self.candidates):
            raise ValueError("candidates must be unique")
        if len(set(self.diagnostic_candidates)) != len(
            self.diagnostic_candidates
        ):
            raise ValueError("diagnostic_candidates must be unique")
        if any(value <= 0 for value in self.candidates):
            raise ValueError("candidates must be positive")
        if any(value <= 0 for value in self.diagnostic_candidates):
            raise ValueError("diagnostic candidates must be positive")
        if set(self.candidates) & set(self.diagnostic_candidates):
            raise ValueError("diagnostic candidates must stay separate")
        if self.backend.upper() == "CUDA" and any(
            value > 32 for value in self.candidates
        ):
            raise ValueError("CUDA production candidates must not exceed 32")

    @property
    def represented_block_sizes(self) -> tuple[int | None, ...]:
        """Return ``None`` for platform auto, followed by production sizes."""

        return (None, *self.candidates)


def _normalize_supported(supported: Iterable[int]) -> set[int]:
    values = set(supported)
    if any(not isinstance(value, int) or isinstance(value, bool) for value in values):
        raise ValueError("supported block sizes must be integers")
    if any(value <= 0 for value in values):
        raise ValueError("supported block sizes must be positive")
    return values


def cuda_plan(
    supported: set[int],
    *,
    enable_diagnostic_size_one: bool = False,
    vllm_version: str | None = None,
    capability_source: str | None = None,
) -> BlockSizePlan:
    """Plan CUDA candidates from an observed supported set.

    Sizes 64/128/256 are never emitted.  Size 1 stays in a separate diagnostic
    lane and is included only after explicit opt-in plus observed support.
    """

    supported_values = _normalize_supported(supported)
    preferred = (8, 16, 32)
    candidates = tuple(
        value
        for value in preferred
        if value in supported_values and value <= 32
    )
    if not candidates:
        raise PlanningError("No supported CUDA KV block-size candidate")
    diagnostics = (
        (1,)
        if enable_diagnostic_size_one and 1 in supported_values
        else ()
    )
    return BlockSizePlan(
        baseline_auto=True,
        candidates=candidates,
        diagnostic_candidates=diagnostics,
        backend="CUDA",
        vllm_version=vllm_version,
        capability_source=capability_source,
    )


def backend_plan(
    *,
    backend: str,
    supported: Iterable[int] | None,
    vllm_version: str | None,
    capability_source: str | None,
    enable_diagnostic_size_one: bool = False,
) -> BlockSizePlan:
    """Build a backend-aware plan without guessing unsupported values."""

    normalized_backend = backend.strip().upper()
    if not normalized_backend:
        raise PlanningError("backend is required")
    if supported is None:
        raise PlanningError("version/capability supplied candidates are required")
    supported_values = _normalize_supported(supported)
    if normalized_backend == "CUDA":
        return cuda_plan(
            supported_values,
            enable_diagnostic_size_one=enable_diagnostic_size_one,
            vllm_version=vllm_version,
            capability_source=capability_source,
        )
    if not vllm_version or not capability_source:
        raise PlanningError(
            "non-CUDA candidates require vLLM version and capability source"
        )
    production = tuple(sorted(value for value in supported_values if value != 1))
    if not production:
        raise PlanningError(
            "no non-diagnostic candidate supplied by backend capability"
        )
    diagnostics = (
        (1,)
        if enable_diagnostic_size_one and 1 in supported_values
        else ()
    )
    return BlockSizePlan(
        baseline_auto=True,
        candidates=production,
        diagnostic_candidates=diagnostics,
        backend=normalized_backend,
        vllm_version=vllm_version,
        capability_source=capability_source,
    )


@dataclass(frozen=True)
class CandidateRunPlan:
    """One immutable fresh-process canary plan."""

    run_id: str
    baseline_auto: bool
    block_size: int | None
    diagnostic_only: bool
    order: int
    canary_host: str
    canary_port: int
    cache_path: str
    data_path: str
    server_configuration: tuple[tuple[str, Any], ...]
    fresh_process_required: bool = True
    dynamic_block_size_mutation_allowed: bool = False


def changed_configuration_keys(
    baseline: Mapping[str, Any], candidate: Mapping[str, Any]
) -> frozenset[str]:
    """Return semantic settings whose values differ."""

    missing = object()
    return frozenset(
        key
        for key in set(baseline) | set(candidate)
        if baseline.get(key, missing) != candidate.get(key, missing)
    )


def validate_only_block_size_varies(
    baseline: Mapping[str, Any], candidate: Mapping[str, Any]
) -> None:
    """Reject candidate semantic configuration drift."""

    changed = changed_configuration_keys(baseline, candidate)
    if changed != frozenset({"block_size"}):
        raise SafetyValidationError(
            "candidate must differ from baseline only by block_size"
        )


def randomized_run_values(
    plan: BlockSizePlan,
    *,
    seed: int,
    include_diagnostics: bool = False,
) -> tuple[tuple[int | None, bool], ...]:
    """Return deterministic randomized auto/explicit run values."""

    values: list[tuple[int | None, bool]] = [
        (None, False),
        *((value, False) for value in plan.candidates),
    ]
    if include_diagnostics:
        values.extend((value, True) for value in plan.diagnostic_candidates)
    random.Random(seed).shuffle(values)
    return tuple(values)


def build_candidate_run_plans(
    plan: BlockSizePlan,
    *,
    baseline_server_configuration: Mapping[str, Any],
    seed: int,
    canary_host: str,
    first_canary_port: int,
    cache_root: str | Path,
    data_root: str | Path,
    include_diagnostics: bool = False,
) -> tuple[CandidateRunPlan, ...]:
    """Create isolated, randomized plans; this function launches nothing."""

    if "block_size" in baseline_server_configuration:
        raise SafetyValidationError(
            "baseline auto must omit block_size from server configuration"
        )
    if not (1 <= first_canary_port <= 65535):
        raise SafetyValidationError("invalid first canary port")
    values = randomized_run_values(
        plan, seed=seed, include_diagnostics=include_diagnostics
    )
    if first_canary_port + len(values) - 1 > 65535:
        raise SafetyValidationError("canary port range exceeds 65535")

    cache_base = Path(cache_root)
    data_base = Path(data_root)
    if cache_base == data_base:
        raise SafetyValidationError("cache and data roots must be separate")

    run_plans: list[CandidateRunPlan] = []
    for order, (block_size, diagnostic) in enumerate(values):
        label = "baseline-auto" if block_size is None else f"block-{block_size}"
        if diagnostic:
            label = f"diagnostic-{label}"
        run_id = f"run-{order:02d}-{label}"
        config = dict(baseline_server_configuration)
        if block_size is not None:
            config["block_size"] = block_size
            baseline_for_comparison = dict(baseline_server_configuration)
            baseline_for_comparison["block_size"] = None
            validate_only_block_size_varies(
                baseline_for_comparison, config
            )
        run_plans.append(
            CandidateRunPlan(
                run_id=run_id,
                baseline_auto=block_size is None,
                block_size=block_size,
                diagnostic_only=diagnostic,
                order=order,
                canary_host=canary_host,
                canary_port=first_canary_port + order,
                cache_path=str(cache_base / run_id),
                data_path=str(data_base / run_id),
                server_configuration=tuple(sorted(config.items())),
            )
        )
    return tuple(run_plans)


def _normalized_endpoint(endpoint: str) -> tuple[str, str, int]:
    raw = endpoint.strip()
    if not raw:
        raise SafetyValidationError("endpoint must not be empty")
    parsed = urlsplit(raw if "://" in raw else f"http://{raw}")
    if parsed.scheme not in {"http", "https"}:
        raise SafetyValidationError("endpoint scheme must be http or https")
    if parsed.username or parsed.password:
        raise SafetyValidationError("endpoint credentials are forbidden")
    if parsed.query or parsed.fragment:
        raise SafetyValidationError("endpoint query and fragment are forbidden")
    if parsed.path not in {"", "/"}:
        raise SafetyValidationError("endpoint must be an origin, not an API path")
    if not parsed.hostname:
        raise SafetyValidationError("endpoint hostname is required")
    try:
        port = parsed.port
    except ValueError as exc:
        raise SafetyValidationError("endpoint port is invalid") from exc
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    return parsed.scheme, parsed.hostname.lower().rstrip("."), port


def validate_canary_endpoint(
    candidate_endpoint: str, production_endpoints: Sequence[str]
) -> None:
    """Reject exact or clearly production-labelled endpoint origins."""

    normalized_candidate = _normalized_endpoint(candidate_endpoint)
    production = {
        _normalized_endpoint(endpoint) for endpoint in production_endpoints
    }
    if normalized_candidate in production:
        raise SafetyValidationError("production endpoint is forbidden")
    host_labels = normalized_candidate[1].replace("_", "-").split(".")
    if any(label in {"prod", "production"} for label in host_labels):
        raise SafetyValidationError("production-labelled endpoint is forbidden")


_APPROVAL_REFERENCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$")


@dataclass(frozen=True)
class CanaryLaunchAuthorization:
    owner_approved: bool
    owner_approval_reference: str | None
    owner_thermal_limit_c: float | None
    metrics_available: bool
    candidate_endpoint: str
    production_endpoints: tuple[str, ...] = ()


def validate_canary_launch_authorization(
    authorization: CanaryLaunchAuthorization,
) -> None:
    """Enforce the hard approval, thermal, metrics, and endpoint gates."""

    if not authorization.owner_approved:
        raise SafetyValidationError("explicit owner approval is required")
    reference = authorization.owner_approval_reference
    if not reference or not _APPROVAL_REFERENCE_RE.fullmatch(reference):
        raise SafetyValidationError("a non-sensitive owner approval reference is required")
    limit = authorization.owner_thermal_limit_c
    if limit is None or not math.isfinite(limit) or limit <= 0:
        raise SafetyValidationError("owner-defined thermal limit is required")
    if not authorization.metrics_available:
        raise SafetyValidationError("required metrics must be available")
    validate_canary_endpoint(
        authorization.candidate_endpoint,
        authorization.production_endpoints,
    )


@dataclass(frozen=True)
class SafetyObservation:
    request_count: int = 0
    error_count: int = 0
    oom_count: int = 0
    gpu_reset_or_xid: bool = False
    crash_loop: bool = False
    gpu_temperature_peak_c: float | None = None
    host_memory_critical: bool = False
    disk_critical: bool = False
    production_impact_detected: bool = False
    consecutive_metrics_unavailable: int = 0
    identity_safety_gate_passed: bool = True

    def __post_init__(self) -> None:
        counts = (
            self.request_count,
            self.error_count,
            self.oom_count,
            self.consecutive_metrics_unavailable,
        )
        if any(value < 0 for value in counts):
            raise ValueError("safety observation counts must be non-negative")
        if self.error_count > self.request_count:
            raise ValueError("error_count cannot exceed request_count")
        if (
            self.gpu_temperature_peak_c is not None
            and not math.isfinite(self.gpu_temperature_peak_c)
        ):
            raise ValueError("GPU temperature must be finite")


def evaluate_abort_conditions(
    observation: SafetyObservation, *, owner_thermal_limit_c: float
) -> tuple[str, ...]:
    """Return immediate-abort reasons using an owner-supplied thermal limit."""

    if not math.isfinite(owner_thermal_limit_c) or owner_thermal_limit_c <= 0:
        raise ValueError("owner_thermal_limit_c must be supplied and positive")
    reasons: list[str] = []
    if observation.oom_count > 0:
        reasons.append("gpu_oom")
    if observation.gpu_reset_or_xid:
        reasons.append("gpu_reset_or_xid")
    if observation.crash_loop:
        reasons.append("vllm_crash_loop")
    if observation.request_count > 0 and (
        observation.error_count / observation.request_count
    ) > 0.01:
        reasons.append("error_rate_above_one_percent")
    if (
        observation.gpu_temperature_peak_c is not None
        and observation.gpu_temperature_peak_c > owner_thermal_limit_c
    ):
        reasons.append("owner_thermal_limit_exceeded")
    if observation.host_memory_critical:
        reasons.append("host_memory_critical")
    if observation.disk_critical:
        reasons.append("disk_critical")
    if observation.production_impact_detected:
        reasons.append("production_endpoint_impact")
    if observation.consecutive_metrics_unavailable >= 2:
        reasons.append("metrics_unavailable_two_consecutive_runs")
    if not observation.identity_safety_gate_passed:
        reasons.append("identity_or_safety_gate_failure")
    return tuple(reasons)


def _package_availability(distribution: str, module: str) -> dict[str, Any]:
    try:
        available = importlib.util.find_spec(module) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        available = False
    version: str | None = None
    try:
        version = importlib.metadata.version(distribution)
        available = True
    except importlib.metadata.PackageNotFoundError:
        pass
    return {"available": available, "version": version}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def collect_local_preflight(*, observed_at_utc: str | None = None) -> dict[str, Any]:
    """Collect non-invasive Orange Pi facts without commands or network calls."""

    command_availability = {
        name: shutil.which(name) is not None
        for name in (
            "vllm",
            "nvidia-smi",
            "nvcc",
            "rocminfo",
            "rocm-smi",
            "hipcc",
            "node",
        )
    }
    package_availability = {
        "vllm": _package_availability("vllm", "vllm"),
        "cbor2": _package_availability("cbor2", "cbor2"),
    }
    nvidia_device = os.path.exists("/dev/nvidiactl")
    rocm_device = os.path.exists("/dev/kfd")
    dri_render = (
        any(name.startswith("renderD") for name in os.listdir("/dev/dri"))
        if os.path.isdir("/dev/dri")
        else False
    )
    compatible_gpu = nvidia_device or rocm_device
    vllm_available = bool(
        command_availability["vllm"]
        or package_availability["vllm"]["available"]
    )
    if not compatible_gpu:
        status = "BLOCKED_NO_GPU"
        blocking_reasons = [
            "no locally detectable NVIDIA or ROCm compute device",
            "Orange Pi remains orchestrator/metrics client only",
        ]
    elif not vllm_available:
        status = "BLOCKED_VERSION"
        blocking_reasons = [
            "compatible compute device detected but local vLLM version unavailable"
        ]
    else:
        status = "BLOCKED_VERSION"
        blocking_reasons = [
            "vLLM help/log capability discovery was not performed in offline preflight"
        ]

    unknown_fields = {
        "vllm_version": None,
        "engine_version": None,
        "backend": None,
        "gpu_name": None,
        "gpu_count": None,
        "gpu_memory_bytes": None,
        "driver_version": None,
        "runtime_version": None,
        "model_id": None,
        "model_revision": None,
        "tokenizer_revision": None,
        "model_architecture": None,
        "attention_types": None,
        "num_layers": None,
        "num_attention_heads": None,
        "num_kv_heads": None,
        "head_dim": None,
        "model_dtype": None,
        "kv_cache_dtype": None,
        "tensor_parallel_size": None,
        "pipeline_parallel_size": None,
        "max_model_len": None,
        "gpu_memory_utilization": None,
        "kv_cache_memory_bytes": None,
        "enable_prefix_caching": None,
        "prefix_hash_algorithm": None,
        "resolved_cache_config": None,
        "resolved_default_block_size": None,
        "num_gpu_blocks": None,
    }
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "wave": "WAVE0_OBSERVE_ONLY",
        "status": status,
        "observed_at_utc": observed_at_utc or _utc_now(),
        "host_role": "orange_pi_orchestrator_and_metrics_client",
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "offline_preflight": True,
        "network_calls_performed": False,
        "service_actions_performed": False,
        "process_environment_collected": False,
        "process_command_lines_collected": False,
        "production_endpoint_probed": False,
        "command_availability": command_availability,
        "package_availability": package_availability,
        "device_availability": {
            "nvidia_compute_device": nvidia_device,
            "rocm_compute_device": rocm_device,
            "dri_render_node": dri_render,
            "compatible_vllm_gpu_detected": compatible_gpu,
            "note": (
                "A generic DRI render node alone is not evidence of a "
                "vLLM-compatible CUDA/ROCm accelerator."
            ),
        },
        "supported_block_sizes": None,
        "block_size_plan": {
            "baseline_auto": True,
            "candidates": [],
            "diagnostic_candidates": [],
            "reason": "requires same-version vLLM help/log capability evidence",
        },
        "hybrid_kv_cache": {
            "full_attention_groups": None,
            "sliding_window_groups": None,
            "local_attention_groups": None,
            "mamba_ssm_groups": None,
            "kv_cache_group_count": None,
            "physical_page_size_bytes": None,
            "padding_grouping_overhead_bytes": None,
            "experimental_or_limited": None,
            "limitations": (
                "unknown until model and same-version GPU-host cache config "
                "are resolved"
            ),
        },
        "owner_thermal_limit_c": None,
        "metrics_available": False,
        "blocking_reasons": blocking_reasons,
    }
    result.update(unknown_fields)
    if status not in FINAL_STATUSES:
        raise AssertionError("preflight emitted an invalid final status")
    return result
