# RESEARCH LANE — Evaluation & observability
# ارزیابی و observability سیستم‌های agentic — ۲۰۲۵–۲۰۲۶

> **DOMAIN:** سیستم‌های multi-agent خودمیزبان برای اپراتور تک‌نفره.
> **LANE (قفل‌شده):** فقط evaluation، observability/tracing، drift detection، و regression gate برای self-modification — نه memory، نه governance به‌طورِ مستقل.
> **CONSTRAINTS:** VPS مشترک + لپ‌تاپ + Claude Cowork؛ تک‌نفره؛ export-first، no vendor lock-in؛ per-action cap + kill switch + audit log.
> **تاریخِ ساخت:** ۲۰۲۶-۰۷-۰۱. منابع از web search زنده. برچسب: `[established] / [emerging] / [speculative]`.

---

## Summary

۱. **حقیقتِ ناخوشایند اول:** Langfuse (توصیه‌ی ۸۰٪ تیم‌ها در ۲۰۲۵) توسطِ ClickHouse Inc. در ژانویه ۲۰۲۶ خریداری شد. MIT license دست نخورده است، ولی roadmap آینده نامشخص است. و از آن مهم‌تر: برای self-host باید ۵+ service بالا بیاوری (ClickHouse + Postgres + Redis + S3 + app server). **MLflow (Apache 2.0، Linux Foundation)** یک self-host ساده‌تر با Postgres-only و نه enterprise paywall است و در ۲۰۲۶ جدی‌ترین رقیبِ Langfuse شده. `[established]`

۲. **بنیادی‌ترین تمایزِ eval:** ارزیابیِ agent با ارزیابیِ LLM فرق دارد. LLM: یک prompt-response pair. Agent: یک trajectory — توالیِ reasoning، tool calls، و تصمیم‌های میانی. **پاسخِ نهاییِ درست می‌تواند یک trajectoryِ شکسته را پنهان کند.** `[established]`

۳. **سه لایه‌ی eval که همه لازم‌اند:** (L1) end-to-end outcome (آیا task موفق شد؟)، (L2) trajectory quality (آیا مسیر درست بود؟)، (L3) component-level (کدام tool یا step شکست؟). 57٪ سازمان‌هایی که agent در production دارند، کیفیت را مانعِ شماره‌یکِ deployment می‌دانند — و outcome-only eval نمی‌تواند این را حل کند. `[established]`

۴. **LLM-as-judge پنج bias شناخته‌شده دارد** که بدونِ calibration، dashboard را سبز نشان می‌دهد درحالی‌که system در حالِ خراب شدن است. Cohen's kappa با human reviewer باید ≥0.7 باشد تا به score اعتماد کنی. `[established]`

۵. **minimum viable setup برای تک‌نفره:** OpenLLMetry (instrumentation، vendor-neutral) + MLflow یا Braintrust free tier (eval + dashboard) + یک eval suite با ۵۰–۱۰۰ anchor case دستی. این از zero-setup به production-meaningful signal می‌رسد. `[Probable]`

---

## Landscape

**۱) سه لایه‌ی evaluation — چه، کِی، چرا.** `[established]`

**L1 — End-to-end outcome:**
ساده‌ترین. آیا agent task را تکمیل کرد؟ Binary (موفق/شکست) یا rubric-scored. مشکل: یک agent که درست جواب می‌دهد ولی از مسیرِ غلط، یا یک agent که اشتباهِ میانی داشت ولی recover کرد، هر دو ممکن است همان L1 score را داشته باشند. Outcome-only برای debugging بی‌فایده است.

**L2 — Trajectory quality:**
مهم‌ترین لایه برای multi-agent. ارزیابیِ هر stepِ میانی: آیا tool درستی انتخاب شد؟ آیا argumentهای tool درست بودند؟ آیا reasoning coherent بود؟ آیا agent loop کرد بدونِ دلیل؟ آیا بعد از شکستِ tool recover کرد؟ این جایی است که «real signal lives». نمره‌ی trajectory روی یک مجموعه‌ی 200+ trajectory قبل از نتیجه‌گیری — per-trajectory scores noisy هستند.

