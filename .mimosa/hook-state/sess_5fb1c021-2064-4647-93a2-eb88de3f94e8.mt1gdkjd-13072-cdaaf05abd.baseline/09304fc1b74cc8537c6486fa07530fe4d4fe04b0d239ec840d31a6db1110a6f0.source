#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""watcher.py — دو ساعت مشاهدهٔ زندهٔ سطحِ تلگرام (۲۰۲۶-۰۷-۲۶).

رأیِ مالک: «دو ساعت زنده زیرنظر داشته باش، ذخیره کن برای ایجنتِ بعدی».

read-only مطلق. هیچ فایلِ ارگانیسم را نمی‌نویسد؛ فقط `samples.jsonl` کنارِ خودش.
`getUpdates` هرگز زده نمی‌شود — با pollerِ زندهٔ هر دو بات ۴۰۹ می‌شود. پس
پاسخ‌های مالک با **اثرشان** سنجیده می‌شوند نه با خواندنِ متنشان:
  · `last_offset` جلو رفت  → باتِ مرکز پیامی گرفت
  · `telegram_offset` جلو رفت → باتِ اصلی پیامی گرفت
  · ردیفِ تازه در send-log → چیزی بیرون رفت
  · ردیفِ تازه در rfc_decision → یک کلیکِ واقعی ثبت شد
این دقیقاً همان انضباطی است که کلِ این جلسه رویش بنا شد: اثر، نه ادعا.
"""
import json
import sqlite3
import time
from pathlib import Path

OPS = Path(r"F:\backup\_ops")
OUT = Path(__file__).resolve().parent / "samples.jsonl"
DURATION_S = 2 * 3600
EVERY_S = 120


def _j(rel, default=None):
    try:
        return json.loads((OPS / rel).read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return default


def _lines(rel):
    try:
        return sum(1 for x in (OPS / rel).read_text("utf-8", errors="replace").splitlines()
                   if x.strip())
    except Exception:  # noqa: BLE001
        return -1


def _mtime(rel):
    try:
        return round((OPS / rel).stat().st_mtime, 1)
    except Exception:  # noqa: BLE001
        return None


def _sqlite_count(rel, table):
    try:
        c = sqlite3.connect(str(OPS / rel))
        n = c.execute(f'select count(*) from "{table}"').fetchone()[0]
        c.close()
        return n
    except Exception:  # noqa: BLE001
        return -1


def _procs():
    """PID پروسه‌های ارگانیسم.

    نسخهٔ اول `wmic` می‌زد و همیشه {} می‌داد — wmic در ویندوز ۱۱ حذف شده. یعنی
    ناظر بی‌صدا کور بود و «هیچ پروسه‌ای نیست» را شبیهِ «نتوانستم بخوانم» گزارش
    می‌کرد. حالا PowerShell، و شکستِ خواندن صریحاً {"_error": …} می‌دهد تا با
    «پروسه‌ای نیست» اشتباه گرفته نشود."""
    try:
        import subprocess
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"],
            capture_output=True, text=True, timeout=30)
        data = json.loads(r.stdout or "[]")
        if isinstance(data, dict):
            data = [data]
        out = {}
        for p in data:
            cl = str(p.get("CommandLine") or "")
            for tag in ("organism.py", "center.py", "cortex.py", "server.py"):
                if tag in cl:
                    out[tag] = p.get("ProcessId")
        return out or {"_none": True}
    except Exception as e:  # noqa: BLE001
        return {"_error": type(e).__name__}


def sample(i):
    cfg = _j("state/telegram/center-config.json", {}) or {}
    c6 = []
    try:
        c6 = [json.loads(x) for x in
              (OPS / "state/c6/hypothesis-queue.jsonl").read_text("utf-8").splitlines()
              if x.strip()]
    except Exception:  # noqa: BLE001
        pass
    return {
        "i": i, "ts": round(time.time(), 1),
        "procs": _procs(),
        "centre_offset": cfg.get("last_offset"),
        "centre_cfg_mtime": _mtime("state/telegram/center-config.json"),
        "main_offset": (_j("state/telegram_offset.json", {}) or {}).get("offset"),
        "send_log_rows": _lines("state/tg-send-log.jsonl"),
        "rfc_decisions": _sqlite_count("state/doctor/rfc-verdicts.db", "rfc_decision"),
        "c6_rows": len(c6),
        "c6_pending": sum(1 for r in c6 if r.get("status") == "PENDING"),
        "c6_undelivered": sum(1 for r in c6
                              if r.get("status") == "DONE" and not r.get("card_delivered")),
        "discoveries": _lines("state/discoveries.jsonl"),
        "nudged_marker": _mtime("state/discoveries-nudged.json"),
        "instant_fear": _mtime("state/instant-fear.json"),
        "instant_c6": _mtime("state/instant-c6_new.json"),
        "alerts_mtime": _mtime("governor/governor-alerts.md"),
        "organism_booted": (_j("state/ORGANISM-STATE.code", {}) or {}).get("booted"),
        "heart_wires_mtime": _mtime("state/heart-wires-latest.json"),
        "thesis_stream": _lines("state/thesis/measurements.jsonl"),
    }


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    i = 0
    with OUT.open("a", encoding="utf-8") as f:
        while time.time() - t0 < DURATION_S:
            i += 1
            try:
                row = sample(i)
            except Exception as e:  # noqa: BLE001
                row = {"i": i, "ts": round(time.time(), 1), "error": f"{type(e).__name__}"}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            time.sleep(EVERY_S)
    print(f"watch finished: {i} samples over {int(time.time()-t0)}s -> {OUT}")
