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
from contextlib import contextmanager

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

try:   # R-12 (audit): correlation_idِ run-scoped — یک id برای کلِ emitهای یک tick
    import events as _events   # noqa: E402
except Exception as _ee:  # noqa: BLE001 — additive؛ نبودش نباید متابولیسم را بکشد
    _events = None
    print(f"organism: events لود نشد ({_ee}) — بدون correlation_idِ run-scoped ادامه می‌دهیم")

try:   # stage-3 گام ۱ (2026-07-24): probeٔ اندازه‌گیریِ مدتِ فازها — additive
    import tick_timing as _tt  # noqa: E402
except Exception:  # noqa: BLE001 — probe نباید متابولیسم را بکشد
    _tt = None

PORT = 8771
TICK_SECONDS = 300           # تیک سبک ۵ دقیقه‌ای؛ epoch واقعی آلوستاتیک است
STATE_FILE = opslib.STATE_DIR / "ORGANISM-STATE.json"
START_TS = opslib.now_iso()


@contextmanager
def _noop_ctx():
    """context manager خالی برای وقتی tick_timing غایب یا flag خاموش است."""
    yield

# A3 (تری‌اسکن 2026-07-17): حسگرِ نسخهٔ کد. در بوت، (mtime,size) ماژول‌های بارشده را
# در یک سایدکارِ جدا می‌نویسیم تا کاکپیت بتواند «کدِ در حالِ اجرا کهنه‌تر از دیسک است»
# را تشخیص دهد — همان مشکلِ سه‌صفحه‌ای که ماه‌ها بی‌صدا بود. سایدکارِ جدا چون STATE_FILE
# هر تیک بازساخته می‌شود و بلوکِ نسخه گم می‌شد.
CODE_SIDECAR = opslib.STATE_DIR / "ORGANISM-STATE.code"
# فقط ماژول‌هایی که خودِ این پروسه بار می‌کند. cortex.py عمداً نیست: پروسهٔ جداست
# (8772، لایف‌سایکلِ مستقل) — سنجشِ کهنگیِ cortex به سنسورِ خودِ cortex نیاز دارد،
# وگرنه ری‌استارتِ فقط-ارگانیسم، کهنگیِ cortex را false-fresh نشان می‌داد (بازبینی 2026-07-17).
_KEY_MODULES = {
    "organism.py": _HERE / "organism.py",
    "wiring.py": _HERE / "wiring.py",
    "live_loop.py": _HERE / "live_loop.py",
}


def _write_code_sidecar() -> None:
    """عکسِ لحظهٔ بوت از (mtime,size) ماژول‌های کلیدی. fail-soft — نباید بوت را بکشد."""
    mods = {}
    for name, p in _KEY_MODULES.items():
        try:
            st = p.stat()
            mods[name] = {"mtime": round(st.st_mtime, 3), "size": st.st_size}
        except OSError:
            mods[name] = None
    try:
        CODE_SIDECAR.parent.mkdir(parents=True, exist_ok=True)
        tmp = CODE_SIDECAR.with_suffix(".code.tmp")
        tmp.write_text(json.dumps({"booted": START_TS, "modules": mods},
                                  ensure_ascii=False, indent=2), "utf-8")
        import os as _os
        _os.replace(tmp, CODE_SIDECAR)
    except Exception as e:  # noqa: BLE001 — سایدکارِ اختیاری
        opslib.alert([f"code sidecar write failed (non-fatal): {type(e).__name__}"])

# CARDIAC-ALLOMETRY: لایهٔ آلوستاتیکِ ضربان (additive، پشتِ OCTOPUS_WIRE_BIO).
# اگر flag off باشد، _cardiac None می‌ماند و رفتار عیناً فعلی است (no regression).
# نظریه: 07 - Knowledge/CARDIAC-ALLOMETRY-v1.md
try:
    import cardiac as _cardiac_mod   # noqa: E402
    _cardiac_budget, _cardiac_baro = _cardiac_mod.get_layer()
except Exception:  # noqa: BLE001 — additive، نباید بوت را بکشد
    _cardiac_mod = None
    _cardiac_budget, _cardiac_baro = None, None

# HH-P11: داورِ نبض — سه قلب (cardiac/control_law/rhythm) → یک periodِ advisory.
# additive، پشتِ OCTOPUS_WIRE_PULSE_ARBITER، read-only/سایه. flag off → shadow (رفتارِ فعلی).
try:
    from heart import pulse_arbiter as _arbiter_mod   # noqa: E402
except Exception:  # noqa: BLE001 — additive، نباید بوت را بکشد
    _arbiter_mod = None


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
        if self.path == "/api/tick-timing":
            # stage-3 گام ۱: خلاصهٔ اندازه‌گیریِ مدتِ فازها (probe، additive، $0)
            try:
                import tick_timing as _ttx
                body = json.dumps(_ttx.recent_summary(), ensure_ascii=False).encode("utf-8")
            except Exception:  # noqa: BLE001
                body = b'{"enabled": false, "reason": "probe unavailable"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return
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


def _write_state(extra: dict, merge_prev: bool = False) -> None:
    state = {
        "ts": opslib.now_iso(), "started": START_TS,
        "epoch_mode": "allostatic — تابع فشار (نه clock)",
        "halted": opslib.halted(), "frozen": opslib.frozen(),
        "stop_organism": opslib.STOP_ORGANISM.exists(),
        **extra,
    }
    if merge_prev:
        # مسیرِ خطا/STOP: بلوک‌های غنیِ آخرین tickِ سالم را حفظ کن، نه دور بریز.
        # فقط کلیدهای غایب back-fill می‌شوند (base + markerِ نو برنده‌اند). خواندنِ
        # ساده — نه LockedJson (re-entrant نیست). beatِ سطح‌بالا در fresh نیست پس از
        # prev می‌آید و «یخ» می‌زند در حالی که ts جلو می‌رود → سیگنالِ «آخرین‌دانسته».
        try:
            prev = json.loads(STATE_FILE.read_text("utf-8")) if STATE_FILE.exists() else {}
        except (OSError, ValueError):
            prev = {}
        if isinstance(prev, dict):
            for k, v in prev.items():
                if k in ("exited", "last_error"):
                    continue   # markerهای گذرا را از prev حمل نکن (وگرنه STOPِ اجرای قبل می‌ماند)
                state.setdefault(k, v)
    try:
        with opslib.LockedJson(STATE_FILE) as lj:
            lj.write(state)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"organism state write failed: {e}"])


