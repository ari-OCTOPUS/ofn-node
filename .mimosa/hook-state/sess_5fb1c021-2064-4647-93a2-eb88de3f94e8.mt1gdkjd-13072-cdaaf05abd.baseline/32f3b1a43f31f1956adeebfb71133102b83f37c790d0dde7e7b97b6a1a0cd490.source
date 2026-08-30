---
type: survival-governor-design
authority: Owner Constitutional Directive (OCTOPUS GENOME AMENDMENT)
status: design-only (no implementation without owner verdict)
created: 2026-07-18
updated: 2026-07-18
tags: [octopus, survival, governor, design, telemetry]
---

# SURVIVAL-GOVERNOR — طراحی (Design)

> **فقط طراحی.** هیچ کدی اجرا/سیم‌کشی نمی‌شود تا رأی مالک. این سند نگهبانِ بقا را روی **زیرساختِ موجود** طراحی می‌کند، نه از صفر.
> پیش‌نیازها: [[OCTOPUS-SURVIVAL-GENOME-2026-07-18]] (قانون) · [[OCTOPUS-REALITY-TO-REVENUE-MAP]] (واقعیت).

---

## ۰. اصلِ طراحی: «روی آنچه هست بساز، نه کنارش»

اختاپوس **قبلاً یک لایهٔ حاکمیتی دارد** که کار می‌کند `[E1/E2]`:

| قابلیتِ Governor | ماژولِ موجود روی دیسک | وضعیت |
|---|---|---|
| سقفِ بودجه + halt | `_ops/budget/budgets.yaml` + `budget-state.json` | زنده |
| گیتِ پول | `_ops/budget/money_gate.py` | زنده |
| گیتِ توانمندی (fail-closed) | `_ops/budget/capability_gate.py` | زنده |
| کانالِ approvalِ انسانی | `_ops/budget/approval_channel.py` + `approval_state_machine.py` | زنده |
| ماتریسِ خودمختاری (self/important) | `_ops/cortex/autonomy_matrix.py` + `auto_approve` | زنده |
| گیتِ ارگان | `_ops/budget/organ_gate.py` + `organ-state.json` | زنده |
| circuit breaker | `_ops/budget/circuit_breaker.py` | زنده |
| fitness / attribution | `_ops/budget/{fitness,attribution,telemetry}.py` | زنده |
| ledgerِ ممیزی | `_ops/state/{action-audit,approval-log}.jsonl` | زنده |
| Metabolic Governor (shadow) | `04 - Architect System/2026-07-06 METABOLIC-GOVERNOR-proposal.md` | طراحی |

**نتیجه:** «Survival Governor» یک ماژولِ جدید نیست؛ یک **لایهٔ نازکِ تصمیم** روی این‌هاست که یک سؤال را اضافه می‌کند: *«آیا این کار به E3+ ختم می‌شود، یا فقط E0–E2 تولید می‌کند؟»* — و انرژی/توجه را طبقِ طبقاتِ R0–R5 اولویت‌بندی می‌کند.

---

## ۱. مسئولیتِ نگهبان (Responsibility)

برای هر Mission یا Organ، نگهبان باید به این ۱۰ پرسش پاسخِ ساختاریافته بدهد (از منشور §۵):

1. چه ارزشِ واقعی؟ 2. برای چه کسی؟ 3. evidenceِ موفقیت؟ 4. مسیر به درآمد/کاهش‌هزینه/runway؟ 5. هزینهٔ اجرا + توجهِ مالک؟ 6. کِی باید متوقف شود؟ 7. اگر شکست خورد چه یاد می‌گیریم؟ 8. آیا از مسیرِ مهم‌تر عقب می‌اندازد؟ 9. سطحِ ریسک؟ 10. آیا رأی مالک لازم است؟

خروجیِ نگهبان یک **verdictِ ساختاریافته** است، نه اجرا:

```json
{
  "target_id": "mission:paint-first-real-quote",
  "survival_class": "R0",
  "evidence_projection": "E1→E3 (quote delivered) → potential E4 (paid job)",
  "cost": { "money_aud": 0, "owner_attention_minutes": 25 },
  "priority_rank": 1,
  "blocks_higher_value": false,
  "risk": "low (owner sends manually; no auto-outreach)",
  "owner_gate_required": true,
  "governor_verdict": "PROMOTE | HOLD | THROTTLE | PAUSE | KILL | ESCALATE",
  "reason": "R0, near-E3, minimal attention, uses existing skill"
}
```

