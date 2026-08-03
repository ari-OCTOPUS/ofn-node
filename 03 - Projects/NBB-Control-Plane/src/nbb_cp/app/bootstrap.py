"""Wiring: build a ControlPlaneService from config. Adapters chosen here, nowhere else."""

from __future__ import annotations

from ..adapters.llm.cassette import ReplayLLM
from ..adapters.llm.mock import MockLLM
from ..adapters.runtime.system import FileKillSwitch, SystemClock, UuidGen
from ..adapters.storage.memory import MemoryBudgetStore, MemoryLedgerStore
from ..adapters.storage.sqlite import SqliteBudgetStore, SqliteLedgerStore
from ..adapters.telemetry.noop import NoopTelemetry
from ..kernel.domain import Organ
from ..kernel.errors import FailClosedError
from ..kernel.ports import LLMPort
from .config import AppConfig
from .service import ControlPlaneService, default_budget_state


def build_llm(config: AppConfig) -> LLMPort:
    if config.llm_mode == "mock":
        return MockLLM()
    if config.llm_mode == "cassette":
        return ReplayLLM(config.cassette_path)
    if config.llm_mode == "live":
        # Phase 1 deliverable: the LangGraph adapter plugs in here, behind
        # LLMPort, wrapped in RecordingLLM when NBB_CASSETTE_PATH is set.
        raise FailClosedError("live LLM mode is a Phase 1 deliverable; use mock or cassette")
    raise FailClosedError(f"unknown NBB_LLM_MODE {config.llm_mode!r}")


def build_service(config: AppConfig, *, in_memory: bool = False) -> ControlPlaneService:
    organs = [Organ(organ_id=oid, name=name) for oid, name in config.organs]
    if in_memory:
        ledger = MemoryLedgerStore()
        budget = MemoryBudgetStore(default_budget_state(config.global_cap_cents))
    else:
        ledger = SqliteLedgerStore(config.db_path)
        budget = SqliteBudgetStore(config.db_path, default_budget_state(config.global_cap_cents))
    return ControlPlaneService(
        ledger=ledger,
        budget=budget,
        llm=build_llm(config),
        telemetry=NoopTelemetry(),
        clock=SystemClock(),
        idgen=UuidGen(),
        kill=FileKillSwitch(config.kill_switch_file),
        organs=organs,
        mode=config.mode,
        sigma_window_epochs=config.sigma_window_epochs,
    )
