"""equation_advice.py — فاز J: اتصال خودکار معادلات به‌صورت مشاهده‌گر/توصیه فقط.

برچسب اجباری برای هر خروجی:
    equation_advice_only = True
    decision_effect      = False
    apply_effect         = False

معادلات فقط «نظر» می‌دهند؛ هیچ تصمیمی را تغییر نمی‌دهند. fail-soft مطلق:
هر فایل state غایب/خراب → آن معادله skip می‌شود، نه crash.
بدون IO به‌جز خواندن state. هیچ فایل قفل‌شده‌ای را لمس نمی‌کند.
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

ADVICE_SCHEMA = "equation-advice.v1"

# نام‌های معادلات کانونی (برای `equations_consulted`)
EQ_PAIN = "nociceptor-pain"
EQ_CONTROL = "living-beat-control"
EQ_SIGMA = "spectral-sigma-legacy"
EQ_SIGMA_V2 = "spectral-connectivity-v2"
EQ_PHI = "phi-accrual"
EQ_BCM = "bcm"


def _read_json(rel: str) -> dict | None:
    p = STATE_DIR / rel
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def _read_jsonl_tail(rel: str, n: int = 3) -> list[dict]:
    p = STATE_DIR / rel
    out: list[dict] = []
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines[-n:]:
            if line.strip():
                try:
                    d = json.loads(line)
                    if isinstance(d, dict):
                        out.append(d)
                except ValueError:
                    continue
    except OSError:
        pass
    return out


def _pain_signal(org: dict | None) -> dict | None:
    """معادلهٔ درد (nociceptor) — فقط مشاهده. threshold 0.7 تاریخی."""
    if not org:
        return None
    pa = org.get("pain_assessment")
    if not isinstance(pa, dict):
        return None
    pain = pa.get("pain")
    if pain is None:
        return None
    try:
        pain = float(pain)
    except (TypeError, ValueError):
        return None
    return {
        "eq": EQ_PAIN,
        "value": round(pain, 3),
        "threshold": 0.7,
        "advice": "slow_down" if pain > 0.7 else "continue",
    }


def _control_signal(org: dict | None) -> dict | None:
    """قانون کنترل Living-Beat — از ORGANISM-STATE (math_control یا period)."""
    if not org:
        return None
    mc = org.get("math_control")
    if not isinstance(mc, dict):
        return None
    period = mc.get("period_s")
    if period is None:
        return None
    try:
        period = float(period)
    except (TypeError, ValueError):
        return None
    return {
        "eq": EQ_CONTROL,
        "value": round(period, 2),
        "unit": "s",
        "advice": "slow_down" if period >= 600 else "continue",
    }


def _sigma_signal(org: dict | None) -> dict | None:
    """σ legacy (طیف لاپلاسین) — فقط مشاهده. σ≈1 = بحرانیت."""
    if not org:
        return None
    rep = org.get("replication")
    sig = None
    if isinstance(rep, dict):
        sig = rep.get("sigma")
    if sig is None:
        # replication-latest.json جدا
        rep2 = _read_json("replication-latest.json")
        if rep2:
            sig = (rep2.get("sigma") or {}).get("sigma_effective")
    if sig is None:
        return None
    try:
        sig = float(sig)
    except (TypeError, ValueError):
        return None
    return {
        "eq": EQ_SIGMA,
        "value": round(sig, 3),
        "advice": "slow_down" if abs(sig - 1.0) < 0.3 else "continue",
    }


def _phi_signal() -> dict | None:
    """phi-accrual — از leg_clock آخرین حالت. فقط مشاهده."""
    rows = _read_jsonl_tail("leg_clock.jsonl", 3)
    if not rows:
        return None
    last = rows[-1]
    phi = last.get("vitality_phi")
    state = last.get("state")
    if phi is None and state is None:
        return None
    return {
        "eq": EQ_PHI,
        "value": round(float(phi), 2) if phi is not None else None,
        "leg_state": state,
        "advice": "slow_down" if state == "failed" else "continue",
    }


def equation_advice_snapshot() -> dict[str, Any]:
    """خلاصهٔ advice معادلات زنده. همیشه با برچسب advice-only.

    Returns:
        {schema, ts, equation_advice_only, decision_effect, apply_effect,
         equations_consulted, advice[]}
    """
    org = _read_json("ORGANISM-STATE.json")
    signals: list[dict] = []
    for fn in (_pain_signal, _control_signal, _sigma_signal, _phi_signal):
        try:
            s = fn(org)
            if s:
                signals.append(s)
        except Exception:  # noqa: BLE001 — یک معادله هرگز snapshot را نمی‌کشد
            continue
    consulted = [s["eq"] for s in signals]
    worst = "continue"
    if any(s.get("advice") == "slow_down" for s in signals):
        worst = "slow_down"
    return {
        "schema": ADVICE_SCHEMA,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "equation_advice_only": True,
        "decision_effect": False,
        "apply_effect": False,
        "may_authorize": False,
        "equations_consulted": consulted,
        "aggregate_advice": worst,
        "advice": signals,
    }


if __name__ == "__main__":
    print(json.dumps(equation_advice_snapshot(), ensure_ascii=False, indent=2))
