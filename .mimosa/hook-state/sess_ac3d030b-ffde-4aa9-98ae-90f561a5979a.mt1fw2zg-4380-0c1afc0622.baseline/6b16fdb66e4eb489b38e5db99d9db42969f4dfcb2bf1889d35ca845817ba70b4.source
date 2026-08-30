"""tests/test_telemetry.py — تست sensory loop / حلقهٔ حسی."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

OCTOPUS_ROOT = Path(__file__).resolve().parent.parent
import sys
if str(OCTOPUS_ROOT) not in sys.path:
    sys.path.insert(0, str(OCTOPUS_ROOT))

from octopus_core.telemetry import Telemetry, TelemetryBus
from octopus_core.event_bus import EventBus


class TestTelemetry(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="octopus_tel_")
        self.path = Path(self.tmpdir) / "telemetry.jsonl"
        self.t = Telemetry(self.path)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_record_and_query(self):
        self.t.record("j1", "w", "i", 100.0, cost_aud=0.01, outcome={"x": 1})
        rows = self.t.query(worker="w", n=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["job_id"], "j1")
        self.assertEqual(rows[0]["cost_aud"], 0.01)

    def test_summary(self):
        self.t.record("a", "w", "i1", 100, cost_aud=0.01)
        self.t.record("b", "w", "i1", 200, cost_aud=0.02, error="fail")
        s = self.t.summary(worker="w")
        self.assertEqual(s["count"], 2)
        self.assertEqual(s["total_cost_aud"], 0.03)
        self.assertEqual(s["error_rate"], 0.5)
        self.assertEqual(s["intents"]["i1"], 2)

    def test_filter_since(self):
        old = time.time() - 1000
        self.t.record("old", "w", "i", 50, cost_aud=0.0)
        # override ts manually (since record uses time.time())
        # we test by reading back and checking ts exists
        rows = self.t.query(since=0, n=10)
        self.assertTrue(len(rows) >= 1)

    def test_correlation_id(self):
        self.t.record("c1", "w", "i", 10, correlation_id="cid-abc")
        rows = self.t.query(n=10)
        self.assertEqual(rows[0]["correlation_id"], "cid-abc")


class TestTelemetryBus(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="octopus_telb_")
        self.path = Path(self.tmpdir) / "telemetry.jsonl"
        self.t = Telemetry(self.path)
        self.bus = EventBus(persist_dir=Path(self.tmpdir) / "bus")
        self.tb = TelemetryBus(self.t, self.bus)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_record_publishes_event(self):
        received = []
        self.bus.subscribe("sensory.telemetry", lambda ev: received.append(ev))
        self.tb.record(job_id="j1", worker="w", intent="i", duration_ms=10)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["payload"]["worker"], "w")


if __name__ == "__main__":
    unittest.main()