---

## ۲. schema و قواعدِ تصمیم

### ۲.۱ ورودی

نگهبان از این‌ها می‌خواند (همه موجود): Mission Genome (+ بلوکِ `survival` از [[OCTOPUS-SURVIVAL-GENOME-2026-07-18|§۷]]) · `budgets.yaml` · `organ-state.json` · `fitness-latest.json` · `action-audit.jsonl` · GOALS-OCTOPUS.md.

### ۲.۲ قواعدِ اصلی (deterministic — نه LLM)

```text
R1  اولویتِ پیش‌فرض:              R0 > R1 > R2 > R3 > R4 > R5
R2  دروازهٔ R3:                   R3 فقط اگر گلوگاهِ مشخصِ R0/R1/R2 + owner + budget + deadline + success/fail
R3  دروازهٔ R4:                   R4 فقط اگر budget + expiry + kill-criteria سخت؛ وگرنه HOLD
R4  کفِ evidence برای ادعای پول:  فقط E4/E5 → می‌تواند "revenue" برچسب بخورد؛ E0–E2 → "pre-revenue/hypothesis"
R5  گیتِ توجهِ مالک:              اگر owner_attention_minutes از سقفِ هفتگی رد شود → THROTTLE کارهای غیرِ R0/R1
R6  ضدِ theater:                 organ با success_signal همه E0–E1 و maintenance بالا → downgrade به R5
R7  هم‌راستایی با هسته:            barbell.core_share=0.70 به Ziman+Lead؛ satellite هرگز > 10% منفرد
R8  مرزِ سخت:                     پول/کد/ژنوم/ارسال/حذف/PII → همیشه ESCALATE (هرگز PROMOTE خودکار)
```

### ۲.۳ چهار سطحِ خودمختاری (هم‌راستا با `autonomy_matrix.py` موجود)

```text
A0 Observe          خواندن/اسکن/گزارش/تحلیل                       — آزاد
A1 Propose          Mission/plan/patch-proposal/draftِ پیام        — آزاد (فقط draft)
A2 Isolated Execute تست/doctor/patch در worktreeِ محدود           — آزاد، برگشت‌پذیر، ledger
A3 Owner-Gated Apply اثر روی درختِ زنده یا دنیای بیرون             — فقط verdictِ صریحِ مالک
```

هیچ ایجنتی سطحِ A خود را بالا نمی‌برد. نگهبان فقط تا A2 «PROMOTE» می‌کند؛ A3 همیشه ESCALATE.

---

## ۳. حالت‌های شکست (Failure Modes) و پادزهر

| حالتِ شکست | نشانه | پادزهرِ نگهبان |
|---|---|---|
| **Revenue hallucination** | ثبتِ lead/forecast/message-sent به‌عنوان درآمد | قاعدهٔ R4: فقط E4/E5 → "revenue"؛ بقیه "hypothesis" |
| **Green-test theater** | تستِ سبز بدونِ outcomeِ بیرونی | evidence_projection اجباری؛ تستِ سبز = E1، هرگز E3 |
| **UI theater** | دکمه/کارت بدونِ executor | check: هر دکمه به action_id در ledger وصل باشد |
| **Autonomy theater** | «خودکار» نامیدن چیزی که مالک دستی می‌کند | برچسبِ صادقِ A-level در هر گزارش |
| **Metabolic debt** | اسناد/agent بیشتر از خروجی | نسبتِ complexity/E3؛ R5 → archive |
| **Memory hoarding** | ذخیرهٔ همه‌چیز بدونِ freshness/permission | حافظه باید evidence-linked + expiry |
| **Silent fallback** | چرخشِ مدل/مسیرِ بی‌alert | هر fallback → trace + alert |
| **Permanent research** | R4 بی deadline/kill | expiry اجباری؛ cull سیگنالِ صفرِ ۳۰روزه |
| **Owner-attention burn** | رگبارِ سؤال/گزارش | سقفِ هفتگیِ attention؛ فقط ردهٔ «مهم» به مالک |

---

## ۴. تله‌متری (Telemetry) — چه چیزی اندازه بگیریم

نگهبان روی `telemetry.py` + tracer موجود سوار می‌شود و این‌ها را می‌افزاید (فقط خواندن/محاسبه، نه اکشن):

