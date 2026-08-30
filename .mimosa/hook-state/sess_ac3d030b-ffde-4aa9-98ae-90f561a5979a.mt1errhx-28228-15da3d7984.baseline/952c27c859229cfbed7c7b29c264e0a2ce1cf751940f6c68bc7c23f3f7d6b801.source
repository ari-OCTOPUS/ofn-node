#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prescription_gate.py — گیت تجویز دکتر (فاز ۴ MEGA-FINISH-ALL-v1).

قرارداد: هر تجویز باید فرضیهٔ علّیِ ابطالپذیر + شرط ابطال + هزینه + rollback +
شاهد داشته باشد؛ B0 هرگز اینجا تجویز نمیشود (→ صف مالک). دکتر خودش patch نمیزند
— فقط تجویز میدهد و به LAB میسپارد.

خروجی همیشه MEASURED؛ هیچ VERIFIED.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

SCHEMA = "prescription-gate.v1"
ALLOWED_ZONES = ("B1", "B2")
REQUIRED = ("observed_symptom", "causal_hypothesis", "falsification_condition",
            "rollback", "evidence_refs")
MUTATION_REQUIRED = ("target_path", "target_zone", "description")


@dataclass(frozen=True)
class CostCap:
    tokens: float = 10000.0
    calls: int = 5
    risk_weight: float = 5.0
    time_s: float = 600.0


def validate(prescription: dict, cap: CostCap = CostCap()) -> dict:
    """اعتبارسنجی ساختاری. هیچ استثنا بیرون نمیرود."""
    p = prescription or {}
    missing = [k for k in REQUIRED if not p.get(k)]
    mut = p.get("proposed_mutation") or {}
    mut_missing = [k for k in MUTATION_REQUIRED if not mut.get(k)]
    zone = str(mut.get("target_zone") or "")
    cost = p.get("expected_cost") or {}
    try:
        c_tokens = float(cost.get("tokens") or 0)
        c_calls = int(cost.get("calls") or 0)
        c_risk = float(cost.get("risk_weight") or 0)
        c_time = float(cost.get("time_s") or 0)
    except (TypeError, ValueError):
        c_tokens = c_calls = c_risk = c_time = -1.0
    cost_ok = (0 < c_tokens <= cap.tokens and 0 <= c_calls <= cap.calls
               and 0 <= c_risk <= cap.risk_weight and 0 < c_time <= cap.time_s)
    if missing or mut_missing:
        return {"schema": SCHEMA, "grade": "MEASURED", "valid": False,
                "reason": "missing-fields", "missing": missing + mut_missing}
    if zone not in ALLOWED_ZONES:
        return {"schema": SCHEMA, "grade": "MEASURED", "valid": False,
                "zone": zone,
                "reason": ("owner-queue" if zone == "B0" else "unknown-zone") + f":{zone}",
                "note": "B0 هرگز در این گیت تجویز نمیشود — صف مالک"}
    if not cost_ok:
        return {"schema": SCHEMA, "grade": "MEASURED", "valid": False,
                "reason": "cost-over-cap", "cost": {"tokens": c_tokens, "calls": c_calls,
                                                    "risk_weight": c_risk, "time_s": c_time}}
    return {"schema": SCHEMA, "grade": "MEASURED", "valid": True, "zone": zone,
            "reason": "ok", "cost": {"tokens": c_tokens, "calls": c_calls,
                                     "risk_weight": c_risk, "time_s": c_time}}


def run_falsifier(prescription: dict, snapshot: dict | None = None) -> dict:
    """اجرای شرط ابطال روی snapshot. شرط ساده: {"metric","threshold","direction"}.

    direction: "lt" = متغیر باید زیر آستانه باشد؛ "gt" = بالای آستانه.
    شرطِ غیرقابلارزیابی (بدون snapshot یا فرمت ناشناخته) = "not-evaluable" — یعنی
    ابطال «ندیده» است؛ این خودش یک نتیجه است نه پاس.
    """
    cond = (prescription or {}).get("falsification_condition")
    if isinstance(cond, str) and not cond:
        return {"falsified": None, "status": "no-condition"}
    if isinstance(cond, dict):
        metric = cond.get("metric")
        thr = cond.get("threshold")
        direction = str(cond.get("direction") or "lt")
        if not snapshot or metric not in (snapshot or {}):
            return {"falsified": None, "status": "not-evaluable",
                    "reason": f"metric '{metric}' not in snapshot"}
        try:
            val = float(snapshot[metric])
            thr = float(thr)
        except (TypeError, ValueError):
            return {"falsified": None, "status": "not-evaluable", "reason": "bad-types"}
        falsified = (val < thr) if direction == "lt" else (val > thr)
        return {"falsified": falsified, "status": "evaluated", "metric": metric,
                "value": val, "threshold": thr, "direction": direction}
    return {"falsified": None, "status": "not-evaluable", "reason": "unknown-condition-format"}


def receipt(prescription: dict) -> dict:
    canon = json.dumps({"rx": prescription}, ensure_ascii=False, sort_keys=True)
    import hashlib
    return {"schema": SCHEMA, "grade": "MEASURED", "ts": time.time(),
            "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "prescription_hash": hashlib.sha256(canon.encode("utf-8")).hexdigest()[:24]}
