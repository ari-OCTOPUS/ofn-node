# BOTS-REGISTRY — وضعیتِ تمامِ ربات‌های تلگرام (verdict 2026-07-18 integration-debug)

> منبعِ واحدِ حقیقت برای اینکه کدام ربات زنده است، کدام مرده، و کدام خطرِ 409 دارد.
> هر تغییری در ربات‌ها باید این‌جا هم به‌روز شود.

## 📊 خلاصه‌ی اجرایی

از ۹ ربات تعریف‌شده در پروژه، فعلاً **فقط ۲ ربات زنده و در حال poll** هستند.
ریسکِ فعلیِ 409 Conflict = **پایین** (نظری)، چون هیچ دو رباتی با tokenِ یکسان همزمان poll نمی‌کنند.

## 🤖 فهرست ربات‌ها

| # | نام | Bot ID | Token env | وضعیت | Entry file |
|---|-----|--------|-----------|-------|------------|
| 1 | **Octopus Unified Bot** (approval) | `8187434784` | `TELEGRAM_BOT_TOKEN` (.env:18) | ✅ **LIVE** | `_ops/budget/approval_channel.py` |
| 2 | **TG Center Bot** (group cmd centre) | `7992324219` | `TG_CENTER_BOT_TOKEN` (.env:28) | ✅ **LIVE** | `_ops/telegram_center/center.py` |
| 3 | **Ziman Studio Bot** (مامان) | `8861821707` | `TG_ZIMAN_STUDIO_BOT_TOKEN` (.env:24) | ⚠️ DORMANT — کد مصرف‌کننده پیدا نشد | (نامشخص) |
| 4 | **Saba Studio Bot** | (ساخته‌نشده) | `TELEGRAM_SABA_BOT_TOKEN` (placeholder) | ⚠️ DORMANT — token هنوز در BotFather ساخته نشده | `03 - Projects/اونلی فنز/studio/saba_studio.py` |
| 5 | **Painting Bot** | `8824797527` | `PAINTING_TELEGRAM_TOKEN` (control-brain/.env:8) | ⚠️ DORMANT — در _launchpad، کد موجود ولی لانچ نمی‌شود | `_launchpad/.../painting-bot/telegram_bot.py` |
| 6 | **Accounting Bot** (Node.js) | `7992324219` | `ACCOUNTING_TELEGRAM_TOKEN` (control-brain/.env:9) | ⚠️ DORMANT — با #2 هم‌ID | `_launchpad/.../accounting-bot/bot.js` |
| 7 | **Control Brain Bot** | `8187434784` (با #1 مشترک!) | `TELEGRAM_TOKEN` (control-brain/.env:2) | ⚠️ DORMANT — خطرِ 409 اگه لانچ شود | `_launchpad/.../control-brain/adapters/telegram_bot.py` |
| 8 | **LangarBot** (Project-F cockpit) | — | `TELEGRAM_LANGAR_BOT_TOKEN` (تنها در کد) | ⚠️ DORMANT — env مقدار ندارد | `03 - Projects/اونلی فنز/langar/langar_bot.py` |
| 9 | **4D Brain Bot** | — | `TELEGRAM_BOT_TOKEN` (با #1 مشترک) | ⚠️ DORMANT — خطرِ 409 اگه لانچ شود | `4d_system/brain/telegram_bot.py` |

## 🚨 خطراتِ بحرانی (۴۰۹ Conflict)

| ریسک | شرح | احتمال فعلی | کم‌کردن |
|------|------|-------------|---------|
| **#1 و #7 هم‌ID** | Octopus Unified و Control Brain هر دو `8187434784`. اگه هر دو poll کنند → 409. | پایین (#7 لانچ نمی‌شود) | token را unify کن یا #7 را به‌طور رسمی deprecate کن |
| **#2 و #6 هم‌ID** | TG Center و Accounting هر دو `7992324219`. | پایین (#6 لانچ نمی‌شود) | هم‌token‌شان کن یا یکی را بکش |
| **#1 و #9 هم‌token** | Octopus Unified و 4D Brain هر دو از `TELEGRAM_BOT_TOKEN` استفاده می‌کنند. | پایین (#9 لانچ نمی‌شود) | 4D Brain را به token جدا منتقل کن |

## 🔒 قواعدِ تک‌نمونه (Singleton Guards)

| ربات | singleton guard دارد؟ | توصیه |
|------|----------------------|-------|
| Organism (8771) | ✅ port-bind انحصاری | - |
| Cortex (8772) | ✅ port-bind انحصاری | - |
| Live Cockpit (8773) | ✅ port-bind انحصاری | - |
| TG Center | ⚠️ file-lock (`STOP-TG-CENTER`) | کافی |
| **Saba Studio** | ❌ ندارد | اضافه کن پیش از لایو شدن |
| **LangarBot** | ❌ ندارد | اضافه کن پیش از لایو شدن |

## 📝 نکاتِ مهم

1. **توکن‌ها همیشه در `.env`** (gitignored)، هرگز در `OCTOPUS-flags.cmd` (که non-secret است).
   - انتقال: `TG_CENTER_BOT_TOKEN` در 2026-07-18 از flags.cmd به .env منتقل شد. ✅
2. **chat-idهای مجاز** باید always-on باشند (ربات فقط به owner جواب می‌دهد).
3. **هر رباتِ جدید** باید در این فایل ثبت شود و singleton guard داشته باشد.

## 🛠️ راهنمایِ فعال‌سازیِ رباتِ Saba (وقتی owner آماده بود)

1. در BotFather یک bot بساز (نامِ بی‌ربط به برند):
   - دستور: `/newbot` → نام → username
2. توکن را در `.env` بگذار:
   ```
   TELEGRAM_SABA_BOT_TOKEN=<token_از_BotFather>
   TELEGRAM_SABA_CHAT_ID=<chat-id_صبا>
   ```
3. chat-id صبا را بگیر (پیام به ربات → بررسیِ `getUpdates`).
4. ربات را لانچ کن:
   ```
   cd "F:\backup\03 - Projects\اونلی فنز\studio"
   run-saba.bat
   ```
5. (اختیاری) auto-restart در startup:
   ```
   schtasks /Create /TN "OCTOPUS-Saba-Studio" /SC ONLOGON /TR "F:\backup\03 - Projects\اونلی فنز\studio\run-saba.bat"
   ```

## 🔗 پیشنهادِ Singleton Guard برای saba_studio و langar_bot

هر دو باید قبل از لایو شدن این الگو را بپذیرند (الگوی organism.py:160):

```python
import socket
def _acquire_singleton_lock(lock_port: int = 8774) -> bool:
    """bind انحصاری به port؛ OSError یعنی نمونه‌ی دیگری زنده است."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        s.bind(("127.0.0.1", lock_port))
        s.listen(1)
        return True
    except OSError:
        return False  # نمونه‌ی دیگری زنده است
```

پورت‌های پیشنهادی: Saba = 8774، Langar = 8775.
