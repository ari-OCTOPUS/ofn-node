#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""studio_pf_leg.py — پای Project-F (کدِ cross-domain: «Project-F»، هرگز نامِ پروژه/هویت).

**چرا این فایل وجود دارد** (رأیِ مالک ۲۰۲۶-۰۸-۰۳: «هرکاری می‌کنن اختاپوس یادش بمونه»):
تا امروز `studio_pf` در `ORGANISM-STATE.business_legs` **غایب** بود، در حالی که ۱۲ ماژول
آن فهرست را می‌خوانند (doctor · self_knowledge · self_accuracy · organism · weekly_review ·
render · miniapp_state · brain_worker · budget_judge · approval_channel · lead_leg ·
leg_room_report). یعنی این پا نه زنده گزارش می‌شد نه مرده — **در خودآگاهیِ ارگانیسم
اصلاً وجود نداشت**. همان استدلالی که در `_BUSINESS_LEGS_SPEC` برای افزودنِ `lead`
ثبت شده («خودآگاهیِ ارگانیسم پاهای مرده را می‌شمرد و کسب‌وکارِ واقعی را نمی‌دید»).

قرارداد مشترکِ پاها — helperِ فقط‌خواندنیِ سطحِ ماژول:
    studio_pf_status() -> {"leg","live","signal","note", ...}

