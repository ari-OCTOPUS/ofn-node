---
type: report
project: "[[03 - Projects/Accounting/PROJECT]]"
status: active
created: 2026-07-17
updated: 2026-07-29
created_by: deep-scan agent (ZCode)
tags: [accounting, pocketsmith, deep-scan, status, read-first]
aliases: ["دیپ‌اسکن Accounting PocketSmith", "PocketSmith Status Check"]
# purpose: "وضعیت راستی‌آزمایی‌شدهٔ اتصال PocketSmith و موتور حسابداری، با پرامپت اجرایی پیوست."
---

# 🔭 DEEP SCAN — Accounting / PocketSmith — 2026-07-17

> **پرسش مالک:** «آیا حسابداری اپدیت هست با PocketSmith یا نه؟»
> **پاسخ کوتاه (یک‌خطی):** کدِ PocketSmith کامل و راستی‌آزمایی‌شده ساخته شده، ولی **هیچ‌کدام از فلگ‌های live روشن نیستند**. آخرین sync داده‌های **تا ۲۰۲۶-۰۴-۲۰** است (~۳ ماه stale). یعنی API حداقل یک‌بار در گذشته وصل بوده ولی الان در حالت **read-only خاموش** است و داده‌ها قدیمی‌اند. باید دوباره sync زده شود.

---

## ۱. اتصال PocketSmith — وضعیت واقعی همین الان

| محور | وضعیت | مدرک |
|---|---|---|
| API key در `.env` | ✅ **موجود** (`POCKETSMITH_API_KEY=<set>`) | `.env` |
| فلگ `OCTOPUS_WIRE_POCKETSMITH` | 🔴 **خاموش** (در `.env` نیست) | `.env` فقط `OCTOPUS_WIRE_MINING` روشن |
| فلگ `OCTOPUS_WIRE_PS_WRITEBACK` | 🔴 خاموش | `.env` |
| فلگ `ACCT_BEAT_SYNC` | 🔴 خاموش | `.env` |
| آخرین sync موفق | ⚠️ **داده‌ها تا ۲۰۲۶-۰۴-۲۰** | `txn-store.json` generated=2026-07-16T11:33 اما max date=2026-04-20 |
| تعداد تراکنش‌ها | **۵۷۶** | `txn-store.json` count=576 |
| منبع داده‌ها | ۴۱۹ از API + ۱۵۷ از CSV (Armin/Rent/behzad/maliheh/sume) | توزیع source |
| writeback تا الان | 🔴 **هرگز اجرا نشده** | فایل‌های `ps-writeback*` وجود ندارند |
| فلگ‌های Xero (ریل A) | 🔴 **خاموش + کلیدها نیستند** | `.env` کلید XERO ندارد |

### تفکیک منبع داده (۵۷۶ تراکنش)
```
419  pocketsmith-api     ← حداقل یک‌بار API وصل بوده
 69  csv:maliheh
 49  csv:sume asadi
 20  csv:behzad
 13  csv:Rent
  6  csv:Armin
```

### وضعیت review/classification (هشدار کیفیت)
```
review:    528 needs_review · 27 auto · 21 confirmed   ← فقط ۳٫۶٪ تأییدشده!
ptype:     478 unknown · 38 expense · 26 wage · 24 transfer · 10 income
```
**نتیجه:** ۸۳٪ تراکنش‌ها هنوز `unknown` و در صف مرورند. اعداد سطحِ طرف/بیزنس محکم‌اند (چون transferها از net حذف می‌شوند) ولی دسته‌بندی ریزِ خرج ناتمام.

---

## ۲. چه چیزی واقعاً ساخته‌شده vs اجراشده

### ✅ ساخته‌شده و تست‌شده (کد موجود در `_ops/legs/`)
- `money.py` — موتور سنتِ صحیح (integer cents، float ممنوع). استاندارد طلایی.
- `pocketsmith_api.py` — کلاینت read-only API v2 (`/me`, `/users/{id}/transactions`). پشت فلگ، key هرگز log نمی‌شود. ۷ تست.
- `txn_store.py` — مخزن یکتا، dedup با content-hash، ۲۶۱ خط.
- `attributor.py` — دسته‌بندِ قاعده‌محور (income/expense/wage/transfer).
- `accountant.py` — ارکستراتور multi-agent + کارت `/finance` (PII-safe، k-anonymity≥2).
- `acct_review.py` — مرور تلگرامیِ تعاملی (`/review`).
- `ps_writeback.py` — write-back برچسب‌ها به PocketSmith (تنها استثنای صفر-نوشتن، PUT فقط `labels`). ۲۰+ تست.
- `ledger_core.py` — **دفتر دوطرفهٔ واقعی (double-entry)** با COA، append-only، reversal، GST gate، قفل دوره.
- `journal_bridge.py` — پلِ label → double-entry (4 ptype → journal entries).
- `recon.py` — reconciliation تراکنش‌به‌تراکنش (strict، ضد خطای پنهان).
- `raw_store.py` + `acct_memory.py` + `txn_categorize.py` (local-first ollama، cloud با scrub).

