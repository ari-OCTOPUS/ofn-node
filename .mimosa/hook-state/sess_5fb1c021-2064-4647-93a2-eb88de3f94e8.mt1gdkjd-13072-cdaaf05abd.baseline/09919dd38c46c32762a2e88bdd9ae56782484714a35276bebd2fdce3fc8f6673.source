#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""heart_wires.py — سیم‌کشیِ اندام‌های پژوهش به ضربانِ قلب.

وظیفه: هر beat (یا هر N beat) سه اندام را در صورتِ flag-on فراخوانی می‌کند:
  1) thesis_queue — دفترِ تز → قراردادِ پژوهش
  2) coherence — پروبِ انسجام ←→ دفترِ تز
  3) identity_equations — مگا-معادلات (writeback به state)

همه fail-soft، zero-cost lanes، صفر شبکه/پول. سقف ۱ فراخوان per beat.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

OUT = opslib.STATE_DIR / "heart-wires-latest.json"


def _save(report: dict) -> None:
    try:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        tmp = OUT.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(OUT)
    except OSError:
        pass


def thesis_wire() -> dict:
    """دفترِ تز را می‌خواند و خلاصه برمی‌گرداند. اجرا نمی‌کند."""
    if not str(os.environ.get("OCTOPUS_WIRE_THESIS_QUEUE", "")).strip().lower() in ("1", "true", "yes", "on"):
        return {"ok": False, "reason": "thesis-queue-flag-off"}
    try:
        import thesis_queue as tq  # noqa: WPS433
        sel = tq.select(limit=3)
        return {
            "ok": True,
            "runnable": sel.get("runnable_total", 0),
            "needs_design": len(sel.get("needs_design") or []),
            "blocked": len(sel.get("blocked") or []),
            "rows": sel.get("ledger_rows", 0),
            "kill": sel.get("kill_check", {}).get("verdict"),
            "top_runnable": [c["id"] for c in (sel.get("runnable") or [])[:3]],
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"fail:{type(e).__name__}"}


def coherence_wire() -> dict:
    """پروبِ انسجام — فقط ادعاهای بی‌kill می‌شمارد، نمی‌نویسد."""
    if not str(os.environ.get("OCTOPUS_WIRE_COHERENCE", "")).strip().lower() in ("1", "true", "yes", "on"):
        return {"ok": False, "reason": "coherence-flag-off"}
    try:
        import coherence as _coh  # noqa: WPS433
        report = _coh.probe() if hasattr(_coh, "probe") else {}
        bad = sum(1 for v in (report.values() if isinstance(report, dict) else [])
                  if isinstance(v, dict) and v.get("verdict") not in (None, "ok", "no_input"))
        total = max(1, sum(1 for v in (report.values() if isinstance(report, dict) else [])
                          if isinstance(v, dict)))
        return {"ok": True, "bad": bad, "total": total, "health": round(1.0 - bad / total, 3)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"fail:{type(e).__name__}"}


def identity_wire() -> dict:
    """مگا-معادلات هویت را محاسبه و in-place می‌نویسد."""
    if not str(os.environ.get("OCTOPUS_WIRE_IDENTITY_EQ", "")).strip().lower() in ("1", "true", "yes", "on"):
        return {"ok": False, "reason": "identity-flag-off"}
    try:
        import identity_equations as ie  # noqa: WPS433
        rpt = ie.evaluate()
        ie_out = opslib.STATE_DIR / "identities-latest.json"
        try:
            ie_out.parent.mkdir(parents=True, exist_ok=True)
            tmp = ie_out.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(rpt, ensure_ascii=False, indent=2), "utf-8")
            tmp.replace(ie_out)
        except OSError:
            pass
        ids = rpt.get("identities") or {}
        return {
            "ok": True,
            "O": ids.get("organism", {}).get("value", 0),
            "L": ids.get("learner", {}).get("value", 0),
            "E": ids.get("earner", {}).get("value", 0),
            "G": ids.get("guardian", {}).get("value", 0),
            "K": ids.get("creator", {}).get("value", 0),
            "missing": rpt.get("signals", {}).get("missing") or [],
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"fail:{type(e).__name__}"}


def romajan_wire() -> dict:
    """romajan bridge — یک sync در روز. fail-soft."""
    try:
        import romajan_bridge as rb  # noqa: WPS433
        return rb.sync()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"fail:{type(e).__name__}"}


def seed_killer_wire() -> dict:
    """اگر C6_PRODUCER روشن است، seed_default_hypothesis را حذف کن (ضد seed جعلی)."""
    if str(os.environ.get("OCTOPUS_WIRE_C6_PRODUCER", "")).strip().lower() not in ("1", "true", "yes", "on"):
        return {"ok": False, "reason": "producer-off"}
    try:
        queue = opslib.STATE_DIR / "c6" / "hypothesis-queue.jsonl"
        if not queue.exists():
            return {"ok": True, "deleted": 0, "reason": "no-queue"}
        lines = queue.read_text("utf-8").splitlines()
        kept = []
        killed = 0
        for ln in lines:
            if not ln.strip():
                continue
            try:
                d = json.loads(ln)
            except ValueError:
                kept.append(ln)
                continue
            sid = str(d.get("id") or "")
            src = str(d.get("source") or "")
            if sid.startswith("seed-") or src == "seed" or d.get("kind") == "seed_default":
                killed += 1
                continue
            kept.append(ln)
        if killed:
            tmp = queue.with_suffix(".jsonl.tmp")
            tmp.write_text("\n".join(kept) + ("\n" if kept else ""), "utf-8")
            tmp.replace(queue)
        return {"ok": True, "deleted": killed, "kept": len(kept)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"fail:{type(e).__name__}"}


def beat(*, run_romajan: bool = False) -> dict:
    """یک ضربانِ پژوهش. از organism یا cron هر N beat صدا زده شود."""
    wires = {}
    for name, fn in [
        ("thesis", thesis_wire),
        ("coherence", coherence_wire),
        ("identity", identity_wire),
        ("seed_killer", seed_killer_wire),
    ]:
        try:
            wires[name] = fn()
        except Exception:  # noqa: BLE001
            wires[name] = {"ok": False, "reason": "exception"}
    if run_romajan:
        wires["romajan"] = romajan_wire()
    wires["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _save(wires)
    return wires


if __name__ == "__main__":
    print(json.dumps(beat(), ensure_ascii=False, indent=2))
