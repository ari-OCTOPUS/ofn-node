---
type: instructions
status: active
project: "[[03 - Projects/Crypto - etoro/PROJECT]]"
tags: [crypto, rules, governance]
created: 2026-07-03
updated: 2026-07-03
---

# Standing Rules — قواعد ثابت معاملات

> تغییر این قواعد فقط با verdict آری و ثبت در ledger. ایجنت‌ها پیشنهاد اصلاح می‌دهند، اعمال نمی‌کنند.

1. **رویداد باینری** (اعلام SEC/ETF، هاوینگ، دادگاه، لیستینگ بزرگ): پیش از رویداد، پوزیشن مربوطه به **۲–۳٪** trim می‌شود — اگر قاعده‌اش در exit_rules همان پوزیشن ثبت و تأیید شده باشد.
2. **BUY فقط انسانی — با هر مبلغی.** ایجنت‌ها فقط evidence جمع می‌کنند (D1). هیچ استثنایی ندارد.
3. **SELL خودکار فقط از مسیر exit_rules** ثبت‌شده و تأییدشده — با سه شرط همزمان: Security Gate باز + ورودی Anchor Ledger + نوتیف فوری تلگرام. SELL اختیاری = verdict.
4. **کلیدهای exchange:** off-box کامل، صفر دسترسی LLM، امضای همراه انسان (D-11).
5. **وضعیت فعلی:** مسیر اجرای خودکار وجود ندارد `[Assumption: eToro API معاملاتی retail ندارد]` → همه اجراها دستی توسط آری؛ ایجنت‌ها alert-only.
6. تصمیم مالی cross-model چک می‌شود (D-09: داور بین‌خانواده، مثل Gemini) پیش از ارائه به انسان.
