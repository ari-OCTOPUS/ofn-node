#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mission_kernel — پروندهٔ واحدِ مأموریت: timeline / resume / fsck. فقط‌خواندنی.

ممیزی ۰۷-۳۱ گفت «چند مسیرِ مأموریت، بدونِ یک پروندهٔ واحد و بدونِ trace ِ
سراسری». این ماژول عمداً **FSM ِ نو نمی‌سازد** (قاعدهٔ «چه نسازیم»): دفترهای
موجودِ زنجیرهٔ SGC-14 را — که هرکدام صاحب و نویسندهٔ خودشان را دارند — به یک
پروندهٔ خواندنیِ واحد join می‌کند:

    prereg.jsonl → journal.jsonl → missions.jsonl → action-ledger.jsonl
    → verdicts.jsonl → memory-consolidated.json

سه سوالی که جواب می‌دهد (و قبلاً فقط با grep ِ دستیِ چند JSONL جواب داشت):
    timeline(cycle_id)      این چرخه در هر مرحله چه شد؟ با کدام شناسه‌ها؟
    resume_status(cycle_id) کجا ایستاد؟ (اولین مرحلهٔ غایب — برای resume ِ
                            صادقانه بعد از crash؛ خودِ resume را زنجیرهٔ زنده
                            با دفترِ persisted ِ idempotency انجام می‌دهد)
    fsck()                  زنجیرهٔ شناسه‌ها سالم است؟ (mission↔receipt،
                            verdict↔prereg، journal↔prereg)

مرزها: صفر نوشتن، صفر فلگ (read-only اثری ندارد که فلگ بخواهد)، صفر import از
organism/wiring؛ ردیفِ خراب skip و شمرده می‌شود، نه exception.

$0 · stdlib · فقط‌خواندنی.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

SCHEMA = "mission-kernel.v1"

# ترتیبِ مرحله‌ها = ترتیبِ واقعیِ زنجیرهٔ زنده (direction داخلِ خودِ ردیفِ
# prereg است — دفترِ جدا ندارد).
STAGES = ("prereg", "journal", "mission", "receipt", "verdict", "memory")


def _state_dir(state_dir=None) -> Path:
    if state_dir:
        return Path(state_dir)
    try:
        import opslib
        return Path(opslib.STATE_DIR) / "test_cycle"
    except Exception:  # noqa: BLE001
        return _OPS / "state" / "test_cycle"


def _rows(path: Path) -> list:
    """JSONL → ردیف‌های dict؛ خطِ خراب skip (شمارش با caller)."""
    rows = []
    try:
        for line in path.read_text("utf-8").splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict):
                rows.append(d)
    except OSError:
        pass
    return rows


def _consolidated(st: Path) -> set:
    try:
        d = json.loads((st / "memory-consolidated.json").read_text("utf-8"))
        return {str(c) for c in (d.get("cycle_ids") or [])}
    except (OSError, ValueError):
        return set()


# ── پروندهٔ واحدِ یک چرخه ───────────────────────────────────────────────────
def timeline(cycle_id: str, *, state_dir=None) -> dict:
    st = _state_dir(state_dir)
    cid = str(cycle_id)
    out = {"schema": SCHEMA, "cycle_id": cid,
           "stages": {}, "ids": {}, "gaps": [], "complete": False}

    pre = [r for r in _rows(st / "prereg.jsonl") if str(r.get("cycle_id")) == cid]
    jr = [r for r in _rows(st / "journal.jsonl") if str(r.get("cycle_id")) == cid]
    mis = [r for r in _rows(st / "missions.jsonl") if str(r.get("cycle_id")) == cid]
    ver = [r for r in _rows(st / "verdicts.jsonl") if str(r.get("cycle_id")) == cid]
    led = _rows(st / "action-ledger.jsonl")
    task_ids = {str(m.get("task_id")) for m in mis if m.get("task_id")}
    rec = [r for r in led if str(r.get("action_id")) in task_ids]
    mem_done = cid in _consolidated(st)

    p = pre[-1] if pre else {}
    m = mis[-1] if mis else {}
    rc = rec[-1] if rec else {}
    v = ver[-1] if ver else {}
    out["ids"] = {
        "prereg_id": p.get("prereg_id") or (jr[-1].get("prereg_id") if jr else None),
        "goal_key": p.get("goal_key"),
        "mission_id": m.get("mission_id"),
        "trace_id": m.get("trace_id"),
        "action_id": rc.get("action_id") or (m.get("task_id") if m else None),
        "receipt_status": rc.get("status"),
        "mission_status": m.get("status"),
        "verdict": v.get("verdict"),
    }
    present = {
        "prereg": bool(pre), "journal": bool(jr), "mission": bool(mis),
        "receipt": bool(rec), "verdict": bool(ver), "memory": mem_done,
    }
    detail = {
        "prereg": {"n": len(pre), "direction": p.get("direction"),
                   "method_index": p.get("method_index"), "ts": p.get("ts")},
        "journal": {"n": len(jr)},
        "mission": {"n": len(mis), "status": m.get("status")},
        "receipt": {"n": len(rec), "status": rc.get("status")},
        "verdict": {"n": len(ver), "verdict": v.get("verdict"),
                    "reason": v.get("reason")},
        "memory": {"consolidated": mem_done},
    }
    for s in STAGES:
        out["stages"][s] = {"present": present[s], **detail[s]}
    out["gaps"] = [s for s in STAGES if not present[s]]
    out["complete"] = not out["gaps"]
    return out


