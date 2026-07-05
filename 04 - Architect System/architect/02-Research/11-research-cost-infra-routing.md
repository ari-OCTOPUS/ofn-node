# RESEARCH LANE — Cost / infra / model routing
# هزینه، زیرساخت، و model routing برای multi-agent روی VPS محدودِ مشترک

> **DOMAIN:** سیستم‌های multi-agent خودمیزبان برای اپراتور تک‌نفره.
> **LANE (قفل‌شده):** فقط هزینه‌ی model inference، routing strategy، caching، prompt optimization، و تصمیمِ self-host در برابرِ API — نه governance، نه evaluation.
> **CONSTRAINTS:** VPS مشترک + لپ‌تاپ + Claude Cowork؛ بودجه‌ی محدود؛ منابعِ مشترکِ بینِ چند پروژه.
> **تاریخِ ساخت:** ۲۰۲۶-۰۷-۰۱. قیمت‌ها از منابعِ ژوئن ۲۰۲۶ تأییدشده‌اند. **⚠️ قیمت‌ها monthly تغییر می‌کنند — قبل از تصمیم، صفحه‌ی provider را verify کن.** برچسب: `[established] / [emerging] / [speculative]`.

---

## Summary

۱. **حقیقتِ ناخوشایند اول:** در multi-agent، هزینه به‌شدت غیرخطی است. یک chatbot تک‌turn: ۲٬۰۰۰–۴٬۰۰۰ توکن. یک task agentی با tool callها و planning: **۵۰٬۰۰۰ تا ۵۰۰٬۰۰۰ توکن.** ضرب‌درِ ۱۰۰ task روزانه = $۴۰–$۴۰۰ روزانه فقط از inference اگر همه‌چیز روی Sonnet برود. `[established]`

۲. **قانونِ ۸۰/۲۰ هزینه:** ۸۰٪ هزینه از ۲۰٪ taskها می‌آید. این ۲۰٪ معمولاً long reasoning chain، context injection بزرگ، یا retry از خطاست. پیدا کردنِ همین ۲۰٪ و optimize کردنشان بیشتر از هر استراتژیِ دیگری اثر دارد. `[established]`

۳. **دو lever با بالاترین ROI:** (A) **Prompt caching**: تا ۹۰٪ تخفیف روی cached input در Anthropic — اگر system prompt بزرگی داری، کشینگ همین امروز پولِ قابلِ توجهی صرفه می‌کند. (B) **Model routing**: مسیر دادنِ ۷۰٪ taskها به مدلِ ارزان می‌تواند bill را ۴۰–۸۶٪ کاهش بدهد. `[established]`

۴. **خط تصمیمِ self-host:** کمتر از ۵۰M توکن/ماه → API ارزان‌تر است، self-host نکن. ۵۰M–۵۰۰M توکن/ماه → cost-neutral با hardware مناسب. برای VPS اجاره‌ای بدونِ GPU، Ollama روی CPU فقط برای taskهای async و batch معقول است (۵–۱۰ tok/s برای 7B). `[established]`

۵. **⚠️ خبرِ مهم ژوئن ۲۰۲۶:** Claude Fable 5 و Mythos 5 از ۱۲ ژوئن ۲۰۲۶ به‌دلیلِ US export-control directive suspend شدند. Claude Opus 4.8، Sonnet 4.6، و Haiku 4.5 تأثیر نگرفتند. `[established، uncertain]` دسترسی برای کاربرانِ US حدودِ ۱ ژوئیه بازمی‌گردد — verify با Anthropic.

---

## Landscape

**۱) قیمتِ فعلیِ API — تأییدشده‌ی ژوئن ۲۰۲۶.** `[established]`

> ⚠️ قیمت‌ها quarterly تغییر می‌کنند. پیشِ از commit به volume contract، از صفحه‌ی رسمیِ provider verify کن.

