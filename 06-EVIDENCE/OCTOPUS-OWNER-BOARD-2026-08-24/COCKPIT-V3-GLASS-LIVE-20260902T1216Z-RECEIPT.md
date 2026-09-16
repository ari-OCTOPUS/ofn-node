---
type: cockpit-live-verification-receipt
created: 2026-09-02T12:16:25Z (checked live by ZCode session)
artifact: OCTOPUS Cockpit v3 «شیشهٔ شفاف» glass-1.0.0-single (خروجی اورکستراتور؛ اجرا با دست مالک)
rules: may_authorize=false · may_execute=false · may_propose=true · fail-closed
---

# صحه‌گذاری زندهٔ پنل Cockpit v3 — ۱۲:۱۶Z

## فایل‌ها (واقعی و هش‌خورده)

| فایل | بایت | sha256 |
|---|---|---|
| C:\Users\Armin\Downloads\cockpit-v3\index.html | 10,146 | `e39c2cdd1b1be56667ab3ac42487bdb4ae4746ef9ed702c9cced024fc9f3f3ee` |
| C:\Users\Armin\Downloads\cockpit-v3\data\glass-snapshot.json | 5,799 | `858078c673d397b8766ed8403061c8951fdefb61b60f0b58339f21ac197a6328` (با خروجی ترمینال مالک یکی است) |

خود‌آزمون پنل: 42 assertion پاس. سرور `127.0.0.1:8899` در زمان بررسی این رسید (12:16:25Z) **پاسخ نمی‌داد** (connection refused) — احتمالاً Ctrl+C شده؛ برای دیدن پنل همان یک خط دوباره اجرا شود.

## حکم پنل راستی‌آزمایی شد

- **INCONSISTENT روی main_sha = درست.** زنده (12:16:25Z): main=`45dd913`، بورد=`3cf9fa1` (یک نسل عقب، بعد از مرج #91)، لپ‌تاپ/والت=45dd913. یافتهٔ تازهٔ مفید پنل: `board-behind-main STALE` تأیید می‌شود؛ جلوی کشیدن بورد (فقط `git pull --ff-only` طبق رویهٔ شش‌خطی مصوب مرحلهٔ ۲) منتظر یک کلمهٔ مالک است — این جلسه بدون فرمان نمی‌کشد.
- **verified_payment_count=0 سالم** روی هر چهار سطح ✓ · **SYSTEM-SELF-MODEL.json ABSENT** ✓ (دلیل فنی: --output مسیر وب را نوشت؛ producer default هرگز اجرا نشد) · **WAL execution UNVERIFIED** ✓ (فلگ "0"، re-arm هرگز اجرا نشد؛ ریزتر از پنل: فایل `.bak` با وضعت قبلی "1" موجود است، sha256 cd196260…).

## چهار اصلاح برای رفرش بعدی پنل (داده‌ای، نه حکمی)

1. **owner_queue_count=19 قدیمی است** — شمارش زنده 12:16Z = **۲۱ PR باز** (#93–#97 بعد از برداشت پنل باز شده‌اند/دیده نشده‌اند).
2. **#92 با برچسب `review_stale:true` گمراه‌کننده است** — طبق تعریف REV-3 هیچ approve انسانی قبلی روی #92 وجود نداشت که بی‌اعتبار شود؛ درست‌تر: «HEAD امشب عوض شد؛ approve باید روی 00e9b91 باشد».
3. **#76 با `merge_state:CODEOWNERS_CONFLICT` نادرست است** — زنده: mergeable=MERGEABLE، mergeState=**CLEAN** روی base=release/p0، reviewDecision خالی. تعارض add/add مربوط به فرود روی main است (مال لین صاحب)، نه merge_state شاخه.
4. **#92 وضعیت فعلی**: head=00e9b91 · review=REVIEW_REQUIRED · state=BLOCKED · mergeable=MERGEABLE (12:16Z) — approve الهه هنوز ثبت نشده.

## جمع‌بندی

پنل همان کاری را می‌کند که پلن مرحلهٔ ۷ خواسته بود: ناهم‌خوانی را با صدای بلند می‌گوید (INCONSISTENT)، unknown/absent را سبز نشان نمی‌دهد، و هیچ دکمهٔ merge/send/pay ندارد. اولین snapshot آن با واقعیت زنده هم‌خوان است جز در چهار مورد بالا که همه داده‌ای‌اند و با رفرش درست می‌شوند.
