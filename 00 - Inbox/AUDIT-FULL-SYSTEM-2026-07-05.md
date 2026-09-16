---
type: report
status: done
tags: [audit, system-state, ground-truth, security, handoff]
created: 2026-07-05
updated: 2026-07-07
---

# 🔍 AUDIT — گزارش کامل وضعیت سیستم (ground-truth)

> **دامنه:** کل vault (backup) — پیمایش تک‌تک دایرکتوری‌ها روی فایل‌سیستم، بدون اتکا به اسناد داخلی · **روش:** filesystem walk (find/du/stat) + live scheduler diff — نه HANDOFF/registry · **مخاطب:** مهندس ارشد (سازمان‌دهی و هندل کل سیستم)

> **چرا این گزارش:** آری اعلام کرد «آپدیت داشتیم، به اسناد vault اعتماد نکن — تک‌تک دایرکتوری‌ها را چک کن.» این گزارش **از روی فایل‌سیستم واقعی** ساخته شده، نه از HANDOFF/AGENT_REGISTRY/PROJECT.md (که ثابت شد drift دارند). همه اعداد از `find/du/stat` روی ۶٬۸۹۸ فایل. **هیچ مقدار secret خوانده/echo نشده** — فقط مسیر و اندازه.
> **هدف:** یک مهندس ارشد بتواند با همین یک فایل کل سیستم را مرتب و هندل کند.

---

## 1) خلاصه اجرایی (TL;DR)

- **حجم واقعی:** ۵۲۱MB · ۶٬۸۹۸ فایل · اما فقط **۶۳۶ فایل `.md`** (نوت واقعی). یعنی >۹۰٪ حجم و تعداد فایل «دانش» نیست: venv پایتون، dumpهای دیتای کریپتو، DNA، عکس، و تکراری‌ها.
- **۴ مشکل درجه‌یک که مهندس باید اول حل کند:**
  1. 🔴 **secretهای زنده هنوز داخل vault‌اند** — دست‌کم ۳ فایل `.env` واقعی و غیرخالی + چند فایل کد کلید/wallet. (مستقل از `secrets-export/` که امروز حذف شد.)
  2. 🔴 **~۶۰MB داده ژنتیکی/بیومتریک شخصی (PII)** داخل vault و **تکرارشده** در `_Duplicates`.
  3. 🟠 **کل vault خارج از version control است** (نه `.git`) — درحالی‌که تسک‌های خودکار مدام می‌نویسند. صفر rollback.
  4. 🟠 **drift شدید بین اسناد و واقعیت** — رجیستری «۶ تسک زنده» می‌گوید، زمان‌بندِ زنده **~۴۰ تسک enabled** دارد؛ ۳ تسک «ratified هسته» اصلاً در زمان‌بند نیستند؛ یک ناوگان کاملِ «Research Radar» مستند نشده.
- **«آپدیت» امروز چه بود:** بازنویسی بزرگ Project-F (۱۰:۵۵–۱۱:۳۱)، ساخت پوشه ممیزی `07 - Knowledge/_audit` توسط یک AI دیگر (۱۰:۲۴–۱۰:۳۵)، منشور استقلال/RATIFIED-TASKS (۰۹:۵۴–۱۰:۰۰)، و فعالیت زندهٔ کد `fusion-mvp` (۱۱:۵۰–۱۱:۵۱، همین حالا در حال نوشتن).

---

## 2) نقشه حجم واقعی (ground-truth inventory)

**کل: 521MB · 6,898 file · 636 markdown**

