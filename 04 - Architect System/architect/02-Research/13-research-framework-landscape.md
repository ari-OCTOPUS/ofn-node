# RESEARCH LANE — Framework landscape
# چشم‌اندازِ frameworkهای agentic در ۲۰۲۶ — وضعیتِ جاری، نه تاریخی

> **DOMAIN:** سیستم‌های multi-agent خودمیزبان برای اپراتور تک‌نفره.
> **LANE (قفل‌شده):** فقط frameworkهای agentic، مقایسه‌ی production-grade، و پاسخ به سؤالِ کلیدی: برای stack تو (Claude Cowork) کدام انتخاب بهتر است و کِی اصلاً framework لازم نیست؟
> **CONSTRAINTS:** VPS مشترک + لپ‌تاپ + Claude Cowork؛ تک‌نفره؛ no vendor lock-in؛ export-first.
> **تاریخِ ساخت:** ۲۰۲۶-۰۷-۰۱. منابع از web search زنده. برچسب: `[established] / [emerging] / [speculative]`.

---

## Summary

۱. **حقیقتِ ناخوشایند اول:** framework انتخابِ تو می‌تواند benchmark performance را **۳۰ درصد** روی همان مدل تغییر دهد — نه کیفیتِ مدل، بلکه scaffold. Princeton HAL benchmark: Claude Opus 4 در یک scaffold 64.9٪، در دیگری 57.6٪. `[established]`

۲. **یافته‌ی اصلی برای تو:** اگر stack تو Cowork-centric است، **Claude Agent SDK + SKILL.md** طبیعی‌ترین انتخاب است — بدونِ framework اضافه. اگر workflow پیچیده با conditional branching، rollback، و checkpoint لازم داری، **LangGraph** را به Claude Agent SDK اضافه کن. برای ۷۰٪ taskها، هیچ‌کدام لازم نیست — raw API call کافی است. `[Probable]`

۳. **تغییرِ ساختاریِ ۲۰۲۶:** Microsoft AutoGen به maintenance mode رفت (Q1 2026). AG2 fork community است. Microsoft Agent Framework (v1.0 GA آوریل ۲۰۲۶) جایگزینِ AutoGen + Semantic Kernel شد. Claude Code SDK → Claude Agent SDK تغییرِ نام داد. `[established]`

۴. **همگرایی روی MCP:** همه‌ی frameworkهای اصلی الان MCP دارند. A2A support فقط Google ADK و CrewAI به‌شکلِ native دارند. `[established]`

۵. **هزینه‌ی پنهانِ framework:** خودِ frameworkها همه OSS هستند. هزینه‌ی واقعی: (A) token overhead orchestration — CrewAI 3× بیشتر از LangGraph در simple workflow مصرف می‌کند. (B) LangGraph Platform و CrewAI Enterprise پولی‌اند (cloud-hosted). `[established]`

---

## Landscape

### ۱) سه دسته‌بندیِ اصلی

**[established]** landscape ۲۰۲۶ به سه دسته تقسیم می‌شود:

**(A) Provider-native SDKs (عمیق ولی locked):**
Claude Agent SDK، OpenAI Agents SDK، Google ADK — برای stack خودشان عمیق‌ترین integration را دارند ولی model-locked هستند.

**(B) Framework‌های مستقل (model-agnostic، بیشترین کنترل):**
LangGraph، CrewAI، AG2، Strands، Pydantic AI، Smolagents، LlamaIndex — با هر مدلی کار می‌کنند.

**(C) Enterprise platforms (managed، governed):**
Microsoft Copilot Studio، AWS Bedrock AgentCore، Vertex AI Agent Builder — managed infrastructure. برای تک‌نفره/self-host irrelevant.

---

### ۲) شش frameworkِ اصلیِ production — وضعیتِ دقیق

---

#### LangGraph (MIT، LangChain)

`[established]`

**چیست:** directed graph با conditional edges. نودها = agents/tools/checkpoints. edgeها = transition conditionها. developer کنترلِ صریح روی execution flow، retry، و HITL دارد. نه «LLM بتصمیم بگیرد کجا بروم» — کد تصمیم می‌گیرد.

