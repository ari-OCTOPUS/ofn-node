# ADMISSION & QUARANTINE (LIVE-2)
- گیت در کل مسیر live فعال (FLAG فقط در فرایند آزمایش) · رادار قبل از ADMITTED
- تزریق‌ها: duplicate→IDEMPOTENT_SKIP ✓ · contradiction→QUARANTINED (قبل از ADMITTED) ✓ ·
  incomplete metadata→REJECTED (fail-closed) ✓ · expired→فیلتر بازیابی + TTL ✓ · provider-fail→fail-closed ✓
- صفر write کانونی خارج از گیت · هر تصمیم رسید دارد (۵۰ رسید)
- نکته: ردیف‌های ADMITTED 482→486 — دو ردیف تزریق duplicate/anchor با TTL پیش‌فرض وارد شدند (قابل RETRACT با مالک)
