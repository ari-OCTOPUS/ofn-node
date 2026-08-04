#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reach_probe.py — «کدام کد **واقعاً** دویده؟» با کتابخانهٔ استاندارد.

    مسئله‌ای که این حل می‌کند
    ─────────────────────────
    `orphan_scan.py` یک حدس‌زنِ **ایستا** است و در docstring ِ خودش نوشته
    «عمداً محافظه‌کار است و کم‌گزارش می‌دهد». یک بار ۳۱ مثبتِ کاذب داد چون
    `card()` و لانچرهای `.bat` را مدل نمی‌کرد. تحلیلِ ایستا ذاتاً نمی‌تواند
    بگوید چه چیزی اجرا شد — فقط می‌تواند حدس بزند چه چیزی **قابلِ** اجراست.

    `sys.monitoring` (PEP 669، پایتون ۳.۱۲+) سؤال را از حدس به واقعیت
    می‌برد: مفسر بارِ اولی که هر تابع اجرا می‌شود یک رویداد می‌دهد، و
    callback با برگرداندنِ `DISABLE` می‌گوید «دیگر این یکی را خبرم نکن».
    پس هزینه بعد از گرم‌شدن به صفر میل می‌کند — هر تابع در کلِ عمرِ پروسه
    دقیقاً **یک** callback دارد.

    نتیجهٔ عملی برای مالک: «زدم و هیچ نشد» از یک حس به یک حقیقتِ دوحالته
    تبدیل می‌شود — نامِ handler بعد از تپِ تو در دفتر آمد، یا نیامد.

    ⚠️ سه قیدِ سختِ طراحی
    ─────────────────────
    ۱. **غیاب ≠ «هرگز نپرید».** نبودِ یک نام در دفتر دو معنیِ کاملاً متفاوت
       دارد: یا واقعاً اجرا نشد، یا **پروب در آن پروسه نصب نبود**. رندرکردنِ
       دومی به‌عنوان «یتیم» همان صفرِ جعلی است که منشور ممنوع کرده. پس هر
       پروسه هنگامِ نصب یک ردیفِ provenance می‌نویسد، و خواننده بدونِ آن
       ردیف باید **UNKNOWN** بگوید نه «نپرید».
    ۲. **فقط نام، هرگز مقدار.** callback فقط `co_qualname` و `co_filename`
       را می‌گیرد. نه آرگومان، نه متغیرِ محلی، نه مقدارِ بازگشتی — چون
       همان‌جاست که یک secret به لاگ می‌رسد (منشور §۱۰).
    ۳. **دیسکِ مکانیکی.** این لپ‌تاپ ۵۴۰۰ دور است و یک بار `du` نُه دقیقه
       طول کشید. پس هیچ نوشتنی در callback نیست: در RAM جمع می‌شود و روی
       ضربان/atexit یک بار flush می‌شود.
