#!/usr/bin/env python3
"""tick_timing.py — probeٔ اندازه‌گیریِ مدتِ فازها/beatهای tick (additive، صفر تغییر رفتار).

هدف (stage-3 گام ۱): بدون تغییرِ رفتار، بفهمیم کدام beat واقعاً زمان‌بر است تا
بهینه‌سازیِ هدف‌مند (نه حدس). پشتِ flag OCTOPUS_TICK_TIMING (پیش‌فرض خاموش = no-op).

قرارداد:
  - flag خاموش → همهٔ توابع no-op (بایت‌به‌بایتِ امروز).
  - flag روشن → هر beat مدتِ خودش را به یک JSONL سبک (state/pulse/tick-timing.jsonl)
    می‌نویسد. هرگز محتوا/prompt؛ فقط name, ms, beat, ok.
  - fail-soft: هر خطا → سکوت (probe هرگز tick را نمی‌کشد).
  - append-only؛ خودش rotation/dedup ندارد (حجم کم: یک سطر/beat).

استفاده در organism.py:
  from tick_timing import timing
  with timing("ziman_beat", beat=N):
      ... beat work ...
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from contextlib import contextmanager

_HERE = Path(__file__).resolve().parent
_OUT = _HERE / "state" / "pulse" / "tick-timing.jsonl"
_FLAG = "OCTOPUS_TICK_TIMING"
_written = False   # یک‌بار mkdir در عمرِ پروسه


def _flag_on() -> bool:
    return str(os.environ.get(_FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


@contextmanager
def timing(name: str, beat: int = 0):
    """context manager: مدتِ یک بلوک را می‌سنجد و (اگر flag روشن است) می‌نویسد.
    flag خاموش → صفر overhead (فقط yield، بدون I/O)."""
    if not _flag_on():
        yield
        return
    global _written
    t0 = time.time()
    ok = True
    err = ""
    try:
        yield
    except Exception as _e:  # noqa: BLE001 — probe هرگز caller را نمی‌کشد
        ok = False
        err = f"{type(_e).__name__}"
        raise
    finally:
        ms = int((time.time() - t0) * 1000)
        try:
            if not _written:
                _OUT.parent.mkdir(parents=True, exist_ok=True)
                _written = True
            with _OUT.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"name": name, "beat": beat, "ms": ms,
                                    "ok": ok, "err": err}, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            pass


def recent_summary(limit: int = 200) -> dict:
    """خلاصهٔ فوری برای داشبورد/API: میانگین/حداکثر/تعدادِ هر beat از آخرِ لاگ."""
    if not _OUT.exists():
        return {"enabled": _flag_on(), "samples": 0}
    by: dict[str, list[int]] = {}
    try:
        lines = _OUT.read_text("utf-8").splitlines()[-limit:]
    except Exception:  # noqa: BLE001
        return {"enabled": _flag_on(), "samples": 0}
    for ln in lines:
        try:
            d = json.loads(ln)
            by.setdefault(d["name"], []).append(int(d["ms"]))
        except Exception:  # noqa: BLE001
            continue
    out = {}
    for name, vals in by.items():
        out[name] = {"count": len(vals), "avg_ms": round(sum(vals)/len(vals)),
                     "max_ms": max(vals), "last_ms": vals[-1]}
    return {"enabled": _flag_on(), "samples": sum(len(v) for v in by.values()), "beats": out}
