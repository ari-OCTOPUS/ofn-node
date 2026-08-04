#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""miniapp_registration.py — «در باز است» با «تلگرام درِ ما را می‌شناسد» یکی نیست.

مسئله‌ای که می‌بندد (فاز ۲، ۲۰۲۶-۰۸-۰۴)
────────────────────────────────────────
`owner_readiness._check_miniapp` تا امروز فقط دو چیز می‌سنجید: آدرس با
`https://` شروع می‌شود، و پورتِ گیت‌وی جواب می‌دهد. هر دو **دسترس‌پذیری**اند.
هیچ‌کدام نمی‌پرسند «آیا تلگرام اصلاً این اپ را می‌شناسد؟» — و جوابِ زندهٔ
امروز این بود:

    getMe().has_main_web_app  = False
    getChatMenuButton().type  = "commands"     ← هیچ دکمهٔ web_app ای نیست

یعنی گزارشِ آمادگی سبز می‌داد در حالی که هیچ مینی‌اپی ثبت نشده بود. و شاهدِ
رفتاری هم همین را می‌گوید: در **۸۸ ساعت** لاگِ ضربه، دقیقاً **یک** نشستِ
احرازشده.

⚠️ و یک تصحیح که در همین ریپو باید بماند: هدرِ `run-miniapp-tunnel-named.ps1`
می‌گوید از ۲۰۲۶-۰۷-۲۰ «اپ باز نمی‌شود» مگر origin ثبت شده باشد. این **بیش
از حد قوی** است — همان اپ امروز ساعتِ ۱۱:۰۰ باز شد و احراز هم شد، از روی
همان هاستِ تصادفی. سخت‌گیریِ ۱۰.۲ دربارهٔ **فراخوانیِ متدها از origin ِ
بیگانه** است، نه دربارهٔ بازشدن. مسئلهٔ واقعی این نیست که در قفل است؛ این
است که **در، دستگیره ندارد**: نه اپِ ثبت‌شده، نه دکمهٔ منو.

قرارداد
────────
`status(fetch_fn=...)` → dict. تزریق‌پذیر، پس تست هرگز به شبکه نمی‌رود.

    registered   تلگرام اپ یا دکمهٔ منو را می‌شناسد
    unregistered می‌شناسد که **نمی‌شناسد** (جوابِ قطعی)
    mismatch     دکمهٔ منو هست ولی به آدرسِ دیگری اشاره می‌کند
    unknown      شبکه/توکن جواب نداد ⇒ **حکم نیست** (سبز هم نیست)

⚠️ `unknown` هرگز `ok` نمی‌شود. نبودِ داده حکم نیست — و همین اشتباه بود که
اجازه داد چهار روز «سبز» ببینیم.

ناوردی‌ها: فقط‌خواندنی (هیچ متدِ تغییردهنده‌ای صدا نمی‌زند) · stdlib-only ·
**هرگز آدرس یا توکن را برنمی‌گرداند** — آدرسِ مینی‌اپ در این پروژه secret
طبقه‌بندی شده؛ فقط شکل و هم‌خوانی گزارش می‌شود.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

SCHEMA = "miniapp-registration.v1"
_API = "https://api.telegram.org"
TIMEOUT_S = 12.0


def live_url() -> str:
    """آدرسِ جاری از فایلِ تحویل. خالی = نامعلوم."""
    try:
        p = opslib.STATE_DIR / "telegram" / "miniapp-url.json"
        return str(json.loads(p.read_text("utf-8")).get("url") or "")
    except (OSError, ValueError, TypeError):
        return ""


