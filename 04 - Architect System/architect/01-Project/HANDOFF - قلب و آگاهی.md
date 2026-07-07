---
type: reference
status: active
tags: [langar, heart-awareness, always-on, spec]
updated: 2026-07-04
---

# HANDOFF — قلب و آگاهی + سیستم همیشه‌روشن

> این فایل یک handoff کامل برای انتقال context به یک AI جدید است.
> هیچ فایل خارجی‌ای نیاز نیست — همه چیز اینجاست.

---

## زمینه‌ی پروژه

**صاحب پروژه:** Armin  
**هدف کلی:** یک سیستم شخصی N-of-1 برای بررسی رابطه‌ی ماریجوانا، ضربان قلب، و آگاهیِ درونی (interoception) — با یک بات تلگرام به‌عنوان رابط همیشه‌روشن.

دو بخش جداگانه:
1. **نقشه‌ی پژوهش (HTML)** — مرجع علمی + پروتکل‌های عملی
2. **سیستم همیشه‌روشن (Markdown)** — معماری بات تلگرام + دستورالعمل ساخت

---

## بخش ۱ — نقشه‌ی پژوهش (heart-awareness-map-v3.html)

### خلاصه‌ی آنچه ساخته شده

یک صفحه‌ی HTML با طراحی dark-mode و متن فارسی RTL که:
- شواهد علمی را با تگ E (مستحکم) / S (حدس) / P (استعاره) دسته‌بندی می‌کند
- پروتکل‌های مشخص برای ۵ آزمایش N-of-1 دارد
- یک قالب لاگ روزانه دارد
- یک بخش «امروز چه کار کنم» در ابتدا دارد

### پنج آزمایش (E1–E5)

**E1 — منحنی autonomic:** اندازه‌گیری RMSSD در سه نقطه (قبل / onset / peak نشئگی) برای پیدا کردن عددِ tip-over شخصی.

**E2 — accuracy × confidence:** شمارش ضربان قلب بدون ابزار + ثبت میزان اطمینان → مقایسه‌ی هوشیار vs نشئه. از دو سنجه استفاده شود (شمارش + تشخیص هم‌زمانی).

**E3 — تست زمان:** تخمین ۳۰ ثانیه بدون ساعت → تأیید یا رد tolerance.

**E4 — retest بینش:** هر بینشِ نشئه را تگ [E/S/P] بزن → فردای هوشیار داوری کن.

**E5 — baseline خالص واگ:** یک روز بدون مصرف، RMSSD صبح + بعد از تنفس رزونانس + عصر → جدا کردن اثر THC از نوسانِ روزانه.

### یافته‌های علمی کلیدی (تأییدشده)

- **THC:** dose-dependent HR↑, HF-HRV↓. مدل PBPK-PD 2025 منحنی را کمّی کرد. [E]
- **taVNS 2025:** SDNN بالا رفت ولی RMSSD نه → مکانیسم: کاهش سمپاتیک، نه افزایش واگ. [E]
- **Interoception:** شمارش ضربان به‌تنهایی شکننده (Ferentzi 2025) — دو سنجه لازم است. [E]
- **HRVB:** برای افسردگی g=−0.41 معنادار، برای HRV g=+0.44. برای اضطراب/استرس: null. [S]
- **Kaduk 2025 تصحیح:** «غذا روی واگ» ادعای پشتیبانی‌نشده است. taVNS مستقل از کالری HRV را کاهش داد.

### قالب لاگ روزانه

| فیلد | مقدار | یادداشت |
|---|---|---|
| تاریخ | YYYY-MM-DD | همیشه |
| RMSSD | عدد ms | صبح · قبل از کافئین · ۲ دقیقه |
| خواب | ۱–۵ | ۱=خیلی بد، ۵=عالی |
| مصرف | بله/خیر | اگر بله: دوز و زمان |
| مکان | خانه/کار | |
| یادداشت | اختیاری | بینش با تگ E/S/P |

### حلقه‌ی روزمره

- **صبح (۱۲–۱۵ دقیقه):** baseline RMSSD → تنفس رزونانس ۶ نفس/دقیقه
- **حین روز (on-demand):** sigh دوگانه هر وقت موجِ عاطفی بالا زد
- **هفتگی (۱۰ دقیقه):** ترند ۷ روزه + cross-reference با خواب/مصرف

---

## بخش ۲ — سیستم همیشه‌روشن (Markdown)

### خلاصه‌ی آنچه ساخته شده

یک دستورالعمل MVP-first برای ساختن یک بات تلگرام شخصی با:
- معماری ۵ فایل ساده (بدون hash-chain، بدون Wilson score، بدون execution rings)
- Gate ساده (flag در SQLite)
- Kill-switch واقعی (`/halt`)
- Schema کامل
- کد Python واقعی برای gate و kill-switch
- ConversationHandler برای `/log`
- پرامپت ساده‌شده برای ایجنت کدنویس

