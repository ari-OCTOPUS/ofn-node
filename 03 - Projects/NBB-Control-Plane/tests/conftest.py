"""Shared fixtures: a fully wired in-memory service with deterministic doubles."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nbb_cp.adapters.runtime.system import FixedClock, ManualKillSwitch, SequentialIdGen
from nbb_cp.adapters.storage.memory import MemoryBudgetStore, MemoryLedgerStore
from nbb_cp.adapters.llm.mock import MockLLM
from nbb_cp.adapters.telemetry.noop import CapturingTelemetry
from nbb_cp.app.service import ControlPlaneService, default_budget_state
from nbb_cp.kernel.domain import Mode, Money, Organ

CAP_CENTS = 3000

ORGANS = (
    Organ(organ_id="accounting", name="Accounting", vital=True),
    Organ(organ_id="painting-leads", name="Lead-Painting", vital=True),
    Organ(organ_id="ziman", name="Ziman Gallery", vital=True, floor=Money(100)),
)


@pytest.fixture()
def clock() -> FixedClock:
    return FixedClock()


@pytest.fixture()
def kill() -> ManualKillSwitch:
    return ManualKillSwitch()


@pytest.fixture()
def telemetry() -> CapturingTelemetry:
    return CapturingTelemetry()


@pytest.fixture()
def ledger() -> MemoryLedgerStore:
    return MemoryLedgerStore()


@pytest.fixture()
def budget_store() -> MemoryBudgetStore:
    return MemoryBudgetStore(default_budget_state(CAP_CENTS))


@pytest.fixture()
def service(ledger, budget_store, clock, kill, telemetry) -> ControlPlaneService:
    return ControlPlaneService(
        ledger=ledger,
        budget=budget_store,
        llm=MockLLM(),
        telemetry=telemetry,
        clock=clock,
        idgen=SequentialIdGen(),
        kill=kill,
        organs=ORGANS,
        mode=Mode.SHADOW,
    )


@pytest.fixture()
def service_factory():
    """Build additional services over existing stores (projection-rebuild tests)."""

    def make(ledger, budget_store, *, mode: Mode = Mode.SHADOW, kill=None) -> ControlPlaneService:
        return ControlPlaneService(
            ledger=ledger,
            budget=budget_store,
            llm=MockLLM(),
            telemetry=CapturingTelemetry(),
            clock=FixedClock(),
            idgen=SequentialIdGen(),
            kill=kill or ManualKillSwitch(),
            organs=ORGANS,
            mode=mode,
        )

    return make
