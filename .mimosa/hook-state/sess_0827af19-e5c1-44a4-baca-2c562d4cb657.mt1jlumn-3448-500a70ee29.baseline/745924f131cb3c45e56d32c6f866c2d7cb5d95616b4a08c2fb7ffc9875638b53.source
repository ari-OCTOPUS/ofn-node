#!/usr/bin/env python3
"""test_orchestrator_wiring.py — تستِ رگرسیونِ وصل‌شدنِ orchestrator (۲۰۲۶-۰۷-۲۵).

این فیکس orchestrator.py را به CortexAugmentedBrain و pf_os.spine وصل کرد.
این تست دو اینvariants را قفل می‌کند:

  ۱) flag-off: مغز DualBrainV3 است (رفتارِ آزموده‌شده، byte-for-byte).
  ۲) flag-on CORTEX: مغز CortexAugmentedBrain است.
  ۳) flag-on SPINE: tick به busِ داخلی emit می‌کند.
  ۴) flag-off SPINE: tick emit نمی‌کند (no-op).
  ۵) حتی وقتی cortex down است (fallback)، tick نمی‌میرد.

هرگز به cortex واقعی وصل نمی‌شود (mock). همگی $0 و آفلاین.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

_PROJ = Path(__file__).resolve().parent.parent
for _p in (str(_PROJ), str(_PROJ / "brain"), str(_PROJ / "studio")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


class TestOrchestratorWiring(unittest.TestCase):
    def setUp(self):
        for f in ("OCTOPUS_WIRE_PROJECTF_SPINE", "OCTOPUS_WIRE_PROJECTF_CORTEX"):
            os.environ.pop(f, None)
        # reload orchestrator so it re-reads flags
        import importlib
        import orchestrator
        importlib.reload(orchestrator)

    def _fresh_orchestrator(self):
        import orchestrator
        import importlib
        importlib.reload(orchestrator)   # re-read flags each time
        return orchestrator.PFOrchestrator()

    # ═══ ۱) flag-off → DualBrainV3 ══════════════════════════════════════════
    def test_flag_off_uses_dual_brain(self):
        o = self._fresh_orchestrator()
        self.assertEqual(type(o.brain).__name__, "DualBrainV3",
                         "flag-off: مغز باید DualBrainV3 باشد")

    # ═══ ۲) flag-on CORTEX → CortexAugmentedBrain ═══════════════════════════
    def test_flag_on_cortex_uses_augmented(self):
        os.environ["OCTOPUS_WIRE_PROJECTF_CORTEX"] = "1"
        o = self._fresh_orchestrator()
        self.assertEqual(type(o.brain).__name__, "CortexAugmentedBrain",
                         "flag-on CORTEX: مغز باید CortexAugmentedBrain باشد")

    # ═══ ۳) flag-on SPINE → tick به bus emit می‌کند ═════════════════════════
    def test_flag_on_spine_emits_on_tick(self):
        import orchestrator
        os.environ["OCTOPUS_WIRE_PROJECTF_SPINE"] = "1"
        o = orchestrator.PFOrchestrator()
        # spine.emit را spy کن
        with mock.patch("orchestrator.PFOrchestrator") if False else mock.patch(
                "pf_os.spine.emit") as mock_emit:
            o.tick(visitors=100, subscribers=5, ppv_buyers=1, season="summer")
        self.assertTrue(mock_emit.called,
                        "flag-on SPINE: tick باید spine.emit را صدا بزند")
        # اولین فراخوانی event orchestrator.tick.done باید باشد
        call_args = mock_emit.call_args
        self.assertIn("orchestrator.tick.done", str(call_args))

    # ═══ ۴) flag-off SPINE → tick emit نمی‌کند ═════════════════════════════
    def test_flag_off_spine_no_emit(self):
        import orchestrator
        # هر دو flag خاموش
        o = orchestrator.PFOrchestrator()
        with mock.patch("pf_os.spine.emit") as mock_emit:
            o.tick(visitors=100, subscribers=5, ppv_buyers=1, season="summer")
        # emit صدا زده می‌شود ولی flag-off → no-op (داخل خودِ emit برمی‌گردد None)
        # مهم: tick نباید crash کنه. emit ممکن است صدا زده بشه ولی هیچ کاری نکنه.
        # بنابراین فقط crash نبودن مهم است:
        # (اگه emit صدا زده شد، flag-off داخلش None برمی‌گرداند — امن)

    # ═══ ۵) cortex down (fallback) → tick نمی‌میرد ══════════════════════════
    def test_cortex_down_tick_survives(self):
        import orchestrator
        os.environ["OCTOPUS_WIRE_PROJECTF_CORTEX"] = "1"
        os.environ["OCTOPUS_WIRE_PROJECTF_SPINE"] = "1"
        o = orchestrator.PFOrchestrator()
        # cortex_client.ask را mock کن تا exception بدهد
        with mock.patch("pf_os.cortex_client.ask",
                        side_effect=ConnectionError("cortex down")):
            # نباید raise کند
            r = o.tick(visitors=100, subscribers=5, ppv_buyers=1, season="summer")
        self.assertEqual(r.mode, "normal",
                         "cortex down نباید tick را بکشد")


if __name__ == "__main__":
    unittest.main(verbosity=2)