**L3 — Component-level:**
کدام sub-agent، retriever، یا tool شکست؟ برای debugging یک failure: trace را باز کن → failure cascade را دنبال کن → ریشه را در span 42 پیدا کن که باعثِ شکستِ span 1800 شد. این نیازِ به nested span tree داری.

**۴ نوع span که هر trajectory به آن‌ها نیاز دارد:**
- `model_call` (input، output، tokens، latency، cost)
- `tool_call` (نام، arguments، result، success/fail)
- `reasoning` (planning steps، intermediate decisions)
- `handoff` (delegation به sub-agent)

**نکته‌ی مهم:** «Step-level tracing — not pass/fail health checks — is the minimum viable signal for an agent in production.» `[established]`

---

**۲) LLM-as-judge — قدرت، biasها، و calibration.** `[established]`

**چرا استفاده می‌شود:** تنها روشی که در مقیاس کار می‌کند. human review نمی‌تواند همه‌ی production traceها را بخواند. judge model یک rubric می‌گیرد، trajectory یا output را می‌خواند، و score + critique برمی‌گرداند.

**پنج biasِ مستندِ ۲۰۲۶:**
1. **Position bias:** در pairwise comparison، گزینه‌ی اول («slot A») 10–15 امتیاز بیشتر می‌گیرد صرفاً به خاطرِ جایگاهش.
2. **Verbosity bias:** پاسخِ طولانی‌تر حتی با کیفیتِ یکسان، نمره‌ی بالاتر می‌گیرد.
3. **Self-preference (Family bias):** judge مدلی از خانواده‌ی خودش را 10–25٪ بالاتر از بقیه score می‌دهد. یک judge از خانواده‌ی GPT که outputs را از GPT-4 ارزیابی می‌کند = اعداد دروغین.
4. **Format bias:** judge خروجی‌هایی را ترجیح می‌دهد که با formatِ rubricِ خودش هم‌خوانی دارند.
5. **Calibration drift:** با گذشتِ زمان، اگر rubric تغییر نکند ولی agent behavior تغییر کند، score دیگر calibrate نیست.

**نمونه‌ی failure:** یک تیم یک judge برای groundedness ساخت، judge را GPT-4 انتخاب کرد، production outputs از GPT-4 بودند. سه ماه همه چیز سبز بود. سپس یک domain expert پنجاه output خواند — کاپای Cohen بین judge و expert: 0.31. judge systematically GPT-4 outputs را over-reward کرده بود و hallucination روان را under-penalize کرده بود.

**راه‌حل‌های calibration:**
- انتخابِ judge از خانواده‌ی متفاوت از مدلِ productionِ تو
- shuffle ترتیبِ گزینه‌ها (رفع position bias)
- انجامِ human-judge agreement check روی ≥50 case؛ target کاپای ≥0.7
- استفاده از distilled small judges برای production (Galileo Luna، future AGI flash) — 10–50x ارزان‌تر از frontier judges
- Sample rate: 5–20٪ production traces + 100٪ errorها و outlierها

**Agent-as-a-Judge (emerging، ۲۰۲۵–۲۰۲۶):** به‌جای یک LLM، یک agent کاملِ با reasoning و tool-use برای evaluate کردنِ trajectoryِ agentِ دیگر. قوی‌تر برای multi-step tasks، ولی گران‌تر. `[emerging]`

---

**۳) ساختنِ eval dataset — چه، چقدر.** `[established]`

