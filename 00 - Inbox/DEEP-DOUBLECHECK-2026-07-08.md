---
type: report
kind: deep-doublecheck
status: done
created: 2026-07-08
updated: 2026-07-29
tags: [octopus, audit]
created_by: Agent-Auditor (GLM)
# scope: read-only, propose-only, secret-metadata-only
extends: "[[07 - Knowledge/_audit/MASTER_REPORT]]"
---

# DEEP DOUBLE-CHECK — 2026-07-08

> مأموریت: پیدا کردنِ دادهٔ خوانده‌نشده/ingest‌نشده که نتیجه‌گیری‌های قبلی را ناقص می‌کند.
> روش: walk کاملِ درخت (به‌جز `.agentignore`)، گرافِ ارجاع، diff ORPHAN/DANGLING، طبقه‌بندی، نمرهٔ پوشش.
> **صفر نوشتن روی منبع.** فقط گزارش. هرگز محتوای `*.env/*key*/*seed*/*wallet*` باز/echo نشد (طبقِ `.agentignore`).

---

## خلاصهٔ اجرایی

| معیار | مقدار |
|---|---|
| کل فایل‌ها (non-secret, non-skip) | **12,378** (1,918.9 MB) |
| فایل‌های نویز (worktree/venv) | ~9,800 (در `.claude/` + `_launchpad/` + `survival-gateway/`) |
| دادهٔ خامِ قابلِ ingestion (pdf/xlsx/csv/parquet/docx, non-noise) | **48 فایل (~25 MB)** |
| نمرهٔ **پوشش** (دادهٔ خام با نوتِ ارجاعی) | **۳۵٪** (۱۷/۴۸ covered، **۳۱ uncovered**) |
| پروژه‌هایی با PROJECT.md | **۶/۶** ✅ |
| رویدادهای MONEY_ATTRIBUTION در ledger زنده | **۰** (Track B هنوز فقط در تست) |

**سه ریسکِ ساختاریِ اصلی** (جزئیات در §E):
1. **۶۵٪ دادهٔ خامِ پاهای فعال transcription ندارد** — مخصوصاً Accounting (۶ xlsx مالی = ۰ نوت) و Mining (۱۶ PDF = ۰ نوت).
2. **Track B هرگز روی ledger زنده نرفته** — ۰ MONEY_ATTRIBUTION؛ `reconcile/` فقط README دارد. حلقهٔ paper-dollar در تست سبز است ولی در runtime فعال نیست.
3. **دادهٔ خام در `.claude/worktrees/*` (۷ worktree)** موازی‌اند ولی canonical در درختِ اصلی است — ریسکِ کور شدن از کپیِ کهنه.

---

## فاز A — inventoryِ کامل

### شمارشِ کل (raw counts)
```
count=12378  size=1918.9 MB
```

### top-level dirs (file count)
```
  7211  .claude              ← نویز: worktreeهای قدیمی
  1676  survival-gateway     ← نویز: runtime gateway
  1655  _launchpad           ← نویز: second-brain runtime
   693  08 - Assets
   379  03 - Projects
   216  07 - Knowledge
   148  00 - Inbox
   121  04 - Architect System
    70  _ops
    38  CHRONOS-FABLE-OS
```

### شمارشِ پسوند (top)
```
  4310  .jpg (624 MB)        ← عمدتاً 08-Assets/Photos + Accounting/photos
  2923  .md (46 MB)
  1838  (noext) (67 MB)
  1829  .py (17 MB)          ← includes venv noise
   221  .pdf (128 MB)        ← ← دادهٔ خامِ actionable
   152  .json (709 MB)       ← map files + venv
   142  .txt (74 MB)
    35  .xlsx (281 KB)       ← ← دادهٔ مالی
    14  .csv (17 MB)
    14  .parquet (78 KB)
```

### دادهٔ خامِ ویژه (پاهای فعال)
| پروژه | نوع | فایل | نوت؟ |
|---|---|---|---|
| **Accounting** | 6 × .xlsx (۴۴ KB) | Armin/Rent/behzad/maliheh/sume asadi/حساب و کتاب | **۰ نوت** |
| **Crypto-etoro** | 8 × .pdf (1.2 MB) | briefings/handoffs/scout prompts | ۰ نوت PDF-specific |
| **Mining** | 16 × .pdf (19.6 MB) | Quantum dataset (7) + strategy (6) + bot (3) | **۰ نوت** |
| **Lead-نقاشی** | 2 × .pdf (۹۳ KB) | Estimate 0100-A, 0101-B | ارجاع در نوت‌ها هست |
| **Ziman** | 1 × .xlsx | FirstSale-Tracker | ارجاع در نوت‌ها هست |

---

## فاز B — گرافِ ارجاع

```
md/jsonl files scanned: 659
unique referenced targets: 2,340
files on disk (non-skip): 12,379
```

منابعِ اسکن: همهٔ `*.md` + `*.jsonl` (به‌جز نویز). الگوها: `[[wikilink]]` + path-cite (مسیر/پسوند).

---

## فاز C — diff: ORPHAN vs DANGLING

