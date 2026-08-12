# ADR-039: Epistemic Test Engine — موتور آزمونِ معرفتیِ fail-closed در `_ops/epistemics/`

**وضعیت:** PROPOSED (نیازمند رأی مالک — گزینهٔ A: خودتقویتِ آزمون‌پذیر، invariant صداقت دست‌نخورده)
**تاریخ:** 2026-08-12 · **شماره:** 039 (بعد از ADR-037 hypothesis-engine، ADR-038 observe-4d)
**معمار:** جلسهٔ طراحی — بر پایهٔ ممیزی ۱۰ ساعته و دو سند پژوهشی مفهومی

---

## ۰. خلاصهٔ اجرایی (یک بند)

سیستم فعلی می‌تواند **فرضیه بسازد** (ADR-037) اما نمی‌تواند به‌طور مکانیکی **بین «مدل‌کردنِ یک جهان» و «موفقیتِ تصادفی در یک benchmark» تمایز بگذارد**. ADR-039 یک کابینِ مستقلِ TCB-grade به نام `_ops/epistemics/` اضافه می‌کند که هر ادعا را به یک زنجیرهٔ قابل‌ابطال تبدیل می‌کند:

```
claim → discriminating prediction → bounded sandbox test → tamper-evident receipt → belief-update | refute
```

هیچ ادعایی صرفاً بر پایهٔ متنِ ایجنت، خروجی یک ابزار، یا success یک run پذیرفته نمی‌شود. گیت **deterministic، بدون LLM، و fail-closed** است و `may_execute` در آن **ثابتِ سخت‌کدشدهٔ False** است.

---

## ۱. مسئله‌ای که حل می‌کنیم — تفکیک سه پدیده

خطای مفهومیِ فعلی: «B در deceptive-grid از A بهتر است» را به‌غلط می‌توان نشانهٔ خودمختاری یا AGI خواند. سه پدیدهٔ متفاوت باید جدا و هرکدام آزمونِ علّیِ خود را داشته باشند:

| لایه | پرسش واقعی | شاهد معتبر | گیت چه enforce می‌کند |
|---|---|---|---|
| **CAPABILITY** (توانایی شناختی) | آیا ساختار پنهانِ فریب را می‌یابد؟ | انتقال + ablation + کنترلِ novelty | claim باید transfer/ablation prediction داشته باشد |
| **OP-AUTONOMY** (خودمختاری عملیاتی) | آیا بدون دخالت پیوسته، در ODD مجاز عمل می‌کند؟ | trigger مستقل + provenance بدون human-edge پس از start | claim باید provenance DAG بدون `human_prompt_id` پس از start داشته باشد |
| **GOAL-AGENCY** (عاملیت هدف‌ساز) | آیا از state داخلی goal-gap می‌سازد و پایدار پیگیری می‌کند؟ | goal-formation trace + تعمیم میان-domain | claim باید goal_id درون‌زاد + cross-domain داشته باشد |

**این جدول، «دیوارِ آتشِ ضدِ خلط‌مبحث» است.** deceptive-grid فعلاً فقط بخشی از لایهٔ اول را می‌سنجد.

### چهار تبیینِ رقیب که داده فعلی تفکیک نکرده
1. **Heuristic فریب‌محور** — «در محیط مشکوک prior را نقض کن».
2. **Novelty پوشیده** — exploration پیچیده‌تر بدون reasoning علّی.
3. **Overfit به generator** — فرضیه‌ها با ساختارِ خودِ grid کوک شده‌اند.
4. **توانایی epistemic واقعی** — تمایزِ فرضیه‌های رقیب، انتخاب test، پذیرش evidence خلاف انتظار، حفظ چرخه در domain جدید.

چون **B بر novelty برتری معنادار نداشت** (p=0.32، δ=−0.11)، گزینه‌های ۱–۴ هنوز از هم جدا نشده‌اند. ADR-039 برای همین تفکیک ساخته می‌شود.

---

## ۲. تصمیم معماری — پنج پلان (Plane) و یک ستون‌فقرات

