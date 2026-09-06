"""Arbiter claim — one assertion from one body, with vantage and scope.

A claim is not a fact. This module is the vocabulary for that distinction.
It does not write a ledger, it does not bind an address, and it does not
grant a send.

Rules locked here (each has a second record in the tests):

  * Default scope is ``this_host_only``.
  * ``system_wide`` is refused unless evidence names two distinct node_ids.
  * UNKNOWN is not FALSE.
  * A proposal is not execution.
  * An agent-reported claim is not independently verified.
  * Timeout does not prove concurrent writing.
  * Missing LAN ports do not prove loopback APIs are absent.
  * Disk absence on this host is ``body_not_on_this_host``, not
    ``body_missing``.
  * Identity contradiction (claimed node vs observed address) fails closed.
  * Ready is not authorized. ``grants_send`` is structurally False.

Not wired into the run store (that file is owned by an open change).

Kernel purity: dataclasses + typing + re. No clock, no I/O, no json.
The caller supplies every field; this module only classifies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Sequence

from .errors import FailClosedError
from .events import is_forbidden_effect_name

SCOPES = frozenset({"this_host_only", "system_wide"})
VANTAGES = frozenset({"this_host_only", "loopback", "lan", "remote"})
CLAIM_TYPES = frozenset({
    "measurement",
    "inference",
    "proposal",
    "agent_reported",
})
ABSENCE_KINDS = frozenset({"disk_this_host", "lan_ports"})

# Closed refusal / verdict vocabulary. Widen only with a test.
ABSENCE_VERDICTS = frozenset({"body_not_on_this_host", "UNKNOWN"})
IDENTITY_VERDICTS = frozenset({"consistent", "UNKNOWN"})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})

_NODE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_IPV4_RE = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")

# The unspecified address is not a vantage. Binding it is adapter work
# and is out of scope here; naming it as asserted_ip is already a refuse.
_UNSPECIFIED_IP = "0.0.0.0"


def grants_send() -> bool:
    """A typed claim never authorizes a send. Structurally False."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready is not a rename of authorized."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A proposal is not an execution."""
    return False


def agent_reported_is_verified() -> bool:
    """Structurally False. Agent-reported is one record, not a pair."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is not evidence of a writer."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A claim is not filesystem immutability."""
    return False


def halt_blocks_claim() -> bool:
    """Structurally False. HALT stops STARTS, not claim classification."""
    return False


def _refuse_sealed(value: str, *, what: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if is_forbidden_effect_name(value) or value.strip().lower() in _SEALED:
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r}")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"{what} names a sealed send/ready alias: {value!r}")


def _require_token(value: object, *, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} required: {value!r}")
    if isinstance(value, bool):  # pragma: no cover — bool is not str
        raise FailClosedError(f"{what} must be a name, not bool")
    text = value.strip()
    _refuse_sealed(text, what=what)
    return text


def require_node_id(value: object, *, what: str = "node_id") -> str:
    """Non-empty token. Bool / int / sealed send names fail closed."""
    text = _require_token(value, what=what)
    if not _NODE_ID_RE.match(text):
        raise FailClosedError(f"{what} malformed: {value!r}")
    return text


def require_ipv4(value: object, *, what: str = "asserted_ip") -> str:
    """Dotted IPv4. Bool, empty, unspecified, and sealed names fail closed."""
    text = _require_token(value, what=what)
    match = _IPV4_RE.match(text)
    if match is None:
        raise FailClosedError(f"{what} must be dotted IPv4: {value!r}")
    for part in match.groups():
        if len(part) > 1 and part.startswith("0"):
            raise FailClosedError(f"{what} octet leading zero: {value!r}")
        n = int(part)
        if n > 255:
            raise FailClosedError(f"{what} octet out of range: {value!r}")
    if text == _UNSPECIFIED_IP:
        raise FailClosedError(
            f"{what} refuses the unspecified address {text!r}")
    return text


def require_exact_int(value: object, *, what: str) -> int:
    """Exact int. ``True`` / ``1.0`` / ``\"1\"`` are not integers."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise FailClosedError(f"{what} must be exact int: {value!r}")
    return value