| مدل | Input ($/1M) | Output ($/1M) | Context | یادداشت |
|---|---|---|---|---|
| **Claude Opus 4.8** | $5 | $25 | 1M | SWE-bench 88.6٪؛ بهترینِ موجودِ Anthropic |
| **Claude Sonnet 4.6** | $3 | $15 | 1M | کدِ عالی، اکثرِ production tasks |
| **Claude Haiku 3.5** | $0.80 | $4 | 200K | بهترین کیفیتِ budget tier Anthropic |
| **DeepSeek V4 Flash** | $0.14 | $0.28 | — | ارزان‌ترین «GPT-4 class»؛ latency/availability نامنظم |
| **Gemini 3.1 Pro** | $2 | $12 | 2M | ارزان‌ترین frontier-hosted API؛ بزرگ‌ترین context window |
| **Gemini 2.5/2.0 Flash** | $0.10–0.15 | $0.40–0.60 | 1M | cost leader برای taskهای ساده |
| **GPT-5.5** | ~$5 | ~$30 | — | `uncertain` — verify با OpenAI |
| **GPT-4.1 Mini** | $0.40 | $1.60 | 1M | budget tier OpenAI |
| **GPT-4.1 Nano** | $0.10 | $0.40 | 1M | ارزان‌ترین GPT-4 class API |
| **MiniMax M3** | $0.60 | $2.40 | — | SWE-bench 80.5٪، ارزان‌ترین بالای ۸۰٪ |

**Batch API / Prompt caching:**
- **Anthropic prompt caching:** ۹۰٪ تخفیف روی cached input (read: $0.30/1M به‌جای $3 روی Sonnet)
- **OpenAI Batch API:** ۵۰٪ تخفیف برای non-realtime
- **اگر هر دو استک شوند:** effective cost می‌تواند به ۲۵٪ standard rate برسد

**نکته‌ی مهمِ tokenizer:** مدل‌های از Opus 4.7 به بعد از یک tokenizer جدید استفاده می‌کنند که ممکن است تا ۳۵٪ توکنِ بیشتر برای همان text تولید کند — cross-provider comparison را inflate می‌کند.

---

**۲) مدلِ هزینه‌ی multi-agent.** `[established]`

**چرا multi-agent اینقدر گران است:**

یک multi-agent run به‌جای یک LLM call، ۲۰–۵۰ LLM call می‌زند. هر sub-agent:
- system promptِ کامل را در context دارد (تکرار per-call)
- tool definitionها (تکرار per-call؛ تا lane 4 دیدیم این ۷۲٪ context را می‌خورد)
- history مکالمه را accumulate می‌کند

**مدلِ ساده‌ی تخمینِ هزینه:**

```
cost_per_run ≈ N_agents × avg_turns × avg_tokens_per_turn × avg_token_price

برای یک task با:
- ۳ sub-agent
- ۵ turn هر agent
- ۱٬۰۰۰ توکنِ input + ۵۰۰ توکنِ output per turn
- روی Claude Sonnet 4.6 ($3 input / $15 output)

cost = 3 × 5 × (1000×$3 + 500×$15) / 1,000,000
     = 3 × 5 × ($0.003 + $0.0075)
     = 3 × 5 × $0.0105
     ≈ $0.16 per run

100 run/روز × $0.16 = $16/روز = ~$480/ماه

اگر Opus 4.8 به‌جای Sonnet:
100 task × $0.16 × (25/15) × (5/3) ≈ $444 ماهانه ولی با routing 70/20/10:
0.7×Haiku + 0.2×Sonnet + 0.1×Opus:
effective_price ≈ 0.7×$4 + 0.2×$15 + 0.1×$25 = $8.3/1M output
→ savings ~45% vs all-Sonnet
```

**parallel overhead:** چون multi-agent parallel context است، ~۱۵× توکنِ بیشتر از sequential نمایندگیِ خام مصرف می‌شود.

---

**۳) سه استراتژیِ کاهشِ هزینه با بالاترین ROI.** `[established]`

**(A) Prompt caching — بالاترین ROI، فوری:**

Anthropic's cached input: ۹۰٪ تخفیف. اگر system prompt تو ۲٬۰۰۰ توکن است و هر task آن را دوباره می‌فرستد:
- بدونِ caching: 2000 توکن × $3 = $0.006 per request
- با caching: 2000 توکن × $0.30 = $0.0006 per request → ۱۰× ارزان‌تر

**چطور:** همه‌ی tool definitionها، RAG context ثابت، و policy text را به ابتدای prompt بده و cache_control={"type": "ephemeral"} را set کن.

**ولی:** caching بد می‌تواند latency را بدتر کند. cache blocks را تست کن.

**(B) Model routing — دومین ROI:**

