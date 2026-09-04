"""Lineage class — kernel-pure TaskEnvelope parent/child admission.

``create_envelope`` (envelope.py) mints a run_id. This module is the
third witness: may a proposed root, a successor that names a prior
node, or an observe of an already-recorded node be classified?

``mint`` is a START (a root). HALT refuses it. ``succeed`` and
``observe`` are not STARTS — HALT does not block them. This module
does not mint a run_id and does not write a ledger.

A sealed send/ready name is never a node_id and never a parent_id.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as ``sealed_effect``.

A missing prior set is UNKNOWN, not empty. An empty prior set is
a supplied empty witness. A supplied parent absent from prior is
``orphan`` — a known refusal, not FALSE. A missing parent on
``succeed`` is UNKNOWN (``missing_parent``), not FALSE.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not mint a root.

Distinct from hash_chain (byte digest), event_id (evt- uniqueness),
envelope_class (mint/validate/replay of one envelope), and
store_class (append/replay/reopen). Not wired into the run store.

Admitting a successor or an observe is not ``send_authorized``,
``quote_sent``, or ``campaign_envelope_ready``. Ready is not
authorized.

Kernel purity: typing + dataclasses + re (via envelope.RUN_ID_RE).
No json, no clock, no I/O. This file must not name a business
or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Optional

from .envelope import RUN_ID_RE
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
INTENTS = frozenset({"mint", "succeed", "observe"})
ROLES = frozenset({"root", "successor", "orphan", "unknown"})
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
ACTIVITIES = frozenset({"idle", "concurrent", "unknown"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "halt_start",
    "orphan_parent",
    "self_parent",
    "missing_parent",
    "unknown_prior",
    "unknown_activity",
    "suspected_concurrent",
    "malformed_id",
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
    """A lineage class never authorizes a send. Structurally False."""
    return False


def halt_blocks_succeed() -> bool:
    """Structurally False. HALT stops STARTS, not succeed/observe."""
    return False


def mints_run_id() -> bool:
    """Structurally False. The factory in envelope.py mints. This classifies."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A lineage verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a lineage edge is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def missing_prior_is_empty() -> bool:
    """Structurally False. A missing prior set is UNKNOWN, not empty."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent writing."""
    return "UNKNOWN"