| پوشه سطح‌بالا | فایل | md | حجم | ماهیت واقعی |
|---|---:|---:|---:|---|
| `03 - Projects` | 897 | 188 | **230M** | بیشترش dump دیتا + کد بات‌ها (نه نوت) |
| `08 - Assets` | 625 | 0 | 89M | عکس (Telegram-2023 + WhatsApp-2026) — مشروع |
| `_Duplicates` | 303 | 146 | 84M | قرنطینه تکراری‌ها — هنوز داخل vault |
| `07 - Knowledge` | 120 | 90 | 65M | ~۴MB متن + ۶۰MB DNA باینری |
| `04 - Architect System` | 4,841 | 114 | 53M | **۴٬۴۱۸ فایل venv** + ۴٬۷۵۳ در `_code`؛ فقط ۱۱۴ نوت |
| `00 - Inbox` | 55 | 55 | 652K | پرامپت‌ها + scout-digests |
| `01 - Dashboard` | 9 | 4 | 125K | Home/HANDOFF/Brain + ۲ داشبورد HTML |
| `_memory` | 11 | 11 | 112K | ledger، blueprint، heartbeat |
| `05 - Agents` | 5 | 5 | 64K | رجیستری + fleet |
| `06 - Architecture Maps` | 4 | 4 | 20K | ECOSYSTEM/SYSTEM_MAP/Schema |
| `10 - Telegram processing` | 4 | 4 | 16K | SOP/ROUTING |
| `02 - Life OS` | 2 | 2 | 8K | تقریباً خالی |
| `09 - People` | 1 | 1 | 4K | فقط ایندکس خالی |
| `_Templates` | 6 | 6 | 4.5K | قالب نوت |

**هیستوگرام پسوند (کل vault):** `py` 1767 · `pyc` 1559 · `jpg` 980 · **`md` 636** · `pdf` 91 · `txt` 73 · `sample` 42 · `json` 39 · `typed` 33 · `bat` 21 · `sh` 20 · `exe` 18 · `zip` 17 · `html` 15 · `csv` 10 · `xlsx` 7 · `env` 3 · `docx` 3 · `pem` 2.

**درس کلیدی برای مهندس:** «vault دانش» در عمل ~۵MB متن واقعی است که زیر ۵۱۶MB بار غیرمتنی (venv/dump/DNA/عکس/dup) دفن شده. تمیزکاری = جداکردن این دو لایه.

---

## 3) پروژه‌ها — تفکیک واقعی

| پروژه | فایل | md | حجم | نکته ground-truth |
|---|---:|---:|---:|---|
| **Crypto - etoro** | 101 | 23 | **164M** | ۹۵٪ حجم = dump کهنهٔ lunarcrush/cryptoquant (JSON/CSV، June 2026). بزرگ‌ترین: ۵۲MB یک فایل. |
| **Mining** | 278 | 23 | 41M | کد بات‌ها + باینری (`PowerISO.exe` 5.5MB، `.lnk`ها، zipها) + PDFهای Quantum Dataset ~۱۷MB |
| **Lead-نقاشی** | 366 | 69 | 25M | کد `کاریابی/bot` + `brushline` (AiFarm-Lead). بیشترین md پروژه‌ای. |
| **اونلی فنز (Project-F)** 🔒 | 51 | 42 | 1.6M | محتوامحور؛ **کانون آپدیت امروز** (۲۰+ فایل نو ۱۰:۵۵–۱۱:۳۱) |
| **Ziman Galerry** | 67 | 18 | 267K | **کد واقعی نو**: `control-brain/` + `ziman-agent/` + `.env` + `secrets.py` — `PROJECT.md` هنوز این را ندارد (stale) |
| **Accounting** | 33 | 12 | 964K | dashboardهای JS + پوشه‌های مبهم `1/`,`2/`,`importer/`؛ صفر دفتر واقعی |

---

## 4) 🔴 امنیت و داده حساس (بالاترین اولویت)

### 4.1 secretهای زنده که هنوز داخل vault‌اند
`secrets-export/` امروز (۲۰۲۶-۰۷-۰۵) با عنوان «فیک» حذف شد، **ولی این‌ها هنوز سرجایشان‌اند** (فقط مسیر و اندازه — محتوا خوانده نشد):