یک routing layer ساده بین agentها:

```python
def route_model(task_description: str, estimated_complexity: str) -> str:
    if estimated_complexity == "simple":  # classification، extraction، formatting
        return "claude-haiku-4-5-20251001"
    elif estimated_complexity == "medium":  # analysis، code، reasoning
        return "claude-sonnet-4-6"
    else:  # complex multi-step، security-critical
        return "claude-opus-4-8"

# تخمینِ complexity:
# ساده: task با ≤3 step و بدونِ tool call پیچیده
# متوسط: task با tool call اما ≤10 step
# پیچیده: task با reasoning chain عمیق، financial decision، security-critical
```

**نتیجه‌ی مستند:** routing 70٪ به cheap + 20٪ mid + 10٪ frontier → ۴۰–۸۶٪ کاهشِ هزینه.

**(C) Context trimming — سومین ROI:**

- system prompt را کوتاه و versioned نگه دار
- tool outputs را قبل از pass شدن summarize کن
- conversation history قدیمی را drop کن (sliding window)
- از structured output استفاده کن تا model توکن صرفِ formatting نکند
- RAG: snippet به‌جای document کامل

**محاسبه‌ی تأثیر:** «A 100K token input to Claude Sonnet costs $0.30 per request.» تقلیل ۵۰٪ context = $0.15 صرفه‌جویی per request.

---

**۴) VPS infra و resource contention.** `[established]`

**مشکلِ multi-tenant روی یک VPS:**
وقتی tenant تحقیق یک reasoning task سنگین می‌کند و tenant ماینینگ هم‌زمان CPU می‌خواهد، contention می‌کنند. راه‌حل‌ها:

**cgroups v2 / systemd slices** (رایگان، توی لینوکس):
```bash
# per-tenant resource slice
systemctl set-property agent-research.service CPUQuota=25%
systemctl set-property agent-mining.service CPUQuota=20%
systemctl set-property agent-accounting.service CPUQuota=15%
# باقی‌مانده برای OS و سیستم
```

**job queue** (برای async tasks):
- تمامِ taskهای non-realtime را از طریقِ یک queue (Redis/Postgres LISTEN-NOTIFY) ارسال کن
- worker تک‌نفره task را پردازش می‌کند
- rate limit: حداکثر N request/دقیقه به API
- هیچ parallel spike از tenantها

**API rate limit awareness:**
- Anthropic tier 1: کافی برای prototype/solo
- اگر taskها burst داری، exponential backoff + jitter اضافه کن
- Batch API برای taskهایی که ۲۴ ساعت delay تحمل می‌کنند (batch research، weekly reports)

---

**۵) Self-host تصمیم: API در برابرِ Ollama / vLLM.** `[established]`

**نتیجه‌ی اصلی:** کمتر از ۵۰M توکن/ماه → API ارزان‌تر است.

**جدولِ break-even:**

| سناریو | شرطِ break-even | یادداشت |
|---|---|---|
| Ollama CPU-only (7B) روی VPS اجاره‌ای (€50/ماه) | ~۶M توکن/ماه vs Sonnet | فقط اگر task async + batch باشد (5-10 tok/s) |
| self-hosted vLLM vs DeepSeek V4 Flash ($0.14/M) | ~۸۰۰M توکن/ماه | تقریباً هرگز برای solo-operator |
| self-hosted vLLM با GPU ($30K H100) vs Sonnet ($9/M avg) | ~۳۵M توکن/ماه | مناسب برای ≥۳۵M/ماه |
| Ollama Cloud Pro (~$20/ماه) | همیشه ارزان‌تر از GPU hardware تا ~۵۰M توکن/ماه | ولی data بیرون از VPS |

**هزینه‌ی پنهانِ self-hosting:**
- «Raw GPU costs represent only 30-40% of true infrastructure investment»
- Engineering labor: 1.5-2 FTE برای ops = $270K-$550K/سال
- Ollama memory leaks و OOM crashes → real engineering hours
- Ollama Cloud در آوریل ۲۰۲۶ یک ۹۵٪ failure window داشت

**تنها سناریوی معقولِ self-host برای تو:**
اگر laptop یا mining rig با GPU موجود است (free electricity)، Ollama روی لپ‌تاپ برای taskهای non-critical معقول است. ولی production decision-making را به API (Claude) بسپار.