```
                        ┌──────────────────────────── TRUST BOUNDARY (TCB) ────────────────────────────┐
                        │                                                                               │
  ┌─────────────┐       │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   ┌────────────┐  │
  │  PLANE 1    │ draft │   │  PLANE 2     │    │  PLANE 3     │    │  PLANE 4     │   │  OWNER     │  │
  │ UNTRUSTED   │──────▶│   │ VALIDATE+PLAN│───▶│ BOUNDED EXEC │───▶│ GATE + BELIEF│──▶│ DECISION   │  │
  │ producers   │       │   │ schemas.py   │    │ runner.py    │    │ gate.py      │   │ PACKET     │  │
  │ (hypothesis │       │   │ test_planner │    │ (sandbox     │    │ bayes.py     │   │ (advisory) │  │
  │  brain,LLM) │       │   │ ADR-037 cabin│    │  no_network) │    │ multi_agent  │   │ owner-only │  │
  └─────────────┘       │   └──────────────┘    └──────────────┘    └──────┬───────┘   └────────────┘  │
                        │                                                  │                           │
                        │   ┌──────────────────────────────────────────────▼─────────────────────┐   │
                        │   │ SPINE — PROVENANCE  receipt_store.jsonl  +  autonomy_provenance.jsonl│   │
                        │   │ (append-only, prev_hash chain, per-segment signature)                │   │
                        └───┴──────────────────────────────────────────────────────────────────────┴──┘
                                       may_execute == False  (hard-coded, always)
```

**Plane 1 — تولید draft (خارج از TCB، untrusted).** `hypothesis_brain` موجود + (اختیاری) LLM فقط `EpistemicClaimDraft` و `TestPlanDraft` می‌سازند. بدون هیچ authority. خروجی صرفاً پیشنهاد.

**Plane 2 — اعتبارسنجی و طرح (TCB).** `schemas.py` با Pydantic v2 (`strict=True, extra="forbid", frozen=True`) draft را به `EpistemicClaim` تبدیل می‌کند؛ `test_planner` یک `TestPlan` می‌سازد که به‌اجبار `sandbox_profile="no_network"` است. رد می‌کند: ادعای غیرقابل‌آزمون، prior جزمی (0/1)، ادعای causal بدون counterfactual.

**Plane 3 — اجرای محدود (sandbox).** `runner.py` طرح را روی **محیطِ مولدِ پارامتریک** (نه grid ثابت) اجرا می‌کند و `EvidenceReceipt` با همهٔ hashهای binding تولید می‌کند. no-network، بدون write بیرون `outputs/epistemics/`.

**Plane 4 — گیت و باور (TCB، deterministic، fail-closed).** `epistemic_gate` → یکی از `{SUPPORTED, REFUTED, INCONCLUSIVE, BLOCKED}`. سپس belief-update محدود (log-odds, clipped) و تجمیع چندایجنتی با خوشه‌بندیِ استقلال + جریمهٔ اختلاف. خروجی: `OwnerDecisionPacket` (فقط مشورتی).

