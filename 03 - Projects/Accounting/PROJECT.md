---
type: project
kind: area
project: "[[03 - Projects/Accounting/PROJECT]]"
status: active
owner: آری
risk_level: high
autonomy_level: read-only
tags: [accounting, tax, australia]
created: 2026-07-03
updated: 2026-07-29
---

# پروژه: Accounting

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه یک node در §۳ رجیستریِ اتصال است (build/test/delete پشتِ verdict).

## Mission

دفاتر audit-ready برای شرکت (Pty Ltd — D3) تا آری بتواند قراردادهای بزرگ‌تر بگیرد. **tenant #1** سیستم architect (ترتیب D-26: Accounting → Lead-نقاشی → Mining).

> ⚠️ هیچ ایجنتی مشاوره مالیاتی نمی‌دهد. همه قواعد مالیاتی/انطباقی این نوت `[Unverified — accountant to confirm]` هستند تا حسابدار رسمی تأیید کند.

## Current state (شواهد)

- ساختار: Pty Ltd ثبت‌شده یا در حال ثبت (تصمیم D3) `[Assumption — مالک تأیید کند]`
- محتوای موجود vault: فقط لاگ تلگرام (`03 - Projects/Accounting/Accounting.md`) و `README.md` — هیچ دفتر/فاکتور ساختاریافته‌ای هنوز داخل vault نیست `[Verified: ls همین پوشه]`

## رجیستر انطباق شرکت (Australian company compliance)

| فیلد | مقدار | وضعیت |
|---|---|---|
| ACN | — | `[To measure — مالک]` |
| ABN | — | `[To measure — مالک]` |
| Director ID | — | `[To measure — مالک]` |
| ASIC annual review date | — | `[To measure — مالک]` |
| Registered office | — | `[To measure — مالک]` |
| ثبت GST | وضعیت ما: — `[To measure — مالک]` · آستانه اجباری: گردش سالانه ≥ $75,000 (ثبت تا ۲۱ روز پس از عبور) | `[Verified: ato.gov.au، 2026-07]` |
| چرخه BAS | فصلی — استاندارد برای گردش < $20M؛ سررسید: ۲۸امِ ماه بعد از هر فصل | `[Verified: ato.gov.au]` · تطبیق با وضعیت ما: حسابدار |
| نرخ مالیات شرکت | ۲۵٪ اگر base rate entity (گردش تجمیعی < $50M **و** ≤۸۰٪ درآمد passive)، وگرنه ۳۰٪ — سال مالی 2025-26 | `[Verified: ato.gov.au tax-rates-2025-26]` · تشخیص BRE بودن ما: حسابدار |
| PAYG withholding | — | `[To measure — مالک]` |

**اگر بیزنس نقاشی نیرو بگیرد (هرکدام یک فیلد وضعیت):** STP فعال؟ — `[To measure]` · Superannuation guarantee: **۱۲٪** از 2025-07-01 (آخرین پله افزایش) و **از 2026-07-01 پرداخت super هر payday** به‌جای فصلی — `[Verified: ato.gov.au super-guarantee + payday-super]` · NSW workers comp (icare) — `[To measure]`

## گردش‌کار فاکتور و رسید

1. هر فاکتور/رسید → عکس/PDF به `00 - Inbox` (یا تلگرام) → ایجنت پیشنهاد دسته‌بندی می‌دهد (draft) → تأیید انسان → بایگانی در پوشه Accounting.
2. دسته‌های هزینه: مواد نقاشی، ابزار، سوخت/خودرو، بیمه، اشتراک نرم‌افزار/AI، بازاریابی، تلفن/اینترنت، حق‌الزحمه حرفه‌ای، متفرقه.
3. نگهداری سوابق: ۵ سال (ATO، از تاریخ تهیه/تکمیل تراکنش) و **۷ سال اسناد مالی شرکت** (Corporations Act 2001 s 286 — ASIC) `[Verified: ato.gov.au + asic.gov.au]`.

## Assets & resources

درآمد renovation/painting (منبع اصلی)؛ حسابدار خارجی `[To measure — انتخاب نشده]`؛ هنوز نرم‌افزار حسابداری انتخاب نشده `[To measure]`.

