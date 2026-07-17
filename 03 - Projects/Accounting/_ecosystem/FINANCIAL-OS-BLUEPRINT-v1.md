---
type: master-blueprint
id: FINOS-SSOT-v1
project: "[[04 - Architect System/architect/ARCHITECT_CHARTER]]"
status: draft-v1
autonomy_level: read-only (Security Gate closed)
owner: آری
created: 2026-07-13
supersedes: [scattered rollout/architecture notes — see §9 Conflict Log]
tags: [finos, blueprint, ssot, architecture, accounting, governance, obsidian]
confidence: "structure 0.86 · tax-rules [Unverified — registered tax agent]"
---

# 🏛️ FINANCIAL OPERATING SYSTEM — بلوپرینتِ یکپارچه (SSOT) v1.0

> **این سند = Single Source of Truth معماری.** هدفش این است که همهٔ اسناد پراکنده (charter, manifestها, rollout plans, per-project READMEها) را در **یک نقشهٔ متصل** ادغام کند، تعارض‌ها را حل کند، و نام‌گذاری/متادیتا/ساختار را نرمال کند. هر جای دیگری با این تعارض داشت → این سند مقدم است، مگر خودِ `ARCHITECT_CHARTER §1` (human-verdict) و قواعد قفل‌شدهٔ ایمنی.
>
> ⚠️ **سلب مسئولیت:** بخش‌های مالیاتی «اطلاعات» است نه «مشاورهٔ مالیاتی». هر قاعده `[Unverified — registered tax agent to confirm]` است. این سیستم **هرگز** به ATO/ASIC ارسال نمی‌کند و **هرگز** پول جابه‌جا نمی‌کند.

---

## §0 — چطور این سند را بخوان

سه لایهٔ خواندن: (۱) اگر عجله داری → §1 (اصول) + §2 (نقشهٔ لایه‌ها) + §13 (اقدامات فوری). (۲) اگر معمار/ایجنتی → کل سند. (۳) اگر دنبال یک تصمیم خاصی → هر تصمیمِ بزرگ یک **بلوکِ تصمیم** دارد با این قالب ثابت:

> **چرا هست · چه مشکلی را حل می‌کند · چه جایگزینی رد شد · مسیر ارتقا · وابستگی‌ها · ریسک‌ها · هزینهٔ نگهداری · پیچیدگی (۱–۱۰) · اطمینان (۰–۱)**

نمادِ اطمینان در کل سند: `⟨c=0.0–1.0⟩`. تگ‌های epistemic: `[FACT]` `[EST]` `[OPINION]` `[SPEC]` `[OPEN]` `[Unverified]`.

---

## §1 — چشم‌انداز و اصولِ اولیه (First Principles)

**مسئله:** یک اکوسیستمِ چندپروژه‌ایِ درآمدزا (نقاشی، ماینینگ، کریپتو، Project-F، Ziman) روی یک مالکِ تنها (آری) که مغزش تصویری کار می‌کند، بدون یک لایهٔ مالیِ واحد، منجر به: قاطی‌شدن پول شخصی/بیزنس، ریسکِ Division 7A، داده‌های پراکنده، و ناتوانی در «audit-ready» شدن (که پیش‌نیازِ قراردادهای بزرگ‌تر و وام است).

**راه‌حل (یک خط):** یک **Financial Operating System** که Obsidian را به‌عنوان *لایهٔ دانشِ انسانی* و یک **دفترِ رویدادمحورِ append-only** را به‌عنوان *حقیقتِ مالی* می‌گیرد، و ایجنت‌ها فقط **draft** تولید می‌کنند تا انسان (و حسابدارِ رسمی) verdict بدهد.

**پنج اصلِ قفل‌شده (از charter + manifestها، نرمال‌شده):** ⟨c=0.95⟩
1. **Draft-only / Human-verdict.** هیچ خروجی «نهایی» بدون verdictِ صریحِ آری. timeout = DENY. *(D-01)*
2. **هرگز lodge، هرگز پرداخت.** این توابع برای ایجنت‌ها وجود ندارند.
3. **Read-only تا باز شدنِ Security Gate** (الان بسته — §7).
4. **PII هرگز وارد LLM نمی‌شود** — قبل از inference توکنایز کن.
5. **Append-only + Auditability.** هر تصمیم/ثبت = ورودیِ Anchor Ledger؛ در ابهام fail-closed.

**فلسفهٔ vault:** «vault یک سیستم‌عامل است، نه دفترچه.» یعنی ساختار، متادیتا، و کوئری‌ها طوری طراحی می‌شوند که vault خودش پاسخ بدهد (dashboardهای زنده)، نه اینکه انسان دستی جست‌وجو کند.

---

## §2 — معماریِ ادغام‌شده (Layer Cake)

نمای بصریِ زنده در فایلِ همراه: `FinOS-System-Map.html`. لایه‌ها از پایین به بالا:

