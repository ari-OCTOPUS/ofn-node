"""
guardrails.py — چک‌لیست #۷ (نسخه‌ی ساده): سیاست روی خروجی + هشدار آنومالی.

یک گاردریل حداقلی که خروجی نهایی را قبل از تحویل بررسی می‌کند:
  - اگر خروجی خالی/خیلی کوتاه باشد → رد.
  - اگر نشانه‌ی محتوای اثبات‌نشده باشد ولی هشدار آن نیامده باشد → پرچم.
این لایه در فاز ۳ با NeMo Guardrails / Guardrails AI ارتقا می‌یابد.
"""
from __future__ import annotations

SUSPICIOUS = ("اثبات‌نشده", "نامطمئن", "شایعه")


def check_output(text: str) -> tuple[bool, str]:
    if not text or len(text.strip()) < 15:
        return False, "خروجی خالی یا بیش از حد کوتاه است"
    has_claim = any(w in text for w in SUSPICIOUS)
    has_caveat = ("راستی‌آزمایی" in text) or ("احتیاط" in text)
    if has_claim and not has_caveat:
        return False, "ادعای نامطمئن بدون هشدارِ راستی‌آزمایی"
    return True, "ok"
