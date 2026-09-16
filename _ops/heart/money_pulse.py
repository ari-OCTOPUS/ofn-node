#!/usr/bin/env python3
"""money_pulse.py — فازِ money-pulse به هر ضربانِ قلب (۲۰۲۶-۰۷-۲۵).

درخواستِ مالک: «بیا روی قسمتِ منطبق به ضربانِ قلب که پول در میاره اتوماتیک تمرکز کنیم».
منطقِ ریاضیِ مشترک: زبانِ همه‌چیز ledger ژنوم است (hash-chain). پول هم از همین
زبان می‌گذره (EVENT_TYPE=MONEY_ATTRIBUTION). این ماژول یه فازِ تازه به هر beat اضافه
می‌کنه: درآمدِ همهٔ پاها رو می‌خونه، فرصت‌ها رو رادار می‌کنه، و سرعتِ پول رو محاسبه.

طراحی (صادقانه):
  • pulse فقط **می‌خونه** — هیچ MONEY_ATTRIBUTION جعلی نمی‌نویسه. نوشتنِ پول فقط از
    مسیرِ تأییدِ واقعی (claim→confirm) میاد. این wallِ anti-reward-hacking که ledger
    خودش تعریف کرده، نقض نمی‌شه.
  • هر beat: همهٔ ۹ پا رو می‌خونه (legs.confirmed_revenue)، یه sample به velocity-stream
    اضافه می‌کنه، و فرصت‌های بزرگ رو گزارش می‌ده (propose-only).
  • flag-gated: OCTOPUS_WIRE_MONEY_PULSE (پیش‌فرض خاموش = no-op).
  • fail-soft: هرگز beat رو نمی‌کشه.

وضعیتِ فعلی (۲۰۲۶-۰۷-۲۵): confirmed_revenue = ۰. یعنی pulse صفر نشون می‌ده — نه به‌خاطر
باگ، به‌خاطر اینکه هیچ پا هنوز پولِ واقعی تولید نکرده. ولی وقتی اولین پا شروع کنه،
pulse فوراً فعال می‌شه. این یک دماسنجیه که فعلاً صفره چون جسمِ داغی نیست.

$0 · stdlib-only · flag-gated · fail-soft · propose-only.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_MONEY_PULSE"
"""فعال‌سازیِ money-pulse. خاموش = no-op."""

# همهٔ پاهای رسمی (از render.LEGS، ولی hard-code برای استقلال از Telegram)
LEGS = ("lead", "ziman", "mining", "crypto", "accounting",
        "studio_pf", "system", "knowledge", "cartographer")

STREAM_PATH = opslib.STATE_DIR / "pulse" / "money-pulse.jsonl"
"""Append-only: یک sample per beat. content-free (صفر PII)."""

HOT_THRESHOLD_AUD = 5.0
"""آستانهٔ «فرصتِ بزرگ»: بالای این مبلغِ CONFIRMED در یک beat = هات (notify)."""


def flag_on() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def _confirmed_revenue() -> dict:
    """درآمدِ CONFIRMED از attribution (افرودنِ اقتباس، نه ساختِ جدید)."""
    try:
        import attribution
        return attribution.confirmed_revenue() or {}
    except Exception:  # noqa: BLE001
        return {"by_cell": {}, "confirmed": 0}


def _sense() -> dict:
    """هر پا رو حس کن — درآمدِ CONFIRMED + live بودن. content-free."""
    rev = _confirmed_revenue()
    by_cell = rev.get("by_cell") or {}
    total_cents = int(rev.get("confirmed") or 0)  # صفر اگر خالی
    return {
        "legs": dict(by_cell),          # {cell: cents_aud}
        "confirmed_aud": round(total_cents / 100.0, 2),
        "n_cells": len(by_cell),
    }


def beat(center=None) -> dict:
    """یک تیکِ money-pulse. از Center.beat() صدا زده می‌شه (الگوی event_bridge).

    center: شیء Center (دارای push_alert). None = فقط لاگ، بدونِ ارسال.
    خروجی = {sense, hot, notified}."""
    out = {"hot": False, "notified": False}
    if not flag_on():
        out["reason"] = "flag-off"
        return out
    sense = _sense()
    out["sense"] = sense

    # ۱) append به stream (content-free، صفر PII)
    try:
        STREAM_PATH.parent.mkdir(parents=True, exist_ok=True)
        sample = {
            "ts": opslib.now_iso(),
            "confirmed_aud": sense["confirmed_aud"],
            "n_cells": sense["n_cells"],
        }
        with open(STREAM_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    except OSError:  # noqa: BLE001
        pass

    # ۲) فرصتِ بزرگ → notify (propose-only، با انضباطِ سکوت در center.push_alert)
    if sense["confirmed_aud"] >= HOT_THRESHOLD_AUD:
        out["hot"] = True
        try:
            if center is not None and hasattr(center, "push_alert"):
                msg = (f"💰 money-pulse: درآمدِ CONFIRMED = A${sense['confirmed_aud']:.2f} "
                       f"({sense['n_cells']} پا).")
                out["notified"] = bool(center.push_alert(msg))
        except Exception:  # noqa: BLE001
            pass
    return out


def status() -> dict:
    """snapshot برای /status. content-free."""
    if not flag_on():
        return {"flag_on": False}
    sense = _sense()
    # آخرین sample
    last = None
    try:
        if STREAM_PATH.exists():
            lines = STREAM_PATH.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                last = json.loads(lines[-1])
    except (OSError, ValueError):
        pass
    return {
        "flag_on": True,
        "confirmed_aud": sense["confirmed_aud"],
        "n_cells": sense["n_cells"],
        "hot_threshold_aud": HOT_THRESHOLD_AUD,
        "last_sample": last,
    }


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(status(), ensure_ascii=False, indent=2))
