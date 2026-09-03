"""Envelope binding hash — the second witness of create-level dedup.

``RunStore.create`` collapses a repeated ``idempotency_key`` to the same
run. That key is caller-chosen. This module hashes the *contract* the
key is supposed to name, so a later store can refuse a reused key that
points at a different goal, budget, deadline, or allowlist.

The store is not wired here. Wiring would edit ``run_store.py``, which
another open PR already owns. The hash is the independent record: if two
envelopes bind equally, their contracts matched; if they do not, a silent
collapse would have been a lie.

Kernel purity: hashlib only. No json (the purity wall does not admit it),
no clock, no I/O. ``run_id`` is excluded — it is minted at the boundary
and must not make the same contract look like two contracts.
"""

from __future__ import annotations

import hashlib
from typing import Iterable

from .envelope import TaskEnvelope
from .errors import FailClosedError

# Field separator that cannot appear inside a sha256 hex digest.
_SEP = "\n"


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _digest_seq(values: Iterable[str]) -> str:
    """Order-preserving sequence digest. Empty is a defined value."""
    parts = [_digest_text(v) for v in values]
    return _digest_text(_SEP.join(parts))


def envelope_binding_material(envelope: TaskEnvelope) -> str:
    """Canonical, length-safe material for one envelope.

    Each field is hashed before join so a newline inside ``goal`` cannot
    collide with the separator. ``run_id`` is omitted on purpose.
    """
    if not isinstance(envelope, TaskEnvelope):
        raise FailClosedError(
            f"envelope_binding_material needs TaskEnvelope: {type(envelope)!r}")
    fields = (
        f"version={envelope.version}",
        f"goal={envelope.goal}",
        f"risk_tier={envelope.risk_tier}",
        f"authority_level={envelope.authority_level}",
        f"idempotency_key={envelope.idempotency_key}",
        f"acceptance_criteria_hash={envelope.acceptance_criteria_hash}",
        f"budget_tokens={envelope.budget_tokens}",
        f"budget_aud_cents={envelope.budget_aud_cents}",
        f"deadline_iso={envelope.deadline_iso}",
        f"allowed_tools={_digest_seq(envelope.allowed_tools)}",
        f"parent_evidence={_digest_seq(envelope.parent_evidence)}",
        f"rollback_plan={envelope.rollback_plan or ''}",
        f"rollback_ref={envelope.rollback_ref or ''}",
    )
    return _SEP.join(_digest_text(f) for f in fields)


def envelope_binding_hash(envelope: TaskEnvelope) -> str:
    """sha256 hex of the binding material. Stable for equal contracts."""
    return _digest_text(envelope_binding_material(envelope))


def same_contract(left: TaskEnvelope, right: TaskEnvelope) -> bool:
    """True only when both envelopes bind to the same contract hash."""
    return envelope_binding_hash(left) == envelope_binding_hash(right)
