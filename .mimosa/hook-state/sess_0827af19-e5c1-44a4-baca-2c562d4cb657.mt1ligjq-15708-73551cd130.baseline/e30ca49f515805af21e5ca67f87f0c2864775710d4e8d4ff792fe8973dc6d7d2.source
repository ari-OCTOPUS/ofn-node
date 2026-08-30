"""shadow_influence.py — فاز K: دو مسیر (واقعی vs سایه)، فقط ثبت اختلاف.

مسیر واقعی: تصمیم فعلی ارگانیسم (از state).
مسیر سایه:  همان ورودی‌ها + advice معادلات → تصمیم فرضی.
هیچ‌کدام اثر نمی‌گذارد: `applied` همیشه False. فقط divergence ثبت می‌شود.

خروجی: JSONL در `state/shadow-influence/divergence.jsonl`.
fail-soft مطلق. هیچ فایل قفل‌شده‌ای لمس نمی‌شود.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
STATE_DIR = Path(os.environ.get("OCTOPUS_STATE_DIR", str(_OPS / "state")))
OUT_DIR = STATE_DIR / "shadow-influence"
DIVERGENCE = OUT_DIR / "divergence.jsonl"

SHADOW_SCHEMA = "shadow-influence.v1"


def _read_json(rel: str) -> dict | None:
    p = STATE_DIR / rel
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def real_decision_from_state() -> dict[str, Any]:
    """تصمیم واقعی فعلی از ORGANISM-STATE (فقط خواندن)."""
    org = _read_json("ORGANISM-STATE.json") or {}
    beat = org.get("beat")
    halted = bool(org.get("halted"))
    ps = bool(org.get("protective_skip"))
    if halted:
        decision = "halt"
    elif ps:
        decision = "protective_skip"
    else:
        decision = "continue"
    return {"tick": beat, "real_decision": decision, "halted": halted,
            "protective_skip": ps}


def shadow_decision_from_advice() -> dict[str, Any]:
    """تصمیم فرضی از advice معادلات (فاز J) — فقط سایه."""
    try:
        import sys
        if str(_HERE) not in sys.path:
            sys.path.insert(0, str(_HERE))
        import equation_advice as _ea  # noqa: WPS433
        adv = _ea.equation_advice_snapshot()
        shadow = adv.get("aggregate_advice") or "continue"
        return {
            "shadow_decision": shadow,
            "equations_consulted": adv.get("equations_consulted") or [],
            "equation_reason": "; ".join(
                f"{s.get('eq')}={s.get('value')}->{s.get('advice')}"
                for s in (adv.get("advice") or [])
            ) or "no-equation-signal",
        }
    except Exception as exc:  # noqa: BLE001
        return {"shadow_decision": "unknown",
                "equations_consulted": [],
                "equation_reason": f"advice-unavailable:{type(exc).__name__}"}


def evaluate_shadow() -> dict[str, Any]:
    """یک نقطهٔ Shadow Influence — divergence واقعی vs سایه."""
    real = real_decision_from_state()
    sh = shadow_decision_from_advice()
    divergence = (real.get("real_decision") != sh.get("shadow_decision")
                  and sh.get("shadow_decision") not in (None, "unknown"))
    rec = {
        "schema": SHADOW_SCHEMA,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tick": real.get("tick"),
        "real_decision": real.get("real_decision"),
        "shadow_decision": sh.get("shadow_decision"),
        "equation_reason": sh.get("equation_reason"),
        "equations_consulted": sh.get("equations_consulted"),
        "divergence": bool(divergence),
        "applied": False,          # ← همیشه False در فاز K
        "may_authorize": False,
    }
    return rec


def record_divergence(rec: dict | None = None) -> dict[str, Any]:
    """append رکورد به JSONL (فقط این مسیر). fail-soft."""
    r = rec or evaluate_shadow()
    try:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with DIVERGENCE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        r["recorded"] = True
    except OSError:
        r["recorded"] = False
    return r


def count_records() -> int:
    try:
        if not DIVERGENCE.is_file():
            return 0
        return sum(1 for line in DIVERGENCE.read_text("utf-8", errors="replace")
                   .splitlines() if line.strip())
    except OSError:
        return 0


if __name__ == "__main__":
    import sys as _sys
    if "--probe" in _sys.argv[1:]:
        rec = record_divergence()
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        print(f"[records so far: {count_records()}]")
    else:
        print(json.dumps(evaluate_shadow(), ensure_ascii=False, indent=2))
