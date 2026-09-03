"""Architecture-contract bind — kernel-pure admission.

A bind maps a named architecture contract onto a closed surface.
It is a classification, not an export, not a send, and not a
mutation of the contract text.

Closed contract vocabulary (widen only with a test):

  task_envelope, typed_event, run_store, dedup, receipt,
  halt, otel_map, token_budget, worktree_inventory

Closed surfaces: kernel, adapter, test, doc.

``observe`` is admitted for a known vocabulary so inventory can
continue while the owner is absent. ``bind`` is admitted for a
known contract and a known surface. ``mutate`` is never admitted.

A sealed send/ready name is never a contract and never a surface.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as ``sealed_effect``.

Unknown contract, surface, or intent fail closed — UNKNOWN is
not FALSE and is not admitted as a bind.

HALT stops STARTS. This module has no halt parameter: classifying
a contract is not a run start.

Not wired into the run store (that file is owned by an open change).
Not a second copy of otel_map, token_ceiling, or census_class.

Admitting a bind is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
CONTRACTS = frozenset({
    "task_envelope",
    "typed_event",
    "run_store",
    "dedup",
    "receipt",
    "halt",
    "otel_map",
    "token_budget",
    "worktree_inventory",
})
SURFACES = frozenset({"kernel", "adapter", "test", "doc"})
INTENTS = frozenset({"bind", "observe", "mutate"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "mutate_forbidden",
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
    """A bind never authorizes a send. Structurally False."""
    return False


def halt_blocks_bind() -> bool:
    """Structurally False. HALT stops STARTS, not a contract bind."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A bind is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def mutates_contract() -> bool:
    """Structurally False. Binding does not rewrite the contract."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a bind is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def copies_canonical() -> bool:
    """Structurally False. A bind cites a name; it does not embed text."""
    return False


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent writing."""
    return "UNKNOWN"


def _fold(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name) or is_sealed_tool_name(name):
        return True
    return _fold(name) in {_fold(s) for s in _SEALED}


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


def _require_member(value: object, *, what: str, allowed: frozenset[str]) -> str:
    name = _require_name(value, what=what)
    if name not in allowed:
        raise FailClosedError(
            f"unknown {what} is not a refusal and not a grant: {name!r}")
    return name


@dataclass(frozen=True)
class BindDecision:
    """The bind-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    contract: str
    surface: str
    intended: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "BindDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a bind is not a send")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        object.__setattr__(
            self, "contract", _require_name(self.contract, what="contract"))
        object.__setattr__(
            self, "surface", _require_name(self.surface, what="surface"))
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed bind must not carry a reason: {self.reason!r}")
            if self.intended == "mutate":
                raise FailClosedError(
                    "BindDecision cannot allow mutate")
            if self.intended not in ("bind", "observe"):
                raise FailClosedError(
                    f"BindDecision cannot allow intended={self.intended!r}")
            if self.contract not in CONTRACTS:
                raise FailClosedError(
                    "allowed bind requires a known contract")
            if self.surface not in SURFACES:
                raise FailClosedError(
                    "allowed bind requires a known surface")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.contract) or _is_sealed(self.surface):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "BindDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def bind_arch(
    *,
    contract: object,
    surface: object,
    intended: object,
    timed_out: object = False,
) -> BindDecision:
    """May this architecture contract be bound or observed?

    ``contract``, ``surface``, and ``intended`` are required names.
    Unknown names fail closed — UNKNOWN is not FALSE and is not
    admitted as a bind.

    ``timed_out`` must be an exact bool. True is recorded on the
    decision and classifies as UNKNOWN via ``classify_timeout``.
    It does not refuse an otherwise valid observe or bind, and it
    does not prove concurrent writing.

    ``mutate`` is always refused.

    Signature is sealed: no ``resend``, no ``send_authorized``,
    no ``halt``. Tests lock the parameter list; the kernel does
    not import inspect.
    """
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")

    contract_name = _require_name(contract, what="contract")
    surface_name = _require_name(surface, what="surface")
    intent = _require_member(intended, what="intended", allowed=INTENTS)

    if _is_sealed(contract_name) or _is_sealed(surface_name):
        return BindDecision(
            allowed=False,
            reason="sealed_effect",
            contract=contract_name,
            surface=surface_name,
            intended=intent,
            timed_out=timed_out,
        )

    _require_member(contract_name, what="contract", allowed=CONTRACTS)
    _require_member(surface_name, what="surface", allowed=SURFACES)

    if intent == "mutate":
        return BindDecision(
            allowed=False,
            reason="mutate_forbidden",
            contract=contract_name,
            surface=surface_name,
            intended=intent,
            timed_out=timed_out,
        )

    return BindDecision(
        allowed=True,
        reason=None,
        contract=contract_name,
        surface=surface_name,
        intended=intent,
        timed_out=timed_out,
    )
