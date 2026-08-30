"""tests/test_actuator.py — تست قلب اجرا / motor cortex."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

OCTOPUS_ROOT = Path(__file__).resolve().parent.parent
import sys
if str(OCTOPUS_ROOT) not in sys.path:
    sys.path.insert(0, str(OCTOPUS_ROOT))

from octopus_core.actuator import Actuator, ActuatorMode, ActionStatus


class TestActuator(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="octopus_act_")
        self.act = Actuator(mode=ActuatorMode.SHADOW,
                            persist_dir=Path(self.tmpdir))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_shadow_auto_approve(self):
        r = self.act.submit("test_intent", {"k": "v"}, actor="bot")
        self.assertTrue(r["ok"])
        self.assertEqual(r["mode"], "shadow")
        rec = self.act.get(r["action_id"])
        self.assertEqual(rec["status"], "completed")

    def test_dry_run(self):
        act = Actuator(mode=ActuatorMode.DRY_RUN, persist_dir=Path(self.tmpdir))
        r = act.submit("post_draft", {"channel": "reddit"}, actor="bot")
        self.assertTrue(r["ok"])
        self.assertEqual(r["mode"], "dry_run")
        self.assertTrue(r["result"]["feasible"])

    def test_live_needs_approval(self):
        act = Actuator(mode=ActuatorMode.LIVE, persist_dir=Path(self.tmpdir))
        r = act.submit("post_draft", {"channel": "reddit"}, actor="bot")
        self.assertEqual(r["status"], "pending")
        self.assertEqual(r["note"], "waiting for approval")
        # approve
        a = act.approve(r["action_id"], approver="owner")
        self.assertTrue(a["ok"])
        self.assertEqual(a["mode"], "live")

    def test_reject(self):
        r = self.act.submit("x", {}, actor="bot")
        a = self.act.reject(r["action_id"], reason="no", approver="owner")
        self.assertTrue(a["ok"])
        self.assertEqual(a["status"], "denied")

    def test_persistence(self):
        self.act.submit("a", {"v": 1})
        del self.act
        act2 = Actuator(mode=ActuatorMode.SHADOW, persist_dir=Path(self.tmpdir))
        items = act2.list_by_status()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["intent"], "a")

    def test_rollback(self):
        act = Actuator(mode=ActuatorMode.SHADOW, persist_dir=Path(self.tmpdir))
        r = act.submit("post", {"text": "hi"}, actor="bot")
        # manually set rollback payload in record (normally set by on_execute)
        act._actions[r["action_id"]]["rollback_payload"] = {"delete": "post_123"}
        act._save()
        rb = act.rollback(r["action_id"])
        self.assertTrue(rb["ok"])
        self.assertIn("rollback_action_id", rb)

    def test_unknown_intent_dry_run(self):
        act = Actuator(mode=ActuatorMode.DRY_RUN, persist_dir=Path(self.tmpdir))
        r = act.submit("nuclear_launch", {}, actor="bot", risk_tier="RED")
        # RED در dry_run هم نیاز به approve دارد
        a = act.approve(r["action_id"], approver="owner")
        self.assertTrue(a["ok"])
        self.assertFalse(a["result"]["feasible"])  # unknown intent


if __name__ == "__main__":
    unittest.main()
