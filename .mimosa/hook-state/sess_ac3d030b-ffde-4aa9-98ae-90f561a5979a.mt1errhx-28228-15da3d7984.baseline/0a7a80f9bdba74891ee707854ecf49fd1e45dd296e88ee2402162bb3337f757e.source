#!/usr/bin/env python3
"""drift_metric.py — سنجه‌ی رانشِ زمانی (up-ae4a7476a9، P2 Missing → Done).

مسئله: self_audit می‌گوید «drift over time measured: Missing». سیستم coherence
را در هر cycle می‌سنجد ولی آن را به‌صورت temporal series نگه نمی‌دارد و شیبِ
منفی را هشدار نمی‌دهد. یک خودآگاهیِ بدونِ drift-detection نمی‌داند آیا رو به
خرابی می‌رود یا ثابت است.

راه‌حل: این ماژول journal.jsonl را می‌خواند، coherence/velocity را در پنجره‌های
زمانی میانگین می‌گیرد، و شیبِ بینِ پنجرهٔ اخیر و قبلی را محاسبه می‌کند.
شیبِ منفیِ پایدار = drift (هشدار).

خروجی: {current, previous, slope, trend, drifting, window_count}
  - drifting=True اگر slope < -DRIFT_THRESHOLD در N پنجرهٔ متوالی
  - trend: "improving" | "stable" | "declining"

مرزها: فقط می‌خواند (journal.jsonl). هرگز نمی‌نویسد. fail-soft.
پشتِ flag: OCTOPUS_WIRE_DRIFT_METRIC (پیش‌فرض خاموش).
$0، stdlib-only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_HERE), str(_OPS), str(_OPS / "budget")):
    if _p not in __import__("sys").path:
        __import__("sys").path.insert(0, _p)
import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_DRIFT_METRIC"
SCHEMA = "drift-metric.v1"
STATE = opslib.STATE_DIR / "cortex" / "drift-metric-latest.json"

# پارجره: هر N ورودیِ journal یک پنجره. اخیر vs قبلی.
WINDOW_SIZE = 20          # ~۲۰ cycle هر پنجره
DRIFT_THRESHOLD = -0.05   # شیبِ منفیِ بیشتر از این = drift
CONSECUTIVE_FOR_ALERT = 2  # N پنجرهٔ متوالیِ شیبِ منفی = هشدار


def _read_coherence_series(limit: int = 200) -> list[float]:
    """آخرین N مقدار coherence از journal.jsonl."""
    journal = opslib.STATE_DIR / "cortex" / "journal.jsonl"
    if not journal.exists():
        return []
    try:
        lines = journal.read_text("utf-8").strip().splitlines()
        vals = []
        for line in reversed(lines):
            if len(vals) >= limit:
                break
            try:
                d = json.loads(line)
                c = d.get("coherence")
                if isinstance(c, (int, float)):
                    vals.append(float(c))
            except (json.JSONDecodeError, TypeError):
                continue
        vals.reverse()
        return vals
    except Exception:  # noqa: BLE001
        return []


def _windowed_avg(series: list[float], window: int) -> list[float]:
    """میانگینِ متحرکِ ساده."""
    if len(series) < window:
        return [sum(series) / max(len(series), 1)] if series else []
    out = []
    for i in range(0, len(series) - window + 1, window):
        chunk = series[i:i + window]
        out.append(sum(chunk) / len(chunk))
    return out


def compute() -> dict:
    """رانشِ زمانی را محاسبه می‌کند."""
    series = _read_coherence_series()
    if len(series) < WINDOW_SIZE * 2:
        return {"schema": SCHEMA, "status": "insufficient-data",
                "n_points": len(series), "drifting": False, "trend": "unknown"}
    windows = _windowed_avg(series, WINDOW_SIZE)
    if len(windows) < 2:
        return {"schema": SCHEMA, "status": "insufficient-windows",
                "n_points": len(series), "drifting": False, "trend": "unknown"}

    current = windows[-1]
    previous = windows[-2]
    slope = current - previous

    # شیب‌های اخیر برای تشخیصِ drift پایدار
    recent_slopes = []
    for i in range(1, min(len(windows), CONSECUTIVE_FOR_ALERT + 1)):
        if i < len(windows):
            recent_slopes.append(windows[i] - windows[i - 1])

    negative_count = sum(1 for s in recent_slopes if s < DRIFT_THRESHOLD)
    drifting = negative_count >= CONSECUTIVE_FOR_ALERT

    if slope > 0.02:
        trend = "improving"
    elif slope < DRIFT_THRESHOLD:
        trend = "declining"
    else:
        trend = "stable"

    result = {
        "schema": SCHEMA, "ts": opslib.now_iso(),
        "n_points": len(series), "n_windows": len(windows),
        "current": round(current, 4), "previous": round(previous, 4),
        "slope": round(slope, 4), "trend": trend,
        "drifting": drifting, "negative_windows": negative_count,
        "window_size": WINDOW_SIZE, "threshold": DRIFT_THRESHOLD,
    }

    if drifting:
        try:
            opslib.alert([f"⚠️ drift-detected: coherence در حالِ افتِ پایدار است "
                          f"(slope={slope:.4f}, {negative_count} پنجرهٔ منفی متوالی)"])
        except Exception:  # noqa: BLE001
            pass

    return result


def run_and_persist() -> dict:
    """محاسبه + نوشتن در drift-metric-latest.json. fail-soft."""
    try:
        result = compute()
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
        return result
    except Exception as e:  # noqa: BLE001
        return {"schema": SCHEMA, "status": "error", "error": str(e)[:100]}
