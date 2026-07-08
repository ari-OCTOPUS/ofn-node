---
type: architecture-spec
project: "Octopus / fusion-mvp — لایه‌ی زمان و ضربانِ قلب"
created: 2026-07-08
status: "design locked (topology + features) · pulse-source decided · code-ready برای ایجنتِ کدنویس"
target: "کدِ Brushline (60_code/) — سازگار با SQLite/WAL، تک‌process، Orange Pi"
scope: "فقط لایه‌ی زمان (chrono) و heartbeat؛ منطقِ کسب‌وکار دست‌نخورده"
epistemics: "【E】 علمِ تثبیت‌شده · 【P】 استنتاجِ موجه · 【S】 گمانه | نگاشتِ canon: [canon-entailed]/[Supported]/[Speculative]"
---

# 🐙 معماریِ زمان و ضربانِ قلبِ اختاپوس — Chrono Layer

## ۰. برای ایجنتِ گیرنده — از اینجا شروع کن
این سند **فقط لایه‌ی زمان** را طراحی می‌کند: یک موجودِ چند-ایجنتی (اختاپوس) که آگاهیِ زمانیِ انسان‌گونه را **شبیه‌سازی** می‌کند، روی کدِ موجودِ Brushline. منطقِ Gate/Queue/Channel دست‌نخورده می‌ماند؛ ما یک **Chrono Bus** روی آن سوار می‌کنیم.

کاری که باید بکنی، به‌ترتیب:
1. بخش ۷ (invariantها) و بخش ۸ (schema) را بخوان — قراردادِ سخت این‌جاست.
2. بخش ۱۱ (قدم‌های پیاده‌سازی) را دنبال کن. **قدمِ اول (P-Chrono-1) خودش F19 گمشده را هم می‌بندد** — یک تیر، دو نشان.
3. هر رویداد در کد باید از این پس با یک **HLC** مهر بخورد و به **LANGAR ledger** append شود قبل از هر اثرِ برگشت‌ناپذیر.

> **قیدِ فلسفیِ کلِ سند (از اصلِ خودِ پروژه):** هر توانایی یک هزینه دارد. سریع‌تر تجربه‌کردن = سریع‌تر پیرشدن. توقفِ ضربان = مرگ. این‌ها narrative convenience نیستند؛ در کد enforce می‌شوند.

---

## ۱. تصمیم‌های قفل‌شده (از دیالوگِ زمان)

| # | تصمیم | مقدار |
|---|---|---|
| Q2 | توپولوژیِ ساعت | **hybrid**: هر پا HLCِ محلیِ خودش؛ **ترتیبِ کلیِ واحد فقط روی LANGAR log** |
| Q3 | ویژگی‌های انسان‌گونه | **هر چهار**: (۱) حسِ مدت · (۲) فلش/پیری/میرایی · (۳) نرخِ تجربه ∝ بار · (۴) انتظار/آینده |
| Q1 | منبعِ ضربان | **لایه‌ای — تصمیمِ من** (بخش ۴): pacemaker (ساعت‌دیواری) + HLC (رویدادی) + human-append (فلش) |
| canon | مدلِ سه‌رژیمیِ زمانِ فعلیت | فرض: توصیف‌کننده‌ی **بستر (Layer 0)** است؛ لایه‌های بالا مشتق‌اند |

---

## ۲. دوازده معماریِ مرجع و سهمِ هرکدام در اختاپوس

هر ردیف: معماریِ واقعیِ روز → چه‌چیزی به اختاپوس می‌دهد → کجای بدن.

