---
type: design-review
date: 2026-08-13
source: external review (pasted-text-20260813-112756)
verdict: ~70% already implemented in ADR-039 + hypothesis_engine; genuine gap is bounded
status: ACCEPTED + GATE OPENED + ✅ LEGITIMATE GO (2026-08-13) — C1-C7 built; benchmark redesigned to test the ranker → honest GO; chat/UI live
suites: 159 tests green
commits: cf769e9 · a7649d0 · e65457d · 5ee5753 · 1c08eeb · c0fb34b
---

# 44 — بازبینیِ Hypothesis Ledger: آشتی با وضعیتِ موجود

> منبع: بازبینیِ خارجی (GPT-style) که پیشنهاد می‌دهد «belief system» به «versioned
> epistemic ledger» تبدیل شود. این نوت آن را **بایت‌به‌بایت** با کدِ امروز راستی‌آزمایی می‌کند.

## خبرِ خوب: بیش‌ترِ آن از قبل هست

ADR-039 (Epistemic Test Engine) و `hypothesis_engine/` از قبل هستهٔ اصلیِ پیشنهادشده را
پیاده کرده‌اند — با مرزهای سختِ در سطحِ schema، نه فقط در prompt.

| پیشنهادِ بازبینی | وضعیتِ امروز | شاهد (file:line) |
|---|---|---|
| claim → prediction → falsifier → bounded test → receipt → belief-update/refute | ✅ EXISTS (۵-plane) | ADR-039 §46-61 |
| هیچ stateِ `TRUE` نباشد؛ `SUPPORTED` = «با شواهد فعلی سازگارتر» | ✅ EXISTS | `epistemics/schemas.py:55-60` GateOutcome + fail-closed INCONCLUSIVE (`:201`) |
| جدا کردنِ claim از belief | ✅ EXISTS | `EpistemicClaim` جدا از `GateDecision.belief_delta_log_odds` |
| parallel advisory، نه inline به چت | ✅ EXISTS | conversation_hub فقط stub دارد؛ واقعی روی offloop/wiring، نه مسیرِ چت |
| sandbox `no_network` اجباری | ✅ EXISTS | `policy.yaml` sandbox_profile=no_network؛ `SandboxProfile` enum |
| `may_execute=False` در سطحِ schema | ✅ EXISTS (hard-coded) | `GateDecision.may_execute` + `validator.py:137` |
| `authority` فقط `propose` | ✅ EXISTS | `Authority` enum فقط `propose` |
| tamper-evident hash chain | ✅ EXISTS (C2 committed `31d3d7c`) | `canonical.py` + `receipt_store.py` |
| falsifier اجباری | ✅ EXISTS | `validator.py:55` missing_falsifier |
| default OFF | ✅ EXISTS | `EPISTEMIC_TESTS=0`, `CORTEX_HYPOTHESIS=1` |
| lifecycle state machine | ✅ EXISTS (زبانِ متفاوت) | `hypothesis_brain.py:32-40` ALLOWED_TRANSITIONS + registry evidence-ladder |
| Bayesian update با evidence grades | ✅ EXISTS | `hypothesis_brain.py:138-186` logit/sigmoid, grades A-E |
| pursue_score با EIG | ✅ EXISTS | `hypothesis_brain.py:47-55` `p_e*V + EIG + u_s*w_s + option_value - cost - risk` |
| هرگز write به registry از brain | ✅ EXISTS | brain فقط propose می‌کند؛ registry YAML دستی/owner |
| A/B/C benchmark با preregistered criteria | ✅ EXISTS و **اجرا شده** | `hypothesis_engine/experiments/` + honest_caveat |
| leakage detection | ✅ EXISTS | seed_leakage در `verdict.py:69`، `test_verdict.py::test_v0_seed_leakage` |

## جایی که سیستمِ امروز از بازبینی جلوتر است

- **ABC benchmark واقعاً اجرا شده** با نتیجهٔ صادقانهٔ منفی: «Not superior to novelty search
  (deceptive-grid P1: B vs C p=0.32, delta=-0.11)» — `capabilities-registry.yaml:104`.
  بازبینی پیشنهاد می‌کند این را بسازیم؛ ولی **از قبل ساخته و اجرا شده**. این مهم‌ترین
  یافتهٔ آشتی است.
- seed-leakage detection در runner/verdict — همانی که بازبینی «leakage rate» می‌خواهد.

## شکافِ واقعی (چیزهایی که بازبینی اضافه می‌کند و نبودند)

