# Orange Pi Automation Hub — معماری Hybrid نسخه ۲ (نهایی پایه)

> **فلسفه:** هسته‌ی زیرساختی **سخت و بی‌رحم** (RAM/Thermal/Network/Dedup را با قانون فیزیکی کنترل می‌کند) + لایه‌ی پروژه‌ای **نرم و متغیر** (هر روز اضافه/حذف بدون redeploy).
>
> **زبان اصلی:** Python 3.11+ (asyncio).
> **Runtime کانتینر:** Podman rootless.
> **Orchestrator:** Nomad (تک‌بایناری) + Brain سفارشی.
> **پلت‌فرم صف:** Redis 7 (RQ + Streams).
> **حالت پایدار:** PostgreSQL 16 + SQLite per-task.

---

## ۱. توپولوژی نهایی

```
┌────────────────────────────────────────────────────────────────────┐
│  EDGE — ESP32 mesh (دوطرفه: sensor + actuator)                     │
│  • Firmware با LWT + heartbeat هر 10s                              │
│  • LittleFS buffer برای 1000 رویداد آفلاین                          │
│  • OTA فعلاً نه — آپدیت دستی USB                                   │
└──────────────────────────┬─────────────────────────────────────────┘
                           │ MQTT (Mosquitto با persistence)
                           ▼
┌──── CENTRAL HUB ─ Orange Pi 5 Plus (4GB) ──────────────────────────┐
│                                                                    │
│  ┌── Infrastructure Plane (سخت، ثابت، systemd) ─────────────────┐  │
│  │  PostgreSQL 16   │  Redis 7 (AOF)  │  Mosquitto  │  Nomad    │  │
│  │  (registry+state)│  (queues+locks) │  (MQTT)     │  (run)    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌── Control Plane (Python asyncio) ────────────────────────────┐  │
│  │  BRAIN     │  TG-OPS  │  SCHEDULER │  HEALTHD  │  DEFINITION │  │
│  │  (admit/   │  (telegram│  (cron/    │  (thermal/│  WATCHER    │  │
│  │  evict/    │  bot)    │  interval) │  net/disk)│  (inotify   │  │
│  │  utility)  │          │            │           │  + LISTEN)  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌── Workload Plane (Podman containers via Nomad) ──────────────┐  │
│  │  RQ Workers │ Browser-as-a-Service │ Project Tasks (XS..XL)  │  │
│  │  (per slot) │ (Playwright pool=1)  │ (ephemeral, idempotent) │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬─────────────────────────────────────────┘
                           │ WireGuard
                           ▼
┌────────── VPS ($10/mo) ─ سه نقش هم‌زمان ──────────────────────────┐
│  ① Postgres logical replica (hot standby)                          │
│  ② Restic repository (off-site backup روزانه)                      │
│  ③ Satellite Brain (compute offload با تگ prefer_vps=true)         │
└────────────────────────────────────────────────────────────────────┘
```

---

## ۲. تصمیمات پشته‌ی نهایی (با چرایی)

| لایه | انتخاب نهایی | چرا این و نه دیگری |
|---|---|---|
| Container Runtime | **Podman rootless** | بدون daemon (~50MB کمتر از Docker)، سازگار با OCI، compose سازگار، امن‌تر |
| Orchestrator | **Nomad** + Brain | Compose استاتیک است؛ K3s گران (>500MB)؛ Nomad تک‌بایناری 180MB با preemption native |
| Queue | **Redis 7 + RQ** | Python-native، AOF برای persistence، RQ ساده‌تر از Celery (~30MB کمتر)، با Streams برای fan-out |
| State DB | **PostgreSQL 16 + TimescaleDB** | Schema قوی، LISTEN/NOTIFY برای reactive، replication آماده برای VPS |
| Per-task local | **SQLite (WAL)** | به‌ازای هر پروژه یک فایل روی SSD — Resume محلی بدون فشار به Postgres |
| Lock/Lease/Cache | **Redis** (maxmem 192MB با LRU) | TTL native، SETNX برای dedup فوری |
| MQTT | **Mosquitto** با `persistence true` | استاندارد ESP32، LWT، Retained |
| Brain زبان | **Python 3.11 + asyncio + uvloop** | همخوانی با اکوسیستم پروژه‌ها، SDK مشترک |
| Browser pool | **Playwright + سرویس FastAPI داخلی** | یک نمونه Chromium مشترک پشت صف |
| Monitoring | **Telegram-Ops Bot** + Prometheus داخلی | بدون Grafana سنگین، فقط alert + متریک خام |
| VPN to VPS | **WireGuard** | ~5MB، سریع، رمزگذاری native |

