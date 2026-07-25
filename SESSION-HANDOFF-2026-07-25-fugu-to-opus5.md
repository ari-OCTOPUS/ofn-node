# SESSION HANDOFF — Fugu → Opus 5 — 2026-07-25

## حکم کوتاه

C2 و C3 و آماده‌سازی تاریک سه مسیر router تکمیل شده‌اند. شاهد نهایی مالک:

```text
✅ همهٔ 292 فایل تست سبز (capability marker با fingerprint نوشته شد)
exit=0
ALL GREEN
```

فرمان شاهد:
`powershell -NoProfile -ExecutionPolicy Bypass -File "F:\backup\_ops\VERIFY-2026-07-25-C2-C3-ROUTER.ps1"`

**هنوز commit ساخته نشده است.** Fugu shell/git ندارد. write-lock Fugu آزاد شده؛ Opus فقط پس از بررسی diff و اطمینان از نبود writer دیگر ادامه دهد.

## چه تعمیر شد

### C2 — hypothesis producer

- `_ops/c6_probes.py` و `_ops/c6_producer.py` افزوده شدند.
- producer فقط از evidence واقعی hypothesis می‌سازد؛ صف خالی مجاز است.
- lifecycle صف در `_ops/c6_trigger.py` id-safe شد؛ `_mark_hypothesis` دیگر همهٔ RUNNINGها را نمی‌بندد.
- stale RUNNING reaper، id-backfill و fail-soft producer wiring افزوده شد.
- `mechanism_count` بازتولید نقص را می‌سنجد و ادعای «اصلاح اعمال‌شده» نمی‌کند.
- C6 همچنان propose-only است؛ تست مرزی PASS است.

### C3 — owner trust

- `research_loop.py` دیگر `source=owner` و `OWNER_CONFIRMED` جعل نمی‌کند.
- trust مالک فقط از attestation پایدار writer کانونی `verdict_recorder` مشتق می‌شود.
- claim بی‌گواهی در semantic به GRADED cap و audit می‌شود؛ در owner_fact مسدود می‌شود.
- `memory/gate.py` دفاع لایهٔ دوم علیه producer خودکار با `source=owner` دارد.
- مسیر واقعی رأی مالک همچنان OWNER_CONFIRMED می‌ماند.

### Router dark config

- مسیرهای governor، heart doctor و self-knowledge با fixture کاملاً آفلاین تست شدند.
- تست fail-softِ خطای router نیز اجرا شد.
- `OCTOPUS-flags.cmd` با CRLF و assignment صریح `0` برای این‌ها قفل شد:
  - `OCTOPUS_WIRE_C6_PRODUCER`
  - `OCTOPUS_GOVERNOR_USE_ROUTER`
  - `OCTOPUS_HEART_DOCTOR_USE_ROUTER`
  - `OCTOPUS_DOCTOR_SELFKNOW_PAID`
- **هیچ تماس provider، مصرف سهمیه، restart یا خروج داده در lane Fugu رخ نداد.**

## commitهای پیشنهادی — سریالی

ابتدا `git diff -- <paths>` را بررسی کن. اگر writer دیگری همان فایل را تغییر داده، توقف و ownership را حل کن.

```powershell
cd F:\backup

git add -- _ops/c6_probes.py _ops/c6_producer.py _ops/c6_trigger.py _ops/tests/test_c6_hypothesis_producer.py _ops/tests/test_c6_trigger_propose_only.py
git commit -m "fix(c6): add honest hypothesis producer and id-safe queue lifecycle"

git add -- _ops/outcomes/learning_gate.py _ops/memory/gate.py _ops/outcomes/research_loop.py _ops/tests/test_learning_loop.py _ops/tests/test_c3_owner_trust_forgery.py
git commit -m "fix(memory): derive owner trust from durable attestation"

git add -- _ops/tests/test_paid_router_dark_config.py _ops/tests/run_all.py _ops/OCTOPUS-flags.cmd
git commit -m "chore(llm): lock router paths behind explicit dark flags"
```

قفل آنتی‌ویروس روی `.git/objects` ممکن است برگردد؛ add/commit را retry کن، اما هرگز `git clean` نزن.

پس از commit سوم:

```powershell
python -X utf8 "F:\backup\_ops\tests\run_all.py"
```

عدد و exit code را ثبت کن؛ baseline اکنون 292 فایل است.

## هماهنگی با MEGAPROMPT

`MEGAPROMPT--octopus-repair-2026-07-25.md` کارهای T1..T8 را جداگانه تعریف می‌کند. آن‌ها را با این lane مخلوط نکن:

1. اول سه commit بالا و suite پس از commit.
2. سپس T1/T2/T3/T4 را با ownership سریالی انجام بده.
3. T5 activation مرحله‌ای جداست. owner در گفت‌وگوی جاری اختیار تصمیم‌گیری داده، اما سه فلگ router **فعلاً صفرند** و تست dark-config همین را اثبات می‌کند. برای فعال‌سازی:
   - تست dark-config را به contract مرحله‌ای مناسب تبدیل کن؛ تست را صرفاً حذف/شل نکن.
   - فایل cmd فقط byte-level و CRLF-preserving ویرایش شود؛ هرگز dump/tail/echo نشود.
   - restart فقط پس از suite سبز.
   - `paid-calls.jsonl` و `fugu-quota.json` شاهد استفاده‌اند؛ `cost_usd=0` شاهد عدم استفاده نیست.
   - سقف جلسه طبق MEGAPROMPT: 25 فراخوان.
   - خطای نو در governor-alerts یا جلو نرفتن beat = توقف و rollback فلگ‌ها به 0.
4. `production_wire`، `OCTOPUS_CB_SECRET` و `_ops/ACTIVATION-C6-RESEARCH.flag` همچنان قفل‌های خاص خود را دارند؛ ایجنت secret/activation file را نمی‌سازد.

## artifacts

- گزارش کامل: `_program-deliverables/C6-substance-2026-07-25/EXECUTION-REPORT-2026-07-25.md`
- checkpoint زنده: `_program-deliverables/C6-substance-2026-07-25/LIVE-CHECKPOINT-2026-07-25-fugu.md`
- verify سریع: `_ops/VERIFY-QUICK-2026-07-25.ps1`
- verify کامل: `_ops/VERIFY-2026-07-25-C2-C3-ROUTER.ps1`

این artifacts ممکن است هنوز untracked باشند؛ پیش از commit با `git status --short` تصمیم بگیر کدام‌ها باید در commit مستندات جدا ثبت شوند.

## صداقت فرایندی

Fugu یک‌بار در میانهٔ کار `OCTOPUS-flags.cmd` را متنی خواند؛ این خلاف قانون بود. پس از آن، بررسی فقط byte-level و بدون چاپ محتوا انجام شد. این رخداد نباید از گزارش حذف شود.

## آنچه Fugu انجام نداد

- commit واقعی
- restart/deploy/send
- تماس پولی یا شبکه
- روشن‌کردن فلگ‌های router
- ساخت `OCTOPUS_CB_SECRET`
- ساخت `_ops/ACTIVATION-C6-RESEARCH.flag`
- اجرای T1..T8 مگاپرامپت
