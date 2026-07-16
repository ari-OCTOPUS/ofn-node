"""تست‌های v3 Approvals — flag-gated، double-confirm، فقط مسیرِ امنِ موجود، audit کامل."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import _bootstrap  # noqa: F401

from control_plane.approvals import (approvals_live, audit_tail,
                                     decide_self_code, proposal_diff,
                                     resolve_bus_approval)
from control_plane.policy import evaluate


def _clean_cp_env(tc: unittest.TestCase):
    patcher = mock.patch.dict(os.environ)
    patcher.start()
    tc.addCleanup(patcher.stop)
    for k in list(os.environ):
        if k.startswith("CONTROL_PLANE_"):
            del os.environ[k]


class TestGates(unittest.TestCase):
    def test_policy_says_approval_is_high_risk(self):
        r = evaluate("self_code_approve")
        self.assertTrue(r.requires_approval)
        self.assertGreaterEqual(r.level, 3)

    def test_default_flag_off_refuses_and_never_touches_brain(self):
        """قاعده‌ی طلایی: default-off → حتی با confirm هم هیچ تماسی با brain نیست."""
        _clean_cp_env(self)
        self.assertFalse(approvals_live())
        with tempfile.TemporaryDirectory() as td, \
             mock.patch("brain.self_code.approve") as m_ap, \
             mock.patch("brain.self_code.reject") as m_rj:
            res = decide_self_code("xxx", "approve", confirmed=True,
                                   audit_dir=Path(td))
            self.assertFalse(res["result"]["ok"])
            self.assertIn("خاموش", res["result"]["reason"])
            m_ap.assert_not_called()
            m_rj.assert_not_called()
            # حتی تلاشِ ردشده هم audit می‌شود (evidence trail)
            trail = audit_tail(audit_dir=Path(td))
            self.assertEqual(len(trail), 1)
            self.assertFalse(trail[0]["flag_live"])

    def test_no_confirm_refused_even_with_flag_on(self):
        _clean_cp_env(self)
        os.environ["CONTROL_PLANE_APPROVALS_LIVE"] = "1"
        with tempfile.TemporaryDirectory() as td, \
             mock.patch("brain.self_code.approve") as m_ap:
            res = decide_self_code("xxx", "approve", confirmed=False,
                                   audit_dir=Path(td))
            self.assertFalse(res["result"]["ok"])
            self.assertIn("double-confirm", res["result"]["reason"])
            m_ap.assert_not_called()

    def test_invalid_decision_refused(self):
        _clean_cp_env(self)
        os.environ["CONTROL_PLANE_APPROVALS_LIVE"] = "1"
        with tempfile.TemporaryDirectory() as td, \
             mock.patch("brain.self_code.approve") as m_ap:
            res = decide_self_code("xxx", "yolo", confirmed=True,
                                   audit_dir=Path(td))
            self.assertFalse(res["result"]["ok"])
            m_ap.assert_not_called()


class TestLivePathUsesExistingSafeFunctions(unittest.TestCase):
    def setUp(self):
        _clean_cp_env(self)
        os.environ["CONTROL_PLANE_APPROVALS_LIVE"] = "1"

    def test_approve_delegates_to_self_code(self):
        with tempfile.TemporaryDirectory() as td, \
             mock.patch("brain.self_code.approve",
                        return_value={"ok": True, "reason": "اعمال شد"}) as m_ap:
            res = decide_self_code("pid1", "approve", confirmed=True,
                                   audit_dir=Path(td))
            m_ap.assert_called_once_with("pid1")
            self.assertTrue(res["result"]["ok"])
            self.assertGreaterEqual(res["policy_level"], 3)

    def test_reject_passes_note(self):
        with tempfile.TemporaryDirectory() as td, \
             mock.patch("brain.self_code.reject",
                        return_value={"ok": True, "reason": "رد شد"}) as m_rj:
            res = decide_self_code("pid2", "reject", note="نه", confirmed=True,
                                   audit_dir=Path(td))
            m_rj.assert_called_once_with("pid2", "نه")
            self.assertTrue(res["result"]["ok"])

    def test_bus_resolve_delegates_to_events(self):
        with tempfile.TemporaryDirectory() as td, \
             mock.patch("brain.events.resolve_latest_approval",
                        return_value=True) as m_ev:
            res = resolve_bus_approval("approved", confirmed=True,
                                       audit_dir=Path(td))
            m_ev.assert_called_once_with("approved")
            self.assertTrue(res["result"]["ok"])

    def test_bus_invalid_state_refused(self):
        with tempfile.TemporaryDirectory() as td, \
             mock.patch("brain.events.resolve_latest_approval") as m_ev:
            res = resolve_bus_approval("maybe", confirmed=True, audit_dir=Path(td))
            self.assertFalse(res["result"]["ok"])
            m_ev.assert_not_called()


class TestAuditTrail(unittest.TestCase):
    def test_appends_parseable_records(self):
        _clean_cp_env(self)
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            decide_self_code("a", "approve", confirmed=False, audit_dir=d)
            decide_self_code("b", "reject", confirmed=False, audit_dir=d)
            raw = (d / "approvals_log.jsonl").read_text(encoding="utf-8")
            lines = [json.loads(x) for x in raw.strip().splitlines()]
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0]["pid"], "a")
            self.assertEqual(lines[1]["decision"], "reject")
            self.assertEqual(audit_tail(1, audit_dir=d)[0]["pid"], "b")


class TestDiff(unittest.TestCase):
    def test_missing_proposal_diff_is_graceful(self):
        self.assertEqual(proposal_diff("no-such-pid-000"), "(دیف در دسترس نیست)")


class TestAuditOnError(unittest.TestCase):
    def test_delegate_exception_is_still_audited(self):
        """#19: اگر مسیرِ امن exception بدهد، تلاش باز هم باید در evidence-trail ثبت شود."""
        _clean_cp_env(self)
        os.environ["CONTROL_PLANE_APPROVALS_LIVE"] = "1"
        with tempfile.TemporaryDirectory() as td, \
             mock.patch("brain.self_code.approve",
                        side_effect=OSError("disk full mid-apply")):
            res = decide_self_code("pid1", "approve", confirmed=True, audit_dir=Path(td))
            self.assertFalse(res["result"]["ok"])
            trail = audit_tail(audit_dir=Path(td))
            self.assertEqual(len(trail), 1)             # ثبت شد، نه skip بی‌صدا
            self.assertFalse(trail[0]["result"]["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
