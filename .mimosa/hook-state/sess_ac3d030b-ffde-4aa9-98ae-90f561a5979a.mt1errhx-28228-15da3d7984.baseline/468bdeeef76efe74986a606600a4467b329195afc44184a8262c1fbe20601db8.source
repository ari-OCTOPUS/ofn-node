#!/usr/bin/env python3
"""
smoke_live.py — اسموک‌تستِ اتصالِ زنده‌ی API (مرحله‌ی A).

مستقل از منطقِ پروژه: نه کرنل، نه ایجنت، نه گراندینگ. فقط:
  ۱) .env را لود می‌کند،
  ۲) وجودِ ANTHROPIC_API_KEY را چک می‌کند،
  ۳) یک کالِ ارزانِ هایکو (max_tokens=50) می‌زند،
  ۴) متنِ پاسخ + توکنِ usage + هزینه‌ی همان کال (با نرخِ هایکو) را چاپ می‌کند.

اجرا:  python smoke_live.py
"""
from __future__ import annotations
import os, sys

# شناسه و نرخِ هایکو ۴.۵ (USD به ازای هر ۱ میلیون توکن) — طبق دستورِ کاربر، بدونِ حدس.
HAIKU_MODEL = "claude-haiku-4-5-20251001"
PRICE_IN_PER_MTOK = 1.0
PRICE_OUT_PER_MTOK = 5.0


def load_env() -> None:
    """فقط .env کنارِ همین فایل را می‌خواند (نه .env.example)."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'").strip('"'))


def main() -> int:
    load_env()
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        print("❌ ANTHROPIC_API_KEY پیدا نشد.")
        print("   مطمئن شو فایلِ «.env» (نه .env.example) کنارِ همین اسکریپت هست و کلید را دارد.")
        return 1
    print(f"✅ کلید لود شد (پایان: …{key[-4:]}) | مدل: {HAIKU_MODEL}")

    try:
        import anthropic
    except ImportError:
        print("❌ پکیجِ anthropic نصب نیست →  pip install anthropic")
        return 1

    try:
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=50,
            messages=[{"role": "user", "content": "در یک جمله بگو سلام"}],
        )
    except Exception as e:
        print(f"❌ کالِ API ناموفق بود: {e}")
        print("   (کلیدِ نامعتبر، نبودِ اعتبار، یا قطعیِ شبکه؟)")
        return 1

    text = "".join(b.text for b in msg.content if b.type == "text")
    ti = msg.usage.input_tokens
    to = msg.usage.output_tokens
    cost = ti / 1_000_000 * PRICE_IN_PER_MTOK + to / 1_000_000 * PRICE_OUT_PER_MTOK

    print("\n────────── نتیجه ──────────")
    print(f"📝 پاسخ: {text}")
    print(f"🔢 توکن (از usage): ورودی={ti} · خروجی={to}")
    print(f"💸 هزینه‌ی این کال (نرخِ هایکو {PRICE_IN_PER_MTOK}/{PRICE_OUT_PER_MTOK}): ${cost:.6f}")
    print("───────────────────────────")
    print("✅ اگر این سه خط را دیدی، کلید معتبر است و اتصال + محاسبه‌ی هزینه سالم است.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