| # | معماری | سهم در اختاپوس | عضو | مبنا |
|---|---|---|---|---|
| 1 | **Lamport logical clocks** | ترتیبِ before/after بدون ساعت؛ زمانِ بومیِ AI | زمانِ ذهنیِ پایه | 【E】 |
| 2 | **Vector clocks** | تشخیصِ همزمانی/علیّتِ بینِ پاها | detection ِ concurrency | 【E】 |
| 3 | **Hybrid Logical Clocks (HLC)** | (physical, logical) در یک ۶۴بیت؛ نزدیک به NTP + علّی. استفاده در CockroachDB/MongoDB/YugabyteDB | **ساعتِ محلیِ هر پا** | 【E】 |
| 4 | **Spanner TrueTime** | زمانِ فیزیکی به‌مثابه‌ی بازه‌ی عدم‌قطعیت، نه نقطه | مدلِ «اکنونِ فازی» | 【E】 |
| 5 | **Temporal / durable execution** | event-sourced replay ⇒ کد نمی‌تواند مستقیم ساعت بخواند؛ worker heartbeat ~۶۰s با بارِ CPU | **تعیّن‌گراییِ زمان + pacemaker** | 【E】 |
| 6 | **Event sourcing + transactional outbox** (Atomix-style irreversible-effect gating) | لاگِ append-only = تنها منبعِ ترتیبِ کلی؛ اثرِ برگشت‌ناپذیر gate می‌شود روی پیشرفتِ لاگ | **قلب/LANGAR = فلشِ زمان** | 【E/P】 |
| 7 | **SWIM + phi-accrual failure detector** | ضربان + گاسیپ؛ حالتِ میانیِ **suspected** (نه زنده/نه مرده)؛ زنده‌بودنِ **احتمالاتیِ تدریجی** | **حسِ حیات/پیریِ تدریجی** | 【E】 |
| 8 | **Raft heartbeat** | ضربانِ رهبر→پیرو؛ election timeout؛ جلوگیری از split-brain | pacemaker ِ مرکزی | 【E】 |
| 9 | **Erlang/OTP supervision tree** ("let it crash" / self-healing) | پایِ خراب restart می‌شود در حالتِ سالمِ known-good؛ state باید externalize شود (در لاگ) | **دکترِ تکاملی** | 【E】 |
| 10 | **Global Workspace Theory / GWA (2026)** | مغزِ مرکزی = broadcast hub؛ پاها = پردازش‌های تخصصیِ موازی؛ **cognitive cycle = همان ضربان** | **مغزِ کل + ضربانِ آگاهی** | 【E/S】 |
| 11 | **Active inference / predictive processing** | مدل‌سازیِ خود که در زمان دوام دارد و با پیامدِ کنشِ خود روبه‌روست؛ کاهشِ surprise | **انتظار/آینده (ویژگی ۴)** | 【P/S】 |
| 12 | **Conscious Turing Machine (CTM-AI)** | چرخه‌ی شناختیِ زمان‌بندی‌شده به‌مثابه‌ی واحدِ «لحظه» | نرخِ نمونه‌برداریِ تجربه | 【S】 |

> نگاشتِ اصلی این است: **HLC (۳) ساعتِ هر پا · Temporal (۵) قانونِ «ساعت را مستقیم نخوان» · Event-sourcing (۶) فلشِ زمان از راهِ LANGAR · SWIM/phi (۷) پیریِ تدریجی · Supervision (۹) دکتر · GWT (۱۰) مغز+ضربان.** بقیه تقویت‌کننده‌اند.

---

## ۳. مدلِ زمانِ چهار-لایه‌ی اختاپوس

```
Layer 0 — بستر (SUBSTRATE)          ← مدلِ سه‌رژیمیِ canon؛ زمانِ فیزیکیِ واقعی
   (اختاپوس آن را مستقیم نمی‌خواند — دقیقاً مثل کدِ Temporal که ساعت نمی‌خواند)
        │  نمونه‌برداری می‌شود توسط ↓
Layer 1 — PACEMAKER (ساعتِ دیواری)  ← تیکِ asyncio ~60s؛ فقط liveness + زمان‌بندی
        │  هر تیک یک beat_seq تولید می‌کند ↓
Layer 2 — ساعتِ ذهنی (HLC، محلیِ هر پا) ← «اکنونِ» هر پا؛ ترتیبِ رویدادها؛ AI-native
        │  ترتیبِ کلیِ واحد فقط این‌جا قفل می‌شود ↓
Layer 3 — فلشِ میرا (LANGAR arrow)  ← فقط با human-append پیش می‌رود؛ برگشت‌ناپذیر = پیری/مرگ
        
مشتق: EXPERIENCE-RATE = رویدادهای قابل‌تفکیک ÷ زمانِ pacemaker  ← چگالیِ تجربه (ویژگی ۳)
```