**چه مشکلی حل می‌کند:** stateful، auditable workflows با branching پیچیده. «LangGraph is the production standard for stateful, auditable agentic workflows.»

**مستنداتِ production:** Klarna (85 میلیون کاربر)، Uber، LinkedIn، BlackRock، JPMorgan. GA v1.0 اکتبر ۲۰۲۵، الان v1.0.x+.

**مزیت‌ها:**
- Built-in checkpointing با time-travel debugging
- کمترین token cost در routing: code-based (if/else) نه LLM-driven → ۳۰–۴۷٪ کمتر از CrewAI روی medium tasks
- 120ms overhead per node (در برابرِ 450ms CrewAI per task transition)
- LangSmith observability: state transitions، replays، annotationsقابلِ search
- Model-agnostic

**ضعف‌ها:**
- Learning curve: graph concepts + state schemas + reducer logic
- LangSmith = بهترین observability ولی pricing در scale می‌تواند تعجب آور باشد
- LangGraph Platform (cloud-hosted) پولی است
- API churn — مستنداتِ متضاد از نسخه‌های مختلف

**لایسنس:** MIT (OSS)؛ LangGraph Platform = SaaS پولی. `verify` pricing

---

#### Claude Agent SDK (proprietary license، Anthropic)

`[established]`

**چیست:** همان infrastructure که Claude Code را اجرا می‌کند، به‌شکلِ library expose شده. September 2025 تغییرِ نام از Claude Code SDK. Python (`claude-agent-sdk-python`) + TypeScript (`@anthropic-ai/claude-agent-sdk`). از مه ۲۰۲۵ در دسترس؛ April 2026 با Claude 4.6 رسماً announce شد.

**چه مشکلی حل می‌کند:** agent loop با tool use، subagents، sessions، MCP، SKILL.md، و hooks در ecosystem Claude.

**built-in tools:** file editing، bash execution، web search/fetch، grep. **هیچ framework دیگری این را out-of-the-box ندارد.**

**ویژگی‌های کلیدی:**
- **Subagents:** Agent tool برای spawn کردنِ child agentهای ایزوله با context خودشان
- **Skills (SKILL.md):** progressive disclosure — metadata همیشه در context، instructions on-demand
- **Hooks:** pre/post operations (مثلاً lint بعد از هر code edit)
- **Sessions:** persistent execution state
- **MCP:** deepest integration در بینِ همه‌ی frameworkها
- June 15, 2026: metering جداگانه از interactive Claude Code (کمک به cost tracking)

**ضعف‌های مهم:**
- **Claude models only** — هیچ model flexibility ندارد
- **Not embeddable like a library:** نمی‌توانی explicit state machine یا conditional edge تعریف کنی مثلِ LangGraph. «You describe what you want in natural language. You cannot define explicit state machines, conditional edges, or custom routing logic.»
- **لایسنس proprietary:** نه MIT، نه Apache. `verify` terms قبل از commit به production
- State persistence فقط via MCP servers یا در context — نه built-in checkpoint با time-travel

**لایسنس:** proprietary (Anthropic Commercial Terms of Service). این مهم‌ترین تفاوت با بقیه است.

---

#### CrewAI (MIT)

`[established]`

**چیست:** role-based crews — هر agent یک نقش (researcher، writer، reviewer)، goal، و backstory دارد. سریع‌ترین path برای prototype.

**چه مشکلی حل می‌کند:** content pipelines، research-to-write-to-review workflows، هر task که به «تیمِ متخصص» تقسیم می‌شود.

**مستنداتِ production:** 52٬000+ GitHub stars، v1.14 با A2A + MCP support، 1500+ شرکت بر اساسِ خودِ CrewAI.

**مزیت‌ها:**
- ۲۰–۵۰ خط کد به یک working multi-agent prototype
- Fastest path (2–4 ساعت)
- A2A support native (بینِ frameworkها نادر است)
- بزرگ‌ترین community در class