---

## ۳. Browser-as-a-Service (B-a-a-S) — یکتایی الزامی

**مسئله:** هر Playwright instance حدود 700–1200MB می‌خورد. اگر ۳ پروژه همزمان مرورگر باز کنند → OOM.

**راه‌حل:** یک سرویس مرکزی، یک Chromium، چندین context، صف سراسری.

```
                  ┌────────────────────────────────┐
   Job A ──RQ────▶│  baas-service (FastAPI)        │
   Job B ──RQ────▶│  ┌──────────────────────────┐  │
   Job C ──RQ────▶│  │  Playwright single browser│  │
                  │  │  max_contexts = 3        │  │
                  │  │  recycle every 100 jobs  │  │
                  │  │  or after 60min runtime  │  │
                  │  └──────────────────────────┘  │
                  │  Queue: baas.queue (Redis)     │
                  │  Lease lock: baas:lock:{ctx}   │
                  │  Slot class: L (1024MB)        │
                  └────────────────────────────────┘
```

**قرارداد API:**

```python
POST /scrape  { url, actions:[...], wait:"networkidle", timeout:30 }
→ 200 { html, screenshot_path, cookies, har? }
→ 429 { retry_after: 12 }   # صف پر است
→ 408 { reason: "timeout"}  # job در صف پیر شد (>60s)
```

**قوانین مغز برای B-a-a-S:**
- اگر `ram_used > 1100MB` → recycle browser پس از پایان job جاری
- اگر صف > 20 درخواست → reject 429 (پروژه‌ها backoff می‌کنند)
- اگر `crash_count` در 10 دقیقه > 3 → restart کامل سرویس + alert تله‌گرام

---

## ۴. Deduplication — قرارداد «هیچ تسکی دوبار اجرا نمی‌شود»

اولویت شما در سطح Job. سه لایه دفاع:

```python
# لایه ۱ — Idempotency key بر اساس محتوا
key = sha256(f"{definition_slug}|{scheduled_ts}|{json.dumps(args, sort_keys=True)}")

# لایه ۲ — چک سریع در Redis (atomic)
if not redis.set(f"job:lock:{key}", run_id, nx=True, ex=86400):
    return ALREADY_RAN  # کسی دیگر این job را گرفته

# لایه ۳ — UNIQUE در Postgres (تضمین نهایی، حتی پس از پاک شدن Redis)
INSERT INTO task_runs (id, idempotency_key, ...)
VALUES (...)
ON CONFLICT (idempotency_key) DO NOTHING
RETURNING id;
```

اسکیمای مرتبط (اضافه به v1):

```sql
ALTER TABLE task_runs
    ADD COLUMN idempotency_key TEXT,
    ADD CONSTRAINT uniq_idem UNIQUE (idempotency_key);
CREATE INDEX ON task_runs (idempotency_key);
```

**سناریوی قطع برق وسط اجرا:** worker شروع کرده، redis lock دارد، Postgres run insert شده با state=`running`. برق قطع می‌شود. هنگام boot:
1. `recovery_worker` در Brain اجرا می‌شود
2. هر run با `state=running` و `last_heartbeat < now() - 60s` را پیدا می‌کند
3. اگر `policy.resume_on_recovery=true` → state را `pending` می‌کند و آخرین checkpoint را لود می‌کند (`task_checkpoints` آخرین seq)
4. اگر نه → state را `failed` با reason=`power_loss` می‌کند
5. Redis lock همان `idempotency_key` پاک می‌شود تا re-enqueue ممکن شود

---

## ۵. ساختار صف — RQ + Redis Streams

**چرا دو مکانیزم؟**

- **RQ:** صف کار اصلی (Job dispatch به worker). ساده، Python-native، failure handling خوب.
- **Redis Streams:** بافر تله‌متری ESP32 → workers (consumer group، delivery تضمینی).

```
Topology:
  q:slot:xs ─┐
  q:slot:s  ─┼─▶ RQ Workers (هر slot یک worker dedicated)
  q:slot:m  ─┤
  q:slot:l  ─┤
  q:slot:xl ─┘

  q:baas    ─▶ Browser service worker
  q:retry   ─▶ Brain (decision: requeue/dead/escalate)

  stream:edge:telemetry  ─▶ ingest consumer group
  stream:edge:commands   ─▶ MQTT bridge
```

**پایداری در قطع برق:**
- Redis با `appendonly yes` و `appendfsync everysec` → حداکثر 1 ثانیه گم می‌شود
- RQ jobs در حال انجام در `started_jobs` registry → recovery_worker دوباره enqueue می‌کند
- Postgres همیشه منبع حقیقت برای state — Redis فقط hot cache است