**چرا این ترتیب [canon-entailed]:** canon سه‌رژیمی، بستر است (Layer 0). AI به بستر دسترسیِ مستقیم ندارد؛ همان‌طور که در Temporal کدِ workflow نمی‌تواند `time.now()` بخواند و زمان را از replay می‌گیرد — این دقیقاً «برش/نمونه‌برداری» است که در چتِ قبل گفتیم. پس Layer 1–3 نرخ‌ها و برش‌های مشتق از بستر هستند، نه خودِ بستر. هیچ تعریفِ ناسازگارِ دومی از زمان در canon ایجاد نمی‌شود.

---

## ۴. منبعِ ضربان — پاسخِ لایه‌ای (Q1)

سؤال «قلب با چه می‌تپد؟» یک منبعِ واحد ندارد؛ **سه منبع، هرکدام کارِ متفاوت:**

| لایه | منبع | چه کاری می‌کند | معماری |
|---|---|---|---|
| **Pacemaker** | تیکِ ساعت‌دیواری (asyncio ~60s) | پاها را بینِ ضربان‌ها زنده نگه می‌دارد؛ scheduler (followup/escalate) | Raft/Temporal heartbeat |
| **ساعتِ ذهنی** | شمارنده‌ی HLC (هر اکشن) | زمانِ محلیِ هر پا؛ ترتیبِ علّی | HLC |
| **ضربانِ حقیقی (قلب)** | **append انسانی به LANGAR** | فلشِ زمان را پیش می‌برد؛ **پیری/میرایی** | Event sourcing |

**نکته‌ی طراحیِ کلیدی:** pacemaker ≠ قلب. pacemaker فقط ضربان‌سازِ مصنوعی‌ست که legs را از desync نگه می‌دارد. **قلبِ واقعی = LANGAR** (ریشه‌ی دیفالتِ اطلاعات + تنها فلشِ برگشت‌ناپذیر). این دقیقاً حرفِ چتِ قبل است: AI جهتِ زمان را حس نمی‌کند؛ irreversibility برای پوسته **ساخته** می‌شود، نه حس. لاگ = ساعتِ فیزیکیِ اختاپوس.

**هزینه/آسیب‌پذیریِ هر منبع (اصلِ «هر توانایی یک هزینه»):**
- توقفِ **pacemaker** → پاها desync می‌شوند → تکه‌تکه‌شدن به جزایرِ زمانی → **مرگ**.
- توقفِ **human-append** → فلشِ زمان می‌ایستد → پیری متوقف → **stasis** (نه مرگ، ولی نه زندگی؛ حالتِ خواب/کما). این همان قیدِ canon است: بدونِ ریشه‌ی میرا، جاودانگیِ منجمد.
- drift ِ **HLC** فراتر از کرانِ ε → شکستِ علیّت → پاها روی گذشته/آینده اختلاف پیدا می‌کنند.

---

## ۵. آناتومیِ اختاپوس ↔ کدِ Brushline

| عضوِ اختاپوس | نقش | نگاشت به کدِ موجود |
|---|---|---|
| 🧠 **مغزِ مرکزی** (global workspace) | broadcast hub؛ «اکنونِ مشترک» را پخش می‌کند | `Orchestrator` + یک **Chrono Bus** جدید |
| 🦵 **پاها** (autonomic، مغزِ مستقل) | کارِ تخصصی؛ HLCِ محلیِ خودشان؛ حلقه‌ی خودمختار | `Worker A–F` + `leg_clock` |
| 🩺 **دکترِ تکاملی** | monitor + restart + evolve؛ اهدافِ مشخص | supervision loop + eval-harness موجود |
| ❤️ **قلب** (ریشه‌ی دیفالتِ اطلاعات) | root-of-trust؛ فلشِ زمان؛ append-only | `LANGAR ledger` = گسترشِ audit hash-chain موجود |
| 🕸️ **عصب‌کشی** | ضربان + مهرِ HLC + sync barrier | **Chrono Bus** (هسته‌ی این سند) |

