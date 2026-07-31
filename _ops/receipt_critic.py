#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""receipt_critic — منتقدِ گمشده بینِ «رسیدِ اقدام» و «یادگیری» (GAP-4 ممیزی ۰۷-۳۱).

cycle_evaluator حرکتِ *سنجه* را قضاوت می‌کند؛ هیچ‌کس خودِ *رسید* را قضاوت
نمی‌کرد: `action-ledger.jsonl` نوشته می‌شد و صفر خواننده داشت. یعنی اگر
اجراکننده‌ای روزی ناوردی‌هایش را بشکند (اثرِ بیرونی، هزینه، artifact ِ بی‌rollback،
EXECUTED ِ بی‌قدم) هیچ زنگی نمی‌خورد و هیچ درسی ثبت نمی‌شد.

این منتقد فقط از دیسک می‌خواند (ادعای اجراکننده رأی ندارد — همان قاعدهٔ
cycle_evaluator) و هر رسیدِ تازه را با ناوردی‌های اعلام‌شدهٔ خودِ executor
می‌سنجد:

    C1  external_effects == []        (قولِ صریحِ executor.py — در همهٔ مسیرها)
    C2  cost == 0                     (همان)
    C3  EXECUTED ⇒ steps_completed ≠ []   (اجرای بی‌قدم = ادعای بی‌شاهد)
    C4  artifact ِ written ⇒ rollback_available   (قاعدهٔ Scope/Receipt/Rollback)
    C5  دفترِ mission ردیفِ terminal ِ هم‌خوان دارد (EXECUTED→done وگرنه failed)

حکم: PASS / FAIL (+ نامِ چک‌های شکسته). حکم‌ها append-only در
`receipt-verdicts.jsonl` می‌نشینند و از مسیرِ MemoryGate (episodic،
deterministic) به حافظه می‌روند — outcome-bound؛ authority نیستند.

فلگ `OCTOPUS_WIRE_RECEIPT_CRITIC` عمداً غایب از flags.cmd و بیرون از
PAPER_FULL_FLAGS ⇒ غیاب = خاموش. $0 · stdlib · فقط‌خواندنی جز دو فایلِ خودش.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

FLAG = "OCTOPUS_WIRE_RECEIPT_CRITIC"
SCHEMA = "receipt_verdict.v1"


def enabled() -> bool:
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def _state_dir() -> Path:
    try:
        import opslib
        return Path(opslib.STATE_DIR) / "test_cycle"
    except Exception:  # noqa: BLE001
        return _OPS / "state" / "test_cycle"


def _jsonl(p: Path) -> list:
    out = []
    try:
        for line in p.read_text("utf-8").splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict):
                out.append(d)
    except OSError:
        pass
    return out


# ── قضاوتِ خالص روی یک رسید ─────────────────────────────────────────────────
def judge(receipt: dict, missions_latest: dict) -> dict:
    """{verdict, checks_failed}. خالص؛ ورودی همان چیزی است که روی دیسک است."""
    failed = []
    if list(receipt.get("external_effects") or []):
        failed.append("C1-external-effects-nonempty")
    try:
        if float(receipt.get("cost") or 0) != 0:
            failed.append("C2-cost-nonzero")
    except (TypeError, ValueError):
        failed.append("C2-cost-unreadable")
    status = str(receipt.get("status") or "")
    if status == "EXECUTED" and not list(receipt.get("steps_completed") or []):
        failed.append("C3-executed-without-steps")
    wrote = any(bool(a.get("written")) for a in (receipt.get("artifacts") or [])
                if isinstance(a, dict))
    if wrote and not bool(receipt.get("rollback_available")):
        failed.append("C4-written-artifact-without-rollback")
    # C5 — دفترِ mission باید نتیجهٔ هم‌خوان داشته باشد. رسیدی که mission ندارد
    # به‌تنهایی FAIL نیست (BLOCKED/REJECTED ِ قبل از دفتر مشروع است)، ولی
    # EXECUTED ِ بی‌mission یعنی ادعای انجام بدونِ ثبتِ مأموریت.
    aid = str(receipt.get("action_id") or "")
    linked = None
    for env in missions_latest.values():
        refs = " ".join(str(r) for r in (env.get("output_refs") or []))
        if aid and aid in refs:
            linked = env
            break
    if status == "EXECUTED":
        if linked is None:
            failed.append("C5-executed-without-mission-row")
        elif str(linked.get("status")) != "done":
            failed.append("C5-mission-status-mismatch")
    elif status == "FAILED" and linked is not None \
            and str(linked.get("status")) != "failed":
        failed.append("C5-mission-status-mismatch")
    return {"verdict": "PASS" if not failed else "FAIL",
            "checks_failed": failed}


