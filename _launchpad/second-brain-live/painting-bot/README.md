# Paint Leads Bot — Sydney

ربات autonomous کشف لید برای نقاشی ساختمان در سیدنی.

دو لایه:
- **Harvester** — هر منبع با زمان‌بندی خودش لید می‌کشه:
  - PlanningAlerts (DAهای شوراها) — هر ۳ ساعت (سقف ۱۰۰۰ درخواست/روز رعایت می‌شه)
  - AusTender (مناقصه فدرال، API رسمی OCDS) — هر ۱ ساعت
  - NSW eTendering (RSS مناقصه‌های NSW) — هر ۱ ساعت
  - EstimateOne — غیرفعال تا Playwright/اشتراک (فایلش هست، در ALL نیست)
- **Hunter** — هر ۶ ساعت با Claude می‌گرده دنبال کانال‌های جدید

پیش‌نیاز خواندن: `../05_راهنمای_API_keys.md`

---

## نصب (Windows)

### ۱. Python 3.11+ نصب کن
بررسی:
```powershell
python --version
```
اگه نبود از python.org نصب کن. موقع نصب گزینه «Add to PATH» رو تیک بزن.

### ۲. ایجاد virtual env
داخل فولدر `bot/`:
```powershell
cd C:\Users\Armin\Documents\Claude\Projects\کاریابی\bot
python -m venv .venv
.venv\Scripts\activate
```

### ۳. نصب dependencies
```powershell
pip install --upgrade pip
pip install -e .
playwright install chromium
```

اگه `pip install -e .` به مشکل خورد، مستقیماً نصب کن:
```powershell
pip install anthropic python-telegram-bot httpx beautifulsoup4 feedparser tavily-python playwright sqlmodel apscheduler python-dotenv pydantic pydantic-settings tenacity rich pytz
playwright install chromium
```

### ۴. ایجاد .env
```powershell
copy .env.example .env
notepad .env
```
فایل رو با کلیدهای واقعی پر کن (راهنما: `../05_راهنمای_API_keys.md`).

### ۵. اولین اجرا
```powershell
python main.py
```

اگه همه‌چی درست باشه:
- در ترمینال لاگ Rich می‌بینی
- در تلگرام پیام `🚀 Paint Leads bot online` می‌گیری
- بعد چند ثانیه harvester اول اجرا می‌شه و چند لید push می‌کنه

---

## دستورات تلگرام

| دستور | کاربرد |
|---|---|
| `/start` یا `/help` | پیغام راهنما |
| `/new` | ۱۰ لید اخیر ۲۴ ساعت |
| `/digest` | ۵ تای امتیاز بالای ۲۴ ساعت |
| `/hunt` | اجبار اجرای Hunter همین لحظه |
| `/channels` | کانال‌های در انتظار تایید |
| `/stats` | شمارش لید/کانال/run |
| `/save_<id>` / `/skip_<id>` | ذخیره یا رد یک لید (دکمه‌های زیر هر پیام لید) |
| `/approve_<id>` / `/reject_<id>` | تایید یا رد کانال پیشنهادی Hunter |
| `/draft_<id>` | پیش‌نویس ایمیل outreach با Claude — **ارسال همیشه دستی توسط خودت** (Spam Act) |
| `/report` | گزارش هفتگی: لید per منبع، pipeline، کانال‌ها، مصرف توکن Hunter |

---

## ساختار فولدر

```
bot/
├── pyproject.toml
├── .env                 ← (با دست بساز، .env.example رو کپی کن)
├── .gitignore
├── README.md
├── main.py              ← entry point
├── config.py            ← خواندن .env
├── db.py                ← schemaهای SQLite (Lead, Channel, RunLog)
├── scorer.py            ← امتیازدهی لید با Claude
├── scheduler.py         ← APScheduler jobs
├── telegram_bot.py      ← دستورات تلگرام
├── prompts/
│   └── hunter.md        ← system prompt ربات Hunter
├── harvesters/
│   ├── base.py
│   ├── planning_alerts.py
│   ├── austender.py
│   └── estimate_one.py
├── hunter/
│   ├── agent.py         ← agent loop + tool use
│   └── tools.py         ← web_search, fetch_page, save_channel
└── data/                ← خودکار ساخته می‌شه
    ├── leads.db
    └── hunter_memory.md
```

---

## چرخه کاری روزانه

```
هر ۱۵ دقیقه  →  Harvester همه منابع رو می‌کشه و score می‌ده
                لیدهای score>=85 فوراً push می‌شن

هر ۶ ساعت   →  Hunter agent بیدار می‌شه، ۳-۵ کانال جدید کشف می‌کنه
                نوتیف می‌دی، تو با /channels تایید/رد می‌کنی

ساعت ۸ صبح  →  digest پنج تای برتر دیروز
```

---

## افزودن Harvester جدید

وقتی Hunter یه کانال جدید پیدا کرد و /approve کردی، یه فایل جدید در `harvesters/` بساز:

```python
# harvesters/my_new_source.py
from harvesters.base import Harvester
from db import Lead

class MyNewSourceHarvester(Harvester):
    name = "my_new_source"

    async def fetch(self) -> list[Lead]:
        # ... fetch logic
        return []
```

بعد در `harvesters/__init__.py` به `ALL` اضافه کن.

---

## تست‌ها

بدون نیاز به کلید واقعی یا اینترنت (کلیدهای dummy خودکار ست می‌شوند):
```powershell
pip install -e .[dev]
pytest tests/ -q
```

برای تست زنده منابع (با کلید واقعی): `python test_run.py --source austender`

---

## Troubleshooting

**ربات پیام نمی‌فرسته:**
- `TELEGRAM_BOT_TOKEN` و `TELEGRAM_CHAT_ID` رو چک کن
- یه بار خودت در تلگرام `/start` بزن به ربات

**`401 Unauthorized` از Anthropic:**
- کلید رو دوباره کپی کن
- مطمئن شو credit در console.anthropic.com داری

**PlanningAlerts خالی برمی‌گردونه:**
- API key رو verify کن: `https://api.planningalerts.org.au/applications.json?key=YOUR_KEY&authority=sydney`

**Playwright error:**
```powershell
playwright install chromium
```

**خواستی همیشه run باشه:**
- ساده‌ترین راه: یه shortcut روی desktop به `python C:\path\to\main.py`
- یا Task Scheduler ویندوز رو طوری تنظیم کن که at-startup اجرا کنه
- یا با `nssm` به‌عنوان Windows service نصب کن

---

## مرحله بعد

انجام شد: ✅ `/draft` (پیش‌نویس outreach) · ✅ statusهای CRM (save/skip + shown/saved/skipped) · ✅ AusTender OCDS · ✅ NSW eTendering RSS

باقی‌مانده:
1. خرید subscription BCI Central و یه harvester `bci_central.py` اضافه کن
2. IMAP harvester برای پارس ایمیل alertهای رسمی (builderها + tenders.nsw.gov.au)
3. تکمیل CRM: دستورهای `/quoted_<id>` `/won_<id>` `/lost_<id>` + حلقه بازخورد به scorer
4. EstimateOne با Playwright یا اشتراک paid
5. کالیبراسیون scorer با نتایج واقعی (پرامپت تحقیقاتی #۷ در `06_پرامپت‌های_تحقیقاتی`)
