# Orange Pi Automation Hub — معماری Self-Adaptive نسخه ۱

> **پارادایم:** اکوسیستم زنده، ماژولار، Plug-&-Play، با مغز خودتطبیق‌پذیر.
> **محدودیت سخت:** 4GB RAM روی Orange Pi 5 Plus + ARM64 + Always-on.
> **اصل حاکم:** هیچ تصمیمی استاتیک نیست. هر تسک در لحظه‌ی اجرا توسط مغز سنجیده، پذیرفته، یا کشته می‌شود.

---

## ۱. نمای کلی معماری (سه لایه + یک مغز)

```
┌────────────────────────────────────────────────────────────────────┐
│  EDGE TIER (ESP32 mesh)                                            │
│  • منطق محلی مستقل (هر ESP32 یک ماشین حالت کوچک)                  │
│  • فقط State + Telemetry را Publish می‌کند                         │
│  • LWT (Last Will) برای تشخیص آفلاینی فوری                         │
└──────────────────────────┬─────────────────────────────────────────┘
                           │ MQTT (Mosquitto, QoS 1)
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│  CENTRAL HUB — Orange Pi 5 Plus                                    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  BRAIN / CONDUCTOR  (سرویس Go یا Python-asyncio)              │  │
│  │  • Resource Ledger زنده (RAM/CPU/Temp/IO هر ۲ ثانیه)         │  │
│  │  • Admission Controller (قبل از start هر تسک)                │  │
│  │  • Eviction Loop (هر ۵ ثانیه)                                 │  │
│  │  • Policy Engine (قوانین JSON قابل ویرایش زنده)              │  │
│  │  • Utility Scorer (تسک «بی‌فایده» را تشخیص می‌دهد)            │  │
│  └────────────────┬─────────────────────────────────────────────┘  │
│                   │ HTTP API + gRPC                                │
│                   ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ORCHESTRATOR — HashiCorp Nomad (single binary, ~180MB)      │  │
│  │  • زمان‌بند با Priority + Preemption                          │  │
│  │  • Driver: docker + exec + raw_exec                          │  │
│  │  • Reschedule + Restart policies                             │  │
│  └────────────────┬─────────────────────────────────────────────┘  │
│                   │                                                │
│                   ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  WORKER TIER — کانتینرهای کوتاه‌عمر یا پایدار                │  │
│  │  Slot XS / S / M / L / XL (هر اسلات سقف RAM ثابت)            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────── State & Messaging Plane ──────────────────────┐    │
│  │  PostgreSQL 16 + TimescaleDB  (registry + history)         │    │
│  │  Redis 7 (hot state, locks, leases)                        │    │
│  │  NATS JetStream (work queue با persistence)                │    │
│  │  Mosquitto (MQTT برای ESP32)                               │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘
```

---

## ۲. چرا Nomad و نه Docker Compose / K3s

| گزینه | RAM Overhead | پشتیبانی ARM64 | Resource-Aware Scheduling | Preemption | حکم |
|---|---|---|---|---|---|
| Docker Compose | ~0 | ✓ | ✗ استاتیک | ✗ | ضعیف — معماری زنده نمی‌سازد |
| K3s (Kubernetes) | 500–900MB | ✓ | ✓ | ✓ | با 4GB RAM گران است |
| **Nomad** | **150–250MB** | ✓ (single binary) | ✓ | ✓ | **انتخاب** |
| Custom Python | متغیر | ✓ | ✓ | با کد | بازاختراع چرخ |

**Nomad** تک‌فایل است، Drift ندارد، Job Spec با HCL ساده، و دقیقاً همان قابلیت‌هایی را که می‌خواهیم (priority، preemption، constraint، resource isolation) به‌صورت Native دارد. مغز ما فقط با Nomad API صحبت می‌کند.

---

## ۳. لایه پیام و صف — چه چیزی، کجا؟

| نوع ترافیک | تکنولوژی | چرا |
|---|---|---|
| تله‌متری ESP32، فرمان به Edge | **MQTT (Mosquitto)** | سبک، LWT، QoS، Retained |
| صف کار بین تسک‌ها، Resume queue | **NATS JetStream** (~30MB) | Persistent، exactly-once، subject hierarchy |
| State داغ، Lock، Lease، Counter | **Redis 7** (~40MB، maxmemory 128MB با LRU) | سرعت + TTL |
| Registry تسک‌ها، تاریخچه، Checkpointها | **PostgreSQL 16 + TimescaleDB** (~200MB) | Schema قوی، Time-series برای متریک |

**چرا نه Redis تنها؟** چون Redis در RAM است؛ با 4GB رم نمی‌توان همه‌چیز را آنجا گذاشت. هر چیزی که باید Resume را تضمین کند → Postgres/JetStream (روی SSD). هر چیزی Transient → Redis.

---

