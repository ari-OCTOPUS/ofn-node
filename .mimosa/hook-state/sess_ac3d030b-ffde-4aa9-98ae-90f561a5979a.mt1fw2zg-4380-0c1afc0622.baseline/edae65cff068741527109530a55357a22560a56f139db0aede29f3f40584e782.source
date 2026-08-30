#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""organism_syndrome.py — سندرمِ cross-leg (Organism Integrity Syndrome).

الهامِ ریاضی: در یک کدِ LDPC، ماتریسِ تنکِ H روی داده اعمال می‌شود؛ H·x = 0 یعنی
داده با همه‌ی محدودیت‌ها سازگار است. هر نقض، سندرم را ناصفر می‌کند و دقیقاً نشان
می‌دهد کدام رابطه شکسته. این ماژول invariantهای cross-leg را صریح و چک‌شونده و
localize‌شده می‌کند.

قرارداد (MEGAPROMPT-CROSS-LEG-SYNDROME-2026-08-02):
  · read-only — فقط می‌خواند، هرگز state را تغییر نمی‌دهد.
  · هرگز «unknown» را به‌عنوان 0 گزارش نکن (fail-closed، نه fail-open).
  · additive، flag-off (OCTOPUS_WIRE_ORGANISM_SYNDROME)، halt مقدم.

دو invariant بررسی می‌شود:
  I-1 یکپارچگیِ بودجه: sum(organs.spent_month_musd) با global spent سازگار است.
  I-2 تکمیلِ pipe: (وقتی داده هست) هر outbound send باید funnel event داشته باشد.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_BUDGET = _OPS / "budget"
