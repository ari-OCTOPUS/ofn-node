#!/usr/bin/env python3
"""mail_credentials.py — Lane G (منشور TG-UI ۲۰۲۶-۰۷-۳۱، رأی ۱۷): حلِ credential ِ SMTP.

چرا این ماژول هست: تا امشب `lead_outbound_transport` همیشه NOT_ARMED می‌داد چون
۵ متغیرِ `OCTOPUS_SMTP_*` هرگز وجود نداشتند — یعنی قوسِ ارسال «اعلام‌شده ولی
واقعاً کار-نکن» بود. ولی `.env` ِ زنده از قبل credential ِ کارآمدِ میل دارد
(کلیدهای `GMAIL_ADDRESS` و `GMAIL_APP_PASSWORD`). پس لوله بدونِ **هیچ secret ِ نو**
کامل می‌شود — فقط با یک تصمیمِ صریحِ مالک.

قراردادِ سختِ secret (§۱۰ قانونِ اساسی):
  · `resolve()` **هرگز خودِ پسورد را برنمی‌گرداند** — فقط **نامِ** متغیرِ env ی که
    پسورد در آن نشسته (`secret_env`). خواننده (فرستنده) لحظهٔ ارسال با آن نام
    از `os.environ` می‌خواند. پس پسورد نه در dict می‌نشیند، نه در رسید، نه در لاگ.
  · این ماژول هیچ چیزی log/print نمی‌کند مگر در `__main__` — و آن‌جا هم فقط
    نام/بولین/ماسک، هرگز مقدار.
  · `status()` آدرسِ مالک را ماسک‌شده می‌دهد (گزارشِ امن برای سطحِ owner-readiness).

ترتیبِ تقدم (اولین منطبق برنده):
  ۱. صریح: هر ۵ تای `OCTOPUS_SMTP_HOST/PORT/USER/PASS/FROM`. ستِ **ناقص** =
     خطای اپراتور ⇒ ok=False با نامِ کلیدهای غایب — نه سقوطِ بی‌صدا به Gmail
     (وگرنه هویتِ فرستنده بی‌خبر عوض می‌شود؛ دقیقاً همان «سکوتِ دروغ‌گو»).
  ۲. Gmail: `GMAIL_ADDRESS` + `GMAIL_APP_PASSWORD` روی smtp.gmail.com:465
     (TLS ِ implicit) — **فقط** اگر فلگِ `OCTOPUS_SMTP_USE_GMAIL=1` باشد.

چرا فلگِ جدا برای Gmail (و نه مسلح‌شدنِ خودکار): این صندوقِ **شخصیِ** مالک است.
اینکه ارگانیسم آن را به‌عنوانِ هویتِ ارسالِ لید بردارد باید یک رأیِ عمدی باشد،
نه عارضهٔ اینکه اتفاقاً آن کلیدها برای کارِ دیگری در `.env` بوده‌اند. با فلگِ
خاموش (پیش‌فرض) رفتارِ کلِ درخت دقیقاً همان دیروز است: NOT_ARMED ِ صادق.

stdlib-only. هیچ I/O شبکه‌ای این‌جا نیست — فقط حلِ نام.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# ── نام‌ها (فقط نام — هیچ مقداری در این فایل هاردکد نیست) ──────────────────────
EXPLICIT_ENV = ("OCTOPUS_SMTP_HOST", "OCTOPUS_SMTP_PORT", "OCTOPUS_SMTP_USER",
                "OCTOPUS_SMTP_PASS", "OCTOPUS_SMTP_FROM")
GMAIL_ADDR_ENV = "GMAIL_ADDRESS"
GMAIL_SECRET_ENV = "GMAIL_APP_PASSWORD"
GMAIL_FALLBACK_FLAG = "OCTOPUS_SMTP_USE_GMAIL"

GMAIL_HOST = "smtp.gmail.com"
GMAIL_PORT = 465          # implicit TLS (SMTP_SSL) — نه STARTTLS ِ ۵۸۷

_TRUTHY = {"1", "true", "yes", "on"}


def _env(name: str) -> str:
    return str(os.environ.get(name, "") or "").strip()


def _ensure_env_loaded() -> None:
    """`.env` ِ کانونی را (اگر هنوز لود نشده) از مسیرِ رسمی لود کن — fail-soft.

    در بوتِ زنده `organism.py` این کار را کرده؛ ولی ابزارِ تک‌شات (و self_test ِ
    دستی) ممکن است مستقیم اجرا شود. `load_env` خودش idempotent است و مقدارِ
    از-قبل-موجود را overwrite نمی‌کند."""
    try:
        _b = str(Path(__file__).resolve().parent.parent / "budget")
        if _b not in sys.path:
            sys.path.insert(0, _b)
        import env_loader   # noqa: WPS433 — lazy
        env_loader.load_env()
    except Exception:  # noqa: BLE001 — نبودِ .env هرگز حلِ credential را نمی‌کُشد
        pass


def mask_address(addr: str) -> str:
    """«ab***@domain» — آدرس هرگز کامل در گزارش/رسید نمی‌نشیند.
    (عمداً کپیِ کوچکِ `lead_outbound_transport.mask_recipient` است تا این ماژول
    وابستگیِ دوطرفه به فرستنده نداشته باشد.)"""
    a = str(addr or "").strip()
    local, _, dom = a.partition("@")
    if not dom:
        return "***"
    return (local[:2] + "***@" + dom) if local else ("***@" + dom)


def _blank(reason: str) -> dict:
    """شکلِ ثابتِ خروجی حتی در شکست — صداکننده هرگز KeyError نمی‌گیرد."""
    return {"ok": False, "how": "none", "reason": reason,
            "host": "", "port": 0, "user": "", "from_addr": "", "secret_env": ""}


def gmail_fallback_enabled() -> bool:
    return _env(GMAIL_FALLBACK_FLAG).lower() in _TRUTHY


def resolve() -> dict:
    """credential ِ SMTP را حل کن — **بدونِ** پسورد.

    خروجی (همیشه dict، همیشه با همین کلیدها):
      {ok, how, host, port, user, from_addr, secret_env, reason?}
      · `secret_env` = **نامِ** متغیرِ env ِ حاملِ پسورد (نه خودِ پسورد).
      · `how` ∈ {"octopus-smtp-env", "gmail-app-password", "none"}.
    ok=False همیشه `reason` ِ صادق دارد که می‌گوید دقیقاً چه کم است.
    """
    _ensure_env_loaded()

    # ── ۱) مسیرِ صریح: هر ۵ تا ────────────────────────────────────────────────
    present = {k: _env(k) for k in EXPLICIT_ENV}
    missing = [k for k in EXPLICIT_ENV if not present[k]]
    if len(missing) < len(EXPLICIT_ENV):          # اپراتور دست به این‌ها زده
        if missing:
            # ستِ ناقص = خطای اپراتور. سقوطِ بی‌صدا به Gmail ممنوع است:
            # هویتِ فرستنده بی‌خبر عوض می‌شد. بلند و صادق شکست بخور.
            return _blank("octopus-smtp-incomplete:" + ",".join(missing))
        try:
            port = int(present["OCTOPUS_SMTP_PORT"])
            if not (0 < port < 65536):
                raise ValueError("port out of range")
        except (TypeError, ValueError):
            return _blank("octopus-smtp-bad-port:OCTOPUS_SMTP_PORT")
        return {"ok": True, "how": "octopus-smtp-env",
                "host": present["OCTOPUS_SMTP_HOST"], "port": port,
                "user": present["OCTOPUS_SMTP_USER"],
                "from_addr": present["OCTOPUS_SMTP_FROM"],
                "secret_env": "OCTOPUS_SMTP_PASS"}

    # ── ۲) fallback ِ Gmail — فقط با فلگِ صریحِ مالک ─────────────────────────
    addr = _env(GMAIL_ADDR_ENV)
    has_secret = bool(_env(GMAIL_SECRET_ENV))
    if not gmail_fallback_enabled():
        if addr and has_secret:
            # credential هست ولی رأی نیست — این را صریح بگو، نه «creds missing».
            return _blank("gmail-fallback-not-enabled:" + GMAIL_FALLBACK_FLAG)
        return _blank("smtp-creds-missing")
    gm_missing = [n for n, v in ((GMAIL_ADDR_ENV, addr),
                                 (GMAIL_SECRET_ENV, has_secret)) if not v]
    if gm_missing:
        return _blank("gmail-creds-missing:" + ",".join(gm_missing))
    return {"ok": True, "how": "gmail-app-password",
            "host": GMAIL_HOST, "port": GMAIL_PORT,
            "user": addr, "from_addr": addr,
            "secret_env": GMAIL_SECRET_ENV}


def owner_address() -> str:
    """آدرسِ خودِ مالک (هویتِ فرستنده) — مقصدِ **تنها**-مجازِ self_test.
    حل‌نشدن ⇒ رشتهٔ خالی."""
    cr = resolve()
    return str(cr.get("from_addr") or "") if cr.get("ok") else ""


def secret_present(cr: dict | None = None) -> bool:
    """آیا متغیرِ حاملِ پسورد واقعاً پُر است؟ (فقط بولین — هرگز مقدار.)"""
    c = cr if isinstance(cr, dict) else resolve()
    name = str(c.get("secret_env") or "")
    return bool(name) and bool(_env(name))


def status() -> dict:
    """گزارشِ امن برای سطح‌های owner-readiness — هرگز مقدارِ secret، آدرس ماسک‌شده."""
    cr = resolve()
    return {"ok": bool(cr.get("ok")), "how": cr.get("how"),
            "reason": cr.get("reason"),
            "host": cr.get("host"), "port": cr.get("port"),
            "from_masked": mask_address(cr.get("from_addr") or ""),
            "secret_env": cr.get("secret_env"),
            "secret_present": secret_present(cr),
            "gmail_fallback_flag": GMAIL_FALLBACK_FLAG,
            "gmail_fallback_enabled": gmail_fallback_enabled()}


if __name__ == "__main__":
    # فقط نام/بولین/ماسک — هرگز مقدارِ کلید.
    print(json.dumps(status(), ensure_ascii=False, indent=2))