**Ollama روی CPU VPS برای async tasks:**
- 7B model (Qwen3.5-7B، Phi-4): ۵–۱۵ tok/s روی shared VPS
- ۳B model: ۱۵–۲۵ tok/s
- مناسب: classification، extraction، summarization، batch research
- نامناسب: complex reasoning، realtime response، anything >10B

---

**۶) مدلِ routing برای stack تک‌نفره‌ی تو.** `[Probable]`

```
Request → Task Router
         ├── Simple (classification/extraction/formatting) → Haiku 3.5 ($0.80/$4)
         │   مثال: دسته‌بندیِ email، خلاصه‌ی document کوتاه
         ├── Medium (analysis/code/RAG) → Sonnet 4.6 ($3/$15)
         │   مثال: اکثرِ agent steps، tool use، code generation
         ├── Complex (multi-step reasoning/security-critical) → Opus 4.8 ($5/$25)
         │   مثال: final decision در ماینینگ، architecture design
         └── Background/Batch (async, 24h tolerance) → DeepSeek V4 Flash یا Gemini Flash ($0.10-0.14)
             مثال: weekly reports، research crawling، log analysis
```

**پیاده‌سازیِ ساده‌ی classifier:**
```python
def classify_task(task: str) -> str:
    # سریع‌ترین classifier: keyword + rule-based (latency <1ms)
    simple_keywords = ["summarize", "classify", "extract", "format", "convert"]
    complex_keywords = ["decide", "analyze trade", "compare alternatives", "design"]
    
    if any(k in task.lower() for k in simple_keywords) and len(task) < 500:
        return "haiku"
    elif any(k in task.lower() for k in complex_keywords):
        return "opus"
    else:
        return "sonnet"  # default
```

---

## Comparison table

> نمره‌ی ۱–۱۰: بهترین برای تک‌نفره/VPS مشترک/بودجه‌ی محدود. `[Probable]` جز جایی که pricing data داریم.

| Option | Cost | Quality | Latency | Self-host | Lock-in |
|---|---|---|---|---|---|
| **Claude Haiku 3.5 ($0.80/$4)** | 9 | 7 | 8 | N/A | 4 |
| **Claude Sonnet 4.6 ($3/$15)** | 7 | 9 | 8 | N/A | 4 |
| **Claude Opus 4.8 ($5/$25)** | 5 | 10 | 7 | N/A | 4 |
| **DeepSeek V4 Flash ($0.14/$0.28)** | 10 | 7 | 5* | N/A | 3 |
| **Gemini 2.5 Flash ($0.10/$0.40)** | 10 | 7 | 8 | N/A | 4 |
| **Gemini 3.1 Pro ($2/$12)** | 7 | 9 | 7 | N/A | 4 |
| **Ollama 7B (CPU VPS، async)** | 9† | 5 | 3 | 10 | 1 |
| **Ollama 7B (GPU laptop، local)** | 9† | 6 | 7 | 10 | 1 |
| **vLLM + GPU dedicated** | 8† | 8 | 9 | 9 | 1 |
| **Anthropic Batch API (50% off)** | 8 | 9 | 1‡ | N/A | 4 |

\* DeepSeek: latency/availability inconsistent
† هزینه‌ی نقدی کم، ولی هزینه‌ی ops و setup بالا
‡ Batch: نتیجه در ساعت‌ها، نه ثانیه‌ها

---

## Blind spots

- **Multi-agent context repeat = hidden cost.** `[established]` هر sub-agent در هر turn کلِ system prompt + tool definitions را می‌فرستد. بدونِ progressive disclosure و caching، این ۵–۱۰× inflate می‌کند. Tool Search و deferred loading (لِینِ ۴) مستقیماً به این کمک می‌کند.

- **DeepSeek reliability.** `[established]` «Rate limits and availability have been inconsistent. Factor reliability into your cost calculations — the cheapest API is not cheap if it is down when you need it.» برای production decision-making روی tenant ماینینگ، DeepSeek ریسکِ uptime دارد.

- **Tokenizer inflation در Anthropic 4.7+.** `[established]` مدل‌های از Opus 4.7 به‌بعد tokenizer جدیدی دارند که ممکن است تا ۳۵٪ توکنِ بیشتر تولید کند. cross-model cost comparison را بر اساسِ character یا task، نه فقط MTok انجام بده.

