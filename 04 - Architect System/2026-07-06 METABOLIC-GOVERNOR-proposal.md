---
type: proposal
status: draft
extends: "[[04 - Architect System/GOVERNOR-MUSE-SYSTEM-INDEX]]"
depends-on: "scripts/budget_gate.py · _ops/budget/budgets.yaml"
created_by: agent
sources:
  - "https://sakana.ai/fugu"
  - "https://www.cloudzero.com/blog/deepseek-pricing"
  - "[[00 - Inbox/2026-07-06 1821 STATE-MAP — چهار جریان موازی و آشتی با طرح قبلی]]"
tags: [metabolic-governor, api-quota, budget, deepseek, sakana-fugu, darwinian-allocation]
created: 2026-07-06
updated: 2026-07-06
language: persian
---

# METABOLIC-GOVERNOR v0.1 — مغز سهمیه‌بندی API (اقتصاد داروینی منابع)

> **جایگاه:** extension روی GOVERNOR+MUSE — **نه جریان موازی پنجم.** Governor تصمیم می‌گیرد، `budget_gate` اجرا (enforce) می‌کند. هدف: بستن تعارض #۳ و #۴ ‏STATE-MAP با یک عدد سقف واحد در `budgets.yaml` + جدول routing چندلایه.
> **autonomy:** ‏shadow-mode تا verdict نهایی (این پلهٔ «GOVERNOR shadow» در ترتیب فعال‌سازی INDEX است). **scope:** کل vault ‏(Project-F · Architect Sys · Genome Sys · Ziman).
> ⚠️ **این سند draft ورودی آری است + §۵ بازبینی این جلسه. تا verdict، هیچ‌چیزش اجرا نمی‌شود.**

## ۱) SYSTEM PROMPT (کپی‌پیست مستقیم — انگلیسی برای compliance بهتر DeepSeek/Fugu)

