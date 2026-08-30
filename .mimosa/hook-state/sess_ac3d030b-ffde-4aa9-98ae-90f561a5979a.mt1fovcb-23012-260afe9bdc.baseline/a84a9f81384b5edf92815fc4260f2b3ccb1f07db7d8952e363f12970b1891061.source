#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""soak_scorecard.py — کارت امتیازِ soak ۷۲ساعته (۲۰۲۶-۰۸-۱۰).

قرارداد (نکتهٔ ۳ از review):
  · هر ۱۲ ساعت (با heartbeat) اجرا می‌شود.
  · هر متریک را با آستانهٔ هشدار/توقف مقایسه می‌کند.
  · **هیچ اقدام خودکاری** — عبور از آستانهٔ توقف = توقفِ soak و گزارش به مالک.
  · baseline مرجع: _ops/state/soak-baseline.json (beat=30338, bcm=146, semantic=517).

متریک‌ها:
  deny stop-*  | fugu-quota.json     | هشدار: هر رشد | توقف: >۵ در ۲۴h
  breaker      | circuit-state.json  | هشدار: half_open | توقف: open
  paid success | paid-calls.jsonl    | هشدار: <۹۰٪ روزانه | توقف: <۷۰٪ روزانه
  halt duty    | ORGANISM-STATE.json | هشدار: >۵٪ | توقف: >۱۵٪
  restart      | flags-loaded-*.json | هشدار: هر restart غیربرنامه‌ای | توقف: ≥۲ در ۲۴h
  BCM step     | bcm-weights.json    | هشدار: رکود ۴۸h | توقف: —
  lost effect  | intervention-ledger | هشدار: هر مورد | توقف: ≥۳

CLI:
  python -X utf8 _ops/soak_scorecard.py --check
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
STATE = _HERE / "state"


def _read(p: Path, default=None):
    try:
        return json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        return default


def _soak_start_ts() -> str:
    """شروع soak از baseline — **زمان محلی** (paid-calls با local نوشته می‌شود).
    v2: فیلد start_local. fallback به start_ts قدیمی."""
    b = _read(STATE / "soak-baseline.json", {})
    return b.get("start_local", b.get("start_ts", ""))


def _deny_baseline() -> int:
    """deny در لحظهٔ شروع soak — از intervention-ledger (ورودی model_map_change)."""
    try:
        lines = STATE.joinpath("intervention-ledger.jsonl").read_text("utf-8").splitlines()
        for line in reversed(lines):
            d = json.loads(line)
            if d.get("kind") == "model_map_change":
                return int(d.get("deny_before", 0) or 0)
    except (OSError, ValueError):
        pass
    return 0


def _paid_stats():
    """success rate از لحظهٔ baseline soak (نه کلِ امروز — چون قبل از
    intervention همه deny بودند و متریک را می‌سوزانند)."""
    start = _soak_start_ts()
    try:
        lines = STATE.joinpath("paid-calls.jsonl").read_text("utf-8").splitlines()
    except OSError:
        return {"total": 0, "ok": 0, "rate": None}
    total = ok = 0
    for line in lines[-500:]:
        try:
            d = json.loads(line)
            if d.get("ts", "") >= start:
                total += 1
                if d.get("ok"):
                    ok += 1
        except ValueError:
            continue
    return {"total": total, "ok": ok, "rate": (ok / total if total else None)}


def _halt_duty():
    """halt/frozen از ORGANISM-STATE."""
    d = _read(STATE / "ORGANISM-STATE.json", {})
    return {"halted": bool(d.get("halted")), "frozen": bool(d.get("frozen"))}


def _restarts():
    """شمار restartهای **بعد از baseline** — نه شمار فایل‌ها.
    یک ری‌استارت = mtime یک فایل flags-loaded جدیدتر از شروعِ soak.
    (هر پروسه یک فایل دارد؛ شمارش فایل‌های تازه = شمار ری‌استارت‌ها.)"""
    import glob
    start = _soak_start_ts()
    if not start:
        return 0
    fmt = "%Y-%m-%dT%H:%M:%SZ" if start.endswith("Z") else "%Y-%m-%dT%H:%M:%S"
    start_epoch = time.mktime(time.strptime(start, fmt))
    if start.endswith("Z"):
        start_epoch = time.time() + (start_epoch - time.mktime(time.gmtime()))
    # پروسه‌های شناخته‌شده — هر کدام یک فایل
    known = ["organism", "cortex", "live", "center", "miniapp-gateway"]
    planned = _planned_restarts()
    count = 0
    for name in known:
        if name in planned:
            continue  # ری‌استارتِ برنامه‌ریزی‌شده (مداخلهٔ مستند) — نه drift
        f = STATE / f"flags-loaded-{name}.json"
        try:
            if f.stat().st_mtime >= start_epoch - 5:  # 5s تلورانس
                count += 1
        except OSError:
            continue
    return count


