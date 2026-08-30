#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stall_probe.py — وقتی مرکز هنگ کرد، بگو **کجا** گیر کرده بود.

مسئله‌ای که می‌بندد (۲۰۲۶-۰۸-۰۴)
─────────────────────────────────
مرکز امروز **دو بار** هنگ کرد، هر بار ~۲٫۵ ساعت:

    09:52  centre down (silent 9238s)
    12:37  centre HUNG (alive, silent 9239s) - killing pid 10824

«alive» یعنی پروسه بود و نفس نمی‌کشید — نه کرش، هنگ. واچ‌داگ درست تشخیص داد
و کشتش. ولی **چرا** هنگ کرده بود؟ هیچ‌کس نمی‌داند، و ساختاراً هم نمی‌توانست
بداند:

    RUN-TG-CENTER.bat →  python -X utf8 telegram_center\\center.py
                         ↑ بدونِ هیچ ریدایرکتی

یعنی stdout/stderr ِ مرکز هیچ‌جا نمی‌رود. هر traceback، هر پیامِ خطا، هر
نشانهٔ گیرکردن — نامرئی. کشتنِ یک پروسهٔ هنگ‌کرده بدونِ برداشتنِ ردِ پایش،
همان حادثه را فردا تکرارپذیر می‌کند.

آنچه این ماژول می‌کند
──────────────────────
یک نخِ دیده‌بان که نبضِ روی دیسک را می‌پاید — **همان فایلی که واچ‌داگِ بیرونی
می‌خواند**، تا دو ناظر یک حقیقت را ببینند نه دو تا. اگر نبض کهنه شد، پشتهٔ
**همهٔ نخ‌ها** را در یک فایل می‌ریزد.

⚠️ زمان‌بندی باربر است: آستانه باید **زیرِ** آستانهٔ کشتنِ واچ‌داگ باشد
(۳۰۰ ثانیه)، وگرنه پروسه قبل از نوشتنِ پشته کشته می‌شود و باز هیچ نمی‌فهمیم.
۲۴۰ < ۳۰۰ عمدی است، نه دلبخواه.