def _default_fetch(method: str) -> dict:
    """فقط دو متدِ **خواندنی**. هیچ چیزی تغییر نمی‌کند.

    ⚠️ `getChatMenuButton` با `chat_id` ِ مالک پرسیده می‌شود، نه بی‌آرگومان.
    اندازه‌گیریِ زندهٔ ۲۰۲۶-۰۸-۰۴: `setChatMenuButton` روی دامنهٔ **پیش‌فرض**
    ‏`ok:true` برمی‌گرداند و **هیچ اثری ندارد** (خواندنِ بعدی هنوز
    `commands` می‌دهد) — یک no-op ِ کاملاً بی‌صدا. ولی همان فراخوان با
    `chat_id` ِ صریح کار می‌کند. پس تنها دامنه‌ای که «آیا دکمه هست؟» را
    درست جواب می‌دهد، خودِ چتِ مالک است. خواندنِ دامنهٔ پیش‌فرض یک منفیِ
    کاذب می‌سازد — دقیقاً برعکسِ سبزِ دروغینی که این ماژول برای رفعش ساخته شد.
    """
    tok = os.environ.get("TG_CENTER_BOT_TOKEN", "")
    if not tok:
        raise RuntimeError("no-token")
    url = f"{_API}/bot{tok}/{method}"
    if not url.startswith(_API + "/"):
        raise ValueError("blocked host")
    body = b""
    if method == "getChatMenuButton":
        owner = str(os.environ.get("TELEGRAM_OWNER_CHAT_ID", "") or "").strip()
        if owner:
            body = json.dumps({"chat_id": int(owner)}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json"} if body else {})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def _host(u: str) -> str:
    try:
        from urllib.parse import urlparse
        return (urlparse(str(u or "")).hostname or "").lower()
    except Exception:  # noqa: BLE001
        return ""


def status(fetch_fn=None, *, url: "str | None" = None) -> dict:
    """آیا تلگرام این مینی‌اپ را می‌شناسد؟ **همیشه dict، هرگز استثنا.**"""
    fetch = fetch_fn if fetch_fn is not None else _default_fetch
    cur = live_url() if url is None else str(url or "")
    out = {"schema": SCHEMA, "state": "unknown", "ok": False,
           "has_main_web_app": None, "menu_button": None,
           "menu_matches_live_url": None, "ephemeral_host": None,
           "why": ""}
    # میزبانِ گذرا: هاستی که هر ری‌استارت عوض می‌شود ⇒ ثبتِ پایدار ناممکن است
    h = _host(cur)
    out["ephemeral_host"] = bool(h) and (
        h.endswith(".trycloudflare.com") or h.endswith(".ngrok-free.app")
        or h.endswith(".ngrok.io") or h.endswith(".loca.lt"))

    try:
        me = fetch("getMe") or {}
        mb = fetch("getChatMenuButton") or {}
    except Exception as e:  # noqa: BLE001
        out["why"] = f"پرسش از تلگرام ناموفق ({type(e).__name__}) — حکم صادر نمی‌شود"
        return out

    mres = me.get("result") if isinstance(me, dict) else None
    bres = mb.get("result") if isinstance(mb, dict) else None
    if not isinstance(mres, dict) or not isinstance(bres, dict):
        out["why"] = "پاسخِ تلگرام شکلِ منتظره را نداشت — حکم صادر نمی‌شود"
        return out

    out["has_main_web_app"] = bool(mres.get("has_main_web_app"))
    btype = str(bres.get("type") or "")
    out["menu_button"] = btype
    menu_url = ""
    if btype == "web_app":
        menu_url = str((bres.get("web_app") or {}).get("url") or "")
        # ⚠️ آدرس **برنمی‌گردد** (secret) — فقط هم‌خوانیِ میزبان
        out["menu_matches_live_url"] = bool(
            menu_url and cur and _host(menu_url) == h)

    if out["has_main_web_app"] or btype == "web_app":
        if btype == "web_app" and out["menu_matches_live_url"] is False:
            out["state"] = "mismatch"
            out["why"] = ("دکمهٔ منو به میزبانِ دیگری اشاره می‌کند — کلیکِ مالک "
                          "به گیت‌وی نمی‌رسد")
        else:
            out["state"], out["ok"] = "registered", True
            out["why"] = "تلگرام درِ مینی‌اپ را می‌شناسد"
    else:
        out["state"] = "unregistered"
        out["why"] = ("نه اپِ اصلی ثبت شده نه دکمهٔ منو — تنها راهِ ورود "
                      "دکمه‌های inline است")
    return out


def summary_line(st: "dict | None" = None) -> str:
    """یک خطِ فارسی برای گزارشِ آمادگی. هرگز آدرس چاپ نمی‌کند."""
    d = status() if st is None else st
    mark = {"registered": "✅", "unregistered": "❌",
            "mismatch": "⚠️", "unknown": "❔"}.get(d.get("state"), "·")
    bits = [f"{mark} ثبتِ مینی‌اپ: {d.get('state')}"]
    if d.get("ephemeral_host"):
        bits.append("میزبانِ گذرا (هر ری‌استارت عوض می‌شود)")
    if d.get("why"):
        bits.append(str(d["why"]))
    return " · ".join(bits)


if __name__ == "__main__":  # pragma: no cover — گزارشِ دستی، فقط‌خواندنی
    try:
        sys.path.insert(0, str(_HERE.parent))
        import env_loader
        env_loader.load_env()
    except Exception:  # noqa: BLE001
        pass
    s = status()
    print(json.dumps(s, ensure_ascii=False, indent=2))
    print("\n" + summary_line(s))