## ۴. ساختار دیتابیس — طراحی برای Plug-&-Play روزانه

اصل: **هر تسک یک رکورد در `task_definitions` است.** اضافه کردن تسک جدید = یک INSERT، نه deploy جدید.

```sql
-- 4.1 — Definition Layer (Blueprint)
CREATE TABLE task_definitions (
    id              UUID PRIMARY KEY,
    slug            TEXT UNIQUE NOT NULL,         -- "scraper.tgju.gold"
    version         INT DEFAULT 1,
    kind            TEXT NOT NULL,                -- 'scraper' | 'bot' | 'robot' | 'ml' | ...
    runtime         TEXT NOT NULL,                -- 'docker' | 'exec' | 'esp32'
    image           TEXT,                         -- ghcr.io/me/scraper:1.2
    command         TEXT[],
    env             JSONB DEFAULT '{}',
    
    -- Resource Profile
    slot_class      TEXT NOT NULL,                -- 'XS'|'S'|'M'|'L'|'XL'
    ram_mb_request  INT NOT NULL,
    ram_mb_limit    INT NOT NULL,                 -- مغز با این عدد kill می‌کند
    cpu_shares      INT DEFAULT 256,
    
    -- Scheduling
    schedule_kind   TEXT NOT NULL,                -- 'cron'|'interval'|'event'|'on_demand'|'always_on'
    schedule_expr   TEXT,                         -- '*/15 * * * *' یا 'mqtt:sensor/door/open'
    priority        INT DEFAULT 50,               -- 0–100
    max_concurrent  INT DEFAULT 1,
    
    -- Resilience Policy (JSONB → ویرایش زنده)
    policy          JSONB NOT NULL DEFAULT '{
        "max_runtime_sec": 1800,
        "retry": {"max": 5, "backoff": "exponential", "base_sec": 30},
        "kill_on_ram_over_pct": 120,
        "kill_on_useless_runs": 5,
        "checkpoint_every_sec": 60
    }',
    
    -- Utility Scoring (تشخیص بی‌فایده بودن)
    utility_metric  TEXT,                         -- مثلاً 'rows_inserted' یا 'msgs_published'
    utility_min     NUMERIC DEFAULT 0,            -- زیر این مقدار = بی‌فایده
    
    enabled         BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- 4.2 — Runtime Layer
CREATE TABLE task_runs (
    id              UUID PRIMARY KEY,
    definition_id   UUID REFERENCES task_definitions(id),
    nomad_alloc_id  TEXT,
    state           TEXT NOT NULL,                -- pending|admitted|running|checkpointing|done|failed|evicted|useless_killed
    reason          TEXT,
    
    started_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,
    attempt         INT DEFAULT 1,
    
    ram_peak_mb     INT,
    cpu_secs        NUMERIC,
    exit_code       INT,
    utility_value   NUMERIC,                      -- مغز برای امتیازدهی استفاده می‌کند
    
    parent_run_id   UUID REFERENCES task_runs(id) -- chain برای Retry/Resume
);
CREATE INDEX ON task_runs (definition_id, started_at DESC);

-- 4.3 — Checkpointing (قلب Resume)
CREATE TABLE task_checkpoints (
    run_id          UUID REFERENCES task_runs(id) ON DELETE CASCADE,
    seq             INT,
    state_blob      JSONB NOT NULL,               -- هر چیزی که برای ادامه کافی است
    ts              TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (run_id, seq)
);

-- 4.4 — Telemetry (TimescaleDB hypertable)
CREATE TABLE task_metrics (
    ts              TIMESTAMPTZ NOT NULL,
    run_id          UUID,
    ram_mb          INT,
    cpu_pct         NUMERIC,
    extra           JSONB
);
SELECT create_hypertable('task_metrics', 'ts');
SELECT add_retention_policy('task_metrics', INTERVAL '14 days');

-- 4.5 — Resource Ledger Snapshot (مغز هر ۲s آپدیت می‌کند)
CREATE TABLE host_state (
    ts              TIMESTAMPTZ PRIMARY KEY,
    ram_free_mb     INT,
    ram_avail_mb    INT,
    cpu_load_1m     NUMERIC,
    soc_temp_c      NUMERIC,
    swap_used_mb    INT,
    slots_in_use    JSONB                         -- {"XS":3,"S":2,"M":1,"L":0,"XL":0}
);

-- 4.6 — Policies (قوانین زنده، بدون redeploy قابل ویرایش)
CREATE TABLE policies (
    name            TEXT PRIMARY KEY,
    rule            JSONB NOT NULL,               -- DSL ساده
    enabled         BOOLEAN DEFAULT TRUE
);
-- مثال:
-- INSERT INTO policies VALUES (
--   'emergency_thermal',
--   '{"when":"soc_temp_c > 78","then":"kill lowest_priority where slot_class in (L,XL)"}',
--   true
-- );
```

