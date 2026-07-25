#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""c6_probes.py — C2 · رجیستریِ سنجه‌های read-only برای تولیدکنندهٔ صادقِ فرضیهٔ C6.

قیدِ صداقت: هر سنجه فقط count می‌زند؛ هیچ نتیجهٔ صنعتی/بهبودِ ساختگی تولید نمی‌کند.
خروجیِ نامشخص/کرش → count=-1 (هیچ فرضیه‌ای ساخته نشود). صفر شبکه/پول/اثرِ بیرونی؛
stdlib-only؛ fail-soft؛ هر wrapper خواندنی که را override می‌کند در finally برمی‌گردد.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

OPS = Path(__file__).resolve().parent


def _sys(p: Path) -> None:
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


_sys(OPS / "budget")
import opslib  # noqa: E402


def _load_self_audit_module():
    for p in (OPS / "cortex",):
        _sys(p)
    return importlib.import_module("self_audit")


def _probe_self_audit_redundant_reads() -> dict:
    mod = _load_self_audit_module()
    orig_read, orig_grep = mod._read, mod._grep
    calls = {"_read": 0, "_grep": 0}
    try:
        def counting_read(p):
            calls["_read"] += 1
            return orig_read(p)

        def counting_grep(p, needle):
            calls["_grep"] += 1
            return orig_grep(p, needle)

        mod._read = counting_read
        mod._grep = counting_grep
        mod.main()
        return {"count": calls["_read"], "unit": "read",
                "detail": f"self_audit.main() full-matrix reads={calls['_read']} grep={calls['_grep']}"}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "read",
                "detail": f"probe-failed:{type(e).__name__}"}
    finally:
        mod._read, mod._grep = orig_read, orig_grep


def _probe_rfc_duplicate_surplus() -> dict:
    try:
        rd = opslib.STATE_DIR / "c6" / "rfcs"
        if not rd.exists():
            return {"count": -1, "unit": "rfc",
                    "detail": "rfc dir غایب — قضاوت غیرممکن (هیچ فرضیه‌ای)"}
        rows = []
        for p in sorted(rd.glob("c6-*.json")):
            try:
                d = json.loads(p.read_text("utf-8"))
                hyp = str(d.get("hypothesis", "")).strip().lower()
                if hyp:
                    rows.append((p.name, hyp))
            except (OSError, ValueError):
                continue
        if not rows:
            return {"count": -1, "unit": "rfc",
                    "detail": "هیچ c6-*.json با hypothesis غیرخالی — قضاوت غیرممکن"}
        from collections import Counter
        counts = Counter(h for _, h in rows)
        max_n = max(counts.values()) if counts else 0
        surplus = sum(n - 1 for n in counts.values())
        return {"count": max_n, "unit": "rfc",
                "detail": (f"max_duplicate_hypothesis={max_n} surplus_rfc={surplus} "
                           f"files={len(rows)}")}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "rfc",
                "detail": f"probe-failed:{type(e).__name__}"}


