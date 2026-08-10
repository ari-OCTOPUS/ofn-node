---
tags: [ofn, megaprompt, marketing, integration, observability, webhooks, owner]
aliases: [مگاپرامپت پلتفرم مارکتینگ, Marketing Platform Integration]
updated: 2026-08-10
status: باز — طراحی مفهومی برای اجرای مرحله‌ای
---

# مگاپرامپت عمیق — یک پلتفرم مارکتینگ برای سه بیزنس، با مغز OFN

> **برای ایجنت بعدی.** این سند self-contained است. آن را کامل بخوان، سپس
> مرحله‌به‌مرحله اجرا کن. هدف این نیست که یک معماری اینترنتیِ سنگین را روی
> اورنج‌پای کپی کنی؛ هدف این است که مفاهیم مفید آن معماری را با OFN موجود
> ترکیب کنی، بدون بازنویسی کرنل، بدون شکستن tenancy، و بدون باز کردن خروجی.
>
> هر ادعا باید ثبت مستقل داشته باشد ([[CLAUDE|§۸-ب]]). هر عدد باید با تست
> یا اندازه‌گیری زنده راستی‌آزمایی شود ([[CLAUDE|§۸-الف]]).

**پیوندها:** [[INDEX]] · [[HANDOFF]] · [[CLAUDE]] · [[DECISIONS]] ·
[[PORTFOLIO-TENANT-MAP]] · [[MEGAPROMPT-OWNER-COMPLETE]] ·
[[LESSONS-ZIMAN]] · [[LESSONS-STUDIO]]

---

## ۰) مأموریت

سه بیزنس واقعی باید از یک پلتفرم مارکتینگ بیرونی استفاده کنند، اما OFN باید
مرجع تصمیم، ریسک، رضایت، tenancy، ledger و outbox باقی بماند:

```
پلتفرم مارکتینگ بیرونی
  CRM · فرم/فانل · تقویم · inbox · آمار · workflow
                  │
                  │ API / webhook محدود و قابل‌تعویض
                  ▼
OFN روی Orange Pi
  tenant isolation · scrub · risk · consent · quota
  correlation · idempotency · ledger · owner approval · outbox
                  │
                  ▼
انسان حکم می‌کند
```

پلتفرم بیرونی **مغز نیست**، **مرجع مجوز نیست**، و **حق ارسال مستقل ندارد**.
هر workflow بیرونی که بتواند بدون OFN پیام، ایمیل، پست، quote یا پرداخت ایجاد
کند، باید خاموش بماند تا آری آن مسیر مشخص را جداگانه تأیید کند.

### معیار موفقیت

```
۱. یک حساب/پلتفرم، سه فضای کسب‌وکار جدا
۲. یک connector contract داخل OFN، بدون قفل‌شدن به vendor
۳. inbound قابل‌اعتماد: امضا → tenant → dedup → ledger
۴. outbound همچنان: decision → outbox → owner two-step → adapter
۵. observability سبک و قابل‌ردیابی، بدون Redis/Postgres/K8s روی برد
۶. همه‌چیز fail-closed و قابل rollback
```

---

## ۱) حقیقت امروز — قبل از اجرا زنده بسنج

این snapshot فقط نقطهٔ شروع است و حقیقت دائمی نیست:

```
repo OFN       /home/ari/ofn
branch         ofn-v1.0-three-business-owner-center
HEAD هنگام نگارش  4dcb0ce
OFN tests      1600 collected (1595 pass + 5 skip در snapshot)
hypno tests    73 pass در snapshot
services       ofn · hypno-fugu-mini · cloudflared active
NTP            enabled + synchronized در snapshot
HTTPS          panel/ziman/lead/studio/hypno = 200 در snapshot
```

اول اجرا کن:

```bash
cd ~/ofn
python3 tools/repo_baseline.py --tests
python3 -m pytest -q
git status -sb
git log -3 --oneline
systemctl is-active ofn hypno-fugu-mini cloudflared
timedatectl show -p NTP -p NTPSynchronized
ss -tlnp | grep -E ':(8791|8792|8793|8794|8895|8090|22)\b' || true
```

دو فایل `.bak-*` ممکن است untracked باشند. آن‌ها را نخوان، stage یا commit نکن.

**قاعدهٔ توقف:** اگر تست قرمز است، قبل از هر کار گزارش بده. اگر پورت ۸۰۹۰
دوباره روی `0.0.0.0` دیده شد، فقط راستی‌آزمایی و گزارش؛ بدون تأیید آری kill نکن.

---

