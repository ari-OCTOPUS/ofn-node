#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proposal_token.py — GAP-2: توکنِ stateless و HMAC-bound برای دکمه‌های کارتِ پیشنهاد.

مشکل (ممیزی R-audit B-02 / spec GAP2): `_PROPOSAL_CB` در live_loop فقط RAM بود → restart
= دکمه‌های مرده. این ماژول توکن را **خود-احرازکننده** می‌کند: هیچ state ای در RAM لازم نیست؛
اصالت از HMAC با secret می‌آید و meta از رجیستریِ durable (proposal_registry) بازسازی می‌شود.

قالب (سقف ۶۴ بایتِ callback_data تلگرام):
    pb1.<pid12>.<exp10>.<sig16>              → ۴۴ کاراکتر
    pid12 = sha256(proposal_id)[:12]         → شناسهٔ کوتاهِ قطعی
    exp   = epoch انقضا (۱۰ رقم)             → پیش‌فرض ۷۲ ساعت (OCTOPUS_CB_TTL_S)
    sig   = HMAC-SHA256(secret, "pb1|<proposal_id>|<exp>|<owner_id>")[:16]

قواعد (spec + قانون C2-B):
  - binding: proposal_id (کامل، در canon) + expiry + **owner** (در canon؛ صفر بایتِ اضافه).
    verdict/action در توکن نیست — از دکمه می‌آید؛ جعلِ verdict بدونِ secret ناممکن است
    چون خودِ توکن بدونِ secret ساختنی نیست.
  - single-use از مسیرِ durable است (idempotency در outcomes.db)، نه از توکن — قوی‌تر.
  - secret فقط از env `OCTOPUS_CB_SECRET` (مالک می‌سازد؛ این ماژول هرگز نمی‌سازد/چاپ نمی‌کند).
  - بدونِ secret: mint→None (fail-soft به رفتارِ RAM قدیمی)؛ verify→reject (fail-closed).
  - مقایسهٔ ثابت‌زمان (hmac.compare_digest). stdlib فقط؛ صفر I/O — از live_loop قابلِ import
    بدونِ شکستنِ ناوردیِ «لایهٔ wireِ خالص».
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import time

VERSION = "pb1"
SECRET_ENV = "OCTOPUS_CB_SECRET"          # همان قراردادِ telegram_center/callback_token.py
TTL_ENV = "OCTOPUS_CB_TTL_S"
DEFAULT_TTL_S = 72 * 3600                 # ۷۲ ساعت (spec)
_PID_LEN = 12
_SIG_LEN = 16
_TOKEN_RE = re.compile(r"^pb1\.([0-9a-f]{12})\.(\d{10})\.([0-9a-f]{16})$")


def _secret() -> "bytes | None":
    s = os.environ.get(SECRET_ENV, "")
    return s.encode("utf-8") if s and s.strip() else None


def ready() -> bool:
    """secret موجود است؟ (وجود، نه مقدار — هرگز مقدار را برنمی‌گردانیم/چاپ نمی‌کنیم.)"""
    return _secret() is not None


def ttl_s() -> int:
    try:
        v = int(os.environ.get(TTL_ENV, "") or DEFAULT_TTL_S)
        return v if v > 0 else DEFAULT_TTL_S
    except ValueError:
        return DEFAULT_TTL_S


def pid12(proposal_id) -> str:
    """شناسهٔ کوتاهِ قطعیِ پیشنهاد — کلیدِ رجیستریِ durable (هش، نه truncate)."""
    return hashlib.sha256(str(proposal_id or "").encode("utf-8")).hexdigest()[:_PID_LEN]


def _canon(proposal_id, exp: int, owner_id) -> bytes:
    # F4: ownerِ نرمال‌شده (strip) در هر دو سرِ mint/verify — whitespaceِ env مالک را قفل نکند
    return f"{VERSION}|{proposal_id}|{int(exp)}|{str(owner_id).strip()}".encode("utf-8")


def _sig(sec: bytes, proposal_id, exp: int, owner_id) -> str:
    return hmac.new(sec, _canon(proposal_id, exp, owner_id), hashlib.sha256).hexdigest()[:_SIG_LEN]


def mint(proposal_id, owner_id, *, now: "float | None" = None) -> "str | None":
    """توکنِ stateless بساز. None = آماده نیست (بدونِ secret/owner/pid) → caller به رفتارِ
    قدیمیِ RAM برمی‌گردد (fail-soft؛ هرگز crash)."""
    sec = _secret()
    if sec is None or not proposal_id or owner_id in (None, ""):
        return None
    exp = int(now if now is not None else time.time()) + ttl_s()
    tok = f"{VERSION}.{pid12(proposal_id)}.{exp:010d}.{_sig(sec, proposal_id, exp, owner_id)}"
    return tok if len(tok) <= 54 else None   # 54 + len("prop:later:") = 65-11 → زیر سقف ۶۴


def looks_stateless(token) -> bool:
    return bool(_TOKEN_RE.match(str(token or "")))


def parse(token) -> "tuple[str, int] | None":
    """(pid12, exp) یا None. فقط قالب — اصالت را verify می‌سنجد."""
    m = _TOKEN_RE.match(str(token or ""))
    return (m.group(1), int(m.group(2))) if m else None


def verify(token, proposal_id, owner_id, *, now: "float | None" = None) -> "tuple[bool, str]":
    """احرازِ fail-closed. (ok, reason) — reason ∈ ok|no-secret|bad-format|wrong-pid|expired|bad-sig.
    wrong-owner و forged هر دو در bad-sig می‌افتند (canon شاملِ owner است؛ ساختاری)."""
    sec = _secret()
    if sec is None:
        return (False, "no-secret")
    parsed = parse(token)
    if parsed is None:
        return (False, "bad-format")
    tok_pid12, exp = parsed
    if tok_pid12 != pid12(proposal_id):
        return (False, "wrong-pid")
    if int(now if now is not None else time.time()) >= exp:
        return (False, "expired")
    expected = _sig(sec, proposal_id, exp, owner_id)
    tok_sig = str(token).rsplit(".", 1)[-1]
    if not hmac.compare_digest(tok_sig, expected):
        return (False, "bad-sig")
    return (True, "ok")
