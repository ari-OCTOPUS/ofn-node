"""Cut pin — kernel-pure pin that a RunStore window is closed.

An epoch that is ``open`` may be cut. A cut stops new appends to
that window. It is not a rewrite and it is not a truncate: history
stays; the window stops accepting.

This module is the second witness: given a *prior* state, may this
epoch be pinned cut?

A missing prior state is UNKNOWN, not open — UNKNOWN is not FALSE
and is not a grant. An already-cut window is a known refusal
(``already_cut``), not a rewrite. ``rewrite`` and ``truncate`` as
prior states are known refusals under their own names.

A sealed send/ready name is never an epoch and never a prior
state. ``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused.

HALT stops STARTS. This pin has no halt parameter: an in-flight
cut of an already-open window must still be classifiable so
recovery does not need the owner.

Not wired into the run store (that file is owned by another open
change).

Pinning a cut is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import RUN_ID_RE
from .epoch_class import EPOCH_ID_RE, REFUSED_STATES, classify_state
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Known refusals. Unknown names fail closed — they are not
# classified as FALSE.
REFUSAL_REASONS = frozenset({
    "already_cut",
    "rewrite",
    "truncate",
    "sealed_effect",
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
    """A cut pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_cut() -> bool:
    """Structurally False. HALT stops STARTS, not an in-flight cut."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not chattr +i."""
    return False


def unknown_prior_is_open() -> bool:
    """Structurally False. A missing prior is UNKNOWN, not open."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def cut_is_truncate() -> bool:
    """Structurally False. A cut keeps history; truncate would delete."""
    return False


def cut_is_rewrite() -> bool:
    """Structurally False. A cut does not rewrite prior rows."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Naming a cut is not an external effect."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. This module is not wired into the store."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later disarm/hold outranks a ready name."""
    return True


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


def _require_prior(prior_state: object) -> str:
    """A missing prior is UNKNOWN, not open."""
    if prior_state is None:
        raise FailClosedError(
            "prior_state is UNKNOWN, not open — refusing cut")
    return _require_name(prior_state, what="prior_state")


@dataclass(frozen=True)
class CutPin:
    """The cut-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    epoch_id: str
    prior_state: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "CutPin cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a cut pin is not a send")
        object.__setattr__(self, "epoch_id",
                           _require_name(self.epoch_id, what="epoch_id"))
        object.__setattr__(self, "prior_state",
                           _require_name(self.prior_state, what="prior_state"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed cut must not carry a reason: {self.reason!r}")
            if self.prior_state != "open":
                raise FailClosedError(
                    "CutPin cannot allow a cut from a non-open prior")
            if _is_sealed(self.epoch_id) or _is_sealed(self.prior_state):
                raise FailClosedError(
                    "CutPin cannot grant a sealed send/ready name")
            if not EPOCH_ID_RE.match(self.epoch_id):
                raise FailClosedError(
                    f"allowed cut must carry an epoch-shaped id: "
                    f"{self.epoch_id!r}")
            if RUN_ID_RE.match(self.epoch_id):
                raise FailClosedError(
                    "CutPin cannot admit a run_id as an epoch")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
            if _is_sealed(self.epoch_id) or _is_sealed(self.prior_state):
                if self.reason != "sealed_effect":
                    raise FailClosedError(
                        "CutPin cannot mis-label a sealed send/ready name")


def pin_cut(
    *,
    epoch_id: object,
    prior_state: object,
) -> CutPin:
    """May this open window be pinned cut?

    ``epoch_id`` and ``prior_state`` are required. A missing prior
    (``None``) is UNKNOWN, not open. Unknown priors and malformed
    ids fail closed — UNKNOWN is not FALSE and is not admitted.

    A sealed send/ready name is a known refusal (``sealed_effect``).
    An already-cut window is ``already_cut``. ``rewrite`` and
    ``truncate`` priors are known refusals under their own reason.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    epoch_name = _require_name(epoch_id, what="epoch_id")
    prior = _require_prior(prior_state)

    if _is_sealed(epoch_name) or _is_sealed(prior):
        return CutPin(
            allowed=False,
            reason="sealed_effect",
            epoch_id=epoch_name,
            prior_state=prior,
        )

    classified = classify_state(prior)
    if classified == "cut":
        return CutPin(
            allowed=False,
            reason="already_cut",
            epoch_id=epoch_name,
            prior_state="cut",
        )
    if classified in REFUSED_STATES:
        return CutPin(
            allowed=False,
            reason=classified,
            epoch_id=epoch_name,
            prior_state=classified,
        )

    if RUN_ID_RE.match(epoch_name):
        raise FailClosedError(
            f"run_id is not an epoch window: {epoch_name!r}")

    if not EPOCH_ID_RE.match(epoch_name):
        raise FailClosedError(
            f"epoch_id not shaped at the boundary: {epoch_name!r}")

    return CutPin(
        allowed=True,
        reason=None,
        epoch_id=epoch_name,
        prior_state="open",
    )