def _planned_restarts() -> list:
    """ری‌استارت‌های برنامه‌ریزی‌شده از intervention-ledger (مداخله‌های مستند)."""
    try:
        lines = STATE.joinpath("intervention-ledger.jsonl").read_text("utf-8").splitlines()
        out = []
        for line in lines:
            d = json.loads(line)
            out.extend(d.get("planned_restarts", []))
        return out
    except (OSError, ValueError):
        return []


def _bcm():
    d = _read(STATE / "bcm-weights.json", {})
    return {"step": d.get("step")}


def check() -> dict:
    """همهٔ متریک‌ها + verdict."""
    fq = _read(STATE / "fugu-quota.json", {})
    cs = _read(STATE / "circuit-state.json", {})
    paid = _paid_stats()
    halt = _halt_duty()
    restarts = _restarts()
    bcm = _bcm()

    alerts = []
    stops = []

    # 1. deny stop-* — **رشدِ** deny از baseline (نه مجموعِ تاریخی).
    # deny=96 مجموعِ تاریخچه است؛ رشد یعنی deny جدید بعد از شروع soak.
    deny_before = _deny_baseline()
    denied_now = fq.get("denied", {}).get("stop-fugu", 0)
    deny_growth = denied_now - deny_before
    if deny_growth > 5:
        stops.append(f"deny stop-fugu رشد {deny_growth} > 5 در ۲۴h — توقف soak")
    elif deny_growth > 0:
        alerts.append(f"deny stop-fugu رشد {deny_growth} (هشدار)")

    # 2. breaker state
    for name, tgt in (cs.get("targets") or {}).items():
        st = tgt.get("state", "")
        if st == "open":
            stops.append(f"breaker[{name}] OPEN — توقف soak")
        elif st == "half_open":
            alerts.append(f"breaker[{name}] half_open — هشدار")

    # 3. paid success rate
    rate = paid.get("rate")
    if rate is not None:
        if rate < 0.70:
            stops.append(f"paid success {rate:.0%} < 70% — توقف soak")
        elif rate < 0.90:
            alerts.append(f"paid success {rate:.0%} < 90% — هشدار")

    # 4. halt duty
    if halt["halted"] or halt["frozen"]:
        stops.append(f"halt/frozen فعال — توقف soak ({halt})")

    # 5. restarts
    if restarts >= 2:
        stops.append(f"restart count {restarts} ≥ 2 در ۲۴h — توقف soak")
    elif restarts >= 1:
        alerts.append(f"restart count {restarts} در ۲۴h — هشدار")

    # 6. BCM stagnation
    # (baseline bcm_step مقایسه — رکود ۴۸h یعنی تغییری در ۴۸h گذشته)

    # 7. lost effect
    try:
        il = STATE.joinpath("intervention-ledger.jsonl").read_text("utf-8").splitlines()
        if len(il) >= 3:
            stops.append(f"intervention-ledger {len(il)} ورودی ≥ ۳ — توقف soak")
    except OSError:
        pass

    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "metrics": {
            "deny_stop_fugu": denied_now,
            "breakers": {k: v.get("state") for k, v in (cs.get("targets") or {}).items()},
            "paid_success_rate": rate,
            "halt": halt,
            "restarts_24h": restarts,
            "bcm_step": bcm.get("step"),
        },
        "alerts": alerts,
        "stops": stops,
        "verdict": "STOP" if stops else ("ALERT" if alerts else "GREEN"),
    }


def main():
    r = check()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    print(f"\nverdict: {r['verdict']}")
    if r["stops"]:
        print("⛔ توقف soak — به مالک گزارش بده (هیچ اقدام خودکاری)")
    return 1 if r["stops"] else (0 if r["verdict"] == "GREEN" else 0)


if __name__ == "__main__":
    raise SystemExit(main())