## Active workstreams

1. تکمیل رجیستر بالا توسط مالک. 2. انتخاب حسابدار + نرم‌افزار. 3. راه‌اندازی گردش‌کار رسیدها (پیش‌نیاز tenant شدن).

## KPIs

فاصله ثبت رسید تا دسته‌بندی (هدف <۷ روز) · BAS بدون جریمه · درصد تراکنش‌های دسته‌بندی‌شده `[To measure]`

## Agent interface

- **می‌خواند:** همین PROJECT.md، رسیدها/فاکتورهای Inbox، لاگ تلگرام Accounting.
- **می‌نویسد:** فقط draft دسته‌بندی و گزارش ماهانه — همه با برچسب `[Unverified — accountant to confirm]`.
- **verdict انسانی لازم:** هر ثبت نهایی، هر ارسال به ATO/ASIC (ایجنت هرگز lodge نمی‌کند)، هر پرداخت.
- **Security Gate:** تا باز بودن CRITICALهای [[ROTATION_CHECKLIST]] فقط read-only.

## Open blockers

- ردیف‌های `[To measure]` رجیستر — فقط مالک.
- حسابدار انتخاب نشده → هیچ قاعده مالیاتی تأییدشده نیست.

## Active Context

- **2026-07-29 (اسکنِ سطحِ تلگرام):** طبق [[../../OCTOPUS-DOCTOR/50-اسکن‌ها/TG-GROUP-SCAN-PACKAGE-2026-07-29|TG-SCAN-PACKAGE]]، accounting یکی از **تنها ۴ پا از ۱۰ تا** است که OS/مغزِ زندهٔ واقعی دارد (کنارِ lead، system، studio_pf)؛ دایجستِ تاپیکش از سلولِ `business_legs` تغذیه می‌شود. ولی کنترلش از گروه هنوز فقط pause/resume + دایجست است — هیچ فعلِ اختصاصی مثلِ قیفِ lead ندارد. یادآوریِ تنشِ ثبت‌شده: مسیرِ reconcile با رأیِ خودِ مالک **PARKED** است (`VQ-ACCT-PARK`) و `attribution.confirmed` از همان مسیر پر می‌شود — پس هدفِ ماهِ ارگانیسم («اولین درآمدِ تأییدشده») تا برداشتنِ PARK ساختاراً قابلِ رسیدن نیست.
- **2026-07-18 (جلسهٔ ۲ — دیباگ و یکپارچه‌سازی):** سه agent موازی کل سیستم رو ممیزی کردن. ۱۱ یافتهٔ واقعی + ۳ یافتهٔ کاذب (رد شدند — مهم‌ترین: «COA base accounts حذف شدن» اشتباه بود چون `coa()` merge می‌کنه نه replace). هشت فاز اجرا شد: ① **reset review-session stale** (۳۰ txn_id غایب از storeِ جدید — session از ۵۲۸ تا قدیمی موندبود؛ snapshot + حذف، دفعهٔ بعد `/review` تازه می‌سازه). ② **UX seam‌ها**: منیو button «💰 دارایی‌ها/حساب»→«📊 وضعِ من»؛ `/finance!` و `acct:finance_expert` برای نسخهٔ expert (مالک) با دکمهٔ برگشت. ③ **flag hygiene**: حذفِ `OCTOPUS_SYNTH_EVENT_DRIVEN` duplicate؛ انتقالِ `TG_CENTER_BOT_TOKEN`/`TG_CENTER_CHAT_ID` از flags.cmd به `.env` (secret در جایِ درست)؛ حذفِ `OCTOPUS_WIRE_MINING` از `.env` (فقط flags.cmd). ④ **git hygiene**: `.gitignore` اضافه شد (`*.db-wal`, `*.db-shm`, `ORGANISM-STATE.*` sidecarها، `ps-writeback-*` state)؛ `git rm --cached` برای ۴ فایلِ binary/sidecar. ⑤ **۴ تستِ regression guard**: `t_h_coa_validity` (account codeها در COA)، `t_k_content_hash_unified` (hash هماهنگ)، `t_j_simple_view_zero_jargon` + `t_k_expert_view`، `t_e_acct_sync_dispatch` + `t_f_finance_expert_command`. ⑥ **PII default**: `_EXPENSE_BY_OWNER_DEFAULT` به empty تغییر کرد (صفر PII در source)؛ اگه config غایب شه، warning لاگ می‌شه و owner به ۶۰۰۰ (متفرقه) می‌ره. ⑦ **organism restart** (PID 17792→11752) با flagهای جدید live: `wire_pocketsmith=True`، telegram poll زنده، صفر خطا. ⑧ همهٔ تست‌ها سبز.
- **2026-07-18 (سبزشدنِ واقعیِ تست‌ها روی master — کامیت `fc53252`، جلسهٔ جدا):** سه تستِ تلگرامی (finance_card/review/books) که روی master قرمز بودند با دو فیکسِ env-first ریشه‌کن شدند: `_ops/tests/harness.py` دیگر `REAL_VAULT/_ops` را جلوی sys.path نمی‌گذارد (کدِ زیرِ تست = درختِ خودِ harness؛ قبلاً تستِ worktree کدِ زندهٔ کامیت‌نشده را import می‌کرد) و `_load_lab_seed` در `approval_channel.py` حالا state_dirِ تزریقی را به‌عنوانِ کاندیدِ اول می‌بیند (T-4 فقط در worktree می‌مرد). اثبات: run_all ‏۱۹۸/۱۹۸ در درختِ زنده و worktreeِ تازه از master. UX جدید («وضعِ من»/«ثبتِ نهایی») همراهِ تست‌هایش را جلسهٔ فعال‌سازی با `3994906` کامیت کرده بود.
- **2026-07-18 (فعال‌سازیِ کامل — رأیِ مالک «درست کردن همش»):** شش فازِ هماهنگ از پلنِ full-activation اجرا شد. ① فلگ‌هایِ `_ops/OCTOPUS-flags.cmd`: `OCTOPUS_WIRE_ACCT_BEAT=1` + `ACCT_BEAT_SYNC=1` (سینکِ خودکارِ روزانه از PocketSmith، هر ~۴ ساعت، confirm-preserving) + `OCTOPUS_WIRE_PS_WRITEBACK=1` (RD-004، تنها استثنای صفر-نوشتن) + `OCTOPUS_WIRE_ACCT_REVIEW_LLM=1` (Ollama محلی qwen2.5:latest برای حدسِ desc، propose-only). ② یک sync یکباره: ۸۰۷→۸۱۴ تراکنش، reconcile GREEN، ۲۱ تأیید حفظ شد. ③ **رفعِ باگِ دو-هشِ dedup** (فاز ۵.۲): `accountant._content_hash` حالا به `txn_store._hash` delegate می‌کند (full desc، case-sensitive، ۱۶ hex) — قبلاً desc[:20] + lower + ۴۰ hex بود که باعث suppress می‌شد. ۴ تراکنشِ از‌دست‌رفته برگشت. ④ **گسترشِ COA از ۱۲ به ۳۲ حساب** در `personal/policy-profile.json#chart_of_accounts` (Inventory/Prepaid/Vehicle/Equipment/Depreciation/GST-Payable/PAYG/Super/Share-Capital/Retained-Earnings/Service-Revenue/Fuel/Insurance/Software/Marketing/Phone/Professional-Fees/Bank-Fees/Office-Supplies). ⑤ **journal_bridge.rebuild() اجرا شد** → ۱۶ پیشنهادِ ثبت از ۲۱ confirmed آمادهٔ `/books` (۵ تا skip: expense با علامتِ ورودیِ مبهم). ⑥ **رفعِ PII** در `journal_bridge.py:45`: `_EXPENSE_BY_OWNER` از hardcoded به `categorize-config.json#expense_account_by_owner` (gitignored) منتقل شد. **نکتهٔ مهم: هیچ post به `ledger_core` انجام نشد** — همه‌چیز propose-only است؛ تأییدِ نهایی با `/books` در تلگرام پشتِ رأیِ مالک.
- **2026-07-18 (بازنویسیِ UX فارسیِ «بی‌عدد و بی‌اصطلاح» — فاز ۴):** `_finance_text` → «📊 وضعِ من» (حذفِ Dr/Cr، خالصِ بانکی، ATO-NSW، سنتِ سازگار، ثروتِ خالص؛ جایگزینی با «اومد/رفت/باقی‌مانده»، «مابه‌التفاوتِ آرمین و عباس»، «عدد‌ها می‌خونن»). `_review_card` → «یکی‌دونه باهات چک می‌کنم» با header «🟢 ورودی/🔴 خروجی». `_cmd_acct_sync` → «تازه‌ها رو گرفتم». `_books_card` → «ثبتِ نهایی». نسخهٔ expert به `_finance_text_expert` منتقل شد (برای مالک/توسعه‌دهنده). تست‌های `test_review_telegram`, `test_finance_card`, `test_books_telegram` به‌روز و سبز. جزئیات: `personal/UX-SPEC-2026-07-18.md`. مرز: فقط متن و کیبورد عوض شد؛ **هیچ منطقِ حسابداری دست نخورده**.
- **2026-07-18 (منتظرِ مالک — فاز ۳):** عباس هنوز به allowlist اضافه نشده. مالک chat_idِ تلگرامِ عباس را می‌دهد → به `.env` به‌عنوانِ `TELEGRAM_ALLOWED_CHAT_IDS=<abbas_id>` ست می‌شود. مکانیزم از قبل آماده است (`_allowed_chat_ids` در `approval_channel.py:142`). همچنین `legal_name` و `abn` در `policy-profile.json` هنوز placeholder — برای گزارشِ مالیاتی لازم، ولی ledger محلی با gst_registered=true کار می‌کند.
- **2026-07-16 (write-backِ PocketSmith — رأیِ مالک «همزمان تو پاکت‌اسمیتم ذخیره شه و سینک باشه»):** اولین استثنای کنترل‌شدهٔ دکترینِ صفر-نوشتن ساخته شد — `_ops/legs/ps_writeback.py`: تأییدهای `/review` (و `apply_review`) به‌صورتِ برچسبِ `oct-مالک-…`/`oct-نوع-…` روی همان تراکنش در PocketSmith نوشته می‌شوند. فقط PUT `labels` به `/transactions/{id}`، پشتِ فلگِ خاموشِ `OCTOPUS_WIRE_PS_WRITEBACK`، مرزِ HALT محترم، قفلِ flush، سقف+مهلت، auto-backfillِ یک‌باره، لاگِ ممیزیِ gitignoreشده. verify خصمانهٔ ۵-لنزی → ۲ یافتهٔ HIGH (gitignoreِ صف/لاگ + نمایشِ 403 در کارتِ /sync) و ۴ MED همه بسته شد؛ تست ۳۲چکی سبز. جزئیات و فعال‌سازی: [[RISK-DECISIONS]] §RD-004.
- **2026-07-16 (فازِ صفرِ دفترِ واقعی):** نقدِ بیرونیِ متخصص پذیرفته شد — سیستمِ قبلی «مرور/برچسب‌زنیِ تراکنش» است نه حسابداری. رأیِ مالک: «فقط فازِ صفر». ساخته شد: `ledger_core.py` (دفترِ دوطرفهٔ متوازن، append-only، reversal، قفلِ دوره، GST fail-closed) + `raw_store.py` (شواهدِ خامِ immutable) + `recon.py` (reconciliation واقعیِ تراکنش‌به‌تراکنش — تستِ پرچم‌دار: خالصِ برابر با خطاهای متضاد **رد** می‌شود). واقعیتِ entity ثبت شد (شرکت/ABN به نامِ آرمین؛ عباس related-party). ریسک‌ها در [[RISK-DECISIONS]]؛ قالبِ policy در `personal/policy-profile.example.json`.
- **2026-07-16 (جلسهٔ حسابدارِ مولتی‌ایجنت):** حسابدارِ شبکه‌ایِ واقعی ساخته شد — PocketSmith زندهٔ read-only + CSVهای طرف‌حساب‌ها → ۵۷۶ تراکنشِ یکتا (content-hash dedup)، موتورِ سنتِ صحیح (`money.py`، نه float)، آبشارِ قاعده‌محور (transfer/wage/vendor + صفِ مرور)، reconcile **GREEN**. کد در `_ops/legs/` (money·txn_store·attributor·accountant·pocketsmith_api·txn_categorize). کارتِ `/finance` تلگرام به خلاصهٔ **PII-امنِ** شبکه وصل شد + حسابدارِ گفتگومحورِ `/review` (فعلاً pause تا فازِ صفر کامل شود). گزارشِ کامل + دادهٔ خام همه **gitignore** در پوشهٔ `personal/`.
- **2026-07-06 (جلسه ۱۷):** کد پروژه به `_code/` منتقل شد (B1 پلن NONMD-TRIAGE؛ propose→executed با verdict آری). لاگ کامل: `00 - Inbox/nonmd-move-log-2026-07-06.csv`.
- تمرکز فعلی: حسابدارِ شبکه (فعال، propose-only) — مالک استثناهای صف مرور را دونه‌دونه تأیید می‌کند تا دقت بالا رود
- ۳ قدم بعدی: (۱) مالک: ۳ موردِ بازِ گزارش را روشن کند (حقوق-عباس-به-آرمین $۷٬۱۰۰ · ۶ خروجیِ بی‌صاحب $۱۱٬۰۲۰ · تأییدِ مشتری‌ها) (۲) فعال‌سازیِ pull با فلگ در ری‌استارت (۳) گسترشِ دادهٔ طرف‌حساب‌ها تا امروز
- تصمیم‌های باز: دسته‌بندیِ ریزِ خرج (مدلِ محلی ضعیف) · چرخه BAS با حسابدار

