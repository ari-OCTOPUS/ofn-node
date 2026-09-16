# راهنمای راه‌اندازی ربات تلگرام SENTINEL

---

## مرحله ۱ — ساخت ربات در تلگرام

۱. در تلگرام `@BotFather` رو باز کن
۲. بنویس: `/newbot`
۳. یه اسم برای ربات بده (مثلاً: `Sentinel Monitor`)
۴. یه username بده (باید به bot ختم بشه، مثلاً: `sentinel_armin_bot`)
۵. BotFather یه **Token** بهت می‌ده — این رو کپی کن

مثال Token:
```
<REDACTED-telegram-bot-token-see-secrets-export>
```

---

## مرحله ۲ — پیدا کردن Chat ID

۱. ربات خودت رو در تلگرام پیدا کن و `/start` بزن
۲. این URL رو در مرورگر باز کن (token خودت رو جایگزین کن):

```
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```

۳. جواب JSON می‌گیری — دنبال `"chat":{"id":` بگرد:

```json
"chat": {
  "id": 123456789,   ← این عدد chat_id توست
  "type": "private"
}
```

---

## مرحله ۳ — تنظیم .env

فایل `.env` رو در پوشه sentinel باز کن و پر کن:

```env
TELEGRAM_BOT_TOKEN=<REDACTED-telegram-bot-token-see-secrets-export>
TELEGRAM_CHAT_ID=123456789
```

---

## مرحله ۴ — اجرای ربات

```bash
# رفتن به پوشه sentinel
cd sentinel

# نصب dependencies (اگر نصب نیست)
pip install -r requirements.txt

# اجرای ربات
python3 telegram_bot.py
```

اگه همه چیز درست باشه، یه پیام می‌رسه:
> 🟢 SENTINEL راه‌اندازی شد — آماده‌ی دریافت دستور

---

## دستورات ربات

| دستور | کار |
|-------|-----|
| `/start` | خوش‌آمدگویی |
| `/help` | لیست همه دستورات |
| `/ping` | چک اتصال |
| `/status` | وضعیت فاز و سیستم |
| `/report` | گزارش روزانه همین الان |
| `/score BTC` | امتیاز فوری BTC |
| `/score ETH` | امتیاز فوری ETH |
| `/portfolio` | وضعیت کامل پرتفوی |
| `/confirm_BTC 500 86400` | ثبت خرید ۵۰۰ دلار BTC به قیمت ۸۶۴۰۰ |
| `/scenario fiat_erosion active` | فعال کردن سناریو |

---

## اجرای همزمان با pipeline

اگه می‌خوای هم pipeline رو داشته باشی هم ربات رو، دو ترمینال باز کن:

**ترمینال ۱ — pipeline:**
```bash
python3 main.py
```

**ترمینال ۲ — ربات:**
```bash
python3 telegram_bot.py
```

یا با `screen` روی Raspberry Pi:
```bash
screen -S sentinel-pipeline   # ترمینال ۱
python3 main.py

# Ctrl+A+D برای detach
screen -S sentinel-bot        # ترمینال ۲
python3 telegram_bot.py
```

---

## عیب‌یابی

**ربات پیام نمی‌فرسته:**
- token رو چک کن
- اینترنت Pi/لپ‌تاپ رو چک کن

**`TELEGRAM_BOT_TOKEN در .env تعریف نشده` خطا:**
- مطمئن شو فایل `.env` (نه `.env.example`) وجود داره
- مطمئن شو token وارد شده

**پیام می‌رسه ولی ربات جواب نمی‌ده:**
- chat_id رو چک کن — باید عدد باشه، نه username
- مطمئن شو ربات رو start کردی
