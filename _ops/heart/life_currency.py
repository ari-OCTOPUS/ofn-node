#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""life_currency.py — واحدِ زندگی سه‌بعدی (فاز ۴ دستورالعمل ۲۰۲۶-08-16، D4/D7).

Life Currency = token + call + risk (سندِ LIFE-CURRENCY-AND-ORCHESTRATION §۱):
هر عضوِ کورتکس در هر beat سبز سهمی از استخرِ روزانه می‌گیرد؛ تبدیل به API با
نرخِ provider و وزنِ ریسکِ کلاسِ اقدام.

چرا این ماژول قلبِ دومی نمی‌سازد
────────────────────────────────
`cardiac.py::BeatBudget` سقفِ روزانهٔ ضربان را نگه می‌دارد و `budget_judge.py`
قاضیِ تخصیصِ CPU/API است. این ماژول جایگزین هیچ‌کدام نیست — لایهٔ ارزِ
اعتباریِ اعضاست که از همان `cardiac-budget.json` تغذیه می‌کند (تک‌نویسنده:
cardiac مالکِ سقف است؛ این‌جا فقط تخصیصِ سه‌بعدیِ سهم‌ها را می‌نویسد، در
`state/pulse/life-currency-latest.json`، پشتِ فلگِ خودش — پیش‌فرض dry-run).

پلهٔ رنگ (سند §۶): GREEN → تخصیصِ کامل · AMBER/YELLOW → نصف · RED → survival
فقط (organism + heart). رزروِ اضطراری ۲۰٪ (RESERVE_FLOOR) هرگز پخش نمی‌شود.
سقفِ سخت: تخصیصِ یک beat هرگز > ۲× سهمِ روزانهٔ آن beat (BUDGET_HARD_CAP).

