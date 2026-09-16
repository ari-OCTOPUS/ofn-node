#!/usr/bin/env python3
"""heart/runtime.py — ضربان واحد Heart v2 روی BeatScheduler موجود.

قاعدهٔ بقا: هیچ حلقهٔ مستقل جدیدی ساخته نمی‌شود — همهٔ organها روی همان
BeatScheduler (ترتیب فاز قطعی، بودجه، isolation، circuit-breaker، HALT-safe)
ثبت می‌شوند و هویت beat از همان scheduler می‌آید. HeartStore ژورنالِ ترابزنشی
همان beat را ثبت می‌کند (RESERVED→COMMITTED/DEGRADED)؛ ACT عمداً ثبت نشده
(صفر اثر خارجی؛ اجرا فقط از مسیر آیندهٔ decision_arbiter/EffectorGate).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_HERE), str(_OPS), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import beat_scheduler as bs  # noqa: E402
from heart import kernel as hkernel      # noqa: E402
from heart import sensors as hsensors    # noqa: E402
from heart import state_machine as fsm   # noqa: E402
from heart import store as hstore        # noqa: E402

FLAG_ENV = "OCTOPUS_WIRE_HEART_V2"
FLAG_FILE = opslib.OPS / "ACTIVATION-HEART-V2.flag"
HEART_STATE = opslib.STATE_DIR / "pulse" / "heart-v2-latest.json"

_SCHED = None
_CTX = {"green_streak": 0, "prev_mode": "BOOTING", "prev_wake_beat": -10 ** 9,
        "store": None, "brain_ok": 0, "brain_degraded": 0}


def enabled() -> bool:
    if str(os.environ.get(FLAG_ENV, "")).strip().lower() in ("1", "true", "yes", "on"):
        return True
    try:
        return FLAG_FILE.exists()
    except OSError:
        return False


def _store():
    if _CTX["store"] is None:
        _CTX["store"] = hstore.get_store()
    return _CTX["store"]


# ── organها (هر کدام fail-soft؛ شکست یک organ ضربان را نمی‌ایستاند) ──────────
def _sense_organ(beat: int, dry_run: bool, halt) -> dict:
    observations = hsensors.collect()
    _CTX["observations"] = observations
    return {"n": len(observations)}


def _assess_organ(beat: int, dry_run: bool, halt) -> dict:
    st = _store()
    if st is None:
        return {"store": "unavailable"}
    observations = _CTX.get("observations") or []
    out = hkernel.assess(
        observations, current_mode=_CTX["prev_mode"], beat=int(beat),
        green_streak=_CTX["green_streak"],
        prev_wake_beat=_CTX["prev_wake_beat"],
        kill=bool(halt))
    st.begin_beat(int(beat), mode=out["mode"],
                  period_advisory_s=out.get("period_advisory_s"))
    _CTX["kernel"] = out
    _CTX["prev_mode"] = out["mode"]
    _CTX["green_streak"] = out["green_streak"]
    return {"mode": out["mode"], "reasons": out["reasons"]}


def _brain_organ(beat: int, dry_run: bool, halt) -> dict:
    kern = _CTX.get("kernel") or {}
    if not kern.get("wake_brain"):
        return {"woke": False}
    try:
        sys.path.insert(0, str(_OPS / "cortex"))
        import heart_brain as hb
        advisory = hb.wake(kern, _CTX.get("observations") or [], beat=int(beat))
        hb.record(advisory)
        if advisory.get("status") == "OK":
            _CTX["brain_ok"] += 1
        else:
            _CTX["brain_degraded"] += 1
        _CTX["prev_wake_beat"] = int(beat)
        st = _store()
        if st is not None:
            st.emit(int(beat), "brain.advisory", {
                "status": advisory.get("status"),
                "assessment": advisory.get("assessment"),
                "n_questions": len(advisory.get("questions") or []),
                "n_proposals": len(advisory.get("proposals") or [])},
                correlation=f"beat-{beat}")
        return {"woke": True, "status": advisory.get("status")}
    except Exception as e:  # noqa: BLE001
        return {"woke": False, "error": type(e).__name__}


def _memory_organ(beat: int, dry_run: bool, halt) -> dict:
    """HEAL-گونه: tick پیوستگی (پروجکشن + backup) — idempotent و ارزان."""
    try:
        sys.path.insert(0, str(_OPS / "memory"))
        import continuity as hc
        return hc.tick(beat=int(beat))
    except Exception as e:  # noqa: BLE001
        return {"error": type(e).__name__}


def _heal_organ(beat: int, dry_run: bool, halt) -> dict:
    st = _store()
    kern = _CTX.get("kernel") or {}
    committed = False
    if st is not None:
        committed = st.commit_beat(
            int(beat), mode=kern.get("mode"),
            period_advisory_s=kern.get("period_advisory_s"),
            report={"kernel": {k: kern.get(k) for k in (
                "mode", "mode_prev", "reasons", "green_streak", "wake_brain",
                "wake_reasons", "n_missing", "n_stale", "write_failures_1h")}})
    _write_projection(kern, beat)
    return {"committed": committed}


def _write_projection(kern: dict, beat: int) -> None:
    st = _store()
    counts = st.counts() if st is not None else {}
    proj = {"schema": "heart-v2/1", "ts": opslib.now_iso(), "beat": int(beat),
            "mode": kern.get("mode"), "mode_prev": kern.get("mode_prev"),
            "green_streak": kern.get("green_streak"),
            "period_advisory_s": kern.get("period_advisory_s"),
            "wake_brain": kern.get("wake_brain"),
            "brain_stats": {"ok": _CTX["brain_ok"],
                            "degraded": _CTX["brain_degraded"]},
            "store_counts": counts, "advisory_only": True}
    try:
        HEART_STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = HEART_STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(proj, ensure_ascii=False, indent=1), "utf-8")
        os.replace(tmp, HEART_STATE)
    except OSError:
        pass


def get_scheduler():
    """ساخت idempotentِ scheduler با organهای قلب (تک‌نمونه در هر پروسه)."""
    global _SCHED
    if _SCHED is not None:
        return _SCHED
    if not enabled():
        return None
    state_path = opslib.STATE_DIR / "pulse" / "heart-v2-beat-state.json"
    sched = bs.BeatScheduler(state_path=state_path, spine=None,
                             halted_fn=opslib.halted, production_safe=False)
    sched.register_organ("heart-sense", "SENSE", _sense_organ, budget_ms=800)
    sched.register_organ("heart-assess", "RECORD", _assess_organ, budget_ms=400)
    sched.register_organ("heart-brain", "THINK", _brain_organ,
                         every_n_beats=1, budget_ms=120000)
    sched.register_organ("heart-memory", "HEAL", _memory_organ,
                         every_n_beats=15, budget_ms=20000)
    sched.register_organ("heart-heal", "HEAL", _heal_organ, budget_ms=800)
    _SCHED = sched
    return sched


def tick(beat: int = 0) -> "dict | None":
    """یک ضربان کامل قلب v2 (از حلقهٔ organism صدا زده می‌شود)."""
    sched = get_scheduler()
    if sched is None:
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.master_halted():
        return None
    return sched.tick()


def read_latest() -> dict:
    try:
        return json.loads(HEART_STATE.read_text("utf-8-sig")) if HEART_STATE.exists() else {}
    except (OSError, ValueError):
        return {}