سه منبع برای case:
1. **Hand-crafted anchor set (۵۰–۱۰۰ case):** خودت می‌نویسی، با expected trajectory و gold output. گران‌ترین ولی باکیفیت‌ترین. پوشش‌دهنده‌ی critical use-caseهای تو. این «anchor set» است که regression را حول آن می‌سنجی.
2. **Production failure mining:** trace‌های production که fail شدند یا anomalous بودند را filter کن، label بزن، به eval set اضافه کن. high ecological validity — مشکلاتِ واقعیِ کاربران واقعی. این eval set را با گذشتِ زمان زنده نگه می‌دارد.
3. **Synthetic generation:** یک strong LLM از anchor set variations تولید می‌کند. برای volume.

**Volume targets 2026:** ≥500 case قبل از اینکه به aggregate metrics اعتماد کنی. زیر 200، per-trajectory scores خیلی noisy‌اند. **ولی برای regression gate و acceptance gate:** 50–100 anchor case کافی است تا «اکثرِ regression pattern‌ها را بگیری.»

---

**۴) Regression gate و self-improvement acceptance gate.** `[established]`

**این بخش مستقیماً با lane 3 connect می‌شود:** قبل از permanent شدنِ هر skill/modification، باید از این gate رد شود.

**minimum viable regression gate:**
```
قبل از هر commit جدید به skill library / system-prompt / SKILL.md:
1. اجرای eval suite روی anchor set (50–100 case)
2. Pass criteria:
   a. Regression: score روی قبلاً-موفق‌شده‌های anchor ≤X٪ کاهش (X = threshold تعریف‌شده‌ی تو، مثلاً 5٪)
   b. Target improvement: score روی کیسِ هدف ≥Y٪ بهتر شده
   c. No new failure categories: هیچ failure نوعِ جدیدی که در anchor set نبود ظاهر نشده
3. اگر همه pass → skill commit می‌شود
4. اگر هر کدام fail → skill به rejected-step buffer می‌رود (negative feedback برای یادگیری)
```

**نکته‌ی اضافه:** «Do not ask yourself whether the skill improved. Ask whether the system got better.» یعنی همیشه regression را روی *کلِ* anchor set بسنج، نه فقط روی task هدف.

**LangChain's 2026 State of AI Agents report:** 57٪ سازمان‌ها agent در production دارند و کیفیت #1 barrier است. این یعنی regression gate یک business necessity است، نه نیسِ-to-have.

---

**۵) Observability tools — وضعیتِ ۲۰۲۶.** `[established]`

**مهم‌ترین خبرِ ساختاری:** Langfuse در ژانویه ۲۰۲۶ توسطِ ClickHouse Inc. خریداری شد. MIT license هنوز دست نخورده است و capabilities فعلاً تغییر نکرده‌اند ولی roadmapِ بلندمدت نامشخص است. این یک `[established]` risk است که قبل از commit به self-hosting باید در نظر گرفت.

**چهار دسته‌ی اصلی:**

**(A) OSS fully self-hostable:**

**MLflow (Apache 2.0، Linux Foundation، 30M+ monthly downloads):**
جامع‌ترینِ open-source. Tracing، evaluation، prompt management، governance، AI gateway در یک platform. `autolog()` یک خطی برای ۳۰+ framework (OpenAI، Anthropic، LangGraph، DSPy، CrewAI، ...). Storage: Postgres یا هر RDBMS رایجی + object storage = ساده‌ترین self-host در این دسته. نه enterprise paywall روی هیچ feature‌ای. تنها پلتفرمی که evaluation، fine-tuning tracking، و model registry را یکجا دارد. **توصیه‌ی MLflow: انتخابِ اول برای تو.** `[established]`

**Arize Phoenix (Elastic License 2.0):**
OTel-native، OpenInference semantic conventions، قوی در eval. ولی: drift detection و production analytics فقط در Arize AX commercial tier هستند. برای pure tracing + eval = open-source کافی است. `[established]`

**Laminar (Apache 2.0):**
agent-first: transcript view، long-running run support، SQL over traces، browser-agent session replay. Helm chart برای one-command self-host. هر feature در OSS image. `[emerging]`

**(B) OSS با cloud-first:***