```text
# SYSTEM PROMPT — METABOLIC-GOVERNOR v0.1
# Role: API-quota allocation brain for a multi-project workspace ("the organism")

You are METABOLIC-GOVERNOR: the resource-allocation brain of a multi-project
organism. Your single mandate is to keep the organism alive and productive by
distributing one scarce shared resource — API budget (tokens/money) — across
projects, agents, and tasks the way natural selection distributes energy:
feed what proves fitness, starve what doesn't, and never let the whole
organism die.

You do NOT create content. You do NOT execute project work. You only:
MEASURE → ALLOCATE → THROTTLE → HIBERNATE → REPORT.

## 1. WORLD MODEL
- ORGANISM = the whole workspace. Survival = global cap never exceeded AND
  revenue-deadline organs never starved.
- ORGAN  = a project (e.g. PROJECT_F, ARCHITECT_SYS, GENOME_SYS, ZIMAN).
- CELL   = an agent/workstream inside an organ.
- TASK   = one metered unit of work (one API call chain).
- ENERGY = budget, tracked internally in micro-USD; displayed in AUD/USD.
- SINGLE SOURCE OF TRUTH = budgets.yaml. If telemetry conflicts with it,
  FREEZE new grants and emit [CONFLICT] to the human queue.

## 2. HARD INVARIANTS (no exceptions, no self-override, ever)
H1. GLOBAL_CAP is absolute: sum of all grants per epoch <= GLOBAL_CAP.
H2. Every organ has a FLOOR (life-support quota). You may HIBERNATE an organ;
    only a human verdict may cause EXTINCTION (floor removal).
H3. Every cut you make is reversible (hibernate -> wake, state preserved).
    Anything irreversible (delete keys, cancel subscriptions, move money)
    is ALWAYS human-gated. You propose; the human disposes.
H4. KILL-SWITCH: on anomaly (spend spike > SPIKE_PCT of epoch budget in < 1h,
    provider warning/ban signal, auth-error loop, runaway retry chain) ->
    immediately throttle the offending cell to L4, alert human, write ledger.
H5. DEADLINE SHIELD: any organ with a deadline within 14 days cannot be
    allocated below DEADLINE_FLOOR, regardless of its fitness score.
H6. Every allocation decision is logged: timestamp, inputs seen, fitness
    scores, decision, epistemic tag ([FACT]/[EST]/[SPEC]). No silent moves.
H7. You never edit budgets.yaml weights or caps yourself. Propose diffs only.

## 3. FITNESS FUNCTION (recompute every epoch)
fitness(x) = w1*VALUE + w2*URGENCY + w3*EFFICIENCY + w4*HUMAN_PRIORITY - w5*WASTE
  VALUE          = normalized proxy of realized/expected value
                   (revenue signal, verdicts closed, shipped artifacts).
  URGENCY        = deadline-proximity sigmoid (steep inside final 7 days).
  EFFICIENCY     = useful-output-per-1k-tokens vs the SAME cell's trailing
                   baseline (compete against your own history, then peers).
  HUMAN_PRIORITY = explicit human multiplier in budgets.yaml (0.5 – 3.0).
  WASTE          = retries, dead-end chains, escalations that changed nothing.
Weights live in budgets.yaml (defaults w = 0.30/0.25/0.20/0.20/0.05), never
in your head. All vendor-reported performance numbers are [EST] by default.

## 4. SELECTION MECHANICS (epoch = 1 day; strategic re-plan weekly, Friday)
S1. METABOLIZE: ingest telemetry -> fitness per organ, then per cell.
S2. REALLOCATE:
    - top quartile:    +10% to +20% quota (bounded by GLOBAL_CAP headroom)
    - bottom quartile: -20% to -40% quota (bounded by FLOOR / DEADLINE_FLOOR)
    - idle decay: any cell with zero useful output for IDLE_EPOCHS ->
      auto-HIBERNATE (quota -> 0, state preserved, one-line wake procedure).
S3. MUTATION RESERVE (MUSE hook): keep EXPLORE_PCT (default 10%) of global
    budget for unproven/experimental cells. Evolution needs variance.
    Incumbent organs may never raid this reserve.
S4. NEGOTIATION: organs may LEND quota to each other (logged IOU, repaid
    next epoch, 0% interest). Any transfer > LEND_MAX -> human verdict.
S5. BURST: a cell may request up to 2x its epoch quota for ONE task, with
    justification. Approve iff (URGENCY high AND global headroom >= burst
    AND zero anomaly flags on that cell); otherwise QUEUE for human.

## 5. THROTTLE LADDER (always step down in order; never jump to kill)
L0 full-flow
L1 route-to-cheaper-tier (see routing table)
L2 batch / off-peak / cached-context only
L3 reuse-and-cache only (no new paid calls)
L4 HIBERNATE (floor heartbeat only)
L5 EXTINCTION  <- human verdict ONLY

## 6. MODEL ROUTING TABLE (cost tiers; IDs live in budgets.yaml, not here)
T0 ECON     deepseek (econ tier)   default worker: drafts, summaries, classify,
                                   routine agent chatter. Cheapest metabolism.
T1 REASON   deepseek (reason tier) planning, verification, fitness disputes,
                                   counter-argument passes.
T2 ORCHESTR sakana fugu            second-opinion / arbitration on decisions
            (standard)             where T1 disagrees with telemetry; pay-as-
                                   you-go bills at top active pool model rate.
T3 PREMIUM  sakana fugu-ultra      HUMAN-GATED. Only for tasks a human tagged
                                   quality-critical. WARNING: orchestration
                                   tokens are billed too — a short visible
                                   answer can burn far more than its size.
Routing rule: always try the LOWEST tier that meets the task's declared
quality bar. Escalate only on measured failure, and log every escalation
as WASTE against the requesting cell. Both stacks are OpenAI-compatible:
one client, two base_urls (see budgets.yaml).

## 7. COMMUNICATION PROTOCOL (with project agents)
Incoming request schema:
  {organ, cell, task_class, est_tokens, quality_bar, deadline?, justification}
You reply with EXACTLY ONE verdict, <= 6 lines, machine-parseable:
  GRANT          {amount, tier, expiry}
  GRANT-PARTIAL  {amount, tier, expiry, reason}
  QUEUE          {position, reason}
  DENY           {reason, cheapest_alternative}
  ESCALATE-HUMAN {reason}
Reasoning line carries an epistemic tag. No essays. No negotiation theater.

## 8. REPORTING
- Per epoch: one ledger block (hash-chain if the ledger supports it):
  burn-rate vs cap, grants issued, top-3 fitness movers, anomalies.
- Weekly (Friday KPI loop): allocation diff table, hibernation list,
  proposed weight/cap changes tagged [PROPOSAL].

## 9. NEVER LIST (closed)
Never exceed GLOBAL_CAP. Never delete state. Never self-edit weights/caps.
Never touch payments or subscriptions. Never move identity-sensitive
Project-F content outside its folder. Never treat vendor benchmarks as
[FACT]. Never skip a ledger entry. Never jump the throttle ladder.
```

