#!/usr/bin/env python3
"""test_bridge_api_loop.py — تست‌های فاز ۳/۴/۵: bridge, api, loop.

تمام تست‌ها $0، آفلاین، shadow-mode. هیچ port واقعی bind نمی‌شود (api با flag-off
یا non-blocking روی port موقت تست می‌شود).
"""
from __future__ import annotations

import http.client
import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

from pf_os import bridge as BR  # noqa: E402
from pf_os import config, saba_link as SL  # noqa: E402


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class TestBridge(unittest.TestCase):
    """پلِ pf_os → organism (saba-bridge.jsonl)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        # bridge به state واقعی _ops می‌نویسد — ولی برای تست مسیر را override کن
        self._orig = BR.bridge_path
        self._bridge_file = Path(self._tmp.name) / "saba-bridge.jsonl"
        BR.bridge_path = lambda: self._bridge_file

    def tearDown(self):
        BR.bridge_path = self._orig
        self._tmp.cleanup()

    def test_publish_returns_true(self):
        ok = BR.publish("notify", "test event")
        self.assertTrue(ok)
        self.assertTrue(self._bridge_file.exists())

    def test_publish_creates_jsonl_line(self):
        BR.publish("notify", "hello")
        line = self._bridge_file.read_text(encoding="utf-8").strip()
        rec = json.loads(line)
        self.assertEqual(rec["kind"], "notify")
        self.assertEqual(rec["text"], "hello")
        self.assertEqual(rec["source"], "pf_os")
        self.assertIn("ts", rec)

    def test_publish_rejects_unknown_kind(self):
        self.assertFalse(BR.publish("malicious_kind", "x"))

    def test_publish_scrubs_pii(self):
        """نامتغیرِ PII: نام در summary باید scrubbed شود."""
        ok = BR.publish("notify", "talking to ari about plan")
        self.assertTrue(ok)
        line = self._bridge_file.read_text().strip()
        rec = json.loads(line)
        # یا scrubbed شده یا text خالی
        self.assertNotIn("ari", rec["text"])

    def test_publish_scrubs_city(self):
        ok = BR.publish("notify", "in sydney today")
        self.assertTrue(ok)
        rec = json.loads(self._bridge_file.read_text().strip())
        self.assertNotIn("sydney", rec["text"])

    def test_notify_helpers(self):
        self.assertTrue(BR.notify_halt())
        self.assertTrue(BR.notify_resume())
        self.assertTrue(BR.notify_draft_submitted("DRAFT-001", 3))
        self.assertTrue(BR.notify_boundary("no body shots"))
        self.assertTrue(BR.notify_brain_tick(5, source="cortex"))
        self.assertTrue(BR.notify_kpi("2026-W29", gross_aud=42.5, posts=3))
        self.assertTrue(BR.notify_learning_observed("cozy-socks", n_obs=5))
        # همه باید در فایل باشند
        lines = [l for l in self._bridge_file.read_text().strip().split("\n") if l.strip()]
        self.assertEqual(len(lines), 7)

    def test_snapshot(self):
        BR.publish("notify", "first")
        BR.publish("halt", "creator halted")
        snap = BR.snapshot()
        self.assertTrue(snap["exists"])
        self.assertEqual(snap["lines_total"], 2)
        self.assertIsNotNone(snap["last_event"])
        self.assertEqual(snap["last_event"]["kind"], "halt")
        # نباید PII در snapshot باشد
        self.assertNotIn("ari", str(snap).lower())


class TestAPIServer(unittest.TestCase):
    """REST API — non-blocking روی port موقت."""

    @classmethod
    def setUpClass(cls):
        cls.port = _free_port()
        # flag را set کن
        os.environ[config.WIRE_API] = "1"
        os.environ["PF_OS_PORT"] = str(cls.port)
        # config reload — اما مقادیر import-time بودند؛ مستقیماً override
        config.API_PORT = cls.port
        from pf_os import api as API
        cls._api = API
        cls._orig_state = API._STATE
        API._STATE = None  # تازه state بساز
        # flag check در start_server — چون loop روی همان ماژول، باید مستقیم server بسازیم
        import http.server as _hs
        cls._server = API._sgl.ExclusiveHTTPServer(("127.0.0.1", cls.port), API._Handler)
        cls._thread = threading.Thread(target=cls._server.serve_forever, daemon=True)
        cls._thread.start()
        time.sleep(0.3)  # time to bind

    @classmethod
    def tearDownClass(cls):
        try:
            cls._server.shutdown()
            cls._server.server_close()
        except Exception:
            pass
        os.environ.pop(config.WIRE_API, None)
        cls._api._STATE = cls._orig_state

    def _get(self, path: str) -> tuple:
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        c.request("GET", path)
        r = c.getresponse()
        body = r.read().decode("utf-8")
        c.close()
        return r.status, body

    def _post(self, path: str, payload: dict) -> tuple:
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        c.request("POST", path, json.dumps(payload).encode("utf-8"),
                  {"Content-Type": "application/json"})
        r = c.getresponse()
        body = r.read().decode("utf-8")
        c.close()
        return r.status, body

    def test_health(self):
        code, body = self._get("/api/health")
        self.assertEqual(code, 200)
        d = json.loads(body)
        self.assertTrue(d["ok"])
        self.assertEqual(d["service"], "pf_os")
        self.assertIn("uptime_s", d)
        self.assertIn("brain", d)

    def test_landing_html(self):
        code, body = self._get("/")
        self.assertEqual(code, 200)
        self.assertIn("Project-F OS", body)
        self.assertIn("dir=\"rtl\"", body)

    def test_capabilities(self):
        code, body = self._get("/api/capabilities")
        self.assertEqual(code, 200)
        d = json.loads(body)
        self.assertIn("capabilities", d)
        ids = [c["id"] for c in d["capabilities"]]
        self.assertIn("brain.ask", ids)

    def test_octopus_bridge(self):
        code, body = self._get("/api/octopus/bridge")
        self.assertEqual(code, 200)
        d = json.loads(body)
        self.assertIn("exists", d)
        self.assertIn("lines_total", d)

    def test_saba_endpoint(self):
        code, body = self._get("/api/saba")
        self.assertEqual(code, 200)
        d = json.loads(body)
        self.assertIn("pending_drafts", d)
        self.assertIn("saba_halted", d)

    def test_learning(self):
        code, body = self._get("/api/learning")
        self.assertEqual(code, 200)
        d = json.loads(body)
        self.assertIn("available", d)

    def test_brain_ask(self):
        code, body = self._post("/api/brain/ask",
                                {"task": "daily", "prompt": "test prompt"})
        # ممکن 200 یا 503 (cortex off → fallback)
        self.assertIn(code, (200, 503))
        d = json.loads(body)
        self.assertIn("ok", d)
        self.assertIn("source", d)

    def test_brain_ask_pii_rejected(self):
        """prompt با PII باید scrub شود (نامتغیرِ PII در API)."""
        code, body = self._post("/api/brain/ask",
                                {"task": "daily", "prompt": "tell ari the plan"})
        d = json.loads(body)
        self.assertFalse(d["ok"])
        self.assertIn("scrub", d.get("reason", ""))

    def test_not_found(self):
        code, body = self._get("/api/nonexistent")
        self.assertEqual(code, 404)

    def test_draft_submit_requires_title(self):
        code, body = self._post("/api/draft/submit", {})
        self.assertEqual(code, 400)

    def test_draft_submit_with_title(self):
        code, body = self._post("/api/draft/submit", {"title": "test draft"})
        self.assertEqual(code, 200)
        d = json.loads(body)
        self.assertTrue(d["ok"])


class TestAPISingletonProtection(unittest.TestCase):
    """port تکراری نباید bind شود — ExclusiveHTTPServer باید دومین را رد کنه."""

    def test_second_bind_fails(self):
        port = _free_port()
        from pf_os import singleton as SGL
        import http.server
        # first bind
        srv1 = SGL.ExclusiveHTTPServer(
            ("127.0.0.1", port), http.server.BaseHTTPRequestHandler)
        try:
            # second bind on same port باید شکست بخورد (OSError)
            with self.assertRaises(OSError):
                srv2 = SGL.ExclusiveHTTPServer(
                    ("127.0.0.1", port), http.server.BaseHTTPRequestHandler)
        finally:
            srv1.server_close()


class TestLoop(unittest.TestCase):
    """tick loop — non-blocking، flag-controlled."""

    def setUp(self):
        # studio به tempdir برای isolation
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["PF_STUDIO_DIR"] = self._tmp.name

    def tearDown(self):
        os.environ.pop("PF_STUDIO_DIR", None)
        self._tmp.cleanup()

    def test_tick_once_returns_dict(self):
        from pf_os import loop as LP
        runner = LP.PFTickRunner(tick_seconds=0.01)
        r = runner.tick_once()
        self.assertIsInstance(r, dict)
        self.assertIn("tick", r)
        self.assertEqual(r["tick"], 1)
        self.assertIn("stages", r)
        self.assertGreater(len(r["stages"]), 0)
        # هر stage باید ok یا error داشته باشه
        for s in r["stages"]:
            self.assertIn("name", s)
            self.assertIn("ok", s)

    def test_tick_increments(self):
        from pf_os import loop as LP
        runner = LP.PFTickRunner(tick_seconds=0.01)
        runner.tick_once()
        runner.tick_once()
        runner.tick_once()
        self.assertEqual(runner.tick_n, 3)

    def test_stop_file_stops(self):
        from pf_os import loop as LP
        runner = LP.PFTickRunner(tick_seconds=0.01)
        # STOP file را بساز
        stop_file = Path(config.PF_STATE) / "STOP-PFOS"
        config.ensure_pf_state()
        stop_file.write_text("test")
        try:
            self.assertTrue(runner._should_stop())
        finally:
            stop_file.unlink(missing_ok=True)

    def test_stop_via_method(self):
        from pf_os import loop as LP
        runner = LP.PFTickRunner(tick_seconds=0.01)
        self.assertFalse(runner._should_stop())
        runner.stop()
        self.assertTrue(runner._should_stop())

    def test_flag_off_start_background_returns_false(self):
        """اگر flag off باشد، start_background False برمی‌گرداند."""
        from pf_os import loop as LP
        os.environ.pop(config.WIRE_LOOP, None)
        runner = LP.PFTickRunner()
        self.assertFalse(runner.start_background())


class TestLoopRoutesNewDraftToBrain(unittest.TestCase):
    """fix #2 (metaphor → REAL): tick_once باید درفتِ جدید را واقعاً به مغز route کند.

    قبلاً `new = cur_pending > last` محاسبه و بلافاصله دور ریخته می‌شد؛
    on_new_draft هرگز صدا زده نمی‌شد و brain_tick با یک رشته‌ی هاردکد مغز را
    می‌زد. حالا درفتِ جدیدِ صبا واقعاً به مغز می‌رسد
    (route_new_draft → on_new_draft → brain.respond_to_saba).

    بریج به tempdir ری‌دایرکت می‌شود تا هیچ نوشتنی به _ops/state انجام نشود.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["PF_STUDIO_DIR"] = self._tmp.name
        # ایزوله‌کردنِ بریج (هرگز به _ops واقعی ننویس)
        self._orig_bridge = BR.bridge_path
        self._bridge_file = Path(self._tmp.name) / "saba-bridge.jsonl"
        BR.bridge_path = lambda: self._bridge_file

    def tearDown(self):
        BR.bridge_path = self._orig_bridge
        os.environ.pop("PF_STUDIO_DIR", None)
        self._tmp.cleanup()

    def _write_pending(self, drafts):
        (Path(self._tmp.name) / "drafts.json").write_text(
            json.dumps(drafts), encoding="utf-8")

    def _acks(self):
        p = Path(self._tmp.name) / "for_saba.json"
        if not p.exists():
            return []
        return [m for m in json.loads(p.read_text(encoding="utf-8"))
                if m.get("kind") == "draft_ack"]

    def test_new_draft_routes_to_brain(self):
        from pf_os import loop as LP

        class SpyBrain:
            def __init__(self):
                self.respond_calls, self.classify_calls = [], []

            def _classify_saba_intent(self, text):
                self.classify_calls.append(text)
                return "trend"

            def respond_to_saba(self, text):
                self.respond_calls.append(text)
                return "TREND_ADVICE_FROM_BRAIN"

            def think(self, task, prompt, max_tokens=300):
                class _R:
                    source = "heuristic"
                return _R()

        spy = SpyBrain()
        runner = LP.PFTickRunner(brain=spy, tick_seconds=0.01)
        # tick 1: هیچ درفتی نیست → baseline (last_pending=0)؛ new=False؛ هیچ route
        r1 = runner.tick_once()
        self.assertEqual(len(spy.respond_calls), 0)
        self.assertFalse(r1.get("new_draft_detected"))
        # درفتِ pending اضافه کن
        self._write_pending([{"draft_id": "D1", "title": "seasonal trend idea",
                              "status": "pending"}])
        # tick 2: pending 0→1 → new=True → route → مغز *واقعاً* صدا زده می‌شود
        r2 = runner.tick_once()
        self.assertTrue(r2.get("new_draft_detected"))
        self.assertEqual(len(spy.respond_calls), 1,
                         "brain.respond_to_saba must be called for the new draft")
        self.assertIn("seasonal trend", spy.respond_calls[0])  # محتوای واقعیِ درفت
        # stage route_new_draft وجود دارد و routed است
        stage = next((s for s in r2["stages"] if s["name"] == "route_new_draft"), None)
        self.assertIsNotNone(stage)
        self.assertTrue(stage["ok"])
        self.assertEqual(stage.get("result"), "routed")
        # پیامِ draft_ack با پاسخِ واقعیِ مغز به for_saba.json رفت
        acks = self._acks()
        self.assertEqual(len(acks), 1)
        self.assertIn("TREND_ADVICE_FROM_BRAIN", acks[0]["text"])

    def test_no_new_draft_is_noop(self):
        from pf_os import loop as LP
        runner = LP.PFTickRunner(tick_seconds=0.01)  # default BrainCore
        r = runner.tick_once()  # tick اول: new همیشه False
        stage = next((s for s in r["stages"] if s["name"] == "route_new_draft"), None)
        self.assertIsNotNone(stage)
        self.assertTrue(stage["ok"])
        self.assertEqual(stage.get("result"), "no-new-draft")

    def test_route_is_fail_soft_when_brain_explodes(self):
        """HARD RULE: یک stage خطا نباید loop را بکُشد. مغزِ منفجرشونده →
        on_new_draft داخلِ خودش fail-soft است و پیامِ صادقانه‌ی پیش‌فرض می‌رود."""
        from pf_os import loop as LP

        class BoomBrain:
            def _classify_saba_intent(self, text):
                raise RuntimeError("boom")

            def respond_to_saba(self, text):
                raise RuntimeError("boom")

            def think(self, task, prompt, max_tokens=300):
                class _R:
                    source = "heuristic"
                return _R()

        runner = LP.PFTickRunner(brain=BoomBrain(), tick_seconds=0.01)
        runner.tick_once()  # baseline
        self._write_pending([{"draft_id": "D1", "title": "x", "status": "pending"}])
        r = runner.tick_once()  # نباید exception بدهد
        self.assertIsInstance(r, dict)
        stage = next((s for s in r["stages"] if s["name"] == "route_new_draft"), None)
        self.assertIsNotNone(stage)
        self.assertTrue(stage["ok"])  # loop زنده ماند
        # پیامِ صادقانه‌ی پیش‌فرض رفت (نه دروغِ «مغز محاسبه کرد»)
        acks = self._acks()
        self.assertEqual(len(acks), 1)
        self.assertNotIn("مغز داره بهترین قیمت/زمان", acks[0]["text"])


if __name__ == "__main__":
    unittest.main()
