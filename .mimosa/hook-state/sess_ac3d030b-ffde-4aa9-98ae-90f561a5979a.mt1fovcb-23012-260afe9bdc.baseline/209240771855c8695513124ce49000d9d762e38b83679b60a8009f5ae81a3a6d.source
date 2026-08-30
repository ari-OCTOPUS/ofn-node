"""tests/test_health.py — تست unified heartbeat / نبض ارگانیسم."""
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

from octopus_core.health import OrganHealth, OrganismHealth, HeartBeat
from octopus_core.event_bus import EventBus


class TestOrganHealth(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="octopus_h_")
        self.path = Path(self.tmpdir) / "organ.json"
        self.o = OrganHealth("brain_a", self.path)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_beat_and_alive(self):
        self.o.beat("healthy", {"mem": 80})
        self.assertTrue(self.o.is_alive(timeout_sec=300))
        d = self.o.to_dict()
        self.assertEqual(d["status"], "healthy")
        self.assertEqual(d["details"]["mem"], 80)

    def test_dead_status(self):
        self.o.beat("dead")
        self.assertFalse(self.o.is_alive(timeout_sec=300))

    def test_stale_timeout(self):
        import time as tmod
        self.o.beat("healthy")
        tmod.sleep(0.05)
        self.assertFalse(self.o.is_alive(timeout_sec=0.01))

    def test_persistence(self):
        self.o.beat("ok", {"x": 1})
        o2 = OrganHealth("brain_a", self.path)
        self.assertEqual(o2.to_dict()["status"], "ok")


class TestOrganismHealth(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="octopus_oh_")
        self.bus = EventBus(persist_dir=Path(self.tmpdir) / "bus")
        self.org = OrganismHealth(Path(self.tmpdir) / "health", bus=self.bus)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_register_and_beat(self):
        o = self.org.register("arm_1")
        o.beat("healthy")
        self.assertTrue(o.is_alive())
        self.assertEqual(len(self.org.status()), 1)

    def test_dead_organs(self):
        self.org.register("arm_1").beat("healthy")
        # arm_2 never beats
        self.org.register("arm_2")
        dead = self.org.dead_organs(timeout_sec=0.01)
        self.assertIn("arm_2", dead)
        self.assertNotIn("arm_1", dead)

    def test_organism_healthy(self):
        self.org.register("a").beat("healthy")
        self.org.register("b").beat("healthy")
        self.assertTrue(self.org.is_healthy(timeout_sec=300))

    def test_check_and_alert(self):
        self.org.register("stale_arm")
        # no beat
        alerts = self.org.check_and_alert(timeout_sec=0.01)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["organ"], "stale_arm")

    def test_bus_publish_on_beat(self):
        received = []
        self.bus.subscribe("organ.heartbeat", lambda ev: received.append(ev))
        self.org.beat("arm_1", status="healthy", details={"load": 0.5})
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["payload"]["organ"], "arm_1")


class TestHeartBeat(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="octopus_hb_")
        self.org = OrganismHealth(Path(self.tmpdir) / "health")
        self.hb = HeartBeat(self.org, "worker", interval_sec=0.01)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_tick(self):
        self.hb.tick(status="ok")
        self.assertTrue(self.hb.is_alive())

    def test_interval(self):
        import time as tmod
        self.hb.tick(status="ok")
        tmod.sleep(0.02)
        self.hb.tick(status="ok")  # should beat again because interval passed
        organ = self.org.register("worker")
        self.assertTrue(organ.is_alive(timeout_sec=0.05))


if __name__ == "__main__":
    unittest.main()
