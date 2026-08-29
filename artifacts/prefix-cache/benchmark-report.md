# vLLM APC Hash Benchmark Report

- created_at_utc: `2026-08-25T09:16:46Z`
- suite: `vllm_apc_hash_benchmark`

## Workload

- block_size: `16`
- blocks_per_prompt: `4`
- collision_samples: `5000`
- iterations: `400`
- lora_id: `base`
- model_id: `model-qwen3-0.6b`
- model_revision: `rev-1`
- prompts_per_tenant: `12`
- random_seed: `7`
- tenant_count: `4`
- tokenizer_id: `tokenizer-qwen3`

## Algorithm Results

### sha256

- serialization mean_us: `8.378`
- serialization p95_us: `8.167`
- overlap_ratio without salt: `1.0`
- overlap_ratio with salt: `0.0`
- collision_rate: `0.0`
- cross-language reproducibility: `python_pickle_not_cross_language_stable`

### sha256_cbor

- status: `UNAVAILABLE`
- reason: `cbor2_not_installed`

## Notes

- APC hash keys are benchmarked offline; no vLLM service mutation.
- KV cache is inference-temporary and not event memory.
- Use tenant-specific cache_salt for isolation in multi-tenant serving.
