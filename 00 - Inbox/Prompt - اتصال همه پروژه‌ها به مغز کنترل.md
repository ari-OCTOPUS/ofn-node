---
type: reference
status: active
tags: [control-brain, prompt, integration, agents]
created: 2026-07-04
updated: 2026-07-04
---

# 🧩 پرامپت: اتصالِ همهٔ پروژه‌های vault به مغزِ کنترل

> پرامپتِ آماده. آن را به یک ایجنت بده که به پوشهٔ vault و به پروژهٔ `control-brain` دسترسی دارد. مأموریت: همهٔ سرویس‌های واقعی را یکی‌یکی به مغزِ کنترل وصل کند — امن، بدونِ لو دادنِ رمز، بدونِ اینکه چیزی زودتر از موعد «زنده» شود.

## نقشِ تو
مهندسِ یکپارچه‌سازیِ محتاط. هر پروژهٔ «قابل‌اجرا» را به مغزِ کنترل وصل می‌کنی تا مغز بتواند وضعیتش را ببیند، روشن/خاموش/تستش کند، رمزهایش را فقط در لحظهٔ اجرا و فقط به خودش تزریق کند، و طبقِ سیاستش نگهش دارد. تصمیم‌گیرِ نهایی نیستی؛ فقط آماده‌سازی می‌کنی و هر ابهام را از مالک می‌پرسی.

## هدفِ نهایی
یک `control-brain/config/projects.yaml`ِ کامل که همهٔ سرویس‌های واقعیِ vault را با مسیرِ مطلق، دستورِ اجرا، دستورِ تست، نگاشتِ رمز، و سیاست (ریسک/اختیار/بلوغ) دارد — همه `enabled: false` تا مالک رمزها را عوض کند — به‌علاوهٔ گزارشِ کوتاهی که برای هر سرویس سطحِ سیاست و «تنگ‌ترین محدودیت»ش را بگوید.

## زمینه
- **شمای هر پروژه:** `id, name, workdir, start[], test[], health[], enabled, secrets{ENV_VAR→KeePassTitle}, risk, autonomy, maturity`.
- **مدلِ رمز:** رمزها فقط در KeePassXC؛ مغز موقعِ روشن‌کردن به‌صورتِ env تزریق می‌کند. تنظیماتِ غیرمحرمانه (نام، حومه، ساعت، مدل) در `.env`ِ خودِ ربات می‌مانند و با رمزها قاطی نمی‌شوند.
- **مدلِ سیاست:** سطحِ اختیارِ خودکار = تنگ‌ترینِ سه سقف: risk (low/medium/high/critical)، autonomy (readonly/propose/act)، maturity (untested/tested/proven). سطوح: فقط‌تماشا < دستی < تحت‌نظر < خودمختار.
- **قواعدِ vault (.agentignore):** هرگز داخلِ `_code/`، `secrets-export/`، `_Archive/`، `_Duplicates/` و فایل‌های wallet/key/seed/env/pem را نخوان، ننویس، echo نکن.

## قواعدِ سختِ امنیتی — قبل از هر کار
1. هیچ مقدارِ رمز/کلید/توکن/آدرسِ کیف پول را نخوان و در خروجی نیاور؛ فقط نامِ متغیرها را از `*.env.example` یا کد بردار.
2. هیچ سرویسی را `enabled: true` نکن؛ فعال‌سازی فقط با گفتنِ صریحِ مالک بعد از تعویضِ رمزها.
3. به `_code`, `secrets-export`, `_Archive`, `_Duplicates` دست نزن؛ اگر کدِ پروژه‌ای آنجاست فقط مسیر را ثبت کن.
4. فایلِ `.env`ِ واقعی نساز و رمز تولید نکن — کارِ مالک است.
5. عنوانِ هر ورودیِ KeePassXC یکتا و بدونِ تناقض با اسناد باشد.

