# RESEARCH LANE — Tool design & interoperability
# طراحیِ tool و interoperability بین عامل‌ها — ۲۰۲۵–۲۰۲۶

> **DOMAIN:** سیستم‌های multi-agent خودمیزبان برای اپراتور تک‌نفره.
> **LANE (قفل‌شده):** فقط طراحیِ tool، protocolهای interop، progressive disclosure، و tool-use safety — نه framework orchestration، نه memory.
> **CONSTRAINTS:** VPS مشترک + لپ‌تاپ + Claude Cowork؛ تک‌نفره؛ export-first، no vendor lock-in؛ per-action cap + kill switch + audit log.
> **تاریخِ ساخت:** ۲۰۲۶-۰۷-۰۱. منابع از web search زنده. برچسب: `[established] / [emerging] / [speculative]`.

---

## Summary

۱. **تمایزِ بنیادین که اکثر منابع گیج می‌شوند:** MCP = agent-to-tool (یک agent به ابزارها/data sources وصل می‌شود). A2A = agent-to-agent (یک agent کار را به agentِ دیگری در frameworkِ دیگر واگذار می‌کند). این دو لایه مکمل‌اند، نه رقیب. `[established]`

۲. **بحرانِ context bloat:** setup استانداردِ MCP می‌تواند **۷۲٪** از context window را با tool definitions بخورد قبل از اینکه agent اولین سؤال کاربر را بخواند. Anthropic با progressive tool loading این را از ~150k توکن به ~2k توکن (98.7٪ کاهش) رساند. این الان GA است (فوریه ۲۰۲۶). `[established]`

۳. **tool poisoning یک خطرِ واقعیِ مستند است.** MCPTox benchmark: o1-mini با ۷۲.۸٪ success rate قابلِ حمله است؛ Claude 3.7-Sonnet کمتر از ۳٪ این حملات را رد کرد. CVE واقعی در MCP serverهای رسمیِ Anthropic (ژانویه ۲۰۲۶). `[established]`

۴. **برای پروژه‌ی تک‌نفره روی VPS مشترک:** MCP فقط جایی لازم است که tool باید توسطِ agentهای مختلف یا Cowork کشف و استفاده شود. برای operationهای داخلی یک‌پروژه، یک Python function ساده کافی‌تر و امن‌تر است. `[Probable]`

۵. **A2A v1.0 (اوایل ۲۰۲۶):** برای ارتباطِ عامل‌ها در frameworkهای مختلف. IBM ACP در آن ادغام شد. ۱۵۰+ سازمان در production. برای تک‌نفره روی VPS مشترک الان **over-engineering** است — مگر tenant‌هایت واقعاً نیازِ به cross-framework agent communication داشته باشند. `[emerging]`

---

## Landscape

**۱) MCP (Model Context Protocol) — وضعیتِ ۲۰۲۶.** `[established]`

Anthropic نوامبر ۲۰۲۴ MCP را معرفی کرد، اواخرِ ۲۰۲۵ به Agentic AI Foundation (Linux Foundation) واگذار شد. استانداردِ «USB-C برای AI». در آوریل ۲۰۲۶: بیش از ۱۰٬۰۰۰ enterprise MCP server و بیش از ۹۷ میلیون SDK download از فروشندگانِ مختلف. MCP الان توسطِ Claude، ChatGPT، Cursor، VS Code Copilot، GitHub Copilot پشتیبانی می‌شود.

**اسپکِ RC جدید (2026-07-28، نهایی ۲۸ ژوئیه):** `[emerging / uncertain]` هسته‌ی stateless روی HTTP معمولی (بدونِ نیاز به sticky session یا shared session store)، افزونه‌ی Tasks (کارِ طولانی)، MCP Apps (UI serverside)، authorizationِ OAuth/OIDC‌ هم‌تراز، W3C Trace Context برای distributed tracing، و `ttlMs/cacheScope` برای caching نتایجِ tool list. Mcp-Method و Mcp-Name headers برای routing بدونِ body inspection.

**چرا در ۲۰۲۶ باید MCP server بنویسیم؟** — سه دلیلِ واقعی:
- tool باید توسطِ Cowork / agentهای مختلف کشف شود بدونِ hardcoding
- می‌خواهی access control، logging، و rate-limiting را یکجا اعمال کنی (gateway pattern)
- می‌خواهی در آینده tool را به agent دیگری expose کنی بدونِ تغییرِ کد