**نکته کلیدی:** اضافه کردن تسک جدید روزانه = یک INSERT در `task_definitions`. مغز با inotify/LISTEN روی Postgres تغییرات را می‌گیرد و بلافاصله در حلقه برنامه‌ریزی لحاظ می‌کند. **هیچ کدی redeploy نمی‌شود.**

---

## ۵. سیستم Slot — مهار رم با هندسه‌ی ثابت

به‌جای اینکه به Linux scheduler اعتماد کنیم، **اسلات** تعریف می‌کنیم:

| Slot | RAM Limit | Cap همزمان | کاربرد |
|---|---|---|---|
| XS | 128 MB | 8 | Ping، Cron ساده، MQTT bridge |
| S | 256 MB | 4 | Telegram bot، API poller، SQLite |
| M | 512 MB | 2 | اسکریپر سبک، پردازشگر داده |
| L | 1024 MB | 1 | Playwright، headless chrome |
| XL | 1500 MB | 1 (انحصاری) | ML inference، تحلیل سنگین |

قانون عبور: **Σ(slots_used × ram_limit) ≤ 2600 MB.** بقیه برای OS، Postgres، Redis، Nomad، Mosquitto، NATS، Brain ذخیره می‌شود. مغز قبل از admission این جمع را چک می‌کند.

---

## ۶. مغز / Conductor — منطق هسته

**زبان پیشنهادی:** Go (~20MB RAM، latency پایین). اگر می‌خواهی سریع‌تر شروع کنی، Python+asyncio (~80MB) قابل قبول است.

### ۶.۱ — حلقه‌های موازی

```
┌─ Sensor Loop (2s) ─────────────────────────┐
│  cgroup stats + /proc/meminfo + thermal     │
│  → INSERT host_state                        │
│  → UPDATE redis: host:current                │
└────────────────────────────────────────────┘

┌─ Admission Loop (event-driven) ────────────┐
│  وقتی Nomad می‌خواهد job جدید start کند:    │
│   1. اسلات کافی هست؟                        │
│   2. ram_free > limit*1.3 ?                  │
│   3. soc_temp < 75°C ?                       │
│   4. policies را اعمال کن                    │
│   5. allow / deny / queue                    │
└────────────────────────────────────────────┘

┌─ Eviction Loop (5s) ───────────────────────┐
│  هر run در حال اجرا را بسنج:                │
│   • ram > limit*1.2 برای >30s → KILL hard   │
│   • cpu_pct > 95% و runtime > expected*3    │
│   • utility_value < utility_min در آخرین    │
│     N run متوالی → useless_killed            │
│   • soc_temp > 80°C → kill پایین‌ترین prio │
└────────────────────────────────────────────┘

┌─ Replanner Loop (10s) ─────────────────────┐
│  صف pending را بر اساس priority + age      │
│  مرتب کن، به Nomad submit کن                │
└────────────────────────────────────────────┘

┌─ Policy Watcher ───────────────────────────┐
│  Postgres LISTEN/NOTIFY روی policies        │
│  هر تغییر بلافاصله reload می‌شود            │
└────────────────────────────────────────────┘
```

### ۶.۲ — تشخیص «بی‌فایدگی» (مهم‌ترین تفاوت با سیستم استاتیک)

هر تسک یک `utility_metric` تعریف می‌کند (مثلاً تعداد ردیف جدید درج‌شده، تعداد سیگنال موفق، تعداد پیام منتشرشده). تسک در checkpoint مقدار را در `task_runs.utility_value` می‌نویسد. مغز:

```
window = last N runs (e.g., 10)
if median(utility_value) < utility_min:
    → mark definition.enabled = false
    → emit alert "useless: <slug>"
```

این منطق دقیقاً پاسخ نیاز شما به «استراتژی پرریسک/پرسود» است — مغز تسک‌های بی‌بازده را خاموش می‌کند تا منابع برای موفق‌ها آزاد شود.

---

## ۷. Resume/Retry — قرارداد قابل اجرا

هر تسک باید این قرارداد را رعایت کند (SDK کوچک در Python و Go ارائه می‌شود):

```python
from hub_sdk import Task

t = Task.load()                          # checkpoint قبلی را برمی‌گرداند
state = t.checkpoint or {"cursor": 0}

for i in range(state["cursor"], total):
    do_work(i)
    if i % 100 == 0:
        t.checkpoint({"cursor": i, "ts": ...})
        t.report_utility(rows_inserted=i)
t.done()
```

پشت صحنه: SDK به Postgres می‌نویسد (`task_checkpoints`) و به Redis lease می‌دهد. اگر تسک kill شود، instance بعدی با `Task.load()` از همان `cursor` ادامه می‌دهد. **هیچ logic سفارشی برای Resume در خود تسک‌ها نیست.**

