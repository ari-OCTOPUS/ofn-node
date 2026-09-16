"""تستِ دروازه‌ی W1: شکستِ detector نباید «NULL RESULT مطمئن» تولید کند."""
from tests import _bootstrap  # noqa: F401

import unittest


class FakeRouter:
    """روترِ ساختگی — هیچ تماسِ شبکه‌ای نمی‌زند."""

    def ask(self, prompt, system=None, task=None, temperature=0.7, **kw):
        return "mock-narrative"


class TestPipelineGate(unittest.TestCase):
    def test_w1_fail_halts_pipeline(self):
        """series=None → W1 با status=fail → توقف در W1، نه گزارشِ منفیِ کاذب."""
        from agents.orchestrator import OrchestratorAgent
        orch = OrchestratorAgent(router=FakeRouter())
        result = orch.run({"series": None, "label": "t", "run_mc": False})
        self.assertEqual(result.halted_at, "W1")
        self.assertIsNone(result.reporter)
        self.assertIsNone(result.analyst)
        self.assertFalse(result.completed)
        self.assertEqual(result.detector.status, "fail")

    def test_reporter_incomplete_when_detector_missing(self):
        """reporter با detector غایب/شکست‌خورده باید INCOMPLETE بدهد نه NULL مطمئن."""
        from agents.reporter import ReporterAgent
        rep = ReporterAgent(router=FakeRouter())
        res = rep.run({"verifier": None, "detector": None,
                       "analyst": None, "series": None, "label": "x"})
        self.assertIn("INCOMPLETE", res.findings["verdict"])
        self.assertEqual(res.findings["confidence"], "none")
        self.assertEqual(res.status, "warning")
        self.assertNotIn("NULL RESULT", res.findings["verdict"])


if __name__ == "__main__":
    unittest.main()
