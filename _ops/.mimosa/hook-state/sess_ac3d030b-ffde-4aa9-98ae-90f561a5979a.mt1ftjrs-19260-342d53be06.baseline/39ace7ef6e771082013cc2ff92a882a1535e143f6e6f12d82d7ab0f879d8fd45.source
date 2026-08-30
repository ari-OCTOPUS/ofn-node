#!/usr/bin/env python3
"""temperature.py — Blueprint Phase 5 — دمای Chamber: T بالا = اکتشاف، T پایین = پالایش.
فقط sandbox؛ هرگز auto-merge؛ مهارهای ایمنی (Red-Critic، λ_persist) هرگز تابع دما نیستند.

دما فقط «عمقِ حلقهٔ Chamber» (تعدادِ دور) را تنظیم می‌کند — advisory و propose-only:
  - رکود (مدت‌ها هیچ RFCای merge نشده) → T بالا → اکتشافِ بیشتر (دورهای بیشتر، تا سقفِ ۳).
  - نرخِ merge بالا (مسیرِ فعلی جواب می‌دهد) → T پایین → پالایش (دورهای کمتر).
منبعِ سیگنال: verdict-history از calibration (خواندنِ صرف؛ هیچ نوشتنی در chrono.db).

مرزهای سخت (RED / zero-auto-merge):
  - این ماژول هیچ gate/effector/کانالی را صدا نمی‌زند؛ فقط یک float برمی‌گرداند.
  - rounds_for هرگز از MAX_ROUNDS چمبر (=۳) بالاتر نمی‌رود.
  - deterministic: هیچ random؛ time.time فقط metadata در persist.
  - fail-soft: db=None یا هر خطا → دمای خنثی (وسطِ بازه).
پیش‌ثبتِ متریک (state/phase-metrics.jsonl): chamber_temperature_range همیشه در [T_min,T_max].
stdlib-only، $0 آفلاین.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# bootstrap هم‌پوشه (الگوی chamber.py) — تا 'calibration' مسطح import شود
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))


def _env_float(name: str, default: float) -> float:
    v = os.environ.get(name)
    if v is None:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    v = os.environ.get(name)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


class TemperatureController:
    """کنترلرِ دمای Chamber. current() → T ∈ [t_min, t_max] از روی verdict-history.

    اولویتِ پارامترها (الگوی bcm._env_float): آرگومانِ سازنده > env > پیش‌فرض.
      t_min  ← OCTOPUS_CHAMBER_T_MIN    (پیش‌فرض 0.2)
      t_max  ← OCTOPUS_CHAMBER_T_MAX    (پیش‌فرض 1.5)
      window ← OCTOPUS_CHAMBER_T_WINDOW (پیش‌فرض 20 رکوردِ آخر)
    persist_path پیش‌فرض state/chamber-temperature.json (تست‌ها tmp تزریق می‌کنند).
    """

    def __init__(self, db=None, t_min: float | None = None, t_max: float | None = None,
                 window: int | None = None, persist_path=None):
        self._db = db
        self.t_min = float(t_min) if t_min is not None else _env_float(
            "OCTOPUS_CHAMBER_T_MIN", 0.2)
        self.t_max = float(t_max) if t_max is not None else _env_float(
            "OCTOPUS_CHAMBER_T_MAX", 1.5)
        self.window = int(window) if window is not None else _env_int(
            "OCTOPUS_CHAMBER_T_WINDOW", 20)
        if persist_path is not None:
            self._persist_path = Path(persist_path)
        else:
            # OPS_DIR اگر ست باشد (harness تست‌ها آن را به tmp می‌برد)، وگرنه _ops کنارِ این فایل
            _ops = Path(os.environ.get("OPS_DIR", str(_HERE.parent)))
            self._persist_path = _ops / "state" / "chamber-temperature.json"

    # ─── دمای فعلی — read-only روی verdict-history ─────────────────────────────
    def current(self) -> float:
        """T ∈ [t_min, t_max]. deterministic از روی history؛ خطا/بی‌داده → خنثی (وسطِ بازه).
        explore = 0.7·stag_norm + 0.3·(1 − merge_rate) — رکود وزنِ بیشتری دارد."""
        history: list[dict] = []
        if self._db is not None:
            try:
                import calibration  # lazy — هم‌پوشه، بدونِ وابستگیِ production
                history = calibration.get_verdict_history(self._db)
            except Exception:  # noqa: BLE001 — fail-soft: بی‌تاریخچه = دمای خنثی
                history = []
        recent = list(history[-self.window:]) if self.window > 0 else []
        merged_count = sum(1 for d in recent if d.get("verdict") == "merged")
        rejected_count = sum(1 for d in recent if d.get("verdict") == "rejected")
        denom = merged_count + rejected_count
        merge_rate = (merged_count / denom) if denom > 0 else None
        # stagnation = تعدادِ رکوردها از آخرین merged به بعد (هیچ merged → کلِ recent)
        stagnation = len(recent)
        for i in range(len(recent) - 1, -1, -1):
            if recent[i].get("verdict") == "merged":
                stagnation = len(recent) - 1 - i
                break
        stag_norm = min(1.0, stagnation / 10.0)
        if merge_rate is None and stagnation == 0:
            explore = 0.5   # بی‌داده → خنثی (وسطِ بازه)
        else:
            mr = merge_rate if merge_rate is not None else 0.5
            explore = _clip01(0.7 * stag_norm + 0.3 * (1.0 - mr))
        t = self.t_min + (self.t_max - self.t_min) * explore
        t = max(self.t_min, min(self.t_max, t))   # hard-clip — متریکِ پیش‌ثبت‌شده
        self._persist(t, explore, merge_rate, stagnation)
        return t

    # ─── نگاشتِ دما → تعدادِ دور (سقفِ مطلق = MAX_ROUNDS چمبر = ۳) ─────────────
    def rounds_for(self, temperature: float) -> int:
        """max(1, min(3, round(T·2))) — 3 = chamber.MAX_ROUNDS؛ هرگز بالاتر."""
        return max(1, min(3, round(float(temperature) * 2)))

    # ─── persist اتمی fail-soft — فقط observability، هیچ تصمیمی از آن نمی‌آید ──
    def _persist(self, t: float, explore: float, merge_rate: float | None,
                 stagnation: int) -> None:
        try:
            payload = {"ts": time.time(),   # فقط metadata — نه ورودیِ تصمیم
                       "T": round(t, 4), "explore": round(explore, 4),
                       "merge_rate": merge_rate, "stagnation": stagnation}
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._persist_path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self._persist_path)
        except Exception:  # noqa: BLE001 — persist صرفاً observability؛ خطا نباید دما را بکشد
            pass
