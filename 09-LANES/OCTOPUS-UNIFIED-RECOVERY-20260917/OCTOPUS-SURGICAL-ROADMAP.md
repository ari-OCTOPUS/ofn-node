# OCTOPUS-SURGICAL-ROADMAP — فقط پیشنهاد (PROPOSED_ONLY) · هیچ‌یک اجرا نشد
# lane: OCTOPUS-UNIFIED-RECOVERY-20260917 · ترتیب پیش‌فرض: safety → canonical clarity → CRM → funnel → hygiene → cognition → runtime فقط پس از GO
# کلاس‌ها: S0 اطلاعاتی · S1 سند/رجیستری افزایشی · S2 آزمایش آفلاین ایزوله · S3 پچ کم‌ریسک برگشت‌پذیر · S4 سیم‌کشی/deploy · S5 فقط-مالک/اثر بیرونی

---

## SURG-01 · سیم‌کشی پوشش HALT (OD-4) — کلاس S4 · P0
- مشکل: ۳ مصرف‌کنندهٔ اثرگذار (تلگرام/ask/brain) مسیرWIRED ولی پوشش DOC_ONLY؛ mismatch=4.
- شاهد: PRE receipt (e150099) + doctor 51 تست؛ فایل‌ها: `ofn/node.py` · `ofn/adapters/router.py` · `ofn/run.py` · `ofn/assistant_update.py`؛ oracle همیشه `opslib.master_halted()`.
- بدنه: ofn-node. ریسک: تغییر رفتار ارسال/فراخوان مغز. blast-radius: مسیرهای outbound.
- پیش‌شرط‌ها: رأی مالک (کارت DC-02)؛ POST با همان دستور PRE؛ BASELINE_MOVED ⇒ توقف.
- rollback: revert ۴ فایل (فقط این ۴). اعتبارسنجی: POST receipt ماشین‌خوان + شاهد مستقل برای deploy (Class B).
- review مستقل: بله (Elahe-z یا aram-ui طبق CODEOWNERS). اثر بیرونی: ممکن (مسیر تلگرام) ⇒ پشت گیت.

## SURG-02 · یکسان‌سازی مستند kill-switch (HALT vs HALT-ALL) — S1 · P0
- مشکل: AGENTS.md والت می‌گوید `F:\ofn-node\HALT`؛ کد main می‌خواند `HALT-ALL`.
- اقدام پیشنهادی: sidecar + به‌روزرسانی رجیستری/ایندکس (بدون دست‌زدن به AGENTS.md تاریخ خود repo بدون رأی). ریسک: صفر (سند).
- rollback: حذف sidecar. اعتبارسنجی: grep یک مسیر واحد در همهٔ مستندات زنده.

## SURG-03 · هم‌ترازسازی سه بدنهٔ سورس (GitHub main / F:\ofn-node / 138) — S4 · P0
- مشکل: سه HEAD واگرا (dba9971 / 0da921b+dirty / 63938eb+dirty)؛ «کدام سورس اجرا می‌شود» مبهم.
- اقدام پیشنهادی (پس از رأی): diff فقط‌خواندن 63938eb↔dba9971 → فهرست یافته‌ها → تصمیم مالک برای push orderly یا انجماد. **هیچ force/push بدون رأی.**
- rollback: n/a (فاز اول فقط‌خواندن). اعتبارسنجی: manifest محتوایی مثل OD-4 baseline.

## SURG-04 · چرخش توکن تلگرام — S5 · P0
- مشکل: ۲ alert باز telegram_bot_token (validity unknown). مالک گفته «بعداً».
- اقدام: فقط با کارت مالک (DC-04)؛ جایگزینی در secret store + ابطال قدیمی + رسید. اثر بیرونی: بله (ربات ممکن است لحظه‌ای قطع شود).
- rollback: توکن قبلی تا ابطال معتبر می‌ماند.