def main() -> int:
    import os
    # secrets/keys از فایلِ کانونیِ .env (env_loader؛ fail-soft، idempotent، هرگز مقدار را echo نمی‌کند).
    # پیش از wiring لود می‌شود تا make_telegram_channel توکنِ TELEGRAM_BOT_TOKEN را در os.environ ببیند.
    try:
        import env_loader
        env_loader.load_env()
    except Exception:  # noqa: BLE001 — additive؛ نبودِ .env نباید بوت را بکشد
        pass
    port = int(os.environ.get("ORGANISM_PORT", PORT))
    try:
        _serve(port)   # bind انحصاری = قفل تک‌نمونه + endpoint وضعیت، هم‌زمان
    except OSError:
        print(f"organism: نمونهٔ دیگری روی 127.0.0.1:{port} روشن است — خروج تمیز.")
        return 0

    print(f"organism: زنده روی http://127.0.0.1:{port} — kill تمیز: فایل _ops/STOP-ORGANISM")
    opslib.heartbeat(f"organism=START port={port}")
    _write_code_sidecar()   # A3: عکسِ نسخهٔ کدِ بارشده در بوت
    # ── W-1..W-5 + neural wiring (پشتِ flag، paper-mode؛ پیش‌فرض خاموز = no regression)
    _wire = {}
    _doctor_inst = None
    _neural_stack = None
    _school_bridge = None
    _sensory_bus = None
    _bus = None
    _leg = None
    _ziman_leg = None
    _cartographer_leg = None
    _live_loop = None
    _idea_graph = None
    _pacemaker = None   # P-L1: نمونهٔ Pacemaker (HLC/ackِ LeadLeg). در boot پر می‌شود.
    _rhythm = None      # Rhythm (mode_color GREEN/AMBER/RED)
    _circadian = None   # CircadianMap (readiness ساعتِ روز)
    _sprint_runner = None  # SprintRunner (sprint management)
    _chan = None        # جلسه ۴۶: pre-init تا شکستِ wiring، nudge را NameError نکند
    # جلسه ۴۶ (رفعِ P0/E16): گاردِ human-append را با رازِ per-boot پیکربندی کن (ENABLE).
    # از این پس فقط approval_channel (که همین گاردِ ماژول-سطح را mint می‌کند) می‌تواند توکنِ
    # معتبر بسازد؛ enforce پشتِ OCTOPUS_WIRE_HUMAN_APPEND_GUARD در chrono. fail-safe.
    try:
        import secrets as _secrets
        sys.path.insert(0, str(_HERE / "budget"))
        from human_append_guard import configure as _cfg_guard
        _cfg_guard(_secrets.token_bytes(32))
        opslib.heartbeat("human-append guard configured (per-boot secret)")
    except Exception as _hge:  # noqa: BLE001 — گارد اختیاری؛ نبودش = passthrough امن
        opslib.alert([f"human-append guard configure failed (non-fatal): {type(_hge).__name__}"])
    # جلسه ۴۶: knobهای auto-اعمال‌شده را از دیسک بازگردان (تا با restart گم نشوند).
    try:
        sys.path.insert(0, str(_HERE / "cortex"))
        import auto_approve as _aa
        _knobs = _aa.load_persisted_knobs()
        if _knobs:
            opslib.heartbeat(f"auto-tuned knobs restored: {list(_knobs)}")
    except Exception as _ake:  # noqa: BLE001 — اختیاری
        opslib.alert([f"auto-knobs restore failed (non-fatal): {type(_ake).__name__}"])
    try:
        import wiring as _w
        _profile = _w.apply_profile()   # P-W3: paper-full → flagهای امن
        _wire = _w.wire_summary()
        # W-3 (2026-07-10): پا پیش از کانال ساخته می‌شود تا /lead از مسیرِ LeadLeg.intake برود
        _leg = _w.make_lead_leg()
        _ziman_leg = _w.make_ziman_leg()
        _cartographer_leg = _w.make_cartographer_leg()   # default-off flag → None تا گام ۵
        _chan = _w.make_telegram_channel(leg=_leg)   # auto-on اگر توکن
        # C7.2: ingress MUST remain closed until all durable callback/RFC projections
        # have been rebuilt.  Starting long-poll here created a boot race where an old
        # owner callback was consumed as "unknown" and its Telegram offset advanced.
        # The poller is started only after pending-card recovery below.
        # Trust-Engine ingress (2026-07-21): مرزِ امضاشدهٔ HTTP فقط پشتِ OCTOPUS_WIRE_LEAD_BOUNDARY
        # (پیش‌فرض خاموش، خارج از PAPER_FULL) → no-op. loopback-only، fail-soft.
        _lb_t = _w.maybe_start_lead_boundary()
        # جلسه ۴۶: تزریقِ db به دکتر — بدونِ آن calibration/effects_pending داده‌مرده بود
        # (اولین پیشنهادِ خودِ حلقهٔ خودارتقایی به خودش). زنده‌کنندهٔ حلقهٔ یادگیری. fail-soft.
        _doctor_db = None
        try:
            if chrono is not None:
                _doctor_db = chrono.ChronoDB(str(opslib.STATE_DIR / "chrono.db"))
        except Exception as _dde:  # noqa: BLE001 — db اختیاری؛ نبودش = رفتارِ قبلی
            opslib.alert([f"doctor db init failed (non-fatal): {type(_dde).__name__}"])
        _doctor_inst = _w.make_doctor(state_dir=str(opslib.STATE_DIR), db=_doctor_db,
                                      channel=_chan)
        # W (P-W1): returnها را نگه دار، نه دور بریز — نخاع: bus + leg + LiveLoop
        _bus = _w.make_unified_bus()
        _neural_stack = _w.make_neural_stack()   # W: neural ۸ ماژول
        # W: rhythm + circadian + sprint (neural subsystems)
        if _wire.get("wire_neural"):
            _rhythm = _w.make_rhythm()
            _circadian = _w.make_circadian()
            _sprint_runner = _w.make_sprint_runner()
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
        # G3 arc (ported to master 2026-07-18): اگر OCTOPUS_WIRE_PROPOSAL_BUTTONS=1، هوکِ
        # رأیِ کارتِ پیشنهاد را وصل کن (prop: → record_proposal_outcome_by_token). فلگ خاموش
        # → no-op و کارت‌ها همان متنِ بی‌دکمهٔ قبلی. measurement-only، هرگز settle.
        try:
            if _chan is not None and _live_loop is not None:
                _w.wire_proposal_buttons(channel=_chan, live_loop=_live_loop)
        except Exception as _pe:  # noqa: BLE001 — هوک نباید بوت را بکشد
            opslib.alert([f"wire_proposal_buttons failed (non-fatal): {type(_pe).__name__}"])
        # C2-D: بازیابیِ resume-not-restart در بوت (RESURRECTION فاز ۴+۷): journal اسکن
        # (advisory — هرگز re-runِ کور) + EXECUTINGِ رهاشده → RECONCILE_REQUIRED. fail-soft.
        try:
            import journal_recovery as _jr   # noqa: WPS433
            _rec = _jr.boot_recovery()
            _ji = _rec.get("journal", {})
            _ci = _rec.get("chrono", {})
            opslib.heartbeat(
                f"boot recovery: journal incomplete={len(_ji.get('incomplete', []))} "
                f"chrono reconciled={_ci.get('reconciled_now', 0)} "
                f"attention={_ci.get('attention_total', 0)}")
        except Exception as _re:  # noqa: BLE001 — بازیابی هرگز بوت را نمی‌کشد
            opslib.alert([f"boot recovery failed (non-fatal): {type(_re).__name__}"])
            _rec = {}
        # C2-E: شناسنامهٔ تولد (RESURRECTION فاز ۱۰) — `system.booted` → spine با زنجیرهٔ
        # prev_boot_id. پشتِ OCTOPUS_WIRE_SPINE؛ fail-soft؛ هیچ secret خوانده نمی‌شود.
        try:
            import sys as _bs
            _sp = str(Path(__file__).resolve().parent / "spine")
            if _sp not in _bs.path:
                _bs.path.insert(0, _sp)
            import boot_certificate as _bc   # noqa: WPS433
            _cert = _bc.emit_birth_certificate(extras={
                "journal_incomplete": len((_rec.get("journal") or {}).get("incomplete", [])),
                "chrono_reconciled": (_rec.get("chrono") or {}).get("reconciled_now", 0)})
            if _cert.get("emitted"):
                opslib.heartbeat(
                    f"birth certificate: boot={str(_cert.get('boot_id'))[:12]} "
                    f"prev={str(_cert.get('prev_boot_id'))[:12]} "
                    f"slept={_cert.get('uptime_gap_s')}s")
        except Exception as _bce:  # noqa: BLE001 — شناسنامه هرگز بوت را نمی‌کشد
            opslib.alert([f"birth certificate failed (non-fatal): {type(_bce).__name__}"])
        # C7 Slice 1: بازسازیِ کارت‌های approvalِ معلق (money از gated_effect، RFC از rfcs.json) —
        # projection-only، HALT-aware، fail-soft. صفر تغییرِ semanticِ authorizationِ پول.
        try:
            if _chan is not None:
                import outcomes.pending_card_recovery as _pcr  # noqa: WPS433
                _owner = os.environ.get("TELEGRAM_OWNER_CHAT_ID")
                _halted = bool(opslib.halted())
                try:
                    _bid = str((_cert or {}).get("boot_id") or os.getpid())
                except Exception:  # noqa: BLE001
                    _bid = str(os.getpid())
                _mc = _pcr.rebuild_money_cards(
                    channel=_chan, chrono_db_path=str(opslib.STATE_DIR / "chrono.db"),
                    owner=_owner, state_dir=str(opslib.STATE_DIR), halted=_halted, boot_id=_bid)
                _rc2 = _pcr.rebuild_rfc_cards(
                    channel=_chan, rfcs_path=str(opslib.STATE_DIR / "doctor" / "rfcs.json"),
                    state_dir=str(opslib.STATE_DIR))
                if _mc.get("rebuilt") or _rc2.get("rebuilt"):
                    opslib.heartbeat(f"pending-card recovery: money={_mc.get('rebuilt', 0)} "
                                     f"rfc={_rc2.get('rebuilt', 0)} halted={_halted}")
        except Exception as _pce:  # noqa: BLE001 — بازسازیِ کارت هرگز بوت را نمی‌کشد
            opslib.alert([f"pending-card recovery failed (non-fatal): {type(_pce).__name__}"])
        # C7.2: callback ingress opens only after recovery.  A recovery failure keeps
        # mutating callbacks fail-closed because their durable verifier cannot find a card.
        if _chan is not None:
            import threading as _tg
            _poll_t = _tg.Thread(target=_chan.run_forever, daemon=True,
                                 name="telegram-poll")
            _poll_t.start()
            opslib.heartbeat("telegram poll thread started after callback recovery (C7.2)")
        if any(_wire.values()):
            opslib.heartbeat(f"organism wiring: {_wire}")
    except Exception as _e:  # noqa: BLE001 — wiring اختیاریِ additive
        opslib.alert([f"organism wiring failed (non-fatal): {_e}"])
    if chrono is not None:
        try:   # P-Chrono-1: pacemaker به‌عنوان background task (additive، fail-soft)
            _pacemaker = chrono.start_pacemaker_thread(
                doctor=_doctor_inst, dispatcher=_w.make_scheduler())   # B5+B6: self-heal + scheduler
        except Exception as e:  # noqa: BLE001
            opslib.alert([f"chrono pacemaker start failed: {e}"])
    _beat_sched = None   # C7 Slice 4: ضربانِ سایه (فقط اگر OCTOPUS_ONE_HEARTBEAT=1؛ پیش‌فرض خاموش)
    next_epoch_at = 0.0
    last_daily = ""
    last_heartbeat = 0.0
    # P3 (truth-map 2026-07-17): حافظهٔ حلقه برای تغذیهٔ عصبِ درد — sigma از آخرین
    # ارزیابیِ روزانه، afferent_ratio از آخرین afferent_beat. بدونِ این‌ها nociceptor
    # با dictِ خالی، ۴ از ۶ ورودی‌اش همیشه صفر بود و protective_halt غیرقابل‌وصول.
    _last_sigma = 0.0
    _last_afferent_ratio = 1.0
    _ziman_last = None   # 2026-07-16 برنامه ۷: کشِ آخرین statusِ زیمان — کارت دیگر ۵۹/۶۰ تاریک نیست

    while True:
        _protective_skip = False   # آیا این تیک کارِ غیرضروری را skip کند؟ (protective-halt، enforceِ واقعی)
        # Always expose a fresh truthful block.  Flag-off is explicitly HARNESS rather
        # than a missing/stale value carried from a previous boot.
        try:
            import brain_core as _bc_status  # noqa: WPS433
            _bc_block = _bc_status.organism_state_block(
                state_dir=opslib.STATE_DIR, sched=_beat_sched)
        except Exception:  # noqa: BLE001
            _bc_block = {"mode": "HARNESS", "flag_on": False, "degraded": False}
        _heart_status = None       # HH-P5: پیش از try تعریف می‌شود تا بلوکِ _sleep_s (بیرونِ try) هرگز NameError نخورد
        _arb_status = None         # HH-P11: داورِ نبض — پیش از try (بلوکِ _sleep_s بیرونِ try می‌خواندش)
        # R-12 (audit): یک correlation_id برای کلِ این tick mint کن تا همهٔ emitهای این ضربان
        # (heartbeat/leg/doctor/incident/…) همبسته شوند و runِ input→output بازسازی‌پذیر شود.
        # نخ‌های هم‌زمان contextِ خالی دارند → آلوده نمی‌شوند. fail-soft (نبودِ events = None).
        _run_token = _events.begin_run() if _events is not None else None
        # C7 Slice 4: ضربانِ سایه — تنها یک scheduler، پشتِ OCTOPUS_ONE_HEARTBEAT=0 (پیش‌فرض خاموش
        # → صفر اثر؛ loopهای قدیمی authoritative). adapterها read-only؛ صفر ACT؛ HALT-safe؛
        # persistence fail-closed. fail-soft: هرگز ضربانِ اصلی را نمی‌کشد.
        try:
            import brain_core as _bc  # noqa: WPS433
            if _bc.flag_on():
                if _beat_sched is None:
                    _beat_sched = _bc.build_shadow_scheduler(
                        state_dir=opslib.STATE_DIR, halted_fn=opslib.halted)
                if _beat_sched is not None:
                    _beat_sched.tick()
                    # C7.2: refresh status after the shadow tick.
                    _bc_block = _bc.organism_state_block(state_dir=opslib.STATE_DIR,
                                                         sched=_beat_sched)
        except Exception:  # noqa: BLE001 — ضربانِ سایه هرگز ضربانِ اصلی را نمی‌کشد
            pass
        try:
            # P2 (structural, 2026-07-20 Stage-1): سیگنالِ restartِ کاکپیت = RESTART-REQUESTED
            # (نه overwriteِ STOP-ORGANISM). organism روی آن هم clean-exit می‌کند؛ launcher
            # فقط همین marker را پاک و relaunch می‌کند و هرگز STOP-ORGANISMِ مالک را حذف
            # نمی‌کند → دیگر هیچ مسیرِ خودکاری STOPِ مالک را ابطال نمی‌کند.
            _restart_req = (opslib.OPS / "RESTART-REQUESTED").exists()
            if opslib.STOP_ORGANISM.exists() or opslib.master_halted() or _restart_req:
                _why = "RESTART" if (_restart_req and not opslib.STOP_ORGANISM.exists()
                                     and not opslib.master_halted()) else "STOP"
                opslib.heartbeat(f"organism=HALT ({_why}) — خروج تمیز")
                _write_state({"exited": _why}, merge_prev=True)
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
            # vital ناوردی ۳: کهنگی germline — از طریقِ wiring.enrich_state_with_germline
            # (قراردادِ testable germline.py با CRIT-tier alert + fallback). پشتِ flag:
            # OCTOPUS_WIRE_GERMLINE=1 → ماژولِ غنی؛ خاموز → fallback (رفتارِ فعلی، safety-vital).
            germ = {}
            _w.enrich_state_with_germline(germ)

            # ── S (S-fix-3): protective-override ابتدای کار محاسبه و enforce می‌شود (arXiv fix)
            # غیرقابل‌سرکوب و واقعی: تصمیم اینجا (پیش از epoch/fitness/doctor) گرفته می‌شود تا همان تیک
            # آن‌ها را جلو بگیرد (نه بعد از اجرا). sleep همیشه در انتهای tick → بدونِ busy-loop.
            prot_state = {}
            # ── Rhythm: mode_color (GREEN/AMBER/RED) + circadian readiness برای neural_beat
            _rhythm_state = None
            _circadian_state = None
            if _rhythm is not None:
                try:
                    # fix (بازبینیِ خصمانهٔ 37cebf2): musd میکرو-دلار است؛ تقسیمِ مستقیم بر
                    # سقفِ دلاری، pct را ۱۰⁶ برابر می‌کرد — اولین خرجِ paidِ ماه ریتم را
                    # تا آخرِ ماه RED می‌چسباند. opslib.usd = مبدلِ رسمیِ میکرو→دلار.
                    _budget_pct = opslib.usd(snap["month"].get("musd", 0)) / max(opslib.load_budgets().get("global", {}).get("cap_monthly", 30), 1)
                    _rhythm_state = _w.rhythm_beat(_rhythm, readiness=0.6,
                                                   stress=min(1.0, _budget_pct * 2),
                                                   novelty=0.3, sigma=0.5)
                except Exception:  # noqa: BLE001
                    _rhythm_state = None
            if _circadian is not None:
                try:
                    _circadian_state = _w.circadian_readiness(_circadian)
                except Exception:  # noqa: BLE001
                    _circadian_state = None
            # HH-P11: داورِ نبض — سه قلب (cardiac + control_law + rhythm) → یک periodِ advisory.
            # shadow مگر wire_open (ساختاراً بسته تا رأیِ مالک). persist بدونِ flag نمی‌نویسد،
            # همیشه snapshot می‌دهد. fail-soft: داور هرگز tick را نمی‌کشد.
            if _arbiter_mod is not None:
                try:
                    _card_snap = (_cardiac_mod.status_snapshot()
                                  if _cardiac_mod is not None else None)
                    _arb_status = _arbiter_mod.persist(
                        cardiac_snapshot=_card_snap, rhythm_state=_rhythm_state,
                        beat=(_cstat or {}).get("beat", 0))
                    pulse["arbiter"] = {
                        "effective_period_s": _arb_status.get("effective_period_s"),
                        "driver": _arb_status.get("driver"),
                        "color": _arb_status.get("color"),
                        "n_present": _arb_status.get("n_present"),
                        "n_braking": _arb_status.get("n_braking"),
                        "wire_open": _arb_status.get("wire_open"),
                    }
                except Exception:  # noqa: BLE001 — §۴: داور نباید tick را بکشد
                    _arb_status = None
            if _neural_stack is not None:
                try:
                    _beat_n = (_cstat.get("beat", 0) if _cstat else 0)
                    # P3 (truth-map): error_rate = استرسِ خودگزارشیِ کورتکس (selfheal/day،
                    # هم‌واحدِ 0..1) از فایلِ state — fail-soft، بدونِ وابستگیِ import.
                    _err_rate = 0.0
                    try:
                        _sj = json.loads((opslib.STATE_DIR / "cortex" / "stress-latest.json")
                                         .read_text("utf-8"))
                        _err_rate = min(1.0, max(0.0, float(_sj.get("organism_stress", 0.0) or 0.0)))
                    except Exception:  # noqa: BLE001 — فایلِ غایب/خراب = صفر (رفتارِ قبلی)
                        _err_rate = 0.0
                    _neural_r = _w.neural_beat(_neural_stack, _beat_n, {
                        "rhythm": _rhythm_state or pulse.get("chrono", {}),
                        "budget": {"pct": opslib.usd(snap["month"].get("musd", 0)) / max(opslib.load_budgets().get("global", {}).get("cap_monthly", 30), 1)},
                        "spectral": {"sigma": _last_sigma},
                        "sensory": {"afferent_ratio": _last_afferent_ratio,
                                    "error_rate": _err_rate},
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
            # Phase 1: epoch-based sweep of stale gated_effects
            try:
                if chrono is not None:
                    _db_path = opslib.STATE_DIR / "chrono.db"
                    if _db_path.exists():
                        _cdb = chrono.ChronoDB(str(_db_path))
                        _gate = chrono.EffectorGate(db=_cdb)
                        _sw = _gate.sweep_stale_effects()
                        if _sw["refused"] > 0:
                            epoch_info["effect_sweep"] = _sw
            except Exception:  # noqa: BLE001 — sweep نباید tick را بکشد
                pass
            daily = {}
            if not _protective_skip and opslib.today() != last_daily:
                fit = fitness.compute()
                rep = replication.evaluate()
                last_daily = opslib.today()
                daily = {"fitness_authoritative": fit["authoritative"],
                         "sigma": rep["sigma"]["sigma_effective"],
                         "sigma_zone": rep["sigma"]["zone"]}
                # P3 (truth-map): sigmaی واقعی برای عصبِ درد در tickهای بعدی.
                try:
                    _last_sigma = float(rep["sigma"]["sigma_effective"] or 0.0)
                except (TypeError, ValueError, KeyError):
                    pass
                # B1 (تری‌اسکن 2026-07-17): verifyِ زنجیرهٔ هشِ لجر — فقط‌خواندنی، روزی یک‌بار.
                # هرگز لجر را تغییر نمی‌دهد (قانونِ ژنوم)؛ دستکاری → alert، نه crash. تا امروز
                # verify فقط در callerهای import‌نشده بود؛ حلقهٔ زنده هرگز چک نمی‌کرد.
                try:
                    _lok, _lreason = opslib.genome_ledger().verify()
                    daily["ledger_ok"] = bool(_lok)
                    if not _lok:
                        opslib.alert([f"GENOME LEDGER verify FAILED: {_lreason}"])
                except Exception as _lve:  # noqa: BLE001 — verify نباید tick را بکشد
                    daily["ledger_ok"] = None
                    opslib.alert([f"ledger verify error (non-fatal): {type(_lve).__name__}"])
                opslib.ledger_note("ORGANISM_DAILY", {
                    "month_aud": snap["month"]["aud"],
                    "suspects": snap["suspect_zero_total"],
                    "sigma": rep["sigma"]["sigma_effective"],
                    "conflicts": len(conflicts)}, actor="organism")
                # A1 (Phase 3): reconcile در بلوکِ روزانه، پشتِ flag. $0، بدون spend.
                try:
                    _w.reconcile_beat(day=opslib.today())
                except Exception:  # noqa: BLE001 — §۴
                    opslib.alert(["reconcile_beat error (non-fatal)"])
                # گاف #۱ دبل‌چک: اکچوایتورِ تصمیم‌های تأییدشده، پشتِ OCTOPUS_WIRE_ACTUATOR
                # (پیش‌فرض خاموش). $0، بدونِ اکشنِ خودکار/بیرونی — فقط visibility.
                try:
                    _w.actuator_beat()
                except Exception:  # noqa: BLE001 — §۴
                    opslib.alert(["actuator_beat error (non-fatal)"])
                # Blueprint P6 (2026-07-10): متریک فیشر — advisory فقط، پشتِ flag
                # (عمداً خارج از profile؛ وزن‌های واقعی فقط از budgets.yaml — I4/I6).
                if _w.flag("OCTOPUS_WIRE_FISHER"):
                    try:
                        import fisher as _fisher_mod
                        _fr = _fisher_mod.compute_fisher(write=True) or {}
                        daily["fisher_condition"] = _fr.get("fisher_condition_number")
                    except Exception as _fe:  # noqa: BLE001 — advisory نباید tick را بکشد
                        opslib.alert([f"fisher advisory error (non-fatal): {type(_fe).__name__}: {_fe}"])
                # ── C6 (stage-4): تولید مثل = خودبهبودیِ کد. روزی یک‌بار: یک فرضیه از صف
                # → آزمایشِ sandbox → RFC card به مالک (propose-only). پشتِ دو گیتِ
                # OCTOPUS_WIRE_C6_RESEARCH + ACTIVATION-C6-RESEARCH.flag. هرگز auto-apply.
                if _w.flag("OCTOPUS_WIRE_C6_RESEARCH"):
                    try:
                        import c6_trigger as _c6
                        _c6.seed_default_hypothesis()   # صفِ خالی → یک نمونهٔ بی‌خطر
                        _c6.c6_research_beat(
                            state_dir=str(opslib.STATE_DIR),
                            channel=_chan, beat=_cstat.get("beat", 0) if _cstat else 0)
                    except Exception as _c6e:  # noqa: BLE001 — §۴: c6 نباید tick را بکشد
                        opslib.alert([f"c6_research_beat error (non-fatal): {type(_c6e).__name__}: {_c6e}"])
            # ── W-2: Doctor beat (غیرضروری → زیرِ همان گیت؛ STOP/protective مقدم)
            _doctor_result = None
            if not _protective_skip and _doctor_inst is not None and _cstat is not None:
                try:
                    _db_t0 = _tt.timing("doctor_beat", beat=_cstat.get("beat", 0)) \
                        if _tt is not None else _noop_ctx()
                    with _db_t0:
                        _doctor_result = _w.doctor_beat(_doctor_inst, _cstat.get("beat", 0))
                except Exception:  # noqa: BLE001 — §۴: خطای خاموش ممنوع (Doctor نباید tick را بکشد)
                    opslib.alert(["doctor_beat error (non-fatal)"])
            # ── Doctor self-knowledge (2026-07-18): «باهوش و فعال» — یادگیریِ فقط‌خواندنیِ
            # خودِ اختاپوس با LLM. عمداً بیرونِ گیتِ _protective_skip/fear است (یادگیری ≠
            # تغییر) و در threadِ daemon اجرا می‌شود، پس نه tick را بلاک می‌کند نه ترس قفلش
            # می‌کند. flag خاموش (پیش‌فرض) → no-op.
            try:
                _w.doctor_selfknowledge_beat(beat=_cstat.get("beat", 0) if _cstat else 0)
            except Exception as _ske:  # noqa: BLE001 — خودشناسی نباید tick را بکشد
                opslib.alert([f"doctor_selfknowledge_beat error (non-fatal): {type(_ske).__name__}"])
            # ── M (P-M2): canonical consolidation در حلقهٔ زنده (هر N beat، پشتِ flag)
            # یک مسیرِ حافظهٔ واحد — منبعِ School را می‌گنجاند. advisory فقط، صفر spend.
            if not _protective_skip and _neural_stack is not None and _cstat is not None:
                try:
                    _w.consolidation_beat(_neural_stack, school_bridge=_school_bridge,
                                          beat=_cstat.get("beat", 0))
                except Exception as _ce:  # noqa: BLE001 — §۴: خطای خاموش ممنون (consolidation نباید tick را بکشد)
                    opslib.alert([f"consolidation_beat error (non-fatal): {type(_ce).__name__}: {_ce}"])
            # ── TG-EXEC (2026-07-15): مصرفِ verbهای صف‌شدهٔ تلگرام روی beat (پیش‌فرض خاموش). ──
            if not _protective_skip:
                try:
                    _tgx = _w.cockpit_requests_beat(state_dir=str(opslib.STATE_DIR),
                                                    doctor=_doctor_inst, channel=_chan)
                    if _tgx.get("ran"):
                        opslib.heartbeat(f"tg-exec ran: {_tgx['ran']}")
                except Exception as _qe:  # noqa: BLE001 — §۴ non-fatal
                    opslib.alert([f"cockpit_requests_beat error (non-fatal): {type(_qe).__name__}"])
            # ── W (P-W2): آورانِ واقعی — observationهای انتزاعی (ازِ snapshot، صفر PII)
            # → sensory_bus → school_bridge.learn_from → afferent_status. هر N beat، پشتِ flag.
            _afferent_status = None
            if not _protective_skip and _sensory_bus is not None and _cstat is not None:
                try:
                    _aff = _w.afferent_beat(_sensory_bus, school_bridge=_school_bridge,
                                            snap=snap, beat=_cstat.get("beat", 0))
                    if _aff and _aff.get("school_report"):
                        _afferent_status = _aff.get("sensory_status")
                    # P3 (truth-map): تغذیهٔ عصبِ درد در tickهای بعدی — نسبتِ آورانِ واقعی.
                    if _aff and isinstance(_aff.get("sensory_status"), dict):
                        try:
                            _v = float(_aff["sensory_status"].get("afferent_ratio", 1.0))
                            # NaN هر مقایسه‌ای را fail می‌کند → مقدارِ مسموم sticky نمی‌شود.
                            if 0.0 <= _v <= 1.0:
                                _last_afferent_ratio = _v
                        except (TypeError, ValueError):
                            pass
                except Exception as _ae:  # noqa: BLE001 — §۴: afferent نباید tick را بکشد
                    opslib.alert([f"afferent_beat error (non-fatal): {type(_ae).__name__}: {_ae}"])
            # ── W (P-W1): سیگنال‌های این tick را به bus (نخاع) منتشر کن.
            # مغز ← bus → subscriberها (LiveLoop.advisory_signals و غیره) فایر می‌شوند.
            # advisory فقط — هیچ effector. هر سیگنال در try مستقل (fail-soft، §۴).
            # W7: doctor_result واقعی را به bus منتقل کن (نه None).
            if not _protective_skip and _live_loop is not None:
                try:
                    _rh = _rhythm_state or pulse.get("chrono") or None   # rhythm (mode_color) یا chrono
                    _w.publish_tick_signals(_live_loop, beat=_cstat.get("beat", 0) if _cstat else 0,
                                            rhythm_state=_rh,
                                            afferent_status=_afferent_status,
                                            doctor_result=_doctor_result)
                except Exception as _pe:  # noqa: BLE001 — §۴: publish نباید tick را بکشد
                    opslib.alert([f"publish_tick_signals error (non-fatal): {type(_pe).__name__}: {_pe}"])
            # ── L (P-L1): LeadLeg حلقهٔ خودمختار — HLC محلی + ack + propose-only.
            # آبجکتِ _leg (از P-W1 نگه‌داشته‌شده) به LegHandle/HLC روی pacemaker.bus بسته می‌شود.
            # هر tick: HLC می‌زند + ack می‌دهد. هیچ effector؛ settle فقط از approval_channel.
            _leg_status = None
            if not _protective_skip and _leg is not None and _pacemaker is not None:
                try:
                    _lb_t0 = _tt.timing("leg_beat", beat=_cstat.get("beat", 0) if _cstat else 0) \
                        if _tt is not None else _noop_ctx()
                    with _lb_t0:
                        _leg_status = _w.leg_beat(_leg, pacemaker=_pacemaker,
                                                  beat=_cstat.get("beat", 0) if _cstat else 0)
                except Exception as _le:  # noqa: BLE001 — §۴: leg نباید tick را بکشد
                    opslib.alert([f"leg_beat error (non-fatal): {type(_le).__name__}: {_le}"])
            # ── Ziman limb: local proposal-only beat. جدا از Lead/HLC است تا
            # status و D4-gated inventory proposals به state برسند، بدون اجرای بیرونی.
            _ziman_status = None
            if not _protective_skip and _ziman_leg is not None:
                try:
                    _zb_t0 = _tt.timing("ziman_beat", beat=_cstat.get("beat", 0) if _cstat else 0) \
                        if _tt is not None else _noop_ctx()
                    with _zb_t0:
                        _ziman_status = _w.ziman_beat(
                            _ziman_leg,
                            beat=_cstat.get("beat", 0) if _cstat else 0,
                            doctor=_doctor_inst)
                except Exception as _ze:  # noqa: BLE001 — limb نباید tick را بکشد
                    opslib.alert([f"ziman_beat error (non-fatal): {type(_ze).__name__}: {_ze}"])
            _ziman_last = _ziman_status or _ziman_last   # برنامه ۷: کش برای رایت‌های off-beat

            # ── G1/G3: Proposal Router — پاها propose-only می‌مانند؛ LiveLoop فقط پیشنهادهای
            # محلیِ leg.proposals را dedupe/rank و به کارتِ owner-visible/advisory تبدیل می‌کند.
            # هیچ approve/settle/pay/send واقعی اینجا نیست؛ delivery itself = سیگنالِ یادگیری.
            _proposal_router = None
            _proposal_metrics = None
            if not _protective_skip and _live_loop is not None:
                try:
                    _proposal_router = _live_loop.route_leg_proposals(
                        [x for x in (_leg, _ziman_leg, _cartographer_leg) if x is not None],
                        deliver=True, limit=5)
                except Exception as _pre:  # noqa: BLE001 — §۴: router نباید tick را بکشد
                    opslib.alert([f"proposal_router error (non-fatal): {type(_pre).__name__}: {_pre}"])
                try:
                    # P0-G3 (2026-07-17): متریکِ نزدیک‌به‌عمل → state تا goal_directed.measure
                    # بخواند (فقط اندازه‌گیری؛ هیچ approve/settle — I7 دست‌نخورده).
                    _proposal_metrics = _live_loop.proposal_metrics()
                except Exception:  # noqa: BLE001 — metrics هرگز tick را نمی‌کشد
                    _proposal_metrics = None

            # ── Cartographer limb: read-only map-staleness sentinel. پشتِ
            # OCTOPUS_WIRE_CARTOGRAPHER (پیش‌فرض خاموش) → None تا فعال‌سازیِ مالک. inert.
            _cartographer_status = None
            if not _protective_skip and _cartographer_leg is not None:
                try:
                    _cartographer_status = _w.cartographer_beat(
                        _cartographer_leg,
                        beat=_cstat.get("beat", 0) if _cstat else 0)
                except Exception as _ce:  # noqa: BLE001 — limb نباید tick را بکشد
                    opslib.alert([f"cartographer_beat error (non-fatal): {type(_ce).__name__}: {_ce}"])

            # ── Business legs (blind-spot LEG-01): جمعِ status ِ ۴ پای نو (mining/crypto/
            # accounting/knowledge) → ORGANISM-STATE.business_legs تا داشبورد تاریک نباشد.
            # read-only/safe (بی‌فلگ، STOP-gated داخلِ خودش)؛ write=False → بی sidecarِ اضافه.
            _biz_legs = None
            if not _protective_skip:
                try:
                    _biz_legs = _w.business_legs_beat(
                        beat=_cstat.get("beat", 0) if _cstat else 0, write=False)
                except Exception as _ble:  # noqa: BLE001 — §۴: نباید tick را بکشد
                    opslib.alert([f"business_legs_beat error (non-fatal): {type(_ble).__name__}: {_ble}"])
            # ── Asset oversight (ASSET-OVERSIGHT): نقشهٔ داراییِ کل → ORGANISM-STATE.asset_map
            # پشتِ OCTOPUS_WIRE_ASSET_MAP (پیش‌فرض خاموش، خارج از PAPER_FULL_FLAGS) → None.
            # فقط‌خواندنی/fail-soft؛ هرگز مبلغ echo نمی‌کند؛ propose-only مطلق.
            _asset_map = None
            if not _protective_skip:
                try:
                    _asset_map = _w.asset_map_beat(
                        beat=_cstat.get("beat", 0) if _cstat else 0)
                except Exception as _ame:  # noqa: BLE001 — §۴: نباید tick را بکشد
                    opslib.alert([f"asset_map_beat error (non-fatal): {type(_ame).__name__}: {_ame}"])
            # ── Accounting (ضربانِ ضدِ فراموشی): حافظهٔ قواعد + صفِ ثبت + drift →
            # ORGANISM-STATE.accounting. پشتِ OCTOPUS_WIRE_ACCT_BEAT (پیش‌فرض خاموش،
            # خارج از PAPER_FULL_FLAGS) → None. propose-only؛ صفر پول/LLM در ضربان.
            _acct_beat = None
            if not _protective_skip:
                try:
                    _acct_beat = _w.acct_beat(
                        beat=_cstat.get("beat", 0) if _cstat else 0)
                except Exception as _acbe:  # noqa: BLE001 — §۴: نباید tick را بکشد
                    opslib.alert([f"acct_beat error (non-fatal): {type(_acbe).__name__}: {_acbe}"])
            # ── Email inbound (blind-spot LEG-06): پشتِ OCTOPUS_WIRE_EMAIL (پیش‌فرض خاموش)
            # → None (dry، بی polling). فقط با فلگِ مالک زنده می‌شود.
            if not _protective_skip:
                try:
                    _w.email_beat(beat=_cstat.get("beat", 0) if _cstat else 0)
                except Exception as _eme:  # noqa: BLE001 — §۴: نباید tick را بکشد
                    opslib.alert([f"email_beat error (non-fatal): {type(_eme).__name__}: {_eme}"])
            # ── Harvest (تری‌اسکن 2026-07-17): سرِ لولهٔ lead-inbox — AusTender keyless.
            # پشتِ OCTOPUS_WIRE_HARVEST (پیش‌فرض خاموش) → None. قبل از discovery تا صندوق
            # پر باشد وقتی discovery می‌خواند. propose-only، keyless، $0، fail-soft.
            _harvest = None
            if not _protective_skip:
                try:
                    _harvest = _w.harvest_beat(beat=_cstat.get("beat", 0) if _cstat else 0)
                except Exception as _hve:  # noqa: BLE001 — §۴: نباید tick را بکشد
                    opslib.alert([f"harvest_beat error (non-fatal): {type(_hve).__name__}: {_hve}"])
            # ── Lead discovery (مرحلهٔ ۲ نقشهٔ لید 2026-07-15): SENSE→SCORE→propose پشتِ
            # OCTOPUS_WIRE_LEAD_DISCOVERY (پیش‌فرض خاموش، خارج از PAPER_FULL_FLAGS) → None.
            # propose-only مطلق؛ نیازمندِ _leg (OCTOPUS_WIRE_LEAD) — بدونِ آن no-op.
            _lead_disc = None
            if not _protective_skip:
                try:
                    _lead_disc = _w.lead_discovery_beat(
                        _leg, beat=_cstat.get("beat", 0) if _cstat else 0)
                except Exception as _lde:  # noqa: BLE001 — §۴: نباید tick را بکشد
                    opslib.alert([f"lead_discovery_beat error (non-fatal): {type(_lde).__name__}: {_lde}"])
            # ── Legs cultivation (2026-07-16): متابولیسمِ دادهٔ $0 برای همهٔ پاها —
            # پشتِ OCTOPUS_WIRE_LEG_CULTIVATE (پیش‌فرض خاموش، خارج از PAPER_FULL_FLAGS)
            # → None. digest → دکتر (گزارشِ گلوگاه) + مغزِ B (اگر bus/bridge زنده باشند).
            _legs_cult = None
            if not _protective_skip:
                try:
                    _legs_cult = _w.legs_cultivation_beat(
                        beat=_cstat.get("beat", 0) if _cstat else 0,
                        sensory_bus=_sensory_bus, school_bridge=_school_bridge)
                except Exception as _lce:  # noqa: BLE001 — §۴: نباید tick را بکشد
                    opslib.alert([f"legs_cultivation_beat error (non-fatal): {type(_lce).__name__}: {_lce}"])
            # ── F3 (2026-07-14): seed ِ scheduler برای RFCهای دکتر — پشتِ OCTOPUS_WIRE_SCHEDULER
            # (پیش‌فرض خاموش) → no-op. producer (scheduler_seed_doctor_rfc) قبلاً سیم‌نشده بود.
            if not _protective_skip:
                try:
                    _w.scheduler_seed_beat(doctor=_doctor_inst, pacemaker=_pacemaker,
                                           beat=_cstat.get("beat", 0) if _cstat else 0)
                except Exception as _sse:  # noqa: BLE001 — §۴: نباید tick را بکشد
                    opslib.alert([f"scheduler_seed_beat error (non-fatal): {type(_sse).__name__}: {_sse}"])
            # ── I (P-I): موتورِ ایده-گراف — هر N beat گرافِ vault را تحلیل کن.
            # هاب‌ها/خوشه‌ها/پل‌ها/یال‌های پیشنهادی. propose-only مطلق (هیچ effector).
            if not _protective_skip and _idea_graph is not None and _cstat is not None:
                try:
                    _w.idea_beat(_idea_graph, beat=_cstat.get("beat", 0))
                except Exception as _ie:  # noqa: BLE001 — §۴: idea نباید tick را بکشد
                    opslib.alert([f"idea_beat error (non-fatal): {type(_ie).__name__}: {_ie}"])
            # ── Phase 5: epistemics wiring (پشتِ flag، advisory، non-enforcer).
            # هر N beat، پنج متریک را محاسبه و advisory publish کن. annotate، نه fork.
            if not _protective_skip and _cstat is not None:
                try:
                    _w.epistemics_beat(live_loop=_live_loop, beat=_cstat.get("beat", 0))
                except Exception as _ee:  # noqa: BLE001 — §۴: epistemics نباید tick را بکشد
                    opslib.alert([f"epistemics_beat error (non-fatal): {type(_ee).__name__}: {_ee}"])

            # ── HH-P5: قلبِ ترکیبی (سایه) — پشتِ OCTOPUS_WIRE_HEART، هر N beat.
            # فقط محاسبه + سینکِ جدا؛ periodِ واقعی در بلوکِ انتهایی و فقط با predicateِ ۸شرطی.
            if not _protective_skip and _cstat is not None:
                try:
                    _heart_status = _w.heart_beat(beat=_cstat.get("beat", 0), snap=snap)
                except Exception as _hbe:  # noqa: BLE001 — §۴: قلب نباید tick را بکشد
                    opslib.alert([f"heart_beat error (non-fatal): {type(_hbe).__name__}: {_hbe}"])
            # ── جلسه ۴۶: نوتیفِ «نیازت دارم» — پشتِ OCTOPUS_WIRE_NEEDS_NUDGE، هر N beat،
            # ضدِ اسپم با hash. فقط‌خواندنی + یک sendMessage به مالک (fail-soft).
            if not _protective_skip and _cstat is not None:
                try:
                    _w.needs_nudge_beat(_chan, beat=_cstat.get("beat", 0))
                    # جلسه ۴۶: نوتیفِ «چی یاد گرفتم» — کشف/یادگیری را دیدنی می‌کند.
                    _w.discovery_nudge_beat(_chan, beat=_cstat.get("beat", 0))
                    # جلسه ۴۶: heartbeat summary هر ~۵min — خوراکِ داشبوردِ اتوماسیون.
                    _w.heartbeat_summary_beat(_chan, beat=_cstat.get("beat", 0))
                    # جلسه ۴۶: علائمِ حیاتی (استرس+عصب‌کشی) مستقیم از ستونِ فقرات —
                    # تا حتی با خوابِ دیمنِ کورتکس، مانیتور کور نشود و نقطهٔ مرده لو برود.
                    _w.cortex_vitals_beat(beat=_cstat.get("beat", 0))
                    # Task 3 (2026-07-24): دیالوگِ owner↔organ — سه organ روی همان _chan
                    # (کادنسِ زمان-محور + hash-throttle؛ پشتِ flagهای خودشان؛ fail-soft).
                    _w.doctor_digest_beat(_chan, beat=_cstat.get("beat", 0))
                    _w.brain_digest_beat(_chan, beat=_cstat.get("beat", 0))
                    _w.heart_card_beat(_chan, beat=_cstat.get("beat", 0))
                except Exception as _nne:  # noqa: BLE001 — §۴: نوتیف نباید tick را بکشد
                    opslib.alert([f"needs_nudge error (non-fatal): {type(_nne).__name__}: {_nne}"])
            if now - last_heartbeat > 3600:
                opslib.heartbeat(
                    f"organism=ok · ماه AU${snap['month']['aud']:.2f} · "
                    f"مشکوک متر صفر={snap['suspect_zero_total']} · "
                    f"{'CONFLICT×' + str(len(conflicts)) if conflicts else 'سالم'}"
                    f"{' · PROTECTIVE' if _protective_skip else ''}")
                last_heartbeat = now
            _write_state({"month": snap["month"], "today": snap["today"],
                          "beat": (_cstat.get("beat") if _cstat else None),
                          "suspect_zero_total": snap["suspect_zero_total"],
                          "conflicts": conflicts, **germ, **epoch_info, **daily,
                          **pulse, **prot_state,
                          "protective_skip": _protective_skip, "wiring": _wire,
                          **({"leg": _leg_status} if _leg_status else {}),
                          **({"ziman": (_ziman_status or _ziman_last)} if (_ziman_status or _ziman_last) else {}),
                          **({"cartographer": _cartographer_status} if _cartographer_status else {}),
                          **({"business_legs": _biz_legs} if _biz_legs else {}),
                          **({"asset_map": _asset_map} if _asset_map else {}),
                          **({"accounting": _acct_beat} if _acct_beat else {}),
                          **({"lead_discovery": _lead_disc} if _lead_disc else {}),
                          **({"harvest": _harvest} if _harvest else {}),
                          **({"proposal_router": _proposal_router} if _proposal_router else {}),
                          **({"proposal_metrics": _proposal_metrics}
                             if _proposal_metrics is not None else {}),
                          **({"legs_cultivation": _legs_cult} if _legs_cult else {}),
                          **({"heart": _heart_status} if _heart_status else {}),
                          "brain_core": _bc_block,
                          **({"cardiac": _cardiac_mod.status_snapshot()}
                             if _cardiac_mod is not None else {})})
        except KeyboardInterrupt:
            opslib.heartbeat("organism=STOP (KeyboardInterrupt)")
            return 0
        except Exception as e:  # noqa: BLE001 — خطای خاموش = شدیدترین باگ (منشور §۴)
            opslib.alert([f"organism tick error: {type(e).__name__}: {e}"])
            _write_state({"last_error": f"{type(e).__name__}: {e}"}, merge_prev=True)
        finally:
            # R-12: پایانِ runِ این tick — contextِ correlation_id را همیشه بازگردان (حتی روی
            # returnِ STOP/KeyboardInterrupt) تا sleepِ بینِ ضربان‌ها و ضربانِ بعدی idِ این tick
            # را به ارث نبرند. fail-soft (_run_token=None → no-op).
            if _events is not None:
                _events.end_run(_run_token)
        # CARDIAC-ALLOMETRY: periodِ داینامیک (پشتِ OCTOPUS_WIRE_BIO، advisory).
        # اگر flag off یا خطا → عیناً TICK_SECONDS (رفتارِ فعلی).
        _sleep_s = TICK_SECONDS
        if _cardiac_mod is not None:
            try:
                _eff = _cardiac_mod.effective_period(
                    base_period_s=TICK_SECONDS,
                    budget=_cardiac_budget, baro=_cardiac_baro)
                _sleep_s = _eff["period_s"]
                # خرجِ بودجهٔ این تیک — P5 (truth-map 2026-07-17): بعد از depletion دیگر
                # «active» شمرده نمی‌شود؛ resting = ضربانِ مجانیِ استراحت. بدونِ این، spent
                # از سقف رد می‌شد (۳۲۷>۲۸۸) و شمارنده سنجهٔ صادقِ «کارِ ارزشمند» نبود.
                if _cardiac_budget is not None:
                    _depl = bool((_eff.get("budget") or {}).get("depleted"))
                    _cardiac_budget.spend("resting" if _depl else "active")
            except Exception:  # noqa: BLE001 — §۴: cardiac نباید tick را بکشد
                pass
        # HH-P5: قلبِ ترکیبی — سایه همیشه در سینکِ جدا؛ periodِ زنده فقط اگر predicateِ
        # ۸شرطیِ مالک (production_wire، محاسبه‌شده داخلِ همین heart_beat — صفر I/O اینجا)
        # باز باشد. flag خاموش → _heart_status=None → این بلوک no-op (بایت‌به‌بایت رفتارِ فعلی).
        if _heart_status is not None and _heart_status.get("wire_open"):
            try:
                # HH-P8 رأی ۳ (مصوبِ مالک): کفِ tickِ زنده ۶۰s — هر tick تلمتریِ کامل
                # می‌خواند؛ کفِ ۳۰ فقط برای ریاضی/سایه/sim معتبر می‌ماند.
                import os as _os
                _floor = float(_os.environ.get("HEART_LIVE_FLOOR_S", "60"))
                _hp = float(_heart_status.get("period_shadow_s") or TICK_SECONDS)
                _sleep_s = max(_floor, min(900.0, _hp))
            except Exception:  # noqa: BLE001 — §۴: قلب نباید sleep را بشکند
                pass
        # HH-P11: seamِ زندهٔ داورِ نبض — periodِ *واحد* از سه قلب فقط اگر wire_open باز باشد
        # (ساختاراً بسته تا رأیِ مالک: OCTOPUS_WIRE_PULSE_ARBITER + …). بسته → _sleep_s دست‌نخورده.
        if _arb_status is not None and _arb_status.get("wire_open"):
            try:
                _sleep_s = float(_arb_status.get("effective_period_s") or _sleep_s)
            except (TypeError, ValueError):
                pass
        time.sleep(_sleep_s)


if __name__ == "__main__":
    sys.exit(main())
