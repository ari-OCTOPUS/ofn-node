---
type: report
version: "1.1"
project: Mining
created_by: ZCode Agent (claude/octopus-event-bridge-aligned)
created: 2026-07-28
updated: 2026-07-29
status: done
# status پیشین: COMPLETE — owner verdicts collected + zip artifacts analyzed
owner: آری
tags: [mining, scan, handoff, full-report]
---

# 🔬 اسکن کامل پروژه Mining — ریپورت برای ایجنت ارشد

> **تاریخ:** 2026-07-28
> **اسکن‌کننده:** ZCode Agent
> **مخاطب:** ایجنت ارشد (Senior Agent)
> **وضعیت:** ✅ اسکن تمام + سوالات مالک پاسخ داده شد

---

## 0. خلاصه اجرایی (Executive Summary)

| آیتم | مقدار |
|---|---|
| **پروژه** | سیستم ماینینگ CPU/ARM نوظهور — شکار خودکار کوین + ماین + تعویض |
| **سخت‌افزار** | ۱۶۲ نود (۱۶ OPI-5 Pro + ۱۴۰ ESP32 + ۲ FPGA) — **تمام در سیدنی** |
| **وضعیت ریگ‌ها** | ❌ همه خاموش — نیاز به راه‌اندازی |
| **برق** | ☀️ فقط خورشیدی — نصب‌شده + فعال — کفایت برای ۱۶۲ نود |
| **بودجه** | Regime A = صفر دلار/ماه (تأیید مالک D-006) |
| **کد** | کامل — اما خاموش |
| **اولویت مالک** | ۱) اختاپوس کامل کن ۲) کامپیوترها رو کنترل کن ۳) تلگرام وصل بشه ۴) Coin Hunter Bot زنده بشه |
| **فاز مالک** | **شروع ماین واقعی** — میخواد بات هر هفته کوین پیدا کنه، ماین کنه، عوض کنه |

---

## 1. پاسخ‌های مالک (جمع‌بندی جلسه 2026-07-28)

| سوال | جواب | تأثیر |
|---|---|---|
| تعداد ریگ؟ | **۱۶۲ نود** (solar-swarm درسته، Hcash-era ۶ نود منسوخ) | Hardware Registry باید بازنویسی بشه |
| وضعیت ریگ؟ | **همه خاموش/ناکار** | فاز اول = راه‌اندازی فیزیکی |
| برق؟ | **فقط خورشیدی — نصب + فعال** ✅ | گیت برق پاس — <$0.05/kWh تأیید |
| ریگ‌ها کجا؟ | **سیدنی** — ایران فقط تحقیق بود (۶ ماه طول میکشه) | ساده‌تر: یک سایت فقط |
| خورشیدی فعال؟ | **بله، نصب + فعال** ✅ | بلوکر برق حذف شد |
| اولین کوین؟ | **Coin Hunter Bot زنده بشه — استراتژی خاص — هر هفته کوین پیدا، ماین، عوض** | اولویت: بات زنده |
| فاز بعدی؟ | **شروع ماین واقعی** | نه فقط آماده‌سازی |
| ایران؟ | **فقط تحقیق بود** — تحریم مسئله نیست | حذف بلوکر حقوقی |

### دستور مالک (کلمات دقیق):

> «یک ربات باید بسازیم برا ماین کردن کوین‌های نوظهور و طبق استراتژی خیلی خیلی خاص. فعلاً کوین هانتر رو باید زنده کنیم — اون هر هفته کوین پیدا کنه، ماین کنه، عوض کنه. بعداً بیشتر درستش میکنیم. **الآن بقیه رو درست کن — اصلاً کامپیوترها کنترل بشن با اختاپوس و اتصالاتش برقرار بشه، تلگرام جای مخصوصش پیدا بشه تو یکی از ربات‌ها وصل بشه، کنترل بشه.**»

### ترجمه به تسک:

