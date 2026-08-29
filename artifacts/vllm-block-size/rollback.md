# Rollback — vLLM KV Block-Size Harness

No rollback was executed. Review the repository state first, then remove only
the files introduced by this harness:

- `ofn/benchmarks/__init__.py`
- `ofn/benchmarks/vllm_block_size.py`
- `ofn/benchmarks/workload_manifest.py`
- `ofn/benchmarks/result_store.py`
- `ofn/adapters/vllm_metrics.py`
- `scripts/benchmark_vllm_block_size.py`
- `ofn/organism/tests/test_vllm_block_size_estimator.py`
- `ofn/organism/tests/test_vllm_block_size_planning.py`
- `ofn/organism/tests/test_vllm_workload_manifest.py`
- `ofn/organism/tests/test_vllm_metrics.py`
- `ofn/organism/tests/test_vllm_result_store.py`
- `ofn/organism/tests/test_vllm_block_size_cli.py`
- `docs/adr/ADR-VLLM-KV-BLOCK-SIZE.md`
- `artifacts/vllm-block-size/preflight.json`
- `artifacts/vllm-block-size/workload-manifest.json`
- `artifacts/vllm-block-size/results.csv`
- `artifacts/vllm-block-size/pareto-report.md`
- `artifacts/vllm-block-size/recommendation.md`
- `artifacts/vllm-block-size/rollback.md`

Scoped command (documentation only; not executed):

```bash
rm -f -- 'ofn/benchmarks/__init__.py' 'ofn/benchmarks/vllm_block_size.py' 'ofn/benchmarks/workload_manifest.py' 'ofn/benchmarks/result_store.py' 'ofn/adapters/vllm_metrics.py' 'scripts/benchmark_vllm_block_size.py' 'ofn/organism/tests/test_vllm_block_size_estimator.py' 'ofn/organism/tests/test_vllm_block_size_planning.py' 'ofn/organism/tests/test_vllm_workload_manifest.py' 'ofn/organism/tests/test_vllm_metrics.py' 'ofn/organism/tests/test_vllm_result_store.py' 'ofn/organism/tests/test_vllm_block_size_cli.py' 'docs/adr/ADR-VLLM-KV-BLOCK-SIZE.md' 'artifacts/vllm-block-size/preflight.json' 'artifacts/vllm-block-size/workload-manifest.json' 'artifacts/vllm-block-size/results.csv' 'artifacts/vllm-block-size/pareto-report.md' 'artifacts/vllm-block-size/recommendation.md' 'artifacts/vllm-block-size/rollback.md'
rmdir --ignore-fail-on-non-empty   artifacts/vllm-block-size scripts ofn/benchmarks
```

Do not reset the branch, clean untracked files, or touch existing prefix-cache
work, services, systemd, endpoints, state, logs, or unrelated dirty files.
