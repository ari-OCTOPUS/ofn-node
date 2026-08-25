"""vLLM prefix-cache hash guide and benchmark helpers.

This module is intentionally read-only with respect to infrastructure:
- It does not start, stop, or reconfigure services.
- It does not require GPU access.
- It benchmarks hash-key construction overhead and multi-tenant isolation
  properties for vLLM Automatic Prefix Caching (APC) modes:
  `sha256` and `sha256_cbor`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import random
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Literal

try:
    import cbor2  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - depends on runtime environment.
    cbor2 = None


HashAlgorithm = Literal["sha256", "sha256_cbor"]


@dataclass(frozen=True)
class WorkloadConfig:
    """Synthetic workload parameters used by the benchmark suite."""

    tenant_count: int = 8
    prompts_per_tenant: int = 48
    blocks_per_prompt: int = 8
    block_size: int = 16
    model_id: str = "model-qwen3-0.6b"
    tokenizer_id: str = "tokenizer-qwen3"
    model_revision: str = "rev-1"
    lora_id: str = "base"
    iterations: int = 1500
    collision_samples: int = 20000
    random_seed: int = 7

    def validate(self) -> None:
        for field_name in (
            "tenant_count",
            "prompts_per_tenant",
            "blocks_per_prompt",
            "block_size",
            "iterations",
            "collision_samples",
        ):
            value = getattr(self, field_name)
            if value <= 0:
                raise ValueError(f"{field_name} must be > 0")


@dataclass(frozen=True)
class PrefixHashInput:
    """A single block-hash identity input."""

    tenant_id: str
    prompt_id: int
    block_index: int
    parent_hash: str | None
    block_tokens: tuple[int, ...]
    model_id: str
    tokenizer_id: str
    model_revision: str
    lora_id: str
    cache_salt: str | None


@dataclass(frozen=True)
class HashRecord:
    tenant_id: str
    block_hash: str


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * q))))
    return ordered[index]


def _build_block_tokens(prompt_id: int, block_index: int, block_size: int) -> tuple[int, ...]:
    base = prompt_id * 1009 + block_index * 131
    return tuple((base + offset * 17) % 32000 for offset in range(block_size))


def _normalize_hash_components(
    parent_hash: str | None,
    block_tokens: tuple[int, ...],
    extra_hashes: dict[str, str],
) -> dict[str, Any]:
    if parent_hash is not None and not isinstance(parent_hash, str):
        raise ValueError("parent_hash must be str or None")
    if not block_tokens:
        raise ValueError("block_tokens must not be empty")
    if any(token < 0 for token in block_tokens):
        raise ValueError("block_tokens must be non-negative integers")
    if not extra_hashes:
        raise ValueError("extra_hashes must not be empty")

    return {
        "parent_hash": parent_hash,
        "block_tokens": block_tokens,
        "extra_hashes": {key: extra_hashes[key] for key in sorted(extra_hashes)},
    }


def serialize_hash_components(
    *,
    algorithm: HashAlgorithm,
    parent_hash: str | None,
    block_tokens: tuple[int, ...],
    extra_hashes: dict[str, str],
) -> bytes:
    payload = _normalize_hash_components(parent_hash, block_tokens, extra_hashes)
    if algorithm == "sha256":
        return pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    if algorithm == "sha256_cbor":
        if cbor2 is None:
            raise RuntimeError("cbor2 is required for sha256_cbor")
        return cbor2.dumps(payload, canonical=True)
    raise ValueError(f"unsupported algorithm: {algorithm}")


def compute_block_hash(
    *,
    algorithm: HashAlgorithm,
    parent_hash: str | None,
    block_tokens: tuple[int, ...],
    extra_hashes: dict[str, str],
) -> tuple[str, int]:
    encoded = serialize_hash_components(
        algorithm=algorithm,
        parent_hash=parent_hash,
        block_tokens=block_tokens,
        extra_hashes=extra_hashes,
    )
    return hashlib.sha256(encoded).hexdigest(), len(encoded)


def _extra_hashes(item: PrefixHashInput, include_cache_salt: bool) -> dict[str, str]:
    result = {
        "model_id": item.model_id,
        "tokenizer_id": item.tokenizer_id,
        "model_revision": item.model_revision,
        "lora_id": item.lora_id,
    }
    if include_cache_salt and item.cache_salt is not None:
        result["cache_salt"] = item.cache_salt
    return result


def _generate_prompt_inputs(config: WorkloadConfig) -> list[PrefixHashInput]:
    generated: list[PrefixHashInput] = []
    for tenant_idx in range(config.tenant_count):
        tenant_id = f"tenant-{tenant_idx:02d}"
        cache_salt = f"salt-{tenant_idx:02d}"
        for prompt_id in range(config.prompts_per_tenant):
            for block_index in range(config.blocks_per_prompt):
                generated.append(
                    PrefixHashInput(
                        tenant_id=tenant_id,
                        prompt_id=prompt_id,
                        block_index=block_index,
                        parent_hash=None,
                        block_tokens=_build_block_tokens(
                            prompt_id=prompt_id,
                            block_index=block_index,
                            block_size=config.block_size,
                        ),
                        model_id=config.model_id,
                        tokenizer_id=config.tokenizer_id,
                        model_revision=config.model_revision,
                        lora_id=config.lora_id,
                        cache_salt=cache_salt,
                    )
                )
    return generated


def _hash_records(
    *,
    algorithm: HashAlgorithm,
    config: WorkloadConfig,
    include_cache_salt: bool,
) -> list[HashRecord]:
    records: list[HashRecord] = []
    parent_by_tenant_prompt: dict[tuple[str, int], str | None] = {}
    for item in _generate_prompt_inputs(config):
        key = (item.tenant_id, item.prompt_id)
        parent_hash = parent_by_tenant_prompt.get(key)
        block_hash, _ = compute_block_hash(
            algorithm=algorithm,
            parent_hash=parent_hash,
            block_tokens=item.block_tokens,
            extra_hashes=_extra_hashes(item, include_cache_salt=include_cache_salt),
        )
        parent_by_tenant_prompt[key] = block_hash
        records.append(HashRecord(tenant_id=item.tenant_id, block_hash=block_hash))
    return records


def benchmark_serialization(
    *,
    algorithm: HashAlgorithm,
    config: WorkloadConfig,
    include_cache_salt: bool = True,
) -> dict[str, Any]:
    inputs = _generate_prompt_inputs(config)
    samples = max(1, min(len(inputs), config.iterations))
    elapsed_us: list[float] = []
    payload_sizes: list[int] = []
    parent_hash: str | None = None
    for index in range(samples):
        item = inputs[index]
        extra = _extra_hashes(item, include_cache_salt=include_cache_salt)
        started = time.perf_counter_ns()
        block_hash, payload_size = compute_block_hash(
            algorithm=algorithm,
            parent_hash=parent_hash,
            block_tokens=item.block_tokens,
            extra_hashes=extra,
        )
        finished = time.perf_counter_ns()
        parent_hash = block_hash
        elapsed_us.append((finished - started) / 1000.0)
        payload_sizes.append(payload_size)

    total_s = sum(elapsed_us) / 1_000_000.0
    return {
        "samples": samples,
        "total_seconds": round(total_s, 6),
        "mean_us": round(statistics.fmean(elapsed_us), 3),
        "p50_us": round(_quantile(elapsed_us, 0.50), 3),
        "p95_us": round(_quantile(elapsed_us, 0.95), 3),
        "mean_payload_bytes": round(statistics.fmean(payload_sizes), 2),
    }


def tenant_overlap_metrics(
    *,
    algorithm: HashAlgorithm,
    config: WorkloadConfig,
    include_cache_salt: bool,
) -> dict[str, Any]:
    records = _hash_records(
        algorithm=algorithm,
        config=config,
        include_cache_salt=include_cache_salt,
    )
    by_hash: dict[str, set[str]] = {}
    for record in records:
        by_hash.setdefault(record.block_hash, set()).add(record.tenant_id)

    overlapping_hashes = [
        block_hash
        for block_hash, tenant_ids in by_hash.items()
        if len(tenant_ids) > 1
    ]
    overlap_ratio = 0.0
    if by_hash:
        overlap_ratio = len(overlapping_hashes) / len(by_hash)
    return {
        "records": len(records),
        "unique_hashes": len(by_hash),
        "overlapping_hash_count": len(overlapping_hashes),
        "overlap_ratio": round(overlap_ratio, 6),
        "cache_salt_included": include_cache_salt,
    }


def collision_probe(
    *,
    algorithm: HashAlgorithm,
    config: WorkloadConfig,
) -> dict[str, Any]:
    random.seed(config.random_seed)
    seen: set[str] = set()
    collisions = 0
    started = time.perf_counter_ns()
    for sample_index in range(config.collision_samples):
        tokens = tuple(random.randint(1, 32000) for _ in range(config.block_size))
        extra = {
            "model_id": config.model_id,
            "tokenizer_id": config.tokenizer_id,
            "model_revision": config.model_revision,
            "lora_id": config.lora_id,
            "cache_salt": f"salt-{sample_index % max(1, config.tenant_count)}",
            "sample_index": str(sample_index),
        }
        block_hash, _ = compute_block_hash(
            algorithm=algorithm,
            parent_hash=None,
            block_tokens=tokens,
            extra_hashes=extra,
        )
        if block_hash in seen:
            collisions += 1
        else:
            seen.add(block_hash)
    finished = time.perf_counter_ns()
    duration_s = (finished - started) / 1_000_000_000.0
    throughput = config.collision_samples / duration_s if duration_s > 0 else 0.0
    return {
        "samples": config.collision_samples,
        "collisions": collisions,
        "collision_rate": round(collisions / config.collision_samples, 12),
        "throughput_hashes_per_second": round(throughput, 2),
    }


def reproducibility_probe(algorithm: HashAlgorithm) -> dict[str, Any]:
    base_tokens = (101, 102, 103, 104)
    extra_a = {
        "model_id": "m",
        "tokenizer_id": "t",
        "model_revision": "r",
        "lora_id": "l",
        "cache_salt": "s",
    }
    extra_b = {
        "cache_salt": "s",
        "lora_id": "l",
        "model_revision": "r",
        "tokenizer_id": "t",
        "model_id": "m",
    }
    payload_a = serialize_hash_components(
        algorithm=algorithm,
        parent_hash=None,
        block_tokens=base_tokens,
        extra_hashes=extra_a,
    )
    payload_b = serialize_hash_components(
        algorithm=algorithm,
        parent_hash=None,
        block_tokens=base_tokens,
        extra_hashes=extra_b,
    )
    return {
        "same_bytes_after_key_reordering": payload_a == payload_b,
        "encoding_size_bytes": len(payload_a),
        "cross_language_reproducibility": (
            "stronger"
            if algorithm == "sha256_cbor"
            else "python_pickle_not_cross_language_stable"
        ),
    }


def run_suite(config: WorkloadConfig, algorithms: Iterable[HashAlgorithm]) -> dict[str, Any]:
    config.validate()
    reports: list[dict[str, Any]] = []
    for algorithm in algorithms:
        if algorithm == "sha256_cbor" and cbor2 is None:
            reports.append(
                {
                    "algorithm": algorithm,
                    "status": "UNAVAILABLE",
                    "reason": "cbor2_not_installed",
                }
            )
            continue

        reports.append(
            {
                "algorithm": algorithm,
                "status": "OK",
                "serialization_overhead": benchmark_serialization(
                    algorithm=algorithm,
                    config=config,
                    include_cache_salt=True,
                ),
                "tenant_overlap_without_salt": tenant_overlap_metrics(
                    algorithm=algorithm,
                    config=config,
                    include_cache_salt=False,
                ),
                "tenant_overlap_with_salt": tenant_overlap_metrics(
                    algorithm=algorithm,
                    config=config,
                    include_cache_salt=True,
                ),
                "collision_probe": collision_probe(
                    algorithm=algorithm,
                    config=config,
                ),
                "reproducibility_probe": reproducibility_probe(algorithm),
            }
        )
    return {
        "suite": "vllm_apc_hash_benchmark",
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "workload_config": asdict(config),
        "algorithms": reports,
        "notes": [
            "APC hash keys are benchmarked offline; no vLLM service mutation.",
            "KV cache is inference-temporary and not event memory.",
            "Use tenant-specific cache_salt for isolation in multi-tenant serving.",
        ],
    }


def render_markdown_report(result: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# vLLM APC Hash Benchmark Report")
    lines.append("")
    lines.append(f"- created_at_utc: `{result['created_at_utc']}`")
    lines.append("- suite: `vllm_apc_hash_benchmark`")
    lines.append("")
    lines.append("## Workload")
    lines.append("")
    workload = result["workload_config"]
    for key in sorted(workload):
        lines.append(f"- {key}: `{workload[key]}`")
    lines.append("")
    lines.append("## Algorithm Results")
    lines.append("")
    for item in result["algorithms"]:
        lines.append(f"### {item['algorithm']}")
        if item["status"] != "OK":
            lines.append("")
            lines.append(f"- status: `{item['status']}`")
            lines.append(f"- reason: `{item.get('reason', 'n/a')}`")
            lines.append("")
            continue
        serialization = item["serialization_overhead"]
        overlap_no_salt = item["tenant_overlap_without_salt"]
        overlap_with_salt = item["tenant_overlap_with_salt"]
        collision = item["collision_probe"]
        reproducibility = item["reproducibility_probe"]
        lines.append("")
        lines.append(f"- serialization mean_us: `{serialization['mean_us']}`")
        lines.append(f"- serialization p95_us: `{serialization['p95_us']}`")
        lines.append(
            f"- overlap_ratio without salt: `{overlap_no_salt['overlap_ratio']}`"
        )
        lines.append(
            f"- overlap_ratio with salt: `{overlap_with_salt['overlap_ratio']}`"
        )
        lines.append(f"- collision_rate: `{collision['collision_rate']}`")
        lines.append(
            "- cross-language reproducibility: "
            f"`{reproducibility['cross_language_reproducibility']}`"
        )
        lines.append("")
    lines.append("## Notes")
    lines.append("")
    for note in result["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def _parse_algorithm_list(raw: str) -> list[HashAlgorithm]:
    supported = {"sha256", "sha256_cbor"}
    items = [part.strip() for part in raw.split(",") if part.strip()]
    if not items:
        raise ValueError("at least one algorithm is required")
    unknown = [item for item in items if item not in supported]
    if unknown:
        raise ValueError(f"unsupported algorithms: {', '.join(unknown)}")
    return items  # type: ignore[return-value]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark vLLM APC hash algorithms (sha256 vs sha256_cbor) "
            "for serialization overhead, reproducibility, and tenant isolation."
        )
    )
    parser.add_argument("--tenants", type=int, default=8)
    parser.add_argument("--prompts-per-tenant", type=int, default=48)
    parser.add_argument("--blocks-per-prompt", type=int, default=8)
    parser.add_argument("--block-size", type=int, default=16)
    parser.add_argument("--iterations", type=int, default=1500)
    parser.add_argument("--collision-samples", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--algorithms",
        default="sha256,sha256_cbor",
        help="Comma-separated list. Supported: sha256,sha256_cbor",
    )
    parser.add_argument(
        "--output-json",
        default="artifacts/prefix-cache/benchmark-report.json",
    )
    parser.add_argument(
        "--output-markdown",
        default="artifacts/prefix-cache/benchmark-report.md",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    algorithms = _parse_algorithm_list(args.algorithms)
    config = WorkloadConfig(
        tenant_count=args.tenants,
        prompts_per_tenant=args.prompts_per_tenant,
        blocks_per_prompt=args.blocks_per_prompt,
        block_size=args.block_size,
        iterations=args.iterations,
        collision_samples=args.collision_samples,
        random_seed=args.seed,
    )
    result = run_suite(config, algorithms)

    json_path = Path(args.output_json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    markdown_path = Path(args.output_markdown)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown_report(result), encoding="utf-8")

    print(f"wrote_json={json_path}")
    print(f"wrote_markdown={markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
