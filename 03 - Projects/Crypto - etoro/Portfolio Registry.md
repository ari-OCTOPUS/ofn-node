---
type: reference
status: active
project: "[[03 - Projects/Crypto - etoro/PROJECT]]"
tags: [crypto, portfolio, registry]
created: 2026-07-03
updated: 2026-07-03
---

# Portfolio Registry — رجیستری پوزیشن‌ها

> یک بلوک برای هر پوزیشن. **exit_rules خالی = صفر autonomy برای آن پوزیشن** ([[04 - Architect System/architect/ARCHITECT_CHARTER|§Trading Autonomy]]). فقط آری این فایل را نهایی می‌کند؛ ایجنت‌ها فقط فیلد evidence را پیشنهاد می‌دهند.

## قالب پوزیشن (کپی کن)

```yaml
position: ""            # نماد/دارایی
platform: eToro
size_pct: 0             # ٪ از پرتفوی
thesis: ""              # چرا وارد شدیم — یک پاراگراف
invalidation_level: ""  # چه چیزی thesis را باطل می‌کند (قیمت/رویداد)
evidence: []            # لینک نوت‌های تحقیق (ایجنت پر می‌کند)
exit_rules:             # قواعد از پیش ثبت‌شده فروش/کاهش — تأیید کتبی آری
  - ""                  # مثال: "اگر قیمت < X بست → فروش کامل"
  - ""                  # مثال: "۴۸h قبل از <رویداد باینری> → trim به ۲–۳٪"
approved_by_owner: no   # تا yes نشود، exit_rules اجرایی نیست
updated: YYYY-MM-DD
```

## پوزیشن‌های فعال

*(خالی — مالک وارد کند `[To measure]`)*

## پوزیشن‌های بسته (آرشیو یادگیری)

*(خالی)*