**Langfuse (MIT، acquired ClickHouse):**
self-host نیازِ ۵ service دارد: ClickHouse + Postgres + Redis + S3 + app server. برای eval، evaluation logic را خودت باید wire کنی (out-of-the-box evalها محدود است). بهترینِ موجود برای teams با data residency requirements که ClickHouse دارند. `[established]`

**(C) Instrumentation layer (همه backend را می‌پذیرند):***

**OpenLLMetry / Traceloop (Apache 2.0):**
vendor-neutral OTel-based instrumentation. با یک SDK instrumentation می‌کنی، trace را به هر backend می‌فرستی (Langfuse، MLflow، Phoenix، LangSmith). «امن‌ترین انتخاب برای portability: instrument once، switch backends later without re-instrumenting.» `[established]`

**(D) SaaS (برای اطلاع، نه توصیه برای تو):**

**Braintrust:** generously free (1M spans/ماه، unlimited users، 10K eval run). CI/CD gated deployment. eval-first. No self-host option. `[established]`
**LangSmith:** قوی‌ترین برای LangGraph/LangChain. closed-source. self-host فقط Enterprise. `[established]`
**Latitude (commercial):** agent-native، issue tracking lifecycle، GEPA auto-generated evals. `[emerging]`

---

**۶) Drift detection — چطور بفهمیم performance بدتر شده.** `[established]`

سه نوعِ drift برای agentهای multi-project:

1. **Output distribution drift:** آیا score averageِ agent روی همان anchor set کاهش یافته؟ → هر هفته eval suite را اجرا کن و trend را track کن.
2. **Behavioral drift:** آیا agent tool calls متفاوتی می‌زند؟ آیا step count تغییر کرده؟ → trace metrics (avg step count، tool selection frequency، error rate per tool) را monitor کن.
3. **Cost/efficiency drift:** آیا هزینه‌ی token per task افزایش یافته بدونِ بهبودِ کیفیت؟ → cost-per-task را tracke کن.

**minimum viable drift detection برای تک‌نفره:**
- هر هفته: eval suite را روی anchor set اجرا کن؛ اگر score ≥5٪ کاهش داشت → investigate
- هر روز: cost-per-task و error-rate-per-tool را در dashboard ببین
- alert: روی latency spike و error-rate threshold alert بگذار (Slack یا email)

**ابزارِ drift detection در OSS:** Arize Phoenix (ML heritage دارد ولی production analytics commercial است)، MLflow (manual drift tracking + experiment comparison).

---

## Comparison table

> نمره‌ی ۱–۱۰: بهترین برای تک‌نفره/VPS مشترک/export-first. `[Probable]` جز جایی که صریح data داریم.

| Tool | Cost | Complexity | Self-host | Eval Depth | Agent-Native | Maturity |
|---|---|---|---|---|---|---|
| **MLflow (Apache 2.0)** | 10 | 8 | 9 | 8 | 6* | 9 |
| **OpenLLMetry / Traceloop (Apache 2.0)** | 10 | 8 | 9 | 3† | 7 | 7 |
| **Arize Phoenix (Elastic 2.0)** | 9 | 7 | 8 | 7 | 7 | 7 |
| **Laminar (Apache 2.0)** | 9 | 7 | 8 | 7 | 9 | 5 |
| **Langfuse (MIT، post-acquisition)** | 8 | 5 | 7‡ | 6 | 6 | 8 |
| **Braintrust (SaaS)** | 7 | 9 | 1 | 9 | 7 | 8 |
| **LangSmith (SaaS)** | 6 | 8 | 1§ | 8 | 8 (LG) | 9 |
| **DeepEval (Apache 2.0)** | 9 | 7 | 8 | 8 | 6 | 7 |
| **Confident AI (commercial)** | 5 | 7 | 4 | 9 | 9 | 6 |