```
Priority 1: اختاپوس کامل شود + کامپیوترها کنترل شوند
Priority 2: تلگرام وصل شود — جای مخصوص Mining پیدا شود
Priority 3: Coin Hunter Bot زنده شود — شروع ماین واقعی
Priority 4: استراتژی خاص هر-هفته-کوین-جدید
```

---

## 2. ساختار پروژه (نقشه کامل)

### 2A. مکان‌های کد (Canonical Paths)

```
📁 F:\backup\03 - Projects\Mining\
│
├── 📄 Root (13 فایل مدیریتی)
│   ├── PROJECT.md              ← شناسنامه پروژه + Active Context
│   ├── MANIFEST.yaml           ← Hard rules + spec
│   ├── VERDICT_QUEUE.md        ← ۶ تصمیم باز (MIN-V1..V6)
│   ├── DecisionLog.md          ← D2, D-005, D-006, D-007
│   ├── OpenQuestions.md        ← ۷ مجهول (بعضی حل‌شده با جواب مالک)
│   ├── Coin Scouting Framework.md
│   ├── Hardware Registry & Runbook.md  ← ⚠️ باید بازنویسی شود
│   ├── contracts/adapter.yaml  ← رابط Mining ↔ اختاپوس
│   └── ...
│
├── 📁 01 - Docs/ (اسناد معماری)
│   ├── NEXT_AGENT_HANDOFF_MINING_PREEXEC_v2.0.md  ← HANDOFF اصلی
│   ├── Phase Status - Execution Plan & Prompt v2.0.md  ← Truth Anchor
│   ├── 10-Step Roadmap -- Competitive Intel & Execution.md
│   ├── Coin-Hunter-Bot Architecture/  ← ۱۳ سند معماری کامل
│   ├── Strategy & Roadmap/ (7 PDF)
│   └── ...
│
├── 📁 02 - Code/
│   ├── 📁 Ai bots/
│   │   ├── 📁 QuantumAlphaBot/  ← بات اصلی شکار کوین (15+ module)
│   │   ├── 📁 sentinel/         ← داده‌گرد (CryptoQuant + LunarCrush)
│   │   ├── 📁 coordinator/      ← هماهنگ‌کننده بین بات‌ها
│   │   ├── 📁 fleet/            ← مدیریت ناوگان (REST :7700)
│   │   └── 📁 deploy/           ← دیپلویoment (systemd + ESP32)
│   │
│   ├── 📁 mining_preexec_mvp/  ← ابزار read-only قبل از اجرا
│   └── 📁 Robo-data/            ← نسل قبلی بات‌ها (legacy)
│
├── 📁 03 - Rigs/
│   ├── Mining-1/Hcash/          ← اسکریپت‌های deploy Hcash (6 node)
│   └── Mining-10- pro-plus/Verus coin/ ← مانیتور ورسکوین
│
├── 📁 04 - Research/
│   ├── SCOUT-B.md               ← تحقیق ARM mining (25 الگو)
│   └── 2026-07-14 solar-swarm-mining-research.md  ← طرح 162 نود
│
├── 📁 05 - Media/ (58 عکس + 2 دیاگرام)
│
└── 📁 mining_os/                ← زیر-OS Mining (متصل به اختاپوس)
    ├── core.py                  ← mining_beat() — نقطه ورود
    ├── loop.py                  ← tick(beat) — اتصال به heartbeat
    ├── organs/governance.py      ← گیت‌های fail-closed
    ├── organs/death_watch.py    ← D2 death-watch
    ├── brains/ (coin_brain, hardware_brain)
    ├── ui/tg_mining.py          ← منوی تلگرام Mining
    └── tests/ (20 تست سبز)
```

### 2B. اتصالات اختاپوس

```
📁 F:\backup\_ops\
├── legs/mining_leg.py           ← لگ Mining اختاپوس (2 brain)
├── wiring.py                    ← OCTOPUS_WIRE_MINING=1 (خط 696, 2363)
├── organism.py                  ← mining در business_legs
├── telegram_center/center.py    ← Mining = topic 24 (⛏ emoji)
├── telegram_center/render.py    ← آیکون pickaxe + digest cell
├── tests/test_mining_leg.py    ← 20 تست لگ
└── tests/test_mining_wiring.py ← 10 تست وایرینگ
```

