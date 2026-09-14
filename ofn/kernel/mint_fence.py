"""Mint fence — kernel-pure admission for a run_id mint.

``create_envelope()`` is the trust boundary's factory. This module is
the second witness: may this *proposed* run_id be minted here?

A run_id is an identity. Identity collisions were a real bug in the
sister project (two different contradictions both called C-008). The
fence refuses a proposed id that already sits in a provided registry.
A missing registry is UNKNOWN, not an empty set — UNKNOWN is not
FALSE and is not a grant.

Only ``trusted_boundary`` may mint. An arm, pack, or model proposing
an id is a known refusal (``untrusted_boundary``), not an unknown.
Unknown boundary names fail closed.

A sealed send/ready name is never a run_id. ``campaign_envelope_ready``
is structurally distinct from ``send_authorized``; both are refused.

HALT stops STARTS. This fence has no halt parameter: collision
lookup on an in-flight registry must still work so recovery does
not need the owner.

Not wired into the run store or ``create_envelope`` (those files are
owned by other open changes).

Admitting a mint is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import AbstractSet, Iterable, Optional

from .envelope import RUN_ID_RE
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed boundary vocabulary. Widen only with a test.
BOUNDARIES = frozenset({"trusted_boundary"})

# Known untrusted proposers. These are a refusal, not an unknown.
UNTRUSTED_BOUNDARIES = frozenset({"arm", "pack", "model"})

# Known refusals. Unknown names fail closed — they are not
# classified as FALSE.
REFUSAL_REASONS = frozenset({
    "id_collision",
    "sealed_effect",
    "untrusted_boundary",
})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A mint fence never authorizes a send. Structurally False."""
    return False


def halt_blocks_mint() -> bool:
    """Structurally False. HALT stops STARTS, not collision lookup."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. Admission is not chattr +i."""
    return False


def unknown_registry_is_empty() -> bool:
    """Structurally False. A missing registry is UNKNOWN, not empty."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Naming a run_id is not an external effect."""
    return False


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    folded = name.strip().lower().replace("-", "_")
    return folded in {s.replace("-", "_") for s in _SEALED}


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


def _require_registry(existing_ids: object) -> AbstractSet[str]:
    """A missing registry is UNKNOWN, not an empty set.

    ``None`` fails closed. A string is not a registry (iteration
    would walk characters). A bool is not a registry.
    """
    if existing_ids is None:
        raise FailClosedError(
            "existing_ids registry is UNKNOWN, not empty — refusing mint")
    if isinstance(existing_ids, (bool, str, bytes, bytearray)):
        raise FailClosedError(
            f"existing_ids must be a set of names: {existing_ids!r}")
    if not isinstance(existing_ids, Iterable):
        raise FailClosedError(
            f"existing_ids must be a set of names: {existing_ids!r}")
    out: set[str] = set()
    for item in existing_ids:
        if isinstance(item, bool) or not isinstance(item, str) or not item.strip():
            raise FailClosedError(
                f"existing_ids entries must be names: {item!r}")
        if _is_sealed(item):
            raise FailClosedError(
                f"existing_ids cannot name a sealed send/ready state: {item!r}")
        out.add(item.strip())
    return out


@dataclass(frozen=True)
class MintDecision:
    """The mint-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    boundary: str
    proposed_id: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "MintDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a mint fence is not a send")
        object.__setattr__(self, "boundary",
                           _require_name(self.boundary, what="boundary"))
        object.__setattr__(self, "proposed_id",
                           _require_name(self.proposed_id, what="proposed_id"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed mint must not carry a reason: {self.reason!r}")
            if self.boundary not in BOUNDARIES:
                raise FailClosedError(
                    "MintDecision cannot allow an untrusted boundary")
            if _is_sealed(self.proposed_id) or _is_sealed(self.boundary):
                raise FailClosedError(
                    "MintDecision cannot grant a sealed send/ready name")
            if not RUN_ID_RE.match(self.proposed_id):
                raise FailClosedError(
                    f"allowed mint must carry a boundary-shaped run_id: "
                    f"{self.proposed_id!r}")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
            if _is_sealed(self.proposed_id) or _is_sealed(self.boundary):
                if self.reason != "sealed_effect":
                    raise FailClosedError(
                        "MintDecision cannot mis-label a sealed send/ready name")


def admit_mint(
    *,
    boundary: object,
    proposed_id: object,
    existing_ids: object,
) -> MintDecision:
    """May this proposed run_id be minted at this boundary?

    ``boundary``, ``proposed_id``, and ``existing_ids`` are required.
    A missing registry (``None``) is UNKNOWN, not empty. Unknown
    boundary names and malformed ids fail closed — UNKNOWN is not
    FALSE and is not admitted.

    A sealed send/ready name is a known refusal (``sealed_effect``).
    An arm/pack/model proposer is a known refusal
    (``untrusted_boundary``). A collision against the registry is
    ``id_collision``.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    boundary_name = _require_name(boundary, what="boundary")
    proposed = _require_name(proposed_id, what="proposed_id")
    registry = _require_registry(existing_ids)

    if _is_sealed(boundary_name) or _is_sealed(proposed):
        return MintDecision(
            allowed=False,
            reason="sealed_effect",
            boundary=boundary_name,
            proposed_id=proposed,
        )

    if boundary_name in UNTRUSTED_BOUNDARIES:
        return MintDecision(
            allowed=False,
            reason="untrusted_boundary",
            boundary=boundary_name,
            proposed_id=proposed,
        )

    if boundary_name not in BOUNDARIES:
        raise FailClosedError(
            f"unknown mint boundary is not a refusal and not a grant: "
            f"{boundary_name!r}")

    if not RUN_ID_RE.match(proposed):
        raise FailClosedError(
            f"proposed_id not minted at the boundary: {proposed!r}")

    if proposed in registry:
        return MintDecision(
            allowed=False,
            reason="id_collision",
            boundary=boundary_name,
            proposed_id=proposed,
        )

    return MintDecision(
        allowed=True,
        reason=None,
        boundary=boundary_name,
        proposed_id=proposed,
    )
