# ADR — vLLM Automatic Prefix Caching Hash Strategy

Status: Accepted (WAVE0_OBSERVE_ONLY)  
Date: 2026-08-25

## Context

- Orange Pi (`/opt/octopus/lab`) is control-plane/read-only for cognition and telemetry.
- vLLM is expected to run on a separate GPU host.
- We need stable prefix reuse, tenant isolation, and measurable APC behavior without patching vLLM internals.
- vLLM supports APC hash algorithms through server flags:
  - `sha256` (default since v0.11, pickle serialization)
  - `sha256_cbor` (canonical CBOR serialization via `cbor2`)

## Decision

1. Keep vLLM core unpatched.
2. Use hash algorithm selection only through supported vLLM config flags.
3. Treat `cache_salt` as mandatory in multi-tenant deployments.
4. Add an offline benchmark suite at `ofn/adapters/vllm_prefix_cache.py` to compare:
   - serialization overhead (`sha256` vs `sha256_cbor`)
   - reproducibility properties
   - collision and overlap metrics under multi-tenant workloads
5. Keep APC and event memory separate concerns:
   - APC/KV cache is temporary inference memory.
   - It is not organism identity, not episodic memory, and not safety state.

## Rationale

- `sha256` is usually faster but uses Python pickle serialization, which is not a cross-language canonical format.
- `sha256_cbor` provides canonical serialization when `cbor2` is present and is better aligned with cross-language reproducibility requirements.
- `cache_salt` materially reduces cross-tenant hash overlap and timing-leak risk.

## Consequences

- Deployments can benchmark and choose an APC mode using measured data instead of assumptions.
- In environments without `cbor2`, `sha256_cbor` is reported as unavailable rather than silently downgraded.
- The benchmark suite remains safe for Orange Pi because it does not start/stop services or mutate vLLM runtime.

## Guardrails

- No service restarts or soak start from this ADR alone.
- No prompt/token raw logging in benchmark outputs.
- No claim that KV cache provides long-term memory or identity continuity.