| لایه | نام | نقش | مصنوعِ اصلی |
|---|---|---|---|
| **L0** | Governance | langar / charter: gate, verdict, ledger, kill-switch, budget | `ARCHITECT_CHARTER` |
| **L1** | Knowledge | Obsidian vault-OS (این سند §4) | vault |
| **L2** | Financial Core | دفترِ رویدادمحور + double-entry (§5) | event log + projections |
| **L3** | Agents/Organs | importer, OCR, compliance, dashboards, scouts (§5.4) | `_code/` |
| **L4** | Integration | MCP/API catalog + hybrid local↔cloud (§8) | connectors |
| **L5** | Observability | audit log, KPIها, compliance flags (§7) | Anchor Ledger + dashboards |

**قاعدهٔ اتصال:** هیچ لایه‌ای مستقیم به دو لایه بالاتر دست نمی‌زند؛ ارتباط از راهِ `contracts/adapter.yaml` هر tenant. این «thin-tenant روی mother control-plane» است که در همهٔ manifestها تکرار شده. ⟨c=0.9⟩

---

## §3 — اکوسیستمِ ایجنت‌ها (langar + ۶ لِگ)

**Mother:** `langar` (در `04 - Architect System`) — میزبانِ Telegram · Brain · Safety · Anchor Ledger · Chief Orchestrator. همهٔ tenantها thin هستند و به langar وابسته‌اند.

**ترتیبِ tenant (D-26):** Accounting → Lead-نقاشی → Mining → (Crypto, Project-F, Ziman موازی).

### نقشهٔ جریانِ پول (قلبِ سیستم) — منبع: `Ecosystem-Rollout §2`

| لِگ | نوعِ درآمد | رفتارِ ATO `[Unverified]` | اتصال |
|---|---|---|---|
| **Lead-نقاشی** | نقاشی/renovation | business income + GST ۱۰٪ | منبعِ اصلی → Accounting |
| **Mining** | کریپتوی استخراج‌شده | درآمدِ کسب‌وکار به **ارزشِ AUD در لحظهٔ دریافت** + استهلاک rig/برق | financial exec **HARD_STOP (D-10)** — Accounting فقط ثبت |
| **Crypto-eToro** | eToro/Bybit/OKX | **CGT** (سرمایه‌ای) — ⚠️ شرکت‌ها تخفیفِ ۵۰٪ CGT ندارند؛ CFD = revenue account (TR 2005/15) | احتمالاً **شخصی** بماند، نه Pty Ltd؛ کلیدها off-box (D-11) |
| **Project-F** | creator | فقط **۵۰٪ سهمِ آری**؛ آستانهٔ GST جدا | privacy §6: فقط «Project-F»، بدون نامِ پلتفرم/پارتنر |
| **Ziman** | فروشِ هدیه | income + COGS | زیرِ سقفِ ظرفیت (D4) |
| **Accounting** | — (تجمیع‌گر) | **قلبِ مالی**؛ همه را برای ATO آماده می‌کند | tenant #1 |

**Organهای مشترک:** QuantumAlphaBot (L3 scout) و Fleet Manager (L7) بینِ **Crypto ↔ Mining** مشترک‌اند (hashrate_oracle به لبهٔ ENERGY وصل است). Anchor Ledger و Chief Orchestrator بینِ **همه** مشترک‌اند.

