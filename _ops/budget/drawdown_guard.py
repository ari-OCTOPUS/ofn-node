#!/usr/bin/env python3
"""drawdown_guard.py — بک‌لاگِ ۲۰۲۷ #۴: circuit-breakerِ drawdown، **فقط shadow-count**.

استاندارد: کنترلِ ریسکِ سختِ pre-trade، **بیرونِ منطقِ معامله** (SEC 15c3-5 / Nygard 2018 /
EU AI Act Art.14). امروز `spike_pct=25` در `budgets.yaml` فقط test-asserted است — هیچ
enforcerِ زنده‌ای نداشت. این ماژول تابعِ خالصِ وردیکت + شمارندهٔ سایه را اضافه می‌کند.

⚠️ مرزِ پول (رأی مالک «فقط پیشنهاد»): این ماژول **هرگز چیزی را زنده HALT نمی‌کند**. حالتِ
تنها = shadow-count (فقط لاگِ would-halt). سیم‌کشیِ زنده به هر مسیرِ معامله/ارگانیسم =
میزِ مالک، پشتِ فلگِ `HH_DRAWDOWN_ENFORCE` + تصمیمِ صریح. `enforced_live` همیشه False است.

fail-closed (Saltzer-Schroeder): drawdownِ نامعلوم/غیرمتناهی → وردیکتِ HALT (محتاطانه) —
چون یک circuit-breaker در ابهام باید بایستد، نه عبور دهد. ولی چون فقط shadow است، این
HALT صرفاً ثبت می‌شود.

$0 · stdlib · fail-soft. الگوی fail-closedِ مورد #۱ (human_append_guard) بازاستفاده شد.

⚠️ نام‌گذاریِ هم‌نام (۲۰۲۶-۰۸-۰۷، پیگیریِ اسکنِ بازطراحی): یک ماژولِ هم‌نامِ کاملاً
مستقل در `04 - Architect System/scripts/drawdown_guard.py` وجود دارد که نسخهٔ زندهٔ
enforcer است (توابعِ `evaluate`/`build_alert`/`observe`/`enforce_action`)، در حالی که
این نسخهٔ `_ops/budget/` فقط `verdict`/`shadow_count` دارد و صفر صداکنندهٔ تولیدی
است (تأییدِ مستقلِ فازِ ۶ اسکنِ ۰۸-۰۷). این دو APIهای متفاوت و صفر overlap دارند —
«کدام canonical» و سرنوشتِ این نسخه (ادغام / آرشیو / ماندن به‌عنوانِ نمونهٔ سایه)
سؤالِ بازِ مالک است (در AGENT_QUESTIONS.md ثبت شد). این کامنت فقط برایِ جلوگیری از
سردرگمیِ بعدی است: اگر دنبالِ enforcerِ زنده می‌گردی، در مسیرِ scripts/ است.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/budget
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import opslib  # noqa: E402

SCHEMA = "drawdown-shadow.v1"
FLAG = "HH_DRAWDOWN_ENFORCE"                      # فقط نوشتنِ سایه را روشن می‌کند؛ هرگز HALT ِ زنده
SPIKE_DEFAULT = 25.0                             # هم‌ترازِ budgets.yaml global.spike_pct
SHADOW_PATH = opslib.STATE_DIR / "budget" / "drawdown-shadow.jsonl"


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def spike_threshold_pct() -> float:
    """آستانهٔ kill-switch از `budgets.yaml → global.spike_pct` (config-only، پیش‌فرض ۲۵)."""
    try:
        b = opslib.load_budgets()
        v = (b.get("global") or {}).get("spike_pct")
        v = float(v)
        if math.isfinite(v) and v > 0:
            return v
    except Exception:  # noqa: BLE001 — نبودِ config/عددِ خراب → پیش‌فرضِ محافظه‌کار
        pass
    return SPIKE_DEFAULT


def verdict(drawdown_pct, threshold_pct: float | None = None) -> dict:
    """وردیکتِ خالص (بدونِ I/O، بدونِ side-effect). fail-closed روی ورودیِ نامعلوم.

    HALT اگر drawdown ≥ آستانه، یا اگر drawdown اندازه‌گیری‌ناپذیر باشد (محتاطانه)."""
    thr = float(threshold_pct) if threshold_pct is not None else spike_threshold_pct()
    try:
        dd = float(drawdown_pct)
    except (TypeError, ValueError):
        dd = None
    if dd is None or not math.isfinite(dd):
        return {"halt": True, "reason": "fail-closed: drawdownِ اندازه‌گیری‌ناپذیر",
                "drawdown_pct": None, "threshold_pct": thr, "measurable": False}
    halt = dd >= thr
    return {"halt": halt,
            "reason": (f"drawdown {dd:.2f}% ≥ آستانهٔ {thr:.2f}%" if halt
                       else f"drawdown {dd:.2f}% < آستانهٔ {thr:.2f}%"),
            "drawdown_pct": dd, "threshold_pct": thr, "measurable": True}


def shadow_count(drawdown_pct, threshold_pct: float | None = None,
                 *, out_path: Path | None = None) -> dict:
    """وردیکت را حساب کن و — فقط با فلگ — یک would-halt در سینکِ سایه ثبت کن.
    **هرگز چیزی را زنده HALT نمی‌کند** (`enforced_live=False` همیشه)."""
    v = verdict(drawdown_pct, threshold_pct)
    rec = {"ts": opslib.now_iso(), "schema": SCHEMA, "mode": "shadow-count",
           "enforced_live": False,          # ثابت — این ماژول هرگز اکشنِ زنده نمی‌سازد
           "would_halt": v["halt"], **v}
    if _truthy(FLAG):
        path = out_path or SHADOW_PATH
        try:
            opslib.append_jsonl(path, rec)
            rec["_persisted"] = str(path)
        except Exception as e:  # noqa: BLE001
            rec["_persist_error"] = str(e)
    return rec


if __name__ == "__main__":
    # دموِ read-only: چند drawdown نمونه در برابرِ آستانهٔ config
    for dd in (5, 24.9, 25, 40, float("nan"), None):
        print(json.dumps(shadow_count(dd), ensure_ascii=False))
