#!/usr/bin/env python3
"""heartstate.py — HeartState adapter (پیشنهاد #۱۲، URCP: «HEART = regulator نه commander»).

جمع‌کنندهٔ telemetry ِ read-only: سایهٔ قلب + استرس + عصب‌کشی → یک envelope واحد
(`heartstate.v1`). این ماژول فقط *می‌خواند* و — **فقط با فلگ** — در
`state/pulse/heartstate-latest.json` می‌نویسد. هرگز رفتار/کنترل نمی‌سازد (ADR-001
coupled-not-merged): «HEART از روزِ صفر telemetry بدهد، بدونِ commander شدن».

فلگ (هر کدام کافی است): env `HEARTSTATE_SHADOW=1`  یا  فایلِ `_ops/ACTIVATION-HEARTSTATE.flag`.
بدونِ فلگ: `persist()` هیچ نمی‌نویسد (no-op)، ولی `build()`/`read_latest()` همیشه کار می‌کنند.

$0 · stdlib · fail-soft (هر منبعِ غایب = بخشِ خالی، هرگز crash) · additive (فایلِ نو).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/heart
_OPS = _HERE.parent                              # _ops
for _p in (str(_OPS / "budget"), str(_OPS), str(_HERE), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402

SCHEMA = "heartstate.v1"
LATEST = opslib.STATE_DIR / "pulse" / "heartstate-latest.json"
_FLAG_ENV = "HEARTSTATE_SHADOW"
_FLAG_FILE = _OPS / "ACTIVATION-HEARTSTATE.flag"


def enabled() -> bool:
    """فقط با فلگِ صریحِ truthy نوشتن مجاز است (سایه، owner-gated).
    allowlist ِ truthy (case-insensitive) — تا FALSE/off/no تصادفاً فعال نکند."""
    if str(os.environ.get(_FLAG_ENV, "")).strip().lower() in ("1", "true", "yes", "on"):
        return True
    try:
        return _FLAG_FILE.exists()
    except OSError:
        return False


def _shadow() -> dict:
    try:
        import shadow  # _ops/heart/shadow.py
        return shadow.read_shadow_latest() or {}
    except Exception:  # noqa: BLE001 — منبعِ غایب هرگز adapter را نمی‌کشد
        return {}


def _stress() -> dict:
    try:
        import stress  # _ops/cortex/stress.py
        return stress.assess() or {}
    except Exception:  # noqa: BLE001
        return {}


def _innervation() -> dict:
    try:
        import innervation  # _ops/cortex/innervation.py
        return innervation.summary() or {}
    except Exception:  # noqa: BLE001
        return {}


def build() -> dict:
    """envelope ِ HeartState را از سه منبعِ زندهٔ state بساز (خالص، بدونِ نوشتن).

    نگاشتِ فیلدها دقیقاً طبقِ رکوردِ shadow.read_shadow_latest (ساختارِ تودرتو):
      velocity ← telemetry.velocity_per_hr · sigma ← signal.sigma_now
      · band ← setpoint.viable_band_{lo,hi} · wire_open ← production_wire.open
    نکتهٔ حیاتی: production_wire یک دیکشنری است (همیشه truthy) — پس باید `.open` خوانده
    شود، نه خودِ دیکشنری؛ وگرنه هر رکوردِ سایه دروغین «live» گزارش می‌شود (ریویوی خصمانه)."""
    sh, st, inn = _shadow(), _stress(), _innervation()
    pw = sh.get("production_wire") or {}
    sig = sh.get("signal") or {}
    tel = sh.get("telemetry") or {}
    sp = sh.get("setpoint") or {}
    wire_open = bool(pw.get("open"))     # قلبِ واقعاً live؟ (باید False/سایه بماند تا رأیِ مالک)
    dead = inn.get("dead_spots") or []
    return {
        "ts": opslib.now_iso(),
        "schema": SCHEMA,
        "epistemic": "access-only telemetry — read-only، regulator نه commander",
        "shadow": {
            "velocity": tel.get("velocity_per_hr"),
            "sigma": sig.get("sigma_now"),
            "period_s": sh.get("period_s"),
            "mode": sh.get("mode"),
            "band": [sp.get("viable_band_lo"), sp.get("viable_band_hi")] if sp else None,
            "wire_open": wire_open,
        },
        "stress": {
            "organism": st.get("organism_stress"),
            "level": st.get("level"),
            "in_fear": st.get("in_fear") or [],
        },
        "innervation": {
            "coverage_pct": inn.get("coverage_pct"),
            "heart_period_s": inn.get("heart_period_s"),
            "dead_count": len(dead),
            "dead_spots": dead[:8],
        },
        "shadow_only": not wire_open,
    }


def persist() -> dict:
    """envelope را بساز و — فقط اگر فلگ روشن بود — در heartstate-latest.json بنویس.
    خروجی همیشه = envelope (+ کلیدِ `written` که می‌گوید نوشت یا no-op بود)."""
    env = build()
    env["written"] = False
    if not enabled():
        return env                                   # سایه‌ی خاموش: هیچ نوشتنی
    try:
        # written پیش از serialize ست می‌شود تا نسخهٔ روی دیسک هم صادق باشد —
        # قبلاً فایل همیشه «written: false» حمل می‌کرد (dump قبل از فلگ).
        env["written"] = True
        LATEST.parent.mkdir(parents=True, exist_ok=True)
        LATEST.write_text(json.dumps(env, ensure_ascii=False, indent=1), "utf-8")
    except OSError:
        env["written"] = False                       # fail-soft
    return env


def read_latest() -> dict:
    try:
        return json.loads(LATEST.read_text("utf-8")) if LATEST.exists() else {}
    except (OSError, ValueError):
        return {}


if __name__ == "__main__":
    print(json.dumps(persist(), ensure_ascii=False, indent=2))
