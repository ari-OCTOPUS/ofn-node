"""Explainable pre-call token estimates for one request.

The Round-1 incident billed every owner question at the same flat estimate —
`Job.estimated_tokens` defaulted to 2000 regardless of the prompt, and the
quota's invisible-spend multiplier turned that into a 5200-token projection
against a 700-token share. A number with no visible derivation is a number
nobody can argue with, so the estimator now shows its work:

    estimated_input  = ceil(chars / chars_per_token)   (never zero)
    request_estimate = estimated_input + reserved_output

Both figures are *visible* tokens. The orchestration multiplier is applied
once, inside the quota, where admission and accounting already agree on it —
applying it here too would double-charge the projection.

The chars-per-token figure is deliberately conservative for Persian text
(a prompt of N characters is rarely fewer than N/2 tokens on current
tokenizers) and it is a ceiling on the estimate, not a claim about the
provider: the estimate gates admission, the billed figure records reality.
"""

from __future__ import annotations

import math

DEFAULT_CHARS_PER_TOKEN = 2.0
DEFAULT_RESERVED_OUTPUT_TOKENS = 800


def estimate_request(
    text: str,
    *,
    chars_per_token: float = DEFAULT_CHARS_PER_TOKEN,
    reserved_output: int = DEFAULT_RESERVED_OUTPUT_TOKENS,
) -> dict[str, int]:
    """Estimate one prompt's visible-token cost, with the arithmetic exposed."""
    if chars_per_token <= 0:
        raise ValueError("chars_per_token must be positive")
    if reserved_output < 0:
        raise ValueError("reserved_output must not be negative")
    chars = len(text)
    estimated_input = max(1, math.ceil(chars / chars_per_token))
    return {
        "chars": chars,
        "chars_per_token": chars_per_token,
        "estimated_input": int(estimated_input),
        "reserved_output": int(reserved_output),
        "request_estimate": int(estimated_input + reserved_output),
    }
