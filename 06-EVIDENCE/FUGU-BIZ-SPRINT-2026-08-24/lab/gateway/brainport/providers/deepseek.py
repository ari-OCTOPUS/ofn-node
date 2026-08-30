"""DeepSeekProvider — stub only. Do not call from business packages directly."""
from __future__ import annotations

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


class DeepSeekProvider(ModelProvider):
    name = "deepseek"

    def generate(self, req: GenerateRequest) -> GenerateResponse:
        raise NotImplementedError("DeepSeekProvider is a lab stub — not wired. Use router default (fugu).")

    def stream(self, req: GenerateRequest) -> Iterator[str]:
        raise NotImplementedError("DeepSeekProvider stub — stream unavailable.")

    def tool_call(self, req: ToolCallRequest) -> ToolCallResponse:
        raise NotImplementedError("DeepSeekProvider stub — tool_call unavailable.")

    def health(self) -> HealthStatus:
        return HealthStatus(ok=False, provider=self.name, detail="stub_not_wired")

    def estimate_cost(self, req: Union[GenerateRequest, ToolCallRequest], *, chars: int | None = None) -> float:
        return 0.0

    def model_capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            provider=self.name,
            generate=False,
            stream=False,
            tool_call=False,
            max_context=0,
            capabilities=[],
        )
