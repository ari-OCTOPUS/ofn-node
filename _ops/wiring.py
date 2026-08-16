#!/usr/bin/env python3
"""wiring.py — Phase 5+ · W-1..W-5: اتصالِ ۵ لایه به یک حلقهٔ زنده (پشتِ flag، paper-mode).

٥ لایه (chrono, telegram, legs, doctor, survival) را به organism متصل می‌کند.
همه پشتِ env-flags — پیش‌فرض خاموش (paper-mode امن، no regression).
پول تا ۲۱-۰۷ قفل: هیچ مسیرِ spend وصل نمی‌شود.

Flags (همه پیش‌فرض خاموز):
  OCTOPUS_WIRE_DOCTOR=1    → Doctor.run_cycle هر N beat از Pacemaker
  OCTOPUS_WIRE_TELEGRAM=1  → TelegramApprovalChannel (auto-on اگر توکن باشد)
  OCTOPUS_WIRE_UNIFIED=1   → UnifiedBus.publish به ledger+chrono
  OCTOPUS_WIRE_LEAD=1      → LeadLeg (incubating تا organ در budgets.yaml)
  OCTOPUS_WIRE_ZIMAN=1     → ZimanLeg (organ=ZIMAN؛ propose-only، D4 capacity)
  (W-1 germline_lag همیشه روشن — flag لازم ندارد، فقط read-only enrichment)

additive؛ stdlib-only؛ kill-switch مطلق (هر حلقه اول STOP را چک می‌کند).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE / "budget"))
import opslib        # noqa: E402


def flag(name: str) -> bool:
    """env-flag با پیش‌فرض خاموز."""
    return os.environ.get(name, "0") == "1"


def effective_flag(name: str) -> bool:
    """فلگِ مؤثر برای رأی‌های tracked: env صریح (حتی ``0``) برنده است.

    فقط callerهایی که عمداً رأیِ ماندگار در ``owner-verdicts.yaml`` دارند از این
    helper استفاده می‌کنند. نبود/خرابیِ فایل fail-soft به رفتارِ env-only قبلی
    برمی‌گردد؛ بنابراین این تابع منبعِ رقیب یا راهِ دورزدنِ rollback نیست.
    """
    try:
        import owner_verdicts as _verdicts
        value = _verdicts.get(name)
    except Exception:  # noqa: BLE001 — رأیِ fallback نباید wiring را بکشد
        value = os.environ.get(name, "0")
    return str(value or "0").strip().lower() in ("1", "true", "yes", "on")


def rhythm_enabled() -> bool:
    """حقیقتِ CR-B0: فلگ مستقل + fallback tracked، با حفظِ معنای ``bare``.

    env صریح همیشه حرف آخر است؛ بنابراین کاربر می‌تواند حتی زیرِ profile bare
    ریتم را عمداً روشن کند. ولی اگر env غایب باشد، bare باید «همه off» بماند و
    رأیِ tracked فقط در paper-full/live اعمال می‌شود.
    """
    name = "OCTOPUS_WIRE_CHRONO_RHYTHM"
    if name in os.environ:
        return effective_flag(name)
    if resolve_profile() == "bare":
        return False
    return effective_flag(name)


# ── W1: 4d_system read-only data access (فاز ۷ دستورالعمل ۲۰۲۶-۰۸-۱۶) ────────
# فقط همین مرحله وصل است (DUAL-BRAIN-CONSTITUTION §۵). W2 پروپوزال/W3 ارزیابی/
# W4 وتو/W5 ارز — هر کدام رأیِ جداگانهٔ مالک می‌خواهند و عمداً این‌جا نیستند.
# درِ واقعی داده در _ops/fourd_access.py است (allowlist + fail-closed + فقط‌خواندن)؛
# این‌جا فقط stage-marker و delegate — تا خوانندهٔ wiring بداند W1 از کجا می‌گذرد.
def fourd_w1_snapshot() -> dict:
    """W1: نمایِ دادهٔ read-only برای مغزِ 4d — delegate به fourd_access (fail-soft)."""
    try:
        import fourd_access   # noqa: WPS433 — lazy، _ops روی sys.path
        return fourd_access.snapshot()
    except Exception:  # noqa: BLE001 — W1 هرگز wiring را نمی‌کشد
        return {"schema": "fourd-access.v1", "enabled": False,
                "reason": "wiring-delegate-failsoft"}


def _syspath(p) -> None:
    """افزودنِ idempotent به sys.path. توابعِ این ماژول per-beat صدا زده می‌شوند و
    `sys.path.insert` بی‌گارد هر ضربان یک ورودیِ تکراری اضافه می‌کرد (اندازه‌گیری
    2026-07-24: ۵۰ ضربان = ۵۲ ورودیِ تکراری؛ پروسهٔ چندروزه = هزاران). لیستِ باد‌کرده
    هر importِ ناموفق را کند می‌کند. الگوی گاردشده قبلاً در همین فایل بود — این فقط
    یکدستش می‌کند."""
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


# ── anti-aliasing cadence gate (تری‌اسکن 2026-07-17) ───────────────────────────
# باگِ ریشه‌ای: tickِ واقعی ~۹۰۰s ضربانِ ۶۰s را با گامِ ~۱۵ نمونه‌برداری می‌کند، پس
# `beat % N == 0` روی مضرب‌ها می‌پرد و شلیک‌ها را از دست می‌دهد (droughtهای چندساعته
# تا چندهفته‌ای). قالبِ درست (هم‌الگوی _ACCT_STATE/_HEART_STATE): هر epoch حداکثر یک
# شلیک. این هلپر همان منطق را DRY می‌کند تا هر ۸ سایتِ باقی‌مانده یک‌دست شوند.
_EPOCH_STATE: dict = {}   # name -> آخرین epochِ شلیک‌شده. in-memory (مثلِ _HEART_STATE/
                          # _ACCT_STATE): پس از restart پاک می‌شود، پس یک شلیکِ مجددِ
                          # بی‌ضرر در همان پنجره ممکن است — propose-only، پذیرفته‌شده.


def _epoch_fire(name: str, beat: int, every_n) -> bool:
    """آیا این beat باید همین الان شلیک کند؟ هر پنجرهٔ epoch (=beat//every_n) دقیقاً
    یک‌بار True می‌دهد، مستقل از اینکه tick کدام beatِ داخلِ پنجره را نمونه بگیرد.
    flag/kill پیش از این فراخوانی چک می‌شوند، پس خاموش = هرگز به اینجا نمی‌رسد."""
    try:
        every_n = int(every_n)
    except (TypeError, ValueError):
        every_n = 0
    if every_n <= 0:
        return True   # every_n<=0 = «هر beat» (هم‌معنیِ منطقِ کهنه: بدونِ cadence-gating)
    epoch = beat // every_n
    if epoch < 1 or epoch <= _EPOCH_STATE.get(name, 0):
        return False
    # ۲۰۲۶-۰۷-۲۸ — `_EPOCH_STATE` **در حافظه** است، پس هر ری‌استارت صفرش می‌کند و
    # اولین تیکِ بعد از هر بوت این شرط را رد می‌کند: همهٔ کادنس‌ها با هم شلیک
    # می‌کنند، صرف‌نظر از اینکه پنجره‌شان رسیده باشد.
    # نشانهٔ اندازه‌گیری‌شده: کارتی با تناوبِ **۶ ساعت** چهار بار در یک ساعت آمد،
    # چون آن ساعت چهار ری‌استارت داشت. تناوب درست بود؛ بوت آن را دور می‌زد.
    # حافظهٔ دیسکی این را می‌بندد. فلگ خاموش → `already_fired` همیشه False →
    # رفتارِ بایت‌به‌بایتِ قبلی.
    try:
        import epoch_guard as _eg   # noqa: WPS433 — lazy، خودش flag را چک می‌کند
        if _eg.already_fired(name, epoch):
            _EPOCH_STATE[name] = epoch      # حافظه را هم‌گام کن تا دوباره نپرسد
            return False
        _eg.mark_fired(name, epoch)
    except Exception:  # noqa: BLE001 — گاردِ اختیاری هرگز کادنس را نمی‌کشد
        pass
    _EPOCH_STATE[name] = epoch
    return True


def _epoch_window(name: str, epoch: int, mem: dict, *, min_epoch: int = 1,
                  key: str = "last_epoch") -> bool:
    """همان گاردِ `_epoch_fire`، برای حالت‌های **دست‌سازِ** قدیمی.

    ۲۰۲۶-۰۷-۲۸ — شش کادنس چکِ پنجره را خودشان نوشته بودند و از `_epoch_fire` رد
    نمی‌شدند: `_INGEST_STATE` · `_HEART_STATE` · `_ACCT_STATE` · `_NUDGE_STATE` ·
    `_HEARTBEAT_STATE` · `_DISCOVERY_STATE`. همه در حافظه، پس هر ری‌استارت
    صفرشان می‌کرد و **هر شش با هم** بی‌قید شلیک می‌کردند.

    اندازه‌گیری: با فلگ خاموش ۵ ری‌استارت = ۵ شلیک؛ با فلگ روشن = ۱ شلیک.

    این تابع همان دو گارد را کنارِ هم می‌گذارد تا یک قاعده بماند، نه شش کپی:
    حافظه (سریع، درون‌پروسه) + دیسک (بقا از ری‌استارت). خروجی True یعنی
    «شلیک کن» و خودش هر دو را علامت می‌زند.
    """
    if epoch < min_epoch or epoch <= mem.get(key, min_epoch - 1):
        return False
    try:
        import epoch_guard as _eg   # noqa: WPS433 — lazy، خودش flag را چک می‌کند
        if _eg.already_fired(name, epoch):
            mem[key] = epoch
            return False
        _eg.mark_fired(name, epoch)
    except Exception:  # noqa: BLE001 — گاردِ اختیاری هرگز کادنس را نمی‌کشد
        pass
    mem[key] = epoch
    return True


def leg_paused(key: str) -> bool:
    """مکثِ runtimeِ تک‌پا از مرکزِ تلگرام (رأی مالک 2026-07-17) — قالبِ اثبات‌شدهٔ
    projectf-paused.flag: فایلِ سبکِ state/leg-<key>-paused.flag که هر ضربان بازخوانی
    می‌شود (بدونِ restart). studio_pf به فایلِ موجودش نگاشت (یک حقیقت، دو نام ممنوع).
    خطا → False (fail-open به‌سمتِ کار — مکث فقط با فایلِ سالم)."""
    try:
        name = ("projectf-paused.flag" if key == "studio_pf"
                else f"leg-{key}-paused.flag")
        return (opslib.STATE_DIR / name).exists()
    except OSError:
        return False


# ════════════════════════════════════════════════════════════════════════════════
# W3 · boot profile — یک سوئیچ به‌جای ۶ flagِ پراکنده (P-W3)
# ════════════════════════════════════════════════════════════════════════════════

# paper-full = همهٔ wiringِ امنِ propose-only روشن (neural + consolidation + school +
# sensory + doctor + evolution + box + unified + legs + ideas + germline + checkpoint +
# spectral). پول/live جدا و همچنان capability-gated (profile آن را باز نمی‌کند).
PAPER_FULL_FLAGS = (
    "OCTOPUS_WIRE_DOCTOR", "OCTOPUS_WIRE_NEURAL", "OCTOPUS_WIRE_UNIFIED",
    "OCTOPUS_WIRE_LEAD", "OCTOPUS_WIRE_ZIMAN", "OCTOPUS_WIRE_SCHOOL",
    "OCTOPUS_WIRE_CONSOLIDATION",
    "OCTOPUS_WIRE_EVOLUTION", "OCTOPUS_WIRE_BOX", "OCTOPUS_WIRE_LEAD_TICK",
    "OCTOPUS_WIRE_IDEAS",
    "OCTOPUS_WIRE_CHRONO_RHYTHM",  # CR-B0: فلگ مستقل؛ circadian/sprint هنوز neural
    "OCTOPUS_WIRE_SPECTRAL",   # P-spectral: complementary spectral bottleneck
    "OCTOPUS_WIRE_BCM",        # P3 blueprint: BCM forgetting — default-applied
                               # 2026-07-10 (قابل‌وتو، AGENT_QUESTIONS)؛ فقط ایندکس retrieval
    "OCTOPUS_WIRE_SPARSE",     # P4 blueprint: sparse input filter — verdict آری
                               # «برو» 2026-07-10؛ فقط ورودیِ acquisition را باریک می‌کند
    "OCTOPUS_WIRE_FISHER",     # P6 blueprint: Fisher advisory — verdict آری «برو»
                               # 2026-07-10؛ فقط fisher-latest.json، هیچ تغییرِ scoring (I4/I6)
    "OCTOPUS_WIRE_CARTOGRAPHER",  # verdictِ مالک 2026-07-12: پای نقشه‌بردار با بوتِ اختاپوس
                                  # روشن شود (read-only sentinel، content-free، صفر spend/outward).
                                  # kill/rollback: حذفِ همین خط یا OCTOPUS_WIRE_CARTOGRAPHER=0.
    # NOTE: germline/checkpoint همیشه‌رون‌اند (safety-vital) — enrich_state_with_
    # germline و unified_bus._checkpoint همیشه اجرا می‌شوند، flag لازم ندارند.
    # NOTE: OCTOPUS_WIRE_CHAMBER_T (P5، برچسب RED) همچنان عمداً اینجا نیست —
    # «برو»ِ کلی کافی نیست؛ فقط جملهٔ صریحِ مالک دربارهٔ خودِ chamber-T.
)


def resolve_profile() -> str:
    """profile را از OCTOPUS_PROFILE بخوان. پیش‌فرضِ نو = paper-full (وقتی متغیر ست
    نشده) → بوتِ عادی کلِ بدنِ امن را فعال می‌کند. bare = همه off (debug/emergency).
    live = paper-full + (در آینده) effectorهای پول، ولی فقط با capability_gate + history.
    money/live مطلقاً جدا: این تابع فقط flagهای امن را ست می‌کند، هرگز capability/money."""
    return os.environ.get("OCTOPUS_PROFILE", "paper-full")


def apply_profile() -> str:
    """profile را resolve کن و flagهای مربوطه را در env ست کن.
    paper-full = همهٔ flagهای امن = 1 (اگر هنوز ست نشده‌اند).
    bare = همه off (debug/emergency).
    live = همانِ paper-full + (effectorها جدا، فقط با capability_gate).
    flagهای مجزای OCTOPUS_WIRE_* اگر صریحاً ست شده باشند → override (پایین می‌مانند اگر 0).
    money/live مطلقاً جدا: این تابع هرگز capability_gate/money_gate را باز نمی‌کند.
    برمی‌گرداند: نامِ profile."""
    profile = resolve_profile()
    if profile in ("paper-full", "live"):
        for f in PAPER_FULL_FLAGS:
            # فقط اگر هنوز ست نشده (override: اگر کاربر صریحاً 0 ست کرده، پایین می‌ماند)
            if f not in os.environ:
                os.environ[f] = "1"
    # live: effectorهای پول به‌طور جداگانه capability-gated می‌شوند (این تابع بازشان نمی‌کند)
    return profile


# ─── W-1 · germline_lag → ORGANISM-STATE (همیشه روشن، read-only) ───────────────
def enrich_state_with_germline(state: dict) -> dict:
    """germline_lag را از germline.py به state اضافه کن + CRIT-tier alert.
    اگر germline.py نباشد → fallback به opslib.germline_lag_hours (همان قبل).
    همیشه روشن چون read-only است و ریسک صفر دارد. CRIT/ERROR → opslib.alert."""
    try:
        import germline
        alarm = germline.lag_alarm()
        state["germline_lag_h"] = alarm.get("germline_lag_h")
        state["germline_alert"] = alarm.get("germline_alert")
    except Exception:  # noqa: BLE001 — fallback
        try:
            lag = opslib.germline_lag_hours()
            state["germline_lag_h"] = lag
            if lag is None or lag > opslib.GERMLINE_ERR_H:
                state["germline_alert"] = "ERROR"
            elif lag > opslib.GERMLINE_WARN_H:
                state["germline_alert"] = "warn"
        except Exception:  # noqa: BLE001
            pass
    # CRIT-tier alert (ناوردی ۳): ERROR/CRIT → opslib.alert (نه بی‌صدا)
    alert = state.get("germline_alert", "")
    lag = state.get("germline_lag_h")
    if alert in ("ERROR", "CRIT"):
        opslib.alert([f"germline_lag {alert}: {lag}h — بک‌آپ off-box کهنه/غایب (ناوردی ۳)"])
    return state


# ─── نمونه‌سازیِ لایه‌ها (در startup، پشتِ flag) ─────────────────────────────────
def make_doctor(state_dir=None, db=None, channel=None):
    """ساختِ Doctor با wiring کامل. پشتِ OCTOPUS_WIRE_DOCTOR."""
    if not flag("OCTOPUS_WIRE_DOCTOR"):
        return None
    try:
        _syspath(str(_HERE / "doctor"))
        from doctor import Doctor
        # ۲۰۲۶-۰۸-۰۸ (up-1363aae4df): suite_fn برای measured_lift واقعی.
        # بدونِ این، _default_eval به fallbackِ severity برمی‌گردد. suite_runner
        # یک subset سبک از تست‌ها را اجرا می‌کند تا suite-delta واقعی ساخته شود.
        suite_fn = None
        try:
            from suite_runner import make_suite_fn
            suite_fn = make_suite_fn()
        except Exception:  # noqa: BLE001 — نبودِ suite_runner نباید Doctor را بکشد
            pass
        return Doctor(state_dir=state_dir, db=db, approval_channel=channel,
                      suite_fn=suite_fn)
    except Exception as e:  # noqa: BLE001 — Doctor اختیاریِ additive
        opslib.alert([f"wiring: Doctor ساخت نشد: {e}"])
        return None


def make_telegram_channel(leg=None):
    """ساختِ TelegramApprovalChannel. auto-on اگر توکن باشد.
    T-8: gate و ledger از chrono تزریق می‌شوند تا T-2 settle فعال باشد.
    W-3 (2026-07-10): leg اختیاری — /lead از مسیرِ LeadLeg.intake برود (propose-only)."""
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        return None
    try:
        _syspath(str(_HERE / "budget"))
        from approval_channel import TelegramApprovalChannel
        # T-8: gate/ledger injection — T-2 settle فقط با این دو فعال است.
        _gate = _ledger = None
        try:
            import chrono as _chrono_mod
            # فیکسِ کرشِ نهفته (2026-07-21): db=None می‌کرد settle/request روی self.db.ex
            # با AttributeError کرش کند لحظه‌ای که producerِ واقعی اضافه شود. ChronoDBِ واقعی
            # تزریق می‌کنیم (مثلِ مسیرِ organism.py و doctor_db) تا مسیرِ settleِ تلگرام سالم بماند.
            _gate_db = _chrono_mod.ChronoDB(str(opslib.STATE_DIR / "chrono.db"))
            _gate = _chrono_mod.EffectorGate(db=_gate_db)
        except Exception:  # noqa: BLE001 — chrono import شکست = بدون gate
            pass
        kw = {"gate": _gate, "ledger": None, "state_dir": str(opslib.STATE_DIR)}
        if leg is not None:
            kw["leg"] = leg
        try:
            return TelegramApprovalChannel(**kw)   # no-op امن اگر توکن نباشد
        except TypeError:
            # نسخهٔ قدیمیِ channel بدونِ پارامترِ leg — عقب‌رو امن
            kw.pop("leg", None)
            return TelegramApprovalChannel(**kw)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: Telegram ساخت نشد: {e}"])
        return None


def maybe_start_lead_boundary():
    """Trust-Engine ingress: مرزِ امضاشدهٔ HTTP (POST /api/v1/lead-candidates روی 127.0.0.1)
    را فقط اگر OCTOPUS_WIRE_LEAD_BOUNDARY=1 باشد در یک daemon-thread راه‌انداز.

    flag خاموش (پیش‌فرض، خارج از PAPER_FULL) → None، هیچ threadی، هیچ portی (بایت‌به‌بایتِ
    امروز). fail-soft: هر خطا None + alert، هرگز بوت را نمی‌کشد. loopback-only (serve خودش
    روی 127.0.0.1 bind می‌کند و دوباره enabled() را چک می‌کند — double-safe)."""
    if os.environ.get("OCTOPUS_WIRE_LEAD_BOUNDARY") != "1":
        return None
    try:
        import threading
        _syspath(str(_HERE / "legs"))
        import lead_boundary_http as _lbh   # noqa: WPS433 — lazy
        t = threading.Thread(target=_lbh.serve, daemon=True, name="lead-boundary-http")
        t.start()
        opslib.heartbeat("lead-boundary HTTP started (Trust-Engine ingress, loopback)")
        return t
    except Exception as e:  # noqa: BLE001 — ingress هرگز بوت را نمی‌کشد
        opslib.alert([f"lead-boundary start failed (non-fatal): {type(e).__name__}: {e}"])
        return None


def make_unified_bus(ledger=None, db=None):
    """ساختِ UnifiedBus. پشتِ OCTOPUS_WIRE_UNIFIED."""
    if not flag("OCTOPUS_WIRE_UNIFIED"):
        return None
    try:
        _syspath(str(_HERE))
        from unified_bus import UnifiedBus
        return UnifiedBus(ledger=ledger, db=db)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: UnifiedBus ساخت نشد: {e}"])
        return None


def make_lead_leg():
    """ساختِ LeadLeg. پشتِ OCTOPUS_WIRE_LEAD."""
    if not flag("OCTOPUS_WIRE_LEAD"):
        return None
    try:
        _syspath(str(_HERE / "legs"))
        _syspath(str(_HERE / "budget"))
        from leg import TaskPacket
        from lead_leg import LeadLeg
        packet = TaskPacket(
            # 2026-07-10: organ با §۵ِ budgets-proposed-diff هم‌راستا شد (PAINTING نه
            # LEAD_PAINTING) — تا verdict مالک روی diff، پا incubating می‌ماند (INV-14)
            # و بعد از اعمالِ diff بدون تغییرِ کدِ دیگر active می‌شود.
            leg_id="lead-naghshi", organ="PAINTING",
            read_allowlist=("03 - Projects/Lead-نقاشی/PROJECT.md",),
            tools=("draft_quote",), budget_aud=5.0)
        return LeadLeg(packet, organ_table=opslib.organ_table())
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: LeadLeg ساخت نشد: {e}"])
        return None


# LEG-08 (2026-07-13): make_ziman_leg و ziman_beatِ «نسخهٔ اول» (dead duplicate) از
# اینجا حذف شدند — نسخهٔ زندهٔ غنی‌تر پایین‌تر است (§ Z · Ziman limb): singleton via
# _ZIMAN_STATE + status_snapshot/telegram_digest/biology + persist به ORGANISM-STATE.ziman،
# با امضایِ ziman_beat(leg=None, beat, doctor=…) که organism.py صدا می‌زند. تعریفِ دومی
# بایندِ نهایی بود → این جفتِ اول عملاً هرگز اجرا نمی‌شد (module-level shadowing).


def make_cartographer_leg():
    """ساختِ CartographerLeg. پشتِ OCTOPUS_WIRE_CARTOGRAPHER.
    ⚠️ عمداً در PAPER_FULL_FLAGS نیست → پیش‌فرض خاموش (incubating) تا verdictِ مالک (گام ۵).
    read-only floor، propose-only ceiling؛ هیچ send/publish/spend. organ=CARTOGRAPHER در
    budgets نیست → money_link=incubating (هرگز بودجه رزرو نمی‌کند).
    """
    if not flag("OCTOPUS_WIRE_CARTOGRAPHER"):
        return None
    try:
        _syspath(str(_HERE / "legs"))
        _syspath(str(_HERE / "budget"))
        from cartographer_leg import CartographerLeg, default_packet
        return CartographerLeg(default_packet(), organ_table=opslib.organ_table())
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: CartographerLeg ساخت نشد: {e}"])
        return None


# ── Mining leg (2026-08-06، رأیِ مالک سندِ ۲۰ §۲.۲: «کد رو ببر سمت factory-function») ──
# تناقضِ ۲.۲: test_mining_wiring.py انتظارِ make_mining_leg()/mining_beat() داشت ولی Mining
# واقعاً با `_BUSINESS_LEGS_SPEC` (status فقط‌خواندنی) ساخته می‌شد — ۶ قرمز از ۰۸-۰۱. مهاجرت
# به factory-function (هم‌الگویِ lead/cartographer) تا leg object قابل‌ساخت/تست‌پذیر بشه.
# organ="MINING" در budgets نیست → money_link="incubating" (هرگز reserve نمی‌کند).
# propose-only/read-only مطلق: زیرکلاسِ مستقیمِ Leg، صفر send/publish/pay/trade.
def make_mining_leg():
    """ساختِ پای Mining. پشتِ OCTOPUS_WIRE_MINING.
    ⚠️ عمداً در PAPER_FULL_FLAGS نیست → پیش‌فرض خاموش (incubating) تا verdictِ مالک.
    skeletonِ صادقانه: read-only floor، propose-only ceiling؛ هیچ send/publish/spend.
    organ=MINING در budgets نیست → money_link=incubating (INV-14). brains دو-نیمکره‌ی
    سخت‌افزار/کشف‌سکه (هم‌الگوی mining_leg.py) ولی هرگز اجرا نمی‌شوند (propose-only)."""
    if not flag("OCTOPUS_WIRE_MINING"):
        return None
    try:
        _syspath(str(_HERE / "legs"))
        _syspath(str(_HERE / "budget"))
        from leg import Leg, TaskPacket
        packet = TaskPacket(
            leg_id="mining-fleet",
            organ="MINING",                       # در budgets.yaml نیست → incubating
            read_allowlist=("03 - Projects/Mining/Mining.md",),
            tools=("status_snapshot",),           # فقط read-only، صفر اکشنِ خارجی
            budget_aud=0.0,                       # $0 — read-only، هرگز reserve
            spawn=0,
            secrets=(),
        )
        return Leg(packet, organ_table=opslib.organ_table())
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: MiningLeg ساخت نشد: {e}"])
        return None


def mining_beat(mining_leg, beat: int = 0) -> dict | None:
    """یک ضربانِ سبک برای پای Mining — فقط status (سنتینلِ کهنگیِ سخت‌افزار/سکه).
    پشتِ OCTOPUS_WIRE_MINING (پیش‌فرض خاموش). STOP/HALT مقدم. content-free.
    خودِ beat هیچ emit/mutate نمی‌کند؛ هم‌الگویِ cartographer_beat.
    هیچ Telegram/publish/send/spend از این مسیر نیست. $0 آفلاین."""
    if not flag("OCTOPUS_WIRE_MINING"):
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    if leg_paused("mining"):
        return None   # مکثِ تک‌پا از مرکزِ تلگرام (runtime)
    if mining_leg is None:
        return None
    try:
        return {
            "leg_id": mining_leg.packet.leg_id,
            "organ": "MINING",
            "money_link": mining_leg.money_link,     # "incubating"
            "autonomy_floor": "read-only",
            "read_only": True,
            "propose_only": True,
            "outward_execution": False,
            "beat": beat,
            # دو مغزِ مفهومیِ Mining (skeleton — هرگز اجرا نمی‌شوند، فقط خودآگاهی):
            "brains": ["hardware_control", "coin_discovery"],
            "proposals_total": len(mining_leg._proposals_emitted),
        }
    except Exception as e:  # noqa: BLE001 — یک limb نباید ارگانیسم را بکشد
        opslib.alert([f"wiring: mining_beat خطا: {type(e).__name__}: {e}"])
        return None


# ════════════════════════════════════════════════════════════════════════════════
# W · spinal cord (نخاع) — organism ↔ LiveLoop/UnifiedBus (P-W1)
# ════════════════════════════════════════════════════════════════════════════════

def make_live_loop(bus=None, leg=None, doctor=None, channel=None, brain=None,
                   studio=None, effect_status_fn=None):
    """ساختِ LiveLoop روی همان bus که organism ساخته. مغز + بدن روی یک نخاع.
    پشتِ OCTOPUS_WIRE_UNIFIED (اگر bus نباشد → LiveLoop یک busِ in-memory می‌سازد،
    که برای تست کافی است ولی LIVE_FLAG_NEEDED برای production). هرگز None برنمی‌گرداند
    اگر LiveLoop import شود — همیشه یک instance. fail-soft: استثنا → None.

    عقب‌رو: اگر bus=None و UnifiedBus هم نباشد → LiveLoop._InMemoryBus درست می‌کند.
    صفر effectorِ خودکار — publish/subscribe فقط. settle فقط از approval_channel/EffectorGate."""
    try:
        _syspath(str(_HERE))
        from live_loop import LiveLoop
        kw = dict(bus=bus, brain=brain, studio=studio, cockpit=None,
                  approval_channel=channel, doctor=doctor,
                  effect_status_fn=effect_status_fn)
        if leg is not None:
            kw["leg"] = leg   # W-3 (2026-07-10): پارامترِ leg دیگر drop نمی‌شود
        try:
            return LiveLoop(**kw)
        except TypeError:
            kw.pop("leg", None)   # LiveLoop قدیمی بدونِ leg — عقب‌رو امن
            return LiveLoop(**kw)
    except Exception as e:  # noqa: BLE001 — LiveLoop اختیاریِ additive
        opslib.alert([f"wiring: LiveLoop ساخت نشد: {e}"])
        return None


def publish_tick_signals(live_loop, *, beat=None, neural_result=None,
                         rhythm_state=None, spectral_result=None,
                         afferent_status=None, doctor_result=None) -> int:
    """سیگنال‌های موجودِ یک tick را به bus منتشر کن — از طریقِ LiveLoop.
    هر سیگنال فقط اگر داده‌اش موجود باشد publish می‌شود (نباید None پابلیش کنیم).
    kill-switch: اول STOP. advisory فقط — هیچ effector. $0.

    خروجی: تعدادِ سیگنال‌های publishشده (برای observability/self-test).

    توجه: این تابع از publish_*_advisoryهای LiveLoop استفاده می‌کند تا منطقِ
    wiring در wiring.py بماند، نه در organism.py (اصلِ جداییِ concern)."""
    if live_loop is None:
        return 0
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return 0
    n = 0
    try:
        if rhythm_state:
            live_loop.publish_rhythm_advisory(rhythm_state)
            n += 1
        if spectral_result:
            live_loop.publish_spectral_advisory(spectral_result)
            n += 1
        if afferent_status:
            live_loop.publish_afferent_advisory(afferent_status)
            n += 1
        if doctor_result:
            live_loop.publish_doctor_advisory(doctor_result)
            n += 1
    except Exception as e:  # noqa: BLE001 — §۴: خطای خاموش ممنون، ولی publish نباید tick را بکشد
        opslib.alert([f"wiring: publish_tick_signals خطا: {type(e).__name__}: {e}"])
    return n


# ════════════════════════════════════════════════════════════════════════════════
# L · LeadLeg autonomous loop — HLC + ack + propose-only (P-L1)
# (LEG-08: ziman_beatِ «نسخهٔ اول» که اینجا بود حذف شد — نسخهٔ زندهٔ § Z پایین‌تر است.)
# ════════════════════════════════════════════════════════════════════════════════

def _cartographer_map_signal():
    """(map_updated_iso, drift_count) — read-only، fail-soft، content-free.
    آخرین `06 - Architecture Maps/MASTER-ARCHITECTURE-*.md` و شمارِ فایل‌های .py در `_ops`
    که mtimeشان از تاریخِ نقشه جدیدتر است (= دریفتِ کد از زمانِ ترسیمِ خودنگاره).
    هیچ محتوایی خوانده نمی‌شود جز خطِ `updated:` نقشه (metadata)."""
    import re as _re
    from datetime import datetime as _dt
    try:
        vault = opslib.STATE_DIR.parent.parent               # _ops/state → vault root
        maps = sorted((vault / "06 - Architecture Maps").glob("MASTER-ARCHITECTURE-*.md"))
        if not maps:
            return None, 0
        m = _re.search(r"^updated:\s*(\S+)",
                       maps[-1].read_text("utf-8", errors="replace"), _re.M)
        updated = m.group(1).strip() if m else None
        drift = 0
        if updated:
            try:
                cutoff = _dt.fromisoformat(updated).timestamp()
                for p in (vault / "_ops").rglob("*.py"):
                    if "__pycache__" in p.parts:
                        continue
                    try:
                        if p.stat().st_mtime > cutoff:
                            drift += 1
                    except OSError:
                        continue
            except (ValueError, OSError):
                drift = 0
        return updated, drift
    except Exception:  # noqa: BLE001 — سیگنال اختیاری؛ نبودش نباید beat را بکشد
        return None, 0


def cartographer_beat(cartographer_leg, beat: int = 0) -> dict | None:
    """یک ضربانِ سبک برای CartographerLeg — فقط status (سنتینلِ کهنگیِ نقشه).
    پشتِ OCTOPUS_WIRE_CARTOGRAPHER (پیش‌فرض خاموش). STOP/HALT مقدم. content-free.
    خودِ beat هیچ emit/mutate نمی‌کند؛ propose_refresh فقط on-demand صدا زده می‌شود.
    هیچ Telegram/publish/send/spend از این مسیر نیست."""
    if not flag("OCTOPUS_WIRE_CARTOGRAPHER"):
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    if leg_paused("cartographer"):
        return None   # مکثِ تک‌پا از مرکزِ تلگرام (runtime)
    if cartographer_leg is None:
        return None
    try:
        s = cartographer_leg.tick()
        map_updated, drift = _cartographer_map_signal()      # read-only FS metadata
        a = cartographer_leg.assess_map(map_updated, drift_count=drift)
        return {
            "leg_id": s.get("leg_id", "vault-cartographer"),
            "organ": s.get("organ", "CARTOGRAPHER"),
            "money_link": s.get("money_link", "incubating"),
            "autonomy_floor": "read-only",
            "read_only": True,
            "proposals_total": s.get("proposals_emitted", 0),
            "propose_only": True,
            "outward_execution": False,
            "beat": beat,
            # ── drift-pulse (سیگنالِ واقعی؛ beat فقط محاسبه/برمی‌گرداند — نه emit/mutate) ──
            "map_updated": a.get("map_updated"),
            "map_age_days": a.get("age_days"),
            "map_stale": a.get("stale"),
            "drift_files": a.get("drift_files"),
            "refresh_recommended": a.get("refresh_recommended"),
            "mood": a.get("mood"),
        }
    except Exception as e:  # noqa: BLE001 — یک limb نباید ارگانیسم را بکشد
        opslib.alert([f"wiring: cartographer_beat خطا: {type(e).__name__}: {e}"])
        return None


# T3 (2026-07-25): مکملِ phi-timeout ِ chrono — وقتی خودِ لِگ استثنا می‌دهد،
# نوع+پیام+آخرین فریم را در state/legs/<leg>-last-error.json پایدار ثبت کن.
# تا امروز استثنا فقط alert می‌شد و علتِ واقعیِ خاموشیِ لِگ هرگز روی دیسک نمی‌ماند.
def _record_leg_error(leg_id: str, exc: BaseException) -> None:
    """ثبتِ آخرین خطای واقعیِ لِگ — فقط نوشتنی، atomic، هرگز beat را نمی‌کشد."""
    try:
        import json as _json
        import traceback as _tb
        frames = (_tb.extract_tb(exc.__traceback__)
                  if getattr(exc, "__traceback__", None) is not None else [])
        last = frames[-1] if frames else None
        ctx = {"leg": str(leg_id or "?"), "ts": opslib.now_iso(),
               "reason": "exception",
               "error_type": type(exc).__name__,
               "error": str(exc)[:300],
               "frame": (f"{last.filename}:{last.lineno} in {last.name}"
                         if last else None)}
        d = opslib.STATE_DIR / "legs"
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{ctx['leg']}-last-error.json"
        tmp = p.with_suffix(".tmp")
        tmp.write_text(_json.dumps(ctx, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, p)
    except Exception:  # noqa: BLE001 — ثبتِ خطا هرگز beat را نمی‌کشد
        pass


def leg_beat(lead_leg, pacemaker=None, beat: int = 0) -> dict | None:
    """هر tick: LeadLeg را در حلقهٔ ضربان بران — HLC محلی بزند + ack + کارِ propose-only.
    پشتِ OCTOPUS_WIRE_LEAD_TICK (پیش‌فرض خاموز = no-op). kill-switch: اول STOP.

    آبجکتِ LeadLeg را به یک LegHandle/HLC روی pacemaker.bus می‌بند (اگر نباشد، ثبت می‌کند).
    سپس leg_handle.event() را صدا می‌زند → HLC محلی +۱ و ack حیات (TINV-1، TINV-4).
    هیچ effector؛ پا فقط proposal تولید می‌کند (propose-only مطلق). settle فقط از
    approval_channel/EffectorGate (دست‌نخورده). single-writer حفظ: LegHandle فقط در حافظه
    بافر می‌کند، pacemaker تنها writer دیسک است.

    خروجی: {leg_id, hlc, events_this_beat, money_link, proposals_emitted} یا None (advisory)."""
    if not flag("OCTOPUS_WIRE_LEAD_TICK"):
        return None   # flag خاموش = no-op (no regression)
    if leg_paused("lead"):
        return None   # مکثِ تک‌پا از مرکزِ تلگرام (runtime)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch
    if lead_leg is None or pacemaker is None:
        return None   # بدونِ leg یا pacemaker → نمی‌توان HLC زد
    try:
        bus = getattr(pacemaker, "bus", None)
        if bus is None:
            return None
        leg_id = lead_leg.packet.leg_id
        # ثبتِ LegHandle روی bus (idempotent — اگر هست، همان را برمی‌گرداند)
        handle = bus.register_leg(leg_id)
        # HLC محلی +۱ + ack حیات (پا یک «رویداد» تولید کرد = زنده است)
        hlc = handle.event()
        # W-3 (2026-07-10): آخرین HLC روی خودِ leg — proposalهای بعدی مهرِ زمانِ علّی بگیرند
        try:
            lead_leg.last_hlc = tuple(hlc)
        except Exception:  # noqa: BLE001 — مهرِ HLC هرگز beat را نمی‌کشد
            pass
        # status فقط‌خواندنی (propose-only — هیچ effector)
        st = lead_leg.status()
        out = {"leg_id": leg_id, "hlc": list(hlc),
               "events_this_beat": handle.events_this_beat,
               "last_beat_seen": handle.last_beat_seen,
               "money_link": st.get("money_link"),
               "proposals_emitted": st.get("proposals_emitted", 0),
               "propose_only": True}
        # ── LEG-02/03/05 (money · DRY): زنجیرهٔ درآمدِ Lead پشتِ OCTOPUS_WIRE_LEAD_DRAFT
        # (پیش‌فرض خاموش و عمداً خارج از PAPER_FULL_FLAGS → حتی در profileِ paper-full هم
        # روشن نمی‌شود). با flag خاموش این بلوک عیناً no-op است (بایت‌به‌بایتِ رفتارِ فعلی).
        # روشن = فقط artifact/draft می‌سازد؛ هیچ ارسال/تماس/ایمیل/پرداخت. fail-soft.
        if flag("OCTOPUS_WIRE_LEAD_DRAFT"):
            try:
                out["lead_chain"] = _lead_draft_chain(lead_leg, beat=beat)
            except Exception as _de:  # noqa: BLE001 — §۴: زنجیرهٔ درآمد نباید beat را بکشد
                opslib.alert([f"wiring: lead_draft_chain خطا: {type(_de).__name__}: {_de}"])
        return out
    except Exception as e:  # noqa: BLE001 — §۴: leg نباید tick را بکشد
        opslib.alert([f"wiring: leg_beat خطا: {type(e).__name__}: {e}"])
        try:   # T3: علتِ واقعی پایدار ثبت شود (نه فقط alertِ زودگذر)
            _record_leg_error(getattr(getattr(lead_leg, "packet", None), "leg_id", "?"), e)
        except Exception:  # noqa: BLE001
            pass
        return None


def _lead_draft_chain(lead_leg, beat: int = 0) -> dict:
    """LEG-05 · دنبالهٔ زنجیرهٔ درآمدِ Lead به‌صورت DRY (propose-only مطلق).

    پشتِ OCTOPUS_WIRE_LEAD_DRAFT از leg_beat صدا زده می‌شود.
    2026-07-15 (مرحلهٔ ۵ نقشهٔ لید): probeِ ساختگیِ LEAD-PROBE حذف شد — draftِ واقعی
    حالا در lead_discovery_beat با attribution_id واقعی + lead_to_intake ساخته می‌شود
    (create_quote دیگر یتیم نیست). این‌جا فقط قدمِ بعدیِ زنجیره می‌ماند:
      LEG-05: برای draftهای *واقعیِ* pending (state/legs/lead-drafts/)، حداکثر یکی
      در هر beat، create_invoice (artifact). هرگز mark_paid و هرگز reconcileِ واقعی.
    هیچ‌چیز پول/بیرون را لمس نمی‌کند؛ همه محلی + fail-soft."""
    out = {"drafted": False, "invoice": None}
    # LEG-05: invoice artifact از draftِ واقعیِ pending (DRY — بدونِ mark_paid/reconcile)
    try:
        _syspath(str(_HERE / "legs"))
        import lead_quote as _lq          # noqa: WPS433 — lazy
        import invoice as _inv            # noqa: WPS433 — lazy
        pend = _lq.pending()
        if pend:
            aid = str((pend[0] or {}).get("attribution_id") or "")
            if aid:
                out["drafted"] = True     # draftِ واقعیِ pending وجود دارد (نه probe)
                r = _inv.create_invoice(aid)   # persist سندِ invoice؛ paid فقط اگر از قبل CONFIRMED (read-only fold)
                out["invoice"] = r.get("inv_number") if isinstance(r, dict) and r.get("ok") else None
    except Exception as _ie:  # noqa: BLE001 — invoice نباید زنجیره را بکشد
        opslib.alert([f"wiring: lead invoice خطا: {type(_ie).__name__}: {_ie}"])
    return out


# ─── W-2 · Doctor hook به Pacemaker ────────────────────────────────────────────
def doctor_beat(doctor, beat: int, trace: dict | None = None) -> dict | None:
    """هر N beat دکتر را اجرا کن. kill-switch: اول STOP را چک کن.
    اگر doctor نباشد → None. propose-only: هیچ merge."""
    if doctor is None:
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    every_n = int(os.environ.get("CHRONO_DOCTOR_EVERY_N_BEATS", "1440"))   # روزانه
    if beat <= 0 or every_n <= 0:
        return None   # ضربان ۰/منفی هرگز fire نمی‌کند (گاردِ fresh-db)
    # ضدِ aliasing (2026-07-10): tick ارگانیسم (۳۰۰s) ضربانِ ۶۰s را نمونه‌برداری می‌کند و
    # ممکن است دقیقاً مضربِ N دیده نشود → به‌جای «beat % N == 0»، عبور از پنجرهٔ N-تایی.
    epoch = beat // every_n
    last = getattr(doctor, "_beat_epoch_fired", 0)
    if not isinstance(last, int):
        last = 0   # doctorهای mock/قدیمی بدونِ attr
    if epoch < 1 or epoch <= last:
        return None
    try:
        doctor._beat_epoch_fired = epoch
        return doctor.run_cycle(beat=beat, trace=trace)
    except Exception as e:  # noqa: BLE001 — دکتر نباید ضربان را بکشد
        opslib.alert([f"wiring: doctor.run_cycle خطا: {e}"])
        return None


def doctor_selfknowledge_beat(beat: int = 0) -> dict | None:
    """حلقهٔ خودشناسیِ دکتر (2026-07-18، رأی مالک «باهوش و فعال») پشتِ
    OCTOPUS_WIRE_DOCTOR_SELFKNOW (پیش‌فرض خاموش → no-op). «به‌محضِ روشن‌شدن»: چون
    _EPOCH_STATE در بوت صفر می‌شود، اولین tick شلیک می‌کند؛ سپس هر
    CHRONO_DOCTOR_SELFKNOW_EVERY_N_BEATS (پیش‌فرض ۳۰ ≈ نیم‌ساعت). فقط‌خواندنی، $0 محلی
    (Ollama/هیوریستیک)، در threadِ daemon تا tick بلاک نشود. ترس قفلش نمی‌کند: این
    یادگیری است نه تغییر — همان چیزی که بن‌بستِ ترس را دور می‌زند."""
    if not flag("OCTOPUS_WIRE_DOCTOR_SELFKNOW"):
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    every_n = int(os.environ.get("CHRONO_DOCTOR_SELFKNOW_EVERY_N_BEATS", "30"))
    if not _epoch_fire("doctor_selfknow", beat, every_n):
        return None
    try:
        _dp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "doctor")
        _syspath(_dp)
        import self_knowledge  # noqa: E402
        started = self_knowledge.run_async()   # non-blocking daemon thread
        return {"self_knowledge": "spawned" if started else "busy"}
    except Exception as e:  # noqa: BLE001 — خودشناسی نباید ضربان را بکشد
        opslib.alert([f"doctor_selfknowledge_beat error (non-fatal): {type(e).__name__}: {e}"])
        return None


def synapse_beat(beat: int = 0) -> dict | None:
    """اندامِ SENSE (C8، ۲۰۲۶-۰۷-۲۸) — حسِ خود-ارجاعیِ ریاضیِ ارگانیسم روی
    تله‌متریِ خودش. سه ماژولِ synapse کاملاً ساخته بودند ولی **ادغامِ رانتایمِ صفر**
    داشتند (هیچ beat/وایرینگ/فلگی آن را صدا نمی‌زد)؛ این اولین وصل‌کردن است.

    پشتِ OCTOPUS_SYNAPSE_ENABLED (پیش‌فرض خاموش → no-op کامل). هر
    CHRONO_SYNAPSE_EVERY_N_BEATS (پیش‌فرض ۶۰ ≈ یک ساعت با تیکِ ۶۰s). $0 (صرفاً ریاضی،
    صفر LLM)، propose-only (خروجی فقط proposal + سریِ زمانیِ صداقت)، fail-closed.
    ترس قفلش نمی‌کند: این مشاهدهٔ فقط‌خواندنی است، نه تغییر.

    چرا مهم: پچِ ایمن (C4) باید از حسِ Δ خود تغذیه کند. تا امروز ارگانیسم حسِ
    خود-ارجاعی نداشت — یعنی حتی نمی‌دانست آیا ضربانِ خودش ساختار دارد یا نه."""
    if not flag("OCTOPUS_SYNAPSE_ENABLED"):
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    every_n = int(os.environ.get("CHRONO_SYNAPSE_EVERY_N_BEATS", "60"))
    if not _epoch_fire("synapse_sense", beat, every_n):
        return None
    try:
        _sp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synapse")
        _syspath(_sp)
        import sense  # noqa: E402 — lazy
        r = sense.sense_once()
        if r.get("ran"):
            return {"synapse": r.get("kind", "observation"), "cpm": r.get("cpm")}
        return None   # daily-cap / no-events / degraded → بی‌صدا
    except Exception as e:  # noqa: BLE001 — Sense نباید ضربان را بکشد
        opslib.alert([f"synapse_beat error (non-fatal): {type(e).__name__}: {e}"])
        return None


def wire_proposal_buttons(*, channel=None, live_loop=None) -> bool:
    """G3 arc (ported to master 2026-07-18): هوکِ رأیِ کارتِ پیشنهاد را به کانالِ تلگرام
    وصل کن. پشتِ OCTOPUS_WIRE_PROPOSAL_BUTTONS (پیش‌فرض خاموش). با فلگ خاموش → False و
    کانال دست‌نخورده (کارت‌ها همان متنِ بی‌دکمهٔ قبلی). measurement-only: مسیرِ 'prop'
    هرگز settle/ledger نمی‌زند — جدا از 'app' (پول)."""
    if os.environ.get("OCTOPUS_WIRE_PROPOSAL_BUTTONS") != "1":
        return False
    if channel is None or live_loop is None:
        return False
    if not callable(getattr(live_loop, "record_proposal_outcome_by_token", None)):
        return False
    channel._proposal_hook = live_loop.record_proposal_outcome_by_token
    # GAP-3 (C2-C): بازسازیِ کارت‌های معوق از SoTِ durable (outcomes.db) — RESURRECTION
    # فاز ۶ (PROJECTIONS). fail-soft؛ dedupeِ بینِ بوت‌ها durable است (idempotency در DB)؛
    # DB غایب/فلگ خاموش → skip بی‌صدا. UI projection است، نه حقیقت.
    try:
        import sys as _sys
        _op = str(Path(__file__).resolve().parent / "outcomes")
        if _op not in _sys.path:
            _sys.path.insert(0, _op)
        import deferral_rebuild as _dr   # noqa: WPS433 — lazy
        _res = _dr.rebuild_deferred_cards(live_loop, channel)
        if _res.get("rebuilt"):
            opslib.heartbeat(f"deferral rebuild: {_res}")
    except Exception:  # noqa: BLE001 — بازسازی هرگز بوت را نمی‌کشد
        pass
    return True


def wire_summary() -> dict:
    """خلاصهٔ وضعیتِ wiring (برای startup-log / state)."""
    return {
        "wire_doctor": flag("OCTOPUS_WIRE_DOCTOR"),
        "wire_telegram": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
        "wire_unified": flag("OCTOPUS_WIRE_UNIFIED"),
        "wire_lead": flag("OCTOPUS_WIRE_LEAD"),
        "wire_neural": flag("OCTOPUS_WIRE_NEURAL"),
        "wire_school": flag("OCTOPUS_WIRE_SCHOOL"),
        "wire_consolidation": flag("OCTOPUS_WIRE_CONSOLIDATION"),
        "wire_live_loop": flag("OCTOPUS_WIRE_UNIFIED"),   # نخاع = bus + LiveLoop
        "wire_evolution": flag("OCTOPUS_WIRE_EVOLUTION"), # P-N1: Doctor evolution
        "wire_box": flag("OCTOPUS_WIRE_BOX"),             # P-N2: Box-of-Agents
        "wire_leg_tick": flag("OCTOPUS_WIRE_LEAD_TICK"),  # P-L1: LeadLeg HLC loop
        # مغزهای پولی (2026-07-25): این سه فلگ در هیچ‌کدام از ۴۵ کلیدِ این خلاصه نبودند،
        # پس «مسلح بودنِ مسیرِ پولی» از state/کاکپیت دیده نمی‌شد — تنها راهِ فهمیدنش
        # خواندنِ فایلِ رازدارِ flags.cmd بود. اینها نامِ فلگ‌اند و مقدارِ بولی، نه secret.
        "paid_governor_router": flag("OCTOPUS_GOVERNOR_USE_ROUTER"),
        "paid_heart_doctor_router": flag("OCTOPUS_HEART_DOCTOR_USE_ROUTER"),
        "paid_doctor_selfknow": flag("OCTOPUS_DOCTOR_SELFKNOW_PAID"),
        # arm_gate تزئینی است تا وقتی OCTOPUS_REQUIRE_ARM ست نشود (arm_gate.py:51 —
        # بدونِ آن `require` یک pass-through است). قابلیتِ مسلح‌شدهٔ ۲۰۲۶-۰۷-۲۵
        # (cortex_paid) در arm_gate.DANGEROUS فهرست است ولی سایتِ فراخوانش چک نمی‌کند،
        # پس «قفلِ دومِ مسیرِ پولی» عملاً باز است. این کلید فقط آن را **دیدنی** می‌کند؛
        # اعمالِ واقعی‌اش رأیِ مالک است (VQ-ARM-001) چون روشن‌کردنش بدونِ tokenِ arm
        # می‌تواند همان مغزهای پولی را که مالک امروز مسلح کرد ببندد.
        "arm_gate_enforcing": flag("OCTOPUS_REQUIRE_ARM"),
        "wire_actuator": flag("OCTOPUS_WIRE_ACTUATOR"),   # گاف #۱: اکچوایتورِ approval (visibility)
        # غربالِ prompt-injection روی هر ورودیِ LLM (۲۰۲۶-۰۸-۰۱). سیم‌کشی‌اش از قبل کامل
        # بود — model_router.ask + چهار callerِ مستقیم — ولی در هیچ‌کدام از ۴۹ کلیدِ این
        # خلاصه نبود، پس تنها سطحی که ARMING-ORDER «سنجهٔ قطعی» می‌نامدش
        # (`state/ORGANISM-STATE.json`، خروجیِ همین تابع **بعد از** apply_profile)
        # دربارهٔ فنس ساکت بود: مالک نمی‌توانست بعد از مسلح‌کردن تأییدش کند.
        # عمداً در PAPER_FULL_FLAGS **نیست** → غیاب یعنی خاموش، نه روشن.
        "wire_context_fence": flag("OCTOPUS_WIRE_CONTEXT_FENCE"),
        "wire_ideas": flag("OCTOPUS_WIRE_IDEAS"),        # P-I: idea-graph engine
        "wire_spectral": flag("OCTOPUS_WIRE_SPECTRAL"),  # P-spectral: spectral bottleneck
        "wire_rhythm": rhythm_enabled(),  # CR-B0 independent rollback؛ bare-safe
        "wire_circadian": flag("OCTOPUS_WIRE_NEURAL"),   # circadian (shares neural flag)
        "wire_sprint": flag("OCTOPUS_WIRE_NEURAL"),      # sprint (shares neural flag)
        "wire_barbell": flag("OCTOPUS_WIRE_BARBELL"),    # barbell allocation
        "wire_debate": flag("OCTOPUS_WIRE_DEBATE"),      # debate loop
        "wire_scheduler": flag("OCTOPUS_WIRE_SCHEDULER"), # B6: F19 scheduler
        "wire_reconcile": flag("OCTOPUS_WIRE_RECONCILE"), # A1: Track-B reconcile
        "wire_fitness": flag("OCTOPUS_WIRE_FITNESS"),    # A2: outbox/EXPERIENCE
        "wire_epistemics": flag("OCTOPUS_WIRE_EPISTEMICS"), # Phase 5: epistemics wiring
        "wire_bcm": flag("OCTOPUS_WIRE_BCM"),            # Blueprint P3: BCM forgetting
        "wire_sparse": flag("OCTOPUS_WIRE_SPARSE"),      # Blueprint P4: sparse input filter
        "wire_chamber_t": flag("OCTOPUS_WIRE_CHAMBER_T"), # Blueprint P5 (RED): chamber temperature
        # P11 (truth-map 2026-07-17): این بلاک خودش را جدولِ حقیقتِ wiring جا می‌زد ولی
        # ~۱۰ لایهٔ روشن را کم‌شماری می‌کرد — داشبورد/آدیت باید یک بلاک را بخواند.
        "wire_heart": flag("OCTOPUS_WIRE_HEART"),
        "wire_heart_work": flag("OCTOPUS_WIRE_HEART_WORK"),
        "wire_bio": flag("OCTOPUS_WIRE_BIO"),
        "wire_pulse": flag("OCTOPUS_WIRE_PULSE"),
        "wire_selfheal": flag("OCTOPUS_WIRE_SELFHEAL"),
        "wire_pocketsmith": flag("OCTOPUS_WIRE_POCKETSMITH"),
        "wire_web_research": flag("OCTOPUS_WIRE_WEB_RESEARCH"),
        "wire_ziman": flag("OCTOPUS_WIRE_ZIMAN"),
        "wire_cartographer": flag("OCTOPUS_WIRE_CARTOGRAPHER"),
        "wire_fisher": flag("OCTOPUS_WIRE_FISHER"),
        "wire_mining": flag("OCTOPUS_WIRE_MINING"),
        "wire_email": flag("OCTOPUS_WIRE_EMAIL"),
        "wire_ingest": flag("OCTOPUS_WIRE_INGEST"),
        "wire_harvest": flag("OCTOPUS_WIRE_HARVEST"),
        # D1 (فاز D): وصلِ رأیِ کارتِ لید به لایهٔ اثر (lead_effect_gate.on_lead_verdict).
        # پیش‌فرض خاموش = no-op مطلق؛ transport همچنان NOT_ARMED. رأیِ owner-gated برای روشن‌کردن.
        "wire_lead_verdict_effect": flag("OCTOPUS_WIRE_LEAD_VERDICT_EFFECT"),
        "profile": resolve_profile(),                    # P-W3: boot profile
        "doctor_every_n": int(os.environ.get("CHRONO_DOCTOR_EVERY_N_BEATS", "1440")),
        "consolidation_every_n": int(os.environ.get("CHRONO_CONSOLIDATION_EVERY_N_BEATS", "720")),
        "afferent_every_n": int(os.environ.get("CHRONO_AFFERENT_EVERY_N_BEATS", "1440")),
    }


# ════════════════════════════════════════════════════════════════════════════════
# W · neural wiring — ۸ ماژول + school_bridge به tick وصل، پشتِ flag
# ════════════════════════════════════════════════════════════════════════════════

def make_rhythm():
    """ساختِ Rhythm موجودِ CR-B0، پشتِ فلگِ مستقلِ tracked.

    env صریح ``OCTOPUS_WIRE_CHRONO_RHYTHM=0`` kill-switch است؛ اگر env غایب
    باشد رأیِ tracked فعال می‌ماند. هستهٔ ریتم هیچ IO/ledger ندارد و authorityِ
    مستقیم نمی‌گیرد؛ فقط pulse-arbiter می‌تواند spacing دیواری را مصرف کند.
    """
    if not rhythm_enabled():
        return None
    try:
        _syspath(str(_HERE / "chrono_rhythm"))
        from rhythm import Rhythm
        return Rhythm()
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: Rhythm ساخت نشد: {e}"])
        return None


def rhythm_beat(rhythm, readiness: float = 0.6, stress: float = 0.2,
                novelty: float = 0.3, sigma: float = 0.5) -> dict | None:
    """یک گامِ Rhythm → mode_color + T_beat + HRV. advisory فقط.
    kill-switch: اول STOP. خروجی برای neural_beat (rhythm input) + publish_advisory."""
    if rhythm is None:
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    try:
        st = rhythm.step(readiness=readiness, stress=stress,
                         novelty=novelty, sigma=sigma)
        return {"mode_color": st.mode_color, "T_beat": round(st.T_beat, 2),
                "hrv": round(st.hrv, 4), "tau": round(st.tau, 3),
                "mode_focus": st.mode_focus}
    except Exception as e:  # noqa: BLE001 — §۴
        opslib.alert([f"wiring: rhythm_beat خطا: {type(e).__name__}: {e}"])
        return None


def make_circadian():
    """ساختِ CircadianMap (آگاهیِ ساعتِ روز). پشتِ OCTOPUS_WIRE_NEURAL."""
    try:
        _syspath(str(_HERE / "neural"))
        from circadian import CircadianMap
        return CircadianMap()
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: CircadianMap ساخت نشد: {e}"])
        return None


def circadian_readiness(circadian, hour: int | None = None) -> dict | None:
    """readiness ساعتِ روز → advisory. kill-switch اول."""
    if circadian is None:
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    try:
        import datetime as _dt
        h = hour if hour is not None else _dt.datetime.now().hour
        return {"hour": h, "phase": circadian.phase(h),
                "readiness": circadian.readiness(h),
                "is_maintenance": circadian.is_maintenance(h)}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: circadian_readiness خطا: {e}"])
        return None


def make_sprint_runner():
    """ساختِ SprintRunner. پشتِ OCTOPUS_WIRE_NEURAL."""
    try:
        _syspath(str(_HERE / "neural"))
        from sprint import SprintRunner
        return SprintRunner()
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: SprintRunner ساخت نشد: {e}"])
        return None


# ════════════════════════════════════════════════════════════════════════════════
# B6 · scheduler F19 — dispatcherِ propose-only (پشتِ flag)
# ════════════════════════════════════════════════════════════════════════════════

def make_scheduler():
    """ساختِ یک dispatcherِ propose-only برای F19 scheduler. پشتِ OCTOPUS_WIRE_SCHEDULER.
    dispatcher یک callable است: (task_dict) → None. task را به advisory NOTE در ledger
    تبدیل می‌کند — هیچ effector، هیچ settle. propose-only مطلق."""
    if not flag("OCTOPUS_WIRE_SCHEDULER"):
        return None
    def _dispatcher(task: dict):
        """task را به advisory NOTE تبدیل کن. propose-only — هیچ اثرِ برگشت‌ناپذیر."""
        try:
            opslib.ledger_note("SCHEDULER_DISPATCH", {
                "kind": task.get("kind", "unknown"),
                "task_ref": task.get("task_ref", ""),
                "leg_id": task.get("leg_id"),
                "due_beat": task.get("due_beat"),
                "fired_beat": task.get("fired_beat"),
                "advisory_only": True,
                "no_effector": True,
            }, actor="scheduler")
        except Exception:  # noqa: BLE001 — §۴: خطای خاموش ممنون
            opslib.alert([f"scheduler dispatch failed: {task.get('task_ref', '?')}"])
    return _dispatcher


def scheduler_seed_doctor_rfc(doctor, pacemaker):
    """یک تولیدکنندهٔ حداقلی: RFCهای دکتر را به‌عنوانِ follow-up در scheduler ثبت کن.
    پشتِ OCTOPUS_WIRE_SCHEDULER. propose-only — فقط schedule() می‌زند، نه effector."""
    if not flag("OCTOPUS_WIRE_SCHEDULER"):
        return
    if doctor is None or pacemaker is None:
        return
    try:
        # RFCهای اخیر را به‌عنوانِ follow-up در N beat ثبت کن
        for rfc_id, rfc in doctor._rfcs.items():
            if rfc.status in ("submitted", "submitted-no-channel"):
                # یک follow-up در ۱۰ beat بعدی ثبت کن (اگر تکراری نباشد)
                pacemaker.schedule(kind="rfc-followup", task_ref=rfc_id,
                                   leg_id=None, in_beats=10)
    except Exception:  # noqa: BLE001 — fail-soft
        pass


def scheduler_seed_beat(doctor=None, pacemaker=None, beat: int = 0) -> dict | None:
    """F3 wiring (2026-07-14): نقطهٔ اتصالِ آمادهٔ scheduler_seed_doctor_rfc به حلقهٔ ضربان.

    این تولیدکننده (scheduler_seed_doctor_rfc) پشتِ flag تعریف شده بود ولی هیچ‌جا صدا
    نمی‌شد (unwired). این wrapper همان producer را با kill-switch + observability به یک
    beat می‌بندد تا organism.py فقط یک خط صدا بزند (جداییِ concern: منطقِ wiring اینجا
    می‌ماند، نه در organism.py).

    پشتِ OCTOPUS_WIRE_SCHEDULER (پیش‌فرض خاموش). با flag خاموش عیناً no-op است
    (بایت‌به‌بایتِ رفتارِ فعلی: نه schedule، نه ledger، نه هیچ اثر). kill-switch اول.
    propose-only مطلق — فقط pacemaker.schedule() (صفِ anticipation، advisory)، هیچ effector.

    خروجی: {seeded: bool, beat} یا None (flag خاموش/kill/precondition/خطا)."""
    if not flag("OCTOPUS_WIRE_SCHEDULER"):
        return None   # flag خاموش = no-op (no regression)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch
    if doctor is None or pacemaker is None:
        return None   # بدونِ doctor/pacemaker چیزی برای seed نیست
    try:
        scheduler_seed_doctor_rfc(doctor, pacemaker)
        return {"seeded": True, "beat": beat, "propose_only": True}
    except Exception as e:  # noqa: BLE001 — §۴: seed نباید tick را بکشد
        opslib.alert([f"wiring: scheduler_seed_beat خطا: {type(e).__name__}: {e}"])
        return None


# ════════════════════════════════════════════════════════════════════════════════
# A1 · reconcile_beat — Track-B money reconciliation (پشتِ flag، propose-only)
# ════════════════════════════════════════════════════════════════════════════════

def reconcile_beat(reconcile_dir=None, day: str = "") -> dict | None:
    """A1: reconcile.run() را در حلقهٔ روزانه صدا بزن. پشتِ OCTOPUS_WIRE_RECONCILE.
    kill-switch اول. هرگز budget_gate.reserve صدا نزن (I2). $0، بدون spend.
    reconcile.run خودش idempotency دارد (seen set + CONFIRMED_STATES check).
    خروجی: گزارشِ reconcile یا None."""
    if not flag("OCTOPUS_WIRE_RECONCILE"):
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    try:
        import reconcile
        report = reconcile.run(reconcile_dir=reconcile_dir, write=True)
        opslib.ledger_note("RECONCILE_BEAT", {
            "confirmed": len(report.get("confirmed", [])),
            "unmatched": len(report.get("unmatched", [])),
            "double_claims": len(report.get("double_claims", [])),
            "rows_read": report.get("rows_read", 0),
            "day": day,
        }, actor="reconcile-beat")
        return report
    except Exception as e:  # noqa: BLE001 — §۴
        opslib.alert([f"wiring: reconcile_beat خطا: {type(e).__name__}: {e}"])
        return None


# ════════════════════════════════════════════════════════════════════════════════
# A1b · actuator_beat — اکچوایتورِ تصمیم‌های تأییدشده (رفعِ گاف #۱، پشتِ flag)
# ════════════════════════════════════════════════════════════════════════════════

def actuator_beat() -> dict | None:
    """اکچوایتورِ تصمیم‌های تأییدشده را بچرخان. پشتِ OCTOPUS_WIRE_ACTUATOR (پیش‌فرض
    خاموش، خارج از paper-full — approvalها شاملِ پول‌اند). kill-switch اول. $0،
    بدونِ spend، بدونِ اکشنِ بیرونی/خودکار (فقط visibility + seamِ handler)."""
    if not flag("OCTOPUS_WIRE_ACTUATOR"):
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    try:
        if str(_HERE / "cortex") not in sys.path:
            sys.path.insert(0, str(_HERE / "cortex"))
        import approval_actuator
        return approval_actuator.run()
    except Exception as e:  # noqa: BLE001 — §۴
        opslib.alert([f"wiring: actuator_beat خطا: {type(e).__name__}: {e}"])
        return None


# ════════════════════════════════════════════════════════════════════════════════
# A2 · append_outbox + EXPERIENCE — fitness feed (پشتِ flag)
# ════════════════════════════════════════════════════════════════════════════════

def append_outbox(business: str, status: str, channel: str = "",
                  to_ref: str = "", text: str = "", detail: str = "") -> bool:
    """A2: یک ردیفِ sent/rejected به outbox.jsonl append کن + EXPERIENCE به ledger.
    پشتِ OCTOPUS_WIRE_FITNESS. measure-only (فیتنس تا ۲۸ روز authoritative=False می‌ماند).
    $0، بدون spend. kill-switch اول."""
    if not flag("OCTOPUS_WIRE_FITNESS"):
        return False
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return False
    try:
        import json
        import time as _time
        outbox_path = opslib.BRAIN_DIR / "logs" / "outbox.jsonl"
        outbox_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": _time.time(),
            "business": business, "status": status, "channel": channel,
            "to_ref": to_ref, "text": text[:200], "detail": detail[:500],
        }
        with open(outbox_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        # EXPERIENCE event در ledger (measure-only)
        opslib.ledger_note("EXPERIENCE", {
            "business": business, "status": status,
            "channel": channel, "to_ref": to_ref,
        }, actor="outbox-append")
        return True
    except Exception as e:  # noqa: BLE001 — §۴
        opslib.alert([f"wiring: append_outbox خطا: {type(e).__name__}: {e}"])
        return False


# ════════════════════════════════════════════════════════════════════════════════
# Phase 5 · epistemics_beat — wiringِ epistemics به tick (پشتِ flag)
# ════════════════════════════════════════════════════════════════════════════════

def epistemics_beat(live_loop=None, beat: int = 0) -> dict | None:
    """Phase 5: هر N beat، epistemics.compute_all() را اجرا کن و خروجی را advisory publish کن.
    پشتِ OCTOPUS_WIRE_EPISTEMICS (پیش‌فرض off). kill-switch اول.
    advisory فقط — non-enforcer. no-collision: فقط annotate، نه fork.

    خروجی: گزارشِ {metrics_count, authoritative_count} یا None."""
    if not flag("OCTOPUS_WIRE_EPISTEMICS"):
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    every_n = int(os.environ.get("CHRONO_EPISTEMICS_EVERY_N_BEATS", "720"))   # ۱۲ ساعت
    if not _epoch_fire("epistemics", beat, every_n):
        return None
    try:
        from epistemics.run_offloop import compute_all
        results = compute_all()
        auth_count = sum(1 for r in results if isinstance(r, dict) and r.get("authoritative"))
        # advisory publish روی bus (نه control-path، annotate)
        if live_loop is not None:
            for r in results:
                if isinstance(r, dict) and r.get("metric"):
                    live_loop._emit_advisory("EPISTEMICS", {
                        "metric": r["metric"],
                        "value_summary": str(r.get("value"))[:120],
                        "authoritative": r.get("authoritative", False),
                        "confidence": r.get("confidence", 0),
                    })
        return {"metrics_count": len(results),
                "authoritative_count": auth_count,
                "advisory_only": True}
    except Exception as e:  # noqa: BLE001 — §۴: epistemics نباید tick را بکشد
        opslib.alert([f"wiring: epistemics_beat خطا: {type(e).__name__}: {e}"])
        return None


def _real_spectral_sigma() -> float | None:
    """σِ طیفیِ واقعی — doctor/spectral.py::estimate_sigma روی طیفِ لاپلاسینِ گرافِ
    خطا (از همان دو فایلِ state که doctor.py::_gather_trace می‌خواند:
    ORGANISM-STATE.json + telemetry-latest.json). پشتِ OCTOPUS_WIRE_HEBBIAN_SPECTRAL
    (پیش‌فرض خاموش — همان قلمروی «وقتی قلب به σِ طیفیِ واقعی وصل شد، رأیِ مالک،
    شادو-اول» که کامنتِ بالادستِ `_hebbian_signals` به آن اشاره می‌کند).
    read-only، fail-soft، $0. گرافِ بی‌یال (ارگانیسمِ سالم/بی‌خطا) → None، همان گاردِ
    دژنرهٔ spectral_mine — سلامتِ کامل هرگز σ=1.00ِ ساختگی نمی‌شود."""
    if not flag("OCTOPUS_WIRE_HEBBIAN_SPECTRAL"):
        return None   # flag خاموش = no-op (no regression)
    try:
        import json as _json
        _syspath(str(_HERE / "doctor"))
        from spectral import build_event_graph, laplacian_spectrum, estimate_sigma
        trace: dict = {"organs": {}, "errors": []}
        org_p = opslib.STATE_DIR / "ORGANISM-STATE.json"
        if org_p.exists():
            org = _json.loads(org_p.read_text("utf-8"))
            for c in (org.get("conflicts") or []):
                if isinstance(c, dict):
                    trace["errors"].append({"organ": c.get("organ", "_global"),
                                            "msg": str(c.get("msg", c.get("reason", "")))[:200]})
                elif isinstance(c, str):
                    trace["errors"].append({"organ": "_global", "msg": c[:200]})
        tel_p = opslib.STATE_DIR / "telemetry-latest.json"
        if tel_p.exists():
            tel = _json.loads(tel_p.read_text("utf-8"))
            per_organ = tel.get("per_organ_alltime_musd") or {}
            if isinstance(per_organ, dict):
                trace["organs"] = {k: {} for k, v in per_organ.items()
                                   if isinstance(v, (int, float))}
        edges, n = build_event_graph(trace)
        if n < 2 or not edges:
            return None   # گرافِ دژنره — همان گاردِ spectral_mine (سلامتِ کامل ≠ σ=1.00)
        eigvals, _L = laplacian_spectrum(edges, n)
        return estimate_sigma(eigvals)
    except Exception as e:  # noqa: BLE001 — §۴: خطای خاموش ممنون، ولی fail-soft (beat را نمی‌کشد)
        opslib.alert([f"wiring: real spectral sigma خطا: {type(e).__name__}: {e}"])
        return None


def _real_budget_depleted() -> bool | None:
    """budget.depleted واقعی — cardiac.py::status_snapshot()['budget']['depleted']
    (تنها تولیدکنندهٔ واقعیِ این مفهوم؛ خودش پشتِ OCTOPUS_WIRE_BIO دروازه دارد —
    پیش‌فرض خاموش → status_snapshot همیشه {'enabled': False} → این تابع هم None).
    فلگِ **جداگانهٔ** OCTOPUS_WIRE_HEBBIAN_CARDIAC (پیش‌فرض خاموش) تا I/Oِ per-tickِ
    تازه (خواندنِ cardiac-budget.json) فقط با تصمیمِ صریحِ مالک به داغ‌ترین حلقهٔ
    ارگانیسم اضافه شود — همان نگرانیِ هزینه‌ای که SIGNAL_DORMANT ثبت کرده بود،
    حالا پشتِ یک کلیدِ روشن/خاموشِ مجزا. read-only، fail-soft."""
    if not flag("OCTOPUS_WIRE_HEBBIAN_CARDIAC"):
        return None   # flag خاموش = no-op (no regression)
    try:
        import cardiac as _cardiac_mod
        cs = _cardiac_mod.status_snapshot()
        if not isinstance(cs, dict) or not cs.get("enabled"):
            return None   # OCTOPUS_WIRE_BIO خودش خاموش است — چیزی برای گفتن نیست
        return bool((cs.get("budget") or {}).get("depleted"))
    except Exception as e:  # noqa: BLE001 — §۴: خطای خاموش ممنون، ولی fail-soft
        opslib.alert([f"wiring: real budget depleted (cardiac) خطا: {type(e).__name__}: {e}"])
        return None


def _hebbian_signals(inputs: dict) -> list:
    """واژگانِ سیگنالِ Hebbian.

    ۲۰۲۶-۰۷-۲۶ — چرا این تابع ساخته شد. نسخهٔ قبلی دقیقاً **دو** سیگنالِ ممکن
    داشت (`green_mode` وقتی rhythm سبز است، `stable` وقتی sigma<0.8). یعنی
    associator ساختاراً نمی‌توانست بیش از **یک جفت** یاد بگیرد.
    اندازه‌گیریِ زنده: `hebbian.json` بعد از **۲۲۳۵ هم‌رخدادی** هنوز یک ردیف
    داشت — `green_mode`+`stable` با strength=1.0. مشکل «یاد نگرفته» نبود؛
    چیزی برای یادگرفتن به آن نداده بودیم. یک قاعدهٔ هبی با واژگانِ دوکلمه‌ای
    یک شمارنده است با حرفِ یونانی.

    این‌جا واژگان از حالتی می‌آید که ارگانیسم **از قبل دارد** — هیچ سنسورِ نو،
    هیچ هزینه، هیچ شبکه. سیگنال‌ها عمداً دودویی و پراکنده‌اند تا هم‌رخدادی
    معنا داشته باشد؛ چیزی که همیشه روشن است اطلاعاتی حمل نمی‌کند.

    ⚠️ این یادگیری را **ممکن** می‌کند، نه **مفید**. تا وقتی هیچ تصمیمی خروجیِ
    Hebbian را نخواند (تستِ نویزِ ۲۰۲۶-۰۷-۲۶: خروجیِ protective_override با
    ورودیِ یادگیریِ کاملاً نویزی بایت‌به‌بایت یکسان بود)، این فقط جدولِ
    غنی‌تری است. مصرف‌کننده قدمِ بعدی و رأیِ مالک است.

    پیش‌فرض خاموش (`OCTOPUS_HEBBIAN_RICH`) → واژگانِ دوکلمه‌ایِ قبلی، بایت‌به‌بایت.
    """
    # گاردِ نوع روی legacy هم لازم شد: نسخهٔ اصلی `inputs.get("spectral", {}).get(...)`
    # می‌زد و اگر آن کلید یک رشته بود AttributeError می‌داد — باگِ از-پیش-موجود که
    # تستِ متخاصمِ ۲۰۲۶-۰۷-۲۶ لوش داد. خروجی برای ورودیِ سالم بایت‌به‌بایت همان است.
    rhythm = inputs.get("rhythm") if isinstance(inputs.get("rhythm"), dict) else {}
    spectral = inputs.get("spectral") if isinstance(inputs.get("spectral"), dict) else {}
    legacy = []
    if rhythm.get("mode_color") == "GREEN":
        legacy.append("green_mode")
    try:
        if float(spectral.get("sigma", 0) or 0) < 0.8:
            legacy.append("stable")
    except (TypeError, ValueError):
        pass
    if not flag("OCTOPUS_HEBBIAN_RICH"):
        return legacy

    # ── درسِ تستِ متخاصمِ همان روز ──────────────────────────────────────────
    # (واژگانِ کاملِ ممکن در `BCM_VOCAB` پایینِ همین ماژول است — BCM باید همهٔ
    #  کلیدهای ممکن را بشناسد تا سیگنالی که *آتش نکرد* هم زوال بگیرد.)
    # نسخهٔ اولِ همین تابع باندهای low/mid/high می‌ساخت. تست گرفتش: آن یک
    # **پارتیشن** است — همیشه دقیقاً یکی آتش می‌کند، پس با هر سیگنالِ دیگری
    # هم‌رخداد می‌شود و strength را بدونِ اطلاعات بالا می‌برد. یعنی همان
    # بیماریِ `green_mode`+`stable` با واژه‌های بیشتر.
    # اصلِ درست: **فقط انحراف سیگنال است، نه حالتِ عادی.** ارگانیسمِ سالمِ
    # بی‌حادثه باید صفر سیگنال بدهد → `decay()` → use-it-or-lose-it. آن‌وقت
    # هم‌رخدادی واقعاً یعنی «این چیزهای غیرعادی با هم آمدند».
    # به همین دلیل سیگنال‌های legacy (که هر دو حالتِ عادی‌اند) در حالتِ rich
    # حمل نمی‌شوند.
    def _d(x):
        return x if isinstance(x, dict) else {}

    def _f(d, k, default=None):
        try:
            v = _d(d).get(k, default)
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    rhythm, spectral = _d(rhythm), _d(spectral)
    budget, sensory = _d(inputs.get("budget")), _d(inputs.get("sensory"))
    sig = []

    mc = str(rhythm.get("mode_color") or "").upper()
    if mc in ("AMBER", "YELLOW", "RED"):      # سبز = عادی، خبر نیست
        sig.append(f"rhythm_{mc.lower()}")
    # ⚠️ `spectral.sigma` عمداً **استفاده نمی‌شود**. ۲۰۲۶-۰۷-۲۶ ردیابی شد که آن
    # مقدار از `replication-latest.json` می‌آید (organism.py:586) و کمیتش
    # spawnهای تأییدشده ÷ سلول‌های فعال است، نه شکنندگی. چون هیچ spawnی تأیید
    # نشده، ساختاراً صفر است: ۱۰۴۹ نمونه طیِ ۱۶ روز، همه صفر. سیگنالی که
    # روی چنین مقداری سوار شود یا هرگز آتش نمی‌کند، یا — مثلِ `stable`ِ قدیمی
    # که روی `sigma<0.8` بود — همیشه آتش می‌کند و ۲۲۳۵ بار یک ثابت را می‌شمارد.
    # هر دو حالت یادگیری را روی چیزی آموزش می‌دهند که اطلاعات ندارد.
    # وقتی قلب به σِ طیفیِ واقعی وصل شد (رأیِ مالک، شادو-اول)، این سیگنال
    # برمی‌گردد — با آستانه‌ای که از دادهٔ واقعی کالیبره شده، نه از حدس.
    if spectral.get("sigma_is_replication_ratio") is False:
        s = _f(spectral, "sigma")
        if s is not None and s >= 1.2:
            sig.append("sigma_high")
    else:
        # مسیرِ نو (۲۰۲۶-۰۸-۰۶، پشتِ OCTOPUS_WIRE_HEBBIAN_SPECTRAL — پیش‌فرض خاموش):
        # organism.py/brain_worker.py را دور می‌زند (هر دو یا literalِ True هاردکد
        # می‌کنند یا اصلاً کلید را نمی‌دهند — SIGNAL_DORMANT['sigma_high']) و
        # مستقیم از doctor/spectral.py::estimate_sigma می‌خواند. با فلگ خاموش
        # `_real_spectral_sigma` بی‌درنگ None می‌دهد → این else هیچ سیگنالی اضافه
        # نمی‌کند = رفتارِ قبلی بایت‌به‌بایت.
        s = _real_spectral_sigma()
        if s is not None and s >= 1.2:
            sig.append("sigma_high")
    bp = _f(budget, "pct")
    if bp is None:
        bp = _f(budget, "used_pct")
    if bp is not None and bp > 0.8:
        sig.append("budget_tight")
    if budget.get("depleted"):
        sig.append("budget_depleted")
    elif _real_budget_depleted():
        # مسیرِ نو (۲۰۲۶-۰۸-۰۶، پشتِ OCTOPUS_WIRE_HEBBIAN_CARDIAC — پیش‌فرض خاموش):
        # payload هرگز `depleted` نمی‌دهد (SIGNAL_DORMANT['budget_depleted'])؛ اینجا
        # مستقیم از cardiac.py::status_snapshot می‌خواند. با فلگ خاموش
        # `_real_budget_depleted` همیشه None می‌دهد → این شاخه هرگز true نیست =
        # رفتارِ قبلی بایت‌به‌بایت.
        sig.append("budget_depleted")
    ar = _f(sensory, "afferent_ratio")
    if ar is not None and ar <= 0.1:
        sig.append("afferent_starved")
    er = _f(sensory, "error_rate")
    if er is not None and er > 0.2:
        sig.append("errors_high")
    return sig


# واژگانِ کاملِ سیگنال‌های انحرافی — منبعِ `known_keys` برای BCM.
# چرا لازم است: `BCM.step` فقط کلیدهایی را دنبال می‌کند که به آن داده شود، پس
# اگر فقط آتش‌کرده‌های همین تیک را بدهیم، سیگنالی که **آتش نکرد** اصلاً وجود
# نخواهد داشت و هرگز زوال نمی‌گیرد — یعنی نیمهٔ «فراموشی»ِ BCM مرده می‌ماند.
# هر سیگنالِ تازه در `_hebbian_signals` باید این‌جا هم اضافه شود؛ یک تست این را
# ماشین‌چک می‌کند تا واژگان و منبع از هم جدا نیفتند.
BCM_VOCAB = (
    "rhythm_amber", "rhythm_yellow", "rhythm_red",
    "sigma_high", "budget_tight", "budget_depleted",
    "afferent_starved", "errors_high",
)


# ── قراردادِ payloadِ تولید (آینهٔ organism.py، بلوکِ `_w.neural_beat(...)`) ──────
# چرا لازم است: `_hebbian_signals` هشت نام **می‌تواند** بسازد، ولی فقط آن‌هایی
# واقعاً آتش می‌کنند که تولیدکنندهٔ زنده ورودی‌شان را بدهد. اندازه‌گیریِ ۲۰۲۶-۰۷-۳۰
# روی ۵۱۱۴ ردیفِ `state/neural/effect-shadow.jsonl` (اسنپ‌شاتِ ۱۰:۴۲؛ فایل زنده
# است و رشد می‌کند): تا امروز فقط دو نام دیده
# شده‌اند — `errors_high` (۳۹۱۴ بار) و `rhythm_amber` (۱۲۲ بار). یعنی کلِ واژگان
# دقیقاً **یک** جفتِ ممکن دارد.
# این جدول آن مرز را ماشین‌خوان می‌کند: مقدارِ `FREE` یعنی تولیدکننده یک متغیرِ
# واقعی می‌دهد؛ مقدارِ ثابت یعنی organism همان literal را هاردکد می‌کند و هیچ
# وضعیتِ واقعی‌ای نمی‌تواند عوضش کند. تستِ driftِ دوطرفه این را با متنِ
# organism.py مقابله می‌کند (`_ops/tests/test_hebbian_eventclock.py`).
FREE = "*"
NEURAL_PAYLOAD_CONTRACT = {
    "rhythm":   {"mode_color": FREE},
    "budget":   {"pct": FREE},
    "spectral": {"sigma": FREE,
                 "sigma_is_replication_ratio": True,   # ← literalِ هاردکد
                 "sigma_source": FREE},
    "sensory":  {"afferent_ratio": FREE, "error_rate": FREE},
}

# سیگنال‌هایی که با قراردادِ بالا **ساختاراً** نمی‌توانند آتش کنند — نه «کم آتش
# می‌کنند»، بلکه هیچ وضعیتِ واقعیِ ارگانیسم روشنشان نمی‌کند.
# اعلامِ صریح جای حذف: کلیدشان در `BCM_VOCAB` می‌ماند چون نیمهٔ «فراموشی»ِ BCM
# دقیقاً به کلیدهایی که y=0 می‌مانند نیاز دارد (bcm.py::step) — حذفشان وزنِ زنده
# را drop می‌کرد. ولی از امروز واژگان دیگر ادعا نمی‌کند همه‌شان زنده‌اند.
SIGNAL_DORMANT = {
    "sigma_high":
        "شرطش `spectral.sigma_is_replication_ratio is False` است، ولی organism "
        "همان کلید را literalِ True می‌دهد و brain_worker اصلاً نمی‌دهدش "
        "(None is False → False). σِ طیفیِ واقعی در doctor/spectral.py::"
        "estimate_sigma تولید می‌شود؛ وصل‌کردنش تغییرِ رفتارِ ایمنی است و "
        "`_hebbian_signals` آن را صریحاً به رأیِ مالک سپرده است. ۲۰۲۶-۰۸-۰۶: "
        "مسیرِ جانبیِ `_real_spectral_sigma` پشتِ فلگِ نوِ "
        "OCTOPUS_WIRE_HEBBIAN_SPECTRAL (پیش‌فرض خاموش) اضافه شد — این جدول با "
        "فلگِ خاموش هنوز دقیق است؛ فلگ که روشن شود، مرده نیست.",
    "budget_depleted":
        "`budget.get(\"depleted\")` را می‌خواند ولی payloadِ زنده فقط `pct` دارد "
        "→ همیشه None. تنها تولیدکنندهٔ واقعیِ این مفهوم `cardiac.py::status()` "
        "است که در scopeِ محلِ payload نیست؛ دادنِ `False`ِ ساختگی fabrication "
        "می‌شد، و افزودنِ I/Oِ per-tick به داغ‌ترین حلقهٔ ارگانیسمِ زنده برای "
        "سیگنالی که با سقفِ ۲۰۰۰ ضربان تقریباً هرگز آتش نمی‌کند صرف ندارد. "
        "۲۰۲۶-۰۸-۰۶: مسیرِ جانبیِ `_real_budget_depleted` پشتِ فلگِ نوِ "
        "OCTOPUS_WIRE_HEBBIAN_CARDIAC (پیش‌فرض خاموش) اضافه شد — همان هزینه، "
        "حالا پشتِ یک کلیدِ روشن/خاموشِ مجزا به‌جای پیش‌فرضِ همیشه‌روشن.",
}

# ── سیگنال‌هایِ «عملاً خاموش» — گزارش، نه گارد (ورودی‌شان زنده است) ─────────────
#   · budget_tight     — شرط `pct > 0.8`؛ مقدارِ زندهٔ اندازه‌گیری‌شده ۰.۰۰۰۷۲.
#   · afferent_starved — شرط `afferent_ratio <= 0.1`؛ مقدارِ زنده ۱.۰ — همان
#     مقدارِ اولیه در organism.py که فقط `afferent_beat` عوضش می‌کند، و آن هم
#     `afferent_every_n=1440` است. یعنی آشکارسازِ گرسنگی‌ای که خودش گرسنه است.

# ── ساعتِ رویدادیِ Hebbian (۲۰۲۶-۰۷-۳۰) ────────────────────────────────────────
# پنجرهٔ eligibility، به واحدِ **تیکِ سیگنال‌دار** (نه ثانیه، نه تیکِ خام).
HEBBIAN_WINDOW = 20


def _emit_hebbian_observation(heb, window_n: int, union: list) -> None:
    """W2 (۲۰۲۶-۰۷-۳۱): انتشارِ یک رخدادِ spine برای مشاهدهٔ Hebbian — «پلِ به EFE».

    پشتِ OCTOPUS_HEBBIAN_LEDGER (پیش‌فرض خاموش → این تابع صدا زده نمی‌شود).
    fail-soft: emit_event هرگز raise نمی‌کند؛ خطا = بی‌اثر.
    importِ lazy: spine_adapters فقط هنگامِ نیاز بارگذاری می‌شود تا circular-import
    نباشد (wiring در bootstrap زود است).
    payload: شمارهٔ پنجره، اجتماعِ سیگنال‌ها، تعداد جفت‌ها، قوی‌ترین قدرتِ فعلی.
    این مشاهده‌پذیری است، نه محاسبهٔ EFE."""
    try:
        from spine import spine_adapters  # lazy — جلوگیری از circular import
    except Exception:  # noqa: BLE001 — instrumentation نباید حلقه را بکشد
        return
    n_pairs = len(union) * (len(union) - 1) // 2  # جفت‌های بالقوه (combinatorial)، نه necessarily observed
    top = 0.0
    if len(union) >= 2:
        for i in range(len(union)):
            for j in range(i + 1, len(union)):
                s = heb.strength_of(union[i], union[j])
                if s > top:
                    top = s
    try:
        spine_adapters.emit_event(
            event_type="hebb.observation",
            domain="neural",
            correlation_id=f"hebb-win-{window_n}",
            producer="wiring.hebbian",
            trust="ADVISORY",
            # «signals» به‌جای list union_signals: _sanitize_payload در event_spine.py
            # فقط scalar/str کوتاه می‌پذیرد و list را ساکت حذف می‌کند (audit 2026-07-31).
            # جدا‌شده با کاما تا نامِ سیگنال‌ها در payload باقی بماند (واژگان = ۸ کلمه، <۸۰char).
            payload={"window_n": window_n, "signals": ",".join(union),
                     "n_pairs": n_pairs, "top_strength": round(top, 4)},
        )
    except Exception:  # noqa: BLE001 — fail-soft؛ spine نباید beat را متوقف کند
        pass


def _hebbian_eventclock_beat(neural_stack, signals) -> dict:
    """کلاکِ زوال را با کلاکِ یادگیری یکی کن + پنجرهٔ eligibility.

    نقصِ اندازه‌گیری‌شدهٔ ۲۰۲۶-۰۷-۳۰ (۵۱۱۴ ردیفِ effect-shadow.jsonl، جدول `[]`
    با mtime~۰ یعنی هر تیک بازنویسیِ یک فایلِ خالی):
      · `decay()` **هر تیک** صدا زده می‌شد (~۴۳s) ولی هم‌رخدادی در انفجارهای
        ۵-۱۰ تیکی می‌آمد و فاصلهٔ بینِ انفجارها ~۱۰۰۰ تیک (~۱۲.۶ ساعت). با
        `DECAY_RATE=0.95` هر جفت بعد از ~۹۰ تیک (~۶۵ دقیقه) زیرِ
        `PRUNE_THRESHOLD` می‌رفت و حذف می‌شد → جدول ساختاراً ~۹۳٪ وقت خالی بود.
        اختلافِ دو کلاک ~۱۰۰۰× بود؛ این باگ نبود، **واحد** بود.
      · گیتِ `>=2` روی **هم‌زمانیِ دقیقِ یک تیک** بود، پس دو انحراف که چند دقیقه
        فاصله داشتند هرگز جفت نمی‌شدند (۱۰ تیکِ زنده دقیقاً همین بودند:
        `rhythm_amber` تنها، بدونِ `errors_high`).

    فیکس، سه تکه:
      (a) زوال فقط روی تیکِ سیگنال‌دار — «چرخهٔ خالی زوال ندارد»، آینهٔ همان
          قراردادِ `neural/bcm.py::step` (FIX #214: وقتی نمی‌دانیم، پاک نکن).
      (b) یک زوال به‌ازای هر **گردشِ کاملِ پنجره** (HEBBIAN_WINDOW تیکِ
          سیگنال‌دار) → یک واحد برای هر دو کلاک.
      (c) `observe()` روی **اجتماعِ پنجره** — ولی دقیقاً **یک‌بار به‌ازای هر
          پنجره** (پنجرهٔ tumbling، اعتبار در لحظهٔ بستنِ پنجره).

    ⚠️ تصحیحِ ۲۰۲۶-۰۷-۳۰ (بازبینیِ متخاصم) — نسخهٔ اولِ همین تابع پنجره را
    rolling گرفته بود و **هر تیک** روی اجتماعِ آن `observe()` می‌زد. اندازه‌گیریِ
    مستقیم: یک تیکِ amberِ تنها روی ۶۰ تیکِ سیگنال‌دار ⇒ ۲۰ فراخوانیِ
    `observe()` · `co_occurrences=20` · `strength=0.9025`. یعنی شمارنده‌ای به
    نامِ «هم‌رخدادی» یک هم‌رخدادی را بیست بار می‌شمرد و `strong_associations()`
    قدرتی گزارش می‌کرد که هرگز رخ نداده بود. حالا هر پنجره **یک** اعتبار
    می‌گیرد، پس عدد همان چیزی است که نامش می‌گوید.

    حسابِ عمرِ یک جفت — **محاسبه از کادنسِ اندازه‌گیری‌شده، نه مشاهده**:
      ورودی‌های اندازه‌گیری‌شده (۵۱۱۴ ردیفِ `state/neural/effect-shadow.jsonl`،
      ۲۰۲۶-۰۷-۲۷ ۱۶:۰۴ → ۰۷-۳۰ ۱۰:۴۲): میانهٔ فاصلهٔ تیک ۴۳.۰s · نسبتِ تیکِ
      سیگنال‌دار ۳۹۲۴/۵۱۱۴ = ۷۶.۷٪ ⇒ یک پنجره ≈ ۲۶ تیک ≈ **۱۸.۷ دقیقه**.
      پس «۱۳ پنجره» ≈ **۴.۰ ساعت** — نه «مقیاسِ روز» (ادعای غلطِ نسخهٔ اول).
      با LEARN_RATE=0.1 و DECAY_RATE=0.95 و PRUNE_THRESHOLD=0.01:
        · یک پنجرهٔ اعتبارگرفته و بعد سکوت: 0.1×0.95=0.095 →
          0.095×0.95^k < 0.01 ⇒ k=۴۴ پنجره ≈ **۱۳.۷ ساعت**.
        · دو پنجرهٔ پشت‌سرهم (انفجارِ روی مرزِ پنجره): 0.185 ⇒ ۵۷ پنجره ≈ ۱۷.۷h.
      فاصلهٔ اندازه‌گیری‌شدهٔ بینِ انفجارهای amber (۱۲۲ ردیف): ۱.۵ · ۲.۲ · ۲.۸ ·
      ۳.۲ · ۱۰.۱ · ۱۲.۰ · ۱۲.۴ · ۱۴.۵ ساعت. یعنی یک اعتبارِ تک‌پنجره‌ای هفت
      فاصله از هشت را پوشش می‌دهد و **پیش از ۱۴.۵ ساعت prune می‌شود**؛ دو
      اعتبار همه را. این ادعای «حافظه دارد» نیست — ادعای «۱۳.۷ ساعت دوام،
      محاسبه‌شده» است، و هر عددِ واقعی فقط بعد از مسلح‌شدنِ فلگ دیده می‌شود.

    گیتِ `>=2` عمداً دست‌نخورده می‌ماند: `observe()` با یک سیگنال ساختاراً صفر
    جفت ثبت می‌کند، پس پایین‌آوردنش به `>=1` صفر اثر و صرفاً I/Oِ بیشتر است.
    """
    if _tg_halt_reason():
        # D2 (شکافی که test_d2_halt_coverage رو کرد — تنها beat ِ بی‌گیت):
        # زیرِ مرزِ سختِ سراسری حتی یادگیری/زوالِ جدول هم نباید بجنبد؛ پنجرهٔ
        # نیمه‌پر دست‌نخورده می‌ماند تا بعد از رفعِ halt همان‌جا ادامه یابد.
        return {"fired": 0, "window": 0, "union": 0,
                "observed": False, "decayed": False, "skipped": "halt"}
    heb = neural_stack["hebbian"]
    fired = tuple(sorted(set(signals or [])))
    if not fired:
        # چرخهٔ خالی: نه یادگیری، نه زوال، نه یک بایت I/O.
        return {"fired": 0, "window": 0, "union": 0,
                "observed": False, "decayed": False}
    acc = neural_stack.get("_hebbian_window_acc")
    if not isinstance(acc, set):
        acc = set()
        neural_stack["_hebbian_window_acc"] = acc
    acc.update(fired)
    n = int(neural_stack.get("_hebbian_event_n") or 0) + 1
    neural_stack["_hebbian_event_n"] = n
    union = sorted(acc)
    filled = n % HEBBIAN_WINDOW or HEBBIAN_WINDOW
    observed = decayed = False
    if filled == HEBBIAN_WINDOW:
        # پنجره بست: **یک** اعتبار و **یک** زوال — نه بیشتر، نه کمتر.
        if len(union) >= 2:
            heb.observe(union)
            observed = True
        heb.decay()
        decayed = True
        acc.clear()
        # W2 (۲۰۲۶-۰۷-۳۱): instrument کردنِ لایهٔ Hebbian واقعی — «پلِ به EFE».
        # هم‌وقوعی/قدرتِ انجمن‌ها تا حالا فقط به hebbian.json (flat، بن‌بست) می‌رفت.
        # حالا هر بستنِ پنجرهٔ observable یک رخدادِ spine می‌شود (پشتِ flag،
        # fail-soft، additive). این EFE نیست — مشاهده‌پذیر کردنِ واقعیت است؛
        # پیش‌نیازِ هر EFEٔ آینده. محاسبات یادگیری عوض نمی‌شود.
        if flag("OCTOPUS_HEBBIAN_LEDGER") and observed:
            _emit_hebbian_observation(heb, n, union)
    return {"fired": len(fired), "window": filled, "union": len(union),
            "observed": observed, "decayed": decayed}


# ── مینِ learned_pressure (۲۰۲۶-۰۷-۳۰) ─────────────────────────────────────────
# منبعِ BCM برای `evaluate` **نامدار** می‌شود تا repointِ تصادفی دیده شود.
NEURAL_EVAL_BCM_SOURCE = "bcm_signals"
LEARNED_PRESSURE_CEILING = 0.25
# ⚠️ نامِ **تازه** برای مقدارِ سقف‌خورده. `learned_pressure` هرگز بازنویسی
# نمی‌شود: همان فیلدی است که در `state/neural/effect-shadow.jsonl` می‌نشیند و
# مالک روی سریِ آن رأی می‌دهد که OCTOPUS_NEURAL_LEARNED_APPLY را مسلح کند یا نه.
# اندازه‌گیریِ ۲۰۲۶-۰۷-۳۰: از ۳۷۲۶ ردیفِ دارای این فیلد، **۸۵۳ ردیف (۲۲.۹٪)** از
# ۰.۲۵ بالاترند (بیشینه ۰.۷۳۹). اگر سقف را زیرِ همین نام می‌نوشتیم، معنیِ یک
# فیلد در میانهٔ سری عوض می‌شد — یعنی سری برای تصمیم بی‌اعتبار می‌شد و بدتر:
# بی‌صدا. سقف یک فیلدِ **کنارِ** آن است، نه جانشینش.
LEARNED_PRESSURE_CAPPED_KEY = "learned_pressure_capped"


def _derive_learned_pressure_cap(result) -> None:
    """سقفِ سختِ learned_pressure — امنیتِ تصادفیِ امروز را ساختاری می‌کند.

    امروز `neural_beat` منبعِ BCM را `NEURAL_EVAL_BCM_SOURCE` می‌دهد
    (`bcm_signals`، واژگانِ ۸ سیگنال، theta≈۰) و learned_pressureِ
    اندازه‌گیری‌شده روی ۵۱۱۴ تیک در بازهٔ ۰.۰۰–۰.۷۳۹ بود. ولی
    `neural_stack["bcm"]` — همان stack، ایندکسِ latent — وزنِ **اشباع** دارد:
    `state/bcm-weights.json` امروز w تا ۳.۹۹۵ از سقفِ ۴.۰.
    اگر کسی روزی منبع را به آن repoint کند:
        learned_pressure = (۳.۹۹۵+۳.۹۹۵+۳.۸۷۵)/۱۲ ≈ ۰.۹۹
        → `protective_override` با APPLY: pain += ۰.۹۹×۰.۵ = +۰.۴۹۶
        → با آستانهٔ کالیبرهٔ ۰.۳۵ **هر تیک** `protective_halt` — توقفِ
          بی‌قیدوشرطِ کلِ کارِ غیرضروری.
    این سقف آن را می‌بندد: بیشینهٔ افزودنی به درد ۰.۲۵×۰.۵ = ۰.۱۲۵ و بیشینهٔ
    دردِ اندازه‌گیری‌شده روی ۵۱۱۴ تیک ۰.۱۵۲ بود → ۰.۲۷۷ < ۰.۳۵. یعنی
    یادگیری می‌تواند تکان بدهد، ولی هرگز تنها-عاملِ halt نشود.

    ⚠️ تصحیحِ ۲۰۲۶-۰۷-۳۰ (بازبینیِ متخاصم): نسخهٔ اول خودِ
    `brain_inputs["learned_pressure"]` را بازنویسی می‌کرد — یعنی همان فیلدی که
    مالک در shadow log می‌خواند. این تابع **هیچ فیلدِ موجودی را عوض نمی‌کند**؛
    فقط `learned_pressure_capped` را اضافه می‌کند و ترمز از همان می‌خواند
    (`protective_override`). سریِ مالک خام، پیوسته و بی‌دست‌کاری می‌ماند.

    ⚠️ عمداً سرِ **منبع** می‌نشیند و نه داخلِ `protective_override`: آن تابع
    مقدارِ خام را pin شده دارد (`test_neural_loop_close.py::
    t_apply_flag_on_combines_learned`, learned=0.9 → halt) و بازنویسیِ گاردِ
    دیگران برای سبزکردن ممنوع است — پس ترمز وقتی کلیدِ سقف **نباشد** (نتیجهٔ
    دست‌ساز یا کهنه) به همان خام برمی‌گردد، و وقتی باشد (هر دو تولیدکنندهٔ زنده،
    organism.py و brain_worker.py، از همین `neural_beat` می‌گذرند) سقف می‌بیند.
    """
    try:
        bi = (result or {}).get("brain_inputs")
        if not isinstance(bi, dict):
            return
        raw = float(bi.get("learned_pressure", 0.0) or 0.0)
        bi[LEARNED_PRESSURE_CAPPED_KEY] = round(
            min(raw, LEARNED_PRESSURE_CEILING), 3)
    except (TypeError, ValueError, AttributeError):   # noqa: BLE001 — سقف تیک را نمی‌کشد
        return


def make_neural_stack():
    """ساختِ NeuralDriver + Hebbian + Consolidation.
    پشتِ OCTOPUS_WIRE_NEURAL. اگر خاموش → None.
    C9: hooks/nociceptor/reflex حذف شدند (مرده در stack — pain/reflex از NeuralDriver داخلی وصل است)."""
    if not flag("OCTOPUS_WIRE_NEURAL"):
        return None
    try:
        _syspath(str(_HERE / "neural"))
        from neural_driver import NeuralDriver
        from hebbian import HebbianAssociator
        from consolidation import ConsolidationCycle
        return {
            "driver": NeuralDriver(),
            "hebbian": HebbianAssociator(),
            "consolidation": ConsolidationCycle(),
        }
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: neural stack ساخت نشد: {e}"])
        return None


def neural_beat(neural_stack, beat: int, snap_inputs: dict | None = None) -> dict | None:
    """هر tick: neural snapshot + reflex + nociceptor. پشتِ flag.
    kill-switch: اول STOP. advisory فقط."""
    if neural_stack is None:
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    try:
        driver = neural_stack["driver"]
        inputs = snap_inputs or {}
        # FIX #310 (2026-07-28): نمونهٔ bcm_signals را به evaluate پاس بده تا برای
        # اولین‌بار وزن‌های آموخته‌شده در brain_inputs fold بشن. اگر نباشد → None
        # و learned_pressure=0 (backward compat). اعمال پشت flag جداگانه.
        # منبعِ نامدار (نه literalِ پراکنده) — `_derive_learned_pressure_cap` توضیح
        # می‌دهد چرا repointِ این یک خط به `"bcm"` یعنی halt بی‌قیدوشرط.
        _bcm_for_eval = (neural_stack.get(NEURAL_EVAL_BCM_SOURCE)
                         if isinstance(neural_stack, dict) else None)
        result = driver.evaluate(
            beat=beat,
            rhythm=inputs.get("rhythm"),
            sensory=inputs.get("sensory"),
            spectral=inputs.get("spectral"),
            budget=inputs.get("budget"),
            bcm=_bcm_for_eval)
        # سقفِ learned_pressure را **کنارِ** مقدارِ خام بگذار (خام دست‌نخورده).
        _derive_learned_pressure_cap(result)
        # hebbian observe
        signals = _hebbian_signals(inputs)
        # ۲۰۲۷-۰۷-۲۷، مشاهدهٔ زنده بعد از ری‌استارت: جدول سه دقیقه **کاملاً ثابت**
        # ماند — نه رشد، نه decay. علت: `observe()` روی جفت‌ها حلقه می‌زند، پس با
        # **یک** سیگنالِ تنها صفر جفت ثبت می‌کند؛ و چون `signals` خالی نیست، شاخهٔ
        # else هرگز به decay نمی‌رسد. نتیجه: یک انحرافِ تنها نه یاد می‌گیرد نه
        # فراموش می‌کند، و هر جفتِ کهنه برای همیشه روی strength کامل زنده می‌ماند.
        # همین است که `green_mode`+`stable` روی 1.0 مانده با اینکه ۱۶ روز است
        # دیگر دیده نشده.
        # با واژگانِ همیشه‌روشنِ قدیمی این هرگز دیده نمی‌شد چون دو سیگنال همیشه
        # با هم می‌آمدند؛ واژگانِ انحراف-محور رونمایی‌اش کرد.
        # درستش الگوی متعارفِ هبی است: **decay پیوسته، تقویت رویدادمحور.**
        # فقط در حالتِ rich تغییر می‌کند؛ مسیرِ قدیمی بایت‌به‌بایت دست‌نخورده.
        if flag("OCTOPUS_HEBBIAN_RICH"):
            # ۲۰۲۶-۰۷-۳۰ — ساعتِ رویدادی پشتِ فلگِ جدا و پیش‌فرض خاموش.
            # با فلگ خاموش، دو خطِ else بایت‌به‌بایت همان مسیرِ ۲۰۲۶-۰۷-۲۷ است
            # (که اندازه‌گیری نشان داد جدول را ~۹۳٪ وقت خالی نگه می‌دارد).
            if flag("OCTOPUS_HEBBIAN_EVENTCLOCK"):
                _hebbian_eventclock_beat(neural_stack, signals)
            else:
                neural_stack["hebbian"].decay()   # هر تیک، چه سیگنالی باشد چه نه
                if len(set(signals or [])) >= 2:  # جفت فقط با ≥۲ انحرافِ هم‌زمان
                    neural_stack["hebbian"].observe(signals)
        elif signals:
            neural_stack["hebbian"].observe(signals)
        else:
            neural_stack["hebbian"].decay()   # use-it-or-lose-it: بی‌سیگنال = تضعیفِ تدریجی + prune
        # consolidation every 10 beats
        if beat > 0 and beat % 10 == 0:
            sources = {}
            if inputs.get("acquisition"):
                sources["acquisition"] = inputs["acquisition"]
            if sources:
                _cons_res = neural_stack["consolidation"].run(sources)
                # ۲۰۲۶-۰۷-۲۸ — **دو نویسنده روی یک تاریخچه**، و پرتکرارش فقیر بود.
                # این مسیر هر ۱۰ ضربان (~۱۰ دقیقه) رکورد می‌نوشت و مسیرِ canonical
                # هر ۷۲۰ ضربان (~۱۲ ساعت) رکوردِ **غنی**. نتیجه: از ۵۳۷ ردیف، صفر
                # تا بردار داشتند — نه چون بردار ساخته نمی‌شد، بلکه چون ۹۸٪ ردیف‌ها
                # از نویسنده‌ای می‌آمدند که `latent_space` اصلاً در دستش نبود
                # (`make_neural_stack` آن را نمی‌سازد).
                # همین نویسنده عاملِ «۵۳۷ ردیف با ~۲۱ جملهٔ یکتا» هم هست.
                # اینجا همان ابزار به او داده می‌شود: latent_space یک‌بار ساخته و
                # در stack کش می‌شود (نه هر ۱۰ ضربان از نو). پیش‌فرض خاموش.
                if flag("OCTOPUS_WIRE_LATENT_PERSIST") and _cons_res is not None:
                    try:
                        _ls = neural_stack.get("latent_space")
                        if _ls is None:
                            from neural.latent_space import SharedLatentSpace as _SLS
                            _ls = _SLS()
                            neural_stack["latent_space"] = _ls
                        _enrich_with_latent(_cons_res, sources, None, _ls)
                        _c = neural_stack["consolidation"]
                        if hasattr(_c, "sync_latent"):
                            _c.sync_latent(_cons_res)
                    except Exception as _nle:  # noqa: BLE001 — latent هرگز tick را نمی‌کشد
                        opslib.alert([f"neural_beat latent خطا: "
                                      f"{type(_nle).__name__}: {_nle}"])
        # ── تغذیهٔ BCM (۲۰۲۶-۰۷-۲۷) ───────────────────────────────────────────
        # `bcm-weights.json` بعد از ۶۵ قدم `keys: {}` داشت. علت در امضای خودِ
        # `BCM.step(activations, known_keys)` است: **هرگز خودش کلید نمی‌سازد**، فقط
        # `known_keys` را دنبال می‌کند — و هیچ‌کس هرگز کلیدی نداده بود. پس کلِ
        # ریاضیِ ضدِ اشباع روی مجموعهٔ تهی کار می‌کرد و `wire_bcm: true` دروغ بود.
        # واژگانِ درست همان سیگنال‌های انحرافیِ زنده است: آتش‌کرده‌ها y=1 (تقویت)،
        # بقیه غایب یعنی y=0 (زوال) — دقیقاً قراردادِ BCM.
        # این فقط **می‌نویسد**؛ هیچ تصمیمی هنوز وزن‌ها را نمی‌خوانَد.
        if flag("OCTOPUS_WIRE_BCM_FEED"):
            # ⚠️ نمونهٔ **جدا** با فایلِ جدا — نه `neural_stack["bcm"]`.
            # ممیزیِ متخاصمِ همان روز این را گرفت: `BCM.step` هر وزنی را که در
            # `known_keys` نباشد حذف می‌کند. `_apply_bcm` کلیدهای latent-space را
            # می‌دهد (هر ۷۲۰ بیت) و این تغذیه ۸ نامِ سیگنال را (هر تیک) — دو واژگانِ
            # کاملاً جدا روی یک نمونه و یک فایل، یعنی هر فراخوان کلِ کلیدهای دیگری
            # را پاک می‌کرد و از بیرون همچنان «wired» به نظر می‌رسید.
            # ضمناً `make_neural_stack` اصلاً کلیدِ `bcm` نمی‌سازد (فقط مسیرِ
            # consolidation آن را cache می‌کند)، پس نسخهٔ قبلی تا اولین epoch
            # یک no-opِ بی‌صدا بود. این‌جا هر دو مشکل با هم بسته می‌شود.
            try:
                _fired = sorted(set(signals or []))
                _bcm = neural_stack.get("bcm_signals") if isinstance(neural_stack, dict) else None
                if _bcm is None and isinstance(neural_stack, dict):
                    from neural.bcm import BCMStabilizer as _BCM
                    _bcm = _BCM(persist_path=opslib.STATE_DIR / "bcm-signal-weights.json")
                    neural_stack["bcm_signals"] = _bcm
                if _bcm is not None and hasattr(_bcm, "step"):
                    _bcm.step({k: 1.0 for k in _fired}, known_keys=list(BCM_VOCAB))
            except Exception as _be:  # noqa: BLE001 — تغذیه هرگز تیک را نمی‌کشد
                opslib.alert([f"wiring: bcm feed خطا (non-fatal): "
                              f"{type(_be).__name__}: {_be}"])
        # ── سایهٔ اثرِ عصبی (۲۰۲۶-۰۷-۲۷) ──────────────────────────────────────
        # `neural_driver` تا امروز `advisory_only: True` بود و هیچ تصمیمی رویش سوار
        # نبود — یعنی کلِ زیرسیستمِ عصبی یک حسگرِ فقط‌خواندنی بود. رأیِ مالک این است
        # که یادگیری باید یک تصمیمِ واقعی را عوض کند، ولی **بی‌واسطه خطرناک است**:
        # سیگنالی که هرگز آزموده نشده نباید مستقیم روی مسیرِ زنده بنشیند.
        # پس اول سایه: همان تصمیمی که *می‌گرفت* ثبت می‌شود، بدونِ اینکه چیزی عوض شود.
        # وقتی چند روز داده جمع شد و دیدیم کِی درست می‌گفت، فلگِ دومِ جدا آن را زنده
        # می‌کند. این خط هیچ رفتاری را تغییر نمی‌دهد — فقط می‌نویسد.
        if flag("OCTOPUS_NEURAL_EFFECT_SHADOW"):
            try:
                _bi = (result or {}).get("brain_inputs") or {}
                _pain = (result or {}).get("pain") or {}
                _learned_applied = bool(
                    flag("OCTOPUS_NEURAL_LEARNED_APPLY") and
                    float(_bi.get(LEARNED_PRESSURE_CAPPED_KEY,
                                  _bi.get("learned_pressure", 0.0)) or 0.0) > 0.0)
                opslib.append_jsonl(
                    opslib.STATE_DIR / "neural" / "effect-shadow.jsonl",
                    {"ts": opslib.now_iso(), "beat": beat,
                     "schema": "neural-effect-shadow.v1",
                     # آنچه *می‌کرد* اگر زنده بود:
                     "would_throttle_brain": _bi.get("throttle_brain"),
                     "would_schedule": _bi.get("schedule_hint"),
                     "confidence_adjustment": _bi.get("confidence_adjustment"),
                     "pain": _pain.get("level"),
                     "protective": _pain.get("protective"),
                     # FIX #310 (2026-07-28): برای اولین‌بار، ثبتِ آنچه یادگیری می‌گفت.
                     # این فیلدها تنها زمانی غیرصفرند که bcm تغذیه شده باشد و وزن یاد گرفته باشد.
                     # ⚠️ این فیلد **خام** است و خام می‌ماند — سریِ ۳۷۲۶ ردیفیِ
                     # همین نام همان چیزی است که رأیِ مالک روی آن گرفته می‌شود
                     # (۸۵۳ ردیفش از سقفِ ۰.۲۵ بالاتر است؛ دست‌کاری‌اش یعنی عوض‌شدنِ
                     # معنیِ یک فیلد در میانهٔ سری). `_derive_learned_pressure_cap`.
                     "learned_pressure": _bi.get("learned_pressure", 0.0),
                     # فیلدِ **تازه** (۲۰۲۶-۰۷-۳۰): همان مقدار با سقفِ ایمنی —
                     # چیزی که ترمز واقعاً می‌بیند. اضافه‌شدنِ نامِ نو سری را
                     # نمی‌شکند؛ ردیفِ قدیمی صرفاً این کلید را ندارد.
                     LEARNED_PRESSURE_CAPPED_KEY:
                         _bi.get(LEARNED_PRESSURE_CAPPED_KEY, 0.0),
                     "learned_top_signal": _bi.get("learned_top_signal", ""),
                     "learned_n_keys": _bi.get("learned_n_keys", 0),
                     # زمینه، تا بعداً بشود سنجید درست می‌گفت یا نه:
                     "signals": sorted(set(signals or [])),
                     "budget_pct": _bi.get("budget_pct"),
                     # ۲۰۲۶-۰۸-۰۷: این قبلاً همیشه False بود و بعد از روشن‌شدنِ
                     # LEARNED_APPLY هم از روی همین فایل نتیجهٔ غلط می‌شد گرفت که
                     # «یادگیری هیچ‌وقت وارد تصمیم نشده». این field فقط observability
                     # است: true یعنی فشارِ آموخته‌شده در این beat پشتِ APPLY-flag
                     # به ورودیِ تصمیم fold شده؛ نه اینکه الزاماً protective_halt شلیک کرد.
                     "applied": _learned_applied})
            except Exception:  # noqa: BLE001 — سایه هرگز تیک را نمی‌کشد
                pass
        return result
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: neural_beat خطا: {e}"])
        return None


# ════════════════════════════════════════════════════════════════════════════════
# S · protective-override — غیرقابل‌سرکوب توسط orchestrator
# ════════════════════════════════════════════════════════════════════════════════

# ⚠️ ۲۰۲۶-۰۷-۲۸ — نقصِ اندازه‌گیری‌شده: `severity` در مسیرِ تولید **وجود ندارد**.
# `NeuralDriver.evaluate` (neural/neural_driver.py:126-127) رفلکس‌ها را این‌طور
# تصویر می‌کند: `{"name":…, "triggered":…, "action":…}` — و `severity` را می‌اندازد.
# ولی دو شاخهٔ زیر دقیقاً روی `r.get("severity")` تصمیم می‌گیرند. یعنی روی مسیرِ
# زنده، هر دو شاخهٔ critical و high **مرده**اند: پروبِ مستقیم با
# sigma=2.0/budget=0.95/afferent=0.0/RED هر ۵ رفلکس را triggered کرد و هیچ‌کدام
# کلیدِ severity نداشت. تنها شاخهٔ زندهٔ این تابع `pain > threshold` است.
# این نقشه آینهٔ `neural/reflex.py` است (همان فایل تنها تولیدکنندهٔ این نام‌هاست)؛
# تستِ drift آن را pin می‌کند تا اگر reflex.py عوض شد، اینجا بی‌صدا کهنه نشود:
#   `_ops/tests/test_pain_calibration.py::t_severity_map_matches_reflex_module`
_REFLEX_SEVERITY = {
    "sigma-throttle": "critical",
    "pain-protect": "critical",
    "budget-slow": "high",
    "disconnect-alarm": "high",
    "red-pause": "high",
    "all-clear": "low",
}


def _reflex_severity(r: dict) -> str:
    """severityِ یک رفلکس — با بازیابیِ نامِ‌محورِ فلگ‌دار.

    فلگ خاموش (پیش‌فرض) → دقیقاً همان `r.get("severity")`ِ قبلی؛ رکوردِ بدونِ
    severity رشتهٔ خالی می‌دهد و هیچ شاخه‌ای را باز نمی‌کند (بایت‌به‌بایتِ امروز).
    فلگ OCTOPUS_REFLEX_SEVERITY_RECOVER روشن → severity از نامِ رفلکس بازسازی
    می‌شود و شاخه‌های critical/high برای اولین‌بار روی مسیرِ زنده قابلِ‌رسیدن
    می‌شوند. این جهت **فقط محافظت را اضافه می‌کند** (هیچ شاخه‌ای بسته نمی‌شود)."""
    s = r.get("severity")
    if s:
        return str(s)
    if flag("OCTOPUS_REFLEX_SEVERITY_RECOVER"):
        return _REFLEX_SEVERITY.get(str(r.get("name") or ""), "")
    return ""


def _pain_threshold() -> tuple[float, str]:
    """آستانهٔ دردِ فعال + متنِ آن برای reason. پیش‌فرض = ۰.۷۰ی تاریخی.

    فلگ OCTOPUS_PAIN_THRESHOLD_CALIBRATED → آستانهٔ داده‌محورِ
    `neural.nociceptor.PROTECTIVE_THRESHOLD_CALIBRATED` (مستندِ توزیع در همان فایل).
    fail-safe: اگر import شکست، به رفتارِ امروز برمی‌گردیم نه به آستانهٔ حدسی."""
    if flag("OCTOPUS_PAIN_THRESHOLD_CALIBRATED"):
        try:
            from neural.nociceptor import PROTECTIVE_THRESHOLD_CALIBRATED as _cal
            return float(_cal), f"{float(_cal):.2f}"
        except Exception:  # noqa: BLE001 — ترمز هرگز به‌خاطرِ import نمی‌میرد
            pass
    return 0.7, "0.7"


def protective_override(neural_result: dict | None) -> dict:
    """Protective signals from neural beat.

    Dual-mode (ADR-035 owner re-arm 2026-08-12):
      · APPLY=0 → ADR-034 proposal/SHADOW only (executable=False).
      · APPLY=1 → production apply: pain fold + protective_halt may set
        override/executable so organism/brain_worker can protective_skip.
    Explicit control-plane halt API remains request_protective_halt (PolicyGate).
    """
    return emit_pain_assessment(neural_result)


def emit_pain_assessment(neural_result: dict | None) -> dict:
    """Build PainAssessment; optionally executable halt when APPLY=1 (ADR-035)."""
    if neural_result is None:
        return {
            "override": False,
            "action": "none",
            "reason": "no neural data",
            "suppressible": True,
            "executable": False,
            "shadow_alert": False,
            "assessment": None,
        }

    from neural.pain_assessment import build_pain_assessment

    pain_raw = (neural_result.get("pain") or {}).get("level")
    contributors = (neural_result.get("pain") or {}).get("contributors") or {}
    reflexes = neural_result.get("reflexes") or []
    triggered = [r for r in reflexes if r.get("triggered")]
    critical = [r for r in triggered if _reflex_severity(r) == "critical"]
    high = [r for r in triggered if _reflex_severity(r) == "high"]
    _thr, _thr_txt = _pain_threshold()
    _bi = neural_result.get("brain_inputs") or {}
    _lp = float(_bi.get(LEARNED_PRESSURE_CAPPED_KEY,
                        _bi.get("learned_pressure", 0.0)) or 0.0)

    apply_on = effective_flag("OCTOPUS_NEURAL_LEARNED_APPLY")
    # Fold learned pressure into assessment when APPLY or PROPOSAL is on.
    fold = bool(apply_on or flag("OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL")) and _lp > 0

    assessment = build_pain_assessment(
        pain_level=pain_raw,
        contributors={str(k): float(v) for k, v in contributors.items()}
        if isinstance(contributors, dict) else {},
        learned_pressure=_lp,
        threshold=float(_thr),
        critical_reflex=bool(critical),
        high_reflex=bool(high),
        apply_learned=fold,
    )

    action = assessment.proposal
    if action == "none" and high:
        action = "warn"

    override = False
    executable = False
    suppressible = True

    if assessment.status == "UNKNOWN":
        reason = "UNKNOWN pain — no influence"
        action = "none"
    elif apply_on:
        # ADR-035 production apply — beat-local protective_skip / throttle.
        _ln = ""
        if _lp > 0:
            _ln = f" [+learned={_lp:.2f}:{_bi.get('learned_top_signal', '')}]"
        if assessment.pain is not None and float(assessment.pain) > float(_thr):
            action = "protective_halt"
            reason = (f"pain={assessment.pain}>{_thr_txt}{_ln} "
                      f"— non-essential paused (ADR-035 APPLY)")
            override = True
            executable = True
            suppressible = False
        elif critical:
            action = "throttle"
            reason = (f"critical reflex: {critical[0].get('name')}{_ln} "
                      f"— throttle (ADR-035 APPLY)")
            override = True
            executable = True
            suppressible = False
        elif high:
            action = "warn"
            reason = f"high reflex: {high[0].get('name')}{_ln}"
        else:
            action = "none"
            reason = "all clear"
    else:
        # ADR-034 proposal-only path.
        if assessment.proposal == "protective_proposal":
            reason = f"pain={assessment.pain}>{_thr_txt} — proposal only (ADR-034)"
        elif critical:
            reason = f"critical reflex: {critical[0].get('name')} — proposal only"
        elif high:
            reason = f"high reflex: {high[0].get('name')}"
        else:
            reason = "all clear"

    if flag("OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL") or flag("OCTOPUS_NEURAL_EFFECT_SHADOW") or apply_on:
        try:
            opslib.append_jsonl(
                opslib.STATE_DIR / "neural" / "pain-assessment.jsonl",
                {
                    "ts": opslib.now_iso(),
                    "schema": "pain-assessment.v1",
                    "adr": "ADR-035" if apply_on else "ADR-034",
                    **assessment.as_dict(),
                    "learned_apply_flag": apply_on,
                    "production_apply_enabled": apply_on,
                    "returned_action": action,
                    "executable": executable,
                },
            )
        except Exception:
            pass

    return {
        "override": override,
        "action": action,
        "reason": reason,
        "suppressible": suppressible,
        "executable": executable,
        "shadow_alert": (not executable) and action in (
            "protective_proposal", "throttle_proposal",
        ),
        "assessment": assessment.as_dict(),
    }


def request_protective_halt(
    *,
    run_id: str,
    approval_id: str | None,
    idempotency_key: str | None,
    provenance_id: str | None,
    kill_switch_engaged: bool = False,
    store_ok: bool = True,
    policy_version: str = "ADR-033-v1",
    state_version: int = 0,
) -> dict:
    """Control-plane halt request — PolicyGate only. Neural path must not call this."""
    if not store_ok:
        return {"allowed": False, "decision": "deny", "reason": "store_unavailable"}
    try:
        from policy.policy_gate import (
            PROTECTIVE_CONTROL_POLICY,
            Decision,
            Policy,
            PolicyGate,
            RequestContext,
        )
        pol = Policy(
            version=policy_version,
            read_only_actions=PROTECTIVE_CONTROL_POLICY.read_only_actions,
            approval_actions=PROTECTIVE_CONTROL_POLICY.approval_actions,
            forbidden_actions=PROTECTIVE_CONTROL_POLICY.forbidden_actions,
        )
        ctx = RequestContext(
            run_id=run_id,
            checkpoint_id="protective-halt",
            state_version=state_version,
            policy_version=policy_version,
            actor="protective_control",
            action="protective_halt",
            trust_level="verified",
            provenance_id=provenance_id,
            approval_id=approval_id,
            idempotency_key=idempotency_key,
            kill_switch_engaged=kill_switch_engaged,
        )
        res = PolicyGate().decide(ctx, pol)
        return {
            "allowed": res.decision == Decision.ALLOW,
            "decision": res.decision.value,
            "reason": res.reason,
        }
    except Exception as exc:
        return {
            "allowed": False,
            "decision": "deny",
            "reason": f"policy_gate_exception:{type(exc).__name__}",
        }


# ════════════════════════════════════════════════════════════════════════════════
# M · canonical consolidation — یک مسیرِ واحد با verification-gate
# ════════════════════════════════════════════════════════════════════════════════

def _enrich_with_latent(result, sources, school_bridge, latent_space) -> None:
    """Phase 2: encode هر verified source → latent vector → retrieval.

    result: ConsolidatedInsight (mutated in-place — latent_vector + similar_keys)
    sources: dict of verified sources passed to consolidation.run()
    school_bridge: برای full_awareness_vector (richer encoding)
    latent_space: SharedLatentSpace instance

    advisory-only: اگر خطا → latent fields می‌مانند None (backward compat)."""
    from neural.encoders import (
        encode_observation, encode_awareness, encode_rfc, encode_phi_t,
        encode_calibration)
    import numpy as _np

    cycle_key = f"cycle-{result.cycle}"
    encoded_keys = []
    dim = latent_space.dim

    # acquisition → hash-based encoding از نام + مقدار
    if "acquisition" in sources:
        data = sources["acquisition"]
        best = max(data.items(), key=lambda x: x[1]) if data else None
        if best:
            vec = encode_observation("acquisition", best[0], dim=dim)
            key = f"{cycle_key}:acquisition:{best[0]}"
            latent_space.embed(key, vec, layer="acquisition", source="consolidation")
            encoded_keys.append(key)

    # doctor_archive → hash-based encoding
    if "doctor_archive" in sources:
        data = sources["doctor_archive"]
        n_approved = sum(1 for d in data
                        if isinstance(d, dict) and d.get("outcome") in ("approved", "published"))
        # ۲۰۲۶-۰۸-۱۶ — rfc_id دیگر شمارهٔ سیکل ندارد: همان n_approved باید
        # همان بردار را بسازد تا بازیابیِ دور ممکن شود. قبلاً archive-{cycle}
        # هر سیکل را به یک hash منحصربفرد (و اغلب NaN) تبدیل می‌کرد.
        vec = encode_rfc("archive", f"{n_approved} approved", "medium", dim=dim)
        key = f"{cycle_key}:doctor_archive:{n_approved}"
        latent_space.embed(key, vec, layer="doctor", source="consolidation")
        encoded_keys.append(key)

    # school_awareness → full vector encoding (richer)
    if "school_awareness" in sources and school_bridge:
        try:
            aw_vec = school_bridge.full_awareness_vector()
            if aw_vec and len(aw_vec) > 0:
                vec = encode_awareness(aw_vec, dim=dim)
                key = f"{cycle_key}:school_awareness"
                latent_space.embed(key, vec, layer="school", source="consolidation")
                encoded_keys.append(key)
        except Exception as _awe:  # noqa: BLE001 — §۴
            opslib.alert([f"latent school_awareness خطا: {type(_awe).__name__}: {_awe}"])

    # mean-pool از همه encoded sources → latent_vector
    if encoded_keys:
        integrated = latent_space.integrate(encoded_keys)
        result.latent_vector = integrated.tolist()
        # retrieval: نزدیک‌ترین سیکل‌های *گذشته* به بردارِ همین سیکل.
        # ۲۰۲۶-۰۷-۳۰ — پیش‌تر `nearest(cycle_key)` بود: کلیدِ خودِ سیکل را lookup
        # می‌کرد، ولی `nearest` برای کلیدِ غایب [] می‌دهد (latent_space.py:98-99) و
        # این خط **قبل از** embedِ همان کلید (پایین) اجرا می‌شود ⇒ روی هر سیکلِ تازه
        # similar_keys همیشه خالی بود. غیرخالی‌بودنش فقط artifactِ باگِ پین‌شدنِ
        # شمارنده بود (کلیدِ تکراری از عمرِ قبلیِ پروسه)، نه بازیابیِ واقعی.
        # `similar(integrated)` مستقیم با بردار کار می‌کند ⇒ بی‌وابستگی به ترتیب.
        # کلیدهای خودِ همین سیکل فیلتر می‌شوند (با تک-منبع، `cycle-N:src` بایت‌به‌بایت
        # همان integrated است و بدونِ فیلتر خودارجاعی می‌شد)؛ top_k جبران می‌شود.
        _own = len(encoded_keys) + 1
        # top_k بزرگ‌تر: تا کلیدهای دورِ بالای آستانه در رقابتِ nearest گم نشوند
        nn = latent_space.similar(integrated, top_k=max(64, 5 + _own))
        from neural.consolidation import select_recall_keys as _sel
        result.similar_keys = _sel(nn, cycle_key, limit=5, far_slots=3)
        # خود cycle را هم embed کن
        latent_space.embed(cycle_key, integrated, layer="consolidation", source="cycle")
        latent_space.store()

def _apply_bcm(result, latent_space, bcm) -> None:
    """Blueprint Phase 3: BCM forgetting روی ایندکسِ retrieval (latent space).

    فقط ایندکسِ بازیابی هرس می‌شود — consolidation.json (تاریخچهٔ append-only، I1)
    هرگز لمس نمی‌شود؛ حافظهٔ بلندمدت cold-reconstructable می‌ماند.

    فعال‌سازی این گام: کلیدهای همین cycle = 1.0 (حافظهٔ تازهٔ gate-passed)،
    کلیدهای بازیابی‌شده = cosine score (بازیابی = فعال‌سازی)، بقیه = 0 (زوال β).
    گزارش در result: bcm_pruned / bcm_theta / bcm_saturation."""
    cycle_key = f"cycle-{result.cycle}"
    prefix = f"{cycle_key}:"
    activations: dict[str, float] = {}
    all_keys = latent_space.keys()
    for k in all_keys:
        if k == cycle_key or k.startswith(prefix):
            activations[k] = 1.0
    for k, score in latent_space.nearest(cycle_key, top_k=5):
        if k != cycle_key and not k.startswith(prefix):
            activations[k] = max(0.0, float(score))
    report = bcm.step(activations, known_keys=all_keys)
    for k in report.pruned:
        latent_space.remove(k)
    if report.pruned:
        latent_space.store()
    result.bcm_pruned = report.pruned
    result.bcm_theta = report.theta_mean
    result.bcm_saturation = report.saturation


def canonical_consolidation(neural_stack, school_bridge=None,
                            acquisition_data=None,
                            doctor_archive=None,
                            latent_space=None,
                            bcm=None):
    """یک مسیرِ canonical consolidation. فقط verified.
    دو مسیرِ موازی نماند — همه از اینجا.
    verification-gate: فقط CONFIRMED/verified منابع.

    Return semantics (Phase 1):
      None                  → precondition failure (neural_stack is None) or exception
      ConsolidatedInsight()  → ran (empty insights = nothing to consolidate, NOT error)

    Phase 2: اگر latent_space موجود → هر verified source را encode + retrieve.
    Phase 3: اگر bcm موجود (پشتِ OCTOPUS_WIRE_BCM) → فراموشیِ BCM روی ایندکسِ retrieval."""
    # lazy import: Avoid circular at module level — consolidation.py is under neural/
    from neural.consolidation import ConsolidatedInsight

    if neural_stack is None:
        # پیام صادقانه (2026-07-10): این تابع flag را نمی‌بیند؛ در مسیرِ production
        # consolidation_beat قبلاً گارد کرده — رسیدن به اینجا یعنی caller بدونِ گارد.
        opslib.alert(["consolidation: neural_stack=None (caller بدونِ گارد — precondition)"])
        return None  # precondition failure
    try:
        consolidation = neural_stack["consolidation"]
        sources = {}
        # acquisition: فقط اگر real numeric data
        if acquisition_data and isinstance(acquisition_data, dict):
            verified_acq = {k: v for k, v in acquisition_data.items()
                           if isinstance(v, (int, float)) and v > 0}
            if verified_acq:
                sources["acquisition"] = verified_acq
        # doctor archive: فقط outcome=approved/rejected
        if doctor_archive and isinstance(doctor_archive, list):
            verified_doc = [d for d in doctor_archive
                           if isinstance(d, dict)
                           and d.get("outcome") in ("approved", "rejected", "published")]
            if verified_doc:
                sources["doctor_archive"] = verified_doc
        # school: فقط اگر awareness numeric
        if school_bridge:
            try:
                awareness = school_bridge.mean_awareness()
                if isinstance(awareness, (int, float)):
                    sources["school_awareness"] = {"mean_awareness": awareness}
            except Exception as _se:  # noqa: BLE001 — §۴: خطای خاموش ممنون
                opslib.alert([f"wiring: school mean_awareness خطا: {type(_se).__name__}: {_se}"])
        if not sources:
            # nothing to consolidate — bare object, NOT None (تمایز با error)
            return ConsolidatedInsight(
                cycle=0, insights=[], verified_sources=[], discarded_sources=[])
        result = consolidation.run(sources)
        # Phase 2: latent integration (advisory-only، fail-soft)
        if latent_space is not None and result is not None:
            try:
                _enrich_with_latent(result, sources, school_bridge, latent_space)
                # ۲۰۲۶-۰۷-۲۸ — بازگرداندنِ غنی‌سازی به دیسک. `run()` رکورد را
                # **قبل از** این خط ذخیره کرده، پس mutation ِ بالا فقط روی شیء
                # می‌نشست: ۵۳۶ ردیفِ تثبیت همه `latent_vector: null` داشتند در
                # حالی که ایندکسِ بازیابی برای همان سیکل وزنِ شلیک‌کرده داشت.
                # پیش‌فرض خاموش؛ خاموش = رفتارِ قبلی بایت‌به‌بایت.
                if flag("OCTOPUS_WIRE_LATENT_PERSIST") and hasattr(consolidation, "sync_latent"):
                    consolidation.sync_latent(result)
            except Exception as _le:  # noqa: BLE001 — latent نباید consolidation را بکشد
                opslib.alert([f"consolidation latent خطا: {type(_le).__name__}: {_le}"])
        # Phase 3: BCM forgetting (advisory-only، fail-soft — فقط ایندکس retrieval)
        if bcm is not None and latent_space is not None and result is not None:
            try:
                _apply_bcm(result, latent_space, bcm)
            except Exception as _be:  # noqa: BLE001 — BCM نباید consolidation را بکشد
                opslib.alert([f"consolidation bcm خطا: {type(_be).__name__}: {_be}"])
        return result
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: canonical_consolidation خطا: {e}"])
        return None  # real error


# ════════════════════════════════════════════════════════════════════════════════
# TG-EXEC (2026-07-15): مصرف‌کنندهٔ صفِ cockpit-requests روی beat-thread.
# «دکمه‌های تلگرام واقعاً اجرا شوند» — _run_act فقط در state/cockpit-requests.jsonl صف می‌کند
# (INV-7: هرگز inline روی poll-thread)؛ این تابع آن‌ها را روی beat اجرا می‌کند. امن به‌صورتِ سازه:
# (۱) فلگِ OCTOPUS_TG_EXEC پیش‌فرض خاموش → no-op؛ (۲) هر لحظه halt-gated؛ (۳) allowlist فقط
# verbهای داخلیِ بی‌پول (doctor/consolidate)؛ (۴) at-most-once با cursorِ byte (persist پیش از exec)؛
# (۵) sقفِ هر beat + first-activation ffwd + truncation-reset + lock (ضدِ split-brain). دو بار
# adversarial-review شد (wf_26797077 + wf_4cb7bcf2). school/ingest عمداً بیرون‌اند.
# ════════════════════════════════════════════════════════════════════════════════
_TG_EXEC_SAFE = frozenset({"doctor", "consolidate"})
_TG_EXEC_KNOWN = frozenset({"doctor", "consolidate", "school", "ideas", "ingest"})
_TG_EXEC_MAX_PER_BEAT = 5


def _supports_stream(fn) -> bool:
    """آیا این پیاده‌سازیِ send_text آرگومانِ `stream` را می‌فهمد؟

    چرا لازم است: `stream` (۲۰۲۶-۰۷-۲۶) فقط در TelegramApprovalChannel هست، ولی
    این توابع هر channel-مانندی را می‌پذیرند. بدونِ این چک، یک پیاده‌سازیِ قدیمی
    TypeError می‌داد و try/exceptِ خودِ beat آن را می‌بلعید — یعنی نوتیف بی‌صدا
    گم می‌شد و تست هم سبز می‌ماند. بررسیِ صریحِ امضا به‌جای بلعیدنِ استثنا."""
    try:
        import inspect
        params = inspect.signature(fn).parameters
        return "stream" in params or any(
            p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())
    except (TypeError, ValueError):
        return False


# ۲۰۲۶-۰۸-۰۷ — نگاشتِ streamِ دایجست به دستهٔ notif_inbox. عمداً فقط همین پنج
# جریان: کارت‌های per-leg گروه (leg_rooms_beat، stream=نامِ پا مثلِ mining/crypto)
# این‌جا نیستند و دست‌نخورده می‌مانند — دستهٔ ناشناخته یعنی notif_inbox کاری
# نمی‌کند (کلیدِ dict.get پیدا نمی‌شود، مستقیم به _real_send می‌رود).
_NOTIF_STREAM_CATEGORY = {
    "needs": "needs", "discovery": "discovery",
    "doctor": "doctor_digest", "brain": "brain_digest", "heart": "heart_digest",
}


def _notif_inbox_mod():
    _syspath(str(_HERE / "telegram_center"))
    import notif_inbox as _ni
    return _ni


def _send_stream(channel, text, kb=None, stream=None):
    """ارسال به تاپیکِ جریان اگر ممکن باشد، وگرنه دقیقاً مثلِ قبل به DM.
    استثنا را نمی‌بلعد — try/exceptِ خودِ beat مسئولِ آن است.

    ۲۰۲۶-۰۸-۰۷ — پشتِ notif_inbox.FLAG (پیش‌فرض خاموش): برای پنج جریانِ دایجست/
    گزارش در _NOTIF_STREAM_CATEGORY، فلگ روشن یعنی به‌جای ارسالِ تلگرام، اعلان
    در صندوقِ مینی‌اپ می‌نشیند و channel.send_text هرگز صدا زده نمی‌شود. فلگ
    خاموش یا streamِ ناشناخته = دقیقاً رفتارِ امروز، بایت‌به‌بایت."""
    def _real_send():
        if stream and _supports_stream(getattr(channel, "send_text", None)):
            return channel.send_text(text, kb, stream=stream)
        return channel.send_text(text, kb)

    category = _NOTIF_STREAM_CATEGORY.get(stream)
    if category:
        return _notif_inbox_mod().route(category, "", text, send_fn=_real_send)
    return _real_send()


def _tg_ack(channel, text):
    if channel is None:
        return
    try:
        channel.send_text(text)
    except Exception:  # noqa: BLE001 — outbound شکست نباید beat را بکشد
        pass


def _tg_halt_reason():
    if opslib.STOP_ORGANISM.exists():
        return "STOP"
    h = opslib.halted()
    if h:
        return h
    try:
        if opslib.frozen():
            return "FREEZE"
    except Exception:  # noqa: BLE001
        pass
    return None


def _tg_exec_run_one(verb, key, doctor=None) -> str:
    """اجرای یک verbِ امن از entrypointِ واقعی. OCTOPUS_TG_EXEC = رضایتِ صریحِ مالک،
    پس cadence-wrapperهای paper دور زده می‌شوند — هر verb ایمنیِ داخلیِ خودش را نگه می‌دارد.
    خروجی: 'ran' | 'not-wired'."""
    import sys as _sys
    if verb == "consolidate" and key == "run":
        p = str(_HERE / "cortex")
        if p not in _sys.path:
            _sys.path.insert(0, p)
        import consolidate as _c
        _c.consolidate_once()   # SELF-gate روی CORTEX_CONSOLIDATE؛ خاموش → no-op ولی 'ran'. state-only.
        return "ran"
    if verb == "doctor" and key == "run":
        # doctor:run == همان کاری که doctor_beat دوره‌ای می‌کند — قابلیتِ نو نیست. propose-only،
        # cost_usd=0. اگر OCTOPUS_WIRE_APPLY_MERGE=1 و RFCِ از-قبل-تأییدشده معلق باشد، merge می‌شود
        # (state-only). برای propose-only محض: OCTOPUS_WIRE_APPLY_MERGE=0.
        d = doctor if doctor is not None else make_doctor(state_dir=str(opslib.STATE_DIR))
        if d is None:
            return "not-wired"
        d.run_cycle(beat=1_000_000)
        return "ran"
    return "not-wired"


def cockpit_requests_beat(state_dir=None, doctor=None, channel=None) -> dict:
    import json as _json
    import os as _os
    import time as _time
    from pathlib import Path as _P
    if not flag("OCTOPUS_TG_EXEC"):
        return {"skipped": "flag-off"}
    if _tg_halt_reason():
        return {"skipped": "halt"}
    sd = _P(state_dir) if state_dir else (_HERE / "state")
    logp = sd / "cockpit-requests.jsonl"
    curp = sd / "cockpit-requests.cursor"
    lockp = sd / "cockpit-requests.lock"
    if not logp.exists():
        return {"skipped": "no-queue"}
    pid = _os.getpid()
    try:  # single-consumer lock (ضدِ split-brain)
        if lockp.exists():
            prev = (lockp.read_text(encoding="utf-8").strip() or ":")
            if prev.split(":")[0] not in ("", str(pid)) and (_time.time() - lockp.stat().st_mtime) < 120:
                return {"skipped": "locked-by-other"}
        lockp.write_text(f"{pid}:{opslib.now_iso()}", encoding="utf-8")
    except OSError:
        pass
    size = logp.stat().st_size
    if not curp.exists():   # first-activation → ffwd، بدونِ replayِ backlog
        try:
            curp.write_text(str(size), encoding="utf-8")
        except OSError:
            pass
        return {"skipped": "first-activation-ffwd", "at": size}
    try:
        off = int(curp.read_text(encoding="utf-8").strip() or 0)
    except (OSError, ValueError):
        off = 0
    if off > size:   # rotation/truncation → reset + alert
        opslib.alert([f"tg-exec: cockpit-requests کوچک شد ({off}>{size}) — cursor صفر شد"])
        off = 0
    try:
        with open(logp, "rb") as f:
            f.seek(off)
            chunk = f.read()
    except OSError:
        return {"skipped": "read-fail"}
    nl = chunk.rfind(b"\n")
    if nl < 0:
        return {"skipped": "no-complete-line"}
    raw_lines = chunk[:nl + 1].decode("utf-8", "replace").splitlines(keepends=True)
    take = raw_lines[:_TG_EXEC_MAX_PER_BEAT]
    consumed = len("".join(take).encode("utf-8"))
    new_off = off + consumed
    try:  # at-most-once: cursor پیش از exec؛ شکستِ persist → بدونِ اجرا
        tmp = curp.with_suffix(".cursor.tmp")
        tmp.write_text(str(new_off), encoding="utf-8")
        _os.replace(tmp, curp)
    except OSError as e:
        opslib.alert([f"tg-exec: نوشتنِ cursor شکست ({type(e).__name__}) — beat رد شد"])
        return {"skipped": "cursor-persist-failed"}
    ran, failed, skipped = [], [], []
    for line in take:
        line = line.strip()
        if not line:
            continue
        try:
            req = _json.loads(line)
        except ValueError:
            continue
        if req.get("status") != "requested":
            continue
        verb, key = req.get("verb"), req.get("key")
        if verb not in _TG_EXEC_KNOWN:
            continue
        if _tg_halt_reason():
            _tg_ack(channel, f"⛔ «{verb}:{key}» اجرا نشد — halt/انجماد. بعد از /resume دوباره بزن.")
            skipped.append(f"{verb}:{key}:halt")
            continue
        if verb not in _TG_EXEC_SAFE:
            _tg_ack(channel, f"⏸ «{verb}» در این نسخه اجرا نمی‌شود (فعّال: doctor، consolidate).")
            skipped.append(f"{verb}:{key}:not-enabled")
            continue
        try:
            res = _tg_exec_run_one(verb, key, doctor=doctor)
            if res == "ran":
                ran.append(f"{verb}:{key}")
                _tg_ack(channel, f"✅ اجرا شد (تلگرام→بیت): {verb}:{key}")
            else:
                skipped.append(f"{verb}:{key}:not-wired")
                _tg_ack(channel, f"⚠️ «{verb}» وصل نیست (فلگِ زیرسیستم خاموش).")
        except Exception as e:  # noqa: BLE001 — یک verbِ بد نباید beat را بکشد
            failed.append(f"{verb}:{key}:{type(e).__name__}")
            opslib.alert([f"tg-exec {verb}:{key} failed: {type(e).__name__}: {e}"])
            _tg_ack(channel, f"⚠️ اجرای {verb}:{key} خطا داد: {type(e).__name__}")
    return {"ran": ran, "failed": failed, "skipped": skipped}


# ════════════════════════════════════════════════════════════════════════════════
# M · live-loop wiring — canonical_consolidation در حلقهٔ زنده (P-M2)
# ════════════════════════════════════════════════════════════════════════════════

def make_school_bridge(state_path=None):
    """ساختِ SchoolBridge (منبعِ awareness برای consolidation). پشتِ flag لازم نیست —
    فقط اگر consolidation نیازش داشته باشد ساخته می‌شود. همیشه یک instance برمی‌گرداند
    اگر import موفق باشد، وگرنه None (fail-soft). $0 آفلاین، stdlib-only."""
    try:
        _syspath(str(_HERE / "afferent"))
        from school_bridge import SchoolBridge
        kw = {}
        if state_path is not None:
            kw["state_path"] = state_path
        return SchoolBridge(**kw)
    except Exception as e:  # noqa: BLE001 — SchoolBridge اختیاریِ additive
        opslib.alert([f"wiring: SchoolBridge ساخت نشد: {e}"])
        return None


def _real_acquisition_data() -> dict | None:
    """acquisition_data واقعی — درآمدِ CONFIRMED/ATTRIBUTED per-cell از budget/attribution.py
    (`confirmed_revenue().by_cell`، همان سطحی که fitness.py هم می‌خواند؛ ناوردیِ
    attribution.py: هرگز چیزی زیرِ CONFIRMED). پشتِ OCTOPUS_WIRE_CONSOLIDATION_ACQUISITION
    (پیش‌فرض خاموش — سیم‌کشیِ نو، رأیِ مالک لازم). read-only، $0، fail-soft.

    امروز (۲۰۲۶-۰۸-۰۶) `by_cell` روی دادهٔ زندهٔ ledger خالی است — هنوز هیچ درآمدی
    reconcile نشده تا CONFIRMED برسد. این سیم واقعی است، فقط دادهٔ بالادستش هنوز صفر؛
    وقتی reconcile.py اولین CONFIRMED را بنویسد، همین‌جا واقعاً جاری می‌شود."""
    if not flag("OCTOPUS_WIRE_CONSOLIDATION_ACQUISITION"):
        return None   # flag خاموش = no-op (no regression)
    try:
        _syspath(str(_HERE / "budget"))
        import attribution as _attribution
        rev = _attribution.confirmed_revenue()
        by_cell = rev.get("by_cell") if isinstance(rev, dict) else None
        if not isinstance(by_cell, dict) or not by_cell:
            return None   # چیزی CONFIRMED نیست — سکوتِ صادق (نه dictِ جعلی)
        return {k: v for k, v in by_cell.items() if isinstance(v, (int, float))}
    except Exception as e:  # noqa: BLE001 — §۴: خطای خاموش ممنون، ولی fail-soft (consolidation نباید بشکند)
        opslib.alert([f"wiring: acquisition_data (attribution) خطا: {type(e).__name__}: {e}"])
        return None


def _real_doctor_archive(max_n: int = 50) -> list | None:
    """doctor_archive واقعی — تاریخچهٔ verdictِ RFC از chrono.db (doctor/calibration.py::
    get_verdict_history، جدولِ duration_marker، durable — بر خلافِ self._rfcs که RFCهای
    terminal را در بوت skip می‌کند). پشتِ OCTOPUS_WIRE_CONSOLIDATION_ARCHIVE (پیش‌فرض
    خاموش — سیم‌کشیِ نو، رأیِ مالک لازم). read-only، fail-soft.

    ترجمه: calibration ثبت می‌کند verdict∈{merged, rejected, ignored}؛
    canonical_consolidation فقط outcome∈{approved, rejected, published} را verified
    می‌شمارد. نگاشتِ صادق: merged→approved، rejected→rejected؛ ignored عمداً بدونِ
    outcome می‌ماند و با همان گیتِ verification در canonical_consolidation کنار گذاشته
    می‌شود — نه دادهٔ جعلی، فقط دو واژگانِ متفاوت برای همان رویداد."""
    if not flag("OCTOPUS_WIRE_CONSOLIDATION_ARCHIVE"):
        return None   # flag خاموش = no-op (no regression)
    try:
        db_path = opslib.STATE_DIR / "chrono.db"
        if not db_path.exists():
            return None
        import chrono as _chrono_mod
        _syspath(str(_HERE / "doctor"))
        from calibration import get_verdict_history
        db = _chrono_mod.ChronoDB(str(db_path))
        history = get_verdict_history(db)
        if not history:
            return None
        _VERDICT_TO_OUTCOME = {"merged": "approved", "rejected": "rejected"}
        out = []
        for h in history[-max_n:]:
            if not isinstance(h, dict):
                continue
            outcome = _VERDICT_TO_OUTCOME.get(h.get("verdict"))
            if outcome is None:
                continue   # 'ignored' یا نامعتبر — عمداً بدونِ outcome (verification-gate خودش discard می‌کند)
            out.append({**h, "outcome": outcome})
        return out or None
    except Exception as e:  # noqa: BLE001 — §۴: خطای خاموش ممنون، ولی fail-soft (consolidation نباید بشکند)
        opslib.alert([f"wiring: doctor_archive (verdict-history) خطا: {type(e).__name__}: {e}"])
        return None


def consolidation_beat(neural_stack, school_bridge=None, beat: int = 0,
                       acquisition_data=None, doctor_archive=None) -> dict | None:
    """هر N beat: canonical_consolidation را در حلقهٔ زنده صدا بزن.
    پشتِ OCTOPUS_WIRE_CONSOLIDATION. kill-switch: اول STOP. هر N beat (نه هر tick).
    فقط verified/CONFIRMED (verification-gate حفظ می‌شود). صفر مسیرِ spend.

    خروجی: ConsolidatedInsight یا None. advisory فقط — هیچ اثرِ جانبیِ irreversible."""
    if not flag("OCTOPUS_WIRE_CONSOLIDATION"):
        return None   # flag خاموش = no-op (no regression)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch
    every_n = int(os.environ.get("CHRONO_CONSOLIDATION_EVERY_N_BEATS", "720"))  # ۱۲ ساعت
    if beat <= 0 or every_n <= 0:
        return None   # هنوز نوبتِ consolidation نیست
    if neural_stack is None:
        return None   # بدونِ neural_stack → چیزی برای consolidate نیست
    # ضدِ aliasing (2026-07-10، مثل doctor_beat): tick ۳۰۰sِ ارگانیسم ضربانِ ۶۰s را
    # نمونه‌برداری می‌کند و ممکن است مضربِ دقیقِ N دیده نشود → عبور از پنجرهٔ N-تایی.
    epoch = beat // every_n
    last = neural_stack.get("_consolidation_epoch_fired", 0) if isinstance(neural_stack, dict) else 0
    if not isinstance(last, int):
        last = 0
    if epoch < 1 or epoch <= last:
        return None   # این پنجره قبلاً fire شده (یا هنوز به پنجرهٔ اول نرسیده)
    if isinstance(neural_stack, dict):
        neural_stack["_consolidation_epoch_fired"] = epoch
    # Phase 2: latent space instance از neural_stack یا lazy construction
    latent_space = neural_stack.get("latent_space")
    if latent_space is None:
        try:
            from neural.latent_space import SharedLatentSpace
            latent_space = SharedLatentSpace()
            neural_stack["latent_space"] = latent_space  # cache
        except Exception:  # noqa: BLE001 — latent fail-soft
            latent_space = None
    # Phase 3: BCM stabilizer پشتِ OCTOPUS_WIRE_BCM — env-default خاموش؛ از 2026-07-10
    # در PAPER_FULL_FLAGS است (verdict default-applied «همرو کامل انجام بده»، قابل‌وتو —
    # AGENT_QUESTIONS). سوار شدن در runtime = restart مالک (INC-1).
    bcm = None
    if flag("OCTOPUS_WIRE_BCM") and latent_space is not None:
        bcm = neural_stack.get("bcm")
        if bcm is None:
            try:
                from neural.bcm import BCMStabilizer
                bcm = BCMStabilizer()
                neural_stack["bcm"] = bcm  # cache
            except Exception:  # noqa: BLE001 — BCM fail-soft
                bcm = None
    # Phase M-real (۲۰۲۶-۰۸-۰۶): اگر caller منبعِ صریح نداده (organism.py/brain_worker.py
    # هیچ‌وقت acquisition_data=/doctor_archive= پاس نمی‌دهند)، دو منبعِ واقعیِ **موجود**
    # را امتحان کن — هر دو پشتِ فلگِ نو و پیش‌فرض خاموش، پس با فلگ خاموش این بلوک
    # دقیقاً None برمی‌گرداند و رفتار بایت‌به‌بایت همان قبل می‌ماند. کالر که صریح
    # چیزی داده (تست‌ها) همیشه برنده است — این‌جا override نمی‌شود.
    if acquisition_data is None:
        acquisition_data = _real_acquisition_data()
    if doctor_archive is None:
        doctor_archive = _real_doctor_archive()
    # Phase 4: فیلترِ ورودیِ sparse (L1/prediction-error) پشتِ OCTOPUS_WIRE_SPARSE —
    # فقط acquisition فیلتر می‌شود؛ دادهٔ خام جایی حذف نمی‌شود (منابع اصلی دست‌نخورده).
    sparse_report = None
    if flag("OCTOPUS_WIRE_SPARSE") and acquisition_data:
        try:
            sf = neural_stack.get("sparse_filter")
            if sf is None:
                from neural.sparse_filter import SparseInputFilter
                sf = SparseInputFilter()
                neural_stack["sparse_filter"] = sf  # cache
            sparse_report = sf.filter(acquisition_data)
            acquisition_data = sparse_report.passed   # فقط novel/high-error
        except Exception as _spe:  # noqa: BLE001 — sparse fail-soft
            opslib.alert([f"wiring: sparse filter خطا: {type(_spe).__name__}: {_spe}"])
            sparse_report = None
    try:
        result = canonical_consolidation(
            neural_stack, school_bridge=school_bridge,
            acquisition_data=acquisition_data, doctor_archive=doctor_archive,
            latent_space=latent_space, bcm=bcm)
        # Phase 4: گزارشِ sparse روی result (additive، advisory)
        if sparse_report is not None and result is not None:
            result.sparse_ratio = sparse_report.sparsity_ratio
            result.sparse_filtered = list(sparse_report.filtered)
        return result
    except Exception as e:  # noqa: BLE001 — §۴: خطای خاموش ممنون، ولی consolidation نباید tick را بکشد
        opslib.alert([f"wiring: consolidation_beat خطا: {type(e).__name__}: {e}"])
        return None


# ════════════════════════════════════════════════════════════════════════════════
# W · afferent path (آوران واقعی) — sensory_bus → school_bridge در حلقهٔ زنده (P-W2)
# ════════════════════════════════════════════════════════════════════════════════

def make_sensory_bus():
    """ساختِ SensoryBus (مسیرِ آورانِ واحد). پشتِ OCTOPUS_WIRE_SCHOOL.
    $0 آفلاین، stdlib-only. اگر import موفق نباشد → None (fail-soft)."""
    try:
        _syspath(str(_HERE / "afferent"))
        from sensory_bus import SensoryBus
        return SensoryBus()
    except Exception as e:  # noqa: BLE001 — SensoryBus اختیاریِ additive
        opslib.alert([f"wiring: SensoryBus ساخت نشد: {e}"])
        return None


def _observations_from_snapshot(snap: dict) -> list:
    """از snapshotِ telemetry یک‌دسته observationِ کاملاً انتزاعی بساز.
    هیچ رکوردِ خام/PII. فقط نوع/ساختارِ کلی (مانندِ ingest_raw: برچسبِ انتزاعی).
    این منبعِ آورانِ زندهٔ ارگانیسم است — سیستم از «شکلِ کلیِ فعالیت» یاد می‌گیرد،
    نه از دادهٔ مشتری."""
    from sensory_bus import Observation
    obs = []
    if not isinstance(snap, dict):
        return obs
    per_organ = snap.get("per_organ_alltime_musd") or {}
    # هر organ فعال یک observationِ status (لیبلِ کاملاً انتزاعی)
    n_organs = len([v for v in per_organ.values() if isinstance(v, (int, float)) and v > 0])
    if n_organs > 0:
        obs.append(Observation(
            source="organism", obs_type="status",
            label=f"organ activity · {n_organs} organs with spend (structure only)",
            intensity=min(0.6, 0.3 + n_organs * 0.05)))
    sz = snap.get("suspect_zero_total", 0)
    if isinstance(sz, (int, float)) and sz > 0:
        obs.append(Observation(
            source="organism", obs_type="error",
            label=f"{sz} suspect zero-cost records (anomaly signal)",
            intensity=0.4))
    mon = snap.get("month") or {}
    mon_musd = mon.get("musd", 0) if isinstance(mon, dict) else 0
    if isinstance(mon_musd, (int, float)) and mon_musd > 0:
        obs.append(Observation(
            source="organism", obs_type="payment",
            label=f"month spend · {int(mon_musd)} micro-USD (aggregate only)",
            intensity=0.35))
    return obs


def afferent_beat(sensory_bus, school_bridge=None, snap=None, beat: int = 0) -> dict | None:
    """هر N beat: آورانِ واقعی. observationهای انتزاعی (ازِ snapshot، صفر PII) →
    sensory_bus.ingest → school_bridge.learn_from → خروجی = afferent_status برای bus.

    پشتِ OCTOPUS_WIRE_SCHOOL. kill-switch: اول STOP. هر N beat (نه هر tick).
    صفر رکوردِ خام/PII (classifier فقط لیبل می‌بیند؛ PII رد می‌شود).
    verification-gate: فقط afferent=True یاد گرفته می‌شود (PII-رد/internal نادیده).

    خروجی: {school_report, sensory_status, n_observations} یا None (advisory)."""
    # LEG-09: پلِ ingest_raw (crypto/accounting) پشتِ OCTOPUS_WIRE_INGEST — مستقل از
    # OCTOPUS_WIRE_SCHOOL. ingest_beat خودش STOP + flag + cadence را چک می‌کند و با flag
    # خاموش بی‌درنگ None برمی‌گرداند (no-op) → این تماس رفتارِ afferent_beat را عوض نمی‌کند.
    ingest_beat(beat=beat)
    if not flag("OCTOPUS_WIRE_SCHOOL"):
        return None   # flag خاموش = no-op (no regression)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch
    every_n = int(os.environ.get("CHRONO_AFFERENT_EVERY_N_BEATS", "1440"))  # روزانه
    if not _epoch_fire("afferent", beat, every_n):
        return None   # هنوز نوبتِ afferent نیست
    if sensory_bus is None:
        return None   # بدونِ SensoryBus → هیچ آورانی
    try:
        # ۱) observationهای انتزاعی از snapshot (صفر PII)
        observations = _observations_from_snapshot(snap)
        # ۲) ingest هر observation → AfferentEvent (PII اینجا رد می‌شود)
        events = [sensory_bus.ingest(o) for o in observations]
        # ۳) alarm check
        sensory_bus.check_alarm()
        # ۴) school_bridge یاد بگیرد ازِ afferent events (فقط afferent=True)
        school_report = None
        if school_bridge is not None and any(getattr(e, "afferent", False) for e in events):
            school_report = school_bridge.learn_from(events, persist=True)   # 2026-07-15 باگ ۳: سیمِ یادگیری وصل شد — awareness حالا واقعاً می‌ماند (قبلاً persist=False = هرگز ذخیره)
        return {"n_observations": len(observations),
                "school_report": school_report,
                "sensory_status": sensory_bus.status(),
                "alarm": sensory_bus.alarms[-1] if sensory_bus.alarms else None}
    except Exception as e:  # noqa: BLE001 — §۴: خطای خاموش ممنون، ولی afferent نباید tick را بکشد
        opslib.alert([f"wiring: afferent_beat خطا: {type(e).__name__}: {e}"])
        return None


_INGEST_STATE = {"last_epoch": 0}


def ingest_beat(beat: int = 0) -> dict | None:
    """LEG-09 · پلِ ورودیِ خامِ واقعی → مصرف‌کننده (sensory_bus/School).

    پشتِ OCTOPUS_WIRE_INGEST (پیش‌فرض خاموش و خارج از PAPER_FULL_FLAGS). با flag خاموش
    بی‌درنگ None (no-op؛ بایت‌به‌بایتِ رفتارِ فعلی — ingest_raw.run هیچ‌وقت صدا نمی‌شود).
    روشن = هر N beat (پیش‌فرض روزانه) ``afferent/ingest_raw.run()`` را اجرا می‌کند تا
    obsهای واقعیِ crypto/accounting (aggregate/structure-only، صفر PII) به SensoryBus +
    SchoolBridge برسند. kill-switch اول؛ ضدِ aliasing با پنجرهٔ N-تایی؛ fail-soft مطلق.
    propose-only: ingest_raw فقط نوتِ draft/summary می‌سازد — هیچ send/spend/outward."""
    if not flag("OCTOPUS_WIRE_INGEST"):
        return None   # flag خاموش = no-op (no regression)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch مقدم
    every_n = int(os.environ.get("CHRONO_INGEST_EVERY_N_BEATS", "1440"))  # روزانه
    if beat <= 0 or every_n <= 0:
        return None
    epoch = beat // every_n
    if not _epoch_window("ingest", epoch, _INGEST_STATE):
        return None   # هنوز نوبتِ ingest نیست (پنجرهٔ ضدِ aliasing، بقا از ری‌استارت)
    try:
        _INGEST_STATE["last_epoch"] = epoch
        _syspath(str(_HERE / "afferent"))
        import ingest_raw  # noqa: WPS433 — lazy (سنگین: فایل‌های بازار/حساب را می‌خواند)
        report = ingest_raw.run()
        return {"observations": report.get("observations", 0),
                "crypto_notes": len(report.get("crypto_notes") or []),
                "acct_notes": len(report.get("acct_notes") or []),
                "pii_flags": len(report.get("pii_flags") or []),
                "beat": beat}
    except Exception as e:  # noqa: BLE001 — §۴: ingest نباید tick را بکشد
        opslib.alert([f"wiring: ingest_beat خطا: {type(e).__name__}: {e}"])
        return None


# ════════════════════════════════════════════════════════════════════════════════
# I · idea-graph — موتورِ اتصالِ ایده‌ها/پروژه‌ها (P-I، نو)
# ════════════════════════════════════════════════════════════════════════════════

def make_idea_graph(vault_root=None):
    """ساختِ IdeaGraph. پشتِ OCTOPUS_WIRE_IDEAS. lazy: گراف در اولین idea_beat ساخته
    می‌شود (build کند است). $0 آفلاین، stdlib-only."""
    try:
        from idea_graph import IdeaGraph
        return IdeaGraph()
    except Exception as e:  # noqa: BLE001 — idea_graph اختیاریِ additive
        opslib.alert([f"wiring: IdeaGraph ساخت نشد: {e}"])
        return None


def idea_beat(idea_graph, vault_root=None, beat: int = 0,
              rebuild_every_n: int = 1440) -> dict | None:
    """هر N beat: گرافِ ایده‌ها را بازساز/تحلیل کن و insightها را گزارش کن.
    پشتِ OCTOPUS_WIRE_IDEAS. kill-switch: اول STOP. هر N beat (نه هر tick).
    rebuild_every_n = هر چند beat گراف را از نو بساز (۱۴۴۰ = روزانه).

    propose-only مطلق: فقط تحلیل + پیشنهادِ یالِ نو (human-append). هیچ effector.

    خروجی: گزارشِ تحلیل (hubs/clusters/bridges/proposed-edges) یا None."""
    if not flag("OCTOPUS_WIRE_IDEAS"):
        return None   # flag خاموش = no-op (no regression)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch
    every_n = int(os.environ.get("CHRONO_IDEAS_EVERY_N_BEATS", "1440"))
    if not _epoch_fire("ideas", beat, every_n):
        return None   # هنوز نوبتِ idea نیست
    if idea_graph is None:
        return None   # بدونِ graph engine → هیچ تحلیلی
    try:
        # گراف را بساز/به‌روز کن. cache ساده: هر rebuild_every_n یک بار.
        should_rebuild = (not hasattr(idea_graph, "_last_built_beat")
                          or (beat - getattr(idea_graph, "_last_built_beat", 0)) >= rebuild_every_n)
        if should_rebuild:
            root = vault_root or str(_HERE.parent)
            idea_graph.build(root)
            idea_graph._last_built_beat = beat
        # تحلیل (propose-only)
        report = idea_graph.analyze()
        # ⚠️ ۲۰۲۶-۰۸-۰۵ — تا امروز این خروجی هر روز محاسبه و **دور ریخته**
        # می‌شد: organism.py صدایش می‌زد بدونِ assign کردنِ نتیجه. تبِ
        # کوکپیتِ «brain/idea» (approval_channel.py) از قبل منتظرِ همین
        # فایل بود (`cockpit_readmodel.read_idea()` →
        # `state/idea-graph-latest.json`) و همیشه «هنوز تحلیلی ننوشته»
        # نشان می‌داد. نوشتن این‌جاست تا کنارِ نویسندهٔ تحلیل بماند، نه در
        # organism.py که جای دیگری همین شب رویش کار می‌کند.
        try:
            import json as _json3  # noqa: WPS433 — این فایل import سطحِ ماژول ندارد
            sp = opslib.STATE_DIR / "idea-graph-latest.json"
            tmp = sp.with_suffix(".tmp")
            tmp.write_text(_json3.dumps(report, ensure_ascii=False, indent=2,
                                        default=str), encoding="utf-8")
            os.replace(tmp, sp)
        except Exception:  # noqa: BLE001 — نوشتنِ نمایشی هرگز idea_beat را نمی‌کشد
            pass
        return report
    except Exception as e:  # noqa: BLE001 — §۴: خطای خاموش ممنون، ولی idea نباید tick را بکشد
        opslib.alert([f"wiring: idea_beat خطا: {type(e).__name__}: {e}"])
        return None


# ════════════════════════════════════════════════════════════════════════════════
# HH-P5 — heart_beat: قلبِ تکاملیِ ترکیبی در سایه (velocity + SOG-setpoint + Governor)
# ════════════════════════════════════════════════════════════════════════════════
_HEART_STATE = {"last_epoch": 0, "last_setpoint_epoch": 0}


def heart_beat(beat: int = 0, snap: dict | None = None) -> dict | None:
    """هر N beat قلبِ سایه را بزن (HH-P5). پشتِ OCTOPUS_WIRE_HEART — پیش‌فرض خاموش و
    **عمداً خارج از PAPER_FULL_FLAGS** (ورود به profile فقط با رأی صریحِ مالک).
    kill-switch اول؛ ضدِ aliasing با پنجرهٔ N-تایی (tick ۳۰۰s ضربانِ ۶۰s را
    نمونه‌برداری می‌کند). **هرگز period ارگانیسم را set نمی‌کند** — فقط محاسبهٔ سایه
    به سینکِ جدا (state/pulse/) + خلاصه برای ORGANISM-STATE. propose-only مطلق.

    HH-P6 داخلِ همین ضربان: هر CHRONO_HEART_SETPOINT_EVERY_N_BEATS (پیش‌فرض ۱۴۴۰ =
    روزانه؛ واحدِ beat=۶۰s) دکترِ w-slow باندِ target-velocity را propose می‌کند."""
    # HEART-01: پایداریِ heartstate (envelope) در سایه — مستقل از OCTOPUS_WIRE_HEART،
    # پشتِ HEARTSTATE_SHADOW. heartstate_beat خودش STOP + فلگِ سایه را چک می‌کند و با فلگ
    # خاموش None برمی‌گرداند (no-op) → این تماس رفتارِ heart_beat را عوض نمی‌کند.
    heartstate_beat(beat=beat)
    if not flag("OCTOPUS_WIRE_HEART"):
        return None   # flag خاموش = no-op (no regression)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch
    every_n = int(os.environ.get("CHRONO_HEART_EVERY_N_BEATS", "5"))
    if beat <= 0 or every_n <= 0:
        return None
    epoch = beat // every_n
    if not _epoch_window("heart", epoch, _HEART_STATE):
        return None   # هنوز نوبتِ قلب نیست (پنجرهٔ ضدِ aliasing، بقا از ری‌استارت)
    try:
        _syspath(str(_HERE))
        from heart import shadow as _shadow
        _HEART_STATE["last_epoch"] = epoch
        rec = _shadow.shadow_step(beat=beat, snap=snap)
        out = {"period_shadow_s": rec.get("period_s"),
               "wire_open": bool(rec.get("production_wire", {}).get("open", False)),
               "wire_reasons_n": len(rec.get("production_wire", {}).get("reasons", [])),
               "gate0": rec.get("gate0_live_producer"),
               "sampled": rec.get("sampled_this_step"),
               "beat": beat}
        # HH-P6: setpointِ w-slow (روزانه) — همان الگوی cadence دکتر.
        # جلسه ۴۶ (فیکسِ #۱، ممیزیِ قلب): seedِ اولیه را جلو بینداز — به‌جای انتظارِ کادنسِ
        # ۱۴۴۰ (روزها)، همان اولین ضربانی که velocity هست و هنوز باندی نیست، seed کن. تا آن،
        # قلب روی باندِ پیش‌فرضِ اشتباه قضاوت می‌کرد و در حداکثر استراحت گیر می‌کرد.
        sp_n = int(os.environ.get("CHRONO_HEART_SETPOINT_EVERY_N_BEATS", "1440"))
        from heart import doctor_setpoint as _ds
        try:
            _need_seed = _ds.hi.read_setpoint() is None
        except Exception:  # noqa: BLE001
            _need_seed = False
        sp_epoch = beat // sp_n if sp_n > 0 else 0
        _cadence_due = sp_n > 0 and sp_epoch >= 1 and sp_epoch > _HEART_STATE["last_setpoint_epoch"]
        if _cadence_due and _HEART_STATE["last_setpoint_epoch"] == 0 and not _need_seed:
            # درسِ ledger ‏2026-07-24: last_setpoint_epoch در حافظه است، پس هر restartِ
            # واچ‌داگ cadenceِ «روزانه» را دوباره می‌چکاند و دکتر یک epoch اضافه می‌نویسد —
            # hysteresis ±۲۰٪ِ w-slow عملاً تند می‌شد (باند در یک روز چند epoch جابه‌جا شد).
            # بازیابیِ stateless: اگر setpointِ روی دیسک داخلِ همین پنجرهٔ epoch نوشته شده،
            # آن epoch قبلاً served است → فقط علامت بزن، ننویس. fail-open به رفتارِ قبلی.
            try:
                import datetime as _dt2
                import json as _json2
                _spd = _json2.loads(_ds.hi.SETPOINT_PATH.read_text("utf-8"))
                _spt = _dt2.datetime.fromisoformat(str(_spd.get("ts")))
                if _spt.tzinfo is not None:
                    _spt = _spt.astimezone().replace(tzinfo=None)
                _beat_s = float(os.environ.get("CHRONO_PERIOD_S", "60.0"))
                if (_dt2.datetime.now() - _spt).total_seconds() < sp_n * _beat_s:
                    _HEART_STATE["last_setpoint_epoch"] = sp_epoch
                    _cadence_due = False
            except Exception:  # noqa: BLE001 — بازیابی هرگز cadence مشروع را نمی‌کشد
                pass
        if _need_seed or _cadence_due:
            if _cadence_due:
                _HEART_STATE["last_setpoint_epoch"] = sp_epoch
            sp = _ds.run_epoch_setpoint(write=True)
            out["setpoint_epoch_seq"] = sp.get("epoch_seq")
            out["setpoint_seeded"] = sp.get("written") and sp.get("rationale", "").startswith("seeded")
        # HH-P9: پمپِ کار — «طبق ضربان، کارِ واقعی». پشتِ flag دوم (پیش‌فرض خاموش،
        # خارج از profile). cadenceِ کار از periodِ سایهٔ همین ضربان فرمان می‌گیرد؛
        # ردهٔ paid (سرچ/LLM) داخلِ پمپ پشتِ live-gateِ دوقفله می‌ماند.
        if flag("OCTOPUS_WIRE_HEART_WORK"):
            try:
                from heart import work_pump as _wp
                out["work"] = _wp.pump_step(beat=beat, period_s=rec.get("period_s"))
            except Exception as _we:  # noqa: BLE001 — §۴: کار نباید ضربان را بکشد
                opslib.alert([f"wiring: work_pump خطا: {type(_we).__name__}: {_we}"])
        return out
    except Exception as e:  # noqa: BLE001 — §۴: قلب نباید tick را بکشد
        opslib.alert([f"wiring: heart_beat خطا: {type(e).__name__}: {e}"])
        return None


def heartstate_beat(beat: int = 0) -> dict | None:
    """HEART-01 · envelope حیاتِ قلب را در سایه persist کن (heartstate-latest.json).

    پشتِ HEARTSTATE_SHADOW (پیش‌فرض خاموش). heartstate.persist خودش هم فلگ را چک می‌کند
    (double-safe): با فلگ خاموش envelope را می‌سازد ولی چیزی نمی‌نویسد. اینجا هم اگر
    heartstate.enabled() خاموش باشد بی‌درنگ None برمی‌گردانیم (no-op؛ صفر I/O، بایت‌به‌بایت).
    kill-switch مقدم. read/observe-only — هیچ کنترل/رفتار (ADR-001). fail-soft."""
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch مقدم
    try:
        _syspath(str(_HERE))
        from heart import heartstate as _hs  # noqa: WPS433 — lazy
        if not _hs.enabled():                # HEARTSTATE_SHADOW خاموش → no-op کامل
            return None
        env = _hs.persist()
        return {"written": bool(env.get("written")),
                "shadow_only": bool(env.get("shadow_only", True)),
                "beat": beat}
    except Exception as e:  # noqa: BLE001 — §۴: heartstate نباید tick را بکشد
        opslib.alert([f"wiring: heartstate_beat خطا: {type(e).__name__}: {e}"])
        return None


def _lead_first_reply_draft(candidate: dict, submit_out: dict) -> dict:
    """کاندیدِ پذیرفته‌شده → **پیش‌نویسِ** پاسخِ اول روی دیسک. هرگز ارسال.

    این تنها صداکنندهٔ تولیدیِ `lead_first_reply` است. بدونِ آن، آن ماژول —
    با ۳۶ تستِ سبز — کدِ مرده بود؛ همان الگویی که در این مخزن دو بار در ۲۴
    ساعت تکرار شد و در حافظه ثبت است.

    مرزها، به‌ترتیبِ اهمیت:
      · **صفر transport.** خروجی یک فایلِ پیش‌نویس است. تبدیلِ پیش‌نویس به
        ایمیلِ واقعی تصمیمِ جداگانه و گیت‌شدهٔ مالک است (`OCTOPUS_SMTP_*` +
        `OCTOPUS_WIRE_LEAD_OUTBOUND`، هر دو امروز تاریک).
      · **رضایت را خودش نمی‌سنجد.** `compose_first_reply` داخلاً از
        `consent_firewall` می‌پرسد و برای هرچه `consented_inbound` نباشد
        `ok=False` و بدنهٔ تهی می‌دهد. اینجا آن حکم فقط رعایت می‌شود.
      · **fail-soft.** هر خطایی بلعیده می‌شود؛ لیدِ ثبت‌شدهٔ بی‌پیش‌نویس بی‌نهایت
        بهتر از لیدِ ازدست‌رفته است.

    ⚠️ شکافِ صادقانه: این پیش‌نویس هنوز **سطحِ مالک‌رو ندارد** — کارتِ تلگرام
    آن را نشان نمی‌دهد. یعنی امروز نوشته می‌شود و کسی نمی‌خواندش. آگاهانه
    این‌طور رها شده تا «نویسنده‌ای بی‌خواننده» در سند ثبت باشد نه پنهان؛
    قدمِ بعدیِ این زنجیره وصلِ همین فایل به کارت است.
    """
    try:
        _syspath(str(_HERE / "legs"))
        import lead_first_reply   # noqa: WPS433 — lazy تا env ِ تست اثر کند
        res = lead_first_reply.compose_first_reply(candidate) or {}
        if not res.get("ok"):
            return res
        lead_id = str((submit_out or {}).get("lead_id") or "").strip()
        if not lead_id:
            return {"ok": False, "reason": "no_lead_id"}
        import json as _json  # noqa: WPS433
        d = opslib.STATE_DIR / "legs" / "lead-first-reply-drafts"
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{lead_id}.json"
        if p.exists():          # idempotent: پیش‌نویسِ موجود بازنویسی نمی‌شود
            return {"ok": True, "reason": "already_drafted"}
        tmp = p.with_suffix(".tmp")
        tmp.write_text(_json.dumps(
            {"lead_id": lead_id, "subject": res.get("subject"),
             "body": res.get("body"), "delivered": False,
             "drafted_at": opslib.now_iso()}, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, p)
        return {"ok": True, "lead_id": lead_id}
    except Exception:  # noqa: BLE001 — §۴: پیش‌نویس هرگز جذبِ لید را نمی‌کشد
        return {"ok": False, "reason": "draft_failed"}


def lead_email_intake_beat(beat: int = 0, fetch_fn=None) -> dict | None:
    """۲۰۲۶-۰۸-۰۱ · **تولیدکنندهٔ گمشدهٔ سرِ لولهٔ لید** — پشتِ OCTOPUS_WIRE_LEAD_EMAIL_INTAKE.

    ممیزیِ ۱۱-ایجنتی: کلِ ماشینِ لید مسلح بود و صفر پروپوزال داشت، چون هر نویسندهٔ
    `state/legs/lead-inbox/` انسان-ماشه بود؛ هیچ producer ای وجود نداشت. این ضربان آن
    producer است: صندوقِ ایمیل را **فقط‌خوانده** می‌خواند، محافظه‌کارانه استعلام را از
    غیرِ استعلام جدا می‌کند، و فقط استعلام‌ها را به درِ canonical ِ
    `lead_candidate_inbox.submit_candidate` می‌دهد.

    مرزها: صفر ارسال (این مسیر هیچ SMTP ای ندارد)؛ صفر حذف/انتقال؛ هرگز `\\Seen`
    نمی‌گذارد (EXAMINE + BODY.PEEK)؛ کانال صادقانه انتخاب می‌شود تا consent_firewall
    سخت‌گیر بماند. پیامِ غیرِ استعلام **هیچ ردی** نمی‌گذارد — سایدکار فقط عدد و کُد دارد،
    نه subject، نه بدنه، نه آدرس. اتصالِ واقعی قفلِ دومِ صریح دارد (OCTOPUS_IMAP_USE_GMAIL)
    چون این صندوقِ **شخصیِ** مالک است؛ بدونِ آن ضربان صادقانه not_armed گزارش می‌دهد.
    kill-switch مقدم؛ pause ِ تک‌پا؛ epoch-gate؛ fail-soft مطلق."""
    if not flag("OCTOPUS_WIRE_LEAD_EMAIL_INTAKE"):
        return None   # flag خاموش = «not wired» (بایت‌به‌بایتِ امروز)
    if leg_paused("lead"):
        return None   # مکثِ تک‌پا از مرکزِ تلگرام (runtime)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch مقدم
    every_n = int(os.environ.get("CHRONO_LEAD_EMAIL_INTAKE_EVERY_N_BEATS", "15"))
    if not _epoch_fire("lead_email_intake", beat, every_n):
        return None
    try:
        _syspath(str(_HERE / "legs"))
        import lead_email_intake   # noqa: WPS433 — lazy تا env ِ تست اثر کند
        r = lead_email_intake.beat(fetch_fn=fetch_fn,
                                   reply_fn=_lead_first_reply_draft) or {}
        out = {k: r.get(k) for k in ("ok", "armed", "fetched", "inquiries", "submitted",
                                     "signals", "duplicates", "dropped", "quarantined",
                                     "replies_drafted", "blocked", "reason")}
        out["beat"] = beat
        try:   # سایدکارِ cockpit — **فقط شمارش و کُد**، هرگز محتوای هیچ پیامی
            sp = opslib.STATE_DIR / "ORGANISM-STATE.lead_email_intake"
            sp.parent.mkdir(parents=True, exist_ok=True)
            import json as _json  # noqa: WPS433
            tmp = sp.with_suffix(".lead_email_intake.tmp")
            tmp.write_text(_json.dumps({**out, "updated_at": opslib.now_iso()},
                                       ensure_ascii=False, indent=2), "utf-8")
            os.replace(tmp, sp)
        except (OSError, TypeError, ValueError):
            pass   # fail-soft: سایدکار اختیاری است
        return out
    except Exception as e:  # noqa: BLE001 — §۴: intake نباید tick را بکشد
        opslib.alert([f"wiring: lead_email_intake_beat خطا: {type(e).__name__}: {e}"])
        return None


def email_beat(beat: int = 0) -> dict | None:
    """LEG-06 · پلِ ایمیلِ ورودی (لیدِ نقاشی از ایمیل) پشتِ OCTOPUS_WIRE_EMAIL.

    پیش‌فرض خاموش و خارج از PAPER_FULL_FLAGS. با فلگ خاموش، email_inbound.poll_and_digest
    خودش no-op برمی‌گرداند و اینجا هم پیش از هر کاری فلگ را چک می‌کنیم → صفر pollِ صندوق
    (بایت‌به‌بایتِ امروز: «not wired»). روشن = هر N beat یک بار صندوق را می‌خواند/parse می‌کند
    (propose-only: فقط تشخیصِ لیدِ کاندید؛ هیچ replyِ خودکار/send). kill-switch مقدم؛ fail-soft.
    ⚠️ هیچ‌گاه پیش‌فرضِ pollِ صندوقِ واقعی را روشن نمی‌کند.

    ۲۰۲۶-۰۸-۰۱ — این تابع علاوه‌بر کارِ خودش، **قبل از** گیتِ OCTOPUS_WIRE_EMAIL،
    `lead_email_intake_beat` را صدا می‌زند (که خودش فلگِ مستقل دارد). چرا اینجا:
    `email_beat` تنها تابعِ ایمیلیِ wiring است که دو صداکنندهٔ تولیدی دارد
    (`organism.py` و `brain_worker.py`) و نویسندهٔ intake مالکِ آن دو فایل نیست.
    اگر producer پشتِ گیتِ OCTOPUS_WIRE_EMAIL می‌ماند، «مسیرِ درست به فرمانِ خاموش»
    می‌شد — یعنی گرسنگیِ بی‌صدا. هر دو فلگ خاموش ⇒ همان None ِ دیروز."""
    _intake = lead_email_intake_beat(beat=beat)
    if not flag("OCTOPUS_WIRE_EMAIL"):
        return _intake   # flag خاموش = «not wired» (رفتارِ فعلی؛ intake ِ خاموش None است)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch مقدم
    every_n = int(os.environ.get("CHRONO_EMAIL_EVERY_N_BEATS", "60"))  # ~۱h با tick=60s
    if not _epoch_fire("email", beat, every_n):
        return None
    try:
        _syspath(str(_HERE / "legs"))
        import email_inbound  # noqa: WPS433 — lazy
        d = email_inbound.poll_and_digest()
        return {"n_unread": d.get("n_unread", 0),
                "n_leads": len(d.get("leads") or []),
                "note": d.get("note"),
                "beat": beat}
    except Exception as e:  # noqa: BLE001 — §۴: email نباید tick را بکشد
        opslib.alert([f"wiring: email_beat خطا: {type(e).__name__}: {e}"])
        return None


def harvest_beat(beat: int = 0) -> dict | None:
    """ضربانِ هاروسترِ AusTender (تری‌اسکن 2026-07-17) — سرِ لولهٔ خشکِ lead-inbox (DAM-1).

    تنها تولیدکنندهٔ صندوقِ لید که کلید نمی‌خواهد (AusTender OCDS عمومی/keyless). هر epoch
    یک fetchِ عمومی → کاندیدهای مرتبطِ نقاشی را به state/legs/lead-inbox می‌نویسد تا
    lead_discovery_beat امتیازشان بدهد. پشتِ OCTOPUS_WIRE_HARVEST (پیش‌فرض خاموش، عمداً
    خارج از PAPER_FULL_FLAGS). kill-switch مقدم؛ هر N beat (CHRONO_HARVEST_EVERY_N_BEATS،
    پیش‌فرض ۷۲۰=~۱۲h — محترمانه با API). صفر ارسال/خرج/راز؛ fail-soft."""
    if not flag("OCTOPUS_WIRE_HARVEST"):
        return None   # flag خاموش = «not wired» (رفتارِ امروز، بایت‌به‌بایت)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch مقدم
    every_n = int(os.environ.get("CHRONO_HARVEST_EVERY_N_BEATS", "720"))
    if not _epoch_fire("harvest", beat, every_n):
        return None
    try:
        _syspath(str(_HERE / "legs"))
        import harvest_austender   # noqa: WPS433 — lazy تا env تست اثر کند
        return harvest_austender.harvest()
    except Exception as e:  # noqa: BLE001 — هاروستر نباید tick را بکشد
        opslib.alert([f"harvest_beat error (non-fatal): {type(e).__name__}: {e}"])
        return None


def _record_lead_decisions(items, beat: int = 0) -> dict:
    """LEG-06 (spine) · تصمیم→اثر→نتیجهٔ لیدهای draft‌شدهٔ این beat را پایدار ثبت کن.

    record-only پشتِ OCTOPUS_WIRE_LEAD_OUTCOME: برای هر لید یک Decision Receiptِ immutable
    (effect_class=E1) + یک Outcome (delivered، sandbox) در state/outcomes می‌نویسد و لینک
    می‌کند؛ اگر Memory Gate از قبل db داشته باشد، memories_used را پر می‌کند. verdict=PENDING.
    هیچ ارسال/پول/EffectorGate/شبکه (خودِ recorder ساختاراً اثبات شده). این «قابلِ‌رسیدن»‌کردنِ
    تولیدکنندهٔ spine است (تا امروز flag داشت ولی صفر caller = ۱/۳ سیم‌کشی). کاملاً fail-soft:
    هرگز beat را نمی‌کشد. items = [(lead, attribution_id), …]. correlation = lead_<aid> (لینکِ پایدار)."""
    out = {"recorded": 0, "errors": 0}
    if not items:
        return out
    o = r = mem = spine = mgate = None
    _esx = None
    try:
        for _p in (str(_HERE / "outcomes"), str(_HERE / "memory"),
                   str(_HERE / "legs"), str(_HERE / "spine")):
            _syspath(_p)
        import outcome_store as _osx        # noqa: WPS433 — lazy
        import decision_receipt as _drx     # noqa: WPS433
        import lead_outcome_recorder as _lor  # noqa: WPS433
        odir = opslib.STATE_DIR / "outcomes"
        odir.mkdir(parents=True, exist_ok=True)
        o = _osx.OutcomeStore(path=odir / "outcomes.db")
        # GAP-1 (۰۷-۳۱): مخزنِ رسید دو-پاره بود — این‌جا outcomes/receipts.db باز
        # می‌شد ولی c6_trigger و verdict_recorder روی receipts/receipts.db می‌نویسند
        # (و روی دیسکِ زنده فقط دومی وجود دارد). «همهٔ رسیدها» باید یک مخزن باشد.
        rdir = opslib.STATE_DIR / "receipts"
        rdir.mkdir(parents=True, exist_ok=True)
        r = _drx.DecisionReceiptStore(rdir / "receipts.db")
        # حافظه: READ (memories_used) اگر db از قبل هست؛ WRITE (episodic) اگر Memory Gate
        # روشن است (آن‌گاه db ساخته می‌شود — این beat تولیدکنندهٔ واقعیِ گیت است، رفعِ dead-flag).
        mem_db = opslib.STATE_DIR / "memory" / "memory.db"
        _gate_on = False
        try:
            import gate as _mgx   # noqa: WPS433
            _gate_on = _mgx.flag_on()
        except Exception:  # noqa: BLE001
            _mgx = None
        if mem_db.exists() or _gate_on:
            try:
                import memory_store as _msx  # noqa: WPS433
                mem_db.parent.mkdir(parents=True, exist_ok=True)
                mem = _msx.MemoryStore(path=mem_db)
                if _gate_on and _mgx is not None:
                    mgate = _mgx.MemoryGate(mem)
            except Exception:  # noqa: BLE001 — حافظه اختیاری است
                mem = mgate = None
        # LEG-07: Event Spine (اختیاری، پشتِ OCTOPUS_WIRE_SPINE) — dual-write زنجیرهٔ
        # decided→delivered به SoTِ یگانه. flag خاموش → spine=None → صفر I/O (db خالی نمی‌سازد).
        try:
            import event_spine as _esx   # noqa: WPS433
            if _esx.flag_on():
                sdir = opslib.STATE_DIR / "spine"
                sdir.mkdir(parents=True, exist_ok=True)
                spine = _esx.EventSpine(path=sdir / "spine.db")
        except Exception:  # noqa: BLE001 — spine اختیاری است
            spine = None
        # W1 · قوسِ یادگیری: همان نوشتنِ حافظه، ولی از learning_gate (بایندِ outcome +
        # رسیدِ اجباری + گیتِ held-out) نه submitِ خام. پشتِ OCTOPUS_WIRE_LEARN_FROM_LEAD
        # (پیش‌فرض خاموش = رفتارِ امروز بایت‌به‌بایت). ارزیابیِ held-out **یک‌بار برای کلِ
        # batch** — fast_ledger_eval یک subprocessِ verify است و per-lead یعنی چند subprocess
        # در یک beat. هر خطا → fail-closed (یاد نمی‌گیریم). صفر شبکه/تلگرام/پول.
        _learn_on = bool(flag("OCTOPUS_WIRE_LEARN_FROM_LEAD") and mgate is not None)
        _lg = None
        _held = {"overall_verdict": "fail", "anti_hacking_flag": False}
        if _learn_on:
            try:
                import learning_gate as _lg   # noqa: WPS433 — lazy
                _held = _lg.fast_ledger_eval()
            except Exception:  # noqa: BLE001 — یادگیری هرگز ثبتِ لید را نمی‌کشد
                _lg, _learn_on = None, False
        for lead, aid in items:
            try:
                res = _lor.record_lead_decision(
                    lead, o, r, memory_store=mem,
                    correlation_id=("lead_" + str(aid or ""))[:64])
                if isinstance(res, dict) and not res.get("skipped"):
                    out["recorded"] += 1
                    if spine is not None:   # dual-write زنجیره به SoTِ یگانه (shadow، fail-soft)
                        try:
                            _via_adapter = os.environ.get("OCTOPUS_SPINE_VIA_ADAPTER") == "1"
                            _sa2 = None
                            if _via_adapter:
                                import spine_adapters as _sa2   # noqa: WPS433
                            for _et, _tr in (("decided", "DETERMINISTIC"),
                                             ("delivered", "UNVERIFIED")):
                                _pl2 = {"receipt_id": res["receipt_id"],
                                        "outcome_ref": res["outcome_ref"],
                                        "verdict": res["verdict"]}
                                # C4: سطحِ تولیدِ واحد پشتِ compat flag (پیش‌فرض 0، parity-proven)
                                if _via_adapter and _sa2 is not None:
                                    _sa2.emit_event(spine=spine, event_type=_et, domain="lead",
                                                    correlation_id=res["correlation_id"],
                                                    mission_id=res["mission_id"],
                                                    subject=res["proposal_id"],
                                                    producer="lead_outcome_recorder",
                                                    trust=_tr, payload=_pl2)
                                else:
                                    _esx.dual_write(spine, {
                                        "event_type": _et, "domain": "lead",
                                        "correlation_id": res["correlation_id"],
                                        "mission_id": res["mission_id"],
                                        "subject": res["proposal_id"],
                                        "producer": "lead_outcome_recorder", "trust": _tr,
                                        "payload": _pl2})
                            out["spine_events"] = out.get("spine_events", 0) + 2
                        except Exception:  # noqa: BLE001 — spine نباید ثبت را بشکند
                            pass
                    if mgate is not None:   # LEG-08: حافظهٔ تصمیم — PII-free
                        try:                # (فقط IDها و دستهٔ قطعی، هرگز متنِ خامِ لید)
                            if _learn_on and _lg is not None:
                                # namespace=semantic چون **تنها خوانندهٔ حافظه** در درختِ زنده
                                # lead_outcome_recorder است و فقط semantic را search می‌کند
                                # (lead_outcome_recorder.py:66) — نوشتنِ episodic یعنی خاطره‌ای
                                # که هرگز استناد نمی‌شود. outcome_ref همان ردیفِ deliveredی است
                                # که همین‌الان نوشته شد → trust به واقعیت bind می‌شود.
                                _lr = _lg.learn_from_outcome(
                                    memory_gate=mgate, receipt_store=r, outcome_store=o,
                                    evaluator=(lambda **_k: _held),
                                    signal={"namespace": "semantic",
                                            "mkey": res["correlation_id"],
                                            "content": (
                                                f"lead-decision category={res.get('category')} "
                                                f"score={res.get('score')} "
                                                f"action={res.get('action')} "
                                                f"value_aud={res.get('value_aud_claimed')} "
                                                f"proposal={res['proposal_id']}"),
                                            "correlation_id": res["correlation_id"],
                                            "mission_id": res["mission_id"],
                                            "outcome_ref": res["outcome_ref"],
                                            "trust": "DETERMINISTIC", "salience": 0.5,
                                            "privacy": "scrubbed", "source": "deterministic",
                                            "producer": "lead_outcome_recorder"})
                                if _lr.get("learned"):
                                    out["memories_written"] = out.get("memories_written", 0) + 1
                                    out["learn_receipts"] = out.get("learn_receipts", 0) + 1
                                else:
                                    # صادقانه: چرا یاد نگرفت (dedup / held-out قرمز / رسید نخورد)
                                    out["learn_blocked"] = out.get("learn_blocked", 0) + 1
                                    out["learn_reason"] = str(_lr.get("reason"))[:100]
                            else:
                                mgate.submit({
                                    "namespace": "episodic", "source": "lead_outcome_recorder",
                                    "mkey": res["correlation_id"], "salience": 0.4,
                                    "privacy": "scrubbed",
                                    "content": (f"lead-decision proposal={res['proposal_id']} "
                                                f"corr={res['correlation_id']} "
                                                f"verdict={res['verdict']} "
                                                f"value_aud={res.get('value_aud_claimed')}")})
                                out["memories_written"] = out.get("memories_written", 0) + 1
                        except Exception:  # noqa: BLE001 — حافظه نباید ثبت را بشکند
                            pass
            except Exception:  # noqa: BLE001 — یک لیدِ بد کلِ ثبت را نکشد
                out["errors"] += 1
    except Exception as _re:  # noqa: BLE001 — §۴: ثبتِ spine هرگز beat را نمی‌کشد
        opslib.alert([f"wiring: lead outcome-record خطا: {type(_re).__name__}: {_re}"])
    finally:
        for _s in (spine, mem, r, o):   # بستنِ WAL (checkpoint TRUNCATE) — ضدِ نشتِ فایلِ ویندوز
            try:
                if _s is not None:
                    _s.close()
            except Exception:  # noqa: BLE001
                pass
    return out


def lead_discovery_beat(lead_leg, beat: int = 0) -> dict | None:
    """مرحلهٔ ۲ نقشهٔ لید (2026-07-15) · SENSE→SCORE→propose پشتِ OCTOPUS_WIRE_LEAD_DISCOVERY.

    پیش‌فرض خاموش و عمداً خارج از PAPER_FULL_FLAGS (تولیدکنندهٔ PROPOSALِ واقعی است؛
    profile هرگز خودکار روشنش نمی‌کند). روشن = هر N beat صندوقِ state/legs/lead-inbox
    را می‌خواند (lead_sense)، با موتورِ قطعیِ $0 امتیاز می‌دهد (lead_scorer)، و فقط برای
    action=='draft' از leg.intake یک PROPOSAL می‌سازد (attribution.propose — پایین‌ترین
    حالت؛ هرگز واردِ fitness نمی‌شود، صفر ارسال/خرج). save/skip فقط آرشیو می‌شوند.
    dedup محتوایی + سقفِ LEAD_DISCOVERY_MAX_PER_BEAT ضدِ سیلِ لجر. kill-switch مقدم؛
    fail-soft؛ سایدکارِ ORGANISM-STATE.lead_discovery (الگوی business_legs).
    ⚠️ propose-only مطلق — این beat هیچ راهی به مشتری/بیرون ندارد."""
    if not flag("OCTOPUS_WIRE_LEAD_DISCOVERY"):
        return None   # flag خاموش = «not wired» (رفتارِ امروز، بایت‌به‌بایت)
    if leg_paused("lead"):
        return None   # مکثِ تک‌پا از مرکزِ تلگرام (runtime)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch مقدم
    if lead_leg is None:
        return None   # نیازمندِ OCTOPUS_WIRE_LEAD (make_lead_leg) — بدونِ پا، propose نداریم
    every_n = int(os.environ.get("CHRONO_LEAD_DISCOVERY_EVERY_N_BEATS", "30"))
    if not _epoch_fire("lead_discovery", beat, every_n):
        return None
    try:
        _syspath(str(_HERE / "legs"))
        import lead_sense    # noqa: WPS433 — lazy
        import lead_scorer   # noqa: WPS433 — lazy
        max_n = int(os.environ.get("LEAD_DISCOVERY_MAX_PER_BEAT", "5"))
        cands = lead_sense.read_inbox(limit=max_n)
        scorer = lead_scorer.LeadScorer()
        proposed = saved = skipped = dups = 0
        _to_record = []   # LEG-06: (lead, attribution_id)های draft‌شده برای ثبتِ spine پس از حلقه
        for path, lead in cands:
            if lead_sense.seen_before(lead):
                lead_sense.mark_processed(path, lead, {"duplicate": True})
                dups += 1
                continue
            sc = scorer.score(lead)
            res = sc.as_dict()
            # مرحلهٔ ۴ (2026-07-15): غنی‌سازیِ اختیاریِ $0 با LLMِ محلی — پشتِ
            # OCTOPUS_WIRE_LEAD_LLM (پیش‌فرض خاموش). امتیازدهندهٔ قاعده‌محور «مرجع»
            # می‌ماند: llm فقط res["llm_note"] می‌افزاید، هرگز score/action را عوض نمی‌کند.
            if flag("OCTOPUS_WIRE_LEAD_LLM"):
                try:
                    _syspath(str(_HERE / "cortex"))
                    import model_router  # noqa: WPS433 — lazy
                    _llm = model_router.ask(
                        "classify",
                        f"این آگهی/سرنخِ نقاشی را در یک جمله دسته‌بندی و فوریتش را بگو:\n"
                        f"{str(lead.get('description', ''))[:400]}",
                        max_tokens=120, tier="local")
                    if _llm.get("ok") and _llm.get("text"):
                        res["llm_note"] = str(_llm["text"])[:200]
                except Exception:  # noqa: BLE001 — غنی‌سازی هرگز beat را نکشد
                    pass
            if sc.action == "draft":
                name = str(lead.get("applicant") or lead.get("address")
                           or str(lead.get("description", ""))[:60]).strip()
                r = lead_leg.intake(name,
                                    float(lead.get("expected_aud") or 0.0),
                                    cell="lead.doer",
                                    description=str(lead.get("description", ""))[:200],
                                    day=lead.get("day"))
                res["intake"] = r
                if r.get("ok"):
                    proposed += 1
                    # مرحلهٔ ۵ (2026-07-15): لیدِ mint‌شده → پیش‌فاکتورِ قیمت‌خوردهٔ DRAFT
                    # پشتِ OCTOPUS_WIRE_LEAD_DRAFT (خاموش). create_quote یتیم بود (۰ caller)؛
                    # حالا با attribution_id واقعی + intakeِ نگاشتی صدا می‌شود. draft_only=True،
                    # sent=False — هیچ ارسالی وجود ندارد.
                    if flag("OCTOPUS_WIRE_LEAD_DRAFT"):
                        try:
                            import lead_quote  # noqa: WPS433 — lazy
                            q = lead_quote.create_quote(
                                lead_leg, r["attribution_id"],
                                lead_quote.lead_to_intake(lead, res))
                            if q.get("ok"):
                                res["quote"] = {"qt_number": q.get("qt_number"),
                                                "total_incl_gst": (q.get("breakdown") or {})
                                                .get("total_incl_gst")}
                        except Exception as _qe:  # noqa: BLE001 — quote نباید beat را بکشد
                            opslib.alert([f"wiring: lead quote-draft خطا: "
                                          f"{type(_qe).__name__}: {_qe}"])
                    # LEG-06 (spine): این لیدِ draft‌شده را برای ثبتِ تصمیم→اثر→نتیجه صف کن
                    # (پشتِ OCTOPUS_WIRE_LEAD_OUTCOME؛ خاموش = صف خالی = هیچ). ثبت پس از حلقه.
                    if flag("OCTOPUS_WIRE_LEAD_OUTCOME"):
                        _to_record.append((lead, r.get("attribution_id")))
                else:
                    skipped += 1   # intake fail-closed → صادقانه skip بشمار
            elif sc.action == "save":
                saved += 1
            else:
                skipped += 1
            lead_sense.mark_processed(path, lead, res)
        result = {"sensed": len(cands), "proposed": proposed, "saved": saved,
                  "skipped": skipped, "duplicates": dups, "beat": beat,
                  "propose_only": True}
        if _to_record:   # LEG-06: ثبتِ پایدارِ spine (record-only، fail-soft — هرگز beat را نمی‌کشد)
            result["outcomes"] = _record_lead_decisions(_to_record, beat=beat)
        try:
            sp = opslib.STATE_DIR / "ORGANISM-STATE.lead_discovery"
            sp.parent.mkdir(parents=True, exist_ok=True)
            import json as _json  # noqa: WPS433
            tmp = sp.with_suffix(".lead_discovery.tmp")
            tmp.write_text(_json.dumps({**result, "updated_at": opslib.now_iso()},
                                       ensure_ascii=False, indent=2), "utf-8")
            os.replace(tmp, sp)
        except (OSError, TypeError, ValueError):
            pass   # fail-soft: سایدکار اختیاری است
        return result
    except Exception as e:  # noqa: BLE001 — §۴: discovery نباید tick را بکشد
        opslib.alert([f"wiring: lead_discovery_beat خطا: {type(e).__name__}: {e}"])
        return None


def lead_pipeline_beat(lead_leg=None, beat: int = 0, send_fn=None) -> dict | None:
    """Lane G (منشور TG-UI ۲۰۲۶-۰۷-۳۱، رأی ۱۳/۱۷/۱۸) · ارکستراتورِ ماشینِ لید — پشتِ
    OCTOPUS_WIRE_LEAD_PIPELINE (پیش‌فرض خاموش، عمداً خارج از PAPER_FULL_FLAGS).

    حلقهٔ کامل در legs/lead_pipeline.beat: کشف→تحقیق→امتیاز→پیش‌نویس→گیر=کارِ BLOCKED با
    سؤالِ فارسی→لیدِ آماده=کارت در 🎨 (stream="lead"). **هیچ ارسالِ خروجی به مشتری** —
    کارت فقط با send_fn ِ کانالِ approval (لِینِ سریِ سیم‌کشی پاس می‌دهد؛ بدونش headless).
    ارسالِ واقعی همچنان فقط از قوسِ verdict→lead_effect_gate→outbound_worker (سقفِ ۱۰/روز،
    رأی مالک ۲۰۲۶-۰۷-۳۱). هم‌الگوی lead_discovery_beat: kill-switch مقدم، pause ِ تک‌پا،
    epoch-gate، fail-soft مطلق."""
    if not flag("OCTOPUS_WIRE_LEAD_PIPELINE"):
        return None   # flag خاموش = «not wired» (بایت‌به‌بایتِ امروز)
    if leg_paused("lead"):
        return None   # مکثِ تک‌پا از مرکزِ تلگرام (runtime)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch مقدم
    every_n = int(os.environ.get("CHRONO_LEAD_PIPELINE_EVERY_N_BEATS", "30"))
    if not _epoch_fire("lead_pipeline", beat, every_n):
        return None
    result = None
    try:
        _syspath(str(_HERE / "legs"))
        import lead_pipeline   # noqa: WPS433 — lazy
        result = lead_pipeline.beat(deps={"lead_leg": lead_leg, "send_fn": send_fn})
    except Exception as e:  # noqa: BLE001 — §۴: pipeline نباید tick را بکشد
        opslib.alert([f"wiring: lead_pipeline_beat خطا: {type(e).__name__}: {e}"])
        return None
    # ── درایورِ قوسِ ارسال (بازبینی ۰۷-۳۱، wiring W2؛ در deploy تاریک) ──────────
    # فقط با فلگِ مسترِ OCTOPUS_WIRE_LEAD_OUTBOUND (پیش‌فرض خاموش = بایت‌به‌بایتِ
    # امروز؛ خودِ drive_outbound هم اول فلگ را چک می‌کند — دو قفله). گیت با همان
    # کارخانهٔ canonical ِ chrono ساخته می‌شود که make_telegram_channel به
    # approval_channel تزریق می‌کند (live_loop گیتش را از channel.gate می‌گیرد که
    # خروجیِ همین کارخانه است) — یک ChronoDB، یک حقیقت. fail-soft مطلق.
    if flag("OCTOPUS_WIRE_LEAD_OUTBOUND"):
        try:
            import chrono as _chrono_lp   # noqa: WPS433 — lazy
            _gdb = _chrono_lp.ChronoDB(str(opslib.STATE_DIR / "chrono.db"))
            _gate_lp = _chrono_lp.EffectorGate(db=_gdb)
            import outbound_worker as _ow_lp   # noqa: WPS433 — lazy
            _drv = _ow_lp.drive_outbound(gate=_gate_lp)
            if isinstance(result, dict) and isinstance(_drv, dict):
                result["outbound"] = _drv
        except Exception as e:  # noqa: BLE001 — درایور هرگز beat را نمی‌کشد
            opslib.alert([f"wiring: drive_outbound خطا: {type(e).__name__}: {e}"])
    return result


# ─── قرارداد مشترکِ ۴ پای بیزنسیِ نو (mining/crypto/accounting/knowledge) ─────────
# WP-F ماژول‌ها را می‌سازد؛ اینجا (WP-C) status()های read-only را جمع می‌کنیم؛ WP-D در
# رندر می‌خواند. هر پا یک helperِ ماژول‌سطحِ فقط‌خواندنی دارد:
#   <name>_leg.<name>_status() -> {"leg","live","signal","note"}.
_BUSINESS_LEGS_SPEC = (
    # 2026-07-25 (رأیِ مالک «آگاهیِ اختاپوس به این پا»): پای درآمدیِ نقاشی **اول** می‌آید.
    # تا امروز این فهرست چهار پا داشت که هر چهار skeleton/کهنه‌اند و تنها پای زندهٔ
    # درآمدی در آن نبود — یعنی خودآگاهیِ ارگانیسم پاهای مرده را می‌شمرد و کسب‌وکارِ
    # واقعی را نمی‌دید. lead_status فقط‌خواندنی و fail-soft است (الگوی همان چهار).
    ("lead", "lead_leg", "lead_status"),
    # 2026-08-02 G-02: sync_agent was armed but invisible in ORGANISM-STATE/cards.
    # Status-only/read-only/fail-soft like the other business legs.
    ("sync_agent", "sync_agent", "sync_agent_status"),
    ("mining", "mining_leg", "mining_status"),
    ("crypto", "crypto_leg", "crypto_status"),
    ("accounting", "accounting_leg", "accounting_status"),
    ("knowledge", "knowledge_leg", "knowledge_status"),
    # 2026-08-03 (رأیِ مالک «هرکاری می‌کنن اختاپوس یادش بمونه»): پای Project-F تا امروز
    # در این فهرست **نبود** — نه زنده گزارش می‌شد نه مرده، یعنی در خودآگاهیِ ارگانیسم
    # وجود نداشت (همان بیماریِ ۰۷-۲۵ که برای `lead` بالا ثبت شده). status فقط‌خواندنی،
    # fail-soft و **content-free** است (مرزِ قاعدهٔ #۷: صفر متن/هویت، فقط شمار).
    ("studio_pf", "studio_pf_leg", "studio_pf_status"),
)


def business_legs_beat(beat: int = 0, write: bool = True) -> dict | None:
    """۴ پای بیزنسیِ نو را جمع کن → ORGANISM-STATE key «business_legs».

    status()ها read-only + بی‌خطرند (صفر spend/outward) پس این beat فلگ لازم ندارد؛ فقط
    kill-switch مقدم است. هر helper در try مستقل: نبودِ ماژول/helper یا خطا →
    {"live": False, "note": "…"} (fail-soft، هرگز beat را نمی‌کشد). خروجی برای merge در
    ORGANISM-STATE توسطِ organism.py، و — چون organism.py تنها writerِ فایلِ اصلی است —
    یک سایدکارِ ORGANISM-STATE.business_legs هم نوشته می‌شود تا مستقلاً قابل‌مشاهده باشد
    (همان الگوی ORGANISM-STATE.ziman)."""
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch مقدم
    _syspath(str(_HERE / "legs"))
    legs: dict = {}
    for name, mod_name, fn_name in _BUSINESS_LEGS_SPEC:
        try:
            mod = __import__(mod_name)
            fn = getattr(mod, fn_name, None)
            if fn is None:
                raise AttributeError(f"{fn_name} missing")
            st = fn()
            if not isinstance(st, dict):
                raise TypeError("status is not a dict")
            st.setdefault("leg", name)
            legs[name] = st
        except Exception as e:  # noqa: BLE001 — نبودِ یک پا نباید بقیه/beat را بکشد
            legs[name] = {"leg": name, "live": False, "signal": "unknown",
                          "note": f"status unavailable ({type(e).__name__})"}
    result = {"business_legs": legs, "beat": beat}
    if write:
        try:
            sp = opslib.STATE_DIR / "ORGANISM-STATE.business_legs"
            sp.parent.mkdir(parents=True, exist_ok=True)
            import json as _json  # noqa: WPS433
            tmp = sp.with_suffix(".business_legs.tmp")
            tmp.write_text(_json.dumps({**result, "updated_at": opslib.now_iso()},
                                       ensure_ascii=False, indent=2), "utf-8")
            os.replace(tmp, sp)
        except (OSError, TypeError, ValueError):
            pass   # fail-soft: سایدکار اختیاری است
    return result


# ── زیر-OSِ Mining ────────────────────────────────────────────────────────────
# ۲۰۲۶-۰۷-۲۸ — **بازسازیِ سیم‌کشیِ گم‌شده.** بستهٔ `mining_os/` در `88aaa29` کامیت شد
# (۲۴ فایل، ۳۲ تستِ سبز) ولی هوکِ صداکننده‌اش هرگز کامیت نشد. `mining_os/ACTIVATION.md`
# می‌گفت «وصل‌شده به organism.py:712» — آن خط بلوکِ **فیشر** است، و grep روی کلِ `_ops`
# صفر ارجاع به mining_os می‌داد. یعنی یک بستهٔ کامل با تست‌های سبز که هیچ‌وقت اجرا
# نمی‌شد: «سبز به‌خاطرِ نبودِ صداکننده». فلگ هم وجود نداشت، پس «روشن‌کردنِ فلگ» ممکن نبود.
_MINING_OS_DIR = _HERE.parent / "03 - Projects" / "Mining"   # از __file__، پس worktree-safe


def mining_os_beat(beat: int = 0, write: bool = True) -> dict | None:
    """ضربانِ زیر-OSِ Mining → ORGANISM-STATE key «mining_os» + سایدکارِ اتمیک.

    پشتِ OCTOPUS_WIRE_MINING_OS — پیش‌فرض خاموش و **عمداً خارج از PAPER_FULL_FLAGS**
    (فعال‌سازی فقط با رأیِ صریحِ مالک، هم‌الگویِ asset_map). با فلگِ خاموش → None،
    یعنی رفتارِ امروز بایت‌به‌بایت. kill-switch مقدم. cadence با
    CHRONO_MINING_OS_EVERY_N_BEATS (پیش‌فرض ۰ = هر beat، مطابقِ قراردادِ ACTIVATION.md).

    `mining_os.loop.tick` خودش fail-soft است و هرگز استثنا پرت نمی‌کند، ولی **import**ش
    می‌تواند شکست بخورد (پوشهٔ پروژه جابه‌جا/غایب) — پس اینجا هم try. propose-only مطلق:
    فقط‌خواندنی، صفر spend/outward/SSH (D-20)، wallet همیشه False (D-11)."""
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch مقدم
    if not flag("OCTOPUS_WIRE_MINING_OS"):
        return None   # flag خاموش = «not wired» (رفتارِ امروز، بایت‌به‌بایت)
    if not _epoch_fire("mining_os", beat,
                       os.environ.get("CHRONO_MINING_OS_EVERY_N_BEATS", "0")):
        return None
    try:
        _syspath(str(_MINING_OS_DIR))
        from mining_os.loop import tick as _mining_tick  # noqa: WPS433 — lazy
        # write را واقعاً پاس بده: وگرنه mining_os_beat(write=False) فقط سایدکارِ _ops
        # را ساکت می‌کرد و snapshotِ داخلِ بسته را همچنان می‌نوشت (قولِ شکسته).
        snap = _mining_tick(beat, write=write)
    except Exception as e:  # noqa: BLE001 — زیر-OS نباید tickِ ارگانیسم را بکشد
        opslib.alert([f"wiring: mining_os_beat خطا: {type(e).__name__}: {e}"])
        return None
    result = {"mining_os": snap, "beat": beat}
    if write:
        try:
            sp = opslib.STATE_DIR / "ORGANISM-STATE.mining_os"
            sp.parent.mkdir(parents=True, exist_ok=True)
            import json as _json  # noqa: WPS433
            tmp = sp.with_suffix(".mining_os.tmp")
            tmp.write_text(_json.dumps({**result, "updated_at": opslib.now_iso()},
                                       ensure_ascii=False, indent=2), "utf-8")
            os.replace(tmp, sp)
        except (OSError, TypeError, ValueError):
            pass   # fail-soft: سایدکار اختیاری است
    return result


def asset_map_beat(beat: int = 0) -> dict | None:
    """نظارتِ دارایی (ASSET-OVERSIGHT): نقشهٔ داراییِ کل را جمع کن → ORGANISM-STATE key
    «asset_map» + سایدکارِ اتمیکِ ORGANISM-STATE.asset_map.

    پشتِ OCTOPUS_WIRE_ASSET_MAP — پیش‌فرض خاموش و **عمداً خارج از PAPER_FULL_FLAGS**
    (فعال‌سازی فقط با رأیِ صریحِ مالک). با فلگِ خاموش → None (رفتارِ امروز، بایت‌به‌بایت).
    kill-switch مقدم؛ هر N beat (CHRONO_ASSET_MAP_EVERY_N_BEATS، پیش‌فرض ۲۴۰).

    asset_map_status() فقط‌خواندنی + fail-soft است (یک پای خراب نقشه را نمی‌کشد) و
    **هرگز مبلغ/net-worth** محاسبه یا echo نمی‌کند — فقط سیگنالِ امن + پیشنهادِ advisory.
    propose-only مطلق: هیچ اکشنِ اجراپذیر، صفر spend/outward/trade."""
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch مقدم
    if not flag("OCTOPUS_WIRE_ASSET_MAP"):
        return None   # flag خاموش = «not wired» (رفتارِ امروز، بایت‌به‌بایت)
    every_n = int(os.environ.get("CHRONO_ASSET_MAP_EVERY_N_BEATS", "240"))
    if not _epoch_fire("asset_map", beat, every_n):
        return None
    try:
        _syspath(str(_HERE / "legs"))
        import asset_map   # noqa: WPS433 — lazy تا env تست اثر کند
        result = asset_map.asset_map_status()
        # ── سایدکارِ اتمیک (الگوی business_legs/legs_cultivation)
        try:
            sp = opslib.STATE_DIR / "ORGANISM-STATE.asset_map"
            sp.parent.mkdir(parents=True, exist_ok=True)
            import json as _json  # noqa: WPS433
            tmp = sp.with_suffix(".asset_map.tmp")
            tmp.write_text(_json.dumps({**result, "beat": beat,
                                        "updated_at": opslib.now_iso()},
                                       ensure_ascii=False, indent=2), "utf-8")
            os.replace(tmp, sp)
        except (OSError, TypeError, ValueError):
            pass   # fail-soft: سایدکار اختیاری است
        return result
    except Exception as e:  # noqa: BLE001 — §۴: نظارتِ دارایی نباید tick را بکشد
        opslib.alert([f"wiring: asset_map_beat خطا: {type(e).__name__}: {e}"])
        return None


_ACCT_STATE = {"last_epoch": 0}      # الگوی _HEART_STATE — پنجرهٔ epoch ضدِ aliasing


def _ps_flag_on() -> bool:
    """گرامرِ واحدِ فلگِ PocketSmith (اسکن #19): 1/true/yes/on — هم‌رفتار با pocketsmith_api."""
    return str(os.environ.get("OCTOPUS_WIRE_POCKETSMITH", "") or "").strip().lower() \
        in ("1", "true", "yes", "on")


def acct_beat(beat: int = 0) -> dict | None:
    """ضربانِ زندهٔ حسابداری (2026-07-16) — ضدِ فراموشی + دقت، propose-only مطلق.

    پشتِ OCTOPUS_WIRE_ACCT_BEAT — پیش‌فرض خاموش و **عمداً خارج از PAPER_FULL_FLAGS**
    (فعال‌سازی فقط با رأیِ صریحِ مالک). خاموش → None (رفتارِ امروز، بایت‌به‌بایت).
    kill-switch مقدم؛ هر N beat (CHRONO_ACCT_EVERY_N_BEATS، پیش‌فرض ۲۴۰).

    هر دور (همه $0، محلی، بدونِ LLM):
      ۱) acct_memory.rebuild — قواعدِ merchant از تأییدهای مالک (بازتولیدپذیر؛ crash/sync
         هیچ دانشی را نمی‌کشد) + evaluate → سنجهٔ drift (دقتِ قواعد روی طلایی).
      ۲) journal_bridge.rebuild — صفِ ثبتِ /books تازه (idempotent، تصمیم‌ها دست‌نخورده).
      ۳) شمارش‌های صادق → سایدکارِ اتمیکِ ORGANISM-STATE.accounting (خوراکِ دایجست/کابین):
         needs_review، پیشنهادهای منتظر، قواعدِ فعال، drift_alarm.
    pullِ شبکه (sync_network) فقط اگر مالک جدا ACCT_BEAT_SYNC=1 هم بدهد (پیش‌فرض: بدونِ
    شبکه — ضربان local می‌ماند و /sync دستِ مالک). هرگز ثبت/پول/LLM در ضربان."""
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch مقدم
    if not flag("OCTOPUS_WIRE_ACCT_BEAT"):
        return None   # flag خاموش = «not wired» (رفتارِ امروز، بایت‌به‌بایت)
    # پنجرهٔ epoch (اسکن #26: tickِ ۳۰۰s ضربانِ ۶۰s را نمونه‌برداری می‌کند — `beat % N`
    # شلیک‌ها را از دست می‌دهد؛ الگوی مستندِ درست: هر epoch حداکثر یک شلیک)
    every_n = max(1, int(os.environ.get("CHRONO_ACCT_EVERY_N_BEATS", "240")))
    epoch = beat // every_n
    if not _epoch_window("accounting", epoch, _ACCT_STATE):
        return None
    _ACCT_STATE["last_epoch"] = epoch
    try:
        _syspath(str(_HERE / "legs"))
        import acct_memory   # noqa: WPS433 — lazy تا env تست اثر کند
        import journal_bridge  # noqa: WPS433
        result: dict = {"synced": False}
        if os.environ.get("ACCT_BEAT_SYNC") == "1" and _ps_flag_on():
            try:
                import accountant  # noqa: WPS433
                sn = accountant.sync_network()          # confirm-preserving (content-hash pin)
                result["synced"] = bool(sn.get("ok"))
                result["sync_restored"] = sn.get("restored_confirmed")
            except Exception:  # noqa: BLE001 — شبکه اختیاری است؛ ضربان local ادامه می‌دهد
                result["synced"] = False
        mem = acct_memory.rebuild()
        ev = acct_memory.evaluate()
        jb = journal_bridge.rebuild()
        # شمارشِ صفِ مرور از store (بدونِ pull)
        pending_review = 0
        try:
            txns = acct_memory._load_txns()
            pending_review = sum(1 for t in txns if isinstance(t, dict)
                                 and t.get("review") == "needs_review")
        except Exception:  # noqa: BLE001
            pass
        result.update({
            "memory_rules": mem.get("rules", 0), "memory_active": mem.get("active", 0),
            "golden_n": ev.get("n", 0), "accuracy_pct": ev.get("accuracy_pct"),
            "drift_alarm": bool(ev.get("drift_alarm")),
            "pending_review": pending_review,
            "pending_books": jb.get("pending", 0) if isinstance(jb, dict) else 0,
        })
        if result["drift_alarm"]:
            opslib.alert(["accounting: دقتِ قواعدِ حافظه زیرِ ۹۰٪ افتاد (drift) — "
                          "چند تأییدِ اخیر با الگو ناسازگارند؛ /review را مرور کن"])
        # ── سایدکارِ اتمیک (الگوی asset_map_beat)
        try:
            sp = opslib.STATE_DIR / "ORGANISM-STATE.accounting"
            sp.parent.mkdir(parents=True, exist_ok=True)
            import json as _json  # noqa: WPS433
            tmp = sp.with_suffix(".accounting.tmp")
            tmp.write_text(_json.dumps({**result, "beat": beat,
                                        "updated_at": opslib.now_iso()},
                                       ensure_ascii=False, indent=2), "utf-8")
            os.replace(tmp, sp)
        except (OSError, TypeError, ValueError):
            pass   # fail-soft: سایدکار اختیاری است
        return result
    except Exception as e:  # noqa: BLE001 — §۴: حسابداری نباید tick را بکشد
        opslib.alert([f"wiring: acct_beat خطا: {type(e).__name__}: {e}"])
        return None


def legs_cultivation_beat(beat: int = 0, sensory_bus=None,
                          school_bridge=None) -> dict | None:
    """متابولیسمِ دادهٔ $0 برای همهٔ پاها (2026-07-16) — تعمیمِ SENSE→DIGESTِ لید.

    پشتِ OCTOPUS_WIRE_LEG_CULTIVATE — پیش‌فرض خاموش و **عمداً خارج از PAPER_FULL_FLAGS**
    (فعال‌سازی فقط با رأی صریحِ مالک). با فلگِ خاموش → None، صندوق‌ها بایت‌به‌بایت
    دست‌نخورده (رفتارِ امروز). روشن = هر N beat (CHRONO_CULTIVATE_EVERY_N_BEATS،
    پیش‌فرض ۶۰) صندوقِ هر پا (state/legs/<leg>-inbox) با سقفِ LEG_CULTIVATE_MAX_PER_BEAT
    هضم می‌شود (leg_cultivate.cultivate_all): dedup محتوایی + انتقال-نه-حذف + سایدکار.

    سه خروجی (همه propose-only، صفر ارسال/خرج):
      ۱) digestِ پاها → merge در ORGANISM-STATE با کلیدِ legs_cultivation + سایدکارِ
         اتمیکِ ORGANISM-STATE.legs_cultivation (الگوی business_legs).
      ۲) گزارشِ فشردهٔ state/legs/cultivation-report.json برای دکترِ تکاملی —
         doctor.mine پاهای گرسنه/منبعِ راکد را به‌عنوانِ کاندیدِ گلوگاه می‌بیند
         (RFCِ propose-only مثلِ امروز؛ هیچ اتونومیِ نو).
      ۳) پیوندِ مغزِ B: به‌ازای هر digestِ واقعی (digested>0) یک Observationِ انتزاعی
         (فقط شمارش — صفر PII) → sensory_bus.ingest → school_bridge.learn_from
         (persist=True). بدونِ bus/bridge (فلگ‌های SCHOOL خاموش) صادقانه skip می‌شود.
    kill-switch مقدم؛ fail-soft (هرگز tick را نمی‌کشد)."""
    if not flag("OCTOPUS_WIRE_LEG_CULTIVATE"):
        return None   # flag خاموش = «not wired» (رفتارِ امروز، بایت‌به‌بایت)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch مقدم
    every_n = int(os.environ.get("CHRONO_CULTIVATE_EVERY_N_BEATS", "60"))
    if not _epoch_fire("cultivate", beat, every_n):
        return None
    try:
        _syspath(str(_HERE / "legs"))
        # ── قبل از هضم: خوراکِ حسّی (رأی مالک 2026-08-12) — پشتِ فلگ جدا
        feed_report = None
        if flag("OCTOPUS_WIRE_LEG_FEED"):
            try:
                import leg_feed  # noqa: WPS433 — lazy
                feed_report = leg_feed.ensure_food(force=False)
            except Exception as _fe:  # noqa: BLE001 — feed نباید cultivate را بکشد
                opslib.alert([f"wiring: leg_feed خطا: {type(_fe).__name__}: {_fe}"])
        import leg_cultivate   # noqa: WPS433 — lazy
        max_n = int(os.environ.get("LEG_CULTIVATE_MAX_PER_BEAT", "10"))
        report = leg_cultivate.cultivate_all(limit_per_leg=max_n, write_report=True)
        legs = report.get("legs") or {}
        result = {"legs": legs, "starved_legs": report.get("starved_legs") or [],
                  "stale_legs": report.get("stale_legs") or [],
                  "digested_total": sum(int(d.get("digested") or 0)
                                        for d in legs.values() if isinstance(d, dict)),
                  "beat": beat, "propose_only": True,
                  "feed": ({"fed": [x.get("leg") for x in (feed_report or {}).get("fed") or []],
                            "skipped": (feed_report or {}).get("skipped") or [],
                            "pulses": (feed_report or {}).get("pulses") or []}
                           if isinstance(feed_report, dict) else None)}
        # ── پیوندِ مغزِ B (اختیاری): digestها → آورانِ School (صفر PII، فقط ساختار)
        school_report = None
        if sensory_bus is not None:
            try:
                _syspath(str(_HERE / "afferent"))
                from sensory_bus import Observation   # noqa: WPS433 — lazy
                events = []
                for name, d in legs.items():
                    n = int(d.get("digested") or 0) if isinstance(d, dict) else 0
                    if n <= 0:
                        continue   # یک event به‌ازای هر digestِ واقعی — نه اسپم برای صفر
                    ev = sensory_bus.ingest(Observation(
                        source=f"legs.{name}", obs_type="status",
                        label=f"cultivation · {name} digested {n} items (structure only)",
                        intensity=min(0.5, 0.2 + 0.05 * n)))
                    events.append(ev)
                if school_bridge is not None and \
                        any(getattr(e, "afferent", False) for e in events):
                    school_report = school_bridge.learn_from(events, persist=True)
            except Exception as _se:  # noqa: BLE001 — پیوندِ مغز نباید هضم را بکشد
                opslib.alert([f"wiring: legs_cultivation school-link خطا: "
                              f"{type(_se).__name__}: {_se}"])
        result["school"] = ({"taught_signals": school_report.get("taught_signals")}
                            if isinstance(school_report, dict) else None)
        # ── سایدکارِ اتمیک (الگوی business_legs/lead_discovery)
        try:
            sp = opslib.STATE_DIR / "ORGANISM-STATE.legs_cultivation"
            sp.parent.mkdir(parents=True, exist_ok=True)
            import json as _json  # noqa: WPS433
            tmp = sp.with_suffix(".legs_cultivation.tmp")
            tmp.write_text(_json.dumps({**result, "updated_at": opslib.now_iso()},
                                       ensure_ascii=False, indent=2), "utf-8")
            os.replace(tmp, sp)
        except (OSError, TypeError, ValueError):
            pass   # fail-soft: سایدکار اختیاری است
        return result
    except Exception as e:  # noqa: BLE001 — §۴: cultivation نباید tick را بکشد
        opslib.alert([f"wiring: legs_cultivation_beat خطا: {type(e).__name__}: {e}"])
        return None


# ════════════════════════════════════════════════════════════════════════════════
# جلسه ۴۶ — needs_nudge: نوتیفِ هوشمند «وقتی به داده/تأییدت نیاز است» (ADHD-first)
# ════════════════════════════════════════════════════════════════════════════════
_NUDGE_STATE = {"last_epoch": 0}


def needs_nudge_beat(channel=None, beat: int = 0) -> dict | None:
    """هر N beat (پیش‌فرض ۳۶۰ = ~۶ ساعت با ضربانِ ۶۰s) نیازها را حساب کن و فقط اگر
    چیزی «عوض شده» یک پیامِ کوتاه به مالک بفرست. پشتِ OCTOPUS_WIRE_NEEDS_NUDGE.

    ضدِ اسپم (مغزِ ADHD را بمباران نکن): throttle با hashِ نیازها در
    state/needs-nudge.json — همان نیازها دوباره فرستاده نمی‌شوند مگر ۲۴h بگذرد و
    هنوز کارتِ معلق باشد. kill-switch اول؛ فقط‌خواندنی + یک sendMessage."""
    if not flag("OCTOPUS_WIRE_NEEDS_NUDGE"):
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    every_n = int(os.environ.get("CHRONO_NUDGE_EVERY_N_BEATS", "360"))
    if beat <= 0 or every_n <= 0:
        return None
    epoch = beat // every_n
    if not _epoch_window("needs_nudge", epoch, _NUDGE_STATE):
        return None
    _NUDGE_STATE["last_epoch"] = epoch
    try:
        import json
        _syspath(str(_HERE / "budget"))
        import needs_digest
        pending = None
        if channel is not None and hasattr(channel, "_count_pending"):
            try:
                pending = channel._count_pending()
            except Exception:  # noqa: BLE001
                pending = None
        d = needs_digest.compute(pending_count=pending)
        st_path = opslib.STATE_DIR / "needs-nudge.json"
        try:
            st = json.loads(st_path.read_text("utf-8")) if st_path.exists() else {}
        except (OSError, ValueError):
            st = {}
        import datetime as _dt
        now = _dt.datetime.now().timestamp()
        aged = (now - float(st.get("last_ts", 0))) > 86400
        # ۲۰۲۶-۰۷-۲۸ — `stable_hash` به‌جای `hash`: شمارندهٔ هشدار (۱۳→۱۴→۲۵)
        # متنِ آیتم را عوض می‌کرد و همان سه نگرانی را دوباره «تغییر» می‌نمایاند.
        h = d.get("stable_hash") or d["hash"]
        changed = h != st.get("last_hash")
        # و گاردِ تلاشِ مکرر: تا امروز حالت **فقط بعد از ارسالِ موفق** نوشته
        # می‌شد، پس هر ارسالِ ناموفق (ساعتِ سکوت، خطای شبکه، یا نگه‌داشتنِ
        # سیاستِ سطح) یعنی حالت کهنه می‌ماند و همان کارت هر epoch دوباره تلاش
        # می‌شد. اندازه‌گیری: دو نگه‌داشتهٔ یکسان با فاصلهٔ ۶ دقیقه.
        # حالا محتوای یکسان حداکثر ساعتی یک‌بار تلاش می‌کند.
        # ⚠️ اصلاحِ همان روز. نسخهٔ اول شرط را روی `changed` گذاشته بود، ولی
        # `last_hash` فقط با ارسالِ **موفق** جلو می‌رود. حالا که سیاستِ سطح این
        # جریان را نگه می‌دارد، ارسالِ موفقی در کار نیست ⇒ `changed` برای همیشه
        # True ⇒ گارد هرگز شلیک نمی‌کرد. دیده‌بانِ زنده گرفتش، نه سوئیت.
        #
        # مُهر باید روی «چه چیزی را آخرین بار **تلاش** کردم» بنشیند، نه «چه چیزی
        # را رساندم». آن دو یک چیز نیستند، و همین تفاوت کلِ گارد را بی‌اثر کرد.
        # نتیجه: محتوای یکسان حداکثر ساعتی یک تلاش — چه برسد چه نه؛ و اگر
        # نگه‌داشتن برداشته شود، ساعتِ بعد دوباره تلاش می‌کند و گم نمی‌شود.
        same_attempt = (h == st.get("last_attempt_hash"))
        too_soon = same_attempt and (now - float(st.get("last_attempt", 0))) < 3600
        should_send = d["n"] > 0 and (changed or (aged and pending)) and not too_soon
        sent = False
        if should_send and channel is not None and getattr(channel, "wired", False):
            body = "\n".join(f"• {it}" for it in d["items"])
            kb = {"inline_keyboard": [[
                {"text": "📌 الان — کارای من", "callback_data": "menu:now"}]]}
            sent = bool(_send_stream(channel, 
                f"🔔 <b>نیازت دارم</b> ({d['n']})\n──────────\n{body}", kb,
                    stream="needs"))
            # حالت **همیشه** نوشته می‌شود، نه فقط بعد از موفقیت.
            # `last_hash`/`last_ts` فقط با ارسالِ واقعی جلو می‌روند (پس کارتی که
            # هرگز نرسید بعداً دوباره تلاش می‌کند و گم نمی‌شود)، ولی
            # `last_attempt` هر بار ثبت می‌شود تا تلاشِ مکرر کران‌دار بماند.
            with opslib.LockedJson(st_path) as lj:
                lj.write({"last_hash": h if sent else st.get("last_hash"),
                          "last_ts": now if sent else float(st.get("last_ts", 0)),
                          "last_attempt": now, "last_attempt_hash": h,
                          "last_n": d["n"], "ts": opslib.now_iso()})
        return {"n": d["n"], "changed": changed, "sent": sent}
    except Exception as e:  # noqa: BLE001 — §۴: نوتیف نباید tick را بکشد
        opslib.alert([f"wiring: needs_nudge خطا: {type(e).__name__}: {e}"])
        return None


def cortex_vitals_beat(beat: int = 0) -> dict | None:
    """جلسه ۴۶ (رأی مالک «قلب به تمومِ اندام‌ها، کم‌نقطهٔ مرده»): علائمِ حیاتیِ سبک —
    استرس + عصب‌کشی — را مستقیم از ستونِ فقراتِ اصلی beat می‌زند، تا حتی اگر دیمنِ
    کورتکس بخوابد، مانیتور کور نشود و نقطهٔ مردهٔ کورتکس تشخیص داده شود. $0، fail-soft."""
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    out = {}
    try:
        _syspath(str(_HERE / "cortex"))
        import stress
        out["stress"] = stress.persist().get("level")
    except Exception:  # noqa: BLE001
        pass
    try:
        import innervation
        a = innervation.persist()
        out["coverage"] = a.get("coverage_pct")
        out["dead"] = a.get("dead_spots")
    except Exception:  # noqa: BLE001
        pass
    return out or None


_HEARTBEAT_STATE = {"last_epoch": -1}


def heartbeat_summary_beat(channel=None, beat: int = 0) -> dict | None:
    """رأی مالک «هر ۵ دقیقه heartbeat summary بده». هر N beat یک رویدادِ
    system.heartbeat با شمارِ کارها emit می‌کند (خوراکِ داشبوردِ اتوماسیون).
    فقط رویداد — بی‌صدا (نوتیفِ تلگرام جداست). kill-switch اول."""
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    every_n = int(os.environ.get("CHRONO_HEARTBEAT_EVERY_N_BEATS", "300"))  # ~۵min با ۱s beat
    if beat <= 0 or every_n <= 0:
        return None
    epoch = beat // every_n
    if not _epoch_window("heartbeat", epoch, _HEARTBEAT_STATE, min_epoch=0):
        return None
    _HEARTBEAT_STATE["last_epoch"] = epoch
    try:
        _syspath(str(_HERE))
        import events
        s = events.summary_window(5)
        pending = None
        if channel is not None and hasattr(channel, "_count_pending"):
            try:
                pending = channel._count_pending()
            except Exception:  # noqa: BLE001
                pending = None
        summ = (f"{s['completed']} تمام، {s.get('waiting', pending or 0)} منتظر، "
                f"{s['failed']} خطا، {s['blocked']} گیر")
        events.emit("system.heartbeat", "organism", summary=summ,
                    approval_state="required" if pending else "none")
        return {"summary": summ, "pending": pending}
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: heartbeat_summary خطا: {type(e).__name__}: {e}"])
        return None


_DISCOVERY_STATE = {"last_epoch": -1}


# ════════════════════════════════════════════════════════════════════════════════
# Z · Ziman limb — ZimanLeg seam (propose-only، D4، organ=ZIMAN)
# ════════════════════════════════════════════════════════════════════════════════

_ZIMAN_STATE: dict = {"leg": None, "state_path": None}
_ZIMAN_BEAT_EVERY_N = 60   # یک بار در هر ۶۰ beat (~۱h با tick=60s)
# برندینگِ خودکار: کادنسِ جدا و کندتر (پیش‌فرض ~روزی یک‌بار با tick=60s) تا نه هزینه/
# لتنسیِ LLM روی هر بیت بیاید و نه کارتِ تلگرام مالک را پُر کند. پشتِ OCTOPUS_ZIMAN_BRANDING.
_ZIMAN_BRANDING_EVERY_N = 1440   # 1440 beat ≈ ۲۴h
_ZIMAN_OCCASIONS = ("هدیه", "سالگرد", "تولد", "نامزدی", "روز مادر", "یلدا", "قدردانی")


def make_ziman_leg(organ_table: dict | None = None) -> "ZimanLeg | None":
    """ساختِ ZimanLeg پشتِ OCTOPUS_WIRE_ZIMAN. fail-soft: None اگر flag خاموش یا import نشد.

    organ_table قابلِ تزریق (تست بدونِ budgets.yaml). None = opslib.organ_table().
    پا حداکثر یک‌بار در هر اجرا ساخته می‌شود (singleton slab، ذخیره در _ZIMAN_STATE)."""
    if not flag("OCTOPUS_WIRE_ZIMAN"):
        return None
    if _ZIMAN_STATE["leg"] is not None:
        return _ZIMAN_STATE["leg"]
    try:
        _syspath(str(_HERE / "legs"))
        _syspath(str(_HERE / "budget"))
        from ziman_leg import ZimanLeg   # noqa: WPS433 — lazy import (not at module level)
        table = organ_table
        if table is None:
            try:
                table = opslib.organ_table()
            except Exception:  # noqa: BLE001
                table = {"ZIMAN": {"floor": 1}}
        leg = ZimanLeg(organ_table=table)
        _ZIMAN_STATE["leg"] = leg
        _ZIMAN_STATE["state_path"] = opslib.STATE_DIR / "ORGANISM-STATE.ziman"
        return leg
    except Exception as e:  # noqa: BLE001 — additive: pا نباید organism را بکشد
        opslib.alert([f"wiring: ZimanLeg ساخت نشد: {type(e).__name__}: {e}"])
        return None


def ziman_beat(leg=None, beat: int = 0, doctor=None) -> dict | None:
    """یک tick سبک از ZimanLeg پشتِ OCTOPUS_WIRE_ZIMAN.

    قرارداد:
    * propose-only: هیچ publish/send/spend/DM داخل این تابع نیست.
    * هر ZIMAN_BEAT_EVERY_N beat وضعیت را به ORGANISM-STATE.ziman می‌نویسد.
    * اگر leg نیاید، make_ziman_leg() را یک‌بار امتحان می‌کند.
    * خروجی dict با کلیدهای ثابت (برای test_ziman_wiring) یا None.
    * kill-switch اول.
    """
    if not flag("OCTOPUS_WIRE_ZIMAN"):
        return None
    if leg_paused("ziman"):
        return None   # مکثِ تک‌پا از مرکزِ تلگرام (runtime)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    every_n = int(os.environ.get("CHRONO_ZIMAN_EVERY_N_BEATS", str(_ZIMAN_BEAT_EVERY_N)))
    if not _epoch_fire("ziman", beat, every_n):
        return None
    _leg = leg
    if _leg is None:
        _leg = make_ziman_leg()
    if _leg is None:
        return None
    try:
        snap = _leg.status_snapshot()
        digest = _leg.telegram_digest()
        # Sol-T5 تصحیحِ صداقتی (2026-07-20): کامنتِ قبلی ادعا می‌کرد ziman_biology «هرگز در repo/گیت
        # وجود نداشت» — این روی HEADِ فعلی **غلط** است: `_ops/legs/ziman_biology.py` موجود است
        # (۷۵۱۲ بایت)، `observability/leg_monitor.py` importش می‌کند، `test_ziman_biology.py` هست، و
        # `ziman_leg.accept_biology_status` تعریف شده. واقعیت: ماژول موجود ولی **ORPHAN** است —
        # این beat عمداً `biology=None` نگه می‌دارد. سیم‌کشیِ واقعی owner-gated است (رأیِ Sol-T6:
        # «فقط اگر رفتار/اقتدارش فهمیده شد») تا اقتدار/side-effectِ biology روشن نشده. رفتار دست‌نخورده.
        biology = None
        # ── برندینگِ خودکار (پشتِ OCTOPUS_ZIMAN_BRANDING، پیش‌فرض خاموش) ──
        # روزی یک‌بار یک draftِ برند از مغزِ مشترک (model_router محلی‌اول → Fugu) می‌سازد
        # و به‌صورتِ proposalِ leg emit می‌کند؛ route_leg_proposals (در organism.py) آن را
        # خودکار به کارتِ advisoryِ owner-visible تبدیل می‌کند. propose-only، fail-soft،
        # هیچ publish/spend اینجا. خاموش/خطا → خروجی byte-identical با امروز.
        branding = None
        if flag("OCTOPUS_ZIMAN_BRANDING"):
            b_every = int(os.environ.get("CHRONO_ZIMAN_BRANDING_EVERY_N_BEATS",
                                         str(_ZIMAN_BRANDING_EVERY_N)))
            if _epoch_fire("ziman_branding", beat, b_every):
                try:
                    fams = list(_leg.product_families().keys())
                    fam = fams[(beat // max(1, b_every)) % len(fams)] if fams else "C3"
                    occ = _ZIMAN_OCCASIONS[(beat // max(1, b_every)) % len(_ZIMAN_OCCASIONS)]
                    prop = _leg.draft_content(kind="caption", product_family=fam,
                                              occasion=occ, use_llm=True)
                    pl = getattr(prop, "payload", {}) or {}
                    branding = {"emitted": hasattr(prop, "payload"),
                                "body_source": pl.get("body_source"),
                                "family": pl.get("product_family"), "occasion": occ}
                except Exception as _be:  # noqa: BLE001 — برندینگ نباید بیت را بکشد
                    opslib.alert([f"ziman branding beat خطا: {type(_be).__name__}: {_be}"])
        result = {
            "leg_id": snap.get("leg_id", "ziman-gallery"),
            "organ": snap.get("organ", "ZIMAN"),
            "money_link": snap.get("money_link", "?"),
            "capacity_ceiling": snap.get("capacity_ceiling_per_week"),
            "inventory_hint": snap.get("inventory_hint"),
            "drafts_count": snap.get("drafts_count", 0),
            "propose_only": True,
            "outward_execution": False,
            "beat": beat,
            "digest": digest,
            "biology": biology,
            "branding": branding,   # additive: None وقتی خاموش/غیرِفایر
        }
        # ORGANISM-STATE.ziman — وضعیت پایدار برای organism و داشبورد
        sp = _ZIMAN_STATE.get("state_path")
        if sp is None:
            sp = opslib.STATE_DIR / "ORGANISM-STATE.ziman"
            _ZIMAN_STATE["state_path"] = sp
        try:
            sp.parent.mkdir(parents=True, exist_ok=True)
            tmp = sp.with_suffix(".ziman.tmp")
            import json as _json
            tmp.write_text(_json.dumps(
                {**result, "updated_at": opslib.now_iso()},
                ensure_ascii=False, indent=2
            ), "utf-8")
            os.replace(tmp, sp)
        except (OSError, TypeError, ValueError):
            pass
        return result
    except Exception as e:  # noqa: BLE001 — §۴: Ziman نباید tick را بکشد
        opslib.alert([f"wiring: ziman_beat خطا: {type(e).__name__}: {e}"])
        return None


def discovery_nudge_beat(channel=None, beat: int = 0) -> dict | None:
    """رأی مالک «کشف و نوتیف به من نداره»: هر N beat اگر سیستم چیزِ تازه‌ای یاد گرفت/کشف
    کرد، یک نوتیفِ ملایمِ اطلاعی می‌فرستد («یه چیزِ جدید یاد گرفتم»). پشتِ
    OCTOPUS_WIRE_NEEDS_NUDGE (همان پرچمِ نوتیف). ضدِ اسپم با epoch. kill-switch اول."""
    if not flag("OCTOPUS_WIRE_NEEDS_NUDGE"):
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    every_n = int(os.environ.get("CHRONO_DISCOVERY_NUDGE_EVERY_N_BEATS", "480"))  # ~۸h
    if beat <= 0 or every_n <= 0:
        return None
    epoch = beat // every_n
    if not _epoch_window("discovery", epoch, _DISCOVERY_STATE):
        return None
    _DISCOVERY_STATE["last_epoch"] = epoch
    try:
        _syspath(str(_HERE / "cortex"))
        import discoveries
        # ۲۰۲۶-۰۷-۲۶ پشتِ فلگ: «چند تا از آخرین باری که خبر دادم» به‌جای «چند تا از
        # آخرین باری که مالک کلیک کرد». نشانگرِ SEEN فقط با کلیک جلو می‌رود، پس
        # بدونِ کلیک همان انبار هر بار دوباره اعلام می‌شد. flag خاموش = رفتارِ امروز.
        _delta = str(os.environ.get("OCTOPUS_DISCOVERY_NUDGE_DELTA", "")).strip().lower() \
            in ("1", "true", "yes", "on")
        n = discoveries.unseen_since_nudge() if _delta else discoveries.unseen_count()
        if n <= 0:
            return {"n": 0, "sent": False, "delta_mode": _delta}
        sent = False
        if channel is not None and getattr(channel, "wired", False):
            preview = "\n".join(discoveries.lines(3))
            kb = {"inline_keyboard": [[
                {"text": "📚 ببین چی یاد گرفتم", "callback_data": "menu:learned"}]]}
            sent = bool(_send_stream(channel,
                f"🔍 <b>{n} چیزِ جدید یاد گرفتم!</b>\n──────────\n{preview}", kb,
                    stream="discovery"))
        # علامت فقط روی ارسالِ موفق — نوتیفِ نرسیده نباید دفن شود.
        if sent and _delta:
            import time as _time
            # ERRORHUNT 2026-08-16: mark_nudged(high_water) اجباری است؛
            # فراخوانِ بی‌آرگومان TypeError می‌داد و در governor-alerts انبار می‌شد.
            discoveries.mark_nudged(_time.time())
        return {"n": n, "sent": sent, "delta_mode": _delta}
    except Exception as e:  # noqa: BLE001 — نوتیف نباید tick را بکشد
        opslib.alert([f"wiring: discovery_nudge خطا: {type(e).__name__}: {e}"])
        return None


# ════════════════════════════════════════════════════════════════════════════════
# Task 3 (2026-07-24) · دیالوگِ owner↔organ — Doctor / Brains / Hearts
# efferentِ سه organ روی همان کانالِ in-process (_chan)؛ هیچ transport/pollerِ نو.
# کادنس زمان-محور است نه beat-محور — عمداً: INC فعلیِ frozen-beat (pacemaker مرده،
# beat روی 9890 یخ‌زده) هر کادنسِ beat-epochی را هم یخ می‌زند؛ لایهٔ دیالوگ باید
# دقیقاً در همین حالت هم به مالک خبر بدهد. throttle با hash + interval (ضدِ اسپم،
# همان دکترینِ needs_nudge). همه fail-soft، $0، پشتِ flag (پیش‌فرض خاموش).
# ════════════════════════════════════════════════════════════════════════════════

def _organ_dialogue_mod():
    if str(_HERE) not in sys.path:
        _syspath(str(_HERE))
    import organ_dialogue as _od
    return _od


def _dialogue_gate(state_name: str, new_hash: str, min_interval_s: float,
                   force: bool = False) -> bool:
    """true = بفرست. state: state/<state_name>.json {last_hash,last_ts}.
    ارسال وقتی: (hash عوض شده و interval گذشته) یا force (با کفِ ضدِ flap ِ 300s)."""
    import json as _json
    import time as _time
    p = opslib.STATE_DIR / state_name
    try:
        st = _json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        st = {}
    now = _time.time()
    age = now - float(st.get("last_ts") or 0)
    changed = st.get("last_hash") != new_hash
    # ۲۰۲۶-۰۷-۲۸ — گاردِ تلاشِ مکرر. تا امروز `last_ts` فقط بعد از ارسالِ **موفق**
    # جلو می‌رفت، پس هر ارسالی که نرسید (سیاستِ سطح آن را نگه داشت، شبکه خطا داد،
    # ساعتِ سکوت) یعنی حالت کهنه می‌ماند و همان کارت **هر تیک** دوباره ساخته و
    # تلاش می‌شد. اندازه‌گیریِ زنده: سه کارتِ قلب با فاصلهٔ ۴۵ ثانیه، دوتایشان
    # با **همان ضربان**؛ و `heart-card-nudge.json` از ۰۶:۴۰ یخ‌زده.
    # همان درسِ needs_nudge، سه ماژول آن‌طرف‌تر: مُهر باید روی «آخرین چیزی که
    # **تلاش** کردم» بنشیند، نه «آخرین چیزی که رساندم».
    same_attempt = st.get("last_attempt_hash") == new_hash
    attempt_age = now - float(st.get("last_attempt_ts") or 0)
    if same_attempt and attempt_age < min(float(min_interval_s or 0), 3600.0):
        return False
    if force:
        return age > 300
    return changed and age > min_interval_s


def _dialogue_mark(state_name: str, new_hash: str, *, sent: bool = True) -> None:
    """مُهرِ دیالوگ. `sent=False` یعنی تلاش شد ولی نرسید.

    `last_hash`/`last_ts` فقط با ارسالِ واقعی جلو می‌روند — پس کارتی که هرگز
    نرسید بعداً دوباره تلاش می‌شود و گم نمی‌شود. ولی `last_attempt_*` همیشه
    ثبت می‌شود تا تلاشِ مکرر کران‌دار بماند.
    """
    import json as _json
    import time as _time
    p = opslib.STATE_DIR / state_name
    now = _time.time()
    try:
        old = _json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        old = {}
    try:
        with opslib.LockedJson(p) as lj:
            lj.write({"last_hash": new_hash if sent else old.get("last_hash"),
                      "last_ts": now if sent else float(old.get("last_ts") or 0),
                      "last_attempt_hash": new_hash, "last_attempt_ts": now,
                      "ts": opslib.now_iso()})
    except Exception:  # noqa: BLE001
        pass


def doctor_digest_beat(channel=None, beat: int = 0) -> dict | None:
    """3a-efferent: دکتر «حرف می‌زند» — تشخیصِ self-knowledge + RFCهای باز به مالک.
    پشتِ OCTOPUS_WIRE_DOCTOR_DIGEST (پیش‌فرض خاموش). kill-switch اول."""
    if not flag("OCTOPUS_WIRE_DOCTOR_DIGEST"):
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    try:
        _od = _organ_dialogue_mod()
        d = _od.doctor_digest()
        min_s = float(os.environ.get("CHRONO_DOCTOR_DIGEST_MIN_S", "21600"))
        if not _dialogue_gate("doctor/digest-nudge.json", d["hash"], min_s):
            return {"sent": False, "hash": d["hash"], "beat": beat}
        sent = False
        if channel is not None and getattr(channel, "wired", False):
            kb = {"inline_keyboard": [[
                {"text": "🩺 تبِ دکتر", "callback_data": "menu:doctor"}]]}
            sent = bool(_send_stream(channel, d["text"], kb,
                stream="doctor"))
            _dialogue_mark("doctor/digest-nudge.json", d["hash"], sent=sent)
        return {"sent": sent, "rfc_open": d.get("rfc_open"), "beat": beat}
    except Exception as e:  # noqa: BLE001 — دیالوگ نباید tick را بکشد
        opslib.alert([f"wiring: doctor_digest_beat خطا: {type(e).__name__}: {e}"])
        return None


_BRAIN_DIGEST_STATE = {"last_stress": ""}


def brain_digest_beat(channel=None, beat: int = 0) -> dict | None:
    """3b-efferent: مغز «حرف می‌زند» — از state-fileهای cortex/debate (پلِ درستِ
    out-of-process؛ cortex هرگز خودش bot/poller نمی‌سازد → صفر 409).
    ارسال روی تغییرِ high-leverage (hash) یا فلیپِ تنش به 🔴 (فوری، ضدِ flap).
    پشتِ OCTOPUS_WIRE_BRAIN_DIGEST (پیش‌فرض خاموش)."""
    if not flag("OCTOPUS_WIRE_BRAIN_DIGEST"):
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    try:
        _od = _organ_dialogue_mod()
        d = _od.brain_digest()
        prev = _BRAIN_DIGEST_STATE.get("last_stress", "")
        cur = str(d.get("stress_level") or "")
        _BRAIN_DIGEST_STATE["last_stress"] = cur
        red_flip = ("🔴" in cur) and ("🔴" not in prev) and prev != ""
        min_s = float(os.environ.get("CHRONO_BRAIN_DIGEST_MIN_S", "21600"))
        if not _dialogue_gate("cortex/brain-digest-nudge.json", d["hash"], min_s,
                              force=red_flip):
            return {"sent": False, "hash": d["hash"], "beat": beat}
        sent = False
        if channel is not None and getattr(channel, "wired", False):
            # ۲۰۲۶-۰۸-۰۶ — تلاشِ اولِ فیکس («📮 صف تأیید» → callback_data="mn:ap")
            # خودش کارتِ مرده بود: این کارت از کانالِ ارگانیسم می‌رود (چون این‌جا
            # approval_channel.TelegramApprovalChannel روی TELEGRAM_BOT_TOKEN /
            # @Robo2725_bot است — همان تلهٔ دو-باتیِ کامنتِ approval_channel.py:
            # 996-1014)، و روترِ همان بات (`dispatch_callback`) هیچ شاخهٔ
            # `parts[0] == "mn"` ندارد → کلیک همیشه «نادیده» برمی‌گرداند، دقیقاً
            # همان چیزی که مالک گزارش داد. verb ِ "mn:ap" فقط در
            # telegram_center/center.py (باتِ دیگر، @intergrade2725_Bot) هندلر
            # دارد. راستیِ این ادعا: test_tg_callback_emitter_parity.py.
            # چون یک callback_data نمی‌تواند از این بات به آن بات برسد، فقط
            # دکمه‌ای که *در همین بات* واقعاً کار می‌کند می‌ماند؛ راهنماییِ
            # «کدام بات برای رأی» به متنِ کارت منتقل شد (organ_dialogue.py:
            # debate_survivor_card).
            #
            # ۲۰۲۶-۰۸-۰۶ (ادامه — خواستهٔ صریحِ مالک «کار نمی‌کنه»): callback_data
            # بینِ دو بات نمی‌رسد ولی دکمهٔ `url` چرا — تلگرام آن را در همین بات
            # می‌سازد و با تپ، چتِ باتِ دیگر را با متنِ کاملِ `/start ap` باز
            # می‌کند (deep-link رسمیِ Bot API). `center._start_cmd` این payload
            # را می‌شناسد و مستقیم به صفِ رأی می‌پرد — یک تپ، نه تایپِ دستی.
            kb = {"inline_keyboard": [
                [{"text": "📮 برو صفِ رأی (بات دیگر)",
                  "url": "https://t.me/intergrade2725_Bot?start=ap"}],
                [{"text": "🧠 تبِ مغز", "callback_data": "menu:brain"}]]}
            head = "🚨 تنشِ مغز 🔴 شد!\n" if red_flip else ""
            sent = bool(_send_stream(channel, head + d["text"], kb,
                stream="brain"))
            _dialogue_mark("cortex/brain-digest-nudge.json", d["hash"], sent=sent)
        return {"sent": sent, "red_flip": red_flip,
                "debate_pending": d.get("debate_pending"), "beat": beat}
    except Exception as e:  # noqa: BLE001 — دیالوگ نباید tick را بکشد
        opslib.alert([f"wiring: brain_digest_beat خطا: {type(e).__name__}: {e}"])
        return None


def heart_card_beat(channel=None, beat: int = 0) -> dict | None:
    """3c-efferent: قلب «حرف می‌زند» — کارتِ cardiac (mode/period/velocity/σ/بودجه/
    setpoint) + alertهای vital: frozen-beat (stall)، بودجهٔ ته‌کشیده، فلیپِ 🔴،
    protective. پشتِ OCTOPUS_WIRE_HEART_CARD **و** wire_pulse (هر دو لازم).
    alertها force-send با کفِ ضدِ flap؛ digestِ عادی interval-دار."""
    if not (flag("OCTOPUS_WIRE_HEART_CARD") and flag("OCTOPUS_WIRE_PULSE")):
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    try:
        _od = _organ_dialogue_mod()
        d = _od.heart_digest(beat=beat)
        force = bool(d.get("stall_new")) or bool(d.get("alerts")) and False
        # stall تازه همیشه force؛ سایر alertها از راهِ تغییرِ hash خودشان می‌روند
        min_s = float(os.environ.get("CHRONO_HEART_CARD_MIN_S", "21600"))
        if not _dialogue_gate("pulse/heart-card-nudge.json", d["hash"], min_s,
                              force=force):
            return {"sent": False, "stalled": d.get("stalled"), "beat": beat}
        sent = False
        if channel is not None and getattr(channel, "wired", False):
            kb = {"inline_keyboard": [[
                {"text": "📊 وضعیت", "callback_data": "menu:overview"}]]}
            sent = bool(_send_stream(channel, d["text"], kb,
                stream="heart"))
            _dialogue_mark("pulse/heart-card-nudge.json", d["hash"], sent=sent)
        return {"sent": sent, "stalled": d.get("stalled"),
                "alerts": len(d.get("alerts") or []), "beat": beat}
    except Exception as e:  # noqa: BLE001 — دیالوگ نباید tick را بکشد
        opslib.alert([f"wiring: heart_card_beat خطا: {type(e).__name__}: {e}"])
        return None


def leg_rooms_beat(beat: int = 0, channel=None, legs: dict | None = None,
                   now: float | None = None) -> dict | None:
    """به پاها در اتاقِ خودشان صدا بده — فقط وقتی وضعیتشان عوض شده.

    ۲۰۲۶-۰۷-۲۸ (رأیِ مالک «گروه و پاها همه‌رو اتصالات رو کدنویسی کن»): ۷ تاپیکِ
    گروه از روزِ ساختشان یک پیام هم نگرفته بودند. علتش نبودِ نگاشت نبود —
    `surface_policy.LEG_TOPIC` درست بود — بلکه این بود که در کلِ این فایل فقط
    **پنج** جریان تولید می‌شد (needs, discovery, doctor, brain, heart) و
    هیچ‌کدام پا نبود. این beat آن حفرهٔ تولید را پر می‌کند.

    محتوا اختراع نمی‌شود: همان سلولِ `business_legs` که از قبل ساخته می‌شد و
    فقط در کارتِ جمعیِ `/organs` دیده می‌شد. مسیرِ ارسال هم همان `_send_stream`
    است، پس `surface_policy` تصمیمِ اتاق را می‌گیرد نه این تابع.

    `due`/`mark` عمداً جدایند: اگر ارسال شکست بخورد هیچ‌چیز mark نمی‌شود و دورِ
    بعد دوباره تلاش می‌شود — علامت‌زدنِ **قصد** به‌جای **اثر** همان اشتباهی است
    که این هفته سه بار پیدا شد.
    """
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None                      # kill-switch مقدم
    try:
        _syspath(str(_HERE / "legs"))
        import leg_room_report as _lrr   # noqa: WPS433 — lazy، خودش فلگ را چک می‌کند
        if not _lrr.enabled():
            return {"sent": 0, "flag": "off", "beat": beat}
        if legs is None:
            got = business_legs_beat(beat, write=False) or {}
            legs = got.get("business_legs") or {}
        pending = _lrr.due(legs, now=now)
        if not pending:
            return {"sent": 0, "due": 0, "beat": beat}
        if channel is None or not getattr(channel, "wired", False):
            # کانال نیست: هیچ mark نمی‌کنیم، پس وقتی بیاید همه‌شان می‌رسند.
            return {"sent": 0, "due": len(pending), "no_channel": True,
                    "beat": beat}
        done = []
        for leg, text, h in pending:
            if bool(_send_stream(channel, text, None, stream=leg)):
                done.append((leg, h))
        _lrr.mark(done, now=now)
        return {"sent": len(done), "due": len(pending),
                "legs": [l for l, _ in done], "beat": beat}
    except Exception as e:  # noqa: BLE001 — اتاقِ پاها نباید tick را بکشد
        opslib.alert([f"wiring: leg_rooms_beat خطا: {type(e).__name__}: {e}"])
        return None
