# vLLM APC Hash Configuration and Benchmark Guide

This guide defines how to evaluate vLLM Automatic Prefix Caching (APC) hash modes in WAVE0 without patching vLLM internals.

Scope:
- Compare `sha256` and `sha256_cbor` hash-key modes.
- Measure serialization overhead and tenant-isolation behavior.
- Produce reproducible benchmark artifacts.

Out of scope:
- Running vLLM on Orange Pi.
- Starting/stopping systemd units from this procedure.
- Treating KV cache as long-term memory.

## 1) Safety and invariants

- Orange Pi acts as client/observer only.
- Keep `executable_total == 0` for local wave0 governance.
- Never log raw secrets, full prompts, or user-private payloads.
- Use per-tenant `cache_salt`; do not share one global salt in multi-tenant workloads.

## 2) Server-side APC configuration (GPU host)

Use one algorithm at a time for A/B measurements.

### A. `sha256` (default path)

```bash
vllm serve <MODEL> \
  --enable-prefix-caching \
  --prefix-caching-hash-algo sha256
```

Notes:
- Serialization backend is Python pickle.
- Fast path, but not cross-language canonical by design.

### B. `sha256_cbor` (canonical serialization path)

```bash
vllm serve <MODEL> \
  --enable-prefix-caching \
  --prefix-caching-hash-algo sha256_cbor
```

Notes:
- Requires `cbor2` support in the vLLM environment.
- Canonical CBOR improves reproducibility across language/runtime boundaries.

## 3) Prompt assembly constraints for high prefix-hit rates

Stable prefix order:

1. `stable_system_contract`
2. `stable_tool_contracts`
3. `retrieved_relevant_memory`
4. `current_homeostatic_state`
5. `current_request`

Rules:
- Keep timestamp/UUID/random fields out of the stable prefix.
- Put dynamic fields only near the end (`current_request`).
- Keep model/tokenizer/revision/adapter identity explicit in cache key context.

## 4) Multi-tenant isolation policy

- Inject tenant-scoped `cache_salt` per request.
- Rotate salt when privacy domain changes.
- Invalidate old assumptions when model weights, tokenizer, or adapters change.
- Never infer event-memory corruption from APC miss spikes.

## 5) Benchmark suite (offline-safe)

Tool:
- `ofn/adapters/vllm_prefix_cache.py`

What it measures:
- Serialization latency distribution (`mean`, `p50`, `p95` microseconds)
- Mean encoded payload size
- Synthetic collision probe (`collision_rate`)
- Cross-tenant overlap with and without `cache_salt`
- Reproducibility probe

Run:

```bash
python3 -m ofn.adapters.vllm_prefix_cache \
  --algorithms sha256,sha256_cbor \
  --tenants 8 \
  --prompts-per-tenant 48 \
  --blocks-per-prompt 8 \
  --block-size 16 \
  --iterations 1500 \
  --collision-samples 20000 \
  --output-json artifacts/prefix-cache/benchmark-report.json \
  --output-markdown artifacts/prefix-cache/benchmark-report.md
```

If `cbor2` is missing:
- `sha256_cbor` result is marked `UNAVAILABLE`.
- Install `cbor2` only on the GPU host where policy permits.

## 6) Required benchmark matrix

Run at least:

1. `sha256` with tenant salt.
2. `sha256` without tenant salt (risk baseline).
3. `sha256_cbor` with tenant salt.
4. `sha256_cbor` without tenant salt (risk baseline).

For live server A/B (optional, separate from this offline suite), collect:
- prefix cache hit/miss
- eviction/preemption
- queue time
- TTFT
- end-to-end latency
- tokens/second

## 7) Collision-prevention metrics

Report these fields from the suite:
- `collision_rate`
- `overlap_ratio` without salt
- `overlap_ratio` with salt
- `overlapping_hash_count` (cross-tenant)

Acceptance guidance:
- `collision_rate` should be zero in synthetic probe.
- `overlap_ratio(with_salt)` should approach zero.
- Significant `overlap_ratio(without_salt)` is expected and demonstrates why salt is mandatory.

## 8) Artifact outputs

Expected files:
- `artifacts/prefix-cache/benchmark-report.json`
- `artifacts/prefix-cache/benchmark-report.md`

Preserve alongside:
- vLLM version info (`vllm --version`)
- exact serve flags for each run
- host identity and UTC timestamps

## 9) Decision rule for WAVE0

- Choose algorithm only after measured trade-off review:
  - latency overhead budget
  - reproducibility requirement
  - tenant isolation requirements
- Do not apply runtime changes automatically from benchmark scripts.
- Escalate to owner before any deployment/restart/soak transition.