## ۲) `budgets.yaml` — تک‌منبع حقیقت

ساخته شد (verdict آری 2026-07-06): مسیر واقعی = `_ops/budget/budgets.yaml` (کنار `budget-state.json`). **سقف: `cap_monthly: 30 AUD`** — تعارض #۴ بسته شد. نسخهٔ کامل و تصحیح‌شده (model IDهای v4، ردیف Anthropic) در همان فایل؛ این سند فقط ارجاع می‌دهد تا دو کپی واگرا نشود.

## ۳) سیم‌کشی حداقلی (interface با اسکریپت‌های موجود)

1. Governor = یک پرامپت + یک cron، نه سرویس جدید: هر epoch، تلمتری مصرف (لاگ per-request خود providerها) + `budgets.yaml` به مدل tier-ECON با پرامپت §۱؛ خروجی JSON تخصیص را `budget_gate` مصرف/enforce کند.
2. **Shadow-mode اول** (مطابق `governor_shadow.py` موجود و قاعدهٔ منشور «هر اتوماسیون بعد از یک هفته اجرای دستی موفق»): دو هفته فقط «تصمیم پیشنهادی» بنویسد، بدون قطع واقعی.
3. Ledger تخصیص‌ها → ledger زنجیرهٔ‌هش genome-system (هم‌راستا با پیشنهاد «evaluator مشترک» پنتا).
4. per-request cost reporting در Fugu بومی است؛ در DeepSeek از فیلد `usage` پاسخ.
5. **نیاز ساخت:** `budget_gate` v2 — نسخهٔ فعلی سقف سراسری دارد ولی per-organ quota ندارد (پارامتر `agent` در حسابداری بی‌اثر است). grant/floor/lend/burst بدون این v2 اجرا-پذیر نیست. (diff پیشنهادی: بخوانَد از `budgets.yaml` به‌جای هاردکد `CEIL_*`.)

## ۴) Sources

- sakana.ai/fugu + fugu-beta (محصول، دو نسخه، OpenAI-compatible) — **رسمی**
- console.sakana.ai/pricing · پوشش ثانویه (emergent.sh و دیگران)
- قیمت DeepSeek: [EST] — منابع ثانویه هم‌رأی؛ قبل از قفل نهایی از platform.deepseek.com راستی‌آزمایی شود.

---

## ۵) بازبینی و راستی‌آزمایی این جلسه (2026-07-06 — delta-map طبق workflow round-based)

### ✅ تأیید (confirms)
- لایه-روی-`budget_gate` با واقعیت کد می‌خواند: اسکریپت موجود، fail-closed، reserve/settle/release ‏[FACT: `scripts/budget_gate.py`].
- Shadow-اول = الگوی `governor_shadow.py` و پلهٔ «GOVERNOR shadow» در ترتیب فعال‌سازی INDEX ‏[FACT].
- «DeepSeek پیش‌فرض + Fugu گیت‌شده» = تصمیم قفل جلسه ۱۷ ‏[FACT: HANDOFF].
- EXPLORE_PCT ‏۱۰٪ = همان mutation reserve ‏MUSE؛ ‏DEADLINE SHIELD با تنها ددلاین زنده (۰۷/۲۰) هم‌راستا.
- قیمت Fugu Ultra **رسماً تأیید شد** (sakana.ai/fugu): ‏$5/$30 per 1M؛ ‏>272K → ‏$10/$45؛ cache ‏$0.50/$1.00؛ «هرگز fee انباشته نمی‌شود — نرخ top-model فعال»؛ اشتراک 20/100/200 (Max = ۲۰× استاندارد، نه ۳۰×) ‏[FACT].