### DANGLING (ارجاع‌شده ولی غایب)
```
count=1040 (اما ~۹۰۰ regex-noise: رشته‌های عددی که pathcite اشتباهاً path گرفته)
real dangling ≈ 100-140 (مجسمه‌های تاریخچه Inbox که rename/move شده‌اند)
```
نمونهٔ واقعی: `00 - Inbox/2026-07-06 0245 MASTER-ARCHITECTURE-SPEC-v1.4-draft\` (با بک‌اسلشِ ته — احتمالاً escape در نوت). این‌ها عمدتاً Inbox قدیمی‌اند و ریسکِ پایین.

### ORPHAN (روی دیسک ولی ارجاع‌نشده) — فقط دادهٔ خام + نوت
```
actionable orphans (raw data unreferenced): 769
  703 .jpg   ← 08-Assets/Photos (عمدتاً کم‌اهمیت، skip)
   37 .pdf   ← ← اصلی
   20 .jpeg
    6 .xlsx  ← ← اصلی (Accounting)
    2 .png
    1 .csv
```
**by project (uncovered raw):**
```
  625 Photos          ← skip (08-Assets)
   81 Mining          ← ← 16 PDF استراتژی/quantum
   30 Crypto-etoro    ← ← 8 PDF briefing
   12 هیپنوتیزم
   10 Accounting      ← ← 6 xlsx مالی
    8 اونلی فنز