### ✅ معماری قطعی‌شده (رأی مالک ۲۰۲۶-۰۷-۱۶ — `ARCHITECTURE-TWO-RAILS.md`)
- **ریل B (خانوادگی، آرمین↔عباس):** PocketSmith = منبع. کامل و سخت‌شده (۵ دور verify خصمانه).
- **ریل A (شرکت، ATO):** **Xero** انتخاب شد (تحقیق ۵-ایجنتی). `company_books.py` + `books_xero.py` ساخته‌شده ولی **کلیدها تنظیم‌نشده**.

### 🔴 ساخته‌شده ولی هرگز اجرا نشده (state files وجود ندارند)
- **double-entry ledger:** دایرکتوری `personal/ledger/` خالی است، `journals.jsonl` نیست → `ledger_core` هرگز چیزی post نکرده.
- `journal-proposals.json` نیست → `journal_bridge.rebuild()` هرگز اجرا نشده.
- `review-session.json` نیست → `/review` تعاملی هرگز شروع نشده.
- `ps-writeback*` نیست → writeback هرگز flush نشده.

**تفسیر:** پروژه در فاز «کد کامل، فعال‌سازی نکرده» است. آخرین کار مفید = تولید گزارش `personal/REPORT-2026-07-16.md` (با داده‌های تا آوریل).

---

## ۳. گزارش آخر (۲۰۲۶-۰۷-۱۶) — اعداد کلیدی

از `personal/REPORT-2026-07-16.md` (داده‌ها تا ۲۰۲۶-۰۴-۲۰، reconcile GREEN):

| طرف | خالص بانکی | نقش |
|---|---:|---|
| عباس (حساب بیزنس) | **+$۵٬۳۹۴** | مرکز کار |
| آرمین (حساب تو) | **−$۱۲٬۶۰۳** | کارگر + عبور پول |
| sume asadi | −$۲۷٬۰۷۸ | پیمانکار |
| اجاره | −$۱۷٬۱۳۸ | هزینه ثابت |
| maliheh | −$۷٬۴۵۷ | پیمانکار |
| behzad | −$۱٬۷۵۰ | پیمانکار |

- درآمدِ مشتریان شناسایی‌شده: **$۴۲٬۰۷۴** (Carmy $۱۴٬۴۰۰ رأس).
- حقوق آرمین برچسب‌خورده: **$۱۹٬۲۵۰** در ۲۶ قلم (خام — شامل موارد ۲۰۲۴).
- pass-through ~$۹٬۶۰۸ از net حذف شد (ضدِ double-count).
- **۳ مورد باز برای مالک** (هنوز تأییدنشده): حقوق-عباس-به-آرمین $۷٬۱۰۰ (۲۰ آوریل) · ۶ خروجی بی‌صاحب جمعاً −$۱۱٬۰۲۰ · تأییدِ ۸ مشتری.

---

## ۴. MEGAPROMPT vs واقعیت — تصحیح مهم

MEGAPROMPT (۲۰۲۶-۰۷-۱۶، repo root) ادعا می‌کند سیستم «single-entry با ۳ ptype و owner=account-holder» است و می‌خواهد آن را به double-entry ارتقا دهد. **این ادعا تا حدی تاریخ‌گذشته است:**

