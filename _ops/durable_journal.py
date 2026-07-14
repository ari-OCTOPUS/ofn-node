#!/usr/bin/env python3
"""durable_journal.py — 2027 Standards backlog #2 (P-08 diff-ب):
run-journal سبک برای resume-not-restart.
منبع: 00 - Inbox/build-proposals/08-agent-orchestration-durability-2026-07-05.md
      (۱۳ منبعِ واقعیِ ۲۰۲۶: Inngest/MS Durable Task/Diagrid/LangChain/Temporal/…)

مسئله: این ارگانیسم checkpoint دارد (rfcs.json، ledgerِ append-only) ولی journalِ
اجرا ندارد — یعنی می‌داند «آخرین state چیست»، ولی نه «این گذار کامل شد یا session
درست وسطِ همان قدم قطع شد». تمایز (Diagrid 2026، سندِ P-08 محورِ۳):
    checkpoint       = «state کجاست»
    durable/run-journal = «چه‌طور امن جلو برویم / از کجا دوباره شروع کنیم»

طراحی (additive · $0 · stdlib-only · fail-soft · append-only، هرگز rewrite):
  * record(run_id, step, status) → یک خطِ JSON در state/journal/run-journal.jsonl.
  * resume_point(run_id) → آخرین stepی که status='ok' گرفت (caller از *بعدِ* آن
    ادامه می‌دهد = resume، نه از صفر = restart).
  * incomplete_runs() → هر (run_id, step) که 'start' خورد ولی نه 'ok' نه 'error' —
    یعنی session دقیقاً وسطِ همان قدم قطع شده (برای dashboard/self_audit).

مکملِ M5 (بکاپِ at-rest، مرگِ دیسک) است، نه جایگزینش — این‌جا مرگِ session
وسطِ اجرا (in-flight) را می‌پوشاند. فازِ اول عمداً فقط observability است: خودش
هیچ کنترلِ جریانی را تغییر نمی‌دهد (skip نمی‌کند)؛ تصمیمِ «از resume_point ادامه
بده» با caller است. اتصالِ نمونه: _ops/doctor/doctor.py (run_sandbox/
submit_for_approval/apply_merge) — سه گامِ RFC که امروز نزدیک‌ترین معادلِ واقعیِ
ماشینِ PROPOSE→…→PROMOTE ِ سندِ اصلی است.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

_STATUSES = ("start", "ok", "error")


def _default_path() -> Path:
    import opslib  # lazy: این ماژول باید بدونِ هستهٔ ارگانیسم هم import شود (fail-soft)
    p = opslib.STATE_DIR / "journal" / "run-journal.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def record(run_id: str, step: str, status: str, *,
           path: Optional[Path] = None, **meta) -> None:
    """یک گذارِ حالت را ثبت کن. status ∈ {start, ok, error}. fail-soft مطلق:
    خطای نوشتنِ journal هرگز caller را نمی‌کشد — این فقط بوکیپینگ است، نه گیت."""
    if status not in _STATUSES:
        raise ValueError(f"status must be one of {_STATUSES}")
    line = {"run_id": str(run_id), "step": str(step), "status": status,
            "ts": time.time(), "meta": meta}
    try:
        p = path or _default_path()
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — journal هرگز مسیرِ اصلی را نمی‌شکند
        pass


def _read_all(path: Optional[Path] = None) -> list[dict]:
    p = path or _default_path()
    if not p.exists():
        return []
    out: list[dict] = []
    try:
        for ln in p.read_text("utf-8").splitlines():
            try:
                row = json.loads(ln)
                if isinstance(row, dict):
                    out.append(row)
            except (ValueError, TypeError):
                continue
    except OSError:
        pass
    return out


def resume_point(run_id: str, *, path: Optional[Path] = None) -> Optional[str]:
    """آخرین stepی که برای این run_id به status='ok' رسید، یا None اگر هیچ‌کدام
    (یعنی: یا اصلاً شروع نشده، یا هنوز هیچ قدمی کامل نشده). caller از *بعدِ*
    این step resume می‌کند، نه از اول."""
    last_ok = None
    for row in _read_all(path):
        if row.get("run_id") == run_id and row.get("status") == "ok":
            last_ok = row.get("step")
    return last_ok


def run_status(run_id: str, *, path: Optional[Path] = None) -> dict:
    """خلاصهٔ کاملِ یک run: {step: آخرین‌status اش} — برای دیباگ/دشبورد."""
    steps: dict[str, str] = {}
    for row in _read_all(path):
        if row.get("run_id") == run_id:
            steps[str(row.get("step", "?"))] = str(row.get("status", "?"))
    return steps


def incomplete_runs(*, within_h: float = 24.0,
                     path: Optional[Path] = None) -> list[dict]:
    """هر (run_id, step) که 'start' خورد ولی در همان within_h ساعتِ اخیر نه 'ok'
    نه 'error' گرفت — نشانهٔ صادقِ «session دقیقاً وسطِ این قدم قطع شد»."""
    cutoff = time.time() - within_h * 3600
    starts: dict[tuple, dict] = {}
    finished: set = set()
    for row in _read_all(path):
        key = (row.get("run_id"), row.get("step"))
        if row.get("status") == "start" and row.get("ts", 0) >= cutoff:
            starts[key] = row
        elif row.get("status") in ("ok", "error"):
            finished.add(key)
    return [{"run_id": k[0], "step": k[1], "since": v.get("ts")}
            for k, v in starts.items() if k not in finished]


if __name__ == "__main__":
    import sys
    rid = sys.argv[1] if len(sys.argv) > 1 else "demo"
    print(json.dumps({"resume_point": resume_point(rid), "status": run_status(rid),
                      "incomplete_runs": incomplete_runs()},
                     ensure_ascii=False, indent=2))