def _require_choice(value: object, allowed: frozenset[str], *, what: str) -> str:
    text = _require_token(value, what=what)
    if text not in allowed:
        raise FailClosedError(f"unknown {what}: {value!r}")
    return text


def _require_string_tuple(value: object, *, what: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        raise FailClosedError(f"{what} must be a sequence of names: {value!r}")
    if not isinstance(value, Sequence):
        raise FailClosedError(f"{what} must be a sequence of names: {value!r}")
    out: list[str] = []
    for item in value:
        out.append(_require_token(item, what=what))
    return tuple(out)


def require_two_node_ids(ids: object, *, what: str = "peer_node_ids") -> tuple[str, ...]:
    """Two or more distinct node_ids. One body cannot go system_wide."""
    cleaned = tuple(require_node_id(i, what=what) for i in _require_string_tuple(ids, what=what))
    if len(set(cleaned)) < 2:
        raise FailClosedError(
            f"{what} needs two distinct node_ids for system_wide: {ids!r}")
    return cleaned


def require_alternatives(value: object) -> tuple[str, ...]:
    """Inference requires at least two distinct alternative explanations.

    One explanation is not an alternative. UNKNOWN is not FALSE, so a
    single story cannot close the question.
    """
    cleaned = _require_string_tuple(value, what="alternative_explanations")
    if len(set(cleaned)) < 2:
        raise FailClosedError(
            "inference needs two distinct alternative_explanations; "
            "one story is not an alternative")
    return cleaned


def classify_absence(kind: object) -> str:
    """Name what a missing body or missing LAN ports actually means.

    ``disk_this_host`` → ``body_not_on_this_host`` (not ``body_missing``).
    ``lan_ports`` → ``UNKNOWN`` (not ``loopback_absent``).
    Unknown kinds fail closed — they are not treated as FALSE.
    """
    text = _require_choice(kind, ABSENCE_KINDS, what="absence_kind")
    if text == "disk_this_host":
        return "body_not_on_this_host"
    return "UNKNOWN"


def classify_identity(
    *,
    claimed_node_id: object,
    asserted_ip: object,
    observed_ip: object,
) -> str:
    """Compare a claimed address to an observed one.

    Missing ``observed_ip`` is UNKNOWN, not FALSE, not a contradiction.
    A mismatch is identity_contradiction and fails closed.
    """
    require_node_id(claimed_node_id, what="claimed_node_id")
    asserted = require_ipv4(asserted_ip, what="asserted_ip")
    if observed_ip is None:
        return "UNKNOWN"
    observed = require_ipv4(observed_ip, what="observed_ip")
    if observed != asserted:
        raise FailClosedError(
            "identity_contradiction: asserted_ip does not match observed_ip")
    return "consistent"


def is_execution(claim_type: object) -> bool:
    """No claim type in this vocabulary is an execution.

    ``proposal`` is the named reminder. ``measurement`` / ``inference`` /
    ``agent_reported`` are also not execution. Sealed send names refuse.
    """
    _require_choice(claim_type, CLAIM_TYPES, what="claim_type")
    return False


def is_independently_verified(claim_type: object) -> bool:
    """A single typed claim is never a second witness."""
    _require_choice(claim_type, CLAIM_TYPES, what="claim_type")
    return False


@dataclass(frozen=True)
class ArbiterClaim:
    """One assertion. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``scope`` and ``grants_send``
    are both recorded, and the constructor refuses ``grants_send=True``.
    """

    node_id: str
    asserted_ip: str
    vantage: str
    scope: str
    claim_type: str
    evidence: tuple[str, ...]
    alternative_explanations: tuple[str, ...]
    peer_node_ids: tuple[str, ...]
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "ArbiterClaim cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a claim is not a send")
        object.__setattr__(self, "node_id", require_node_id(self.node_id))
        object.__setattr__(
            self, "asserted_ip", require_ipv4(self.asserted_ip))
        object.__setattr__(
            self, "vantage", _require_choice(self.vantage, VANTAGES, what="vantage"))
        object.__setattr__(
            self, "scope", _require_choice(self.scope, SCOPES, what="scope"))
        object.__setattr__(
            self, "claim_type",
            _require_choice(self.claim_type, CLAIM_TYPES, what="claim_type"),
        )
        evidence = _require_string_tuple(self.evidence, what="evidence")
        if not evidence:
            raise FailClosedError(
                "evidence required — a claim without a second record is "
                "self-confirming")
        object.__setattr__(self, "evidence", evidence)
        if self.claim_type == "inference":
            alts = require_alternatives(self.alternative_explanations)
        else:
            alts = _require_string_tuple(
                self.alternative_explanations, what="alternative_explanations")
        object.__setattr__(self, "alternative_explanations", alts)
        if self.scope == "system_wide":
            peers = require_two_node_ids(self.peer_node_ids)
            if self.node_id not in peers:
                raise FailClosedError(
                    "system_wide peer_node_ids must include this node_id")
            object.__setattr__(self, "peer_node_ids", peers)
        else:
            if self.peer_node_ids:
                raise FailClosedError(
                    "this_host_only cannot carry peer_node_ids — that would "
                    "look like a silent promotion")
            object.__setattr__(self, "peer_node_ids", ())


