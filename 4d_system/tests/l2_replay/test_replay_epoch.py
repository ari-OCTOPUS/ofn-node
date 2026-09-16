"""L2: full epochs replayed from the committed cassette — no live brain anywhere.

These tests pin three properties:
  1. the demo epoch runs end-to-end against ReplayLLM (cassette hit for every call);
  2. two independent replays produce byte-identical ledgers (determinism);
  3. prompt drift fails closed (CassetteMissError), it never guesses.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.l2

from nbb_cp.adapters.llm.cassette import CassetteMissError, ReplayLLM
from nbb_cp.adapters.runtime.system import FixedClock, ManualKillSwitch, SequentialIdGen
from nbb_cp.adapters.storage.memory import MemoryBudgetStore, MemoryLedgerStore
from nbb_cp.adapters.telemetry.noop import NoopTelemetry
from nbb_cp.app.governor import run_demo_epoch
from nbb_cp.app.service import ControlPlaneService, default_budget_state
from nbb_cp.kernel.domain import Mode, Organ
from nbb_cp.kernel.events import verify_chain
from nbb_cp.kernel.ports import LLMRequest

CASSETTE = Path(__file__).resolve().parent.parent.parent / "cassettes" / "demo_epoch.jsonl"

ORGANS = (
    Organ(organ_id="accounting", name="Accounting"),
    Organ(organ_id="painting-leads", name="Lead-Painting"),
    Organ(organ_id="ziman", name="Ziman Gallery"),
)


def fresh_service() -> tuple[ControlPlaneService, MemoryLedgerStore]:
    ledger = MemoryLedgerStore()
    service = ControlPlaneService(
        ledger=ledger,
        budget=MemoryBudgetStore(default_budget_state(3000)),
        llm=ReplayLLM(CASSETTE),
        telemetry=NoopTelemetry(),
        clock=FixedClock(),
        idgen=SequentialIdGen(),
        kill=ManualKillSwitch(),
        organs=ORGANS,
        mode=Mode.SHADOW,
    )
    return service, ledger


class TestReplayEpoch:
    def test_two_epochs_replay_from_cassette(self):
        service, ledger = fresh_service()
        llm = ReplayLLM(CASSETTE)
        first = run_demo_epoch(service, llm)
        second = run_demo_epoch(service, llm)
        assert first["grants_executed"] == 3
        assert second["epoch_completed"] == 1
        assert first["audit_violations"] == 0 and second["audit_violations"] == 0
        verify_chain(ledger.read_all())

    def test_replay_is_deterministic_across_runs(self):
        service_a, _ = fresh_service()
        service_b, _ = fresh_service()
        llm_a = ReplayLLM(CASSETTE)
        llm_b = ReplayLLM(CASSETTE)
        summary_a = [run_demo_epoch(service_a, llm_a) for _ in range(2)]
        summary_b = [run_demo_epoch(service_b, llm_b) for _ in range(2)]
        assert summary_a == summary_b
        assert summary_a[-1]["head_hash"] == summary_b[-1]["head_hash"]

    def test_budget_committed_matches_plan_arithmetic(self):
        service, _ = fresh_service()
        summary = run_demo_epoch(service, ReplayLLM(CASSETTE))
        # epoch 0: headroom 3000c, 3 organs -> min(500, 3000//6) = 500c each.
        assert summary["committed_cents"] == 1500

    def test_drifted_prompt_fails_closed(self):
        llm = ReplayLLM(CASSETTE)
        with pytest.raises(CassetteMissError):
            llm.complete(LLMRequest(task="govern", prompt="a prompt that was never recorded"))

    def test_cassette_is_committed_and_nonempty(self):
        assert CASSETTE.exists(), "cassettes/demo_epoch.jsonl must be committed"
        assert CASSETTE.read_text(encoding="utf-8").strip(), "cassette must not be empty"
