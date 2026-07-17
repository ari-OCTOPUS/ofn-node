#!/usr/bin/env python3
"""circuit_breaker.py — Circuit breaker per-target برای تماس‌های بیرونی (M1-M2).

خط‌قرمزهای سخت:
  • fail-closed: circuit باز = هرگز تماس نمی‌زند (fast-fail).
  • state اتمیک (LockedJson) — چندپارگی بین فرایندها محال.
  • اعداد از budgets.yaml (I6)؛ نبود = default با tag EST (همان الگوی opslib.fx).
  • stdlib-only؛ $0 offline؛ propose-only.
"""
from __future__ import annotations

import json
import sys
from enum import Enum
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import opslib  # noqa: E402

STATE_PATH = opslib.STATE_DIR / "circuit-state.json"


class State(Enum):
    CLOSED = "closed"       # عادی — تماس مجاز
    OPEN = "open"           # fail-fast — صفر تماس
    HALF_OPEN = "half_open" # یک تماس آزمایشی مجاز


def _cfg() -> dict:
    """پیکربندی از budgets.yaml → resilience.circuit_breaker. نبود = default."""
    try:
        b = opslib.load_budgets()
    except Exception:  # noqa: BLE001
        b = {}
    r = (b.get("resilience") or {}).get("circuit_breaker") or {}
    return {
        "failure_threshold": int(r.get("failure_threshold", 5)),
        "cooldown_seconds": float(r.get("cooldown_seconds", 60)),
        "half_open_max": int(r.get("half_open_max", 3)),
        "success_to_close": int(r.get("success_to_close", 2)),
        "tag": "FACT(budgets.yaml)" if r else "EST(default)",
    }


def _load_state() -> dict:
    with opslib.LockedJson(STATE_PATH) as lj:
        return lj.read()


def _save_state(state: dict) -> None:
    with opslib.LockedJson(STATE_PATH) as lj:
        lj.write(state)


def _target_entry(state: dict, target: str) -> dict:
    t = state.setdefault("targets", {}).setdefault(target, {})
    t.setdefault("state", State.CLOSED.value)
    t.setdefault("fail_count", 0)
    t.setdefault("success_count", 0)
    t.setdefault("last_fail_ts", None)
    t.setdefault("last_ok_ts", None)
    t.setdefault("opened_at_ts", None)
    t.setdefault("half_open_attempts", 0)
    return t


def check(target: str) -> dict:
    """بررسی circuit برای target. خروجی: {allow: bool, state: str, reason: str}.
    allow=False → فراخوان‌کننده باید فوراً fail-soft کند (صفر شبکه)."""
    cfg = _cfg()
    state = _load_state()
    t = _target_entry(state, target)
    st = State(t["state"])

    if st is State.OPEN:
        opened = t.get("opened_at_ts")
        if opened:
            import time as _time
            elapsed = _time.time() - opened
            if elapsed >= cfg["cooldown_seconds"]:
                t["state"] = State.HALF_OPEN.value
                t["half_open_attempts"] = 0
                _save_state(state)
                return {"allow": True, "state": State.HALF_OPEN.value,
                        "reason": f"cooldown elapsed ({int(elapsed)}s) → half_open"}
        return {"allow": False, "state": State.OPEN.value,
                "reason": f"circuit open (cooldown {cfg['cooldown_seconds']}s)"}

    if st is State.HALF_OPEN:
        if t.get("half_open_attempts", 0) >= cfg["half_open_max"]:
            return {"allow": False, "state": State.HALF_OPEN.value,
                    "reason": f"half_open max attempts ({cfg['half_open_max']}) reached"}
        return {"allow": True, "state": State.HALF_OPEN.value,
                "reason": "half_open (one probe allowed)"}

    return {"allow": True, "state": State.CLOSED.value, "reason": "circuit closed"}


def record_success(target: str) -> dict:
    """ثبت موفقیت. اگر در half_open به success_to_close رسید → closed."""
    cfg = _cfg()
    state = _load_state()
    t = _target_entry(state, target)
    t["last_ok_ts"] = opslib.now_iso()
    t["fail_count"] = 0

    st = State(t["state"])
    if st is State.HALF_OPEN:
        t["success_count"] = t.get("success_count", 0) + 1
        t["half_open_attempts"] = t.get("half_open_attempts", 0) + 1
        if t["success_count"] >= cfg["success_to_close"]:
            t["state"] = State.CLOSED.value
            t["success_count"] = 0
            t["half_open_attempts"] = 0
            t["opened_at_ts"] = None
    _save_state(state)
    return {"state": t["state"], "target": target}


def record_failure(target: str, reason: str = "") -> dict:
    """ثبت شکست. اگر threshold رد شد → OPEN + FREEZE اگر critical."""
    cfg = _cfg()
    state = _load_state()
    t = _target_entry(state, target)
    t["last_fail_ts"] = opslib.now_iso()
    t["fail_count"] = t.get("fail_count", 0) + 1

    st = State(t["state"])
    if st is State.HALF_OPEN:
        t["half_open_attempts"] = t.get("half_open_attempts", 0) + 1
        # شکست در half_open → فوراً باز
        t["state"] = State.OPEN.value
        t["opened_at_ts"] = __import__("time").time()
    elif t["fail_count"] >= cfg["failure_threshold"]:
        t["state"] = State.OPEN.value
        t["opened_at_ts"] = __import__("time").time()

    _save_state(state)

    # alert اگر تازه باز شد
    if t["state"] == State.OPEN.value and st is not State.OPEN:
        opslib.alert([f"circuit OPEN for {target} (fail_count={t['fail_count']}) {reason}"])

    return {"state": t["state"], "target": target, "fail_count": t["fail_count"]}


def status(target: str | None = None) -> dict:
    """snapshot وضعیت circuit breaker(ها)."""
    state = _load_state()
    cfg = _cfg()
    targets = state.get("targets", {})
    if target:
        t = targets.get(target, {})
        return {"target": target, **t, "config": cfg}
    return {"targets": targets, "config": cfg, "ts": opslib.now_iso()}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(json.dumps(status(sys.argv[1]), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(status(), ensure_ascii=False, indent=2))
