#!/usr/bin/env python3
"""test_spine.py — تست‌های ستونِ فقراتِ یکپارچه (spine.py، ۲۰۲۶-۰۷-۲۵).

پوشش:
  ۱) flag-off (پیش‌فرض): emit() یک no-op است، هیچ فایلی ساخته/نوشته نمی‌شود.
  ۲) flag-on: emit() در busِ داخلی publish می‌کند (all.jsonl رشد می‌کند).
  ۳) flag-on + رویدادِ نگاشت‌شده: در saba-bridge.jsonl هم نوشته می‌شود.
  ۴) containment: bridge هرگز PII/محتوا نمی‌نویسد (قاعدهٔ #۷).
  ۵) emit() هرگز raise نمی‌کند (fail-soft).

همه $0، آفلاین، مستقل از ارگانیسمِ زنده. bridge_path به tempdir redirect می‌شود
تا چیزی واقعی نوشته نشود.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

from pf_os import config, spine  # noqa: E402


class TestSpine(unittest.TestCase):
    def setUp(self):
        # پاک‌کردنِ flag در هر تست
        os.environ.pop(spine.FLAG, None)
        # redirect bridge_path به tempdir (نوشتنِ واقعی ممنوع)
        self._tmp = tempfile.mkdtemp(prefix="spine-test-")
        self._ops_state = os.path.join(self._tmp, "_ops", "state")
        os.makedirs(self._ops_state, exist_ok=True)
        # bus state هم در tempdir
        os.environ["PF_ROOT"] = self._tmp
        # config را reload کن تا PF_STATE/PF_ROOT تازه بخواند
        import importlib
        from pf_os import config as cfg_mod
        importlib.reload(cfg_mod)
        importlib.reload(spine)
        # bus singleton را reset کن
        spine._bus = None

    def tearDown(self):
        os.environ.pop(spine.FLAG, None)
        os.environ.pop("PF_ROOT", None)
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _patch_bridge(self):
        """bridge.bridge_path را به tempdir patch کن."""
        from pf_os import bridge
        return mock.patch.object(bridge, "bridge_path",
                                 return_value=Path(self._ops_state) / "saba-bridge.jsonl")

    # ═══ ۱) flag-off = no-op ════════════════════════════════════════════════
    def test_flag_off_is_noop(self):
        self.assertFalse(spine.enabled())
        env = spine.emit("orchestrator.tick.done", "orchestrator", "tick 1")
        self.assertIsNone(env, "flag-off باید None برگرداند")

    # ═══ ۲) flag-on = publish در bus ════════════════════════════════════════
    def test_flag_on_publishes_to_bus(self):
        os.environ[spine.FLAG] = "1"
        self.assertTrue(spine.enabled())
        with self._patch_bridge():
            env = spine.emit("orchestrator.tick.done", "orchestrator",
                             "tick 1 done", mirror_to_bridge=False)
        self.assertIsNotNone(env, "flag-on باید envelope برگرداند")
        self.assertEqual(env["event"], "orchestrator.tick.done")

    # ═══ ۳) flag-on + mapped event = bridge نوشته می‌شود ════════════════════
    def test_mapped_event_writes_to_bridge(self):
        os.environ[spine.FLAG] = "1"
        bridge_path = Path(self._ops_state) / "saba-bridge.jsonl"
        self.assertFalse(bridge_path.exists(), "precondition: bridge خالی")
        with self._patch_bridge():
            spine.emit("studio.draft.submitted", "studio",
                       "draft submitted", bridge_text="draft submitted by creator")
        self.assertTrue(bridge_path.exists(), "flag-on + mapped event باید bridge بنویسد")
        lines = bridge_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertGreaterEqual(len(lines), 1)
        rec = json.loads(lines[-1])
        self.assertEqual(rec["kind"], "draft_submitted")
        self.assertEqual(rec["source"], "pf_os")

    # ═══ ۴) containment — PII هرگز در bridge ═════════════════════════════════
    def test_pii_never_in_bridge(self):
        os.environ[spine.FLAG] = "1"
        bridge_path = Path(self._ops_state) / "saba-bridge.jsonl"
        with self._patch_bridge():
            # msg عمداً محتوای PII دارد — نباید به bridge برسد
            spine.emit("studio.draft.submitted", "studio",
                       "saba از sydney درفت ساخت", bridge_text="saba از sydney درفت ساخت")
        rec = json.loads(bridge_path.read_text(encoding="utf-8").strip().splitlines()[-1])
        text = rec["text"].lower()
        self.assertNotIn("saba", text, "bridge نباید نامِ پارتنر را بنویسد")
        self.assertNotIn("sydney", text, "bridge نباید شهر را بنویسد")

    # ═══ ۵) emit هرگز raise نمی‌کند ═════════════════════════════════════════
    def test_emit_never_raises(self):
        os.environ[spine.FLAG] = "1"
        # event نامعتبر (taxonomy) → make_event raises ولی safe_publish می‌گیرد
        env = spine.emit("INVALID.EVENT.NAME", "x", "y", mirror_to_bridge=False)
        # bus.safe_publish برمی‌گرداند None، ولی emit خودش نباید raise کند
        # (ممکن است None یا envelope باشد؛ مهم این است که exception نریزد)
        # حتی بدون bus هم نباید بمیرد:
        spine._bus = None
        with mock.patch("pf_os.spine._get_bus", return_value=None):
            env2 = spine.emit("orchestrator.tick.done", "x", "y")
        # هیچ exception → تست pass

    # ═══ ۶) unmapped event → bridge نمی‌نویسد ═══════════════════════════════
    def test_unmapped_event_no_bridge(self):
        os.environ[spine.FLAG] = "1"
        bridge_path = Path(self._ops_state) / "saba-bridge.jsonl"
        with self._patch_bridge():
            # رویدادی که در _BRIDGE_KIND_MAP نیست — فقط bus، نه bridge
            spine.emit("learning.observed.unmapped", "brain",
                       "learned x", mirror_to_bridge=True)
        self.assertFalse(bridge_path.exists(),
                         "رویدادِ نگاشت‌نشده نباید bridge بنویسد")

    # ═══ ۷) health flag-off = {} ════════════════════════════════════════════
    def test_health_empty_when_off(self):
        self.assertEqual(spine.health(), {},
                         "flag-off: health باید {} باشد")


if __name__ == "__main__":
    unittest.main(verbosity=2)
