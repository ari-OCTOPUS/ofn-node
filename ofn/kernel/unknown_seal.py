"""Unknown seal — UNKNOWN is not FALSE.

A missing observation, a timeout, an absent document, a missing LAN
port, or an agent-only report is UNKNOWN. Coercing it to False would
open a gate (absence-as-permission). Coercing it to True would mint
a fact. Both are FailClosedError.

Closed evidence kinds and their forced verdicts:

  timeout             → UNKNOWN  (does not prove concurrent writing)
  missing_port        → UNKNOWN  (inference; not 'loopback API absent')
  disk_absence        → UNKNOWN  (body_not_on_this_host, not body_missing)
  absent_doc          → UNKNOWN  (document missing is not a negative)
  unparsed            → UNKNOWN  (not a verdict)
  agent_report_only   → UNKNOWN  (not independently verified)
  missing_second_node → UNKNOWN  (cannot promote to system_wide)
  direct_observation  → TRUE or FALSE only, never UNKNOWN-as-bool

TRUE and FALSE require ``direct_observation`` plus an explicit
non-bool verdict name. A Python bool is not an observation.

A sealed send/ready name is never a kind, never a witness, never a
payload key or string value. ``campaign_envelope_ready`` is
structurally distinct from ``send_authorized``; both are refused.

HALT stops STARTS. This seal has no halt parameter: classification
is collection-only and must still run so recovery does not need
the owner.

Not wired into the run store (that file is owned by an open change).

Classifying is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from .errors import FailClosedError
from .events import is_forbidden_effect_name, payload_forbidden_effect

VERDICTS = frozenset({"TRUE", "FALSE", "UNKNOWN"})

# Closed evidence vocabulary. Widen only with a test.
EVIDENCE_KINDS = frozenset({
    "timeout",
    "missing_port",
    "disk_absence",
    "absent_doc",
    "unparsed",
    "agent_report_only",
    "missing_second_node",
    "direct_observation",
})

FORCED_UNKNOWN = frozenset({
    "timeout",
    "missing_port",
    "disk_absence",
    "absent_doc",
    "unparsed",
    "agent_report_only",
    "missing_second_node",
})

SCOPES = frozenset({"this_host_only", "system_wide"})

DISK_ABSENCE_LABEL = "body_not_on_this_host"
TIMEOUT_LABEL = "UNKNOWN"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A classification never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not collection."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_is_true() -> bool:
    """Structurally False. UNKNOWN is not TRUE."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout does not prove concurrent writing."""
    return False


def missing_port_proves_absent() -> bool:
    """Structurally False. A missing LAN port is not proof of absence."""
    return False


def disk_absence_is_body_missing() -> bool:
    """Structurally False. Disk absence here is body_not_on_this_host."""
    return False


def default_scope() -> str:
    """Claims default to this host. Promotion is a separate function."""
    return "this_host_only"


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


@dataclass(frozen=True)
class UnknownDecision:
    """One classification. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``verdict`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``. UNKNOWN cannot be stored as a Python bool.
    """

    verdict: str
    kind: str
    witness: str
    label: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "UnknownDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a classification is not a send")
        if self.verdict not in VERDICTS:
            raise FailClosedError(f"unknown verdict is not a bool: {self.verdict!r}")
        object.__setattr__(self, "kind", _require_name(self.kind, what="kind"))
        object.__setattr__(self, "witness", _require_name(self.witness, what="witness"))
        object.__setattr__(self, "label", _require_name(self.label, what="label"))
        if _is_sealed(self.kind) or _is_sealed(self.witness) or _is_sealed(self.label):
            raise FailClosedError(
                "UnknownDecision cannot carry a sealed send/ready name")
        if self.kind in FORCED_UNKNOWN and self.verdict != "UNKNOWN":
            raise FailClosedError(
                f"{self.kind} must stay UNKNOWN, got {self.verdict!r}")
        if self.kind == "direct_observation" and self.verdict == "UNKNOWN":
            raise FailClosedError(
                "direct_observation cannot record UNKNOWN — that would "
                "launder a missing witness as a measured fact")


