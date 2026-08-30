"""
agents/verifier.py — W0: Numerical Verifier.

Reproduces the anchor formulas from 4.py against the live model,
then asks the LLM to interpret any discrepancies.

Gate: all anchors must PASS before downstream agents can run.
"""
from __future__ import annotations
import numpy as np
from .base import BaseAgent, AgentResult
from core.model import solve_from_stds, run_self_test, ANCHORS
from config.settings import ANCHORS as SETTINGS_ANCHORS


class VerifierAgent(BaseAgent):
    name = "W0-Verifier"
    role = "verifier (numeric gate)"
    task_type = "verify"

    def run(self, inputs: dict) -> AgentResult:
        """Verify the model's anchor values and MC consistency."""
        # 1) Run the self-test (analytical anchors)
        test_results = run_self_test()

        all_pass = True
        discrepancies = []
        report_lines = []

        for name, (computed, expected, rel_err) in test_results.items():
            passed = rel_err < 1e-4
            if not passed:
                all_pass = False
                discrepancies.append(f"{name}: computed={computed:.8f} "
                                     f"expected={expected:.8f} rel_err={rel_err:.2e}")
            report_lines.append(f"  {'✓' if passed else '✗'} {name:12s}  "
                                f"val={computed:.8f}  rel_err={rel_err:.2e}")

        # 2) Optional: cross-check with a short MC simulation
        mc_check = "skipped"
        if inputs.get("run_mc", False):
            from core.simulator import simulate, verify_against_model
            result = simulate(T=50_000, seed=inputs.get("mc_seed", 42))
            checks = verify_against_model(result, tol=0.1)
            mc_pass = all(p for _, _, p in checks.values())
            if not mc_pass:
                all_pass = False
            mc_check = "PASS" if mc_pass else "FAIL"
            report_lines.append(f"\n  Monte-Carlo (T=50k): {mc_check}")
            for name, (emp, thy, passed) in checks.items():
                report_lines.append(f"    {'✓' if passed else '✗'} {name}")

        # 3) Ask LLM to interpret (if discrepancies exist)
        narrative = ""
        if discrepancies:
            prompt = (
                f"در راستی‌آزمایی لنگرها، این اختلاف‌ها یافت شد:\n"
                + "\n".join(discrepancies) +
                "\n\nاحتمالِ دلایل؟ آیا هسته‌ی نظریه در خطر است یا فقط خطای رُندسازی؟"
            )
            narrative = self.llm(prompt, temperature=0.3)
        else:
            narrative = (
                "همه‌ی لنگرهای عددی با خطای نسبی < ۱e-۴ بازتولید شدند.\n"
                "هسته‌ی ریاضیِ مدل سالم است و می‌توان به مرحله‌ی تشخیص رفت."
            )

        findings = {
            "anchors": {n: {"computed": c, "expected": e, "rel_err": r}
                        for n, (c, e, r) in test_results.items()},
            "all_pass": all_pass,
            "mc_check": mc_check,
            "report": "\n".join(report_lines),
        }

        return self._make_result(
            findings=findings,
            narrative=narrative,
            status="ok" if all_pass else "fail",
            discrepancies=discrepancies,
        )
