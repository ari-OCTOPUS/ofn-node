#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""پایش مسمومیت حافظهٔ 4d — شرط شورا برای R15-shadow (2026-08-16).

فقط-خواندن. هر ۶ ساعت (تسک ویندوزی). خروجی: append به
06-EVIDENCE/POISONING-WATCH-4d.md + exit code (0=سالم، 2=هشدار).

سنجه‌ها: ۱) read-before-decision پنجرهٔ پس از سیم‌کشی (≥0.95)
۲) نرخ تکرار gistهای سمنتیکِ «پس از گیت» (باید ~صفر باشد)
۳) وضعیت صف فرضیه (R16) ۴) زنده‌بودن daemon.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(r"F:\backup")
FOURD = VAULT / "4d_system"
OUT = VAULT / "06-EVIDENCE" / "POISONING-WATCH-4d.md"
DB = FOURD / "outputs" / "4d_experiments.db"
SEM = VAULT / "_ops" / "state" / "semantic_memory.jsonl"
GATE_TS = "2026-08-16T03:5"   # زمان نصب گیت gist — نوت‌های پس از آن سنجه می‌شوند


def _run(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:  # noqa: BLE001
        return f"ERR:{e}"


def main() -> int:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    alerts: list[str] = []
    parts: list[str] = [f"\n## {now}"]\

    # ۱) telemetry پنجره‌ای
    t = _run(["py", "-X", "utf8", "-c",
              "import sys; sys.path.insert(0, r'F:/backup/4d_system'); "
              "from brain import memory_read_patch as mrp; import sqlite3; "
              f"con=sqlite3.connect(r'file:{DB}?mode=ro', uri=True); "
              "first=con.execute(\"SELECT MIN(id) FROM dashboard_events "
              "WHERE event_name='memory.read'\").fetchone()[0]; con.close(); "
              "m=mrp.telemetry_metrics(after_id=first-1); "
              "print(m['decision_jobs'], m['decision_jobs_with_read'], "
              "round(m['memory_read_before_decision_ratio'],4), "
              "m['readback_total'], m['readback_ok'])"])
    parts.append(f"- telemetry(windowed): jobs/read/ratio/readback = {t.strip()[:120]}")
    try:
        ratio = float(t.strip().split()[2])
        if ratio < 0.95:
            alerts.append(f"read-before-decision پنجره‌ای {ratio} < 0.95")
    except (ValueError, IndexError):
        alerts.append("telemetry خوانده نشد")

    # ۲) تکرار gistهای نو (پس از گیت)
    try:
        rows = [json.loads(l) for l in SEM.read_text(encoding="utf-8").splitlines() if l.strip()]
        fresh = [r for r in rows if str(r.get("ts", "")) > GATE_TS]
        from collections import Counter
        g = Counter(str(r.get("gist"))[:70] for r in fresh)
        dups = sum(n - 1 for n in g.values() if n > 1)
        parts.append(f"- semantic: کل={len(rows)} نو-پس-گیت={len(fresh)} تکرارِ نو={dups}")
        if len(fresh) >= 10 and dups / max(1, len(fresh)) > 0.20:
            alerts.append(f"تکرار gistهای نو {dups}/{len(fresh)} > 20% — گیت بی‌اثر؟")
    except OSError:
        parts.append("- semantic: فایل ناخوانا")

    # ۳) صف فرضیه
    q = _run(["py", "-X", "utf8", "-c",
              f"import sqlite3; con=sqlite3.connect(r'file:{DB}?mode=ro', uri=True); "
              "print(con.execute('SELECT status, COUNT(*) FROM hypotheses "
              "GROUP BY status').fetchall()); con.close()"])
    parts.append(f"- queue: {q.strip()[:100]}")

    # ۳-ب) readback پس از 05:00 (پیش‌ثبت‌نام READBACK-ACCEPTANCE-WINDOW-v1)
    try:
        import sqlite3 as _sq
        con = _sq.connect(f"file:{FOURD / 'outputs' / '4d_experiments.db'}?mode=ro", uri=True)
        rb = con.execute(
            "SELECT COUNT(*), SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END)"
            " FROM dashboard_events WHERE event_name='memory.readback'"
            " AND timestamp >= '2026-08-16T05:00'").fetchone()
        con.close()
        n, ok = int(rb[0] or 0), int(rb[1] or 0)
        ratio = round(ok / n, 4) if n else None
        parts.append(f"- readback(پنجرهٔ پس از 05:00): {ok}/{n}" +
                     (f" = {ratio}" if n else " (هنوز نمونه‌ای نیست)"))
        if n >= 50 and ratio is not None and ratio < 0.99:
            alerts.append(f"readback پنجره‌ای {ok}/{n} < 0.99 (نمونه کافی — ناکامی واقعی)")
    except Exception as e:  # noqa: BLE001
        parts.append(f"- readback: خوانده نشد ({type(e).__name__})")

    # ۳-ج) recall_reach (_ops) — سری زمانی برای حلقهٔ دور
    try:
        sys.path.insert(0, str(VAULT / "_ops" / "neural"))
        from consolidation import recall_reach as _rr  # noqa: WPS433
        cons = VAULT / "_ops" / "neural" / "consolidation.json"
        hist = json.loads(cons.read_text(encoding="utf-8"))
        if not isinstance(hist, list):
            hist = []
        m = _rr(hist)
        parts.append(
            f"- recall_reach: events={m.get('events')} keys={m.get('keys')} "
            f"median={m.get('reach_median')} max={m.get('reach_max')} "
            f"coverage={round(float(m.get('coverage') or 0), 4)} rows={len(hist)}")
    except Exception as e:  # noqa: BLE001
        parts.append(f"- recall_reach: خوانده نشد ({type(e).__name__})")

    # ۴) daemon
    st = FOURD / "outputs" / "daemon_state.json"
    parts.append(f"- daemon_state.json: {'موجود' if st.exists() else 'غایب!'}")
    if not st.exists():
        alerts.append("daemon_state.json غایب — daemon نمرده؟")

    verdict = "🟢 سالم" if not alerts else "🔴 هشدار: " + "؛ ".join(alerts)
    parts.append(f"- حکم: {verdict}")
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write("\n".join(parts) + "\n")
    print(verdict)
    return 2 if alerts else 0


if __name__ == "__main__":
    sys.exit(main())