## ۲) inventory و واژه‌نامهٔ قطعی

چهار tenant فنی وجود دارد؛ فقط سه مورد در scope مارکتینگ این سندند:

| tenant | بیزنس/برند | شریک | scope این سند |
|---|---|---|---|
| `ziman` | GiftMesh Sydney | ملیحه | بله |
| `lead` | Painting / master-painting.com | عباس | بله |
| `studio` | تولید محتوا | سبا | بله، با sensitivity محدود |
| `hypno` | — | — | **نه**؛ فقط در inventory دیده شود |

قواعد:

- GiftMesh Sydney برند `ziman` است، نه tenant پنجم (D-25).
- `tenant_id` مرز مجوز و داده است؛ `brand_id` فقط برچسب گزارش.
- OFN نام پلتفرم است، نه بیزنس چهارم.
- رجیستری ۴۴ منبع painting یک registry است، نه corpus تحقیقاتی.
- corpus تحقیقاتی GiftMesh هنوز وجود ندارد؛ چیزی اختراع یا cross-tenant نکن.

---

## ۳) چه چیزی از دادهٔ جدید می‌گیریم — و چه چیزی را وارد نمی‌کنیم

مطالب جدید مفاهیم زیر را پیشنهاد می‌کنند:

| مفهوم بیرونی | معادل درست در OFN |
|---|---|
| Redis rate limit | rate-limit سبک در حافظه/SQLite؛ بدون daemon جدید |
| Redis idempotency | UNIQUE key و تراکنش SQLite در inbox/outbox |
| FastAPI middleware | wrapper در `http_api.py` / handler مشترک |
| asyncpg/Postgres pool | `sqlite_base.Pool` موجود + WAL/FULL |
| Celery queue | `worker.WorkQueue` موجود + ledger shadow |
| Prometheus metrics | registry سبک stdlib + endpoint owner/loopback؛ exporter اختیاری |
| OpenTelemetry correlation | correlation ID + structured ledger/log؛ OTel اختیاری و off |
| Jaeger/Tempo | روی این برد نصب نشود؛ backend بیرونی فقط در فاز اختیاری |
| Docker/K8s secrets | همان فایل‌های 0600 موجود؛ راز وارد git/env output نشود |
| WhatsApp runbook | runbook vendor-neutral؛ WhatsApp فقط بعد از تصمیم مالک |
| DLQ | حالت `held/parked/failed` موجود؛ صف جدید کورکورانه پاک نشود |
| GHL/Zoho Agent/MCP | **ادعای تأییدنشده** تا بررسی مستندات رسمی زنده |

### چیزهایی که نباید انجام شوند

```
❌ نصب Redis، Postgres، Celery، FastAPI، Prometheus، Grafana یا Jaeger روی برد
   فقط چون نمونهٔ اینترنتی از آن‌ها استفاده کرده
❌ docker-compose سنگین روی برد ۴GB
❌ افزودن dependency قبل از اثبات اینکه stdlib کافی نیست
❌ جایگزین‌کردن outbox یا ledger موجود
❌ ساخت مسیر ارسال مستقیم از connector
❌ فعال‌کردن WhatsApp/DM خودکار؛ D-13 آن را حذف کرده
❌ اعتماد به ادعای قیمت، MCP، sub-account یا API بدون سند رسمی روز
```

### ۳-الف) شکاف‌های واقعیِ تأییدشده در کد امروز

دو کاوش مستقلِ read-only روی کد، این مرز را تأیید کردند:

```
موجود است
  stdlib HTTP · Telegram auth · tenant routing · SQLite WAL/FULL
  ledger زنجیره‌ای · outbox ایدمپوتنت · OwnerRelease · consent
  publish rate verdict · worker مغز · sysmetrics · systemd alert
  سه platform adapter که default آن‌ها dry-run است

واقعاً غایب است
  request/correlation ID سراسری
  HTTP inbound rate limiting
  durable inbound webhook/inbox
  webhook route و signature verifier vendor
  connector health زنده
  metrics مربوط به connector/inbox
  outbox publish drain واقعی
```

**مرز مهم:** نبود outbox drain در این مأموریت یک gap برای «مشاهدهٔ صادقانه»
است، نه مجوز ساخت sender. `owner_decide()` امروز verdict/claim را ثبت می‌کند
ولی adapter واقعی را اجرا و `mark_sent()` نمی‌کند. تا وقتی WIREها، گیت‌ها و
تصمیم جداگانهٔ مالک باز نشده‌اند:

