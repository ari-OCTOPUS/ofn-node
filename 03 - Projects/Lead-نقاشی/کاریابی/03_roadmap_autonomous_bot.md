# Roadmap — Autonomous Lead-Hunter Bot
## ربات خودگردان کشف لید برای نقاشی ساختمان سیدنی

> **هدف:** ربات وقتی روشن می‌مونه، خودش بدون دستور
> ۱) منابع جدید لید رو **کشف** می‌کنه
> ۲) لیدهای موجود رو **رصد** می‌کنه
> ۳) با پیام تلگرام/دسکتاپ آلرت می‌ده
> ۴) هر هفته الگوهای جدید بازار رو **گزارش** می‌ده
>
> **Host:** لپ‌تاپ خودت (Windows). **Budget:** فعلاً سقف نداره. **زبان:** mixed FA/EN.

---

## معماری دو لایه

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 1: HUNTER 🕵️                       │
│              (هر ۶ ساعت، autonomous با LLM)                  │
│                                                             │
│  Goal: کشف کانال‌های جدید لید                                │
│  ─────────────────────────────                              │
│  • Web search agentic loop (Tavily/Serper/Brave)           │
│  • تحلیل سایت رقبا → کجاها لیست شدن                         │
│  • LinkedIn scrape: PMها، Procurement Managers              │
│  • Reddit/Forum monitoring: r/AustralianBusiness, etc.     │
│  • Council new tender pages discovery                       │
│  • شناسایی Builder/Developer جدید NSW                       │
│  • Trend detection: کلمات کلیدی جدید بازار                   │
│                                                             │
│  Output → channels_discovered.db                            │
│           (نام، URL، نوع، score اعتبار، نمونه لید)            │
└──────────────────────────┬──────────────────────────────────┘
                           ▼ (انسان تایید می‌کنه یا auto-add)
┌─────────────────────────────────────────────────────────────┐
│                  LAYER 2: HARVESTER 🌾                       │
│                (هر ۱۵ دقیقه، deterministic)                  │
│                                                             │
│  Goal: استخراج لید از کانال‌های تایید شده                     │
│  ─────────────────────────────                              │
│  • Scrape با Playwright / API call                          │
│  • Dedup با hash + SQLite                                   │
│  • Normalize به schema یکسان                                 │
│  • Score هر لید با LLM (relevance 0-100)                    │
│                                                             │
│  Output → leads.db + Telegram push                          │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              LAYER 3: ASSISTANT 💬                           │
│                                                             │
│  • /digest — خلاصه روزانه ۸ صبح                              │
│  • /hunt — اجبار اجرای Hunter همین الان                      │
│  • /new — لیدهای ۲۴ ساعت اخیر                                │
│  • /channels — کانال‌های کشف‌شده هفته                         │
│  • /quote <id> — تولید پیش‌نویس پیش‌فاکتور با LLM             │
│  • /draft <lead-id> — متن ایمیل cold outreach                │
│  • /report — گزارش هفتگی الگوها                              │
└─────────────────────────────────────────────────────────────┘
```

---

## فاز ۱ — MVP (هفته ۱)

**هدف:** ربات روی لپ‌تاپ run بشه، از ۳ منبع داده اولیه لید push کنه به تلگرام.

### Stack نهایی (پیشنهادی)

```python
# Core
Python 3.12
poetry / uv                        # package manager
SQLite (sqlmodel)                  # دیتابیس لوکال

# Agent loop
anthropic                          # Claude Sonnet 4.5 برای Hunter
openai                             # backup / cheap classification

# Web tools
playwright                         # scraping با JS
beautifulsoup4 + httpx
feedparser                         # RSS
tavily-python                      # web search برای Hunter

# Bot
python-telegram-bot                # interface تلگرام
apscheduler                        # cron داخلی