## SURG-05 · اتصال CRM: merge #261 سپس PR نویسنده — S3/S4 · P1
- مشکل: جدول بدون writer (#261) و writer بدون جدول (#248)؛ PR اتصال غایب.
- اقدام: (۱) merge #261 (سبز، فقط گیت review) پس از رأی؛ (۲) PR سوم که `log_outcome` را به `call_log` وصل کند با migration تست‌شده. ریسک: دو منبع حقیقت موقت.
- rollback: revert merge (linear history اجازه می‌دهد). review مستقل: بله.

## SURG-06 · گسترش حفاظت شاخه‌ها — S5 (ruleset edit) · P1
- مشکل: ruleset فقط main؛ ۱۵۷ شاخهٔ unmerged بدون حفاظت (force-push/delete بی‌مانع).
- اقدام پیشنهادی: افزودن `refs/heads/landing/*` و `refs/heads/release/*` و `refs/heads/rescue/*` به protect-main (فقط deletion+non_fast_forward). فقط با رأی مالک (DC-08).
- rollback: ویرایش ruleset معکوس. اثر بیرونی: روی گردش کار ایجنت‌ها.

## SURG-07 · نقش‌دهی 01-TRUTH و پذیرش ایندکس — S1 · P1
- مشکل: ۱۲ نسخهٔ CURRENT-TRUTH؛ نقش 01-TRUTH نامعلوم.
- اقدام: sidecar `status: unknown→(رأی مالک)` + پذیرش CURRENT-TRUTH-INDEX.md ساخته‌شده در wave-1. ریسک: صفر.

## SURG-08 · تمرین گیت‌های G1/G2 مهاجرت — S2 · P1
- مشکل: snapshot/manifest verify هنوز تمرین نشده.
- اقدام: روی یک کپی کوچک (نمونهٔ ۵۰ فایلی) در فضای کاری، نه والت: verify مانیفست + restore drill + link-rewrite dry-run؛ خروجی = گزارش تمرین برای باز کردن G1/G2/G5/G6.
- rollback: n/a (آزمایش ایزوله).

## SURG-09 · بهداشت langar — S3 · P2
- مشکل: `.fuse_hidden…` tracked؛ `_verify/` drift؛ P1 امضا.
- اقدام: (۱) re-measure P1 به‌صورت آزمایش آفلاین (S2)؛ (۲) آرشیو fuse_hidden به 99-ARCHIVE با pre-image؛ (۳) `_verify` فقط با رأی جداگانه (DC-09).
- rollback: git revert + بازگردانی آرشیو. review: بله.

## SURG-10 · سرنوشت workflows با نام بازنشسته — S3 · P2
- مشکل: `observation-contract.yml` و `observatory-fixture.yml` فعالند؛ مفهوم OBSERVATORY بازنشسته (R2-3).
- اقدام: بررسی مصرف‌کنندگان (آیا تست‌های فعال به آن‌ها وابسته‌اند؟ full-suite سبز است پس باید بمانند تا تصمیم)؛ پیشنهاد rename/disable فقط با رأی.
- rollback: revert workflow change. اثر بیرونی: CI فقط.

## SURG-11 · تابلوی triage فراموش‌شده‌ها — S1 · P2
- اقدام: تبدیل OCTOPUS-FORGOTTEN-ITEMS.md به صف رأی مالک (هر آیتم یک micro-card؛ نرخ ۳ کارت/هفته). ریسک: صفر.

---
**ترتیب پیشنهادی با حکم 4D:** SURG-02 (امروز، S1) → SURG-03 فاز فقط‌خواندن → SURG-01 (پشت رأی DC-02 + شاهد) → SURG-05 → SURG-06..08 → SURG-09..11.
**قانون ثابت:** هیچ جراحی S3+ بدون pre-image و rollback نوشته‌شده شروع نمی‌شود؛ هیچ S4/S5 بدون رأی مالک و (برای deploy) شاهد مستقل.