---

## ۸. لایه Edge — قرارداد ESP32

هر ESP32 یک ماشین حالت کوچک با:

- **MQTT client با LWT** → topic `edge/{id}/status` با retained payload `{"online":false}` به‌عنوان وصیت
- **Heartbeat** هر 10s
- **State buffering** روی LittleFS → اگر MQTT قطع شد، تا 1000 رویداد بافر می‌شود
- **OTA endpoint** → مغز می‌تواند firmware push کند

ESP32ها مستقل کار می‌کنند؛ اگر هاب مرکزی down شود، رفتار محلی ادامه دارد. این مرز معماری حیاتی است.

---

## ۹. Plug-&-Play — افزودن تسک جدید در ۳ دقیقه

```bash
# 1. فایل تعریف YAML بساز:
cat > /opt/hub/tasks.d/my_new_scraper.yaml <<EOF
slug: scraper.coingecko.btc
kind: scraper
runtime: docker
image: ghcr.io/me/cg-scraper:1.0
slot_class: S
schedule_kind: interval
schedule_expr: "5m"
priority: 60
utility_metric: rows_inserted
utility_min: 1
policy:
  max_runtime_sec: 240
  kill_on_useless_runs: 6
EOF

# 2. تمام. Brain فایل را inotify می‌بیند، در task_definitions ثبت می‌کند،
#    و در run بعدی scheduler وارد چرخه می‌شود.
```

برای حذف: فایل را پاک کن یا `enabled=false` کن. هیچ restart لازم نیست.

---

## ۱۰. بودجه RAM واقعی (با مالیات OS)

```
Armbian Minimal + kernel        ~250 MB
Docker daemon                   ~120 MB
Nomad agent                     ~200 MB
PostgreSQL (tuned, shared=128M) ~220 MB
Redis (maxmem 128M)              ~50 MB
NATS JetStream                   ~40 MB
Mosquitto                        ~25 MB
Brain (Go)                       ~30 MB
Node exporter + cAdvisor (لازم)  ~80 MB
─────────────────────────────────────────
زیرساخت کل:                    ~1015 MB
بودجه آزاد برای workloads:     ~2600 MB
buffer ایمنی (swap-resist):    ~400 MB
```

این یعنی همیشه فضای ~2.5GB برای تسک‌ها داریم. swap روی SSD (2GB، swappiness=10) فقط شبکه ایمنی است، نه ابزار اصلی.

---

## ۱۱. مسیر استقرار پیشنهادی (فاز‌بندی شده)

**فاز ۰ — پایه (روز ۱–۲):** Armbian + Docker + Mosquitto + Postgres + Redis + NATS + Nomad (single-node).

**فاز ۱ — مغز (روز ۳–۵):** Brain v0: فقط Resource Ledger + Admission ساده + اسکیمای دیتابیس.

**فاز ۲ — Resume SDK (هفته ۲):** SDK Python و Go، یک تسک نمونه با checkpoint.

**فاز ۳ — Policy Engine (هفته ۳):** Eviction Loop + Utility Scorer + Plug-&-Play YAML.

**فاز ۴ — Edge (هفته ۴):** ESP32 SDK، MQTT topology، LWT، OTA.

**فاز ۵ — مشاهده‌پذیری (هفته ۵):** Prometheus + Grafana + هشدار تلگرامی.

**فاز ۶ — Failover (ماه ۲):** Orange Pi دوم به‌عنوان warm standby با Postgres streaming replication + Nomad federation.

**فاز ۷ — VPS Hybrid (اختیاری):** تسک‌های شبکه‌محور (Telegram، API) را روی VPS اجرا کن، Postgres را cross-replicate.

---

## ۱۲. تصمیمات باز که در نسخه ۲ نهایی می‌کنیم

این موارد را عمداً در v1 ساده گذاشتم؛ اگر تأیید کنی، در نسخه بعدی عمیق می‌شوند:

1. **زبان Brain:** Go (پیشنهاد من) یا Python؟
2. **Policy DSL:** JSON ساده با عملگرها (پیشنهاد) یا CEL/Rego؟
3. **Auth بین لایه‌ها:** mTLS داخلی یا فقط shared secret؟
4. **Failover Postgres:** streaming replication روی Pi دوم یا فقط بکاپ logical روزانه به VPS؟

---

**خلاصه فلسفه:** سیستم استاتیک نمی‌سازیم. یک هسته‌ی کوچک و باهوش (Brain ~30MB) می‌سازیم که Nomad را به‌عنوان «بازوی اجرایی» استفاده می‌کند، و تمام رفتار سیستم از داده‌های زنده در Postgres/Redis درمی‌آید. اضافه کردن تسک جدید = INSERT. تغییر سیاست = UPDATE. هیچ redeploy، هیچ downtime.
