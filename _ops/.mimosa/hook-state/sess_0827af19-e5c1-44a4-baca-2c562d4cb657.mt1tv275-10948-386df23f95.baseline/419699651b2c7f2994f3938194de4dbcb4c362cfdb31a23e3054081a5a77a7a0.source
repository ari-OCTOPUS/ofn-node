#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""telegram_pep_shadow — DA-4-P1: PEP سایه روی مرز ارسال تلگرام (PHASE02 STEP1).

«کوچک‌ترین پچ مؤثر» به روایت قاضی (نقض INV-4: دو کلاینت تلگرام/دو PolicyGate).
این ماژول **سایه** است: هیچ مسیر زنده‌ای را نمی‌بندد؛ فقط هر ارسالِ ردشده از
گلوگاه را در برابر قراردادِ lease می‌سنجد و حکمِ «اگر enforce بود» را ثبت
می‌کند. فعال‌سازی = رأی مالک (پیش‌نویس ADR: 02-DECISIONS/DECISION-ARTIFACTS).

قرارداد lease (هم‌خانوادهٔ councils/pep_shadow، DA-4):
  · متصل به hashِ دقیقِ (action, params) — نه رشتهٔ آزاد
  · تک‌مصرف (nonce) · انقضای کوتاه · kill توزیع‌شده (لیست ابطالِ محلی)
  · deny-by-default در حالتِ enforce؛ سایه = فقط گزارش

نقشهٔ مرز (سطح A، 2026-08-16 ~05:1x):
  بات مرکز:  telegram_center/tg_api.py::TelegramBot._call_post  (تنها POST)
  بات پول:   budget/approval_channel.py::http_post (ساختار داخلی خودش)
  دکتر:      بدون ارسال مستقیم — relay از center (doctor_link)
  ارسال قانونی امروز بدون lease: همه — به همین دلیل سایه می‌سنجیم، نه می‌بندیم.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

STATE = Path(os.environ.get("OCTOPUS_STATE_DIR",
                            Path(__file__).resolve().parent.parent / "state"))
LOG = STATE / "telegram-pep-shadow.jsonl"
_TTL_S = 30.0


def params_sha(action: str, params: dict) -> str:
    blob = json.dumps([action, params], ensure_ascii=False,
                      sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


class Lease:
    """اجارهٔ تک‌مصرف متصل به عمل — ساخت/امضا در آینده با رأی مالک."""
    __slots__ = ("lease_id", "action", "sha", "nonce", "expires_at", "consumed")

    def __init__(self, action: str, params: dict, ttl_s: float = _TTL_S):
        self.lease_id = f"tg-{hashlib.sha256(os.urandom(8)).hexdigest()[:8]}"
        self.action = action
        self.sha = params_sha(action, params)
        self.nonce = os.urandom(8).hex()
        self.expires_at = time.monotonic() + ttl_s
        self.consumed = False


class PepState:
    """ریجستریِ leaseها + ابطال — در سایه فقط برای سنجش، نه اجرا."""

    def __init__(self):
        self.leases: dict[str, Lease] = {}
        self.revoked: set[str] = set()

    def evaluate(self, action: str, params: dict, lease: Lease | None) -> dict:
        """حکم enforce-اگر-بود. هیچ اثری ندارد — خروجی = گزارش."""
        if lease is None:
            v, why = "deny", "no-lease (deny-by-default)"
        elif lease.lease_id in self.revoked:
            v, why = "deny", "revoked (distributed kill)"
        elif lease.consumed:
            v, why = "deny", "replay (single-use)"
        elif time.monotonic() > lease.expires_at:
            v, why = "deny", "expired"
        elif lease.sha != params_sha(action, params):
            v, why = "deny", "hash-mismatch (action/params drifted)"
        else:
            v, why = "allow", "lease-valid"
            lease.consumed = True
        return {"verdict": v, "reason": why,
                "lease": lease.lease_id if lease else None}


def observe(sender: str, action: str, params: dict,
            lease: Lease | None = None, state: PepState | None = None) -> dict:
    """ناظرِ سایه — fail-soft؛ هرگز مسیرِ ارسال را نگه نمی‌دارد."""
    try:
        st = state or _SHARED
        r = st.evaluate(action, params, lease)
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "sender": str(sender)[:60], "action": str(action)[:40],
               "params_sha": params_sha(action, params),
               "mode": "shadow", **r}
        STATE.mkdir(parents=True, exist_ok=True)
        log = STATE / "telegram-pep-shadow.jsonl"   # تازه محاسبه شود — قابل‌تزریق برای تست
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return r
    except Exception:  # noqa: BLE001 — سایه هرگز مرز را نمی‌کشد
        return {"verdict": "shadow-error", "reason": "observer failed"}


_SHARED = PepState()


def hook(sender: str, action: str, params: dict) -> None:
    """نقطهٔ اتصالِ fail-soft برای گلوگاه‌های زنده (الگوی ADR-042 phase-0).
    در مسیرِ tg_api._call_post / approval http_post صدا زده می‌شود؛
    صفر تغییر رفتار — فقط مشاهده."""
    observe(sender, action, params)