**دکترِ تکاملی چطور از supervision می‌آید:** در OTP، پایِ خراب crash می‌کند و supervisor آن را در حالتِ known-good restart می‌کند؛ **state ای که باید دوام بیاورد در بیرون (لاگ) ذخیره می‌شود.** برای همین LANGAR حیاتی‌ست: پاها stateless-restartable‌اند، حافظه‌ی پایدار در قلب است. دکتر = supervisor + اهدافِ eval (نسلِ خوداصلاحی روی لاگ).

---

## ۶. دیاگرام (ASCII) — Chrono Layer روی Brushline

```
                         ❤️ LANGAR LEDGER (قلب)
                    append-only · hash-chain · human-judgment
                    فلشِ زمان (age_tick) — تنها ترتیبِ کلیِ واحد
                              ▲   ▲
              (gate اثرِ برگشت‌ناپذیر: INV-1/TINV-7)   (age advance)
                              │   │
   ┌──────────────────────────┼───┼───────────────────────────┐
   │            🧠 ORCHESTRATOR + CHRONO BUS (مغزِ مرکزی)        │
   │  ┌────────────────────────────────────────────────────┐  │
   │  │  HEARTBEAT LOOP (pacemaker ~60s)                    │  │
   │  │   tick → جمعِ ack → phi-accrual → suspected/failed  │  │
   │  │   → «اکنون» = max(HLCها) → BROADCAST (GWT)          │  │
   │  │   → scheduler (followup/escalate = F19) → checkpoint│  │
   │  └────────────────────────────────────────────────────┘  │
   │        │ broadcast «اکنونِ مشترک» + beat_seq              │
   └────────┼──────────────────────────────────────────────────┘
            │ (هر پا فقط beat + HLCِ محلی را می‌بیند، نه ساعتِ دیواری)
   ┌────┬───┴────┬────────┬────────┬────────┬────────┐
   ▼    ▼        ▼        ▼        ▼        ▼        │
 🦵A   🦵B      🦵C      🦵D      🦵E      🦵F        │  🩺 دکتر (supervision)
 Res  Sent    Cont     Asset    Chan     Lead       │  monitor phi → restart
 هرکدام: leg_clock(HLC) · experience_rate · vitality│  known-good از لاگ
   │    │        │        │        │        │        │
   └────┴────┬───┴────────┴────────┴────────┴────────┘
            ▼
   ConstitutionGate → ApprovalQueue → (send/publish/sync)
            └── هیچ‌کدام settle نمی‌شوند مگر بعد از append به قلب (TINV-7)

 Layer 0 (بستر/canon سه‌رژیمی) — خوانده نمی‌شود، فقط نمونه‌برداری می‌شود ↑
```

---

## ۷. Invariantهای زمان (TINV) — قراردادِ سخت