**چرا function ساده کافی‌تر است؟** — وقتی:
- tool فقط یک agent می‌خواند
- operation internal است و نیازِ به discovery ندارد
- می‌خواهی overhead و attack surface را کم کنی

---

**۲) A2A (Agent2Agent Protocol) — وضعیتِ ۲۰۲۶.** `[established → emerging در production]`

Google آوریل ۲۰۲۵ معرفی کرد با ۵۰+ launch partner، ژوئن ۲۰۲۵ به Linux Foundation واگذار شد (Apache 2.0)، IBM ACP در آگوست ۲۰۲۵ در آن ادغام شد. v1.0 اوایل ۲۰۲۶: Signed Agent Cards (cryptographic signatures برای domain verification)، task lifecycle ساختاریافته (pending/in-progress/completed/failed)، Server-Sent Events برای streaming.

**۱۵۰+ سازمان در production (نه pilot):** Microsoft Azure AI Foundry، Amazon Bedrock AgentCore، Salesforce، SAP، ServiceNow و Google Cloud همگی A2A را native integrate کرده‌اند. v1.2 با AP2 extension (payments) در Cloud Next 2026.

**A2A vs MCP:** یک agent از A2A استفاده می‌کند تا کار را به agentِ specialistِ دیگری واگذار کند؛ آن specialist از MCP استفاده می‌کند تا به toolهایش وصل شود. هر دو در یک stack production وجود خواهند داشت.

**برای تک‌نفره الان:** A2A برای دوِ tenant مختلف که با هم صحبت نمی‌کنند، over-engineering است. اگر routing بین pipelineها نیاز داری، یک function call ساده‌تر است. A2A وقتی ارزش دارد که agentهای مستقل در frameworkهای مختلف باشند که باید task delegation داشته باشند.

---

**۳) Progressive tool disclosure — از بحران به standard.** `[established]`

**بحران:** یک agent که به ۳ MCP server (GitHub، Playwright، IDE) وصل بود، ۱۴۳٬۰۰۰ از ۲۰۰٬۰۰۰ توکنِ context window را با tool definitions پر کرد — **قبل از خواندنِ اولین سؤال کاربر.** ۷۲٪ حافظه‌ی کاریِ model، صرفِ descriptionهایی که در اکثرِ requestها استفاده نمی‌شوند.

**راه‌حل‌های GA شده در ۲۰۲۶:**
- **Anthropic Tool Search** (نوامبر ۲۰۲۵، GA فوریه ۲۰۲۶): tools به‌جای preload در context، تنها وقتی agent به آن‌ها نیاز دارد load می‌شوند. ادعا: **۸۵٪ کاهشِ توکن** + حفظِ ۱۹۱٬۰۰۰ توکن در مقایسه با روشِ conventional.
- **Anthropic MCP + code execution** (نوامبر ۲۰۲۵): از ۱۵۰٬۰۰۰ به ۲٬۰۰۰ توکن = **۹۸.۷٪ کاهش** برای همان task.
- **Cloudflare Code Mode** (فوریه ۲۰۲۶): کاهشِ **۹۹.۹٪** در input token با wrap کردنِ ۲٬۵۰۰ endpoint در ۲ tool.

**الگوی سه‌سطحیِ progressive disclosure:**
1. **Level 0 (همیشه):** فقط نامِ tool + یک‌خطی description در context
2. **Level 1 (on-demand):** full schema وقتی agent قصدِ استفاده دارد
3. **Level 2 (on-call):** اجرا + نتیجه

**طراحیِ عملی:** هر tool description باید بگوید «چه کار می‌کند و کِی استفاده شود» در یک جمله، با لینک به documentationِ جداگانه نه embed کردنِ آن در description.

---

**۴) Tool-use safety: Prompt injection، Tool poisoning، Rug pull.** `[established]`

**prompt injection از طریقِ tool result (نه فقط user input):**
وقتی agent یک tool call می‌زند و content آن حاوی دستوراتِ پنهان است، آن محتوا وارد context می‌شود. در آوریل ۲۰۲۶، محققانِ Johns Hopkins، Claude Code، Gemini CLI، و GitHub Copilot را از طریقِ malicious instructions در PR titlesِ GitHub hijack کردند — agentها اسرارِ GitHub Actions را exfiltrate کردند. این attack به compromiseِ زیرساخت نیاز ندارد؛ فقط به رساندنِ محتوایِ مخرب به چیزی که agent می‌خواند.