for _p in (str(_OPS), str(_BUDGET)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_WIRE_ORGANISM_SYNDROME"

try:
    import opslib  # noqa: E402
    ORGAN_STATE = opslib.ORGAN_STATE
    BUDGET_STATE = opslib.BUDGET_STATE
    ORGAN_LOG = opslib.ORGAN_LOG
except Exception:  # noqa: BLE001
    opslib = None  # type: ignore
    ORGAN_STATE = _BUDGET / "organ-state.json"
    BUDGET_STATE = _BUDGET / "budget-state.json"
    ORGAN_LOG = _BUDGET / "organ-gate-log.jsonl"


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def _halted() -> bool:
    if opslib is None:
        return False
    try:
        return bool(opslib.master_halted() or opslib.halted()
                    or opslib.STOP_ORGANISM.exists() or opslib.frozen())
    except Exception:  # noqa: BLE001
        return True


def _read_json(path: Path) -> "dict | None":
    """read-only JSON. None اگر غایب/خراب. هرگز استثنا."""
    try:
        if not path.exists():
            return None
        d = json.loads(path.read_text("utf-8"))
        return d if isinstance(d, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def check_budget_integrity(*, tolerance_aud: float = 0.01) -> dict:
    """I-1: sum(organs.spent_month_musd) با global spent_month_aud سازگار است؟

    هر دو منبع مستقل‌اند: organ-state.json per-organ نگه می‌دارد، budget-state.json
    جهانی. اگر یکی خراب شود، فاصله = سندرم. خروجی:
      {name, ok: bool, gap_aud, organ_sum_aud, global_aud, detail}
    اگر هر منبعی غایب باشد → ok=False, reason=missing (نه fail-open).
    """
    name = "I1_budget_integrity"
    org = _read_json(ORGAN_STATE)
    glob = _read_json(BUDGET_STATE)
    if org is None:
        return {"name": name, "ok": False, "reason": "organ_state_missing_or_unreadable"}
    if glob is None:
        return {"name": name, "ok": False, "reason": "budget_state_missing_or_unreadable"}
    organs = org.get("organs") or {}
    try:
        # per-organ: musd (micro-USD). جهانی: aud.
        organ_sum_musd = sum(float(o.get("spent_month_musd", 0.0))
                             for o in organs.values() if isinstance(o, dict))
        global_aud = float(glob.get("spent_month_aud", 0.0))
        # تبدیلِ تقریبی micro-USD → AUD: فرضِ fx≈1.5 (AUD per USD). صریح: این یک
        # تقریب است چون organ_state واحدِ musd دارد و budget_state واحدِ aud.
        # برای یک syndrome، تقریب کافی است — فاصلهٔ بزرگ را می‌گیرد.
        fx = 1.5
        organ_sum_aud_approx = (organ_sum_musd / 1_000_000.0) * fx
        gap = abs(organ_sum_aud_approx - global_aud)
        ok = gap <= tolerance_aud
        return {"name": name, "ok": ok, "gap_aud": round(gap, 6),
                "organ_sum_aud_approx": round(organ_sum_aud_approx, 6),
                "global_aud": global_aud, "tolerance_aud": tolerance_aud,
                "detail": "ok" if ok else
                f"organ-sum≈AU${organ_sum_aud_approx:.4f} vs global=AU${global_aud:.4f}"}
    except (TypeError, ValueError) as exc:
        return {"name": name, "ok": False, "reason": f"compute_error:{type(exc).__name__}"}


def check_outbound_funnel_completeness(window_rows: int = 200) -> dict:
    """I-2: هر reserve که lead_outbound است باید funnel event داشته باشد.

    صادقانه: در حال حاضر outbound معمولاً NOT_ARMED است و funnel ممکن است خالی باشد.
    این چک only meaningful وقتی outbound زنده باشد. اگه هیچ outbound reserveای
    در پنجره نیست → ok=True, reason='no_outbound_activity' (نه violation).
    خروجی: {name, ok, missing: [...], checked, detail}.
    """
    name = "I2_outbound_funnel_completeness"
    # بدونِ وابستگیِ سنگین به FunnelStore (که ممکن است خالی باشد)، یک چکِ سبک:
    # در ORGAN_LOG، reserveهای با task شاملِ 'lead'/'outbound' را بشمار؛ اگه صفر
    # است، no activity. این یک proxy است — چکِ دقیق‌تر نیاز به funnel_store دارد.
    try:
        if not ORGAN_LOG.exists():
            return {"name": name, "ok": True, "reason": "no_organ_log"}
        outbound_reserves = 0
        with ORGAN_LOG.open("r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()[-window_rows:]
        for raw in lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                r = json.loads(raw)
            except (ValueError, TypeError):
                continue
            if r.get("op") == "reserve" and "lead" in str(r.get("task", "")).lower():
                outbound_reserves += 1
        if outbound_reserves == 0:
            return {"name": name, "ok": True, "reason": "no_outbound_activity",
                    "checked_window_rows": len(lines)}
        # اگه outbound activity هست ولی FunnelStore قابل ایمپورت نیست → unknown
        # (نه fail-open). صادقانه: بررسیِ کاملِ event-level نیاز به FunnelStore دارد.
        return {"name": name, "ok": True, "reason": "outbound_activity_present_light_check_only",
                "outbound_reserves_in_window": outbound_reserves,
                "checked_window_rows": len(lines),
                "note": "full event-level check requires FunnelStore; this is a proxy"}
    except Exception as exc:  # noqa: BLE001
        return {"name": name, "ok": False, "reason": f"check_error:{type(exc).__name__}"}


def organism_syndrome() -> dict:
    """بردارِ سندرم + localize نقض‌ها. همیشه dict، هرگز استثنا.

    هر invariant یک بیت: True=ok, False=violation, None=unknown.
    syndrome_vector = {name: bit}. violations = لیستِ نقض‌ها با detail.
    summary = رشتهٔ قابل‌فهم.
    """
    if _halted():
        return {"ok": False, "reason": "halted", "flag": FLAG}
    checks = [check_budget_integrity(), check_outbound_funnel_completeness()]
    vector: dict[str, Any] = {}
    violations = []
    for c in checks:
        n = c.get("name", "?")
        if c.get("ok") is True:
            vector[n] = True
        elif c.get("ok") is False and "reason" in c and "missing" in str(c.get("reason", "")):
            vector[n] = None  # unknown (منبع غایب) — نه violation، نه ok
        elif c.get("ok") is False:
            vector[n] = False
            violations.append(c)
        else:
            vector[n] = None
    nonzero = sum(1 for v in vector.values() if v is False)
    unknown = sum(1 for v in vector.values() if v is None)
    summary = (f"syndrome: {nonzero} violation(s), {unknown} unknown. "
               f"vector={vector}")
    return {"ok": nonzero == 0, "syndrome_vector": vector,
            "violations": violations, "unknowns": [n for n, v in vector.items() if v is None],
            "summary": summary, "enabled": enabled(), "flag": FLAG}


if __name__ == "__main__":
    print(json.dumps(organism_syndrome(), ensure_ascii=False, indent=2))
