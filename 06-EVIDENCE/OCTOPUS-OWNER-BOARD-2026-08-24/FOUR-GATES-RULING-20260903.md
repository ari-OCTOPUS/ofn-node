---
type: owner-ruling-execution-receipt
ruling: مالک 2026-09-03 ~01:20 AEST — «تموم گیت های عمدی رو بپرس و باز کن» → AskUserQuestion ۴گانه، هر ۴ پاسخ صریح
files_i_merged=none
---

# چهار گیت — رأی و اجرا

## گیت ۱ — مادهٔ ۱۰ (فریز اندام‌ها) = **باز، هر دو**
- رأی: «هر دو باز (پیشنهادی)» — Cockpit هفت‌کارته + تلگرام شیشه‌ای
- اجرا: دو لین ساخت به‌صورت PR زیر گیت GOV-V6 آغاز شد (ایجنت‌های پس‌زمینه؛ گزارش مستقل)
- PARKED-LANES به‌روز شد: دو لین از پارک خارج

## گیت ۲ — WAL = **مسلح با رسید** ✓اجرا شد
```
FILE   = /home/ari/ofn/ofn/agi2027_runtime/managed_flags.json @ board138
BEFORE = {"OCTOPUS_WIRE_LEAD_OUTBOUND_WAL":"0","set_by":"owner-disarm-armin-2026-09-02"} · sha256 edad54e7…
AFTER  = {"OCTOPUS_WIRE_LEAD_OUTBOUND_WAL":"1","set_by":"owner-ruling-4gates-2026-09-03-askuserquestion","set_at":"2026-09-02T15:10:00Z","previous_value":"0"} · sha256 234f81f8… · JSON_VALID
ROLLBACK = بازگرداندن مقدار به "0" (همان فرمان python، reversible)؛ نگاتیو قبلی در .bak موجود
سقف‌ها پابرجا: 25 send/day · AUD 50/day · per-board 0 · تأیید دو-مرحله‌ای در کد
```
## گیت ۳ — V2 = **اصلاح سنسور** ✓PR ساخته شد
- **PR #111**: MEMBER_PORTS مرده (877x) → MEMBER_UNITS واقعی (۶ سرویس همیشه‌روشن) با `systemctl is-active`؛ بدون systemctl = UNKNOWN صادقانه؛ ۴۳/۴۳ تست؛ شماتیک v3
- SYSTEM-SELF-MODEL.json بازتولید = بخشی از همین رأی، بعد از merge #111 روی بورد اجرا می‌شود (فریز REV-3 بند۴ با همین رأی برداشته شد)

## گیت ۴ — صف = **fast-lane + درافت‌های P1 + حل #71** ✓اجرا شد
- **fast-lane روشن** — ثبت تفصیلی: زیر GOV-V6 خودش، «فست» یعنی همان یک رأی معتبر (Elahe-z یا aram-ui) برای docs/tests سبز؛ تنظیمات جدیدی لازم نیست؛ معتبر از merge شدن #107
- **#82/#83/#87/#88 از درافت خارج و sync شدند** (BLOCKED در صف review)
- **#71 حل شد**: مرج main به شاخهٔ landing با حل ۴ add/add به نفع main (CODEOWNERS=حاکمیت فعلی؛ سه فایل agents=نسخه‌های tested) → head `c2e11ff`، **MERGEABLE** برای اولین بار

## وضعیت صف پس از این دور
ریویو‌خواه (هر کدام یک رأی GOV-V6): **#107 → #108 → #106 → #110 → #111 → #67 → #109 → #82 → #83 → #87 → #88 → #71 → #73 → #76 → #72** + دو PR تازهٔ لین‌های مادهٔ ۱۰ (در راه) · #65 (merge نخواسته) · ۹ درافت باقی

## اصلاحیهٔ قالب گواهی (2026-09-03 ~01:50) — درخواست اورکستراتور پذیرفته شد
```
WAL_REARM_DECISION  = AUTHORIZED (رأی گیت۲، AskUserQuestion صریح)
WAL_REARM_EXECUTION = REPORTED / UNVERIFIED-from-remote
```
اجرا توسط ایجنت با این شاهدِ زنده انجام شده (before edad54e7… → after 234f81f8…، set_by=owner-ruling-4gates-2026-09-03، set_at=2026-09-02T15:10:00Z، rollback=بازگرداندن به "0")؛ طبق قاعدهٔ addendum، تا خواندنِ مستقلِ فایل زنده توسط ناظر بیرونی، وضعیت «UNVERIFIED» ثبت می‌شود، نه «WAL=1».
فرمان راستی‌آزمایی مستقل (تک‌خط، بدون گیومه):
```
ssh board138 cat /home/ari/ofn/ofn/agi2027_runtime/managed_flags.json
```