**مرزِ سخت (قاعدهٔ قفل‌شدهٔ #۷ پروژه):** بیرون از پوشهٔ پروژه فقط aggregate/count.
این ماژول **هیچ فیلدِ متنی‌ای** از صف‌ها نمی‌خوانَد — نه hook، نه کپشن، نه بدنهٔ DM،
نه نامِ فایلِ رسانه، نه هویت. فقط شمار، وضعیت، و بولی‌های گیت. هم‌راستا با schema ِ
`05_OCTOPUS_ADAPTER_SHADOW` و با `_ops/telegram_center/pf_miniapp.py` (همان منبع، همان مرز).

صداقتِ سه‌حالتی: فایلِ غایب/خراب ⇒ `None` و نامِ فیلد در `unknown` — **نه صفرِ جعلی**
و نه «همه‌چیز امن» (درسِ «نبودِ داده حکم نیست»).

`live` یعنی چه: این پا وقتی `live=True` است که **اجرای بیرونی مجاز باشد** — یعنی مهرِ
انسانیِ `GATE-STAMP-GO` روی دیسک باشد. تا آن لحظه صادقانه `live=False` با سیگنالِ
`gated` گزارش می‌شود؛ این «مرده» نیست، «عمداً قفل» است و تفاوتش در `note` می‌آید.

صفر side-effect · صفر secret · stdlib-only · $0 آفلاین · هرگز crash نمی‌کند.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

_OPS = _HERE.parent
VAULT = _OPS.parent
# نامِ پوشه فارسی است؛ در هر خروجی/لاگ فقط کدِ «Project-F» استفاده می‌شود.
PF_ROOT = VAULT / "03 - Projects" / "اونلی فنز"

_MAX_JSON_BYTES = 2_000_000        # فایلِ غول = نمی‌خوانیم (گاردِ حافظه/AV)


def _read_json(path: Path):
    """(data, reason). هرگز استثنا بیرون نمی‌دهد؛ هرگز فایلِ بزرگ را کامل نمی‌خواند."""
    try:
        if not path.exists():
            return None, "missing"
        if path.stat().st_size > _MAX_JSON_BYTES:
            return None, "too_large"
        return json.loads(path.read_text(encoding="utf-8", errors="replace")), None
    except json.JSONDecodeError:
        return None, "corrupt"
    except OSError:
        return None, "unreadable"
    except Exception:  # noqa: BLE001 — شک = ناموجود
        return None, "error"


def _items(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("items", "queue", "drafts"):
            v = data.get(k)
            if isinstance(v, list):
                return v
    return []


def _count_status(data, wanted: str):
    """شمارِ آیتم‌های دارای وضعیتِ خواسته‌شده — فقط عدد، هیچ محتوایی لمس نمی‌شود."""
    n = 0
    for it in _items(data):
        if isinstance(it, dict) and str(it.get("status", "")) == wanted:
            n += 1
    return n


def studio_pf_status() -> dict:
    """snapshotِ فقط‌خواندنی و content-free ِ پای Project-F. هرگز crash نمی‌کند."""
    leg = "studio_pf"
    unknown: list = []

    if not PF_ROOT.exists():
        return {"leg": leg, "live": False, "signal": "absent",
                "note": "پوشهٔ Project-F روی این درخت نیست — پا غایب گزارش شد (نه صفرِ جعلی).",
                "unknown": ["project_root:missing"], "outward_execution": False,
                "content_free": True}

    acq, r_a = _read_json(PF_ROOT / "brain" / "acq_queue.json")
    dm, r_m = _read_json(PF_ROOT / "brain" / "dm_queue.json")
    drafts, r_d = _read_json(PF_ROOT / "studio" / "drafts.json")

    def _n(data, reason, field, wanted):
        if reason is not None:
            unknown.append(f"{field}:{reason}")
            return None
        return _count_status(data, wanted)

    acq_ready = _n(acq, r_a, "acq_ready", "ready")
    acq_drafted = _n(acq, r_a, "acq_drafted", "drafted")
    dm_pending = _n(dm, r_m, "dm_pending", "pending_review")
    drafts_pending = _n(drafts, r_d, "drafts_pending", "pending")

    # کلیدهای کشتار/توقف — وجودِ فایل، بدونِ خواندنِ محتوا
    killed = (PF_ROOT / "langar" / "KILL").exists()
    halted = (PF_ROOT / "studio" / "HALT").exists()
    paused = (_OPS / "state" / "projectf-paused.flag").exists()
    # تنها مهرِ انسانی که دروازهٔ اجرای بیرونی را باز می‌کند (فقط مالک می‌سازدش)
    stamp_go = (PF_ROOT / "00 - Control" / "GATE-STAMP-GO").exists()

    if killed:
        signal, note = "killed", "کلیدِ کشتارِ کاکپیت (KILL) روی دیسک است."
    elif halted:
        signal, note = "halted", "مرزِ سازنده فعال است (HALT) — مقدمِ مطلق."
    elif paused:
        signal, note = "paused", "پا از مرکز pause شده است (projectf-paused.flag)."
    elif not stamp_go:
        signal = "gated"
        note = ("عمداً قفل — GATE 0 باز است و مهرِ انسانیِ GATE-STAMP-GO روی دیسک نیست. "
                "propose-only: صف‌ها کار می‌کنند، اجرای بیرونی صفر است.")
    else:
        signal = "armed"
        note = "مهرِ انسانی هست؛ اجرای بیرونی همچنان دستیِ انسان است (هیچ auto-post/DM)."

    pending_total = sum(v for v in (acq_ready, acq_drafted, dm_pending, drafts_pending)
                        if isinstance(v, int))

    # ── پلِ رویداد: چند سطر نوشته شده و چند تا مصرف شده؟ ────────────────────
    # ۲۰۲۶-۰۸-۰۳: سنجیده شد که **هر پنج فلگِ pf_os در هر ۴ پروسهٔ زنده ABSENT است**
    # (تولیدکننده تاریک) و مصرف‌کنندهٔ `saba_bridge_beat` هم هیچ صداکننده‌ای در `_ops`
    # ندارد. پس هر رویدادی که این پا تولید کند **فراموش می‌شود**. عمداً مصرف‌کننده
    # سیم نشد (شنونده برای سکوت + نقضِ ADR ِ «pf_os قرنطینه»)؛ به‌جایش گپ را عددی
    # می‌کنیم تا اگر روزی تولیدکننده روشن شد، سکوتِ مصرف بلند فریاد بزند.
    bridge_rows = None
    bridge_cursor = None
    try:
        _bp = _OPS / "state" / "saba-bridge.jsonl"
        if _bp.exists():
            bridge_rows = sum(1 for _ln in _bp.read_text("utf-8", errors="replace").splitlines()
                              if _ln.strip())
        _cp = _OPS / "state" / "saba-bridge.cursor"
        bridge_cursor = int(_cp.read_text("utf-8").strip()) if _cp.exists() else 0
    except Exception:  # noqa: BLE001 — fail-soft: نامعلوم، نه صفرِ جعلی
        unknown.append("bridge:unreadable")

    return {
        "leg": leg,
        # صادقانه: تا وقتی مهرِ انسانی نیست، این پا «زنده»ی عملیاتی نیست.
        "live": bool(stamp_go and not (killed or halted or paused)),
        "signal": signal,
        "note": note + (f" · صفِ منتظر: {pending_total}" if unknown != ["project_root:missing"] else ""),
        # ── فقط aggregate (مرزِ #۷) ──
        "acq_ready": acq_ready,
        "acq_drafted": acq_drafted,
        "dm_pending": dm_pending,
        "drafts_pending": drafts_pending,
        "queue_total": pending_total,
        # پلِ حافظه: rows نوشته‌شده در برابر cursor ِ مصرف‌شده. cursor=0 با rows>0
        # یعنی «این پا حرف زده و هیچ‌کس نشنیده» — عمداً دیدنی شد، نه پنهان.
        "bridge_rows": bridge_rows,
        "bridge_cursor_bytes": bridge_cursor,
        "bridge_consumer_wired": False,   # سنجیده ۲۰۲۶-۰۸-۰۳: صفر صداکننده در _ops
        "producer_flags_live": False,     # سنجیده: هر ۵ فلگِ pf_os در ۴ snapshot غایب
        "gate_stamp_go": stamp_go,
        "kill_switches": {"KILL": killed, "HALT": halted, "paused": paused},
        "outward_execution": False,     # ساختاری: هیچ متدِ ارسال/انتشار در کلِ پروژه نیست
        "content_free": True,
        "unknown": unknown,
    }


if __name__ == "__main__":
    sys.stdout.buffer.write(
        json.dumps(studio_pf_status(), ensure_ascii=False, indent=2).encode("utf-8"))