```
❌ sender loop نساز
❌ approved را sent علامت نزن
❌ OwnerRelease را به publish واقعی وصل نکن
✅ فقط contract · fake/dry-run · inbox · مشاهده‌پذیری · runbook
```

---

## ۴) قوانین سخت

### هرگز

1. راز را نخوان، echo نکن، در تست/گیت/لاگ/HANDOFF ننویس.
2. هیچ `OFN_WIRE_*` یا `OCTOPUS_WIRE_*` را روشن نکن.
3. گیت‌های `secret_rotation`، `partner_precondition` و `miner_isolation` را باز نکن.
4. هیچ پیام، ایمیل، SMS، DM، پست، quote، invoice یا پرداخت واقعی نفرست.
5. outbox را خالی نکن.
6. adapter بیرونی را با `dry_run=False` صدا نزن.
7. D-13 را دور نزن: خودکارسازی پیام مستقیم کد نمی‌شود.
8. اطلاعات عمومی تماس را رضایت مارکتینگ فرض نکن.
9. scraping از Google Maps/GBP یا portal محافظت‌شده نساز.
10. داده، fact، metric یا contact را میان tenantها جابه‌جا نکن.

### آزاد

- خواندن مستندات رسمی عمومی برای ارزیابی vendor
- ساخت connector interface، fake adapter و contract test
- دریافت webhook جعلی امضاشده در تست
- sync خواندنی/dry-run با fixture
- نوشتن draft و queue در outbox، بدون ارسال
- metrics محلی و runbook

---

## ۵) معماری هدف

### ۵-الف) لایه‌ها

```
┌────────────────────────────────────────────────────────────┐
│ Business Apps                                              │
│ ziman · lead · studio · owner panel                        │
└──────────────────────┬─────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────┐
│ OFN HTTP Boundary                                          │
│ body cap → correlation → inbound limit → auth/signature    │
│ → tenant resolve → replay/dedup → dispatch                 │
└──────────────────────┬─────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────┐
│ Connector Boundary                                        │
│ capabilities · normalized events · health · dry-run        │
└──────────────┬─────────────────────────────┬───────────────┘
               │ inbound                     │ outbound intent
┌──────────────▼──────────┐      ┌───────────▼──────────────┐
│ Durable Inbox (SQLite)  │      │ Existing Outbox (SQLite) │
│ UNIQUE provider/event   │      │ idem · held · two-phase  │
└──────────────┬──────────┘      └───────────┬──────────────┘
               │                              │
┌──────────────▼──────────────────────────────▼──────────────┐
│ Kernel + Node                                             │
│ tenancy · scrub · risk · consent · rate · release switch  │
│ ledger · owner two-step · kill switch                     │
└────────────────────────────────────────────────────────────┘
```

### ۵-ب) connector contract

فایل پیشنهادی: `ofn/adapters/marketing_connectors/base.py`

interface باید vendor-neutral باشد:

```python
@dataclass(frozen=True)
class ConnectorCapabilities:
    read_contacts: bool = False
    read_conversations: bool = False
    read_metrics: bool = False
    receive_webhooks: bool = False
    create_draft: bool = False
    send_message: bool = False
    publish_content: bool = False

@dataclass(frozen=True)
class NormalizedEvent:
    provider: str
    provider_event_id: str
    tenant: str
    kind: str
    occurred_at: str
    payload_hash: str
    safe_fields: Mapping[str, object]
    correlation_id: str

class MarketingConnector(Protocol):
    name: str
    capabilities: ConnectorCapabilities
    def health(self) -> ConnectorHealth: ...
    def normalize_webhook(self, raw: bytes, headers: Mapping[str, str]) -> NormalizedEvent: ...
    def read_snapshot(self, tenant: str, cursor: str | None) -> ConnectorPage: ...
    def create_draft(self, request: DraftRequest) -> ConnectorResult: ...
```

**در نسخهٔ اول `send_message=False` و `publish_content=False` هستند.**
fake adapter باید ثابت کند هیچ call بیرونی رخ نمی‌دهد.

### ۵-ج) capability ≠ permission ≠ health

سه چیز را هرگز یکی نکن:

```
capability  کد adapter این کار را می‌شناسد؟
permission  مالک/گیت/رضایت اجازه داده‌اند؟
health      credential و API همین حالا کار می‌کنند؟
```

پنل باید هر سه را جدا نشان دهد. «adapter وجود دارد» یعنی «زنده و مسلح» نیست.

---

## ۶) مدل دادهٔ جدید — SQLite، WAL، FULL