| مسیر | اندازه | نوع |
|---|---:|---|
| `03 - Projects/Lead-نقاشی/کاریابی/bot/.env` | 1663 B | `.env` واقعی و پرمحتوا |
| `04 - Architect System/architect/_code/ai-farm/AI-sume/langar/.env` | 838 B | `.env` واقعی |
| `03 - Projects/Ziman Galerry/control-brain/.env` | 618 B | `.env` واقعی |

به‌علاوه فایل‌های کد/الگوی حساس: `check_keys.py`, `sentinel/wallet_tracker.py`, `control-brain/core/secrets.py`, `control-brain/SECRETS.md`, `langar/SEED-MEMORY.bat`, `seed_memory_win.py`, `langar.db.bak-preseed`، و **۱۸ فایل الگوی-کلید داخل venv**. همچنین چند `.env.example`/`.env.template` که طبق یادداشت GAPS G-01 ممکن است مقدار **واقعی** داشته باشند.
۱۳ فایل `MOVED - *.md` (pointerهای درست) نشان می‌دهند نسخهٔ اصلی منتقل شده — ولی سه `.env` بالا pointer ندارند، یعنی **واقعی و زنده‌اند**.

**تناقض حاکمیتی که باید حل شود:** کل سیستم به‌خاطر §Security Gate در حالت read-only است (۴ ردیف CRITICAL باز در `ROTATION_CHECKLIST`). آری `secrets-export` را «فیک» خواند و حذف کرد. اما (الف) این ۳ `.env` واقعی مستقل از آن پوشه‌اند، و (ب) ردیف‌های rotation به حساب‌های واقعی (Bybit/OKX/Monero/Anthropic) اشاره دارند. → **verdict مالک لازم است:** یا حساب‌ها واقعی‌اند و باید rotate شوند و این `.env`ها هم پاک‌سازی شوند، یا همه‌چیز dummy است و گیت برداشته می‌شود. تا آن verdict، فرض = گیت بسته.

### 4.2 PII بیومتریک — ۶۰MB داده ژنتیکی داخل vault
`07 - Knowledge/هیپنوتیزم و خودآگاهی/Marathon/امواج مغزی/`:

- `armin_dna.vcf` (23.6MB) · `armin_dna_23andme_format.txt` (14.1MB) · `armin_dna.map` (13.6MB) · `MyHeritage_raw_dna_data.zip` (5.4MB) · `armin_dna.ped` (2.2MB) · گزارش‌های مشتق (`ARMIN_DNA_REPORT.md`, `armin_dna_summary.json`, PDF).
- **همه این‌ها در `_Duplicates` هم کپی شده‌اند** (دوبار روی دیسک).
- طبق `ARCHITECT_CHARTER §Privacy` داده شخصی باید laptop-only بماند و به VPS/sync نرود. ممیزیِ خودِ Knowledge (`07 - Knowledge/_audit/MASTER_REPORT.md`) هم این را **ریسک #۱** خوانده.
- **اقدام پیشنهادی:** خروج کامل به cold storage آفلاین (خارج vault)، حذف نسخهٔ vault و نسخهٔ `_Duplicates`.

---

## 5) 🟠 نبود version control
- **`.git` در ریشهٔ vault وجود ندارد** (تأییدشده). هیچ تاریخچه/rollback/blame وجود ندارد.
- هم‌زمان، تسک‌های خودکار (`bio-synthesis`, `brain-pulse`, fusion-mvp) مدام فایل می‌نویسند — یعنی نوشتن بدون شبکهٔ ایمنی.
- HANDOFFها بارها نوشته‌اند «commit نزدم چون vault هنوز git repo نیست — تصمیم باز init با آری».
- **اقدام:** `git init` + `.gitignore` سخت‌گیر (venv، `*.env`، DNA، dumpها، عکس، `_Duplicates`) + commit پایه. این پیش‌نیاز هر کار خودکار امنِ بعدی است.

---

## 6) 🟠 بار غیردانشی که باید از vault خارج شود