**ضعف‌ها:**
- 3× token overhead نسبت به LangGraph در simple workflows (LLM-driven delegation)
- 450ms per task transition overhead
- وقتی workflow به branching پیچیده نیاز دارد، role abstraction constraining می‌شود
- CrewAI Enterprise = paid (cloud hosting، observability dashboard)

**لایسنس:** MIT.

---

#### OpenAI Agents SDK (MIT)

`[established]`

**چیست:** چهار primitive: Agent + Handoffs + Guardrails + Tools. عمداً minimal. یک agent به دیگری handoff می‌کند.

**چه مشکلی حل می‌کند:** OpenAI-centric stacks با handoff pattern ساده.

**مستنداتِ production:** v0.10.2، March 2026 GA به‌عنوانِ successor Swarm. 19K stars، 10.3M monthly downloads. الان 100+ LLM از طریقِ Chat Completions API support می‌کند (نه فقط OpenAI).

**مزیت‌ها:** simple، clean، fast to ship، built-in tracing.

**ضعف‌ها:**
- هنوز primary optimization برای OpenAI
- هیچ built-in checkpointing برای long-running workflows
- Coarse-grained error handling

**لایسنس:** MIT.

---

#### Microsoft Agent Framework (MIT)

`[established]`

**چیست:** ادغامِ AutoGen + Semantic Kernel در یک SDK. Python + .NET. GA v1.0 آوریل ۲۰۲۶.

**چه مشکلی حل می‌کند:** Azure/Microsoft stacks، enterprise .NET.

**AutoGen:** maintenance mode رفت Q1 2026. **AG2** = community fork که conversation-pattern را ادامه می‌دهد.

**برای تو:** irrelevant مگر Azure dependency داشته باشی.

---

#### Google ADK (Apache 2.0)

`[established]`

**چیست:** hierarchical agent tree، native A2A support، multimodal first-class. GA v2.0 مه ۲۰۲۶. Java + Go SDK هم.

**مزیت:** native A2A = cross-vendor agent interop. تنها framework که واقعاً A2A را به‌شکلِ first-class دارد.

**ضعف:** Gemini-native (سایر مدل‌ها پشتیبانی ولی نه به‌عمق). GCP-native deployment.

**لایسنس:** Apache 2.0.

---

### ۳) Frameworkهای خاص‌منظور

**Strands Agents (MIT، AWS):** «Model-driven — give model tools, give it a goal, get out of the way.» سبک‌ترین abstraction. Model-agnostic (LiteLLM). OTel → AWS X-Ray. برای AWS-native. بهترین وقتی inference trust to the model داری.

**Pydantic AI (MIT، Pydantic team):** type-safe، FastAPI-style DX. هر input/output/tool typed و validated. بهترین برای compliance-sensitive (financial، healthcare). نه orchestration framework — یک layer داخلِ پایپلاین. Logfire برای observability.

**Smolagents (Apache 2.0، Hugging Face):** code-first، agent Python می‌نویسد و execute می‌کند. Minimal، no ceremony. بهترین برای quick prototype یا code-execution agents.

**LlamaIndex Agents:** RAG-grounded agents. وقتی retrieval مشکلِ اصلی است.

---

### ۴) سؤالِ کلیدی: کِی اصلاً framework لازم نیست؟

`[established]`

«For simple single-agent function calling workflows with one or two tools, skip the framework entirely. Raw API calls with structured outputs will serve you better.»

**Raw API (بدون framework) کافی است وقتی:**
- یک agent با ≤۲ tool call
- sequential task که branching ندارد
- هیچ sub-agent ندارد
- هیچ checkpoint/resume لازم نیست

**هزینه‌ی framework = واقعی است:**
- هر framework abstraction layer اضافه می‌کند
- CrewAI 3× token overhead روی simple tasks
- LangGraph بدونِ LangSmith observability story خودش را از دست می‌دهد
- Framework lock-in با گذشتِ زمان سخت‌تر می‌شود

---

### ۵) مقایسه‌ی Claude Agent SDK در برابرِ LangGraph برای stack تو

