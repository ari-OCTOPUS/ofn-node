---
type: mining_phase_note
status: pre-execution
verdict_queue_status: all-open
execution_prompt_version: v2.0, v3.0
role: future_execution_spec
phase_locked_by: VERDICT_QUEUE
parent_system: MYCELIAL organism (_ops/)
parent_flag: OCTOPUS_WIRE_MINING (now ON — 2026-07-12)
created: 2026-07-12
updated: 2026-07-12
tags: [mining, phase-status, verdict-queue, tentacle-alpha, execution-spec, mycelial-subordinate]
---

# Phase Status — Execution Plan & Prompt v2.0/v3.0

> **truth anchor.** هر ایجنتی که وارد پروژه می‌شود، **اول این نوت را بخواند**.
> نقش فعلی: تحلیل و آماده‌سازی — نه اجرای خودکار.
> این پا (leg) **زیرمجموعه اختاپوس مرکزی (MYCELIAL organism)** است.

---

## جایگاه در اختاپوس مرکزی

```yaml
parent: MYCELIAL organism (_ops/organism.py)
leg_file: _ops/legs/mining_leg.py (389 lines, 2 brains)
flag: OCTOPUS_WIRE_MINING = OFF (default)
telegram_key: "mining" (icon ⛏)
activation_gates:
  - OCTOPUS_WIRE_MINING=1 (env var)
  - owner verdict
  - Security Gate open (wallet seed rotation complete)
deactivation: OCTOPUS_WIRE_MINING=0 or delete leg
```

### دو مغز Mining Leg

| مغز | نقش | status |
|---|---|---|
| **HardwareControlBrain** | fleet health، electricity gate ($0.05/kWh)، thermal warnings | ✅ ساخته شده، خاموش |
| **CoinDiscoveryBrain** | algo classification (ARM-viable)، candidate scoring، death-watch D2 | ✅ ساخته شده، خاموش |

### ارتباط با اختاپوس

```
MYCELIAL organism (_ops/organism.py)
├── tick loop → mining_beat() → writes ORGANISM-STATE.json
├── telegram_center/render.py → _collect_legs() → digest cell "mining"
└── wiring.py → make_mining_leg() + wire_summary()["wire_mining"]
    │
    └── Mining Leg (_ops/legs/mining_leg.py)
        ├── HardwareControlBrain → electricity safety + fleet summary
        └── CoinDiscoveryBrain → coin scouting + death-watch
```

**الگوی اصلی = اختاپوس.** Mining Leg از organism تیک می‌گیره، state میده، digest تلگرام از طریق اختاپوس. همه قواعد MYCELIAL اعمال می‌شه.

---

## وضعیت فعلی

پروژه در فاز **pre-execution** قرار دارد.

```yaml
phase: pre-execution
execution_state: ZERO mining active
wallet_seed: in rotation
hashrate_measured: false
profitability_data: none
fleet_physical_status: unknown
VERDICT_QUEUE: 6 items, all open
autonomy_floor: INFORM-only / read-only
mining_leg_built: true (389 lines, 2 brains, propose-only)
mining_leg_active: true (OCTOPUS_WIRE_MINING=1 since 2026-07-12)
activation_date: 2026-07-12
rollback: delete OCTOPUS_WIRE_MINING=1 from F:/backup/.env + restart organism
```

هیچ ابزار execution واقعی (OSINT Engine، Black-Box Monitor، Anomaly Detection) **فعال نیست**. Mining Leg ساخته شده ولی **خاموش** است.

---

## شرط ورود به فاز execution

برای خروج از pre-execution، **هر سه لایه** باید باز بشن:

### لایه ۱: VERDICT_QUEUE پروژه Mining

| ID | تصمیم | چیزی که باید مشخص شود |
|---|---|---|
| MIN-V1 | چند rig/Orange Pi قابل‌استفاده؟ | تعداد ریگ‌های سالم و آماده |
| MIN-V2 | برق <$0.05/kWh یا solar؟ | تأیید منبع برق و هزینه واقعی |
| MIN-V3 | الان هیچ mining فعال نیست؟ | تأیید safety state |
| MIN-V4 | Hardware Registry پر شود؟ | تکمیل رجیستری فیزیکی |
| MIN-V5 | wallet access برای agent صفر بماند؟ | تأیید سیاست zero-access |
| MIN-V6 | coin scouting فقط report باشد؟ | تأیید scope فعلی |

