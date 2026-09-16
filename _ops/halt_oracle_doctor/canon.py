"""canon — the single canonicalization rule, pinned by a frozen vector.

Why this file exists: the vault/audit found TWO incompatible "canonical" JSON rules
in the organism (`ofn/adapters/ledger.py:52` uses compact separators; 
`ofn/octopus_observation/fixture_run.py:68` uses default separators). Both call
themselves canonical. A hash computed under one rule cannot match the other, so a
cross-artifact comparison can pass or fail for the wrong reason.

This module states ONE rule, and `self_test()` pins it against a literal digest so
drift is caught rather than assumed away. It deliberately does NOT import the ledger
(to avoid dragging SQLite and the live DB path into an offline tool).

The pinned vector (frozen 2026-09-17, computed independently):
    value          = {"z":1,"a":"های","n":[3,2,1]}
    compact sha256 = a021a5910b521e416dfb517cf16bfb93bee8cf762d5f547088624fc9a771261a
    default-sep    = 84072699f0aad94ffa50c1e1e35cd72c6b96e97a9d0023973a5f29e58b374177
The two differ, which is the whole point: the rule must be stated, not implied.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

RULE_ID = "octopus.canon.compact-sortkeys-utf8/1"

# Frozen vector — literal, never recomputed from the same call it is testing.
VECTOR_VALUE: dict[str, Any] = {"z": 1, "a": "های", "n": [3, 2, 1]}
VECTOR_COMPACT_SHA256 = "a021a5910b521e416dfb517cf16bfb93bee8cf762d5f547088624fc9a771261a"
VECTOR_DEFAULT_SEP_SHA256 = "84072699f0aad94ffa50c1e1e35cd72c6b96e97a9d0023973a5f29e58b374177"


def canonical(obj: Any) -> str:
    """Deterministic JSON. sort_keys, compact separators, UTF-8, no ASCII escaping.

    This is the LEDGER's rule, adopted deliberately as the doctor's single rule.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(obj: Any) -> str:
    """sha256 over the canonical bytes."""
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def canonical_default_separators(obj: Any) -> str:
    """The OTHER rule, present only so the divergence can be demonstrated in a test."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def self_test() -> list[str]:
    """Return a list of failures; empty list == green. No I/O, no network, no env."""
    failures: list[str] = []

    got = digest(VECTOR_VALUE)
    if got != VECTOR_COMPACT_SHA256:
        failures.append(f"compact vector drift: expected {VECTOR_COMPACT_SHA256}, got {got}")

    other = hashlib.sha256(
        canonical_default_separators(VECTOR_VALUE).encode("utf-8")
    ).hexdigest()
    if other != VECTOR_DEFAULT_SEP_SHA256:
        failures.append(f"default-separator vector drift: expected {VECTOR_DEFAULT_SEP_SHA256}, got {other}")

    if got == other:
        failures.append(
            "the two rules no longer diverge — the pinned vectors are wrong or the "
            "rules collapsed; either way this pin is no longer testing anything"
        )

    # Determinism: same input twice must be byte-identical.
    if canonical(VECTOR_VALUE) != canonical(VECTOR_VALUE):
        failures.append("canonical() is not deterministic on the same input")

    return failures