`[Probable]`

| بُعد | Claude Agent SDK | LangGraph |
|---|---|---|
| Model dependency | Claude only | Model-agnostic |
| Orchestration | Tool-use chain + subagents | Directed graph با conditional edges |
| State persistence | Via MCP servers / context | Built-in checkpoint + time-travel |
| SKILL.md integration | Native (progressive disclosure) | Via tools/adapters |
| MCP integration | Deepest در بینِ همه | Via adapters |
| Conditional branching | LLM decides | Code-level if/else |
| Token cost routing | متوسط | کمتر (code-based) |
| Learning curve | Medium (tool patterns، MCP) | Medium-High (graph، state schema) |
| License | Proprietary | MIT |
| Lock-in | High (Claude only) | Medium (LangSmith dependency) |
| Cowork compatibility | ✅ Native | ⚠️ باید wire شود |

**پاسخِ مستقیم به سؤالِ کلیدی:**

**برای Cowork-centric stack:** Claude Agent SDK + SKILL.md بهترین default است. هم native است، هم SKILL.md skill library را پشتیبانی می‌کند، هم MCP deep integration دارد. **ولی:** proprietary license = اگر بخواهی migrate کنی یا production-scale بشوی، هزینه دارد.

**چه زمانی LangGraph اضافه کنی:**
- Workflow شامل conditional branching پیچیده است که Claude بدونِ explicit graph گیج می‌شود
- نیازِ به checkpoint + resume داری (برای long-running tasks که ساعت‌ها طول می‌کشند)
- نیازِ به time-travel debugging داری
- می‌خواهی از Claude به مدلِ دیگری migrate کنی (LangGraph model-agnostic است)

**چه زمانی raw code (بدون هیچ framework):**
- هر tenant با ≤۵ step و ≤۲ concurrent agent
- هیچ handoff pattern پیچیده ندارید
- می‌خواهید محدودترین surface area را داشته باشید

---

## Comparison table

> نمره‌ی ۱–۱۰: بهترین برای تک‌نفره روی VPS مشترک با Claude Cowork. `[Probable]`

| Framework | Model-agnostic | MCP | A2A | State/Checkpoint | Token Efficiency | Lock-in (۱=کم) | Maturity |
|---|---|---|---|---|---|---|---|
| **LangGraph (MIT)** | ✅ 10 | 7 | ❌ 1 | 10 | 9 | 4 | 9 |
| **Claude Agent SDK (proprietary)** | ❌ 1 | 10 | ❌ 2 | 5 | 7 | 8 | 7 |
| **CrewAI (MIT)** | ✅ 9 | 8 | ✅ 8 | 5 | 4 | 2 | 8 |
| **OpenAI Agents SDK (MIT)** | 7 | 6 | ❌ 2 | 3 | 7 | 5 | 7 |
| **Strands (MIT، AWS)** | ✅ 9 | 7 | ❌ 2 | 5 | 8 | 3 | 6 |
| **Pydantic AI (MIT)** | ✅ 9 | 6 | ❌ 2 | 4 | 8 | 2 | 7 |
| **Smolagents (Apache 2.0)** | ✅ 10 | 6 | ❌ 2 | 3 | 7 | 1 | 6 |
| **Microsoft Agent Framework (MIT)** | 6 | 5 | ❌ 2 | 5 | 6 | 6 | 7 |
| **Google ADK (Apache 2.0)** | 7 | 7 | ✅ 9 | 7 | 7 | 5 | 7 |
| **Raw API (no framework)** | ✅ 10 | manual | manual | manual | 10 | 1 | N/A |
| **AG2 (Apache 2.0)** | ✅ 9 | 6 | ❌ 2 | 4 | 6 | 1 | 6 |

---

## Blind spots

- **لایسنسِ proprietary Claude Agent SDK.** `[established]` همه‌ی مقایسه‌ها این را «MIT یا Apache» می‌گویند ولی این اشتباه است. «Anthropic Agent SDK was published with a proprietary license.» (Promptfoo docs). قبل از commit به production، Anthropic Commercial Terms of Service را بخوان. این با ارزشِ export-first تو conflict دارد. `[certain، verify terms]`

