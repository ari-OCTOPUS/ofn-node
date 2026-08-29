# vLLM KV Block-Size Pareto Report

- final_status: `BLOCKED_NO_GPU`
- empirical_result_rows: `0`
- pareto_frontier: `not computed`

No GPU benchmark was run. `results.csv` contains only its redacted schema
header, so there is no empirical TTFT, E2E, throughput, APC, preemption,
fragmentation, queue, or memory winner.

Theoretical tail-fragmentation estimates cannot select a block size. Candidate
selection requires at least three independent repetitions, separate cold/warm
cache phases, complete metrics, safety gates, and non-overlapping confidence
evidence.