### لایه ۲: Security Gate اختاپوس

| شرط | وضعیت |
|---|---|
| Wallet seed rotation | 🟡 in rotation |
| Security Gate open | 🔴 closed |

### لایه ۳: فعال‌سازی Leg

| شرط | وضعیت |
|---|---|
| `OCTOPUS_WIRE_MINING=1` | ✅ ON (2026-07-12) |
| Owner verdict | ✅ داده شد |
| اختاپوس فعال و تیک‌زننده | ⏳ منتظر ری‌استارت |

**تا زمانی که هر سه لایه آماده نیست → فاز تغییر نمی‌کند.**

---

## نقش پرامپت Tentacle-Alpha v2.0 / v3.0

پرامپت v2.0/v3.0 یک **طرح معماری برای فاز execution آینده** است — نه ابزار فعال فعلی.

**v3.0** (۷۶۷ خط، ۱۷ سکشن): ارتقای بزرگ با ۸ ایجنت، OSINT v3، Black-Box v3 (eBPF)، Audit Merkle-tree، Competitor Intel، Telegram interface، رودمپ ۱۶ هفته‌ای. فایل: `01 - Docs/TENTACLE-ALPHA-MINING_Hybrid_MegaPrompt_v3.0.md`. دیاگرام‌ها: `05 - Media/TENTACLE-ALPHA_*.png`

### نقش v3.0 نسبت به Mining Leg فعلی:

```
v3.0 (پرامپت مگا)           Mining Leg (_ops/legs/)
━━━━━━━━━━━━━━━━━━         ━━━━━━━━━━━━━━━━━━━━━━━━
OSINT Engine v3            ❌ هنوز built نشده
Black-Box Monitor v3       ❌ هنوز built نشده
Audit Merkle-tree           ❌ DecisionLog ساده
Competitor Intel           ❌ هنوز built نشده
Telegram interface         ✅ از طریق اختاپوس
HardwareControlBrain       ✅ built (electricity + fleet)
CoinDiscoveryBrain         ✅ built (algo + scoring + D2)
Risk Score 0-100           ⚠️ فقط qualitative
COO Sync                   ✅ = اختاپوس organism
```

**v3.0 = نقشه راه آینده. Mining Leg = اسکلت فعلی. اختاپوس = محیط اجرا.**

---

## Gap Map — شکاف بین وضعیت فعلی و v3.0

```
لایه                  موجود؟     اولویت    شرط شروع
─────────────────────────────────────────────────────
VERDICT_QUEUE         ✅ باز      🔴 فوری    —
Security Gate         🔴 closed   🔴 فوری    wallet rotation
OCTOPUS_WIRE_MINING   🔴 OFF      🔴 فوری    owner verdict
Hardware Registry     ⚠️ stub    🔴 فوری    MIN-V1, V4
Electricity Check     ❌          🔴 فوری    MIN-V2
OSINT Engine          ❌          🟡 بعد     pool URL مشخص
Black-Box Monitor     ❌          🟡 بعد     ریگ فعال + leg ON
Audit Trail v2        ⚠️ ساده    🟡 بعد     MIN-V4
Risk Score 0-100       ⚠️ 4-رنگ   🟡 بعد     اولین data
Anomaly Detection     ❌          🔴 بلند     baseline چند موج
Competitor Intel      ❌          🔴 بلند     leg ON + steady state
Compliance (SOC2)     ❌          🔴 بلند     خارج از scope فعلی
```

---

## تضادهای شناخته‌شده

1. **OSINT قبل از فایل‌ها** — پرامپت می‌گوید "قبل از لمس هر فایلی OSINT برو". واقعیت: pool URLها و wallet addressها هنوز ثبت نشده‌اند.

2. **Black-Box روی سیستم خاموش** — پرامپت فرض می‌کند ماینرها اجرا هستند. واقعیت: `execution_state: ZERO`.

