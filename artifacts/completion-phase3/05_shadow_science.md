# Phase 3 — OFN-L4 shadow, Active Inference, WBE, vLLM observe

LIVE_RUNTIME_MODIFIED: false
SERVICES_RESTARTED: false
HTTP_8091: false
GPU_BENCHMARK_RUNS: 0
EXECUTABLE_TOTAL: 0

## OFN-L4

- Kernel + outbox in `/opt/octopus/ofn-l4/ofnl4/kernel.py` and `store.py`
- Shadow ticks: `ofnl4/shadow.py` (`HTTP_LISTEN=false`, port `None`)
- Identity bridge: read-only v1 backup → `identity_bridge` rows with `merged=0`
- Gate file: `artifacts/completion-phase3/gates/OFN_L4_RUN.json` execute=false
- `var/L4-GATE.json` listen=false run=false
- Shadow DB for this mission: `artifacts/completion-phase3/ofn-l4-shadow.db` (gitignored)

## Active Inference

`ofn/organism/cognition/active_inference.py` — stdlib POMDP `|S|≤4`, EFE = risk + ambiguity, `executable=false`, no pymdp/jax.

## WBE

`ofn/organism/science/wbe_allometry.py` — analysis only. Not imported by homeostasis. Not a timer or SAFE_HALT trip.

## vLLM

`ofn/adapters/vllm_observe.py` status `BLOCKED_NO_GPU`. No cbor2 install. No GPU benchmark.
