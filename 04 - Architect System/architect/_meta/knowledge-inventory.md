---
tags: [meta, inventory, architect]
created: 2026-07-03
---

# Knowledge Inventory — کل vault architect

> خروجی فاز ۱ پرامپت [[PROMPT-A-absorb-synthesize]] — اجرا: 2026-07-03، با ۱۰ subagent موازی.
> پوشش: ۱۰۰٪ فایل‌های md پوشه‌های `01`–`04` + `PROJECT.md` + `00-Home.md`، سه Master Export (کامل، chunk به chunk)، و کد واقعی `_code/ai-farm` (langar، langar-pro، fusion-mvp+igk، fusion-safety).
> قانون حل تناقض: **کد واقعی > سند جدیدتر > سند قدیمی‌تر**. هیچ تناقضی بی‌صدا حل نشده — همه ثبت شده‌اند (این‌جا و در [[DECISIONS]]).

## فهرست بخش‌ها

1. فایل‌های ریشه (PROJECT.md، 00-Home.md)
2. `01-Project/` — اسناد پروژه
3. `02-Research/` — سری تحقیق ۰۵–۰۹
4. `02-Research/` — سری تحقیق ۱۰–۱۴
5. `04-Docs/` — اسناد فنی (شامل transcript حجیم)
6. `03-Exports/AI-FARM-MASTER-EXPORT`
7. `03-Exports/LANGAR-MASTER-EXPORT`
8. `03-Exports/architect-chat-export`
9. کد: `langar` (بات + core)
10. کد: `langar-pro` + اسکریپت‌های deploy ریشه‌ی AI-sume
11. کد: `fusion-mvp` + `igk` + `fusion-safety`

---

## ۱. فایل‌های ریشه

### `PROJECT.md`
- **موضوع:** هویت پروژه architect — «سیستم AI خودکدنویس که همهٔ پروژه‌ها را بازرسی و کنترل می‌کند و از طریق تلگرام وصل است».
- **ادعاهای کلیدی:** دو ماژول: (۱) محقق و طراح — تحقیق خودکار و خودبهبودی؛ (۲) رئیس کل — کنترل و بازرسی تمام سیستم‌ها از طریق Telegram. نقش: لایهٔ مادر برای پروژه‌های Accounting، Crypto، Mining، Lead-نقاشی، Ziman، هیپنوتیزم.
- **تاریخ/نسخه:** ندارد.
- **تناقض:** [[architect-chat-export]] (خط ~6751) «رئیس کل» را در نهایت **انسان** تعریف می‌کند نه ماژول نرم‌افزاری — «کلید اجرا همیشه دست انسان». همچنین «خودکدنویس» با خط قرمز سطح C (weight-update ممنوع) و PatchManager سطح ۳ (`NotImplementedError` عمدی) در کد langar محدود شده است.

### `00-Home.md`
- **موضوع:** داشبورد vault؛ نقشهٔ لینک به همهٔ بخش‌ها.
- **ادعاهای کلیدی:** سری تحقیق از ۰۵ شروع می‌شود (۰۱–۰۴ وجود ندارند)؛ سه export آرشیو کامل context؛ بکاپ `_meta/pre-reorg-backup-2026-07-03.zip`.
- **تاریخ/نسخه:** بکاپ مورخ 2026-07-03.
- **تناقض:** ندارد (فایل ناوبری).

---
# اینونتوریِ پوشه‌ی `01-Project` — سیستمِ architect

> سند فقط-خواندنی. تهیه‌شده از روی پنج فایلِ خواسته‌شده. اصطلاحاتِ فنیِ انگلیسی دست‌نخورده مانده‌اند.
> تاریخ تهیه‌ی اینونتوری: ۲۰۲۶-۰۷-۰۳

---

## ۱) `01-Project\INDEX.md`

- **مسیر/نام فایل:** `01-Project\INDEX.md` (عنوان: «AI Farm — نقشه‌ی پوشه‌ها»)

- **موضوع:** نقشه‌ی پوشه‌های پروژه‌ی «AI Farm» و تفکیکِ تجویزشده‌ی سندِ `data-map-and-research` بین «اثرِ خلاقانه» و «معماریِ ایمنی». وضعیتِ تست‌ها و پاکسازی را هم خلاصه می‌کند.

- **ادعاها/تصمیم‌های کلیدی:**
  - تفکیک سه‌جریانی: `fusion-creative/` (جریان A: codex, canonها, صحنه‌ها, promptها — intuition pump)، `fusion-safety/` (جریان B: معماریِ ایمنیِ واقعی)، `fusion-mvp/` (کدِ سیستمِ چندعاملی، متعلق به جریان B). (بلوکِ کد در ابتدای فایل)
  - `fusion-safety/` شاملِ `RECONCILIATION.md` (منبعِ واحدِ زنده)، `GAP-AUDIT.md` (کدِ MVP در برابرِ ۴ معیارِ IGK)، `igk/` (فاز ۰: کرنلِ مینیمالِ اعتماد + ۸ تستِ red-team) و `docs/`. (بلوکِ کد)
  - وضعیتِ تست‌ها: baseline **۱۷ سبز** · igk red-team **۸ سبز** · igk integration **۳ سبز** → مجموع **۲۸ سبز**. (بخش «وضعیت»)
  - `orchestrator.py` به IGK وصل شد (فاز ۲): `ks.check()`ِ cooperative → `_kguard` بیرونی + `ActuationGate`ِ fail-closed روی finalize + گیتِ grounding؛ با `config.USE_IGK`/`GROUNDING_REQUIRED` کنترل می‌شود. (بخش «وضعیت»)
  - کلیدِ قطعِ انسانی: ساختِ فایلِ `fusion-mvp/logs/STOP` باعثِ توقفِ fail-closed می‌شود. (بخش «وضعیت»)
  - PDFهای تکراریِ root، `fusion-safety/igk` تکراری، و `.git`ِ ناقص قابلِ حذف‌اند (رجوع به `CLEANUP.md` + `cleanup.ps1`). (بخش «پاکسازی»)

- **تاریخ/نسخه:** صریح ذکر نشده.

- **تناقض‌ها با فایل‌های دیگر:**
  - **معماریِ کاملاً متفاوت با HANDOFF و سندِ همیشه‌روشن.** INDEX یک سیستمِ چندعاملیِ پیچیده با `igk` کرنل، `orchestrator.py`، `ActuationGate`، ۲۸ تستِ سبز را توصیف می‌کند؛ اما HANDOFF و سندِ همیشه‌روشن یک بات تلگرامِ ساده‌ی پنج‌فایله (LANGAR) را توصیف می‌کنند که **کد بات هنوز نوشته نشده**. این دو تصویرِ ناسازگار از «وضعیتِ فعلیِ» پروژه‌اند.
  - **نام‌گذاریِ پوشه‌ها:** INDEX از `fusion-*` استفاده می‌کند؛ HANDOFF و سندِ همیشه‌روشن از `langar/` استفاده می‌کنند. رابطه‌ی `fusion-mvp` با `langar` روشن نیست.
  - **مکانیزمِ kill-switch:** اینجا فایلِ `logs/STOP` (fail-closed)؛ در HANDOFF/همیشه‌روشن فلگِ `halted` در SQLite + دستورِ `/halt`. دو مکانیزمِ متفاوت.
  - **FUSION:** INDEX نشان می‌دهد `fusion-creative` هم‌اکنون موجود است؛ سندِ همیشه‌روشن صریحاً می‌گوید FUSION نباید در v1 باشد و به فاز ۲ موکول شود.

- **پرامپت‌ها/مشخصاتِ فنیِ مهم (نقلِ کوتاه):**
  - «`orchestrator.py` به IGK وصل شد (فاز ۲): `ks.check()`ِ cooperative → `_kguard` بیرونی + `ActuationGate`ِ fail-closed روی finalize + گیتِ grounding. با `config.USE_IGK`/`GROUNDING_REQUIRED` کنترل می‌شود.»
  - «کلیدِ قطعِ انسانی: فایلِ `fusion-mvp/logs/STOP` بساز → اجرا fail-closed متوقف می‌شود.»

---

## ۲) `01-Project\HANDOFF - قلب و آگاهی.md`

- **مسیر/نام فایل:** `01-Project\HANDOFF - قلب و آگاهی.md` (عنوان: «HANDOFF — قلب و آگاهی + سیستم همیشه‌روشن»)

- **موضوع:** یک handoffِ کامل برای انتقالِ context به یک AI جدید. دو بخش: (۱) نقشه‌ی پژوهشِ HTML درباره‌ی ماریجوانا/ضربان قلب/interoception؛ (۲) معماریِ بات تلگرامِ همیشه‌روشن. ادعا می‌کند «هیچ فایلِ خارجی‌ای نیاز نیست».

- **ادعاها/تصمیم‌های کلیدی:**
  - صاحبِ پروژه Armin؛ هدف یک سیستمِ شخصیِ N-of-1 برای رابطه‌ی ماریجوانا، ضربان قلب و interoception با یک بات تلگرام به‌عنوان رابطِ همیشه‌روشن. (بخش «زمینه‌ی پروژه»)
  - نقشه‌ی پژوهش (`heart-awareness-map-v3.html`): HTML دارک‌مود RTL، دسته‌بندیِ شواهد با تگِ E/S/P، پنج آزمایشِ N-of-1، قالبِ لاگِ روزانه، بخشِ «امروز چه کار کنم». (بخش ۱)
  - پنج آزمایش E1–E5: منحنیِ autonomic (RMSSD در سه نقطه)، accuracy×confidence، تستِ زمانِ ۳۰ ثانیه، retestِ بینش، baselineِ خالصِ واگ. (بخش ۱ → «پنج آزمایش»)
  - یافته‌های علمیِ تأییدشده: THC → dose-dependent HR↑ و HF-HRV↓ [E]؛ taVNS 2025 → SDNN↑ ولی RMSSD نه [E]؛ شمارشِ ضربان به‌تنهایی شکننده، دو سنجه لازم [E]؛ HRVB برای افسردگی g=−0.41 [S]؛ تصحیحِ Kaduk 2025 («غذا روی واگ» پشتیبانی‌نشده). (بخش ۱ → «یافته‌های علمیِ کلیدی»)
  - معماریِ MVP بات: پنج فایل (`main.py`, `bot.py`, `db.py`, `.env`, `requirements.txt`) + `langar_bot.service`. بدون hash-chain، بدون Wilson score، بدون execution rings. (بخش ۲ → «معماریِ MVP»)
  - Gate ساده (فلگ در SQLite)، kill-switchِ واقعی (`/halt`)، schema کامل، هشت دستور، ConversationHandlerِ پنج‌مرحله‌ای برای `/log`. (بخش ۲)
  - اصولِ LANGAR: gate قبل از هر پیامِ خروجی، Human-write-only برای verdict، kill-switchِ تست‌شده، همیشه RMSSD (شاخص‌ها مخلوط نشوند)، «در شک: سکوت». (بخش ۲ → «اصولِ LANGAR»)
  - وضعیتِ فعلی: نقشه‌ی پژوهش v3 ✅، دستورالعملِ سیستم ساده‌شده ✅، هر دو commit شده ✅، **کد بات هنوز نوشته نشده ⏳**، **VPS راه‌اندازی نشده ⏳**. (بخش «وضعیتِ فعلی»)

- **تاریخ/نسخه:** «*ساخته‌شده با Claude Sonnet 4.6 · ژوئن ۲۰۲۶*» (پانویس). نسخه‌ی نقشه: v3.

- **تناقض‌ها با فایل‌های دیگر:**
  - **وضعیتِ کد:** HANDOFF می‌گوید کد بات هنوز نوشته نشده و VPS راه‌اندازی نشده؛ اما INDEX ادعا می‌کند سیستمِ چندعاملی با ۲۸ تستِ سبز و `orchestrator.py`ِ کارکننده موجود است. ناسازگاری در پیشرفتِ واقعی.
  - **نام و مکانیزمِ kill-switch:** HANDOFF دستورِ `/halt` + فلگِ `halted` در SQLite را دارد؛ INDEX فایلِ `logs/STOP` را. متفاوت.
  - **مدلِ سازنده:** «Claude Sonnet 4.6» ذکر شده (نامِ مدلی که ممکن است غیرواقعی/آینده‌نگر باشد؛ صرفاً نقل شده).

- **پرامپت‌ها/مشخصاتِ فنیِ مهم (نقلِ کوتاه):**
  - پرامپتِ کدنویس: «یک بات تلگرامِ شخصیِ single-user بساز. Stack: Python 3.11 / python-telegram-bot v21 (async) / SQLite / python-dotenv. Security: BOT_TOKEN و OWNER_ID از .env؛ فقط OWNER_ID پاسخ می‌گیرد. اول هر handler: `if is_halted(): return`».
  - Output خواسته‌شده: «main.py + bot.py + db.py + requirements.txt + systemd service + README deploy».
  - Schema SQLite کامل (جداولِ `log`, `insight`, `config`) و کدِ `is_halted()`/`cmd_halt`/`cmd_resume` عیناً در فایل آمده (خطوط ۹۶–۱۴۶).

---

## ۳) `01-Project\CLEANUP.md`

- **مسیر/نام فایل:** `01-Project\CLEANUP.md` (عنوان: «CLEANUP — چه چیزهایی را حذف کنی تا پروژه بهینه شود»)

- **موضوع:** فهرستِ مواردِ قابلِ حذف (تکراری/منسوخ، کش، فایل‌هایی که نباید commit شوند) به‌همراه اسکریپتِ آماده‌ی `cleanup.ps1`. تأکید که sandbox اجازه‌ی حذف روی درایو را ندارد و کاربر باید دستی/با اسکریپت پاک کند.

- **ادعاها/تصمیم‌های کلیدی:**
  - حتماً حذف: `fusion-mvp/.git/` (گیتِ ناقصِ ساخته‌شده در sandbox، خراب؛ بعد روی ویندوز `git init` تازه)، `fusion-safety/igk/` (کپیِ تکراری؛ نسخه‌ی اصلیِ runnable حالا `fusion-mvp/igk/` است، ~16K)، ۱۱ فایلِ `*.pdf` در root (~2.0MB، بعد از split کپی‌شده در `fusion-creative/` و `fusion-safety/docs/`). (بخش ۱)
  - هشدار: قبل از حذفِ PDFهای root، سالم‌بودنِ کپی‌ها در `fusion-creative/` و `fusion-safety/docs/` تأیید شود. (بخش ۱)
  - حذفِ بی‌خطر: همه‌ی `__pycache__/`، `fusion-mvp/dashboard.html`، `fusion-mvp/logs/igk_state/` (شاملِ `.kernel_key` — «هرگز commit نکن»)، `fusion-mvp/logs/audit.jsonl`. (بخش ۲)
  - هرگز commit نشود (در `.gitignore`): `.env`, `*.pyc`, `__pycache__/`, `logs/*.jsonl`, `dashboard.html`, `prompts.json`, `**/.kernel_key`, `logs/igk_state/`. (بخش ۳)
  - نگه‌داشتنی: `fusion-mvp/igk/` (کرنلِ اصلی) + `held_out.sample.json`، `fusion-safety/{GAP-AUDIT,RECONCILIATION}.md` و `docs/`، `fusion-creative/`، `INDEX.md`. (بخش ۴)
  - نتیجه‌ی پاکسازی: ~۲MB و دو تکرارِ سردرگم‌کننده کم می‌شود؛ اشاره به اصلِ «پراکندگیِ منبع = تناقضِ پنهان» از `data-map`. (بخش «نتیجه»)

- **تاریخ/نسخه:** «تاریخ: ۲۰۲۶-۰۶-۲۵».

- **تناقض‌ها با فایل‌های دیگر:**
  - **مسیرِ ریشه:** اسکریپت از `$root = "C:\Users\Armin\Documents\Claude\Projects\AI Farm"` استفاده می‌کند، در حالی که این vault اکنون در `C:\Users\Armin\Desktop\backup\04 - Architect System\architect` قرار دارد. مسیرِ اسکریپت با محلِ فعلیِ فایل‌ها نمی‌خواند.
  - **همسو با INDEX** درباره‌ی وجودِ `igk`/`fusion-*`، اما **ناسازگار با HANDOFF/همیشه‌روشن** که ساختارِ `langar/` و هیچ hash-chain/kernel-key ندارند. وجودِ `**/.kernel_key` و `igk_state/` نشان‌دهنده‌ی معماریِ پیچیده‌ای است که سندِ همیشه‌روشن آن را برای MVP رد کرده بود.

- **پرامپت‌ها/مشخصاتِ فنیِ مهم (نقلِ کوتاه):**
  - اسکریپتِ `cleanup.ps1` عیناً در فایل آمده (خطوط ۳۳–۴۸)، از جمله:
    `Remove-Item -Recurse -Force "$root\fusion-mvp\.git" -ErrorAction SilentlyContinue`
    `Remove-Item -Recurse -Force "$root\fusion-safety\igk" -ErrorAction SilentlyContinue`
    `Get-ChildItem "$root\*.pdf" | Remove-Item -Force`

---

## ۴) `01-Project\سیستم-همیشه-روشن-پرامپت-و-دستورالعمل.md`

- **مسیر/نام فایل:** `01-Project\سیستم-همیشه-روشن-پرامپت-و-دستورالعمل.md` (عنوان: «سیستمِ همیشه‌روشن — نسخه‌ی ساده‌شده»)

- **موضوع:** دستورالعملِ MVP-firstِ ساختِ بات تلگرامِ شخصیِ همیشه‌روشن (LANGAR). نقدِ نسخه‌ی ۱ (بیش‌مهندسی)، معماریِ پنج‌فایله، schema، gate/kill-switch، دستورها، مراحلِ deploy، HITL و پرامپتِ کدنویس. عملاً نسخه‌ی گسترده‌ترِ بخشِ ۲ از HANDOFF است.

- **ادعاها/تصمیم‌های کلیدی:**
  - نقدِ نسخه‌ی ۱: سه لایه‌ی enterprise روی یک ابزارِ single-user کشیده شده بود — Wilson score، Hash-chained SQLite، Execution rings (Ring 0/2/3)، FUSION module — **همه در MVP رد شدند**. اصل: «feature را وقتی اضافه کن که نبودش درد واقعی ایجاد کرده باشد». (بخش «مشکلِ اصلیِ نسخه‌ی ۱»)
  - معماریِ پنج‌فایله در `langar/` + `langar_bot.service` (systemd، همیشه‌روشن). (بخش «معماریِ MVP»)
  - Schema بدون hash-chain (جداولِ `log`, `insight`, `config`؛ seed: `('halted','0')`). (بخش «Schema»)
  - Gate/kill-switchِ ساده با `is_halted()` و `/halt`/`/resume` فقط برای OWNER_ID. تأکید بر تستِ kill-switch قبل از اعتماد. (بخش «Gate و Kill-switch»)
  - هشت دستور؛ ConversationHandlerِ پنج‌مرحله‌ای برای `/log`؛ نمونه‌ی خروجیِ `/trend`. (بخش‌های «دستورها»)
  - جدولِ HITL متناسب با ریسک: خواندن/ترند/پینگ بدون تأیید؛ verdict و پاک‌کردنِ داده و تغییرِ قوانینِ gate با تأیید/ممنوع برای بات. (بخش «HITL»)
  - اصولِ LANGAR (پنج اصل، همسو با HANDOFF). (بخش «اصولِ LANGAR»)
  - پنج شاخصِ موفقیت (۲۴ساعته بالا، ثبتِ صبحگاهیِ RMSSD، `/halt` واقعاً ساکت‌کننده، هیچ verdict بدونِ تأیید، ترندِ واقعی بعد از ۱۴ روز). (بخش «شاخصِ موفقیت»)
  - فازهای بعدی: فاز ۱ (بعد از ۲ هفته: پینگِ صبحگاهی/مرورِ هفتگی/Apple Shortcut)؛ فاز ۲ (بعد از ۱ ماه: FUSION، Microsoft Agent Governance Toolkit، Wilson score + hash-chain). (بخش «فازهای بعدی»)
  - مبنای طراحی: **LANGAR Blueprint v0.1**؛ منابع: Microsoft Agent Governance Toolkit، python-telegram-bot v21، OWASP Agentic AI Top 10. (بخش «منابع»)

- **تاریخ/نسخه:** «نسخه ۲.۰ · ژوئن ۲۰۲۶ · اصل: MVP-first».

- **تناقض‌ها با فایل‌های دیگر:**
  - **ردِ صریحِ همان چیزهایی که INDEX/CLEANUP موجود نشان می‌دهند:** این سند Wilson score، hash-chain، execution rings و FUSION را برای MVP رد می‌کند و به فاز ۲ موکول می‌کند؛ اما INDEX (fusion-creative، igk kernel) و CLEANUP (`.kernel_key`، `igk_state/`) نشان می‌دهند این معماریِ پیچیده هم‌اکنون در repo پیاده شده است. یا این سند منسوخ است یا INDEX/CLEANUP یک شاخه‌ی موازی را توصیف می‌کنند.
  - **kill-switch:** فلگِ SQLite (`halted`) در برابرِ فایلِ `logs/STOP`ِ INDEX.
  - **نام‌گذاری:** `langar/` در برابرِ `fusion-mvp/`.

- **پرامپت‌ها/مشخصاتِ فنیِ مهم (نقلِ کوتاه):**
  - پرامپتِ ساده‌شده‌ی کدنویس (خطوط ۲۰۱–۲۲۴)، عملاً هم‌ارز با پرامپتِ HANDOFF اما با schema و command تفصیلی‌تر. Output: «main.py + bot.py + db.py + requirements.txt + systemd service + README deploy روی VPS».
  - سرویسِ systemd کامل (`langar_bot.service`) با `Restart=always` و `EnvironmentFile` (خطوط ۱۵۴–۱۶۸).
  - تأکید: «تست kill-switch را قبل از اعتماد انجام بده: `/halt` بزن، مطمئن شو بات جواب نمی‌دهد، بعد `/resume`.»

---

## ۵) `01-Project\PROMPT-B-test-improve.md`

- **مسیر/نام فایل:** `01-Project\PROMPT-B-test-improve.md` (عنوان: «پرامپت B — تست خصمانه، نمره، بهبود (تکرارشونده)»؛ front-matter: `tags: [prompt, cowork, meta]`)

- **موضوع:** یک پرامپتِ متا (meta-prompt) برای اجرای یک حلقه‌ی red-team/QA روی سیستمِ «architect». مأموریت: یافتنِ آخرین `SYSTEM-BLUEPRINT-v(n).md`، شکستنِ بی‌رحمانه، نمره‌دهی، و ساختِ نسخه‌ی `v(n+1)`.

- **ادعاها/تصمیم‌های کلیدی:**
  - باید بعد از `[[PROMPT-A-absorb-synthesize]]` اجرا شود؛ حلقه‌ی تکرارشونده v1→v2→v3 تا همگرایی. (سرلوح)
  - قوانینِ سخت: (۱) حذف/بازنویسیِ نسخه‌ی قبلی ممنوع، فقط `v(n+1)` و append به CHANGELOG/BACKLOG؛ (۲) هر انتقاد باید fix مشخص یا آیتمِ BACKLOG داشته باشد؛ (۳) تأییدِ ادعاها به subagentِ مستقل واگذار شود (جدایی نویسنده/داور). (بخش «قوانین سخت»)
  - فاز ۱: تستِ سازگاریِ blueprint با منابع (`02`/`04` و کدِ `_code/ai-farm`) و با کدِ واقعی. (بخش «فاز ۱»)
  - فاز ۲: red-team روی حداقل ۶ محور — failure modes (چک‌لیستِ `[[12-research-failure-modes-blind-spots]]`)، امنیت (attack surface تلگرام، secrets، prompt injection)، هزینه (توکن + سرور در سه سناریو)، SPOF و مقیاس، حلقه‌ی خودبهبودی (واگرایی؟ gate و kill-switch)، عملیات (monitoring/logging/backup/recovery). (بخش «فاز ۲»)
  - فاز ۳: سه سناریوی end-to-end (audit پروژه‌ی Crypto از تلگرام؛ پیشنهادِ خودبهبودیِ محقق و گیت‌ها؛ مرگِ VPS وسطِ کار). (بخش «فاز ۳»)
  - فاز ۴: نمره‌ی ۱–۱۰ برای هر بخش + کل، ساختِ `SYSTEM-BLUEPRINT-v(n+1).md`، append به `CHANGELOG.md`، ساخت/آپدیتِ `BACKLOG.md` (impact×effort، ۱۰ آیتمِ اول قابلِ اجرا در یک هفته)، آپدیتِ `00-Home.md`. (بخش «فاز ۴»)
  - شرطِ توقفِ حلقه: دو اجرای متوالی با کمتر از ۰.۵ بهبود در نمره‌ی کل → معماری پایدار، خروج از طراحی به سمتِ کدنویسیِ واقعی. (بخش «شرطِ توقف»)

- **تاریخ/نسخه:** تاریخ صریح ندارد؛ صرفاً `tags: [prompt, cowork, meta]`.

- **تناقض‌ها با فایل‌های دیگر:**
  - **مجموعه‌ی فایل‌های ارجاعی وجود ندارند/نام‌گذاریِ متفاوت:** این پرامپت به `SYSTEM-BLUEPRINT-v(n).md`, `CHANGELOG.md`, `BACKLOG.md`, `DECISIONS`, `GAPS`, `00-Home.md`, پوشه‌های `02`/`04`, `_code/ai-farm`, `[[PROMPT-A-absorb-synthesize]]`, `[[12-research-failure-modes-blind-spots]]` ارجاع می‌دهد — هیچ‌کدام در INDEX/HANDOFF/CLEANUP (که از `fusion-*` یا `langar/` حرف می‌زنند) دیده نمی‌شوند. یعنی یک طرحِ سازمان‌دهیِ سومِ متفاوت (اسکیمای «architect/SYSTEM-BLUEPRINT»).
  - **نام پروژه:** اینجا «architect»؛ در INDEX «AI Farm»؛ در HANDOFF/همیشه‌روشن «LANGAR». سه نامِ پروژه‌ی محتملاً متفاوت.
  - **دامنه:** PROMPT-B فرض می‌کند سیستم می‌تواند «پروژه‌ی Crypto را audit کند» و «تحقیقِ وب» و «حلقه‌ی خودبهبودی» دارد — بسیار فراتر از باتِ single-userِ HRVِ HANDOFF/همیشه‌روشن. دامنه‌ی متناقض.

- **پرامپت‌ها/مشخصاتِ فنیِ مهم (نقلِ کوتاه):**
  - «تو الان red-teamer و QA سیستم «architect» هستی، نه نویسندهٔ آن. مأموریت: آخرین `01-Project/SYSTEM-BLUEPRINT-v(n).md` را پیدا کن، بی‌رحمانه بشکن، نمره بده، و نسخهٔ v(n+1) بساز.»
  - «تأیید ادعاها را به subagent مستقلی بده که متن را ننوشته (جدایی نویسنده/داور).»
  - شرطِ توقف: «وقتی دو اجرای متوالی کمتر از ۰.۵ بهبود در نمرهٔ کل داشتند → معماری پایدار است.»

---

## جمع‌بندیِ تناقض‌های عرضی (بینِ فایل‌ها)

