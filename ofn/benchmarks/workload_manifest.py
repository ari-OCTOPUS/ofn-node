"""Deterministic, prompt-free W1-W5 workload manifests.

Only request lengths and synthetic prefix-sharing identifiers are persisted.
No token content, tenant identity, endpoint, or cache salt is accepted.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


PHASES = ("cold", "warm")
WORKLOAD_IDS = ("W1", "W2", "W3", "W4", "W5")
_FORBIDDEN_KEYS = frozenset(
    {
        "raw_prompt",
        "prompt_text",
        "token_ids",
        "api_key",
        "authorization",
        "endpoint",
        "master_secret",
        "cache_salt",
        "tenant_id",
        "user_id",
    }
)


@dataclass(frozen=True)
class LengthRange:
    minimum: int
    maximum: int

    def __post_init__(self) -> None:
        if self.minimum < 0 or self.maximum < self.minimum:
            raise ValueError("invalid non-negative length range")


@dataclass(frozen=True)
class WorkloadDefinition:
    workload_id: str
    name: str
    profile: str
    prompt_tokens: LengthRange
    generation_tokens: LengthRange
    concurrency: tuple[int, ...]
    shared_prefix: str
    apc_enabled: bool
    source: str
    status: str = "READY"
    stable_prefix_tokens: LengthRange | None = None
    query_tail_tokens: LengthRange | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if self.workload_id not in WORKLOAD_IDS:
            raise ValueError("unknown workload_id")
        if not self.concurrency or any(value <= 0 for value in self.concurrency):
            raise ValueError("concurrency must be non-empty and positive")


@dataclass(frozen=True)
class AnonymizedHistogramBin:
    """A text-free W4 histogram bin supplied by the owner."""

    prompt_tokens: int
    generation_tokens: int
    count: int
    concurrency: int
    shared_prefix_fraction: float

    def __post_init__(self) -> None:
        if self.prompt_tokens < 0 or self.generation_tokens < 0:
            raise ValueError("histogram token lengths must be non-negative")
        if self.count <= 0 or self.count > 10_000:
            raise ValueError("histogram count must be in [1, 10000]")
        if self.concurrency <= 0:
            raise ValueError("histogram concurrency must be positive")
        if not 0.0 <= self.shared_prefix_fraction <= 1.0:
            raise ValueError("shared_prefix_fraction must be in [0, 1]")


@dataclass(frozen=True)
class SyntheticRequest:
    synthetic_request_id: str
    workload_id: str
    phase: str
    prompt_tokens: int
    generation_tokens: int
    concurrency: int
    shared_prefix_tokens: int
    synthetic_prefix_group: str
    synthetic_prefix_pattern: str

    def __post_init__(self) -> None:
        if self.phase not in PHASES:
            raise ValueError("phase must be cold or warm")
        if self.workload_id not in WORKLOAD_IDS:
            raise ValueError("unknown workload_id")
        if min(
            self.prompt_tokens,
            self.generation_tokens,
            self.shared_prefix_tokens,
        ) < 0:
            raise ValueError("token lengths must be non-negative")
        if self.shared_prefix_tokens > self.prompt_tokens:
            raise ValueError("shared prefix cannot exceed prompt length")
        if self.concurrency <= 0:
            raise ValueError("concurrency must be positive")


@dataclass(frozen=True)
class WorkloadPhase:
    workload_id: str
    phase: str
    cache_initial_state: str
    requests: tuple[SyntheticRequest, ...]

    def __post_init__(self) -> None:
        if self.phase not in PHASES:
            raise ValueError("phase must be cold or warm")
        if any(request.phase != self.phase for request in self.requests):
            raise ValueError("cold and warm requests must never be mixed")
        if any(
            request.workload_id != self.workload_id for request in self.requests
        ):
            raise ValueError("phase contains another workload")


def standard_workload_definitions() -> tuple[WorkloadDefinition, ...]:
    """Return the specification-backed W1-W5 definitions."""

    return (
        WorkloadDefinition(
            workload_id="W1",
            name="Short Interactive",
            profile="interactive",
            prompt_tokens=LengthRange(128, 512),
            generation_tokens=LengthRange(32, 128),
            concurrency=(1, 4, 16),
            shared_prefix="low",
            apc_enabled=True,
            source="deterministic_synthetic",
        ),
        WorkloadDefinition(
            workload_id="W2",
            name="Multi-turn Agent",
            profile="agent",
            prompt_tokens=LengthRange(1_024, 8_192),
            generation_tokens=LengthRange(64, 256),
            concurrency=(1, 8, 32),
            shared_prefix="high",
            apc_enabled=True,
            source="deterministic_synthetic",
        ),
        WorkloadDefinition(
            workload_id="W3",
            name="Long Document QA",
            profile="document_qa",
            prompt_tokens=LengthRange(8_224, 33_024),
            generation_tokens=LengthRange(64, 256),
            concurrency=(1, 4, 16),
            shared_prefix="very_high",
            apc_enabled=True,
            source="deterministic_synthetic",
            stable_prefix_tokens=LengthRange(8_192, 32_768),
            query_tail_tokens=LengthRange(32, 256),
            note="stable document and query tail are represented separately",
        ),
        WorkloadDefinition(
            workload_id="W4",
            name="Mixed Production Trace",
            profile="mixed",
            prompt_tokens=LengthRange(0, 0),
            generation_tokens=LengthRange(0, 0),
            concurrency=(1,),
            shared_prefix="histogram_supplied",
            apc_enabled=True,
            source="owner_anonymized_histogram_required",
            status="BLOCKED_MISSING_ANONYMIZED_HISTOGRAM",
            note=(
                "No distribution is guessed; supply text-free length and "
                "prefix-sharing histogram bins."
            ),
        ),
        WorkloadDefinition(
            workload_id="W5",
            name="Long Generation Control",
            profile="decode_heavy_control",
            prompt_tokens=LengthRange(512, 2_048),
            generation_tokens=LengthRange(512, 2_048),
            concurrency=(1, 4, 16),
            shared_prefix="variable",
            apc_enabled=True,
            source="deterministic_synthetic",
            note=(
                "Control workload: block/APC changes need not improve "
                "decode-heavy traffic."
            ),
        ),
    )


def _stable_seed(seed: int, workload_id: str) -> int:
    digest = hashlib.sha256(
        f"vllm-block-size-public-seed:{seed}:{workload_id}".encode("ascii")
    ).digest()
    return int.from_bytes(digest[:8], "big")


def _prefix_pattern(seed: int, workload_id: str, group: str) -> str:
    """Return a public synthetic pattern identifier, never token content."""

    return hashlib.sha256(
        f"synthetic-prefix:{seed}:{workload_id}:{group}".encode("ascii")
    ).hexdigest()[:16]


def _shared_prefix_length(
    *,
    sharing: str,
    prompt_tokens: int,
    rng: random.Random,
) -> int:
    if sharing == "low":
        fraction = rng.uniform(0.0, 0.20)
    elif sharing == "high":
        fraction = rng.uniform(0.65, 0.90)
    elif sharing == "very_high":
        fraction = rng.uniform(0.90, 0.99)
    elif sharing == "variable":
        fraction = rng.uniform(0.0, 0.90)
    else:
        fraction = 0.0
    return min(prompt_tokens, int(prompt_tokens * fraction))


def _base_requests_for_definition(
    definition: WorkloadDefinition,
    *,
    seed: int,
    samples_per_concurrency: int,
) -> tuple[dict[str, Any], ...]:
    rng = random.Random(_stable_seed(seed, definition.workload_id))
    generated: list[dict[str, Any]] = []
    for concurrency_index, concurrency in enumerate(definition.concurrency):
        stable_document: int | None = None
        if definition.stable_prefix_tokens is not None:
            stable_document = rng.randint(
                definition.stable_prefix_tokens.minimum,
                definition.stable_prefix_tokens.maximum,
            )
        for sample_index in range(samples_per_concurrency):
            group_index = (
                sample_index
                if definition.shared_prefix == "low"
                else sample_index // 2
            )
            group = f"group-{concurrency_index:02d}-{group_index:02d}"
            if (
                stable_document is not None
                and definition.query_tail_tokens is not None
            ):
                query_tail = rng.randint(
                    definition.query_tail_tokens.minimum,
                    definition.query_tail_tokens.maximum,
                )
                prompt_tokens = stable_document + query_tail
                shared_prefix_tokens = stable_document
            else:
                prompt_tokens = rng.randint(
                    definition.prompt_tokens.minimum,
                    definition.prompt_tokens.maximum,
                )
                shared_prefix_tokens = _shared_prefix_length(
                    sharing=definition.shared_prefix,
                    prompt_tokens=prompt_tokens,
                    rng=rng,
                )
            generation_tokens = rng.randint(
                definition.generation_tokens.minimum,
                definition.generation_tokens.maximum,
            )
            generated.append(
                {
                    "base_id": (
                        f"{definition.workload_id.lower()}-"
                        f"{concurrency_index:02d}-{sample_index:03d}"
                    ),
                    "prompt_tokens": prompt_tokens,
                    "generation_tokens": generation_tokens,
                    "concurrency": concurrency,
                    "shared_prefix_tokens": shared_prefix_tokens,
                    "group": group,
                }
            )
    return tuple(generated)


def _base_requests_for_histogram(
    bins: Iterable[AnonymizedHistogramBin],
) -> tuple[dict[str, Any], ...]:
    generated: list[dict[str, Any]] = []
    for bin_index, item in enumerate(bins):
        for sample_index in range(item.count):
            generated.append(
                {
                    "base_id": f"w4-{bin_index:03d}-{sample_index:05d}",
                    "prompt_tokens": item.prompt_tokens,
                    "generation_tokens": item.generation_tokens,
                    "concurrency": item.concurrency,
                    "shared_prefix_tokens": int(
                        item.prompt_tokens * item.shared_prefix_fraction
                    ),
                    "group": f"group-{bin_index:03d}",
                }
            )
    return tuple(generated)


def _phase_pair(
    workload_id: str,
    base_requests: Iterable[dict[str, Any]],
    *,
    seed: int,
) -> tuple[WorkloadPhase, WorkloadPhase]:
    base = tuple(base_requests)
    phases: list[WorkloadPhase] = []
    for phase in PHASES:
        requests = tuple(
            SyntheticRequest(
                synthetic_request_id=f"{item['base_id']}-{phase}",
                workload_id=workload_id,
                phase=phase,
                prompt_tokens=item["prompt_tokens"],
                generation_tokens=item["generation_tokens"],
                concurrency=item["concurrency"],
                shared_prefix_tokens=item["shared_prefix_tokens"],
                synthetic_prefix_group=item["group"],
                synthetic_prefix_pattern=_prefix_pattern(
                    seed, workload_id, item["group"]
                ),
            )
            for item in base
        )
        phases.append(
            WorkloadPhase(
                workload_id=workload_id,
                phase=phase,
                cache_initial_state=(
                    "empty_isolated_cache"
                    if phase == "cold"
                    else "controlled_prewarmed_isolated_cache"
                ),
                requests=requests,
            )
        )
    return phases[0], phases[1]


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_value(nested) for key, nested in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(nested) for nested in value]
    return value


def build_workload_manifest(
    *,
    seed: int = 20_260_825,
    samples_per_concurrency: int = 4,
    anonymized_histogram: Iterable[AnonymizedHistogramBin] | None = None,
) -> dict[str, Any]:
    """Build a deterministic manifest with distinct cold/warm phase objects."""

    if samples_per_concurrency <= 0:
        raise ValueError("samples_per_concurrency must be positive")
    definitions = list(standard_workload_definitions())
    histogram = tuple(anonymized_histogram or ())
    if histogram:
        definitions[3] = WorkloadDefinition(
            workload_id="W4",
            name="Mixed Production Trace",
            profile="mixed",
            prompt_tokens=LengthRange(
                min(item.prompt_tokens for item in histogram),
                max(item.prompt_tokens for item in histogram),
            ),
            generation_tokens=LengthRange(
                min(item.generation_tokens for item in histogram),
                max(item.generation_tokens for item in histogram),
            ),
            concurrency=tuple(
                sorted({item.concurrency for item in histogram})
            ),
            shared_prefix="anonymized_histogram",
            apc_enabled=True,
            source="owner_supplied_anonymized_length_histogram",
            status="READY",
            note="Synthetic requests preserve only supplied length/share bins.",
        )

    phase_manifests: list[WorkloadPhase] = []
    for definition in definitions:
        if definition.workload_id == "W4":
            base = _base_requests_for_histogram(histogram)
        else:
            base = _base_requests_for_definition(
                definition,
                seed=seed,
                samples_per_concurrency=samples_per_concurrency,
            )
        phase_manifests.extend(
            _phase_pair(definition.workload_id, base, seed=seed)
        )

    result = {
        "schema_version": "1.0",
        "suite": "vllm_kv_block_size_w1_w5",
        "seed": seed,
        "content_policy": {
            "raw_prompts_stored": False,
            "token_ids_stored": False,
            "tenant_or_user_labels_stored": False,
            "secrets_or_endpoints_stored": False,
            "synthetic_lengths_and_prefix_patterns_only": True,
        },
        "cache_phase_policy": (
            "cold and warm cache measurements are separate run records"
        ),
        "invariants": [
            "APC reuses full logical vLLM blocks only.",
            "A prefix may have up to block_size - 1 unreused suffix tokens.",
            "vLLM logical block size is not LMCache/external transfer chunking.",
            "The same request shapes are paired across cold and warm phases.",
        ],
        "definitions": [_json_value(asdict(item)) for item in definitions],
        "phase_manifests": [
            _json_value(asdict(item)) for item in phase_manifests
        ],
    }
    validate_workload_manifest(result)
    return result


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _walk_keys(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            yield from _walk_keys(nested)


def validate_workload_manifest(manifest: dict[str, Any]) -> None:
    """Validate workload coverage, separation, and forbidden-content keys."""

    forbidden = _FORBIDDEN_KEYS.intersection(_walk_keys(manifest))
    if forbidden:
        raise ValueError("manifest contains forbidden sensitive-content keys")
    definitions = manifest.get("definitions", [])
    if tuple(item.get("workload_id") for item in definitions) != WORKLOAD_IDS:
        raise ValueError("manifest must define W1 through W5 in order")
    seen_pairs: set[tuple[str, str]] = set()
    seen_request_ids: set[str] = set()
    for phase_manifest in manifest.get("phase_manifests", []):
        workload_id = phase_manifest.get("workload_id")
        phase = phase_manifest.get("phase")
        if phase not in PHASES:
            raise ValueError("unknown cache phase")
        pair = (workload_id, phase)
        if pair in seen_pairs:
            raise ValueError("duplicate workload/cache phase")
        seen_pairs.add(pair)
        for request in phase_manifest.get("requests", []):
            if request.get("phase") != phase:
                raise ValueError("cold and warm cache requests are mixed")
            request_id = request.get("synthetic_request_id")
            if not request_id or request_id in seen_request_ids:
                raise ValueError("synthetic request IDs must be unique")
            seen_request_ids.add(request_id)
    expected_pairs = {
        (workload_id, phase)
        for workload_id in WORKLOAD_IDS
        for phase in PHASES
    }
    if seen_pairs != expected_pairs:
        raise ValueError("each workload needs separate cold and warm phases")


def write_workload_manifest(path: str | Path, manifest: dict[str, Any]) -> None:
    validate_workload_manifest(manifest)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