**Tool poisoning:**
توضیحاتِ tool (tool description) می‌توانند شاملِ دستوراتِ پنهانی باشند که کاربر نمی‌بیند ولی model می‌بیند. MCPTox benchmark (۲۰ agent، ۴۵ MCP server، ۳۵۳ tool): نتیجه‌ی نگران‌کننده: **o1-mini در ۷۲.۸٪ مواقع تحتِ حمله قرار می‌گیرد**؛ modelهای قوی‌تر اغلب *آسیب‌پذیرترند* چون instruction-following قوی‌تری دارند. Claude 3.7-Sonnet تنها کمتر از ۳٪ این حملات را رد کرد.

**Rug pull attack:**
tool در ابتدا legitimate است، بررسی و approve می‌شود، سپس رفتارش عوض می‌شود (version update مخرب). هیچ defense ایستایی را ۱۰۰٪ نمی‌گیرد.

**CVE واقعی در MCP serverهای Anthropic:**
CVE-2025-68143، CVE-2025-68144، CVE-2025-68145 — سه آسیب‌پذیریِ prompt injection در Git MCP server رسمیِ Anthropic (ژانویه ۲۰۲۶). مهاجم فقط نیاز داشت محتوایِ مخربی (مثلاً README آلوده) در چیزی که agent می‌خواند قرار دهد.

**دفاع‌های عملی که کار می‌کنند (نه ۱۰۰٪ ولی مهم):**
- input validation و sanitization روی **tool results** (نه فقط user input)
- least-privilege: هر tool فقط permissionهایی که واقعاً لازم دارد
- sandbox execution برای tool callهای با side-effect
- human-in-the-loop برای high-risk tool calls
- version locking + cryptographic signatures برای tool definitions
- mcp-scan (Snyk) برای audit toolهای MCP

**مهم:** «هیچ دفاعِ کاملی وجود ندارد چون آسیب‌پذیری معماری است.» International AI Safety Report ۲۰۲۶ نشان داد مهاجمانِ پیچیده در ۵۰٪ موارد با ۱۰ تلاش از بهترین defenseها عبور می‌کنند.

---

## Comparison table

> جهتِ نمره: ۱۰ = بهترین برای تک‌نفره/VPS مشترک. `[Probable]` جز جایی که explicit data داریم.

| رویکرد | Cost | Complexity | Security | Interop | Buildable Now | Maturity |
|---|---|---|---|---|---|---|
| **Function ساده (internal)** | 10 | 10 | 8* | 2 | ✅ | 10 |
| **MCP server (self-host، stdio)** | 9 | 7 | 6† | 8 | ✅ | 8 |
| **MCP server (self-host، Streamable HTTP، اسپکِ ۲۵-۱۱-۲۵)** | 8 | 6 | 6† | 9 | ✅ | 7 |
| **MCP Gateway (IBM Context Forge)** | 8 | 5 | 7 | 8 | ✅ | 6 |
| **A2A (v1.0، Apache 2.0)** | 7 | 4 | 7 | 9 | ⚠️ (emerging) | 6 |
| **Progressive disclosure + Tool Search** | 9 | 7 | 7 | 7 | ✅ (GA) | 8 |
| **Cloudflare MCP Workers** | 6 | 7 | 8 | 8 | ✅ | 7 |
| **Raw HTTP API (بدونِ MCP)** | 9 | 7 | 7 | 3 | ✅ | 10 |

\* function ساده: attack surface کم‌تر چون external discovery ندارد.
† MCP: tool result می‌تواند حاملِ injectionِ پنهان باشد؛ باید input validation روی result هم داشته باشی.

---

## Blind spots

- **«MCP = امن» یک فرضِ اشتباه است.** `[established]` MCP بدونِ validation روی tool results، یک سطحِ حملهٔ جدید باز می‌کند که بدتر از HTTP plain است چون agent به tool result بیشتر اعتماد می‌کند. ۳ CVE در serverهای رسمیِ Anthropic در ژانویه ۲۰۲۶ این را اثبات کرد.

- **context bloat اگر progressive disclosure فعال نباشد.** `[established]` ۷۲٪ context waste در setup استاندارد. اگر از Cowork و چند MCP server استفاده می‌کنی و Tool Search را فعال نکردی، احتمالاً بیشتر توکن‌هایت صرفِ tool definitions می‌شود تا کار واقعی.

- **A2A در production بدونِ Signed Agent Cards فاصله دارد.** `[established]` v1.0 با Signed Agent Cards برای domain verification آمد (اوایل ۲۰۲۶). قبل از v1.0، هر agent می‌توانست ادعا کند هر کسی است. اگر از A2A استفاده می‌کنی، v1.0 حداقل است.