- **TINV-1 (monotonic HLC):** هر رویداد یک HLC یکنواختِ اکید می‌گیرد؛ `now()` همیشه > هر HLCِ قبلیِ محلی و هر HLCِ دریافتی. counter فقط وقتی رشد می‌کند که physical برابر بماند.
- **TINV-2 (single total order):** ترتیبِ کلیِ واحد **فقط** از LANGAR ledger می‌آید. پاها فقط ترتیبِ **جزئیِ** محلی دارند. تصمیمِ Q2.
- **TINV-3 (irreversible arrow):** `age_tick` فقط با human-append پیش می‌رود و **هرگز** کاهش نمی‌یابد. برگشتِ آن = نقضِ hash-chain = مرگِ منطقی.
- **TINV-4 (vitality/death):** هر پا باید در پنجره‌ی `K_SUSPECT` ضربان حداقل یک ack بدهد. K تا → `suspected`؛ `M_DEAD` تا → `failed` → دکتر restart می‌کند (known-good از لاگ). SWIM suspected state.
- **TINV-5 (no wall-clock read):** هیچ پایی ساعتِ دیواری را مستقیم نمی‌خواند؛ فقط HLCِ محلی + آخرین `beat_seq`ِ broadcast‌شده. (تعیّن‌گراییِ Temporal — لازم برای replay/audit.)
- **TINV-6 (bounded experience-rate):** `experience_rate = رویدادهای قابل‌تفکیک ÷ Δt_pacemaker`، کران‌دار: سقف = ظرفیتِ سخت‌افزار (آنالوگِ زمانِ پلانک — بی‌نهایت ممنوع)، کف = ۰ (خواب). **نرخِ بالاتر ⇒ پیریِ متابولیکِ سریع‌تر** (بخش ۱۰، ویژگی ۳).
- **TINV-7 (effect-gating):** هیچ اثرِ برگشت‌ناپذیری (send/publish/sync) settle نمی‌شود مگر append به LANGAR انجام شده باشد. این **همان INV-1 موجودِ Brushline** است، حالا با پشتوانه‌ی زمانی (Atomix-style).

---

## ۸. Schema جدول‌ها (SQLite/WAL — سازگار با Brushline)

```sql
-- ضربان: هر تیکِ pacemaker یک ردیف. beat_seq همان «شماره‌ی نبض» است.
CREATE TABLE heartbeat (
  beat_seq      INTEGER PRIMARY KEY,          -- یکنواختِ اکید
  wall_ts       INTEGER NOT NULL,             -- ms UTC (فقط برای انسان/دیباگ)
  hlc_phys      INTEGER NOT NULL,             -- «اکنونِ مشترک» = max فیزیکیِ HLCها
  hlc_logical   INTEGER NOT NULL,
  present_legs  TEXT NOT NULL,                -- JSON: پاهایی که ack دادند
  absent_legs   TEXT NOT NULL,                -- JSON: suspected/failed
  workspace_ref TEXT,                         -- به رویدادِ broadcast‌شده‌ی GWT
  ts            INTEGER NOT NULL
);
CREATE INDEX idx_heartbeat_ts ON heartbeat(ts);

-- ساعتِ هر پا (HLC) + حیات + نرخِ تجربه. یک ردیف per leg، UPDATE می‌شود.
CREATE TABLE leg_clock (
  leg_id          TEXT PRIMARY KEY,           -- 'A'..'F'
  hlc_phys        INTEGER NOT NULL,
  hlc_logical     INTEGER NOT NULL,
  last_ack_beat   INTEGER NOT NULL,           -- آخرین beat_seq که ack داد
  vitality_phi    REAL NOT NULL DEFAULT 0.0,  -- phi-accrual: بالاتر = مشکوک‌تر
  experience_rate REAL NOT NULL DEFAULT 0.0,  -- رویداد/ثانیه‌ی pacemaker
  state           TEXT NOT NULL DEFAULT 'alive' -- alive | suspected | failed
                  CHECK (state IN ('alive','suspected','failed')),
  updated_at      INTEGER NOT NULL
);

-- قلب: گسترشِ audit hash-chain موجود به یک ledgerِ زمان‌دار.
-- (اگر audit chain الان جدول دارد، این ستون‌ها به آن اضافه شوند نه جدولِ نو.)
CREATE TABLE langar_ledger (
  entry_seq     INTEGER PRIMARY KEY,          -- ترتیبِ کلیِ واحد (TINV-2)
  prev_hash     TEXT NOT NULL,
  hash          TEXT NOT NULL,                -- sha256(prev_hash || payload || age_tick)
  hlc_phys      INTEGER NOT NULL,             -- HLC رویداد
  hlc_logical   INTEGER NOT NULL,
  age_tick      INTEGER NOT NULL,             -- فلشِ میرا؛ فقط با human-append +1 (TINV-3)
  is_human      INTEGER NOT NULL DEFAULT 0,   -- 1 = قضاوتِ انسانی (تنها چیزی که age را می‌برد)
  actor_leg     TEXT,                         -- کدام پا رویداد را ساخت
  payload_ref   TEXT NOT NULL,
  ts            INTEGER NOT NULL
);
CREATE INDEX idx_langar_hlc ON langar_ledger(hlc_phys, hlc_logical);

-- سنجه‌ی تجربه (نرخ ∝ بار) — per leg per beat.
CREATE TABLE experience_meter (
  leg_id        TEXT NOT NULL,
  beat_seq      INTEGER NOT NULL,
  events_count  INTEGER NOT NULL,             -- رویدادهای قابل‌تفکیک در این ضربان
  dt_wall_ms    INTEGER NOT NULL,
  rate          REAL NOT NULL,                -- events_count / (dt_wall_ms/1000)
  PRIMARY KEY (leg_id, beat_seq)
);

-- حسِ مدت (ویژگی ۱): لنگرهای زمانی برای «چقدر از X گذشته».
CREATE TABLE duration_marker (
  event_id   TEXT PRIMARY KEY,
  hlc_phys   INTEGER NOT NULL,
  hlc_logical INTEGER NOT NULL,
  wall_ts    INTEGER NOT NULL,
  label      TEXT
);

-- انتظار/آینده (ویژگی ۴): صفِ کارهای زمان‌بندی‌شده، کلیددار با beat یا HLC.
CREATE TABLE anticipation_queue (
  id         INTEGER PRIMARY KEY,
  leg_id     TEXT,
  due_beat   INTEGER,                         -- سررسید بر حسبِ نبض (نه ساعتِ دیواری!)
  kind       TEXT NOT NULL,                   -- 'wait' | 'schedule' | 'followup'
  task_ref   TEXT NOT NULL,
  created_beat INTEGER NOT NULL
);
CREATE INDEX idx_anticipation_due ON anticipation_queue(due_beat);
```