```text
survival.evidence_level_max            بیشینه E رسیده در کلِ سیستم (هدف: از E2 به E3)
survival.by_class_effort               تخصیصِ تلاش/توجه به تفکیکِ R0..R5
survival.owner_attention_minutes_week  دقیقهٔ توجهِ مالک در هفته (گلوگاهِ اصلی)
survival.blocked_on_owner              فهرستِ مسیرهای درآمدیِ قفل‌شده روی رأی مالک
survival.dead_weight_count             organ/mission یتیم/منقضی/R5
survival.external_signals              شمارِ E3+ (اکنون: 0 — این عددِ کلیدی است)
survival.revenue_evidence_aud          فقط از E4/E5 (اکنون: 0)
survival.cost_avoidance_verified       فقط با baseline روشن (اکنون: 0)
```

منابع همه روی دیسک‌اند: `events.jsonl`, `fitness-history.json`, `action-audit.jsonl`, `organ-state.json`, `budget-state.json`.

---

## ۵. طراحیِ داشبوردِ بقا (OCTOPUS SURVIVAL BOARD)

یک گزارشِ **فقط‌خواندنی** (نه vanity metrics). سه بورد (منشورِ ۲۰۲۷):

**۱) Mission Board** — چه کاری در چه مرحله، مالک کجا باید تصمیم بگیرد.
**۲) Evidence Board** — هر ادعا به کدام artifact/trace/outcome وصل است (سطحِ E هر ادعا).
**۳) Survival Board** — Runway · Value Pipeline · Revenue Evidence · Cost Avoidance · Dead Weight · Safety.

بخش‌های Survival Board (حداقل):

```text
RUNWAY          هزینهٔ ماهانه (API/Xero/نگهداری) · سقفِ تأییدشده · هزینهٔ نامعلوم · توجهِ مالک
VALUE PIPELINE  Missionهای R0–R2: approved / running / evidence / realized / blocked / killed
REVENUE (E4/E5) درآمدِ واقعی · leadِ qualifiedِ E3 · attribution به organ  [اکنون: خالی — صادقانه]
COST AVOIDANCE  زمانِ ذخیره با baseline · خطای حذف‌شده  [اکنون: حسابداری، در حالِ اثبات]
DEAD WEIGHT     organ بی‌استفاده · mission منقضی · dashboard تزئینی · agent پرهزینهٔ بی‌اثر
SAFETY          تلاشِ bypassِ approval · اکشنِ بیرونیِ blocked · وضعیتِ secret · markerهای کهنه
```

> **پیاده‌سازیِ پیشنهادی (owner-gated):** یک Live Artifact قابل‌بازگشایی که از همان JSONهای `_ops/state/*` می‌خواند — نه یک world جدیدِ 3D. این جایگزینِ بیشترِ داشبوردهای تزئینیِ فعلی می‌شود (verdictِ PAUSE/ARCHIVE در نقشهٔ واقعیت).

---

## ۶. ادغام با Mission Genome و مرزهای اعتماد

```text
        GOALS-OCTOPUS.md (جهتِ مالک)
                 │
        ┌────────▼─────────┐   می‌خواند: budgets.yaml, organ-state, fitness, ledger
        │ SURVIVAL GOVERNOR │   خروجی: governor_verdict (PROMOTE/HOLD/THROTTLE/PAUSE/KILL/ESCALATE)
        └────────┬─────────┘
      A0/A1/A2 │ آزاد        │ A3 (بیرونی/مالی/کد/ژنوم/ارسال)
        ┌───────▼──────┐   ┌─▼───────────────┐
        │ Mission Runner│   │ OWNER (Telegram) │  approval_channel → action-audit.jsonl
        │ (isolated)    │   └──────────────────┘
        └───────┬───────┘
        evidence│ → telemetry → Survival Board
```

**مرزهای اعتماد (Trust boundaries):**
- نگهبان **رأی می‌دهد، اجرا نمی‌کند**. اجرا فقط از Runner/tools با schemaی سخت.
- هر toolِ حساس metadata دارد: `risk`, `allowed_callers`, `writes_live_state`, `requires_approval`, `audit_required` (الگوی منشورِ ۲۰۲۷ §۵).
- LLM هیچ‌جا verifier نهایی نیست؛ evidenceِ بیرونی داور است.

---

## ۷. دروازه‌های دقیقِ مالک (Exact Owner Gates)