## Progress

- چه کار می‌کند: حسابدارِ شبکه‌ایِ زنده (PocketSmith read-only → ۵۷۶ تراکنش، سنتِ صحیح، reconcile GREEN، کارتِ `/finance` PII-امن) + manifestِ انطباق
- چه مانده: تأییدِ استثناهای صف مرور (مالک)، دسته‌بندیِ ریزِ خرج، اجرای BAS با حسابدار
- مشکلات شناخته: دسته‌بندیِ ریزِ خرج با مدلِ محلیِ کوچک ضعیف است (۵۲۸ قلم در صفِ مرور)؛ reconcile با اسکرین‌شاتِ قدیمی ~$۵٬۰۰۰ فرق دارد (دورهٔ جدیدتر، درست)

## Next actions

- [ ] تکمیل رجیستر انطباق (مالک)
- [ ] انتخاب حسابدار و جلسه اول
- [ ] پایلوت گردش‌کار رسید

## نوت‌های مرتبط

- 📗 [[03 - Projects/Accounting/RAHNAMA-HESABDARI|راهنمای گام‌به‌گامِ حسابداری (برای مالک — ساده)]]
- [[03 - Projects/Accounting/RISK-DECISIONS|RISK-DECISIONS — تصمیم‌های ریسک]]
- [[03 - Projects/Accounting/Report - Accounting - Tax Map FY2025-26|Report - Tax Map FY2025-26]]
- [[03 - Projects/Accounting/Accounting|لاگ پیام‌های تلگرام — Accounting]]
- [[03 - Projects/Accounting/app/README|README]]
- [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]]

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[03 - Projects/Lead-نقاشی/Lead-نقاشی|Lead-نقاشی]]

## 🎛 کابین کنترل (two-brain)

- کابین مشترک: ارتیفکت `fleet-live-dashboard` · نقشه: [[_memory/TWO-BRAIN-CONTROL-BLUEPRINT|TWO-BRAIN]] · نقشهٔ ساخت: [[_memory/FRANKENSTEIN-BUILD-PLAN|FRANKENSTEIN-BUILD-PLAN]]
- عملیات استاندارد از کابین (intent → sendPrompt): «تست <پروژه>» = validators + چک کد + تست قرارداد · «بساز» = اسکلت از `_Templates` + ثبت همین‌جا · «آرشیو» = فقط انتقال به `_Archive`/`_Duplicates` (هرگز حذف واقعی).
- تست قرارداد این پروژه: هنوز تعریف نشده — طبق BUILD-PLAN §۲ تعریف شود.
