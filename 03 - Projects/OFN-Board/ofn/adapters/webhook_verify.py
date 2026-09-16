"""Vendor-neutral webhook signature verification.

Most marketing platforms sign their webhook payloads with HMAC. The exact
algorithm, header name, and payload construction differ by vendor, but the
shape is always: HMAC(secret, payload) transmitted in a header.

This module provides:
  * a generic HMAC verifier that accepts the header name and signing secret;
  * vendor-specific presets (empty for now — filled when official docs arrive);
  * a no-op verifier for the fake connector and testing.

No real secrets are read from env or config in this module. The caller
(either the node wiring or the connector) provides the secret at call time.
That keeps this module testable without mocking the environment.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class VerifyResult:
    valid: bool
    reason: str = ""


def verify_hmac(payload: bytes, secret: str, signature: str,
                *, algorithm: str = "sha256",
                digest_separator: str = "=") -> VerifyResult:
    """Verify an HMAC signature from a webhook payload.

    Args:
        payload: The raw request body.
        secret: The signing secret (provided by the caller, never read from env).
        signature: The signature value from the header.
        algorithm: Hash algorithm name (default sha256).
        digest_separator: Character separating the algorithm name and hex digest
            in the header value (e.g. "sha256=abcdef...").

    Returns VerifyResult with valid=True if the signature matches.
    """
    if not secret:
        return VerifyResult(False, "no signing secret configured")
    if not signature:
        return VerifyResult(False, "no signature in header")

    # Strip prefix if present (e.g. "sha256=")
    if digest_separator and digest_separator in signature:
        expected_prefix, _ = signature.split(digest_separator, 1)
    else:
        expected_prefix = algorithm

    try:
        mac = hmac.new(
            secret.encode("utf-8"), payload,
            getattr(hashlib, algorithm))
    except (AttributeError, ValueError) as exc:
        return VerifyResult(False, f"unsupported algorithm: {exc}")

    expected = f"{expected_prefix}={mac.hexdigest()}"
    if not hmac.compare_digest(signature, expected):
        return VerifyResult(False, "signature mismatch")
    return VerifyResult(True)


def noop_verify(payload: bytes, headers: Mapping[str, str]) -> VerifyResult:
    """Accept everything. Used by the fake connector and in tests."""
    return VerifyResult(True)


def verify_with_header(payload: bytes, headers: Mapping[str, str],
                        header_name: str, secret: str,
                        algorithm: str = "sha256") -> VerifyResult:
    """Extract signature from a header and verify it.

    The header name comparison is case-insensitive.
    """
    signature = ""
    for key, value in headers.items():
        if key.lower() == header_name.lower():
            signature = value
            break
    return verify_hmac(payload, secret, signature, algorithm=algorithm)
