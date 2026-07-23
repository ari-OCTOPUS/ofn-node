# PHASE-0-RISK-REGISTER

| # | ریسک | شدت | وضعیت | کاهش |
|---|---|---|---|---|
| R1 | مسیرهای LIVE-EFFECT (PS_WRITEBACK/APPLY_MERGE/MISSION_RUNNER…) در حین جراحی armed هستند | 🔴 بالا | باز | `PHASE-0-OWNER-APPROVAL-PACKET.md` — disarm موقت (owner action) |
| R2 | BLOCKER-2 ناقص: approval بدون effect_id هنوز money را batch-release می‌کند | 🔴 بالا | باز | فیکس کامل = ستون `proposal_id` (بخش C)؛ فعلاً dormant (بدونِ producerِ money-effect زنده) |
| R3 | فایل arming (`OCTOPUS-flags.cmd`) gitignored → در هیچ git-restore نیست | 🟠 متوسط | کاهش‌یافته | حالا در safety backup + manifest ثبت شد؛ owner باید backup رسمیِ خارج‌از‌git بسازد |
| R4 | global halt فقط جزئی اثبات شده؛ `outbound_worker`=0 halt-ref، `cortex`/`mission_runner` audit‌نشده | 🔴 بالا | باز | تکمیل `GLOBAL-HALT-MATRIX.csv` + integration test (بخش D/F) |
| R5 | full suite (۲۵۱ تست) اجرا نشد چون `opslib.ORG_ROOT` پیش‌فرض = live | 🟠 متوسط | باز | isolated test launcher (بخش F) که ORG_ROOT/network/providers را sandbox کند |
| R6 | تست‌ها ایزوله نیستند (مسیرهای hardcoded، آلودگیِ vault در گذشته) | 🟠 متوسط | باز | همان launcher + sentinel/mtime قبل و بعد |
| R7 | fail-closed کردنِ guard: اگر ماژول guard بشکند، approvalهای مشروع هم downgrade می‌شوند | 🟡 پایین | پذیرفته‌شده | جهتِ امن؛ alert بلند؛ guard reliability باید monitored شود |
| R8 | split-brain STOP در `.ps1`/launcherها هنوز اثبات‌نشده (فقط watchdog.py اصلاح شد) | 🟠 متوسط | باز | ماتریس halt + تستِ تطبیقِ مسیرِ STOP هر supervisor |
| R9 | انتقالِ زودهنگامِ propagation-lab هم‌زمان با جراحی safety | 🟡 پایین | کنترل‌شده | عمداً به بعد از Phase 0 موکول شد (بخش H) |

## بالاترین اولویت‌ها برای نشست بعد
1. **C** — فیکس کاملِ BLOCKER-2 (proposal_id schema + migration روی fixture).
2. **F** — isolated test launcher + اجرای کل ۲۵۱ تست در sandbox (گیتِ خروج).
3. **D** — تکمیلِ global halt matrix + integration test زیر HALT-ALL.
