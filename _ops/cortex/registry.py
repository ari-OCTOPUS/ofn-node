#!/usr/bin/env python3
"""registry.py — دفترِ اعضا: هر عضو آگاهیِ خودش را در state-fileِ خودش دارد؛
کورتکس فقط می‌خواند و نمرهٔ تازگی/سلامت می‌دهد (read-only، هیچ دستکاری).

نمرهٔ آگاهیِ عضو = تازگیِ فایلِ آگاهی‌اش نسبت به SLA خودش (۰..۱) — عضوِ ساکت/کهنه
خودش را لو می‌دهد. coherence مجموعه = میانگینِ وزنیِ اعضای حیاتی.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

# هر عضو: id، فایلِ آگاهی (نسبت به STATE_DIR مگر مطلق)، SLA تازگی (ثانیه)، وزنِ حیاتی
MEMBERS: list[dict] = [
    {"id": "organism", "file": "ORGANISM-STATE.json", "sla_s": 1800, "vital": 3},
    {"id": "heart", "file": "pulse/heart-shadow-latest.json", "sla_s": 3600, "vital": 3},
    {"id": "producers", "file": "pulse/heart-signals-latest.json", "sla_s": 3600, "vital": 2},
    {"id": "work_pump", "file": "pulse/work-state.json", "sla_s": 7200, "vital": 2},
    {"id": "doctor_setpoint", "file": "pulse/heart-setpoint-latest.json", "sla_s": 172800, "vital": 1},
    {"id": "governor", "file": "telemetry-latest.json", "sla_s": 7200, "vital": 3},
    {"id": "sigma", "file": "replication-latest.json", "sla_s": 172800, "vital": 3},
    {"id": "fitness", "file": "fitness-latest.json", "sla_s": 172800, "vital": 1},
    {"id": "school", "file": "school-awareness.json", "sla_s": 259200, "vital": 1},
    {"id": "reconcile", "file": "reconcile-latest.json", "sla_s": 259200, "vital": 1},
]


def _age_s(p: Path) -> float | None:
    try:
        if not p.exists():
            return None
        return max(0.0, dt.datetime.now().timestamp() - p.stat().st_mtime)
    except OSError:
        return None


def member_awareness(m: dict, state_dir: Path | None = None) -> dict:
    """آگاهیِ یک عضو: presence + تازگی نسبت به SLA + یک خلاصهٔ یک‌خطی."""
    state = state_dir or opslib.STATE_DIR
    p = Path(m["file"]) if str(m["file"]).find(":") == 1 else state / m["file"]
    age = _age_s(p)
    # P8 (truth-map 2026-07-17): عضو خود-توصیف می‌شود — این نمره «تازگیِ فایل» است، نه
    # فلگِ wiring. بدونِ این، /api/cortex «reconcile حاضر» می‌گفت و ارگانیسم
    # «wire_reconcile=false» — دو سنجهٔ متفاوت با یک اسم (تناقضِ U11).
    if age is None:
        return {"id": m["id"], "present": False, "awareness": 0.0,
                "age_s": None, "note": "state غایب",
                "source": "file-freshness", "watches": str(m["file"])}
    sla = float(m.get("sla_s", 3600))
    freshness = max(0.0, min(1.0, 1.0 - (age / (2.0 * sla))))
    note = "تازه" if age <= sla else f"کهنه ({int(age / 3600)}h)"
    return {"id": m["id"], "present": True,
            "awareness": round(freshness, 3),
            "age_s": int(age), "sla_s": int(sla), "note": note,
            "source": "file-freshness", "watches": str(m["file"])}


def ping() -> str:
    return "ok"


def sweep(state_dir: Path | None = None) -> dict:
    """جاروی کاملِ اعضا → آگاهیِ per-عضو + coherence مجموعه (وزنی با vital)."""
    rows = [member_awareness(m, state_dir) for m in MEMBERS]
    w_sum = sum(m.get("vital", 1) for m in MEMBERS)
    coherence = sum(r["awareness"] * m.get("vital", 1)
                    for r, m in zip(rows, MEMBERS)) / max(1, w_sum)
    stale = [r["id"] for r in rows if r["awareness"] < 0.5]
    return {"ts": opslib.now_iso(), "members": rows,
            "coherence": round(coherence, 3),
            "stale_members": stale, "n": len(rows)}


if __name__ == "__main__":
    print(json.dumps(sweep(), ensure_ascii=False, indent=2))