- **Token overhead CrewAI پنهان است.** `[established]` وقتی CrewAI برای delegation از LLM call استفاده می‌کند نه code، این $4.10 هزینه‌ی اضافه روی ۱۰۰ loop research workflow تولید می‌کند در برابرِ نزدیکِ صفر برای LangGraph. در low-volume این مهم نیست؛ در scale خیلی مهم می‌شود.

- **«Claude Agent SDK = Claude Code» اشتباه‌تر از آن است که به نظر می‌رسد.** `[established]` Claude Code برای interactive development است. Claude Agent SDK برای programmatic workflows. ولی «you cannot embed Claude Code's agent logic into your own Python or Node application the way you can with CrewAI or LangGraph.» اگر می‌خواهی agent را embed کنی، Claude Agent SDK دقیقاً همین کار را نمی‌کند.

- **LangGraph Platform در scale گران می‌شود.** `[established]` OSS LangGraph رایگان است. LangGraph Platform (cloud-hosted، managed execution) می‌تواند در scale تعجب‌آور باشد. برای VPS self-host، LangGraph OSS + self-managed observability (MLflow/Langfuse) راهِ آزادتر است.

- **AutoGen → AG2 مهاجرت واقعی است.** `[established]` اگر کدِ قدیمی روی AutoGen داری، به AG2 (community fork، Apache 2.0) یا Microsoft Agent Framework (MIT) ببری. AutoGen maintenance mode = ممکن است ببهبودهای جدید نداشته باشد.

- **Framework choice ≠ capability.** `[established]` «Framework choice moves benchmark performance by up to 30 points on identical models.» این به معنایِ «framework هوشمندتر می‌کند» نیست — به معنای «scaffold می‌تواند مانعِ model باشد.» یک scaffold بد = ۳۰ امتیاز کمتر روی GAIA.

- **همگرایی ≠ یکسانی.** `[Probable]` همه‌ی frameworkها MCP دارند، همه ReAct pattern را implement می‌کنند. ولی تفاوتِ واقعی در state management، token efficiency، و observability story است — نه feature list.

- **SKILL.md open standard شد دسامبر ۲۰۲۵.** `[established]` Anthropic آن را به‌عنوانِ open standard منتشر کرد. این یعنی بعضی frameworkهای دیگر هم می‌توانند SKILL.md را consume کنند — lock-in کمتری از آنچه به نظر می‌رسد.

- **Cowork + Claude Agent SDK metering جداگانه از ژوئن ۲۰۲۶.** `[established]` «From June 15, 2026, Claude Agent SDK and Claude Code GitHub Actions usage is metered separately from interactive Claude Code.» cost tracking بهتر می‌شود ولی باید این را در بودجه‌بندی حساب کنی. `verify` با Anthropic pricing page.

---

## Recommendation

**پیشنهادِ اصلی برای stack تو (Claude Cowork-centric، VPS مشترک، تک‌نفره):**

### سه‌مرحله‌ای:

**مرحله‌ی ۱ (الان — بدونِ هیچ framework جدید):**
از همانِ Cowork + MCP gateway که داری استفاده کن. برای هر task، ابتدا ببین آیا raw API call ساده کافی است. اگر task با ≤۵ step و ≤۲ concurrent sub-task حل می‌شود، هیچ framework اضافه نکن.

**مرحله‌ی ۲ (وقتی subagent یا skill management لازم شد):**
Claude Agent SDK (subagents + SKILL.md + hooks + MCP). این native-ترین است برای Claude. ولی: لایسنس proprietary را بخوان قبل از commit.

**مرحله‌ی ۳ (وقتی conditional branching یا دurable checkpoint لازم شد):**
LangGraph (MIT) را به pipeline اضافه کن. نه به‌جای Claude Agent SDK، بلکه در کنارش یا به‌جای raw code. LangGraph model-agnostic است = migration option بعداً.

