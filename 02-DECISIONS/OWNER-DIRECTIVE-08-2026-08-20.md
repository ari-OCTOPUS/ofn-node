---
type: decision
decision_id: OWNER-DIRECTIVE-08
status: ACTIVE — حاکم بر دستورهای #۱ تا #۷
created: 2026-08-20
created_by: OWNER — ثبت توسط ایجنت B (ZCode) از متن پیست‌شدهٔ مالک
audience: ایجنت A و ایجنت B
base_state: WAVE0_OBSERVE_ONLY / L2_ARMED / executable=false / GAP-001=OPEN / paid_calls_authorized=0
---

# OCTOPUS — دستور مالک #۸
## حداکثر پیشروی مجاز: فعال‌سازی lease، event-time واقعی، خواندن حافظه

# ۰) دو تصحیح از سمت مالک

۱. حق با ایجنت B بود: «تست بکاپ کلید توسط ایجنت» با §۳ دستور #۷ ناسازگار بود؛
حاکم متن دستور است. حکم `UNTESTED` پذیرفته؛ `backup_recovery: UNKNOWN` تا اجرای
شخصی مالک. ۲. کیفیت کار پذیرفته شد (ERRATA-2، لنگر اعتماد، رفع باگ
default-arg، حکم UNLOCATED).

# ۱) رفع انسداد LIVE-A

```yaml
LEASE_MANDATORY_FOR_ALL_AGENTS: true
authority: OWNER-DIRECTIVE-08
agent_A_acceptance: GRANTED_BY_OWNER_ON_BEHALF
agent_B_acceptance: ALREADY_IMPLIED_BY_IMPLEMENTATION
```

خط ثبت‌شده در AGENT_QUESTIONS: «LEASE_ACCEPTED_BY_A — granted by
OWNER-DIRECTIVE-08 (2026-08-20). هر ایجنتی که lease نگیرد، حق نوشتن ندارد.
عدم پاسخ = پذیرش.»

## T47 — فعال‌سازی فیزیکی lease
فعال‌سازی `_ops/writer_lease.py`؛ fail-closed پیش‌فرض (بدون lease یا نامعلوم ⇒
read-only)؛ دامنهٔ اجباری ledger/evidence/budgets/state/git-write؛ TTL کوتاه با
renew صریح؛ lease منقضی بایگانی نه پاک؛ هر رسید با agent_id و session_id؛
یک چرخهٔ واقعی acquire→renew→release با رسید. **گیت: با فعال شدن lease و رسید
واقعی آن ⇒ LIVE-A = PASS.**

# ۲) مجوز صریح تغییر کد زنده — دامنهٔ محدود (instrumentation)

allowed: مبدأ زمان رویداد در producerها · فیلد در رسیدهای router · شمارندهٔ
تلمتری · مسیر خواندن حافظه (read-only) · feature flag و rollback.
forbidden: Planner/policy/actuator/money execution · مقادیر بودجه/سقف · منطق
داور/arbiter · C-042/rounding/warm-up · scheduler/cron · deploy روی Orange Pi ·
هر executable=true.
شرط هر تغییر: زیر lease + feature flag + rollback مکتوب + baseline قبل/بعد.
هیچ ریاستارتی بدون ثبت baseline پیش از اولین رخداد.

# ۳) T48 — دو producer واقعی event-time (LIVE-B)

producer_1: domain=provider · occurred_at=server response timestamp ·
recorded_at=زمان نوشتن محلی · time_precision=ms.
producer_2: domain=telegram · occurred_at=message.date ·
recorded_at=زمان ingest محلی · time_precision=1s.

قواعد سخت: ساعت نوشتن هرگز occurred_at نمی‌شود؛ نبود منبع واقعی ⇒
`INELIGIBLE_TEMPORAL_METADATA`؛ `occurred_at > recorded_at` ⇒
`CLOCK_SKEW_SUSPECTED` بدون اصلاح خودکار؛ دامنه‌های داخلی (system, doctor,
neural, lead, ziman) دست نخورند؛ **dual-write فقط افزودنی** — ستون‌های موجود
بازنویسی نشوند؛ رکوردهای قدیمی `legacy_no_event_time: true` و نسخهٔ schema یک
پله بالا؛ هیچ backfill جعلی.
سنجش: ≥۶۰ دقیقه جمع‌آوری واقعی؛ توزیع delta هر دو producer با
median/stdev/min/max/n؛ حداقل یک late-arriving واقعی.
گیت LIVE-B: ‏independent_sources≥2 · stdev>10ms در هر دو · real_late≥1 ·
suite ۱۵تایی روی داده واقعی PASS · همهٔ مسیر خواندن از decision_time = PROVEN.

# ۴) T49 — سیم‌کشی خواندن حافظه (LIVE-C)

مجوز صریح: `_ops/memory_read_loop.py` به حلقهٔ زندهٔ `organism.py`، فقط خواندن.
سه تابع: query_experiments · get_pending_hypotheses · search_vault؛ همه با
decision_time؛ شمارندهٔ `memory_reads_per_cycle` در تلمتری؛ flag پیش‌فرض روشن
برای خواندن/خاموش برای اثر جانبی؛ خطای مسیر هرگز حلقه را نکشد ⇒
`MEMORY_READ_DEGRADED`؛ تست read-back زنده (نوشتن N، خواندن N+1).
گیت LIVE-C: ‏reads_per_cycle>0 زنده · read-back=PASS · هیچ خواندنی بدون
decision_time · executable=false · organism crash=0.

# ۵) T50 — تفکیک رسید هزینه
فیلدهای `task_id` و `run_id` به رسیدهای router؛ رسید بدون task_id ⇒
`UNATTRIBUTED`؛ T35 با UPPER_BOUND بماند؛ بازنویسی گذشته ممنوع.

# ۶) T51 — کارت LIVE-D بدون اجرا
`PRE-REG-FULL-LOOP-FLASH-2026-08-20`: tasks=12 · interval=5m · max_calls=12 ·
concurrency=1 · hard_stop=AU$0.50 · timeout=60s · max_retries=1 ·
judge=advisory_only (D6 pair-dependent) · output=proposal_only ·
executable=false · execution_condition: LIVE-A+B+C=PASS و امضای Ed25519 جداگانه.
هزینه از سطل علم موجود؛ هیچ سقفی بالا نرود.

# ۷) ترتیب و توقف‌ها
```text
1. lease activation → LIVE-A=PASS     2. receipt fields (T50)
3. event-time producers (T48) — 60m   4. memory read wiring (T49)
5. bitemporal suite روی داده واقعی     6. کارت LIVE-D (T51) بدون اجرا
```
STOP فوری: هر executable=true · crash ارگانیسم/daemon · خطای acquire/renew که به
دو نویسندهٔ هم‌زمان بینجامد · هر فراخوان پولی · write به Planner/actuator ·
شکستن hash chain لجر/evidence · occurred_at جعلی/backfill.
در این حالت‌ها: rollback همان feature flag + گزارش؛ اصلاح خلاقانه ممنوع.

# ۸) ممنوعیت‌های ثابت
ablation BLOCKED تا LIVE-A=PASS و امضای مخصوص · رأی چت هرگز جانشین امضا نیست ·
سقف بودجه بالا نرود · amend/rebase ممنوع · Orange Pi دست نخورد · GAP-001 با این
دستور بسته نمی‌شود.
