# LANGAR — بات تلگرامِ شخصیِ همیشه‌روشن

یک بات single-user برای ثبت RMSSD، خواب، مصرف و بینش‌ها — با kill-switch واقعی و gate امنیتی.
بر اساس HANDOFF پروژه‌ی «قلب و آگاهی».

## فایل‌ها

| فایل | کار |
|---|---|
| `main.py` | نقطه‌ی ورود — env، init، polling |
| `bot.py` | هندلرها، گفتگوها، gate و kill-switch |
| `db.py` | لایه‌ی SQLite — schema، config، ترند |
| `requirements.txt` | وابستگی‌ها |
| `langar_bot.service` | سرویس systemd (همیشه‌روشن) |
| `.env.example` | الگوی متغیرهای محیطی |

## دستورها

| دستور | کار | معاف از halt؟ |
|---|---|---|
| `/start` | معرفی | خیر |
| `/log` | ثبت پنج‌مرحله‌ای (RMSSD→خواب→مصرف→مکان→یادداشت) | خیر |
| `/trend [N]` | میانگین RMSSD + همبستگی با خواب/مصرف (پیش‌فرض N=۷) | خیر |
| `/insight <متن>` | ثبت بینش با تگ E/S/P؛ داوری برای فردا زمان‌بندی می‌شود | خیر |
| `/recheck` | بینش‌های امروز را با دکمه‌ی تأیید/رد نشان می‌دهد (HITL، **برگشت‌ناپذیر**) | خیر |
| `/export` | خروجی JSON از همه‌ی log‌ها و بینش‌ها (به‌صورت فایل) | خیر |
| `/status` | آخرین log + وضعیت سیستم | ✅ بله |
| `/halt` | توقف فوری — همه ساکت | ✅ بله |
| `/resume` | ادامه | ✅ بله |

> **نکته‌ی امنیتی مهم:** `/halt`، `/resume` و `/status` عمداً از gate معاف‌اند. اگر معاف نبودند، پس از `/halt` خودِ `/resume` هم ساکت می‌شد و بات قفل می‌شد. این طراحیِ درستِ kill-switch است.

## اجرای محلی (تست)

```bash
cd langar
python -m venv venv
source venv/bin/activate          # ویندوز: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # و مقادیر واقعی را بگذار
python main.py
```

در تلگرام `/start` بزن. اگر جواب داد، آماده‌ی deploy است.

## راه‌اندازی روی VPS — پنج گام

**۱) بات بساز** — در تلگرام `@BotFather` → `/newbot` → توکن.

**۲) chat_id بگیر** — به `@userinfobot` پیام بده → عددِ id خودت = `OWNER_ID`.

**۳) VPS** — Hetzner CX11 یا DigitalOcean، Ubuntu 22.04، Python 3.11.

**۴) deploy:**

```bash
sudo adduser --disabled-password ubuntu   # اگر کاربر ubuntu نداری
sudo su - ubuntu
git clone <repo> langar      # یا فایل‌ها را کپی کن داخل /home/ubuntu/langar
cd langar
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env
nano .env                    # BOT_TOKEN و OWNER_ID را پر کن
venv/bin/python main.py      # تست — /start بزن، بعد Ctrl+C
```

**۵) همیشه‌روشن:**

```bash
sudo cp langar_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable langar_bot
sudo systemctl start langar_bot
sudo systemctl status langar_bot      # باید active (running) باشد
journalctl -u langar_bot -f           # لاگ زنده
```

> اگر مسیر یا کاربر فرق دارد، `WorkingDirectory`، `User` و `ExecStart` را در `.service` ویرایش کن.

## تستِ kill-switch (قبل از اعتماد، حتماً)

1. `/halt` بزن → باید بگوید «سیستم متوقف شد».
2. `/log` بزن → باید **هیچ پاسخی ندهد** (سکوت کامل).
3. `/resume` بزن → باید بگوید «دوباره فعال شد».
4. `/log` بزن → حالا باید کار کند.

اگر مرحله‌ی ۳ کار نکرد، یعنی gate اشتباه روی resume اعمال شده — در این کد چنین نیست.

## اصول LANGAR که در کد رعایت شده

- **gate قبل از هر خروجی** — دکوریتور `guarded`
- **فقط مالک** — دکوریتور `owner_only` (مقدار OWNER_ID تنبل خوانده می‌شود تا باگِ ترتیبِ بارگذاری پیش نیاید)؛ غریبه = سکوت، نه پیام خطا
- **kill-switch واقعی و معاف از gate**
- **Human-write-only و برگشت‌ناپذیر برای verdict** — verdict فقط با دکمه‌ی انسان و فقط یک‌بار ثبت می‌شود؛ بازداوری ممکن نیست
- **شاخص قفل‌شده** — همیشه RMSSD
- **در شک: سکوت**

## فاز ۱ (بعد از ۲ هفته)

- پینگ صبحگاهی خودکار با `JobQueue` (`pip install "python-telegram-bot[job-queue]"`)
- مرور هفتگی خودکار
- Apple Shortcut → HTTP POST → ثبت خودکار RMSSD از Health
