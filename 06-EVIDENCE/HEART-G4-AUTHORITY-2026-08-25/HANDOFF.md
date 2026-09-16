---
type: handoff
schema: octopus-heart-session-handoff/1
session: 2026-08-24/25 (zcode)
status: G4_LIVE_VERIFIED · GATE1_CODE_LIVE_TESTED_NOT_ACTIVATED · SAFE_HANDOFF
created: 2026-08-25
audience: next agent (read fully before any restart or activation)
owner_directive_chain:
  - "قلب موجود را دقیق بسازیم؛ قراره زنده بشه؛ همه‌چیز داخل خود ابسیدین ذخیره بشه"
  - "دیگه متوقف نشو؛ همرو بیار به دنیای واقعی؛ اختاپوس کامل روی لپ‌تاپ کار کنه"
  - "همه چیو یادداشت کن ایجنت بعدی بفهمه؛ بعدش متوقف شو"
---

# HANDOFF — Heart v2: G4 زنده + Gate 1 آمادهٔ فعال‌سازی

## وضعیت همین الان (خلاصهٔ ۳۰ ثانیه‌ای)

1. **G4 (سلب اختیار رأی shadow) زنده است و کار می‌کند** — از ری‌استارت 11:44 امروز،
   arbiter با `authority_policy=pulse-authority-g4.v1`، رأی control_law فقط
   observable (`SHADOW_ONLY`)، anchor ثابت مانع تسریع. تأیید ۲ beat (49093/49095).
2. **Gate 1 (Heart v2 کامل) روی درخت زنده کپی شده و ۱۹/۱۹ تست hermetic سبز است،
   ولی هنوز فعّال نشده** — فعلاً بی‌اثر (inert) است تا فلگ ساخته و ری‌استارت شود.
3. **پروسهٔ organism فعلی** همان بوت 11:44 است (کد G4؛ بدون Heart v2). سالم می‌تپد.
4. **هیچ چیزی گم نشده**: همهٔ evidence در `06-EVIDENCE/HEART-G4-AUTHORITY-2026-08-25/`
   داخل خود vault است + contradiction ثبت‌شده (C-054) + مانیتور tip.

## کارهای انجام‌شده این نشست (به ترتیب)

### الف) G4 — بستن نشت اختیار رأی shadow در نبض زنده

- **مشکل**: رأی `control_law` از `heart-shadow-latest.json` (که خودش
  `production_wire.open=false` داشت) وارد اجماع زندهٔ arbiter می‌شد و نبض ~96s را
  می‌راند — یعنی عددِ تولیدکننده‌اش آن را غیرمعتبر اعلام کرده بود ولی داور آن را
  می‌پذیرفت.
- **رفع**: `pulse_arbiter.py` — رأی همچنان observable (با `observed_period_s` و
  دلایل) ولی `eligible_for_live=false`؛ `arbitrate()` fail-closed روی نبودِ authority؛
  **anchor ثابتِ pre-G4** (اولین beat مقدار زندهٔ قبل را قفل می‌کند؛ کندی موقت آن را
  بالا نمی‌برد = ضد-ratchet؛ حذف رأی shadow هرگز تسریع نمی‌آورد)؛ commit اتمیک
  read→apply→write زیر `LockedJson` با recheck گیت/STOP داخل قفل؛ شکست primary
  write سیم را می‌بندد؛ شکست sink ثانویه commit را باطل نمی‌کند.
- **تست**: `test_pulse_arbiter_authority.py` (۲۷ تست) + اصلاح قراردادی
  `test_pulse_arbiter_wire_readiness.py`.
- **زنده**: پچ اعمال شد، ری‌استارت کنترل‌شده (RESTART-REQUESTED → خروج تمیز →
  relaunch)، تأیید ۲ beat. ثبت تناقض: **C-054** در `01-TRUTH/CONTRADICTIONS.md`
  (owner-ratify طبق قاعده باقی مانده).

### ب) کشف و رفع باگ `seal_tip` ژنوم + ترمیم tip زنده

