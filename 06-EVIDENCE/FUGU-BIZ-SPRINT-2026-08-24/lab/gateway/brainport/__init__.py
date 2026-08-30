"""BrainPort Lab gateway — shared ModelProvider for Ziman + Studio.

Businesses: `from brainport.router import get_provider` then generate/stream/...
Never import provider classes or model name strings from marketing/Ziman/Studio code.
"""
from .contract import ModelProvider
from .router import get_provider
from .types import GenerateRequest, GenerateResponse, HealthStatus, ToolCallRequest, ToolCallResponse

__all__ = [
    "ModelProvider",
    "get_provider",
    "GenerateRequest",
    "GenerateResponse",
    "HealthStatus",
    "ToolCallRequest",
    "ToolCallResponse",
]