"""
from __future__ import annotations

import atexit
import json
import os
import sys
import threading
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent

#: فلگ — پیش‌فرض خاموش. بدونِ آن این ماژول یک no-op ِ مطلق است.
FLAG = "OCTOPUS_REACH"
#: شناسهٔ ابزارِ sys.monitoring. ۰–۵ آزادند؛ ۳ انتخاب شد چون coverage.py
#: معمولاً ۰ یا ۱ می‌گیرد و اگر روزی داخلِ همین پروسه بدود تصادم نکنیم.
#: ⚠️ هر شناسه فقط **یک** مالک دارد؛ تصادم یعنی یکی‌شان کور می‌شود.
TOOL_ID = 3
TOOL_NAME = "octopus-reach"

LEDGER = _HERE / "state" / "reach" / "ledger.jsonl"
PROVENANCE = _HERE / "state" / "reach" / "probes.jsonl"

#: فقط کدِ خودِ اختاپوس. بدونِ این فیلتر، هر تابعِ stdlib و هر کتابخانه هم
#: ثبت می‌شود و دفتر بی‌فایده و بزرگ می‌شود.
ROOT = str(_HERE).lower()

_seen: "set[str]" = set()
_lock = threading.Lock()
_installed = False
_install_ts = 0.0


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def _proc_name() -> str:
    """نامِ پروسه — از env اگر صداکننده گفته، وگرنه نامِ اسکریپت."""
    n = os.environ.get("OCTOPUS_PROC_NAME", "").strip()
    if n:
        return n
    try:
        return Path(sys.argv[0]).stem or "python"
    except Exception:  # noqa: BLE001
        return "python"


def _cb(code, offset):
    """callback ِ PY_START. بایدِ مطلق: **سریع** و **بی‌استثنا**.

    هر استثنا این‌جا داخلِ مفسر بالا می‌رود و می‌تواند پروسه را بکشد، پس
    کلِ بدنه در try است و در بدترین حالت DISABLE برمی‌گرداند.
    """
    try:
        fn = code.co_filename
        # فیلترِ ارزان **قبل از** هر کارِ دیگر
        if not fn or not fn.lower().startswith(ROOT):
            return sys.monitoring.DISABLE
        key = f"{fn}::{code.co_qualname}"
        if key not in _seen:
            with _lock:
                _seen.add(key)
    except Exception:  # noqa: BLE001
        pass
    # ⚠️ همیشه DISABLE: هر تابع در کلِ عمرِ پروسه یک بار callback می‌گیرد.
    # بدونِ این، هزینه به ~۲۰۰۰٪ می‌رسد (همان چیزی که sys.settrace بود).
    return sys.monitoring.DISABLE


def install() -> dict:
    """پروب را نصب کن و یک ردیفِ **provenance** بنویس.

    آن ردیف باربر است: بدونش خوانندهٔ دفتر نمی‌تواند «اجرا نشد» را از
    «پروب نصب نبود» جدا کند، و همان جدایی کلِ ارزشِ این ابزار است.
    """
    global _installed, _install_ts
    if _installed:
        return {"ok": True, "already": True}
    if not enabled():
        return {"ok": False, "reason": "flag off"}
    m = getattr(sys, "monitoring", None)
    if m is None:
        return {"ok": False, "reason": "sys.monitoring unavailable (need py3.12+)"}
    try:
        owner = m.get_tool(TOOL_ID)
        if owner is not None:
            # تصادم: شناسه مالکِ دیگری دارد. **ننشین رویش** — یکی‌شان کور
            # می‌شود و بدتر از نداشتنِ پروب است.
            return {"ok": False, "reason": f"tool id {TOOL_ID} owned by {owner!r}"}
        m.use_tool_id(TOOL_ID, TOOL_NAME)
        m.register_callback(TOOL_ID, m.events.PY_START, _cb)
        m.set_events(TOOL_ID, m.events.PY_START)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}
    _installed = True
    _install_ts = time.time()
    rec = {"ts": _install_ts, "pid": os.getpid(), "proc": _proc_name(),
           "py": sys.version.split()[0], "probe": "reach.v1", "root": str(_HERE)}
    _append(PROVENANCE, rec)
    atexit.register(flush)
    return {"ok": True, **rec}


def _append(path: Path, rec: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — دفتر هرگز پروسه را نمی‌کشد
        pass


def flush() -> int:
    """آنچه از آخرین flush تازه دیده شده را بنویس. برمی‌گرداند: چندتا.

    روی ضربان صدا زده می‌شود، و atexit. **هرگز** در callback — دیسکِ
    مکانیکی همان چیزی است که یک بار `du` را نُه دقیقه‌ای کرد.
    """
    if not _installed:
        return 0
    with _lock:
        fresh = sorted(_seen)
        _seen.clear()
    if not fresh:
        return 0
    pid, proc, ts = os.getpid(), _proc_name(), time.time()
    for key in fresh:
        fn, _, qual = key.partition("::")
        try:
            rel = str(Path(fn).relative_to(_HERE)).replace("\\", "/")
        except ValueError:
            rel = fn
        _append(LEDGER, {"ts": ts, "pid": pid, "proc": proc,
                         "file": rel, "qual": qual})
    return len(fresh)


def probed_processes(since_s: float = 7 * 86400) -> dict:
    """کدام پروسه‌ها **پروب داشتند**؟ کلیدِ تفکیکِ UNKNOWN از «نپرید»."""
    out: dict = {}
    try:
        cutoff = time.time() - since_s
        for line in PROVENANCE.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if float(r.get("ts") or 0) >= cutoff:
                out.setdefault(str(r.get("proc") or "?"), []).append(r)
    except Exception:  # noqa: BLE001
        return {}
    return out


def reached(since_s: float = 7 * 86400) -> set:
    """مجموعهٔ `file::qual` هایی که در پنجره واقعاً دویده‌اند."""
    out = set()
    try:
        cutoff = time.time() - since_s
        for line in LEDGER.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if float(r.get("ts") or 0) >= cutoff:
                out.add(f"{r.get('file')}::{r.get('qual')}")
    except Exception:  # noqa: BLE001
        return set()
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # type: ignore[attr-defined]
    os.environ.setdefault(FLAG, "1")
    print("نصب:", json.dumps(install(), ensure_ascii=False))

    # خودآزمون: یک تابعِ واقعی صدا بزن و ببین در دفتر می‌آید یا نه.
    def _demo_target():
        return 42

    _demo_target()
    n = flush()
    hits = reached(since_s=60)
    mine = [h for h in hits if "_demo_target" in h]
    print(f"flush: {n} ردیف")
    print(f"خودِ تابعِ آزمایشی در دفتر: {'✅ ' + mine[0] if mine else '❌ نیامد'}")
    print(f"پروسه‌های پروب‌دار: {list(probed_processes(60))}")
