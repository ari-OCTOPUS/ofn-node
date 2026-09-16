"""FuguProvider — preferred Lab BrainPort backend (local/prefer-fugu)."""
from __future__ import annotations

import os
import time
from typing import Iterator, Union

from ..contract import ModelProvider
from ..types import (
    GenerateRequest,
    GenerateResponse,
    HealthStatus,
    ModelCapabilities,
    ToolCallRequest,
    ToolCallResponse,
)

# Rough token~char heuristic for estimate_cost only
_CHARS_PER_TOKEN = 4
# Prefer-fugu default rate card (placeholder; override via env)
_USD_PER_1K_IN = float(os.environ.get("FUGU_USD_PER_1K_IN", "0.0001"))
_USD_PER_1K_OUT = float(os.environ.get("FUGU_USD_PER_1K_OUT", "0.0002"))


class FuguProvider(ModelProvider):
    name = "fugu"

    def __init__(self, endpoint: str | None = None, api_key: str | None = None) -> None:
        self.endpoint = endpoint or os.environ.get("FUGU_ENDPOINT", "")
        self.api_key = api_key or os.environ.get("FUGU_API_KEY", "")

    def generate(self, req: GenerateRequest) -> GenerateResponse:
        # Thin adapter: if no endpoint, return deterministic local stub text for marketing dry-run.
        if not self.endpoint:
            text = self._local_copy(req)
            return GenerateResponse(
                text=text,
                provider=self.name,
                usage={"prompt_chars": len(req.prompt), "completion_chars": len(text), "mode": "local_stub"},
                cost_usd_est=self.estimate_cost(req, chars=len(req.prompt) + len(text)),
            )
        # Live path placeholder — wire HTTP when FUGU_ENDPOINT is set (no business model names).
        raise NotImplementedError(
            "FuguProvider live HTTP not wired in this lab stub; set no FUGU_ENDPOINT for local_stub, "
            "or extend generate() once endpoint contract is fixed."
        )

    def stream(self, req: GenerateRequest) -> Iterator[str]:
        text = self.generate(req).text
        # coarse chunk stream for callers that expect streaming
        step = max(24, len(text) // 8 or 1)
        for i in range(0, len(text), step):
            yield text[i : i + step]

    def tool_call(self, req: ToolCallRequest) -> ToolCallResponse:
        # Fugu lab stub: no native tools yet — echo empty tool_calls with note
        return ToolCallResponse(
            content="[fugu] tool_call not enabled in lab stub; use generate for copy.",
            tool_calls=[],
            provider=self.name,
            usage={"mode": "stub_no_tools"},
            cost_usd_est=0.0,
        )

    def health(self) -> HealthStatus:
        t0 = time.perf_counter()
        ok = True
        detail = "local_stub" if not self.endpoint else f"endpoint_configured:{bool(self.endpoint)}"
        if self.endpoint:
            # Do not probe network in shared-infra stub by default (keep dry-run safe).
            detail = "endpoint_set_unprobed"
        ms = (time.perf_counter() - t0) * 1000
        return HealthStatus(ok=ok, provider=self.name, detail=detail, latency_ms=ms)

    def estimate_cost(self, req: Union[GenerateRequest, ToolCallRequest], *, chars: int | None = None) -> float:
        if chars is None:
            chars = len(getattr(req, "prompt", "") or "") + len(getattr(req, "system", "") or "")
            chars += int(getattr(req, "max_tokens", 256) or 256) * _CHARS_PER_TOKEN
        tokens = max(1, chars // _CHARS_PER_TOKEN)
        # split 40/60 in/out heuristic
        inn, out = int(tokens * 0.4), int(tokens * 0.6)
        return (inn / 1000.0) * _USD_PER_1K_IN + (out / 1000.0) * _USD_PER_1K_OUT

    def model_capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            provider=self.name,
            generate=True,
            stream=True,
            tool_call=False,
            max_context=8192,
            capabilities=["copy", "chat"],
        )

    def _local_copy(self, req: GenerateRequest) -> str:
        # Deterministic helper for Ziman marketing dry-runs (not production copy).
        sys_bit = (req.system or "You write short product copy.").strip()
        return (
            f"[fugu/local] {sys_bit}\n"
            f"Draft for: {req.prompt.strip()[:500]}\n"
            f"— warm, concrete, AU-friendly; capability={req.capability}"
        )
