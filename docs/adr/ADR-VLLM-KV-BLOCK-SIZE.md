# ADR — vLLM KV-Cache Logical Block Size

Status: Accepted for harness only (`WAVE0_OBSERVE_ONLY`)  
Date: 2026-08-25

## Context

OCTOPUS needs evidence for the best vLLM logical KV-cache `block_size` for a
specific model, GPU, backend, and workload. The Orange Pi is only an
orchestrator/metrics client. It is not assumed to be a vLLM GPU host.

The existing APC hash work in `ofn/adapters/vllm_prefix_cache.py` remains
unchanged. APC hash serialization and tenant isolation are separate from the
logical KV block-size experiment. Likewise, an LMCache or other external
transfer chunk is not a vLLM logical block and must not be varied as though it
were one.

## Decision

1. Preserve the platform's automatic block-size choice as the mandatory
   baseline by omitting `--block-size`.
2. Derive explicit candidates only from help/log/capability evidence for the
   same vLLM version and backend.
3. For CUDA, intersect the observed supported set with `8, 16, 32`; never emit
   a production candidate above 32.
4. Keep supported size 1 in a separate diagnostic-only lane, enabled only by
   explicit opt-in. It is never a default production candidate.
5. For non-CUDA backends, require both a version and supplied capability
   candidates. Do not guess values.
6. Use a fresh canary process, unique canary port, and unique cache/data path
   for each candidate. Block size is immutable for that process.
7. Compare candidates only after complete empirical evidence. The theoretical
   estimator cannot choose a winner.
8. Never launch, deploy, restart, or begin soak from the default harness.
   Canary validation requires an explicit owner approval reference, an
   owner-defined thermal limit, complete metrics, and a non-production origin.
   WAVE0 still refuses live execution.

## Fragmentation semantics

For request length `L` and logical block size `b`:

```text
allocated_tokens = ceil(L / b) * b
tail_waste_tokens = allocated_tokens - L
fragmentation_ratio = sum(tail_waste_tokens) / sum(allocated_tokens)
```

Inputs require a positive block size and a non-empty collection of
non-negative lengths. A collection of only zero-length requests has ratio
zero.

The proposed unrestricted monotonicity statement needs correction: an
arbitrary numerically smaller block can have more tail waste than a larger
one. For example, at `L=7`, size 6 wastes 5 tokens while size 8 wastes 1.
The valid property used by tests is:

```text
if small divides large, waste(L, small) <= waste(L, large)
```

Consequently, 8 versus 16 is not an inversion example—8 divides 16, so it is
inside the restricted guarantee. Divisibility, not numeric ordering alone, is
the required scope.

APC reuses full logical blocks only. A shared prefix can therefore leave
`prefix_length mod block_size`, at most `block_size - 1`, suffix tokens
unreused.

## Memory estimate and hybrid attention

The full-attention planning approximation is:

```text
bytes_per_token ~= 2 * layers * kv_heads * head_dim
                  * bytes_per_element / TP_sharding
bytes_per_block ~= block_size * bytes_per_token
```

This excludes replication, metadata, GQA/MQA implementation details, hybrid
grouping, physical-page padding, and backend behavior. Resolved vLLM cache
configuration and profiling are authoritative.

Preflight records separate unknown fields for full-attention,
sliding-window/local-attention, and Mamba/SSM groups, plus KV group count,
physical page size, and padding/grouping overhead. Any experimental hybrid KV
manager limitation must be resolved against the actual model and same vLLM
version. On this board those fields remain unknown rather than inferred.

## Workloads

The prompt-free manifest contains:

- W1 Short Interactive: prompt 128–512, generation 32–128, concurrency
  1/4/16, low prefix sharing.
- W2 Multi-turn Agent: prompt/history 1K–8K, generation 64–256, concurrency
  1/8/32, high prefix sharing, APC enabled.
- W3 Long Document QA: stable document 8K–32K, query tail 32–256, generation
  64–256, very high prefix sharing.
- W4 Mixed Production Trace: requires an owner-supplied anonymized histogram.
  No distribution is guessed and no raw text is accepted.
- W5 Long Generation Control: prompt and generation 512–2K, variable sharing;
  this detects decode-heavy cases where block/APC changes do not help.

Every workload has distinct cold-cache and warm-cache phase objects. Synthetic
request lengths and prefix-pattern identifiers are deterministic; no prompt
text, token IDs, secrets, endpoints, cache salts, or user/tenant identities are
stored.

## Metrics and experiment protocol

At least three independent repetitions are required. Candidate order is
randomized while model, revision, seed, request shapes, concurrency,
generation parameters, and all non-block-size settings stay fixed.

The metrics adapter parses bounded caller-supplied Prometheus text without
network access. It selects a version profile, discovers observed aliases,
reports missing required families, and redacts unapproved labels. Client-side
latency distributions and official same-version server counters/gauges are
needed for TTFT, TPOT, ITL, E2E, queue, prefill, decode, throughput, APC
queries/hits, cache use, preemption, waiting requests, memory, utilization,
temperature, errors, and OOM.

## Selection

Any error, OOM, crash/restart, thermal abort, production impact, critical host
resource condition, unavailable required metrics, or identity/safety failure
rejects a candidate.

The remaining records form a Pareto frontier that minimizes TTFT p95, E2E p95,
preemption, theoretical fragmentation, queue p95, and memory while maximizing
throughput and APC hit ratio. An interactive candidate exceeding the
owner/service TTFT p95 limit is rejected.

- Improvement below 5% preserves platform auto.
- Incomplete evidence or overlapping confidence intervals yields
  `BLOCKED_NO_CLEAR_WINNER`.
- Different interactive/batch winners may become separate deployment
  profiles, never dynamic mutation inside one process.
- The harness can at most recommend an owner-approved canary. It cannot
  authorize deployment.

## Abort conditions

Abort the isolated canary on GPU OOM, reset/Xid, vLLM crash loop, error rate
above 1%, temperature above the owner-defined limit, critical host
memory/disk, production impact, two consecutive metrics failures, or an
identity/safety gate failure. No generic thermal number is embedded.

## Current evidence and consequence

Read-only local preflight found no vLLM command/package, no NVIDIA/ROCm tools,
and no NVIDIA or ROCm compute device node. A generic DRI render node is not
evidence of a vLLM-compatible accelerator. No endpoint was probed and no
service/process was changed.

The current status is `BLOCKED_NO_GPU`. `results.csv` remains header-only;
there is no empirical winner and no production recommendation.
