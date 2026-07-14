"""تست‌های policy ladder + flagها — high-risk گیت می‌خورد، autonomy کم‌ریسک می‌ماند."""
from __future__ import annotations

import os
import unittest
from unittest import mock

from tests import _bootstrap  # noqa: F401

from control_plane import policy
from control_plane.flags import FLAG_DEFAULTS, all_flags, flag, governance_mode
from control_plane.policy import Level, evaluate


class TestPolicyLadder(unittest.TestCase):
    def test_ladder_ordering(self):
        self.assertLess(Level.OBSERVE, Level.REQUIRE_APPROVAL)
        self.assertLess(Level.REQUIRE_APPROVAL, Level.KILL_SWITCH)
        self.assertEqual(int(Level.KILL_SWITCH), 5)

    def test_owner_high_risk_list_requires_approval(self):
        """لیستِ high-risk مالک (تصمیم 2026-07-11) → همه approval-gated."""
        for action in ("change_tcb", "self_code_apply", "self_code_approve",
                       "flip_live_flag", "budget_increase", "external_send_publish",
                       "delete_data", "change_env_or_secrets", "change_config",
                       "cross_project_write", "change_daemon_behavior",
                       "model_promotion", "backup_restore", "run_external_command"):
            r = evaluate(action)
            self.assertTrue(r.requires_approval, f"{action} باید approval بخواهد")
            self.assertGreaterEqual(r.level, int(Level.REQUIRE_APPROVAL), action)

    def test_low_risk_stays_autonomous(self):
        """تمرکزِ کنترل نباید autonomy کم‌ریسک را بکشد."""
        for action in ("read_only", "write_outputs", "memory_write",
                       "call_cloud_llm", "self_code_propose", "archive",
                       "telegram_digest", "backup_create"):
            r = evaluate(action)
            self.assertFalse(r.requires_approval, f"{action} باید خودمختار بماند")
            self.assertLessEqual(r.level, int(Level.SHADOW_LOG), action)

    def test_kill_switch_is_level_5(self):
        self.assertEqual(evaluate("kill_switch").level, 5)

    def test_unknown_action_needs_review_not_silent_pass(self):
        r = evaluate("teleport_to_mars")
        self.assertTrue(r.needs_review)
        self.assertTrue(r.requires_approval)

    def test_risk_hint_only_escalates(self):
        up = evaluate("write_local_file", risk_hint="high")
        self.assertGreaterEqual(up.level, int(Level.REQUIRE_APPROVAL))
        down = evaluate("change_tcb", risk_hint="low")  # hint هرگز پایین نمی‌آورد
        self.assertGreaterEqual(down.level, int(Level.REQUIRE_APPROVAL))

    def test_destructive_mentions_rollback(self):
        r = evaluate("delete_data")
        self.assertIn("rollback", r.reason)

    def test_policy_module_is_pure(self):
        """shadow نباید رفتارِ live را عوض کند — ماژول I/O ندارد."""
        import inspect
        src = inspect.getsource(policy)
        for forbidden in ("open(", "subprocess", "os.system", "write_text",
                          "sqlite3", "requests", "httpx"):
            self.assertNotIn(forbidden, src, f"policy باید pure بماند: {forbidden}")


class TestFlags(unittest.TestCase):
    def _clean_env(self):
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        for k in list(os.environ):
            if k.startswith("CONTROL_PLANE_"):
                del os.environ[k]

    def test_defaults_only_observe_on(self):
        """default-off برای هر چیزِ live — قاعده‌ی سختِ مالک."""
        self._clean_env()
        f = all_flags()
        self.assertTrue(f["CONTROL_PLANE_OBSERVE_ONLY"])
        for name in ("CONTROL_PLANE_SHADOW_POLICY", "CONTROL_PLANE_APPROVALS_LIVE",
                     "CONTROL_PLANE_LIVE_GOVERNANCE", "CONTROL_PLANE_KILL_SWITCH_LIVE"):
            self.assertFalse(f[name], f"{name} باید default-off باشد")
        self.assertEqual(governance_mode(), "observe-only (v1)")

    def test_env_override_works(self):
        self._clean_env()
        os.environ["CONTROL_PLANE_SHADOW_POLICY"] = "1"
        self.assertTrue(flag("CONTROL_PLANE_SHADOW_POLICY"))
        os.environ["CONTROL_PLANE_OBSERVE_ONLY"] = "0"
        self.assertFalse(flag("CONTROL_PLANE_OBSERVE_ONLY"))

    def test_all_defaults_registered(self):
        self.assertEqual(
            set(FLAG_DEFAULTS),
            {"CONTROL_PLANE_OBSERVE_ONLY", "CONTROL_PLANE_SHADOW_POLICY",
             "CONTROL_PLANE_APPROVALS_LIVE", "CONTROL_PLANE_LIVE_GOVERNANCE",
             "CONTROL_PLANE_KILL_SWITCH_LIVE"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
