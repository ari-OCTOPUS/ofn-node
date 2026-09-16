"""Correlation ID: trace a request from webhook arrival through processing.

Generates a unique ID per inbound request, propagates it in the response
header, and stores it alongside every inbox item and ledger entry it touches.

The ID format is a short hex string from os.urandom — not a UUID — because:
  * it appears in logs and on-screen debugging panels where compactness matters;
  * there is no interoperability requirement (this is purely internal);
  * 8 bytes (16 hex chars) gives 2^64 namespace, which is enough.

No external dependency. Uses only stdlib `os.urandom` and `secrets`.
"""

from __future__ import annotations

import os

HEADER = "X-Correlation-ID"
"""The HTTP header name, both inbound and outbound."""


def generate() -> str:
    """Generate a new correlation ID: 16 hex chars from os.urandom."""
    return os.urandom(8).hex()


def from_header(headers: dict, default: str = "") -> str:
    """Extract the correlation ID from request headers, case-insensitive.

    Returns the caller-supplied ID if present, so a chain of calls through
    the node preserves one correlation across multiple steps. Returns default
    if the header is absent.
    """
    for key, value in headers.items():
        if key.lower() == HEADER.lower():
            return value
    return default