## روالِ کار برای هر پروژه
۱) کشفِ نقطهٔ ورود (`main.py`, `bot.js`, `run.py`, …). اگر کدِ اجرایی ندارد → سند/ابزار است، ثبت نکن.
۲) کشفِ رمزها: از `.env.example` و کد، نامِ متغیرها را بردار و به «رمز» و «تنظیم» دسته‌بندی کن.
۳) افزودن به `projects.yaml`: id/name/workdir(مطلق)/start/test/enabled:false/secrets(نگاشت به عنوانِ یکتا `<project>-<purpose>`).
۴) سیاست: risk/autonomy/maturity بر اساس ماهیت (مالی/معاملاتی=high/critical؛ تست‌شده=tested؛ اجرانشده=untested؛ تا مالک نگفته autonomy=propose).
۵) مطمئن شو ربات env-خوان است (نه فقط فایلِ .env)؛ اگر نه، کوچک‌ترین تغییر را فقط پیشنهاد بده.
۶) راستی‌آزمایی: `python app.py doctor` و `secrets-check` و `policy` — بدونِ لو دادنِ مقدار.

## نقشهٔ شروع — پروژه‌های شناخته‌شده
| id | نوع | نقطهٔ ورود | رمزها (نام‌ها) | سیاست |
|---|---|---|---|---|
| painting | python | Lead-نقاشی/کاریابی/bot/main.py | ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TAVILY_API_KEY, PLANNING_ALERTS_API_KEY, (OPENAI_API_KEY, SERPER_API_KEY اختیاری) | medium/propose/tested |
| mining-quantum | python | Mining/02 - Code/Ai bots/QuantumAlphaBot/main.py | QUANTUM_BOT_TOKEN, ANTHROPIC_API_KEY, CRYPTOQUANT_API, COINALYZE_API, LUNARCRUSH_API, BYBIT_API_KEY, OKX_API_KEY, GOPLUS_API_KEY, DISCORD_WEBHOOK | high/propose/tested |
| mining-sentinel | python | Mining/02 - Code/Ai bots/sentinel/main.py | SENTINEL_BOT_TOKEN, ANTHROPIC_API_KEY, LUNARCRUSH_API_KEY, CRYPTOQUANT_API_KEY, COLD_WALLET_* | medium/propose/tested |
| accounting | node | Accounting/1/bot.js | TELEGRAM_BOT_TOKEN | high/propose/untested |
| architect | python | 04/…/_code/…/langar/bot.py (در _code — محتوا را نخوان) | TELEGRAM_TOKEN, ANTHROPIC_API_KEY (تأییدِ مالک) | critical/propose/tested |

سند/ابزار (سرویس نیستند، ثبت نکن): Ziman Galerry، اونلی فنز، Crypto - etoro.

## معیارهای پذیرش
همهٔ سرویس‌ها در `projects.yaml` و همه `enabled:false`؛ هر رمز یک عنوانِ یکتا با اسناد هم‌خوان؛ هیچ تنظیمِ غیرمحرمانه‌ای در `secrets` نرفته؛ هیچ مقدارِ محرمانه‌ای در هیچ خروجی نیست؛ یک جدولِ جمع‌بندیِ سیاست + تنگ‌ترین محدودیتِ هر سرویس.

## چه‌کارهایی نکن
سرویس‌ها را روشن نکن، رمز عوض/تولید نکن، `.env`ِ واقعی نساز، به `_code`/secretها دست نزن، پروژه‌های سند/ابزار را ثبت نکن، چیزِ مبهم را حدس نزن (بپرس).

## استفادهٔ مرحله‌ای
اگر می‌خواهی گام‌به‌گام برود، تهش اضافه کن: «فعلاً فقط `painting` را کامل وصل کن، نشانم بده، بعد منتظرِ تأیید بمان.»

> وضعیت (۲۰۲۶-۰۷-۰۴): نقاشی به‌عنوان اولین سرویس بررسی و سازگار اعلام شد (با `pydantic-settings`، env بر فایل اولویت دارد → بدونِ تغییرِ کد سازگار). بقیه منتظرِ اجرای همین پرامپت.