### معماری MVP

```
VPS Linux
├── langar/
│   ├── main.py
│   ├── bot.py
│   ├── db.py
│   ├── .env          (BOT_TOKEN, OWNER_ID, CLAUDE_KEY)
│   └── requirements.txt
└── langar_bot.service
```

### Schema SQLite

```sql
CREATE TABLE IF NOT EXISTS log (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    ts    TEXT    NOT NULL DEFAULT (datetime('now')),
    rmssd REAL,
    sleep INTEGER,   -- 1–5
    used  INTEGER,   -- 0/1
    loc   TEXT,      -- home/work/other
    note  TEXT
);

CREATE TABLE IF NOT EXISTS insight (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      TEXT    NOT NULL DEFAULT (datetime('now')),
    content TEXT,
    tag     TEXT,   -- E / S / P
    recheck TEXT,   -- YYYY-MM-DD
    verdict TEXT    DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    val TEXT
);
INSERT OR IGNORE INTO config VALUES ('halted', '0');
```

### Gate و Kill-switch

```python
# db.py
def is_halted() -> bool:
    return get_config("halted") == "1"

# bot.py
async def any_handler(update, ctx):
    if is_halted():
        return  # سکوت کامل

async def cmd_halt(update, ctx):
    if str(update.effective_user.id) != OWNER_ID:
        return
    db.set_config("halted", "1")
    await update.message.reply_text("⏸ سیستم متوقف.")

async def cmd_resume(update, ctx):
    if str(update.effective_user.id) != OWNER_ID:
        return
    db.set_config("halted", "0")
    await update.message.reply_text("▶ ادامه.")
```

### دستورها

| دستور | کار |
|---|---|
| `/start` | معرفی |
| `/log` | ConversationHandler پنج‌مرحله‌ای |
| `/trend [N=7]` | میانگین RMSSD + correlation با خواب/مصرف |
| `/insight [متن]` | ثبت بینش با E/S/P و recheck |
| `/recheck` | بینش‌های امروز |
| `/status` | آخرین log + halted/active |
| `/halt` | توقف |
| `/resume` | ادامه |

### ConversationHandler /log — پنج مرحله

1. RMSSD (عدد یا /skip)
2. خواب (۱–۵)
3. مصرف (بله/خیر)
4. مکان (خانه/کار/جای دیگر)
5. یادداشت (اختیاری)

### پرامپت برای کدنویس

```
یک بات تلگرامِ شخصیِ single-user بساز.

Stack: Python 3.11 / python-telegram-bot v21 (async) / SQLite / python-dotenv
Security: BOT_TOKEN و OWNER_ID از .env؛ فقط OWNER_ID پاسخ می‌گیرد.
اول هر handler: if is_halted(): return

Schema: [جدول بالا]

Commands: [جدول بالا]

/log با ConversationHandler پنج‌مرحله‌ای
/trend با میانگین RMSSD و Pearson correlation با sleep/used
/insight با ذخیره و recheck date
/recheck بینش‌های recheck=today
/halt و /resume برای kill-switch

Output: main.py + bot.py + db.py + requirements.txt + systemd service + README deploy
```

### راه‌اندازی — پنج گام

1. `@BotFather` → `/newbot` → توکن
2. `@userinfobot` → chat_id
3. VPS بگیر (Hetzner/DigitalOcean، ~۵ دلار/ماه)
4. کد deploy کن + `.env` پر کن + تست
5. `systemctl enable langar_bot && systemctl start langar_bot`

### اصول LANGAR که باید حفظ شود

- gate قبل از هر پیام خروجی
- Human-write-only برای verdict (بات پیشنهاد، تو تأیید)
- kill-switch تست‌شده
- همیشه RMSSD — هرگز شاخص‌ها را مخلوط نکن
- در شک: سکوت

### فازهای بعدی

- **فاز ۱ (بعد از ۲ هفته):** پینگ صبحگاهی خودکار، مرور هفتگی، Apple Shortcut
- **فاز ۲ (بعد از ۱ ماه):** FUSION، Microsoft Agent Governance Toolkit، Wilson score

---

## وضعیت فعلی

- ✅ نقشه‌ی پژوهش v3 ساخته شد (HTML)
- ✅ دستورالعمل سیستم ساده‌شد (Markdown)
- ✅ هر دو فایل commit شدند
- ⏳ کد بات هنوز نوشته نشده — پرامپت آماده است
- ⏳ VPS راه‌اندازی نشده

## گام بعدی پیشنهادی

پرامپت بخش «پرامپت برای کدنویس» را به یک AI کدنویس (Claude/GPT) بده تا کد کامل بات را تولید کند. بعد طبق پنج گام راه‌اندازی روی VPS deploy کن.

---

*ساخته‌شده با Claude Sonnet 4.6 · ژوئن ۲۰۲۶*