- **Rug pull در tool ecosystem هنوز بدونِ راه‌حلِ خوب است.** `[established]` version locking کمک می‌کند ولی اگر tool vendorی ورژن را آپدیت کند با همان شماره، تشخیص سخت است. برای tool به‌شکلِ خودمیزبان (MCP server که تو کنترل می‌کنی) این خطر از بین می‌رود.

- **«A2A برای الان» هنوز ناکافی است.** `[Probable]` ۱۵۰+ سازمان در production ادعا می‌شود، ولی بیشتر در enterprise-scale. برای تک‌نفره با ۵ tenant روی یک VPS، هزینه‌ی یادگیری + opsِ A2A server بیشتر از ارزشِ آن است. `[Probable]`

- **MCP spec 2026-07-28 هنوز RC است.** `[uncertain / emerging]` تا نهایی شدنِ ۲۸ ژوئیه ۲۰۲۶، به اسپکِ پایدارِ ۲۰۲۵-۱۱-۲۵ بچسب.

- **multi-tenant isolation در MCP server — پیش‌فرض نیست.** `[established]` اگر همه‌ی tenantها از یک MCP server مشترک استفاده کنند، باید session/user scoping اجباری باشد. بدونِ این، tenant حسابداری می‌تواند به toolهای tenant ماینینگ دسترسی داشته باشد.

- **Rate-limiting در MCP بدون gateway سخت است.** `[established]` MCP spec خودش rate-limiting ندارد. باید در سطحِ gateway (IBM Context Forge یا Traefik middleware) پیاده شود، یا در خودِ server logic.

- **Tool description quality → security + performance.** `[Probable]` tool description بدِ کوتاه (نگفتن کِی استفاده شود) = agent tool اشتباه انتخاب می‌کند. tool description طولانیِ detailed = context bloat. بهترین: یک جمله چه کار می‌کند + یک جمله کِی. documentation جداگانه.

---

## Recommendation

**برای stack تو (VPS + Cowork + چند tenant):**

### قانونِ ساده: MCP کِی؟ function کِی؟

**Function ساده (Python callable) → بگذار وقتی:**
- tool فقط یک agent یا pipeline می‌خواند
- operation کاملاً داخلی است (Postgres query، file read، calculation)
- می‌خواهی attack surface را کم کنی
- tool هیچ‌وقت نیازِ به discovery از بیرون ندارد
- حالتِ default را اینجا بگذار

**MCP server → بگذار فقط وقتی:**
- Cowork یا Claude باید tool را کشف و مستقیم صدا بزند بدونِ hardcoding
- می‌خواهی access control + audit را یکجا اعمال کنی (از MCP gateway عبور کند)
- tool به بیش از یک agent یا project expose می‌شود
- می‌خواهی در آینده tool را با دیگری به اشتراک بگذاری

**A2A → الان نساز.** برای ارتباطِ عامل‌ها در frameworkهای مختلف؛ برای یک VPS با Cowork-centric orchestration، یک function call کافی است. وقتی واقعاً نیازِ به cross-framework agent delegation داشتی، برگرد.

---

### اجرای عملی (به ترتیبِ اولویت):

**۱. فوری — Tool Search را فعال کن (اگر هنوز نکردی):**
اگر از Claude Code v2.1.7+ یا Cowork استفاده می‌کنی، Tool Search احتمالاً by default فعال است. `[uncertain]` verify کن. اگر نبود، از deferred-loading pattern استفاده کن.

**۲. فوری — Tool descriptions را اصلاح کن:**
برای هر tool: یک جمله «چه کار می‌کند» + یک جمله «کِی استفاده شود». Documentation را بیرون بگذار نه داخلِ description. این ۸۵٪+ کاهشِ توکن را بدونِ هیچ تغییرِ معماری می‌دهد.

**۳. فوری — Validation روی tool results (نه فقط input):**
هر خروجیِ MCP tool / external source را قبل از وارد شدن به context agent sanitize کن. به‌خصوص برای tenant‌هایی که محتوایِ web یا documentِ خارجی می‌خوانند.

**۴. مرحله‌ی بعد — یک MCP gateway (chokepoint) برای همه‌ی tool calls:**
همان MCP gateway که در lane مشترک (shared engineering) توصیه شد. همه‌ی tool callهای همه‌ی tenantها از آن رد شوند:
- rate-limiting per-tenant
- least-privilege enforcement
- audit log per tool call
- tool version locking