- **Retry cost.** `[Probable]` هر بار که agent کاری را اشتباه می‌کند و redo می‌کند، هزینه‌ی double می‌شود. خطاهای model = هزینه‌ی double. اگر error rate 20٪ است، effective cost 24٪ بالاتر از list price است.

- **Batch API = 24h latency.** `[established]` برای taskهای non-critical این عالی است (هفتگی/شبانه). برای هر چیزی که real-time نیاز دارد، Batch API قابلِ استفاده نیست.

- **«Cheaper model per token ≠ cheaper model per task».** `[established]` یک مدلِ ضعیف ممکن است ۳ بار retry کند تا کاری درست انجام شود که Sonnet در یک بار انجام می‌داد. Effective cost per task می‌تواند بالاتر باشد.

- **Caching غلط = latency بدتر.** `[established]` «Naive caching can paradoxically increase latency if cache blocks are positioned poorly.» cache blocks را آزمایش کن.

- **Self-hosting Ollama در production.** `[established]` «Ollama Cloud had a 95% failure window in April 2026. [Ollama] is optimized for simplicity, not maximum throughput.» vLLM برای production serving، Ollama برای dev/prototype.

- **هزینه‌ی VPS برای Ollama CPU.** `[established]` اگر VPS برای agentهای دیگر هم shared است، هزینه‌ی CPU برای Ollama از همه‌ی tenantها می‌دزدد. resource contention مستقیم. جداسازی با cgroups اجباری است.

- **Output tokens ۲–۶× گران‌ترند.** `[established]` اکثرِ محاسبه‌های هزینه روی input focus می‌کنند. ولی output tokens در Sonnet 5× گران‌تر از input‌اند. structured outputs و کاهشِ max_tokens می‌تواند بیشتر از prompt compression صرفه بدهد.

---

## Recommendation

**چرخه‌ی بهینه‌سازیِ هزینه برای تک‌نفره:**

### گامِ ۱ (فوری): Measure first — «۸۰/۲۰» پیدا کن

قبل از هر optimize، یک dashboard ساده بساز که per-task token count و cost را log کند:
```python
cost_per_task = {
    "tenant": tenant_id,
    "task_type": task_type,
    "input_tokens": response.usage.input_tokens,
    "output_tokens": response.usage.output_tokens,
    "cached_tokens": response.usage.cache_read_input_tokens,
    "cost_usd": (input_tokens * 3 + output_tokens * 15) / 1_000_000,
    "timestamp": datetime.now()
}
```
بعد از ۷ روز، taskهای ۸۰٪ هزینه را پیدا کن. فقط روی آن‌ها focus کن.

### گامِ ۲ (این هفته): Prompt caching فعال کن

```python
# هر system prompt که بیشتر از ۱۰۰۰ توکن است:
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": long_system_context,
                "cache_control": {"type": "ephemeral"}
            },
            {"type": "text", "text": actual_request}
        ]
    }
]
```
انتظار: ۵۰–۹۰٪ کاهشِ input cost برای taskهای با context بزرگ.

### گامِ ۳ (این ماه): Tiered routing اضافه کن

یک تابعِ ساده‌ی rule-based classifier بساز (بدونِ LLM call اضافه):
- حداقل ۷۰٪ taskها → Haiku 3.5
- ۲۵٪ → Sonnet 4.6
- ۵٪ (security-critical، complex) → Opus 4.8

انتظار: ۴۵–۶۰٪ کاهشِ کلِ bill.

### گامِ ۴ (ماهِ بعد): Batch API برای async

taskهایی که ۲۴ ساعت delay تحمل می‌کنند (weekly research، report generation، log analysis) را از طریقِ Batch API بفرست → ۵۰٪ discount خودکار.

### گامِ ۵ (اگر GPU موجود است): Ollama روی لپ‌تاپ برای non-critical

برای classification، embedding، و simple summarization از Ollama روی laptop استفاده کن (Qwen3.5-7B، Phi-4-14B). tenant ماینینگ که already GPU/electricity دارد می‌تواند از این برای backtestِ ساده استفاده کند.

**ولی:** هرگز production financial reasoning را به local 7B model بده — کیفیت برای این domain کافی نیست.

### Resource contention روی VPS