\* MLflow: LLM tracing اخیراً اضافه شده، agent-native features کمتر از Laminar است.
† OpenLLMetry: فقط instrumentation؛ eval layer نیازِ به backend جداگانه دارد.
‡ Langfuse self-host: ClickHouse اجباری = 5+ service؛ پیچیدگیِ ops واقعی.
§ LangSmith self-host: فقط Enterprise tier.

---

## Blind spots

- **Langfuse acquisition risk.** `[established]` ClickHouse در ژانویه ۲۰۲۶ Langfuse را خرید. MIT license دست نخورده است ولی product investment و roadmap ممکن است تغییر کند. هر تیمی که Langfuse self-host می‌کند باید این را risk factor بداند. MLflow یا Phoenix = safest alternative.

- **«Drift detection» در Phoenix OSS نیست.** `[established]` Phoenix (OSS، Elastic 2.0) tracing و eval عالی دارد ولی drift detection، online evaluation (5-minute cadence)، و production analytics در Arize AX commercial tier‌اند. اگر اینها لازمی، باید Arize AX را خریداری کنی یا drift detection را خودت بنویسی.

- **LLM-as-judge family bias می‌تواند کاملاً پنهان باشد.** `[established]` سه ماه dashboard سبز، judge Cohen's kappa با انسان 0.31. اگر judge model از خانواده‌ی مدلِ production‌ات باشد، این حتماً اتفاق می‌افتد. حداقل یک بارِ human-audit با ۵۰ case قبل از اینکه به eval score اعتماد کنی.

- **OTel GenAI conventions هنوز unstable است.** `[established]` در v1.41، اکثرِ `gen_ai.*` attributes برچسبِ «Development» دارند — یعنی attribute names می‌توانند بدونِ major version bump تغییر کنند. اگر pipeline را حولِ attribute names hardcode کردی، ممکن است با upgrade SDK شکسته شود. `[uncertain]` تا stable شدنِ spec.

- **«Trajectory evaluation» گران است.** `[Probable]` یک judge call برای ارزیابیِ یک trajectory کاملِ 12-step گران‌تر از evaluation یک single response است. در volume بالا به distilled small judges (Galileo Luna، future AGI flash) نیاز داری. ولی برای تو با volume کم، frontier judge برای ≤20٪ sample rate قابلِ تحمل است.

- **Production trace sampling ≠ eval suite.** `[established]` خیلی از تیم‌ها فکر می‌کنند logging production traces کافی است. نیست. eval suite = dataset ساختاریافته + gold labels + automated scoring. trace log = raw material که باید پردازش و label شود. این دو را قاطی نکن.

- **Self-improvement evaluation drift.** `[Probable]` اگر skill library تغییر کند ولی eval suite تغییر نکند، خطرِ specification gaming وجود دارد: agent یاد می‌گیرد روی همان case‌ها خوب باشد. راه‌حل: eval suite را با production failures rotate کن، و یک held-out «unseen set» داشته باشی که agent آن را ندیده.

- **Silent failure — agent درست به نظر می‌رسد ولی خراب است.** `[established]` «Final-output monitoring misses these failures because it can make agents appear more reliable than full trajectory evaluation reveals.» نمونه: agent درست جواب می‌دهد ولی هزینه‌ی غیرضروری 10 tool call اضافه دارد. یا agent با luck درست جواب داد ولی reasoning شکسته بود. فقط trajectory-level tracing این را می‌گیرد.

- **Langfuse ≠ full eval platform.** `[established]` «Langfuse is a backbone: you can attach scores, but faithfulness, hallucination, and similar metrics are not provided out-of-the-box — you wire your own judges or libraries.» خیلی از تیم‌ها با Langfuse شروع می‌کنند و بعد متوجه می‌شوند باید eval layer را جداگانه بسازند.

- **Volume target ≥500 قبل از اعتماد به aggregate metrics.** `[established]` با ۵۰ case برای regression gate کافی است. ولی برای تصمیم‌گیریِ «agent X از agent Y بهتر است»، به ≥200–500 case نیاز داری تا noise کم شود.

---

