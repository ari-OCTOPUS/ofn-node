#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""trace_context.py -- Unified trace context propagation for Octopus.

Bridges the gap between the four existing trace systems in the vault:
  1. brain/events.py       -- trace_id = uuid4().hex[:8]
  2. otel_setup.py          -- trace_id = uuid4().hex[:16]
  3. semantic_trace.py      -- trace_id = sha256(...).hexdigest()[:16]
  4. cognitive/event_stream.py -- trace_id = uuid4().hex[:12]

This module provides a SINGLE canonical trace_id format (16 hex chars)
and a mechanism for propagation across all subsystems via:
  - Environment variable: OCTOPUS_TRACE_ID
  - Explicit parameter passing (preferred)
  - Context retrieval for integration with brain/events.py

Default OFF (trace propagation only active when a trace_id is set).
No network, no external services, no secrets.
"""
from __future__ import annotations

import hashlib
import os
import uuid
from contextvars import ContextVar
from typing import Optional

TRACE_ID_LENGTH = 16  # canonical length for all Octopus trace IDs
_ENV_KEY = "OCTOPUS_TRACE_ID"

# ContextVar for in-process propagation (async-safe)
_current_trace_id: ContextVar[str | None] = ContextVar(
    "octopus_trace_id", default=None
)


def mint_trace_id() -> str:
    """Generate a new canonical trace ID (16 hex chars, UUID-based)."""
    return uuid.uuid4().hex[:TRACE_ID_LENGTH]


def set_trace_id(trace_id: str) -> None:
    """Set the current trace ID in the context variable."""
    normalized = _normalize_trace_id(trace_id)
    if normalized is None:
        return  # invalid trace_id, do not set
    _current_trace_id.set(normalized)


def get_trace_id() -> str | None:
    """Get the current trace ID from context, then env, then None."""
    tid = _current_trace_id.get()
    if tid is not None:
        return tid
    env_tid = os.environ.get(_ENV_KEY, "").strip()
    if env_tid and len(env_tid) >= 8:
        return env_tid[:TRACE_ID_LENGTH]
    return None


def clear_trace_id() -> None:
    """Clear the current trace ID from context."""
    _current_trace_id.set(None)


def _normalize_trace_id(trace_id: str | None) -> str | None:
    """Normalize a trace_id to 16 hex chars. Returns None if invalid.

    Accepts:
      - 16+ hex chars (truncates to 16)
      - 8 hex chars (pads with zeros to 16) -- backward compat with brain/events.py
      - UUID string (converts to hex[:16])
    """
    if not trace_id or not isinstance(trace_id, str):
        return None
    tid = trace_id.strip()
    if not tid:
        return None
    # If it looks like a UUID, convert to hex
    if "-" in tid and len(tid) >= 32:
        try:
            tid = uuid.UUID(tid).hex
        except ValueError:
            return None
    # Keep only hex chars
    hex_chars = "".join(c for c in tid if c in "0123456789abcdef")
    if len(hex_chars) < 8:
        return None  # too short to be useful
    if len(hex_chars) < TRACE_ID_LENGTH:
        # Pad to 16 for backward compat with short IDs
        hex_chars = hex_chars.ljust(TRACE_ID_LENGTH, "0")
    return hex_chars[:TRACE_ID_LENGTH]


def trace_id_for_brain_events() -> str:
    """Get a trace_id suitable for brain/events.py (8-char format).

    brain/events.py uses uuid4().hex[:8]. This provides backward compatibility
    by truncating the canonical 16-char trace_id to 8 chars.
    """
    tid = get_trace_id()
    if tid:
        return tid[:8]
    return uuid.uuid4().hex[:8]


def trace_id_for_semantic_trace() -> str:
    """Get a trace_id suitable for semantic_trace.py (16-char hash format).

    semantic_trace.py uses sha256-based IDs. This returns a deterministic
    16-char hash from the current trace_id so the semantic trace can be
    correlated back.
    """
    tid = get_trace_id()
    if tid:
        return hashlib.sha256(tid.encode()).hexdigest()[:16]
    return hashlib.sha256(
        f"{os.times()}-{uuid.uuid4().hex}".encode()
    ).hexdigest()[:16]


def trace_id_for_cognitive() -> str:
    """Get a trace_id suitable for cognitive/event_stream.py.

    cognitive/event_stream.py uses trace_{uuid4().hex[:12]} format.
    This returns the canonical trace_id (12 chars for compatibility).
    """
    tid = get_trace_id()
    if tid:
        return f"trace_{tid[:12]}"
    return f"trace_{uuid.uuid4().hex[:12]}"
