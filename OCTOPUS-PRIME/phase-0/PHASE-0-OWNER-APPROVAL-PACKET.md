# PHASE-0-OWNER-APPROVAL-PACKET — temporary disarm during safety surgery

> این پکت فقط **پیشنهاد** است. تأیید این پیام اجازهٔ تغییر live flags، restart، send،
> paid call، PocketSmith writeback یا merge نیست. هیچ‌کدام از این‌ها را ایجنت انجام نمی‌دهد.

## چرا؟

سیستم زنده **در حین جراحیِ کدِ ایمنی** برای ۶ قابلیتِ اثرگذار-بیرونی armed است
(`FLAGS-AUTHORITY-REPORT.md`). امن‌ترین حالت این است که تا سبزشدن Phase 0، این‌ها
موقتاً disarm شوند — تا حتی یک باگ هم نتواند به پول یا apply/merge دست بزند.

## LIVE-EFFECT flags که الان armed هستند (کاندیدای disarm)

| flag | اثر | consumers |
|---|---|---:|
| `OCTOPUS_WIRE_PS_WRITEBACK` | نوشتن روی PocketSmith (مالی) | 17 |
| `OCTOPUS_WIRE_POCKETSMITH` | دسترسی PocketSmith | 22 |
| `OCTOPUS_WIRE_APPLY_MERGE` | اعمالِ merge کد | 17 |
| `OCTOPUS_WIRE_MERGE_APPLIES_KNOB` | کنترلِ merge-apply | 6 |
| `OCTOPUS_WIRE_MISSION_RUNNER` | اجرای mission | 11 |
| `OCTOPUS_WIRE_RUNNER_APPLY` | apply توسط runner | 3 |

## اگر (و فقط اگر) موافقی — کارِ تو (نه ایجنت)

۱. یک نسخهٔ backup از `_ops/OCTOPUS-flags.cmd` بگیر (خارج از git، امن).
۲. در همان فایل، این ۶ خط را از `=1` به `=0` تغییر بده.
۳. سیستم را طبق روال خودت restart کن (اگر لازم است).
۴. بعد از سبزشدن Phase 0، طبق تصمیم خودت دوباره arm کن.

## اثرِ عدمِ disarm

Phase 0 همچنان روی worktree ایزوله پیش می‌رود و live دست‌نمی‌خورد؛ ولی هر جراحیِ
بعدی که سرانجام merge شود، روی سیستمی می‌نشیند که مسیرهای مالی/apply آن زنده‌اند —
پس ریسکِ باقیمانده بالاتر است. توصیه: disarm در طولِ کار.