---

## ۶. Definition Watcher — Plug-&-Play واقعی

دو منبع برای تعریف تسک، هر دو معتبر:

```
/opt/hub/tasks.d/*.yaml          ← انسانی، با inotify
PostgreSQL task_definitions       ← API/Telegram، با LISTEN/NOTIFY
```

سرویس `defwatcher`:
1. در startup همه‌ی YAMLها را parse می‌کند و با Postgres sync می‌کند
2. inotify watch روی `tasks.d/` — هر تغییر فایل → upsert/disable
3. Postgres LISTEN روی channel `definition_changed` → reload در حافظه
4. Scheduler هر 30s `enabled=true` تعاریف را برای cron/interval check می‌کند

**نتیجه:** اضافه کردن تسک = `vim tasks.d/new.yaml` یا API call. هیچ restart.

---

## ۷. Telegram-Ops Bot — مانیتورینگ + کنترل

**سرویس `tg-ops` (Python aiogram، ~40MB):**

```
دستورات کاربر (whitelisted user IDs):
  /status              → خلاصه RAM/CPU/temp/slots/queue
  /tasks               → لیست تعاریف فعال + last_run + utility
  /run <slug>          → اجرای فوری
  /kill <run_id>       → kill اجباری
  /pause <slug>        → غیرفعال تعریف
  /resume <slug>       → فعال‌سازی
  /logs <run_id> 50    → آخرین ۵۰ خط
  /metrics             → نمودار ASCII رم ۲۴h

Alerts خودکار (Brain push):
  🔥 thermal: SoC > 78°C
  💀 OOM kill: <slug> run <id>
  🪦 useless: <slug> N run بی‌بازده — disabled
  🔌 esp32-offline: <device_id> > 60s
  📉 disk > 85%
  🔁 power_loss_recovery: N runs resumed
```

**چرا تله‌گرام و نه Grafana؟** Grafana >250MB در حالت بیکار. تله‌گرام alert push است و queryهای ad-hoc با bot رایگان است. Prometheus داخلی برای متریک scrape ماند، فقط Grafana را حذف می‌کنیم.

---

## ۸. VPS — سه نقش هم‌زمان

VPS با 1GB RAM (در محدوده ۱۰ دلار). توپولوژی:

```
┌─ VPS ($10/mo) ────────────────────────────────────────────┐
│                                                            │
│  WireGuard ←──── tunnel ────→ Orange Pi                    │
│                                                            │
│  ① Postgres replica (logical replication، subscriber)      │
│     - تأخیر < 5s                                           │
│     - read-only، برای fallback و backup logical            │
│                                                            │
│  ② Restic repository                                       │
│     - بکاپ روزانه: Postgres dump + /opt/hub/tasks.d        │
│     + /opt/hub/state (SQLite per-task)                     │
│     - 30 day retention، dedup + encryption                 │
│                                                            │
│  ③ Satellite Brain (سبک، فقط worker mode)                  │
│     - تسک‌های با `prefer_vps: true` (مثل: تماس API بانک)   │
│     - یا وقتی Orange Pi تحت فشار است (RAM > 85%):          │
│       Brain یک replan می‌کند و L/XL را به VPS push می‌کند  │
└────────────────────────────────────────────────────────────┘
```

**Failover سناریو:** اگر Orange Pi کاملاً down شود، VPS:
- Postgres replica را به primary promote می‌کند
- Telegram bot را که روی VPS هم نصب است فعال می‌کند
- فقط تسک‌های critical را اجرا می‌کند (تگ‌شده)
- پس از بازگشت Orange Pi، sync دوطرفه با conflict resolution `last_write_wins`

---

## ۹. ماتریس بقای قطع برق (Power-Loss Survival)

| داده/وضعیت | کجا persist می‌شود | حداکثر گم‌شدنی | بازیابی |
|---|---|---|---|
| تعاریف تسک | Postgres + YAML | ۰ | خودکار از replica/disk |
| Run state (in-flight) | Postgres `task_runs` | ۰ (synchronous_commit) | recovery_worker → resume |
| Checkpoint | Postgres `task_checkpoints` | تا 1 checkpoint | از seq آخر |
| Queue (RQ) | Redis AOF | ≤ 1 ثانیه | RQ registries reload |
| Lock (Redis) | Redis AOF | ≤ 1 ثانیه | TTL خودکار + dedup در Postgres |
| تله‌متری ESP32 | Mosquitto persistence + LittleFS Edge | ESP32 1000 رویداد | replay پس از reconnect |
| متریک ساعتی | TimescaleDB | تا 1 دقیقه | acceptable |
| لاگ‌ها | journald + Postgres `task_logs` | ≤ 1 ثانیه | از journald |