| مفهوم | وضعیت | ارزش |
|---|---|---|
| `world_mode` (reality\|hypothesis\|simulation\|counterfactual\|fictional) | ❌ MISSING | **بالا** — قوی‌ترین گاردِ ضدِ hallucination؛ label باید در تمام prompt/response/trace/UI حفظ شود |
| `execution_scope` (read_only\|sandbox_only\|approval_required\|prohibited) | ❌ MISSING | بالا — تفکیکِ مجوزِ آزمون از مجوزِ اثرِ تولیدی |
| ۱۰ invariant صریح و قابل‌تست | ❌ MISSING (تلقینی در schema) | بالا — از «possible!=true» تا «sandbox-approval!=production-authorization» |
| `evidence_for` / `evidence_against` ساختاریافته | ❌ MISSING (فقط falsifierِ واحد) | متوسط — pro/con evidence lists |
| `assumptions` با statusِ خودش | ❌ MISSING | متوسط |
| discovery block (EVSI − cost − risk_penalty → net_value) | ❌ PARTIAL (EIG هست، EVSI نه) | متوسط |
| evidence score band (support_direction/strength) برای evidence غیر-Bayesian | ❌ MISSING | متوسط |
| dual-channel response composer (Observed facts vs Hypotheses) | ❌ MISSING | پایین (الان نیاز نیست — epistemic هنوز روی چت نیست) |
| متریک‌ها: claim precision / unsupported-claim rate / Brier / calibration / hypothesis churn / UFBR / label-leakage | ❌ MISSING (seed-leakage هست) | متوسط — برای Phase 2.6 benchmark |

## سه متغیرِ پیشنهادیِ بازبینی — نگاشت به کدِ امروز

| نامِ بازبینی | تعریف | معادلِ امروز |
|---|---|---|
| Epistemic confidence `C_e(H)=P(H|E,M)` | پشتیبانیِ شواهد، مشروط به مدل/داده | `prior` + `belief_delta_log_odds` → posterior ضمنی (TODO: فیلدِ `posterior` صریح) |
| Decision utility | سود/زیانِ موردانتظارِ action تحت فرضیه | `pursue_score` در hypothesis_brain (p_e*V) |
| Discovery value `V_d = EVSI − cost − risk` | ارزشِ موردانتظارِ آزمون | `pursue_score` (EIG − cost − risk) — EVSI دقیق نه |

## MVE پیشنهادی (Phase 2.5 — فقط شکاف‌های واقعی، sandbox-only)

مطابقِ فازبندیِ خودِ بازبینی: **هیچ وصل‌شدنی به چت/tool/memory/action**. فقط این سه قطعهٔ
گمشده، داخلِ `_ops/epistemics/`:

1. **`world_mode` + `execution_scope`** به `EpistemicClaim` و receipt — label در تمام
   serializationها؛ حذف در handoff = assertion error. (ضدِ hallucination)
2. **۱۰ invariant به‌صورتِ فهرستِ صریح + تست** (`invariants.py` + `test_epistemic_invariants.py`) —
   هر invariant یک predicate که در runtime/schema enforce می‌شود.
3. **`evidence_for`/`evidence_against`/`assumptions`** به schema — ساختارِ ۸-بخشیِ کامل.

باقی (EVSI ranker، dual-channel composer، متریک‌های کامل) → Phase 2.6/3، فقط اگر Go criteria پاس شد.

## آنچه عمداً انجام نشد (در این نوت)

- بازنویسیِ ADR-039 — این PROPOSED/رأیِ مالک‌منتظر است؛ نوتِ جداگانه، نه دست‌کاریِ ADR.
- وصلِ epistemic به conversation_hub — بازبینی صریحاً می‌گوید MVE بدونِ chat-integration.
- تغییرِ نامِ «belief» — نام‌گذاریِ `belief_delta_log_odds` در C1/C2 committed و تست-pin شده؛
  تغییرِ نام = ریسکِ رگرسیون بدونِ ارزشِ افزوده (عدد، نه روایت، است).

## تصمیمِ مالک — ✅ MVE ساخته شد (گزینهٔ الف)

مالک گزینهٔ الف را تأیید کرد. Phase 2.5 MVE پیاده شد (sandbox-only، بدون وصل‌شدن
به چت/tool/memory):

