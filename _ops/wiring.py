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


# ─── W-1 · germline_lag → ORGANISM-STATE (همیشه روشن، read-only) ───────────────
def enrich_state_with_germline(state: dict) -> dict:
    """germline_lag را از germline.py به state اضافه کن.
    اگر germline.py نباشد → fallback به opslib.germline_lag_hours (همان قبل).
    همیشه روشن چون read-only است و ریسک صفر دارد."""
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


def make_telegram_channel():
    """ساختِ TelegramApprovalChannel. auto-on اگر توکن باشد."""
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        return None
    try:
        sys.path.insert(0, str(_HERE / "budget"))
        from approval_channel import TelegramApprovalChannel
        return TelegramApprovalChannel()   # no-op امن اگر توکن نباشد
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
            leg_id="lead-naghshi", organ="LEAD_PAINTING",
            read_allowlist=("03 - Projects/Lead-نقاشی/PROJECT.md",),
            tools=("draft_quote",), budget_aud=5.0)
        return LeadLeg(packet, organ_table=opslib.organ_table())
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: LeadLeg ساخت نشد: {e}"])
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
    if beat % every_n != 0:
        return None
    try:
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
        "doctor_every_n": int(os.environ.get("CHRONO_DOCTOR_EVERY_N_BEATS", "1440")),
    }


# ════════════════════════════════════════════════════════════════════════════════
# W · neural wiring — ۸ ماژول + school_bridge به tick وصل، پشتِ flag
# ════════════════════════════════════════════════════════════════════════════════

def make_neural_stack():
    """ساختِ NeuralDriver + Hebbian + Consolidation + HookBus.
    پشتِ OCTOPUS_WIRE_NEURAL. اگر خاموش → None."""
    if not flag("OCTOPUS_WIRE_NEURAL"):
        return None
    try:
        sys.path.insert(0, str(_HERE / "neural"))
        from neural_driver import NeuralDriver
        from hebbian import HebbianAssociator
        from consolidation import ConsolidationCycle
        from hooks import HookBus
        from nociceptor import Nociceptor
        from reflex import ReflexArc
        return {
            "driver": NeuralDriver(),
            "hebbian": HebbianAssociator(),
            "consolidation": ConsolidationCycle(),
            "hooks": HookBus(),
            "nociceptor": Nociceptor(),
            "reflex": ReflexArc(),
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

def canonical_consolidation(neural_stack, school_bridge=None,
                            acquisition_data=None,
                            doctor_archive=None) -> dict | None:
    """یک مسیرِ canonical consolidation. فقط verified.
    دو مسیرِ موازی نماند — همه از اینجا.
    verification-gate: فقط CONFIRMED/verified منابع."""
    if neural_stack is None:
        return None
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
            return None   # هیچ منبعِ verified
        return consolidation.run(sources)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"wiring: canonical_consolidation خطا: {e}"])
        return None