def _fold(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
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


def classify_status(*, activity: str, timed_out: bool) -> str:
    """Derive the lineage-row status. Timeout outranks activity.

    A timeout is UNKNOWN even when activity says concurrent.
    That is the load-bearing rule: timeout does not prove a race.
    """
    if timed_out:
        return "UNKNOWN"
    if activity == "unknown":
        return "UNKNOWN"
    if activity == "concurrent":
        return "SUSPECTED"
    if activity == "idle":
        return "VERIFIED"
    raise FailClosedError(
        f"unknown activity is not a refusal and not a grant: {activity!r}")


def _coerce_prior(prior: object) -> Optional[FrozenSet[str]]:
    """None is UNKNOWN (not empty). A supplied iterable is a witness.

    Strings/bytes are refused — a single name is not a prior set.
    """
    if prior is None:
        return None
    if isinstance(prior, (str, bytes, bytearray, bool)):
        raise FailClosedError(
            f"prior must be a set of names or None: {prior!r}")
    if not isinstance(prior, (frozenset, set, tuple, list)):
        raise FailClosedError(
            f"prior must be a set of names or None: {prior!r}")
    names: set[str] = set()
    for item in prior:
        names.add(_require_name(item, what="prior_id"))
    return frozenset(names)


@dataclass(frozen=True)
class LineageDecision:
    """The lineage-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    status: str
    intended: str
    role: str
    node_id: str
    parent_id: Optional[str]
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "LineageDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a lineage class is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown lineage status is not a refusal and not a grant: "
                f"{self.status!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if self.role not in ROLES:
            raise FailClosedError(
                f"unknown or missing role: {self.role!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        object.__setattr__(self, "node_id", _require_name(self.node_id, what="node_id"))
        if self.parent_id is not None:
            object.__setattr__(
                self, "parent_id",
                _require_name(self.parent_id, what="parent_id"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed lineage must not carry a reason: {self.reason!r}")
            if self.intended == "mint" and self.status != "VERIFIED":
                raise FailClosedError(
                    "LineageDecision cannot allow a mint unless VERIFIED")
            if self.intended == "succeed" and self.role != "successor":
                raise FailClosedError(
                    "LineageDecision cannot allow succeed unless successor")
            if self.role == "orphan":
                raise FailClosedError(
                    "LineageDecision cannot allow an orphan")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if (
            _is_sealed(self.node_id)
            or _is_sealed(self.parent_id)
            or _is_sealed(self.intended)
            or _is_sealed(self.role)
        ):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "LineageDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_lineage(
    *,
    intended: object,
    node_id: object,
    parent_id: object = None,
    prior: object = None,
    activity: object = "idle",
    halted: object = False,
    timed_out: object = False,
) -> LineageDecision:
    """May this node be a root, a successor, or an observe?

    ``intended`` and ``node_id`` are required names. Unknown names
    fail closed — UNKNOWN is not FALSE and is not admitted as idle.

    ``parent_id`` is required for ``succeed``. Missing is UNKNOWN
    (``missing_parent``), not FALSE. ``mint`` refuses a supplied
    parent — a root has no parent (shape error).

    ``prior`` is optional. None is UNKNOWN (not empty). A supplied
    empty set is a witness that no prior node exists. A supplied
    parent absent from prior is ``orphan_parent``.

    ``halted`` and ``timed_out`` must be exact bools. HALT refuses
    ``mint`` only. Timeout forces status UNKNOWN and refuses mint
    and succeed; it does not classify the row as SUSPECTED.

    Signature is sealed: no ``resend``, no ``send_authorized``.
    Tests lock the parameter list; the kernel does not import inspect.
    """
    raw_intent = _require_name(intended, what="intended")
    raw_node = _require_name(node_id, what="node_id")
    activity_name = _require_member(
        activity, what="activity", allowed=ACTIVITIES)
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")
    if parent_id is not None:
        raw_parent: Optional[str] = _require_name(parent_id, what="parent_id")
    else:
        raw_parent = None
    prior_set = _coerce_prior(prior)

    if (
        _is_sealed(raw_intent)
        or _is_sealed(raw_node)
        or _is_sealed(raw_parent)
    ):
        return LineageDecision(
            allowed=False,
            reason="sealed_effect",
            status=classify_status(activity=activity_name, timed_out=timed_out),
            intended=raw_intent if raw_intent in INTENTS else "observe",
            role="unknown",
            node_id=raw_node,
            parent_id=raw_parent,
            timed_out=timed_out,
        )

    intent = _require_member(raw_intent, what="intended", allowed=INTENTS)
    status = classify_status(activity=activity_name, timed_out=timed_out)

    if RUN_ID_RE.match(raw_node) is None:
        return LineageDecision(
            allowed=False,
            reason="malformed_id",
            status=status,
            intended=intent,
            role="unknown",
            node_id=raw_node,
            parent_id=raw_parent,
            timed_out=timed_out,
        )
    if raw_parent is not None and RUN_ID_RE.match(raw_parent) is None:
        return LineageDecision(
            allowed=False,
            reason="malformed_id",
            status=status,
            intended=intent,
            role="unknown",
            node_id=raw_node,
            parent_id=raw_parent,
            timed_out=timed_out,
        )

    if intent == "mint":
        if raw_parent is not None:
            raise FailClosedError(
                "mint is a root — a supplied parent is a shape error, "
                "not a successor")
        if halted:
            return LineageDecision(
                allowed=False,
                reason="halt_start",
                status=status,
                intended=intent,
                role="root",
                node_id=raw_node,
                parent_id=None,
                timed_out=timed_out,
            )
        if status == "UNKNOWN":
            return LineageDecision(
                allowed=False,
                reason="unknown_activity",
                status=status,
                intended=intent,
                role="root",
                node_id=raw_node,
                parent_id=None,
                timed_out=timed_out,
            )
        if status == "SUSPECTED":
            return LineageDecision(
                allowed=False,
                reason="suspected_concurrent",
                status=status,
                intended=intent,
                role="root",
                node_id=raw_node,
                parent_id=None,
                timed_out=timed_out,
            )
        return LineageDecision(
            allowed=True,
            reason=None,
            status=status,
            intended=intent,
            role="root",
            node_id=raw_node,
            parent_id=None,
            timed_out=timed_out,
        )

    if intent == "succeed":
        if raw_parent is None:
            return LineageDecision(
                allowed=False,
                reason="missing_parent",
                status=status,
                intended=intent,
                role="unknown",
                node_id=raw_node,
                parent_id=None,
                timed_out=timed_out,
            )
        if raw_parent == raw_node:
            return LineageDecision(
                allowed=False,
                reason="self_parent",
                status=status,
                intended=intent,
                role="unknown",
                node_id=raw_node,
                parent_id=raw_parent,
                timed_out=timed_out,
            )
        if prior_set is None:
            return LineageDecision(
                allowed=False,
                reason="unknown_prior",
                status=status,
                intended=intent,
                role="unknown",
                node_id=raw_node,
                parent_id=raw_parent,
                timed_out=timed_out,
            )
        if raw_parent not in prior_set:
            return LineageDecision(
                allowed=False,
                reason="orphan_parent",
                status=status,
                intended=intent,
                role="orphan",
                node_id=raw_node,
                parent_id=raw_parent,
                timed_out=timed_out,
            )
        if status == "UNKNOWN":
            return LineageDecision(
                allowed=False,
                reason="unknown_activity",
                status=status,
                intended=intent,
                role="successor",
                node_id=raw_node,
                parent_id=raw_parent,
                timed_out=timed_out,
            )
        if status == "SUSPECTED":
            return LineageDecision(
                allowed=False,
                reason="suspected_concurrent",
                status=status,
                intended=intent,
                role="successor",
                node_id=raw_node,
                parent_id=raw_parent,
                timed_out=timed_out,
            )
        return LineageDecision(
            allowed=True,
            reason=None,
            status=status,
            intended=intent,
            role="successor",
            node_id=raw_node,
            parent_id=raw_parent,
            timed_out=timed_out,
        )

    # observe — read-side recovery. HALT does not block. Timeout is
    # UNKNOWN and still admitted. A missing prior does not invent a
    # parent and does not claim root or successor.
    return LineageDecision(
        allowed=True,
        reason=None,
        status=status,
        intended=intent,
        role="unknown",
        node_id=raw_node,
        parent_id=raw_parent,
        timed_out=timed_out,
    )
