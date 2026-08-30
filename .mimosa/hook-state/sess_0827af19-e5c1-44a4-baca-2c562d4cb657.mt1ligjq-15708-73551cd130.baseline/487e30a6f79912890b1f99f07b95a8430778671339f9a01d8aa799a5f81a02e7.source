"""tests/test_capability_registry.py — تست قابلیت‌نامهٔ داینامیک."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

OCTOPUS_ROOT = Path(__file__).resolve().parent.parent
import sys
if str(OCTOPUS_ROOT) not in sys.path:
    sys.path.insert(0, str(OCTOPUS_ROOT))

from octopus_core.capability_registry import CapabilityRegistry, CapabilityRegistrySync


class TestCapabilityRegistry(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="octopus_cap_")
        self.path = Path(self.tmpdir) / "caps.json"
        self.reg = CapabilityRegistry(path=self.path)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_register_and_can_execute(self):
        self.reg.register("s:new", "ui", "saba", executable=True)
        ok, reason = self.reg.can_execute("s:new")
        self.assertTrue(ok)
        self.assertEqual(reason, "")

    def test_revoke(self):
        self.reg.register("s:trend", "ui", "saba", executable=True)
        self.reg.revoke("s:trend", "brain offline")
        ok, reason = self.reg.can_execute("s:trend")
        self.assertFalse(ok)
        self.assertIn("brain offline", reason)

    def test_not_registered(self):
        ok, reason = self.reg.can_execute("ghost:cmd")
        self.assertFalse(ok)
        self.assertIn("not registered", reason)

    def test_persistence(self):
        self.reg.register("a", "ui", "x", executable=True)
        del self.reg
        reg2 = CapabilityRegistry(path=self.path)
        ok, _ = reg2.can_execute("a")
        self.assertTrue(ok)

    def test_render_menu(self):
        self.reg.register("s:new", "ui", "saba", executable=True)
        self.reg.register("s:trend", "ui", "saba", executable=False, reason="coming-soon")
        items = self.reg.render_menu("ui", prefix_filter="s:")
        self.assertEqual(len(items), 2)
        self.assertTrue(items[0]["executable"])
        self.assertFalse(items[1]["executable"])

    def test_heartbeat_and_stale(self):
        import time
        self.reg.register("h", "api", "brain", executable=True)
        self.reg.heartbeat("h")
        self.assertFalse(self.reg.is_stale("h", timeout_sec=10.0))
        time.sleep(0.05)
        self.assertTrue(self.reg.is_stale("h", timeout_sec=0.01))


class TestCapabilityRegistrySync(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="octopus_cap2_")
        self.path = Path(self.tmpdir) / "caps.json"
        self.reg = CapabilityRegistrySync(path=self.path)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_sync_register(self):
        self.reg.register("x", "ui", "test", executable=False, reason="off")
        ok, reason = self.reg.can_execute("x")
        self.assertFalse(ok)
        self.assertIn("off", reason)


if __name__ == "__main__":
    unittest.main()
