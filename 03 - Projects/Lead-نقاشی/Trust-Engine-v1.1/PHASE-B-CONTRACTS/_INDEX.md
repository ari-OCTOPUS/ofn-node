---
type: reference
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
status: idea
tags: [painting, lead, trust-engine, phase-b, index]
created: 2026-07-21
updated: 2026-07-21
---

# فاز B — قراردادها و معماریِ Trust Engine P0 (ایندکس)

خروجیِ **فاز B** مأموریتِ `OPUS_MISSION_PROMPT.md` (فاز A از قبل در `../RUNTIME-TRUTH-RECONCILE-2026-07-21.md`
انجام شده بود). ساخته‌شده با فن‌اوتِ چندایجنته + راستی‌آزماییِ متخاصمِ مستقل. **propose-only — صفر تغییرِ
کد/فلگ/برنچ در ارگانیسم تا رأیِ مالک.** درختِ کانونیِ مرجع: هنگامِ ساخت `wave1/staging`؛ اکنون در master.

## بخوان به این ترتیب
1. **`00_VERIFICATION_AND_FIXES.md`** — سندِ حاکم: نتیجهٔ راستی‌آزمایی، ۲ یافتهٔ blocking (اصلاح‌شده)، اصلاحاتِ فاز C، تصمیمِ ماژول‌ها، سوالاتِ مالک.
2. **`02_CANONICAL_LEAD_CONTRACT.json`** — اسکیمای draft-07 قراردادِ Lead Candidate v1.1؛ firewallِ رضایت ساختاراً در همین‌جا قفل است (پروب‌شده).
3. **`03_EVENT_CONTRACT.json`** — envelope رویداد + enumِ کاملِ نوعِ رویدادها (append-only).
4. **`04_PROPOSAL_CONTRACT.json`** — قراردادِ آبجکتِ proposal که Router می‌راند (سازگار با قوسِ موجود).
5. **`05_CONSENT_STATE_MACHINE.md`** — ماشینِ حالتِ رضایت/انطباق؛ گاردها، fail-closed، suppression، اسکیلیشن، NSW licence.
6. **`06_FUNNEL_STATE_MACHINE.md`** — قیفِ بازار received→…→paid؛ نگاشت به سنجشِ موجود. (اصلاحِ B1 inline)
7. **`07_SECURITY_THREAT_MODEL.md`** — STRIDE کلِ مسیر P0 + نگاشتِ تهدید↔تستِ الزامی.
8. **`07a_API_BOUNDARY_DESIGN.md`** — طراحیِ `POST /api/v1/lead-candidates`: HMAC/nonce/idempotency/quarantine + failure/retry + اثباتِ سلبیِ n8n. (اصلاحِ B2 inline)
9. **`09a_MIGRATION_AND_OWNERSHIP.md`** — همگراییِ دو inbox + نقشهٔ مالکیت + فهرستِ freeze/delete.

## هنوز نوشته‌نشده (کارِ فاز B/C که اگر مالک بخواهد ادامه می‌یابد)
- `01_P0_ARCHITECTURE.md` (دیاگرامِ کلان — عناصرش در 07a/09a پراکنده است)
- `08_TEST_AND_ACCEPTANCE_PLAN.md` (۱۷ تستِ الزامی در 00/07 نگاشت شده؛ سندِ مستقلش نه)
- `09_IMPLEMENTATION_SEQUENCE.md` / `10_OWNER_DECISIONS_REQUIRED.md` (توالی در 09a §1.4؛ تصمیم‌ها در 00 تجمیع شده)

## ناوردی‌های رعایت‌شده
STOP-ORGANISM لمس نشد · صفر فلگ روشن · صفر restart · صفر ارسالِ بیرونی · همه‌چیز پشتِ فلگِ پیش‌فرض-خاموش ·
کارِ کد در worktree ایزوله · هر ادعا به file:line در کانونی پین.
