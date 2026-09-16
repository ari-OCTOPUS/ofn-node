---
type: decision
decision_id: OWNER-DIRECTIVE-AGENT-C-PLAN
status: ACTIVE — lane ایجنت C (organs/afferents)؛ حاکم بر کارهای آن lane
created: 2026-08-20
created_by: OWNER — ثبت verbatim توسط ایجنت B (ثبت‌کنندهٔ دستورها)
lane_boundary: Telegram/owner_console/center/router/organism برای C ممنوع بدون handoff
note: lane تلگرام (canary) همچنان نزد ایجنت B — این سند اجرای B نیست
---

# OCTOPUS — طرح اجرایی عمیق ایجنت C
## از نقشهٔ اندام‌ها تا Knowledge Afferent واقعی
## تاریخ: 2026-08-20 · صادرکننده: OWNER

## نقش و lane

```yaml
agent: C
role: ORGAN_CARTOGRAPHER_AND_WIRING_SURGEON
lane: organs_afferents_and_internal_feedback
priority: SECONDARY_PARALLEL
lease_priority: LOWER_THAN_TELEGRAM_CRITICAL_PATH
```

مالکیت فایل‌های lane:

```text
_ops/organs/*
organ registry و sidecarها
organ-specific tests
knowledge afferent adapter
mapper/cartographer analysis
lead failure analysis
internal cognition inbox contract (نه Telegram handler)
```

فایل‌های Telegram، owner_console، center، router و organism hot path بدون handoff صریح ممنوع.

---

# هدف

یک اندام که فقط اسم یا sidecar دارد باید به یک حس واقعی، قابل اندازه‌گیری و قابل استفاده
تبدیل شود؛ بدون ایجاد نویز، halt، call پولی یا تداخل با حلقهٔ Telegram.

اولویت واحد:

```text
knowledge notes
→ real afferent events
→ bitemporal memory
→ cognition inbox
→ World Model hypothesis
→ owner feedback later
```

---

# C0 — تثبیت گزارش و اصلاح برچسب‌ها

## اجرا

1. گزارش `PASS_WITH_FINDINGS` را freeze کن.
2. ۱۵ تست را در `run_all` ثبت کن؛ تا آن زمان PASS فقط local است.
3. برچسب mapper را اصلاح کن:

```text
1257 MAP_STALENESS_CANDIDATES
```

نه drift قطعی، چون baseline inventory قبلی وجود نداشته است.
4. baseline امروز را به‌عنوان epoch جدید mapper ذخیره کن.
5. تعداد ۱۴ اندام و طبقه‌بندی‌ها را با schema و proof path قفل کن.

## چرا

اگر معیارها وارد regression و baseline canonical نشوند، گزارش امروز فردا قابل مقایسه نیست
و «drift» دوباره به حدس تبدیل می‌شود.

---

# C1 — Root cause starvation را به اجزای قابل تست بشکن

حکم فعلی `MIXED` است:

```text
NO_SOURCE + BROKEN_READER + THRESHOLD_MISCALIBRATION
```

برای هر source جدول بساز:

```yaml
source:
producer_exists:
reader_exists:
last_event:
expected_cadence:
observed_cadence:
threshold:
classification:
```

## آزمون counterfactual آفلاین

بدون تغییر threshold، replay کن:

- source موجود + reader خراب
- source غایب + reader سالم
- cadence واقعی با threshold فعلی
- knowledge events تزریق‌شده از fixture واقعی

اندازه بگیر کدام مؤلفه بیشترین سهم را در `afferent_starved` دارد.

## چرا

حکم MIXED برای تصمیم اجرایی کافی نیست؛ باید بدانیم اولین patch کدام علت را واقعاً کم می‌کند.

---

# C2 — Knowledge sidecar را production-grade کن

۶۵۵ رویداد واقعی ارزشمندند، ولی sidecar باید این شروط را پاس کند:

## Idempotency