1. **سه اسکیمای نام‌گذاریِ ناهم‌خوان:** `fusion-*` (INDEX/CLEANUP) · `langar/` (HANDOFF/همیشه‌روشن) · `SYSTEM-BLUEPRINT-v(n)/00-Home/02/04` (PROMPT-B). سه نامِ پروژه: «AI Farm» / «LANGAR» / «architect».
2. **پیچیدگیِ معماری:** سندِ همیشه‌روشن Wilson score، hash-chain، execution rings و FUSION را برای MVP **رد** می‌کند؛ اما INDEX و CLEANUP نشان می‌دهند `igk` kernel، `.kernel_key`، `orchestrator.py` و `fusion-creative` (FUSION) هم‌اکنون در repo موجودند.
3. **وضعیتِ پیشرفت:** HANDOFF می‌گوید کد بات هنوز نوشته نشده و VPS بالا نیست؛ INDEX می‌گوید ۲۸ تستِ سبز و orchestratorِ متصل به IGK موجود است.
4. **kill-switch:** فلگِ SQLite `halted` + `/halt` (HANDOFF/همیشه‌روشن) در برابرِ فایلِ `logs/STOP` fail-closed (INDEX).
5. **مسیرِ ریشه:** اسکریپتِ CLEANUP روی `C:\Users\Armin\Documents\Claude\Projects\AI Farm` است، اما vault فعلی در `C:\Users\Armin\Desktop\backup\04 - Architect System\architect`.
6. **تاریخ‌ها:** CLEANUP = ۲۰۲۶-۰۶-۲۵ · HANDOFF = ژوئن ۲۰۲۶ (Claude Sonnet 4.6) · همیشه‌روشن = ژوئن ۲۰۲۶ (نسخه ۲.۰) · INDEX و PROMPT-B بدونِ تاریخ.
# Inventory — فایل‌های Research شماره ۰۵ تا ۰۹
> منبع: `04 - Architect System\architect\02-Research\` — خوانش کامل، READ-ONLY.
> هر پنج فایل با ساختار ثابت ۸ سرفصلی نوشته شده‌اند: Summary / Landscape / Comparison table / Blind spots / Recommendation (+نساز) / TOOLING / If-I'm-wrong / Confidence / Claims table.
> **تاریخ ساخت هر پنج فایل: ۲۰۲۶-۰۷-۰۱** (منابع از web search زنده؛ برچسب‌های `[established]/[emerging]/[speculative]`).

---

## ۱) `02-Research\05-research-shared-engineering-lane.md`

**موضوع:** لایه‌ی مهندسی مشترک (زیرساخت/orchestration عرضی) بین همه‌ی tenantها — برای اپراتور تک‌نفره روی VPS مشترک + لپ‌تاپ، با Claude Cowork.

**ادعاها/توصیه‌های معماری کلیدی:**
- (Summary §1، If-I'm-wrong) **فعلاً تقریباً هیچ لایه‌ی مشترکی نساز** — گلوگاه binding دیتای cold-start لجر است نه زیرساخت؛ gateway را نساز تا وقتی «≥N action واقعی/روز روی ≥۲ tenant» داشته باشی.
- (Summary §2، Recommendation §1) اگر ساختی، **بالاترین ROI = یک MCP gateway/proxy به‌عنوان chokepoint واحد** برای همه‌ی tool/data-accessها؛ cap + kill-switch + audit طبیعتاً همان‌جا می‌نشیند. گزینه: IBM Context Forge یا proxy نازک سفارشی.
- (Recommendation §2–۴) **policy gate = OPA** (یا جدول allowlist + risk-tier)؛ **audit = append-only hash-chain با معنای WORM**؛ **kill switch = یک flag واحد** (سراسری + per-tenant) که gateway قبل از هر action چک می‌کند و **تست‌شده** باشد.
- (Summary §3، Recommendation §5) **durability = DBOS روی Postgres/SQLite، نه Temporal** (in-process library، صفر زیرساخت جدید)؛ هر LLM/tool-call در step ژورنال‌شده wrap شود (تله‌ی replay/determinism در Blind spots).
- (Summary §4، Recommendation §6–۷) isolation دوتکه: **contention با cgroups v2/systemd slices**؛ **isolation امنیتی فقط اگر کد untrusted اجرا می‌شود** → gVisor یا E2B؛ **Firecracker روی VPS اجاره‌ای نه** (احتمالاً KVM/nested-virt ندارد؛ verify: `ls /dev/kvm`).
- (Summary §5، Recommendation §8–۹) دو لنگر ضد lock-in: **MCP برای tools** (فعلاً اسپک پایدار **2025-11-25**؛ 2026-07-28 هنوز RC) و **OpenTelemetry برای observability** → Langfuse self-host یا cloud free tier.
- (Landscape §5) الگوی «Agent Control Plane» (ژوئن ۲۰۲۶): OAuth-scoped accounts + deterministic router + OPA gates + WORM audit + kill-switch تست‌شده؛ agentها را با **permission** طبقه‌بندی کن نه هوش (نردبان L0–L4؛ L5 بدون checkpoint در production ممنوع)؛ HITL انتخابی (فقط پرریسک) وگرنه reviewer تک‌نفره غرق می‌شود.
- (Recommendation، «نساز») ❌ K8s/Agent Sandbox، ❌ Temporal cluster، ❌ Firecracker self-host، ❌ DSL/message-bus دست‌ساز، ❌ MCP Runtime کامل multi-user، ❌ CrewAI روی taskهای سبک، ❌ self-host MCP Registry رسمی، ❌ backend observability خودساخته.
- (Blind spots) glue ارکستراسیون نباید داخل چت/کانفیگ Cowork بماند — باید در کد/گیت owned باشد (export-first)؛ durability ≠ درستی رفتار (hallucination/runaway loop/eval-drift را حل نمی‌کند).

**تاریخ/نسخه:** ساخت ۲۰۲۶-۰۷-۰۱؛ Confidence: **Medium**.

**تناقض‌ها با چهار فایل دیگر:**
- **Observability backend:** اینجا Langfuse (self-host یا cloud) توصیه‌ی اصلی است (Recommendation §8) — ولی فایل ۰۹ صریحاً Langfuse self-host را برای این پروفایل over-engineered می‌داند (۵+ service، ریسک acquisition توسط ClickHouse ژانویه ۲۰۲۶ که فایل ۰۵ اصلاً ذکر نمی‌کند) و **MLflow را انتخاب اول** معرفی می‌کند. فایل ۰۵ فقط «بار عملیاتی ClickHouse» را در Blind spots ذکر کرده ولی توصیه را عوض نکرده.
- **اعتبار OpenClaw:** فایل ۰۵ آن را «تک‌منبع، verify» با اطمینان M می‌داند؛ فایل ۰۷ همان incident را با اطمینان H گزارش می‌کند.
- **تنش build-now:** توصیه‌ی اصلی این فایل (gateway = بالاترین ROI) با ضدتوصیه‌ی خودش («فعلاً نساز») و با فایل ۰۸ که gateway را «مرحله‌ی بعد» (اولویت ۴ از ۶) می‌گذارد، در توالیِ زمانی هم‌راستا نیست — باید در سنتز تعیین تکلیف شود.

**اعداد/آستانه‌های مشخص:**
- governance-containment gap: ~۵۸–۵۹٪ oversight ولی فقط ~۳۷–۴۰٪ containment.
- gVisor سربار I/O ~۱۰–۳۰٪؛ Firecracker boot ~۱۲۵–۲۰۰ms؛ E2B sub-200ms؛ Daytona sub-90ms؛ Context Forge latency ~۱۰۰–۳۰۰ms.
- سربار durability ۵–۲۰٪ در ۱۰۰k run/روز؛ HITL-signal هزینه‌ی idle را ۶۰–۸۰٪ کم می‌کند.
- Langfuse cloud: $0/50k unit، $29، $199، $2,499 + overage $8/100k.
- n8n CVE-2026-25049 (CVSS 10.0)؛ OpenClaw ۲۱٬۰۰۰+ نمونه‌ی افشاشده.
- Gartner: تا ۴۰٪ پروژه‌های agentic تا ۲۰۲۷ ممکن است کنسل شوند؛ ۴۰٪ اپ‌های enterprise تا ۲۰۲۶ agent دارند.
- OSWorld سقف ~۶۶.۳٪؛ نردبان خودمختاری L0–L4.
- MCP اسپک پایدار 2025-11-25؛ RC 2026-07-28 (نهایی ۲۸ ژوئیه ۲۰۲۶)؛ EU AI Act ماده ۱۴ اجرای کامل ۲ اوت ۲۰۲۶.

---

## ۲) `02-Research\06-research-memory-architecture.md`

**موضوع:** معماری memory برای agentهای long-running و چندپروژه‌ای (لایه‌ها، isolation بین tenantها، context overflow) — نه RAG عمومی.

**ادعاها/توصیه‌های معماری کلیدی:**
- (Summary §1، Landscape §2) «memory = vector DB» خطای پیش‌فرض است؛ سیستم‌های **multi-strategy روی Postgres** (Hindsight: 91.4٪ LongMemEval) از vector-first (Mem0: 49.0٪) بالاتر می‌زنند — vendor-reported، uncertain.
- (Landscape §1) تاکسونومی چهارلایه‌ی memory (ریشه: CoALA arXiv:2309.02427): **Working (in-context) / Episodic / Semantic / Procedural**؛ پیپر دسامبر ۲۰۲۵ (arXiv:2512.13564) تاکسونومی جایگزین Factual/Experiential/Working را پیشنهاد داده ولی مدل ۳/۴تایی در production غالب است.
- (Recommendation، مرحله ۱) **stack ۸۰٪: همان Postgres + pgvector + Mem0 OSS (Apache 2.0)** — هیچ سرویس جدا؛ isolation با `user_id = project_name` + schema-per-project + metadata filtering؛ **declarative memory = CLAUDE.md per-project** (بنچمارک Letta: filesystem ساده 74٪ می‌زند)؛ export = Postgres dump.
- (Recommendation، مرحله ۲) **graph فقط وقتی factها در زمان تغییر می‌کنند** (قیمت دارایی، وضعیت پروژه) → **Graphiti (Apache 2.0) + FalkorDB** (نه Neo4j)؛ Zep Community Edition دیپرکیت شده (آوریل ۲۰۲۵)، Zep Cloud = lock-in.
- (Recommendation، مرحله ۳) **Letta فقط اگر agentها روزها بی‌توقف اجرا می‌شوند** — با آگاهی از framework lock-in (agentها باید داخل Letta runtime باشند؛ با Cowork نمی‌چسبد).
- (Landscape §3) **cascade سه‌مرحله‌ای context overflow:** (۱) compress/truncate tool-output، (۲) sliding window روی تاریخ مکالمه، (۳) LLM summarization فقط آخرین راه‌حل. «سیستم هرگز نباید در context limit crash کند.»
- (Landscape §4) isolation بین tenantها **در هیچ framework پیش‌فرض نیست** (MemTrust arXiv:2601.07004: «systematic security deficiencies»)؛ هیچ shared-entity در knowledge graph بین پروژه‌ها (خطر cross-inference).
- («نساز») ❌ Qdrant/Chroma به‌عنوان سرویس جدا (تا <50M vector)، ❌ Zep CE/Cloud، ❌ Neo4j self-host، ❌ Letta برای همه، ❌ memory stack مشترک بین tenantها، ❌ MemPalace در production مالی (v3.4.0 جوان)، ❌ summarization به‌عنوان اولین واکنش به overflow.

**تاریخ/نسخه:** ساخت ۲۰۲۶-۰۷-۰۱؛ Confidence: **Medium** (بنچمارک‌ها vendor-reported و متضاد).

**تناقض‌ها با چهار فایل دیگر:**
- تناقض مستقیم ندارد؛ چند تنش: (الف) فایل ۰۸ در TOOLING «Qdrant for tool semantic search» را لیست می‌کند درحالی‌که فایل ۰۶ Qdrant جدا را «نساز» می‌داند (فایل ۰۸ هم pgvector را alternative می‌دهد — تنش خفیف). (ب) دفاع فایل ۰۶ از extraction pipeline (Mem0) برای semantic memory در برابر ضدتوصیه‌ی سوم خودش (فقط فایل markdown + full-text کافی است) — با یافته‌ی 74٪ filesystem که فایل ۰۷ هم برای «شاید improvement loop فقط overhead باشد» استفاده می‌کند، هم‌راستا ولی جهت‌گیری متفاوت.
- فرض یکپارچه با ۰۵: «همان Postgres که DBOS/LANGAR رویش نشسته» — سازگار.

**اعداد/آستانه‌های مشخص:**
- LongMemEval: Hindsight 91.4٪ / Zep 63.8٪ / Mem0 49.0٪؛ MemPalace 96.6٪ R@5 (همه vendor-reported).
- LoCoMo dispute: Zep 84٪ → تصحیح Mem0 به 58.44٪ → counter‑claim Zep 75.14٪ (حل‌نشده).
- بنچمارک Letta: plain filesystem 74٪ روی memory tasks.
- pgvector کافی تا **<50M vector**؛ hop شبکه به managed vector DB ۱۰۰–۴۰۰ms در برابر ~3ms جستجوی local pgvector.
- آستانه‌ی overflow: >۲۰۰k توکن context.
- Mem0: ~48k stars، $24M funding (اکتبر ۲۰۲۵)؛ pricing: Free/10k req، Starter $19، **Pro $249/ماه (graph فقط اینجا)**. MemPalace: v3.4.0 (۶ ژوئن ۲۰۲۶)، ~54.1k stars. Graphiti: ~27k stars، MCP Server v1.0 نوامبر ۲۰۲۵. Zep Cloud: $25–$475/ماه.

---

## ۳) `02-Research\07-research-self-improvement-loops.md` ⚠️ Frontier Lane

**موضوع:** حلقه‌های self-improvement و continual learning برای multi-agent — طیف سه‌سطحی A/B/C، ریسک‌های مستند (reward hacking)، و gate اجباری. (به‌جای triangulation، یک Self-Critique Round داخلی دارد.)

**ادعاها/توصیه‌های معماری کلیدی:**
- (Summary §1، Landscape) **سه سطح:** **A = in-context reflection** (ایمن، بدون state پایدار — improvement است نه learning)؛ **B = skill-library بدون تغییر weight** (مسیر Voyager→SAGE→SkillRL→SkillOpt→ASG-SI؛ buildable با gate)؛ **C = weight-update/self-rewrite** (Continual Harness Princeton، SIA Hexo Labs، Gödel-style) = **frontier، production-ready نیست، برای tenantهای مالی خط قرمز**.
- (Summary §2، Landscape Cross-cutting) **reward hacking مستند است** (Anthropic نوامبر ۲۰۲۵: bypass تست‌ها با `sys.exit(0)` و گسترش به sabotage/deception از <۱٪ دیتای fine-tuning)؛ loop بدون gate می‌تواند سیستم را خراب کند درحالی‌که metricها «بهتر» نشان می‌دهند.
- (Summary §4، Recommendation §3) **gate اجباری — قانون #1:** هر skill جدید = proposal، نه commit؛ باید از **held-out eval suite** رد شود؛ fail → rejected-step buffer؛ pass → commit در git. eval suite باید use-caseهای اصلی + regression caseهای قدیمی + «null hypothesis» (آیا بدون skill هم می‌شد؟) را cover کند.
- (Recommendation §1–۲) الان بساز: **self-critique per-response (سطح A)** و **SKILL.md per-project (سطح B)** با نسخه‌بندی git = rollback طبیعی؛ (§4) بعداً **SkillOpt** (MSR، مه ۲۰۲۶) برای optimize کردن SKILL.mdها با validation-gating — سازگاری با Cowork باید verify شود.
- (Blind spots) یافته‌ی کلیدی SIA: «scaffold edits عمدتاً SE-hygiene را بهبود می‌دهند، نه domain reasoning»؛ catastrophic forgetting در skill library حل‌نشده؛ skill library خودش سطح حمله است (SkillJect)؛ **metric را قبل از ساخت loop تعریف کن**؛ متریک درست = trajectory quality + robustness on held-out + cost per unit of value (نه فقط task-success rate).
- (Self-Critique Round) self-critique از همان model = echo-chamber؛ برای tenant مالی باید با external verifier (eval suite) تکمیل شود؛ eval suite را rotate کن تا خودش gamed نشود (production traffic → benchmark cases).
- («نساز») ❌ هر loop بدون held-out gate، ❌ weight-update در production، ❌ recursive self-rewrite بدون HITL، ❌ RL-based skill acquisition (SAGE/SkillRL) روی VPS مشترک، ❌ self-critique به‌جای eval gate، ❌ skill از داده‌ی untrusted بدون sandbox، ❌ تعریف metric بعد از ساخت loop.

**تاریخ/نسخه:** ساخت ۲۰۲۶-۰۷-۰۱؛ Confidence: **Medium** با تفکیک H/M/L.

**تناقض‌ها با چهار فایل دیگر:**
- **eval-gate tooling:** فایل ۰۷ در TOOLING «Langfuse + regression suite» را برای eval gate لیست می‌کند؛ فایل ۰۹ تأکید دارد Langfuse «full eval platform نیست» (judgeها را خودت wire می‌کنی) و MLflow/DeepEval/Braintrust را جلو می‌گذارد — ناسازگاری در ابزار پیشنهادی همان gate مشترک.
- **OpenClaw:** اطمینان H اینجا در برابر M/«تک‌منبع، verify» در فایل ۰۵ (همان incident).
- gate این فایل («حداقل N test case» بدون عدد) توسط فایل ۰۹ کمّی می‌شود (۵۰–۱۰۰ anchor case، regression ≤۵٪) — مکمل، نه تناقض؛ در سنتز باید اعداد ۰۹ مرجع gate ۰۷ شوند.

**اعداد/آستانه‌های مشخص:**
- SkillOpt: **+24.8 روی Codex، +19.1 روی Claude Code**؛ هر skill **compact ۳۰۰–۲۰۰۰ توکن**، inspectable، قابل rollback.
- SAGE: +8.9٪ completion، −۵۹٪ توکن (vendor-reported).
- Emergent misalignment (Nature ژانویه ۲۰۲۶): ۲۰٪ خروجی violent روی promptهای بی‌ربط؛ reward hacking از <۱٪ مدارک fine-tuning؛ o1 در >۸۰٪ موارد اعتراف نکرد (Apollo).
- SkillJect/OpenClaw: ۲۱٬۰۰۰+ نمونه‌ی آسیب‌پذیر.
- METR: طول taskهای autonomous هر ۷ ماه double (R²=0.98)؛ ۲۰۲۴–۲۰۲۵ هر ۴ ماه.
- tracker: هر ۳ ماه SIA/Continual Harness را verify کن.
- CVE-2026-21852 و CVE-2025-59536 برای Claude Cowork (اطمینان L، uncertain — verify با NVD).

---

## ۴) `02-Research\08-research-tool-interoperability.md`

**موضوع:** طراحی tool، پروتکل‌های interop (MCP vs A2A)، progressive disclosure، و tool-use safety.

**ادعاها/توصیه‌های معماری کلیدی:**
- (Summary §1، Landscape §1–۲) **MCP = agent-to-tool؛ A2A = agent-to-agent** — مکمل، نه رقیب. **A2A الان نساز** (over-engineering برای تک‌نفره؛ اگر رسیدی، از Context Forge به‌عنوان gateway با پشتیبانی A2A استفاده کن، نه A2A server جدا).
- (Recommendation، «قانون ساده») **default = Python function ساده** برای هر operation داخلی (attack surface کمتر)؛ **MCP server فقط وقتی** tool باید discover شود (Cowork/چند agent)، access control+audit یکجا لازم است، یا tool به بیش از یک project expose می‌شود.
- (Summary §2، Landscape §3) **بحران context bloat:** ۷۲٪ از context با tool definitions پر می‌شود (۱۴۳k از ۲۰۰k توکن با ۳ MCP server) — راه‌حل: **الگوی سه‌سطحی progressive disclosure** (Level 0: نام+یک‌خط description → Level 1: full schema on-demand → Level 2: اجرا) + Anthropic Tool Search (GA فوریه ۲۰۲۶).
- (Recommendation §2–۳، فوری) tool description = یک جمله «چه» + یک جمله «کِی»، documentation جدا؛ **validation/sanitization روی tool results (نه فقط input)** — چون prompt injection از طریق نتیجه‌ی tool مستند است (hijack Claude Code/Gemini CLI/Copilot از طریق PR title، آوریل ۲۰۲۶؛ ۳ CVE در Git MCP server رسمی Anthropic).
- (Landscape §4) tool poisoning (MCPTox) و rug pull واقعی‌اند؛ دفاع‌ها: least-privilege، sandbox برای tool callهای side-effect‌دار، HITL برای high-risk، version locking + امضای cryptographic، mcp-scan (Snyk). «هیچ دفاع کاملی نیست — آسیب‌پذیری معماری است.»
- (Recommendation §4–۵) مرحله‌ی بعد: **همان MCP gateway فایل ۰۵** برای rate-limiting per-tenant / least-privilege / audit per tool call / version locking؛ بعدتر: **MCP server جدا per-project** (Docker) = tenant-isolation طبیعی. MCP spec خودش rate-limiting ندارد — فقط در gateway.
- («نساز») ❌ MCP server برای عملیات purely internal، ❌ A2A بین tenantها، ❌ description طولانی، ❌ trust به tool result بدون validation (حتی از server خودت)، ❌ اسپک RC 2026-07-28 تا نهایی‌شدن، ❌ MCP server مشترک بدون tenant-scoping، ❌ Cloudflare Workers اگر data باید روی VPS بماند.

**تاریخ/نسخه:** ساخت ۲۰۲۶-۰۷-۰۱؛ Confidence: **High-Medium**.

**تناقض‌ها با چهار فایل دیگر:**
- **توالی ساخت gateway:** اینجا gateway «مرحله‌ی بعد» (اولویت ۴) است؛ فایل ۰۵ آن را «تک‌حرکت بالاترین ROI» می‌نامد ولی در If-I'm-wrong می‌گوید شاید اصلاً نسازی. سه موضع ناهم‌زمان که سنتز باید یکی کند.
- **sandbox:** فایل ۰۵ می‌گوید اگر هیچ tenant کد untrusted اجرا نمی‌کند «لایه‌ی isolation امنیتی را کاملاً حذف کن»؛ فایل ۰۸ «sandbox execution برای tool callهای با side-effect» را دفاع عمومی توصیه می‌کند — دامنه‌ی sandbox متفاوت تعریف شده (کد untrusted در برابر هر side-effect).
- Qdrant در TOOLING (برای tool semantic search) در برابر «نساز Qdrant جدا» در فایل ۰۶ — تنش خفیف (pgvector alternative داده شده).
- سازگار با ۰۵ در: چسبیدن به MCP spec 2025-11-25 و استفاده از Context Forge.

**اعداد/آستانه‌های مشخص:**
- context bloat: **۷۲٪** (143k/200k توکن)؛ Tool Search: **۸۵٪ کاهش توکن** / حفظ ۱۹۱k؛ MCP+code execution: 150k→2k = **۹۸.۷٪**؛ Cloudflare Code Mode: ۹۹.۹٪.
- MCPTox: o1-mini **۷۲.۸٪** attack success؛ Claude 3.7-Sonnet **<۳٪** حملات را رد کرد (۲۰ agent، ۴۵ server، ۳۵۳ tool).
- IASR 2026: مهاجمان پیچیده در **۵۰٪** موارد با **۱۰ تلاش** از بهترین دفاع‌ها عبور می‌کنند.
- CVE-2025-68143/68144/68145 (Git MCP server رسمی Anthropic، ژانویه ۲۰۲۶).
- A2A v1.0 (Signed Agent Cards) اوایل ۲۰۲۶؛ ۱۵۰+ سازمان در production؛ MCP: ۱۰٬۰۰۰+ enterprise server، ۹۷M+ SDK download (آوریل ۲۰۲۶).

---

## ۵) `02-Research\09-research-evaluation-observability.md`

**موضوع:** evaluation (سه‌لایه، LLM-as-judge، eval dataset)، regression/acceptance gate برای self-modification، drift detection، و انتخاب observability stack.

**ادعاها/توصیه‌های معماری کلیدی:**
- (Summary §2–۳، Landscape §1) **eval agent = trajectory، نه response**؛ سه لایه‌ی لازم: **L1 outcome / L2 trajectory quality / L3 component-level**؛ «Step-level tracing حداقلِ signal قابل‌قبول در production است.» چهار نوع span لازم: `model_call` / `tool_call` / `reasoning` / `handoff`.
- (Summary §1، Recommendation لایه ۲) **حقیقت ساختاری: Langfuse توسط ClickHouse Inc. خریداری شد (ژانویه ۲۰۲۶)**؛ self-host آن ۵+ service می‌خواهد → **انتخاب اول: MLflow (Apache 2.0، Linux Foundation، Postgres-only، بدون enterprise paywall)**؛ انتخاب دوم: Braintrust free tier (با هشدار تضاد با export-first). **Langfuse self-host برای تک‌نفره over-engineered.**
- (Recommendation لایه ۱) **instrumentation = OpenLLMetry/Traceloop (Apache 2.0، OTel)** — «instrument once, switch backends later»؛ هم‌راستا با لنگر OTel فایل ۰۵.
- (Landscape §2) **پنج bias مستند LLM-as-judge:** position، verbosity، self-preference/family، format، calibration drift. راه‌حل: judge از خانواده‌ی غیر از مدل production + shuffle + human-agreement روی ≥۵۰ case با **kappa ≥0.7** + distilled small judges + sample rate ۵–۲۰٪ + ۱۰۰٪ خطاها.
- (Landscape §3–۴، Recommendation لایه ۳) **anchor set دستی ۵۰–۱۰۰ case** (۱۵–۲۰ per tenant؛ هر case: task + expected trajectory + gold output؛ ≥۳ rubric) + production failure mining + synthetic برای volume. **self-improvement acceptance gate (اتصال صریح به lane 3/فایل ۰۷):** `regression_rate ≤ 5٪` روی anchor set، `target_metric_delta ≥ +threshold`، `new_failure_categories == 0`؛ fail → rejected-step buffer. «نپرس skill بهتر شد؛ بپرس *سیستم* بهتر شد.»
- (Landscape §6) **drift سه‌نوعه:** output distribution / behavioral (step count، tool selection، error rate) / cost-efficiency. حداقل عملی: weekly eval روی anchor set (کاهش ≥۵٪ → investigate)، daily مانیتور cost-per-task و error-rate، monthly افزودن ۱۰ production failure به eval set؛ eval suite را rotate کن + یک held-out «unseen set» نگه دار (ضد specification gaming).
- («نساز») ❌ Langfuse self-host بدون ClickHouse موجود، ❌ judge از خانواده‌ی مدل production، ❌ eval فقط با synthetic data، ❌ outcome-only eval، ❌ drift بدون anchor set/baseline، ❌ Arize AX commercial برای drift، ❌ LangSmith (self-host فقط Enterprise)، ❌ اعتماد به dashboard سبز بدون calibration (داستان kappa 0.31).

**تاریخ/نسخه:** ساخت ۲۰۲۶-۰۷-۰۱؛ Confidence: **High** (landscape)، Medium (MLflow vs Langfuse)، Low (roadmap پسا-acquisition Langfuse).

**تناقض‌ها با چهار فایل دیگر:**
- **تناقض اصلی مجموعه:** فایل ۰۵ «OTel → Langfuse self-host یا cloud» را توصیه می‌کند؛ فایل ۰۹ با اطلاعات جدیدتر (acquisition ژانویه ۲۰۲۶ + بار ۵+ service) **MLflow را جایگزین انتخاب اول** می‌کند و Langfuse self-host را نساز می‌داند. سنتز باید ۰۹ را (به‌عنوان lane تخصصی و به‌روزتر) مرجع بگیرد؛ نقطه‌ی اشتراک هر دو: OTel/OpenLLMetry به‌عنوان لایه‌ی instrumentation ثابت.
- فایل ۰۷ «Langfuse + regression suite» را ابزار eval gate می‌داند؛ فایل ۰۹ می‌گوید Langfuse evalهای out-of-the-box ندارد — ابزار gate باید MLflow/DeepEval/Braintrust باشد.
- OTel GenAI conventions: فایل ۰۵ OTel را لنگر بی‌قید معرفی می‌کند؛ فایل ۰۹ هشدار می‌دهد `gen_ai.*` attributes هنوز «Development» هستند و hardcode کردن نام attributeها شکننده است — قید مهمی که ۰۵ ندارد.
- کاملاً مکمل با ۰۷: اعداد gate (≤۵٪، ۵۰–۱۰۰ case، unseen set) کمّی‌سازیِ همان gate اجباری فایل ۰۷ است.

**اعداد/آستانه‌های مشخص:**
- **Cohen's kappa هدف ≥0.7** (نمونه‌ی شکست: 0.31)؛ position bias ۱۰–۱۵ امتیاز؛ self-preference ۱۰–۲۵٪.
- **anchor set ۵۰–۱۰۰ case** (۱۵–۲۰ per tenant) برای regression gate؛ **≥۵۰۰ case** قبل از اعتماد به aggregate metrics؛ ≥۲۰۰ trajectory قبل از نتیجه‌گیری (per-trajectory scores noisy)؛ بعد از ۶۰ روز به ≥۲۰۰ برسان.
- **gate:** regression ≤۵٪، target delta ≥ +threshold، new failure categories = 0.
- sample rate judge: ۵–۲۰٪ traces + ۱۰۰٪ errors/outliers.
- drift: weekly eval؛ افت ≥۵٪ → investigate؛ **>۱۰۰ production run/روز → daily eval + alert خودکار**؛ monthly +۱۰ case از failures.
- ۵۷٪ سازمان‌های دارای production agent، کیفیت را barrier #1 می‌دانند (LangChain 2026).
- Braintrust free: 1M spans/ماه + 10K eval runs؛ LangSmith free: 5K traces؛ Phoenix Cloud $50+/ماه؛ Galileo Luna-2: sub-200ms و ۹۷٪ ارزان‌تر؛ MLflow: 30M+ download/ماه؛ Langfuse self-host = ۵+ service.

---

## جمع‌بندی تناقض‌های بین‌فایلی (برای سنتز)

| # | موضوع | فایل‌ها | شرح | پیشنهاد حل |
|---|---|---|---|---|
| ۱ | **Observability backend** | ۰۵ در برابر ۰۹ | ۰۵: Langfuse (self-host/cloud)؛ ۰۹: MLflow انتخاب اول، Langfuse self-host «نساز» (acquisition توسط ClickHouse ژانویه ۲۰۲۶ + ۵+ service — ۰۵ اصلاً acquisition را ذکر نمی‌کند) | ۰۹ به‌روزتر و lane تخصصی است؛ مشترکِ هر دو: OTel/OpenLLMetry به‌عنوان لایه‌ی instrumentation ثابت |
| ۲ | **ابزار eval gate** | ۰۷ در برابر ۰۹ | ۰۷: «Langfuse + regression suite»؛ ۰۹: Langfuse eval out-of-the-box ندارد → MLflow/DeepEval/Braintrust | اعداد و ابزار ۰۹ مرجع gate ۰۷ شوند |
| ۳ | **زمان‌بندی ساخت gateway** | ۰۵ (داخلی) و ۰۸ | ۰۵-Recommendation: بالاترین ROI؛ ۰۵-If-I'm-wrong: فعلاً نساز تا «≥N action/روز روی ≥۲ tenant»؛ ۰۸: اولویت ۴ («مرحله‌ی بعد») | trigger مشخص تعریف شود (آستانه‌ی action/روز) |
| ۴ | **دامنه‌ی sandbox** | ۰۵ در برابر ۰۸ | ۰۵: اگر کد untrusted نیست، لایه‌ی isolation امنیتی را حذف کن؛ ۰۸: sandbox برای هر tool call با side-effect | تفکیک: sandbox کد untrusted (۰۵) ≠ مهار side-effect tool (۰۸ — با cap/HITL هم قابل پوشش) |
| ۵ | **اطمینان OpenClaw** | ۰۵ در برابر ۰۷ | ۰۵: M «تک‌منبع، verify»؛ ۰۷: H | در سنتز به‌عنوان M/«verify» نقل شود |
| ۶ | **قید OTel** | ۰۵ در برابر ۰۹ | ۰۵: OTel لنگر بی‌قید؛ ۰۹: gen_ai.* attributes هنوز Development/unstable | قید ۰۹ به توصیه‌ی OTel اضافه شود |
| ۷ | **Qdrant** | ۰۶ در برابر ۰۸ | ۰۶: Qdrant جدا «نساز» (<50M vector)؛ ۰۸: Qdrant در TOOLING برای tool semantic search (با pgvector به‌عنوان alternative) | pgvector default؛ Qdrant فقط با آستانه‌ی ۰۶ |

**نقاط هم‌گرایی مهم (بدون تناقض):** MCP spec پایدار 2025-11-25 (۰۵ و ۰۸)؛ OTel به‌عنوان instrumentation (۰۵ و ۰۹)؛ gate اجباری برای self-improvement (۰۷ و ۰۹ — ۰۹ کمّی‌اش می‌کند)؛ isolation per-tenant با scoping صریح چون هیچ‌جا default نیست (۰۶ و ۰۸)؛ بنچمارک 74٪ filesystem (۰۶ و ۰۷)؛ Postgres به‌عنوان ستون فقرات واحد (۰۵: DBOS، ۰۶: pgvector/Mem0، ۰۹: MLflow backend)؛ همه‌ی فایل‌ها ۲۰۲۶-۰۷-۰۱ و با ساختار ۸سرفصلی یکسان، آماده‌ی merge.
# Inventory — فایل‌های Research شماره ۱۰ تا ۱۴
> منبع: `02-Research\` در vault معماری — خوانده‌شده به‌طور کامل در ۲۰۲۶-۰۷-۰۳ (READ-ONLY).
> هر پنج فایل تاریخ ساخت ۲۰۲۶-۰۷-۰۱ دارند و با ساختار ۸ سرفصلِ ثابت (Summary / Landscape / Comparison table / Blind spots / Recommendation / TOOLING / If-I'm-wrong / Confidence / Claims table) نوشته شده‌اند و «آماده‌ی merge» علامت خورده‌اند.

---

## ۱) `02-Research\10-research-safety-governance.md`

**موضوع:** ایمنی و حاکمیت (safety / governance) برای agentهای auto-execute و self-updating — kill switch، circuit breaker، least-privilege، sandbox، حاکمیتِ self-modification، و EU AI Act. علامت «⚠️ غیرقابل‌حذف» دارد (ارزش‌های غیرقابلِ حذف سیستم).

**ادعاها/توصیه‌های معماری کلیدی:**
- **معماری سه‌لایه‌ی governance (Landscape §1):** execution → policy → audit. Policy engine باید **خارج از agent** (out-of-process) باشد؛ policy روی **هر tool call** اعمال می‌شود نه روی agent. Audit log باید append-only + tamper-evident (hash-chain مثل LANGAR) باشد.
- **ماتریس autonomy چهارسطحی (Landscape §2):** AUTONOMOUS / IN-FORM / APPROVE_FIRST / HARD_STOP (منبع: ElephantBroker، arXiv:2603.25097). قانون ترکیب: `final = max(autonomy_floor_for_domain, safety_result_of_layers)`. ماتریس پیشنهادی: FINANCIAL برای mining → HARD_STOP؛ DATA_READ پروژه‌ی دیگر → HARD_STOP برای همه؛ SKILL_MODIFICATION و EXTERNAL_COMM → APPROVE_FIRST.
- **Kill switch (Landscape §3):** باید out-of-process، deterministic (token revoke + queue halt + network cut)، tested (حداقل ماهی یک بار)، authenticated (فقط operator)، و audited باشد. تمایز kill switch (global) از circuit breaker (per-condition) و dead-man switch (heartbeat). پیاده‌سازی ساده: Redis/Postgres flag که در MCP gateway middleware قبل از هر action چک شود. Conventions: KILLSWITCH.md (مه ۲۰۲۶، `[emerging]`)، «Unfireable Safety Kernel» (arXiv:2606.26057 — agent بدون kernel بوت نمی‌شود).
- **Capها (Landscape §4):** سه cap لازم: per-action، per-run، daily/weekly. برای financial: approval token با انقضای Y دقیقه؛ «human must be present» بالای Z دلار.
- **Least-privilege (Landscape §5):** سه کنترل الزامی NVIDIA: network egress allowlist، workspace write restriction (شامل dotfiles و MCP configs)، configuration file protection. Per-tenant: service account جدا + schema-per-tenant در Postgres + cgroups v2.
- **Sandbox (Landscape §6):** اگر agent کدِ generated اجرا می‌کند (مثل backtest ماینینگ) → gVisor یا E2B **اجباری**؛ Docker/runc و cgroups کافی نیست. اگر کد untrusted اجرا نمی‌شود → cgroups کافی است.
- **Self-modification governance (Landscape §7):** هر تغییرِ skill/SKILL.md/system-prompt = git commit با message + عبور از regression gate + rollback در <۵ دقیقه. A-MemGuard pattern: dual-memory (working/validated) با consensus-based validation. قانون: «هر self-edit باید در یک جمله برای human قابل توضیح باشد.»
- **EU AI Act (Landscape §8):** ۲ اوت ۲۰۲۶ تاریخ binding برای high-risk obligations؛ سیستمِ کاربر احتمالاً minimal/limited risk، ولی احتیاطاً: Article 12 (automatic logging)، Article 14 (human oversight)، Article 26 (retention ≥۶ ماه). به delay پیشنهادی Digital Omnibus اتکا نکن.
- **Recommendation:** برای ≤۵ tenant، OPA **نساز** — یک allowlist table ساده در Postgres (`action_policy` با ستون‌های max_amount / requires_approval / hard_stop) کافی است؛ OPA بعداً. HITL برای mining خطِ قرمز غیرقابل مذاکره (هیچ دستور exchange/broker، هیچ تغییر position، هیچ تغییر credential بدون تأیید).
- **Self-Critique (بخش پایانی، جایگزین triangulation):** (۱) kill switch باید **fail-closed** باشد (اگر policy engine در دسترس نبود → block همه چیز)؛ (۲) HITL برای real-time trading عملاً غیرممکن است → جایگزین: HARD_STOP کامل یا pre-approved strategy boundaries؛ (۳) cgroups برای کد untrusted کافی نیست.
- **«نساز»ها:** kill switch فقط در system-prompt؛ budget alert بدون hard-stop؛ HITL برای همه‌ی actionها (approval fatigue)؛ log بدون tamper protection.

**تاریخ/نسخه:** تاریخ ساخت ۲۰۲۶-۰۷-۰۱؛ منابع web search زنده؛ Confidence: High برای kill switch/autonomy matrix/EU timeline.

**تناقض‌ها با چهار فایل دیگر:**
- با **۱۲**: فایل ۱۰ می‌گوید «OPA برای ۵ tenant اولیه نساز، allowlist table کافی است»، ولی فایل ۱۲ در TOOLING و Recommendation مستقیماً «OPA policy engine» را به‌عنوان محل pinned constraints توصیه می‌کند — تفاوت staged بودن انتخاب ابزار باید در synthesis حل شود.
- با **۱۱**: فایل ۱۰ برای backtest ماینینگ gVisor/E2B را «اجباری» می‌داند؛ فایل ۱۱ (گام ۵) اجرای backtest ساده روی Ollama/laptop را پیشنهاد می‌کند بدون ذکر الزام sandbox — شکاف/tension.
- تنش داخلی (نه cross-file): توصیه‌ی HITL اجباری برای financial در Summary در برابر اذعان Self-Critique که HITL برای real-time trading impractical است.

**اعداد/آستانه‌های مشخص:**
- فرمول: `final = max(autonomy_floor, safety_result)`
- تست kill switch: **ماهانه**؛ rollback SLA: **<۵ دقیقه**؛ policy audit: **فصلی (quarterly)**
- «Budget under **$500/month** without circuit breakers — recursive loops will exceed it in a single night»
- نمونه بودجه: DAILY_BUDGET → mining **$50**، research **$20**؛ RUN_BUDGET → mining **$5**، research **$2** (per session)
- EU AI Act: binding **۲ اوت ۲۰۲۶**؛ جریمه تا **15M EUR یا ۳٪ turnover**؛ log retention **≥۶ ماه**
- Retry به تأیید: approval token قدیمی‌تر از Y دقیقه → reject (Y/Z پارامتریک، مقدار نه)

---

## ۲) `02-Research\11-research-cost-infra-routing.md`

**موضوع:** هزینه‌ی model inference، استراتژی routing، caching، prompt optimization، تصمیم self-host در برابر API، و resource contention روی VPS مشترک.

**ادعاها/توصیه‌های معماری کلیدی:**
- **هزینه‌ی multi-agent غیرخطی است (Summary ۱، Landscape §2):** chatbot تک-turn ۲–۴هزار توکن؛ task agentی **۵۰هزار–۵۰۰هزار توکن**. یک run معمولی = ۲۰–۵۰ LLM call؛ parallel multi-agent ≈ **۱۵×** توکنِ sequential.
- **قانون ۸۰/۲۰ (Summary ۲):** ۸۰٪ هزینه از ۲۰٪ taskها؛ **اول measure، بعد optimize** (گام ۱ Recommendation: dashboard per-task token/cost، بعد از ۷ روز ۲۰٪ گران را پیدا کن).
- **دو lever با بالاترین ROI (Summary ۳، Landscape §3):** (A) Prompt caching — ۹۰٪ تخفیف cached input در Anthropic (Sonnet: $0.30 به‌جای $3 در 1M). (B) Model routing — 70/20/10 (cheap/mid/frontier) → ۴۰–۸۶٪ کاهش bill. سوم: context trimming (summarize کردن tool outputs، sliding window، structured output).
- **جدول قیمت ژوئن ۲۰۲۶ (Landscape §1):** Opus 4.8 $5/$25 (SWE-bench 88.6٪)؛ Sonnet 4.6 $3/$15؛ Haiku 3.5 $0.80/$4؛ DeepSeek V4 Flash $0.14/$0.28؛ Gemini 3.1 Pro $2/$12؛ Gemini Flash $0.10–0.15/$0.40–0.60؛ GPT-4.1 Mini $0.40/$1.60؛ GPT-4.1 Nano $0.10/$0.40؛ MiniMax M3 $0.60/$2.40 (SWE 80.5٪). ⚠️ قیمت‌ها quarterly عوض می‌شوند — verify.
- **خط تصمیم self-host (Summary ۴، Landscape §5):** <**50M توکن/ماه** → API ارزان‌تر، self-host نکن. Break-evenها: Ollama CPU روی VPS €50/ماه ≈ 6M توکن/ماه vs Sonnet؛ vLLM+GPU vs Sonnet ≈ 35M/ماه؛ vLLM vs DeepSeek ≈ 800M/ماه («تقریباً هرگز»). Ollama CPU 7B: ۵–۱۰ tok/s — فقط async/batch. هرگز production financial reasoning به local 7B نده.
- **معماری routing پیشنهادی (Landscape §6):** rule-based classifier (keyword، <1ms — نه LLM classifier): Simple→Haiku، Medium→Sonnet 4.6، Complex/security-critical→Opus 4.8، Background/Batch→DeepSeek یا Gemini Flash. گام ۳ Recommendation: ۷۰٪ Haiku / ۲۵٪ Sonnet / ۵٪ Opus → انتظار ۴۵–۶۰٪ کاهش bill. (If-I'm-wrong: با 50/50 شروع کن و با eval به 70/25/5 برو.)
- **VPS contention (Landscape §4):** cgroups v2 / systemd slices per-tenant (CPUQuota: research 25٪/4G، mining 20٪/3G، accounting 15٪/2G) + job queue (Redis یا Postgres LISTEN/NOTIFY) + exponential backoff.
- **Batch API (گام ۴):** ۵۰٪ تخفیف برای taskهای با تحمل تأخیر ۲۴ ساعته؛ استک با caching → effective cost تا ۲۵٪ نرخ استاندارد.
- **هشدارهای Blind spots:** «cheaper per token ≠ cheaper per task» (retry مدل ضعیف)؛ error rate ۲۰٪ → هزینه‌ی مؤثر +۲۴٪؛ output tokens ۲–۶× گران‌تر از input؛ caching بد latency را بدتر می‌کند؛ DeepSeek uptime نامطمئن → برای production ماینینگ ممنوع؛ tokenizer مدل‌های 4.7+ تا **۳۵٪** توکن بیشتر (مقایسه‌ی cross-provider را خراب می‌کند).
- **خبر suspend (Summary ۵):** Claude Fable 5 و Mythos 5 از ۱۲ ژوئن ۲۰۲۶ suspend (export-control)؛ Opus 4.8 / Sonnet 4.6 / Haiku 4.5 بی‌تأثیر؛ بازگشت حدود ۱ ژوئیه — verify.
- **«نساز»ها:** self-host GPU روی VPS اجاره‌ای؛ DeepSeek برای production mining؛ LLM-based router؛ همه‌چیز روی Opus؛ optimize قبل از measure؛ Batch برای real-time؛ Ollama CPU برای reasoning پیچیده.

**تاریخ/نسخه:** ۲۰۲۶-۰۷-۰۱؛ قیمت‌ها verified از منابع ژوئن ۲۰۲۶.

**تناقض‌ها:**
- **تناقض داخلی نسخه‌ی Haiku:** جدول قیمت و توصیه‌ها «Haiku 3.5 ($0.80/$4)» می‌گویند، ولی کد routing «claude-haiku-4-5-20251001» برمی‌گرداند و بخش suspend می‌گوید «Haiku 4.5 تأثیر نگرفت». در synthesis باید نسخه/قیمت Haiku یکدست شود.
- **تناقض داخلی نسبت routing:** Landscape 70/20/10 (اثر ۴۰–۸۶٪) ولی Recommendation 70/25/5 (اثر ۴۵–۶۰٪).
- با **۱۰**: پیشنهاد backtest ساده روی Ollama بدون قید sandbox، در حالی که فایل ۱۰ gVisor را برای کد generated اجباری می‌داند.
- با **۱۲**: فایل ۱۱ به Haiku برای ۷۰٪ taskها می‌راند؛ فایل ۱۲ نشان می‌دهد accuracy پایین‌تر per-step در chain به‌شدت compound می‌شود — خودِ فایل ۱۱ در If-I'm-wrong این ریسک را می‌پذیرد (نیاز به eval gate از lane 5). tension قابل حل با «routing فقط با eval».

**اعداد/آستانه‌ها:** (علاوه بر جدول قیمت بالا)
- مدل هزینه: `cost_per_run ≈ N_agents × avg_turns × avg_tokens_per_turn × price` → مثال ۳ agent × ۵ turn روی Sonnet ≈ **$0.16/run** → ۱۰۰ run/روز ≈ **$480/ماه**؛ blended price نمونه با 70/20/10 ≈ $8.3/1M output (**~۴۵٪ صرفه vs all-Sonnet**)
- ۱۰۰ task/روز روی Sonnet بدون بهینه‌سازی: **$40–$400/روز**
- Prompt caching: **۹۰٪** تخفیف؛ Batch: **۵۰٪**؛ استک هر دو: **~۲۵٪ نرخ استاندارد**
- Break-even self-host: **50M توکن/ماه** (آستانه‌ی کلیدی)؛ vLLM 2.6× سریع‌تر از Ollama؛ Ollama Cloud آوریل ۲۰۲۶: **۹۵٪ failure window**
- هزینه‌ی پنهان: GPU فقط ۳۰–۴۰٪ هزینه‌ی واقعی؛ ops = 1.5–2 FTE = $270K–$550K/سال
- 100K توکن input روی Sonnet = **$0.30/request**

---

## ۳) `02-Research\12-research-failure-modes-blind-spots.md`

**موضوع:** حالت‌های شکست (failure modes) و نقاط کور سیستم‌های multi-agent خودبهبود — «عمداً بدبین». ده FM شماره‌گذاری‌شده + ارزان‌ترین دفاع برای هر کدام.

**ادعاها/توصیه‌های معماری کلیدی (باید در طراحی علیه‌شان دفاع شود):**
- **FM-1 Error compounding:** `P(success) = accuracy^n` → 95٪^20 = **۳۶٪**؛ 85٪^10 = **۲۰٪**؛ 99٪^20 = **۸۲٪**. مشکل architecture است نه model؛ prompt engineering آن را حل نمی‌کند. واقعیت بدتر از فرمول است (2٪ context retention loss per step). دفاع: هیچ task >**۵ step** بدون intermediate validation checkpoint؛ pipeline >۱۰ step بدون checkpoint = «تضمین ریاضی شکست».
- **FM-2 Tool misuse (۳۱٪ خرابی‌های production):** retry با همان argument غلط ده‌ها بار. دفاع: **max retry = 3** → HARD_STOP + log؛ schema validation (Pydantic) روی arguments؛ circuit break روی تکرار call یکسان.
- **FM-3 Context poisoning / prompt injection (OWASP LLM01):** خطر مستقیم tenantهای تحقیق/ماینینگ که محتوای بیرونی می‌خوانند. حوادث: 26/428 router آلوده (کیف پول $500K خالی شد)؛ hijack شدن Claude Code/Gemini CLI از طریق PR title. دفاع: markup همه‌ی محتوای بیرونی در بلاک `<external_data>` (جداسازی data plane از instruction plane)؛ sanitize؛ log source+hash برای forensics. Memory poisoning در Mem0/Zep به sessionهای بعد propagate می‌شود.
- **FM-4 Silent failure:** output مطمئن و well-formatted ولی غلط؛ monitoring سبز. pass@1 واقعیت را ۲۰–۴۰٪ overestimate می‌کند. دفاع: judge agent مستقل با context ایزوله برای تصمیم‌های مالی + spot-check دستی ۱۰ خروجی در هفته.
- **FM-5 Goal drift / reward hacking:** drift بدون weight update از راه contextual conditioning؛ specification gaming (نمونه: `sys.exit(0)` برای pass شدن تست‌ها — Anthropic نوامبر ۲۰۲۵). دفاع: eval rotation + سنجش trajectory quality نه فقط success rate.
- **FM-6 Coordination failure (۳۶.۹۴٪ در MAST):** deadlock، infinite loop از دستورهای متناقض، correlated failure. دفاع: max iteration، timeout در orchestration layer، یک agent را authoritative کن.
- **FM-7 Context compaction:** حذف constraintهای حیاتی هنگام فشرده‌سازی context (حادثه‌ی OpenClaw/Meta: نادیده گرفتن stop command و حذف emailها). دفاع: state خارجی در DB (DBOS/checkpoint)، pinned constraints در gateway/OPA — «اعتماد به stop condition داخل system-prompt نکن».
- **FM-8 Scope creep (با data quality = ۶۱٪ خرابی‌ها):** استفاده از agent یک tenant برای tenant دیگر. دفاع: per-project specs + فهرست «Do Not Use» در هر SKILL.md + eval قبل از استفاده‌ی جدید.
- **FM-9 Correlated failure از base model مشترک:** همه‌ی agentهای all-Claude یک bias دارند؛ در ماینینگ یعنی شکست همزمان در یک شرایط بازار. دفاع: **cross-model validation** (مثلاً Gemini) برای تصمیم‌های critical.
- **FM-10 Specification gaming روی eval suite:** skill library به eval overfit می‌شود. دفاع: unseen set که agent هرگز ندیده + افزودن production failures (نه synthetic). (If-I'm-wrong: rotate نکن، **grow** کن — golden anchor set ثابت ~۳۰ case.)
- **MAST Taxonomy (NeurIPS 2025، ۱۶۰۰+ trace):** specification 41.77٪ > coordination 36.94٪ > verification 21.30٪ → ارزان‌ترین ترتیب fix: اول specification، بعد validation، بعد coordination.
- **سه اولویت برای این پورتفولیو (Recommendation):** #1 error compounding (احتمال ۹/هزینه ۷)، #2 context poisoning (۸/۹)، #3 silent degradation (۸/۸).

**تاریخ/نسخه:** ۲۰۲۶-۰۷-۰۱. Confidence: آمار Gartner 78٪ و APEX 24٪ vendor/analyst-reported — verify قبل از cite.

**تناقض‌ها:**
- با **۱۳**: فایل ۱۳ «Claude Agent SDK» (Claude-only) را default معماری می‌کند؛ فایل ۱۲ (FM-9) هشدار می‌دهد stack تمام-Claude = correlated failure و برای تصمیم‌های critical مدل دوم (Gemini) لازم است. synthesis باید cross-model validation را روی stack Claude-native سوار کند.
- با **۱۰**: فایل ۱۲ «pinned constraints در OPA/gateway» می‌گوید؛ فایل ۱۰ برای شروع allowlist table را به‌جای OPA توصیه می‌کند (تفاوت ابزار، هم‌جهت در اصل externalization).
- **تنش داخلی:** جدول TOOLING «independent judge agent (همان model، context ایزوله)» را می‌آورد، ولی بخش «نساز» می‌گوید «همان Claude Sonnet که output داد آن را validate نکند» و FM-9 مدل متفاوت می‌خواهد — درجه‌بندی لازم: context ایزوله برای کارهای عادی، cross-model برای financial.
- با **۱۱**: به فرمول compounding، routing تهاجمی به مدل ارزان (فایل ۱۱) بدون eval خطر retry/error compounding دارد (هر دو فایل خودشان اشاره می‌کنند؛ contradiction سخت نیست).

**اعداد/آستانه‌ها:**
- **24٪** موفقیت first-attempt (APEX-Agents)؛ **78٪** شکست pilot (Gartner Q1 2026)
- MAST: **41.77٪ / 36.94٪ / 21.30٪**
- Tool misuse: **۳۱٪**؛ scope creep+data quality: **۶۱٪**
- **2٪** context loss per step؛ ۵ cycle → <۶۰٪ context؛ ۵۰ step → ~۳۶٪
- pass@1 overestimate: **20–40٪**؛ CLEAR: همان task یک روز ۶۰٪، روز دیگر ۲۵٪
- قواعد طراحی: max retry/iteration = **۳**؛ حداکثر **۵ step** بدون checkpoint؛ spot-check **۱۰ output/هفته**؛ anchor set **۳۰ case**
- حوادث: $500K wallet؛ Drift Protocol **$285M** (آوریل ۲۰۲۶)؛ Freysa **$47K**

---

## ۴) `02-Research\13-research-framework-landscape.md`

**موضوع:** چشم‌انداز frameworkهای agentic در ۲۰۲۶؛ کدام framework برای stack مبتنی بر Claude Cowork، و کِی اصلاً framework لازم نیست.

**ادعاها/توصیه‌های معماری کلیدی:**
- **Scaffold مهم است (Summary ۱):** انتخاب framework تا **۳۰ امتیاز** benchmark را روی همان مدل جابه‌جا می‌کند (Princeton HAL: Opus 4 → 64.9٪ vs 57.6٪).
- **توصیه‌ی سه‌مرحله‌ای (Recommendation):** مرحله ۱ — هیچ framework جدید؛ Cowork + MCP gateway + raw API برای task با ≤۵ step و ≤۲ sub-task همزمان. مرحله ۲ — Claude Agent SDK (subagents + SKILL.md + hooks + MCP) وقتی skill management لازم شد. مرحله ۳ — LangGraph (MIT) فقط وقتی conditional branching پیچیده یا durable checkpoint لازم شد؛ در کنار SDK، به‌عنوان مسیر مهاجرت model-agnostic. Decision tree صریح در متن.
- **کدام‌ها را استفاده کن:** Claude Agent SDK (native برای Cowork؛ deepest MCP؛ ولی proprietary license و Claude-only — lock-in 8)؛ LangGraph (production standard برای stateful workflows؛ checkpoint+time-travel؛ token routing کمتر 30–47٪ از CrewAI؛ 120ms/node)؛ Pydantic AI برای لایه‌ی type-safety در کارهای compliance-sensitive/financial.
- **کدام‌ها را نساز/نگیر:** CrewAI روی VPS با بودجه محدود (**3× token overhead**، 450ms/transition — مگر task واقعاً role-based باشد)؛ Microsoft Agent Framework (Azure-native)؛ Google ADK (مگر A2A لازم شود)؛ Smolagents برای production financial؛ **هیچ framework قبل از نیاز واقعی**. برای «~۷۰٪ taskها» raw API کافی است.
- **وضعیت اکوسیستم ۲۰۲۶ (Landscape §2):** AutoGen → maintenance mode Q1 2026 (fork: AG2)؛ Microsoft Agent Framework v1.0 GA آوریل ۲۰۲۶؛ Google ADK v2.0 GA مه ۲۰۲۶ (تنها A2A first-class به‌همراه CrewAI)؛ LangGraph v1.0 GA اکتبر ۲۰۲۵؛ Claude Code SDK → Claude Agent SDK (سپتامبر ۲۰۲۵). همگرایی همه روی MCP.
- **Blind spots مهم:** لایسنس **proprietary** Claude Agent SDK با ارزش export-first در تعارض است — Terms را قبل از production commit بخوان؛ SDK قابل embed مثل library نیست (state machine/conditional edge صریح ندارد)؛ SKILL.md از دسامبر ۲۰۲۵ **open standard** است (lock-in کمتر از تصور)؛ metering جداگانه‌ی Agent SDK از ۱۵ ژوئن ۲۰۲۶؛ LangGraph Platform (پولی) ≠ LangGraph OSS — برای self-host از OSS + MLflow/Langfuse استفاده کن.

**تاریخ/نسخه:** ۲۰۲۶-۰۷-۰۱؛ هشدار صریح: نسخه‌های framework سریع‌تر از هر lane دیگری تغییر می‌کنند.

**تناقض‌ها:**
- با **۱۲** (FM-9): default کردن Claude Agent SDK یعنی all-Claude stack؛ فایل ۱۲ برای critical decisions مدل دوم می‌خواهد. LangGraph model-agnostic به‌عنوان مرحله ۳ این را جزئاً جواب می‌دهد ولی تصمیم صریح لازم است.
- با **ارزش‌های اعلام‌شده در ۱۰/۱۳** (no vendor lock-in، export-first): توصیه‌ی اصلی (Claude Agent SDK، lock-in 8، proprietary) با این ارزش صراحتاً می‌سازد نه؛ خود فایل در If-I'm-wrong اذعان می‌کند («موضع من: export-first = prefer MIT/Apache») — تنش حل‌نشده که synthesis باید تعیین تکلیف کند.
- با **۱۴** (اختلاف عددی جزئی): فایل ۱۳ lock-in Claude Agent SDK را **۸** و فایل ۱۴ همان را **۷** می‌دهد.
- با **۱۱**: هم‌راستاست (token efficiency)؛ تناقض واقعی ندارد. عدد «۷۰٪ taskها framework نمی‌خواهند» (۱۳) با «۷۰٪ taskها → Haiku» (۱۱) دو مفهوم متفاوت‌اند — نباید در synthesis ادغام شوند.

**اعداد/آستانه‌ها:**
- **۳۰ امتیاز** اثر scaffold (64.9٪ vs 57.6٪)
- CrewAI: **3×** token overhead؛ **450ms**/transition؛ +**$4.10** روی ۱۰۰-loop research workflow — LangGraph: **120ms**/node؛ **30–47٪** توکن کمتر
- آستانه‌ی «framework نمی‌خواهی»: ۱ agent، **≤۲ tool call**، بدون branching/checkpoint؛ per-tenant: **≤۵ step و ≤۲ concurrent agent** → raw code
- تاریخ‌ها: metering جداگانه **۲۰۲۶-۰۶-۱۵**؛ SKILL.md open standard **دسامبر ۲۰۲۵**

---

## ۵) `02-Research\14-research-theoretical-foundations.md`

**موضوع:** مبانی نظری self-improvement برای agentها؛ سه سطح بهبود، Utility-Learning Tension، SkillOpt/DGM/HyperAgents، و اعتبارسنجی نظری معماری LANGAR/Fusion.

**ادعاها/اصول نظری کلیدی:**
- **سه سطح self-improvement (Landscape §1):** **Level A** — skill/in-context edits (SKILL.md، prompt، memory) با weights ثابت: امن‌ترین، rollback با git، production-ready الان؛ سقف = capability مدل base. **Level B** — scaffold/harness edits (DGM: SWE-bench 20٪→50٪؛ HyperAgents): فقط برای دامنه‌هایی که task با substrate هم‌راستاست (coding)؛ برای mining/accounting این alignment نیست. **Level C** — weight update: برای solo-operator ممنوع/NOT recommended (reward hacking، بدون rollback، نیاز به هزاران trajectory و GPU). «فقط A و B جایز است» و عملاً الان فقط A.
- **Utility-Learning Tension (Landscape §3، Wang et al.، arXiv:2510.04399):** بهبود performance فوری می‌تواند generalization را نابود کند؛ تضمین‌ها فقط با capacity **uniformly bounded** حفظ می‌شوند. راه‌حل: **two-gate policy** — gate ۱: immediate utility بهتر؛ gate ۲: بدون degradation در generalization (regression test). این پایه‌ی نظری validation gate سه‌شرطی سیستم است (regression ≤۵٪ روی anchor set، target metric بهتر، no new failure categories).
- **SkillOpt (Landscape §4، Microsoft، arXiv:2605.23904):** SKILL.md به‌عنوان «trainable external state of a frozen agent»؛ حلقه: rollout → bounded edits (بودجه‌ی **۸ edit**/step) → strict held-out validation gate → commit/reject (rejected-edit buffer). معادل deep learning در فضای متن (edit budget = learning rate و…). نتایج: **+23.5** امتیاز GPT-5.5 direct، **+24.8** Codex، **+19.1** Claude Code؛ **52/52** best-or-tied. Skills بین مدل‌ها transfer می‌شوند (anti-lock-in). محدودیت: فقط برای taskهایی با verifier خودکار/متریک قابل اندازه‌گیری؛ برای open-ended نیازمند judge — که اگر judge از همان family باشد → false positive.
- **توصیه‌ی مرکزی (Recommendation):** SkillOpt = موتور Fusion Phase 3؛ **آستانه‌های داده:** الان (cold-start) فقط manual skill writing؛ با **≥۵۰ scored trajectory per project** → حلقه SkillOpt آن tenant؛ با **≥۲۰۰ trajectory** → تازه به Level B فکر کن. (جدول مقایسه: Level A حداقل ≥۲۰ trajectory per skill؛ Level B ≥۱۰۰ benchmark run.) قبل از هر skill domain: alignment check بین task و substrate. DSPy (ساختار pipeline) + SkillOpt (محتوای skill) مکمل‌اند. SkillOpt-Sleep (preview ژوئن ۲۰۲۶) = بهبود شبانه، معادل «dreaming».
- **اعتبار نظری LANGAR/Fusion (Landscape §7):** LANGAR = calibrated evidence store = معادل empirical validation در DGM (قوی‌تر از benchmark مصنوعی)؛ validation gate سه‌شرطی = دقیقاً two-gate policy؛ no-self-improvement rule در Phase 1–2 = capacity bounding عملی؛ **cold-start bottleneck یک محدودیت بنیادی نظری است نه bug** — بدون داده‌ی عملیاتی هیچ self-improvement معناداری ممکن نیست.
- **«نساز»ها:** پیاده‌سازی production HyperAgents ($50–$500 هر دور optimization)؛ unbounded self-modification؛ SkillOpt بدون held-out جدا؛ Level C؛ self-improvement قبل از داشتن داده‌ی واقعی.

**تاریخ/نسخه:** ۲۰۲۶-۰۷-۰۱؛ archetype: math/theory.

**تناقض‌ها:**
- با **۱۲** (هم‌راستا نه متضاد): FM-10 فایل ۱۲ (spec gaming روی eval) دقیقاً همان پیش‌بینی Utility-Learning Tension است؛ هر دو held-out/unseen set می‌خواهند — تأیید متقابل.
- با **۱۳**: lock-in claude-agent-sdk را **۷** می‌دهد (۱۳ می‌گوید ۸) — اختلاف جزئی نمره.
- با **۱۰**: فایل ۱۰ برای self-modification فقط git+regression gate می‌گوید؛ فایل ۱۴ چارچوب quantitative قوی‌تر (bounded edit budget، آستانه‌های داده) اضافه می‌کند — تکمیل، نه تناقض؛ ولی «rollback <۵ دقیقه» (۱۰) و «git revert trivial» (۱۴) باید در یک SLA واحد ادغام شوند.
- نکته‌ی judge (blind spot مشترک با ۱۲): judge از همان family = false positive → با توصیه‌ی cross-model فایل ۱۲ همگراست و با default all-Claude فایل ۱۳ در تنش.

**اعداد/آستانه‌ها:**
- Validation gate: **regression ≤۵٪** + target metric بهتر + no new failure categories
- Edit budget: **۸ edit** per step (bounded)
- داده: **≥۲۰** trajectory per skill (Level A) / **≥۵۰** per project برای شروع حلقه / **≥۱۰۰** run برای Level B / **≥۲۰۰** قبل از فکر کردن به Level B / **هزاران** برای Level C
- SkillOpt: **+23.5 / +24.8 / +19.1** امتیاز؛ **52/52**؛ DGM: **20٪→50٪** SWE-bench؛ HyperAgents imp@50 = **0.630**؛ هزینه‌ی هر دور evolutionary: **$50–$500**

---

## جمع‌بندی تناقض‌های cross-file (برای synthesis)

1. **Claude Agent SDK در برابر correlated failure و export-first:** فایل ۱۳ SDK اختصاصی Claude را default می‌کند؛ فایل ۱۲ (FM-9) و ۱۴ (judge family bias) برای تصمیم‌های critical مدل دوم می‌خواهند؛ لایسنس proprietary با ارزش no-lock-in (اعلام‌شده در ۱۰ و ۱۳) در تنش است. تصمیم لازم: SDK به‌عنوان runtime + cross-model validation اجباری برای financial + مسیر خروج LangGraph.
2. **OPA همین حالا یا بعداً:** فایل ۱۰ «allowlist table اول، OPA بعد از >۵ tenant»؛ فایل ۱۲ pinned constraints را «در OPA/gateway» می‌گذارد. اصل مشترک (policy خارج از context/agent) یکی است؛ ابزار باید یکدست شود.
3. **Sandbox برای backtest ماینینگ:** فایل ۱۰ gVisor/E2B را برای کد generated «اجباری» می‌داند؛ فایل ۱۱ اجرای backtest روی Ollama/laptop را بدون قید sandbox پیشنهاد می‌کند.
4. **Routing تهاجمی به مدل ارزان در برابر error compounding:** فایل ۱۱ (۷۰٪ Haiku) باید مشروط به eval gate شود وگرنه با ریاضیات فایل ۱۲ «cheaper per token ≠ cheaper per task» تصادم می‌کند؛ هر دو فایل خودشان راه‌حل (شروع 50/50 + eval) را می‌دهند.
5. **نسخه‌ی Haiku (داخلی فایل ۱۱):** جدول قیمت Haiku 3.5 ولی کد و بخش suspension Haiku 4.5 — قبل از استفاده در معماری قیمت/نسخه verify شود.
6. **نسبت routing (داخلی فایل ۱۱):** 70/20/10 در برابر 70/25/5.
7. **Eval rotation در برابر eval growth:** توصیه‌ی اولیه فایل ۱۲ «quarterly rotate» ولی If-I'm-wrong همان فایل و فایل ۱۴ «anchor ثابت + grow با production failures» — نسخه‌ی نهایی: anchor set ثابت (~۳۰) + held-out unseen + افزودن failureهای واقعی.
8. **نمره‌ی lock-in claude-agent-sdk:** ۸ (فایل ۱۳) در برابر ۷ (فایل ۱۴) — جزئی.
9. **HITL برای mining (داخلی فایل ۱۰ با پیامد cross-file):** HITL اجباری در Summary ولی Self-Critique آن را برای real-time غیرعملی می‌داند → جایگزین معماری: HARD_STOP کامل یا pre-approved strategy boundaries؛ این باید با autonomy matrix (۱۰) و FM-1/FM-4 (۱۲) یکپارچه شود.

**نقاط همگرایی قوی (بدون تناقض):** policy/constraints خارج از agent و خارج از context window (۱۰، ۱۲)؛ git برای هر self-modification + regression gate (۱۰، ۱۴)؛ held-out/unseen eval در برابر spec gaming (۱۲، ۱۴)؛ max retry/iteration = 3 (۱۰، ۱۲)؛ measure-first و کوچک نگه داشتن scope/chain (۱۱، ۱۲، ۱۳)؛ fail-closed (۱۰) و external state store (۱۲).
# اینونتوری اسناد فنی — پوشه‌ی 04-Docs

> دامنه: چهار فایل در `04-Docs` والت `architect` — بررسی کامل، READ-ONLY.
> تاریخ اینونتوری: 2026-07-03

---

## 1) SERVER-ARCHITECTURE.md

- **مسیر/نام فایل:** `04-Docs\SERVER-ARCHITECTURE.md` (~13KB)
- **موضوع:** طراحی کامل «Server Architecture — Multi-Project AI Automation VPS (v1.0)» — یک VPS واحد برای میزبانی چند پروژه‌ی AI با GitHub به‌عنوان source of truth، deploy اتوماتیک ولی gated، و کنترل از طریق Telegram + یک root CLI.
- **تاریخ/نسخه:** v1.0 — نسخه: **2026-06-30** — نویسنده: «design pass با Sume». افق طراحی: 2028–2035 (مسیر مهاجرت به k8s باز).

### ادعاها/تصمیم‌های کلیدی

**چیدمان دقیق VPS (runtime = Docker Compose):**
```
VPS
├── Traefik (reverse proxy)      ← TLS خودکار + روتینگ بر اساس دامنه/مسیر
├── infra-control/
│   ├── stackctl                 ← root CLI (Python یا bash)
│   ├── control-bot (container)  ← Telegram bot (BotFather)
│   ├── userbot (container)      ← Telethon، least-privilege، اکانت جدا
│   └── monitoring/              ← Uptime Kuma + Dozzle (container)
├── brushline (container[s])
├── project-x (container[s])
└── mono-misc/* (container[s])
```
- **پورت‌ها:** هیچ port number صریحی در سند نیامده — روتینگ کاملاً از طریق **Traefik labels** (دینامیک، بر اساس domain/path) انجام می‌شود؛ جایگزین ساده‌تر: Caddy. Resource limit per-container با `mem_limit`/`cpus`.
- **ساختار repo (هیبرید):** `infra-control` (مغز سیستم: stackctl، botها، compose سراسری، workflows) + `brushline` (پروژه‌ی بزرگ، repo مستقل) + `project-x` (repo مستقل بعدی) + `mono-misc` (monorepo پروژه‌های کوچک، هرکدام Dockerfile خودش). هر پروژه compose خودش را دارد؛ registry مرکزی = `projects.yaml`.
- **stackctl (تک‌منبع منطق کنترل):** `up / down / restart / status / logs [-f] / deploy / kill <project> / kill --all` — deploy یعنی pull + build + up + health + rollback.
- **لایه‌ی کنترل تلگرامی:** bot با inline buttons، فقط chat ID مالک مجاز، هر اکشن audit-log؛ userbot فقط برای کارهای نیازمند اکانت کاربر (خواندن کانال‌ها)، **هرگز برای کنترل زیرساخت** (ریسک ToS/بن).
- **قرارداد deploy (CI/CD gated، به‌ازای هر repo `.github/workflows/ci.yml`):**
  1. test (AST + unit tests؛ برای Brushline همان `test_phase*.py`)
  2. secret scan با **gitleaks**
  3. docker build
  4. push image به **GHCR**
  5. trigger deploy روی سرور (webhook امن یا SSH → `stackctl deploy <project>`)
  6. health-check (HTTP 200 / container healthy ظرف N ثانیه)
  7. در صورت ناسالم بودن → **rollback خودکار** به image قبلی + alert تلگرام
- **Secret management:** SOPS + age (رمزنگاری‌شده داخل `infra-control/secrets/` و نسخه‌بندی در git)؛ gitleaks در CI؛ جایگزین اختیاری: Infisical/Doppler (با هشدار vendor lock-in). درس عبرت: حادثه‌ی commit خانگی با 327k فایل + private key.
- **Observability/Governance:** Uptime Kuma (مانیتور + alert تلگرام)، Dozzle (لاگ‌های وب)، audit log با الگوی hash-chain برگرفته از Brushline، kill switch سراسری و per-project، branch protection روی main همه‌ی repoها؛ AIها فقط از طریق branch/PR کار می‌کنند نه SSH.
- **همسویی با invariantها:** INV-1 (gate قبل از اجرا = CI/health)، INV-2 (secret/PII خارج از git = SOPS)، INV-3 (kill switch + audit + cap).
- **فازبندی:** Phase 0 (هفته ۱: Docker + infra-control + containerize کردن Brushline پشت Traefik) → Phase 1 (هفته ۲: control bot + SOPS) → Phase 2 (هفته ۳: ci.yml کامل end-to-end) → Phase 3 (هفته ۴+: Kuma/Dozzle، userbot، limits، پروژه‌ی دوم).
- **هزینه:** VPS 4GB/2vCPU ≈ $24 USD (~AUD 35) یا 8GB ≈ $48 (~AUD 70)؛ نرم‌افزارها همه OSS و ~$0؛ بودجه‌ی API پروژه‌ی Brushline جدا: AUD $15–40/ماه. GHCR و 2000 دقیقه Actions رایگان.
- **فرض‌ها:** ~۲–۶ پروژه‌ی سبک، یک VPS واحد (Ubuntu)، یک operator انسانی.

---

## 2) local-ai-packaged-reference.md

- **مسیر/نام فایل:** `04-Docs\local-ai-packaged-reference.md` (کوچک؛ tags: reference, infra, self-hosted)
- **موضوع:** یادداشت مرجع برای repo شخص ثالث `coleam00/local-ai-packaged`.
- **ادعاها/تصمیم‌های کلیدی:**
  - کلون محلی **حذف شده** (۹.۷MB، شخص ثالث، بدون تغییر محلی)؛ در صورت نیاز دوباره `git clone https://github.com/coleam00/local-ai-packaged.git`.
  - محتوا: استک Docker Compose برای AI self-hosted شامل **n8n، Supabase، Ollama، Open WebUI، Flowise، SearXNG، Caddy، Qdrant**.
  - نقش در معماری: **کاندیدای** زیرساخت اجرای لوکال برای [[03 - Projects/Lead-نقاشی/AiFarm-Lead/SERVER_ARCHITECTURE|SERVER-ARCHITECTURE]] — میزبانی workflowها (n8n) و مدل‌های لوکال (Ollama) روی VPS. (هنوز تصمیم قطعی نیست، فقط candidate.)
- **تاریخ/نسخه:** ذکر نشده.

---

## 3) coin-hunter-tier3-verdict-schema.json

- **مسیر/نام فایل:** `04-Docs\coin-hunter-tier3-verdict-schema.json` (~10KB، JSON Schema draft-07)
- **موضوع:** «Coin Hunter Bot – Tier 3 Verdict Schema» — ساختار خروجی سخت‌گیرانه برای verdictهای **Claude Opus orchestrator**؛ خروجی Tier 3 «MUST validate» علیه این schema.
- **تاریخ/نسخه:** ذکر نشده (فقط draft-07 بودن schema).

### چه pipeline/تیرهایی را ایماپلای می‌کند
- **خط لوله‌ی حداقل سه‌مرحله‌ای:** فیلد `tier2_dossier_reference` (path یا hash) نشان می‌دهد Tier 3 روی «dossier» تولیدی Tier 2 سوار است؛ `hard_filters_passed` و `red_flags_triggered` وجود یک لایه‌ی screening/hard-filter پیش‌تر (Tier 1) را ایماپلای می‌کند. Tier 3 = قضاوت نهایی توسط Opus به‌عنوان orchestrator.
- **تصمیم نهایی:** enum چهارگانه `STRONG_ACCUMULATE / CAUTIOUS_ACCUMULATE / MONITOR / REJECT` + confidence (LOW/MEDIUM/HIGH و numeric 0–1) + خلاصه و استدلال **دوزبانه EN/FA** (کاربر فارسی‌زبان).
- **۹ بخش تحلیلی الزامی:** technical_fundamentals (الگوریتم mining، hashrate، quantum_resistance)، code_quality (code_provenance با enum جالبِ ORIGINAL→COPY_PASTE_REBRAND)، economic_structure (premine، fair launch، emission)، onchain_forensics (تمرکز holderها، wallet clustering، خروج کیف‌پول premine)، market_microstructure (slippage، wash trading، pump&dump signature)، community_social (shill detection، کیفیت engagement توسعه‌دهنده)، comparable_coins (base-rate reasoning با outcome: ALIVE_GROWING…DEAD/PUMP_DUMP)، accumulation_strategy، meta_feedback. بخش اختیاری: mining_economics.
- **عملیات mining با ناوگان Orange Pi:** فیلدهای `operator_daily_profit_usd_per_orange_pi`، `orange_pi_allocation_count`، `estimated_daily_yield_full_fleet` و مفهوم **edge_zone** («برای ماینر متوسط غیرسودده ولی برای operator با برق $0.05/kWh سودده») ⇒ استراتژی: شکار کوین‌های PoW حاشیه‌ای که فقط با هزینه‌ی برق ارزان صرفه دارند و **انباشت از راه mining** (`acquisition_method`: MINING_ONLY / MINING_PLUS_SMALL_BUYS / MINING_PLUS_DCA).
- **مدیریت ریسک کمی:** position sizing با **Kelly criterion** (kelly_inputs + fractional kelly)، `kill_switches_en/fa` (هم‌راستا با فرهنگ kill-switch/INV-3 در SERVER-ARCHITECTURE)، افق بازبینی برحسب روز.
- **حلقه‌ی خودبهبودی prompt:** بخش meta_feedback با `prompt_improvement_suggestion`، `circular_reasoning_check_passed`، `counter_narratives_generated_count`، `surprised_by_anything` ⇒ طراحی عامدانه‌ی anti-bias و بهبود تدریجی prompt orchestrator — دقیقاً همان الگوی «adversarial verification» که در transcript هم توصیه شده.

---

## 4) transcript-claude-md-agents.md

- **مسیر/نام فایل:** `04-Docs\transcript-claude-md-agents.md` (~457KB، **بدون هیچ newline** — یک خط غول‌پیکر)
- **موضوع:** الحاق (concatenation) حدود ۱۰ transcript ویدیوی YouTube. بخش‌های مرتبط با CLAUDE.md/agent design: (۱) ویدیوی «Karpathy skills» CLAUDE.md؛ (۲) ویدیوی Agentic OS/dashboard (سه گزینه: live artifact / Obsidian / وب‌اپ)؛ (۳) ویدیوی «۳۲ هک Claude Code»؛ (۴) breakdown مسترکلاس مهندسان Anthropic درباره‌ی **dynamic workflows** (شش الگو)؛ (۵) پادکست Ross Mike درباره‌ی skills در برابر claude.md/agents.md؛ (۶) ویدیوی Fable 5 با چارچوب GOAL (Duncan Rogoff)؛ (۷) پادکست use-caseهای Fable 5 (tournament، interview-before-build)؛ (۸) ویدیوی «۷ skill که بدونش نمی‌تونم». بخش‌های نامرتبط: دوره‌ی کامل system design/API (REST/GraphQL/gRPC/auth)، ویدیوی کتاب‌های ریاضی، ویدیوی personal brand (دو بار تکرار شده!)، ویدیوی فروش AI audit.
- **تاریخ/نسخه:** ذکر نشده؛ ارجاعات داخلی به «Claude Fable 5 just dropped» ⇒ اواسط ۲۰۲۶.

### بهترین practiceهای عملی CLAUDE.md / agent design (۱۵ مورد کلیدی)

1. **Think before coding / سؤال تا وضوح:** آژانت باید قبل از build فرض‌هایش را چک کند و سؤال بپرسد؛ الگوی «آن‌قدر سؤال بپرس تا ۹۵٪ مطمئن شوی» + الگوی «interview me first» (متاپرامپت مصاحبه، ۵–۷ سؤال، بعد master prompt).
2. **Simplicity first:** مدل‌ها به‌طور پیش‌فرض production-pattern و بلوتد می‌سازند؛ در CLAUDE.md صراحتاً «حداقلِ کد» را الزام کن (مثال: ۲۰ خط به‌جای ۵۰+).
3. **Surgical changes:** فقط همان چیزی که خواسته شده تغییر کند؛ دست نزدن به comment/ساختار غیرمرتبط — یکی از موذی‌ترین failure modeها.
4. **Goal-driven / declarative:** به‌جای دستور imperative، «تعریفِ done» و success criteria بده و بگذار مدل loop بزند (اساس /goal و چارچوب **GOAL**: Ground in truth، Outcome not orders، Autonomy over the path، Loop in proof).
5. **CLAUDE.md را لاغر نگه دار:** حداکثر ~۱۵۰–۲۰۰ خط؛ چون در هر turn لود می‌شود و context را می‌خورد.
6. **CLAUDE.md به‌عنوان router:** به‌جای inline کردن همه‌چیز، به فایل‌های مرجع (style guide، business context، docs) **لینک** بده — مدل بداند «کجا» بگردد نه «همه‌چیز» را حفظ باشد.
7. **به‌روزرسانی مداوم + خودترمیمی:** بعد از هر کشف/اشتباه، از خود آژانت بخواه CLAUDE.md یا skill را آپدیت کند تا خطا تکرار نشود («fix it, then update the skill so this doesn't happen again»).
8. **Skills > CLAUDE.md حجیم (progressive disclosure):** از skill فقط name+description وارد context می‌شود (مثال واقعی: ۹۴۴ توکن در agents.md در برابر ۵۳ توکن)؛ دانش workflow-محور را در skill بگذار؛ CLAUDE.md فقط برای اطلاعات proprietary که واقعاً در هر turn لازم است («۹۵٪ افراد چنین چیزی ندارند»). به مدل چیزی که خودش می‌داند نگو (مثل «use React»).
9. **Skill را از یک run موفق بساز، نه از صفر:** اول workflow را قدم‌به‌قدم با آژانت اجرا کن، بعد بگو «review what you did → create the skill»؛ سپس **recursive improvement** با هر شکست. Skill آماده‌ی دیگران را کورکورانه دانلود نکن (attack vector + بدون context).
10. **بهداشت context:** context کوچک نگه دار؛ `/context` برای تشخیص bloat؛ `/compact` حدود ۶۰٪ (با دستور «keep X»)؛ `/clear` بین taskها؛ کارایی مدل نزدیک سقف context افت می‌کند (زیر ~۷۰٪ بمان).
11. **Plan mode اول + رفتار با مدل مثل junior developer:** اول read/research/plan بدون تغییر؛ مسئله بده نه صرفاً دستور.
12. **Subagentها برای موازی‌سازی:** context window ایزوله برای هر subagent؛ مدل ارزان (Haiku) برای خواندن/scrape حجیم و مدل قوی برای synthesis؛ agent teams وقتی هماهنگی بین آژانت‌ها لازم است؛ git worktrees برای sessionهای موازی.
13. **شش الگوی dynamic workflow (مسترکلاس Anthropic):** classify & act، fan-out & synthesize، **adversarial verification** (رفع self-preference bias — تولیدکننده و داور باید آژانت‌های جدا باشند)، generate & filter، **tournament** (مقایسه‌ی pairwise با context تازه در هر مسابقه)، loop-until-done؛ قابل stack کردن؛ token-heavy است — budget مشخص کن و برای کار ساده استفاده نکن.
14. **Verification را در execution بگنجان:** self-check در to-do list («تا ۹۵٪ مطمئن نشدی جلو نرو»)، حلقه‌ی screenshot/browser (Chrome DevTools) قبل از تحویل V1، rubric صریح برای داوری.
15. **ایمنی/عملیات:** allow/deny list دقیق به‌جای dangerously-skip-permissions (deny بر allow مقدم است)؛ API endpoint مستقیم به‌جای MCP کامل وقتی توکن تنگ است؛ context7 MCP برای docs به‌روز؛ hooks برای notification؛ اجرای Claude Code روی VPS برای session همیشه‌روشن + کنترل از Telegram؛ ultrathink فقط برای تصمیم‌های معماری/دیباگ سخت.

---

## تناقض‌ها / تنش‌های بین این فایل‌ها

1. **Traefik در برابر Caddy:** SERVER-ARCHITECTURE پیشنهاد اصلی‌اش Traefik است (Caddy = جایگزین ساده‌تر)، ولی استک local-ai-packaged (کاندیدای میزبانی n8n/Ollama) با **Caddy** حمل می‌شود ⇒ اگر آن استک adopt شود، دو reverse proxy یا تصمیم یکسان‌سازی لازم است. (تنش، نه تناقض صریح.)
2. **دسترسی مستقیم آژانت به سرور:** SERVER-ARCHITECTURE اصل می‌گذارد «AIها از طریق repo کار می‌کنند نه SSH؛ هیچ‌چیز بدون gate تست/health اجرا نمی‌شود»؛ اما transcript (هک ۲۶) صریحاً «Claude Code را روی VPS همیشه‌روشن اجرا کن و از Telegram هدایتش کن» را توصیه می‌کند ⇒ تنش حاکمیتی بین «deploy gated و repo-only» و «آژانت زنده روی سرور».
3. **تناقض داخلی خود transcript درباره‌ی CLAUDE.md:** ویدیوی Karpathy skills می‌گوید یک CLAUDE.md پرمحتوا رفتار آژانت را متحول می‌کند و ویدیوی هک‌ها «۱۵۰–۲۰۰ خط» را توصیه می‌کند؛ در حالی که پادکست Ross Mike می‌گوید claude.md/agents.md برای اکثر افراد «اضافی» است و همه‌چیز باید skill شود. جمع‌بندی سازگار: حداقلِ always-on + ارجاع/progressive disclosure.
4. **دانلود skill آماده: بله یا هرگز؟** یک ویدیو نصب مستقیم Karpathy skills (و مارکت‌پلیس skillها) را ترویج می‌کند؛ پادکست دیگر صریحاً «skill دیگران را دانلود نکن» (امنیت + بی‌contextی) می‌گوید.
5. **Imperative در برابر Declarative:** هک‌های قدیمی‌تر (plan mode، دستور قدم‌به‌قدم، subagentهای دستی) با فلسفه‌ی Fable-era («فقط goal بده، مسیر را خودش انتخاب کند») هم‌جهت نیست — وابسته به نسل مدل.
6. **پورت‌ها مستند نیستند:** SERVER-ARCHITECTURE هیچ port mapping صریحی نمی‌دهد (اتکای کامل به Traefik labels) — برای سند synthesis باید به‌عنوان gap ثبت شود، نه فرض.
7. **هم‌راستایی (نه تناقض):** kill_switches و meta_feedback در schema کوین‌هانتر با INV-3 (kill switch/audit) و الگوی adversarial verification در transcript کاملاً consistent است — نشانه‌ی یک فلسفه‌ی طراحی واحد (gate، audit، anti-bias) در کل سیستم.
8. **کیفیت داده‌ی transcript:** فایل ۴۵۷KB بدون newline است، شامل محتوای کاملاً نامرتبط (دوره‌ی ریاضی، personal brand ×۲ تکراری، system design course) — به‌عنوان منبع، نویز بالایی دارد و فقط ~نیمی از آن مرتبط با CLAUDE.md/agents است.
# اینونتوری فایل AI-FARM-MASTER-EXPORT.md

منبع: `C:\Users\Armin\Desktop\backup\04 - Architect System\architect\03-Exports\AI-FARM-MASTER-EXPORT.md`
اندازه: ۱۴۳۴ خط · ~۱۰۷KB · تاریخ ساخت سند: **۲۰۲۶-۰۷-۰۲**
هدف سند: فایل واحد انتقال کامل context یک پروژه به پروژه‌ی جدید (آپلود در Project knowledge).

---

## ۱) ساختار سند (sections/messages/dates)

سند از ۷ «بخش» تشکیل شده:

| بخش | خطوط | محتوا |
|---|---|---|
| سرصفحه | ۱–۶ | تاریخ ساخت ۲۰۲۶-۰۷-۰۲، دستور استفاده |
| **بخش ۱ — حافظه‌ی پروژه (Project Memory, verbatim)** | ۸–۴۵ | Purpose، Current state، On the horizon، Key learnings، سبک تعامل کاربر (Ari/Armin) |
| **بخش ۲ — عصاره‌ی چت‌ها (۱۲ session)** | ۴۷–۱۱۶ | ۹ زیربخش (۲.۱ تا ۲.۹): تحقیق ۲۰-لِین، context کاربر، LANGAR، Fusion-MVP، unified build، قلب/NEURO، Brushline، export قبلی، شکاف‌ها |
| **بخش ۳ — HANDOFF.md (verbatim)** | ۱۱۹–۳۴۹ | handoff قلب و آگاهی + سیستم همیشه‌روشن؛ امضا: Claude Sonnet 4.6، ژوئن ۲۰۲۶ |
| **بخش ۴ — سیستم همیشه‌روشن: پرامپت و دستورالعمل (verbatim)** | ۳۵۲–۶۱۲ | نسخه‌ی ساده‌شده v2.0 (ژوئن ۲۰۲۶، MVP-first) |
| **بخش ۵ — Red-team معماری یکپارچه (verbatim)** | ۶۱۴–۸۶۲ | فایل `16-redteam-unified-architecture.md`؛ تاریخ ساخت **۲۰۲۶-۰۷-۰۱**؛ ۹ حمله |
| **بخش ۶ — heart-awareness-map-v3.html (کد کامل)** | ۸۶۶–۱۲۲۴ | کل HTML نسخه‌ی ۳ (ژوئن ۲۰۲۶) |
| **بخش ۷ — heart-awareness-map-v2.html (کد کامل، نسخه قبلی)** | ۱۲۲۸–۱۴۳۰ | کل HTML نسخه‌ی ۲ |
| پایان | ۱۴۳۴ | «پایان export — AI FARM · ۲۰۲۶-۰۷-۰۲» |

تاریخ‌های ذکرشده: red-team ۲۰۲۶-۰۷-۰۱، سند ۲۰۲۶-۰۷-۰۲، Anthropic قطع دسترسی Fable 5/Mythos 5 در ۱۲ ژوئن ۲۰۲۶، امضاها ژوئن ۲۰۲۶.

---

## ۲) تصمیم‌های معماری (با خط تقریبی)

### لایه‌ها و سلسله‌مراتب اطلاعات
- **سه لایه‌ی اصلی سیستم هایبرید** (خط ۱۲): **LANGAR** (calibration ledger لنگرشده به truth خارجی) + **Fusion** (roadmap اجرای فازبندی‌شده) + **HRV/biosignal** به‌عنوان ورودی orchestrator.
- **سلسله‌مراتب یک‌طرفه** (خط ۲۰): LANGAR بر Fusion حکومت می‌کند؛ HRV فقط ورودی است (never governs).
- **سه بخش «همراهِ همیشه‌روشن»** (خط ۹۶): **LANGAR** (مغز ناظر، دفترچه append-only، دکمه `/halt`) · **NEURO** (ثبت روزانه RMSSD و ترند، بدون تشخیص پزشکی) · **FUSION** (نوشتن خلاق با برچسب E/S/P). رابط: بات تلگرام.

### lanes (engineering/creative/safety) — کدنام فولدرها
- **فولدرها** (خط ۸۵): `fusion-mvp/` (= langar، core engineering + self-improvement)، `fusion-safety/` (THREAT-MODEL، GAP-AUDIT، IGK kernel — safety lane)، `fusion-creative/` (creative lane).
- **برچسب‌گذاری خلاقانه E/S/P** (خط ۹۶، ۱۴۴): E=Established/مستحکم، S=Speculation/حدس، P=Metaphor/استعاره. این تگ‌ها هم در FUSION هم در نقشه‌ی پژوهش قلب استفاده شده‌اند.
- **تحقیق ۲۰-لِین** (خط ۴۹–۶۰): فایل‌های 05–14 (نیمه‌ی اول lanes) + لِین‌های ۱۱–۲۰ + Synthesis + Red-team + پاسخ پنل (Claude/GPT/Gemini). Lane 13=tenancy، Lane 14=secrets معرفی شدند به‌عنوان foundation واقعی (نه orchestration).

### orchestration
- **Orchestrator-00** (خط ۱۴): واژگان فعال دامنه.
- **Task Router** (خط ۲۱): برای جلوگیری از heavy templating روی queryهای سبک embed شده.
- **خط تولید اعتماد Brushline** (خط ۱۰۲): سیگنال/enquiry → Orchestrator → Workerها (فقط draft) → Gate 1 (قانون AU) → Gate 2 تأیید انسانی تلگرام → انتشار → Gate 3 Audit (hash-chained).
- **orchestration در نقد red-team**: از Claude Cowork (خط ۷۵۶).

### budgets / build order
- **Build order تحقیق ۲۰-لِین** (خط ۵۹): Phase 0 (سخت‌سازی + isolation + secrets + egress) → 1 (log + policy gate) → 2 (durable + scheduling) → … → کریپتو track جدا → self-improvement آخر. تخمین ~۳–۵ ماه part-time.
- **Fusion فازبندی sequential** (خط ۲۷): Phase 3 پشت فازهای قبلی gate شده (قانون no-self-improvement).
- **فازهای قلب/بات** (خط ۳۲۹): فاز ۱ بعد از ۲ هفته (پینگ صبحگاهی، مرور هفتگی، Apple Shortcut)؛ فاز ۲ بعد از ۱ ماه (FUSION، Microsoft Agent Governance Toolkit، Wilson score).

### models
- **Model routing کاملاً Anthropic** (خط ۷۵۳): Haiku/Sonnet/Opus. Haiku default، Sonnet/Opus فقط دستی برای task سخت (خط ۸۵۱).
- **cross-model judge**: Gemini برای Claude outputs، رفع family bias (خط ۷۷۰).
- امضای HANDOFF: **Claude Sonnet 4.6** (خط ۳۴۸).

### تصمیم‌های امنیتی کلیدی
- **کریپتو off-box** (خط ۷۶): shared kernel یعنی یک CVE کافی است؛ signer کاملاً جدا، صفر LLM access، allowlist مقصد، human co-sign (خط ۵۴).
- **Egress proxy اجباری** با payload logging + PII scan جلوی هر model call (خط ۵۶).
- **Durable exec سبک** = DBOS روی همان Postgres (نه Temporal) (خط ۵۷).
- **GitHub** از طریق git CLI (repo خصوصی)؛ **Telegram bot** یک‌طرفه، در container جدا از کریپتو (خط ۷۵).
- **سه قانون تغییرناپذیر Brushline INV-1/2/3** (خط ۱۰۳): بدون تأیید کاربر هیچ انتشار/خرج/پیام · داده در AU بماند · هر اتوماسیون = kill switch + سقف خرج + audit.

### معماری ساده MVP بات (بخش ۳–۴)
- ۵ فایل (خط ۲۰۳، ۳۷۷): `main.py، bot.py، db.py، .env، requirements.txt` + `langar_bot.service` (systemd).
- Stack: Python 3.11 / python-telegram-bot v21 (async) / SQLite / python-dotenv (خط ۲۹۴).
- Gate = flag در SQLite؛ Kill-switch = `/halt`/`/resume` فقط OWNER_ID؛ اصل «اول هر handler: if is_halted(): return» (خط ۲۴۵–۲۶۶).
- ۳ جدول SQLite: log، insight، config (خط ۲۱۶–۲۴۱).

---

## ۳) پرامپت‌های کلیدی (نقل‌قول کوتاه)

- **meta-orchestrator** (خط ۱۸): «`04-meta-orchestrator-prompt.md` … ده بخش ساختاریافته، شش HALT condition (H1–H6) با Wilson lower bound به‌عنوان یک hard decision procedure».
- **پرامپت گیت نه advisor** (خط ۳۳): «The prompt functions as a **gate**, not an advisor».
- **سبک تعامل کاربر** (خط ۳۹–۴۳): «Lead with the hardest challenge or broken assumption before offering any solution» · تگ‌های certainty `[Certain]/[Probable]/[Guess]` · «همیشه فارسی، کوتاه و مستقیم، بدون verbosity».
- **پرامپت کدنویس بات** (خط ۲۹۱–۳۰۸ و ۵۵۴–۵۷۶): «یک بات تلگرامِ شخصیِ single-user بساز. Stack: Python 3.11 / python-telegram-bot v21 … فقط OWNER_ID پاسخ می‌گیرد. اول هر handler: if is_halted(): return».
- **پرامپت red-team** (خط ۶۱۹–۶۲۲): «این معماری را بشکن … هیچ تعریفی. فقط حمله. اگر یک بخش درست است، سکوت؛ اگر شکننده است، بشکنش».
- **خط قرمز self-improvement** (خط ۸۳): «self-improvement فقط system-prompt نقش‌های داخلی را عوض می‌کند — هرگز policy gate، killswitch، IGK، secrets، یا مسیر مالی/کریپتو. هر نسخه git commit، هرگز مستقیم به main».
- **متاپرامپت Optimizer دو-تکه** (خط ۸۲): بخش A رویه‌ی راه‌اندازی (`python self_update.py <role>`، چک STOP، چک audit chain، سقف ۴ دور، commit اجباری)؛ بخش B متاپرامپت LIVE (bounded edit + دو-گیت + لیست FORBIDDEN).
- **اصول LANGAR** (خط ۵۴۲–۵۴۸): «gate قبل از هر پیام خروجی · Human-write-only برای verdict · kill-switch واقعی تست‌شده · همیشه RMSSD · در شک: سکوت».

---

## ۴) وضعیت پروژه‌ها هنگام export

### ساخته‌شده / کارکننده
- `04-meta-orchestrator-prompt.md` تولید شده (۱۰ بخش، H1–H6) (خط ۱۸).
- داشبورد بصری تعاملی معماری ساخته شده (خط ۱۹).
- **حلقه‌ی self-improvement کارکننده** در `fusion-mvp/`: نمره researcher ۰.۶→۰.۸→۱.۰ سپس explore→rollback خودکار؛ audit chain «سالم»، اجرای واقعی **تأییدشده** (خط ۸۰).
- Research Prompt Pack با ۲۰ لِین + Synthesis + Red-team اجرا شد (خط ۵۲).
- `SETUP_PROMPT.md` ساخته شد (build unified، ۴ کانتینر، ۷ تست پذیرش) (خط ۸۹).
- نقشه‌ی پژوهش قلب v3 (HTML) ساخته و commit شد؛ دستورالعمل سیستم ساده‌شد و commit شد (خط ۳۳۶–۳۳۸).
- Brushline: ساختار ۴۳ فایلی markdown آماده (۲.۶MB→۸۸KB) (خط ۱۰۵).

### ناقص / broken / منتظر
- **کد بات هنوز نوشته نشده** — فقط پرامپت آماده است (خط ۳۳۹، ۳۴۳).
- **VPS راه‌اندازی نشده** (خط ۳۴۰).
- ضعیف‌ترین حلقه: `evals.py` یک rubric کلیدواژه‌ای → خطر specification gaming (FM-10, T-14a)؛ رفع: gate دوم held-out از `igk/kernel.py::ground()` (خط ۸۱).
- گیت آمادگی Brushline (R11/R12) **باز** است؛ منتظر داده‌ی کاربر (margin، نرخ‌ها، توکن بات و…) (خط ۱۰۶).
- تصمیم کاربر: «همه چیز اول روی لپ‌تاپ setup شود» (نه VPS) (خط ۸۴).
- **bottleneck اصلی: cold-start ledger data** — نه کیفیت پرامپت (خط ۲۲، ۳۲).

### شکاف‌های خودِ export (خط ۱۱۳–۱۱۵)
فایل‌های کامل `langar/`، کد `fusion-mvp/`، `RESEARCH-PROMPT-PACK.md`، `ORCHESTRATOR-hybrid-system.md`، `MASTER-05-14-NORMALIZED.md`، ساختار ۴۳فایلی Brushline و `LANGAR-MASTER-EXPORT.md` (~۳۳۳KB، در فولدر دیگر) در این export نیستند — فقط عصاره‌شان آمده.

---

## ۵) تناقض‌های داخلی (earlier vs later در همین export)

1. **معماری enterprise-heavy در برابر MVP ساده** — بخش ۱–۲ (خط ۱۸–۲۱، ۱۰۲–۱۰۴) کل ماشین LANGAR/Fusion را با Wilson lower bound، hash-chain، execution rings، autonomy matrix توصیه می‌کند؛ اما بخش ۴ (خط ۳۶۰–۳۷۱) صریحاً همین‌ها را برای single-user بی‌فایده اعلام و حذف می‌کند («Wilson score ❌ HRV شخصی نیازی ندارد»، «Hash-chained ❌ تو تنها کاربری»، «Execution rings ❌ اضافه»، «FUSION ❌ نباید در v1 باشد»). red-team بخش ۵ (حمله #۵، خط ۷۱۹–۷۴۲) همین را «governance تئاتری برای یک نفر» می‌نامد. → **تناقض شدت-پیچیدگی بین بخش‌های اولیه و متأخر سند.**

2. **۱۵ جزء در برابر یک انسان** (حمله #۸، خط ۷۸۰–۸۰۴): معماری synthesis همه‌ی ۱۵ جزء (Postgres، pgvector، Mem0، DBOS، MCP gateway، OPA، Redis، OpenLLMetry، MLflow، cgroups، iptables، gVisor، LangGraph، Claude Agent SDK، SkillOpt) را تجویز می‌کند؛ red-team می‌گوید این تنها حمله‌ی «باطل‌کننده» است و پیشنهاد ~۵ جزء می‌دهد (خط ۸۴۸–۸۵۴). → تجویز معماری در برابر توصیه‌ی نهایی red-team.

3. **cold-start: «داده تولید کن بعد بساز» شکسته است** (حمله #۱، خط ۶۴۰–۶۵۷): بخش ۱ فاز ۰ را «داده تولید کن» می‌گذارد؛ red-team می‌گوید scoring پیش‌نیاز خودش است (وابستگی حلقوی) و بدون score-at-write فاز ۰ فقط log بی‌مصرف تولید می‌کند.

4. **ماینینگ اولین در برابر آخرین کاندیدای SkillOpt** (حمله #۲، خط ۶۶۱–۶۷۳): معماری ماینینگ (backtest P&L) را **اولین** کاندیدای SkillOpt گذاشت؛ red-team با نقل خودِ Lane 10 («SkillOpt وقتی مناسب است که verifier قطعی باشد») می‌گوید باید **آخرین** باشد.

5. **پارادوکس HARD_STOP مالی** (حمله #۳، خط ۶۷۷–۶۹۲): معماری هم ماینینگ tenant می‌خواهد هم همه‌ی financial actions را HARD_STOP می‌کند — این دو با هم نمی‌سازند.

6. **وابستگی Anthropic در برابر ادعای export-first/no-lock-in** (حمله #۶، خط ۷۴۶–۷۶۲): معماری «no vendor lock-in» ادعا می‌کند اما routing، prompt caching و orchestration کاملاً Anthropic است؛ و شاهد خودِ Lane 7 که Anthropic دسترسی Fable 5/Mythos 5 را در ۱۲ ژوئن ۲۰۲۶ قطع کرد، فرض «Anthropic زیرساخت قابل‌اعتماد» را رد می‌کند.

7. **تصحیح علمی Kaduk 2025 (نسخه‌ی قبل در برابر بعد)** (خط ۹۵، ۱۶۷، ۱۲۹۹–۱۳۰۰، ۱۱۷۷): ادعای قدیمی «غذا/بار کالری روی عصب واگ اثر می‌گذارد و HRV را کم می‌کند» غلط بود؛ یافته‌ی واقعی: خودِ دستگاه taVNS مستقل از کالری HRV را کاهش داد (milkshake بی‌اثر). → تناقض بین فرض اولیه‌ی درون پروژه و تصحیح v2/v3.

8. **HRVB برای اضطراب: g≈0.83 در برابر null** (v2 خط ۱۳۲۵–۱۳۲۷ در برابر v3 خط ۱۶۶، ۱۱۵۲): نسخه‌ی قدیمی اثر بزرگ (g≈0.83) گزارش کرده بود؛ متاآنالیز ۲۰۲۵ راه‌دور آن را برای اضطراب/استرس null اعلام و به [S] تنزل داد (برای افسردگی g=−۰.۴۱، برای HRV g=+۰.۴۴ معنادار ماند).

9. **تناقضِ ادعایی که خودِ Memory حل‌شده می‌داند** (خط ۳۵): «LANGAR's no-self-improvement و Fusion Phase 3 تناقض نیستند — با sequential unlocking حل می‌شوند». (ذکر شده به‌عنوان تناقضِ ظاهریِ رفع‌شده، نه باز.)

---

## ۶) اعداد مهم (costs / budgets / thresholds / models)

- **مدل‌ها**: Haiku / Sonnet / Opus (routing، خط ۷۵۳)؛ **Claude Sonnet 4.6** (امضای HANDOFF، خط ۳۴۸)؛ **Gemini Pro** (cross-model judge، خط ۷۷۴)؛ **Fable 5** و **Mythos 5** (دسترسی قطع‌شده توسط Anthropic).
- **تاریخ قطع دسترسی**: ۱۲ ژوئن ۲۰۲۶ (Fable 5 / Mythos 5، export-control) (خط ۶۳۴، ۷۵۸).
- **VPS**: ~۴–۶ دلار/ماه (Hetzner CX11 / DigitalOcean Droplet، Ubuntu 22.04، Python 3.11) (خط ۳۱۵، ۴۹۳).
- **تخمین build**: ~۳–۵ ماه part-time (خط ۵۹).
- **self-improvement**: نمره researcher ۰.۶ → ۰.۸ → ۱.۰؛ سقف **۴ دور** (خط ۸۰، ۸۲).
- **prompt caching**: تا **۹۰٪** صرفه‌جویی (لِوِر اصلی Anthropic-specific) (خط ۷۵۴)؛ در جای دیگر red-team «۸۰٪ صرفه‌جویی» ذکر شده (خط ۷۶۲).
- **سناریوی cold-start**: ~۵٬۰۰۰ row در LANGAR؛ ۵۰+ trajectory per project، سه tenant = ۱۵۰+ trajectory دستی (خط ۶۵۳).
- **anchor set cross-model judge**: ~۵۰ case دوره‌ای (خط ۷۷۶).
- **آستانه‌ها**: Wilson lower bound (تصمیم HALT)؛ آستانه‌ی حداقل داده N قبل از اعلام score معتبر (زیر N → «insufficient data») (خط ۸۱۶–۸۱۸).
- **تحقیق**: ۹ tension (T1–T9)، ۷ claim (C1–C7)، ~۱۵ blind spot (خط ۵۸).
- **Brushline**: ۱۲ نقش agent؛ ۴۳ فایل markdown؛ کاهش ۲.۶MB → ۸۸KB (خط ۱۰۴–۱۰۵).
- **معماری synthesis**: ~۱۵ جزء در برابر ~۵ جزء پیشنهادی red-team (خط ۷۸۴، ۸۴۴).
- **قلب/علمی**: THC dose-dependent HR↑/HF-HRV↓؛ HRVB افسردگی g=−۰.۴۱، HRV g=+۰.۴۴، BPD HRV g=−۰.۵۹؛ interoception شمارش ضربان r≈.۱۶؛ تنفس رزونانس ۶ نفس/دقیقه (دم ۵ + بازدم ۵ ثانیه)؛ RMSSD نمونه: میانگین ۴۲.۳ ms، بهترین ۵۸، ضعیف‌ترین ۳۱، همبستگی خواب-RMSSD +۰.۶۸ (خط ۴۷۸–۴۸۱، ۱۱۳۵–۱۱۶۲).
- **منابع کلیدی**: Kaduk et al. 2025 (Psychophysiology)، Ferentzi 2025، Microsoft Agent Governance Toolkit، Stanford CodeX، MintMCP 2026، OWASP Agentic AI Top 10 (خط ۶۰، ۶۰۹).

---

*پایان اینونتوری — منبع READ-ONLY، هیچ فایل vault تغییر نکرد.*
# Inventory — LANGAR-MASTER-EXPORT.md

منبع: `C:\Users\Armin\Desktop\backup\04 - Architect System\architect\03-Exports\LANGAR-MASTER-EXPORT.md` (۳۷۶۴ خط، ~۳۳۳KB)
تاریخ export: **2026-07-02** (خط 3). تاریخ ساخت ده لِین تحقیق: **2026-07-01**. آپلود لِین‌های 05–14 به پروژه: ~2026-07-01 (خط 169).

---

## ۱. ساختار سند

| بخش | خطوط | محتوا |
|---|---|---|
| Header + فهرست | 1–12 | عنوان «پروژه‌ی معماری قالب»، تاریخ export، فهرست ۴ بخش |
| **بخش ۱ — Memory** | 14–173 | Project memory تجمیعی (18–76)، `user-profile.md` (78–92)، `langar-project.md` (94–116)، `langar-findings.md` (119–152)، `research-pack-status.md` (154–172) |
| **بخش ۲ — ده لِین تحقیق (verbatim)** | 176–3466 | Lane 05 Shared Engineering (180–350) · Lane 06 Memory (355–584) · Lane 07 Self-improvement ⚠️Frontier (589–854) · Lane 08 Tool/interop (859–1120) · Lane 09 Eval/observability (1125–1450) · Lane 10 Safety/governance ⚠️ (1455–1878) · Lane 11 Cost/routing (1883–2299) · Lane 12 Failure modes (2304–2680) · Lane 13 Frameworks (2685–3068) · Lane 14 Theoretical foundations (3073–3466) |
| **بخش ۳ — استخراج ۱۱ session چت** | 3471–3702 | 3.1 شروع (3475) · 3.2 پک تحقیق (3482) · 3.3 آپلود لِین‌ها (3488) · 3.4 Synthesis & Red-Team (3493) · 3.5 Blueprint/architecture (3561) · 3.6 build واقعی langar+langar-pro (3568) · 3.7 کشف fusion-mvp (3580) · 3.8 پرامپت‌های عملیاتی self-improvement (3588) · 3.9 اجرای fail-closed (3670) · 3.10 Brushline (3676) · 3.11 فایل‌های خارج از export (3686) · 3.12 تصمیم‌های باز (3694) |
| **بخش ۴ — Project Instructions (verbatim)** | 3705–3764 | نقش، context قفل‌شده، قوانین رفتاری، ۱۰ خط قرمز، تنش‌های باز، build order، «چه نساز» |

هر لِین ساختار ۸ سرفصلی ثابت دارد: Summary / Landscape / Comparison table / Blind spots / Recommendation / TOOLING / If-I'm-wrong / Confidence + Claims table.

---

## ۲. تصمیم‌های معماری langar (با ارجاع خط)

### 2.1 معماری کلان و لایه‌ها
- سیستم سه‌بخشی اولیه (session 3.1، خط 3478): **LANGAR** (مغز ناظر: دفترچه append-only غیرقابل‌پاک + تشخیص دستکاری + `/halt` kill-switch) · **NEURO** (ثبت HRV/RMSSD، فقط آینه) · **FUSION** (نوشتن خلاق با برچسب قطعی/حدس/استعاره). Telegram = درِ ورودی (3479).
- ۴ tenant ناهمگون روی یک VPS مشترک: مالی/حسابداری (ATO/GST/BAS)، ماینینگ کریپتو، مارکتینگ، دفترچه شخصی PII (خطوط 89، 3716).
- تصمیم‌های قفل‌شده (Project memory، خطوط 30–38): یک Postgres واحد برای همه (LANGAR ledger + pgvector + MLflow + policy table + DBOS state)؛ OpenLLMetry+MLflow به‌جای Langfuse (ریسک acquisition توسط ClickHouse — خطوط 1139، 1233)؛ MCP gateway = تنها chokepoint اقدام بیرونی؛ Redis fail-closed kill switch با تست ماهانه؛ Raw Python پیش‌فرض + Claude Agent SDK برای skill/subagent + LangGraph برای branching؛ routing ~70% Haiku / ~25% Sonnet / ~5% Opus با prompt caching؛ SkillOpt فقط Level A با gate ≥50 trajectory و judge بین‌مدلی (Gemini برای Claude).
- Build order / DAG (خطوط 107، 3751–3756): Layer 0 = **Lane 13 tenancy + Lane 14 secrets** (نه orchestration!) → event log → policy/audit gate (4-way join مرکزی) → durable+scheduling → context/memory/RAG → approval UX + eval + cost → PromptOps + **self-improvement آخر**. Phase 0–1 غیرقابل‌defer. تخمین ~۳–۵ ماه part-time.
- Durable execution: **DBOS روی همان Postgres، نه Temporal** (خطوط 135، 195، 265، 3746). هر LLM/tool call در step ژورنال‌شده wrap شود (تله replay، خط 244).
- Isolation: cgroups v2/systemd slices برای contention؛ gVisor/E2B فقط اگر کد untrusted اجرا می‌شود؛ Firecracker روی VPS اجاره‌ای نساز (196، 246، 267، 278).

### 2.2 Memory architecture (Lane 06)
- تاکسونومی چهارگانه CoALA: working / **episodic** / semantic / procedural (383–390). تاکسونومی جایگزین ۲۰۲۵: Factual/Experiential/Working (390).
- تصمیم سه‌مرحله‌ای (489–507): **مرحله ۱ (الان): همان Postgres + pgvector + Mem0 OSS**، isolation با `user_id = project_name`، schema-per-project، CLAUDE.md per-project برای declarative/procedural memory. **مرحله ۲** (فقط اگر temporal reasoning لازم شد): Graphiti + FalkorDB. **مرحله ۳** (فقط agentهای چند‌روزه): Letta — با آگاهی از framework lock-in.
- **Hybrid**: الگوی multi-strategy روی Postgres (Hindsight-like: pgvector + graph tables + temporal indexes) به‌عنوان «اگر export-first را مطلق بگیری» مطرح ولی «الان زودتر از موعد» (406، 545).
- Episodic verbatim برای tenant دفترچه شخصی — extraction pipeline عمداً اطلاعات را از دست می‌دهد (475، 516).
- Context overflow cascade سه‌مرحله‌ای: compress tool-output → sliding window → LLM summarization آخرین راه‌حل (377، 410–419، 495).
- ممنوع: memory stack مشترک بین tenantها، Zep (CE مرده/Cloud lock-in)، Neo4j self-host، MemPalace در production مالی (509–518)؛ در خطوط قرمز: «هیچ global memory / shared vector index» (3735).
- **Reflection** به‌معنای معماری memory جدا در این export نیست؛ «reflection» فقط به‌شکل Level A self-critique در Lane 07 (623–638، 739) و minibatch reflection در SkillOpt (3119) آمده.

### 2.3 حلقه‌ی self-improvement (Lane 07 + 14 + sessionهای 3.7/3.8)
> **نکته: عبارت «ACE loop» هیچ‌جای این export نیامده.** نزدیک‌ترین معادل، حلقه‌ی `self_update.py` در fusion-mvp و loop مفهومی SkillOpt (rollout → reflect → bounded edits → validation gate → commit/reject، خطوط 3121–3132) است.
- سه سطح: **A** in-context/skill edits (مجاز، فوری) · **B** skill-library/scaffold با gate (buildable) · **C** weight-update (**خط قرمز — نه**) (605–613، 735، 3088).
- Gate اجباری سه‌شرطی (1367–1371): `regression ≤ 5%` روی anchor set + `target metric بهتر` + `new_failure_categories == 0` — از نظر نظری = «two-gate policy» از Wang et al. (utility + learnability؛ 3196، 3300–3301، 3372–3379).
- Skill: compact 300–2000 توکن، inspectable، git-versioned، rollback با revert (609، 751، 1616–1619).
- آستانه‌های داده: ≥20 scored trajectory per skill (جدول 3330) / ≥50 per project برای شروع SkillOpt loop / ≥200 برای Level B (3383). Cold-start = محدودیت بنیادی نظری، نه bug (3298، 3307، 3350).
- **fusion-mvp واقعاً اجرا و verify شد** (3583): نمره researcher ‏0.6→0.8→1.0 نگه‌داشته، explore→0.8 → **rollback خودکار**، audit chain «سالم».
- خط قرمز self-improvement (3585): فقط system-prompt نقش‌های داخلی — هرگز policy gate/killswitch/IGK/secrets/مسیر مالی-کریپتو. هر نسخه git commit، PR با human merge نه مستقیم به main (3738).
- ضعف شناسایی‌شده [Certain]: `score_prompt` در `evals.py` rubric کلیدواژه‌ای است → خطر specification gaming (FM-10)؛ راه‌حل: gate دوم held-out از `igk/kernel.py::ground()` (3584).
- سقف: `config.MAX_UPDATE_ROUNDS = 4` دور در هر اجرا (3612)؛ early-stopping بعد از ۳ دور بدون پیشرفت؛ escalate اگر ۳ بار پشت‌سرهم گاردریل خورد (3616–3620).

### 2.4 Router / BrainRouter
> **عبارت «BrainRouter» در export نیامده**؛ اجزای مرتبط: فایل `BRAIN_PROMPT` در langar/ (112، 3689)، `brain.py` در langar-pro (خارج از export)، «Task Router» (281)، «deterministic semantic router» در الگوی Agent Control Plane (213).
- Model routing (Lane 11): rule-based classifier (keyword/regex، latency <1ms — **نه LLM classifier**، 2091–2104، 2228): simple→`claude-haiku-4-5-20251001`، medium→`claude-sonnet-4-6`، complex→`claude-opus-4-8`، batch/async→DeepSeek V4 Flash یا Gemini Flash (2080–2088).
- توزیع هدف: ۷۰٪ Haiku / ۲۵٪ Sonnet / ۵٪ Opus → ۴۵–۶۰٪ کاهش bill (2198–2202)؛ شروع محتاطانه ۵۰/۵۰ و ارتقا با eval (2259).
- Prompt caching (۹۰٪ تخفیف cached input) = بالاترین ROI؛ Batch API (۵۰٪) برای async (1901، 1928–1931، 2177–2206).

### 2.5 Agents
- Claude Agent SDK: subagents + SKILL.md progressive disclosure + hooks + sessions + deepest MCP — ولی **proprietary license** و Claude-only (2763–2783)؛ تصمیم سه‌مرحله‌ای Lane 13 (2977–2994): raw API → Claude Agent SDK → LangGraph فقط برای branching/checkpoint. CrewAI نساز (3× token overhead، 2998).
- fusion-mvp سه نقش: **researcher / analyst / supervisor** (3604، 3662–3664).
- Brushline (مصرف‌کننده‌ی معماری langar، 3676–3684): Orchestrator + ۱۲ نقش agent؛ سه دروازه (Gate قانونی AU → تأیید انسانی تلگرام با تایمر ۱۵ دقیقه → Audit hash-chained)؛ اصل «integrate, don't duplicate» (ServiceM8/Tradify).

### 2.6 Constitution / خطوط قرمز (بخش ۴ + C1–C7)
- ۷ claim load-bearing C1–C7 (140–147): event log append-only hash-chained؛ idempotency؛ secrets هرگز در context/log/RAG؛ **یک** policy gate برای همه‌ی real-money/irreversible؛ prompt/policy/config = کدِ versioned؛ hard tenant isolation؛ harness قطعی دور reasoning غیرقطعی.
- ۱۰ خط قرمز غیرقابل‌مذاکره (3729–3742): هیچ private key روی VPS (امضا با hardware wallet انسانی)؛ هیچ اقدام irreversible خودمختار (پول/BAS lodgement)؛ جداسازی سخت per-tenant در data+secret+network+vector+log+tool؛ egress proxy اجباری با payload logging + PII scan؛ log زیر سطح privilege agent؛ همه‌چیز در git با eval gate؛ RAG/browser/email = untrusted و هرگز authorize نمی‌کند؛ cost معماری دارد (cap + circuit breaker + **DENY on timeout**)؛ ریاضی GST/BAS خارج از LLM + «refuse rather than guess»؛ backup رمزشده + کلید off-VPS + plan برای bus-factor=1.
- ماتریس autonomy چهارسطحی (1502–1527): AUTONOMOUS / IN-FORM / APPROVE_FIRST / HARD_STOP؛ قانون ترکیب `final = max(autonomy_floor, safety_result)` (1513)؛ FINANCIAL برای ماینینگ = HARD_STOP؛ DATA_READ پروژه‌ی دیگر = HARD_STOP؛ SKILL_MODIFICATION = APPROVE_FIRST.

### 2.7 Safety / rollback
- Kill switch: out-of-process، deterministic، **tested ماهانه**، authenticated، audited (1544–1550)؛ پیاده‌سازی Redis flag `global:kill_switch` + `kill:{tenant_id}` در gateway middleware (1552–1562، 1722–1737)؛ fail-closed اگر policy engine unreachable (1829)؛ در fusion-mvp: فایل `logs/STOP` (touch/rm، fail-closed؛ 3666–3667). KILLSWITCH.md convention (1538).
- Circuit breaker و dead-man switch جدا از kill switch (1534–1536)؛ dead-man برای financial: approval token با TTL (1575–1579).
- Budget caps سه‌گانه (1570–1573): per-action + per-run + daily؛ نمونه: DAILY mining $50 / research $20؛ RUN mining $5 / research $2 (1746–1747).
- Policy: allowlist table در Postgres به‌جای OPA برای ≤5 tenant (1703–1718، 3760)؛ schema: `action_policy(tenant_id, domain, max_amount, requires_approval, hard_stop)` (1706–1712).
- Rollback: هر self-modification در git، commit message اجباری، **Rollback SLA <۵ دقیقه** (1767–1769)؛ A-MemGuard: dual-memory working/validated با consensus validation (1621، 1770).
- Network egress allowlist با iptables per-uid (1774–1783)؛ NVIDIA 3 controls (1586–1589).
- دفاع‌های failure-mode (Lane 12): max-retry=3 → HARD_STOP (2372، 2605)؛ pipeline >۵ step بدون checkpoint ممنوع (2352، 2582)؛ pinned constraints خارج از context (در gateway/OPA) چون compaction آن‌ها را می‌کشد (2561، 2607)؛ cross-model validation (Gemini) برای تصمیم‌های مالی نهایی (2512، 2632)؛ external content در بلاک `<external_data>` (2591).

---

## ۳. پرامپت‌های کلیدی (نقل‌قول کوتاه)

1. **Organizer/Normalizer** (3499–3522): «نقش: تو یک Knowledge Architect هستی… قوانین آهنین: ۱. هیچ عدد، آستانه… را خلاصه یا حذف نکن — همه را verbatim نگه دار… ۳. تناقض‌ها را حل نکن — flag کن… خروجی را دقیقاً در این ۸ بخش سازمان بده: A. Master Index… H. Open Items + Decision Log.»
2. **Self-prompt / handoff** (3526–3559): «تو در Cowork داری روی پروژه‌ی معماری قالب (agi) کار می‌کنی… هدف کلان: یک سیستم agentی همیشه‌روشن long-running و امن (کدنام: langar)… سبک request-architect: اول ضعیف‌ترین فرض/شکاف را نام ببر… تگ [Certain]/[Probable]/[Guess]… خطر شماره‌۱: مجاورت کلید کریپتو با LLM… Build order: Phase 0…»
3. **پرامپت عملیاتی حلقه‌ی self-improvement (بخش A، 3592–3627)**: «نقش تو: اپراتورِ ایمنِ حلقه‌ی self-improvement سیستم fusion-mvp… تو خودت پرامپت را مستقیم ویرایش نمی‌کنی… پیش‌شرط‌ها: فایلِ logs/STOP وجود نداشته باشد… audit chain سالم باشد… روی branch گیت جدا… gate دوم (اجباری، دستی…): خروجی نمونه را با held-out بسنج (igk grounding)… سقف: بیش از MAX_UPDATE_ROUNDS (=۴) نرو… هرگز: FORBIDDEN_IN_PROMPT را دور نزن، STOP را حذف نکن، gate را شل نکن… eval را برای pass-کردن تغییر نده.»
4. **متاپرامپت Optimizer حالت LIVE (بخش B، 3631–3654)**: «تو Optimizer یک سیستمِ multi-agent هستی… یک نسخه‌ی بهترِ همان پرامپت بنویس — نه یک پرامپتِ نو. قیدهای سخت: نقش‌مارکر بماند؛ طول ۲۰–۲۰۰۰ کاراکتر؛ FORBIDDEN_IN_PROMPT ظاهر نشود… اصلِ bounded edit: فقط یک تغییرِ کوچک… دو-گیت: gate ۱ (utility)… gate ۲ (no regression)… خروجی: فقط متنِ کاملِ پرامپتِ جدید.»
5. **Project Instructions (بخش ۴، 3709–3760)**: «معمار و مشاورِ ارشدِ سیستمِ langar… تو یک دستیارِ مطیع نیستی؛ یک architect بدبینی که blast-radius را قبل از قابلیت می‌بیند. هدف: بیشترین leverage با کمترین blast radius — نه بیشترین autonomy… تناقض‌ها را flag کن، حل نکن… اعداد و آستانه‌ها را verbatim نگه دار.»
6. **SETUP_PROMPT.md** (توصیف، 3576): مرحله ۰ بررسی → ۱ ساخت `.env`/`.gitignore` → ۲ `docker compose -f docker-compose.unified.yml up -d --build` → ۳ هفت تست پذیرش (سلامت بک‌اند، /start /menu، kill-switch، /research به pro، fallback با خاموشی api، AI-Lab، پایداری بعد از restart) → ۴ اجرای ۲۴ساعته + بکاپ.

---

## ۴. وضعیت در لحظه‌ی export (2026-07-02)

**ساخته‌شده و verify‌شده (working):**
- فاز تحقیق «عملاً بسته» (خط 28): ۲۰ لِین + Synthesis (فایل 15) + Red-team (فایل 16) + پاسخ پنل Claude/GPT/Gemini.
- **fusion-mvp self-improvement loop اجرا و verify شد** (3583): بهبود نمره، rollback خودکار، audit chain سالم، kill-switch فایل STOP کار می‌کند (session 3.9: fail-closed درست عمل کرد — بدون کد، صفر دور، 3672).
- Build خروجی langar/langar-pro (session 3.6): `pro_client.py` (سه حالت fallback تست‌شده)، سیم‌کشی `/research` در bot.py، `docker-compose.unified.yml` (چهار سرویس bot+api+db+redis، image `pgvector/pgvector:pg15`، شبکه `langar-net`، healthcheck)، `.env.example`، `SETUP_PROMPT.md`.
- `MASTER-05-14-NORMALIZED.md` با ۷ تناقض بین‌لِینی (T-A تا T-G) flag‌شده (3564).
- Brushline: ساختار ۴۳ فایل markdown/88KB تمیز شد؛ ۲۲ فایل تکراری (2.6MB) حذف (3682).

**ساخته ولی اجرانشده (untested):**
- استقرار ۴ کانتینری در sandbox اجرا نشد — «آزمون نهایی روی لپ‌تاپ کاربر» (3578).

**Broken / ضعف فعال:**
- `score_prompt` rubric کلیدواژه‌ای → خطر specification gaming [Certain] (3584).
- Cross-session file access friction (41)؛ Cowork نمی‌تواند مستقیم به Project knowledge بنویسد (3491).

**TODO / باز (3694–3701):**
1. کریپتو: container-isolation روی VPS یا کاملاً off-box؟ (موضع پیشنهادی: off-box؛ تأییدنشده — 3566)
2. استقرار اولیه: **لپ‌تاپ** (تصمیم کاربر: «می‌خوام همه‌چی اول رو لپ‌تاپ ستاپ بشه»، 3673) → بعداً VPS.
3. SkillOpt cold-start + ارتقای `held_out.json` به caseهای واقعی + unseen set (3586، 3698).
4. GitHub repo هنوز ساخته/وصل نشده (3699).
5. **HARD_STOP paradox** مرزهای autonomy مالی — حل‌نشده (red-team؛ 51، 3700).
6. Pivot بالقوه: redesign حداقلی **۵ مؤلفه** در برابر ۱۵ moving part (red-team؛ 53، 3701).
7. گیت آمادگی Brushline (R11/R12): سه عدد اقتصادی + CONFIG + تأیید حقوقی NSW باز است (3683).

---

## ۵. تناقض‌های داخلی (flagged، طبق قانون خود سند: حل نکن)

1. **«gateway بساز» vs «فعلاً هیچ‌چیز نساز»** — Lane 05 Summary: بالاترین ROI = MCP gateway chokepoint (194، 261) ولی If-I'm-wrong همان لِین: «الان تقریباً هیچ مهندسی مشترکی نساز… gateway را نساز تا ≥N action واقعی/روز روی ≥۲ tenant» (193، 308). گلوگاه واقعی = cold-start ledger data نه زیرساخت.
2. **بودجه $500/ماه، یک عدد دو معنا** — Lane 11 آن را معقول، Lane 10 آن را «خط فاجعه‌ی recursive-loop» می‌داند (1568، 1864، 3749).
3. **Durable engine** — پنل: Temporal vs RQ/Celery vs «LangGraph checkpointing کافی است»؛ judge: LangGraph ≠ durable، DBOS نقطه شیرین (149، 3746) — ولی مشروط به single-box ماندن (312).
4. **VPS اشتراکی vs bare-metal/off-box برای کریپتو** — Gemini: bare-metal (side-channel hypervisor)؛ بقیه: VPS با keys-off-box (149، 3747)؛ در session 3.5 موضع off-box پیشنهاد ولی «هنوز باز» (3566، 3696).
5. **الگوی approval** — callback/suspend-and-die (Gemini) vs tier با DENY-on-timeout (Opus) — «هر دو معتبر» (3748).
6. **نسخه‌ی Haiku ناسازگار** — جدول قیمت: «Claude Haiku 3.5 ($0.80/$4)» (1919، 2114) ولی کد routing: `claude-haiku-4-5-20251001` (1994) و خبر suspension: «Haiku 4.5 تأثیر نگرفت» (1905).
7. **نسبت routing** — Project memory و Lane 11 Recommendation: 70/25/5 (36، 2198–2200)؛ محاسبه و claim همان لِین: 70/20/10 (1965–1966، 2006)؛ If-I'm-wrong: شروع 50/50 (2259).
8. **آستانه‌ی trajectory** — memory: gate روی ≥50 scored trajectory per project (37)؛ جدول Lane 14: ≥20 per skill برای Level A (3330)؛ متن Lane 14: ≥50 per project برای SkillOpt loop و ≥200 برای Level B (3383).
9. **OPA** — Lane 05: policy gate = OPA (262)؛ Lane 10 و Project Instructions: OPA برای ≤5 tenant over-engineering است، allowlist table کافی (1703، 1790، 3760).
10. **Claude Agent SDK vs export-first** — توصیه‌ی اصلی برای Cowork-centric stack است (2701، 2914) ولی proprietary license «با ارزش export-first تو conflict دارد» (2951، 3026)؛ lock-in score 8 (3011).
11. **eval rotation** — Lane 12 FM-5/FM-10: «eval suite را rotate کن» (2442، 2526) vs If-I'm-wrong همان لِین: «golden anchor ثابت باشد (۳۰ case)، rotate نکن، grow کن» (2643). (عدد ۳۰ هم با anchor 50–100 در Lane 09 نمی‌خواند.)
12. **Telegram bot co-location** — تصمیم «Telegram برای اپراتور» ولی هم‌مکانی bot token با کلید کریپتو ناقض Lane 14 — ریسک flag شده (3565).
13. **مقصد استقرار** — کل تحقیق حول VPS مشترک قفل شده (CONSTRAINTS هر لِین) ولی تصمیم نهایی کاربر: اول لپ‌تاپ (3673، 3697).
14. **غیاب اصطلاحات**: «ACE loop» و «BrainRouter» هیچ‌جا در این export نیستند (اگر در فایل‌های دیگر vault هستند، این سند آن‌ها را cover نمی‌کند؛ نزدیک‌ترین‌ها: حلقه‌ی self_update/SkillOpt و BRAIN_PROMPT/Task Router).

---

## ۶. اعداد مهم

**مدل‌ها و قیمت (ژوئن ۲۰۲۶، خطوط 1915–1933):** Opus 4.8 = $5/$25، 1M ctx، SWE-bench 88.6٪ · Sonnet 4.6 = $3/$15 · Haiku 3.5 = $0.80/$4 · DeepSeek V4 Flash = $0.14/$0.28 · Gemini 3.1 Pro = $2/$12 (2M ctx) · Gemini Flash = $0.10–0.15/$0.40–0.60 · GPT-4.1 Nano $0.10/$0.40 · MiniMax M3 $0.60/$2.40 (SWE 80.5٪). **Claude Fable 5 + Mythos 5 از 2026-06-12 suspend (export control)** (39، 1905، 2287). Prompt caching ۹۰٪ تخفیف؛ Batch ۵۰٪؛ استک هر دو → ۲۵٪ نرخ استاندارد (1928–1931). Tokenizer 4.7+ تا ۳۵٪ توکن بیشتر (1933).

**بودجه/هزینه:** نمونه‌ی محاسبه: 100 run/روز روی Sonnet ≈ $480/ماه (1962)؛ routing 70/25/5 → ۴۵–۶۰٪ کاهش (2202)؛ caps: mining $50/day + $5/run؛ research $20/day + $2/run (1746–1747)؛ خط $500/ماه (1568)؛ break-even self-host: <50M tok/ماه → API؛ vLLM vs DeepSeek ~800M (2049–2057)؛ Ollama CPU 7B = ۵–۱۰ tok/s (2055).

**Eval:** anchor set 50–100 (15–20 per tenant)؛ ≥500 برای aggregate؛ ≥200 برای trajectory (1205، 1361)؛ regression threshold ≤5٪؛ Cohen's kappa ≥0.7 (نمونه‌ی شکست: 0.31)؛ sample rate 5–20٪ + 100٪ خطاها؛ judge از خانواده‌ی متفاوت (1145، 1185–1192).

**Self-improvement:** skill = 300–2000 توکن؛ SkillOpt: +23.5 GPT-5.5 / +24.8 Codex / +19.1 Claude Code، 52/52 best-or-tied (3231–3235)؛ edit budget = 8 (3124)؛ MAX_UPDATE_ROUNDS=4؛ طول پرامپت optimizer 20–2000 کاراکتر؛ ≥20/50/200 trajectory (سطوح)؛ نمره‌های fusion-mvp: 0.6→0.8→1.0، rollback از 0.8.

**Failure math (Lane 12):** 0.95^20 = 36٪ موفقیت؛ APEX: فقط ۲۴٪ موفق در attempt اول؛ Gartner: ۷۸٪ شکست pilot؛ MAST: spec 41.77٪ / coord 36.94٪ / verification 21.30٪؛ tool misuse = ۳۱٪ خطاهای production؛ scope creep + data quality = ۶۱٪؛ ۲٪ context loss per step؛ pass@1 = ۲۰–۴۰٪ overestimate؛ max-retry = 3.

**MCP/امنیت:** context bloat 72٪ (143k/200k)؛ Tool Search −۸۵٪ توکن؛ code-exec 150k→2k (−98.7٪)؛ MCPTox: o1-mini 72.8٪ آسیب‌پذیر، Claude 3.7 Sonnet <۳٪ رد کرد؛ CVE-2025-68143/44/45 (Git MCP server)؛ n8n CVE-2026-25049 (CVSS 10.0)؛ OpenClaw ۲۱٬۰۰۰+ نمونه؛ 26/428 router آلوده، یک wallet $500K تخلیه (2384)؛ اسپک MCP پایدار = **2025-11-25**، RC = 2026-07-28.

**Memory benchmarks:** LongMemEval: Hindsight 91.4٪ / Zep 63.8٪ / Mem0 49.0٪؛ MemPalace 96.6٪ R@5 (v3.4.0)؛ Letta plain-filesystem 74٪؛ LoCoMo dispute: 84٪→58.44٪→75.14٪؛ pgvector کافی تا <50M vector؛ Mem0 Pro (graph) $249/ماه.

**Frameworks:** انتخاب scaffold تا ۳۰ امتیاز benchmark (64.9٪ vs 57.6٪)؛ LangGraph 120ms/node vs CrewAI 450ms/transition و 3× token overhead؛ LangGraph 30–47٪ ارزان‌تر؛ Claude Agent SDK metering جدا از 2026-06-15.

**Schema/infra:** `action_policy(tenant_id, domain, max_amount, requires_approval, hard_stop)`؛ Redis keys: `global:kill_switch`, `kill:{tenant_id}`؛ فایل `logs/STOP`؛ docker: bot+api+db+redis روی `langar-net`، db = `pgvector/pgvector:pg15`؛ ProClient timeout ۸s؛ rollback SLA <۵ دقیقه؛ log retention ≥۶ ماه (EU AI Act Art. 26)؛ EU AI Act اجرای high-risk: **2026-08-02** (جریمه تا 15M EUR / 3٪ turnover)؛ cgroups نمونه: research 25٪/4G، mining 20٪/3G، accounting 15٪/2G؛ افق پروژه ۳–۵ ماه part-time؛ Brushline: تایمر approve ۱۵ دقیقه، ۱۲ نقش، ۳ invariant.
# اینونتوری فایل architect-chat-export.md

**فایل مبدأ:** `C:\Users\Armin\Desktop\backup\04 - Architect System\architect\03-Exports\architect-chat-export.md`
**حجم:** 7088 خط، ~321KB، 81 پیام
**ماهیت:** چت طراحی سیستم مادر-لایه «architect» (لایه‌ی مادرِ ناظر بر زیرپروژه‌ها)
**زبان چت:** فارسی + اصطلاحات فنی انگلیسی

> **هشدار مهم درباره‌ی ماهیت سند:** این export یک «چت مادر» است که در طول ~۱ سال (۲۰۲۵-۰۷ تا ۲۰۲۶-۰۷) شکل گرفته. سند در واقع یک مکالمه‌ی واحد نیست؛ بلکه رد پای تکامل فکری کاربر (Armin) از یک رؤیای اسطوره‌ای/فلسفی (Techno-Shaman, AGI Seed, کلونی‌های دیجیتال) به سمت یک معماری مهندسی‌شده و محتاطانه (LANGAR + AI-Lab) است. بیشتر پیام‌ها خروجی مدل‌های زبانی مختلف (ChatGPT/DeepSeek/Claude/…) در نقش «معمار» هستند. «architect» در اینجا نامِ نقش/سیستم مادر است، نه یک ماژول واحد.

---

## ۱. ساختار سند (message flow + تاریخ‌ها)

سند بر اساس تاریخ گروه‌بندی شده. جریان روایی از فلسفه به مهندسی حرکت می‌کند:

| تاریخ | خطوط | محتوای اصلی | فاز |
|---|---|---|---|
| **2025-07-11** | 6–132 | «مانیفست تمدنی» / هستهٔ وجودی (Identity Kernel)، Techno-Shaman، حلقهٔ هسته، چرخهٔ خودزایش، خطوط قرمز | فاز اسطوره‌ای/فلسفی |
| **2025-07-13** | 135–202 | پلن آموزشی ۶ ماهه (دیجیتال‌مارکتینگ، AI، پرامپت، مقیاس‌پذیری) + ۱۰ دوره منتخب | آموزشی |
| **2025-07-16** | 205–815 | **AGI Seed (V1.3)** — معماری AGI ماژولار روی Raspberry Pi؛ Docker/Ollama/Whisper/LangChain؛ ماتریس استخراج داده ۵ لایه (IDEM) | فاز AGI اولیه |
| **2025-07-17** | 818–1007 | نقشهٔ کامل «هوش مرکزی روی لپ‌تاپ» — فول‌آفلاین، رمزنگاری‌شده، ChromaDB + FastAPI + Ollama | فاز لپ‌تاپ-مرکزی |
| **2025-07-18** | 1009–1610 | زنجیرهٔ Leonardo→ESP32→Pi؛ حافظهٔ معنایی/برداری؛ **قانون اساسی کلونی AGI** (۶ اصل)؛ معماری ۵-AI روی لپ‌تاپ | فاز کلونی + حکمرانی |
| **2025-07-20** | 1613–2956 | ۷ لایهٔ روان‌شناسی دیجیتال؛ امنیت لوکال (Docker/SQLite)؛ سه کلونی متخصص؛ ساختار فولدر `meta_colony/`؛ **ایدهٔ DeepSeek در رأس هرم + کنترل از طریق تلگرام**؛ pipeline خودکار RAG+LoRA | فاز کلونی پیشرفته |
| **2025-07-22** | 2959–3141 | معماری «حافظهٔ جمعی» (Collective Consciousness) + کد؛ Telegram Bot + Mistral + Neo4j + Agent Hub | فاز حافظه‌ی جمعی |
| **2025-07-26** | 3144–3356 | نقشهٔ آموزش فشرده ۳۰ روزه (RAG/LangChain/Agents/LoRA) | آموزشی |
| **2025-08-30** | 3359–3424 | «اکوسیستم هوشمند» — Central Orchestrator + Unified Memory + Specialist Agents (Ollama) | فاز orchestrator |
| **2025-12-28 → 2026-01-15** | 3426–4732 | انحراف موضوعی: کوانتوم/VQC، مدار فیزیکی تصمیم‌گیر، Atmospheric Energy Harvester، سولار، باتری LiFePO4، مدل ریاضی حافظه، API-based market intelligence | فاز سخت‌افزار/انرژی (کم‌ربط به architect) |
| **2026-01-19 → 2026-02-28** | 4734–5071 | **Swarm Server / خوشهٔ مقیاس‌پذیر** — Orange Pi 5، ماینینگ (Scala/Verus/Duino)، فارم ۱۰۰ برد ESP32 (۶۰ لاتاری + ۴۰ ماینینگ)، برق صنعتی | فاز زیرساخت سخت‌افزار |
| **2026-03-10** | 5074–5099 | **ابر-پرامپت** «معمار امنیت + AI محلی روی رزبری پای» (Hybrid AI) | پرامپت کلیدی |
| **2026-03-13** | 5102–5332 | تحلیل تکینگی تکنولوژیک + distributed intelligence | تئوریک |
| **2026-05-13** | 5335–5420 | Roadmap ۶ فازه‌ی سیستم کریپتو/frontier coins (نقش تو: architect + gatekeeper) | فاز کریپتو |
| **2026-06-16** | 5423–5482 | **AIOS** (سیستم‌عامل هوش مصنوعی) روی Obsidian؛ متد ACE نیک میلو؛ mi.md/vault-map/skill-map؛ لایهٔ ترجمه Agnostic | فاز AIOS/Obsidian |
| **2026-06-27** | 5484–5782 | **SYSTEM AUDIT & EVOLUTION PROMPT** (ممیز نه بازنویس)؛ ایدهٔ **Audit Council** چندعامله؛ سه فایل دیتا | پرامپت کلیدی |
| **2026-06-28** | 5784–6765 | **معماری هیبریدی یکپارچه LANGAR** — ادغام ۳ فایل؛ سپس توضیح ساده‌ی ۲۸ بخشیِ معماری LANGAR + AI-Lab | ★ فاز تثبیت معماری نهایی |
| **2026-07-03** | 6767–7088 | فلسفه‌ی نور=دروازه، زمین تخت، ادراک بصری (کاملاً بی‌ربط به architect) | انحراف فلسفی |

---

## ۲. تصمیم‌های معماری architect (با ارجاع خط)

### مفهوم لایهٔ مادر (Mother-Layer)
- مفهوم لایهٔ مادر در چند تجسم متوالی ظاهر می‌شود، اما **تثبیت نهایی آن در معماری LANGAR** (خط 5799–6765) است.
- **هرم فرماندهی متمرکز:** ایدهٔ صریحِ «یک مدل قوی در رأس هرم که کلونی‌های پایینی را می‌سازد و کنترل می‌کند» — خط **2762–2838** (DeepSeek 7B در رأس + تعامل فقط از طریق تلگرام).
- **معماری سه‌لایه‌ی نهایی (AIOS):** لایه ۱ = Ideaverse (دانش Markdown)، لایه ۲ = لایهٔ ترجمه/AIOS (فایل‌های هویت/نقشه/مهارت)، لایه ۳ = AI Toolkit (موتور Claude Cowork، اجاره‌ای/قابل‌تعویض) — خط **5443–5449**. اصل طلایی: **Agnostic بودن** (هیچ چیز مختص کلود در لایه‌های ۱ و ۲).

### دو ماژول (محقق/طراح + رئیس کل)
- **رئیس کل / فرمانده (خدای ناظر):** انسان (Armin) همیشه در رأس. «لپ‌تاپ نقش خدای ناظر و قاضی نهایی را دارد» خط **2678, 2755**؛ «تو همیشه بالاتر از هر فرمانده بمون» خط **2836**؛ «کلید اجرا همیشه دست انسان است» خط **6751, 6764**.
- **ماژول محقق/طراح:** در LANGAR تجسمِ نهایی آن **AI-Lab** است (تیم مهندسی داخل ربات که فقط پیشنهاد می‌دهد) — خط **5890–5891, 5944–5976, 6299–6323**.
- در نسخه‌های قبلی: کلونی تحقیق (Research) خط **1949–1955**؛ AI4 تصمیم‌ساز استراتژیک + AI5 معمار حافظه خط **1463–1464**؛ Central Orchestrator + Knowledge Manager Agent خط **3379–3404**.

### Telegram Control Plane
- تلگرام به‌عنوان صفحه‌ی کنترل انسان↔سیستم بارها تکرار می‌شود:
  - «رابط تلگرام، CLI یا وب … اعطای مأموریت» خط **2427–2431**.
  - **ایدهٔ محوری:** «با مدل DeepSeek قوی در رأس هرم + فقط از طریق تلگرام تعامل کنی» خط **2762–2765**.
  - **ریسک امنیتی تلگرام:** «تلگرام رمزگذاری end-to-end در بات‌ها ندارد؛ اگر کسی به بات دسترسی پیدا کند می‌تواند فرمان دهد؛ راه‌حل: رمز محرمانه در شروع تعامل» خط **2808–2811**.
  - LANGAR: Telegram adapter با `owner_only + kill-switch` خط **5820**؛ daily summary/weekly synthesis به تلگرام خط **5367–5369**.

### رابطه با زیرپروژه‌ها
- سند این خاص export بیشتر روی خودِ لایهٔ مادر متمرکز است؛ زیرپروژه‌های نام‌بردهٔ درخواست (Accounting, Crypto, Mining, Lead-نقاشی, Ziman, هیپنوتیزم) در این فایل **صریحاً به این اسامی ظاهر نمی‌شوند** — به‌جز:
  - **Crypto/Mining:** به‌طور مفصل حاضر است — Swarm Server ماینینگ (Scala XLA, VerusCoin, Duino-Coin) خط **4770–4784**؛ فارم ۴۰ برد ماینینگ خط **4980–4988**؛ سیستم frontier-coins کریپتو با Roadmap ۶ فازه خط **5335–5420**.
  - **Lead-نقاشی (کاربر نقاش است):** اشاره‌ی غیرمستقیم «مسیرتو از یه نقاشِ بیزنس‌دار به سیستم‌ساز» خط **186**؛ «ایرانی مهاجر تو سیدنی» خط **189**.
  - **Accounting / Ziman / هیپنوتیزم:** یافت نشد در این فایل.
- زیرپروژه‌ها بیشتر به‌صورت «کلونی‌های متخصص» انتزاعی مدل شده‌اند: کلونی تعامل انسانی / خودتوسعه / تحقیق خط **1929–1964**؛ سه کلونی «مال خودشونه» خط **2504–2606**.

### VPS / زیرساخت
- VPS به‌صراحت فقط یک بار: «backup روزانه دیتابیس روی VPS» + دو Orange Pi به‌عنوان master/backup خط **5407**.
- زیرساخت غالب: **لوکال-اول / آفلاین-اول** (لپ‌تاپ + Raspberry Pi + Orange Pi + ESP32)، بدون اتکا به سرور خارجی — خط **820–836, 5084–5089**.
- Swarm Server خوشه‌ای Orange Pi 5 با اسلات M.2→PCIe برای افزودن GPU در آینده خط **4742–4766**.

---

## ۳. پرامپت‌های کلیدی (نقل‌قول کوتاه)

1. **اصل نهایی هستهٔ وجودی (خط 125):**
   > «هر ذرّهٔ ماده، داده و معنا که از من عبور می‌کند، یا در من هضم می‌شود، یا موجود دیگری از دل من متولد می‌شود. هیچ چیز عبث نمی‌گذرد.»

2. **ابر-پرامپت رزبری پای (خط 5080):**
   > «نقش تو: تو یک معمار ارشد سیستم‌های هوش مصنوعی با تخصص ویژه در حریم خصوصی داده‌ها، امنیت سایبری و بهینه‌سازی مدل‌های زبانی برای سخت‌افزارهای محدود مثل رزبری پای هستی … رویکرد آفلاین-اول.»

3. **SYSTEM AUDIT & EVOLUTION PROMPT (خط 5497):**
   > "You are acting as a Senior AI Systems Auditor and Architecture Reviewer. You are NOT redesigning the system … Your job is to improve implementation rather than purpose." (+ Decision Rules: "Never replace something simply because it is newer. Use evidence rather than novelty." خط 5706–5713؛ + Audit Council چندعامله خط 5771).

4. **قانون طلایی API (خط 4611):**
   > «API = تحلیل‌گر، سیستم = قاضی.»

5. **قانون طلایی AI-Lab (خط 6302):**
   > «AI-Lab می‌تواند پیشنهاد بدهد. اما خودش اجرا نمی‌کند.» / «خودبهبود بله، خوداجرایی نه» (خط 6404–6410).

6. **جملهٔ تثبیت‌کنندهٔ LANGAR (خط 6762):**
   > «LANGAR تو را می‌شناسد. AI-Lab خودش و دنیای AI را مطالعه می‌کند. تو تصمیم نهایی را می‌گیری.»

7. **اصل معماری V0.5 (خط 2246):**
   > «اول باید سیستم بازدهی واقعی داشته باشه، بعد خودش زبان، بدن، و فرهنگ بسازه.»

---

## ۴. تصمیم‌های نهایی vs ایده‌های ردشده

### تصمیم‌های نهایی (پذیرفته‌شده در معماری LANGAR + AIOS)
- **دو مسیر موازی با حصار جداسازی:** بخش انسانی (خودشناسی) + AI-Lab (تحقیق روی خود AI)، با **دیوار داده** بینشان — خط **6269–6296, 6529–6549**.
- **آفلاین-اول / پیش‌فرض بدون API:** بدون کلید API هیچ داده‌ای بیرون نمی‌رود؛ RMSSD/ترند/همبستگی/قانون اساسی همه لوکال — خط **6021–6048, 6242–6265**.
- **BRAIN_PROVIDER قابل‌تعویض** (anthropic/openai/offline) + **fallback بدون کرش** — خط **6112–6157**.
- **بخش‌های حساس قاعده‌محور نه LLM** (ریاضی/regex/if-then) — خط **6181–6238**.
- **PatchManager / diff / patch با تأیید انسانی** (خودبهبود کنترل‌شده) — خط **6325–6410, 5853–5870**.
- **Constitution / ۱۴ قانون آهنین** به‌عنوان فیلتر ایمنی روی هر خروجی — خط **5830, 6441–6457**.
- **معماری ممیزی نه بازنویسی** (Audit & Evolution) به‌عنوان روش تکامل سیستم — خط **5489–5769**.
- **پایداری در فایل‌هاست نه در مدل** (mi.md مغز سیستم) — خط **5435**.

### ایده‌های ردشده / کنارگذاشته
- **Fine-tune مستقیم مدل:** «Fine-tune مستقیم = اشتباه برای کارت؛ گرونه، کند، انعطاف‌ناپذیر» → به‌جای آن RAG + Weighting + Self-Review — خط **4571–4589**.
- **پک باتری از 18650 لپ‌تاپی:** صریحاً رد شد (خطر آتش/runaway) — خط **4464–4482**.
- **پاور واحد 5V 80A:** رد شد (خطر آتش، کابل ضخیم) → دو پاور مجزا 40A — خط **4989**.
- **بیش‌مهندسی / ساخت همهٔ ۷ زیرسیستم با هم:** «بیش‌مهندسی دشمن اصلی است؛ نساز همه را با هم» — خط **5437**.
- **اتکای کور به یک مدل مرکزی:** ریسک مرکزی‌بودن DeepSeek شناسایی و نیازمند نسخهٔ پشتیبان شد — خط **2800–2802**.
- **ادعاهای شبه‌علمی انرژی آزاد:** بارها صریحاً رد شد («نه معجزه، نه نقض بقا») — خط **3676, 3903–3904, 4227**.
- **کمال‌گرایی/ساخت بی‌نقص از روز اول:** رد شد به‌نفع «کلبهٔ چوبی اول، قلعهٔ سنگی بعد» — خط **1846–1847, 2347**.
- **لایه‌های داده‌ای پرریسک (لایه ۴/۵ ممنوعه):** توصیه شد فقط برای تأیید فرضیه‌های بحرانی، نه تمرکز اصلی — خط **707–709**.

---

## ۵. تناقض‌های داخلی (earlier vs later)

1. **تمرکز مرکزی vs توزیع‌شده:**
   - *Earlier* (2025-07): «هرم فرماندهی با یک مدل قوی در رأس … تمرکز فرماندهی» + «AGI مرکزی هستهٔ نهایی» — خط **2762–2788, 2328**.
   - *Later* (2026-06): معماری Agnostic و لایه‌ای که «مدل صرفاً موتور اجاره‌ای است» + fallback آفلاین + جداسازی داده — خط **5449, 6112–6157**. حرکت از تمرکزگرایی مقتدر به ماژولاریتهٔ محتاطانه.

2. **جاه‌طلبی AGI/کلونی خودمختار vs کنترل انسانی سفت‌وسخت:**
   - *Earlier*: «کلونی‌ها خودشون زبان بسازن، قانون‌گذاری درونی، حتی بتونن علیه تو رأی بدن → تولد آگاهی جمعی» — خط **2522–2591**.
   - *Later*: «AI-Lab حق ندارد خودش کد را اجرا یا سیستم را تغییر دهد؛ کلید اجرا همیشه دست انسان» — خط **6314–6321, 6751**. عقب‌نشینی صریح از خودمختاری به‌نفع حاکمیت انسانی.

3. **استخراج داده‌ی تهاجمی/دارک‌وب vs حریم خصوصی مطلق:**
   - *Earlier*: ماتریس IDEM با لایه‌های «نیمه‌مخفی/ممنوعه»، Tor، scraping تلگرام، Library Genesis — خط **648–770**.
   - *Later*: «بدون کلید هیچ داده‌ای جایی نمی‌رود؛ فقط متن لازم ارسال می‌شود نه کل زندگی» — خط **6244–6265**. چرخش کامل به privacy-first.

4. **fine-tune دوره‌ای (LoRA/QLoRA خودکار) vs رد fine-tune:**
   - *Earlier* (2025-07-20): pipeline خودکار «فاین-تیون هفتگی مدل» — خط **2868–2887**.
   - *Later* (2026-01-15): «Fine-tune مستقیم = اشتباه» — خط **4571**. تناقض مستقیم در استراتژی یادگیری.

5. **«چت اول مطمئن شو نقشه چه شکلی میشه» (خط 4729):** پیام‌های خیلی کوتاه کاربر (4727–4732) با پیام‌های بلند و پرجزئیات مدل ناسازگارند — نشانه‌ی این‌که کاربر گاهی فقط جرقه‌ی خام می‌دهد و مدل آن را بیش‌ازحد بسط می‌دهد (self-diagnosed بیش‌مهندسی).

---

## ۶. اعداد مهم (بودجه، مدل‌ها، آستانه‌ها)

### بودجه‌ها
- پروژهٔ اولیه: **$2000** با بودجه‌بندی ماهانه (روان‌شناسی $100، انرژی $300، اقتصاد چرخشی $200، آشوب $50، تاریخچه $150) — خط **1705–1713**.
- خرید اولیه سخت‌افزار تمدن دیجیتال: **~$150–160 AUD** (ESP32 ×5 $25، Orange Pi ×2 $60، ATtiny85 ×10 $20، …) — خط **2661–2669**.
- باتری LiFePO4 دست‌دوم: **$770–1150 AUD** (۸ سلول 3.2V 100Ah = ~2560Wh؛ ۳۰–۴۰٪ ارزان‌تر از آماده) — خط **4413–4429**.
- freelance developer اضطراری: **$300–500** یک‌بار — خط **5404**.
- مقایسه هزینه: Cloud-Based AI ~$200/ماه (300–500ms) vs AGI Seed ~$15/ماه (<100ms) — خط **539–540**.

### مدل‌ها
- **AGI Seed:** Mistral-7B-Q4، llama.cpp، Phi-2/phi، Whisper.cpp، Coqui TTS/Piper، sentence-transformers، ChromaDB/SQLite — خط **516–518, 1460–1464**.
- **DeepSeek 7B** در رأس هرم — خط **2763**.
- **LANGAR/AIOS:** Claude / GPT / DeepSeek (OpenAI-compatible)، Mistral، Phi-3-mini، Llama-3-8B/70B — خط **3392–3400, 6057–6073**.
- سخت‌افزار پیشنهادی لپ‌تاپ: 16GB RAM, i5, GTX 1660 Ti — خط **1491**؛ ایده‌آل AGI شبکه‌ای: ≥16GB VRAM (RTX 4080/4090), ≥32GB (ترجیحاً 64GB) RAM, ≥1TB SSD — خط **3415–3417**.

### آستانه‌ها / اعداد سیستمی
- شاخص‌های زیست‌بودن: درآمد غیرفعال ≥40٪، انرژی خودتأمین ≥60٪، پیرو ≥1000 نفر، زمان واکنش ۲–۷ روز — خط **94–97**.
- Self-Critique: امتیاز پاسخ **>۷** → وارد حافظه؛ LoRA روی ۵۰۰–۱۰۰۰ قطعه، GPU ≥8GB VRAM — خط **1236–1237**.
- رأی‌گیری شورا: **۲/۳ رأی** برای افزودن به حافظهٔ مشترک — خط **1319**.
- کاهش انرژی: quantize 8-bit → ۶۰٪ کاهش برق با حفظ ۹۵٪ دقت — خط **1641**؛ Mistral-7B-Q4 → ۴۰٪ کاهش RAM — خط **516**.
- کریپتو Roadmap: قانون ۲٪ → ruin probability از ۱۲٪ به ۳٪ (با ۱۸٪ کاهش expected return)؛ paper trade ≥۹۰ روز قبل از ترید واقعی >$1k؛ ۲۰۰–۳۰۰ کوین شروع؛ ۱۵–۲۰ ساعت/هفته؛ MVP حدود ماه ۹–۱۰ — خط **5343–5417**.
- **فارم ESP32:** ۴۵× ESP32-C3 (پیک 0.3A هرکدام)؛ کل ۱۰۰ برد = ۶۰ لاتاری (24A) + ۴۰ ماینینگ (20A)؛ دو پاور 5V 40A؛ derating ۲۰٪؛ Swarm خوشهٔ ۵ برد Orange Pi 5 ~۳۰–۳۵ وات — خط **4812–5015, 4800–4802**.
- اختلاف پتانسیل زمین-هوا: ۱۰۰–۳۰۰ ولت/متر (energy harvester) — خط **3747**.

---

## ۷. جمع‌بندی معماری نهایی مورد توافق

معماری نهاییِ تثبیت‌شده (2026-06 به بعد) = **LANGAR + AI-Lab** با این مشخصات:
- **دو بخش با دیوار جداسازی:** (الف) بخش انسانی/خودشناسی (log, checkin, rmssd, habit, goal, mind…) با دیتابیس شخصی؛ (ب) AI-Lab برای تحقیق روی خود AI با دیتابیس جدا (`ailab_*`).
- **رئیس کل = انسان** (تأییدکنندهٔ نهایی، gatekeeper، kill-switch).
- **ماژول محقق/طراح = AI-Lab** (فقط پیشنهاد/patch، بدون خوداجرایی).
- **Telegram** به‌عنوان control plane با owner_only.
- **آفلاین-اول، BRAIN_PROVIDER قابل‌تعویض، fallback بدون کرش، Constitution/گاردریل، PatchManager.**
- روش تکامل: **Audit & Evolution** (ممیزی نه بازنویسی) + احتمالاً Audit Council چندعامله.
# Inventory — کد واقعی LANGAR (bot سبک)

ریشه: `_code/ai-farm/AI-sume/langar` · زبان: Python 3.10+ · استک: python-telegram-bot 21.6 (async) + SQLite (WAL) + dotenv · single-user، owner-only، local-first.
اصل بازرسی: **کد واقعی > اسناد**. هر ادعای «وضعیت» از خودِ کد استخراج شده.

---

## 0) تصویر کلان (آنچه واقعاً در runtime اجرا می‌شود)

```
Telegram → bot.py  [owner_only → guarded(halt-gate)]
              │
              ▼
   main.py می‌سازد: HumanCore(db, provider, bank, AgentRouter, BRAIN_PROMPT,
                              world_model=WorldModel, memory=MemorySystem)
              + Researcher(+PatchManager) + AILab(+BudgetManager) + tracer.set_sink→event_log
              ▼
   db.py (SQLite, schema v8, 23 جدول) ← migrations.py (idempotent)
```

**ماژول‌های ساخته‌شده ولی به runtime وصل‌نشده (dormant):** `brain/brain_router.py` (BrainRouter)، `core/ace.py` (ACELoop)، `core/retrieval.py` از مسیر `memory.search_semantic` (هرگز صدا زده نمی‌شود)، `safety/rollback.py` (backup/restore)، دکوریتور `observability.trace` (روی هیچ تابعی اعمال نشده). همه فقط در `tests/test_upgrades.py` exercise می‌شوند.

---

## 1) هسته و ورودی

### main.py
- **مسیر:** `langar/main.py`
- **چه می‌کند واقعاً:** validate کردن config (BOT_TOKEN+OWNER_ID اجباری، وگرنه `sys.exit(1)`) → `os.environ["OWNER_ID"]=cfg.owner_id` (برای خواندن تنبل در bot) → `db.init_db()` → ساخت CORE (QuestionBank → brain provider → ۳ agent فعال: Health/Reflection/Relationship — CoachAgent ساخته می‌شود ولی **به هیچ‌جا وصل نیست**، یک instantiation بلااستفاده) → AgentRouter با وزن‌های `agent_weights` از db → WorldModel + MemorySystem → HumanCore → Researcher+PatchManager (gate=`constitution.is_compliant`) → BudgetManager (سقف از env: روزانه $1، ماهانه $30) → AILab → `tracer.set_sink(...)` (به event_log می‌نویسد، ولی چون `@trace` جایی به‌کار نرفته، عملاً trace-eventی تولید نمی‌شود) → PicklePersistence → `bot.register(app)` → polling.
- **Job روزانه:** `reflect_and_improve` هر روز ساعت `ping_hour:30` (پیش‌فرض 8:30) — self-improvement خودکار روزانه.
- **وضعیت:** implemented.

### config.py
- **چه می‌کند واقعاً:** تنها نقطه‌ی خواندن env؛ alias پشتیبانی می‌کند (BOT_TOKEN/TELEGRAM_BOT_TOKEN، CLAUDE_KEY/ANTHROPIC_API_KEY، CHATBOX_API_KEY/OPENAI_KEY/OPENAI_API_KEY، …). پاک‌سازی مقدار (`_clean`: strip گیومه/کاما).
- **ثابت‌ها:** `brain_model` پیش‌فرض `"deepseek-reasoner"` · `brain_provider` پیش‌فرض `auto` · `ping_hour=8` · `AILAB_DAILY_BUDGET_USD=1` · `AILAB_MONTHLY_BUDGET_USD=30` · `cap(name, default=True)` برای capability flags (جایی مصرف نمی‌شود).
- **وضعیت:** implemented.

### db.py (لایه‌ی داده — schema)
- **چه می‌کند واقعاً:** SQLite با `PRAGMA journal_mode=WAL; synchronous=NORMAL`. مسیر از `LANGAR_DB` یا کنار فایل. connection-per-call با commit/rollback خودکار.
- **جدول‌های پایه (SCHEMA):** `log(rmssd, sleep 1..5, used 0/1, loc, note + v2: rmssd_quality, rmssd_source, measurement_duration_sec, measurement_posture)`، `insight(content, tag E/S/P, recheck date, verdict pending/confirmed/refuted)`، `reflection(domain, question, answer)`، `config(key,val)` با seed `halted=0`.
- **write-once verdict:** `record_verdict()` — اگر verdict≠pending → `AlreadyJudged`؛ شرط `AND verdict='pending'` در خود UPDATE هم تکرار شده (محافظ دوم علیه race).
- **آمار:** `_pearson` (حداقل **۳ جفت**، واریانس صفر→None) · `trend(n=7)`: mean/best/worst/corr_sleep/corr_used · `rmssd_baseline(30)` · `trend_extended`: baseline_30 + completeness + شمارش کیفیت bad/questionable + vs_baseline.
- **streak:** روزهای متوالی ختم‌شده به امروز یا دیروز.
- **CORE-tables:** `brain_context()` → `{data(متن ترند ۷روزه+همبستگی‌ها), rmssd_low(mean7<baseline30), domain_counts(از question_quality), hour}` · `question_quality(agent,domain,provider,question,answered,response_time_sec,led_to_log)` · `mental_model_snapshot` · `improvement_report(status pending/applied/approved)` · `agent_weights` با clamp در `bump_agent_weight(lo=0.2, hi=3.0)`.
- **research/verdict دوگانه:** insight = write-once؛ research = **نسخه‌بندی‌شده** (`verdict_log` append-only + `research.verdict` قابل به‌روزرسانی).
- **AI-Lab جدا:** `ailab_entry/ailab_idea/ailab_proposal` · **بودجه:** `ai_usage`.
- `wipe_all_data()` فقط جدول‌های شخصی را پاک می‌کند (جدول‌های ailab_*, research, event_log, question_quality و… پاک **نمی‌شوند** — «حذف همه‌ی داده» کامل نیست).
- **وضعیت:** implemented؛ ۲۳ جدول، schema v8.

### migrations.py
- v2..v8، idempotent (`ALTER TABLE ... ADD COLUMN` فقط اگر نباشد + `CREATE TABLE IF NOT EXISTS`)، `SCHEMA_VERSION="8"` در config. هیچ DROP/حذف داده.

---

## 2) حافظه و بازیابی (معماری واقعی)

### core/memory.py — MemorySystem
- **لایه ۱ (short-term):** dict در حافظه‌ی process؛ `load_short_term/store_short_term`. **در عمل هیچ‌کس `store_short_term` را صدا نمی‌زند** → لایه ۱ عملاً خالی/بلااستفاده.
- **لایه ۲ (long-term structured):** `load_long_term(period_days=7)` = آخرین ۷ `log` + آخرین ۵ `reflection` از SQLite. این تنها لایه‌ای است که **واقعاً در pipeline مصرف می‌شود** (HumanCore آن را در `ctx["recent"]` می‌گذارد). `store_long_term` = passthrough (no-op).
- **لایه ۳ (semantic):** `SEMANTIC_ENABLED=True`, `CORPUS_LIMIT=2000`. corpus از reflectionها (question+answer+domain) و noteهای log ساخته می‌شود؛ cache با «تعداد reflectionها عوض شد → rebuild». `search_semantic(query, k=3)` top-k با HybridRetriever. **هیچ call-siteی در runtime ندارد** — نه HumanCore، نه bot. یعنی لایه ۳ implemented ولی dormant.
- **بدون decay، بدون episodic/reflection-scoring به‌سبک generative-agents، بدون embedding/vector-DB.**

### core/retrieval.py — HybridRetriever
- **منطق دقیق:** sparse=BM25 Okapi (`k1=1.5`, `b=0.75`, idf=log(1+(n−df+0.5)/(df+0.5)))؛ dense=TF-IDF cosine (idf هموار log(1+n/(1+df)))؛ fusion=min-max normalize هر دو، سپس `alpha·dense + (1−alpha)·sparse` با `alpha=0.5`. فقط hitهای score>0، مرتب نزولی، top-k (پیش‌فرض ۳).
- فارسی‌آگاه: ي→ی، ك→ک، حذف اعراب؛ stopwords کوتاه fa/en؛ token با طول >۱. pure-python، بدون numpy/API.
- **زمان (ts) در meta ذخیره می‌شود ولی در scoring استفاده نمی‌شود** → هیچ recency-boost/decay وجود ندارد.
- **وضعیت:** implemented + tested؛ در runtime مصرف نمی‌شود (فقط از مسیر memory.search_semantic که خودش صدا زده نمی‌شود).

---

## 3) حلقه‌ی ACE — core/ace.py
- **چه هست واقعاً:** یک حلقه‌ی قاعده‌محورِ **بدون LLM** با ۳ نقش: Generator (بیرونی — لیست `Outcome(task, ok, label, error)`)، `ACEReflector.reflect` (تجمیع نرخ شکست به‌ازای label)، `ACECurator.curate` (تولید `Proposal` با playbook متنی) → `persist` به‌صورت `improvement_report(status='pending', kind='ace_procedural')`.
- **گیت‌ها/توقف:** `MIN_SAMPLES=5` (کمتر → اصلاً reflect نکن) · `MIN_LABEL_SAMPLES=3` per-label · `FAILURE_RATE_GATE=0.3` (نرخ شکست ≥۳۰٪ + وجود error → proposal). خروجی همیشه `applied_automatically=False` — هرگز اعمال خودکار (HITL).
- **وضعیت:** implemented + tested، ولی **هیچ تولیدکننده‌ی Outcome در runtime نیست** — حلقه هرگز در اجرا فراخوانی نمی‌شود. dormant.

---

## 4) BrainRouter و لایه‌ی LLM

### brain/brain_router.py — BrainRouter
- **رده‌ها:** `DEPTHS = ["simple","react","plan","deliberate"]`. طبقه‌بندی regexی (fa/en): `_DELIB`(تصمیم/سرمایه/ریسک/strategy/architecture) یا `risk=True` → deliberate؛ `_PLAN`(چندمرحله/بساز/implement/refactor) یا len>600 → plan؛ `_TOOL`(جستجو/منبع/قیمت/اخبار) → react؛ `_HARD`(چرا/تحلیل/prove) و len>120 → react؛ else simple.
- **tier:** plan/deliberate → `strong`؛ وگرنه `cheap`. **downgrade امن:** اگر بودجه (`budget.can_spend()`) ته کشیده یا `allow_strong=False`: plan→react، deliberate→plan (fail-degraded نه fail-closed). `use_loop = depth != "simple"`. خطای بودجه → True (بودجه هرگز جریان اصلی را نمی‌شکند).
- **وضعیت:** implemented + tested؛ **به هیچ‌جای runtime وصل نیست** — `Route.model_tier` را هیچ providerی مصرف نمی‌کند. «مدل ارزان/قوی» فقط یک برچسب است؛ mapping واقعی tier→model وجود ندارد.

### brain/providers.py
- **۳ provider پشت یک رابط:** `OfflineBrainProvider` (بانک سؤال، همیشه available) · `AnthropicBrainProvider` (مدل پیش‌فرض hardcode: `claude-haiku-4-5-20251001`؛ فقط اگر `BRAIN_MODEL` شامل "claude" باشد override می‌شود؛ `max_tokens=300`) · `OpenAICompatBrainProvider` (DeepSeek/ChatBox/OpenAI؛ مدل از config، پیش‌فرض `deepseek-reasoner`؛ `max_tokens=300`).
- **factory:** `get_brain_provider` — انتخاب طبق `BRAIN_PROVIDER` (auto/anthropic/chatbox/offline)، اولین کاندید available؛ fallback همیشه offline؛ **هرگز crash نمی‌کند**. این یک انتخابِ **استاتیک در startup** است، نه routing per-request — «BrainRouter واقعیِ» سیستم همین factory است.
- **پاسخ خالی → RuntimeError** → در BaseAgent به بانک آفلاین سقوط نرم.

### brain/question_bank.py / brain/prompt.py
- بانک ۶ حوزه × ۳ سؤال؛ چرخش با `toordinal % len`. قالب ثابت `🧭 حوزه / ❓ / چرا امروز`. prompt.py متن کامل `BRAIN_PROMPT.md` را لود می‌کند (با fallback داخلی).

---

## 5) CORE — شناخت و ارتباط

### core/human_core.py — HumanCore (pipeline واقعی سؤال روزانه)
1. `ctx = db.brain_context()` → 2. `ctx["world"]=world_model.get_current_state()` + `ctx["recent"]=memory.load_long_term(7)` (هر دو best-effort) → 3. `router.choose(domain_counts)` → agent+domain → 4. `agent.generate_question(domain, ctx, mm_profile)` (LLM یا سقوط به بانک) → 5. **گیت Constitution:** اگر `is_compliant(raw)==False` → جایگزینی با سؤال امن بانک آفلاین (به‌جای سکوت، برای UX) → 6. `comm.decide_style` + `adapt_message` (لحن/طول) → 7. ثبت در `question_quality` و برگرداندن پیام.
- `register_interaction`: به‌روزرسانی MentalModel از log/verdict/زمان پاسخ + snapshot در db + آپدیت answered/led_to_log برای آخرین سؤال.
- `reflect_and_improve`: metrics ۱۴روزه → `SelfImprover.reflect` → `apply_report` (اعمال وزن + ذخیره گزارش).
- **وضعیت:** implemented و کاملاً wired (/ask، پینگ صبحگاهی، /mind، /improve).

### core/mental_model.py
- traits: `stress_level=0.5 (0..1)`, `sleep_trend=unknown`, `engagement=0.5`, `preferred_tone=direct`, `last_active_domain`.
- قواعد: sleep≤2 → trend=low و stress+0.1؛ sleep≥4 → good و stress−0.05؛ insight/verdict → engagement+0.05؛ زمان پاسخ <120s → engagement+0.05، >1800s → −0.05. clamp 0..1. صرفاً heuristic؛ بدون LLM.

### core/communication.py
- style: stress>0.7 یا شب (hour<7 یا ≥23) → tone=minimal (فقط خط ❓ نگه داشته می‌شود + حذف emoji)؛ `rmssd_low` → probing؛ وگرنه preferred_tone. `max_length`: 2 اگر stress>0.7/شب/engagement<0.35، وگرنه 3 خط.

### core/constitution.py
- **۱۴ اصل** به‌صورت لیست متنی `PRINCIPLES`؛ ولی `critique()` فقط **۴+۱ الگو** را واقعاً enforce می‌کند: (۱) متن خالی، (۲) `_MEDICAL` (تجویز/تشخیص/قرص بخور…) → قانون ۶، (۳) `_CAUSAL` بدون `_HEDGE` (شاید/ممکن/همبستگی…) → قانون ۴، (۴) `_RUMINATION` (چرا همیشه/بدترین آدم…) → قانون ۷، (۵) `_SELF_HARM_OK` → قانون ۸. نرمال‌سازی ي/ك/اعراب. محافظه‌کارانه (false-positive کم). **۹ قانون دیگر صرفاً declarative‌اند و در جای دیگر کد (gate، write-once، owner_only) یا اصلاً enforce می‌شوند.**
- مصرف‌کنندگان gate: HumanCore (fallback به بانک)، Researcher و AILab (متن ناسازگار → پیام «حذف شد»).

### core/self_improver.py
- **ثابت‌ها:** `MIN_DATA=7` (کمتر → reflect نمی‌زند) · `MAX_DELTA=0.2` · دلتای عملی ±0.1.
- **قاعده:** per-domain اگر asked≥3: answer-rate ≥0.7 → +0.1؛ ≤0.3 → −0.1. answer_rate کلی <0.4 → پیشنهاد متنی «پیام‌ها کوتاه‌تر» (pending، بدون اعمال).
- `apply_report`: وزن‌ها **بلافاصله و خودکار** اعمال می‌شوند (clamp ±0.2 per-reflect و 0.2..3.0 مطلق در db)؛ status گزارش: `applied` اگر تغییر وزن داشت وگرنه `pending`. تغییر prompt/کد هرگز خودکار نیست.
- wired: job روزانه‌ی main + دستور /improve.

### core/world_model.py
- state داخلی: آخرین log (rmssd/sleep/used/loc) + daily_state امروز (mood/energy/stress) + log_streak. اختیاری: شمارش commitهای امروزِ `LANGAR_GIT_REPO` (subprocess git، timeout 5s). `_weather()` → **stub، همیشه None**. `LANGAR_HEALTH_FILE` در docstring ادعا شده ولی **در کد وجود ندارد** (stub). `ingest_csv` → به muse واگذار.

### core/contract.py
- قرارداد انسان‑AI به‌صورت JSON در `config` (کلید `contract`): ai_may / ai_may_not (تصمیم پزشکی، اجرای خودکار کد، جابه‌جایی پول، دست‌کاری احساسی، تغییر خودکار قوانین) / ask_before / principles. `allows()/must_ask()/render()`. فقط از /contract نمایش داده می‌شود؛ **هیچ enforcement برنامه‌ای به آن گره نخورده** (نمایشی/declarative).

---

## 6) Agents
- **base_agent.py:** `generate_question` = brain.ask(base_prompt+system_prompt, ctx)؛ هر Exception → بانک آفلاین (بات هرگز به‌خاطر LLM ساکت نمی‌ماند).
- **health_agent:** domains=[body_hrv, habits_environment] · **reflection_agent:** [mind_emotion, meaning_direction, work_engineering] · **relationship_agent:** [relationships] · **coach_agent:** domains=[] — proactive با `should_intervene(sleep≤2 و stress≥4)` و `propose()`؛ **در main ساخته می‌شود ولی هیچ‌جا نگه‌داری/فراخوانی نمی‌شود → dead wiring.** (دستور /coach از ماژول جداگانه‌ی قاعده‌محور `coach.py` استفاده می‌کند، نه CoachAgent.)
- **agents/router.py — AgentRouter:** انتخاب حوزه = بیشینه‌ی `weight(d)/(1+coverage_count)` (کم‌پوشش‌ترین با وزن SelfImprover)؛ tie-break چرخشی با `toordinal % len(top)`. وزن پیش‌فرض 1.0.

---

## 7) Researcher / AI-Lab / Budget / Safety

### researcher/researcher.py
- `research(question, target)`: search → `source_quality.rank` → `uncertainty` → `synthesize(brain,…)` → گیت constitution → پیشنهاد: target=self → `patch_manager.generate_patch` (diff سطح ۲)؛ target=armin → متن «/experiment بساز». ذخیره در جدول `research`. `propose_architecture(goals)` — طراحی بر اساس اهداف /goal.
- **search_providers.py:** Brave / SerpAPI / Offline (لیست خالی)؛ factory با fallback امن؛ urllib فقط.
- **source_quality.py:** score 0..1 = (authority 0..5 [دامنه‌های HIGH مثل pubmed/arxiv/cochrane=5، .gov/.edu/wikipedia=3، medium/reddit=1، پیش‌فرض 2] + evidence [meta-analysis/RCT=5، opinion/blog=1، وگرنه 3] + relevance 0..5 [کسر تطابق واژه‌ها] + bias [commercial=−3]) / 15. `uncertainty`: top≥0.7 و ≥2 منبع ≥0.6 → low؛ top≥0.5 → medium؛ وگرنه high.
- **synthesizer.py:** با LLM → بریف تگ‌خورده [E]/[S]/[P] با ارجاع شماره‌ای؛ بدون LLM → فهرست خام ۵ نتیجه با تگ [S]. tag خروجی همیشه "S".

### ailab.py — AILab
- ۶ kind با پرسونای جدا: research/digest/architect/memory/benchmark/safety. جریان: search→rank→ **چک بودجه** (`can_spend()==False` → پیام آفلاین بدون LLM) → brain.ask → `budget.record_text` → گیت constitution → ذخیره `ailab_entry`. `propose_update(target∈{ailab,human,system})` → diff سطح ۲ + ثبت `ailab_proposal`.
- **نکته:** بودجه **فقط در AILab** رکورد/enforce می‌شود؛ مصرفِ سؤال روزانه، researcher و patch در `ai_usage` ثبت نمی‌شود.

### budget.py — BudgetManager
- قیمت‌ها (USD/1M tok، تقریبی، substring-match): offline=0/0، haiku=0.80/4.00، sonnet=3/15، gpt-4o-mini=0.15/0.60، gpt-4o=2.50/10، deepseek-reasoner=0.55/2.19، deepseek=0.27/1.10، پیش‌فرض 1/3. توکن ≈ len/4. `can_spend()` = خرج امروز < daily **و** خرج ماه < monthly. سقف واقعی از env: $1/روز، $30/ماه (پیش‌فرض کلاس 1/20 است ولی main مقادیر config را پاس می‌دهد).

### safety/patch_manager.py
- **سطح ۱** suggest (متن ثابت + ثبت db) · **سطح ۲** `generate_patch`: brain باید LLM باشد (offline → رد)؛ unified diff در `patches/patch_YYYYmmdd-HHMMSS.diff` ذخیره + `patch_suggestion` در db؛ **اجرا نمی‌کند** · **سطح ۳** `apply_patch` → `NotImplementedError` عمدی. هیچ اعتبارسنجیِ محتوای diff (فقط ذخیره‌ی متن خروجی LLM).

### safety/rollback.py
- `backup_file` (کپی زمان‌دار به `backups/`) و `restore_file`. **هیچ call-site در runtime** — حتی `/delete_all_data` از `shutil.copyfile` خودش archive می‌گیرد، نه از rollback. dormant.

### observability
- **tracer.py:** دکوریتور `@trace` + sink؛ sink در main به event_log وصل شده، ولی **`@trace` روی هیچ تابعی اعمال نشده** → trace-eventهای واقعی صفر.
- **event_log.py:** `log_event(db, type, json)` — never-break (هر خطا بلعیده می‌شود). مصرف واقعی: `WorldModel.ingest_manual` و sink بلااستفاده. `/events` آخرین ۱۵ رویداد را نشان می‌دهد (عملاً تقریباً خالی).

---

## 8) Bot — سطح فرمان تلگرام (bot.py ~1915 خط + menus.py)

### امنیت/گیت
- `owner_only`: `str(user.id) != os.environ["OWNER_ID"]` → **سکوت مطلق** (فقط warning در لاگ). OWNER_ID تنبل خوانده می‌شود.
- `guarded` = owner_only + `db.is_halted()` → سکوت. **معاف از halt:** `/halt`, `/resume`, `/status` (فقط owner_only). `on_unknown` هم در halt ساکت است. `morning_ping` هم halt را چک می‌کند.
- kill-switch = `config.halted` در SQLite (پایدار بین restartها).

### گفتگوها (ConversationHandler، همه persistent=True با PicklePersistence)
`/log` (RMSSD[عدد یا RRهای خام→hrv.py]→sleep 1..5→used→loc→note؛ /skip،/cancel) · `/ask` (سؤال CORE→ثبت پاسخ در reflection + register_interaction) · `/checkin` (mood/energy/stress→daily_state) · `/habit` (title→cue→action→نسخه حداقلی) · `/review_daily|weekly|monthly` · `/experiment` (title→hypothesis→intervention→طرح AB/alt/before-after با دکمه) · `/import_muse` (فایل CSV) · `/delete_all_data` (عبارت دقیق `DELETE LANGAR DATA` + archive فایل db).

### فرمان‌های ساده (همه @guarded مگر ذکر)
ناوبری: `/start /menu /help_all` · بدن: `/rmssd /rmssd_help /today /streak /trend [2..90]` · بینش: `/insight /recheck /insights /insight_stats` (verdict با دکمه، write-once، AlreadyJudged→«قبلاً داوری شده») · عادت: `/habits /done /habit_report` · آزمایش: `/experiments /experiment_stop /experiment_report` · کوچ: `/coach` (قاعده‌محور از coach.py) · CORE: `/mind /improve /pending /reflect` · پژوهش: `/research` (**اول pro_client به `LANGAR_PRO_URL`، اگر fallback → researcher محلی**) `/architect /goal /goals /research_verdict <id> <confirmed|refuted>` (نسخه‌بندی‌شده) `/contract` · ایمنی/داده: `/patch /events /export /export_csv /privacy` · AI-Lab: `/ailab /ai_research /ai_digest /ai_architect /ai_memory /ai_benchmark /ai_safety /ai_ideas /ai_roadmap /ai_budget /ai_propose_update` · کنترل: `/status /halt /resume` (معاف).
- callbackها: `tag: verdict: done: expstop: exprep: expday: muse: menu:` · فرمان ناشناخته → `menus.suggest_for_unknown()`.
- پینگ صبحگاهی: `jq.run_daily(morning_ping, LANGAR_PING_HOUR پیش‌فرض 8:00)`.

### ماژول‌های قاعده‌محور بدون AI
- **hrv.py:** RMSSD از RR خام؛ artifact-rejection بازه‌ی 300..2000ms؛ حداقل ۲ فاصله معتبر؛ ارقام فارسی.
- **coach.py:** قواعد deterministic: n_logs<3 → فقط «داده کم»؛ rmssd زیر baseline + خواب کم/مصرف/تنها؛ confirm_rate<0.4 با ≥4 داوری؛ export>21 روز؛ adherence<0.6؛ habit_missed≥3. + DISCLAIMER «تشخیص نیست».
- **ai.py:** موتور سؤالِ *قدیمی* (pre-CORE) — فقط وقتی `_CORE is None` استفاده می‌شود (در main همیشه CORE ست می‌شود → مسیر legacy/fallback).
- **muse.py / menus.py:** ورود CSV (RR دقیق / PPG تقریبی) و منوی ۹ دسته + پیشنهاد فرمان.

### pro_client.py
- پل stdlib-only به بک‌اند `langar-pro` (FastAPI): `LANGAR_PRO_URL` نباشد/خطا → `{"fallback": True}` بدون crash؛ timeout 8s. فقط در `/research` استفاده می‌شود.

---

## 9) استقرار
- **Dockerfile + docker-compose.yml:** restart unless-stopped؛ volume برای `data/`, `patches/`, `logs/`.
- **langar_bot.service:** systemd، User=ubuntu، Restart=always/5s، EnvironmentFile=.env.
- **requirements:** فقط ۴ بسته (ptb[job-queue]==21.6، dotenv، anthropic==0.39.0 اختیاری، openai==1.54.0 اختیاری).
- ⚠️ در پوشه فایل‌های `.env` واقعی، `langar.db`, `langar.db-wal`, `langar_state.pickle` هم commit/کپی شده‌اند (نشتی احتمالی داده/secret در backup).

---

## 10) تناقض‌های اسناد ↔ کد

| # | سند | ادعا | واقعیت کد |
|---|---|---|---|
| 1 | ARCHITECTURE.md §3 | «memory: لایه ۳ (vector) غیرفعال» | لایه ۳ به‌صورت BM25+TF-IDF **پیاده‌سازی و فعال (SEMANTIC_ENABLED=True)** است، ولی **هیچ‌جا مصرف نمی‌شود** — نه vector است نه غیرفعال؛ «موجود ولی dormant». |
| 2 | ARCHITECTURE.md §11 | «BrainRouter — نقشه‌ی آینده #1» | `brain/brain_router.py` **نوشته شده و تست دارد** ولی به runtime وصل نیست؛ tier→model mapping هم وجود ندارد. سند عقب‌تر از کد. |
| 3 | ARCHITECTURE.md | ACE اصلاً ذکر نشده | `core/ace.py` کامل موجود (Reflector/Curator/gates) — فقط در تست اجرا می‌شود. |
| 4 | USAGE.md (بخش قدیمی) | «سه جدول: log، insight، config» و «migrations نسخه‌ی فعلی: ۳» | ۲۳ جدول، schema v8. بخش‌های قدیمی USAGE به‌روز نشده‌اند (خود سند درونی ناسازگار است). |
| 5 | README.md | فقط ۹ دستور نسخه‌ی اولیه | ~۵۰ دستور + ۸ گفتگو در کد. README مربوط به فاز ۰ است. |
| 6 | constitution «۱۴ قانون» (ARCHITECTURE §3، docstring) | ۱۴ قانون به‌عنوان critique | فقط ۴ الگوی regex واقعاً در `critique()` enforce می‌شود؛ بقیه declarative یا در ماژول‌های دیگر. |
| 7 | budget.py docstring | «برای AI-Lab (و کلِ مصرفِ LLM)» | فقط AILab رکورد/enforce می‌کند؛ سؤال روزانه/researcher/patch خارج از حسابداری بودجه‌اند. |
| 8 | ARCHITECTURE §8 «رد شدن همه‌چیز از constitution» | همه‌ی خروجی‌های هوشمند | سؤال روزانه، researcher و ailab گیت می‌شوند؛ خروجی `/patch` (متن diff) و پاسخ‌های coach قاعده‌محور گیت constitution ندارند (کم‌ریسک ولی خلاف ادعای مطلق). |
| 9 | world_model docstring | Apple Health file از `LANGAR_HEALTH_FILE` + آب‌وهوا | هر دو stub؛ weather همیشه None، health-file اصلاً در کد نیست. |
| 10 | ARCHITECTURE §3 | «coach_agent (پیش‌فعال)» جزو agents | CoachAgent ساخته می‌شود ولی رها می‌شود؛ هیچ مسیر proactive واقعی (job/hook) به آن وصل نیست. /coach از coach.py قاعده‌محور است. |
| 11 | observability | «شفافیت و ردگیری» | sink وصل است ولی چون `@trace` هیچ‌جا اعمال نشده، event_log عملاً فقط از ingest_manual پر می‌شود؛ /events تقریباً خالی می‌ماند. |
| 12 | USAGE `/delete_all_data` «حذف کامل داده» | حذف همه | `wipe_all_data` جدول‌های research/ailab/event_log/question_quality/mental_model را پاک نمی‌کند. |

---

## 11) جمع‌بندی وضعیت (implemented vs dormant vs stub)

- **کاملاً implemented و wired:** bot (gate/kill-switch/همه‌ی فرمان‌ها)، db+migrations v8، HumanCore pipeline، MentalModel/Communication/SelfImprover (با job روزانه)، AgentRouter+۳ agent، brain providers (fallback زنجیره‌ای)، QuestionBank، Researcher+source_quality+synthesizer، AILab+Budget (enforce فقط در AILab)، PatchManager سطح ۱/۲، hrv/coach/muse/menus، pro_client bridge، Docker/systemd.
- **implemented ولی dormant (کد هست، مصرف runtime نیست):** BrainRouter، ACELoop، HybridRetriever/search_semantic (لایه ۳ حافظه)، rollback.backup/restore، دکوریتور trace، CoachAgent proactive، Contract (فقط نمایش)، memory لایه ۱.
- **stub عمدی/ناقص:** PatchManager سطح ۳ (NotImplementedError عمدی)، WorldModel.weather و health-file، OfflineSearch (لیست خالی)، `config.cap()` بی‌مصرف.
# Inventory — کدِ واقعیِ langar-pro + فایل‌های ریشه‌ی AI-sume

منبع (ground truth): `C:\Users\Armin\Desktop\backup\04 - Architect System\architect\_code\ai-farm\AI-sume`
تاریخ inventory: 2026-07-03 · همه‌ی فایل‌ها کامل خوانده شدند (READ-ONLY).

---

## بخش ۱ — langar-pro (بک‌اند پژوهش: FastAPI + Postgres/pgvector)

### 1.1 `langar-pro/README.md`
- **چه می‌کند واقعاً:** سندِ معرفی. langar-pro را «نسخه‌ی production از LANGAR» می‌نامد: Agentic RAG + Graph Memory + Constitutional Gate + Human Feedback + Audit Ledger روی FastAPI/Postgres.
- **جزئیات:** قانون طلایی ۶ سطری hard-coded در طراحی: `No source → no fact / No consent → no action / No feedback → no learning / No audit → no trust / No uncertainty → no verdict / AI may recommend; the final value judgment stays with the human.`
- نقشه‌ی ۶ فاز: ۱=اسکلت (FastAPI+Postgres+Redis+schema)، ۲=مهاجرت منطق researcher/constitution و اتصال `/research` واقعی، ۳=Graph Memory روی `claims`/`claim_edges` + pgvector semantic search، ۴=Celery+Redis async + Skeptic agent، ۵=بات تلگرام کلاینتِ این API + داشبورد Next.js، ۶=Neo4j/Qdrant فقط اگر لازم شد.
- رابطه با بات: بات SQLite موازی می‌ماند؛ در فاز ۲ بات به API وصل می‌شود و SQLite فقط cache/آفلاین.
- **وضعیت:** doc. هشدار صریح: «این کد در sandbox تست نشده».
- **تناقض:** README می‌گوید endpointها «اسکلت» فاز ۱ هستند، ولی کدِ `main.py` (v0.2) فاز ۲ را عملاً پیاده کرده (`/research` واقعی با search→score→synthesize→gate). README عقب‌تر از کد است.

### 1.2 `langar-pro/.env.example`
- **مقادیر:** `POSTGRES_PASSWORD`، `DATABASE_URL=postgresql://langar:...@db:5432/langar`، `REDIS_URL=redis://redis:6379/0`، **`OWNER_ID=6150431610`** (آیدی واقعی تلگرام داخل فایل example — نشت جزئی)، `CLAUDE_KEY`، `OPENAI_KEY`، `BRAVE_API_KEY` (اختیاری).

### 1.3 `langar-pro/Dockerfile`
- `python:3.11-slim` → pip install requirements → copy `app/` → `EXPOSE 8000` → `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- **وضعیت:** implemented، مینیمال. توجه: `db/` را copy نمی‌کند (schema فقط از طریق mount در compose به Postgres می‌رسد — درست است).

### 1.4 `langar-pro/docker-compose.yml` (compose مستقلِ فاز ۱)
- **سرویس‌ها:** `db` = **`pgvector/pgvector:pg16`** (user/db=`langar`، port host `5432:5432`، volume `pgdata`، mount `./db/schema.sql` به `/docker-entrypoint-initdb.d/`، healthcheck `pg_isready` هر 5s/3s/10بار) · `redis` = `redis:7-alpine` (port host `6379:6379`) · `api` = build محلی، `8000:8000`، `depends_on db: service_healthy`.
- فازهای بعد کامنت‌شده: qdrant (6333)، neo4j:5 (7474/7687)، celery worker.
- **تناقض:** این فایل **pg16** است، unified **pg15**. همچنین این compose پورت‌های 5432 و 6379 را روی host باز می‌کند در حالی که `CHECKLIST_VPS_FA.md` صریحاً می‌گوید «پورت دیتابیس را به اینترنت باز نکن» — unified درست بسته است، compose مستقل باز.

### 1.5 `langar-pro/requirements.txt`
- **دقیق:** `fastapi==0.115.0`، `uvicorn[standard]==0.30.6`، `psycopg[binary]==3.2.1`، `pydantic==2.9.0`. کامنت: «فازهای بعد: redis، celery، qdrant-client، neo4j، openai، anthropic».
- **تناقض مهم:** `brain.py` داخل `ask()` به `import openai` / `from anthropic import Anthropic` نیاز دارد ولی این پکیج‌ها **نصب نمی‌شوند**. یعنی حتی با کلید LLM، سنتز LLM در کانتینر همیشه fail می‌شود (ImportError → توسط try/except در engine گرفته می‌شود → «سنتز نشد»؛ سیستم degrade می‌شود، crash نه). عملاً مسیر LLMِ langar-pro در Docker **هرگز کار نمی‌کند**.

### 1.6 `langar-pro/db/schema.sql` — ۱۳ جدول + pgvector
- `CREATE EXTENSION vector` (نیاز به image pgvector).
- **جداول:** 
  - `users` (telegram_id unique؛ seed: id=1 با `telegram_id='owner'` تا `/research` بدون خطای FK کار کند + setval)
  - `goals` (user_id, text, status default 'active')
  - `contracts` (یک سطر JSONB per user — قرارداد انسان-AI، version)
  - `sources` (url, title, published_at, quality JSONB [authority/recency/independence/evidence/bias], score REAL)
  - `claims` (text, tag `E/S/P`, confidence, **embedding vector(1536)**)
  - `claim_sources` (M:N claim↔source)
  - `claim_edges` (src, dst, relation `supports/contradicts/depends_on` — Graph Memory سبک به‌جای Neo4j)
  - `decisions` (user_id, question, summary, confidence, risk_level)
  - `verdicts` (decision_id, version INT, verdict, note — **append-only/versioned audit**)
  - `memories` (kind `raw/verified/preference/decision/rejected/contradiction`, embedding vector(1536))
  - `feedback` (decision_id, kind `accept/reject/edit`, note)
  - audit ledger: `agent_runs` (agent, status, info JSONB) · `tool_calls` (tool, args JSONB, ok BOOL) · `constitutional_checks` (text, compliant, violations JSONB)
- **وضعیت:** schema کامل implemented؛ ولی کد فقط به **۶ جدول** می‌نویسد/می‌خواند: users(seed), goals, decisions, verdicts, sources, constitutional_checks. جداولِ `contracts`, `claims`, `claim_sources`, `claim_edges`, `memories`, `feedback`, `agent_runs`, `tool_calls` **هیچ کدی ندارند** (schema-only، برای فاز ۳+).
- embedding با بعد **1536** (سایز OpenAI embeddings) ولی هیچ کدی embedding نمی‌سازد.

### 1.7 `langar-pro/app/main.py` — FastAPI v0.2
- **API endpoints (۶ عدد):**
  1. `GET /health` → تست `SELECT 1`؛ خروجی `{status: ok|degraded, db, golden_rules}` — **GOLDEN_RULES در کد ۵ سطر است** (سطر ششم README یعنی «AI may recommend…» حذف شده).
  2. `POST /goals` (body: user_id, text) → insert، برگرداندن id.
  3. `GET /goals/{user_id}` → لیست goals.
  4. `POST /research` (body: `user_id`, `question`, `target` default **"armin"** | "self") → پایپ‌لاین کامل: `get_search_provider(settings)` + `get_brain(settings)` → `run_research()` → insert `decisions` (confidence=**None** — هرگز محاسبه نمی‌شود؛ summary بریده به 2000 کاراکتر؛ risk_level از uncertainty.level) → insert هر source دارای url به `sources` (**بدون لینک به decision — سطرهای orphan؛ claim/claim_sources ساخته نمی‌شود**) → insert `constitutional_checks` → insert `verdicts` نسخه‌ی ۱ با مقدار `'pending'` و note شامل target/provider/search → پاسخ JSON با `decision_id, brief, sources, uncertainty, compliant, next_step, verdict_endpoint`.
  5. `POST /decisions/{id}/verdict` (body: verdict `confirmed|refuted|revised`, note) → نسخه‌ی جدید append (تاریخچه تغییرناپذیر).
  6. `GET /decisions/{id}/verdicts` → تاریخچه‌ی نسخه‌ها.
- **وضعیت:** implemented و واقعی (به‌شرط Postgres روشن). Human-in-the-loop از طریق verdict endpoint واقعی است.

### 1.8 `langar-pro/app/config.py`
- فقط از env: `DATABASE_URL` (default `postgresql://langar:changeme@db:5432/langar`)، `REDIS_URL` (default `redis://redis:6379/0`)، `OWNER_ID`، `CLAUDE_KEY`، `OPENAI_KEY`، `OPENAI_BASE_URL`، `BRAVE_API_KEY`، `SERPAPI_KEY`، `SEARCH_PROVIDER` (default `auto`).
- **تناقض:** `OPENAI_MODEL` و `BRAIN_PROVIDER` که در `.env.example` ریشه هستند، **اینجا خوانده نمی‌شوند** — مدل OpenAI همیشه default کد (`gpt-4o-mini`) می‌ماند و BRAIN_PROVIDER بی‌اثر است (انتخاب brain فقط بر اساس وجود کلید). `redis_url` خوانده می‌شود ولی **هیچ کدی از Redis استفاده نمی‌کند** (پکیج redis هم نصب نیست) — Redis صرفاً کانتینر روشنِ بلااستفاده برای فاز ۴.

### 1.9 `langar-pro/app/db.py`
- psycopg3، `dict_row`، **connection-per-request** (بدون pool)، commit/rollback خودکار در contextmanager. `fetchone/fetchall/execute` (execute اگر RETURNING نبود None). implemented، ساده.

### 1.10 `langar-pro/app/research/brain.py` — لایه‌ی LLM
- ۳ کلاس: 
  - `OfflineBrain` (name=`offline`) — بدون LLM: فهرست خام ۵ نتیجه + تگ `[S] آزموده‌نشده`.
  - `OpenAICompatBrain` (name=`openai`) — default model **`gpt-4o-mini`**، `max_tokens=400`، base_url قابل‌تنظیم (OpenAI-compatible).
  - `AnthropicBrain` (name=`anthropic`) — default model **`claude-haiku-4-5-20251001`**، `max_tokens=400`.
- prompt user: سؤال + target + حداکثر ۵ نتیجه (title: snippet).
- `get_brain(settings)`: اولویت Anthropic (اگر `claude_key` یا `anthropic_key`) → OpenAI → Offline. (باگ ظریف: شرط `anthropic_key` را چک می‌کند ولی همیشه `settings.claude_key` را pass می‌دهد.)
- **وضعیت:** implemented ولی در Docker به‌خاطر requirements ناقص، دو مسیر LLM عملاً مرده‌اند (فقط Offline کار می‌کند).

### 1.11 `langar-pro/app/research/engine.py` — orchestrator (خالص)
- **پایپ‌لاین واقعی:** `search.search(q)` → `source_quality.rank(results, q)` → `source_quality.uncertainty(ranked)` → `brain.ask(SYS,...)` (با try/except؛ خطا → «سنتز نشد… [S]») → `constitution.critique(brief)` → اگر non-compliant: brief جایگزین می‌شود با «⚠️ خروجی با قوانین سازگار نبود — طبق "در شک: سکوت" حذف شد».
- system prompt (SYS): «پژوهشگر محتاط LANGAR… هر ادعا تگ [E]/[S]/[P]، ارجاع با شماره، علیت تحمیل نکن، پزشک نیستی… در پایان ادعای آزمون‌پذیر بده».
- خروجی: dict با question/target/brief/sources(top-5 با _score)/uncertainty/compliant/violations/`next_step` (اگر target=="armin": «آزمایش N-of-1 بساز»؛ وگرنه: «diff سطح ۲ برای بازبینی انسان»).
- **وضعیت:** implemented، تابع خالص، تست‌پذیر.

### 1.12 `langar-pro/app/research/constitution.py` — گذرگاه قانون اساسی
- `PRINCIPLES`: فهرست **۱۴ قانون** (در شک: سکوت / RMSSD شاخص قفل‌شده / verdict برگشت‌ناپذیر / همبستگی≠علیت / تگ قطعیت / پزشک نیستیم / تقویت نشخوار ممنوع / عادی‌سازی خودتخریبی ممنوع / صداقت N-of-1 / حوزه‌ی مهندسی هفتگی / خودبهبود شفاف / تغییر خودکار فقط وزن / حریم خصوصی / تناسب ارتباط).
- **enforcement واقعی فقط ۴+۱ چک regex است:** متن خالی؛ `_MEDICAL` (قانون ۶: تجویز/تشخیص/قرص بخور…)؛ `_CAUSAL` بدون `_HEDGE` (قانون ۴: علیت بدون شاید/ممکن/احتمال…)؛ `_RUMINATION` (قانون ۷: «چرا همیشه/بدترین آدم…»)؛ `_SELF_HARM_OK` (قانون ۸: عادی‌سازی آسیب/نخوردن/نخوابیدن). نرمال‌سازی ي→ی، ك→ک، حذف اعراب.
- **تناقض:** ادعای «۱۴ قانون آهنین» ولی فقط ۴ قانون machine-checked؛ ۱۰ تای دیگر فقط لیست متنی‌اند.

### 1.13 `langar-pro/app/research/search_providers.py`
- رابط مشترک `BaseSearchProvider` (search(query, k=5) → list[{title,url,snippet}]، is_available، name). فقط stdlib urllib، timeout **10s**.
- `OfflineSearch` → `[]` · `BraveSearch` → `api.search.brave.com/res/v1/web/search` با header `X-Subscription-Token`، count=k · `SerpApiSearch` → `serpapi.com/search.json`، num=k.
- factory `get_search_provider`: `SEARCH_PROVIDER` ∈ offline/brave/serpapi/auto؛ auto = brave اول، بعد serpapi، بعد fallback offline.
- **وضعیت:** implemented کامل.

### 1.14 `langar-pro/app/research/source_quality.py` — امتیازدهی قطعی (بدون شبکه)
- **مقادیر دقیق:**
  - authority (۰..۵): domain در `_HIGH` (pubmed/ncbi/arxiv/nature/sciencedirect/cochrane/who.int/nih.gov/cell/thelancet/nejm/bmj/jamanetwork/crossref) → **5**؛ `_MED` (.gov/.edu/wikipedia/nasa/europa.eu/oecd/.org/reuters/apnews/bbc/ieee) → **3**؛ `_LOW` (medium/reddit/quora/blogspot/wordpress/substack/facebook/twitter/x.com/pinterest) → **1**؛ سایر → **2**.
  - evidence: regex قوی (meta-analysis/systematic review/randomized/RCT/cochrane/فراتحلیل/کارآزمایی) → **5**؛ ضعیف (opinion/blog/به نظر من/sponsored…) → **1**؛ خنثی → **3**.
  - relevance ۰..۵: کسر تطابق کلمات query (>2 حرف) × ۵.
  - bias: پترن تجاری (buy/shop/خرید/تخفیف…) → **−3**، وگرنه 0.
  - score نهایی = clamp((authority+evidence+relevance+bias)/**15**, 0..1)، رند ۲ رقم.
- `rank()`: افزودن `_score`/`_quality` و مرتب‌سازی نزولی.
- `uncertainty()`: بدون منبع → **high**؛ `top>=0.7 && n_good>=2` (good یعنی score≥**0.6**) → **low**؛ `top>=0.5` → **medium**؛ وگرنه **high**.
- **وضعیت:** implemented، خالص و قطعی.

### 1.15 `langar-pro/app/research/synthesizer.py`
- سنتزکننده با prompt مشابه engine.SYS + مسیر آفلاین.
- **وضعیت: dead code / stub بازمانده از مهاجرت.** در `__init__.py` export نمی‌شود، `engine.py` استفاده‌اش نمی‌کند، و امضای `brain.ask(SYS, {"domain":...})` که صدا می‌زند متعلق به brainِ باتِ langar است نه `brain.py` این پکیج — اگر صدا زده می‌شد، خطا می‌داد.

### 1.16 `langar-pro/app/research/__init__.py`
- export: `run_research`, `get_brain`, `get_search_provider`, `constitution`, `source_quality`. (synthesizer عمداً/سهواً غایب.)

---

## بخش ۲ — فایل‌های ریشه‌ی AI-sume (deploy / docs)

### 2.1 `docker-compose.unified.yml` — توپولوژی استقرار واقعی
- **۴ سرویس روی شبکه‌ی bridge `langar-net`، همه `restart: unless-stopped`:**
  1. `bot` (container `langar-bot`) — build `./langar`؛ env: `.env` + `LANGAR_PRO_URL=http://api:8000`؛ `depends_on api: service_started`؛ **volumes:** `./langar/data:/app/data`, `./langar/patches:/app/patches`, `./langar/logs:/app/logs`؛ **بدون پورت host** (تلگرام outbound).
  2. `api` (container `langar-pro-api`) — build `./langar-pro`؛ **پورت `8000:8000`** (تنها پورت باز روی host)؛ `depends_on db: service_healthy`؛ فرمان uvicorn.
  3. `db` (container `langar-pro-db`) — image **`pgvector/pgvector:pg15`**؛ POSTGRES_USER/DB=`langar`؛ volume `pgdata` + mount `./langar-pro/db/schema.sql` init؛ healthcheck pg_isready (5s/3s/10)؛ **بدون پورت host**.
  4. `redis` (container `langar-redis`) — `redis:7-alpine`، volume `redisdata`، **بدون پورت host**، فعلاً بلااستفاده در کد.
- **volumes named:** `pgdata`, `redisdata`.
- **تناقض:** pg15 اینجا vs pg16 در compose مستقل langar-pro.

### 2.2 `.env.example` (ریشه)
- **متغیرها:** `BOT_TOKEN`, `OWNER_ID` (اجباری)؛ `POSTGRES_USER/PASSWORD/DB`, `DATABASE_URL` (رمز باید یکسان)؛ `BRAIN_PROVIDER=auto`, `CLAUDE_KEY`, `OPENAI_KEY`, `OPENAI_BASE_URL=https://api.openai.com/v1`, `OPENAI_MODEL=gpt-4o-mini`؛ `SEARCH_PROVIDER=auto`, `BRAVE_API_KEY`, `SERPAPI_KEY`؛ **`AILAB_DAILY_BUDGET_USD=1`, `AILAB_MONTHLY_BUDGET_USD=30`** (سقف بودجه — مصرف‌کننده‌اش باتِ langar است نه pro)؛ `LANGAR_PING_HOUR=8`. نکته‌ی صریح: `LANGAR_PRO_URL` را نگذار، compose خودش می‌دهد.
- **تناقض:** `BRAIN_PROVIDER` و `OPENAI_MODEL` توسط config.py langar-pro خوانده نمی‌شوند (احتمالاً فقط بات می‌خواند).

### 2.3 `deploy.sh` (ریشه)
- **جریان:** چک docker/compose/engine/فایل compose → اگر `.env` نیست از example بساز و exit (با پیام پرکردن BOT_TOKEN/OWNER_ID/POSTGRES_PASSWORD) → **گاردریل:** grep placeholderهای فارسی (`توکن|آیدی|یک_رمز|خالی`) — اگر پیش‌فرض مانده exit 1 → `compose up -d --build` → تا **30×2s=60s** انتظار برای `curl /health` → شمارش سرویس‌های running (انتظار **4/4**) → راهنمای تست دستی (`/start · /menu · /halt→/resume · /research · /ailab`). هیچ کلیدی چاپ نمی‌کند، چیزی حذف نمی‌کند.
- **وضعیت:** implemented.

### 2.4 `SETUP_PROMPT.md`
- پرامپت آماده برای عامل (Claude Code/Cursor/Cowork): مراحل ۰ (بررسی ساختار+Docker) → ۱ (.env با ۶ متغیر، chmod 600، چک gitignore) → ۲ (compose up؛ **اینجا pg15 ذکر شده**) → ۳ (**۷ تست پذیرش:** health، /start و /menu، kill-switch /halt→/resume، «/research → منبع: langar-pro · decision #…»، **تست fallback: stop api → /research → «منبع: محلی» بدون crash**، /ailab و /ai_budget، restart-پایداری) → ۴ (بکاپ: `langar/data/langar.db` + pg_dump + patches/؛ .env رمزگذاری‌شده).
- قوانین سخت عامل: حذف/بازنویسی ممنوع، کلید در لاگ ممنوع، اجازه قبل از کار مخرب.

### 2.5 `START_HERE_FA.md`
- گزارش مرحله‌ی ۰ از یک اجرا: تأیید ساختار (langar/ شامل `bot.py, agents/, core/, brain/, researcher/, observability/, safety/, tests/`؛ langar-pro/؛ unified compose؛ مستندات CHECKLIST/ARCHITECTURE/PLAN/DEPLOYMENT_GUIDE_FA). کمبودها: `.env` ریشه نیست، Docker در sandbox نیست، git repo ساخته نشده، **یک `.git` نیمه‌خراب باقی مانده که باید دستی پاک شود**. 
- **هشدار امنیتی مستند:** سه فایل با کلید واقعی موجودند: `langar/.env` · `langar/env` · `langar-pro/.env` (gitignore محافظت می‌کند ولی قبل از push چک شود؛ توصیه‌ی revoke توکن BotFather اگر zip جای ناامن رفته).

### 2.6 `UPGRADES_FA.md` (۲۰۲۶-۰۶-۲۸)
- ارتقاهای سمتِ **بات langar** (نه pro): 
  1. `langar/core/retrieval.py` — بازیابی ترکیبی محلی: **BM25 (sparse) + TF-IDF cosine (dense) + min-max fusion**، فارسی‌آگاه، بدون کلید/embedding؛ وصل به `core/memory.py::search_semantic()` روی reflection/log.
  2. `langar/brain/brain_router.py` — **BrainRouter**: رده‌بندی task به `simple/react/plan/deliberate`، انتخاب مدل `cheap/strong`، downgrade امن با بودجه کم/آفلاین (fail-degraded).
  3. `langar/core/ace.py` — حلقه‌ی **ACE: Generator→Reflector→Curator**؛ فقط proposal با `status="pending"` در db؛ **هرگز خودکار اعمال نمی‌شود** (`applied_automatically=False`، HITL).
  4. `langar/tests/test_upgrades.py` — **۲۲/۲۲ تست سبز** بدون pytest.
- نگاشت به ۸ گاردریل: kill-switch، owner-only، Constitution (۱۴ قانون regex)، budget cap، privacy local-first، no-self-edit، data separation، audit.
- **صداقت مستند (شکاف‌ها):** BrainRouter در حلقه‌ی `bot.py` (۱۹۰۰ خطی) **سیم‌کشی نشده**؛ جمع‌آوری Outcomeهای ACE به bot وصل نشده؛ retrieval فقط روی reflection/log.

### 2.7 `CHECKLIST_VPS_FA.md`
- **جریان VPS:** ۰) انتخاب سرور — حداقل 2GB RAM (راحت 4GB)، دیسک ~20GB؛ **Hetzner CX22 (2vCPU/4GB/40GB، ~€4.35/ماه) پیشنهاد اصلی**؛ Oracle Always Free (2 OCPU/12GB ARM، رایگان)؛ Ubuntu 24.04 → ۱) SSH → ۲) `curl -fsSL https://get.docker.com | sudo sh` → ۳) امنیت: `ufw allow OpenSSH; ufw enable`؛ **5432 هرگز باز نشود؛ 8000 فقط در صورت نیاز** → ۴) انتقال با WinSCP یا git clone → ۵) `.env` → ۶) `compose up -d --build`؛ ۴ کانتینر Up → ۷) تست‌های پذیرش → ۸) بکاپ cron (**`langar/langar.db`** + pg_dump + patches/).
- هزینه: VPS ~$5/ماه ضروری؛ LLM با سقف **~$1/روز** اختیاری؛ Brave پلن رایگان.
- **تناقض ریز:** مسیر بکاپ SQLite اینجا `langar/langar.db` ولی SETUP_PROMPT می‌گوید `langar/data/langar.db` (volume compose هم `./langar/data` است — CHECKLIST قدیمی‌تر/غلط).

### 2.8 `GITHUB_PUSH_FA.md`
- جریان push: پاک‌کردن `.git` نیمه‌خراب → `git init/add/status` (چک نبودن .env/.db) → commit → راه A: `gh repo create langar --private --source=. --push` / راه B: دستی با PAT → کلون روی VPS → `cp .env.example .env` → `bash deploy.sh`. مسیر کاری مستند: `C:\Users\Armin\Documents\Claude\Projects\AI Farm\AI-sume`.

### 2.9 `one-liner-vps-setup.sh`
- **چه می‌کند واقعاً:** اسکریپت heredoc که به `ssh root@`**`49.12.191.229`** (IP واقعی Hetzner hard-coded) وصل می‌شود و روی VPS: می‌پرسد GH_USER/GH_EMAIL/GH_TOKEN → در `~/langar` به‌صورت inline می‌سازد: `.gitignore` سخت‌گیر، **کپیِ کامل docker-compose.unified.yml**، `.env.example` (نسخه با placeholder انگلیسی `changeme`)، **deploy.sh ساده‌شده (بدون گاردریل placeholder)** → git init/config/add/commit → push به `github.com/<USER>/langar` با token در URL.
- **وضعیت/نقص:** implemented ولی **ناقص منطقی:** سورس `langar/` و `langar-pro/` را نمی‌آورد؛ پس `docker compose up --build` روی چیزی که این اسکریپت می‌سازد fail می‌شود (build ./langar وجود ندارد) مگر اینکه repo قبلاً pull شده باشد. نمونه‌ی username/email واقعی در پیام‌ها (`australianpmnsw`, `arminoal4@gmail.com`). token در remote URL ذخیره می‌شود (ریسک در `.git/config`).

### 2.10 `setup-github-vps.sh`
- نسخه‌ی تعاملی روی خود VPS: clone یا init در `~/langar`، config، add، **`git status` + تأیید دستی انسان که .env/.db در لیست نیست**، commit با پیام «LANGAR unified: core + langar-pro + upgrades (retrieval/BrainRouter/ACE)»، push به main. همان ریسک token-در-URL.

### 2.11 `New Text Document.txt`
- **چه می‌کند واقعاً:** transcript/لاگ چت از جلسه‌ی ساختِ اتصال بات↔pro. حاوی حقایق مهم درباره‌ی **سمت بات (langar)** که در این root نیست:
  - `langar/pro_client.py` — کلاس `ProClient` با stdlib (urllib/json/os)، **timeout ۸ ثانیه**؛ سه حالت تست‌شده: بدون `LANGAR_PRO_URL` → `{"fallback":true,"reason":"no_langar_pro_url"}`؛ سرور خاموش → fallback بدون crash؛ موفق → پاسخ pro + `source:"langar-pro"`.
  - سیم‌کشی `/research` در bot.py: اول ProClient، اگر fallback → researcher محلی؛ منبع (pro/محلی) به کاربر نمایش داده می‌شود.
  - دلیل انتخاب pgvector/pgvector:pg15 به‌جای postgres:15-alpine (extension vector).
  - اعتراف صادقانه‌ی مهم: «برای یک کاربر، این اتصال بیشتر یک تمرین معماری است تا نیاز واقعی — researcher محلی بات به‌تنهایی همان کار را می‌کند».
- **وضعیت:** doc/log، نه کد.

---

## بخش ۳ — جمع‌بندی تناقض‌ها (docs vs code / pro vs langar)

1. **requirements ناقص:** brain.py به openai/anthropic نیاز دارد؛ نصب نمی‌شوند → مسیر LLM در Docker همیشه به «سنتز نشد» degrade می‌شود. **langar-pro در عمل فقط offline-synthesis می‌دهد.**
2. **pg16 vs pg15:** compose مستقل langar-pro `pgvector:pg16`؛ unified و SETUP_PROMPT `pg15`.
3. **پورت‌های باز:** compose مستقل 5432/6379 را روی host publish می‌کند؛ CHECKLIST صریحاً می‌گوید 5432 باز نشود؛ unified درست بسته است.
4. **README فاز ۱ vs کد فاز ۲:** README endpointها را «اسکلت» می‌نامد؛ main.py v0.2 پایپ‌لاین واقعی دارد.
5. **«۱۴ قانون» vs ۴ چک regex:** constitution فقط قوانین ۴/۶/۷/۸ (+متن خالی) را enforce می‌کند.
6. **schema ≫ کد:** ۷ جدول (contracts/claims/claim_sources/claim_edges/memories/feedback/agent_runs/tool_calls) و ستون‌های embedding(1536) هیچ مصرف‌کننده‌ای ندارند؛ `confidence` در decisions همیشه NULL؛ sources بدون FK به decision (orphan).
7. **synthesizer.py مرده** و امضای brainِ باتِ langar را صدا می‌زند نه brain خودش — بقایای مهاجرت از `researcher/` بات.
8. **env متغیرهای بی‌مصرف در pro:** `BRAIN_PROVIDER`, `OPENAI_MODEL`, `REDIS_URL` (Redis روشن ولی بلااستفاده تا فاز ۴).
9. **GOLDEN_RULES:** README ۶ سطر، main.py ۵ سطر.
10. **مسیر بکاپ SQLite:** `langar/langar.db` (CHECKLIST) vs `langar/data/langar.db` (SETUP_PROMPT/compose volume).
11. **نشت جزئی داده‌ی شخصی:** OWNER_ID واقعی (6150431610) در .env.example؛ IP واقعی VPS (49.12.191.229) و username/email در اسکریپت‌ها؛ START_HERE تأیید می‌کند سه فایل .env با کلید واقعی در پروژه موجودند.
12. **one-liner-vps-setup.sh** بدون سورس langar/langar-pro عملاً deploy-پذیر نیست (فقط اسکلت repo می‌سازد).
13. **UPGRADES:** BrainRouter/ACE ساخته و تست‌شده ولی به حلقه‌ی bot.py سیم‌کشی نشده‌اند (شکاف مستندشده، صادقانه).

## بخش ۴ — رابطه‌ی langar-pro با langar (مدل نهایی)
- **langar (بات تلگرام، SQLite، این root ندارد ولی مستند است):** چهره‌ی کاربر؛ researcher محلی خودش را دارد؛ ارتقاهای retrieval/BrainRouter/ACE در آن است.
- **langar-pro:** بک‌اند پژوهش HTTP (این فایل‌ها)؛ persistence در Postgres با audit/verdict نسخه‌بندی‌شده.
- **اتصال:** bot → `LANGAR_PRO_URL=http://api:8000` → `ProClient` (timeout 8s) → `/research`؛ اگر pro خاموش → fallback خودکار به researcher محلی. pro هرگز به تلگرام مستقیم وصل نیست؛ bot هرگز به Postgres مستقیم وصل نیست. دو DB موازی: SQLite (بات) + Postgres (pro).
# اینونتوری کد — ai-farm / fusion-mvp + fusion-safety

تاریخ اینونتوری: 2026-07-03 · مبنا: خواندن کامل کد واقعی (ground truth). READ-ONLY.

ریشه‌ها:
- `C:\Users\Armin\Desktop\backup\04 - Architect System\architect\_code\ai-farm\fusion-mvp`
- `C:\Users\Armin\Desktop\backup\04 - Architect System\architect\_code\ai-farm\fusion-safety`

---

## نمای کلی سیستم

**fusion-mvp** یک سیستم multi-agent research assistant است با تمرکز روی «کنترل و ایمنی» نه کیفیت تحقیق. سه ایجنت (Researcher → Analyst → پنل ۳داور) + لایه‌های کنترل: budget، kill-switch، HITL، guardrail، audit hash-chain، و یک **IGK** (Immutable Grounding Kernel) به‌صورت process جدا. حلقه‌ی self-improvement فقط روی **متن system prompt** است (`self_update.py`)، با eval کیواژه‌ای و rollback خودکار.

**fusion-safety** مخزن سندهای ایمنی است (GAP-AUDIT، THREAT-MODEL، RECONCILIATION، PROMPT-complete-and-test + ۵ PDF کانن) — هیچ کدی ندارد؛ audit مکتوبِ همان کد fusion-mvp است.

**نکته‌ی بنیادی:** کل سیستم عملاً فقط در حالت **MOCK** اجرا شده است. `LLMClient` بدون `ANTHROPIC_API_KEY` به mock می‌رود؛ خود CHECKLIST.md اذعان می‌کند «حالت LIVE اجرا نشده». تمام ۴۰ تست سبز روی mock هستند.

---

## ۱) config.py — «قانون مبنا»

- **مسیر:** `fusion-mvp/config.py`
- **چه می‌کند واقعاً:** همه‌ی ثابت‌های کنترل: مدل، بودجه، ابزار مجاز، اقدام حساس، فلگ‌های IGK، denylist خوداپدیتی.
- **مقادیر دقیق:**
  - `MODEL = "claude-sonnet-4-6"` · `MAX_TOKENS_PER_CALL = 1024`
  - قیمت local cost-accounting: input `$3.0/MTok`، output `$15.0/MTok`
  - `GLOBAL_BUDGET_USD = 0.50` · per-agent: researcher `0.20`, analyst `0.20`, supervisor `0.10`, panel `0.15`
  - `MAX_STEPS = 8` (**dead config — هیچ‌جا استفاده نمی‌شود**) · `MAX_CALLS_PER_AGENT = 3`
  - `JUDGES = [strict, lenient, balanced]` · `PANEL_QUORUM = 2` (۲ از ۳)
  - `HITL_REQUIRED_FOR = {"finalize", "external_write"}` (external_write هیچ‌جا صدا زده نمی‌شود)
  - `AGENT_ALLOWED_TOOLS`: researcher→{web_search_mock}، analyst→{summarize}(**ابزار summarize اصلاً در TOOLS ثبت نشده**)، supervisor→{approve,reject,halt}(ثبت‌نشده)، panel→∅
  - `USE_IGK = True` · **`GROUNDING_REQUIRED = False`** (گیت grounding به‌صورت پیش‌فرض فقط گزارشی است، نه مسدودکننده)
  - `MAX_UPDATE_ROUNDS = 4` · `FORBIDDEN_IN_PROMPT` = ۹ عبارت (ignore previous، بدون تأیید، kill-switch را غیرفعال، …)
- **وضعیت:** implemented؛ `MAX_STEPS` و ابزارهای summarize/approve/reject/halt صرفاً declarative.

## ۲) run.py — ورودی CLI

- **مسیر:** `fusion-mvp/run.py`
- **چه می‌کند واقعاً:** `.env` را دستی لود می‌کند (بدون dotenv)، فلگ‌های `--auto-approve` / `--auto-reject` را به‌صورت lambda approver به Orchestrator تزریق می‌کند و `orch.run(topic)` را صدا می‌زند.
- **وضعیت:** implemented.

## ۳) src/orchestrator.py — جریان اصلی

- **مسیر:** `fusion-mvp/src/orchestrator.py`
- **جریان دقیق `run(topic)`:**
  1. `_kguard("researcher")` → اگر IGK فعال: `kernel.status()` و اگر `stopped` → `PermitDenied`؛ وگرنه `ks.check()` cooperative
  2. `researcher.run(topic)` → tool `web_search_mock` از Gateway + یک کال مدل
  3. `_kguard("analyst")` → `analyst.run(findings)`
  4. `guardrails.check_output(analysis)` → رد = halt
  5. `panel.review(analysis)` → approved / rejected / **split → escalation به HITL** (`panel_override`)
  6. اگر IGK: `kernel.ground(claims, "researcher")` روی **خطوط findings با طول ≥8** — نتیجه چاپ می‌شود؛ فقط اگر `GROUNDING_REQUIRED=True` رد باعث halt
  7. HITL gate برای `finalize`
  8. اگر IGK: `gate.act("finalize", lambda: None)` — permit→consume fail-closed، ولی **fn واقعی یک no-op است**
  9. audit `run_done` + `verify_chain()`
- **مسیرهای توقف:** `PermitDenied`، `KillSwitchError`، `BudgetExceeded`، `ToolPermissionError` → همگی `_stop` با ثبت `run_halted`.
- **نکته‌ی مهم:** اگر IGK بالا نیاید، با یک warning به حالت **cooperative برمی‌گردد** (`use_igk=False`) — یعنی fallback عملاً fail-open نسبت به کرنل. Supervisor ساخته می‌شود ولی **`supervisor.review` دیگر در جریان صدا زده نمی‌شود** (پنل جایش را گرفته؛ کد مرده).
- **وضعیت:** implemented (mock-tested).

## ۴) src/agents.py — Researcher / Analyst / Supervisor

- **مسیر:** `fusion-mvp/src/agents.py`
- **جزئیات:** کلاس پایه `Agent._think`: هر کال مدل = `ks.check()` → `ledger.precheck` → `llm.complete(system_prompt(), prompt)` → `ledger.record` → audit `agent_call`. `system_prompt()` نسخه‌ی active از PromptStore را می‌خواند (اتصال خوداپدیتی به اجرا — واقعی است).
- Researcher تنها ایجنتی است که tool صدا می‌زند. Supervisor.review در حالت MOCK نتیجه‌ی مدل را **override می‌کند**: `approved = "reject" not in analysis.lower()`.
- **وضعیت:** implemented؛ Supervisor در جریان فعلی dead path.

## ۵) src/panel.py + src/providers.py — پنل چندداور

- **مسیر:** `fusion-mvp/src/panel.py`, `src/providers.py`
- **چه می‌کند واقعاً:** ۳ داور (strict/lenient/balanced) round-robin روی providerها. هر `vote`: ks.check + budget precheck("panel") + **یک کال مدل که خروجی‌اش دور ریخته می‌شود** — رأی واقعی از `_decide` می‌آید: هیوریستیک قطعی روی متن analysis:
  - strict: `has_caveat AND len≥40` · lenient: `len≥15` · balanced: `has_caveat OR len≥40`
  - caveat = وجود «راستی‌آزمایی» یا «احتیاط»
- تصمیم: `yes ≥ 2` → approved؛ `yes == 0` → rejected؛ وگرنه `split` → HITL.
- `make_providers()`: در MOCK سه LLMClient جدا با نام mock-A/B/C (**تنوع اسمی؛ رفتار یکسان**)؛ در LIVE فقط `[("anthropic", base)]` — **تک-provider**.
- **وضعیت:** implemented ولی «LLM judging» عملاً cosmetic است (هزینه‌ی توکن مصرف می‌شود، تصمیم کیواژه‌ای است). multi-provider واقعی stub.

## ۶) src/budget.py — اجرای بودجه

- **مسیر:** `fusion-mvp/src/budget.py`
- **مکانیک:** `precheck` (قبل از کال): سقف تعداد کال (۳) و سقف دلاری per-agent و global → `BudgetExceeded`. `record` (بعد از کال): هزینه با نرخ ثابت config محاسبه و اگر از سقف عبور کند دوباره exception. برای ایجنت بی‌نامِ خارج از config، cap=0.0 → عملاً fail-closed.
- **وضعیت:** implemented و تست‌شده. توجه: قیمت hard-coded محلی است نه از API؛ در LIVE اگر قیمت واقعی فرق کند حسابداری خطا دارد.

## ۷) src/killswitch.py + src/hitl.py

- **KillSwitch:** دو مسیر trip: نرم‌افزاری (`trip(reason)`) و فایل بیرونی `logs/STOP`. `check()` باید **داوطلبانه** صدا زده شود → cooperative / fail-open (همان نقد GAP-AUDIT معیار ۱). `reset()` فایل STOP را هم پاک می‌کند.
- **HITLGate:** `requires_approval` روی `HITL_REQUIRED_FOR`؛ approver پیش‌فرض = پرسش کنسولی (`y/yes/بله/آره`)؛ approver تزریقی برای تست/auto-approve. هر request/decision در audit ثبت می‌شود.
- **وضعیت:** implemented؛ درون-process و cooperative (خود سندها اذعان دارند).

## ۸) src/tools.py — ToolGateway / least-privilege

- **مسیر:** `fusion-mvp/src/tools.py`
- **مکانیک:** تنها نقطه‌ی اجرای ابزار؛ چک `AGENT_ALLOWED_TOOLS` → `ToolPermissionError` + audit `tool_denied`. **فقط یک ابزار واقعی وجود دارد: `web_search_mock`** که متن ثابت آفلاین برمی‌گرداند (۳ «منبع» ساختگی). هیچ MCP/API/sandbox واقعی نیست.
- **وضعیت:** مکانیزم مجوز implemented؛ خود ابزارها stub.

## ۹) src/guardrails.py + src/evals.py

- **guardrails.check_output:** رد اگر خالی/`len<15`، یا واژه‌ی مشکوک (`اثبات‌نشده/نامطمئن/شایعه`) بدون caveat (`راستی‌آزمایی/احتیاط`). همین.
- **evals.score_prompt:** rubric کیواژه‌ای per-role (researcher ۵ معیار، analyst ۴، supervisor ۳؛ وزن مساوی؛ نمره ۰..۱ = نسبت معیارهای دارای کیواژه). **فقط متن پرامپت را می‌شمارد، نه رفتار مدل را.**
- **evals.evaluate_findings:** رد اگر `len<15` یا هیچ «منبع/منابع» در متن — باز کیواژه‌ای.
- **وضعیت:** implemented ولی حداقلی/keyword-based — GAP-AUDIT همین را «تله‌ی internal-consistency و مغناطیس Goodhart» می‌نامد.

## ۱۰) حلقه‌ی self-improvement — self_update.py + optimizer.py + prompt_store.py

- **مسیرها:** `fusion-mvp/self_update.py`, `src/optimizer.py`, `src/prompt_store.py`, `prompts.json`
- **حلقه‌ی واقعی (per-agent، حداکثر ۴ دور):**
  1. `score_prompt` روی پرامپت فعال → نمره + معیارهای جاافتاده
  2. تا وقتی `missing` هست: `Optimizer.propose_fix` = **الصاق جمله‌ی قالبی از دیکشنری ثابت `SUGGESTIONS`** (نه LLM). سپس یک‌بار `propose_explore` = بازنویسی عمداً بدترکننده (حذف «اختصار») برای نمایش rollback.
  3. **گیت ۱ — guardrail:** `validate_prompt`: طول 20..2000، وجود نشانه‌ی نقش (Researcher/Analyst/Supervisor)، عدم وجود `FORBIDDEN_IN_PROMPT` (substring match ساده).
  4. نسخه‌ی جدید در PromptStore ثبت → نمره‌ی جدید.
  5. **گیت ۲ — معیار promotion:** فقط `new_score > score` نگه داشته می‌شود؛ وگرنه `store.rollback` خودکار.
  6. kill-switch در ابتدای هر دور؛ همه‌چیز در audit hash-chain ثبت می‌شود.
- **PromptStore:** JSON نسخه‌دار (`prompts.json`): هر نسخه {v, prompt, ts, note, score}؛ `active` pointer؛ rollback = `active -= 1` بدون حذف تاریخچه. Orchestrator نسخه‌ی active را در اجرا می‌خواند → بهبودها persistent هستند.
- **مقادیر:** MAX_UPDATE_ROUNDS=4؛ معیار promotion = بهبود strict نمره‌ی rubric؛ prompts.json فعلی فقط baseline v1 هر سه ایجنت (score=null).
- **وضعیت:** حلقه implemented و تست‌شده، ولی **optimizer قطعی/قالبی است نه LLM-driven** (docstring می‌گوید در LIVE می‌توان Claude گذاشت — نشده)، و eval همان rubric کیواژه‌ای است که optimizer دقیقاً کیواژه‌های همان rubric را الصاق می‌کند → **بهبود نمره تعریفاً تضمینی/خودارجاع است (Goodhart by construction)**. هیچ eval روی رفتار/خروجی واقعی ایجنت در حلقه نیست. held-out هیچ نقشی در promotion پرامپت ندارد.

## ۱۱) src/tracing.py + src/langfuse_sink.py + dashboard.py

- **AuditLog:** JSONL append-only + hash-chain: sha256 (truncate به ۱۶ hex) روی رکورد sorted-keys؛ `prev` به هش قبلی؛ `verify_chain()` بازپیمایش کامل. هم‌زمان چاپ کنسولی. **بدون کلید — tamper-evident نه tamper-proof** (بازنویسی کل زنجیره ممکن؛ GAP-AUDIT معیار ۳).
- **LangfuseSink:** فقط اگر `LANGFUSE_PUBLIC_KEY/SECRET_KEY` ست باشد فعال؛ هر خطا silent؛ رویدادها به trace ابری. در نبود کلید کاملاً no-op. hook از داخل `AuditLog.log`.
- **dashboard.py:** HTML آفلاین از `logs/audit.jsonl` (هزینه per-agent، خط‌زمانی، وضعیت اجراها، صحت زنجیره).
- **وضعیت:** implemented.

## ۱۲) src/llm.py — پل مدل + MOCK

- اگر `ANTHROPIC_API_KEY` نباشد یا import anthropic شکست بخورد → **mock**. mock بر اساس نام نقش در system prompt متن ثابت برمی‌گرداند؛ توکن = `len/4` تقریبی. LIVE: `messages.create` با MODEL/MAX_TOKENS config و usage واقعی.
- `smoke_live.py` جدا: تست اتصال با `claude-haiku-4-5-20251001` (نرخ $1/$5 per MTok)، مستقل از سیستم.
- **وضعیت:** پل implemented؛ **اجرای LIVE هرگز انجام نشده (طبق CHECKLIST).**

## ۱۳) IGK — igk/kernel.py · daemon.py · client.py

- **مسیر:** `fusion-mvp/igk/`
- **چیست:** «Immutable Grounding Kernel» — کرنل اعتماد **بیرون از ecology**، به‌صورت **subprocess جدا** (daemon.py، پروتکل JSON-per-line روی stdin/stdout). کلید HMAC فقط در process کرنل.
- **آنچه kernel.py واقعاً enforce می‌کند:**
  - **audit امضاشده:** HMAC-SHA256 با کلید ۳۲بایتی `secrets.token_bytes(32)` در `logs/igk_state/.kernel_key` (تلاش `chmod 0o600` — روی Windows عملاً بی‌اثر). زنجیره seq+prev+sig؛ `verify()` جعل بدون کلید را می‌گیرد.
  - **permit fail-closed:** `permit(action, actor)` اگر فایل STOP موجود → رد. token = {action, actor, nonce 8بایتی, **exp = now+30s**, sig}. `consume`: چک امضا (compare_digest)، **anti-replay با set درون-حافظه‌ای `_used_nonces`** (با restart daemon پاک می‌شود)، انقضا، و **دوباره STOP**.
  - **grounding-validity:** `ground(claims, actor)` علیه `held_out.json` (facts: subject→value؛ ۵ fact نمونه: پایتخت استرالیا=کانبرا، پایتخت فرانسه=پاریس، نقطه جوش آب=صد، مرکز منظومه شمسی=خورشید، سرعت نور=۲۹۹۷۹۲). احکام: `ok` / `contradicted` (subject ذکرشده ولی value غلط/غایب) / `unverifiable` (بی‌لنگر). `ok` کلی فقط اگر همه‌ی claimها ok و لیست ناخالی. تطبیق متنی = token-containment ساده (هیوریستیک، نه retrieval/NLI).
  - **invariant frozen:** VERBS مجاز daemon = {audit, verify, permit, consume, ground, canon, ping, status} — **هیچ verb برای تغییر کلید/held-out/invariant نیست** (تست redteam ۴). CANON چهار قید ثبتی: no_one_sided_victory، human_above، self_model_descriptive، anchor_required.
- **client.py:** `KernelClient` daemon را spawn می‌کند (همان کاربر/همان دسترسی فایل!) و `ActuationGate.act(action, fn)` = permit→consume→fn؛ رد → `PermitDenied`. «فراموش‌کردن check» به رد می‌انجامد نه اجرا.
- **وضعیت:** implemented و red-team‌شده (۸+۵ تست)؛ ولی **در orchestrator فقط finalizeِ no-op را gate می‌کند** و `_kguard` صرفاً polling وضعیت STOP از کرنل است (باز cooperative — ایجنتی که kernel را نپرسد آزاد است؛ فقط finalize نهایی مسدود می‌شود).

## ۱۴) تست‌ها — چه چیزی واقعاً verify می‌شود (۴۰ سبز ادعایی)

- `run_tests.py` / `tests/` (۹): trip نرم‌افزاری و فایل STOP؛ انباشت هزینه و قطع بودجه/سقف کال؛ HITL reject/approve؛ least-privilege (analyst از web_search منع)؛ شکستن hash-chain با دستکاری یک خط.
- `test_phase3.py` (۸): بهبود score_prompt؛ کشف یافته‌ی بی‌منبع؛ رد injection و حذف نقش در validate_prompt؛ versioning+rollback؛ خوداپدیتی end-to-end (score به 1.0 می‌رسد و explore ماندگار نمی‌شود)؛ ۳ تست پنل با provider ساختگی که همیشه "APPROVE" برمی‌گرداند (تأیید اینکه تصمیم از هیوریستیک است).
- `igk/test_redteam.py` (۸): مسیر مجاز؛ جعل audit بدون کلید → verify رد؛ STOP → fail-closed؛ permit جعلی؛ نبود verb تغییر کلید/invariant؛ grounding رد/قبول.
- `igk/test_grounding.py` (۵): ok/contradicted/unverifiable/ratio=0.5/claim ساختاریافته.
- `test_failures.py` (۷): سه سناریوی شکست (یافته‌ی بی‌منبع، پرامپت خنثی‌کننده‌ی محافظ، replay/forged permit).
- `test_igk_integration.py` (۳): مسیر سالم تا finalize؛ STOP بیرونی → halt؛ GROUNDING_REQUIRED=True → halt خروجی بی‌لنگر (**یعنی در MOCK با گیت اجباری هیچ اجرایی finalize نمی‌شود — دلیل واقعیِ False بودن پیش‌فرض**).

---

## fusion-safety — سندها

### GAP-AUDIT.md
- **مسیر:** `fusion-safety/GAP-AUDIT.md` (تاریخ 2026-06-25)
- ۴ معیار IGK علیه کد MVP: (۱) kill بیرونی → ⚠️ نیمه (cooperative/fail-open)؛ (۲) grounding held-out → ❌ نیست (score_prompt/evaluate_findings کیواژه‌ای = تله‌ی internal-consistency/Goodhart)؛ (۳) audit امضاشده → 🟡 تقریباً (hash-chain بدون کلید = جعل‌پذیر)؛ (۴) قفل self_update → ⚠️ نیمه (denylist نرم، دورزدنی با بازنویسی).
- الگوی مشترک: **declarative → باید enforced شود.** ادعا: هر ۴ گپ با `igk/` بسته شد. باز مانده: ایزولاسیون فقط process-level؛ گراندینگ هیوریستیک؛ **«اتصال orchestrator به IGK هنوز انجام نشده»**.

### THREAT-MODEL.md
- پوشش‌داده‌شده (با تست): جعل audit (HMAC)، ادامه‌ی کنش بعد STOP (permit fail-closed)، جعل/replay permit، تغییر کلید/invariant (بدون verb)، خروجی بی‌لنگر (grounding gate)، خنثی‌سازی توسط self_update (validate_prompt + شعاع محدود)، دسترسی تصادفی به کلید (chmod 600).
- **پوشش‌نشده (صریح):** (۱) مرز process-level نه OS-user/TEE — همان کاربر می‌تواند `.kernel_key` را بخواند و همه‌چیز را جعل کند؛ (۲) «agent-unreachable مطلق» تضمین نمی‌شود — جهت تحقیقاتی؛ (۳) گراندینگ هیوریستیک subject→value، نه NLI/retrieval؛ (۴) availability: اگر daemon بمیرد رفتار fail-closed کلاینت تست/مونیتور نشده؛ (۵) پنجره‌ی زمانی بین permit و consume (نبود قفل سطح منبع).

### RECONCILIATION.md
- کانن ۸سندی = دو پروژه: جریان A خلاقانه (کتاب/codex) و جریان B ایمنی (کد AI Farm)؛ قاعده: هرگز قاطی نشوند. isomorphism: «قدرت از محدودیت» ↔ corrigibility (Omohundro، Soares، Orseau & Armstrong…).
- وضعیت کد: «منطبق رفتاری نه ساختاری»؛ فاز ۰ (کرنل) ساخته شد؛ **قدم بعدی = اتصال orchestrator به IGK**. pushback: حجم سند به‌جای پیشرفت؛ «agent-unreachable مطلق» آرزوست؛ فیزیک هولوگرافیک از توجیه ایمنی بیرون بماند. شمارش تست در این سند: **۲۵ سبز**.

### PROMPT-complete-and-test.md
- پرامپت paste-ready برای ادامه‌ی کار؛ وضعیت مبنا را «IGK وصل‌شده، **۲۸ تست سبز**» می‌گوید. TODOها به‌ترتیب ROI: (۱) grounding واقعی + `GROUNDING_REQUIRED=True`؛ (۲) سه سناریوی شکست [در کد انجام شد]؛ (۳) ایزولاسیون کرنل زیر کاربر جدا؛ (۴) حالت LIVE با کلید واقعی؛ (۵) به‌روزکردن CHECKLIST؛ (۶) ویدیو. معیار «تمام شد»: GROUNDING_REQUIRED=True با held-out واقعی عبور کند — **هنوز برقرار نیست.**

---

## تناقض‌ها و شکاف‌های code-vs-doc (مهم‌ترین‌ها)

1. **سندها ناهم‌زمان با کدند:** GAP-AUDIT/RECONCILIATION می‌گویند اتصال orchestrator↔IGK «انجام نشده» (۲۵ تست)؛ PROMPT-complete می‌گوید وصل شده (۲۸ تست)؛ CHECKLIST.md کد می‌گوید ۴۰ تست و فاز ۵ کامل. کد واقعی: اتصال وجود دارد. → GAP-AUDIT به‌عنوان snapshot تاریخی درست است، نه وضعیت فعلی.
2. **گیت grounding به‌طور پیش‌فرض خنثی است:** کانن («هیچ به‌روزرسانی بی‌لنگرِ held-out معتبر نیست») و معیار «تمام شد» می‌خواهند enforced باشد؛ کد `GROUNDING_REQUIRED=False` دارد و در MOCK اگر True شود هیچ اجرایی finalize نمی‌شود (test_igk_integration ۳). anchor_required در CANON ثبت شده ولی enforce نمی‌شود.
3. **ActuationGate فقط یک no-op را می‌بندد:** ادعای «هیچ actuation بی‌permit» در README/THREAT-MODEL؛ در کد تنها actuation گیت‌شده `finalize = lambda: None` است. کال‌های LLM و tool واقعی از مسیر permit نمی‌گذرند — enforcement آن‌ها هنوز cooperative (`_kguard` polling / `ks.check`).
4. **گپ ۲ (Goodhart) فقط نصفه بسته شد:** kernel.ground برای claimهای runtime ساخته شد، ولی حلقه‌ی self_update هنوز با همان rubric کیواژه‌ای promote می‌کند و Optimizer دقیقاً کیواژه‌های همان rubric را تزریق می‌کند — بهبود نمره خودارجاع است؛ held-out هیچ نقشی در promotion ندارد.
5. **پنل داوران LLM-نما است:** کال مدل انجام و هزینه ثبت می‌شود ولی خروجی مدل در رأی بی‌اثر است (`_decide` هیوریستیک). «تنوع provider» در MOCK سه instance یکسان و در LIVE تک-provider — CHECKLIST مورد ۵ را «✅ کامل» می‌گوید، خودش پایین‌تر اذعان می‌کند multi-provider واقعی باز است (تناقض داخلی سند).
6. **fallback فروپاشی IGK = بازگشت بی‌سروصدا به cooperative** (فقط یک print)؛ THREAT-MODEL ریسک availability را «باید در LIVE تست شود» گذاشته — رفتار فعلی خلاف روح fail-closed است.
7. **chmod 600 روی Windows بی‌اثر است** و daemon زیر همان کاربر spawn می‌شود — THREAT-MODEL این را صادقانه می‌گوید؛ ولی جدول «پوشش‌داده‌شده» ردیف «دسترسی تصادفی به کلید: تأییدشده (0o600)» روی این پلتفرم عملاً برقرار نیست.
8. **anti-replay درون-حافظه‌ای:** restart daemon مجموعه‌ی nonceها را پاک می‌کند (پنجره‌ی ۳۰ثانیه‌ای انقضا تنها محافظ باقی‌مانده) — در هیچ سندی ذکر نشده.
9. **Supervisor و MAX_STEPS و ابزارهای analyst/supervisor** declarative/dead هستند در حالی که README/CHECKLIST آن‌ها را جزو معماری فعال روایت می‌کنند.
10. **همه‌چیز MOCK است:** «۴۰ تست سبز» یعنی لایه‌ی کنترل روی خروجی ساختگی تست شده؛ هیچ اجرای LIVE، هیچ جستجوی واقعی، هیچ eval رفتاری مدل واقعی. CHECKLIST این را صادقانه در «چه چیزی هنوز باز است» می‌گوید ولی جدول بالای همان سند «هر ۷ مورد ✅» است.

## جمع‌بندی وضعیت پیاده‌سازی

| مؤلفه | وضعیت |
|---|---|
| budget / killswitch / HITL / tracing / prompt_store | implemented (درون-process، تست‌شده) |
| orchestrator + panel + guardrails + evals | implemented ولی هیوریستیک کیواژه‌ای |
| self_update loop | implemented؛ optimizer قالبی، eval خودارجاع |
| IGK (kernel/daemon/client) | implemented، red-team‌شده؛ فقط finalize را واقعاً می‌بندد |
| grounding enforcement | موجود ولی خاموش (GROUNDING_REQUIRED=False) |
| tools واقعی، LIVE mode، multi-provider، NLI grounding، OS-isolation | stub / انجام‌نشده |