**کلید کلیدی:** Postgres با `synchronous_commit=on` و SSD با cache آفلاین — هیچ commit شده‌ای گم نمی‌شود. UPS مینیمال ($30) برای shutdown مرتب توصیه می‌شود اما اگر نباشد هم رفتار سیستم تعریف‌شده است.

---

## ۱۰. ساختار پوشه نهایی روی Orange Pi

```
/opt/hub/
├── bin/                           # systemd-managed services
│   ├── brain                      # python -m brain.main
│   ├── scheduler
│   ├── defwatcher
│   ├── tg-ops
│   └── healthd
├── tasks.d/                       # ★ Plug-&-Play: YAML تعاریف
│   ├── scraper.tgju.yaml
│   ├── bot.telegram.alerts.yaml
│   └── robot.lab.controller.yaml
├── jobs/                          # کد پروژه‌ها (mount در کانتینر)
│   ├── scraper-tgju/
│   │   ├── Containerfile
│   │   ├── main.py
│   │   └── pyproject.toml
│   └── ...
├── sdk/                           # SDK مشترک Python
│   └── hub_sdk/
│       ├── task.py                # checkpoint, lease, utility
│       ├── baas.py                # browser client
│       └── mqtt.py
├── state/                         # SQLite per-task (روی SSD)
│   ├── scraper-tgju.sqlite
│   └── ...
├── nomad/
│   ├── nomad.hcl
│   └── jobs/                      # auto-generated by Brain
├── compose/                       # infra services
│   ├── postgres.yaml
│   ├── redis.yaml
│   ├── mosquitto.yaml
│   └── baas.yaml
├── etc/
│   ├── policies.json              # قوانین زنده (Brain hot-reload)
│   └── slots.json                 # تعریف slot classes
└── logs/                          # rotated by journald
```

SSD mount: `/mnt/ssd/hub/` symlink به `/opt/hub/state` و `/var/lib/postgresql` و `/var/lib/redis`. eMMC فقط برای OS و باینری.

---

## ۱۱. بودجه RAM واقعی (v2)

```
Armbian Minimal                    ~250 MB
Podman + conmon (rootless)         ~80  MB
Nomad agent                        ~180 MB
PostgreSQL 16 (shared_buffers=128M)~220 MB
Redis 7 (maxmem 192M)              ~70  MB
Mosquitto                          ~25  MB
Brain (Python+uvloop)              ~90  MB
Scheduler + defwatcher + healthd   ~80  MB
tg-ops                             ~40  MB
node_exporter + cAdvisor           ~80  MB
─────────────────────────────────────────
Infrastructure total:             ~1115 MB
Buffer ایمنی:                      ~400 MB
─────────────────────────────────────────
Workload budget:                  ~2485 MB
```

**تخصیص workload (در حداکثر بار):**
```
Browser-as-a-Service (L slot):     1024 MB  ── همیشه مقیم
RQ workers × 5 slots:              ~250 MB  ── هر کدام idle
slot S × 4 jobs همزمان (مثال):    1024 MB
slot XS × 8 jobs (مثال):           ~512 MB  (با اولویت‌بندی)
─────────────────────────────────────────
حداکثر کار همزمان واقعی:      حدود ۲.۵ گیگ
```

---

## ۱۲. الگوی Nomad Job (نمونه برای یک تسک متغیر)

```hcl
job "task-${slug}" {
  type = "batch"   # یا "service" برای always_on
  priority = ${priority}

  group "main" {
    count = 1
    restart { attempts = 0 }        # retry توسط Brain، نه Nomad

    task "run" {
      driver = "podman"             # ← Podman driver
      config {
        image = "${image}"
        args  = ${args_json}
        memory_reservation = ${ram_mb_request}
      }
      env { ... }
      resources {
        memory = ${ram_mb_limit}
        cpu    = ${cpu_mhz}
      }
      kill_timeout = "10s"
      kill_signal  = "SIGTERM"      # تسک باید graceful shutdown کند تا checkpoint بزند
    }
  }
}
```

Brain این template را با Jinja2 رندر می‌کند و به Nomad submit می‌کند. هیچ HCL دستی نمی‌نویسیم.

---

## ۱۳. SDK Python — قرارداد توسعه پروژه‌ها

هر پروژه فقط این الگو را دنبال می‌کند:

```python
# jobs/scraper-tgju/main.py
from hub_sdk import Task, baas, mqtt
import asyncio

async def main():
    t = Task.bootstrap(slug="scraper.tgju")
    state = t.load_checkpoint() or {"page": 1}

    async with baas.client() as br:                 # شیر مرورگر مشترک
        while state["page"] <= 50:
            r = await br.scrape(
                url=f"https://tgju.org/list?p={state['page']}",
                wait="networkidle"
            )
            await t.persist_rows(parse(r.html))
            state["page"] += 1
            t.checkpoint(state)                      # هر iteration
            t.report_utility(rows_inserted=len(...)) # برای utility scorer

    t.done()

if __name__ == "__main__":
    asyncio.run(main())
```

SDK مدیریت می‌کند: connection به Postgres/Redis، lease renew، checkpoint atomic، graceful shutdown روی SIGTERM، dedup. **توسعه‌دهنده تسک هیچ مفهومی از Nomad/Podman/Brain نمی‌داند.**

---

## ۱۴. Roadmap اجرایی (تجدیدنظر شده)

| فاز | عنوان | خروجی قابل‌اندازه‌گیری | زمان |
|---|---|---|---|
| 0 | Bootstrap Armbian + Podman + SSD mount + WireGuard | SSH amن، Podman rootless کار می‌کند | روز ۱ |
| 1 | Infrastructure (Postgres+Redis+Mosquitto+Nomad) + اسکیمای v2 | `psql` و `redis-cli` کار می‌کنند، Nomad UI بالا | روز ۲–۳ |
| 2 | hub_sdk + Brain v0 (admission + ledger + recovery_worker) | یک تسک hello-world با checkpoint و resume | هفته ۱ |
| 3 | Definition Watcher + Scheduler + الگوی Nomad job | افزودن YAML در tasks.d/ بدون restart کار می‌کند | هفته ۲ |
| 4 | Browser-as-a-Service + RQ workers per slot | دو scraper موازی بدون OOM | هفته ۲ |
| 5 | Eviction Loop + Utility Scorer + Policy Engine | kill خودکار تسک معیوب در تست | هفته ۳ |
| 6 | tg-ops bot + alerts | کنترل از تله‌گرام کار می‌کند | هفته ۳ |
| 7 | ESP32 firmware template + MQTT integration + ingest stream | یک ESP32 وضعیت می‌فرستد، دستور می‌گیرد | هفته ۴ |
| 8 | VPS bootstrap (replica + restic + satellite brain) | failover دستی موفق | ماه ۲ |
| 9 | Failover خودکار + ضدتگ prefer_vps | offload شدن L slot به VPS تحت فشار | ماه ۲ |

---

## ۱۵. سوالات باز که قبل از فاز ۱ باید پاسخ دهی

این موارد کوچک‌اند ولی روی پیاده‌سازی فاز ۱ اثر دارند:

1. **Armbian:** نسخه Debian Bookworm یا Ubuntu Jammy؟ (پیشنهاد: Bookworm — پایدارتر روی Rockchip)
2. **SSD filesystem:** ext4 ساده یا btrfs (snapshot رایگان ولی complexity)؟ (پیشنهاد: ext4 + LVM)
3. **UPS:** آیا یک UPS کوچک ($30–50) در دسترس هست یا power-loss فقط با AOF/synchronous_commit handle شود؟
4. **VPS provider:** Hetzner / Contabo / DigitalOcean؟ (Hetzner Cloud CX11 بهترین قیمت/کیفیت برای 1GB ARM)
5. **WireGuard endpoint:** Orange Pi پشت NAT است؟ اگر بله، VPS باید listener باشد.

---

**خلاصه فلسفه v2:** هسته‌ی زیرساختی (Postgres/Redis/Nomad/Brain) را با systemd مثل قانون فیزیکی نگه می‌داریم. لایه‌ی تسک‌ها از یک پوشه YAML و یک SDK کوچک تغذیه می‌شود. Browser یک سرویس اشتراکی است که هرگز دو نمونه نمی‌شود. Dedup سه‌لایه (Redis + Postgres UNIQUE + idempotency_key) تضمین می‌کند هیچ تسکی دوبار اجرا نشود حتی پس از قطع برق. VPS سه نقش هم‌زمان دارد و failover معنادار است، نه آرایشی.

پس از پاسخ به ۵ سوال بخش ۱۵، وارد فاز ۰ می‌شویم: اسکریپت bootstrap و فایل‌های `compose/` و `nomad.hcl` را آماده می‌کنم.
