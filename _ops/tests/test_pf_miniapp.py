#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_pf_miniapp.py — گاردهای کارت‌های Project-F در Mini App (PROP-D5 فاز ۱).

چهار چیز را می‌سنجد که اگر بشکنند، شکستنشان **بی‌صدا** است:
  ۱) flag-off = مسیر اصلاً وجود ندارد (404) و هیچ فایلی خوانده نمی‌شود.
  ۲) دیوارِ auth: بدونِ initData ِ معتبر هیچ بایتی از PF بیرون نمی‌رود (403).
  ۳) **content-free**: هیچ متنِ درفت/کپشن/بدنهٔ DM از مرزِ پوشهٔ پروژه عبور
     نمی‌کند — با فیکسچرِ واقعی‌شکل که عمداً متنِ قابل‌ردیابی دارد سنجیده
     می‌شود (قاعدهٔ قفل‌شدهٔ #۷).
  ۴) سه‌حالتیِ صادق: فایلِ غایب/خراب = `unknown`، نه صفرِ جعلی و نه «امن».

هرمتیک: همهٔ مسیرها به tmp می‌روند؛ هیچ فایلِ زندهٔ پروژه لمس/نوشته نمی‌شود.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pf_miniapp  # noqa: E402
import miniapp_gateway as gw  # noqa: E402

# متن‌های تله: اگر هر کدام در خروجیِ API ظاهر شوند، مرزِ containment شکسته است
CANARY_HOOK = "CANARY-HOOK-do-not-leak-9f3a"
CANARY_DM = "CANARY-DM-body-do-not-leak-7b21"
CANARY_CAPTION = "CANARY-CAPTION-do-not-leak-4c88"


def _make_pf_tree(root: Path) -> Path:
    """درختِ کوچکِ شبیهِ پروژه با دادهٔ واقعی‌شکل (و متنِ تله)."""
    pf = root / "03 - Projects" / "onlyfans-fixture"
    (pf / "brain").mkdir(parents=True, exist_ok=True)
    (pf / "langar").mkdir(parents=True, exist_ok=True)
    (pf / "studio").mkdir(parents=True, exist_ok=True)
    (pf / "00 - Control").mkdir(parents=True, exist_ok=True)

    (pf / "brain" / "acq_queue.json").write_text(json.dumps([
        {"id": "acq_aaa111", "status": "drafted", "hook": CANARY_HOOK,
         "caption": CANARY_CAPTION, "channel": "reddit"},
        {"id": "acq_bbb222", "status": "ready", "hook": CANARY_HOOK,
         "channel": "x", "flagged": True},
    ], ensure_ascii=False), encoding="utf-8")

    (pf / "brain" / "dm_queue.json").write_text(json.dumps([
        {"id": "DM-abc123", "status": "pending_review", "body": CANARY_DM,
         "kind": "welcome", "channel": "of"},
    ], ensure_ascii=False), encoding="utf-8")

    (pf / "studio" / "drafts.json").write_text(json.dumps([
        {"id": "d-1", "status": "pending", "title": CANARY_CAPTION},
        {"id": "d-2", "status": "approved", "title": CANARY_CAPTION},
    ], ensure_ascii=False), encoding="utf-8")

    (pf / "langar" / "channel_locks.json").write_text(json.dumps({
        "full_stop": False,
        "channels": {"reddit": {"warnings": [{"reason": "test"}], "locked": True}},
    }, ensure_ascii=False), encoding="utf-8")

    (pf / "langar" / "reddit_state.json").write_text(json.dumps({
        "reddit_karma": 25, "threshold_met": True,
    }, ensure_ascii=False), encoding="utf-8")

    (pf / "langar" / "kpi.json").write_text(json.dumps({
        "weeks": [{"week_start": "2026-07-27", "clicks": 120, "follows": 18,
                   "free_subs": 20, "paid_conversions": 1, "ppv_unlocks": 4,
                   "delivery_rate": 0.9, "revenue_usd": 12.5, "posts": 9}],
    }, ensure_ascii=False), encoding="utf-8")

    (pf / "PROJECT-F-CONTROL-MANIFEST.json").write_text(json.dumps({
        "status_snapshot": {"execution_state": "ZERO execution",
                            "primary_blocker": "GATE 0 open",
                            "security_gate": "closed",
                            "pending_human_verdicts": 11},
        "gates": {"G0": {"condition": "Branch A", "status": "OPEN", "eval": "now"}},
        "open_pending_verdicts": ["GATE 0 closure"],
    }, ensure_ascii=False), encoding="utf-8")
    return pf


