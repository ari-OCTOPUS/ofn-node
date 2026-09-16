---
type: decision
status: active
tags: [owner-order, wave1, telegram, verification, 2026-08-21]
created: 2026-08-21
updated: 2026-08-21
created_by: owner
project: "[[04 - Architect System/architect/PROJECT]]"
source: "pasted owner document 2026-08-21 (OWNER_ORDER: OCTOPUS-OWNER-ORDER-WAVE1-2026-08-21)"
---

# OWNER-ORDER — WAVE1_CONDITIONALLY_AUTHORIZED 2026-08-21

مالک فرمان کامل Wave 1 را با چهار مگاپرامپت صادر کرد (منبع: متنِ الصاق‌شدهٔ خودِ
مالک؛ همان جلسه، نه سایدکار). این کارت ثبتِ همان فرمان است — نه تفسیر و نه توسعه.

## حکم اصلی (خلاصهٔ وفادار)

- **قبلی:** `WAVE0_OBSERVE_ONLY` → **جدید:** `WAVE1_CONDITIONALLY_AUTHORIZED`
- **autonomy_level:** `L2_ARMED` · **evidence_required:** true · **append_only_governance:** true
- **هدهای مرجع:** implementation=`fa38d16cca944a80396ae1e1a16c547ab3122f78` · evidence=`d301339`
- **وضعیت فعلی milestone:** `IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING` — فعال‌سازی زنده فقط مرحله‌ای.
- **مجاز اکنون:** خواندن کامل مخزن/شواهد؛ شاخه/کد/تست/فیکسچر/commit؛ تعمیر حلقه‌های
  C1–C23 در معماری موجود؛ ساخت رجیستری/اسکیمه/آداپتر/صف/پل/تله‌متری/داشبورد؛
  سرویس‌های Docker محلی و وابستگی‌های fixture؛ راه‌اندازی مجدد فقط با اثبات امنیت
  ری‌استارت؛ تست‌های امنیت/ماندگاری/بازیابی/ری‌پلی/محدودیت نرخ/کرش؛ checkpoint/
  manifest/هش/گزارش/بستهٔ بازگشت؛ آزمایش‌گاه `FIXTURE_ONLY`؛ آماده‌سازی `CANARY_PROPOSED`؛
  عامل‌های موازی کشف/پیاده‌سازی/تست/حسابرسی؛ تعمیر مستندات در تعارض با پیاده‌سازیِ
  تست‌شده؛ خودبهبودی بیرون از گیت‌های TCB و مالک؛ قرنطینهٔ تحویلِ نامطمئن؛ توقف
  خودکار در شکست هر invariant یا گیت شواهد.

## شرطی‌ها

- **verification مستقل:** مجاز است؛ شرط = هویت/جلسهٔ جدا؛ هدف commit = `d301339`.
- **canary تلگرام:** فقط پس از (۱) گذر verification مستقل، (۲) تعیین هدف چتِ مالک،
  (۳) تست kill switch، (۴) تست rollback، (۵) تمرین transport جعلی، (۶) صفر یا
  کاملاً reconcile شدن صف. سقف: **۱ پیام واقعی**، **۱ گیرنده**، `OWNER_CHAT_ONLY`،
  بدون webhook، polling یا ارسال تکی صریح. گسترش = ممنوع بدون شواهد جدید.
- **ری‌استارت daemon:** فقط توسعه/فیکسچر/پروسهٔ canary ایزوله.

## نیازمند تأیید جداگانهٔ مالک

بیش از یک گیرندهٔ واقعی تلگرام؛ بیش از یک پیام canary؛ فعال‌سازی/مهاجرت webhook؛
ری‌استارت سراسری daemon؛ هر تماس پولی یا تعهد مالی؛ تغییر TCB/هویت مالک/ریشهٔ
رمزنگاری/گیت‌های ایمنی؛ حذف یا بازنویسی شواهد append-only؛ چرخش credential یا
ارتقای مجوز بیرون از Octopus؛ هر اقدام سخت‌افزاری؛ انتشار/خرید/ساخت حساب خودکار.

## هرگز مجاز

افشای اسرار؛ غیرفعال‌سازی audit/receipts/provenance/kill switch/rate limit؛
جعل verification مستقل؛ بازنویسی تاریخ برای پنهان‌کردن شکست؛ ارسال زندهٔ صامت؛
retry/خرج/گسترش گیرنده/خودتکثیری بی‌حد؛ تلقی نتیجهٔ نامطمئن به‌عنوان امن برای
ارسال مجدد؛ ادعای موفقیت بدون شواهد بازتولیدپذیر.

## محدودیت‌های ثابت

`paid_calls=0` · `live_sender_default=OFF` · `webhook_default=OFF` ·
`destructive_actions_default=OFF` · `secrets_in_logs=0` ·
`uncertain_send_policy=DLQ_UNCERTAIN_SEND_OUTCOME` · `owner_actions=A4_REQUIRE_CONFIRMATION` ·
`routine_reversible_actions=A2_AUTOMATIC_WITH_RECEIPT`

## انتقال موفقیت

`IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING` → `WAVE1_CANARY_READY` فقط اگر:
گذر verification سر-به-سر (exact-head)؛ همهٔ سویییت‌های الزامی؛ side effect اجرای
محلی صفر؛ سیم‌کشی زنده هنگام verification غیرفعال؛ هویت verifier واقعاً جدا.

## ترتیب اجرایی (به‌فرمانِ مالک)

`مگاپرامپت ۱ (verification مستقل) → PASS مستقل → مگاپرامپت ۲ (canary تک‌پیامی) → مگاپرامپت ۳ (بستن حلقه‌ها/آزمایش‌گاه) → مگاپرامپت ۴ (طرح توسعهٔ پس از canary)`

متن کامل مگاپرامپت ۱ و ابزار بازتولید: `06-EVIDENCE/OCTOPUS-INDEPENDENT-VERIFIER-KIT-2026-08-21/`
(مگاپرامپت‌های ۲–۴ نزد مالک/در متن اصلی فرمان‌اند و فقط پس از گذرِ گیت‌های قبلی فعال می‌شوند).

## یادداشت پایبندی

این فرمان freeze عمومی توسعه را برمی‌دارد ولی freezeهای امنیتی مالک/TCB/شواهد/
عملیات خارجی را حفظ می‌کند. مانع فعلی طبق شواهدِ `d301339`:
`verifier_independent=false` — همان گیتِ اولِ ترتیب اجرایی.
