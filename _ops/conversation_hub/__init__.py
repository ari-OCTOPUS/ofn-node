# _ops/conversation_hub — Conversation Hub package
# ADR-040: Unified chat orchestrator for Octopus Mini App.
# This is a façade — it rides on top of existing modules, never replaces them.

from .schemas import (
    ChatReply,
    ChatRequest,
    ProvenanceEvent,
    RouteDecision,
    SourceRef,
)
from .service import _enabled, handle
from .router import classify_intent

__all__ = [
    "handle",
    "_enabled",
    "classify_intent",
    "ChatRequest",
    "ChatReply",
    "ProvenanceEvent",
    "RouteDecision",
    "SourceRef",
]
