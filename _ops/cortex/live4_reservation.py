#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""live4_reservation.py — لایهٔ رزروِ ظرفیت برای LIVE-4 (LIVE-4-CAPACITY-RESERVATION-01).

غیر-TCB · برگشت‌پذیر · بدون scheduler: پنجره فقط با «ریستِ مشاهده‌شدهٔ سهمیه» باز می‌شود
(دروازهٔ درونیِ خودِ launcher) و با سقف‌ها/انقضا می‌بندد. حالت در یک JSON کوچک."""
from __future__ import annotations

import json
import time
from pathlib import Path

SCHEMA = "live4-reservation/1"
_HERE = Path(__file__).resolve().parent
STATE = _HERE.parent / "state" / "cortex" / "live4-reservation.json"
QUOTA = _HERE.parent / "state" / "fugu-quota.json"
RECEIPTS = _HERE.parent / "state" / "cortex" / "reservation-receipts.jsonl"
LIVE4_TASK_PREFIX = "live4"
CAPS = {"max_provider_attempts": 200, "max_pairs": 60, "max_judge_evals": 60, "window_max_s": 90 * 60}


def _receipt(event: str, **kw) -> None:
    """G10/G11 (2026-08-19, CORE-AUTO-DEBUG): هر ریست/توقفِ پنجره رسیدِ مستقل
    می‌گیرد — resetِ شمارنده‌ها هرگز اثرِ نامرئی نمی‌ماند (حاکمیتِ ODN-6)."""
    from datetime import datetime, timezone
    rec = {"schema": "reservation-receipt/1", "event": event,
           "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **kw}
    try:
        RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
        RECEIPTS.open("a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def _load() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"active": False}


def _save(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def quota_snapshot() -> dict:
    try:
        q = json.loads(QUOTA.read_text(encoding="utf-8"))
        return {"day": q.get("day"), "used_total": q.get("used_total")}
    except Exception:  # noqa: BLE001
        return {"day": None, "used_total": None}


def observe_quota_reset(previous_day: str | None) -> dict | None:
    """ریست = روزِ سهمیه جلوتر از روزِ ثبت‌شدهٔ قبلی. مشاهده را ثبت می‌کند (بدون scheduler)."""
    snap = quota_snapshot()
    if snap["day"] and previous_day and str(snap["day"]) > str(previous_day):
        rec = {"schema": "quota-reset-observation/1", "observed_at_day": snap["day"],
               "previous_day": previous_day, "used_total_after_reset": snap["used_total"]}
        (STATE.parent / "QUOTA-RESET-OBSERVATION.json").write_text(
            json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        return rec
    return None


def start(previous_day: str | None) -> dict:
    """فقط با ریستِ مشاهده‌شده باز می‌شود؛ وگرنه active=false می‌ماند."""
    rec = observe_quota_reset(previous_day)
    if rec is None:
        return {"active": False, "reason": "QUOTA-RESET-NOT-OBSERVED",
                "quota": quota_snapshot(), "previous_day": previous_day}
    _save({"active": True, "started_at": time.time(), "reset_record": rec,
           "provider_attempts": 0, "judge_evals": 0, "pairs": 0})
    return {"active": True, "reset_record": rec}


def stop(reason: str) -> dict:
    st = _load(); st["active"] = False; st["stopped_reason"] = reason
    _save(st)
    _receipt("RESERVATION_STOPPED", reason=reason,
             counters={k: st.get(k, 0) for k in ("provider_attempts", "judge_evals", "pairs")})
    return st


def is_active() -> bool:
    st = _load()
    if not st.get("active"):
        return False
    if time.time() - float(st.get("started_at", 0)) > CAPS["window_max_s"]:
        stop("window-expired-90min"); return False
    if int(st.get("provider_attempts", 0)) >= CAPS["max_provider_attempts"]:
        stop("attempts-cap-90"); return False
    return True


def gate_paid(task: str) -> dict | None:
    """دروازهٔ ask(): None=عبور؛ dict=ردِ رسیددار (DEFERRED یا شمارش تلاش)."""
    if not is_active():
        return None
    st = _load()
    if str(task or "").startswith(LIVE4_TASK_PREFIX):
        st["provider_attempts"] = int(st.get("provider_attempts", 0)) + 1
        _save(st)
        if int(st["provider_attempts"]) > CAPS["max_provider_attempts"]:
            stop("attempts-cap-90")
            return _defer(task, "CAP_REACHED")
        return None  # عبورِ اختصاصی Live-4
    return _defer(task, "RESERVED_FOR_LIVE4")


def _defer(task: str, code: str) -> dict:
    return {"receipt_status": "DEFERRED_FOR_LIVE4_RESERVATION",
            "provider_actual": "none", "cost_aud": 0,
            "retry_after": "quota_reset_or_window_end",
            "evaluation_eligible": False, "task": str(task), "code": code,
            "schema": SCHEMA}


def record(kind: str) -> None:
    st = _load()
    if kind == "judge":
        st["judge_evals"] = int(st.get("judge_evals", 0)) + 1
    elif kind == "pair":
        st["pairs"] = int(st.get("pairs", 0)) + 1
    _save(st)


def status() -> dict:
    st = _load()
    return {"active": st.get("active", False), "caps": CAPS,
            "used": {k: st.get(k, 0) for k in ("provider_attempts", "judge_evals", "pairs")},
            "quota": quota_snapshot()}


def start_override(owner_decision_id: str) -> dict:
    """LEARNING-FIRST-BUDGET-EXPANSION-01: شروعِ بی‌درنگ — بدون انتظار برای ریستِ سهمیه؛
    مسیرِ usable-provider با probe مشاهده‌شده است. رکورد تصمیم به‌جای QUOTA-RESET می‌نشیند."""
    import time as _t
    rec = {"schema": "reservation-override/1", "owner_decision_id": str(owner_decision_id),
           "basis": "usable paid path probe-observed; budget expanded (30/24/1.00)",
           "observed_at": _t.time()}
    _prev = _load()
    _save({"active": True, "started_at": _t.time(), "reset_record": rec,
           "provider_attempts": 0, "judge_evals": 0, "pairs": 0})
    _receipt("RESERVATION_RESET", owner_decision_id=str(owner_decision_id),
             previous_counters={k: _prev.get(k, 0) for k in ("provider_attempts", "judge_evals", "pairs")},
             note="counters zeroed by override — receipted per ODN-6 governance")
    return {"active": True, "override": rec}