### 2C. داشبورد (Nervous System)

```
📁 F:\backup\nervous-system\
├── extract_mining_data.py       ← استخراج state برای داشبورد
└── mining-data.js               ← window.MINING_DATA (readiness=50/100)
```

### 2D. اسکات دیجست‌ها

```
📁 F:\backup\00 - Inbox\scout-digests\
├── 2026-07-04 mining.md         ← VerusHash ~6.6 MH/s @ 9W + DERO
├── 2026-07-05 mining.md
└── 2026-07-06 mining.md         ← VerusHash merge-mining
```

---

## 3. وضعیت هر کامپوننت

| کامپوننت | وضعیت | تست | وصل به اختاپوس | یادداشت |
|---|---|---|---|---|
| **QuantumAlphaBot** | خاموش، کد کامل | ✅ | ❌ نیاز deploy | بات اصلی شکار کوین |
| **sentinel** | خاموش، کد کامل | ✅ | ❌ نیاز deploy | داده‌گرد CryptoQuant/LunarCrush |
| **coordinator** | خاموش، کد کامل | ✅ | ❌ نیاز deploy | پل بین بات‌ها |
| **fleet/manager** | خاموش، کد کامل | ✅ | ❌ نیاز deploy | REST API :7700 |
| **fleet/worker_agent** | خاموش | ✅ | ❌ نیاز deploy | Per-node agent |
| **mining_preexec_mvp** | کامل، read-only | ✅ | ✅ مستقیم | ابزار قبل از اجرا |
| **mining_os** | کامل، **فلگ خاموش** | ✅ 20 تست | ✅ organism.py:712 | mini-organism Mining |
| **mining_leg.py** | فعال (propose-only) | ✅ 20 تست | ✅ wiring.py | لگ اختاپوس — `live=False` |
| **nervous-system** | فعال (extract) | — | ✅ | داشبورد mining-data.js |
| **telegram_center** | فعال (topic 24) | — | ✅ | منوی تلگرام Mining |
| **deploy scripts** | موجود (Hcash-era) | — | — | نیاز بروزرسانی برای 162 نود |

---

## 4. Hard Rules (غیرقابل عبور)

```yaml
D-2:   "معیار abandon فقط survival: dev dead 8w, chain stalled, community dead"
D-10:  "هر buy/sell/withdraw = HARD_STOP — فقط انسان"
D-11:  "ایجنت هیچ‌وقت wallet/seed/private key نمی‌بینه"
D-20:  "SSH مستقیم ممنوع — فقط repo + deploy gate با verdict"
electricity: "<$0.05/kWh یا solar — بالاتر = HALT"
coin_selection: "فقط از Coin Scouting Framework"
D-006: "Regime A = صفر دلار/ماه"
```

---

## 5. بلوکرهای حل‌شده (با جواب مالک)

| بلوکر | قبلاً | الان (2026-07-28) |
|---|---|---|
| تعداد ریگ | تناقض ۶ vs 162 | ✅ **۱۶۲ نود** (solar-swarm درسته) |
| وضعیت فیزیکی | `[To measure]` | ✅ **همه خاموش** — سیدنی |
| برق | `[unknown]` fail-closed | ✅ **خورشیدی فعال** — پاس |
| ایران/تحریم | بحث باز | ✅ **فقط تحقیق بود** — حذف |
| فاز پروژه | پرسش | ✅ **شروع ماین واقعی** |

---

## 6. بلوکرهای باقی‌مانده

