> **⚠️ سندِ تاریخی (۲۰۲۶-۰۷-۱۷/۱۸).** این گزارشِ پروبِ آن تاریخ است و
> بازتابِ وضعیتِ **پیش از** برش‌های ۰-۳ ِ طرحِ هیدرید کنترل‌پلین. سؤالاتِ بازِ این
> سند (مثل «Source of Truth کدام است؟») در `02-OCTOPUS-KNOWLEDGE-SNAPSHOT.md` پاسخ
> داده شده‌اند. برایِ شناختِ به‌روز `00-README-START-HERE.md` و `04-NEXT-AGENT-MEGAPROMPT.md`
> را بخوان. این دادهٔ پروب برایِ پشت‌زمینه نگه داشته شده، نه برایِ عمل.

# 07 — طراحی حلقه‌ی تقاضای آلوستاتیک (Allostatic Demand Loop)

> **مسیر:** `F:\backup\شناخت اختاپوس\07-ALLOSTATIC-DEMAND-LOOP-DESIGN.md`
> **تاریخ:** 2026-07-17
> **وضعیت:** DESIGN ONLY (Phase 1). هیچ patch اعمال نشده. هیچ فایل production دست‌نخورده.
> **محل کار:** فقط داخل `F:\backup\شناخت اختاپوس\`. هیچ‌چیز به Desktop نمی‌رود.
> **قرارداد برچسب:** `[FACT]` = شاهد مستقیم (file:line) · `[INFERENCE]` = نتیجه از FACT ·
> `[HYPOTHESIS]` = قابل‌راست‌آزمایی · `[UNKNOWN]` = هنوز تست‌نشده.
> **منابع:** این سند، یافته‌های `06-DEEPER-MUTATION-PROBE-REPORT-2026-07-17.md` را با
> مدل سه‌قلبی (Energy/Epistemic/Coherence) ادغام می‌کند که از دو یادداشت پژوهشی استخراج شد.

---

## فهرست

1. [Problem: freeze-on-fear در برابر تقاضای آلوستاتیک](#۱-problem)
2. [نگاشت زیست‌شناختی (اختاپوس) → جدول اندام‌ها](#۲-نگاشت-زیستشناختی)
3. [تغییر قانون کنترل: depleted → EXTEND](#۳-تغییر-قانون-کنترل)
4. [State schema برای `state/demand-manifest.json`](#۴-state-schema)
5. [نقشه‌ی وایرینگ](#۵-نقشه‌ی-وایرینگ)
6. [برنامه‌ی پیاده‌سازی Phase 0 / 1 / 2](#۶-برنامه‌ی-پیاده‌سازی)
7. [ایمنی: auto-revert، propose-only، fail-soft، دایجست تلگرام](#۷-ایمنی)
8. [آزمون‌های پذیرش (۸ مورد لبه‌ای)](#۸-آزمون‌های-پذیرش)
9. [فهرست UNKNOWNهای باز](#۹-fهرست-unknownهای-باز)
10. [مگاپرامپت برای ایجنت پیاده‌ساز (فقط Phase 0، $0)](#۱۰-مگاپرامپت)

---

## ۱. Problem

### ۱.۱ صورت مسئله

`[FACT]` `cardiac.py:108-163` یک `BeatBudget` با `daily_cap` دارد. وقتی `spent >= daily_cap`
می‌شود، `depleted = True` و `mode = "resting-only"` برمی‌گردد.

`[FACT]` `state/ORGANISM-STATE.json` (در زمان گزارش ۰۶): `cardiac.budget.depleted: true`،
`spent: 322`، `daily_cap: 288`، `remaining: 0`.

`[FACT]` `cortex/stress.py:58-75` تابع `_legs_stress` فقط شمارشِ رویدادهای `selfheal-events.jsonl`
در ۲۴ ساعت گذشته را به‌عنوان منبع استرس پاها می‌خواند (`n/8.0`).

`[FACT]` جست‌وجو برای مصرف‌کنندگانِ `cardiac.depleted` در `wiring.py`، `organism.py`،
`cortex/*.py`، `legs/leg.py` **هیچ خروجی‌ای نداد**. یعنی سیگنال `depleted` تولید می‌شود
ولی در حال حاضر **چیزی پاها را روی آن freeze نمی‌کند**.

`[INFERENCE]` این یافته، نتیجه‌گیری گزارش ۰۶ («پاها در حالت fear متوقف شده‌اند») را اصلاح
می‌کند: fear **گزارش می‌شود اما اعمال نمی‌شود**. حلقه‌ی آلوستاتیک **وجود ندارد**، نه
اینکه خراب باشد.

### ۱.۲ چرا این مشکل است

`[INFERENCE]` دو حالت بد:
- **اگر freeze پیاده می‌شد:** ارگانیسم در استرس از کار می‌افتاد — ضدِ هدفِ آلوستازی.
- **همان‌طور که هست (اعمال نمی‌شود):** استرس **هدر می‌رود**. هیچ تقاضا، هیچ جستجو، هیچ
  ارتقای مدل از آن بیرون نمی‌آید. سیگنال تزئینی است.

`[HYPOTHESIS]` اگر یک حلقه‌ی تقاضا وصل شود، همان استرسی که الان هدر می‌رود می‌تواند
ورودیِ جستجوی ابزار/داده/API شود — بدون آنکه نیاز به freeze باشد.

**آزمون:** `state/demand-manifest.json` را بساز، یک depleted شبیه‌سازی کن، ببین آیا
demand تولید می‌شود و آیا `model_router` در نتیجه روی Ollama می‌ماند (نه Fugu).
**Falsifier:** اگر حتی با demand، router بدون نظر governor به tier بالاتر برود، حلقه وصل نیست.

---

## ۲. نگاشت زیست‌شناختی

> اختاپوس واقعی سه قلب، سیستم عصبی توزیع‌شده، و بازوهای نیمه‌مستقل دارد. این نگاشت،
> آن آناتومی را به سه «قلبِ تصمیم‌گیر» نگاشت می‌کند که از یادداشت پژوهشی پیوست استخراج شد.

### ۲.۱ جدول اندام‌ها

| قلبِ زیستی | نقش در تصمیم | معادل در Octopus | ورودی | خروجی (mode) |
|---|---|---|---|---|
| ❤️ **Heart-Energy** (قلب اصلی) | چقدر منابع مصرف کنیم | `cardiac.py` + `budget/` | forecast هزینه/token، `cardiac.depleted`، pressure | GO / EXTEND / CONTAIN / ESCALATE / HALT |
| 🧠 **Heart-Epistemic** (قلب شناختی) | چقدر به دانش/سنجش اعتماد کنیم | `epistemics/` + `cortex/self_model.py` | flag provenance، contradiction، metric validity | GO / EXTEND / CONTAIN / ESCALATE / HALT |
| 🔗 **Heart-Coherence** (قلب پیوستگی) | اندام‌ها هم‌راستا هستند؟ | `cortex/innervation.py` + `neural/` | dead-spots، liveness، wiring disagreement | GO / EXTEND / CONTAIN / ESCALATE / HALT |

`[FACT]` سه منبع داده برای این قلب‌ها همین الان زنده‌اند:
- `state/cortex/stress-latest.json` (Energy/Coherence)
- `state/cortex/innervation-latest.json` (Coherence — `cortex/innervation.py:64-86`)
- `epistemics/` (Epistemic — ولی `epi-ledger.jsonl` وجود ندارد `[FACT]`)

### ۲.۲ انتخابِ تصمیم نهایی — Governor با «حداکثر محدودیت برنده»

| Energy | Epistemic | Coherence | تصمیم نهایی |
|---|---|---|---|
| GO | GO | GO | اجرای عادی با Ollama |
| GO | CONTAIN | GO | اجرا، اما بدون اتکا به metric مشکوک |
| EXTEND | any | any | `demand-manifest` + پژوهش local/web |
| CONTAIN | CONTAIN | GO | فقط diagnose فقط‌خواندنی |
| any | any | CONTAIN | فرمان سراسری ممنوع؛ probe محلی |
| ESCALATE (c≥0.7) | high-c | high-c | Fugu با TTL + auto-revert |
| ESCALATE (c<0.7) | any | any | → EXTEND (escalation ناباور) |
| HALT (hard risk) | any | any | توقف سخت + هشدار انسان |

`[HYPOTHESIS]` قانون طلایی: **«نمی‌دانم، پس Fugu را روشن کن» غلط است.** درست: «نمی‌دانم، پس
`EXTEND`/demand». `ESCALATE` فقط وقتی اعتبار می‌شود که *خودِ تشخیصِ escalation* با confidence بالا باشد.
**آزمون:** `uncertainty=0.9` + `value=high` → نباید ESCALATE یا HALT خودکار شود.

---

## ۳. تغییر قانون کنترل

### ۳.۱ قانون فعلی (ضمنی/گزارش‌شده)

```text
if cardiac.depleted:
    mode = "resting-only"        # cardiac.py:151
# ولی چیزی این mode را مصرف نمی‌کند → سیگنال مرده/تزئینی
```

### ۳.۲ قانون پیشنهادی (آلوستاتیک)

```text
# Governor (جدول بالا) تصمیم نهایی را می‌گیرد. نه قلبِ Energy به‌تنهایی.

if hard_risk:                                          # cancer/loop/ban/corruption
    HALT + هشدار انسان
elif cardiac.depleted and not hard_risk:
    EXTEND  + demand(type="processing", because="cardiac depleted")
    # پاها متوقف نمی‌شوند؛ به حالتِ جستجوی ابزار/داده می‌روند
    # model_router constraint = "ollama_only" (نه Fugu، نه paid)
elif epistemics.flag_on and validity_confidence < MIN:
    CONTAIN metric + demand(type="understanding", because="metric validity unknown")
elif dead_spot and confidence_high:
    probe محلیِ همان leg (نه restart سراسری)
else:
    GO
```

### ۳.۳ محدودیت‌های hard-stop (تغییرناپذیر)

این‌ها حتی اگر همه‌ی قلب‌ها GO بدهند هم HALT می‌کنند:
- `sigma_cancer` (اگر `nociceptor.py` سیگنال دهد) — `[UNKNOWN]`: مسیر مصرف nociceptor هنوز تست‌نشده.
- infinite loop / runaway resource
- data corruption risk
- external-account / financial / ban-risk
- failed rollback یا failed integrity check

`[FACT]` این فهرست با قانون `OCTOPUS-WIRE_*` و `money_gate` فعلی سازگار است (`budget/organ_gate.py:60,140`).

---

## ۴. State schema

> فایلِ پیشنهادی: `F:\backup\_ops\state\demand-manifest.json` (این فایل هنوز وجود ندارد — `[FACT]`).
> برای Phase 0 فقط-read/write در `state/` است؛ production را تغییر نمی‌دهد.

### ۴.۱ Schema (JSON، append-safe، TTLدار)

```json
{
  "schema": "demand-manifest.v1",
  "ts": "2026-07-17T22:00:00",
  "tick_source": "organism:7646",
  "hearts": {
    "energy": {
      "mode": "EXTEND",
      "confidence": 0.42,
      "uncertainty": 0.58,
      "reason": "cardiac depleted (322/288)",
      "evidence_refs": ["state/ORGANISM-STATE.json:cardiac.budget"]
    },
    "epistemic": {
      "mode": "CONTAIN",
      "confidence": 0.20,
      "uncertainty": 0.80,
      "reason": "epistemics flag on but README says off; epi-ledger absent",
      "evidence_refs": ["epistemics/README.md", "wiring.py:544", "OCTOPUS-flags.cmd"]
    },
    "coherence": {
      "mode": "EXTEND",
      "confidence": 0.55,
      "uncertainty": 0.45,
      "reason": "pacemaker dead-spot (1/10 organs)",
      "evidence_refs": ["state/cortex/innervation-latest.json:dead_spots"]
    }
  },
  "governor": {
    "final_mode": "EXTEND",
    "winner_heart": "energy",
    "rule": "max-restriction-wins; ESCALATE underconfident->EXTEND",
    "constraints": ["ollama_only", "no_paid_api", "no_global_command"]
  },
  "demands": [
    {
      "demand_id": "d-energy-001",
      "type": "processing",
      "because": "cardiac depleted; daily_cap 288 vs spent 322",
      "needed": ["free budget", "reduce concurrency", "defer non-critical LLM"],
      "blocked_action": "model_router escalation to fugu/paid",
      "urgency": "medium",
      "confidence": 0.42,
      "ttl_sec": 3600,
      "owner": "organism.py",
      "created_tick": 7646,
      "auto_revert_at": "2026-07-17T23:00:00"
    },
    {
      "demand_id": "d-epistemic-001",
      "type": "understanding",
      "because": "epistemics flag contradicts README; epi-ledger missing",
      "needed": ["flag provenance check", "kill-switch verification", "baseline comparison"],
      "blocked_action": "use epistemics score for routing",
      "urgency": "high",
      "confidence": 0.80,
      "ttl_sec": 86400,
      "owner": "epistemics/run_offloop.py",
      "created_tick": 7646,
      "auto_revert_at": "2026-07-18T22:00:00"
    },
    {
      "demand_id": "d-coherence-001",
      "type": "awareness",
      "because": "pacemaker dead-spot; two beat sources disagree",
      "needed": ["local probe of spine leg", "verify beat provenance"],
      "blocked_action": "global restart of organism",
      "urgency": "medium",
      "confidence": 0.55,
      "ttl_sec": 7200,
      "owner": "cortex/innervation.py",
      "created_tick": 7646,
      "auto_revert_at": "2026-07-17T23:30:00"
    }
  ],
  "digest": {
    "top_n": 3,
    "last_sent": null,
    "last_sent_ts": null
  }
}
```

### ۴.۲ فیلدها

| فیلد | نوع | اجباری | توضیح |
|---|---|---|---|
| `schema` | str | ✓ | نسخه‌بندی. تغییر ناسازگار = `demand-manifest.v2`. |
| `ts` | ISO | ✓ | زمان آخرین بازنویسی. |
| `hearts.<h>.mode` | enum | ✓ | GO/EXTEND/CONTAIN/ESCALATE/HALT. |
| `hearts.<h>.confidence` | float[0,1] | ✓ | `1 - effective_uncertainty`. |
| `hearts.<h>.evidence_refs` | list[str] | ✓ | فایل/سطر/لاگ — بدون evidence، `UNKNOWN`. |
| `governor.final_mode` | enum | ✓ | تصمیم نهایی طبق جدول §۲.۲. |
| `governor.constraints` | list[str] | ✓ | محدودیت‌هایی که router و legs باید رعایت کنند. |
| `demands[].type` | enum | ✓ | `processing`/`understanding`/`awareness`. |
| `demands[].blocked_action` | str | ✗ | چه کاری نباید انجام شود تا demand برطرف شود. |
| `demands[].ttl_sec` | int | ✓ | بعد از این، demand auto-expire. |
| `demands[].auto_revert_at` | ISO | ✓ | زمان ازبین‌رفتن (محدودیت موقت). |
| `demands[].owner` | str | ✓ | کدام ماژول تقاضا را تولید کرده. |
| `digest.top_n` | int | ✓ | پیش‌فرض ۳ — دایجست تلگرام. |

### ۴.۳ اعتبار مؤثر (effective confidence)

از یادداشت پژوهشی پیوست، با استناد به شواهد:

```text
confidence = (1 - uncertainty)
           * exp(-freshness_sec / 120.0)
           * min(1.0, evidence_count / 3.0)
           * (1 - disagreement)
```

`[INFERENCE]` این فرمول اطمینان را برای داده‌ی کهنه، تک‌منبعی، و اختلافِ بین predictorها
تنبیه می‌کند. اگر `epistemics` فقط یک منبعِ مشکوک دارد، confidence پایین می‌ماند حتی اگر
uncertainty ظاهراً پایین باشد.

---

## ۵. نقشه‌ی وایرینگ

> هیچ ماژول جدیدی الزامی نیست. همه‌ی نقاط اتصال، روی کدِ موجودند.

```
              ┌──────────────── organs (state producers) ─────────────────┐
              │                                                             │
   cardiac.py:154  stress.py:96-111  innervation.py:64-86  epistemics/*     │
   (BeatBudget)    (subsystem map)   (dead-spots)         (off-loop)         │
              │          │                │                   │             │
              └──────────┴───────► demand_loop (NEW, $0) ◄────┘             │
                                       │                                    │
                          ┌────────────┼─────────────┐                      │
                          ▼            ▼             ▼                      │
                   state/demand-   governor     model_router constraints     │
                   manifest.json   (max-rest)   ("ollama_only","no_paid")    │
                          │            │             │                      │
                          ▼            ▼             ▼                      │
                 ┌─ daily digest ─┐  HALT/EXTEND  ask() stays on local       │
                 │  center.py:391  │                                          │
                 │  render_leg_    │                                          │
                 │  digest(leg,…)  │                                          │
                 └────────────────┘                                          │
                                       │                                      │
                              web_research ($0) ← EXTEND triggers search     │
                                       │                                      │
                              doctor/box ← demand type=understanding          │
                                       │                                      │
                              money_gate (L4) ← only via human verdict        │
              └─────────────────────────────────────────────────────────────┘
```

### ۵.۱ جدول وایرینگ

| اندام | ورودی از | خروجی به | نقطه‌ی اتصال (`file:line` یا UNKNOWN) |
|---|---|---|---|
| Heart-Energy | `cardiac.status()` | demand-manifest.hearts.energy | `cardiac.py:154` (status) · مصرف‌کننده = UNKNOWN (هیچ‌چیز الان نمی‌خواند) |
| Heart-Epistemic | `epistemics/run_offloop.py` + flag provenance | demand-manifest.hearts.epistemic | `wiring.py:544` (flag) · `epistemics/README.md` (kill-switch) |
| Heart-Coherence | `cortex/innervation.py:64-86` | demand-manifest.hearts.coherence | `state/cortex/innervation-latest.json` (زنده) |
| Governor | هر سه قلب | `final_mode` + `constraints` | NEW: `demand_loop.py` (پیاده‌سازی Phase 1) |
| model_router | `governor.constraints` | ماندن روی Ollama | `cortex/model_router.py:128` (`ask()`) · اتصال = UNKNOWN (الان constraint نمی‌خواند) |
| daily digest | `demands[]` | پیام تلگرام (۳ مورد برتر) | `telegram_center/center.py:391-422` (`render_leg_digest`) |
| doctor/box | demand type=understanding | RFC (propose-only) | `doctor/doctor.py:794-890` (`_run_box_cycle`) |
| web_research | demand EXTEND | جستجوی $0 | `work-log.jsonl` نشان می‌دهد `$0` فعال است |
| money_gate | خرید API | human verdict (L4) | `budget/organ_gate.py:60,140` + `model_router.py:60` (`paid_gate`) |

`[INFERENCE]` بزرگ‌ترین شکافِ وایرینگ: `model_router.ask()` **هنوز constraint از governor
نمی‌خواند**. این مهم‌ترین نقطه‌ی اتصال Phase 1 است.

---

## ۶. برنامه‌ی پیاده‌سازی

> هر فاز، یک patch کوچک، با rollback و test.

### Phase 0 — تشخیص فقط‌خواندنی ($0، بدون تغییر production)

هدف: راست‌آزمایی فرضیه‌های گزارش ۰۶ قبل از طراحی نهایی.

| # | کار | فایل | شواهد موردنیاز |
|---|---|---|---|
| 0.1 | راستی‌آزمایی pacemaker dead-spot | `cortex/innervation.py:64-86`، `chrono.py` | آیا دو منبع beat وجود دارد؟ کدام sla_min نقض می‌شود؟ |
| 0.2 | راستی‌آزمایی stale-boot | `state/ORGANISM-STATE.json.started` در برابر `git log -1 organism.py` | آیا سایدکارِ نسخه غایب است چون بوت قدیمی است؟ |
| 0.3 | راستی‌آزمایی epistemics kill-switch | `epistemics/README.md` در برابر `wiring.py:544` + `OCTOPUS-flags.cmd` | آیا `make_epistemics` در runtime واقعاً None برمی‌گرداند؟ |
| 0.4 | راستی‌آزمایی «fear اعمال نمی‌شود» | grep مصرف‌کنندگانِ `cardiac.depleted` | `[FACT]` این کار انجام شد: خروجی خالی بود. |
| 0.5 | خط‌مشیِ baseline هر leg | `state/pulse/work-log.jsonl` | liveness، age، error rate، cost |

**خروجی Phase 0:** یک فایل truth-map در `شناخت اختاپوس/` (نه production).

### Phase 1 — DESIGN (همین سند + patch proposals)

| Patch ID | هدف | فایل‌های مجاز | خطوط تقریبی |
|---|---|---|---|
| **P1-A** | `demand_loop.py` (محاسبه‌ی hearts + governor) | NEW در `شناخت اختاپوس/` (سند/spec) | — |
| **P1-B** | تعریف schema `demand-manifest.v1` | همین سند §۴ | — |
| **P1-C** | قرارداد دایجست تلگرام (۳ مورد) | همین سند §۷.۴ | — |

### Phase 2 — PATCH PROPOSALS ONLY (بدون اعمال)

هر patch جداگانه، با این فیلدها:
- Patch ID و purpose
- فایل(های) تحت تأثیر + محدوده‌ی خط
- قبل / بعدِ پیشنهادی
- چرا کوچک‌ترین تغییر امن است
- baseline metric
- نتیجه‌ی مورد انتظار
- روش shadow / dry-run
- آستانه‌ی پذیرش
- روش rollback
- نیاز به human approval

**Patch‌های Phase 2 کاندید:**

| Patch ID | هدف | تأثیر |
|---|---|---|
| **P2-1** | `demand_loop.py` واقعی در `_ops/` | NEW file · `$0` · propose-only |
| **P2-2** | `model_router.ask()` بخواند `governor.constraints` | `cortex/model_router.py:128` · اگر `ollama_only`، tier بالاتر بازگردانده شود |
| **P2-3** | `organism.py` در هر tick، `demand-manifest.json` را بازنویسد | `organism.py:312-360` (داخل حلقه) |
| **P2-4** | `center.py` دایجست روزانه از `demands[]` بسازد | `telegram_center/center.py:391` |
| **P2-5** | kill-switch واقعی epistemics: اگر upstream empty → None | `epistemics/README.md` + `wiring.py:544` |

`[UNKNOWN]` خطوط دقیق P2-2 تا P2-5 تا خواندنِ بیشتر در Phase 0 مشخص نیست.

---

## ۷. ایمنی

### ۷.۱ auto-revert

هر محدودیتِ موقت (مثل `ollama_only`) یک `ttl_sec` و `auto_revert_at` دارد. بعد از آن،
حتی اگر کسی فراموش کرد برگرداند، خودکار منقضی می‌شود.

`[HYPOTHESIS]` این با قانونِ «Fugu فقط با TTL + auto-revert» سازگار است.
**آزمون:** TTL بگذار ۶۰ ثانیه، Fugu را شبیه‌سازی کن، ببین بعد از ۶۰s برمی‌گردد Ollama.

### ۷.۲ propose-only

هیچ patch در این سند اعمال نمی‌شود. همه‌چیز proposal است. اعمال فقط در Phase 3 و
فقط با human approval، یک patch در هر بار.

`[FACT]` این با `doctor/doctor.py:529` (`submit_for_approval`) و `budget/organ_gate.py`
سازگار است.

### ۷.۳ fail-soft

هر قلب، اگر نتواند محاسبه شود، `mode = UNKNOWN` و `confidence = 0` برمی‌گرداند.
Governor با «max-restriction-wins» رفتار می‌کند، پس UNKNOWN → EXTEND/CONTAIN، نه HALT.

### ۷.۴ قرارداد دایجست تلگرام روزانه

> سه تقاضای باارزش‌ترین، روزی یک بار، در `chat_id` مالک.

هر آیتم این فیلدها را دارد:
- `title` (یک‌خطی)
- `evidence` (file:line یا log)
- `urgency` (low/medium/high)
- `confidence` (0..1)
- `suggested_next_action` (یک کار کوچک، reversible)
- `blocked_action` (چه چیزی تا resolution نباید انجام شود)

رندر از طریقِ `telegram_center/center.py:391` (`render_leg_digest`) می‌تواند الگو بگیرد،
ولی ورودیِ آن `demands[]` از `demand-manifest.json` است، نه stateِ پاها.

**مثال (برای وضعیت فعلی گزارش ۰۶):**

```text
🐙 دایجستِ تقاضا — 2026-07-17 22:00

1. [HIGH|c=0.80] پرچمِ epistemics روشن است ولی README می‌گوید خاموش.
   evidence: epistemics/README.md · wiring.py:544 · OCTOPUS-flags.cmd
   next: flag provenance را راستی‌آزمایی کن یا kill-switch را فعال کن.
   blocked: استفاده از امتیاز epistemics برای routing.

2. [MEDIUM|c=0.42] قلب depleted (322/288).
   evidence: state/ORGANISM-STATE.json:cardiac.budget
   next: daily_cap را بازبینی کن یا non-critical LLM را به تعویق بینداز.
   blocked: ارتقا به Fugu/paid API.

3. [MEDIUM|c=0.55] pacemaker dead-spot (1/10).
   evidence: state/cortex/innervation-latest.json:dead_spots
   next: probe محلیِ spine، نه restart سراسری.
   blocked: restart کاملِ organism.
```

---

## ۸. آزمون‌های پذیرش

> هر مورد: ورودی → رفتار مورد انتظار → سیگنال موفقیت.

| # | مورد لبه‌ای | ورودی | رفتار مورد انتظار | سیگنال موفقیت |
|---|---|---|---|---|
| A1 | محیطِ جدید (fresh boot) | stateها empty، telemetry صفر | همه‌ی hearts = `UNKNOWN`، governor = `EXTEND` با demand awareness | `demand-manifest.hearts.*.confidence < 0.3` |
| A2 | شیء ناشناخته (unknown object) | داده‌ای که در baseline نیست | Epistemic = `CONTAIN`، demand type=understanding | `demands[]` شامل type=understanding، blocked_action تنظیم شده |
| A3 | depleted | `cardiac.depleted=true`، hard_risk=false | Energy = `EXTEND` (نه HALT)، router = `ollama_only` | governor.final_mode != HALT · constraints شامل ollama_only |
| A4 | dead-spot | `innervation.dead_spots` غیرخالی | Coherence = `CONTAIN`، probe محلی (نه global restart) | blocked_action = global restart |
| A5 | stale boot | mtime کد دیسک > started ts | demand type=awareness، flag staleness | demands[] شامل reason="stale boot" |
| A6 | تناقض flag epistemics | flag=on، validity_confidence<MIN | Epistemic = `CONTAIN` metric، metric از routing حذف می‌شود | constraints شامل `ignore_epistemics_for_routing` |
| A7 | چرخش استراتژی (novelty rotation) | bottleneck پافشاری، φ_t بالا | demand type=processing، pre-registered test | demands[] شامل `strategy_rotation` با test field |
| A8 | دروازه‌ی API | Fugu پیشنهاد می‌شود ولی governor confidence<0.7 | ESCALATE → EXTEND (نه خودکار) | governor.final_mode != ESCALATE · هشدار به انسان |

`[HYPOTHESIS]` اگر هر ۸ مورد سبز شوند، حلقه‌ی تقاضا وصل است.
**Falsifier کلی:** اگر router حتی با `ollama_only` به tier بالاتر برود (A3/A8)، حلقه وصل نیست.

---

## ۹. فهرست UNKNOWNهای باز

این‌ها **نباید** در Phase 0 حدس زده شوند؛ باید راست‌آزمایی شوند:

1. `[UNKNOWN]` آیا pacemaker dead-spot واقعی است یا artifact از دو منبع beat متفاوت؟
2. `[UNKNOWN]` آیا بوت فعلی stale است؟ (سایدکارِ نسخه غایب بود در زمان گزارش ۰۶.)
3. `[UNKNOWN]` آیا `make_epistemics` در runtime واقعاً None برمی‌گرداند با flag فعلی؟
4. `[UNKNOWN]` مسیر مصرفِ `nociceptor.pain` به کدام ماژول می‌رسد؟ (hard-stop روی sigma_cancer به این وابسته است.)
5. `[UNKNOWN]` آیا `model_router.ask()` از قبل هرگونه constraint می‌خواند؟ (P2-2 به این وابسته است.)
6. `[UNKNOWN]` `daily_cap: 288` چگونه تنظیم شده؟ آیا این عدد عقلانی است یا placeholder؟
7. `[UNKNOWN]` آیا `box/_run_box_cycle` در tick فعلی واقعاً اجرا می‌شود یا فقط wiring تعریف شده؟
8. `[UNKNOWN]` آیا `octopus_core` قرار است لایه‌ی جانبی بماند یا جایگزین `_ops` شود؟
9. `[UNKNOWN]` آیا `render_leg_digest` در center.py قابلیت رندرِ generic از `demands[]` را دارد یا فقط leg-specific است؟
10. `[UNKNOWN]` رفتار فعلی governor (اگر چیزی شبیه governor هست) کجاست و چگونه تصمیم می‌گیرد؟

---

## ۱۰. مگاپرامپت

برای ایجنتِ پیاده‌ساز Phase 0 — فقط تشخیص فقط‌خواندنی، `$0`، propose-only:

```text
You are OCTOPUS PHASE-0 DIAGNOSTIC AGENT.

MISSION
Rasti-arzooi (verify) the hypotheses in 07-ALLOSTATIC-DEMAND-LOOP-DESIGN.md.
You do NOT apply patches. You do NOT edit production code. You produce
one read-only truth-map file.

WORKSPACE BOUNDARY
- Work ONLY in: F:\backup\شناخت اختاپوس\
- NEVER write, copy, or surface anything to Desktop.
- Do NOT overwrite 06-*, 07-*, or any _agent_reports/ file.
- Create ONE new file: 08-PHASE0-TRUTH-MAP-<date>.md
- propose-only: no live API, no money_gate, no force-push, no script execution.
- Default brain = always-on local Ollama. Do NOT call Fugu/paid APIs.

EVIDENCE LAW
1. Separate every claim as FACT / INFERENCE / HYPOTHESIS / UNKNOWN.
2. Every FACT needs file:line, command output, log event, or test result.
3. UNKNOWN is a valid final answer. Never invent state, wiring, or status.
4. A dashboard label is NOT proof the capability works.

TASKS (verify each, with evidence)
T1. pacemaker dead-spot: read cortex/innervation.py:64-86 and chrono.py.
    Question: are there two beat sources? which sla_min is violated?
T2. stale boot: compare state/ORGANISM-STATE.json.started vs git log -1 organism.py.
    Question: is the running boot older than the latest code?
T3. epistemics kill-switch: does make_epistemics() return None at runtime
    with the current flag? Read wiring.py:544 and epistemics/README.md.
T4. fear not enforced: re-confirm that nothing consumes cardiac.depleted
    to gate legs. (Already FACT in 07; re-verify against any new code.)
T5. model_router constraints: does cortex/model_router.py:128 ask() read
    any governor constraint today? If not, mark P2-2 ready.
T6. per-leg baseline: from state/pulse/work-log.jsonl, extract liveness,
    last-event age, error rate, cost for each leg.

OUTPUT STRUCTURE (in 08-PHASE0-TRUTH-MAP-<date>.md)
1. Executive state: LIVE / DEGRADED / UNKNOWN
2. Three highest-priority risks
3. Verified vs unknown table (one row per T1..T6)
4. Evidence index with file:line
5. Recommended smallest next action (one reversible step)
6. Explicit UNKNOWN list (items from 07 §9 you could NOT resolve)

STOP CONDITIONS
- If you hit any of: secret access, external side-effect, paid API,
  forbidden action, data-corruption risk -> STOP and mark BLOCKED.
- Never recommend direct production mutation. Observation/test only.

QUALITY BAR
Be skeptical, concrete, reversible, economical.
Prefer one verified UNKNOWN over ten speculative fixes.
```

---

## ضمیمه — Changelog

| نسخه | تاریخ | تغییر |
|---|---|---|
| v1.0 | 2026-07-17 | سند اولیه. ادغامِ یافته‌های ۰۶ + مدل سه‌قلبی (Energy/Epistemic/Coherence) + سندِ reflection contract (JSON). هیچ production تغییری نکرده. |

---

*تهیه‌شده در `F:\backup\شناخت اختاپوس\07-ALLOSTATIC-DEMAND-LOOP-DESIGN.md`.
روش: طراحی مبتنی بر شواهد (evidence-first). همه‌ی ادعاها با `file:line` یا UNKNOWN مشخص.
تغییرات reversibly، proposes-only، $0.*
