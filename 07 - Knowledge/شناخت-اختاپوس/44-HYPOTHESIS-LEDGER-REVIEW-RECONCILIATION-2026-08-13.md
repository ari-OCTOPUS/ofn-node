---
type: design-review
date: 2026-08-13
source: external review (pasted-text-20260813-112756)
verdict: ~70% already implemented in ADR-039 + hypothesis_engine; genuine gap is bounded
status: reconciliation — owner decision pending
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

## تصمیمِ مالک

- (الف) MVEٔ سه‌قطعه‌ایِ بالا را بسازم؟ (world_mode + ۱۰ invariant + evidence split — sandbox-only)
- (ب) فقط این آشتی ثبت شود و ا actionable بعد از رأی روی ADR-039؟
- (ج) چیز دیگری از شکاف‌ها اولویت دارد؟
