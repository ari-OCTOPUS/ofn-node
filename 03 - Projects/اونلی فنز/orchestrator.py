#!/usr/bin/env python3
"""orchestrator.py — #1: Live Orchestrator. همهٔ قطعات در یک حلقه.
neural → brain → acquisition → hebbian → consolidation → comm → studio.
propose-only، $0، advisory. λ_persist<0."""
from __future__ import annotations
import sys, json, time
from dataclasses import dataclass, field, asdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_VAULT = _HERE.parent.parent  # F:\backup (Project-F → Projects → backup)
for _p in [str(_HERE / "brain"), str(_HERE / "studio"),
           str(_VAULT / "_ops" / "neural"),
           str(_VAULT / "_ops")]:
    if _p not in sys.path: sys.path.insert(0, _p)

from dual_brain_v3 import DualBrainV3, COMPLIANCE_RULES, ETHICS_RULES
from content_studio import ContentStudio
from acquisition import AcquisitionBrain, AcquisitionMemory
from neural_driver import NeuralDriver
from hebbian import HebbianAssociator
from consolidation import ConsolidationCycle
from sprint import SprintContract, SprintRunner
from hooks import HookBus
from circadian import CircadianMap

LAMBDA_PERSIST = -1.0


@dataclass
class TickResult:
    beat: int
    mode: str          # normal | protective | throttled
    pain: float
    snapshot: dict
    brain_inputs: dict | None = None
    thoughts: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    reflexes: list = field(default_factory=list)
    advisory_only: bool = True


class PFOrchestrator:
    """حلقهٔ زندهٔ Project-F. هر tick: snapshot → think → comm.
    protective mode: pain>0.7 → فقط heartbeat."""

    def __init__(self, studio=None, brain=None, acquisition=None,
                 data_dir: str | Path | None = None):
        self.studio = studio or ContentStudio()
        self.brain = brain or DualBrainV3()
        self.acquisition = acquisition or AcquisitionBrain(
            memory=AcquisitionMemory(data_path=str(_HERE / "brain" / "acq_orch.json")))
        self.neural = NeuralDriver()
        self.hebbian = HebbianAssociator(data_path=str(_HERE / "brain" / "hebb_orch.json"))
        self.consolidation = ConsolidationCycle(data_path=str(_HERE / "brain" / "con_orch.json"))
        self.circadian = CircadianMap()
        self.hooks = HookBus()
        self.sprint_runner = SprintRunner()
        self.sprint_runner.set_hooks(self.hooks)
        self._beat = 0
        self._protective = False
        self._data_dir = Path(data_dir) if data_dir else _HERE / "brain"
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def tick(self, rhythm=None, sensory=None, spectral=None, budget=None,
             post_feedback=None, competitor_data=None,
             visitors=100, subscribers=5, ppv_buyers=1,
             partner_stress=0.3, season="summer") -> TickResult:
        """یک دورِ کامل. همه advisory."""
        self._beat += 1
        self.hooks.fire("pre_sprint", {"beat": self._beat})

        # ۱. Neural snapshot
        neural_result = self.neural.evaluate(
            beat=self._beat, rhythm=rhythm, sensory=sensory,
            spectral=spectral, budget=budget)
        snap = neural_result["snapshot"]
        pain = neural_result["pain"]["level"]
        reflexes = neural_result["reflexes"]
        brain_inputs = neural_result["brain_inputs"]

        # ۲. Protective mode?
        if pain > 0.7:
            self._protective = True
            self.hooks.fire("on_error", {"reason": "protective mode", "pain": pain})
            return TickResult(beat=self._beat, mode="protective", pain=pain,
                              snapshot=snap, reflexes=reflexes)

        # ۳. Throttle check
        throttle = brain_inputs.get("throttle_brain", False)

        # ۴. Acquisition feedback (اگر داده هست)
        if post_feedback:
            for fb in post_feedback:
                self.acquisition.feedback_loop(**fb)

        # ۵. Thinking (اگر throttle نیست)
        thoughts_data = []
        messages_data = []
        if not throttle:
            checks = {**{r: True for r in COMPLIANCE_RULES},
                      **{r: True for r in ETHICS_RULES}}
            result = self.brain.think_and_communicate(
                checks=checks, competitor_data=competitor_data,
                visitors=visitors, subscribers=subscribers,
                ppv_buyers=ppv_buyers, partner_stress=partner_stress,
                season=season, drafts_count=self.studio.draft_count)
            thoughts_data = result.get("thoughts", [])
            messages_data = result.get("messages", [])

        # ۶. Hebbian: co-occurring signals
        signals = []
        if rhythm and rhythm.get("mode_color") == "GREEN":
            signals.append("green_mode")
        if spectral and spectral.get("sigma", 0) < 0.8:
            signals.append("stable_sigma")
        if brain_inputs.get("data_confidence", 0) > 0.3:
            signals.append("good_data")
        season_tag = season
        signals.append(season_tag)
        if signals:
            self.hebbian.observe(signals)

        # ۷. Consolidation (هر ۱۰ tick)
        if self._beat % 10 == 0:
            sources = {}
            perf = self.acquisition.memory.tag_performance()
            if perf:
                sources["acquisition"] = perf
            learned = self.brain.thinking._historical if hasattr(self.brain.thinking, '_historical') else []
            if learned:
                sources["doctor_archive"] = [{"outcome": d.get("outcome")} for d in learned if d.get("type") == "price"]
            if sources:
                self.consolidation.run(sources)

        # ۸. Sprint management — TINV-5: beat_seq تزریق می‌شود (نه wall-clock)
        if not self.sprint_runner.is_active:
            self.sprint_runner.start(SprintContract(
                sprint_id=f"tick-{self._beat}", scope="pf-cycle",
                budget_beats=1, budget_tokens=50), start_beat=self._beat)
        self.sprint_runner.tick(tokens=0, now_beat=self._beat)
        self.sprint_runner.finish(now_beat=self._beat)

        self.hooks.fire("post_sprint", {"beat": self._beat, "completed": True})

        mode = "throttled" if throttle else "normal"
        return TickResult(beat=self._beat, mode=mode, pain=pain,
                          snapshot=snap, brain_inputs=brain_inputs,
                          thoughts=thoughts_data, messages=messages_data,
                          reflexes=reflexes)

    @property
    def beat(self) -> int:
        return self._beat

    @property
    def is_protective(self) -> bool:
        return self._protective

    def status(self) -> dict:
        return {"beat": self._beat, "protective": self._protective,
                "drafts": self.studio.draft_count,
                "acquisition_confidence": self.acquisition.memory.learning_confidence(),
                "hebbian_assocs": len(self.hebbian.associations),
                "consolidation_cycles": self.consolidation.cycle_count,
                "lambda_persist": LAMBDA_PERSIST}
