"""Thin ModelProvider contract — businesses talk to this, never to model names."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator, Iterator, Union

from .types import (
    GenerateRequest,
    GenerateResponse,
    HealthStatus,
    ModelCapabilities,
    ToolCallRequest,
    ToolCallResponse,
)


class ModelProvider(ABC):
    """Shared Lab BrainPort surface for Ziman + Studio (and later others).

    Rules:
    - Business code imports brainport.router / ModelProvider only.
    - Never import FuguProvider / DeepSeekProvider / model id strings from a business package.
    """

    name: str

    @abstractmethod
    def generate(self, req: GenerateRequest) -> GenerateResponse:
        ...

    @abstractmethod
    def stream(self, req: GenerateRequest) -> Iterator[str]:
        ...

    async def astream(self, req: GenerateRequest) -> AsyncIterator[str]:
        for chunk in self.stream(req):
            yield chunk

    @abstractmethod
    def tool_call(self, req: ToolCallRequest) -> ToolCallResponse:
        ...

    @abstractmethod
    def health(self) -> HealthStatus:
        ...

    @abstractmethod
    def estimate_cost(self, req: Union[GenerateRequest, ToolCallRequest], *, chars: int | None = None) -> float:
        """Return estimated USD cost for the request (best-effort)."""
        ...

    @abstractmethod
    def model_capabilities(self) -> ModelCapabilities:
        ...
