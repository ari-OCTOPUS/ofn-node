#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""callback_token.py — توکنِ HMACِ ضدِ جعل/replay/expiry برای callbackهای `ap:` (Stage-1 P3).

قیدِ توکن (contract 2026-07-20، هم‌راستا با ممیزی):
    jid | action | owner_id | action_hash | expires

- action_hash = mission_contract.content_sha256(action, jid, {type,risk}) — bind به
  محتوای دقیقِ job (anti-TOCTOU؛ اگر type/risk عوض شود توکن باطل می‌شود).
- expires = مهرِ انقضا (epoch؛ ثانیه). داخلِ HMAC است (تمدید بدونِ باطل‌شدن ممکن نیست)
  و handler جداگانه هم `now <= expires` را enforce می‌کند.
- jid در این صف نقشِ approval_id و mission_id را با هم دارد (mission_mod.get(jid)).

secret فقط از env `OCTOPUS_CB_SECRET` — هرگز log/persist/echo نمی‌شود و این ماژول آن را
نمی‌سازد (ساختِ مقدار = کارِ مالک). انضباط:
- پشتِ فلگِ `OCTOPUS_WIRE_CB_TOKEN` (پیش‌فرض خاموش) — خاموش = رفتارِ امروز بایت‌به‌بایت.
- روشن ولی secret غایب = fail-closed: mint="" و verify=False → دکمه‌ها inert.
- مقایسه ثابت‌زمان (hmac.compare_digest). stdlib-only.

نکتهٔ امنیتی (ثبت‌شده): این توکن defense-in-depth است. مسیرِ `ap:` از قبل با `is_owner`
بر پایهٔ from.id گیت می‌شود (fail-closed) و single-use هم اتمیک است (approval_store._move
رکورد را از pending pop می‌کند؛ replay → False).
"""
from __future__ import annotations

import hashlib
import hmac
import os

FLAG = "OCTOPUS_WIRE_CB_TOKEN"
SECRET_ENV = "OCTOPUS_CB_SECRET"
# بودجهٔ سختِ ۶۴B: بلندترین callback = "ap:ok:"(۶) + jid[:48] + ":"(۱) + token.
# با token=۲۰ می‌شد ۷۵B > ۶۴ و تلگرام کلِ sendMessage را رد می‌کرد (نه فقط یک دکمه).
# jid کوتاه‌شدنی نیست (handler دقیقاً aps_mod.get(jid) را lookup می‌کند)؛ پس token
# کوتاه می‌شود: ۶+۴۸+۱+۹=۶۴. تنزلِ ۳۶-bit قابل‌قبول است چون این توکن defense-in-depth
# است — is_owner(from.id) و single-useِ اتمیک گاردهای اصلی‌اند (رأیِ مالک ۲۰۲۶-۰۷-۳۰).
_TOKEN_LEN = 9    # hex chars از sha256 — بودجهٔ ۶۴B را با jid[:48] تضمین می‌کند


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


def _canon(jid, action, owner_id, action_hash, expires) -> bytes:
    return f"{jid}|{action}|{owner_id}|{action_hash}|{expires}".encode("utf-8")


def mint(jid, action, owner_id, action_hash, expires) -> str:
    """توکنِ hex یا "" اگر secret نباشد (fail-closed → کارتِ معتبرِ tokenless ساخته نشود)."""
    sec = _secret()
    if not sec:
        return ""
    mac = hmac.new(sec, _canon(jid, action, owner_id, action_hash, expires), hashlib.sha256)
    return mac.hexdigest()[:_TOKEN_LEN]


def verify(token, jid, action, owner_id, action_hash, expires) -> bool:
    """مقایسه ثابت‌زمان. نبودِ token/secret یا هر عدم‌تطابق = False (fail-closed).

    توجه: این فقط صحتِ HMAC (شاملِ expires) را چک می‌کند؛ enforcementِ `now<=expires`
    و single-use در handler است."""
    if not token or not isinstance(token, str):
        return False
    expected = mint(jid, action, owner_id, action_hash, expires)
    if not expected:            # secret غایب → هیچ توکنی معتبر نیست
        return False
    return hmac.compare_digest(token, expected)
