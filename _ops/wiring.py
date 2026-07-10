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


# ════════════════════════════════════════════════════════════════════════════════
# W3 · boot profile — یک سوئیچ به‌جای ۶ flagِ پراکنده (P-W3)
# ════════════════════════════════════════════════════════════════════════════════

# paper-full = همهٔ wiringِ امنِ propose-only روشن (neural + consolidation + school +
# sensory + doctor + evolution + box + unified + legs + ideas + germline + checkpoint +
# spectral). پول/live جدا و همچنان capability-gated (profile آن را باز نمی‌کند).
PAPER_FULL_FLAGS = (
    "OCTOPUS_WIRE_DOCTOR", "OCTOPUS_WIRE_NEURAL", "OCTOPUS_WIRE_UNIFIED",
    "OCTOPUS_WIRE_LEAD", "OCTOPUS_WIRE_SCHOOL", "OCTOPUS_WIRE_CONSOLIDATION",
    "OCTOPUS_WIRE_EVOLUTION", "OCTOPUS_WIRE_BOX", "OCTOPUS_WIRE_LEAD_TICK",
    "OCTOPUS_WIRE_IDEAS",
    "OCTOPUS_WIRE_SPECTRAL",   # P-spectral: complementary spectral bottleneck
    "OCTOPUS_WIRE_BCM",        # P3 blueprint: BCM forgetting — default-applied
                               # 2026-07-10 (قابل‌وتو، AGENT_QUESTIONS)؛ فقط ایندکس retrieval
    "OCTOPUS_WIRE_SPARSE",     # P4 blueprint: sparse input filter — verdict آری
                               # «برو» 2026-07-10؛ فقط ورودیِ acquisition را باریک می‌کند
    "OCTOPUS_WIRE_FISHER",     # P6 blueprint: Fisher advisory — verdict آری «برو»
                               # 2026-07-10؛ فقط fisher-latest.json، هیچ تغییرِ scoring (I4/I6)
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
        sys.path.insert(0, str(_HERE / "doctor"))
        from doctor import Doctor
        return Doctor(state_dir=state_dir, db=db, approval_channel=channel)
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
        sys.path.insert(0, str(_HERE / "budget"))
        from approval_channel import TelegramApprovalChannel
        # T-8: gate/ledger injection — T-2 settle فقط با این دو فعال است.
        _gate = _ledger = None
        try:
            import chrono as _chrono_mod
            _gate = _chrono_mod.EffectorGate(db=None)
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


def make_unified_bus(ledger=None, db=None):
    """ساختِ UnifiedBus. پشتِ OCTOPUS_WIRE_UNIFIED."""
    if not flag("OCTOPUS_WIRE_UNIFIED"):
        return None
    try:
        sys.path.insert(0, str(_HERE))
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
        sys.path.insert(0, str(_HERE / "legs"))
        sys.path.insert(0, str(_HERE / "budget"))
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
        sys.path.insert(0, str(_HERE))
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
# ════════════════════════════════════════════════════════════════════════════════

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
        return {"leg_id": leg_id, "hlc": list(hlc),
                "events_this_beat": handle.events_this_beat,
                "last_beat_seen": handle.last_beat_seen,
                "money_link": st.get("money_link"),
                "proposals_emitted": st.get("proposals_emitted", 0),
                "propose_only": True}
    except Exception as e:  # noqa: BLE001 — §۴: leg نباید tick را بکشد
        opslib.alert([f"wiring: leg_beat خطا: {type(e).__name__}: {e}"])
        return None


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
        "wire_ideas": flag("OCTOPUS_WIRE_IDEAS"),        # P-I: idea-graph engine
        "wire_spectral": flag("OCTOPUS_WIRE_SPECTRAL"),  # P-spectral: spectral bottleneck
        "wire_rhythm": flag("OCTOPUS_WIRE_NEURAL"),      # rhythm (shares neural flag)
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
        "profile": resolve_profile(),                    # P-W3: boot profile
        "doctor_every_n": int(os.environ.get("CHRONO_DOCTOR_EVERY_N_BEATS", "1440")),
        "consolidation_every_n": int(os.environ.get("CHRONO_CONSOLIDATION_EVERY_N_BEATS", "720")),
        "afferent_every_n": int(os.environ.get("CHRONO_AFFERENT_EVERY_N_BEATS", "1440")),
    }


# ════════════════════════════════════════════════════════════════════════════════
# W · neural wiring — ۸ ماژول + school_bridge به tick وصل، پشتِ flag
# ════════════════════════════════════════════════════════════════════════════════

def make_rhythm():
    """ساختِ Rhythm (mode_color GREEN/AMBER/RED). پشتِ OCTOPUS_WIRE_NEURAL.
    اگر خاموش → None. advisory فقط."""
    try:
        sys.path.insert(0, str(_HERE / "chrono_rhythm"))
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
        sys.path.insert(0, str(_HERE / "neural"))
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
        sys.path.insert(0, str(_HERE / "neural"))
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
    if beat <= 0 or (every_n > 0 and beat % every_n != 0):
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


