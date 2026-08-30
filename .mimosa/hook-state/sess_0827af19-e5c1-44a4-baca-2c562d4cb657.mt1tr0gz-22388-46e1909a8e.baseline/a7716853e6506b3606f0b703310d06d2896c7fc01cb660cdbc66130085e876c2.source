"""Typed data models for the read-only Mining pre-execution MVP."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any


class NodeStatus(str, Enum):
    UNKNOWN = "unknown"
    OFFLINE = "offline"
    AVAILABLE = "available"
    RUNNING = "running"
    BROKEN = "broken"


class PowerSource(str, Enum):
    UNKNOWN = "unknown"
    GRID = "grid"
    SOLAR = "solar"
    FREE = "free"
    MIXED = "mixed"


class DecisionStatus(str, Enum):
    OPEN = "open"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class RiskLevel(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"


@dataclass(frozen=True)
class VerdictItem:
    id: str
    decision: str
    status: DecisionStatus = DecisionStatus.OPEN
    answer: str | None = None
    evidence: str | None = None


@dataclass(frozen=True)
class HardwareNode:
    node_id: str
    device_type: str
    status: NodeStatus = NodeStatus.UNKNOWN
    location_code: str = "unknown"
    power_source: PowerSource = PowerSource.UNKNOWN
    electricity_cost_usd_kwh: float | None = None
    role: str = "unknown"
    access_method: str = "unknown"
    notes_safe: str = ""

    @property
    def is_electricity_safe(self) -> bool:
        if self.power_source in {PowerSource.SOLAR, PowerSource.FREE}:
            return True
        if self.electricity_cost_usd_kwh is None:
            return False
        return self.electricity_cost_usd_kwh <= 0.05


@dataclass(frozen=True)
class CoinCandidate:
    symbol: str
    name: str
    algorithm: str
    launch_date: date | None = None
    launch_age_days: int | None = None
    network_hashrate_hs: float | None = None
    block_reward: float | None = None
    blocks_per_day: float | None = None
    market_cap_usd: float | None = None
    liquidity_notes: str = ""
    dev_activity_notes: str = ""
    community_notes: str = ""
    quantum_resistance_claim: bool = False
    source_urls: list[str] = field(default_factory=list)

    def age_days(self, today: date | None = None) -> int | None:
        if self.launch_age_days is not None:
            return self.launch_age_days
        if self.launch_date is None:
            return None
        today = today or datetime.now(timezone.utc).date()
        return (today - self.launch_date).days


@dataclass(frozen=True)
class DeathWatch:
    coin: str
    dev_dead_weeks: float | None = None
    chain_stalled: bool | None = None
    community_dead: bool | None = None
    evidence: list[str] = field(default_factory=list)

    @property
    def abandon_flag(self) -> bool:
        if self.dev_dead_weeks is not None and self.dev_dead_weeks >= 8:
            return True
        if self.chain_stalled is True:
            return True
        if self.community_dead is True:
            return True
        return False


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    risk: RiskLevel
    message: str
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProjectSnapshot:
    phase: str
    execution_state: str
    wallet_seed_state: str
    hashrate_measured: bool
    profitability_data: str
    fleet_physical_status: str
    verdict_queue_open_count: int


JsonDict = dict[str, Any]