- **گیت promotion** گیتِ `verify ∧ verify_tip` لازم داشت؛ `verify_tip` قرمز بود
  (file=14661 tip=14299، ولی tip_hash با head مطابق).
- **ریشه (forensic دو-مسیره)**: ۳۶۲ شکست خاموشِ نوشتن sidecar در 16–20 اوت
  (قفل فایل ویندوز، بلعیده با `except: pass`) که با منطق `prev_n+1` حفظ شد؛
  **صفر truncation**.
- **باگ دوم که کشف شد**: `seal_tip` اصلاً قادر به ترمیم count نبود چون
  `_commit_tip_unlocked` همیشه `prev_n+1` می‌نوشت. اصلاح شد (شمارش صریح)، تست
  بازتولیدکننده اضافه شد، روی کپی temp تمرین شد، سپس **یک بار روی زنده** با رسید:
  `GENOME-TIP-RESEAL-RECEIPT.json` (14299→14661، همان head hash، تاریخ دست‌نخورده).
  از آن پس verify_tip سبز و پایدار (بعد از ۵+ append هم 14666=14666).

### ج) رفع blocker اعتبارسنجی — timeout کاذب test_bounded_read

- fixture خودش write را از مسیر monkeypatch شدهٔ ۱۰ثانیه‌ای می‌گذراند + ۱۰۰×۳s
  انتظار سریالی = تضمینِ timeout ۳۰۰s. فقط fixture اصلاح شد (production دست‌نخورده).
  ریشه‌نامه: `BOUNDED-READ-ROOT-CAUSE.md`.

### د) Gate 1 — Heart v2 (روی درخت زنده، آماده، فعلاً inert)

فایل‌های جدید روی live (کپی و تست‌شده — ۱۹/۱۹):

| فایل | نقش |
|---|---|
| `_ops/heart/store.py` | HeartStore ترابزنشی روی همان chrono.db: جداول `heart_*`، `heart_schema_meta` مستقل (user_version دست‌نخورده)، نویسنده BEGIN IMMEDIATE، خواننده query_only، Genesis beat 0 (import واقعی، نه جعل تاریخ)، lifecycle RESERVED→COMMITTED/DEGRADED، events idempotent، outbox با lease/DLQ، anchors |
| `_ops/heart/state_machine.py` | FSM حیات: GENESIS/BOOTING/WARMUP/RUNNING/DEGRADED/SAFE/COMA/DORMANT — هیچ یال تهدید→توان‌بیشتر؛ kill supreme؛ recovery با streak=۳ (ضد-لرزش). **گارد خلوص بایت** روی همهٔ نام حالت‌ها (درسِ باگ DEGRAVED — پایین) |
| `_ops/heart/sensors.py` | حسگرهای typed فقط‌خواندنی از state زنده (beat/arbiter/stress/provider/telegram/write-failures) با quality=VALID/STALE/MISSING — غیبت هرگز صفر جعل نمی‌شود |
| `_ops/heart/kernel.py` | هستهٔ خالص: ارزیابی→حالت→period advisory→بیداری مغز (رویدادمحور، نه هر beat؛ آستانه‌ها: red=5، journal=20 شکست نوشتن/ساعت) |
| `_ops/heart/runtime.py` | ضربان واحد روی BeatScheduler موجود (هیچ حلقهٔ موازی جدید نکرده — قاعدهٔ بقا)؛ organها: SENSE/RECORD/THINK(brain)/HEAL(memory+commit). ACT عمداً ثبت نشده = صفر اثر خارجی. projection در `state/pulse/heart-v2-latest.json` |
| `_ops/cortex/heart_brain.py` | مغز مشاور DeepSeek — فقط از `model_router.ask` (درِ واحد موجود)؛ خروجی ساختاریافته، proposals همیشه `executable=false`؛ timeout/schema-نامعتبر ⇒ DEGRADED بدون proposal؛ chain-of-thought خام هرگز ذخیره نمی‌شود |
| `_ops/memory/continuity.py` | «هرگز گم نشود»: backup روزانهٔ chrono.db فقط با SQLite Online Backup API؛ restore-drill خودکار؛ projection در `_memory/OCTOPUS/NOW.md` + `AUTOBIOGRAPHY/YYYY/YYYY-MM-DD.md` (بخش مالک هرگز بازنویسی نمی‌شود) |
| `_ops/tests/test_heart_v2.py` | ۱۹ تست: genesis/lifecycle/idempotency/outbox/FSM-matrix/kernel/scheduler/brain/continuity — همه در sandbox harness |

