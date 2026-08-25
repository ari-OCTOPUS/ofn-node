"""Observe-only vLLM / GPU probe. Never runs a GPU benchmark."""

from __future__ import annotations

import shutil
from typing import Any

BLOCKED = "BLOCKED_NO_GPU"


def observe_vllm_runtime() -> dict[str, Any]:
    nvidia = shutil.which("nvidia-smi")
    vllm_bin = shutil.which("vllm")
    gpu = False
    try:
        import torch  # type: ignore

        gpu = bool(getattr(torch, "cuda", None) and torch.cuda.is_available())
    except Exception:
        gpu = False
    blocked = (not gpu) or nvidia is None
    return {
        "status": BLOCKED if blocked else "GPU_PRESENT_BUT_BENCHMARK_FORBIDDEN",
        "blocked_reason": BLOCKED if blocked else None,
        "nvidia_smi": nvidia,
        "vllm_bin": vllm_bin,
        "cuda_available": gpu,
        "benchmark_runs": 0,
        "cbor2_install_attempted": False,
        "note": "KV cache is not episodic or identity memory. Orange Pi is orchestrator only.",
    }