def make_neural_stack():
    """ساختِ NeuralDriver + Hebbian + Consolidation.
    پشتِ OCTOPUS_WIRE_NEURAL. اگر خاموش → None.
    C9: hooks/nociceptor/reflex حذف شدند (مرده در stack — pain/reflex از NeuralDriver داخلی وصل است)."""
    if not flag("OCTOPUS_WIRE_NEURAL"):
        return None
    try:
        sys.path.insert(0, str(_HERE / "neural"))
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
        result = driver.evaluate(
            beat=beat,
            rhythm=inputs.get("rhythm"),
            sensory=inputs.get("sensory"),
            spectral=inputs.get("spectral"),
            budget=inputs.get("budget"))
        # hebbian observe
        signals = []
        if inputs.get("rhythm", {}).get("mode_color") == "GREEN":
            signals.append("green_mode")
        if inputs.get("spectral", {}).get("sigma", 0) < 0.8:
            signals.append("stable")
        if signals:
            neural_stack["hebbian"].observe(signals)
        # consolidation every 10 beats
        if beat > 0 and beat % 10 == 0:
            sources = {}
            if inputs.get("acquisition"):
                sources["acquisition"] = inputs["acquisition"]
            if sources:
                neural_stack["consolidation"].run(sources)
        return result
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: neural_beat خطا: {e}"])
        return None


# ════════════════════════════════════════════════════════════════════════════════
# S · protective-override — غیرقابل‌سرکوب توسط orchestrator
# ════════════════════════════════════════════════════════════════════════════════

def protective_override(neural_result: dict | None) -> dict:
    """بررسیِ protective signals. اگر خطر → override غیرقابل‌سرکوب.
    خروجی: {override: bool, action: str, reason: str}.
    این تابع Structural است — orchestrator نمی‌تواند نادیده بگیرد."""
    if neural_result is None:
        return {"override": False, "action": "none", "reason": "no neural data"}
    pain = neural_result.get("pain", {}).get("level", 0)
    reflexes = neural_result.get("reflexes", [])
    triggered = [r for r in reflexes if r.get("triggered")]

    # pain > 0.7 → protective redirect (غیرقابل‌سرکوب)
    if pain > 0.7:
        return {"override": True, "action": "protective_halt",
                "reason": f"pain={pain:.2f}>0.7 — non-essential paused",
                "suppressible": False}   # ← کلید: غیرقابل‌سرکوب

    # reflex triggered → throttle
    critical = [r for r in triggered if r.get("severity") == "critical"]
    if critical:
        return {"override": True, "action": "throttle",
                "reason": f"critical reflex: {critical[0].get('name')}",
                "suppressible": False}

    # high reflex → warning (قابل‌سرکوب ولی logged)
    high = [r for r in triggered if r.get("severity") == "high"]
    if high:
        return {"override": False, "action": "warn",
                "reason": f"high reflex: {high[0].get('name')}",
                "suppressible": True}

    return {"override": False, "action": "none", "reason": "all clear"}


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
        vec = encode_rfc(f"archive-{result.cycle}", f"{n_approved} approved", "medium", dim=dim)
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
        # retrieval: nearest از cycles قبلی
        nn = latent_space.nearest(cycle_key, top_k=5)
        result.similar_keys = [k for k, _ in nn if k != cycle_key]
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
# M · live-loop wiring — canonical_consolidation در حلقهٔ زنده (P-M2)
# ════════════════════════════════════════════════════════════════════════════════

def make_school_bridge(state_path=None):
    """ساختِ SchoolBridge (منبعِ awareness برای consolidation). پشتِ flag لازم نیست —
    فقط اگر consolidation نیازش داشته باشد ساخته می‌شود. همیشه یک instance برمی‌گرداند
    اگر import موفق باشد، وگرنه None (fail-soft). $0 آفلاین، stdlib-only."""
    try:
        sys.path.insert(0, str(_HERE / "afferent"))
        from school_bridge import SchoolBridge
        kw = {}
        if state_path is not None:
            kw["state_path"] = state_path
        return SchoolBridge(**kw)
    except Exception as e:  # noqa: BLE001 — SchoolBridge اختیاریِ additive
        opslib.alert([f"wiring: SchoolBridge ساخت نشد: {e}"])
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
        sys.path.insert(0, str(_HERE / "afferent"))
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
    if not flag("OCTOPUS_WIRE_SCHOOL"):
        return None   # flag خاموش = no-op (no regression)
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None   # kill-switch
    every_n = int(os.environ.get("CHRONO_AFFERENT_EVERY_N_BEATS", "1440"))  # روزانه
    if beat <= 0 or (every_n > 0 and beat % every_n != 0):
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
            school_report = school_bridge.learn_from(events, persist=False)
        return {"n_observations": len(observations),
                "school_report": school_report,
                "sensory_status": sensory_bus.status(),
                "alarm": sensory_bus.alarms[-1] if sensory_bus.alarms else None}
    except Exception as e:  # noqa: BLE001 — §۴: خطای خاموش ممنون، ولی afferent نباید tick را بکشد
        opslib.alert([f"wiring: afferent_beat خطا: {type(e).__name__}: {e}"])
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
    if beat <= 0 or (every_n > 0 and beat % every_n != 0):
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
        return idea_graph.analyze()
    except Exception as e:  # noqa: BLE001 — §۴: خطای خاموش ممنون، ولی idea نباید tick را بکشد
        opslib.alert([f"wiring: idea_beat خطا: {type(e).__name__}: {e}"])
        return None