```bash
# cgroups per-tenant + job queue:
systemctl set-property agent-research.service CPUQuota=25% MemoryMax=4G
systemctl set-property agent-mining.service CPUQuota=20% MemoryMax=3G
systemctl set-property agent-accounting.service CPUQuota=15% MemoryMax=2G
# task queue: Redis یا Postgres LISTEN/NOTIFY برای throttle
```

### دقیقاً چه چیزی را **نساز:**

- ❌ **Self-host GPU در VPS اجاره‌ای** — احتمالاً KVM ندارد؛ حتی اگر داری، break-even >50M توکن/ماه است
- ❌ **DeepSeek برای production ماینینگ** — uptime ناپایدار؛ جایی که پولِ واقعی در کار است، reliability > cost
- ❌ **Routing با LLM classifier** — یک regex/keyword rule ۱ms latency دارد؛ یک LLM classifier ۵۰۰ms اضافه می‌کند
- ❌ **همه‌ی taskها روی Opus** — ۶× گران‌تر از Haiku؛ برای ۷۰٪ taskها بیش از حد است
- ❌ **Optimize کردن قبل از measuring** — ممکن است روی ۲۰٪ بودجه optimize کنی نه ۸۰٪
- ❌ **Batch API برای real-time tasks** — ۲۴h delay ندارند
- ❌ **Ollama CPU برای reasoning پیچیده** — 5-10 tok/s × long chain = دقیقه‌ها برای یک task

---

## TOOLING

| Tool | Pricing | Best alternative | Lock-in (۱–۱۰) |
|---|---|---|---|
| **Claude API (Anthropic)** | pay-per-token (verify) | OpenAI / Gemini | **4** — MCP/OTel ضدِ lock-in |
| **Anthropic Prompt Caching** | ۹۰٪ تخفیفِ cached input | context compression | **4** — Anthropic-specific |
| **Anthropic Message Batches** | ۵۰٪ تخفیف + max 24h latency | OpenAI Batch API | **4** |
| **Gemini 3.1 Pro / Flash** | cheapest frontier / $0.10-0.15 per 1M | Claude Haiku | **4** (Google) |
| **DeepSeek V4 Flash** | cheapest «GPT-4 class» ($0.14) | Gemini Flash | **3** ولی uptime ریسک |
| **Ollama (local)** | OSS رایگان؛ hardware cost | vLLM / llama.cpp | **1** |
| **Ollama Cloud Pro** | ~$20/ماه (`verify`) | self-host | **5** (cloud) |
| **vLLM (Apache 2.0)** | OSS رایگان؛ GPU cost | Ollama / TGI | **1** |
| **LiteLLM (MIT)** | OSS رایگان self-host | Portkey / custom gateway | **2** — wrapper برای multi-provider |
| **Portkey** | freemium; usage-based | LiteLLM self-host | **4** |
| **LLM gateway + routing (custom)** | infrastructure cost | LiteLLM | **1** |
| **Redis** (job queue / rate limiting) | OSS رایگان self-host | Postgres LISTEN-NOTIFY | **2** |

---

## If-I'm-wrong

**قوی‌ترین ضدِ توصیه («Ollama CPU-only برای non-critical»):** اگر بارِ عملیاتیِ VPS زیاد باشد، یک Ollama 7B که 5-10 tok/s پردازش می‌کند همه‌ی CPU را می‌خورد و tenant‌های دیگر را قربانی می‌کند. اگر cgroup را دقیق نگه ندارید، بدتر از API call است (API در جایی دیگر process می‌شود). ابتدا با یک cgroup test مطمئن شو که Ollama روی VPS مشترکِ تو کنترل‌پذیر است.

**ضدِ توصیه‌ی دوم («Haiku برای ۷۰٪ tasks»):** اگر ۷۰٪ taskهایی که به Haiku می‌فرستی در واقع medium-complexity هستند، quality drop می‌شود و retry rate بالا می‌رود — که effective cost را بدتر از all-Sonnet می‌کند. routing باید با eval تأیید شود (lane 5). پیشنهاد: با ۵۰٪ Haiku / ۵۰٪ Sonnet شروع کن، بعد بر اساسِ eval به ۷۰/۲۵/۵ برو.

