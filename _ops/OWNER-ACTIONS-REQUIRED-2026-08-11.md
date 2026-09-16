# OWNER ACTIONS REQUIRED — 2026-08-11

> این فایل فقط برای مالک است. این کارها **توسط کد قابل انجام نیست** — به داده یا
> تصمیمِ انسان نیاز دارند. کد آماده است؛ این سه در ورودی مونده‌اند.

## ۱. آدرس لید ۶۶۷۹۵۱ (۲۲۳ ساعت مسدود)

لید «Remedial render and paint of common property walls» منتظرِ suburb/آدرس است.

**دستور مالک:** در تلگرام به اختاپوس ریپلای کن و آدرس (یا حداقل suburb) را بده.
اگر پروژه لغو شده، لید را ببند.

## ۲. CSV واریزی‌ها در `_ops/reconcile`

بدون این فایل، `attribution.claimed` برای همیشه صفر می‌ماند — حتی اگر لید claims شود.

**دستور مالک:** فایل CSV واریزی‌ها (settlement/export از eToro یا منبع مالی) را در
`_ops/reconcile/` بگذار. نام فایل مهم نیست؛ `attribution.match()` آن را پیدا می‌کند.

## ۳. مسلح‌کردن `OCTOPUS_FUGU_TIMEOUT_NOT_PROVIDER_FAIL`

لاگ نشان می‌دهد `TimeoutError` تکرار می‌شود و ارگانیسم هر بار می‌میرد (۲۹۲/۵۷۵/۳۰۱
دقیقه سکوت). علت: timeoutِ محلیِ سوکت به‌اشتباه شکستِ فروشنده شمرده می‌شود و
`STOP-FUGU` می‌سازد.

این فلگ timeout محلی را از kill-switch جدا می‌کند — بدون اینکه خطای واقعیِ فروشنده
را ignores کند.

**دستور مالک (در `OCTOPUS-flags.cmd`):**

```cmd
set OCTOPUS_FUGU_TIMEOUT_NOT_PROVIDER_FAIL=1
```

سپس restart.

**تست:** `test_paid_timeout_chain.py` (۶۰/۶۰ سبز) دقیقاً این رفتار را قفل می‌کند —
timeout محلی consecutive_timeouts را بالا می‌برد ولی STOP نمی‌نویسد؛ خطای واقعیِ
فروشنده (HTTPError 500) هنوز STOP می‌زند.

---

## آنچه کد انجام داد (در این worktree، آماده برای commit)

- پیامِ ردِ tool-request حالا صریح می‌گوید چه میدانی کوتاه است و «نمی‌دانم» قبول نیست
- `GOALS-OCTOPUS.md` حالا صادقانه می‌گوید هدف چرا مسدود است
- Test Intelligence pack کامل ساخته شد (۵۸۸/۵۸۸ سبز، صفر skip)