| قلم | مسیر | حجم/تعداد | پیشنهاد |
|---|---|---|---|
| venv پایتون | `04 …/_code/ai-farm/AI-sume/langar/venv` | ۴٬۴۱۸ فایل | خارج vault بازساز (قاعدهٔ ۴ قانون اساسی؛ ریسک EACCES ابسیدین) |
| `__pycache__` | سرتاسر `_code` | ۱۹۰ پوشه | حذف/ignore |
| dumpهای کریپتو | `03 …/Crypto - etoro/*.json,*.csv` | ~۱۵۰MB | آرشیو بیرونی (داده June 2026، کهنه) |
| DNA/بیومتریک | §4.2 | ~۶۰MB ×۲ | cold storage آفلاین |
| باینری/نصب‌کننده | `Mining/_archive/PowerISO.exe` و `.lnk`ها | ~۶MB | آرشیو بیرونی |
| تکراری‌ها | `_Duplicates/` | ۸۴MB / ۳۰۳ فایل | بعد از بازبینی، خارج vault (طبق `_گزارش تکراری‌ها.txt`) |

> نکته: `08 - Assets` (۸۹MB عکس) مشروع است و در جای درست — نیازی به خروج ندارد، فقط از git ignore شود.

---

## 7) کیفیت داده و بهداشت نوت‌ها
- **۱۳۲ از ۴۸۵ نوت md بدون frontmatter** (خارج از `_Duplicates`/venv). عمدتاً اسناد کنار-کد: `brushline/00_governance/*`, `10_knowledge_base/KB-*`, READMEهای Accounting/importer/scraper. → تصمیم: یا از دامنهٔ validator خارج شوند (کد، نه نوت) یا frontmatter بگیرند.
- **پوشه‌های تقریباً خالی/رزرو:** `02 - Life OS` (۲ فایل)، `09 - People` (فقط ایندکس)، `05/06/10` رزرو آینده.
- **دو ممیزی موازی امروز:** `07 - Knowledge/_audit/` (۱۰ فایل، توسط یک AI دیگر — که **ریشهٔ backup برایش در دسترس نبود**، پس CLAUDE.md/.agentignore/secrets را ندید) + همین گزارش (کل vault). باید یکی canonical شود تا سومین drift نسازند.
- **اسناد stale شناخته‌شده:** `PROJECT.md` Ziman (کد جدید را ندارد) · `PROJECT.md` Project-F (۴ سند دیروز/امروز) · `Domains Status` و `Brain.md` نسبت به زمان‌بند زنده.

---

## 8) آشتی اتوماسیون — زمان‌بندِ زنده در برابر اسناد

**قاعده (از ledger خودِ سیستم): منبع حقیقت fleet = خروجی زندهٔ زمان‌بند، نه markdown.** خروجی زنده:

- **~۴۰ تسک `enabled`** (نه «۶ زنده» که رجیستری می‌گوید): ۱۹ اسکات روزانه + ۵ لاین `selfimprove-*` + `selfimprove-deep` + `brain-pulse` + `bio-synthesis-daily` (`*/5`) + `mycelial-consolidator` + `fleet-selection` + `survival-heartbeat` + `mycelium/crypto/mining/…`.
- **enabled ولی stale:** `architect-selfimprove` (`*/3`) آخرین اجرا **۲۰۲۶-۰۷-۰۴ 11:26**؛ `bio-synthesis` و لاین‌های `selfimprove-*` هم lastRun ۰۷-۰۴ — یعنی با اینکه فعال‌اند، ~۲۴ ساعت اجرا نشده‌اند (به‌احتمال زیاد ابزار pre-approve نشده / سشن قطع).
- **ratified ولی غایب:** `brain-focus-board`، `experience-review`، `system-dashboard` — که HANDOFF می‌گوید امروز «از نو ساخته شدند» — در لیست زندهٔ زمان‌بند **نیستند**. پس `HEARTBEAT` که «beat موفق brain-focus-board» ثبت کرده با واقعیت نمی‌خواند.
- **مستند نشده:** یک ناوگان کامل **«Research Radar»** (`ai-eng-radar-brief`, `ai-eng-week-in-review`, `research-radar-curator`) + **۱۰ تسک `radar-qa-01..10`** در زمان‌بند هست ولی در `AGENT_REGISTRY` هیچ ردی ندارد.
- **کد زندهٔ در حال نوشتن:** `04 …/_code/ai-farm/fusion-mvp/` همین‌الان `__pycache__`, `audit.jsonl`, `prompts.json` را می‌نویسد (۱۱:۵۰–۱۱:۵۱) — یعنی fusion-mvp یک runtime فعال است، نه کد ساکن.

