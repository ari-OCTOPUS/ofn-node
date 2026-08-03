"""Re-record cassettes/demo_epoch.jsonl from the deterministic demo epoch.

Run whenever the demo epoch script or governor prompt changes:
    python scripts/record_cassette.py
L2 replay tests fail closed on drift until this is re-run and committed.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from nbb_cp.adapters.llm.cassette import RecordingLLM
from nbb_cp.adapters.llm.mock import MockLLM
from nbb_cp.adapters.runtime.system import FixedClock, ManualKillSwitch, SequentialIdGen
from nbb_cp.adapters.storage.memory import MemoryBudgetStore, MemoryLedgerStore
from nbb_cp.adapters.telemetry.noop import NoopTelemetry
from nbb_cp.app.governor import run_demo_epoch
from nbb_cp.app.service import ControlPlaneService, default_budget_state
from nbb_cp.kernel.domain import Mode, Organ

CASSETTE = ROOT / "cassettes" / "demo_epoch.jsonl"

ORGANS = (
    Organ(organ_id="accounting", name="Accounting"),
    Organ(organ_id="painting-leads", name="Lead-Painting"),
    Organ(organ_id="ziman", name="Ziman Gallery"),
)


def build_service() -> ControlPlaneService:
    return ControlPlaneService(
        ledger=MemoryLedgerStore(),
        budget=MemoryBudgetStore(default_budget_state(3000)),
        llm=MockLLM(),
        telemetry=NoopTelemetry(),
        clock=FixedClock(),
        idgen=SequentialIdGen(),
        kill=ManualKillSwitch(),
        organs=ORGANS,
        mode=Mode.SHADOW,
    )


def main() -> None:
    if CASSETTE.exists():
        CASSETTE.unlink()
    service = build_service()
    recorder = RecordingLLM(MockLLM(), CASSETTE)
    for _ in range(2):  # two epochs on tape
        summary = run_demo_epoch(service, recorder)
        print(summary)
    print(f"recorded -> {CASSETTE}")


if __name__ == "__main__":
    main()
