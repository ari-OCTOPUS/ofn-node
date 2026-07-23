#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""journal_recovery.py — C2-D: بازیابیِ resume-not-restart در بوت (RESURRECTION فاز ۴+۷).

دو رگِ بازیابی که تا امروز قطع بود:
  ۱. **journal** (فاز ۷): durable_journal از D-A یتیم بود — حالا doctor قدم‌هایش را ثبت
     می‌کند و این ماژول در بوت `incomplete_runs` را می‌خواند: runهایی که وسطِ قدمی
     مرده‌اند (start بدونِ ok/error). بازیابی **advisory** است: گزارش + resume_point؛
     **هرگز re-runِ کورِ هیچ قدمی**.
  ۲. **chrono in-flight** (فاز ۴): اثرِ EXECUTINGای که workerش با خواب/مرگ گم شده →
     `RECONCILE_REQUIRED` (جارویِ C6 — تا امروز صفر caller داشت). هرگز terminal جعلی،
     هرگز اجرای دوباره: اثرِ بیرونی شاید واقعاً رخ داده باشد؛ فقط آشتیِ انسانی.

قواعد:
  - fail-soft کامل: هیچ خطایی بوت را نمی‌کشد؛ journal/chrono غایب → skip با گزارش.
  - صفر effectِ خارجی؛ تنها گذارِ وضعیت EXECUTING→RECONCILE_REQUIRED (جهتِ امنِ صادق).
  - knob همان idiomِ C6: `OCTOPUS_BOOT_RECONCILE_EXEC_H` (پیش‌فرض ۶؛ ۰ = جاروی chrono خاموش).
  - خودِ بازیابی هم journal می‌شود (boot-recovery run) — دیدنِ دیده‌بان.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

EXEC_H_ENV = "OCTOPUS_BOOT_RECONCILE_EXEC_H"
DEFAULT_EXEC_H = 6.0


def _exec_hours() -> float:
    try:
        v = float(os.environ.get(EXEC_H_ENV, "") or DEFAULT_EXEC_H)
        return max(0.0, v)
    except ValueError:
        return DEFAULT_EXEC_H


def boot_recovery(*, state_dir=None, chrono_db_path=None, within_h: int = 48) -> dict:
    """اسکنِ بازیابیِ بوت. خروجی (همیشه برمی‌گردد، هرگز raise):
    {journal: {incomplete: [...], resume_points: {...}} | skipped,
     chrono: {reconciled: n, reconcile_required_total: n, ...} | skipped}"""
    out: dict = {"journal": {}, "chrono": {}}
    for _p in (str(_HERE), str(_HERE / "budget")):
        if _p not in sys.path:
            sys.path.insert(0, _p)

    # ── ۱) journal: مرده‌های وسطِ قدم — advisory، بدونِ re-run ─────────────────
    # C7.1 (B8): هر lane journalِ **خودش** را دارد. resume_point هر ردیف باید از journalِ
    # همان lane خوانده شود — نه اینکه ردیفِ پژوهشی از run-journal resume بگیرد (باگِ بازبینی).
    jpath = None
    try:
        import durable_journal as dj   # noqa: WPS433
        if state_dir is not None:
            jpath = Path(state_dir) / "journal" / "run-journal.jsonl"
        rjp = (Path(state_dir) / "journal" / "research-journal.jsonl") if state_dir is not None \
            else (_HERE / "state" / "journal" / "research-journal.jsonl")
        lanes = [("run", jpath), ("research", rjp if (rjp and rjp.exists()) else None)]
        inc = []                       # هر ردیف lane و path خودش را حمل می‌کند
        for lane, path in lanes:
            if lane == "research" and path is None:
                continue
            try:
                rows = dj.incomplete_runs(within_h=within_h, path=path) if path is not None \
                    else dj.incomplete_runs(within_h=within_h)
            except Exception:  # noqa: BLE001
                rows = []
            for r in rows:
                r["_lane"] = lane
                r["_path"] = str(path) if path is not None else None
                inc.append(r)
        resume = {}
        for row in inc:   # incomplete_runs → [{"run_id","step","since","_lane","_path"}]
            rid = row.get("run_id")
            rp = Path(row["_path"]) if row.get("_path") else None
            try:
                resume[rid] = dj.resume_point(rid, path=rp)   # ← از journalِ **همان lane**
            except Exception:  # noqa: BLE001
                resume[rid] = None
        # نقشهٔ ساختاریافتهٔ resumeِ پژوهش (contract_id/experiment_index/budget) — از research-journal
        research_plan = []
        try:
            for _p in (str(_HERE / "outcomes"),):
                if _p not in sys.path:
                    sys.path.insert(0, _p)
            import research_loop as _rl   # noqa: WPS433
            research_plan = _rl.plan_recovery(state_dir=state_dir, within_h=within_h)
        except Exception:  # noqa: BLE001
            research_plan = []
        out["journal"] = {"incomplete": [{"run_id": r.get("run_id"),
                                          "died_at_step": r.get("step"),
                                          "lane": r.get("_lane")} for r in inc],
                          "resume_points": resume,
                          "research_plan": research_plan}
        # خودِ این اسکن هم ثبت می‌شود (fail-soft)
        try:
            dj.record("boot-recovery", "journal-scan", "ok",
                      path=jpath, incomplete=len(inc))
        except Exception:  # noqa: BLE001
            pass
    except Exception as e:  # noqa: BLE001
        out["journal"] = {"skipped": f"{type(e).__name__}"}

    # ── ۲) chrono: EXECUTINGِ رهاشده → RECONCILE_REQUIRED (هرگز re-run/terminal جعلی) ──
    hours = _exec_hours()
    if hours <= 0:
        out["chrono"] = {"skipped": "knob-off"}
        return out
    try:
        import chrono as _ch   # noqa: WPS433
        db = _ch.ChronoDB(path=chrono_db_path) if chrono_db_path else _ch.ChronoDB()
        try:
            gate = _ch.EffectorGate(db)
            swept = gate.sweep_stale_executions(max_exec_hours=hours)
            report = gate.reconciliation_report(max_exec_hours=hours)
            out["chrono"] = {"reconciled_now": swept.get("reconcile_required", 0),
                             "reconciled_ids": swept.get("ids", []),
                             "reconcile_required_total":
                                 len(report.get("reconcile_required", [])),
                             "attention_total": report.get("attention_total", 0)}
        finally:
            try:
                db._con.close()   # noqa: SLF001
            except Exception:  # noqa: BLE001
                pass
    except Exception as e:  # noqa: BLE001
        out["chrono"] = {"skipped": f"{type(e).__name__}"}
    return out