```text
knowledge_event_id = hash(path + content_hash + schema_version)
```

هر نسخه نوت حداکثر یک event.

## زمان

```yaml
occurred_at: filesystem mtime یا زمان واقعی ثبت‌شده در frontmatter
recorded_at: زمان ingest sidecar
```

اگر هیچ‌کدام معتبر نیست:

```text
INELIGIBLE_TEMPORAL_METADATA
```

نه timestamp فعلی جعلی.

## schema

```yaml
path_hash:
content_hash:
document_type:
tags:
frontmatter_valid:
link_count:
changed_fields:
occurred_at:
recorded_at:
provenance:
quality:
```

## Security

- محتوای کامل نوت وارد telemetry عمومی نشود.
- secret/PII scan قبل از semantic candidate.
- accounting و secret paths denylist.

## چرا

تعداد event زیاد به‌تنهایی حس نیست؛ حس باید idempotent، زمان‌دار، قابل‌اعتماد و قابل مصرف باشد.

---

# C3 — Hook را بساز، ولی فعال نکن

یک hook flag-gated طراحی و کدنویسی کن:

```text
knowledge sidecar queue
→ knowledge_afferent_hook
→ organism afferent registry
→ memory candidate
→ cognition inbox
```

## Flag

```text
OCTOPUS_KNOWLEDGE_AFFERENT_HOOK=0  # پیش‌فرض خاموش
```

## ممنوع تا handoff A/B

- تغییر `organism.py` hot path
- فعال‌کردن flag
- restart
- merge

اگر hook بدون تغییر hot path از plugin registry قابل اتصال است، همان مسیر ارجح است.

## چرا

Telegram هنوز روی canary critical path است. اتصال هم‌زمان Knowledge و Telegram attribution
هر failure را غیرقابل تشخیص می‌کند.

---

# C4 — معیار فعال‌سازی Knowledge

پس از اینکه A/B اعلام کردند Telegram canary PASS شده و lease آزاد است، handoff لازم:

```yaml
handoff_id:
telegram_lane_status: PASS
hot_files_released: true
lease_owner: none
approved_hook_commit:
rollback_commit:
```

سپس فقط یک canary knowledge:

```text
flag ON
→ یک نوت تست تغییر می‌کند
→ یک event
→ afferent counter +1
→ memory candidate
→ cognition inbox heard receipt
→ flag OFF
```

## PASS

```text
exactly one event
future_use=0
fabricated time=0
memory candidate has provenance
at least one brain heard
unexpected executable=0
protective halt=0
alert storm=0
rollback works
```

## چرا

اولین اتصال باید یک event کنترل‌شده بسازد، نه ناگهان ۶۵۵ event را وارد organism کند.

---

# C5 — Backfill ممنوع، catch-up کنترل‌شده

پس از canary، برای ۶۵۵ event:

- backfill تاریخی در live spine ممنوع.
- catch-up queue با برچسب `HISTORICAL_IMPORT`.
- batchهای کوچک، مثلاً ۲۵ event.
- بین batchها health check.
- semantic candidates ابتدا `UNCONFIRMED`.
- توقف با اولین halt/latency anomaly.

## چرا

ورود ناگهانی ۶۵۵ event می‌تواند همان سیستم alert و afferent را flood کند و نتیجه‌ای معکوس بدهد.

---

# C6 — Dead feedback loop دانش

Knowledge اکنون event تولید می‌کند ولی proposalهایش رأی یا سرنوشت ندارند.

## اصلاح طراحی

- event خام به Telegram نرود.
- حداکثر یک digest knowledge در روز یا on-demand.
- proposal فقط اگر:
  - evidence جدید؛
  - owner impact مشخص؛
  - confidence حداقلی؛
  - duplicate proposal وجود نداشته باشد.

هر proposal state:

```text
PROPOSED → SEEN → ACCEPTED | REJECTED | EXPIRED
```

