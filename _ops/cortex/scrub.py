#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scrub.py — اسکرابرِ اجباریِ راز، **پیش از** هر model_router.ask و پیش از هر لاگ.

رأیِ صریحِ مالک ۲۰۲۶-۰۹-۰۹ («توکنم برای اسکن نره») — مقدم بر همهٔ اتصال‌های مغز
(MEGAPROMPT-CORTEX-CONNECT-ALL-2026-09-10 §گاردِ راز). فقط روی **کپیِ ارسالی**
اعمال می‌شود؛ فایلِ اصل دست‌نخورده می‌ماند. stdlib-only، صفر I/O، تابعِ خالص.

الگوها (همان فهرستِ مگاپرامپت، نه بیشتر و نه کمتر):
  · توکنِ رباتِ تلگرام      [0-9]{8,10}:[A-Za-z0-9_-]{35}
  · کلیدهای شناخته‌شده      sk-… · AKIA… · ghp_… · xox[bap]-… · TELNYX_*
  · جفتِ کلید/مقدارِ عمومی  (?i)(api_?key|token|secret)["'\\s:=]{1,4}\\S+
"""
from __future__ import annotations

import re

REDACTED = "[REDACTED]"

# ترتیب مهم است: الگوهای مشخص اول، الگوی عمومیِ کلید/مقدار آخر.
PATTERNS: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    ("tg_bot_token", re.compile(r"[0-9]{8,10}:[A-Za-z0-9_-]{35}")),
    ("openai_key",   re.compile(r"\bsk-[A-Za-z0-9_-]{8,}")),
    ("aws_key",      re.compile(r"\bAKIA[0-9A-Z]{12,}")),
    ("github_pat",   re.compile(r"\bghp_[A-Za-z0-9]{20,}")),
    ("slack_token",  re.compile(r"\bxox[bap]-[A-Za-z0-9-]{10,}")),
    ("telnyx",       re.compile(r"\bTELNYX_[A-Z0-9_]*(?:[\"'\s:=]{1,4}\S+)?")),
    ("kv_secret",    re.compile(r"(?i)(api_?key|token|secret)[\"'\s:=]{1,4}\S+")),
)


def leaks(text) -> list[str]:
    """نامِ الگوهایی که در متن حضور دارند (برای تست/گارد؛ متن را برنمی‌گرداند)."""
    s = str(text or "")
    return [name for name, rx in PATTERNS if rx.search(s)]


def scrub(text) -> str:
    """کپیِ پاک‌شده. هر تطبیق → [REDACTED]. ورودیِ None → رشتهٔ خالی."""
    s = str(text or "")
    for _name, rx in PATTERNS:
        s = rx.sub(REDACTED, s)
    return s


def is_clean(text) -> bool:
    return not leaks(text)