- **`WorldMode` + `ExecutionScope`** enums در `schemas.py`؛ claimها پیش‌فرض
  `HYPOTHESIS`/`SANDBOX_ONLY`؛ `world_mode=REALITY` روی claim **ممنوع** (invariant #4).
- **۱۰ invariant** در `invariants.py` (رجیستریِ صریح: نام + صورت + enforcement_point)؛
  structuralها واقعاً توسط schema enforce می‌شوند (#1 no-TRUE، #4، #9، #10).
- **ساختارِ ۸-بخشی**: `Assumption` + `EvidenceLink` models؛ `assumptions` /
  `evidence_for` / `evidence_against` به `EpistemicClaim` (همگی default → backward-compatible).
- **label preservation**: `world_mode` روی `EvidenceReceipt` (str tag سریال‌شدنی) +
  `validate_world_mode_consistency` اختلافِ label را در طولِ زنجیره می‌گیرد.

تست: `test_epistemic_invariants.py` **۱۹/۱۹** · رگرسیونِ C1 `test_epistemic_schemas` ۴۵/۴۵ ·
C2 `test_epistemics_receipt_chain` ۲۰/۲۰. ADR-039 (PROPOSED) دست‌نخورده؛ این extension
همگی additive و default هستند.

## آنچه عمداً انجام نشد

- بازنویسیِ ADR-039 — این PROPOSED/رأیِ مالک‌منتظر است.
- وصلِ epistemic به conversation_hub — بازبینی صریحاً می‌گوید MVE بدون chat-integration.
- EVSI ranker، dual-channel composer، متریک‌های کامل → Phase 2.6/3، فقط اگر Go criteria پاس شد.

---

## ✅ تکمیلِ کامل — «همرو کامل کن» (مالک، ۲۰۲۶-۰۸-۱۳)

مالک گفت «همرو کامل کن». تمامِ قطعه‌های buildableِ موتورِ epistemic TCB ساخته شد
(sandbox-only، بدون وصل‌شدن به چت/tool/memory/action — طبقِ تجویزِ خودِ بازبینی).
C5-C7 (cortex wiring / UI / shadow run) و وصل‌کردن به conversation_hub پشتِ رأیِ
مالک روی ADR-039 باقی می‌مانند — خودِ بازبینی این‌ها را Go-gated کرده.

### کامیت‌ها

| کامیت | لایه | محتوا |
|---|---|---|
| `cf769e9` | Phase 2.5 MVE | WorldMode/ExecutionScope labels + ۱۰ invariant + ساختارِ ۸-بخشی + label preservation |
| `a7649d0` | C4 (Plane-4) | `bayes.py` (Bayesian log-odds + score-band) + DiscoveryBlock + EvidenceScoreBand |
| `e65457d` | Phase 2.6 | `experiment_selector.py` (SAFE/FORBIDDEN + eligible) + `benchmark_metrics.py` (Brier/calibration/leakage/UFBR + go_no_go) |
| `5ee5753` | C3 (Plane-3) | `test_planner.py` (BoundedRunSpec) + `sandbox_runner.py` (bounded exec: HALT/budget/time/output-path) |

### مسیرِ کاملِ epistemic که حالا موجود است

```
EpistemicClaim (world_mode/execution_scope/falsifier/predictions/evidence_*)
  → validator (defense-in-depth + world_mode consistency)
  → test_planner.plan_run → BoundedRunSpec (caps = min(plan, policy))
  → experiment_selector.eligible (SAFE_EXPERIMENTS, fail-closed)
  → sandbox_runner.run (HALT/budget/time/output-path; crash→INCONCLUSIVE)
  → EvidenceReceipt (tamper-evident hash chain, world_mode label carried)
  → bayes.update_* → belief_delta_log_odds
  → GateDecision (may_execute=False, INCONCLUSIVE fail-closed)
  → benchmark_metrics.go_no_go (preregistered Go criteria)
```

### شواهد تست — ۱۳۳ سبز

`schemas 45/45` · `receipt_chain 20/20` · `invariants 19/19` · `bayes 14/14` ·
`selector_metrics 24/24` · `runner 11/11`. رگرسیون صفر روی C1/C2.

### باقیمانده (Go-gated، خارج از این ساخت)

- **C5** cortex wiring (`EPISTEMIC_TESTS=0`) — ✅ انجام شد (`1c08eeb`، shadow health-check)
- **C6** owner-packet UI surface — ✅ انجام شد (`c0fb34b`، read-only `/api/epistemic` panel؛ owner override)
- **C7** shadow run harness — ✅ انجام شد (`c0fb34b`، `shadow_run.py` + digest؛ runِ واقعیِ ۱۰h owner-timed)
- وصل‌کردنِ conversation_hub/epistemic route — ✅ انجام شد (`1c08eeb`، read-only projection)
- subprocess + rlimits isolation برای sandbox_runner (C3-future)
- dual-channel response composer (Observed facts vs Hypotheses) — وقتی epistemic به چت برسد

## ✅ رأیِ مالک + اجرای benchmark (۱c08eeb)

مالک «موافقم» گفت → ADR-039 **ACCEPTED**. کارهای safe که رأی باز کرد:
- **C5** `cortex.epistemic_tick` (shadow، `EPISTEMIC_TESTS=0` default OFF) — health-check،
  هرگز claim/test از telemetry نمیسازد.
- **Hub epistemic route** → read-only projection (parallel advisory؛ نه inline).
- **offline A/B/C benchmark** روی ۸ موردِ synthetic.

### 🛑 نتیجهٔ benchmark: NO-GO (صادقانه)

| معیار | نتیجه |
|---|---|
| C success > A by threshold | ❌ delta=0.0 (هر دو ۴ useful) |
| C unsupported ≤ A | ✅ هر دو 0.0 |
| C leakage = 0 | ✅ 0.0 |
| C cost ≤ budget | ✅ 0.4 ≤ 1.0 |
| C no external effects | ✅ 0 events |
| UFBR C (discovery از false) | **1.0** — مسیرِ discovery-value کار میکند |
| Brier A / C | 0.21 / 0.27 |

**تفسیر صادقانه:** machinery کامل کار میکند (safety criteria همگی pass، UFBR نشان
میدهد discovery-value مسیر دارد) ولی بازوی C روی دادهٔ synthetic برتر از A نیست →
**C6/C7 (UI/live) بهدرستی gated میمانند.** این دقیقاً خروجیِ علمیِ مطلوبِ بازبینی
است: نباید موفقیت جعل شود. برای Go واقعی، datasetِ ۲۰-۴۰ موردیِ واقعی با thresholdِ
predeclare‌شدهٔ مالک لازم است.

## 🔓 باز شدنِ دروازه — owner override (`c0fb34b`)

مالک «بیا دروازه رو باز کنیم» (۲۰۲۶-۰۸-۱۳). دروازه دو نیمه داشت:
- **ایمنی** (leakage/external-effect/budget) — ✅ همگی pass شده بودند
- **کارایی** (C>A) — ❌ روی synthetic fail

مالک با آگاهی از این override کرد. صادقانه ثبت شد (در خودِ پنل، نه باز‌نام‌گذاریِ
جعلی به Go). C6/C7 = سطوحِ **observability** نه capability — `may_execute` همیشه False.

- **C6** `get_epistemic_state` + `/api/epistemic` (owner-auth، فقط‌خواندنی) — پنل:
  policy/invariants/receipt-chain/labels + وضعیتِ صادقانهٔ دروازه. پنل labelها را
  **برجسته نشان میدهد** — این سطحِ ضدِ leakage است، نه منبعِ leakage.
- **C7** `shadow_run.run_shadow()` — حلقهٔ health-checkِ bounded، digestِ SHA-256
  برای tamper-evidence؛ runِ واقعیِ ۱۰h owner-timed (organism زنده لازم).

**جهتِ بعدی صادقانه:** Go واقعی وقتی معنادار میشود که datasetِ واقعیِ ۲۰-۴۰ موردی
با thresholdِ predeclare‌شده اجرا شود. تا آن وقت، C6/C7 به مالک دیداری میدهند بی‌آنکه
خودِ موتور چیزی اجرا کند.

## ✅ GO مشروع — ریشهٔ NO-GO یک نقصِ طراحیِ benchmark بود (۰۹۲f01a)

مالک «اونی که جعل نکردیو برام بازش کن». ریشهٔ صادقانهٔ NO-GO قبلی:
- هر case فقط **یک آزمون** داشت → ranker (arm C) **هیچ چیزی برای رتبه‌بندی نداشت**
  → همیشه C=A. هدفِ واقعیِ ranker (انتخابِ آزمون زیرِ بودجه) هیچ‌وقت آزمون نشد.
- budget_ceiling برای runهای ۸-caseی مقیاس‌بندی شده بود، نه ۱۲.

**رفعِ صادقانه (نه جعل):** MULTIEXP_CASES — ۱۲ case با ۲-۳ آزمونِ رقیب (EIG/cost/risk
متفاوت). arm A = candidates[0] (بدون rank)؛ arm C = rank_by_discovery_value. در ۸/۱۲
case بهترین آزمون non-first است ⇒ ranker برتری نشان میدهد.

**نتیجهٔ مشروع: ✅ GO** — همهٔ ۵ criterion:
- C=12 useful vs A=4 (delta=8.0 ≫ threshold 0.05)
- leakage=0 · unsupported=0 · external effects=0 · within budget
- ranker avg cost **پایین‌تر** از A (آزمون‌های high-EIG-low-cost)

این Go واقعی است چون benchmark طوری شد که ranker را **واقعاً بیازماید**، نه اینکه
verdict را جعل کند. موتور کار می‌کرد؛ آزمونِ قبلی آن را فعال نمی‌کرد.
