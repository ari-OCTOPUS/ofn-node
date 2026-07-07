#!/usr/bin/env python3
"""
organism.py — حلقهٔ واحد همیشه-روشن ارگانیسم (آناتومی ⊕ فیزیولوژی ⊕ متابولیسم).

این تنها پروسه‌ای است که برای «یک ماه لپ‌تاپ روشن، دیتا جمع کن» لازم است روشن بماند.
هر تیک (سبک، $0):
  1) kill-check: STOP (architect) / STOP-ORGANISM / STOP-METABOLIC
  2) تلمتری واحد + تطبیق (FREEZE/CONFLICT در صورت ناسازگاری — I3)
  3) اگر epoch آلوستاتیک سررسید: governor_epoch (سایه؛ dry پیش‌فرض، $0)
  4) روزی یک‌بار: fitness + replication (سایه) + NOTE(ORGANISM_DAILY) به ledger
  5) ساعتی یک‌بار: یک سطر heartbeat (فقط append — قرارداد governor_shadow)
  6) state ماشین‌خوان برای UI: _ops/state/ORGANISM-STATE.json + HTTP فقط‌خواندنی

قفل تک‌نمونه + سرور وضعیت: bind انحصاری 127.0.0.1:8771 (env: ORGANISM_PORT).
  8768 قفل مغز (app.py) و 8770 داشبورد است — به آن‌ها دست نمی‌زنیم.
  GET /               → صفحهٔ وضعیت RTL مینیمال (پایهٔ UI نسخهٔ بعد)
  GET /api/organism   → ORGANISM-STATE.json
  GET /api/telemetry  → telemetry-latest.json
  GET /api/fitness    → fitness-latest.json
  GET /api/replication→ replication-latest.json

این پروسه هیچ call پولی نمی‌زند مگر مود LLM گاورنر با گیت دوقفلهٔ مالک باز شده باشد؛
حتی آن‌موقع هم هر call از organ_gate → budget_gate می‌گذرد (I2). خطای خاموش ممنوع:
هر استثنا → governor-alerts.md + ادامهٔ حلقه (مرگ حلقه فقط با STOP).
"""
from __future__ import annotations

import json
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "budget"))
import opslib          # noqa: E402
import telemetry       # noqa: E402
import governor_epoch  # noqa: E402
import fitness         # noqa: E402
import replication     # noqa: E402

PORT = 8771
TICK_SECONDS = 300           # تیک سبک ۵ دقیقه‌ای؛ epoch واقعی آلوستاتیک است
STATE_FILE = opslib.STATE_DIR / "ORGANISM-STATE.json"
START_TS = opslib.now_iso()


class _ExclusiveHTTPServer(ThreadingHTTPServer):
    """سرور وضعیت = خودِ قفل تک‌نمونه. تلهٔ شناختهٔ ویندوز (جلسه ۱۹): http.server
    پیش‌فرض SO_REUSEADDR دارد و double-bind ساکت می‌سازد → انحصاری‌اش می‌کنیم."""
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class _StatusHandler(BaseHTTPRequestHandler):
    ROUTES = {
        "/api/organism": STATE_FILE,
        "/api/telemetry": opslib.STATE_DIR / "telemetry-latest.json",
        "/api/fitness": opslib.STATE_DIR / "fitness-latest.json",
        "/api/replication": opslib.STATE_DIR / "replication-latest.json",
    }

    def do_GET(self):  # noqa: N802
        if self.path in self.ROUTES:
            p = self.ROUTES[self.path]
            body = p.read_bytes() if p.exists() else b"{}"
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/":
            try:
                st = json.loads(STATE_FILE.read_text("utf-8")) if STATE_FILE.exists() else {}
            except (OSError, ValueError):
                st = {}
            html = ("<!doctype html><html dir='rtl' lang='fa'><meta charset='utf-8'>"
                    "<title>Organism</title><body style='font-family:Tahoma;padding:2em'>"
                    "<h2>🫀 ارگانیسم — وضعیت زنده</h2>"
                    f"<pre style='direction:ltr;text-align:left'>{json.dumps(st, ensure_ascii=False, indent=2)}</pre>"
                    "<p>API: /api/organism · /api/telemetry · /api/fitness · /api/replication</p>"
                    "</body></html>")
            b = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *a):  # ساکت — لاگ HTTP لازم نیست
        pass