**سؤالِ کلیدی برای هر task:**

```
آیا task واقعاً multi-agent است؟
→ نه: raw API call
→ بله: آیا workflow conditional branching / checkpoint دارد؟
   → نه: Claude Agent SDK (skill + subagent)
   → بله: LangGraph
```

### دقیقاً چه چیزی را **نساز:**

- ❌ **CrewAI روی VPS مشترک با budget محدود** — 3× token overhead روی simple tasks قابلِ توجیه نیست مگر task واقعاً role-based باشد
- ❌ **Microsoft Agent Framework** — برای Azure-native. Stack تو Anthropic-centric است.
- ❌ **هر framework قبل از نیازِ واقعی** — «Jumping to Agent Teams before validating with subagents.» ابتدا با raw + subagent، بعد framework
- ❌ **Google ADK** مگر A2A cross-framework ضروری شود — GCP-native، overhead بدونِ GCP.
- ❌ **Smolagents برای production decision-making** — مناسبِ prototyping و research، نه production financial.

---

## TOOLING (pricing + alternative + lock-in)

| Framework | License | Pricing (cloud/enterprise) | Best alternative | Lock-in (۱=کم) |
|---|---|---|---|---|
| **LangGraph** | MIT | OSS رایگان؛ LangGraph Platform (verify) | Strands / raw code | **3** |
| **Claude Agent SDK** | Proprietary | Anthropic API billing؛ June 2026 separate metering | LangGraph + Anthropic API | **8** |
| **CrewAI** | MIT | OSS رایگان؛ CrewAI Enterprise (verify) | LangGraph | **3** |
| **OpenAI Agents SDK** | MIT | OSS رایگان؛ OpenAI API billing | LangGraph | **5** |
| **Strands Agents** | MIT | OSS رایگان؛ Bedrock AgentCore billing | LangGraph | **3** (higher اگر Bedrock) |
| **Pydantic AI** | MIT | OSS رایگان؛ Logfire (observability) | LangGraph + Pydantic | **2** |
| **Smolagents** | Apache 2.0 | OSS رایگان | raw code | **1** |
| **Microsoft Agent Framework** | MIT | OSS رایگان؛ Azure billing | LangGraph | **5** |
| **Google ADK** | Apache 2.0 | OSS رایگان؛ Vertex AI billing | LangGraph | **4** (higher اگر Vertex) |
| **AG2** | Apache 2.0 | OSS رایگان | LangGraph | **2** |
| **LlamaIndex** | MIT | OSS رایگان؛ LlamaCloud (optional) | LangGraph | **2** |

---

## If-I'm-wrong

**قوی‌ترین ضدِ توصیه («Claude Agent SDK با proprietary license مشکل ندارد»):** اگر Anthropic terms برای use-caseِ تو اجازه می‌دهد (که احتمالاً برای استفاده‌ی شخصی اجازه می‌دهد)، این یک concern مهم نیست. ولی اگر به SaaS تبدیل کنی یا code را distribute کنی، proprietary license یک blocking issue است. موضعِ من: export-first = prefer MIT/Apache.

**ضدِ توصیه‌ی دوم («LangGraph برای multi-project orchestration خیلی پیچیده است»):** واقعی است. Learning curve یک هفته جدی است. یک تک‌نفره که هفته‌ها وقت ندارد ممکن است هرگز به عمقِ LangGraph نرسد. اگر نیازِ به time-travel debugging و durable checkpoint ندارد، CrewAI (با caveats token overhead) یا raw subagent ساده‌تر است.

**ضدِ توصیه‌ی سوم («Raw code اول»):** درست است برای single-agent ساده. ولی اگر بدانی که multi-agent ضروری خواهد بود، از ابتدا LangGraph building blocks استفاده کردن ارزان‌تر از بازنویسی است. Decision: اگر نیازِ واقعی الان نیست → raw code؛ اگر مطمئنی که ۳ ماه دیگر چند agent داری → LangGraph از ابتدا.

---

## Confidence