def mint_claim(
    *,
    node_id: object,
    asserted_ip: object,
    claim_type: object,
    evidence: object,
    vantage: object = "this_host_only",
    scope: object = "this_host_only",
    alternative_explanations: object = (),
    peer_node_ids: object = (),
    observed_ip: object = None,
) -> ArbiterClaim:
    """Mint one claim. Default scope is this_host_only.

    ``observed_ip`` is the identity second record. None is UNKNOWN and
    does not block a this_host_only mint. A mismatch fails closed.

    Signature is sealed: no ``resend``, no ``send_authorized``.
    Tests lock the parameter list; the kernel does not import inspect.
    """
    classify_identity(
        claimed_node_id=node_id,
        asserted_ip=asserted_ip,
        observed_ip=observed_ip,
    )
    return ArbiterClaim(
        node_id=require_node_id(node_id),
        asserted_ip=require_ipv4(asserted_ip),
        vantage=_require_choice(vantage, VANTAGES, what="vantage"),
        scope=_require_choice(scope, SCOPES, what="scope"),
        claim_type=_require_choice(claim_type, CLAIM_TYPES, what="claim_type"),
        evidence=_require_string_tuple(evidence, what="evidence"),
        alternative_explanations=_require_string_tuple(
            alternative_explanations, what="alternative_explanations"),
        peer_node_ids=_require_string_tuple(peer_node_ids, what="peer_node_ids"),
        grants_send=False,
    )


def second_witness_pair(
    first: ArbiterClaim,
    second: ArbiterClaim,
    *,
    subject: object,
) -> bool:
    """Two claims about the same subject from two node_ids.

    A pair is not a send grant. Two ``agent_reported`` records are still
    not independently verified — they are two agent reports.
    """
    if not isinstance(first, ArbiterClaim) or not isinstance(second, ArbiterClaim):
        raise FailClosedError("second_witness_pair needs two ArbiterClaim values")
    token = _require_token(subject, what="subject")
    if first.node_id == second.node_id:
        raise FailClosedError(
            "second witness must be a different node_id — one body cannot pair")
    if token not in first.evidence or token not in second.evidence:
        raise FailClosedError(
            "both claims must cite the same subject in evidence")
    if first.claim_type == "agent_reported" and second.claim_type == "agent_reported":
        return False
    return True