3. **COO = اختاپوس** — پرامپت یک Central Octopus مستقل فرض کرده. واقعیت: COO = MYCELIAL organism (`_ops/organism.py`). Mining Leg زیرمجموعه است.

4. **مقیاس** — پرامپت SOC2/ISO27001 طراحی کرده. واقعیت: ۶ نود Orange Pi با budget صفر.

5. **Mining Leg vs v3.0** — Mining Leg دو مغز پایه دارد. v3.0 هشت ایجنت می‌خواهد. مسیر تکامل: leg فعلی → اضافه کردن ایجنت‌های v3.0 به‌تدریج.

---

## قواعد حاکمیتی برای ایجنت‌ها

```yaml
agents_may:
  - read all files (green)
  - generate analysis reports (green)
  - update OpenQuestions, DecisionLog (yellow — with logging)
  - propose coin candidates via Coin Scouting Framework (yellow — draft only)
  - update this note to reflect phase changes (yellow — with human review)
  - follow MYCELIAL organism patterns for any new leg development

agents_must_not:
  - execute any command on rigs (red — D-20)
  - access wallet/seed/private key (red — D-11)
  - start/stop mining (red — needs verdict)
  - treat v3.0 capabilities as active tools
  - close VERDICT_QUEUE items autonomously
  - activate OCTOPUS_WIRE_MINING without owner verdict
  - deviate from MYCELIAL organism patterns (الگوی اصلی = اختاپوس)
```

---

## مسیر پیشنهادی

```
فاز ۱:  فعال‌سازی Mining Leg در اختاپوس ✅ انجام شد
                ├── OCTOPUS_WIRE_MINING=1 ✅ (2026-07-12)
                ├── اختاپوس تیک می‌زنه → mining_beat() اجرا ⏳ منتظر ری‌استارت
                ├── VERDICT_QUEUE و Security Gate هنوز باز (leg read-only هست)
                └── digest تلگرام فعال می‌شود (⛏ Mining)

فاز ۲:  بستن VERDICT_QUEUE + Security Gate
                ├── تأیید سلامت ریگ‌ها (MIN-V1, V4)
                ├── تأیید هزینه برق (MIN-V2)
                ├── تأیید safety state (MIN-V3)
                ├── تأیید سیاست‌ها (MIN-V5, V6)
                ├── تکمیل Hardware Registry
                └── wallet seed rotation → Security Gate open

فاز ۲:  بستن VERDICT_QUEUE + Security Gate
                ├── تأیید سلامت ریگ‌ها (MIN-V1, V4)
                ├── تأیید هزینه برق (MIN-V2)
                ├── تأیید safety state (MIN-V3)
                ├── تأیید سیاست‌ها (MIN-V5, V6)
                ├── تکمیل Hardware Registry
                └── wallet seed rotation → Security Gate open

فاز ۳:  اولین ریگ → اولین pool → اولین ماین
                ├── Black-Box monitor معنا پیدا می‌کند
                ├── OSINT Engine معنا پیدا می‌کند
                └── اولین Risk Score کمّی

فاز ۴:  ارتقا به v3.0 (ایجنت‌های اضافی)
                ├── OSINT Agent, Competitor Intel Agent
                ├── Audit Trail Merkle-tree
                ├── Anomaly Detection (baseline)
                └── Compliance reporting (در حد مناسب)
```

---

## تغییرات

| تاریخ | تغییر |
|---|---|
| 2026-07-12 | نوت اولیه — تحلیل تقاطع پرامپت v2.0 با وضعیت فعلی |
| 2026-07-12 | آپدیت بزرگ — Mining Leg در _ops/ کشف شد. نوت بازنویسی: زیرمجموعه اختاپوس، ۳ لایه فعال‌سازی، نقش v3.0 vs leg فعلی |
| 2026-07-12 | **فعال‌سازی OCTOPUS_WIRE_MINING=1** — flag در .env ست شد. فاز ۱ از مسیر تکامل تکمیل. leg تیک می‌زند، digest تلگرام فعال. |