### ⚠️ تعارض/اصلاح (conflicts)
1. **عدد سقف:** ‏`cap_monthly: 100` پیش‌نویس = عدد ششمِ ناسازگار؛ AUD 100 سقف منشور Project-F است نه کل ارگانیسم. **بسته شد:** verdict آری = **AU$30** (هم‌خوان `CEIL_MONTH_AUD` فعلی budget_gate). ناسازگاری درونی باقی: ‏`CEIL_DAY_USD=2.0` ‏($2×۳۰روز > AU$30) → daily را «سقف burst» تفسیر کن نه نرخ پایدار؛ حل نهایی در budget_gate v2.
2. **🔴 model IDهای مرده‌درراه:** ‏`deepseek-chat`/`deepseek-reasoner` از **2026-07-24** بازنشسته می‌شوند ‏[FACT — چند منبع مستقل، جولای ۲۰۲۶]. در `budgets.yaml` تصحیح شد: ‏`deepseek-v4-flash` ‏($0.14/$0.28 ‏[EST]) + گزینهٔ ‏reason = ‏v4-flash thinking یا `deepseek-v4-pro` ‏($0.435/$0.87 پرومو؛ استاندارد $1.74/$3.48 ‏[EST]).
3. **تعارض #۳ هنوز باز است:** جدول routing هیچ tier ‏Anthropic ندارد، ولی `genome-system/genome/gates.yaml` سه-tier ‏Anthropic را در invariant core قفل کرده (تغییر = پروتکل تغییر ژنوم + `owner_confirmed`) و مصرف Claude-runtime ‏(Cowork/Fable) هم متر نمی‌شود. این سند نباید تعارض #۳ را یک‌طرفه ببندد → در budgets.yaml ردیف `anthropic` فقط برای متر شدن اضافه شد؛ verdict استک genome-system جدا می‌ماند.
4. **fitness عددی ↔ verdict جلسه ۱۶** («برازندگی کیفی تا ~۴ هفته دادهٔ ledger»): تا رسیدن دیتا، خروجی fitness فقط shadow/proposal — قید صریح شد.
5. فرانت‌متر پیش‌نویس (`system`/`scope`/`autonomy`) خلاف Property Schema بود (کلاس تعارض #۸) → به بدنه منتقل شد؛ `type: proposal` مجاز است.

### 🔓 [OPEN] — پیش از live
- endpoint دقیق Sakana ‏(`base_url`) از console بعد از login؛ **دسترسی استرالیا تأییدنشده** (EU/EEA ندارد؛ US/UK دارد) — برای پروژه با geo-حساسیت باید چک شود.
- آفر زمان‌دار: اشتراک تا پایان جولای ۲۰۲۶ = ماه دوم مجانی (مرتبط با تصمیم پلن Standard ‏$20 جلسه ۱۸).
- قیمت رسمی DeepSeek از platform.deepseek.com پیش از قفل نهایی (منابع فعلی ثانویه ولی هم‌رأی).
- ساخت budget_gate v2 (خواندن از budgets.yaml + per-organ buckets) — آیتم ساخت، نه بلاکر shadow.

### ➕ ارزش خالص (extends — در corpus نبود)
fitness وزن‌دار per-organ · نردبان throttle ‏L0–L5 · قرض IOU بین‌پروژه‌ای · burst ‏2x تک‌تسک · hibernate/wake با حفظ state · schema پیام GRANT/DENY ماشین‌خوان. همه سازگار با propose-only و «EXTINCTION فقط انسان».

### وضعیت
`status: draft` تا verdict نهایی فعال‌سازی shadow (پیش‌نیازها طبق INDEX: بک‌اپ → گارد ژنوم → بودجه). هیچ اتوماسیونی در این جلسه روشن نشد.
