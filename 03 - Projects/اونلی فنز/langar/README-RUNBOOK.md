---
type: runbook
project: "[[PROJECT]]"
tags: [project-f, cockpit, runbook, ops]
up: "[[LANGAR-SPEC]]"
updated: 2026-07-10
---

# ⚓ Langar — Runbook فعال‌سازی (گیت‌دار)

> فعال‌سازی = verdict ردیف ۱۰ در THREAD-CLOSURE §۹. ساخت bot در BotFather **اکشن بیرونی است و فقط دست آری**. قاعدهٔ منشور: هر اتوماسیون جدید فقط بعد از **یک هفته اجرای دستی موفق**.

## گام ۰ — تست‌ها ($0، بدون شبکه)
```
cd "<پوشهٔ پروژه>/langar"
python3 -m unittest test_langar -v      # همهٔ ۸ تست باید سبز باشد
```

## گام ۱ — Shadow-mode (هفتهٔ اول، بدون تلگرام)
```
python3 langar_bot.py        # بدون env → stdin؛ دستور بزن: /status /verdicts /upgrade
```
هر روز یک‌بار /status و جمعه /upgrade — اگر ۷ روز بدون خطا بود، برو گام ۲.

## گام ۲ — اتصال تلگرام (پس از verdict)
1. خودت در BotFather یک bot بساز (نام بی‌ربط به برند/نیش؛ مثلاً «LangarOps»). توکن را جایی commit نکن.
2. chat-id خودت را بگیر (پیام به bot ‏+ ‏getUpdates یا @userinfobot).
3. env:
```
export TELEGRAM_LANGAR_BOT_TOKEN="123:ABC"
export TELEGRAM_ARI_CHAT_ID="123456789"
# اختیاری (پس از verdict V3):
export ANTHROPIC_API_KEY="sk-..."
export LANGAR_MONTHLY_CAP_AUD="15"
python3 langar_bot.py
```
4. `langar_config.json` → آرایهٔ `blocklist` را با نام‌های واقعی پر کن (redact خودکار).

## قواعد ثابت
- لنگر فقط به chat-id تو جواب می‌دهد؛ غریبه = سکوت.
- صفر رسانه/PII؛ همهٔ متن‌ها از OpsecGuard رد می‌شوند؛ بیرون از پوشه فقط «Project-F».
- propose-only: هیچ پست/DM/اکانت/پرداخت؛ /upgrade فقط فایل proposal می‌نویسد؛ اعمال = دست تو.
- `/kill` هر لحظه؛ فایل `KILL` را هم می‌توانی دستی بسازی.
- هر اخطار/رفتار عجیب → kill + ثبت در DecisionLog (قاعدهٔ منشور).