نگهبان این‌ها را **هرگز** خودکار نمی‌کند (همیشه ESCALATE → صفِ approve):

```text
ارسالِ هر پیام/ایمیل/DM به مشتری   ·  انتشار/پستِ عمومی
قیمت‌گذاری / آفر                    ·  قرارداد / فاکتور / پرداخت / برداشت
خریدِ API/Cloud (Xero A$47 و…)      ·  تغییرِ حسابِ مالی
اعمالِ تغییرِ زنده / merge / حذف     ·  هر جابه‌جاییِ secret/PII
تغییرِ هر قاعدهٔ قفل‌شدهٔ ژنوم        ·  فعال‌سازیِ هر اتوماسیونِ outreach
```

هم‌راستا با `human_gate_aud=20` و ردهٔ «مهم»ِ `autonomy_matrix` موجود.

---

## ۸. نگاشتِ ۲۰۲۷ (فشرده) — شش لایه و جایگاهِ فعلی

خروجی‌های A/B/D/E منشورِ معماریِ ۲۰۲۷ اینجا فشرده ادغام شدند (به‌جای ساختِ فایل‌های جداگانه — طبقِ اصلِ «no vanity documents»):

| لایه | مسئولیت | موجود روی دیسک | گپِ اصلی |
|---|---|---|---|
| **1 Survival & Governance Kernel** | ارزش/بودجه/policy/approval | budgets, gates, approval, autonomy_matrix | لایهٔ نازکِ «evidence-projection» + Survival Board |
| **2 Cognitive Plane** | مدل‌ها/planner/critic | cortex (qwen→GLM→Fugu), doctor, debate | verifier مبتنی بر evidenceِ بیرونی (نه LLM-only) |
| **3 Mission/Workflow Control** | Mission → work order | live_loop, organism, phase_gate | durable state + approval-expiry به scope-hash |
| **4 Bounded Execution** | اجرای محدود | isolated worktree، tests، doctor dry-run | **Mission Runner v0** (پایین) |
| **5 Tool & Data Fabric** | vault/git/legs/adapters | `_ops/legs/*`, PocketSmith/Xero adapters | adapterهای capability-scoped + tool metadata |
| **6 Evidence/Eval/Telemetry** | trace/eval/ROI | tracer, eval/, telemetry, ledger | اتصالِ traceِ Telegram→artifact + Survival Board |

### Mission Runner v0 (طراحی، owner-gated)

کوچک‌ترین حلقه‌ای که «هوش» را به عملیاتِ اثبات‌پذیر تبدیل می‌کند — **بدونِ آزادیِ agent**:

```text
از SHA مشخص → worktreeِ موقت → تستِ allowlisted / doctor فقط‌خواندنی
→ ذخیرهٔ diff/exit-code/زمان/SHA/artifact → Mission = verified|failed
→ هرگز خودکار روی master commit/apply نمی‌کند (A3 = مالک)
```

الزامات: idempotency-key، retry امن، approval-pause/resume، scope-hash، artifact-store. (بیشترِ اجزا از قبل در `_ops` هستند؛ v0 فقط آن‌ها را در یک قراردادِ واحد می‌بندد.)

---

## ۹. آنچه این طراحی **نمی‌کند** (مرزِ فاز)

- هیچ کدی نمی‌نویسد/سیم‌کشی نمی‌کند تا رأی مالک.
- هیچ ارگانی را خودکار kill/archive نمی‌کند — فقط **پیشنهادِ verdict** می‌سازد.
- هیچ درآمدِ فرضی ثبت نمی‌کند.
- هیچ داشبوردِ موجود را حذف نمی‌کند — فقط PAUSE/ARCHIVE پیشنهاد می‌دهد.

**گامِ اولِ پیشنهادی برای پیاده‌سازی (بعد از رأی):** فقط بخشِ «Evidence Board + Survival Board» به‌صورتِ یک گزارشِ read-only از JSONهای موجود — صفر ریسک، بیشترین شفافیت. جزئیاتِ رأی در [[OWNER-SURVIVAL-DECISIONS]].

*ژنوم: [[OCTOPUS-SURVIVAL-GENOME-2026-07-18]] · واقعیت: [[OCTOPUS-REALITY-TO-REVENUE-MAP]] · تصمیم‌ها: [[OWNER-SURVIVAL-DECISIONS]]*
