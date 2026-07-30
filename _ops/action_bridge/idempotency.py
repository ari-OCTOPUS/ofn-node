#!/usr/bin/env python3
"""idempotency — «این عمل قبلاً انجام شده؟» و مهم‌تر: «همان عمل بود؟»

دو حالت که یکی گرفتنشان همان اشتباهی است که یک بار روی `prereg` گرفته شد
(۲۰۲۶-۰۷-۳۰، هدفِ A منجمد ولی هدفِ B اجرا):

    همان action_id + همان payload   →  NOOP    (تکرارِ بی‌ضرر)
    همان action_id + payload ِ نو    →  CONFLICT (عملِ دیگری با نامِ قدیمی)

اگر دومی هم NOOP می‌شد، کافی بود کسی `target` را عوض کند و `action_id` را نگه
دارد تا عملِ نو بدونِ هیچ ارزیابی‌ای «قبلاً انجام شده» اعلام شود.

کلید = `action_id` + hashِ میدان‌های امضا (`contracts.payload_hash`). عمداً
شاملِ زمان **نیست** — «شمارنده در کلیدِ dedup» گذشتِ زمان را تغییر می‌شمارد و
گارد را بی‌اثر می‌کند.

$0 · stdlib · تابعِ خالص · ذخیره‌سازی کارِ صداکننده است.
"""
from __future__ import annotations

from contracts import payload_hash  # noqa: E402


def key_for(req: dict) -> str:
    return f"{str(req.get('action_id'))}:{payload_hash(req)}"


def check(req: dict, ledger) -> dict:
    """{state, key, previous}. `ledger`: dict ِ key→receipt (یا هر Mapping).

    state ∈ {NEW, DUPLICATE, CONFLICT}. `CONFLICT` یعنی همین `action_id` قبلاً
    با payload ِ **متفاوت** دیده شده."""
    if not isinstance(req, dict):
        return {"state": "CONFLICT", "key": None, "previous": None,
                "reason": "not-a-dict"}
    aid = str(req.get("action_id") or "")
    k = key_for(req)
    if ledger is None:
        # بدونِ دفتر نمی‌شود گفت تازه است یا تکراری — و «نمی‌دانم» اجازه نیست
        return {"state": "CONFLICT", "key": k, "previous": None,
                "reason": "no-ledger"}
    if k in ledger:
        return {"state": "DUPLICATE", "key": k, "previous": ledger[k],
                "reason": "same-id-same-payload"}
    for existing_key, rec in ledger.items():
        if str(existing_key).split(":", 1)[0] == aid:
            return {"state": "CONFLICT", "key": k, "previous": rec,
                    "reason": "same-id-different-payload"}
    return {"state": "NEW", "key": k, "previous": None, "reason": "unseen"}


def remember(key: str, receipt: dict, ledger) -> None:
    if ledger is not None and key:
        ledger[key] = receipt
