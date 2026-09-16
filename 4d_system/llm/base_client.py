"""
llm/base_client.py — Base class for LLM API clients.

All clients (GLM, Fugu, mock) follow the same interface:
    .chat(messages, system, temperature) -> str
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import time


@dataclass
class Message:
    role: str       # "system", "user", "assistant"
    content: str


class BaseLLMClient(ABC):
    """Abstract interface that all LLM clients implement."""

    name: str = "base"

    @abstractmethod
    def chat(self, messages: list[Message | dict],
             temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Send a chat completion request. Returns the assistant's text."""
        ...

    def quick(self, prompt: str, system: str = "", temperature: float = 0.7) -> str:
        """Convenience: single-turn prompt → response."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, temperature=temperature)


def to_dicts(messages: list[Message | dict]) -> list[dict]:
    """Normalize Message objects to dicts for API payloads."""
    out = []
    for m in messages:
        if isinstance(m, Message):
            out.append({"role": m.role, "content": m.content})
        else:
            out.append(m)
    return out