proposal بی‌پاسخ پس از TTL به `EXPIRED`، نه تکرار notification.

## چرا

حلقهٔ feedback بسته نمی‌شود اگر سیستم فقط پیشنهاد تولید کند و destiny آن‌ها را ثبت نکند.

---

# C7 — Loop breakers عمومی

## Sentinel

`-1` → `UNKNOWN` → «نامعلوم»؛ تست domain nonnegative.

## Tool request

حداکثر دو attempt، سپس quarantine 24h؛ duplicateها digest.

## RFC

- RFCهای مشابه merge؛
- سقف RFC باز؛
- evidence + rollback اجباری.

## Autotune

evidence بدون تغییر → notification جدید ممنوع.

## Protective halt

یک incident per root cause/epoch؛ count update به‌جای پیام جدید.

## چرا

این حلقه‌های معیوب ظرفیت شناختی و توجه مالک را مصرف می‌کنند و مانع حلقهٔ اصلی‌اند.

---

# C8 — Mapper قابل مقایسه

baseline امروز را canonical کن و در scan بعد:

```text
actual new
actual modified
actual deleted
orphan imports
dead paths
duplicate implementations
```

هر ادعای drift باید دو inventory hash داشته باشد.

## چرا

«فایل جدیدتر از نقشهٔ قدیمی» با «تغییر از baseline قبلی» یکی نیست.

---

# C9 — Lead فقط تشخیص

طبقه‌بندی `ACK_TIMEOUT` و `phi NOT_COMPARABLE` پذیرفته است.

قدم بعد:

- تعریف ACK contract؛
- اندازه‌گیری latency distribution؛
- تعیین اینکه phi نسخه‌دار/هم‌واحد است یا نه؛
- replay failure بدون فعال‌سازی business action؛
- RFC حداقلی.

هیچ restart خودکار lead، تماس مشتری یا مسیر درآمد.

---

# C10 — Cognition inbox داخلی

ایجنت C فقط contract و producer اندام‌ها را مالک است. consumer/synthesis با A/B هماهنگ شود.

```yaml
organ_event:
  event_id:
  organ_id:
  occurred_at:
  recorded_at:
  evidence_ids:
  quality:
  payload_hash:
```

هر brain:

```yaml
heard:
input_event_id:
output_hash:
status:
executable: false
```

## چرا

بدون inbox مشترک، اندام‌ها داده تولید می‌کنند ولی مغزها آن را نمی‌شنوند؛ همان شکاف Telegram
در داخل organism تکرار می‌شود.

---

# C11 — ادامه‌سازی پس از Knowledge

فقط پس از PASS کامل knowledge canary، اولویت‌های بعدی:

1. Mapper afferent: تغییرات واقعی کد/ساختار.
2. System health afferent: PID/port/beat/lease.
3. Lead diagnostic afferent: failure receipts فقط‌خواندنی.
4. Crypto/mining/accounting/studio: همچنان map/RFC تا دستور مالک.

هر session حداکثر یک اندام جدید.

## چرا

یک اتصال در هر زمان attribution را حفظ و ریسک cascade را محدود می‌کند.

---

# پروتکل دیباگ C

```text
one hypothesis
→ one failing test
→ one minimal patch
→ replay fixture
→ regression/run_all
→ canary single event
→ observation window
→ verdict
```

اگر نیاز به hot file یا restart شد: STOP و handoff به A/B؛ خودسرانه اجرا نکن.

---

# گزارش نهایی C

```text
C0 regression registered:
C1 dominant starvation cause:
C2 sidecar contract:
C3 hook code ready:
C4 canary status:
C5 catch-up status:
C6 feedback loop:
C7 loop breakers:
C8 mapper baseline:
C9 lead diagnosis:
C10 cognition inbox:
real events:
future-use:
protective halt:
alerts:
paid calls / AUD:
lease conflicts:
Telegram files touched: باید 0
commit / branch:
```