def _probe_thesis_delta_self_sign() -> dict:
    """ردیفِ `delta-self` دفترِ تز: آیا Δ_self هنوز منفی است؟

    ادعا: مدلی با دسترسی به وضعیتِ درونیِ خود، آیندهٔ خود را بهتر از نسخهٔ کور
    پیش‌بینی می‌کند (Δ>0). اندازه‌گیریِ زنده تا امروز منفی است.
    count = تعدادِ نمونهٔ اخیر با Δ<=0. count==0 با nِ کافی ⇒ ادعا حرکت کرده.
    """
    try:
        vals: list[float] = []
        # استریمِ اختصاصیِ مسیرِ رویا (heart/shadow._append_thesis_measurement).
        # `pulse/heart-params-shadow.jsonl` عمداً چک نمی‌شود: شمایش فقط ۶ کلیدِ
        # باروگیرنده است و Δ در آن نیست — خواندنش nِ دروغین می‌ساخت.
        stream = opslib.STATE_DIR / "thesis" / "measurements.jsonl"
        if stream.exists():
            try:
                lines = stream.read_text("utf-8").splitlines()[-500:]
            except OSError:
                lines = []
            for ln in lines:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    d = json.loads(ln)
                except ValueError:
                    continue
                v = d.get("delta_self_live") if isinstance(d, dict) else None
                if isinstance(v, (int, float)):
                    vals.append(float(v))
        if len(vals) < 2:
            latest = opslib.STATE_DIR / "pulse" / "heart-shadow-latest.json"
            try:
                d = json.loads(latest.read_text("utf-8"))
                v = (d.get("telemetry") or {}).get("delta_self_live")
                if isinstance(v, (int, float)):
                    vals.append(float(v))
            except (OSError, ValueError, AttributeError):
                pass
        durable = len(vals)
        if durable < 2:
            # صداقت دربارهٔ نبودِ تاریخ: یک عکسِ لحظه‌ای «روند» نیست. count=-1 یعنی
            # قضاوت غیرممکن — نه صفرِ قلابی، نه n=1ِ گمراه‌کننده.
            snap = None
            try:
                d = json.loads((opslib.STATE_DIR / "pulse"
                                / "heart-shadow-latest.json").read_text("utf-8"))
                v = (d.get("telemetry") or {}).get("delta_self_live")
                snap = float(v) if isinstance(v, (int, float)) else None
            except (OSError, ValueError, AttributeError, TypeError):
                pass
            return {"count": -1, "unit": "sample",
                    "detail": (f"no-durable-history (durable_rows={durable}) — روند "
                               f"غیرقابل‌آزمون تا OCTOPUS_THESIS_MEASURE=1 روشن شود. "
                               f"عکسِ لحظه‌ای: {snap}")}
        neg = sum(1 for v in vals if v <= 0.0)
        mean = sum(vals) / len(vals)
        first_half = vals[:len(vals) // 2]
        second_half = vals[len(vals) // 2:]
        trend = (sum(second_half) / len(second_half)) - (sum(first_half) / len(first_half))
        return {"count": neg, "unit": "sample",
                "detail": (f"n={len(vals)} negative={neg} mean={mean:.6f} "
                           f"latest={vals[-1]:.6f} trend={trend:+.6f} "
                           f"(Δ<=0 ⇒ دسترسیِ درونی بدتر از کوری؛ trend>0 ⇒ به سمتِ مثبت)")}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "sample", "detail": f"probe-failed:{type(e).__name__}"}


def _probe_thesis_phi_saturation() -> dict:
    """ردیفِ `phi-liveness` دفترِ تز: آیا phi هنوز به سقفِ محاسباتیِ خودش می‌چسبد؟

    اشباع = اندازه‌گیری نیست. count = تعدادِ لِگی که phi>=phi_dead دارد.
    count==0 ⇒ آرتیفکت دیگر بازتولید نمی‌شود (فیکس گرفته).
    """
    try:
        p = opslib.STATE_DIR / "ORGANISM-STATE.json"
        d = json.loads(p.read_text("utf-8"))
        diag = ((d.get("chrono") or {}).get("legs_diag") or {})
        if not isinstance(diag, dict) or not diag:
            return {"count": -1, "unit": "leg",
                    "detail": "chrono.legs_diag غایب — قضاوت غیرممکن"}
        sat, mx, parts, honest = 0, 0.0, [], 0
        for leg, v in diag.items():
            if not isinstance(v, dict):
                continue
            phi = v.get("phi")
            dead = v.get("phi_dead")
            if not isinstance(phi, (int, float)) or not isinstance(dead, (int, float)):
                continue
            mx = max(mx, float(phi))
            if bool(v.get("honest_tolerance")):
                honest += 1
            if float(phi) >= float(dead):
                sat += 1
            parts.append(f"{leg}:phi={float(phi):.2f}/dead={float(dead):.1f}"
                         f",n={v.get('ack_samples')},{v.get('state')}")
        if not parts:
            return {"count": -1, "unit": "leg",
                    "detail": "هیچ لِگی phi/phi_dead عددی ندارد — قضاوت غیرممکن"}
        return {"count": sat, "unit": "leg",
                "detail": (f"legs={len(parts)} saturated={sat} max_phi={mx:.2f} "
                           f"honest_tolerance={honest}/{len(parts)} | " + " ".join(parts))}
    except Exception as e:  # noqa: BLE001
        return {"count": -1, "unit": "leg", "detail": f"probe-failed:{type(e).__name__}"}


PROBES = {
    # ── مسیرِ رویا: پروب‌های ردیف‌های دفترِ تز (رأیِ مالک 2026-07-25) ─────────
    # این‌ها فقط دادهٔ زندهٔ **موجود** را می‌شمارند؛ هیچ آزمایشِ نو، هیچ شبکه، هیچ پول.
    # مصرف‌کننده: thesis_queue → hypothesis-queue → همان ضربانِ خودکارِ C6.
    "thesis_delta_self_sign": {
        "measure": _probe_thesis_delta_self_sign,
        "subject": "Δ_self: آیا دسترسی به وضعیتِ درونی، پیش‌بینیِ خود را بهتر می‌کند؟",
        "question": "آیا Δ_self در استریمِ زنده هنوز منفی است (دسترسیِ درونی بدتر از کوری)؟",
        "floor": 1,
    },
    "thesis_phi_saturation": {
        "measure": _probe_thesis_phi_saturation,
        "subject": "phi-accrual: آیا عددِ phi اندازه‌گیری است یا اشباعِ سقفِ محاسباتی؟",
        "question": "آیا هنوز لِگی هست که phi>=phi_dead بگیرد (اشباع، نه اندازه‌گیری)؟",
        "floor": 1,
    },
    "self_audit_redundant_reads": {
        "measure": _probe_self_audit_redundant_reads,
        "subject": "reduce per-sweep redundant reads in self_audit.main()",
        "question": "آیا هر sweep کاملِ self_audit واقعاً خواندنی‌های زیادی می‌کند؟",
        "floor": 10,
    },
    "rfc_duplicate_surplus": {
        "measure": _probe_rfc_duplicate_surplus,
        "subject": "deduplicate identical RFC hypotheses in state/c6/rfcs",
        "question": "آیا فرضیه‌های یکسانِ C6 به‌طور تکراری RFC می‌شوند؟",
        "floor": 1,
    },
}
