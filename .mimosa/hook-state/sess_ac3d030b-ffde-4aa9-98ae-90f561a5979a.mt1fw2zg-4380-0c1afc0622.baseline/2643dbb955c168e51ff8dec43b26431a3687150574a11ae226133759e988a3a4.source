#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""redact.py -- PII and secret redaction for Octopus telemetry export.

Scans attributes and summary strings before export to remove:
  - Secrets/tokens/passwords (patterns matching known secret formats)
  - Email addresses
  - Phone numbers (basic patterns)
  - File paths containing credentials
  - High-cardinality free-text (replaced with hash prefix)

This module is applied BEFORE any telemetry export. It is fail-open:
if redaction fails, the original value is returned with a warning flag
rather than losing the telemetry record.

No secrets in this file -- only detection patterns.
No network calls. stdlib only.
"""
from __future__ import annotations

import hashlib
import os
import re
from typing import Any

# Secret/PII detection patterns (same family as _ops/memory/gate.py _SECRET_RX)
_SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)(api[_-]?key|apikey|secret|token|password|passwd|credential)\s*[=:]\s*['\"]?[^\s'\"]{8,}", re.ASCII),
    re.compile(r"(?i)sk-[a-zA-Z0-9_-]{8,}", re.ASCII),  # OpenAI-style keys (may contain dashes)
    re.compile(r"(?i)ghp_[a-zA-Z0-9]{36,}", re.ASCII),   # GitHub tokens
    re.compile(r"(?i)gho_[a-zA-Z0-9]{36,}", re.ASCII),   # GitHub OAuth
    re.compile(r"(?i)ghu_[a-zA-Z0-9]{36,}", re.ASCII),   # GitHub user tokens
    re.compile(r"(?i)xox[bpas]-[a-zA-Z0-9-]{10,}", re.ASCII),  # Slack tokens
]

_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_PATTERN = re.compile(r"(?<!\d)\+?\d{7,15}(?!\d)")
_PATH_CREDENTIAL_PATTERN = re.compile(
    r"(?i)(id_rsa|id_ed25519|\.pem|\.key|\.p12|\.pfx|credentials|\.env\.local)",
    re.ASCII,
)


def _hash_prefix(text: str, length: int = 12) -> str:
    """SHA256 prefix for replacing sensitive text."""
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def _redact_string(value: str) -> tuple[str, bool]:
    """Redact a single string value. Returns (redacted_value, was_redacted)."""
    was_redacted = False
    result = value

    # Check for secret patterns
    for pat in _SECRET_PATTERNS:
        if pat.search(result):
            result = pat.sub(lambda m: _hash_prefix(m.group()), result)
            was_redacted = True

    # Redact email addresses
    if _EMAIL_PATTERN.search(result):
        result = _EMAIL_PATTERN.sub(
            lambda m: f"{m.group().split('@')[0][:3]}***@***",
            result,
        )
        was_redacted = True

    # Redact phone numbers
    if _PHONE_PATTERN.search(result):
        result = _PHONE_PATTERN.sub("[PHONE_REDACTED]", result)
        was_redacted = True

    # Redact credential file paths
    if _PATH_CREDENTIAL_PATTERN.search(result):
        result = _PATH_CREDENTIAL_PATTERN.sub("[PATH_REDACTED]", result)
        was_redacted = True

    # Truncate very long strings (high-cardinality risk)
    if len(result) > 512:
        result = result[:256] + "...[" + _hash_prefix(result) + "]"
        was_redacted = True

    return result, was_redacted


def redact_attributes(attrs: dict[str, Any]) -> dict[str, Any]:
    """Redact all attribute values in a span's attributes dict.

    Returns a new dict with redacted values. Numeric values pass through.
    """
    redacted: dict[str, Any] = {}
    for k, v in attrs.items():
        if isinstance(v, str):
            redacted[k], _ = _redact_string(v)
        elif isinstance(v, (int, float, bool)):
            redacted[k] = v
        elif v is None:
            redacted[k] = None
        elif isinstance(v, list):
            redacted[k] = [
                _redact_string(item)[0] if isinstance(item, str) else item
                for item in v
            ]
        elif isinstance(v, dict):
            redacted[k] = redact_attributes(v)
        else:
            # Unknown type: convert to string and redact
            redacted[k] = _redact_string(str(v))[0]
    return redacted


def redact_summary(summary: str) -> str:
    """Redact a summary string (used in events, traces)."""
    redacted, _ = _redact_string(summary)
    return redacted


def contains_secrets(text: str) -> bool:
    """Check if text potentially contains secrets. Used for pre-export validation."""
    if not text:
        return False
    for pat in _SECRET_PATTERNS:
        if pat.search(text):
            return True
    return False
