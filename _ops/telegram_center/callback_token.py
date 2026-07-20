#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""callback_token.py — توکنِ HMACِ ضدِ جعل/replay برای callbackهای `ap:` (Stage-1 P3).

قیدِ توکن: jid + action + owner_id + stamp (=`created_at`ِ همان job، پایدار و
per-job). secret فقط از env `OCTOPUS_CB_SECRET` خوانده می‌شود — هرگز log/persist/echo
نمی‌شود و این ماژول آن را نمی‌سازد (ساختِ مقدار = کارِ مالک).

انضباط:
- پشتِ فلگِ `OCTOPUS_WIRE_CB_TOKEN` (پیش‌فرض خاموش) — خاموش = رفتارِ امروز بایت‌به‌بایت
  (کارت `ap:ok:<id>` بدونِ توکن، هیچ verify).
- روشن ولی secret غایب = fail-closed: mint = "" و verify = False → دکمه‌ها inert می‌مانند
  تا مالک secret را ست کند (هرگز کارتِ «tokenless ولی معتبر» ساخته نمی‌شود).
- مقایسه ثابت‌زمان (hmac.compare_digest). stdlib-only.

توجهِ مهمِ امنیتی (ثبت‌شده در گزارش): این توکن defense-in-depth است. مسیرِ `ap:` از
قبل با `is_owner` بر پایهٔ `from.id` fail-closed گیت می‌شود (غیرمالک = سکوت) و single-use
هم از قبل اتمیک است (approval_store._move رکورد را از pending pop می‌کند؛ replay → False).
"""
from __future__ import annotations

import hashlib
import hmac
import os

FLAG = "OCTOPUS_WIRE_CB_TOKEN"
SECRET_ENV = "OCTOPUS_CB_SECRET"
_TOKEN_LEN = 20   # hex chars از sha256 (کوتاه؛ سقفِ ۶۴ بایتِ callback_data)


def flag_on() -> bool:
    """آیا قیدِ توکنِ callback روشن است؟ (پیش‌فرض خاموش)."""
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _secret() -> bytes | None:
    s = os.environ.get(SECRET_ENV, "")
    s = s.strip() if isinstance(s, str) else ""
    return s.encode("utf-8") if s else None


def ready() -> bool:
    """روشن و پیکربندی‌شده (فلگ روشن + secret موجود)."""
    return flag_on() and _secret() is not None


def _canon(jid, action, owner_id, stamp) -> bytes:
    return f"{jid}|{action}|{owner_id}|{stamp}".encode("utf-8")


def mint(jid, action, owner_id, stamp) -> str:
    """توکنِ hex یا "" اگر secret نباشد (fail-closed → کارتِ معتبرِ tokenless ساخته نشود)."""
    sec = _secret()
    if not sec:
        return ""
    mac = hmac.new(sec, _canon(jid, action, owner_id, stamp), hashlib.sha256)
    return mac.hexdigest()[:_TOKEN_LEN]


def verify(token, jid, action, owner_id, stamp) -> bool:
    """مقایسه ثابت‌زمان. نبودِ token/secret یا هر عدم‌تطابق = False (fail-closed)."""
    if not token or not isinstance(token, str):
        return False
    expected = mint(jid, action, owner_id, stamp)
    if not expected:            # secret غایب → هیچ توکنی معتبر نیست
        return False
    return hmac.compare_digest(token, expected)