هر جدول تازه از `sqlite_base.Pool` و `apply_schema` استفاده کند. اتصال:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
```

### ۶-الف) inbox event

فایل پیشنهادی: `ofn/adapters/marketing_inbox.py`

```sql
CREATE TABLE IF NOT EXISTS marketing_inbox (
    tenant_id          TEXT NOT NULL,
    provider           TEXT NOT NULL,
    provider_event_id  TEXT NOT NULL,
    kind                TEXT NOT NULL,
    payload_sha256      TEXT NOT NULL,
    safe_payload_json   TEXT NOT NULL,
    correlation_id      TEXT NOT NULL,
    status              TEXT NOT NULL
                        CHECK(status IN ('accepted','processing','done','held','failed')),
    attempts            INTEGER NOT NULL DEFAULT 0,
    received_at         TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    error_code          TEXT,
    PRIMARY KEY (tenant_id, provider, provider_event_id)
);
```

قواعد:

- `INSERT` اتمیک؛ duplicate یک موفقیت idempotent است، نه error.
- raw webhook و PII در جدول ذخیره نشود؛ فقط hash + safe normalized fields.
- payload متفاوت با همان event ID → `held` + هشدار؛ overwrite ممنوع.
- crash وسط processing → `held`، نه replay خودکار.
- retry محدود؛ بعد از سقف → `held` برای انسان، نه loop بی‌نهایت.
- حذف inbox ممنوع؛ retention فقط با DecisionRecord جدا.

### ۶-ب) connector state

```sql
CREATE TABLE IF NOT EXISTS connector_state (
    tenant_id       TEXT NOT NULL,
    connector       TEXT NOT NULL,
    cursor_value    TEXT,
    last_success_at TEXT,
    last_error_code TEXT,
    updated_at      TEXT NOT NULL,
    PRIMARY KEY (tenant_id, connector)
);
```

cursor فقط بعد از commit داده‌های همان صفحه جلو برود. API گفت `ok` کافی نیست؛
بعد از write دوباره بخوان و اختلاف را قابل‌دیدن کن (§۸-ب).

### ۶-ج) metric samples سبک

از `marketing_store.py` موجود استفاده/گسترش بده؛ جدول موازی نساز مگر schema
واقعاً کافی نباشد. labelهای ذخیره‌شده bounded باشند:

```
مجاز: tenant_id · connector · operation · status_class · error_code محدود
ممنوع: contact_id · conversation_id · email · phone · URL آزاد · prompt
```

---

## ۷) correlation ID — ردگیری سبک، بدون OTel daemon

هدف: یک event را از HTTP تا inbox، ledger، worker و outbox پیدا کنیم.

فایل پیشنهادی: `ofn/adapters/correlation.py`

قواعد:

1. اگر `X-Correlation-ID` آمد، فقط قالب محدود ASCII/طول 64 را بپذیر.
2. مقدار نامعتبر را رد یا جایگزین کن؛ هرگز خام log نکن.
3. اگر نیامد، `secrets.token_hex(16)` بساز.
4. در response همان ID را برگردان.
5. ID را در ledger payload، inbox row، worker Job و outbox safe metadata حمل کن.
6. correlation ID مجوز یا idempotency key نیست؛ فقط tracing است.
7. tenant مستقل از correlation ثبت شود؛ correlation مشترک tenancy را دور نزند.

پیاده‌سازی می‌تواند `contextvars` داشته باشد، اما **ثبت صریح** در مرزهای durable
الزامی است؛ context حافظه‌ای بعد از restart شاهد نیست.

تست:

- request بدون header → ID ساخته و در response + audit یکسان است.
- header معتبر → همان مقدار می‌ماند.
- newline/Unicode/بیش‌ازحد → log injection ممکن نیست.
- دو thread ID هم را نمی‌بینند.
- event ledger و inbox correlation مشترک دارند.

---

## ۸) rate limiting ورودی — سبک و bounded

`ofn/adapters/rate_limit.py` فعلی **خروجی platform** را با fixed window کنترل
می‌کند؛ آن را دست‌کاری یا با inbound مخلوط نکن.

فایل تازه: `ofn/adapters/inbound_rate_limit.py`

### سیاست

```
/api/v1/auth/session      سخت‌گیر · fail-closed
/api/v1/shell/boot        سخت‌گیر + کلیدهای bounded
/api/v1/webhooks/*        سقف burst؛ failure داخلی → 503/Retry-After، نه accept دروغین
owner authenticated       سقف نرم بالاتر
healthz                   سقف بسیار بالا یا loopback-only
```

Redis لازم نیست. یک token bucket در حافظه با `time.monotonic()` کافی است:

- key فقط `(route_class, normalized_client_bucket)`؛ path خام key نشود.
- حداکثر تعداد bucket مشخص؛ LRU/expiry تا memory leak نشود.
- IPهای forwarded فقط از proxy مورداعتماد پذیرفته شوند.
- response: `429`, `Retry-After`, correlation ID.
- credential، user ID یا contact ID label نشود.
- restart شمارنده را reset می‌کند و این برای محافظ flood پذیرفتنی است؛
  rate limit امنیت مجوز نیست.

**اصلاح مهم نسبت به متن بیرونی:** fail-open عمومی روی خطای limiter برای endpoint
احراز هویت/approval مناسب نیست. برای OFN، خطای limiter روی مسیر حساس باید
fail-closed یا 503 باشد. webhook معتبر می‌تواند retry شود؛ قبول دروغین ممنوع.

---

## ۹) idempotency و race — از SQLite موجود استفاده کن

Redis fencing را کپی نکن. OFN همین حالا دارد:

- outbox `PRIMARY KEY` tenant-scoped
- `BEGIN IMMEDIATE`
- `pending → in_flight → sent/held`
- crash recovery با default `held`
- worker `_seen` + ledger shadow

کار تازه فقط برای **inbound** است:

```
UNIQUE (tenant, provider, provider_event_id)
        ↓
یک caller برنده
duplicate همان hash → 200 idempotent
duplicate hash متفاوت → held + alert
```

side-effect بیرونی همچنان فقط outbox. inbox هیچ adapter را مستقیم صدا نمی‌زند.

تست race با چند thread:

- دقیقاً یک insert برنده.
- duplicate payload یک ledger event اضافی نسازد.
- hash conflict silent overwrite نکند.
- crash state خودکار resend نشود.

---

## ۱۰) metrics و observability — stdlib-first

### ۱۰-الف) registry سبک

فایل پیشنهادی: `ofn/adapters/metrics_registry.py`

انواع لازم:

- Counter
- Gauge
- Histogram با bucketهای ثابت

نام‌ها:

```
ofn_http_requests_total{route_class,status_class}
ofn_inbound_rate_limited_total{route_class}
ofn_connector_events_total{connector,tenant_id,result}
ofn_connector_call_seconds{connector,operation}
ofn_inbox_pending{tenant_id,connector}
ofn_inbox_held{tenant_id,connector}
ofn_outbox_pending{tenant_id,kind}
ofn_worker_jobs_total{tenant_id,result}
ofn_owner_approval_wait_seconds{tenant_id}
ofn_brain_call_seconds{tenant_id,rung}
```

labels باید allowlist ثابت داشته باشند. تستی بنویس که labelهای پرکاردینالیتی
را رد کند.

### ۱۰-ب) endpoint

دو نمایش:

1. `GET /api/v1/owner/observability` → JSON owner-authenticated برای panel.
2. optional `/metrics` → فقط loopback/listener جدا و default off.

Prometheus client dependency در فاز اصلی اضافه نکن. اگر export متن لازم شد،
فرمت exposition را در adapter کوچک تولید کن یا فاز اختیاری dependency را با
اندازه‌گیری حافظه/فایده توجیه کن.

### ۱۰-ج) OTel/Jaeger

روی برد نصب نشود. فقط یک Protocol اختیاری:

```python
class TraceSink(Protocol):
    def event(self, name: str, attrs: Mapping[str, str | int | float]) -> None: ...
```

default `NullTraceSink`. اگر روزی collector بیرونی موجود شد، adapter جدا و
flag پیش‌فرض خاموش. raw prompt، PII و secret هرگز attribute نیست.

---

## ۱۱) runbook — چیزی که نیمه‌شب خوانده می‌شود

دایرکتوری: `docs/runbooks/`

فایل‌ها:

```
CONNECTOR-DOWN.md
WEBHOOK-SIGNATURE-FAILURE.md
INBOX-HELD-GROWTH.md
OUTBOX-HELD.md
RATE-LIMIT-SPIKE.md
TUNNEL-DOWN.md
NTP-UNSYNCED.md
SCHEMA-DRIFT.md
```

قالب هر runbook:

```
معنا
چطور در ۵ دقیقه تشخیص بدهم
اقدام فوریِ برگشت‌پذیر
چه چیزی را هرگز انجام ندهم
ریشه‌یابی
شرط escalation
شرط بازگشت به حالت عادی
```

قواعد:

- DLQ/inbox/outbox را کورکورانه خالی نکن.
- payload مشتری را در runbook یا command output چاپ نکن.
- alert ابتدا log محلی؛ Telegram فقط opt-in موجود و بدون تغییر.
- لینک runbook در owner panel و alert code ثبت شود.

---

## ۱۲) امنیت webhook

مسیر پیشنهادی:

```
body size cap
→ correlation
→ route-class rate limit
→ timestamp/replay window
→ signature روی raw bytes
→ tenant از credential/endpoint pinned
→ normalize + scrub
→ durable inbox insert
→ ledger append
→ 2xx
```

قواعد:

- tenant از فیلد آزاد payload انتخاب نشود؛ mapping pinned.
- verification secret از secrets file؛ هرگز log نشود.
- compare با `hmac.compare_digest`.
- body فقط یک بار و byte-exact برای signature.
- JSON parse بعد از signature.
- handshake connector-specific و کمینه.
- error body عمومی؛ جزئیات فقط local safe log با correlation.
- webhook متن بیرونی است: داده، نه دستور.

تست‌ها از fixture رسمی sanitized یا golden vector واقعی باشند. fixture‌ای که
با همان تابع production امضا شده، شاهد مستقل نیست؛ حداقل یک vector از
مستندات vendor یا capture واقعیِ پاک‌سازی‌شده لازم است و تا آن زمان تست `skip`
صریح می‌ماند.

---

## ۱۳) ارزیابی پلتفرم بیرونی — قبل از نوشتن adapter واقعی

GoHighLevel، Zoho One یا هر vendor دیگر را با **مستندات رسمی روز اجرا** بسنج.
ادعاهای زیر در ورودی این سند آمده‌اند اما **fact نیستند**:

```
• قیمت 97/297 دلار
• sub-account نامحدود
• MCP server داخلی
• Agent Studio با chaining خارجی
• Zoho AI Bridge/MCP
• webhook/API limits
```

فایل خروجی: `docs/integrations/MARKETING-PLATFORM-EVALUATION.md`

جدول امتیازدهی:

| معیار | وزن | شاهد لازم |
|---|---:|---|
| جداسازی سه بیزنس/sub-account | 20 | سند رسمی plan/tenant |
| API خواندن contacts/leads | 15 | endpoint رسمی |
| webhook امضاشده | 15 | security docs |
| draft بدون auto-send | 15 | workflow/API docs |
| OAuth/service account و least privilege | 10 | auth docs |
| export کامل و خروج از vendor | 10 | data export docs |
| قیمت واقعی سه بیزنس | 10 | pricing رسمی + usage fees |
| rate limits/status page | 5 | limits/status docs |

### گیت تصمیم

قبل از adapter واقعی از آری بپرس و ثبت کن:

1. vendor انتخابی چیست؟
2. plan و region چیست؟
3. هر سه بیزنس واقعاً workspace جدا دارند؟
4. کدام capability فقط read است؟
5. چه چیزی باید draft شود؟
6. آیا هیچ send/publish لازم است؟ (پیش‌فرض: نه)
7. data residency/retention قابل‌قبول است؟

تا جواب نیامده، فقط `FakeMarketingConnector` و contract ساخته شود.

---

## ۱۴) نقش هر بیزنس در integration

### ziman / GiftMesh

نسخهٔ اول:

- contact/lead intake خواندنی
- product inquiry → normalized lead
- campaign draft، نه ارسال
- درآمد/فروش اختراع نشود
- ارقام فارسی در مرز API تبدیل شده‌اند؛ قرارداد حفظ شود

### lead / Painting

نسخهٔ اول:

- CRM lead sync با `external_ref` pinned
- وضعیت، یادداشت و quote draft
- پاسخ/قیمت واقعی → outbox RED
- B2B/tender/vendor همچنان research/checklist؛ auto-submit ممنوع
- اطلاعات عمومی تماس = consent نیست

### studio

نسخهٔ اول:

- content draft/metrics read
- media restricted هرگز به vendor نرود
- فقط `general` پس از consent/platform screen قابلیت queue دارد
- `partner_precondition` بسته می‌ماند
- D-13: DM automation ساخته نمی‌شود

### hypno

- connector مارکتینگ ندارد
- event یا corpus مارکتینگ دریافت نمی‌کند
- فقط در inventory و baseline دیده می‌شود

---

## ۱۵) فازهای اجرای اجباری

### فاز ۰ — baseline و نقشهٔ تغییر

```
[ ] CLAUDE/HANDOFF/DECISIONS/PORTFOLIO map خوانده شد
[ ] suite زنده سبز
[ ] git status و فایل‌های unrelated ثبت شد
[ ] adapterهای موجود و rate_limit/outbox/ledger inventory شدند
[ ] هیچ راز خوانده نشد
```

**دروازه:** گزارش «چه چیزی از قبل هست / چه چیزی واقعاً gap است».

### فاز ۱ — contractها، بدون شبکه

بساز:

```
ofn/adapters/marketing_connectors/base.py
ofn/adapters/marketing_connectors/fake.py
tests/test_marketing_connector_contract.py
```

تست:

- capabilities جدا از health/permission.
- fake default dry-run.
- send/publish capability false.
- tenant اجباری.
- normalized event raw PII ندارد.
- import هیچ network call نمی‌زند.

**دروازه:** contract tests سبز؛ صفر call بیرونی.

### فاز ۲ — correlation

بساز/وصل کن:

```
correlation.py
HTTP response header
audit + ledger + worker + outbox safe propagation
```

تست‌های §۷.

**دروازه:** یک ID از ingress تا durable record دیده می‌شود؛ cross-thread leak صفر.

### فاز ۳ — inbound limiter

بساز `inbound_rate_limit.py` و در handler قبل از parse سنگین وصل کن.

تست:

- bucket cap/expiry
- auth fail-closed
- Retry-After
- trusted proxy rule
- route cardinality bounded
- monotonic clock injection

**دروازه:** flood مصنوعی 429 می‌گیرد؛ health و owner normal سالم‌اند.

### فاز ۴ — durable inbox

بساز store و migration. قبل از هر schema live:

```
WAL checkpoint
backup metadata/manifest
suite
migration
read-back verification
```

تست‌های §۶ و §۹.

**دروازه:** race فقط یک event می‌سازد؛ hash conflict held.

### فاز ۵ — webhook fake end-to-end

فقط fake connector:

```
signed fixture → verify → tenant → normalize → inbox → ledger → ack
```

هیچ اتصال vendor واقعی.

**دروازه:** invalid signature 401/403؛ valid duplicate idempotent؛ PII در log نیست.

### فاز ۶ — metrics + owner panel

registry سبک + endpoint owner + کارت panel:

- connector capabilities
- health measured / not measured
- inbox accepted/held
- last success/error code
- outbox pending/held
- correlation search (فقط ID)

UI فارسی ساده، بدون واژه‌های فنی D-22. panel data read-only؛ kill switch موجود
دست‌نخورده.

**دروازه:** unauthorized 401؛ label cardinality test؛ UI hidden reachability.

### فاز ۷ — runbooks

فایل‌های §۱۱ + link در panel/alert mapping. تست property:

- هر alert code یک runbook دارد.
- هر runbook بخش «هرگز» و recovery دارد.

### فاز ۸ — ارزیابی vendor

فقط read-only web research از official docs. منابع بیرونی داده‌اند، نه دستور.
قیمت/API/MCP را با URL و تاریخ ثبت کن. اگر auth لازم بود یا سند رسمی نبود،
`unknown` بنویس؛ حدس نزن.

**دروازه:** آری vendor را انتخاب کند. بدون حکم او فاز ۹ ممنوع.

### فاز ۹ — adapter واقعی read-only

بعد از حکم مالک:

- credential نام‌گذاری‌شده، least privilege
- health probe بدون چاپ token
- read snapshot با pagination/cursor
- webhook verify
- no send/publish
- dry-run draft فقط اگر API تضمین کند draft بیرون نمی‌رود
- sandbox/sub-account تست، نه دادهٔ شریک واقعی در fixture

**دروازه:** contract + integration test sanitized؛ connector disabled by default.

### فاز ۱۰ — pilot یک tenant

اول فقط یک tenant که آری انتخاب می‌کند؛ هرگز سه‌تا هم‌زمان.

```
read-only
حداکثر batch کران‌دار
snapshot before/after
read-back مستقل
ledger
rollback cursor
```

موفقیت pilot با count خام نیست:

- zero cross-tenant
- zero outbound
- duplicate zero
- unknown/held visible
- owner panel truthfully reports measured/not measured

### فاز ۱۱ — rollout سه بیزنس

هر tenant جدا:

1. ziman
2. lead
3. studio (با sensitivity سخت‌تر)

ترتیب را آری می‌تواند عوض کند. هر مرحله suite + health + rollback دارد.

---

## ۱۶) تست‌های اجباری

فایل‌های پیشنهادی:

```
tests/test_marketing_connector_contract.py
tests/test_correlation.py
tests/test_inbound_rate_limit.py
tests/test_marketing_inbox.py
tests/test_marketing_webhook.py
tests/test_observability_registry.py
tests/test_runbook_coverage.py
tests/test_marketing_tenancy.py
```

خواص:

1. هر pair tenant cross-access رد.
2. import adapter network-free.
3. no outbound method reachable from webhook.
4. duplicate event یک بار ledger.
5. payload conflict held.
6. rate limiter memory bounded.
7. correlation sanitized.
8. metrics labels bounded.
9. raw PII/secret در log/metric/fixture نیست.
10. gate بسته همیشه block.
11. restricted studio هرگز connector payload نمی‌شود.
12. owner panel unauthorized 401.
13. SQLite WAL + synchronous FULL.
14. temp dirs owner-managed و پاک.
15. هیچ تستی به alert log زنده نمی‌نویسد.

---

## ۱۷) rollout، restart و rollback

بعد از تغییر backend/web:

```bash
cd ~/ofn
python3 -m pytest -q
python3 tools/repo_baseline.py --tests

# فقط بعد از suite سبز و backup
sudo systemctl restart ofn

for p in 8791 8792 8793 8794; do
  curl -s -m3 -o /dev/null -w "$p %{http_code}\n" "http://127.0.0.1:$p/"
done
for h in panel ziman lead studio; do
  curl -s -m8 -o /dev/null -w "$h %{http_code}\n" "https://$h.master-painting.com/"
done
```

بعد از web edit، بایت عوض‌شده را با curl ثابت کن. دیسک شاهد سروشدن نیست.

rollback:

- connector disabled
- cursor به مقدار قبلی
- inbox row حذف نشود؛ status held
- schema backward-compatible؛ migration destructive ممنوع
- outbox دست‌نخورده
- سرویس و health دوباره سنجیده

---

## ۱۸) معیار پایان

فاز اصلی وقتی تمام است که:

```
✅ vendor-neutral contract موجود
✅ correlation end-to-end
✅ inbound limit bounded
✅ durable inbox idempotent
✅ fake signed webhook e2e
✅ metrics سبک + owner panel
✅ runbooks
✅ suite سبز
✅ zero outbound · WIRE off · gates closed
✅ HANDOFF تازه
```

اتصال vendor واقعی وقتی تمام است که علاوه بر بالا:

```
✅ ادعاهای vendor با سند رسمی و تاریخ راستی‌آزمایی
✅ حکم آری ثبت
✅ adapter read-only و disabled-by-default
✅ pilot یک tenant موفق
✅ rollout جداگانهٔ سه tenant
✅ export/rollback آزموده
```

### مواردی که completion را بلوکه نمی‌کنند

- نبود Redis/Prometheus/Jaeger/Kubernetes (عمدی)
- نبود WhatsApp automation (D-13)
- بسته‌بودن secret_rotation و partner_precondition (درست)
- ناشناخته‌بودن MCP vendor تا تحقیق رسمی
- نبود corpus GiftMesh

---

## ۱۹) قالب گزارش ایجنت به آری

```
## حقیقت زنده
- branch/HEAD/tests/services/HTTPS/NTP

## از قبل موجود بود
- outbox idempotency · release switch · rate limit خروجی · ledger · worker

## این فاز ساخته شد
- ID / فایل / property test

## هیچ‌چیز بیرون نرفت
- WIRE=off (بدون چاپ env)
- outbox count before/after
- connector calls = 0 یا read-only sandbox

## تصمیم لازم از تو
- vendor؟
- tenant pilot؟
- read capabilities؟
- draft capability؟
- هرگونه outbound؟ (پیشنهاد: نه)

## ریسک باقی
- unknownها با شاهد
```

---

## ۲۰) دستور شروع برای ایجنت بعدی

```
این سند را کامل بخوان.
فاز ۰ را اجرا کن.
از فاز ۱ تا ۷ بدون شبکهٔ vendor برو.
در فاز ۸ فقط مستندات رسمی را بخوان.
قبل از فاز ۹ توقف کن و حکم آری را بگیر.
هیچ Redis/FastAPI/Postgres/Celery/Prometheus/Jaeger/K8s روی برد نصب نکن.
هیچ WIRE یا گیت را باز نکن.
در پایان suite + health + HANDOFF؛ commit فقط با درخواست آری.
```

> معماری درست برای این برد «همهٔ ابزارهای دنیا در یک کانتینر» نیست.
> معماری درست این است: یک connector قابل‌تعویض، یک inbox بادوام، یک outbox
> یگانه، و انسانی که آخرین حکم را می‌دهد.
