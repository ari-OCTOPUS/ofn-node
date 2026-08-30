"""brain — لایه‌ی ارائه‌دهنده‌ی LLM (Anthropic / OpenAI-compat / Offline)."""

from .providers import (
    BaseBrainProvider,
    AnthropicBrainProvider,
    OpenAICompatBrainProvider,
    OfflineBrainProvider,
    get_brain_provider,
)
from .question_bank import QuestionBank
from .prompt import get_system_prompt
from .brain_router import BrainRouter, Route, classify_depth

__all__ = [
    "BaseBrainProvider", "AnthropicBrainProvider", "OpenAICompatBrainProvider",
    "OfflineBrainProvider", "get_brain_provider", "QuestionBank", "get_system_prompt",
    "BrainRouter", "Route", "classify_depth",
]
