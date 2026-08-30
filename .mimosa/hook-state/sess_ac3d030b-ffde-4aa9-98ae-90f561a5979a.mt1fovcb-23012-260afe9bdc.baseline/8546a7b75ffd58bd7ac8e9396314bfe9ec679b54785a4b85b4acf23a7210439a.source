"""The choke point. Exactly one function decides whether anything happens.

`admit()` is the only path from "a leg wants to do X" to "X is permitted".
If a second path ever appears, the guarantees in this package stop holding —
not gradually, but immediately, because every other module assumes this
function ran.

Order of checks is deliberate and not interchangeable:

  1. kill switch      — a halted organism yields; nothing else is evaluated
  2. quota            — spending is refused before risk is even computed, so a
                        RED action cannot consume budget while awaiting a human
  3. risk assessment  — derives the tier from facts, ratcheting only upward
  4. human sovereignty— GREEN proceeds; YELLOW and RED wait for a finger

Putting quota ahead of risk matters: the reverse order lets an action that
will sit in a queue for hours reserve budget it may never use.
"""

from __future__ import annotations

from typing import Sequence

from .domain import Action, Decision, PackSpec, RiskTier
from .quota import NodeQuota
from .risk import assess


def admit(
    action: Action,
    pack: PackSpec,
    quota: NodeQuota,
    *,
    now_epoch_s: int,
    killed: bool = False,
    closed_gates: Sequence[str] = (),
    units_used_this_week: int = 0,
) -> Decision:
    """Decide whether `action` may proceed, and under whose authority.

    Returns an *allowed* Decision even for YELLOW and RED — "allowed" here
    means "not refused by policy", not "execute now". Callers must consult
    `decision.needs_human` before acting; `admit` never executes anything and
    has no way to.
    """
    if action.tenant != pack.tenant:
        return Decision(
            False, RiskTier.RED,
            f"action is for tenant {action.tenant.value!r} but pack is "
            f"{pack.tenant.value!r}",
            rule="gate:tenant-mismatch",
        )

    # 1 ── kill switch. Yield, never resist.
    if killed:
        return Decision(False, RiskTier.RED, "kill switch engaged",
                        rule="gate:kill-switch")

    # 2 ── quota, before anything expensive is contemplated.
    if action.estimated_tokens > 0:
        q = quota.check(action.tenant, action.estimated_tokens, now_epoch_s)
        if not q.allowed:
            return q

    # 3 ── risk, derived from facts rather than asserted by the caller.
    ra = assess(
        action, pack,
        closed_gates=closed_gates,
        units_used_this_week=units_used_this_week,
    )

    # 4 ── who may authorise it.
    checks = ("tenant-match", "kill-switch", "quota", "risk")
    if ra.tier is RiskTier.GREEN:
        return Decision(True, RiskTier.GREEN,
                        "reversible, stays inside the node — runs unattended",
                        rule="gate:green-auto", checks=checks)
    if ra.tier is RiskTier.YELLOW:
        return Decision(True, RiskTier.YELLOW,
                        f"leaves the node — one approval required ({ra.why})",
                        rule="gate:yellow-approval", checks=checks)
    return Decision(True, RiskTier.RED,
                    f"irreversible or sensitive — two-step approval required ({ra.why})",
                    rule="gate:red-double", checks=checks)


def executable(decision: Decision, *, human_approved: bool = False,
               confirmed_twice: bool = False) -> Decision:
    """Second half of the choke point: may this decision run *now*?

    Split from `admit` on purpose. `admit` answers a policy question and can
    be asked speculatively; this answers an execution question and must be
    asked immediately before acting, because approval state decays.
    """
    if not decision.allowed:
        return decision
    if decision.tier is RiskTier.GREEN:
        return Decision(True, RiskTier.GREEN, "green: no approval needed",
                        rule="exec:green")
    if not human_approved:
        return Decision(False, decision.tier,
                        "human approval required and absent",
                        rule="exec:awaiting-approval")
    if decision.tier is RiskTier.RED and not confirmed_twice:
        return Decision(False, RiskTier.RED,
                        "red actions need a second, separate confirmation",
                        rule="exec:awaiting-second-confirm")
    return Decision(True, decision.tier, "approved by owner", rule="exec:approved")
