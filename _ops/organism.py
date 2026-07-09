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

sys.path.insert(0, str(_HERE))
try:
    import chrono      # noqa: E402 — Phase 1 (P-Chrono-1): بسترِ زمان/ضربان
except Exception as _e:  # noqa: BLE001 — chrono اختیاریِ additive است؛ متابولیسم نمی‌میرد
    chrono = None
    print(f"organism: chrono لود نشد ({_e}) — بدون ضربان ادامه می‌دهیم")

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
    # ── W-1..W-5 + neural wiring (پشتِ flag، paper-mode؛ پیش‌فرض خاموز = no regression)
    _wire = {}
    _doctor_inst = None
    _neural_stack = None
    _school_bridge = None
    _sensory_bus = None
    _bus = None
    _leg = None
    _live_loop = None
    _idea_graph = None
    _pacemaker = None   # P-L1: نمونهٔ Pacemaker (HLC/ackِ LeadLeg). در boot پر می‌شود.
    try:
        import wiring as _w
        _profile = _w.apply_profile()   # P-W3: paper-full → flagهای امن
        _wire = _w.wire_summary()
        _chan = _w.make_telegram_channel()   # auto-on اگر توکن
        _doctor_inst = _w.make_doctor(state_dir=str(opslib.STATE_DIR), channel=_chan)
        # W (P-W1): returnها را نگه دار، نه دور بریز — نخاع: bus + leg + LiveLoop
        _bus = _w.make_unified_bus()
        _leg = _w.make_lead_leg()
        _neural_stack = _w.make_neural_stack()   # W: neural ۸ ماژول
        # M (P-M2): اگر consolidation وصل است، SchoolBridge بساز (منبعِ awareness)
        if _wire.get("wire_consolidation"):
            _school_bridge = _w.make_school_bridge()
        # W (P-W2): آورانِ واقعی — اگر school/afferent وصل است، SensoryBus بساز
        if _wire.get("wire_school"):
            _sensory_bus = _w.make_sensory_bus()
        # I (P-I): موتورِ ایده-گراف — اگر ideas وصل است، IdeaGraph بساز
        if _wire.get("wire_ideas"):
            _idea_graph = _w.make_idea_graph()
        # W (P-W1): LiveLoop روی همان bus (نخاع). مغز و بدن روی یک حلقه.
        _live_loop = _w.make_live_loop(bus=_bus, leg=_leg, doctor=_doctor_inst,
                                       channel=_chan)
        if any(_wire.values()):
            opslib.heartbeat(f"organism wiring: {_wire}")
    except Exception as _e:  # noqa: BLE001 — wiring اختیاریِ additive
        opslib.alert([f"organism wiring failed (non-fatal): {_e}"])
    if chrono is not None:
        try:   # P-Chrono-1: pacemaker به‌عنوان background task (additive، fail-soft)
            _pacemaker = chrono.start_pacemaker_thread()   # P-L1: نمونه را نگه دار
        except Exception as e:  # noqa: BLE001
            opslib.alert([f"chrono pacemaker start failed: {e}"])
    next_epoch_at = 0.0
    last_daily = ""
    last_heartbeat = 0.0
    while True:
        _protective_skip = False   # آیا این تیک کارِ غیرضروری را skip کند؟ (protective-halt، enforceِ واقعی)
        try:
            if opslib.STOP_ORGANISM.exists() or opslib.halted() == "STOP(architect)":
                opslib.heartbeat("organism=HALT (STOP) — خروج تمیز")
                _write_state({"exited": "STOP"})
                return 0
            snap = telemetry.snapshot()
            conflicts = telemetry.reconcile(snap)
            now = time.time()
            # نبضِ chrono یک‌بار (استفادهٔ مشترک: neural + doctor + داشبورد)
            _cstat = None
            if chrono is not None:
                try:
                    _cstat = chrono.status()
                except Exception:  # noqa: BLE001
                    _cstat = None
            pulse = {"chrono": _cstat} if _cstat else {}
            # vital ناوردی ۳ (verdict 2026-07-07 #4): کهنگی germline — warn>2h، ERROR>26h/غایب
            lag = opslib.germline_lag_hours()
            germ = {"germline_lag_h": lag}
            if lag is None or lag > opslib.GERMLINE_ERR_H:
                germ["germline_alert"] = "ERROR"
                opslib.alert([f"germline_lag ERROR: {lag}h — بک‌آپ off-box کهنه/غایب (ناوردی ۳)"])
            elif lag > opslib.GERMLINE_WARN_H:
                germ["germline_alert"] = "warn"

            # ── S (S-fix-3): protective-override ابتدای کار محاسبه و enforce می‌شود (arXiv fix)
            # غیرقابل‌سرکوب و واقعی: تصمیم اینجا (پیش از epoch/fitness/doctor) گرفته می‌شود تا همان تیک
            # آن‌ها را جلو بگیرد (نه بعد از اجرا). sleep همیشه در انتهای tick → بدونِ busy-loop.
            prot_state = {}
            if _neural_stack is not None:
                try:
                    _beat_n = (_cstat.get("beat", 0) if _cstat else 0)
                    _neural_r = _w.neural_beat(_neural_stack, _beat_n, {
                        "rhythm": pulse.get("chrono", {}),
                        "budget": {"pct": snap["month"].get("musd", 0) / max(opslib.load_budgets().get("global", {}).get("cap_monthly", 30), 1)},
                        "spectral": {},
                        "sensory": {},
                    })
                    if _neural_r:
                        _prot = _w.protective_override(_neural_r)
                        if _prot.get("override") and not _prot.get("suppressible", True):
                            opslib.alert([f"NEURAL OVERRIDE: {_prot['reason']}"])
                            if _prot.get("action") == "protective_halt":
                                _protective_skip = True   # ← epoch/fitness/doctor این تیک skip می‌شوند
                                prot_state = {"protective_mode": True, "protective_reason": _prot["reason"]}
                                opslib.heartbeat(f"PROTECTIVE HALT: {_prot['reason']}")
                            elif _prot.get("action") == "throttle":
                                prot_state = {"protective_mode": "throttled", "protective_reason": _prot["reason"]}
                                next_epoch_at = now + 600  # ۱۰ دقیقه تأخیرِ epoch
                except Exception as _ne:  # noqa: BLE001 — §۴: خطای خاموش ممنوع
                    opslib.alert([f"neural wiring error (non-fatal): {type(_ne).__name__}: {_ne}"])

            # ── کارِ غیرضروری فقط وقتی protective-halt فعال نیست (enforceِ واقعیِ گیت)
            epoch_info = {}
            if not _protective_skip and now >= next_epoch_at:
                rec = governor_epoch.run_epoch()
                next_epoch_at = now + rec["next_epoch_minutes"] * 60
                epoch_info = {"last_epoch": rec["ts"],
                              "pressure": rec["pressure"],
                              "next_epoch_minutes": rec["next_epoch_minutes"]}
            daily = {}
            if not _protective_skip and opslib.today() != last_daily:
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
            # ── W-2: Doctor beat (غیرضروری → زیرِ همان گیت؛ STOP/protective مقدم)
            _doctor_result = None
            if not _protective_skip and _doctor_inst is not None and _cstat is not None:
                try:
                    _doctor_result = _w.doctor_beat(_doctor_inst, _cstat.get("beat", 0))
                except Exception:  # noqa: BLE001 — §۴: خطای خاموش ممنوع (Doctor نباید tick را بکشد)
                    opslib.alert(["doctor_beat error (non-fatal)"])
            # ── M (P-M2): canonical consolidation در حلقهٔ زنده (هر N beat، پشتِ flag)
            # یک مسیرِ حافظهٔ واحد — منبعِ School را می‌گنجاند. advisory فقط، صفر spend.
            if not _protective_skip and _neural_stack is not None and _cstat is not None:
                try:
                    _w.consolidation_beat(_neural_stack, school_bridge=_school_bridge,
                                          beat=_cstat.get("beat", 0))
                except Exception as _ce:  # noqa: BLE001 — §۴: خطای خاموش ممنون (consolidation نباید tick را بکشد)
                    opslib.alert([f"consolidation_beat error (non-fatal): {type(_ce).__name__}: {_ce}"])
            # ── W (P-W2): آورانِ واقعی — observationهای انتزاعی (ازِ snapshot، صفر PII)
            # → sensory_bus → school_bridge.learn_from → afferent_status. هر N beat، پشتِ flag.
            _afferent_status = None
            if not _protective_skip and _sensory_bus is not None and _cstat is not None:
                try:
                    _aff = _w.afferent_beat(_sensory_bus, school_bridge=_school_bridge,
                                            snap=snap, beat=_cstat.get("beat", 0))
                    if _aff and _aff.get("school_report"):
                        _afferent_status = _aff.get("sensory_status")
                except Exception as _ae:  # noqa: BLE001 — §۴: afferent نباید tick را بکشد
                    opslib.alert([f"afferent_beat error (non-fatal): {type(_ae).__name__}: {_ae}"])
            # ── W (P-W1): سیگنال‌های این tick را به bus (نخاع) منتشر کن.
            # مغز ← bus → subscriberها (LiveLoop.advisory_signals و غیره) فایر می‌شوند.
            # advisory فقط — هیچ effector. هر سیگنال در try مستقل (fail-soft، §۴).
            # W7: doctor_result واقعی را به bus منتقل کن (نه None).
            if not _protective_skip and _live_loop is not None:
                try:
                    _rh = pulse.get("chrono") or None   # rhythm/chrono state موجود این tick
                    _w.publish_tick_signals(_live_loop, beat=_cstat.get("beat", 0) if _cstat else 0,
                                            rhythm_state=_rh, spectral_result=None,
                                            afferent_status=_afferent_status,
                                            doctor_result=_doctor_result)
                except Exception as _pe:  # noqa: BLE001 — §۴: publish نباید tick را بکشد
                    opslib.alert([f"publish_tick_signals error (non-fatal): {type(_pe).__name__}: {_pe}"])
            # ── L (P-L1): LeadLeg حلقهٔ خودمختار — HLC محلی + ack + propose-only.
            # آبجکتِ _leg (از P-W1 نگه‌داشته‌شده) به LegHandle/HLC روی pacemaker.bus بسته می‌شود.
            # هر tick: HLC می‌زند + ack می‌دهد. هیچ effector؛ settle فقط از approval_channel.
            if not _protective_skip and _leg is not None and _pacemaker is not None:
                try:
                    _w.leg_beat(_leg, pacemaker=_pacemaker,
                                beat=_cstat.get("beat", 0) if _cstat else 0)
                except Exception as _le:  # noqa: BLE001 — §۴: leg نباید tick را بکشد
                    opslib.alert([f"leg_beat error (non-fatal): {type(_le).__name__}: {_le}"])
            # ── I (P-I): موتورِ ایده-گراف — هر N beat گرافِ vault را تحلیل کن.
            # هاب‌ها/خوشه‌ها/پل‌ها/یال‌های پیشنهادی. propose-only مطلق (هیچ effector).
            if not _protective_skip and _idea_graph is not None and _cstat is not None:
                try:
                    _w.idea_beat(_idea_graph, beat=_cstat.get("beat", 0))
                except Exception as _ie:  # noqa: BLE001 — §۴: idea نباید tick را بکشد
                    opslib.alert([f"idea_beat error (non-fatal): {type(_ie).__name__}: {_ie}"])

            if now - last_heartbeat > 3600:
                opslib.heartbeat(
                    f"organism=ok · ماه AU${snap['month']['aud']:.2f} · "
                    f"مشکوک متر صفر={snap['suspect_zero_total']} · "
                    f"{'CONFLICT×' + str(len(conflicts)) if conflicts else 'سالم'}"
                    f"{' · PROTECTIVE' if _protective_skip else ''}")
                last_heartbeat = now
            _write_state({"month": snap["month"], "today": snap["today"],
                          "suspect_zero_total": snap["suspect_zero_total"],
                          "conflicts": conflicts, **germ, **epoch_info, **daily,
                          **pulse, **prot_state,
                          "protective_skip": _protective_skip, "wiring": _wire})
        except KeyboardInterrupt:
            opslib.heartbeat("organism=STOP (KeyboardInterrupt)")
            return 0
        except Exception as e:  # noqa: BLE001 — خطای خاموش = شدیدترین باگ (منشور §۴)
            opslib.alert([f"organism tick error: {type(e).__name__}: {e}"])
            _write_state({"last_error": f"{type(e).__name__}: {e}"})
        time.sleep(TICK_SECONDS)


if __name__ == "__main__":
    sys.exit(main())