| بلوکر | شدت | برای حل نیاز به |
|---|---|---|
| **Hardware Registry خالی** | 🔴 CRITICAL | بازنویسی: ۱۶ OPI + 140 ESP32 + 2 FPGA — IP، مکان، وضعیت فیزیکی |
| **ريگ‌ها خاموش** | 🔴 CRITICAL | راه‌اندازی فیزیکی + تست شبکه + نصب OS |
| **کد خاموش** | 🔴 CRITICAL | deploy بات‌ها روی ریگ‌ها — نیاز verdict + دسترسی |
| **اتصال SSH/Tailscale** | 🔴 CRITICAL | بروزرسانی Runbook + تست اتصال (با verdict مالک) |
| **Wallet seed** | 🟡 MEDIUM | چرخش + ذخیره امن — مالک باید انجام بده |
| **Hashrate واقعی** | 🟡 MEDIUM | نیاز ریگ فعال — بنچمارک |
| **Coin Hunter Bot زنده** | 🟡 MEDIUM | deploy + وصل به ناوگان + تلگرام |
| **MIN-V1..V6 باز** | 🟢 LOW | بستن با evidence — V3, V5, V6 الان بسته‌ن |

---

## 7. VERDICT_QUEUE — وضعیت بعد از جواب مالک

| ID | تصمیم | وضعیت قبلی | الان (2026-07-28) |
|---|---|---|---|
| MIN-V1 | چند rig؟ | open | **✅ ۱۶۲ نود — باید Registry بازنویسی بشه** |
| MIN-V2 | برق <$0.05? | open | **✅ خورشیدی فعال — PASSED** |
| MIN-V3 | هیچ mining فعلی؟ | open | **✅ همه خاموش — SAFETY CONFIRMED** |
| MIN-V4 | Registry پر شود؟ | open | **🔄 باید بازنویسی بشه با ۱۶۲ نود** |
| MIN-V5 | wallet access صفر؟ | open | **✅ POLICY CONFIRMED** |
| MIN-V6 | coin scouting فقط report؟ | open | **⚠️ نه — مالک میخواد ماین واقعی — SCOPE CHANGE** |

### ⚠️ تغییر محدوده MIN-V6:

مالک خواسته Coin Hunter Bot **نه فقط گزارش بده بلکه واقعاً ماین کنه و کوین عوض کنه**. این با D-10 (HARD_STOP مالی) و محدوده فعلی MIN-V6 در تناقضه. **نیاز verdict جدید مالک**: آیا بات حق خرید/فروش/تعویض خودکار کوین رو داره یا فقط ماین میکنه و تصمیم خرید/فروش با مالکه؟

---

## 8. نقشه راه پیشنهادی برای ایجنت ارشد

### فاز ۱: زیرساخت (قبل از هر ماین)

```
[ ] 1.1 بازنویسی Hardware Registry — ۱۶ OPI + 140 ESP32 + 2 FPGA
[ ] 1.2 بروزرسانی OpenQuestions — حذف موارد حل‌شده
[ ] 1.3 بستن VERDICT_QUEUE — V1, V2, V3, V5 (با evidence)
[ ] 1.4 بروزرسانی DecisionLog — ثبت جواب‌های مالک 2026-07-28
[ ] 1.5 ویرایش PROJECT.md — Active Context جدید
[ ] 1.6 ریجستری تلگرام Mining در topic اختصاصی
```

### فاز ۲: اختاپوس + کنترل کامپیوترها

```
[ ] 2.1 mining_os فلگ ON بشه (OCTOPUS_WIRE_MINING_OS)
[ ] 2.2 mining_leg.py به live=True ارتقا (وقتی ریگ‌ها وصل شدند)
[ ] 2.3 تلگرام Mining کامل وصل بشه به topic 24
[ ] 2.4 نوار داشبورد mining-data.js بروز بشه
[ ] 2.5 organism.py ریستارت با فلگ‌های جدید
```

### فاز ۳: راه‌اندازی ریگ‌ها

```
[ ] 3.1 تست اتصال SSH/Tailscale به اولین OPI
[ ] 3.2 نصب OS + پیکربندی روی OPI-1
[ ] 3.3 بنچمارک هش‌ریت واقعی
[ ] 3.4 deploy fleet/manager.py
[ ] 3.5 fleet/worker_agent روی هر نود
[ ] 3.6 watchdog + مانیتورینگ
```

### فاز ۴: Coin Hunter Bot زنده