| ادعای MEGAPROMPT | واقعیتِ کد |
|---|---|
| «single-entry، ۳ ptype» | ✅ لایهٔ label single-entry هست (۴ ptype در واقعیت: income/expense/wage/transfer) |
| «نبود Chart of Accounts» | ❌ **غلط** — `ledger_core.DEFAULT_COA` وجود دارد (۱۲ حساب) + قابل گسترش از `policy-profile.json` |
| «نبود double-entry» | ❌ **غلط** — `ledger_core.py` double-entry کامل با Dr/Cr متوازن، append-only، reversal ساخته شده |
| «نبود immutable ledger» | ❌ **غلط** — هم `ledger_core` و هم `raw_store.py` immutable هستند |
| «dedup content-hash باید external_ref شود» | ⚠️ **نیمه‌درست** — API rows از PS numeric id استفاده می‌کنند (external_ref)، ولی CSV/xlsx همچنان content-hash. باگِ دو-هشِ ناهماهنگ (`_hash` تمامِ desc vs `_content_hash` desc[:20]) واقعاً هست. |
| «owner با account-holder خلط شده» | ✅ درست — `owner` هم مالک اقتصادی هم صاحب حساب است (مدل REA پیاده‌نشده) |

**نتیجه:** ارتقای MEGAPROMPT تا حد زیادی **از قبل ساخته شده** (`ledger_core` + `journal_bridge`). آنچه واقعاً ناقص است:
1. **فعال‌سازی/اجرا** (ledger dir خالی).
2. **کامل‌سازی COA** (۱۲ حساب فعلی، MEGAPROMPT ۲۵+ حساب می‌خواهد: تفکیک پیمانکاران به‌نام، AR/AP، Tools/Equipment، Fuel، Insurance، Marketing).
3. **تغییر dedup** به external_ref یکپارچه + رفع باگِ دو-هش.
4. **مدل REA** (جداسازی account-holder از beneficial-owner).

---

## ۵. تست‌ها

| فایل تست | تعداد | پوشش |
|---|---|---|
| `test_ps_writeback.py` | ۲۰+ | writeback کامل (guards، idempotent، 403، lock، race) |
| `test_pocketsmith_api.py` | ۷ | API read-only با mock |
| `test_journal_bridge.py` | ۷ | 4 ptype → double-entry + guards |
| `test_pocketsmith_import.py` | ۳ | xlsx import |
| `test_acct_beat.py` | ۴ | heartbeat در wiring |
| `test_books_telegram.py` | ۴ | `/books` + `/finance` |

**بدون تست مستقیم:** `recon.py`، `accountant.py` (بخش network)، `ledger_core` (تست غیرمستقیم از طریق bridge).

---

## ۶. بلاکرها و ریسک‌ها

1. **داده stale (~۳ ماه):** آخرین تراکنش ۲۰۲۶-۰۴-۲۰. امروز ۲۰۲۶-۰۷-۱۷. گزارش‌های مالی ناقص.
2. **۴۷۸ تراکنش unknown/needs_review (۸۳٪):** دسته‌بندی ریز ناتمام.
3. **فلگ‌ها خاموش:** کل pipeline در حالت خواب.
4. **باگ دو-هش dedup** (`_hash` تمام desc vs `_content_hash` desc[:20]) — ریسک double-count در migration.
5. **Xero (ریل A) کلاً راه‌اندازی‌نشده** — کلیدها نیستند، خرید انجام‌نشده.
6. **۱۰ verdict معلق** در `VERDICT_QUEUE.md` (تاریخ ۲۰۲۶-۰۷-۱۲): ACC-V1 تا V10 — مهم‌ترین‌ها: حسابدار انتخاب‌نشده (V1)، ساختار کسب‌وکار (V2)، GST registered (V4).
7. **PII در کد:** `journal_bridge.py:45` نام‌های واقعی به‌عنوان کلید account mapping (`rent/sume/maliheh/behzad`). `ENTITY_ID="armin-abn"` hardcoded.
8. **MEGAPROMPT فراموش‌کرده که `ledger_core` را ساخته‌اند** — خطر کارِ تکراری.

---

## ۷. جمع‌بندی: آیا اپدیت هست؟

**خیر، به‌روز نیست.** سه مشکل:
1. **سینک نشده** (داده تا آوریل، ۳ ماه عقب).
2. **فعال‌سازی نشده** (فلگ‌ها خاموش، double-entry هرگز اجرا نشده).
3. **دسته‌بندی ناقص** (۸۳٪ unknown).

**اما کد سالم و آماده‌ست.** مشکل عملیاتی است، نه فنی. دو مسیر پیش روی مالک:
- **مسیر سریع (همین جلسه):** فقط sync دوباره + روشن‌کردن فلگ read-only → داده‌های تا امروز.
- **مسیر عمیق (MEGAPROMPT):** فعال‌سازی ledger دوطرفه + تکمیل COA + رفع باگ dedup → حسابداری واقعی.

---

> **پرامپت اجرایی پیوست در ادامه (§8).**