**ضدِ توصیه‌ی سوم («DeepSeek فقط برای background»):** ممکن است تا وقتِ خواندنِ این گزارش، DeepSeek V4 reliability اش بهتر شده باشد. `[uncertain]` — verify. اگر بهتر شده، برای batch research روی tenant تحقیق (نه ماینینگ) گزینه‌ی جذابی است.

---

## Confidence

**High** برای قیمت‌های اصلیِ API (تأییدشده از منابعِ ژوئن ۲۰۲۶ متعدد) و break-even math. **Medium** برای savings projections از routing (vendor-reported یا estimate، نه benchmark مستقل). **Low/uncertain** برای قیمت‌های DeepSeek و Ollama Cloud (frequently change) و Claude Fable 5 availability — verify با providers. ⚠️ قیمت‌ها quarterly تغییر می‌کنند.

---

## Claims table

| claim | evidence | confidence (H/M/L) | source + date |
|---|---|---|---|
| یک chatbot: 2k-4k توکن؛ یک agent task: 50k-500k توکن | practitioner data | H | requesty.ai 2026-06 |
| multi-agent parallel: ~15× توکنِ بیشتر از sequential | practitioner consensus | M | requesty.ai 2026-06 |
| inference 85٪ of enterprise AI budget | Anthropic engineering teams early 2026 | M (vendor-claimed) | requesty.ai 2026-06 |
| قانون ۸۰/۲۰: ۸۰٪ هزینه از ۲۰٪ tasks | practitioner consensus | H | paxrel.com 2026-03 |
| Anthropic prompt caching: ۹۰٪ تخفیف روی cached input | مستنداتِ رسمیِ Anthropic | H | aimagicx.com 2026-03؛ cloudzero.com |
| routing 70٪ cheap + 20٪ mid + 10٪ frontier → ۸۶٪ کاهش از Opus-only | requesty.ai math | M (calculated) | requesty.ai 2026-06 |
| Teams with tiered routing report 40-85% bill reduction | multiple practitioner reports | H | digitalapplied.com؛ aisuperior.com |
| <50M tokens/month: APIs cheaper; >50M: self-host becomes cost-neutral | multiple sources | H | codersera.com 2026-05؛ aipricingmaster.com |
| self-hosted vLLM vs DeepSeek ($0.14): break-even ~800M tokens/month | calculation | M | checkthat.ai/ollama 2026-05 |
| Ollama CPU VPS 7B: 5-10 tok/s sustained | benchmarks | H | danubedata.ro 2026-06 |
| Ollama Cloud April 2026: 95٪ failure window documented | review | H | checkthat.ai/ollama 2026-05 |
| vLLM 2.6× faster tokens/second vs Ollama on same hardware | benchmark | H | checkthat.ai/ollama 2026-05 |
| Claude Fable 5 + Mythos 5 suspended June 12, 2026 (export-control) | morphllm.com pricing page | H | morphllm.com 2026-06-28 |
| Claude Opus 4.8: $5/$25 per 1M tokens (88.6٪ SWE-bench); Sonnet 4.6: $3/$15 | pricing pages (verify) | H | morphllm.com؛ cloudzero.com |
| DeepSeek V4 Flash: $0.14/$0.28 per 1M (cheapest GPT-4 class) | pricing pages (verify) | H | morphllm.com 2026-06؛ curlscape.com |
| Gemini 2.5 Flash: $0.10-0.15/$0.40-0.60 | pricing pages (verify) | H | multiple sources |
| Batch API (OpenAI + Anthropic): 50٪ تخفیف | مستنداتِ رسمی | H | tldl.io 2026-04؛ requesty.ai |
| Anthropic tokenizer در 4.7+: تا 35٪ توکنِ بیشتر | morphllm.com pricing note | H | morphllm.com 2026-06 |
| Engineering labor: 1.5-2 FTE = $270K-$550K/year for self-host ops | industry estimate | M | aipricingmaster.com 2026-01 |
| Ollama 52 million monthly downloads Q1 2026; 135K GGUF models on HuggingFace | Ollama stats | H | dev.to 2026-04 |
| Semantic caching + routing → 30-50٪ cost reduction within 4-6 weeks | industry estimate | M | aisuperior.com 2026-04 |

---

*فایل: `11-research-cost-infra-routing.md` — آماده‌ی merge با سایرِ laneها با همین ۸ سرفصلِ ثابت.*