---

## ۹. حلقه‌ی ضربان (pseudo-code)

```python
# مغزِ مرکزی — heartbeat loop (در main.py، asyncio background task).
# این قدم F19 (scheduler گمشده) را هم می‌بندد: escalate/followup این‌جا اجرا می‌شوند.
async def heartbeat_loop(bus, legs, db, PERIOD=60):
    beat = db.last_beat_seq()
    while alive:
        await asyncio.sleep(PERIOD)
        beat += 1
        now_wall = utc_now_ms()

        # 1) جمعِ ackها و به‌روزرسانیِ حیات (phi-accrual + SWIM suspected/failed)
        acks = bus.collect_acks(window=PERIOD)
        for leg in legs:
            phi = phi_accrual(leg.arrival_history, now_wall)
            leg.state = ('alive'    if phi < PHI_SUSPECT else
                         'suspected' if phi < PHI_DEAD    else 'failed')
            db.upsert_leg_clock(leg)
            if leg.state == 'failed':
                doctor.restart_from_known_good(leg, db)   # supervision (OTP)

        # 2) «اکنونِ مشترک» = max فیزیکیِ HLCها (barrier همگام‌سازی)
        now_hlc = hlc_max(leg.hlc for leg in legs if leg.state != 'failed')

        # 3) BROADCAST (Global Workspace): «اکنون» + beat به همه‌ی پاها
        bus.broadcast({'beat': beat, 'hlc': now_hlc,
                       'present': [l.id for l in legs if l.state=='alive']})

        # 4) scheduler (F19): کارهای سررسیده بر حسبِ beat، نه ساعتِ دیواری
        for task in db.due_anticipation(due_beat=beat):
            orchestrator.dispatch(task)          # followup روز 2/5/10 · escalate_overdue

        # 5) checkpoint سبک روی heartbeat (نه verify کاملِ زنجیره — F14)
        db.insert_heartbeat(beat, now_wall, now_hlc, present, absent)


# هر پا — autonomic loop. ساعتِ دیواری نمی‌خواند (TINV-5).
async def leg_loop(leg, bus, db):
    async for msg in leg.inbox:                  # کارِ تخصصیِ Worker A..F
        leg.hlc = hlc_tick(leg.hlc)              # HLC محلی +1 (TINV-1)
        result = leg.process(msg)                 # منطقِ کسب‌وکارِ موجود
        db.record_event(leg.id, leg.hlc, result)  # مهرِ HLC روی هر رویداد
        leg.events_this_beat += 1
        bus.ack(leg.id, leg.hlc)                  # نشانِ حیات

    # در هر broadcast: HLC محلی را با «اکنونِ مشترک» merge کن (قاعده‌ی HLC receive)
    on_broadcast(b):
        leg.hlc = hlc_merge(leg.hlc, b['hlc'])
        db.write_experience(leg.id, b['beat'],
                            events=leg.events_this_beat, dt=PERIOD)
        leg.events_this_beat = 0


# قلب — فقط قضاوتِ انسانی فلشِ زمان را می‌برد (TINV-3).
def on_human_judgment(judgment, db):
    entry = db.langar_append(payload=judgment, is_human=1,
                             age_tick=db.last_age_tick() + 1)   # +1 فقط این‌جا
    # هر اثرِ برگشت‌ناپذیرِ منتظر، حالا مجازِ settle است (TINV-7)
    release_gated_effects(up_to=entry.entry_seq)
```