تغییرهای دیگر روی live:

- `_ops/organism.py` — بلوک heart_v2 بعد از brain_core shadow tick (fail-soft مطلق؛
  خروجی به `pulse["heart_v2"]` در ORGANISM-STATE). **edit مستقیم زدیم چون فایل
  تغییرات کامیت‌نشدهٔ خودِ مالک داشت — با Edit، نه overwrite**.
- `_ops/watchdog.py` — حالت `--json` (verdict ماشین‌خوان).
- `04 - Architect System/scripts/organism-watchdog.ps1` — **رفع split-brain**:
  دوقلوی PowerShell حالا به verdict کانونی پایتون واگذار می‌کند (+ تشخیص استال
  اجرا می‌شود؛ blind-kill ممنون؛ متنِ alert پایدار برای dedup). PS1-PARSE-OK.
- `_ops/tests/run_all.py` — ثبت `test_heart_v2.py`.

## ⚠️ درسِ مهم: باگ «DEGRAVED»

در اولین نگارش state_machine یکجا `DEGRAVED` (V به‌جای D دوم) نوشته شده بود —
دقیقاً همان املا، در یک و فقط یک literal. نتیجه: مقایسه‌های هم‌منبع سبز،
cross-source قرمز، و دیباگ ساعت‌ها طول کشید چون hex-dump را هم اشتباه خواندیم.
**درس**: هر enum رشته‌ای که بین ماژول‌ها مقایسه می‌شود باید purity-guard بایتی
داشته باشد (`_assert_purity` در state_machine.py الگوست). اگر هرگز حالت‌ها
«می‌پرند»، اول این را چک کنید.

## فعال‌سازی Gate 1 (کار بعدی — فقط بعد از خواندن این سند)

```powershell
# ۰) پیش‌شرط‌ها: هیچ STOP/HALT/FREEZE؛ organism زنده؛ ledger verify+verify_tip سبز
# ۱) ساخت فلگ مالک (owner-gated — مطابق الگوی ACTIVATION-PULSE-ARBITER.flag):
New-Item -ItemType File "F:\backup\_ops\ACTIVATION-HEART-V2.flag"
# ۲) ری‌استارت کنترل‌شده (بدون لمس STOP مالک):
New-Item -ItemType File "F:\backup\_ops\RESTART-REQUESTED"
#    صبر خروج تمیز (تا ~۲ دقیقه)؛ سپس:
Start-Process -FilePath "F:\backup\_ops\RUN-ORGANISM.bat" -WorkingDirectory "F:\backup\_ops" -WindowStyle Hidden
# ۳) تأیید (۲-۳ beat؛ هر beat ~96s):
#    - ORGANISM-STATE.pulse.heart_v2 موجود با mode/beat/store_counts
#    - state/pulse/heart-v2-latest.json با schema=heart-v2/1
#    - chrono.db: SELECT COUNT(*) FROM heart_beat → رشد؛ beat=0 با mode=GENESIS
#    - _memory/OCTOPUS/NOW.md ظاهر شود؛ backup روزانه در state/heart-v2-backups/
#    - مغز: state/cortex/heart-brain/advisories.jsonl (اگر بودجه/کلید DeepSeek فعال باشد؛
#      وگرنه brain_stats.degraded بالا می‌رود — طبیعی و fail-soft)
```

**انتظار رفتاری**: FSM از BOOTING→WARMUP→RUNNING (بعد از ۳ beat با دادهٔ تازه).
period زنده تغییری نمی‌کند (Heart v2 فقط advisory است؛ تنها منبع period همان
pulse_arbiter با anchor G4). مغز حداکثر هر ۲۴ beat بیدار می‌شود یا رویدادمحور.

## بازگشت (rollback)

