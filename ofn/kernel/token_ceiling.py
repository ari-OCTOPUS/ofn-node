"""Both token ceilings must pass. Neither grants a send.

Two independent questions:

  * per-run  — ``TaskEnvelope.budget_tokens`` (0 = no spend authorized)
  * node     — ``NodeQuota.check`` (tenant share + node week)

A caller that only checks one of them can still blow the other. This
module is the single place that asks both. ``Decision.allowed`` here
means "this spend fits the ceilings". It is not ``send_authorized``,
not ``quote_sent``, and not a campaign-envelope promotion.

Kernel purity: no I/O, no clock. Time and the quota ledger arrive as
arguments.
"""

from __future__ import annotations

from .domain import Decision, RiskTier, TenantId
from .envelope import TaskEnvelope
from .errors import FailClosedError
from .quota import NodeQuota

# Names this module refuses to grant. Presence in a Decision.reason or
# rule would mean the ceiling was smuggled into a send authorization.
SEND_STATES = frozenset({"send_authorized", "quote_sent"})


def per_run_fits(budget_tokens: int, already_consumed: int, request: int) -> bool:
    """The envelope rule, without needing the envelope object.

    Same semantics as ``TaskEnvelope.may_consume_tokens``: 0 budget
    authorizes only a 0 request; negatives fail closed.
    """
    for name, value in (("budget_tokens", budget_tokens),
                        ("already_consumed", already_consumed),
                        ("request", request)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise FailClosedError(f"{name} must be a non-negative int: {value!r}")
    if budget_tokens == 0:
        return request == 0
    return already_consumed + request <= budget_tokens


def tokens_from_payload(payload) -> int:
    """BUDGET_DEBIT payload → token request. Missing key is 0 (no-op).
    A present non-int fails closed — unknown is not zero."""
    if payload is None:
        return 0
    if not isinstance(payload, dict):
        raise FailClosedError(f"BUDGET_DEBIT payload must be a mapping: {payload!r}")
    if "tokens" not in payload:
        return 0
    value = payload["tokens"]
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise FailClosedError(
            f"BUDGET_DEBIT tokens must be a non-negative int: {value!r}")
    return value


def admit_token_spend(
    envelope: TaskEnvelope,
    quota: NodeQuota,
    tenant: TenantId | str,
    *,
    already_consumed: int,
    request: int,
    now_epoch_s: int,
) -> Decision:
    """Admit one token spend against both ceilings.

    Order is deliberate: the per-run cap is cheaper to evaluate and is
    the one an arm can lie about if it only talks to the node quota.
    Node refusal is returned as the quota's own Decision so the rule
    name stays ``quota:*``.
    """
    if not envelope.may_consume_tokens(already_consumed, request):
        return Decision(
            False, RiskTier.RED,
            f"per-run token ceiling: {already_consumed} + {request} "
            f"> {envelope.budget_tokens} (0 budget authorizes no spend)",
            rule="token:per-run-ceiling",
        )
    node = quota.check(tenant, request, now_epoch_s)
    if not node.allowed:
        return node
    return Decision(
        True, RiskTier.GREEN,
        "within per-run and node token ceilings",
        rule="token:both-ceilings",
        checks=tuple(node.checks) + ("per-run-ceiling",),
    )


def grants_send(decision: Decision) -> bool:
    """A token admit is never a send authorization.

    Structurally False. If a Decision ever carries a send-state name
    in ``rule`` or ``reason``, that is a defect — fail closed rather
    than treat it as granted.
    """
    blob = f"{decision.rule} {decision.reason}"
    if any(name in blob for name in SEND_STATES):
        raise FailClosedError(
            "token ceiling Decision mentioned a send state — "
            "this module does not grant send_authorized")
    return False