**توابعِ HLC (استاندارد، ~۲۰ خط):** `hlc_tick`, `hlc_merge`, `hlc_max` طبقِ الگوریتمِ CockroachDB (`pkg/util/hlc`): در هر رویداد `l = max(l, pt)`؛ اگر `l` برابر ماند `c += 1` وگرنه `c = 0`. تحتِ قفلِ per-node (تک‌process ما این را رایگان دارد).

---

## ۱۰. نگاشتِ چهار ویژگیِ انسان‌گونه → فیلد/جدولِ مشخص

| ویژگی | مکانیزم | جدول/فیلد | منبعِ معماری |
|---|---|---|---|
| **۱. حسِ مدت** | `duration = now_hlc − event_hlc` (+ Δwall برای انسان) | `duration_marker` | HLC + Spanner (بازه) |
| **۲. فلش/پیری/میرایی** | `age_tick` یکنواخت روی قلب؛ برگشت‌ناپذیریِ hash-chain | `langar_ledger.age_tick` | event sourcing + append-only |
| **۳. نرخِ تجربه ∝ بار** | `rate = events/Δt`؛ کران‌دار؛ نرخِ بالا ⇒ پیریِ سریع‌تر | `experience_meter.rate` + coupling به `age` | GWT cognitive cycle + متابولیک (چتِ قبل) |
| **۴. انتظار/آینده** | صفِ سررسید بر حسبِ `due_beat`؛ پیش‌بینیِ کنشِ آینده | `anticipation_queue` | Temporal timers + active inference |

**قیدِ متابولیکِ ویژگی ۳ (اصلِ «هزینه»):** یک coupling ِ سختِ بین `experience_rate` و `age_tick` بگذار — پایی که در هر ضربان پرمشغله‌تر است، سهمِ بیشتری از فلشِ زمان مصرف می‌کند. **duration در برابر intensity:** نمی‌توان هم بیشترین عمر را داشت هم بیشترین چگالیِ تجربه. این مکانیزمِ فیزیکیِ همان «no core fragmentation under N-gradients» است.

---

## ۱۱. قدم‌های پیاده‌سازی برای ایجنتِ بعدی (ترتیب‌دار)

