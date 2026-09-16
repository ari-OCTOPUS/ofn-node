---
title: OWNER DIRECTIVE 2026-09-17B — PR#71 + بازبینی مستقل + ۴ ممیزی + روز فانل (اجرا و ثبت)
updated: 2026-09-17T07:20:00Z
tags: [octopus, owner-decisions, pr-71, audit, funnel, integrity-incident]
status: EXECUTED
---

# اجرای رأی چهاربخشی مالک — ۲۰۲۶-۰۹-۱۷ (ب)

**پیش‌شرط:** توکن‌های لو‌رفته توسط مالک revoke شدند → **CLOSED، دیگر گزارش/پیگیری نمی‌شود.**

## ۱) PR #71 — rebase تمیز، تعارض‌ها رفع، **هیچ merge**

- شاخه: `landing/release-p0-20260902` روی `main` @ `dba9971` بازپخش شد → head **`ba1464d`** (۹ کامیت؛ merge-commit و یک کامیت تکراری حذف).
- **وضعیت PR: `MERGEABLE`** (بود `CONFLICTING/DIRTY`). `mergeStateStatus=BLOCKED` و `reviewDecision=REVIEW_REQUIRED` — یعنی منتظر **شرط خود مالک** (Blocker resolved by owner / Independent review). هیچ merge انجام نشد.
- تعارض‌ها با شواهد حل شدند (فایل کامل: کامنت PR + جدول داخل آن). خلاصهٔ منطق:
  - `lead_outbound_transport.py` → main (نسخهٔ شاخه پیش از containment مالک روی `OCTOPUS_WIRE_LEAD_OUTBOUND_WAL→0` است؛ رخداد ۶ در `docs/octopus-os/07-INCIDENTS.md`).
  - `outbound_worker.py` → main (گیت OWNER_ABSENT/Conservation).
  - `quote_pipeline.py` → main (default امن `dry=True`).
  - `quote_engine.py` → main (PR #110A عمداً مسیر ارسال و `book_wins` را برداشته؛ در docstring ماژول تصریح شده).
  - `CODEOWNERS` → main (رأی جدیدتر GOV-V6).
  - `.gitignore` → اجتماع؛ `painting_source_registry.json` → ادغام (منبع یکتای `nsw_ocp_registry` اضافه شد).
  - `independent-review-gate.yml` → main + حذف کامیت تکراری (خط `ofn/agents/` تکراری بود؛ main از قبل دارد) — این هم‌زمان قید `workflow`-scope توکن را دور زد.
- **تست‌های محلی روی head:** ۹۶۸۱ pass / ۱۴ fail / ۲۸ skip.
  - ۶ شکست **پیش-موجود روی main خالص** (در worktree دوم تأیید شد).
  - ۸ شکست در فایل‌های تستی که **خود شاخه اضافه کرده** (`test_hf.py`×۵، `test_teeth.py`×۳) و مسیر ارسالِ پارک‌شدهٔ 110A را می‌سنجند → **نیازمند کارت تصمیم مالک** (حذف/PORT به 110B/رهاکردن قرمز).
- **push:** با force-with-lease انجام شد (پس از حذف تغییر workflow، که توکن فاقد scope آن بود). SSH key محلی روی گیت‌هاب ثبت نیست و توکن `workflow` ندارد — ثبت شد.

## ۲) درخواست بازبینی مستقل — ثبت شد (OPEN)

- reviewer انسانی: **@Elahe-z** اضافه شد (به‌همراه `aram-ui` که از قبل بود).
- کامنت PR #71 ثبت شد: <https://github.com/ari-OCTOPUS/ofn-node/pull/71#issuecomment-5704562796> با یادآوری صریح **INTEGRITY_INCIDENT #51** («ruleset lowered to self-merge PR #46 — gate bypass, I5»).
- ایجنت **خودش تأیید نمی‌کند**؛ منتظر پاسخ انسانی.

## ۳) چهار PR ممیزی — همه از قبل MERGED (۱/۱ سبز: Cursor Bugbot)

خلاصهٔ یک‌خطی یافته + ریسک هر کدام در پیام نهایی به مالک ارائه شد (طبق دستور: فقط آماده‌سازی، بدون تأیید).

## ۴) روز فانل — اجرا شد

**دو نقص کشف و رفع شد (هر دو با pre-image):**

1. **۳۲ ایمیل زندانی در فیلد متنی `contact_channel`** (مثل `info@absolutestrata.com.au`) هیچ‌وقت به لجر ارسال‌شدنی نمی‌رسیدند، چون انریچر هر حسابِ حاوی «@» را «قبلاً ایمیل‌دار» رد می‌کرد. → ابزار جدید `lead_email_extract.py` نوشته و اجرا شد: **+۳۲ ایمیل**.
2. **cursor انریچر از طول لیست گذشته بود** (۳۳ > ۲۹) → هر چرخه بی‌صدا `attempted:0`. → پچ تک‌هانکی با pre-image (`lead_enrich.py.pre-cursor-fix-20260917`) + ۴ چرخه اجرا: ۲۷ سایت وارسی شد، **+۲ ایمیل**.

**نتیجه:** لجر ارسال از **۳۴ → ۶۸** ایمیل (از ۹۷ لید). ۲۹ لید بدون ایمیل قابل‌یافت (تلفنی).

**رسید روزانهٔ تقاضا:** `season-meter.json` بازتولید شد (بود ۱۸:۰۰Z با عدد کهنه):

| فیلد | قبل | بعد |
|---|---|---|
| emails_known | 34 | **68** |
| staged_packets | 79 | 83 |
| leads_total | 97 | 97 |
| sent_today / sent_total | 11 / 3 | 11 / 3 |
| replies_detected | 1 | 1 |
| verified_cash | 0.0 | 0.0 |

کادنس رسید: تایمر `octopus-revenue-drive.timer` هر ۶ ساعت (۴× در روز > الزام روزانهٔ ORDER-LAW).

## بازها / نیازمند مالک

1. **تصمیم تست‌های 110A** (۸ شکست فایل‌های تستی خود شاخه): حذف / port / رها.
2. چهار خلاصهٔ ممیزی (بخش ۳) برای تأیید.
3. ارجاع SSH/توکن: برای pushهای آیندهٔ حاوی فایل workflow، مالک باید `gh auth refresh -s workflow` بزند یا کلید SSH را ثبت کند.
