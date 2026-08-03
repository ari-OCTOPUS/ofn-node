"""Darwinian fitness from the ledger (INV-7, INV-8).

Fitness reads only CONFIRMED/ATTRIBUTED revenue — real money in the bank —
never agent self-reports. Cost accounting is three-bucket (input, output,
orchestration): orchestration tokens are the hidden bucket that silently
poisons EFFICIENCY when omitted, so it is a first-class field here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .domain import FITNESS_COUNTABLE, RevenueState
from .events import EventKind, LedgerEvent

COST_BUCKETS = ("input_cents", "output_cents", "orchestration_cents")


@dataclass(frozen=True)
class FitnessReport:
    organ_id: str
    confirmed_value_cents: int
    spend_cents: int

    @property
    def net_cents(self) -> int:
        return self.confirmed_value_cents - self.spend_cents

    @property
    def efficiency(self) -> float:
        """Confirmed value per cent spent. Zero spend with zero value scores 0."""
        if self.spend_cents == 0:
            return float(self.confirmed_value_cents > 0)
        return self.confirmed_value_cents / self.spend_cents


def compute_fitness(events: Iterable[LedgerEvent], organ_id: str) -> FitnessReport:
    value = 0
    spend = 0
    for e in events:
        if e.payload.get("organ_id") != organ_id:
            continue
        if e.kind is EventKind.REVENUE:
            state = RevenueState(e.payload["state"])
            if state in FITNESS_COUNTABLE:
                value += int(e.payload["amount_cents"])
            # REPORTED/APPROVED/SETTLED are visible in the ledger but worth 0
            # to fitness by construction (INV-7).
        elif e.kind is EventKind.SPEND:
            spend += sum(int(e.payload.get(bucket, 0)) for bucket in COST_BUCKETS)
    return FitnessReport(organ_id=organ_id, confirmed_value_cents=value, spend_cents=spend)