**۵. مرحله‌ی بعدتر — خودمیزبانیِ MCP server per-project:**
هر project یک MCP server خودش (Docker container در VPS)، با scope محدود به همان project. tenant-isolation طبیعی می‌شود چون server جدا است.

**۶. اگر واقعاً به A2A رسیدی:**
IBM Context Forge از A2A پشتیبانی دارد. آن را به‌عنوانِ gateway استفاده کن و A2A server را جدا راه نینداز.

### دقیقاً چه چیزی را **نساز**:

- ❌ **MCP server برای operationهای purely internal** — function ساده کافی است.
- ❌ **A2A برای routing بین tenantهایت** — آن‌ها agentهای مستقل در frameworkهای مختلف نیستند.
- ❌ **Tool description طولانی** — context waste بدون ارزش.
- ❌ **Trust کردنِ tool result بدونِ validation** — حتی از MCP server خودت.
- ❌ **اسپکِ RC جدیدِ MCP (2026-07-28) تا نهایی شدن** — از 2025-11-25 استفاده کن.
- ❌ **یک MCP server مشترکِ بدونِ tenant-scoping** — cross-project leakage.
- ❌ **Cloudflare Workers** اگر data باید روی VPS خودت بماند — export-first ارزشِ تو را نقض می‌کند.

---

## TOOLING

| Tool | Pricing model | Best alternative | Lock-in (۱–۱۰) |
|---|---|---|---|
| **MCP (استاندارد)** | OSS رایگان (Apache 2.0 / Agentic AI Foundation) | — (هدف ضدِ lock-in است) | **1** |
| **A2A (v1.0، Apache 2.0)** | OSS رایگان (Linux Foundation) | function call ساده | **1** |
| **IBM Context Forge** (MCP gateway) | OSS رایگان self-host (`verify` license) | SelfHostedMCP.com blueprint | **2** |
| **mcp-scan (Snyk)** | OSS رایگان (`verify` license) | custom allowlist check | **2** |
| **Anthropic Tool Search** | بخشیِ Claude/Cowork (هزینه‌ی API مدل) | manual deferred loading | **4** (Anthropic ecosystem) |
| **SelfHostedMCP.com gateway blueprint** | OSS رایگان (Traefik+WireGuard+CrowdSec) | IBM Context Forge | **1** |
| **Cloudflare Workers MCP** | رایگانِ free-tier + Workers Paid $5/ماه | self-host روی VPS | **6** (data بیرون) |
| **Qdrant for tool semantic search** | Apache 2.0 self-host رایگان | pgvector | **2** |
| **LLM Guard / Rebuff** (prompt injection defense) | OSS رایگان | Microsoft Prompt Shields | **2** |
| **Python function (internal)** | رایگان کاملاً | — | **1** |

---

## If-I'm-wrong

**قوی‌ترین ضدِ توصیه («function ساده به‌جای MCP»):** اگر Cowork به‌شکلی طراحی شده که **فقط از طریقِ MCP** به toolها دسترسی دارد (بعضی tool-calling environments همین‌طوراند)، آن‌وقت «function ساده» اصلاً قابلِ call نیست. `[uncertain]` — باید با مستنداتِ Cowork verify کنی که آیا direct function invocation پشتیبانی می‌شود یا فقط MCP.

**ضدِ توصیه‌ی دوم («A2A الان نساز»):** اگر در آینده‌ی نزدیک بخواهی agentهای مستقلی بسازی که با Gemini Agentspace یا Azure AI Foundry ارتباط دارند، A2A را از اول نداشتن migration گران‌تر می‌کند. ولی این سناریو برای یک VPS تک‌نفره با ۵ tenant home-grown خیلی دور است. `[Probable]`

**ضدِ توصیه‌ی سوم («tool description یک‌جمله‌ای کافی است»):** برای toolهایی با semanticهای پیچیده (مثلاً ابزارِ ماینینگ با parameter طولانی) یک جمله ممکن است ambiguous باشد و agent tool اشتباه صدا بزند. در این موارد description طولانی‌تر (ولی جدا از schema) + few-shot examples بهتر است. `[Probable]` — trade-off بین context cost و accuracy را با eval بسنج.

---

## Confidence