class TestPfMiniappFlag(unittest.TestCase):
    def setUp(self):
        self._orig = os.environ.get(pf_miniapp.FLAG)

    def tearDown(self):
        if self._orig is None:
            os.environ.pop(pf_miniapp.FLAG, None)
        else:
            os.environ[pf_miniapp.FLAG] = self._orig

    def test_flag_off_is_404_for_every_path(self):
        os.environ[pf_miniapp.FLAG] = "0"
        for p in sorted(pf_miniapp.PATHS):
            st, body, _ = pf_miniapp.dispatch_api(p)
            self.assertEqual(st, 404, f"{p} با فلگِ خاموش نباید داده بدهد")
            self.assertNotIn(b"drafts_count", body)

    def test_flag_only_literal_one(self):
        for val in ("true", "yes", "on", "2", ""):
            os.environ[pf_miniapp.FLAG] = val
            self.assertFalse(pf_miniapp.enabled(), f"«{val}» نباید روشن حساب شود")
        os.environ[pf_miniapp.FLAG] = "1"
        self.assertTrue(pf_miniapp.enabled())


class TestPfMiniappData(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.pf = _make_pf_tree(self.root)
        self._orig = os.environ.get(pf_miniapp.FLAG)
        os.environ[pf_miniapp.FLAG] = "1"

    def tearDown(self):
        if self._orig is None:
            os.environ.pop(pf_miniapp.FLAG, None)
        else:
            os.environ[pf_miniapp.FLAG] = self._orig
        self._tmp.cleanup()

    def _all_payloads(self) -> str:
        out = []
        for fn in (pf_miniapp.get_pf_status, pf_miniapp.get_pf_gates,
                   pf_miniapp.get_pf_queue, pf_miniapp.get_pf_kpi,
                   pf_miniapp.get_pf_guards, pf_miniapp.get_pf_capabilities):
            out.append(json.dumps(fn(self.pf), ensure_ascii=False, default=str))
        return "\n".join(out)

    # ── ۳) content-free: قلبِ قاعدهٔ #۷ ──────────────────────────────────
    def test_no_draft_text_crosses_the_boundary(self):
        blob = self._all_payloads()
        for canary in (CANARY_HOOK, CANARY_DM, CANARY_CAPTION):
            self.assertNotIn(canary, blob,
                             "متنِ محتوا از مرزِ پوشهٔ پروژه بیرون رفت — نقضِ قاعدهٔ #۷")

    def test_ids_pass_but_only_id_shaped(self):
        q = pf_miniapp.get_pf_queue(self.pf)
        self.assertIn("acq_aaa111", q["acquisition"]["ids"])
        self.assertEqual(q["acquisition"]["counts"], {"drafted": 1, "ready": 1})
        self.assertEqual(q["acquisition"]["flagged"], 1)
        self.assertEqual(q["dm"]["counts"], {"pending_review": 1})

    # ── ۱/۴) شمارش و سه‌حالتیِ صادق ───────────────────────────────────
    def test_status_counts_real_data(self):
        s = pf_miniapp.get_pf_status(self.pf)
        self.assertEqual(s["drafts_count"], 1)      # فقط pending
        self.assertEqual(s["dm_pending"], 1)
        self.assertEqual(s["acq_ready"], 1)
        self.assertIs(s["full_stop"], False)
        self.assertIs(s["karma_met"], True)
        self.assertEqual(s["unknown_fields"], ["beat:missing"])
        self.assertIs(s["outward_execution"], False)

    def test_missing_files_are_unknown_not_safe_zero(self):
        empty = self.root / "empty-project"
        empty.mkdir()
        s = pf_miniapp.get_pf_status(empty)
        self.assertIsNone(s["full_stop"], "نبودِ فایل نباید «قفلی نیست» معنی شود")
        self.assertIsNone(s["karma_met"])
        self.assertIsNone(s["drafts_count"])
        self.assertTrue(any(u.startswith("full_stop:") for u in s["unknown_fields"]))
        g = pf_miniapp.get_pf_guards(empty)
        self.assertEqual(g["channel_locks"]["status"], "unknown")
        k = pf_miniapp.get_pf_kpi(empty)
        self.assertEqual(k["status"], "unknown")

    def test_corrupt_json_is_unknown(self):
        bad = self.root / "bad-project"
        (bad / "langar").mkdir(parents=True)
        (bad / "langar" / "channel_locks.json").write_text("{not json", encoding="utf-8")
        s = pf_miniapp.get_pf_status(bad)
        self.assertIsNone(s["full_stop"])
        self.assertTrue(any("corrupt" in u for u in s["unknown_fields"]))

    def test_kpi_lights_follow_spec_thresholds(self):
        k = pf_miniapp.get_pf_kpi(self.pf)
        self.assertEqual(k["status"], "ok")
        # clicks=120 → بینِ قرمزِ ۱۰۰ و سبزِ ۲۰۰ ⇒ amber
        self.assertEqual(k["lights"]["clicks_cumulative"]["light"], "amber")
        # follows/clicks = 15% ≥ ۱۰ ⇒ green
        self.assertEqual(k["lights"]["click_to_follow_pct"]["light"], "green")
        # paid/free = 5% ≥ ۵ ⇒ green
        self.assertEqual(k["lights"]["free_to_paid_pct"]["light"], "green")
        # delivery 0.9 → ۹۰٪ ⇒ green
        self.assertEqual(k["lights"]["delivery_rate_pct"]["light"], "green")

    def test_capabilities_are_locked_without_human_stamp(self):
        c = pf_miniapp.get_pf_capabilities(self.pf)
        self.assertFalse(c["outward_allowed"], "بدونِ مهرِ انسانی نباید باز باشد")
        self.assertTrue(c["capabilities"], "فهرستِ قابلیت خالی = دکمهٔ نامرئی")
        for cap in c["capabilities"]:
            self.assertFalse(cap["executable"])
            self.assertTrue(cap["reason"], "هر قفل باید دلیل داشته باشد")

    def test_gates_read_from_manifest(self):
        g = pf_miniapp.get_pf_gates(self.pf)
        self.assertEqual(g["status"], "ok")
        self.assertEqual(g["pending_human_verdicts"], 11)
        self.assertIn("G0", g["gates"])
        self.assertFalse(g["gate_stamp_go_file"])
        self.assertFalse(g["outward_allowed"])

    def test_stale_snapshot_is_marked(self):
        old = self.pf / "brain" / "acq_queue.json"
        past = time.time() - (pf_miniapp.STALE_AFTER_S + 600)
        os.utime(old, (past, past))
        s = pf_miniapp.get_pf_status(self.pf)
        self.assertTrue(s["freshness"]["acq"]["stale"],
                        "snapshot ِ کهنه باید کهنه اعلام شود، نه سبز")


class TestPfGatewayWall(unittest.TestCase):
    """دیوارِ 8774: هیچ بایتی از PF بدونِ initData ِ معتبرِ مالک بیرون نرود."""

    OWNER = "424242"
    TOKEN = "123456:TEST-TOKEN-not-a-real-secret"

    def setUp(self):
        self._env = {k: os.environ.get(k) for k in
                     ("TG_CENTER_BOT_TOKEN", "TELEGRAM_OWNER_CHAT_ID", pf_miniapp.FLAG)}
        os.environ["TG_CENTER_BOT_TOKEN"] = self.TOKEN
        os.environ["TELEGRAM_OWNER_CHAT_ID"] = self.OWNER
        os.environ[pf_miniapp.FLAG] = "1"
        self._stop = gw._stopped
        gw._stopped = lambda: False        # کلیدِ کشتارِ زنده نباید تست را ببندد

    def tearDown(self):
        gw._stopped = self._stop
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _init_data(self, uid: str, age_s: float = 5.0) -> str:
        auth = int(time.time() - age_s)
        user = json.dumps({"id": int(uid)}, separators=(",", ":"))
        fields = {"auth_date": str(auth), "user": user}
        check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
        secret = hmac.new(b"WebAppData", self.TOKEN.encode(), hashlib.sha256).digest()
        h = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        from urllib.parse import urlencode
        return urlencode({**fields, "hash": h})

    def test_no_initdata_is_403(self):
        st, body, _ = gw.handle("GET", "/api/pf/status", {})
        self.assertEqual(st, 403)
        self.assertEqual(body, b"", "بدنهٔ 403 باید خالی باشد (بدونِ نشتِ اطلاعات)")

    def test_forged_initdata_is_403(self):
        forged = self._init_data(self.OWNER)[:-4] + "dead"
        st, _, _ = gw.handle("GET", "/api/pf/status", {"X-Tg-Init-Data": forged})
        self.assertEqual(st, 403)

    def test_stranger_user_is_403(self):
        st, _, _ = gw.handle("GET", "/api/pf/status",
                             {"X-Tg-Init-Data": self._init_data("999999")})
        self.assertEqual(st, 403)

    def test_expired_initdata_is_403(self):
        old = self._init_data(self.OWNER, age_s=gw.AUTH_MAX_AGE_S + 120)
        st, _, _ = gw.handle("GET", "/api/pf/status", {"X-Tg-Init-Data": old})
        self.assertEqual(st, 403)

    def test_valid_owner_gets_data(self):
        st, body, ctype = gw.handle("GET", "/api/pf/status",
                                    {"X-Tg-Init-Data": self._init_data(self.OWNER)})
        self.assertEqual(st, 200)
        self.assertIn("application/json", ctype)
        data = json.loads(body.decode("utf-8"))
        self.assertIn("drafts_count", data)
        self.assertIs(data["outward_execution"], False)

    def test_post_to_pf_path_is_rejected(self):
        """مسیرهای PF فقط خواندنی‌اند — هیچ POST ی نباید به آن‌ها برسد."""
        st, _, _ = gw.handle("POST", "/api/pf/status",
                             {"X-Tg-Init-Data": self._init_data(self.OWNER)})
        self.assertEqual(st, 405)

    def test_flag_off_gives_404_even_for_owner(self):
        os.environ[pf_miniapp.FLAG] = "0"
        st, _, _ = gw.handle("GET", "/api/pf/status",
                             {"X-Tg-Init-Data": self._init_data(self.OWNER)})
        self.assertEqual(st, 404)

    def test_stop_file_wins_over_everything(self):
        gw._stopped = lambda: True
        st, _, _ = gw.handle("GET", "/api/pf/status",
                             {"X-Tg-Init-Data": self._init_data(self.OWNER)})
        self.assertEqual(st, 503)


if __name__ == "__main__":
    unittest.main(verbosity=2)