**High** برای وضعیتِ فعلیِ frameworkها (GA dates، license، token efficiency benchmarks از منابعِ مستقل). **Medium** برای توصیه‌ی Claude Agent SDK vs LangGraph (وابسته به جزئیاتِ Cowork که `uncertain` هستند). **Low/uncertain** برای LangGraph Platform pricing در scale و Claude Agent SDK license implications — `verify` با مستنداتِ رسمی. ⚠️ Framework versions سریع‌تر از هر lane دیگری تغییر می‌کنند — verify با latest releases قبل از commit.

---

## Claims table

| claim | evidence | confidence (H/M/L) | source + date |
|---|---|---|---|
| Framework choice: 30 امتیاز تفاوتِ benchmark روی همان مدل | Princeton HAL benchmark: Claude Opus 4 → 64.9٪ vs 57.6٪ | H | uvik.net 2026-06 |
| LangGraph: production standard stateful workflows؛ Klarna 85M users | enterprise deployments | H | requesty.ai 2026-06 |
| LangGraph v1.0 GA اکتبر ۲۰۲۵؛ token cost 30-47٪ کمتر از CrewAI روی medium tasks | benchmark از AI Dev Day India | H | requesty.ai 2026-06 |
| LangGraph 120ms overhead per node؛ CrewAI 450ms per task transition | benchmark | H | requesty.ai 2026-06 |
| Claude Agent SDK: renamed از Claude Code SDK September 2025؛ subagents، SKILL.md، hooks، MCP | official docs | H | code.claude.com؛ totalum.app 2026 |
| Claude Agent SDK: proprietary license (نه MIT/Apache) | Promptfoo docs | H | promptfoo.dev |
| Claude Agent SDK: Claude models only؛ نمی‌تواند explicit state machine تعریف کند | comparative review | H | qubittool.com 2026-05؛ developersdigest.tech |
| Claude Agent SDK June 15, 2026: separate metering از interactive Claude Code | vendor announcement | H | totalum.app 2026 |
| SKILL.md open standard: دسامبر ۲۰۲۵ publish | Anthropic engineering blog | H | anthropic.com |
| Agent Skills proprietary: خارج از ZDR؛ data retention standard | platform docs | H | platform.claude.com |
| CrewAI 52K stars، v1.14، native A2A + MCP، 1500+ company | vendor stats | H | letsdatascience.com 2026-03 |
| CrewAI 3× token overhead نسبت به LangGraph در simple workflows (LLM-driven routing) | benchmark | H | requesty.ai 2026-06 |
| OpenAI Agents SDK v0.10.2 March 2026؛ 19K stars؛ 100+ LLMs support | framework docs | H | letsdatascience.com 2026-03 |
| Microsoft AutoGen → maintenance mode Q1 2026؛ AG2 = community fork | official announcement | H | uvik.net 2026-06؛ uvik.net python 2026 |
| Microsoft Agent Framework v1.0 GA April 3, 2026 (AutoGen + Semantic Kernel merger) | official | H | rasa.com 2026-05 (lane 0) |
| Google ADK v2.0 GA مه ۲۰۲۶؛ native A2A؛ Java + Go SDK | official | H | requesty.ai 2026-06 |
| Strands Agents: MIT، AWS، model-agnostic via LiteLLM، OTel → X-Ray | framework docs | H | builder.aws.com 2026-03 |
| Pydantic AI: MIT، type-safe، 16K+ stars، FastAPI DX | framework docs | H | langfuse.com comparison |
| Smolagents: Apache 2.0، Hugging Face، code-first Python execution | framework docs | H | langfuse.com comparison |
| همه‌ی ۱۲ framework OSS (MIT یا Apache 2.0)؛ هزینه‌ی واقعی = API spend | framework docs | H | uvik.net python 2026 |
| برای single-agent ≤۲ tool، raw API call بهتر از framework است | practitioner consensus | H | letsdatascience.com 2026-03 |

---

*فایل: `13-research-framework-landscape.md` — آماده‌ی merge با سایرِ laneها با همین ۸ سرفصلِ ثابت.*