def as_bool(verdict: object) -> bool:
    """Coerce a named verdict. UNKNOWN and foreign names fail closed.

    A Python bool is refused: passing True/False here would hide that
    the caller never classified.
    """
    if isinstance(verdict, bool) or not isinstance(verdict, str):
        raise FailClosedError(f"verdict must be a name, not {verdict!r}")
    name = verdict.strip()
    if name == "TRUE":
        return True
    if name == "FALSE":
        return False
    if name == "UNKNOWN":
        raise FailClosedError("UNKNOWN is not FALSE and is not TRUE")
    raise FailClosedError(f"foreign verdict is not a bool: {name!r}")


def classify(
    *,
    kind: object,
    witness: object,
    observed: Optional[object] = None,
    payload: Optional[Mapping[str, object]] = None,
) -> UnknownDecision:
    """Classify one observation.

    ``kind`` and ``witness`` are required names. Unknown kinds fail
    closed — they are not classified as FALSE. A sealed send/ready
    name is a known refusal (FailClosedError), not an unknown.

    Forced-UNKNOWN kinds ignore ``observed``: a timeout cannot be
    argued into concurrent-write, a missing port cannot be argued
    into 'API absent'.

    ``direct_observation`` requires ``observed`` in {TRUE, FALSE}
    as a name. A Python bool is refused.

    ``payload`` is optional. When supplied it must be a mapping.
    A smuggled sealed name fails closed.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    kind_name = _require_name(kind, what="kind")
    witness_name = _require_name(witness, what="witness")

    if _is_sealed(kind_name) or _is_sealed(witness_name):
        raise FailClosedError(
            "sealed send/ready name is not a classification")

    if kind_name not in EVIDENCE_KINDS:
        raise FailClosedError(
            f"unknown evidence kind is not FALSE: {kind_name!r}")

    if payload is not None:
        if isinstance(payload, (str, bytes, bytearray)) or not isinstance(payload, Mapping):
            raise FailClosedError(f"payload must be a mapping: {payload!r}")
        smuggled = payload_forbidden_effect(payload)
        if smuggled is not None:
            raise FailClosedError(
                f"payload smuggles forbidden effect name {smuggled!r}")

    if kind_name in FORCED_UNKNOWN:
        if kind_name == "timeout":
            label = TIMEOUT_LABEL
        elif kind_name == "disk_absence":
            label = DISK_ABSENCE_LABEL
        elif kind_name == "missing_port":
            label = "inference"
        else:
            label = "UNKNOWN"
        return UnknownDecision(
            verdict="UNKNOWN",
            kind=kind_name,
            witness=witness_name,
            label=label,
        )

    # direct_observation
    if observed is None:
        raise FailClosedError(
            "direct_observation requires an explicit TRUE/FALSE name")
    observed_name = _require_name(observed, what="observed")
    if observed_name not in {"TRUE", "FALSE"}:
        raise FailClosedError(
            f"direct_observation observed must be TRUE or FALSE: {observed_name!r}")
    return UnknownDecision(
        verdict=observed_name,
        kind=kind_name,
        witness=witness_name,
        label="direct_observation",
    )


def promote_scope(node_ids: object) -> str:
    """system_wide only with evidence from two distinct node ids.

    One node, zero nodes, duplicates, bools, or a non-sequence fail
    closed. Missing a second node is UNKNOWN, not a silent stay on
    this_host_only and not a promotion. Does not grant send.
    """
    if isinstance(node_ids, (str, bytes, bytearray, bool)) or node_ids is None:
        raise FailClosedError(f"node_ids must be a sequence of names: {node_ids!r}")
    if not isinstance(node_ids, Sequence):
        raise FailClosedError(f"node_ids must be a sequence of names: {node_ids!r}")
    names: list[str] = []
    for item in node_ids:
        names.append(_require_name(item, what="node_id"))
    unique = frozenset(names)
    if len(unique) != 2 or len(names) != 2:
        raise FailClosedError(
            "system_wide requires evidence from exactly two distinct "
            f"node_ids; got {len(unique)} unique of {len(names)} — "
            "UNKNOWN is not a promotion")
    return "system_wide"