def resume_status(cycle_id: str, *, state_dir=None) -> dict:
    """اولین مرحلهٔ غایب = جایی که ایستاد. تشخیص است، نه اقدام — resume ِ
    واقعی را زنجیرهٔ زنده با دفترِ persisted انجام می‌دهد (replay=NOOP)."""
    tl = timeline(cycle_id, state_dir=state_dir)
    if tl["complete"]:
        return {"schema": SCHEMA, "cycle_id": tl["cycle_id"],
                "state": "COMPLETE", "stopped_at": None, "timeline": tl}
    stopped = tl["gaps"][0]
    # verdict/memory ممکن است هنوز due نشده باشند — «ناتمام» با «گیرکرده» فرق
    # دارد؛ این تمایز را صادقانه گزارش می‌کنیم نه حدسی.
    state = "PENDING_EVALUATION" if stopped in ("verdict", "memory") and \
        tl["stages"]["receipt"]["present"] else "INCOMPLETE"
    return {"schema": SCHEMA, "cycle_id": tl["cycle_id"], "state": state,
            "stopped_at": stopped, "timeline": tl}


# ── سلامتِ زنجیرهٔ شناسه‌ها ─────────────────────────────────────────────────
def fsck(*, state_dir=None, limit: int = 500) -> dict:
    """گاردِ integrity: هر لینکِ ادعاشده باید دو سرش روی دیسک باشد.
    خروجی صادق: problems (شکسته) جدا از legacy_unlinked (ردیفِ قدیمی که هنوز
    cycle_id روی envelope نداشت — واقعیتِ تاریخی، نه خرابی)."""
    st = _state_dir(state_dir)
    pre = _rows(st / "prereg.jsonl")[-limit:]
    jr = _rows(st / "journal.jsonl")[-limit:]
    mis = _rows(st / "missions.jsonl")[-limit:]
    ver = _rows(st / "verdicts.jsonl")[-limit:]
    led = _rows(st / "action-ledger.jsonl")[-limit:]

    pre_ids = {str(r.get("prereg_id")) for r in pre}
    rec_by_action = {str(r.get("action_id")): r for r in led}
    problems, legacy = [], 0

    for m in mis:
        if not m.get("cycle_id"):
            legacy += 1
        if str(m.get("status")) == "done":
            r = rec_by_action.get(str(m.get("task_id")))
            if not r:
                problems.append({"kind": "mission-done-without-receipt",
                                 "mission_id": m.get("mission_id"),
                                 "task_id": m.get("task_id")})
            elif str(r.get("status")) not in ("EXECUTED", "NOOP"):
                problems.append({"kind": "mission-done-receipt-not-executed",
                                 "mission_id": m.get("mission_id"),
                                 "receipt_status": r.get("status")})
        if m.get("prereg_id") and str(m["prereg_id"]) not in pre_ids:
            problems.append({"kind": "mission-prereg-missing",
                             "mission_id": m.get("mission_id"),
                             "prereg_id": m.get("prereg_id")})

    for v in ver:
        if str(v.get("prereg_id")) not in pre_ids:
            problems.append({"kind": "verdict-prereg-missing",
                             "cycle_id": v.get("cycle_id"),
                             "prereg_id": v.get("prereg_id")})

    for j in jr:
        pid = j.get("prereg_id")
        if pid and str(pid) not in pre_ids:
            problems.append({"kind": "journal-prereg-missing",
                             "cycle_id": j.get("cycle_id"), "prereg_id": pid})

    return {"schema": SCHEMA, "ok": not problems,
            "checked": {"prereg": len(pre), "journal": len(jr),
                        "missions": len(mis), "verdicts": len(ver),
                        "receipts": len(led)},
            "problems": problems, "legacy_unlinked": legacy}


if __name__ == "__main__":   # pragma: no cover — نمای دستیِ اپراتور
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    res = fsck() if arg in ("", "fsck") else resume_status(arg)
    print(json.dumps(res, ensure_ascii=False, indent=1))
