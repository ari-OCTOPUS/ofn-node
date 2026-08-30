#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""daily_loop.py — حلقهٔ روزانهٔ خوداجرا (مالک: «خودکفا»، انتخاب ۱؛ 2026-08-19).

ورودیِ روزانهٔ مالک (در چت یا فایل): نرخ RBA AUD/USD روز.
قدم‌ها: ① FX-pin جدید با دقت کامل+هش ② launcher (ریست سهمیه؟ → پنجرهٔ رزرو → Live-4)
③ سلامت‌سنجی (دیمون/بودجه/رسیدها/پوشش حافظه) ④ گزارش یک‌صفحه‌ای برای مالک.
اجرای دستیِ روزانه توسط مالک/نشست — بدون scheduler."""
from __future__ import annotations
import json, subprocess, sys, sqlite3
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(r"F:/backup")
L4 = ROOT / "06-EVIDENCE/CL01-191-20260818-2233/live4"
sys.path.insert(0, str(L4)); sys.path.insert(0, str(ROOT/"_ops")); sys.path.insert(0, str(ROOT/"_ops/cortex"))
import live4_harness as H

def pin_fx(aud_usd: float, day: str) -> dict:
    rate = round(1.0 / float(aud_usd), 10)
    rec = {"fx_source_id": f"RBA_EXCHANGE_RATES_DAILY_{day}",
           "fx_timestamp_utc": f"{day}T06:00:00Z", "fx_rate_usd_to_aud": rate,
           "FX_SOURCE_VALUE": f"AUD_USD = {aud_usd}", "FX_CONVERSION_METHOD": "reciprocal_of_RBA_AUD_USD",
           "owner_pin_id": f"FX-PIN-{day.replace('-','')}-01"}
    rec["fx_hash"] = H.fx_canonical_hash(rec)
    (L4/"FX-RECORD.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    import json as _j
    p = ROOT/"_ops/cortex/pricing_pinned.json"
    d = _j.loads(p.read_text(encoding="utf-8")); d["fx_usd_to_aud"] = rate; d["fx_record"] = rec
    p.write_text(_j.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return H.validate_fx(rec)

def health() -> dict:
    out = {}
    try:
        r = subprocess.run(["powershell","-NoProfile","-Command",
          "(Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | Where-Object {$_.CommandLine -like '*brain.daemon*'}).ProcessId"],
          capture_output=True, text=True, timeout=20).stdout.strip()
        out["daemon_pid"] = r or "DOWN"
    except Exception: out["daemon_pid"] = "UNKNOWN"
    txt = (ROOT/"4d_system/outputs/daemon-launch4b.err.log").read_text(encoding="utf-8", errors="replace")
    out["protective_halts"] = txt.count("protective HALT")
    b = json.loads((ROOT/"_ops/budget/budget-state.json").read_text(encoding="utf-8"))
    out["budget"] = {"date": b.get("date"), "spent_today_usd": b.get("spent_today_usd"), "halted": b.get("halted")}
    con = sqlite3.connect(f"file:{ROOT}/_ops/state/memory/memory.db?mode=ro", uri=True)
    row = con.execute("SELECT COUNT(*), SUM(confidence IS NOT NULL AND confidence!=''), SUM(valid_to IS NOT NULL AND valid_to!='') FROM memory WHERE admission_state='ADMITTED'").fetchone()
    con.close(); out["memory_admitted"] = {"n": row[0], "with_conf": row[1], "with_expiry": row[2]}
    out["halts_frozen"] = (ROOT/"_ops/budget/FREEZE.flag").exists()
    out["sh_armed"] = (ROOT/"_ops/ACTIVATION-RAW-SHELL.flag").exists()
    return out

if __name__ == "__main__":
    day = datetime.now(timezone.utc).date().isoformat()
    aud = float(sys.argv[1]) if len(sys.argv) > 1 else None
    rep = {"day": day, "generated": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if aud:
        rep["fx"] = pin_fx(aud, day)
        rep["launcher"] = subprocess.run([sys.executable, "-X", "utf8", str(L4/"reservation/SILENT-WINDOW-LAUNCHER.py")],
                                         capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()[:300]
    rep["health"] = health()
    print(json.dumps(rep, ensure_ascii=False, indent=1))