```

---

## فاز D — طبقه‌بندیِ orphanها

### D-1) دادهٔ خامِ نیازمندِ transcription
| دسته | تعداد | اندازه | توضیح |
|---|---|---|---|
| Accounting xlsx | 6 | 44 KB | **دادهٔ مالیِ شخصی** — PII؛ فقط محلی، هرگز به LLM. نیازمندِ transcription دستی/داخل-سیستم. |
| Crypto PDFs | 8 | 1.2 MB | briefings/handoffs — محتوای تصمیمِ معاملاتی؛ transcription ایمن (نه PII). |
| Mining PDFs | 16 | 19.6 MB | quantum dataset + strategy — بزرگ‌ترین تکهٔ منتقل‌نشده. |

### D-2) کدِ بی‌نوت (بدونِ .md در همان پوشه)
`_ops/legs/`, `_ops/panel/`, `_ops/tests/` — کد، بدونِ README پوشه. docstring داخلِ فایل‌ها هست ولی **نوتِ سطحِ پوشه** نیست. اولویتِ پایین (کد docstringدار است).

### D-3) کانِنِ موازیِ reconcile‌نشده
**خبر خوب:** کانِن موازیِ خطرناک **نیست**.
- `ledger.py`: فقط ۲ نسخه (canonical + یک backup staging) — سازگار.
- `chrono.py`: فقط ۱ نسخه (`_ops/chrono.py`).
- `ORGANISM-SPEC.md`: فقط ۱ نسخه.
- `CHRONOS-FABLE-OS/` = کانِنِ **مرجع/تحقیق** (read-only spec)، `_ops/` = کانِنِ **اجرا**. هم‌پوشانیِ عمدی (spec→impl)، نه تناقض.

### D-4) کپیِ موازی: `.claude/worktrees/*`
**۷ worktree** وجود دارد. بررسی شد: **دادهٔ خامِ Accounting/Crypto در worktreeها نیست** (فقط snapshot کاملِ vault). بنابراین:
- **canonical = درختِ اصلی** (`F:\backup\03 - Projects/...`)
- worktreeها = کپی‌های کهنهٔ session‌های قبلی (jolly-ardinghelli، hopeful-elgamal، و غیره).
- **ریسک:** اگر کسی در worktree ویرایش کند و main رها شود، drift. ولی فعلاً دادهٔ raw منحصر به worktree نیست.

### D-5) duplicate/archive
- `_Archive/`, `_Duplicates/` = skip (طبق `.agentignore`، فقط مقصدِ mv).
- `_backups/` در genome = staging snapshots (`.tar.gz`) — count فقط.

---

## فاز E — خروجی (propose-only)

### 📊 نمرهٔ پوشش
```
دادهٔ خام (pdf/xlsx/csv/parquet/docx, non-noise): 48 فایل
├── COVERED (ارجاع در نوت):   17 (35%)
└── UNCOVERED (بی‌نوت):        31 (65%)  ← ← شکاف
```
**تفسیر:** بیش از سه‌چهارمِ دادهٔ خامِ پاهای فعال (Accounting 100% uncovered، Mining 100% uncovered، Crypto 100% uncovered) منتقل‌نشده است. Lead-نقاشی و Ziman پوششِ بهتر دارند.

### 📥 صفِ ingestionِ اولویت‌دار (top 10)
اولویت = پاهای فعال (Accounting, Crypto, Lead) → Mining → بقیه. درونِ هر پروژه، size desc.

| # | فایل | اندازه | پروژه | چرا |
|---|---|---|---|---|
| 1 | `Crypto - etoro/armin briefing june11 2026.pdf` | 258 KB | Crypto | briefing اصلیِ اپراتور |
| 2 | `Crypto - etoro/SENTINEL BUILD PROMPT.pdf` | 239 KB | Crypto | پرامپتِ build |
| 3 | `Crypto - etoro/briefing june2026 market.pdf` | 174 KB | Crypto | وضعیتِ بازار |
| 4 | `Crypto - etoro/watchlist-handoff-2026-06.pdf` | 156 KB | Crypto | فهرستِ دارایی |
| 5 | `Crypto - etoro/big scenarios framework.pdf` | 141 KB | Crypto | سناریوها |
| 6 | `Crypto - etoro/session knowledge handoff.pdf` | 101 KB | Crypto | انتقالِ جلسه |
| 7 | `Crypto - etoro/tier1 scout prompt.pdf` | 77 KB | Crypto | پرامپتِ scout |
| 8 | `Crypto - etoro/WLD handoff brief.pdf` | 62 KB | Crypto | داراییِ WLD |
| 9 | `Accounting/data/حساب کتاب/حساب و کتاب.xlsx` | 10 KB | Accounting | **دادهٔ مالی** ⚠ PII |
| 10 | `Accounting/data/حساب کتاب/maliheh.xlsx` | 10 KB | Accounting | **دادهٔ مالی** ⚠ PII |

⚠ **هشدار PII:** فایل‌های Accounting حاوی دادهٔ مالی/شخصی هستند (طبق D-26). transcription باید **داخل-سیستم/محلی** باشد، هرگز به LLM بیرونی. برای PDFs غیر-PII، transcription با LLM مجاز است.

### 🚨 سه ریسکِ ساختاریِ اصلی (نیازمندِ verdict مالک)

**ریسک ۱ — شکافِ transcriptionِ پاهای فعال (۶۵٪ uncovered).**
Accounting (۶ xlsx، ۰ نوت) و Mining (۱۶ PDF، ۰ نوت) و Crypto (۸ PDF، ۰ نوت) بالاترین کارت‌های ناشناخته‌اند. پاهای این پروژه‌ها بدونِ دادهٔ منتقل‌شده نمی‌توانند quote/draft/reason معنادار تولید کنند.
*⏳ verdict مالک:* آیا ingestion اولویت‌بندی شود؟ ترتیبِ پیشنهادی: Crypto PDFs (امن) → Mining strategy PDFs → Accounting xlsx (فقط محلی).

**ریسک ۲ — Track B هرگز روی ledger زنده نرفته (۰ MONEY_ATTRIBUTION).**
`reconcile/` فقط README دارد؛ ledger ۰ رویدادِ پول. حلقهٔ paper-dollar در تست سبز است (`test_leg.py`, `test_attribution.py`) ولی **هیچ لیدِ واقعی‌ای از intake تا CONFIRMED نرفته**. این یعنی سیستم قابلیت را دارد ولی فعلاً خالی است.
*⏳ verdict مالک:* آیا اولین لیدِ واقعی (حتی paper) از `/lead` ثبت شود تا مسیر زنده شود؟

**ریسک ۳ — drift از `.claude/worktrees/*` (۷ worktree کهنه).**
worktreeها snapshot کاملِ vault از session‌های قبلی‌اند. اگر ویرایش در worktree رخ داده باشد و main رها شده، canonical می‌تواند drift کند. فعلاً دادهٔ raw منحصر به worktree نیست، ولی کد و نوت می‌تواند متفاوت باشد.
*⏳ verdict مالک:* آیا worktreeهای کهنه پاک شوند (پس از بررسی)؟ پیشنهاد: `git worktree list` → prune.

### ⚑ برای معمار (Claude)
1. **regex-noise در DANGLING:** ~۹۰۰ از ۱۰۴۰ dangling، artifactsِ pathcite روی رشته‌های عددی‌اند (مثل `0.15/0.60`). ابزارِ audit باید pathcite را محدود به مسیرهای با حداقل ۲ کامپوننت + حرفِ ابتدا کند. این نویز است نه dangling واقعی.
2. **تصمیمِ transcription با LLM یا دستی:** برای PDFs غیر-PII می‌توان از LLM استفاده کرد؛ ولی برای Accounting xlsx (PII) باید ابزارِ محلی (pandas/openpyxl داخل-سیستم) استفاده شود. معماریِ ingestion باید این تفکیک را داشته باشد.
3. **08-Assets/Photos (۶۲۵ orphan):** این‌ها عمدتاً عکس‌های مرجع/پروفایل‌اند. آیا cataloging لازم است یا skip؟ اولویتِ پایین.
4. **`_ops/legs/` بدون README:** کدِ Phase 4 docstring دارد ولی نوتِ سطحِ پوشه نه. وقتی پاها واقعاً spawn شوند، یک `legs/README.md` ارزش دارد.

---

## منابعِ audit (refresh شدند در `07 - Knowledge/_audit/`)
این گزارش، `MASTER_REPORT` و `INVENTORY` موجود را extend می‌کند (نسخهٔ ۲۰۲۶-۰۷-۰۸). فایل‌های audit قبلی (۵ جولای) refresh شدند تا شکافِ transcription را منعکس کنند.

*پایان. read-only. هیچ فایلِ منبعی دست‌نخورده. commit با مالک.*
