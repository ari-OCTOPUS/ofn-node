#!/usr/bin/env python3
"""receipt — رسیدِ عمل. و قاعده‌ای که آسان است فراموش شود:

    **رسیدی که ننشسته، عملی است که اثباتش وجود ندارد.**

پس اگر نوشتنِ رسید شکست بخورد، وضعیت `EXECUTED` **نمی‌شود** — حتی اگر کار
واقعاً انجام شده باشد. این عمداً محافظه‌کارتر از واقعیت است: یک عملِ انجام‌شدهٔ
بی‌رسید در بدترین حالت دوباره اجرا می‌شود (و idempotency جلویش را می‌گیرد)،
ولی یک `EXECUTED` ِ بی‌شاهد وارد کارتِ نمره می‌شود و «تکمیل» جعل می‌کند.

نوشتن اتمیک و **محدود به namespace خودِ پل** است — عمداً از
`opslib.LockedJson` استفاده نمی‌کند: آن ماژول امروز روی `_ops/state/` با
`WinError 5` شکست می‌خورد (VQ-OBS-REPLACE-001) و پلِ اقدام نباید به مشکلی که
هنوز تشخیصش باز است گره بخورد.

$0 · stdlib · فقط داخلِ sandbox می‌نویسد.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import contracts


def _atomic_write(path: Path, text: str) -> dict:
    """نوشتنِ اتمیکِ محلی + یک retry. شکست = صریح، نه بلعیده.

    retry ِ محدود عمدی است: علتِ شناخته‌شدهٔ شکستِ `os.replace` روی این ماشین
    هندلِ گذرای یک خوانندهٔ دیگر است. اگر بارِ دوم هم نشد، دروغ نمی‌گوییم."""
    last = None
    for attempt in (1, 2):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + f".tmp{attempt}")
            tmp.write_text(text, encoding="utf-8")
            os.replace(tmp, path)
            return {"ok": True, "attempts": attempt}
        except OSError as e:
            last = f"{type(e).__name__}: {e}"
            try:
                tmp.unlink()
            except OSError:
                pass
    return {"ok": False, "error": last}


def write(rec: dict, *, receipts_dir) -> dict:
    """رسید را بنشان. خروجی: {ok, path, error}."""
    aid = str(rec.get("action_id") or "unknown")
    safe = "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in aid)[:80]
    p = Path(receipts_dir) / f"{safe}.json"
    r = _atomic_write(p, json.dumps(rec, ensure_ascii=False, indent=1))
    return {"ok": r["ok"], "path": str(p) if r["ok"] else None,
            "error": r.get("error")}


def append_ledger(rec: dict, *, ledger_path) -> dict:
    """دفترِ append-only ِ همهٔ رسیدها — سریِ زمانیِ «چه شد»."""
    try:
        p = Path(ledger_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return {"ok": True}
    except OSError as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def finalize(rec: dict, *, receipts_dir, ledger_path) -> dict:
    """رسید را بنویس و در صورتِ شکست، وضعیت را **پایین** بیاور.

    `EXECUTED → FAILED` وقتی رسید ننشیند. `BLOCKED`/`REJECTED`/`NOOP` دست‌نخورده
    می‌مانند: آن‌ها ادعای انجامِ کاری ندارند، پس نبودِ رسید ادعایشان را باطل
    نمی‌کند — فقط در `errors` ثبت می‌شود."""
    w = write(rec, receipts_dir=receipts_dir)
    a = append_ledger(rec, ledger_path=ledger_path)
    if w["ok"] and a["ok"]:
        return {"ok": True, "receipt": rec, "path": w["path"]}
    errs = [e for e in (w.get("error"), a.get("error")) if e]
    out = dict(rec)
    out["errors"] = list(out.get("errors") or []) + ["receipt-write-failed"] + errs
    if out.get("status") == "EXECUTED":
        out["status"] = "FAILED"
        out["errors"].append("status-downgraded: عملِ بی‌رسید اثباتِ انجام ندارد")
    return {"ok": False, "receipt": out, "path": w.get("path")}


def new(**kw) -> dict:
    return contracts.new_receipt(**kw)