addon-only · stdlib · total functions (هیچ استثنا بیرون نمی‌رود) · fail-soft.
"""
from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_LIFE_CURRENCY"
SCHEMA = "life-currency.v1"
LATEST_PATH = opslib.STATE_DIR / "pulse" / "life-currency-latest.json"

# ── نردبان اقدامات (D7) — هم‌خانوادهٔ taxonomy EFFECT_CLASSES اما مقیاسِ ارز ────
class ActionClass(IntEnum):
    A0 = 0  # observation
    A1 = 1  # sandbox reversible
    A2 = 2  # reversible change
    A3 = 3  # owner gate
    A4 = 4  # external effect
    A5 = 5  # money/commitment
    A6 = 6  # forbidden

RISK_WEIGHTS = {
    ActionClass.A0: 0.1,
    ActionClass.A1: 0.5,
    ActionClass.A2: 2.0,
    ActionClass.A3: 5.0,
    ActionClass.A4: 10.0,
    ActionClass.A5: 50.0,
    ActionClass.A6: float('inf'),
}

# ۱۱ عضو کورتکس — همان هویتِ cortex-state.json (single source: membership)
CORTEX_MEMBERS = [
    "organism", "heart", "producers", "work_pump",
    "doctor_setpoint", "governor", "sigma", "fitness",
    "school", "reconcile", "fourd_system",
]

# ۱۰ پای هیئت‌مدیره (نقشهٔ پاها — دسترسی مشترک، تقسیم بر اساس نوع تصمیم)
BOARD_LEGS = [
    "lead", "ziman", "mining", "crypto", "accounting",
    "studio_pf", "system", "knowledge", "cartographer", "mirror",
]

# نرخ تبدیل provider (توکن به ازای هر life_credit) — D5
PROVIDER_RATES = {
    "fugu": 1.0,
    "deepseek": 0.8,
    "glm": 0.9,
    "ollama": 0.1,
}

# خودمختاری بر اساس provider — D6 (کاهش پله‌ای)
PROVIDER_AUTONOMY = {
    "fugu": "execute",      # A0-A2 auto
    "deepseek": "execute",  # A0-A2 auto
    "glm": "propose",       # A0-A1 auto, A2→propose
    "ollama": "propose",    # A0-A1 auto, A2→propose
}

RESERVE_FLOOR_PCT = 0.20    # ۲۰٪ رزرو اضطراری (RESERVE_FLOOR)
DAILY_BUDGET_HARD_CAP_X = 2  # بیشینهٔ تخصیصِ هر beat = ۲× سهمِ روزانهٔ همان beat

# زیرِ RED فقط این اعضا نجات می‌یابند (سند §۶: «RED → survival فقط»)
SURVIVAL_MEMBERS = ("organism", "heart")

# هر life_credit چند call می‌خرد (سربارِ ثابتِ فراخوانی) — سند §۱: cost = tok×risk + overhead
CALL_COST = 10.0


@dataclass
class LifeBudget:
    """بودجهٔ سه‌بعدیِ یک عضو در یک beat."""
    member: str
    tokens: float
    calls: int
    risk_pool: float

    def as_dict(self) -> dict:
        return {"member": self.member, "tokens": round(self.tokens, 3),
                "calls": int(self.calls), "risk_pool": round(self.risk_pool, 3)}


@dataclass
class BudgetTransfer:
    """مبادلهٔ آزاد با لاگ — D4 (free_with_log؛ DEBT مجاز است)."""
    from_member: str
    to_member: str
    tokens: float
    calls: int
    trace_id: str
    reason: str = ""
    timestamp: str = ""

    def as_dict(self) -> dict:
        return {"from": self.from_member, "to": self.to_member,
                "tokens": round(self.tokens, 3), "calls": int(self.calls),
                "trace_id": self.trace_id, "reason": self.reason,
                "timestamp": self.timestamp}


# ── توابعِ کل (هیچ‌کدام استثنا نمی‌دهند) ───────────────────────────────────────

def _f(v, default=0.0) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return default
    return x if math.isfinite(x) else default


def enabled() -> bool:
    """env صریح برنده؛ وگرنه رأیِ tracked (owner-verdicts.yaml) — هم‌قراردادِ
    wiring.effective_flag، بدونِ importِ کاملِ wiring (قلبِ سبک بماند)."""
    if FLAG in os.environ:
        return str(os.environ[FLAG]).strip().lower() in ("1", "true", "yes", "on")
    try:
        import owner_verdicts as _ov   # noqa: WPS433 — lazy، _ops روی sys.path
        v = _ov.get(FLAG)
        return str(v or "0").strip().lower() in ("1", "true", "yes", "on")
    except Exception:  # noqa: BLE001 — رأیِ fallback نباید قلب را بکشد
        return False


def color_scale(color: str) -> float:
    """ضریبِ رنگ: GREEN=1.0 · AMBER/YELLOW=0.5 · RED=survival-marker(-1)."""
    c = str(color or "").strip().upper()
    if c == "GREEN":
        return 1.0
    if c in ("AMBER", "YELLOW"):
        return 0.5
    if c == "RED":
        return -1.0
    return 0.0   # ناشناخته → تخصیص نکن (fail-closed به سمتِ صفر، نه حدس)


def daily_pool(*, daily_cap=None) -> dict:
    """استخرِ روزانه از cardiac-budget.json (تک‌نویسنده: cardiac). fail-soft."""
    try:
        if daily_cap is None:
            cb = json.loads((opslib.STATE_DIR / "cardiac-budget.json").read_text("utf-8"))
            daily_cap = cb.get("daily_cap")
    except (OSError, ValueError):
        daily_cap = None
    return {"daily_cap": _f(daily_cap, 0.0), "known": _f(daily_cap, 0.0) > 0}


def allocate_beat(color: str, *, daily_cap: float, period_s: float = 124.0,
                  members=None) -> dict:
    """تخصیصِ سهمِ یک beat به اعضا. total: هر ورودی → خروجیِ معتبر یا خالی.

    ناوردی‌ها:
      · Σ tokens ≤ سهمِ beat × (1 − RESERVE_FLOOR) — رزرو هرگز پخش نمی‌شود
      · زیرِ RED فقط SURVIVAL_MEMBERS
      · سقفِ سخت: تخصیص ≤ DAILY_BUDGET_HARD_CAP_X × سهمِ beat
      · مخرج/فهرستِ خالی → تخصیصِ خالی، نه استثنا"""
    scale = color_scale(color)
    cap = max(0.0, _f(daily_cap, 0.0))
    period = max(1.0, _f(period_s, 124.0))
    if scale == 0.0 or cap <= 0.0:
        return {"schema": SCHEMA, "color": str(color or "").upper(), "scale": scale,
                "beat_pool": 0.0, "reserve": 0.0, "members": {}, "hard_cap": 0.0,
                "reasons": ["color ناشناخته یا سقفِ روزانه صفر — تخصیص نکرد"]}
    beats_per_day = 86400.0 / period
    beat_share = cap / beats_per_day
    hard_cap = DAILY_BUDGET_HARD_CAP_X * beat_share
    # |scale|: RED (-1) یعنی «سرِ پایینِ پله» نه استخرِ منفی — survival از همین
    # استخرِ کوچک‌شده تغذیه می‌شود؛ فهرستِ اعضا پایین‌تر محدود می‌شود.
    pool = min(beat_share * abs(scale), hard_cap)
    reserve = pool * RESERVE_FLOOR_PCT
    distributable = pool - reserve
    if distributable <= 0.0:
        return {"schema": SCHEMA, "color": str(color).upper(), "scale": scale,
                "beat_pool": round(pool, 3), "reserve": round(reserve, 3),
                "members": {}, "hard_cap": round(hard_cap, 3),
                "reasons": ["استخرِ قابل‌توزیع صفر (رنگ/سقف)"]}
    names = [m for m in (members or CORTEX_MEMBERS) if isinstance(m, str) and m.strip()]
    if scale < 0.0:   # RED → survival فقط
        names = [m for m in names if m in SURVIVAL_MEMBERS] or list(SURVIVAL_MEMBERS)
    share = distributable / len(names)
    out = {}
    for m in names:
        b = LifeBudget(member=m, tokens=share,
                       calls=int(share // CALL_COST) if CALL_COST > 0 else 0,
                       risk_pool=share * RISK_WEIGHTS[ActionClass.A2])
        out[m] = b.as_dict()
    return {"schema": SCHEMA, "color": str(color).upper(), "scale": scale,
            "beat_pool": round(pool, 3), "reserve": round(reserve, 3),
            "hard_cap": round(hard_cap, 3), "members": out, "reasons": []}


def cost(tokens_used: float, action_class: ActionClass, calls: int = 1) -> float:
    """cost = token_used × risk_weight + call_overhead (سند §۱). A6 → inf."""
    w = RISK_WEIGHTS.get(action_class, RISK_WEIGHTS[ActionClass.A6])
    if math.isinf(w):
        return math.inf
    return _f(tokens_used) * w + max(0, int(calls)) * 1.0


def _read_color() -> tuple:
    """رنگِ فعلیِ داور + period از ORGANISM-STATE.json (fail-soft)."""
    try:
        st = json.loads((opslib.STATE_DIR / "ORGANISM-STATE.json").read_text("utf-8"))
        arb = st.get("arbiter") or {}
        return str(arb.get("color") or ""), _f(arb.get("effective_period_s"), 124.0)
    except (OSError, ValueError):
        return "", 124.0


def plan(*, color: str = None, daily_cap: float = None, period_s: float = None,
         members=None) -> dict:
    """نقشهٔ تخصیصِ همین لحظه — فقط‌خواندنی، چیزی نمی‌نویسد."""
    c = color if color is not None else _read_color()[0]
    if period_s is None:
        period_s = _read_color()[1]
    dp = daily_pool(daily_cap=daily_cap)
    alloc = allocate_beat(c, daily_cap=dp["daily_cap"] if dp["known"] else 0.0,
                          period_s=period_s, members=members)
    alloc["ts"] = opslib.now_iso()
    alloc["daily_cap"] = dp["daily_cap"]
    alloc["dry_run"] = not enabled()
    return alloc


def emit(p: dict | None = None) -> dict:
    """نقشه را بنویسد — فقط با فلگ (همان الگوی budget_judge.emit). dry-run → صفر نوشتن."""
    p = p if isinstance(p, dict) else plan()
    if not enabled():
        return {"ok": True, "written": False, "plan": p}
    try:
        LATEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = LATEST_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(p, ensure_ascii=False, indent=1), "utf-8")
        os.replace(tmp, LATEST_PATH)
    except OSError:
        return {"ok": False, "written": False, "plan": p}
    return {"ok": True, "written": True, "plan": p}


def tick(beat: int = 0) -> dict:
    """نقطهٔ ورودِ beat (organism loop): نقشه + نوشتنِ پشتِ فلگ. هرگز raise نمی‌کند."""
    try:
        p = plan()
        p["beat"] = int(beat or 0)
        res = emit(p)
        try:   # ثبتِ رویداد تخصیص (R8 — بی‌trace هیچ چیز ثبت نمی‌شود)
            import events as _ev   # noqa: WPS433
            _ev.emit("system.heartbeat", "life_currency", status="ok",
                     summary=f"life-currency plan color={p.get('color')} "
                             f"members={len(p.get('members') or {})} dry_run={p.get('dry_run')}",
                     trace_id=f"lc-{int(beat or 0)}",
                     correlation_id=f"lc-{int(beat or 0)}",
                     approval_state="none")
        except Exception:  # noqa: BLE001
            pass
        return res
    except Exception:  # noqa: BLE001 — ارز هرگز تیک را نمی‌کشد
        return {"ok": False, "written": False, "error": "failsoft"}


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps(plan(), ensure_ascii=False, indent=1))
