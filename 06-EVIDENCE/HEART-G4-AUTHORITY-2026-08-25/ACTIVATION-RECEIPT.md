---
type: activation-receipt
schema: octopus-heart-v2-activation-receipt/1
status: GATE1_ACTIVATED_LIVE_VERIFIED
activated: 2026-08-25
owner_directive: "همرو بیار به دنیای واقعی؛ ادامه بده تا اخر؛ سوالم داشتی بپرس"
---

# رسید فعال‌سازی Gate 1 — Heart v2 روی درخت زنده

## ترتیب اجرا (همه مستند و قابل بازگشت)

1. **دابل‌چک پیش از فعال‌سازی** (همه سبز):
   - G4 زنده: `authority_policy=pulse-authority-g4.v1`، رأی control_law `SHADOW_ONLY/eligible_for_live=false`،
     `authority_hold_applied=true`، floor=96.44s، `HELD_NO_ACCELERATION`.
   - **کادنسی واقعی حلقه سنجیده شد**: جدول `heartbeat` (نخ pacemaker، CHRONO_PERIOD_S=60) ≠ خواب حلقه‌ی اصلی
     (94.44s بعد از bias). رکوردهای arbiter هر ~2 دقیقه با delta=2 beat — یعنی حلقه‌ی اصلی دوره‌ی 96.44s
     را واقعاً خوابیده و G4 مؤثر است؛ 60 ثانیه فقط کادنس pacemaker قدیمی (DOC-B §9) بود. هیچ ناهنجاری.
   - ژنوم: `verify=OK`، tip 14667=14667 (بعد از ۶+ append همچنان پایدار).
   - تساوی هش ۱۰/۱۰ فایل Gate 1 بین live و worktree.
   - تست‌ها: heart_v2 19/19، authority 27/27، pulse_arbiter و wire_readiness OK.
   - پیش‌شرط‌ها: بدون STOP/HALT فعال، organism زنده، chrono.db بدون جدول heart_*، user_version=4.

2. **فعال‌سازی**:
   - `_ops/ACTIVATION-HEART-V2.flag` ساخته شد (متن رأی مالک + تاریخ).
   - ردیف رجیستری در `ACTIVATION-FLAGS.md` (RAISED؛ خواننده `heart/runtime.py::FLAG_FILE`).
   - **اصلاح کهنگی هم‌زمان**: ردیف `ACTIVATION-RAW-SHELL.flag` از RAISED → CLOSED
     (مطابق CARD-A-DISARM-2026-08-19؛ فایل از 08-19 با پسوند `.disarmed-20260819-104530` آرشیو شده بود
     و رجیستری عقب مانده بود — تست audit از 6/9 به 9/9 سبز شد).
   - چرخه‌ی RESTART-REQUESTED استاندارد (launcher فقط همان مارکر را پاک کرد؛ STOP مالک هرگز لمس نشد).

3. **دو باگ یکپارچه‌سازی پیدا و رفع شد** (توسط تست‌های hermetic گرفته نشده بودند چون organism.py
   به‌صورت edit مستقیم سیم‌کشی شده بود — درس: integration باید با یک تست زنده/بوت واقعی تأیید شود):
   - **BUG-1**: بلوک قلب v2 در organism.py `pulse["heart_v2"] = ...` را قبل از تعریفِ `pulse` (~خط 598)
     می‌نوشت → هر تیک NameError(pulse) → projection هرگز نوشته نمی‌شد (alert «heart-v2 tick error»).
     رفع: متغیر موقت `_hv2_proj_block` + ادغام بعد از تعریف pulse.
   - **BUG-2**: `_cstat` در بلوک قلب v2 (~خط 536) قبل از تعریفش (~خط 593) خوانده می‌شد →
     اولین تیکِ هر بوت NameError(_cstat) (یک beat از دست می‌رفت + alert).
     رفع: مقداردهی `_cstat = None` در ابتدای حلقه (همان الگوی `_heart_status`/`_arb_status`).
   - هر دو رفع روی **live و worktree** اعمال و `py_compile` تأیید شد.

4. **تأیید زنده (بوت 13:06:51، PID 20788 — کد کامل)**:
   - صفر alert «heart-v2 tick error» بعد از بوت (BUG-2 رفع شد).
   - `state/pulse/heart-v2-latest.json`: schema heart-v2/1؛ FSM: GENESIS(0)→BOOTING→WARMUP→**RUNNING**؛
     green_streak رشد کرد (2→7 در ۱۰ beat اول).
   - Projection در `ORGANISM-STATE.pulse.heart_v2` (beat/mode/streak/period_advisory/brain_stats/store_counts).
   - chrono.db: جداول heart_run (۳ run)، heart_beat (۰..۱۱+)، heart_event، heart_outbox، heart_anchor،
     heart_schema_meta؛ **user_version=4 دست‌نخورده**؛ genesis = import واقعی (نه جعل تاریخ).
   - مغز مشاور: بیداری beat 1 با مدل محلی qwen2.5:1.5b → `status=OK` (advisory ثبت شد)؛ beat 3 یک
     DEGRADED (خروجی غیر-JSON — fail-soft درست). proposals همیشه `executable=false`؛ هیچ ACT ثبت نشد.
   - دوره‌ی advisory 96.44s = همان anchor G4 → **بدون تسریع**؛ نبض زنده همچنان pulse_arbiter با G4.

5. **مشاهده‌ی غیرمرتبط با قلب v2** (بدهی از قبل): یک انتظار ~۹۰-۱۰۰ ثانیه‌ای برای قفل SQLite
   `state/memory/memory.db` در مسیر work_pump→web_research→ingest (قفل توسط فرایند دیگر — احتمالاً cortex —
   نگه داشته شده بود؛ خودبه‌خود آزاد شد؛ حلقه ادامه یافت). مکانیزم از قبل موجود بود (wire_heart_work=true
   پیش از Gate 1)؛ ربطی به قلب v2 ندارد؛ برای پیگیری جدا ثبت شد.

6. **رفع نشت hermeticity تست**: `t_continuity_backup_drill_and_projection` در test_heart_v2 به
   `_memory/OCTOPUS/NOW.md` + AUTOBIOGRAPHY **واقعی** نوشته بود (MEM_DIR هاردکد به vault؛ آلودگی 12:30).
   رفع: در تست `hc.MEM_DIR` به sandbox منتقل شد (هر دو نسخه)؛ 19/19 همچنان PASS؛ فایل جعلی
   AUTOBIOGRAPHY/2026/2026-08-25.md حذف شد. NOW.md واقعی توسط HEAL زنده در beat 15 بازنویسی می‌شود.

## وضعیت نهایی

- **Gate 1 زنده و کار می‌کند**؛ نبض زنده تغییری نکرده (period همچنان از pulse_arbiter+G4).
- بازگشت (rollback): حذف فلگ + ری‌استارت (کد inert می‌شود؛ هیچ migration معکوس لازم نیست) —
  جزئیات در HANDOFF.md.
- هیچ commit/push نشده؛ هیچ گیت پولی/identity باز نشده؛ هیچ STOP مالک لمس نشده.