```
[ ] 4.1 QuantumAlphaBot deploy + وصل به ناوگان
[ ] 4.2 sentinel deploy — داده‌گرد فعال
[ ] 4.3 coordinator deploy — هماهنگ‌کننده بین بات‌ها
[ ] 4.4 اولین اسکن کوین
[ ] 4.5 اولین ماین واقعی
[ ] 4.۶ استراتژی هر-هفته-کوین-جدید
```

---

## 9. کاندیداهای کوین (از تحقیقات)

| کوین | الگوریتم | ARM-viable | هش‌ریت RK3588 | توان | یادداشت |
|---|---|---|---|---|---|
| **Monero (XMR)** | RandomX | ✅ | ~1000 H/s | ~15W | پیشنهاد نقشه راه — نقد: ASIC X5/X9 تهدید |
| **VerusCoin (VRSC)** | VerusHash | ✅ | ~6.6 MH/s | ~9W | بهترین راندمان — merge-mining |
| **DERO** | AstroBWT | ✅ | TBD | TBD | سومین هدف ARM |
| **Salvium** | TBD | ✅? | — | — | کاندید solar-swarm |
| **Wownero** | RandomX | ✅ | — | — | Monero fork |
| **CoinCync** | TBD | — | — | — | کاندید solar-swarm |

> ⚠️ Coin Hunter Bot باید طبق Coin Scouting Framework انتخاب کنه — لانچ <3 ماه + death-watch + CPU/ARM-viable

---

## 10. فایل‌های خواندنی برای ایجنت ارشد (ترتیب)

```yaml
priority:
  1: "03 - Projects/Mining/01 - Docs/NEXT_AGENT_HANDOFF_MINING_PREEXEC_v2.0.md"
     reason: "Handoff اصلی — قوانین + نقشه 10 مرحله"
  2: "03 - Projects/Mining/PROJECT.md"
     reason: "شناسنامه + Active Context — باید بروز بشه"
  3: "03 - Projects/Mining/VERDICT_QUEUE.md"
     reason: "6 تصمیم — الان 4 تا قابل بسته‌شدن"
  4: "03 - Projects/Mining/MANIFEST.yaml"
     reason: "Hard rules + spec"
  5: "03 - Projects/Mining/DecisionLog.md"
     reason: "تاریخچه — باید جواب‌های جدید اضافه بشه"
  6: "03 - Projects/Mining/Hardware Registry & Runbook.md"
     reason: "⚠️ باید بازنویسی بشه با 162 نود"
  7: "03 - Projects/Mining/mining_os/README.md"
     reason: "زیر-OS Mining — فلگ خاموش"
  8: "_ops/legs/mining_leg.py"
     reason: "لگ اختاپوس — live=False"
  9: "03 - Projects/Mining/01 - Docs/Coin-Hunter-Bot Architecture/00 - MASTER-ARCHITECTURE.md"
     reason: "معماری کامل بات"
  10: "03 - Projects/Mining/Coin Scouting Framework.md"
      reason: "چارچوب انتخاب کوین"
```

---

## 11. هشدارها و ریسک‌ها

| ریسک | شدت | کاهش |
|---|---|---|
| D-10 vs استراتژی «هر هفته کوین عوض کن» | 🔴 | مالک باید مشخص کنه: بات فقط ماین یا خرید/فروش هم؟ |
| ریگ‌ها خاموش — وضعیت فیزیکی ناشناخته | 🔴 | نیاز بررسی فیزیکی قبل از deploy |
| ESP32 فقط سنسور — ماین واقعی نمیکُنه | 🟡 | 140 ESP32 = مانیتورینگ، 16 OPI = ماین |
| Monero ASIC تهدید | 🟡 | D2 death-watch پوشش میده |
| Regime A = صفر دلار — API پولی ممنوع | 🟡 | Claude تعاملی اپراتور OK، API metered ممنوع |
| wallet seed در چرخش | 🟡 | مالک باید انجام بده — بلوکر اجرای مالی |

---

## 12. نکات فنی برای ایجنت ارشد

