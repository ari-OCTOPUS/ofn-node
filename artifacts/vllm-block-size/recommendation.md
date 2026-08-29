# vLLM KV Block-Size Recommendation

- final_status: `BLOCKED_NO_GPU`
- selected_profile: `none`
- selected_block_size: `unknown`
- baseline_block_size: `unknown (platform auto was not resolved)`
- model/revision: `unknown`
- GPU/backend: `no compatible local CUDA/ROCm evidence; backend unknown`
- workloads: `W1-W5 planned; W4 awaits an owner-supplied anonymized histogram`
- confidence: `none — no GPU measurements`
- TTFT delta: `not measured`
- throughput delta: `not measured`
- cache-hit delta: `not measured`
- fragmentation delta: `theoretical only; not decision evidence`
- preemption delta: `not measured`
- known limitations: `no local vLLM/GPU, version-resolved capabilities, resolved cache config, or Prometheus run data`
- rollback command: `rm -f -- 'ofn/benchmarks/__init__.py' 'ofn/benchmarks/vllm_block_size.py' 'ofn/benchmarks/workload_manifest.py' 'ofn/benchmarks/result_store.py' 'ofn/adapters/vllm_metrics.py' 'scripts/benchmark_vllm_block_size.py' 'ofn/organism/tests/test_vllm_block_size_estimator.py' 'ofn/organism/tests/test_vllm_block_size_planning.py' 'ofn/organism/tests/test_vllm_workload_manifest.py' 'ofn/organism/tests/test_vllm_metrics.py' 'ofn/organism/tests/test_vllm_result_store.py' 'ofn/organism/tests/test_vllm_block_size_cli.py' 'docs/adr/ADR-VLLM-KV-BLOCK-SIZE.md' 'artifacts/vllm-block-size/preflight.json' 'artifacts/vllm-block-size/workload-manifest.json' 'artifacts/vllm-block-size/results.csv' 'artifacts/vllm-block-size/pareto-report.md' 'artifacts/vllm-block-size/recommendation.md' 'artifacts/vllm-block-size/rollback.md'`

There is no empirical winner. Do not infer a preferred block size from the
estimator, do not alter a running process dynamically, and do not deploy.