**ستون‌فقرات — Provenance.** `autonomy_provenance.jsonl` (همان artifactِ توصیه‌شده در ممیزی #1) اکنون **ابزارِ شناساییِ علّی** است، نه لاگ. هر یال DAG: `trigger_source, initiator, human_prompt_id, goal_id, evidence_ids, approval_id, tool_calls, side_effects, rollback_id, fencing_token`. **اگر هر یالِ پس از start دارای `human_prompt_id` یا `owner` باشد، آن run دیگر شاهدِ self-initiation نیست** — می‌تواند شاهد capability باشد ولی باید صادقانه برچسب بخورد.

---

## ۳. محیطِ مولد — از benchmark به model-organism

grid ثابت = benchmark؛ ما به یک **generator پارامتریک** نیاز داریم که خانواده‌ای از جهان‌ها بسازد:

```
W = (T, O, R, D, C, H)
  T: topology و مسیرها          O: مشاهده‌پذیری و latency
  R: پاداش و هزینه              D: مکانیزم فریب  (agent هرگز D یا seed پنهان را نمی‌بیند)
  C: بودجه و زمان              H: تاریخچه/تغییرِ رژیم درون run
```

خانواده‌های الزامی برای انتقال: `Decoy-reward`, `False-safety`, `Delayed-truth`, `Non-stationary-rule`, `Benign-null` (بهترین رفتار = abstention)، و `Cross-domain` (incident-triage / diagnosis مصنوعی، نه فقط grid).

---

## ۴. ماتریسِ مداخلهٔ علّی — قلبِ علمیِ طرح

معیارِ اصلی **counterfactual sensitivity** است، نه success rate. هر مداخله یک `TestPlan` پیش‌ثبت‌شده با پیش‌بینیِ متمایزکننده و falsifier است:

| مداخله | اگر B واقعاً epistemic باشد | اگر heuristic/novelty باشد |
|---|---|---|
| **حذف EIG** (ablation) | انتخاب آزمایش و efficiency افت می‌کند | تفاوت ناچیز/تصادفی |
| **حذف kill-condition** | فرضیهٔ مرده دیرتر کنار می‌رود، هزینه بالا می‌رود | تفاوت ناچیز |
| **وارونه‌کردن قاعدهٔ فریب** (rule_reversal) | belief update و تغییرِ policy | چسبیدن به رفتار قبلی |
| **Benign-null** | abstain / مسیر ساده | over-explore با هزینه |
| **انتقال domain** (unseen family) | plan جدید اما اصلِ تصمیم ثابت | فروپاشیِ performance |

---

## ۵. نردبانِ بلوغ (جایگزینِ صفر-و-یکِ AGI)

| سطح | ادعای مجاز | حداقل شاهد | نگاشت به گیت / registry |
|---|---|---|---|
| **E0** | harness کار می‌کند | test deterministic + validator green | infra |
| **E1** | مزیتِ شرطی در deceptive | B>A در holdout | `SUPPORTED` → status `TESTING` |
| **E2** | چرخهٔ فرضیه‌ایِ واقعی | ablation: B-full > B-static/no-EIG | `SUPPORTED` تحت ablation → `TESTING` |
| **E3** | انتقالِ محدود | چند family دیده‌نشده + benign-null | نامزدِ `EVIDENCED` |
| **E4** | پژوهشِ خودآغازِ bounded | provenance: telemetry→proposal، بدون human-edge پس از start | `EVIDENCED` (autonomy-scoped) |
| **E5** | robustness عملیاتی | restart/noise/budget/adversarial/replay | `SUPPORTED` |
| **E6** | تعمیمِ میان-domain | انتقال به ODD نامرتبط | — |

**وضعیتِ فعلیِ Octopus: بین E1 و آغازِ E2.** هیچ سطحی به‌تنهایی «AGI» نیست؛ E4 یک نقطهٔ عطفِ مهندسیِ واقعی است، نه ادعای consciousness.

> **قانونِ سخت:** گیت هرگز به‌تنهایی یک فرضیه را به `EVIDENCED` با `may_gate=true` ارتقا نمی‌دهد. ارتقا فقط از طریق `OwnerDecisionPacket` و رأی مالک. `INCONCLUSIVE` هرگز به `SUPPORTED` تبدیل نمی‌شود (fail-closed epistemics).

---

## ۶. مدلِ داده (خلاصه؛ جزئیات کامل در پیوستِ کد)

انواعِ ادعای مجاز: `descriptive | causal | predictive | comparative | safety`. گزاره‌های بدون `operational_definition`, `predictions`, `falsifier`, یا `≥1 competing hypothesis` → **block**. گزارهٔ «Octopus is AGI» → `UNTESTABLE`/`FALSIFIED_BY_CONTRACT` (testability=0).

- **`EpistemicClaim`** — واحدِ معرفتیِ frozen؛ کلیدهای غیرقابل‌حذف: `operational_definition`, `competing_claim_ids`, `predictions`, `falsifier`, `source_git_sha`, `source_config_hash`, `requested_authority=propose` (execute ممنوع).
- **`TestPlan`** — `design ∈ {ablation, rule_reversal, holdout, counterfactual, chaos}`؛ `sandbox_profile` به‌اجبار `no_network`؛ سقفِ `max_runs/wall/cost`.
- **`EvidenceReceipt`** — bindِ کامل: `git_sha, material_hash, config_hash, environment_hash, seed_set_hash, command_hash, artifact_hashes`، `parent_receipt_hash` (زنجیره)، `canonical_payload_hash`, `signature_b64`. `material_hash` از source-tree واقعیِ آزمون، نه فقط HEAD.
- **`GateDecision`** — `outcome + reason_codes + belief_delta_log_odds + may_execute(=False)`.

`canonical.py`: JSON کانونیکال (sort_keys، UTF-8، separator ثابت، حذفِ فیلدهای خودارجاع) → SHA-256. journal به‌صورت append-only با `prev_receipt_hash`؛ پایانِ هر segment با کلیدی خارج از process runner امضا می‌شود و public key در TCB می‌ماند.

تجمیعِ چندایجنتی: ابتدا خوشه‌بندیِ استقلال بر پایهٔ provider/prompt-family/toolchain/data-overlap؛ از هر خوشه فقط median؛ سپس `p_new = σ(logit(p_old) + Σ w_j·median{ℓ_i} − λ·D)`. اگر تعدادِ خوشه‌های مستقل < حداقلِ policy → **INCONCLUSIVE** حتی با اجماعِ ظاهریِ بالا.

---

## ۷. مرزهای سخت (non-negotiable)

1. هیچ متد در `_ops/epistemics/` حق import یا write به `registry`, `ledger`, `brain/`, `strategy`, یا TCB را ندارد.
2. `may_execute` سخت‌کدشده `False`؛ حتی `SUPPORTED` فقط belief-update محدود + owner packet می‌دهد.
3. `sandbox_profile="no_network"` اجباری؛ write فقط در `outputs/epistemics/`.
4. **`STOP-ORGANISM` / `HALT-ALL` → executor فراخوانی نمی‌شود؛ فقط receipt با `verdict="blocked"` ثبت می‌شود.**
5. پیش‌فرض خاموش: `EPISTEMIC_TESTS=0` — فعال‌سازی فقط با رأی مالک و پس از freeze SHA/config.

---

## ۸. اتصال به چرخهٔ `_ops` (additive، الگوی ADR-037)

مانند `hypothesis_brain_run`، یک `epistemic_tick(cycle)` پشتِ فلگ اضافه می‌شود و در `run_cycle` زیرِ همان cadence `IMPROVE_EVERY_N` dispatch می‌گردد:

```python
# در cortex.py، هم‌الگو با business_brain_run / hypothesis_brain_run
def epistemic_tick(cycle: int) -> dict | None:
    if os.environ.get("EPISTEMIC_TESTS", "0") != "1":
        return None
    if halt_flags_active():                       # STOP-ORGANISM / HALT-ALL
        return blocked_receipt("halt_active")
    draft = hypothesis_brain_run(cycle)           # untrusted producer
    if not draft or draft.get("testability", 0) <= 0:
        return None
    claim  = EpistemicClaim.model_validate(draft, strict=True)
    plan   = test_planner.build_shadow_plan(claim)      # no_network
    receipt= sandbox_runner.execute(plan)               # bounded
    decision = epistemic_gate(claim, plan, receipt, ...) # deterministic
    receipt_store.append(receipt, decision)
    provenance.append_edge(claim, plan, receipt, decision)
    return {"outcome": decision.outcome, "may_execute": False}
```

فلگ‌های محیطی: `EPISTEMIC_TESTS=0`, `EPISTEMIC_SANDBOX=no_network`, `EPISTEMIC_MAX_AUTHORITY=propose`.

---

## ۹. نقشهٔ راه — ۷ commit (improve-don't-rewrite، shadow-only، همه fail-closed)

| # | commit | محتوا | گیت‌شده با |
|---|---|---|---|
| C1 | `feat(epistemics): strict schemas + canonical hashing + policy` | `schemas.py`, `canonical.py`, `policy.yaml`, validatorِ pure، بدون wiring | tests سبز |
| C2 | `feat(epistemics): tamper-evident receipt chain + provenance` | `receipt_store.py` (JSONL append-only, prev_hash, segment-sig), `replay verifier`, `provenance.py` (autonomy_provenance.jsonl) | replay-determinism |
| C3 | `feat(epistemics): parametric world generator + sandbox runner` | تبدیلِ `deceptive_grid` به generator خانوادهٔ W + `runner.py` (no_network, budget) + `test_planner.py` | fixture smoke |
| C4 | `feat(epistemics): causal scenarios + bounded bayes + multi-agent` | rule_reversal / benign_null / no-EIG / no-kill / transfer + `bayes.py` + `multi_agent.py` | ماتریسِ §۴ |
| C5 | `feat(cortex): wire epistemic_tick shadow-only (EPISTEMIC_TESTS=0)` | اتصال به `cortex.py` زیرِ cadence؛ HALT→blocked | ۱۵/۱۵ cortex tests |
| C6 | `feat(owner): epistemic owner-packet surface (read-only)` | miniapp/telegram فقط نمایش packet؛ **بدون route اجرا** | no approve-to-execute |
| C7 | `docs(epistemics): 10h shadow run + signed report + ADR-039 evidence` | freeze SHA/config، گزارش امضاشده، ثبت در `capabilities-registry.yaml` (`truth_status: TESTING`, `evidence_level: SHADOW`) | verdict نهایی |

---

## ۱۰. طراحیِ ۱۰ ساعتِ shadow (کاهشِ عدم‌قطعیت، نه اثباتِ AGI)

فرضیهٔ قابل‌رد که پیش‌ثبت می‌شود:
> **H-autonomy-1:** در یک ODD محدود، Octopus می‌تواند از telemetry یک ناهنجاری را تشخیص دهد، بدون prompt انسانی پس از start یک فرضیهٔ آزمون‌پذیر با kill-condition بسازد، آزمونِ sandbox کم‌هزینه انتخاب کند، با evidence خلاف انتظار باورش را به‌روز کند، و فقط یک proposalِ قابل‌ممیزی بسازد.

| بازه | کار |
|---|---|
| ۲h | pre-register فرضیه‌ها، freeze SHA/config، seedهای holdout، معیارها |
| ۳h | S0/S1/S2 — بازتولید، rule reversal، shift در فریب |
| ۲h | ablation چهارگانه (B-full/B-static/B-no-EIG/B-no-kill) در budget برابر |
| ۲h | یک cross-domain کوچکِ هم‌ساختار (triage دادهٔ مصنوعی با sensorهای decoy) |
| ۱h | shadow autonomy run با triggerِ صرفاً telemetry + audit کاملِ provenance |

**سه پاسخِ مجاز در پایان:** `Heuristic-local` / `Conditional-epistemic-capability` / `Bounded-self-initiated-research`. هیچ‌کدام «AGI» نیست.

---

## ۱۱. تست‌های اجباری (fail-closed، هر ۱۲ مورد باید سبز شوند)

1. claim بدون falsifier یا operational_definition → **block**
2. claim با testability=0 → هیچ plan/packet ساخته نشود
3. receipt با `git_sha`/`config_hash` قدیمی → **block** (STALE)
4. receipt با command/seed/environment متفاوت → **block**
5. نتیجهٔ `inconclusive` → belief را افزایش ندهد
6. rule-reversal → belief/policy prediction متفاوت بسازد
7. evidence بدون producer مجاز → **block**
8. timeout/crash/malformed artifact → `INCONCLUSIVE` یا `BLOCKED`، نه pass
9. زنجیرهٔ receipt با `prev_receipt_hash` غلط → **block**
10. هر write بیرونِ `outputs/epistemics/` → fail
11. run با `STOP-ORGANISM`/`HALT-ALL` → فقط proposal؛ executor اصلاً صدا زده نشود
12. هر نتیجه با seed/hash یکسان → **replayable**

---

## ۱۲. پیامدها

- **مثبت:** حلقه مجبور می‌شود فرقِ «مدلِ یک جهان» و «موفقیتِ تصادفی» را نشان دهد؛ هر ادعا به evidence تازه، محدود، بازتولیدپذیر و قابل‌حسابرسی متصل می‌شود؛ artifactِ گمشدهٔ ممیزی #1 (provenance) ساخته می‌شود.
- **هزینه:** وابستگیِ Pydantic محدود به کابین؛ پیچیدگیِ گیت و hashing؛ نگهداریِ generator.
- **خنثی‌شده:** هیچ اثرِ جانبیِ تولیدی؛ invariant صداقتِ ARCHITECTURE-BIBLE دست‌نخورده؛ `may_execute=False` تضمین‌شده.

## بدیل‌های ردشده
- **ادغام در hypothesis-engine بدون کابینِ جدا:** خلطِ «تولید فرضیه» با «آزمونِ فرضیه» → رد.
- **اجازهٔ may_execute پس از SUPPORTED:** نقضِ fail-closed → رد.
- **پذیرشِ evidence بر پایهٔ متنِ ایجنت:** نقضِ DNAی «شواهد-نه-ادعا» → رد.
- **استفاده از grid ثابت به‌جای generator:** overfit، بی‌قدرت برای تفکیک ۴ تبیین → رد.

---
*تولیدشده با پایبندی به: Improve don't rewrite · fail-closed · propose-only · بدون اثر جانبیِ تولیدی · شواهد-نه-ادعا*

---

## پیوست — وضعیتِ پیاده‌سازی (Implementation status)

> این پیوست پس از ثبتِ سند اضافه شد. **وضعیتِ ADR همچنان PROPOSED است** (نیازمندِ رأیِ مالک)؛
> این بخش فقط ثبتِ آنچه از نقشهٔ راهِ §9 واقعاً ساخته شده.

**Commit 1 (C1) — پیاده، تست‌سبز، نه wired (2026-08-12):**
- `schemas.py` — Pydantic v2 (`strict=True, extra="forbid", frozen=True`): `EpistemicClaim`،
  `TestPlan`، `BindHashes`، `EvidenceReceipt`، `GateDecision` + `Prediction`/`Falsifier` + ۶ enum.
  تمامِ مرزهای §7 در سطحِ type/validator: `may_execute=False`، `sandbox=no_network`،
  `authority=propose`، `testability>0`، `prior∈(0,1)`، کلیدهای الزامیِ غیرقابل‌حذف.
- `canonical.py` (stdlib) — canonical JSON → SHA-256، حذفِ فیلدهای خودارجاع، `chain_hash`، `material_hash_of`.
- `policy.yaml` + `policy.py` (stdlib) — بارگذارِ fail-closed (missing/invalid ⇒ STOP)؛ سقف‌های hard ceiling.
- `validator.py` (pure) — claim/plan/receipt/decision با `reason_codes`.
- تست: `_ops/tests/test_epistemic_schemas.py` — **۴۵/۴۵ سبز**؛ پوششِ §11 (#1,#2,#3,#4,#7,#9,#12) در محدودهٔ pure validation.

**ADR-037 amend:** `_ops/epistemics/schemas.py` دومین کابینِ Pydanticِ `_ops` شد (پس از
`hypothesis_engine/impl/schemas.py`). سطحِ Pydantic محدود به همان یک فایل است.

**تأیید نشده (نیازمندِ رأی مالک پیش از wiring):** C2 (receipt chain + provenance + replay) →
C3 (parametric generator + sandbox runner + test_planner) → C4 (causal + bayes + multi_agent) →
C5 (cortex wiring، `EPISTEMIC_TESTS=0`) → C6 (owner packet) → C7 (shadow run + گزارشِ امضاشده).

**Commit 2 (C2) — پیاده، تست‌سبز، نه wired (2026-08-13):**
- `canonical.py` — `append_chained` / `verify_hash_chain` / `last_chain_hash` + `ChainVerification` (helpers مشترکِ hash-chain).
- `schemas.py` — `ProvenanceEdge` + `Initiator` (قراردادِ یالِ DAG خودمختاری، §2).
- `receipt_store.py` — `ReceiptStore` (append-only، `parent_receipt_hash` linkage، path-confined به `_ops/epistemics`|`outputs/epistemics`) + `sign_segment`/`verify_segment` (HMAC).
- `provenance.py` — `ProvenanceWriter` + `classify_initiation` (self/human/mixed) + `verify_provenance`.
- تست: `test_epistemics_receipt_chain.py` — **۲۰/۲۰ سبز**؛ §11 #9 (chain_break)، #10 (path confinement)، #12 (replay byte-identical) + tamper/segment/classify.

**وضعیت git:** C1 committed (`795a052`)، C2 committed (`31d3d7c`). رأیِ git حل‌شده (مالک: «هردو» 2026-08-13).
