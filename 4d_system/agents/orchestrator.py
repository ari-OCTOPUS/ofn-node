"""
agents/orchestrator.py — The lead agent.

Dispatches W0→W1→W2→W3 in the gated pipeline:
    W0 (gate) → W1 (detect) → W2 (analyze) → W3 (report)

If W0 FAILS, the pipeline halts (gate rule from the handoff).
The orchestrator never edits the 4D/ reference — it only reads and dispatches.
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Optional

from .base import BaseAgent, AgentResult
from .verifier import VerifierAgent
from .detector import DetectorAgent
from .analyst import AnalystAgent
from .reporter import ReporterAgent


@dataclass
class PipelineResult:
    """Full output of one experiment run."""
    verifier: AgentResult
    detector: Optional[AgentResult]
    analyst:  Optional[AgentResult]
    reporter: Optional[AgentResult]
    halted_at: str = ""    # "" if completed, or agent name where it stopped
    log: list = field(default_factory=list)

    @property
    def completed(self) -> bool:
        return self.reporter is not None and not self.halted_at


class OrchestratorAgent(BaseAgent):
    name = "Orchestrator"
    role = "orchestrator (pipeline leader)"
    task_type = "orchestrate"

    def __init__(self, router=None):
        super().__init__(router)
        self.w0 = VerifierAgent(self.router)
        self.w1 = DetectorAgent(self.router)
        self.w2 = AnalystAgent(self.router)
        self.w3 = ReporterAgent(self.router)

    def run(self, inputs: dict) -> PipelineResult:
        """
        Execute the full pipeline on a time series.

        Inputs:
            series:  numpy array
            label:   str
            run_mc:  bool (whether to run MC verification)
        """
        series = inputs.get("series")
        label = inputs.get("label", "unknown")
        log = []

        # ── Wave 0: Gate (Verify) ──
        log.append("▶ W0 Verifier: running anchor checks...")
        ver_result = self.w0.run({"run_mc": inputs.get("run_mc", False),
                                  "mc_seed": inputs.get("mc_seed", 42)})
        log.append(f"  W0 done: status={ver_result.status}")

        if not ver_result.findings.get("all_pass", False):
            log.append("✗ GATE FAILED — halting pipeline.")
            return PipelineResult(
                verifier=ver_result, detector=None,
                analyst=None, reporter=None,
                halted_at="W0", log=log,
            )

        # ── Wave 1: Detect ──
        log.append("▶ W1 Detector: scanning for shadow structure...")
        det_result = self.w1.run({"series": series, "label": label})
        log.append(f"  W1 done: detectable={det_result.findings.get('detectable')}")

        # شکستِ W1 (مثلاً series=None) نباید به پایین‌دست برسد — قبلاً reporter
        # از findings خالی «NULL RESULT با اطمینانِ بالا» می‌ساخت (منفیِ کاذبِ مطمئن).
        if det_result.status == "fail":
            log.append("✗ W1 FAILED — halting pipeline (no analyzable data).")
            return PipelineResult(
                verifier=ver_result, detector=det_result,
                analyst=None, reporter=None,
                halted_at="W1", log=log,
            )

        # ── Wave 2: Analyze (geometric) ──
        log.append("▶ W2 Analyst: geometric interpretation...")
        ana_result = self.w2.run({
            "detector_findings": det_result.findings,
            "series": series,
        })
        log.append("  W2 done.")

        # ── Wave 3: Report ──
        log.append("▶ W3 Reporter: compiling final report...")
        rep_result = self.w3.run({
            "verifier": ver_result,
            "detector": det_result,
            "analyst":  ana_result,
            "series":   series,
            "label":    label,
        })
        log.append("  W3 done. Pipeline complete.")

        return PipelineResult(
            verifier=ver_result,
            detector=det_result,
            analyst=ana_result,
            reporter=rep_result,
            log=log,
        )

    def run_experiment(self, series: np.ndarray, label: str = "",
                       run_mc: bool = False) -> PipelineResult:
        """Convenience method."""
        return self.run({
            "series": series,
            "label": label,
            "run_mc": run_mc,
        })


if __name__ == "__main__":
    print("=== Orchestrator pipeline test (mock mode) ===\n")
    orch = OrchestratorAgent()

    # Test with synthetic AR(1) data
    rng = np.random.default_rng(42)
    n = 5000
    s = np.zeros(n)
    for t in range(1, n):
        s[t] = 0.7 * s[t-1] + rng.normal(0, 0.1)

    result = orch.run_experiment(s, label="test AR(1)", run_mc=True)

    for line in result.log:
        print(line)

    print(f"\nCompleted: {result.completed}")
    print(f"Halted at: {result.halted_at or 'none'}")
    if result.reporter:
        print(f"\nVerdict: {result.reporter.findings['verdict']}")
        print(f"Confidence: {result.reporter.findings['confidence']}")