1. **OCTOPUS_WIRE_MINING=1** الان فعاله — mining_leg در organism اجرا میشه ولی `live=False` برمیگردونه چون داده واقعی نداره
2. **OCTOPUS_WIRE_MINING_OS** هنوز uncommitted و خاموشه — فعال‌سازی در `mining_os/ACTIVATION.md`
3. **Telegram Mining** = topic 24 در center.py — آیکون pickaxe — ولی منوی `tg_mining.py` نیاز به وصل شدن واقعی داره
4. **کد Ai bots/** هم در `03 - Projects/Mining/02 - Code/` هست هم در `_code/Mining/` (کپی از NONMD-TRIAGE) — canonical = پروژه
5. **Hcash scripts** تاریخچه‌ای هستن — باید برای کوین جدید بازنویسی بشن
6. **Fleet Manager** :7700 REST — نیاز deploy روی OPI اصلی
7. **QuantumAlphaBot** 7 مرحله pipeline: GemHunter → ScoutForensics → LLM → Veto → QuantumAlloc → PaperTrade → SelfImprove
8. **Coin Scouting Framework**: لانچ <3 ماه، CPU/ARM-viable، survival-based death-watch
9. **نیاز به verdict مالک**: MIN-V6 باید تغییر محدوده بگیره (از report-only به execute)
10. **استراتژی «هر هفته کوین عوض کن»**: نیاز به مشخص شدن — آیا تعویض دستی یا خودکار؟ خرید/فروش کوین = D-10 HARD_STOP

---

## 13. خلاصه تک‌خطی برای ایجنت ارشد

> **مالک تأیید کرده: ۱۶۲ نود در سیدنی (همه خاموش)، خورشیدی فعال، Regime A (صفر دلار)، شروع ماین واقعی. اولویت: ۱) اختاپوس کامل ۲) کنترل کامپیوترها ۳) تلگرام Mining ۴) Coin Hunter Bot زنده. بلوکر اصلی: Hardware Registry خالی + ریگ‌ها خاموش + تغییر محدوده MIN-V6. همه قواعد D-2/D-10/D-11/D-20 برقرار.**

---

---

## 14. تحلیل فایل‌های Zip پیوست (2026-07-28)

### منبع
دو فایل zip از `C:\Users\Armin\Downloads\`:
- **files(3).zip** (6.8 KB) — CLAUDE.md + KICKOFF-PROMPT.md
- **files(2).zip** (32 KB) — SURVIVAL-FILTER.md + OPS-RUNBOOK.md + CANDIDATE-REGISTER.md + PROJECT.md + OpenQuestions.md + DecisionLog.md + INDEX.md + mining-bootstrap.zip (inner)

### نتیجه: این‌ها یک **پروپوزال bootstrap یتیم** هستند — هرگز اعمال نشدند

| شواهد | توضیح |
|---|---|
| ❌ هیچ‌کدوم در رپو نیستن | CLAUDE.md، SURVIVAL-FILTER.md، OPS-RUNBOOK.md، CANDIDATE-REGISTER.md، KICKOFF-PROMPT.md در رپو وجود ندارن |
| ❌ هیچ git history نیست | هیچ‌کدوم jamais commit یا delete نشدن |
| ❌ Phase خروجی ساخته نشد | INVENTORY.md و RECONCILE.md که ALIGN Phase 1-2 تولید میکنه، هرگز ساخته نشدن |
| ✅ رپو قبلاً mature بود | PROJECT.md از 2026-07-03، INDEX 114 خطی، MANIFEST.yaml، REGISTRY.md، Coin Hunter Bot معماری 13 سند |
| ✅ رپو بعداً ارتقا پیدا کرد | 2026-07-18: D-006 Regime A، معماری Coin Hunter Bot سنتز شد |

### تایم‌لاین بازسازی‌شده

```
2026-07-03..06  → رپو Mining ساختار گرفته (PROJECT.md, INDEX.md, code)
2026-07-12     → Mining pre-exec MVP + Octopus leg فعال شد
2026-07-14     → ⬅ یک جلسه Claude Code bootstrap skeleton تولید کرد
                 فایل‌ها zip شدند و به Downloads فرستاده شدند
                 هرگز وارد رپو نشدن
2026-07-14+    → رپو مستقل ادامه داد: research relocate, hardware discrepancy
2026-07-18     → معماری Coin Hunter Bot (13 سند) + D-006 Regime A
2026-07-28     → اسکن کامل + تحلیل zip artifacts (این جلسه)
```

### مقایسه محتوا: Zip vs رپو

| فایل Zip | نسخه رپو | وضعیت |
|---|---|---|
| CLAUDE.md (منشور Mining، 8 hard rule) | ❌ وجود ندارد | **Zip-specific — هرگز اعمال نشد** |
| KICKOFF-PROMPT.md (پرامپت جلسه اول) | ❌ وجود ندارد | **یک‌بار مصرف — هرگز استفاده نشد** |
| SURVIVAL-FILTER.md (99 خط، G1-G5, Scorecard A-F) | Coin Scouting Framework.md (44 خط) | **Zip دقیق‌تره ولی رپو موجود و فعال هست** |
| OPS-RUNBOOK.md (74 خط، isolation, monitoring) | RUNBOOK.md (54 خط، INFORM-only) | **متفاوت — Zip اجرایی، رپو safety-only** |
| CANDIDATE-REGISTER.md (37 خط، C-001 XMR) | ❌ وجود ندارد | **Zip-specific — هرگز اعمال نشد** |
| PROJECT.md (40 خط، bootstrap) | PROJECT.md (86 خط، mature) | **رپو خیلی کامل‌تر و به‌روزتر** |
| DecisionLog.md (D-001..D-004) | DecisionLog.md (D2, D-10, D-20, D-005..D-007) | **دستگاه تصمیم متفاوت — رپو کامل‌تر** |
| OpenQuestions.md (OQ-1..8) | OpenQuestions.md (Q1..7) | **همپوشانی جزئی — فرمت متفاوت** |
| INDEX.md (31 خط، اسکلت) | INDEX.md (114 خط، کامل) | **رپو خیلی کامل‌تر** |

### نکات ارزشمند از Zip (که رپو نداره)

| محتوای ارزشمند | اقدام پیشنهادی |
|---|---|
| **SURVIVAL-FILTER.md** — Gateهای G1-G5 + Scorecard عددی A-F با وزن و آستانه (≥70 وارد، <50 رد) | ✅ ادغام بشه یا جایگزین Coin Scouting Framework بشه |
| **CANDIDATE-REGISTER.md** — رجیستر ساختاریافته با وضعیت‌ها (screening→rejected/watchlist/approved→mining→holding→exited) | ✅ در فاز Coin Hunter Bot ساخته بشه |
| **OPS-RUNBOOK.md** — Build-from-source (Gate G-2)، Kill-switch، monitoring 2 دقیقه‌ای روزانه | ✅ بخش‌هایی有价值 — ادغام با RUNBOOK فعلی |
| **CLAUDE.md §1** — قاعده «Binary isolation» (VM mandatory) | ⚠️ با ۱۶۲ نود فیزیکی OPI/ESP32 این قاعده مرتبط نیست — ریگ‌ها ماشین ایزوله هستن |
| **CLAUDE.md §3** — Epistemic tagging اجباری [FACT]/[EST]/[OPINION] | ✅ خوبه — تو اسناد جدید اعمال بشه |
| **_memory/** — حافظه فشرده پروژه | ❌ رپو خودش کامله — نیاز نیست |

### تصمیم نهایی

> **Zip artifacts رو نگه دار ولی بعنوان reference-only.** رپو Mining از این پروپوزال جلوتر رفته. اما SURVIVAL-FILTER.md و CANDIDATE-REGISTER.md مفاهیم ارزشمند دارن که باید تو فاز Coin Hunter Bot ساخته بشن. CLAUDE.md و KICKOFF-PROMPT.md منسوخ هستن — رپو خودش MANIFEST.yaml + REGISTRY.md + RUNBOOK.md داره.

---

*پایان اسکن v1.1 — 2026-07-28*