**High-Medium.** landscape MCP/A2A خوب مستند است (منابعِ متعددِ ژانویه–مه ۲۰۲۶). بخش‌های با اطمینانِ پایین‌تر: (الف) Cowork-specific behavior — باید از مستنداتِ خودِ Cowork verify شود؛ (ب) A2A production readiness برای solo/small scale هنوز sparse evidence دارد؛ (پ) اسپکِ MCP 2026-07-28 هنوز RC است. نمره‌های امنیتی vendor-self-reported یا از محیطِ lab هستند.

---

## Claims table

| claim | evidence | confidence (H/M/L) | source + date |
|---|---|---|---|
| MCP = agent-to-tool (Anthropic، نوامبر ۲۰۲۴)؛ A2A = agent-to-agent (Google، آوریل ۲۰۲۵) — مکمل، نه رقیب | اتفاقِ نظرِ مستقل | H | dev.to 2026-04؛ IBM think 2025-11 |
| A2A (Apache 2.0): ۱۵۰+ سازمان در production، v1.0 با Signed Agent Cards اوایل ۲۰۲۶، Linux Foundation governance | Google Cloud Next 2026 + Stellagent report | H | thenextweb.com 2026-05؛ stellagent.ai 2026-04 |
| IBM ACP در آگوست ۲۰۲۵ در A2A ادغام شد | IBM Think | H | ibm.com/think 2025-11 |
| MCP context bloat: setup استاندارد ۷۲٪ context را با tool definitions می‌گیرد قبل از کار | case study (3 MCP server، 143k/200k توکن) | H | agentpmt.com 2026-02 |
| Tool Search GA (Anthropic، فوریه ۲۰۲۶): 85٪ کاهشِ توکن، حفظِ ۱۹۱k توکن | Anthropic-claimed | H | agentpmt.com 2026-02؛ mcp.directory 2026-05 |
| Code execution + MCP (Anthropic، نوامبر ۲۰۲۵): 150k → 2k توکن (98.7٪ کاهش) | Anthropic-claimed | H | wire blog 2026-05 |
| Cloudflare Code Mode (فوریه ۲۰۲۶): 99.9٪ کاهشِ input token | Cloudflare-claimed | M (`verify`) | mcp.directory 2026-05 |
| MCPTox benchmark: o1-mini با 72.8٪ success rate آسیب‌پذیر؛ Claude 3.7-Sonnet کمتر از 3٪ رد کرد | benchmark results | H | datadome.co 2026-01 |
| CVE-2025-68143/44/45: prompt injection در Git MCP server رسمیِ Anthropic (ژانویه ۲۰۲۶) | CVE database | H | cyberdesserts.com 2026-12 |
| آوریل ۲۰۲۶: Claude Code/Gemini CLI/GitHub Copilot از طریقِ PR title injection hijack شدند، GitHub Actions secrets exfiltrate شد | Johns Hopkins research | H | aptible.com 2026-06 |
| International AI Safety Report 2026: مهاجمانِ پیچیده در 50٪ موارد با ۱۰ تلاش از بهترین defensها عبور می‌کنند | IASR 2026 | H | cyberdesserts.com |
| MCP اسپکِ 2026-07-28 RC است؛ stateless HTTP core، Tasks extension، OAuth/OIDC، W3C Trace Context؛ نهایی ۲۸ ژوئیه | blog.modelcontextprotocol.io | H (برای RC) / M (تا نهایی) | blog.modelcontextprotocol.io |
| Progressive disclosure الگوی سه‌سطحی: description → schema → execution | consensus در ادبیاتِ ۲۰۲۶ | H | ardalis.com 2026-04؛ mcp.directory 2026-05 |
| Skills (Anthropic): progressive loading سه‌سطحی built-in، context bloat را minimize می‌کند | مستنداتِ Anthropic | H | duet.so 2026-05 |
| mcp-scan (Snyk): ابزارِ audit برای MCP servers و skills برای آسیب‌پذیری‌های شناخته‌شده | مستنداتِ Snyk | H | cyberdesserts.com |
| ۱۰٬۰۰۰+ enterprise MCP server، ۹۷M+ SDK downloads (آوریل ۲۰۲۶) | گزارشِ صنعتی | M (`verify`) | wire blog 2026-05 |
| A2A AP2 extension: payments layer، Google Cloud Next 2026 | Google Cloud Next announcement | H | thenextweb.com 2026-05 |
| IBM Context Forge از A2A/MCP/REST/gRPC federation پشتیبانی می‌کند | GitHub documentation | H | github.com/IBM/mcp-context-forge |

---

*فایل: `08-research-tool-interoperability.md` — آماده‌ی merge با سایرِ laneها با همین ۸ سرفصلِ ثابت.*