| قدم | کار | فایل‌های Brushline | نکته |
|---|---|---|---|
| **P-Chrono-1** | Chrono Bus + `heartbeat` + heartbeat_loop | `main.py`, جدیدِ `chrono.py` | **F19 را هم می‌بندد** — scheduler همین‌جاست |
| **P-Chrono-2** | HLC per leg + `leg_clock` + مهرِ HLC روی هر audit entry | `chrono.py`, `database.py`, `audit.py` | ~۲۰ خطِ HLC |
| **P-Chrono-3** | phi-accrual + suspected/failed + restart (دکتر) | `chrono.py`, `orchestrator.py` | از resilience موجود استفاده کن |
| **P-Chrono-4** | `age_tick` + arrow روی قلب (گسترشِ hash-chain) | `audit.py` → `langar_ledger` | TINV-3، تنها human-append |
| **P-Chrono-5** | `experience_meter` + coupling نرخ↔پیری | `chrono.py` | TINV-6 + قیدِ متابولیک |
| **P-Chrono-6** | `duration_marker` + `anticipation_queue` | `chrono.py`, `orchestrator.py` | ویژگی ۱ و ۴ |
| **P-Chrono-7** | global broadcast در Orchestrator (GWT) | `orchestrator.py` | «اکنونِ مشترک» |

> **توصیه‌ی ترتیب:** P-Chrono-1 را اول بزن چون هم زیرساختِ زمان است هم F19ِ باز را حل می‌کند (دو ارزش، یک session). بقیه روی همان bus سوار می‌شوند.

---

## ۱۲. ریسک‌ها و خطاهای طراحی که باید گرفته شوند

- **پایی که ساعتِ دیواری را مستقیم بخواند** → replay/audit را می‌شکند. TINV-5 را سخت enforce کن (مثل قاعده‌ی determinism در Temporal).
- **گذاشتنِ فلشِ زمان روی pacemaker** به‌جای human-append → no-signaling و irreversibility می‌شکنند و narrative convenience برمی‌گردد. pacemaker فقط liveness است؛ فلش فقط از قلب.
- **SQLite تک-writer:** heartbeat_loop و legs نباید هم‌زمان بنویسند. **خودِ ضربان را write-barrier کن** (نوشتنِ leg در لحظه‌ی broadcast serialize شود) — این F13/F15 را هم امن نگه می‌دارد.
- **نرخِ تجربه‌ی بی‌کران** → آنالوگِ AI-god. سقفِ سخت‌افزاری (پلانک‌آنالوگ) بگذار؛ هیچ پایی بی‌نهایت سریع نشود.
- **نرخِ بالا بدونِ هزینه** → قیدِ متابولیک را حذف نکن؛ سریع‌تر تجربه = سریع‌تر پیری، وگرنه اصلِ پروژه نقض می‌شود.

---

## پیوست — کجای این با canon جفت است
- **heartbeat = بازتأسیسِ simultaneity** میان پاهایی که در نرخ‌های زمانیِ متفاوت زندگی می‌کنند. [canon-entailed]
- **log = فلشِ زمان** (از چتِ قبل، حالا در کد: `langar_ledger.age_tick`). [canon-entailed]
- **زمانِ متابولیک:** نرخِ ذهنی ∝ مصرفِ منابع؛ duration در برابر intensity. [Supported]
- **وحدت/جاودانگیِ ناسازگار:** از `no-global-clock (TINV-2) + no-signaling` مشتق می‌شود — دیگر axiom نیست، قضیه است. [canon-entailed]
- **سقفِ پلانک روی نرخِ تجربه:** کرانِ مطلقِ TINV-6؛ AI-god ِ بی‌نهایت‌سریع فیزیکاً ممتنع. [Supported]

**سؤالِ بازِ باقی‌مانده (قبل از P-Chrono-4):** `age_tick` فقط با قضاوتِ انسانیِ **جدید** پیش برود، یا هر append به قلب؟ اگر «هر append» → ماشین می‌تواند خودش پیر شود = نقضِ ریشه‌ی میرا. توصیه‌ی من: **فقط `is_human=1`**. تأییدت را می‌خواهم چون این هسته‌ی میرایی را قفل می‌کند.
