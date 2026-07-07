---
type: moc
project: "[[03 - Projects/Mining/PROJECT]]"
status: active
tags: [mining, index]
created: 2026-07-03
updated: 2026-07-04
---

# INDEX — فهرست کامل پوشه Mining

> ساختار جدید از ۲۰۲۶-۰۷-۰۳. هیچ فایلی حذف نشده؛ موارد زائد در `_archive/` هستند.

## فایل‌های ریشه (نوت‌های فعال Obsidian — جابجا نشدند)

| فایل | محتوا |
|---|---|
| `PROJECT.md` | شناسنامه پروژه: شکار کوین‌های نوظهور CPU/ARM با ناوگان Orange Pi 5 Pro + ESP32، معیار مرگ survival-based (D2) |
| `Mining.md` | لاگ تلگرام (۷۲ پیام، از ژانویه ۲۰۲۶) — بررسی Kryptex، تحلیل‌ها و تصمیمات روزانه |
| `Hardware Registry & Runbook.md` | رجیستری ناوگان (OPI-1 تا 6، ESP-1) + ران‌بوک عملیات از راه دور (Tailscale/SSH، kill-switch، قاعده برق $0.05/kWh) |
| `Coin Scouting Framework.md` | چارچوب انتخاب کوین: CPU/ARM-پذیر، لانچ <۳ ماه، معیار بقا + قالب لاگ آزمایش و Death-watch |
| `DecisionLog.md` | کیت مغز پروژه — تصمیم‌ها + دلیل (D2/D-10/D-20/قید برق) |
| `OpenQuestions.md` | کیت مغز پروژه — مجهول‌ها (نودها، بنچ H/s، profitability) |

## 01 - Docs — مستندات

### Strategy & Roadmap
| فایل | محتوا |
|---|---|
| `CORE PRINCIPLES.pdf` | اصول تغییرناپذیر سیستم (IMMUTABLE — فقط اپراتور انسانی ویرایش می‌کند) |
| `roadmap-v3-jame.pdf` | نقشه‌راه جامع v3 سیستم چندایجنتی آرمین (ژوئن ۲۰۲۶) — تصمیمات قفل‌شده |
| `CPU Mining Quantum Resistance Plan.pdf` | طرح استراتژیک v0.1 — سرمایه‌گذاری روی روایت کوین‌های مقاوم کوانتومی (مه ۲۰۲۶) |
| `CRITIQUE DEEP.pdf` | نقد عمیق استراتژی از ۴ عدسی: ریاضی کلاسیک، کوانتوم، اکولوژی، روان‌شناسی — ۷ نقص ساختاری |
| `SUMMARY.pdf` | خلاصه کل مسیر پروژه — سند مرجع اگر فقط یک فایل نگه داری |
| `handoff context.pdf` | سند انتقال کانتکست کامل به AI دیگر: پورتفولیو، عملیات ماینینگ، تحلیل بازار (۱۱ ژوئن ۲۰۲۶) |
| `data.txt` | خلاصه مکالمه ۱۶ مه ۲۰۲۶ — ۵ فاز طراحی ربات کوین‌یاب (Hetzner، hybrid LLM، $80-150/ماه) |

### Bot System
| فایل | محتوا |
|---|---|
| `README.pdf` | معماری و راهنمای استقرار Coin Hunter Bot — ایجنت چندلایه خودکار |
| `COWORK OPERATOR PROMPT.pdf` | پرامپت اپراتور Cowork — لایه PM انسانی (مکمل orchestrator_prompt_v2) |
| `tier2 forensics prompt.pdf` | پرامپت Tier 2: بازرس on-chain با LLM محلی (Qwen 2.5 14B) |

### Orange Pi Automation System - 20 Projects
معماری v1 (SelfAdaptive) و v2 (Hybrid Final) سیستم اتوماسیون ۲۰ پروژه‌ای.

## 02 - Code — کد و ابزار

| مورد | محتوا |
|---|---|
| `Ai bots/` | کدبیس اصلی ناوگان (۷۹ فایل py): `sentinel` (جمع‌آوری داده CryptoQuant/LunarCrush + تست‌ها + داده parquet)، `coordinator`، `fleet` (manager/watchdog/worker)، `QuantumAlphaBot` (داشبورد + ماژول‌ها)، `deploy` (systemd + esp32) |
| `Robo-data/` | نسل قبلی ربات‌ها: scout، tesseract v0.4 (DualTrack/PQC)، pqc_classifier، ربات sentinel اولیه + استراتژی‌ها (docx) و نوت‌های فارسی ایده‌ها |
| `cryptoquant-scraper.zip` | اسکریپر دیتاست CryptoQuant |
| `cryptoquant dump.pdf` | سورس‌کد cryptoquant_dump.py به‌صورت PDF |
| `.env.example` | قالب کلیدهای API (GitHub، CoinGecko، SoChain) |

## 03 - Rigs — ریگ‌های ماینینگ

| مورد | محتوا |
|---|---|
| `Mining-1/Hcash/` | اسکریپت‌های استقرار نود Hcash (hardening، fullnode، miner، monitor، autostart) + آرشیوهای files-v1..v3 |
| `Mining-1/Mining E` و `Mining Q/` | اسکرین‌شات‌ها و نوت‌ها (سکرت‌ها قبلاً خارج شده — فایل‌های `MOVED - *`) |
| `Mining-10- pro-plus/Verus coin/` | مانیتورینگ کلاسترهای Verus (`clusters_monitoring.py`) + وضعیت سه دستگاه |

## 04 - Research — پژوهش

`Quantum Physics Dataset/` (نام قبلی: «dataset Quantum physiscs») — ۷ مقاله/گزارش: نقشه‌راه فناوری کوانتومی CSIRO، گذار Quantum-Safe، اصول حاکمیت WEF، مقالات QAOA/quantum walks، دیتاست QDataSet برای ML، قوانین برنامه iPhD.

## 05 - Media — تصاویر

| پوشه | محتوا |
|---|---|
| `Pics/` | ۵۸ عکس (۲۷ فوریه ۲۰۲۶) + زیرپوشه خالی `s5` |
| `photos/` | ۵ عکس (۱۴ و ۲۷ ژانویه ۲۰۲۶) |

## _archive — موارد زائد (قابل حذف پس از بررسی)

| مورد | توضیح |
|---|---|
| `shortcuts/` | ۵ شورت‌کات ویندوز: START-MINING، Verus-Desktop، Fing، PowerISO، Ulead (اگر START-MINING را لازم داری، برگردانش به ریشه) |
| `PowerISO.exe` | فایل اجرایی نامرتبط (داخل پوشه دیتاست کوانتوم بود) |
| `desktop.ini` | فایل سیستمی ویندوز |
| `caches/` | کش‌های pytest از `Ai bots/sentinel` |