# Optional
brightdata / scrapingbee           # proxy برای سایت‌های سخت
serper.dev                         # SERP API
```

### Sources اولیه (فاز ۱)
1. **PlanningAlerts API** — رایگان، JSON
2. **AusTender RSS** — رایگان
3. **EstimateOne NSW** — scrape ساده
4. **NSW eTendering** — IMAP پارس ایمیل alertهای رسمی

### Deliverable فاز ۱
- ربات تلگرام لوکال که روی لپ‌تاپ run می‌شه
- روزی ~۳۰-۸۰ لید با کیفیت push می‌کنه
- digest روزانه ۸ صبح

**زمان:** ۵-۷ روز کدنویسی
**هزینه ماهانه:** ~$0 (همه رایگان)

---

## فاز ۲ — Hunter Layer (هفته ۲-۳)

اضافه کردن لایه autonomous discovery.

### قابلیت‌ها
- agent loop با Claude Sonnet که هر ۶ ساعت بیدار می‌شه
- می‌گرده دنبال:
  - شرکت‌های strata جدید سیدنی
  - Tier-2 builderها (بعد از Tier 1)
  - پنل‌های تازه اعلام شده دولتی
  - DA‌های بزرگ که هنوز پروسه paint نخوردن
  - رویدادها و expo های صنف
- هر کانال جدید رو با LLM verify می‌کنه (URL واقعیه؟ لید واقعی داره؟)
- لیست proposed channels رو می‌فرسته تلگرام، تو با /approve یا /reject تصمیم می‌گیری

### Sources اضافی (پولی، فاز ۲)
- **BCI Central / LeadManager** — subscription (~$500-1500/ماه AUD، contact for quote)
- **Cordell Connect** — Cotality subscription
- **EstimateOne Pro** — ~$200/ماه AUD
- **Tavily API** — $20-100/ماه برای web search agentic
- **Serper.dev** — $50/ماه SERP

**هزینه ماهانه فاز ۲:** ~$1000-2500 AUD (بسته به اشتراک‌ها)

---

## فاز ۳ — Outreach Automation (ماه ۲)

از کشف لید به اقدام:
- **/draft <lead>** — تولید ایمیل cold outreach شخصی‌سازی شده با LLM
- **/research <company>** — تحلیل سریع شرکت قبل از تماس (سایز، پروژه‌های اخیر، DM در LinkedIn)
- **Auto-followup queue** — یادآوری دستی روز ۳، ۷، ۱۴
- **CRM mini داخلی** — هر لید status: new / contacted / quoted / won / lost

### Sources اضافی
- **Apollo.io / Lusha** — کانتکت B2B (decision makers)
- **PhantomBuster / Bright Data** — اسکریپ LinkedIn (محدودیت‌های قانونی!)

---

## فاز ۴ — Pattern Mining (ماه ۳)

ربات حالا چند هزار لید/کانال در دیتابیس داره. این داده رو تحلیل می‌کنه:
- کدوم سابرب‌ها بیشترین density پروژه دارن؟
- کدوم builderها بیشترین RFQ برای painting می‌دن؟
- چه ساعت/روزی tender ها منتشر می‌شن؟ (response time)
- کلمات کلیدی پروژه‌های با مارجین بالا
- موقعیت‌های Niche underserved

گزارش هفتگی markdown به تلگرام push می‌شه.

---

## فاز ۵ — Voice & Field (ماه ۴+)

- Voice مکالمه با ربات (whisper + tts) موقع رانندگی
- Photo-to-quote: عکس ساختمان بفرستی، ربات سطح/شرایط رو تحلیل کنه و quote اولیه بده (Claude Vision)
- اینتگریشن با Xero/MYOB برای صدور invoice مستقیم
- اتصال به Google Calendar برای schedule auto

---

## ساختار پروژه

```
paint-leads-bot/
├── pyproject.toml
├── .env                          # API keys
├── README.md
├── bot/
│   ├── main.py                   # entry
│   ├── config.py                 # تنظیمات
│   ├── db.py                     # SQLite models
│   ├── telegram_handler.py
│   ├── scheduler.py
│   └── prompts/
│       ├── hunter.md             # ← پرامپت اصلی Hunter
│       ├── scorer.md             # امتیازدهی لید
│       ├── outreach.md           # تولید ایمیل
│       └── pattern_miner.md
├── harvesters/
│   ├── base.py
│   ├── planning_alerts.py
│   ├── austender.py
│   ├── estimate_one.py
│   ├── nsw_etendering_email.py
│   ├── hutchies.py
│   └── ... (هر منبع یه فایل)
├── hunter/
│   ├── agent.py                  # autonomous loop
│   ├── tools.py                  # web search, page fetch, verify
│   └── verifier.py
└── data/
    ├── leads.db
    ├── channels.db
    └── logs/
```

---

## Roadmap زمانی

| هفته | تحویل | چک‌لیست |
|---|---|---|
| ۱ | MVP Harvester | ✅ ربات تلگرام + ۳ منبع + digest |
| ۲ | Hunter v1 | ✅ agent loop ساده + کشف کانال |
| ۳ | Sources پولی | ✅ BCI/Cordell/EstimateOne Pro |
| ۴ | Outreach | ✅ /draft + cold email + CRM mini |
| ۵-۶ | Pattern mining | ✅ گزارش هفتگی الگو + analytics |
| ۷-۸ | Polish + Voice | ✅ voice، photo quote، auto-followup |

---

## سوال‌های قبل از شروع کدنویسی

1. **مدل LLM ترجیحی:** Claude Sonnet 4.5 (پیشنهاد من) یا GPT-5 / Gemini؟
2. **سیستم عامل لپ‌تاپ:** Windows (دیدم)، می‌خوای Docker یا run مستقیم Python؟
3. **API keys آماده داری؟** Anthropic، Tavily، Telegram bot token؟
4. **Telegram username یا chat_id خودت** برای config اولیه؟
5. **شروع کنم با چی:** سکلت پروژه + MVP Harvester، یا مستقیم برم سراغ Hunter agent؟
