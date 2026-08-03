"""Deterministic mock LLM — the baseline brain. No network, no keys, no surprises."""

from __future__ import annotations

import hashlib

from ...kernel.ports import LLMRequest, LLMResponse


class MockLLM:
    """Echoes a canned, request-derived answer. Deterministic for a given prompt."""

    def complete(self, request: LLMRequest) -> LLMResponse:
        fingerprint = hashlib.sha256(request.prompt.encode("utf-8")).hexdigest()[:8]
        text = f"[mock:{request.task}:{fingerprint}] proposal acknowledged"
        return LLMResponse(
            text=text,
            input_tokens=len(request.prompt) // 4,
            output_tokens=len(text) // 4,
            orchestration_tokens=0,
        )