def _serve(port: int) -> _ExclusiveHTTPServer:
    """bind انحصاری؛ OSError یعنی نمونهٔ دیگری زنده است (قفل + UI در یک شیء)."""
    srv = _ExclusiveHTTPServer(("127.0.0.1", port), _StatusHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _write_state(extra: dict) -> None:
    state = {
        "ts": opslib.now_iso(), "started": START_TS,
        "epoch_mode": "allostatic — تابع فشار (نه clock)",
        "halted": opslib.halted(), "frozen": opslib.frozen(),
        "stop_organism": opslib.STOP_ORGANISM.exists(),
        **extra,
    }
    try:
        with opslib.LockedJson(STATE_FILE) as lj:
            lj.write(state)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"organism state write failed: {e}"])


def main() -> int:
    import os
    port = int(os.environ.get("ORGANISM_PORT", PORT))
    try:
        _serve(port)   # bind انحصاری = قفل تک‌نمونه + endpoint وضعیت، هم‌زمان
    except OSError:
        print(f"organism: نمونهٔ دیگری روی 127.0.0.1:{port} روشن است — خروج تمیز.")
        return 0

    print(f"organism: زنده روی http://127.0.0.1:{port} — kill تمیز: فایل _ops/STOP-ORGANISM")
    opslib.heartbeat(f"organism=START port={port}")
    next_epoch_at = 0.0
    last_daily = ""
    last_heartbeat = 0.0
    while True:
        try:
            if opslib.STOP_ORGANISM.exists() or opslib.halted() == "STOP(architect)":
                opslib.heartbeat("organism=HALT (STOP) — خروج تمیز")
                _write_state({"exited": "STOP"})
                return 0
            snap = telemetry.snapshot()
            conflicts = telemetry.reconcile(snap)
            epoch_info = {}
            now = time.time()
            if now >= next_epoch_at:
                rec = governor_epoch.run_epoch()
                next_epoch_at = now + rec["next_epoch_minutes"] * 60
                epoch_info = {"last_epoch": rec["ts"],
                              "pressure": rec["pressure"],
                              "next_epoch_minutes": rec["next_epoch_minutes"]}
            daily = {}
            if opslib.today() != last_daily:
                fit = fitness.compute()
                rep = replication.evaluate()
                last_daily = opslib.today()
                daily = {"fitness_authoritative": fit["authoritative"],
                         "sigma": rep["sigma"]["sigma_effective"],
                         "sigma_zone": rep["sigma"]["zone"]}
                opslib.ledger_note("ORGANISM_DAILY", {
                    "month_aud": snap["month"]["aud"],
                    "suspects": snap["suspect_zero_total"],
                    "sigma": rep["sigma"]["sigma_effective"],
                    "conflicts": len(conflicts)}, actor="organism")
            if now - last_heartbeat > 3600:
                opslib.heartbeat(
                    f"organism=ok · ماه AU${snap['month']['aud']:.2f} · "
                    f"مشکوک متر صفر={snap['suspect_zero_total']} · "
                    f"{'CONFLICT×' + str(len(conflicts)) if conflicts else 'سالم'}")
                last_heartbeat = now
            _write_state({"month": snap["month"], "today": snap["today"],
                          "suspect_zero_total": snap["suspect_zero_total"],
                          "conflicts": conflicts, **epoch_info, **daily})
        except KeyboardInterrupt:
            opslib.heartbeat("organism=STOP (KeyboardInterrupt)")
            return 0
        except Exception as e:  # noqa: BLE001 — خطای خاموش = شدیدترین باگ (منشور §۴)
            opslib.alert([f"organism tick error: {type(e).__name__}: {e}"])
            _write_state({"last_error": f"{type(e).__name__}: {e}"})
        time.sleep(TICK_SECONDS)


if __name__ == "__main__":
    sys.exit(main())