# ── ارزیابیِ رسیدهای تازه (idempotent) ──────────────────────────────────────
def evaluate_new(*, now: "float | None" = None, cap: int = 10) -> dict:
    now = float(now if now is not None else time.time())
    if not enabled():
        return {"ok": False, "reason": "flag-off"}
    st = _state_dir()
    ledger = _jsonl(st / "action-ledger.jsonl")
    if not ledger:
        return {"ok": True, "evaluated": 0, "reason": "no-ledger"}
    vpath = st / "receipt-verdicts.jsonl"
    judged = {str(v.get("action_id")) for v in _jsonl(vpath)
              if v.get("schema") == SCHEMA}
    missions_latest: dict = {}
    for row in _jsonl(st / "missions.jsonl"):
        if row.get("mission_id"):
            missions_latest[str(row["mission_id"])] = row
    out_rows = []
    for rec in ledger:
        aid = str(rec.get("action_id") or "")
        if not aid or aid in judged:
            continue
        j = judge(rec, missions_latest)
        out_rows.append({
            "schema": SCHEMA, "ts": now, "action_id": aid,
            "receipt_status": rec.get("status"),
            "classification": rec.get("classification"),
            "verdict": j["verdict"], "checks_failed": j["checks_failed"],
        })
        judged.add(aid)
        if len(out_rows) >= max(1, int(cap)):
            break
    if not out_rows:
        return {"ok": True, "evaluated": 0}
    try:
        vpath.parent.mkdir(parents=True, exist_ok=True)
        with open(vpath, "a", encoding="utf-8") as f:
            for r in out_rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    except OSError as e:
        return {"ok": False, "reason": f"verdict-write:{type(e).__name__}"}
    mem = _consolidate(out_rows)
    return {"ok": True, "evaluated": len(out_rows),
            "fails": sum(1 for r in out_rows if r["verdict"] == "FAIL"),
            "memory": mem}


def _consolidate(rows: list) -> dict:
    """حکم‌های منتقد → MemoryGate (episodic، deterministic). fail-soft."""
    try:
        if str(_OPS / "memory") not in sys.path:
            sys.path.insert(0, str(_OPS / "memory"))
        import gate as memgate
        import memory_store
        g = memgate.MemoryGate(memory_store.MemoryStore())
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"gate:{type(e).__name__}"}
    n = 0
    for r in rows:
        try:
            res = g.submit({
                "namespace": "episodic",
                "source": "deterministic",
                "producer": "receipt_critic",
                "agent_id": "receipt_critic",
                "scope": "project",
                "classification": "internal",
                "task_id": str(r.get("action_id") or ""),
                "content": (f"receipt-verdict action={r.get('action_id')} "
                            f"status={r.get('receipt_status')} "
                            f"verdict={r.get('verdict')}"
                            + (f" checks_failed={','.join(r['checks_failed'])}"
                               if r.get("checks_failed") else "")),
            })
            if res.get("verb") in ("commit", "propose"):
                n += 1
        except Exception:  # noqa: BLE001
            continue
    return {"ok": True, "written": n}


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps(evaluate_new(), ensure_ascii=False, indent=1))