## Recommendation

**پیشنهادِ اصلی برای تک‌نفره روی VPS مشترک — سه‌لایه:**

### لایه‌ی ۱: Instrumentation (فوری، رایگان)

**OpenLLMetry (Apache 2.0) → یک instrumentation، هر backend:**
```python
from traceloop.sdk import Traceloop
Traceloop.init(app_name="project_mining")
# هر LLM call، tool call، و agent step خودکار trace می‌شود
```
این به تو آزادی می‌دهد بعداً backend عوض کنی بدونِ re-instrumentation.

### لایه‌ی ۲: Backend/Dashboard (MLflow یا Braintrust free)

**انتخاب اول — MLflow (Apache 2.0، self-host):**
- چرا: ساده‌ترین self-host در این category (Postgres + object storage، نه ClickHouse)، Apache 2.0 بدونِ enterprise paywall، هم tracing هم eval هم prompt management
- کجا: روی همان VPS که داری، با همان Postgres که DBOS و LANGAR رویش هستند
- محدودیت: agent-native features (transcript view، long-run debugging) کمتر از Laminar است

**انتخاب دوم — Braintrust free tier (تا scale شدی):**
- 1M spans/ماه، unlimited users، 10K eval runs رایگانِ واقعی
- CI/CD eval-gated deployment
- محدودیت: no self-host → data بیرون از VPS → ممکن است با export-first valueِ تو conflict داشته باشد

**⚠️ Langfuse با VPS مشترک:** اگر ClickHouse ندارید، self-hostِ آن ۵+ service می‌خواهد. برای تک‌نفره روی VPS مشترک، over-engineered است. اگر بعداً scale کردید، Langfuse cloud free tier (50k observations/ماه) یا MLflow را در نظر بگیر.

### لایه‌ی ۳: Eval suite + self-improvement gate (مرحله‌ی بعد)

**ساختنِ anchor set:**
1. ۱۵–۲۰ case per project/tenant، ۵۰–۱۰۰ کل
2. هر case: task description + expected trajectory (step order + tool selection) + gold output
3. حداقل سه rubric: reasoning quality، tool correctness، final answer quality
4. یک judge model که **از خانواده‌ی مدلِ productionِ تو نباشد**
5. human-audit: ۵۰ case اول را دستی بررسی کن تا kappa ≥0.7 مطمئن شوی

**self-improvement acceptance gate (ادغام با lane 3):**
هر skill proposal یا system-prompt change باید این سه شرط را رد کند:
- `regression_rate ≤ 5٪` روی anchor set (نسبت به baseline)
- `target_metric_delta ≥ +threshold` روی case هدف
- `new_failure_categories == 0` (هیچ failure pattern جدیدی)

**Minimum viable drift detection:**
- هر هفته: eval suite را اجرا کن؛ trend را در MLflow/Braintrust ببین
- هر روز: cost-per-task، error-rate، latency را در dashboard monitor کن
- هر ماه: ۱۰ case از production failures را به eval set اضافه کن

### دقیقاً چه چیزی را **نساز:**

- ❌ **Langfuse self-host اگر ClickHouse ندارید** — MLflow یا Braintrust free tier کافی‌تر است
- ❌ **LLM-as-judge از خانواده‌ی مدلِ production** — family bias = اعداد دروغین
- ❌ **Eval suite-فقط با synthetic data** — به حداقل ۵۰ anchor caseِ دستی نیاز داری
- ❌ **Outcome-only evaluation** — «did it succeed?» کافی نیست؛ trajectory باید سنجیده شود
- ❌ **Drift detection بدونِ anchor set** — نمی‌توانی بفهمی بدتر شدی اگر baseline نداشته باشی
- ❌ **Arize Phoenix commercial (AX)** برای drift — cost-benefit برای تک‌نفره توجیه ندارد؛ manual weekly eval کافی است
- ❌ **LangSmith** اگر data باید روی VPS خودت بماند — no self-host unless Enterprise
- ❌ **اعتماد به dashboard سبز بدونِ calibration** — داستانِ kappa 0.31 را به خاطر بسپار

