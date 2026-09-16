"""Shared request/response types for BrainPort ModelProvider (lab shared infra)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Iterator, Optional


@dataclass
class GenerateRequest:
    prompt: str
    system: Optional[str] = None
    max_tokens: int = 1024
    temperature: float = 0.4
    # Businesses pass capability hints, NEVER vendor model ids.
    capability: str = "copy"  # copy | chat | tool | embed
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerateResponse:
    text: str
    provider: str
    usage: dict[str, Any] = field(default_factory=dict)
    cost_usd_est: float = 0.0
    raw: Any = None


@dataclass
class ToolCallRequest:
    prompt: str
    tools: list[dict[str, Any]]
    system: Optional[str] = None
    capability: str = "tool"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCallResponse:
    content: Optional[str]
    tool_calls: list[dict[str, Any]]
    provider: str
    usage: dict[str, Any] = field(default_factory=dict)
    cost_usd_est: float = 0.0


@dataclass
class HealthStatus:
    ok: bool
    provider: str
    detail: str = ""
    latency_ms: Optional[float] = None


@dataclass
class ModelCapabilities:
    provider: str
    generate: bool = True
    stream: bool = True
    tool_call: bool = False
    max_context: int = 8192
    capabilities: list[str] = field(default_factory=lambda: ["copy", "chat"])