- **Gate 1 خاموش‌کردن فوری**: `Remove-Item F:\backup\_ops\ACTIVATION-HEART-V2.flag`
  + ری‌استارت (کد inert می‌شود؛ هیچ data-migration معکوس لازم نیست).
- **Gate 1 حذف کد**: حذف ۸ فایل جدید + برگرداندن organism.py/watchdog.py/run_all.py/PS1
  (یا `git checkout --` برای سه فایلِ ویرایش‌شده + `git clean` برای جدیدها — مراقب
  تغییرات کامیت‌نشدهٔ خود مالک در organism.py باشید؛ diff را قبلش ببینید).
- **G4 بازگشت**: `git checkout -- _ops/heart/pulse_arbiter.py` + حذف
  `test_pulse_arbiter_authority.py` + برگرداندن wire_readiness/bounded_read/run_all/ledger.py/test_ledger_tip_commit + ری‌استارت.
- **tip sidecar**: نیاز به بازگشت ندارد (شمارش واقعی را حمل می‌کند).

## بدهی‌های شناخته‌شده (وایسا — ذیل صلاحدید مالک/ایجنت بعد)

1. `test_phantom_guards` ۷/۹ — روی HEAD پاک هم قرمز (AST blind spots + ۶۶ فلگ
   بی‌اعلان)؛ pre-existing، با G4 تغییری نکرد.
2. runner کامل روی checkout تازه ~۶۶ شکست محیطی دارد (فایل‌های gitignored زنده)؛
   سوییت‌های مرتبطِ G4/Heart v2 همه سبز؛ runner روی درخت زندهٔ کامل باید سبزتر باشد.
3. پیگیری پیشنهادی: هشدار برای شکست tip-write در ledger (به‌جای `except: pass`).
4. C-054 منتظر owner-ratify طبق قاعدهٔ دفتر تناقض.
5. Gate 2+ طبق طرح مصوب: decision_arbiter + capabilities، Telegram cockpit یکپارچه،
   ADR-ها، memory graph کامل.

## نقشهٔ evidence (همه داخل vault — هیچ‌وقت گم نمی‌شود)

`06-EVIDENCE/HEART-G4-AUTHORITY-2026-08-25/`:
- `PHASE-0-MANIFEST.json` — snapshot قبل از تغییر + hash گارد
- `BASELINE-TESTS.json` + `baseline-tests/` — وضعیت قبل
- `RUN-ALL-AFTER.log` / `RUN-ALL-FINAL.log` / `RUN-ALL-G4-ONLY.log`
- `OFFLINE-LIVE-BASELINE-REPLAY.json` — بازپخوی G4 روی baseline واقعی
- `BOUNDED-READ-ROOT-CAUSE.md` + `BOUNDED-READ-INDEPENDENT-TIMINGS.json`
- `GENOME-TIP-PROMOTION-BLOCKER.md` (تاریخی) → `FORENSIC-TIP-ROOT-CAUSE.md`
  → `TIP-SEAL-REHEARSAL.json` (باگ کشف) → `TIP-SEAL-REHEARSAL-FIXED.json`
  → `GENOME-TIP-RESEAL-RECEIPT.json` (اجرای زنده)
- `G4-PROMOTION.patch` / `GATE1-PROMOTION.patch` — دقیقاً همان چیزی که اعمال شد
- `APPLY-RUNBOOK.md` / `VERIFICATION-SUMMARY.json` / `REPORT.md` / این `HANDOFF.md`

مانیتور tip: `_ops/state/pulse/g4-tip-monitor.jsonl` (append-only).

## اصولی که این نشست رعایت کرد (نگه دارید)

- کار در worktree ایزوله → تست → promotion فقط با hash-guard.
- هیچ commit/push انجام نشد (کل تغییرات روی درخت زندهٔ کاری مالک است — تصمیم
  کامیت با مالک).
- هیچ گیت پولی/identity/production-wire باز نشد؛ ACT هرگز ثبت نشد؛ همهٔ خروجی‌های
  مغز `executable=false`.
- ری‌استارت فقط با marker استاندارد؛ STOP مالک هرگز پاک نشد.