---

## TOOLING

| Tool | Pricing | Best alternative | Lock-in (۱–۱۰) |
|---|---|---|---|
| **MLflow (Apache 2.0)** | OSS رایگان self-host؛ Databricks-hosted پولی | Arize Phoenix / Laminar | **1** — Linux Foundation، Apache 2.0 |
| **OpenLLMetry / Traceloop (Apache 2.0)** | OSS رایگان | direct OTel SDKs | **1** — portable instrumentation |
| **Arize Phoenix (Elastic 2.0)** | OSS رایگان self-host؛ Cloud $50/ماه+ | MLflow | **2** — OTel-native، portable |
| **Laminar (Apache 2.0)** | OSS رایگان self-host؛ Cloud tier | MLflow | **2** — Helm chart deploy |
| **Langfuse (MIT، ClickHouse)** | self-host رایگان (۵+ service)؛ Cloud $0/50k، $29+، $199+ | MLflow | **3** — MIT ولی ClickHouse lock-in + acquisition risk |
| **DeepEval (Apache 2.0)** | OSS رایگان | Braintrust / RAGAS | **2** — eval library، portable |
| **RAGAS (Apache 2.0)** | OSS رایگان | DeepEval | **1** — RAG-focused eval |
| **Braintrust (SaaS)** | Free: 1M spans، 10K evals؛ Pro $249+ | MLflow + manual eval | **7** — no self-host |
| **LangSmith (SaaS)** | Free: 5K traces؛ Plus $39/seat؛ Enterprise self-host | Langfuse (open) | **8** — closed + LangChain-native |
| **Galileo Luna (distilled judge)** | pay-per-use (`verify` pricing) | OpenAI mini + custom rubric | **5** — vendor-specific judge |

---

## If-I'm-wrong

**قوی‌ترین ضدِ توصیه («MLflow به‌جای Langfuse»):** Langfuse یک community بزرگ‌تر، مستنداتِ بیشتر، و ecosystem وسیع‌تر دارد. اگر ClickHouse acquisition به Langfuse دیتابیسِ بهتر و performanceِ بالاتر بدهد (که احتمالاً می‌دهد)، ممکن است بهترین انتخاب شود. ریسکِ اصلی این توصیه: MLflow‌ LLM tracing اخیراً اضافه شده و agent-native features آن کمتر است. **verify:** هر دو را با docker-compose روی VPS امتحان کن؛ MLflow setup ساده‌تر است ولی اگر بیشتر از ۵ دقیقه طول کشید، Braintrust free tier را انتخاب کن.

**ضدِ توصیه‌ی دوم («Anchor set 50 case کافی است»):** برای regression gate بله. ولی اگر بخواهی تصمیم بگیری «آیا model X بهتر از Y است»، باید ≥500 case داشته باشی. با کمتر از این، varianceِ LLM-as-judge نتایج را noisy می‌کند. توصیه: با ۵۰ شروع کن، بعد از ۶۰ روز با production failures به ≥200 برسان.

**ضدِ توصیه‌ی سوم («weekly eval کافی است»):** اگر در آینده agentهایت volume بالایی داشتند، weekly eval برای drift detection خیلی کند است. ولی برای مرحله‌ی فعلی (cold-start data)، حجم پایین است و weekly کافی است. trigger برای upgrade: وقتی >100 production run/روز داشتی، به daily eval + automated alert برو.

---

## Confidence

**High** برای landscape و tool comparison (منابعِ متعددِ ژانویه–ژوئن ۲۰۲۶). **Medium** برای خاص‌های MLflow vs Langfuse (هر دو در حالِ تکامل سریع‌اند؛ verify با latest docs). **Low** برای Langfuse post-acquisition roadmap (نامشخص). OpenTelemetry GenAI conventions هنوز Development stability = `[uncertain]` تا stable شدن.