ناوردی‌ها: stdlib-only · صفر شبکه · daemon (هرگز جلوی خروج را نمی‌گیرد) ·
fail-soft مطلق (دیده‌بان هرگز مرکز را نمی‌کشد) · هرگز متنِ پیام یا secret
نمی‌نویسد — فقط پشتهٔ کد.
"""
from __future__ import annotations

import faulthandler
import json
import os
import sys
import threading
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

SCHEMA = "stall-probe.v1"

#: ⚠️ **زیرِ** آستانهٔ کشتنِ واچ‌داگ (۳۰۰s در tg-center-watchdog.ps1). اگر این
#: عدد از آن بالاتر برود، پروسه قبل از نوشتنِ پشته کشته می‌شود و این ماژول
#: بی‌فایده است. تستِ t_threshold_is_below_the_killer این را قفل می‌کند.
STALL_AFTER_S = 240.0
POLL_S = 20.0
#: بین دو ریختِ پشته در **یک** اپیزودِ هنگ. بدونِ این، هر ۲۰ ثانیه یک پشته
#: می‌نویسد و فایل را می‌ترکاند — گاردی که گرگ‌گرگ کند خاموش می‌شود.
REDUMP_EVERY_S = 900.0
MAX_BYTES = 2_000_000


def pulse_path() -> Path:
    return opslib.STATE_DIR / "pulse" / "tg-center.json"


def dump_path() -> Path:
    return opslib.STATE_DIR / "telegram" / "stall-traceback.txt"


def pulse_age_s(*, now: "float | None" = None) -> "float | None":
    """چند ثانیه از آخرین نبض. None = نبض خوانا نیست (بی‌خبری، نه سلامت).

    عمداً از **همان فایلی** خوانده می‌شود که واچ‌داگِ بیرونی می‌خواند: دو
    ناظر با دو منبعِ حقیقت، روزی دو حکمِ متضاد می‌دهند."""
    try:
        p = pulse_path()
        if not p.exists():
            return None
        d = json.loads(p.read_text("utf-8"))
        import datetime as _dt
        ts = _dt.datetime.fromisoformat(str(d.get("ts"))).timestamp()
        return float(now if now is not None else time.time()) - ts
    except (OSError, ValueError, TypeError):
        return None


def write_dump(reason: str, *, age: "float | None" = None) -> bool:
    """پشتهٔ همهٔ نخ‌ها → فایل. هرگز استثنا."""
    try:
        p = dump_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        # چرخش: یک فایلِ بی‌سقف روی دیسکِ مکانیکی خودش یک حادثه است
        try:
            if p.exists() and p.stat().st_size > MAX_BYTES:
                p.write_text("", encoding="utf-8")
        except OSError:
            pass
        head = (f"\n{'=' * 68}\n"
                f"{opslib.now_iso()}  pid={os.getpid()}  reason={reason}"
                f"  pulse_age={'?' if age is None else round(age)}s\n"
                f"{'=' * 68}\n")
        # ⚠️ راهنمای نام‌ها. `faulthandler` فقط `Thread 0x…` می‌نویسد — شناسهٔ
        # هگز، بدونِ نام. برای جوابِ «کدام لِن گیر کرده؟» نام همه‌چیز است، و
        # بدونِ این جدول باید شناسهٔ هگز را با چشم به نخ‌ها وصل کنی. تستِ
        # t_f این را کشف کرد: پشته درست بود ولی **ناخوانا**.
        try:
            legend = "\n".join(
                f"  0x{t.ident:08x}  {t.name}{' (daemon)' if t.daemon else ''}"
                for t in threading.enumerate() if t.ident is not None)
            head += f"نخ‌ها:\n{legend}\n{'-' * 68}\n"
        except Exception:  # noqa: BLE001
            pass
        with open(p, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(head)
            fh.flush()
            # ⚠️ all_threads باربر است: نخِ **اصلی** ممکن است سالم باشد و یک
            # لِنِ پس‌زمینه گیر کرده باشد؛ پشتهٔ تک‌نخی آن را نشان نمی‌دهد.
            faulthandler.dump_traceback(file=fh, all_threads=True)
            fh.flush()
        return True
    except Exception:  # noqa: BLE001 — دیده‌بان هرگز مرکز را نمی‌کشد
        return False


#: هندلِ بازِ فایلِ کرش. `faulthandler.enable` یک fd ِ **زنده** می‌خواهد؛ اگر
#: فایل بسته شود، کرشِ سخت دوباره بی‌رد می‌شود.
_crash_fh = None


def crash_path() -> Path:
    return opslib.STATE_DIR / "telegram" / "center-crash.log"


def install_crash_log() -> bool:
    """هر استثنای نگرفته، هر کرشِ نخ، و هر کرشِ سخت → فایل.

    چرا لازم است (۲۰۲۶-۰۸-۰۴): `RUN-TG-CENTER.bat` مرکز را با
    `Start-Process -WindowStyle Hidden` بالا می‌آورد و هیچ ریدایرکتی ندارد،
    پس stdout/stderr به **هیچ‌جا** نمی‌رود. تاریخچهٔ واچ‌داگ چند بار
    «centre+loop both down» دارد — یعنی کرش رخ داده و traceback ِ آن برای
    همیشه گم شده.

    عمداً در پایتون و نه در .bat: آن فایل باربر است و اگر نحوش بشکند مرکز
    اصلاً بالا نمی‌آید — بدترین نتیجهٔ ممکن برای مشکلی که «دیده نمی‌شوم» است.

    سه لایه، چون سه راهِ متفاوتِ مردن وجود دارد:
      · `sys.excepthook`        — استثنای نگرفته در نخِ اصلی
      · `threading.excepthook`  — استثنا در لِن‌های پس‌زمینه (وگرنه فقط روی
                                  stderr ِ گم‌شده چاپ می‌شود)
      · `faulthandler.enable`   — کرشِ سخت (segfault و امثالش)
    """
    global _crash_fh
    try:
        p = crash_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            if p.exists() and p.stat().st_size > MAX_BYTES:
                p.write_text("", encoding="utf-8")
        except OSError:
            pass
        _crash_fh = open(p, "a", encoding="utf-8", newline="\n")
        faulthandler.enable(file=_crash_fh, all_threads=True)

        def _hook(exc_type, exc, tb, _thread=None):
            try:
                import traceback as _tb
                _crash_fh.write(
                    f"\n{'=' * 68}\n{opslib.now_iso()}  pid={os.getpid()}  "
                    f"{'thread=' + str(_thread) + '  ' if _thread else ''}"
                    f"UNCAUGHT {exc_type.__name__}\n{'=' * 68}\n")
                _tb.print_exception(exc_type, exc, tb, file=_crash_fh)
                _crash_fh.flush()
            except Exception:  # noqa: BLE001
                pass

        sys.excepthook = _hook
        threading.excepthook = lambda a: _hook(
            a.exc_type, a.exc_value, a.exc_traceback,
            getattr(a.thread, "name", "?"))
        return True
    except Exception:  # noqa: BLE001 — ثبت هرگز مرکز را نمی‌کشد
        return False


def _loop(stop_evt: "threading.Event", *, stall_after_s: float,
          poll_s: float, redump_every_s: float) -> None:
    last_dump = 0.0
    while not stop_evt.is_set():
        try:
            age = pulse_age_s()
            if age is not None and age >= stall_after_s:
                now = time.time()
                if now - last_dump >= redump_every_s:
                    last_dump = now
                    write_dump("pulse-stalled", age=age)
        except Exception:  # noqa: BLE001
            pass
        stop_evt.wait(poll_s)


def start(*, stall_after_s: float = STALL_AFTER_S, poll_s: float = POLL_S,
          redump_every_s: float = REDUMP_EVERY_S) -> "threading.Event | None":
    """دیده‌بان را روشن کن. خروجی: رویدادِ توقف (یا None اگر نشد).

    daemon=True: هرگز جلوی خاموش‌شدنِ مرکز را نمی‌گیرد."""
    try:
        evt = threading.Event()
        th = threading.Thread(target=_loop, args=(evt,),
                              kwargs={"stall_after_s": float(stall_after_s),
                                      "poll_s": float(poll_s),
                                      "redump_every_s": float(redump_every_s)},
                              name="stall-probe", daemon=True)
        th.start()
        return evt
    except Exception:  # noqa: BLE001
        return None


def tail(n: int = 60) -> str:
    try:
        p = dump_path()
        if not p.exists():
            return "(هیچ پشته‌ای ثبت نشده — یعنی از وقتی این ماژول زنده شده، هنگی نبوده)"
        return "\n".join(p.read_text("utf-8", errors="replace").splitlines()[-n:])
    except OSError as e:
        return f"(خواندنِ فایل ناموفق: {type(e).__name__})"


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps({"pulse": str(pulse_path()), "dump": str(dump_path()),
                      "pulse_age_s": pulse_age_s(),
                      "stall_after_s": STALL_AFTER_S}, ensure_ascii=False, indent=2))
    print("\n" + tail(40))