**اقدام:** یک sync یک‌بارهٔ رجیستری↔زمان‌بند (بدون حذف تسک؛ فقط ثبت واقعیت)، تعیین تکلیف ۳ تسک غایب، و مستندسازی یا بازنشستگیِ ناوگان Radar.

---

## 9) برنامهٔ هندل‌کردن (به‌ترتیب اهرم — برای مهندس ارشد)

**فاز ۰ — ایمن‌سازی (قبل از هر کار دیگر):**
1. verdict مالک روی §Security Gate + secretهای §4.1 (rotate یا اعلام dummy).
2. خروج DNA/PII (§4.2) به cold storage آفلاین + حذف از vault و `_Duplicates`.
3. `git init` + `.gitignore` سخت + commit پایه (§5).

**فاز ۱ — سبک‌سازی (بازیابی ~۳۵۰MB):**
4. خروج venv، dumpهای کریپتو، باینری‌ها، و `_Duplicates` به بیرون vault (§6).
5. حذف `__pycache__` و افزودن به ignore.

**فاز ۲ — آشتی حقیقت:**
6. یک sync زمان‌بند↔رجیستری↔HANDOFF↔HEARTBEAT (§8)؛ تعیین تکلیف ۳ تسک غایب + ناوگان Radar.
7. یکی‌کردن دو ممیزی موازی (§7) به یک منبع canonical.
8. رفرش `PROJECT.md`های stale (Ziman/Project-F) + Brain/Domains.

**فاز ۳ — بهداشت پایدار:**
9. تصمیم دامنهٔ validator برای ۱۳۲ نوت بی‌frontmatter (§7).
10. جداسازی رسمی «کد اجرایی» از «نوت دانش» (همه کد → `_code`/بیرون؛ vault فقط md).

---

## 10) تصمیم‌های باز مالک (verdict لازم — ایجنت تصمیم نمی‌گیرد)
1. **Security Gate:** حساب‌های واقعی rotate شوند یا «فیک» = گیت برداشته شود؟ (بالاترین‌اهرم — ۴ پروژه را باز می‌کند.)
2. **DNA/PII:** مقصد cold storage کجا؟ حذف از vault مجاز؟
3. **git init روی vault:** بله/خیر (تاکنون باز مانده).
4. **مقصد خروج venv/dump/باینری/`_Duplicates`:** همان `Desktop\backup-Archive` بیرونی؟
5. **ناوگان Radar:** مستند شود یا بازنشسته؟
6. **دو ممیزی موازی:** کدام canonical؟

---

## پیوست — روش‌شناسی
پیمایش کامل با `find`/`du`/`stat` روی مِنت فایل‌سیستم؛ کراس‌چک با خروجی زندهٔ scheduled-tasks. رعایت `.agentignore`: هیچ فایل الگوی-secret **خوانده یا echo نشد** — فقط نام مسیر و اندازهٔ بایت گزارش شد. `_Archive` در ریشهٔ vault وجود ندارد (قبلاً بیرون برده شده — تأیید شد). ارقام لحظهٔ ۲۰۲۶-۰۷-۰۵ ~۱۲:۰۰ AEST.