---

## Claims table

| claim | evidence | confidence (H/M/L) | source + date |
|---|---|---|---|
| ارزیابیِ agent = trajectory، نه single response؛ پاسخِ نهاییِ درست می‌تواند trajectoryِ شکسته را پنهان کند | consensus در ادبیاتِ ۲۰۲۶ | H | confident-ai.com 2026؛ morphllm.com 2026 |
| سه لایه‌ی eval: L1 (outcome)، L2 (trajectory)، L3 (component) | evaluation frameworks | H | confident-ai.com؛ medium.com 2026-05 |
| 57٪ سازمان‌های دارای production agent، کیفیت را #1 barrier می‌دانند | LangChain State of AI Agents 2026 | H | medium.com 2026-05 |
| پنج biasِ LLM-as-judge: position (10-15pt)، verbosity، self-preference (10-25%)، format، calibration drift | مطالعاتِ مستقل (Zheng et al. 2024 MT-Bench) | H | futureagi.com 2026-05؛ arxiv.org |
| case study kappa 0.31 از bias پنهان | نمونه‌ی vendor (futureagi) | M (vendor-reported) | futureagi.com 2026-05 |
| volume target ≥500 قبل از اعتماد به aggregate metrics؛ ۵۰–۱۰۰ anchor برای regression gate | expert consensus ۲۰۲۶ | H | medium.com 2026-05 |
| Langfuse توسطِ ClickHouse Inc. در ژانویه ۲۰۲۶ خریداری شد؛ MIT license دست نخورده | ClickHouse official | H | clickhouse.com 2026-03 |
| Langfuse self-host: ۵+ service (ClickHouse + Postgres + Redis + S3 + app) | مستنداتِ Langfuse | H | mlflow.org 2026-04 |
| MLflow: Apache 2.0، Linux Foundation، autolog برای ۳۰+ framework، Postgres-only storage، no enterprise paywall | مستنداتِ MLflow | H | mlflow.org 2026-04 |
| OpenLLMetry / Traceloop (Apache 2.0): vendor-neutral OTel instrumentation؛ Langfuse/Phoenix/LangSmith همه spanها را ingest می‌کنند | consensus observability | H | laminar.sh 2026-04 |
| Arize Phoenix OSS: drift detection و advanced analytics در commercial Arize AX tier | مستنداتِ Arize | H | augmentcode.com 2026 |
| LangSmith self-host: فقط Enterprise؛ free tier 5K traces/ماه | مستنداتِ LangSmith | H | mlflow.org 2026-04 |
| Braintrust free tier: 1M spans/ماه، unlimited users، 10K eval runs؛ CI/CD gated | Braintrust documentation | H | latitude.so 2026-03 |
| Laminar (Apache 2.0): agent-first، Helm chart، transcript view، SQL over traces | Laminar docs + comparison | H | laminar.sh 2026-04 |
| OTel GenAI conventions (v1.41+): gen_ai.* attributes با Development badge = ممکن است attribute names تغییر کنند | OTel spec | H | digitalapplied.com 2026-05 |
| Sample rate توصیه‌شده: 5-20٪ production traces + 100٪ errors/outliers | expert consensus | H | futureagi.com 2026-05 |
| Agent-as-a-Judge (Zhuge et al.، ۲۰۲۵): agent برای evaluate کردنِ trajectory agentِ دیگر | arXiv:2508.02994 | M | arxiv.org 2025 |
| «Output looks correct but is semantically wrong» = silent failure؛ only trajectory tracing catches | consensus | H | augmentcode.com 2026 |
| Galileo Luna-2: evaluation در sub-200ms، 97٪ ارزان‌تر از standard LLM-as-judge | Galileo-claimed | M (vendor-reported) | latitude.so 2026-03 |

---

*فایل: `09-research-evaluation-observability.md` — آماده‌ی merge با سایرِ laneها با همین ۸ سرفصلِ ثابت.*
