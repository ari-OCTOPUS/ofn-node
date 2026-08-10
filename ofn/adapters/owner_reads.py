"""Owner reads facade — the owner surface of the node, extracted gradually.

Phase H of the completion megaprompt (finding 81): Node grew into a
god-object. This facade is the first step: it names the owner surface
explicitly and keeps it reachable as `node.owner`, while the implementation
still lives on Node (the methods touch ledger/outbox/registry directly).

The contract: `node.owner.X(...)` behaves identically to `node.X(...)`.
Nothing is moved here yet — the facade is the seam the extract will cut
along. Moving a method means: copy it here, give it a reference to the
stores it needs, keep the Node method as a one-line delegate, and run the
owner API tests.

No business logic lives in this module. It is a view over the node.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ..node import Node


class OwnerReads:
    """Delegating facade over Node's owner surface.

    Every method forwards to the node. The node remains the source of
    truth; this class exists so callers and tests can address the owner
    surface as one unit, and so the future extract has a defined target.
    """

    def __init__(self, node: "Node") -> None:
        self._node = node

    # ── queue / decisions ─────────────────────────────────────────────────
    def queue(self) -> list:
        return self._node.owner_queue()

    def decide(self, item_id: str, approve: bool,
               confirmed_twice: bool) -> dict:
        return self._node.owner_decide(item_id, approve, confirmed_twice)

    # ── read models ───────────────────────────────────────────────────────
    def status(self) -> dict:
        return self._node.owner_status()

    def metrics(self) -> dict:
        return self._node.owner_metrics()

    def observability(self) -> dict:
        return self._node.owner_observability()

    def snapshot(self) -> dict:
        return self._node.owner_snapshot()

    def events(self, limit: int = 40) -> list:
        return self._node.recent_events(limit)

    def businesses(self) -> dict:
        return self._node.owner_businesses()

    def business_snapshot(self, business_id: str) -> dict | None:
        return self._node.owner_business_snapshot(business_id)

    def core_snapshot(self) -> dict:
        return self._node.owner_core_snapshot()

    def risks(self) -> dict:
        return self._node.owner_risks()

    def ledger_summary(self) -> dict:
        return self._node.owner_ledger_summary()

    def mini_webs(self) -> dict:
        return self._node.owner_mini_webs_summary()

    def telegram(self) -> dict:
        return self._node.owner_telegram_summary()

    # ── painting lead CRM, owner-only ─────────────────────────────────────
    def painting_leads(self, **kw) -> dict:
        return self._node.painting_leads(**kw)

    def painting_dashboard(self) -> dict:
        return self._node.painting_dashboard()
