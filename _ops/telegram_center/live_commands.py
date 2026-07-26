#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""live_commands.py — دستورهای زنده‌سازی از تلگرام (read-only / propose-only).

جدا از center.py تا پچِ hub کوچک بماند. center فقط:
    import live_commands as lc
    if lc.handles(text): return lc.dispatch(text)

دستورها:
  /id | /eq | هویت        → identity_equations.card / detail
  /box | جعبه | blackbox  → blackbox_map.card / detail
  /code | /کد             → collab_coding.handle_command
  /live | زنده            → خلاصهٔ زنده‌بودن (flags + identities + boxes)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "tg"), str(_HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

# ── حالتِ خلوت (OCTOPUS_TG_QUIET) ───────────────────────────────────────────
# بریفِ مالک ۲۰۲۶-۰۷-۲۶: «خلوت و برای ذهنِ ADHD کار کند».
# `/live` امروز ۱۷۴۶ کاراکتر است چون **کلِ `/id` و `/box` را داخلِ خودش تکرار
# می‌کند** — یعنی سه گزارش در یک پیام. سقفِ طراحیِ card_render برای همین ۷۰۰ است.
# محتوا ساده نمی‌شود؛ فقط تکرار و نویز حذف می‌شود (عددها کامل می‌مانند).
QUIET_FLAG = "OCTOPUS_TG_QUIET"


def quiet_on() -> bool:
    return str(os.environ.get(QUIET_FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def _fa_num(x, nd: int = 2) -> str:
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return "?"


def _norm(text: str) -> str:
    t = str(text or "").strip()
    if t.startswith("/"):
        t = t[1:]
    return t.strip()


def handles(text: str) -> bool:
    t = _norm(text).lower()
    if not t:
        return False
    heads = (
        "id", "eq", "identity", "هویت", "معادله",
        "box", "blackbox", "جعبه", "جعبه‌سیاه", "جعبه سیاه",
        "code", "کد", "collab",
        "live", "زنده", "pulse-id",
        "doctrine", "رفتار", "howto", "چطور",
    )
    first = t.split(None, 1)[0]
    return first in heads or any(t.startswith(h + " ") or t == h for h in heads)


def dispatch(text: str) -> str:
    """متن → پاسخ. هرگز raise؛ fail-soft."""
    try:
        return _dispatch(text)
    except Exception as e:  # noqa: BLE001
        return f"live_commands error (fail-soft): {type(e).__name__}: {e}"


def _dispatch(text: str) -> str:
    raw = str(text or "").strip()
    t = _norm(raw)
    low = t.lower()
    parts = t.split(None, 1)
    head = (parts[0] if parts else "").lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    # aliases
    if head in ("هویت", "معادله", "eq", "identity", "id", "pulse-id"):
        head = "id"
    elif head in ("جعبه", "جعبه‌سیاه", "جعبه سیاه", "blackbox", "box"):
        head = "box"
    elif head in ("کد", "collab", "code"):
        head = "code"
    elif head in ("زنده", "live"):
        head = "live"
    elif head in ("رفتار", "doctrine", "howto", "چطور"):
        head = "doctrine"

    if head == "id":
        import identity_equations as ie  # noqa: WPS433
        if arg:
            return ie.detail_card(arg)
        return ie.card()

    if head == "box":
        import blackbox_map as bm  # noqa: WPS433
        if arg:
            return bm.detail_card(arg)
        if quiet_on():
            q = _quiet_box()
            if q:
                return q
        return bm.card()

    if head == "code":
        import collab_coding as cc  # noqa: WPS433
        # re-prefix so collab parser sees /code ...
        return cc.handle_command("/code " + arg if arg else "/code status")

    if head == "doctrine":
        # «فکر می‌کنی چطور باید با من حرف بزنی؟» — همان دکترینی که به خودشناسی
        # تزریق می‌شود، عیناً. اگر این کارت با رفتارِ واقعیِ بات نخواند، یکی از
        # آن دو دروغ می‌گوید و مالک باید بتواند ببیندش.
        try:
            import operator_doctrine as _od  # noqa: WPS433
            return _od.card()
        except Exception as e:  # noqa: BLE001
            return f"دکترین در دسترس نیست: {type(e).__name__}"

    if head == "live":
        if quiet_on():
            q = _quiet_live()
            if q:
                return q
        return _live_summary()

    return "دستور ناشناخته. /live · /id · /box · /code"


# ── رندرِ خلوت ───────────────────────────────────────────────────────────────
# قرارداد: هر کدام یا یک کارتِ معتبر برمی‌گرداند یا "" — و "" یعنی «نسخهٔ کامل را
# بفرست». هیچ مسیری اینجا نباید به سکوت ختم شود: سکوتِ ناشی از یک قیدِ طراحی
# دقیقاً همان باگی است که ۲۰۲۶-۰۷-۲۵ ساعت ۲۲:۰۳ اتفاق افتاد (دستور بی‌پاسخ ماند).
def _flag_counts() -> tuple:
    on = sum(1 for v in _WIRE_FLAGS.values()
             if str(os.environ.get(v, "") or "").strip().lower()
             in ("1", "true", "yes", "on"))
    return on, len(_WIRE_FLAGS) - on


_WIRE_FLAGS = {
    "پژوهش": "OCTOPUS_WIRE_C6_RESEARCH",
    "تولیدِ فرضیه": "OCTOPUS_WIRE_C6_PRODUCER",
    "لیدِ مستقیم": "OCTOPUS_LEAD_DIRECT_RESIDENTIAL",
    "هم‌کدنویسی": "OCTOPUS_WIRE_COLLAB_CODING",
    "معادلهٔ هویت": "OCTOPUS_WIRE_IDENTITY_EQ",
    "دفترِ تز": "OCTOPUS_WIRE_THESIS_QUEUE",
    "انسجام": "OCTOPUS_WIRE_COHERENCE",
    "پروبِ آزمایشگاه": "OCTOPUS_WIRE_ROMAJAN_PROBES",
}


def _quiet_live() -> str:
    """`/live` در یک نگاه. خطای هر جنس → "" → نسخهٔ کامل (هرگز سکوت)."""
    try:
        import card_render as cr  # noqa: WPS433
        import identity_equations as ie  # noqa: WPS433

        ev = ie.evaluate() or {}
        idents = ev.get("identities") or {}
        sig = ev.get("signals") or {}
        on, off = _flag_counts()
        act = (_OPS / "ACTIVATION-C6-RESEARCH.flag").exists()

        org = (idents.get("organism") or {}).get("value")
        head = f"🐙 زنده‌ام — {_fa_num(org)} از 1.00" if org is not None else "🐙 زنده‌ام"

        rows = []
        others = [v for k, v in idents.items() if k != "organism"]
        if others:
            rows.append(" · ".join(
                f"{o.get('label', '?')} {_fa_num(o.get('value'))}" for o in others[:4]))
        d = sig.get("delta")
        if d is not None:
            tone = "منفی — و همین‌طور هم گزارش می‌شود" if float(d) < 0 else "مثبت"
            rows.append(f"رشدِ خودم {_fa_num(d, 4)} ({tone}) · n={sig.get('n_delta', 0)}")
        miss = sig.get("missing") or []
        if miss:
            rows.append("هنوز اندازه‌گیری نشده: " + "، ".join(str(m) for m in miss[:3]))
        dark = [k for k, v in _WIRE_FLAGS.items()
                if str(os.environ.get(v, "") or "").strip().lower()
                not in ("1", "true", "yes", "on")]
        if dark:
            rows.append("خاموش: " + "، ".join(dark[:4])
                        + (f" (+{len(dark) - 4})" if len(dark) > 4 else ""))

        lead = (f"{off} توانایی خاموش، {on} روشن"
                + ("، و کلیدِ پژوهش روی میز است" if act else ""))
        return cr.render_info(
            headline=head, lead=lead, rows=rows,
            next_step="کاملش: /id · جعبه‌ها: /box · روشن‌کردنشان فقط با تو",
        )["text"]
    except Exception:  # noqa: BLE001 — fail-soft به نسخهٔ کامل، نه به سکوت
        return ""


# ژارگونِ ماشینیِ کاتالوگ → معنیِ فارسی. کارتِ خلوت متنِ خام را پاس نمی‌دهد چون
# card_render واژهٔ بی‌ترجمه را ساختاراً رد می‌کند (و درست هم می‌کند: «flag-off» به
# مالک نمی‌گوید *واقعاً* چه شده). این جدول ترجمه است، نه ساده‌سازی.
_DEJARGON = (
    ("flag-off", "خاموش"),
    ("PRODUCER flag", "کلیدِ تولیدِ فرضیه"),
    ("flag", "کلیدِ روشن/خاموش"),
    ("NO GIT", "بدونِ تاریخچه"),
    ("DEPRECATED", "بازنشسته"),
    ("unused organ", "اندامِ بی‌استفاده"),
)


def _dejargon(s: str) -> str:
    out = str(s or "")
    for src, dst in _DEJARGON:
        out = out.replace(src, dst)
    return out


def _quiet_box() -> str:
    """`/box` در یک نگاه: هر جعبه یک خط. خطا → "" → نسخهٔ کامل."""
    try:
        import card_render as cr  # noqa: WPS433
        import blackbox_map as bm  # noqa: WPS433

        s = bm.survey() or {}
        items = list(s.get("items") or [])
        rows = []
        for it in items[:cr.MAX_INFO_ROWS]:
            name = str(it.get("id") or "?").replace("_", " ")
            risk = _dejargon((it.get("risks") or [""])[0])
            risk = risk.split("—")[0].strip()[:52]
            rows.append(f"{name}: {risk}" if risk else name)
        missing = sum(1 for it in items if not (it.get("exists", True)))
        lead = (f"{len(items)} جعبه، همه سرِ جایشان" if not missing
                else f"{len(items)} جعبه، {missing} تا گم شده")
        return cr.render_info(
            headline="📦 جعبه‌سیاه‌ها", lead=lead, rows=rows,
            next_step="جزئیاتِ یکی: /box سپس نامش",
        )["text"]
    except Exception:  # noqa: BLE001
        return ""


def _live_summary() -> str:
    flags = {
        "C6_RESEARCH": os.environ.get("OCTOPUS_WIRE_C6_RESEARCH"),
        "C6_PRODUCER": os.environ.get("OCTOPUS_WIRE_C6_PRODUCER"),
        "LEAD_DIRECT": os.environ.get("OCTOPUS_LEAD_DIRECT_RESIDENTIAL"),
        "COLLAB": os.environ.get("OCTOPUS_WIRE_COLLAB_CODING"),
        "IDENTITY_EQ": os.environ.get("OCTOPUS_WIRE_IDENTITY_EQ"),
        "THESIS_Q": os.environ.get("OCTOPUS_WIRE_THESIS_QUEUE"),
        "COHERENCE": os.environ.get("OCTOPUS_WIRE_COHERENCE"),
        "ROMAJAN_PROBES": os.environ.get("OCTOPUS_WIRE_ROMAJAN_PROBES"),
    }
    act = (_OPS / "ACTIVATION-C6-RESEARCH.flag").exists()
    lines = ["🐙 LIVE summary", "flags:"]
    for k, v in flags.items():
        on = str(v or "").strip().lower() in ("1", "true", "yes", "on")
        lines.append(f"  {'✅' if on else '⚪'} {k}={v or '0'}")
    lines.append(f"  {'✅' if act else '⚪'} ACTIVATION-C6-RESEARCH.flag")
    try:
        import identity_equations as ie  # noqa: WPS433
        lines.append("")
        lines.append(ie.card(focus="organism"))
    except Exception as e:  # noqa: BLE001
        lines.append(f"identity: {type(e).__name__}")
    try:
        import blackbox_map as bm  # noqa: WPS433
        lines.append("")
        lines.append(bm.card())
    except Exception as e:  # noqa: BLE001
        lines.append(f"blackbox: {type(e).__name__}")
    lines.append("")
    lines.append(
        "برای زنده‌شدنِ کامل: "
        "OCTOPUS_WIRE_C6_PRODUCER=1 + LEAD_DIRECT=1 + COLLAB=1 + "
        "IDENTITY_EQ=1 + restart. "
        "OCTOPUS_CB_SECRET فقط با مالک."
    )
    return "\n".join(lines)