> **بلوکِ تصمیمِ #1 — «یک Pty Ltd یا چند شرکت؟»** *(بازترین سؤالِ ساختاری)*
> **چرا هست:** ساختارِ حقوقی، شکلِ کلِ دفاتر و رفتارِ مالیاتیِ هر لِگ را تعیین می‌کند. **مشکل:** ماینینگ + نقاشی + Project-F زیرِ یک شرکت = درهم‌تنیدگیِ مسئولیت و آبرو؛ کریپتو زیرِ شرکت = از‌دست‌رفتنِ تخفیفِ ۵۰٪ CGT. **جایگزین‌های رد/معلق:** (الف) همه زیرِ یک Pty Ltd — رد به‌خاطرِ ریسکِ CGT و آبرو؛ (ب) sole trader واحد — سبک ولی سقفِ مسئولیت ندارد؛ (ج) **hybrid: Pty Ltd برای نقاشی/ماینینگ + کریپتوی شخصی + Project-F جدا** — گزینهٔ پیش‌فرضِ فعلی. **مسیرِ ارتقا:** با رشد، holding company. **وابستگی:** حسابدارِ رسمی (بلاکر #۱). **ریسک:** تصمیمِ اشتباه = بازسازیِ گران. **پیچیدگی:** ۹. **اطمینان:** ⟨c=0.4⟩ — این تصمیم **مالِ انسان+حسابدار است، نه ایجنت.**

---

## §4 — Obsidian Vault-OS (طراحیِ لایهٔ دانش)

### ۴.۱ تاکسونومیِ پوشه‌ها — آشتیِ Johnny Decimal + PARA

> **بلوکِ تصمیمِ #2 — Hybrid JD+PARA.**
> **چرا:** تو الان یک اسکلتِ عددی داری (`00 - Inbox`, `03 - Projects`, `04 - Architect System`, `06 - Architecture Maps`, `07 - Knowledge`). این عملاً **PARA سوارِ Johnny Decimal** است. **مشکلی که حل می‌کند:** آدرسِ پایدار + جای‌گذاریِ بدونِ ابهام (هر چیز فقط یک خانه دارد). **جایگزین‌های رد:** PARA خالص (بدونِ شماره → مرتب‌سازیِ الفبایی شکننده)؛ tag-only (بدونِ سلسله‌مراتب → برای دادهٔ مالی/ممیزی ضعیف). **مسیرِ ارتقا:** افزودنِ زیرشاخهٔ دهدهی داخلِ هر ناحیه وقتی شلوغ شد. **وابستگی:** Property Schema (۴.۲). **ریسک:** انحرافِ نام‌گذاری → با `validate_frontmatter.py` مهار. **نگهداری:** پایین. **پیچیدگی:** ۴. **اطمینان:** ⟨c=0.88⟩

**درختِ کانونیِ نرمال‌شده** (این نسخه، منبعِ حقیقت):

```
Vault/
├── 00 - Inbox/            ← هر ورودی اول اینجا (Inbox-first، §4.7)
├── 01 - Dashboard/        ← HANDOFF + داشبوردهای زنده (Bases/Dataview)
├── 02 - Daily/            ← Daily Notes + periodic reviews
├── 03 - Projects/         ← Accounting · Lead-نقاشی · Mining · Crypto-etoro · Project-F · Ziman
├── 04 - Architect System/ ← langar · ARCHITECT_CHARTER · ROTATION_CHECKLIST · MYCELIAL-MASTER-SPEC
├── 05 - Finance/          ← 🆕 لایهٔ مالیِ عرضی: Ledger · CoA · BAS · Invoices · Receipts · Assets · Associates
├── 06 - Architecture Maps/← ECOSYSTEM · Property Schema · این بلوپرینت
├── 07 - Knowledge/        ← research, SOPs, policies (خانهٔ MISFILED science doc)
├── 08 - Clients/          ← 🆕 CRM سبک: هر مشتریِ نقاشی یک نوت
├── 09 - Archive/          ← _Archive + _Duplicates (هرگز حذفِ واقعی؛ فقط انتقال)
└── _system/               ← _Templates · _memory · scripts (validate/find_broken_links)
```

> **نکتهٔ ادغام:** ناحیهٔ `05 - Finance` جدید است تا دادهٔ مالیِ عرضی (که الان داخلِ `03 - Projects/Accounting/data` حبس است) از منطقِ پروژه جدا شود — چون Accounting «قلبِ عرضی» است نه یک پروژهٔ معمولی. Accounting **کدِ ایجنتش** در `03 - Projects/Accounting` می‌ماند، ولی **دادهٔ دفتری** به `05 - Finance` می‌رود. ⟨c=0.75, [OPEN — verdict مالک]⟩

### ۴.۲ Property Schema (متادیتا کانونی)

هر نوت frontmatter استاندارد دارد؛ **کلیدِ جدید اختراع نکن** (قاعدهٔ موجود). کلیدهای کانونی:

| کلید | نوع | برای | مثال |
|---|---|---|---|
| `type` | enum | نوعِ نوت | project · reference · report · ledger-entry · invoice · receipt · decision · daily · moc |
| `id` | string | شناسهٔ پایدارِ یکتا | `ACC-LEDGER-2025-0001` |
| `project` | link | پروژهٔ مالک | `[[03 - Projects/Accounting/PROJECT]]` |
| `status` | enum | draft · active · verified · archived |
| `scope` | enum | business · personal · `[OPEN]` (برای رکوردِ مالی) |
| `confidence` | float | ۰–۱ |
| `tags` | list | تاکسونومیِ نرمال‌شده (۴.۳) |
| `aliases` | list | نام‌های جایگزین (برای لینکِ طبیعی) |
| `created` / `updated` | date | |
| `verdict_ref` | id | اگر پشتِ verdict است |
| `source` | list | فایل/ID تراکنش (برای citation) |

**IDها (canonical reference):** الگوی `<LEG>-<KIND>-<YYYY>-<seq>` (مثل `ACC-INV-2026-0007`, `CRY-POS-0003`). هر رکوردِ مالی حتماً `bank_id` منبع را نگه می‌دارد (کلیدِ dedup). ⟨c=0.85⟩

### ۴.۳ تاکسونومیِ تگ نرمال‌شده

سه محور، بدونِ همپوشانی: **دامنه** (`#finance/gst`, `#finance/div7a`, `#tax/bas`), **پروژه** (`#leg/accounting`, `#leg/crypto`), **وضعیت** (`#status/draft`, `#needs-verdict`, `#unverified`). تگ‌های آزادِ قدیمی → با یک اسکریپتِ نگاشت به این محورها مهاجرت می‌کنند (§9).

### ۴.۴ MOCها و ایندکس‌ها

- **MOCهای دستیِ کم‌تعداد** (هابِ ناوبری): `ECOSYSTEM` (کل)، `Finance MOC` (05)، هر `PROJECT.md` به‌عنوان MOC محلی.
- **ایندکس‌های خودکار** با Dataview/Bases (نه دستی) → همیشه به‌روز. قاعده: *دستی فقط برای هاب‌های سطح‌بالا؛ بقیه کوئری.* ⟨c=0.9⟩

### ۴.۵ داشبوردها — Bases (بومی) + Dataview

> **بلوکِ تصمیمِ #3 — Bases به‌عنوان موتورِ اصلیِ داشبورد.**
> **چرا:** Bases حالا **core و بومیِ Obsidian** است (نمای database بدونِ افزونه) → روی vaultِ سنگین سریع‌تر و پایدارتر از Dataview. **مشکل:** داشبوردهای مالی باید زنده و مقیاس‌پذیر باشند. **جایگزین‌های رد/مکمل:** Dataview (قوی ولی کندتر روی مقیاس، JS-محور) → به‌عنوان **مکملِ** کوئری‌های پیچیده نگه می‌داریم؛ Datacore (successor سریع ولی هنوز beta). **مسیرِ ارتقا:** مهاجرتِ تدریجیِ کوئری‌های Dataview به Bases. **وابستگی:** Property Schema تمیز. **ریسک:** قفل‌شدن به فرمتِ Bases → کم، چون بر پایهٔ frontmatter است. **نگهداری:** پایین. **پیچیدگی:** ۵. **اطمینان:** ⟨c=0.8⟩

داشبوردهای هدف (هرکدام یک view): **Inbox Triage** · **Verdict Queue** (همهٔ لِگ‌ها) · **BAS/Compliance due** · **P&L تجمیعی** · **Associates/Div7A watch** · **per-project status**. نمونهٔ Dataview:

```dataview
TABLE scope, gst_amount, status FROM "05 - Finance/Ledger"
WHERE type = "ledger-entry" AND status = "draft" AND needs_human_review
SORT date DESC
```

### ۴.۶ Templater + QuickAdd (گردش‌کارها)

QuickAdd macros → Templater templates برای: **ثبتِ تراکنش**, **رسید (capture عکس→Inbox)**, **فاکتور**, **ورودیِ DecisionLog**, **Daily Note**, **نوتِ پروژه**, **ورودیِ Verdict Queue**. هر macro فیلدهای Property Schema را از پیش پر می‌کند تا انحراف صفر شود. ⟨c=0.85⟩

### ۴.۷ Tasks · Canvas · Excalidraw · Periodic Reviews · Automation

- **Tasks:** صفِ verdict و ددلاین‌های BAS/ASIC به‌صورتِ task با `due::` → یک داشبوردِ «این هفته چه سررسید است».
- **Canvas:** نقشهٔ اکوسیستم، جریانِ پول، و «اتاقِ جنگِ» هر تصمیمِ بزرگ.
- **Excalidraw:** درخت‌های تصمیم (مثلِ Div 7A: salary/dividend/loan) و اسکچِ معماری — چون مغزت تصویری است.
- **Periodic Reviews:** روزانه (Inbox صفر)، هفتگی (verdictهای باز)، ماهانه (P&L + compliance scan)، **فصلی = چرخهٔ BAS** (۲۸امِ ماهِ بعدِ فصل).
- **Automation (بی‌خطر، محلی):** `validate_frontmatter.py` و `find_broken_links.py` قبل از هر «تمام»؛ قانونِ **Inbox-first**؛ آرشیو = فقط انتقال (هرگز حذفِ واقعی).

---

## §5 — هستهٔ مالی («Financial Digital Twin»)

### ۵.۱ Event Sourcing + Double-Entry (تصمیمِ بنیادی)

> **بلوکِ تصمیمِ #4 — دفترِ رویدادمحورِ append-only + double-entry.**
> **چرا:** حقیقتِ مالی باید **بازتولیدپذیر، زمان‌سفرپذیر، و audit-ready** باشد؛ این دقیقاً همان چیزی است که هم ATO (سوابقِ ۵/۷ ساله) هم charter (Anchor Ledger append-only) می‌خواهند. **مشکلی که حل می‌کند:** «عددِ دستی» و بازنویسیِ مخرب را حذف می‌کند؛ هر گزارش (P&L, BAS) صرفاً یک **projection** روی رویدادهاست. **جایگزین‌های رد:** جدولِ mutableِ ساده (spreadsheet) — رد چون تاریخچه و auditability ندارد؛ فقط double-entry بدونِ event log — رد چون زمان‌سفر و منبعِ تغییر را از دست می‌دهد. **مسیرِ ارتقا:** از markdown/CSV projections → SQLite → در صورتِ رشد، یک event store واقعی. **وابستگی:** IDها + dedup(bank_id). **ریسک:** پیچیدگیِ مفهومی برای کاربرِ غیرفنی → با draft+verdict و templateها مهار. **هزینهٔ نگهداری:** متوسط. **پیچیدگی:** ۸. **اطمینان:** ⟨c=0.82⟩ *(الگوها: Fowler Accounting Patterns; CQRS/ES در financial services.)*

**مدل:** رویدادها append-only در `05 - Finance/_events/` (هر تراکنش/verdict یک event). **Projectionها** (فقط‌خواندنی، بازتولیدپذیر): `Ledger` (double-entry)، `P&L`، `BAS-draft`، `Associates sub-ledger`. **CQRS:** نوشتن (event) از خواندن (dashboard) جداست → خواندن هرگز حقیقت را عوض نمی‌کند (همان اصلِ read-only).

### ۵.۲ Chart of Accounts (مشترکِ اکوسیستم)

یک CoA واحد که هر لِگ یک دستهٔ درآمد + رفتارِ مالیاتیِ خودش دارد (جدولِ §3). دسته‌های هزینهٔ مصوب: Materials · Tools · Fuel/Vehicle · Insurance · Software/Subscriptions · Marketing · Phone/Internet · Professional Fees · Rent `[OPEN]` · Misc + برچسب‌های شخصی. **scope** هر رکورد: business / personal / `[OPEN]`. برداشت/انتقالِ بینِ حساب‌های خودی → `TRANSFER/DRAWING` با GST=0.

### ۵.۳ اسکیمای تراکنش + قواعدِ آهنین

هر ردیفِ ledger: `{bank_id, date, account, merchant, type, gross_inclusive, gst_amount, amount_ex_gst, category_draft, scope, confidence, flags[], needs_human_review, source}`.
**قواعدِ قفل‌شده (از manifest Accounting):** GST = `total/11` (نه `×0.10`)؛ GST-free/overseas/بهره/حقوق/کارمزد = 0 · dedup روی `ID` بانک · reconcile روی `Closing Balance` فقط روی exportِ کامل · Schema ورودیِ ANZ «PS Export» = ۱۴ ستون. ⟨c=0.95⟩

### ۵.۴ Organها (جعبه‌های سیاه) + Model Tiering

| organ | نقش | آمادگی | tiering |
|---|---|---|---|
| **ANZ CSV importer** | بانک→draft→Inbox→verdict (بیشترین کاهشِ کار) | طراحی v1.1 + تست ۱۳/۱۳✅ | Haiku extract → Sonnet categorize |
| **Receipt OCR** | عکس→{date,vendor,amount,gst,abn}→draft | طراحی؛ منتظرِ ۱۰–۵۰ رسیدِ واقعی (golden set) | Haiku OCR → Sonnet |
| **Compliance monitor** | Div7A · no-ABN>$75 · >$10k (AUSTRAC) · BAS-due | طراحی | Opus (risk) |
| **Associates sub-ledger** | Div 7A loan tracking | داده موجود، ساخته‌نشده | Sonnet |
| **Vendor→Category learner** | یادگیری از تصحیحِ انسان | طراحی | rule + Sonnet |
| **P&L dashboard** | P&L تجمیعیِ اکوسیستم | طراحی، بلاک روی upstream | — |

> **بلوکِ تصمیمِ #5 — Model Tiering (Haiku→Sonnet→Opus).**
> **چرا:** هزینه را با ریسکِ کار تطبیق می‌دهد (استخراج ارزان، ریسکِ انطباق گران). **مشکل:** بودجهٔ سختِ AU$30/ماه برای بات‌های متری. **جایگزین رد:** همه‌کار با Opus (گران و بی‌مورد). **وابستگی:** PII-tokenization قبلِ هر فراخوان. **ریسک:** مدلِ ضعیف روی categorize → با verdictِ انسانی و confidence-threshold مهار. **پیچیدگی:** ۶. **اطمینان:** ⟨c=0.8⟩

### ۵.۵ گردش‌کارهای انطباق (طراحی، `[Unverified]`)

- **GST/BAS:** فصلی (گردش < $20M)؛ سررسید ۲۸امِ ماهِ بعد. GST جمع‌شده روی درآمد − GST قابل‌claim روی هزینهٔ business دارای ABN/مدرک. هیچ عددی «قابل‌ارسال» معرفی نمی‌شود.
- **TPAR** (Taxable Payments Annual Report): صنعتِ ساختمان/نقاشی احتمالاً مشمول است اگر به پیمانکارها پرداخت شود — سررسید ۲۸ آگوست. `[Unverified — حسابدار]`
- **Div 7A:** پرداخت به associate از حسابِ business → کاندیدِ deemed dividend؛ فقط **فهرست** می‌شود (نه قضاوت). نرخِ benchmark ۲۵-۲۶ ≈ ۸.۳۷٪.
- **PAYG/Super/STP:** اگر کارگر (Behzad/رضا) employee باشد؛ Payday Super از ۱ جولای ۲۰۲۶.
- **Crypto/Mining:** CGT (real asset) vs revenue (CFD, TR 2005/15)؛ mining = درآمد به ارزشِ لحظهٔ دریافت. کراس‌رفرنس به لِگ‌های Crypto/Mining.
- **نگهداریِ سوابق:** ۵ سال ATO + ۷ سال Corporations Act. `[Verified: ato.gov.au]`

---

## §6 — مدلِ داده، IDها، مرجعِ کانونی، نرمال‌سازی

**SSOT rules:** (۱) هر واقعیت فقط یک خانهٔ کانونی دارد؛ بقیه با لینک به آن اشاره می‌کنند، نه کپی. (۲) نام‌گذاریِ فایل: `<موضوع>-<scope>-<state>-<YYYY-MM-DD>.<ext>`. (۳) هر عدد **برنامه‌ای و بازتولیدپذیر** است (فرمول/کد ضمیمه). (۴) اعدادِ ground-truth (self-check ایجنت) در یک نوتِ قفل‌شده. (۵) canonical reference برای هر موجودیت (associate, account, vendor, client) یک نوت با `id` پایدار.

---

## §7 — حاکمیت، ممیزی، رصد، امنیت

**Security Gate (بسته):** ۴ ردیفِ CRITICAL باید rotate شوند تا هر اتوماسیونِ نوشتنی روشن شود: **Monero seed** (مشترک با Mining) · **Bybit** + **OKX** (مشترک با Crypto) · **Anthropic keys** (مشترک با Lead+Mining+Crypto). تا آن‌موقع کلِ FinOS **read-only/draft**. مرجع: `ROTATION_CHECKLIST`. ⟨c=0.95⟩

**ستون‌های امنیت/ممیزی:**
- **Anchor Ledger** (append-only): هر verdict/ثبت لاگ می‌شود؛ زمان‌سفر و ممیزی از همین‌جا.
- **Kill-switch:** پرچمِ `halted` (DB) + فایلِ `STOP` → fail-closed؛ همهٔ چرخه‌ها رد می‌شوند.
- **PII tokenization:** نام/مبلغ/شمارهٔ حساب قبل از هر inference توکنایز؛ هرگز به سرویسِ ثالث نمی‌رود. دادهٔ خامِ PII (xlsxها، لاگ تلگرام، رسیدها) **هرگز وارد LLM نمی‌شود**.
- **Budget hard-stop:** اشتراکِ Cowork ~AU$300/ماه (کارِ سنگین)؛ بات‌های متری **AU$30/ماه**؛ APIِ حسابداری ~$۵–۱۵ داخلِ همین سقف.
- **No-LLM-in-command-path (P11):** intent-router قانون‌محور؛ LLM فقط پیشنهاد می‌دهد.
- **Quarantine:** بستهٔ `ACC-05-DO-NOT-FORWARD` (اسکرین‌شاتِ چتِ شخصی) هرگز فوروارد/باز نمی‌شود.

---

## §8 — Integration / MCP Catalog + Hybrid Local↔Cloud

| اتصال | نوع | حالت | نکته |
|---|---|---|---|
| **ANZ CSV (PS Export)** | ورودیِ منبعِ حقیقت | دستی export → Inbox | dedup(ID) + reconcile(Closing Balance) |
| **Xero API** | هستهٔ منطبق (proposed) | draft-only | MYOB قطع شود (هر دو شارژ می‌شوند) |
| **ATO/ASIC** | خروجی | **فقط انسان** — ایجنت هرگز lodge نمی‌کند | — |
| **Telegram** | verdict + alert | langar میزبان | timeout=DENY |
| **Exchange keys (Bybit/OKX)** | Crypto | **off-box، صفر LLM، هم‌امضا** (D-11) | — |
| **MCP (Cowork)** | ابزارها | on-demand | connectorهای auth-دار در تنظیمات |

> **بلوکِ تصمیمِ #6 — Hybrid Local (OrangePi) + Cloud (Cowork).**
> **چرا:** دادهٔ حساسِ مالی و monitorهای همیشه‌روشن روی **OrangePi hub محلی** (کنترل + حریمِ خصوصی)، کارِ سنگینِ تحلیل/ساخت روی **Cowud cloud** (قدرت). **مشکل:** هم حریم خصوصی هم قدرت را می‌خواهی. **جایگزین رد:** all-cloud (PII در ابر) یا all-local (قدرتِ ناکافی). **ریسک:** SPOFِ OrangePi5+ (در manifest Crypto فلگ شده) → نیاز به failover. **پیچیدگی:** ۷. **اطمینان:** ⟨c=0.72⟩

---

## §9 — لاگِ حلِ تعارض (Conflict Resolution)

| # | تعارض/تکرار | حل (با شواهد) | اطمینان |
|---|---|---|---|
| C1 | دادهٔ مالی داخلِ `03-Projects/Accounting/data` ولی Accounting «عرضی» است | ناحیهٔ جدیدِ `05 - Finance`؛ کد در پروژه، داده در Finance | ⟨0.75 · OPEN⟩ |
| C2 | Dataview vs Bases vs Datacore | Bases موتورِ اصلی، Dataview مکمل، Datacore بعداً | ⟨0.8⟩ |
| C3 | ساختار شرکت: sole trader (Tax Map) vs Pty Ltd (MANIFEST/PROJECT) | **تعارضِ واقعی** → verdictِ حسابدار؛ فعلاً هر دو مسیر مستند | ⟨0.4 · OPEN⟩ |
| C4 | «۴ رسیدِ واقعی» (README) vs «رسیدها اسکرین‌شاتِ چت‌اند، قرنطینه» (megaprompt) | قرنطینه درست است؛ رسیدِ واقعی = صفر؛ منتظرِ golden set | ⟨0.9⟩ |
| C5 | MYOB + Xero هم‌زمان | یکی (Xero) نگه، دیگری قطع | ⟨0.85 · verdict مالک⟩ |
| C6 | تگ‌های آزادِ پراکنده | تاکسونومیِ ۳-محورِ §4.3 + اسکریپتِ مهاجرت | ⟨0.8⟩ |
| C7 | چند «master spec» (MYCELIAL, LIVING-BRAIN, TWO-BRAIN, FRANKENSTEIN) | این بلوپرینت به‌عنوان SSOT معماری؛ بقیه به‌عنوان زیرسند لینک می‌شوند | ⟨0.7 · OPEN⟩ |

---

## §10 — رجیسترِ فرضیات (Confidence-Scored)

| ID | فرض | اطمینان | چطور تأیید شود |
|---|---|---|---|
| A1 | ساختار Pty Ltd (ثبت‌شده/در حال ثبت) | ⟨0.5⟩ | مالک + ASIC |
| A2 | همهٔ قواعدِ مالیاتی تا تأییدِ حسابدار `[Unverified]` | ⟨0.99⟩ | Registered Tax Agent |
| A3 | صنعتِ نقاشی مشمولِ TPAR | ⟨0.6⟩ | حسابدار |
| A4 | کریپتو باید شخصی بماند (نه شرکت، به‌خاطرِ CGT) | ⟨0.7⟩ | حسابدار |
| A5 | Bases برای مقیاسِ فعلی کافی است | ⟨0.75⟩ | تستِ روی vaultِ واقعی |
| A6 | OrangePi hub برای monitorهای محلی مناسب است | ⟨0.7⟩ | تستِ بار |
| A7 | گردشِ سالانه > $75k (پس GST اجباری) | ⟨0.8⟩ | داده‌های FY جاری |
| A8 | Behzad/رضا وضعیتشان employee/contractor نامشخص | ⟨0.9⟩ | ابزار ATO + حسابدار |

---

## §11 — رجیسترِ ریسک (Top)

| ریسک | شدت | کاهش |
|---|---|---|
| Division 7A (برداشتِ بدونِ ساختار) | 🔴 | salary/dividend/loan را با حسابدار پیش از lodgment حل کن؛ associates sub-ledger |
| قاطی‌شدنِ شخصی/بیزنس (بزرگ‌ترین فلگِ ممیزی) | 🔴 | حسابِ business جدا؛ scope اجباری روی هر رکورد |
| worker misclassification (Sham contracting) | 🔴 | تعیینِ وضعیت با ابزارِ ATO؛ payroll+workers comp |
| Security Gate باز نشدنِ کلیدها | 🟠 | ROTATION_CHECKLIST؛ تا آن‌موقع read-only |
| PII leak به LLM | 🟠 | tokenization اجباری؛ دادهٔ خام هرگز وارد نمی‌شود |
| SPOF سخت‌افزار (OrangePi) | 🟡 | failover/بکاپ |
| IAWO cliff ($20k→$1k از ۱ جولای ۲۰۲۶) | 🟡 | زمان‌بندیِ خریدِ تجهیزات با حسابدار |

---

## §12 — Rollout فازبندی‌شده (آشتی با Ecosystem-Rollout موجود)

- **فاز ۰ — رفعِ انسداد (فقط مالک):** rotate ۴ CRITICAL → باز کردنِ Security Gate. *(پیش‌نیازِ هر اتوماسیون.)*
- **فاز ۱ — تمیزکاریِ هسته (بی‌خطر، همین حالا draft):** رفعِ باگِ GST (`total/11`)؛ جداسازیِ حساب؛ انتخابِ حسابدار؛ ANZ importer (dedup+reconcile)؛ قطعِ MYOB؛ Associates Registry؛ ساختِ `05 - Finance` + Property Schema + Bases dashboards.
- **فاز ۲ — سیم‌کشیِ cross-project:** CoA مشترک؛ tax touchpoint در هر PROJECT؛ قفل‌کردنِ رفتارِ هر جریان (Mining/Crypto/Project-F).
- **فاز ۳ — Compliance Monitor + گزارش (بعدِ گیت):** اسکنِ ماهانه (Div7A/no-ABN/>$10k/BAS-due)؛ گزارش با verdict به Dashboard + Telegram؛ داخلِ بودجهٔ AU$30.
- **فاز ۴ — داشبوردِ مالیِ یکپارچه:** P&L تجمیعیِ همهٔ جریان‌ها؛ گزارشِ ماهانهٔ «سلامتِ مالیِ اکوسیستم» به‌عنوان ورودیِ تصمیمِ architect.

---

## §13 — verdictهای باز (تجمیعی) + اقداماتِ فوری

**فقط مالک (این هفته):**
1. rotate ۴ CRITICAL → گیت باز شود (کلِ اکوسیستم را unblock می‌کند).
2. انتخابِ **Registered Tax Agent** (بلاکر #۱) + طرحِ سؤالِ «یک Pty Ltd یا چند شرکت؟».
3. جداسازیِ حسابِ business از شخصی.
4. تعیینِ وضعیتِ Behzad/رضا (employee/contractor).
5. verdict روی `05 - Finance` (C1) و قطعِ MYOB (C5).

**ایجنت (مجاز، draft-only، همین حالا):** رفعِ باگِ GST؛ اسکلتِ ANZ importer؛ ساختِ Property Schema + Bases dashboards + templateها؛ Associates sub-ledger draft. **هیچ اتوماسیونِ نوشتنی تا بازِ گیت.**

**صف‌های verdict موجود:** CRY-V1..V6 (Crypto) · ACC-V1..V12 (Accounting) — در بسته‌های مربوطه.

---

## §14 — مسیرِ ارتقا / چشم‌اندازِ ۲۰۲۷

Markdown/CSV projections → SQLite → event store؛ Bases → (در صورتِ نیاز) app اختصاصی؛ importerِ دستی → اتصالِ بانکیِ خودکار (بعدِ گیت)؛ single-owner → چند-کاربر (حسابدار به‌عنوان reviewer)؛ افزودنِ «Decision Intelligence» (چرا هر تصمیم گرفته شد، با Explainable-AI روی Anchor Ledger). هدفِ ۲۰۲۷: یک **سیستم‌عاملِ مالیِ خود-مستندساز** که هر عددش تا رویدادِ منبع قابلِ ردیابی است.

---

## §15 — منابع (Sources)

- اسنادِ خودت: `ARCHITECT_CHARTER` · `Ecosystem-Rollout-Plan` · Accounting `MANIFEST/PROJECT/README` · `Tax-and-Loan-Guide` · `Tax Map FY2025-26` · Crypto/Mining manifestها · megapromptها.
- ATO/AU: [company tax rates](https://www.ato.gov.au/tax-rates-and-codes/company-tax-rates/tax-rates-2025-26) · [Div 7A benchmark](https://www.ato.gov.au/tax-rates-and-codes/division-7a-benchmark-interest-rate) · [payday super](https://www.ato.gov.au/businesses-and-organisations/super-for-employers/payday-super) · [IAWO](https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/depreciation-and-capital-expenses-and-allowances/simpler-depreciation-for-small-business/instant-asset-write-off) · [crypto CGT](https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments) · [TPAR](https://lawbydesign.com.au/post/tpar-contractor-payments-australia-2026/) · [record-keeping](https://www.ato.gov.au/businesses-and-organisations/preparing-lodging-and-paying/record-keeping-for-business).
- الگوهای مهندسی: [Fowler — Accounting Patterns](https://martinfowler.com/eaaDev/AccountingNarrative.html) · [CQRS & Event Sourcing in financial services](https://iconsolutions.com/blog/cqrs-event-sourcing) · [event sourcing](https://microservices.io/patterns/data/event-sourcing.html) · [agentic accounting 2026](https://www.apideck.com/blog/ai-in-accounting) · [digital twins + knowledge graphs](https://enterprise-knowledge.com/digital-twins-and-knowledge-graphs/).

---
*نسخه: FINOS-SSOT v1.0 (draft) · جلسهٔ Cowork 2026-07-13 · این سند SSOT معماری است؛ هر تغییرِ بزرگ = ورودیِ DecisionLog + آپدیتِ همین‌جا. مالیات: `[Unverified]` تا Registered Tax Agent.*
