"""Token quota: one ceiling for the node, shares for the legs, fail-closed.

The provider this is written against publishes no token allowance. It sells
tiers as multiples of a base plan and exposes consumption only as rolling
percentages in a dashboard. So the ceiling here is *derived*, and the module
is built around that uncertainty rather than pretending it away:

  * `estimated_capacity` starts as an extrapolation and is explicitly labelled
    as one.
  * `calibrate()` replaces it with observed reality as soon as reality is
    known. The utilisation fraction is then applied to the *real* number.
  * Until calibration, the fraction is the only safety margin there is.

The second design driver is invisible spend. An orchestrating provider bills
for tokens it consumed internally and does not echo back — in published
measurements roughly 60% of the total. A budget that counts only the visible
half under-reports by ~2.6×, which is exactly enough to blow a ceiling while
the dashboard still looks healthy. So: when the provider does not report its
orchestration cost, we multiply. Assuming the invisible cost is zero is the
one option guaranteed to be wrong.

Kernel purity: this module never reads a clock. `now_epoch_s` is a parameter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .domain import Decision, RiskTier, TenantId, TokenSpend
from .errors import FailClosedError, UnknownTenantError

WEEK_SECONDS = 7 * 24 * 60 * 60

# Ratio of total billed tokens to provider-visible tokens, from published
# measurements of an orchestrating provider (~54k orchestration vs ~35k
# visible in one observed session). Used only when the provider reports no
# orchestration figure of its own.
DEFAULT_ORCHESTRATION_MULTIPLIER = 2.6


def week_index(now_epoch_s: int) -> int:
    """Which 7-day bucket a timestamp falls in. Buckets are fixed-width from
    the epoch — no timezone, no DST, nothing that shifts under us."""
    if now_epoch_s < 0:
        raise FailClosedError("timestamp must not be negative")
    return now_epoch_s // WEEK_SECONDS


@dataclass
class QuotaLedger:
    """Mutable spend accounting for one week. Small, boring, and the only
    place token totals live."""

    week: int
    node_spent: int = 0
    per_tenant: dict[str, int] = field(default_factory=dict)
    calls: int = 0

    def add(self, tenant: str, effective: int) -> None:
        self.node_spent += effective
        self.per_tenant[tenant] = self.per_tenant.get(tenant, 0) + effective
        self.calls += 1


class NodeQuota:
    """The node's single token ceiling, split into per-leg shares.

    Two ceilings apply to every call and both are hard:
      1. the tenant's share of the week, and
      2. the node total.

    When the node total is exhausted every leg stops — not just the one that
    consumed most. A shared ceiling that only throttles the heaviest user
    lets a quiet leg get starved by a noisy one at the worst possible moment,
    and makes the failure mode depend on ordering.
    """

    def __init__(
        self,
        *,
        estimated_capacity_tokens: int,
        utilisation: float,
        shares: Mapping[str, float],
        orchestration_multiplier: float = DEFAULT_ORCHESTRATION_MULTIPLIER,
        capacity_is_estimate: bool = True,
    ) -> None:
        if estimated_capacity_tokens <= 0:
            raise FailClosedError("capacity must be positive")
        if not 0.0 < utilisation <= 1.0:
            raise FailClosedError("utilisation must be within (0, 1]")
        if orchestration_multiplier < 1.0:
            raise FailClosedError(
                "orchestration multiplier below 1.0 would under-count billed spend"
            )
        total = sum(shares.values())
        if total > 1.0 + 1e-9:
            raise FailClosedError(f"shares sum to {total:.3f}, exceeding 1.0")
        for name, share in shares.items():
            if not 0.0 <= share <= 1.0:
                raise FailClosedError(f"share for {name!r} outside 0..1")

        self._capacity = int(estimated_capacity_tokens)
        self._utilisation = float(utilisation)
        self._shares = dict(shares)
        self._multiplier = float(orchestration_multiplier)
        self.capacity_is_estimate = bool(capacity_is_estimate)
        self._ledgers: dict[int, QuotaLedger] = {}

    # ── ceilings ──────────────────────────────────────────────────────────
    @property
    def node_ceiling(self) -> int:
        return int(self._capacity * self._utilisation)

    def tenant_ceiling(self, tenant: TenantId | str) -> int:
        name = tenant.value if isinstance(tenant, TenantId) else tenant
        if name not in self._shares:
            raise UnknownTenantError(f"no quota share for tenant {name!r}")
        return int(self.node_ceiling * self._shares[name])

    # ── accounting ────────────────────────────────────────────────────────
    def effective_cost(self, spend: TokenSpend) -> int:
        """Billed tokens for one call.

        If the provider reported its orchestration cost, trust that number —
        it is measured. If it reported nothing, apply the multiplier: an
        unreported cost is unknown, not zero.
        """
        if spend.orchestration > 0:
            return spend.effective
        return int(round(spend.visible * self._multiplier))

    def ledger(self, now_epoch_s: int) -> QuotaLedger:
        w = week_index(now_epoch_s)
        led = self._ledgers.get(w)
        if led is None:
            led = QuotaLedger(week=w)
            self._ledgers[w] = led
        return led

    def spent(self, now_epoch_s: int, tenant: TenantId | str | None = None) -> int:
        led = self.ledger(now_epoch_s)
        if tenant is None:
            return led.node_spent
        name = tenant.value if isinstance(tenant, TenantId) else tenant
        return led.per_tenant.get(name, 0)

    def remaining(self, now_epoch_s: int, tenant: TenantId | str) -> int:
        """Headroom for a tenant: the smaller of its own and the node's."""
        name = tenant.value if isinstance(tenant, TenantId) else tenant
        own = self.tenant_ceiling(name) - self.spent(now_epoch_s, name)
        node = self.node_ceiling - self.spent(now_epoch_s)
        return max(0, min(own, node))

    # ── the gate ──────────────────────────────────────────────────────────
    def check(
        self,
        tenant: TenantId | str,
        estimated_visible_tokens: int,
        now_epoch_s: int,
    ) -> Decision:
        """Admission for one model call, judged on *billed* cost.

        The estimate passed in is visible tokens; it is inflated by the same
        multiplier before comparison, so admission and accounting agree.
        Checking against the visible figure would admit calls the ledger then
        records as over budget.
        """
        name = tenant.value if isinstance(tenant, TenantId) else tenant
        if name not in self._shares:
            return Decision(False, RiskTier.RED,
                            f"tenant {name!r} has no quota share", rule="quota:unknown-tenant")
        if estimated_visible_tokens < 0:
            return Decision(False, RiskTier.RED,
                            "negative token estimate", rule="quota:bad-input")

        projected = self.effective_cost(TokenSpend(visible=estimated_visible_tokens))
        led = self.ledger(now_epoch_s)
        checks: list[str] = []

        node_after = led.node_spent + projected
        if node_after > self.node_ceiling:
            return Decision(
                False, RiskTier.RED,
                f"node ceiling reached: {node_after} > {self.node_ceiling} "
                f"tokens this week — all legs stop, not just this one",
                rule="quota:node-ceiling", checks=tuple(checks),
            )
        checks.append("node-headroom")

        own_after = led.per_tenant.get(name, 0) + projected
        own_ceiling = self.tenant_ceiling(name)
        if own_after > own_ceiling:
            return Decision(
                False, RiskTier.RED,
                f"tenant share exhausted: {own_after} > {own_ceiling} tokens this week",
                rule="quota:tenant-share", checks=tuple(checks),
            )
        checks.append("tenant-headroom")

        return Decision(True, RiskTier.GREEN, "within quota",
                        rule="quota:ok", checks=tuple(checks))

    def record(
        self,
        tenant: TenantId | str,
        spend: TokenSpend,
        now_epoch_s: int,
    ) -> int:
        """Book a call that already happened. Returns the billed cost.

        Recording is unconditional: a call that overran its ceiling is still
        recorded, because pretending it did not happen would make the next
        `check()` wrong too. The overrun surfaces as exhausted headroom.
        """
        name = tenant.value if isinstance(tenant, TenantId) else tenant
        if name not in self._shares:
            raise UnknownTenantError(f"no quota share for tenant {name!r}")
        cost = self.effective_cost(spend)
        self.ledger(now_epoch_s).add(name, cost)
        return cost

    # ── calibration ───────────────────────────────────────────────────────
    def calibrate(self, observed_capacity_tokens: int) -> None:
        """Replace the extrapolated capacity with a measured one.

        The utilisation fraction is preserved and re-applied, so "use 40% of
        it" keeps meaning 40% of what the plan actually gives — not 40% of a
        guess that turned out to be wrong in either direction.
        """
        if observed_capacity_tokens <= 0:
            raise FailClosedError("observed capacity must be positive")
        self._capacity = int(observed_capacity_tokens)
        self.capacity_is_estimate = False

    def snapshot(self, now_epoch_s: int) -> Mapping[str, object]:
        """Everything a dashboard needs, and nothing it does not."""
        led = self.ledger(now_epoch_s)
        return {
            "week": led.week,
            "capacity_tokens": self._capacity,
            "capacity_is_estimate": self.capacity_is_estimate,
            "utilisation": self._utilisation,
            "node_ceiling": self.node_ceiling,
            "node_spent": led.node_spent,
            "calls": led.calls,
            "orchestration_multiplier": self._multiplier,
            "tenants": {
                name: {
                    "ceiling": self.tenant_ceiling(name),
                    "spent": led.per_tenant.get(name, 0),
                    "remaining": self.remaining(now_epoch_s, name),
                }
                for name in sorted(self._shares)
            },
        }
