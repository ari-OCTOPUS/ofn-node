# RESEARCH LANE — Shared Engineering (لایه‌ی مهندسیِ مشترکِ بین همه‌ی tenantها)

> **DOMAIN:** سیستم‌های multi-agent خودمیزبان برای اپراتور تک‌نفره.
> **LANE (قفل‌شده):** فقط لایه‌ی زیرساخت/orchestrationِ عرضی که همه‌ی پروژه‌ها (تحقیق، حسابداری/lead-gen، مارکتینگ، ماینینگ/سرمایه‌گذاری، دفترچه) روش سوارند — نه استکِ هیچ vertical خاصی.
> **CONSTRAINTS:** یک VPS مشترکِ اجاره‌ای + لپ‌تاپ، ارکستره از Claude Cowork؛ تک‌نفره، operable/maintainable؛ export-first، no vendor lock-in؛ هر auto-execution با per-action cap + kill switch + audit log (غیرقابل‌حذف).
> **تاریخِ ساخت:** ۲۰۲۶-۰۷-۰۱. همه‌ی داده‌ها از web search زنده، نه از حافظه. برچسب‌ها: `[established] / [emerging] / [speculative]`. هرجا بعد از knowledge-cutoff است، `uncertain` علامت خورده و راهِ verify داده شده.

---

## Summary

۱. **حقیقتِ ناخوشایند اول:** طبق جمع‌بندی خودت، گلوگاهِ binding دیتای cold-start لجر است، نه زیرساخت. پس قوی‌ترین توصیه این است که *فعلاً تقریباً هیچ لایه‌ی مشترکی نساز* — این تحقیق را به‌عنوان نقشه‌ی «چه‌وقت چه‌چیزی» بخوان، نه مجوزِ ساختن. (بخش If-I'm-wrong این را کامل باز می‌کند.)
۲. اگر ساختی، **بالاترین ROI یک چیز است: یک chokepointِ واحد به‌شکل MCP gateway/proxy** که *همه‌ی* tool/data-accessِ همه‌ی tenantها از آن رد شود. cap + kill switch + audit-log اجباری‌ات به‌طور طبیعی همان‌جا می‌نشیند، چون هر action با پیامد از همان نقطه عبور می‌کند. `[established]` که این معماریِ chokepoint الگوی غالبِ ۲۰۲۶ است.
۳. **durability را با DBOS (روی Postgres یا حتی SQLite) بگیر، نه Temporal.** یک library در همان process، بدون زیرساختِ جدید — دقیقاً مناسبِ یک‌نفره/یک‌باکس. `[established]`
۴. **isolation را دو تکه کن:** contentionِ منابع (noisy-neighbor) با cgroups v2/systemd slices حل می‌شود (رایگان، توی خودِ لینوکس)؛ isolationِ امنیتیِ کدِ untrusted فقط اگر واقعاً کدِ تولیدشده اجرا می‌کنی — و آن‌وقت gVisor یا E2B، نه Firecracker روی VPS اجاره‌ای. `[established]`
۵. **anti-lock-in را روی دو استاندارد قفل کن:** MCP برای tools و OpenTelemetry برای observability. این دو، لایه‌ی «هر لحظه می‌توانی backend/model را عوض کنی» را می‌سازند. `[established]` برای MCP به‌عنوان استاندارد، `[emerging]` برای اسپکِ ۲۰۲۶-۰۷-۲۸.

---

## Landscape

شش لایه‌ی مشترک را جدا می‌کنم؛ هر لایه با نام‌های غالبِ ۲۰۲۵–۲۰۲۶، تاریخ، و «چه مشکلی را حل می‌کند».

**۱) Agent framework layer — نحوه‌ی coordinationِ agentها/stepها.** `[established]` فضای frameworkها از اوایل ۲۰۲۵ منفجر شد: **OpenAI Agents SDK** (مارس ۲۰۲۵؛ رویکردِ عمداً مینیمال — «agent = model + tools + loop»، MCP-native)، **Google ADK** (آوریل ۲۰۲۵، GCP-native)، **LangGraph** (graph-based با checkpointed state؛ در دلِ بازسازیِ اکتبر ۲۰۲۵ لانگ‌چین که یک orchestration-runtime و یک deployment-platform زیرش نام‌گذاری شد)، **Microsoft Agent Framework** (به GA 1.0 رسید ~آوریل ۲۰۲۶، ادغامِ AutoGen + Semantic Kernel)، **CrewAI** (role-based، ذهنی‌مدلِ ساده ولی سنگین‌ترین token-footprint روی taskهای ساده)، و **Anthropic Agent SDK** (کنارِ Claude، ۲۰۲۵–۲۰۲۶ — تاریخِ دقیق `uncertain`؛ verify از changelogِ Anthropic). مشکلی که حل می‌کنند: الگوی coordination (sequential / graph / handoff / group-chat). نکته‌ی مهم برای lane تو: framework تصمیم می‌گیرد agentها *چطور* کار را رد و بدل کنند، ولی *governance/access/cost* را حل نمی‌کند — آن، لایه‌ی زیرساختِ بالای framework است.

**۲) Durable-execution / runtime layer — زنده‌ماندنِ workflowهای طولانی از میانِ crash.** `[established]` کلِ دسته‌ی durable-execution در ۲۰۲۵ حول agentها repositionشد. **Temporal** دسته را تعریف کرد (بالغ، در مقیاسِ بزرگ جنگ‌آزموده؛ ولی یک cluster/سرویسِ جدا لازم دارد). **DBOS** (رویکردِ رادیکالی ساده: هم دیتای اپ هم state اجرا را در Postgres یا SQLite نگه می‌دارد، کاملاً in-process به‌عنوان library، صفر زیرساختِ جدید؛ آوریل ۲۰۲۶ با Go SDK و پارتنریِ Databricks Lakebase بحثِ «Postgres کافی است» را جدی‌تر کرد). **Restate** (سبک‌تر برای edge/serverless)، **Inngest** (stepهای قابلِ retry با primitiveهای AI)، **Cloudflare Workflows** (GA ۲۰۲۵، روزها/هفته‌ها اجرا). ورودهای بزرگ‌تر: **AWS Lambda Durable Functions** (دسامبر ۲۰۲۵) و **Microsoft Durable Task for AI agents** (آوریل ۲۰۲۶). مشکل: agent که ۱۰ فراخوان LLM را زنجیر می‌کند باید بعد از crash *دقیقاً از همان‌جا* ادامه دهد.

**۳) Isolation / sandbox layer — مهارِ کدِ untrusted و contentionِ منابع.** `[established]` اجماعِ فوریه‌ی ۲۰۲۶ صریح است: Docker/runc برای کدِ تولیدشده‌ی LLM کافی نیست. چهار primitive: containerهای معمولی (سریع، ضعیف)، **gVisor** (رهگیریِ syscall در user-space، سربارِ I/O حدود ۱۰–۳۰٪، بدون نیاز به KVM)، **Firecracker/Kata microVM** (isolationِ سخت‌افزاری، بوت ~۱۲۵–۲۰۰ms، قوی‌ترین مرز — ولی به KVM/nested-virt نیاز دارد)، و **WASM** (سربارِ نزدیکِ صفر، capability-first). ارائه‌دهنده‌ها: **E2B** (پرمصرف‌ترین، مبتنی بر Firecracker، sub-200ms، قابلِ self-host)، **Daytona** (سردترین بوتِ بازار sub-90ms، پیش‌فرض Docker)، **Northflank** (Kata+gVisor)، و **Google Agent Sandbox** (KubeCon NA ۲۰۲۵، پروژه‌ی CNCF زیرِ Kubernetes — ولی K8s لازم دارد). مشکل: کدِ تولیدشده نباید به host فرار کند و پروژه‌ها نباید منابعِ هم را بخورند.

**۴) MCP interop + gateway layer — دسترسیِ استاندارد و قابلِ‌حکمرانی به tools/data.** `[established]` **MCP** (استانداردِ باز، Anthropic نوامبر ۲۰۲۴، «USB-C برای AI») به‌سرعت استانداردِ agent-to-tool شد؛ اسپکِ جدید **۲۰۲۶-۰۷-۲۸** (فعلاً Release Candidate، نهایی ۲۸ ژوئیه) `[emerging]`: هسته‌ی stateless روی HTTP معمولی، افزونه‌های MCP Apps و Tasks (کارِ طولانی)، authorizationِ هم‌ترازِ OAuth/OIDC، و انتشارِ W3C Trace Context برای traceهای توزیع‌شده. `uncertain` تا ۲۸ ژوئیه — verify از blog.modelcontextprotocol.io. **MCP gateway** = control-plane بینِ agentها و MCP serverها: registry (سرورهای approve-شده)، authN/authZ، routing، policy-enforcement، observability (log کردنِ هر tool-call)، tool-permissions، PII-masking. گزینه‌های OSS خودمیزبان: **IBM Context Forge** (federate کردنِ MCP/A2A/REST/gRPC در یک endpoint، OTel، PyPI/Docker؛ ولی latency حدود ۱۰۰–۳۰۰ms و بدون پشتیبانیِ تجاری) و **Obot**. تفکیکِ مهم: Registry (کشف/allowlist) ≠ Gateway (routing، معمولاً یک service-account) ≠ Runtime (per-user OAuth، vaulted secrets، auditِ ساخت‌یافته). مشکل: بدون یک نقطه‌ی مرکزی، هر tenant اتصالِ شکننده و ناامنِ خودش را می‌سازد.

**۵) Governance / control-plane layer — cap، kill switch، audit، approval.** `[established]` این دقیقاً همان چیزی است که اکثر سازمان‌ها *ندارند*: «governance-containment gap» — حدود ۵۸–۵۹٪ monitoring/oversight دارند ولی فقط ۳۷–۴۰٪ containmentِ واقعی (purpose-binding + kill-switch). الگوی مرجعِ ۲۰۲۶ («Agent Control Plane»، ژوئن ۲۰۲۶) پنج جزءِ مهندسی‌شده دارد: OAuth-scoped service accounts، deterministic semantic router، **Open Policy Agent (OPA)** gates، **WORM audit log**، و kill-switchِ *تست‌شده* — با شعارِ «مدل قابلِ‌تعویض است؛ این‌ها نه». دو اصلِ عملیاتی: (الف) agentها را با **permission** طبقه‌بندی کن نه با هوش (نردبانِ خودمختاری L0–L4؛ L5 بدونِ checkpoint نباید در production وجود داشته باشد)؛ (ب) HITL را انتخابی کن — نه هر action (که گلوگاه می‌سازد و تنها human را غرق می‌کند)، فقط actionهای پرریسک. رگولاتوری (خارج از lane، یک‌خطی): EU AI Act ماده‌ی ۱۴ (نظارتِ انسانی، اجرای کاملِ ۲ اوت ۲۰۲۶) و راهنمای Five Eyes ۲۰۲۶.

**۶) Observability layer — ردیابیِ اجرای غیرقطعیِ چندمرحله‌ای + شواهدِ audit.** `[established]` **OpenTelemetry / OpenLLMetry (Traceloop)** = instrumentationِ vendor-neutral و «امن‌ترین انتخاب برای portability»، چون Langfuse/Phoenix/Laminar/LangSmith همه spanهای OTel را می‌بلعند. backendها: **Langfuse** (هسته‌ی MIT از ژوئن ۲۰۲۵، self-host با Postgres+ClickHouse+Redis+S3؛ رایگانِ کامل در OSS)، **Arize Phoenix** (OSS، خوب در مقیاسِ ۱۰M+ event)، **Laminar** (Apache-2.0، ساخته‌شده برای runهای طولانیِ agent)، **LangSmith** (seat-based، قفل به LangChain/LangGraph). مشکل: runِ یک agent که ۱۰ دقیقه طول می‌کشد و ۱۵ tool صدا می‌زند بدون trace = حدس‌زدن؛ و همین trace، همان WORM auditِ توست.

---

## Comparison table

> **جهتِ نمره‌دهی:** ۱۰ = بهترین برای *اپراتور تک‌نفره روی VPS مشترک*. Cost 10=ارزان‌ترین، Complexity 10=ساده‌ترین برای اجرا/نگهداری، Scalability 10=مقیاس‌پذیرترین، Maintainability 10=کم‌زحمت‌ترین، Security 10=قوی‌ترین مرز/تضمین در همان نقش، Maturity 10=پخته‌ترین/جنگ‌آزموده‌ترین. همه‌ی نمره‌ها **قضاوتِ جهت‌دار `[Probable]`‌اند، نه benchmark**.

| Choice (نقش) | Cost | Complexity | Scalability | Maintainability | Security | Maturity |
|---|---|---|---|---|---|---|
| **DBOS** (durable exec — library, PG/SQLite) | 9 | 9 | 6 | 9 | 6 | 6 |
| **Temporal** (durable exec — self-host cluster) | 5 | 3 | 10 | 4 | 7 | 9 |
| **cgroups v2 / systemd slices** (resource isolation) | 10 | 7 | 6 | 8 | 6* | 10 |
| **gVisor** (security isolation, untrusted code) | 9 | 6 | 7 | 7 | 8 | 8 |
| **Firecracker/Kata microVM** (hardware isolation) | 6 | 3 | 7 | 4 | 10 | 8 |
| **E2B** (managed sandbox) | 5 | 8 | 8 | 8 | 9 | 7 |
| **IBM Context Forge** (MCP gateway, self-host) | 8 | 5 | 7 | 5 | 7 | 6 |
| **Open Policy Agent (OPA)** (policy gate) | 9 | 6 | 8 | 7 | 8 | 9 |
| **Langfuse (self-host, MIT) + OTel** (observability) | 8 | 5 | 7 | 5 | 7 | 8 |
| **OpenAI Agents SDK** (framework, MCP-native) | 9 | 8 | 7 | 8 | 6† | 7 |
| **LangGraph** (framework, checkpointed graph) | 8 | 5 | 8 | 6 | 6† | 8 |

\* cgroups فقط contention/resource-limit را حل می‌کند؛ برای کدِ untrusted مرزِ امنیتی نیست.
† نمره‌ی Security برای frameworkها یعنی «چقدر خودش governance/isolation می‌دهد» — frameworkها ذاتاً این را نمی‌دهند؛ پس پایین. این وظیفه‌ی لایه‌ی gateway/OPA است.

---

## Blind spots

- **تله‌ی replay/determinism.** `[established]` فراخوان‌های LLM غیرقطعی‌اند؛ در durable-execution باید هرکدام را به‌شکلِ یک «activity» ژورنال‌شده wrap کنی که در replay دوباره اجرا نشود. رایج‌ترین جایی که تازه‌کارها می‌خورند زمین. اگر ننداختی توی activity، recoveryِ تو state را خراب می‌کند.
- **contention ≠ security.** `[Probable]` noisy-neighborِ CPU/RAM را cgroups حل می‌کند؛ فرارِ کدِ untrusted را فقط microVM/gVisor. قاتی‌کردنِ این دو → یا زیرساختِ over-buildشده می‌سازی یا یک حفره‌ی امنیتی. اول مشخص کن اصلاً کدِ untrusted اجرا می‌شود یا نه.
- **Firecracker روی VPS اجاره‌ای شاید اصلاً ممکن نباشد.** `[Probable / uncertain]` microVMها به KVM/nested-virtualization نیاز دارند؛ خیلی از VPSهای بودجه‌ای (OpenVZ/LXC یا nested-virt خاموش) این را نمی‌دهند. **verify:** `ls -la /dev/kvm` و `egrep -c '(vmx|svm)' /proc/cpuinfo` روی همان VPS. اگر KVM نبود، Firecracker منتفی است → gVisor یا E2B.
- **governance-containment gap.** `[established]` داشتنِ monitoring حسِ کاذبِ امنیت می‌دهد؛ آن‌چه معمولاً غایب است kill-switch و purpose-binding است (فقط ~۳۷–۴۰٪ دارند). تو این را در طراحی داری — ولی kill-switchِ *تست‌نشده* = kill-switچِ نداشته.
- **گلوگاهِ HITL و تک‌بودنِ reviewer.** `[established + solo-specific]` اگر هر action صفِ approval بخورد، agentها می‌ایستند و *تنها human (تو)* غرق می‌شود. باید actionها را با ریسک tier کنی. خطرِ خاصِ تو: تو نقطه‌ی شکستِ واحدِ approval هستی — اگر ۴۸ ساعت نباشی، سیستم یا می‌ایستد یا (بدتر) تو gate را شل می‌کنی.
- **چیزی که durable-execution حل نمی‌کند.** `[established]` hallucination، runaway loop، eval-drift، و disaster-recovery در سطحِ store. durability فقط crash-recovery است، نه درستیِ رفتار.
- **لایه‌ی tool یک سطحِ حمله است.** `[established]` prompt-injection و tool-poisoning *قبل از* اجرای هر کد. شواهدِ واقعی: n8n با CVE-2026-25049 (CVSS 10.0، sandbox-escape، دسامبر ۲۰۲۵)؛ و بحرانِ گزارش‌شده‌ی «OpenClaw» در اوایلِ ۲۰۲۶ با ۲۱٬۰۰۰+ نمونه‌ی افشاشده. برای MCP: manifestهای امضاشده و اجرای sandboxِ کامپوننت‌های third-party.
- **گیرافتادنِ glueِ orchestration داخلِ Claude Cowork.** `[Probable]` اگر منطقِ ارکستراسیون در چت/کانفیگِ Cowork زندگی کند، نه export-first است نه reproducible — مستقیماً ارزشِ خودت را نقض می‌کند. لایه‌ی مشترک باید در کد/کانفیگِ ownedِ تو (git) باشد؛ Cowork فقط یکی از driverها.
- **بارِ عملیاتیِ ClickHouse در self-hostِ Langfuse؛** و data-modelِ observation-firstِ آن برای traceهای طولانیِ agent ضعیف است (بدونِ transcript-view). `[established]`
- **بهینه‌سازی برای مقیاسی که نداری.** `[established]` سربارِ durability (۵–۲۰٪ در ۱۰۰k run/روز) و horizontal-scaling برای تو بی‌ربط است. Gartner: تا ۴۰٪ از پروژه‌های agentic ممکن است تا ۲۰۲۷ به‌خاطرِ هزینه/ارزشِ ناهم‌راستا کنسل شوند — meta-riskِ واقعی، ساختنِ زیرساخت برای agentهایی است که ارزش تحویل نمی‌دهند (دقیقاً همان cold-start-data که خودت گفتی).

---

## Recommendation

**بالاترین ROI برای تیمِ تک‌نفره روی VPS مشترک — حداقلِ قابلِ‌ساخت:**

۱. **یک chokepointِ واحد: MCP gateway/proxy** که *همه‌ی* tool/data-accessِ همه‌ی tenantها از آن رد شود. اینجا تنها جایی است که cap + kill-switch + audit به‌طور طبیعی می‌نشیند، چون هر actionِ باپیامد از همین‌جا عبور می‌کند. یا **IBM Context Forge** (اگر latency و opsش را تحمل می‌کنی) یا یک proxyِ نازکِ سفارشی. `[Probable]`
۲. **policy gate = Open Policy Agent (OPA)** — یا اگر OPA زیادی است، یک جدولِ ساده‌ی allowlist + risk-tier — که enforce کند: کدام tenant کدام tool را صدا بزند، capِ خرج/نرخ per-action، و کدام actionها approvalِ تو را لازم دارند. `[Probable]`
۳. **audit = همان append-only hash-chainِ خودت** با معنایِ WORM؛ هر تصمیمِ gateway + هر action را به آن بده. `[established pattern]`
۴. **kill switch = یک flagِ واحد** که gateway *قبل از هر action* چک می‌کند (سراسری + per-tenant)، و **تست‌شده**. `[established]`
۵. **durability = DBOS روی Postgres یا SQLite، نه Temporal.** in-process، صفر زیرساختِ جدید؛ هر فراخوانِ LLM/tool را در یک stepِ ژورنال‌شده wrap کن. `[Probable]`
۶. **isolationِ contention = cgroups v2 / systemd slices** per-tenant (سقفِ CPU/RAM/IO). توی خودِ لینوکس، رایگان. `[established]`
۷. **isolationِ امنیتی = فقط اگر tenantی کدِ تولیدشده اجرا می‌کند.** آن‌وقت gVisor (user-space، بی‌نیاز از KVM) یا offload به E2B. **Firecracker را روی VPS اجاره‌ای self-host نکن.** اگر هیچ tenantی کدِ untrusted اجرا نمی‌کند، این لایه را کاملاً حذف کن. `[Probable]`
۸. **observability = instrumentationِ OpenTelemetry** (portable) → Langfuseِ self-host یا شروع روی رایگانِ ابریِ Langfuse (۵۰k unit/ماه) و self-host بعداً. OTel لنگرِ ضدِ lock-in است. `[Probable]`
۹. **interop = MCP همه‌جا** برای tools (استانداردِ no-lock-in و زبانِ Cowork). فعلاً به اسپکِ پایدارِ **2025-11-25** بچسب؛ 2026-07-28 را `[emerging]` بدان (نهایی ۲۸ ژوئیه). `[established/emerging]`
۱۰. **framework:** اگر ارکستراسیونِ کد-محور فراتر از Cowork لازم شد، **OpenAI Agents SDK** (مینیمال، MCP-native) یا **LangGraph** (اگر graphِ checkpointed لازم داری). احتمالاً به هیچ frameworkِ سنگینی نیاز نداری — Cowork + MCP + gateway شاید کافی باشد. `[Probable]`

**glueِ ارکستراسیون را از چتِ Cowork بیرون بکش و در کد/گیتِ ownedِ خودت بگذار** تا export-first و reproducible شود؛ Cowork می‌شود یک driver، نه system-of-record.

### دقیقاً چه چیزی را **نساز** (پرچمِ over-engineering)

- ❌ **Kubernetes / Google Agent Sandbox / هرچیزِ k8s-محور.** opsِ عظیم برای یک باکس، یک نفر.
- ❌ **clusterِ Temporal.** نسبت به DBOS برای مقیاسِ تو over-engineered؛ فقط اگر واقعاً به cross-service orchestration خوردی.
- ❌ **self-hostِ Firecracker/Kata روی VPS اجاره‌ای.** احتمالاً ممکن نیست (nested-virt نداری) و اگر کدِ untrusted نیست، لازم هم نیست.
- ❌ **DSLِ سفارشیِ ارکستراسیون / message-busِ دست‌ساز / موتورِ event-sourcing.** Postgres/SQLite خسته‌کننده + DBOS پوشش می‌دهد.
- ❌ **MCP «Runtime»ِ کاملِ multi-user با per-user OAuth/OBO.** تو یک کاربری؛ gateway با یک service-account + auditِ تو کافی است.
- ❌ **role-templatingِ سنگینِ CrewAI روی taskهای سبک** (سنگین‌ترین token-footprint) — دقیقاً همان‌که Task Routerِ خودت حل می‌کند.
- ❌ **self-hostِ MCP Registryِ رسمی** (برای self-host طراحی نشده و maintainerها ساپورت نمی‌کنند)؛ allowlistِ استاتیک یا registryِ داخلیِ Context Forge کافی است.
- ❌ **backendِ observabilityِ خودت.** OTel + Langfuse هست.
- ❌ **بهینه‌سازیِ سربارِ durability / horizontal-scaling** برای ترافیکی که نداری.

**تک‌حرکتِ بالاترین ROI: همان MCP gateway به‌عنوانِ chokepointِ governance.** تنها تکه‌ی مهندسیِ مشترکی است که هر tenant ازش سود می‌برد و cap+killswitch+auditِ اجباری‌ات طبیعتاً همان‌جا زندگی می‌کند. بقیه یا توی خودِ لینوکس هست (cgroups) یا یک library نازک است (DBOS).

### TOOLING (pricing model + best alternative + vendor-lock-in ۱–۱۰، که ۱۰ = بدترین lock-in)

| Tool | Pricing model | Best alternative | Lock-in |
|---|---|---|---|
| **DBOS** | OSS library رایگانِ self-host؛ DBOS Cloud مصرف‌محور (`verify` license/pricingِ فعلی) | Restate / Temporal | **3** — پشتِ interface بگذاری، شعاعِ مهاجرت یک ماژول است |
| **Temporal** | OSS (self-host رایگان)؛ Temporal Cloud مصرف‌محور | DBOS / Restate | **5** — کد workflow-shape است |
| **IBM Context Forge** | OSS رایگانِ self-host (PyPI/Docker)؛ بدون ساپورتِ تجاری (`verify` license) | Obot / proxyِ سفارشی | **2** — OSS + MCP استاندارد؛ ولی opsش مالِ توست |
| **Open Policy Agent** | OSS (Apache-2.0، CNCF)، رایگان | Cerbos / جدولِ قوانینِ دستی | **2** — Rego نسبتاً portable |
| **Langfuse** | MIT core رایگانِ self-host؛ ابری $0/50k، $29، $199، $2,499 + overage $8/100k | Arize Phoenix / Laminar | **2** — MIT + ingestِ OTel |
| **OpenTelemetry / OpenLLMetry** | OSS (Apache-2.0)، رایگان، vendor-neutral | — (خودش لنگرِ ضدِ lock-in است) | **1** |
| **E2B** | core قابلِ self-host + hostedِ مصرف‌محور (per-second) (`verify` pricing) | Daytona / gVisorِ self-host | **4** — API میزبان؛ ولی راهِ فرارِ OSS دارد |
| **gVisor** | OSS (Apache-2.0، Google)، رایگان | Kata/Firecracker (نیازمندِ KVM) | **1** |
| **OpenAI Agents SDK** | OSS (MIT)، رایگان (هزینه‌ی model API جدا) | LangGraph / Google ADK / Anthropic Agent SDK | **3** — toolها via MCP portable |
| **LangGraph** | OSS (MIT)، رایگان؛ LangSmith/deployment پولی | OpenAI Agents SDK / کدِ ساده + durable-exec | **4** — کدِ graph + schemaِ checkpointer |
| **MCP (standard)** | استانداردِ باز، بی‌هزینه‌ی license | — (هدف همین است) | **1** — ولی اتکا به سرورهای مرجعِ Anthropic/رفتارِ خاصِ Cowork، lock-in را بالا می‌برد |

---

## If-I'm-wrong

**قوی‌ترین ضدِ توصیه‌ی من:** خودِ *فرض* که الان باید لایه‌ی مشترک بسازی احتمالاً غلط است. طبق جمع‌بندیِ خودت، constraintِ binding دیتای cold-start لجر است. هر ساعت روی gateway، ساعتی است که صرفِ تولیدِ رکوردهای لجری نشده که تصمیم‌هایت را واقعاً gate می‌کنند. **ضدِ توصیه‌ی حداکثری:** الان *تقریباً هیچ* مهندسیِ مشترکی نساز — هر tenant را به‌شکلِ یک جریانِ منزویِ Cowork+MCP اجرا کن، با یک approvalِ per-action خیلی ساده + یک فایلِ auditِ تخت، و **gateway را نساز تا وقتی ≥N actionِ واقعی/روز روی ≥۲ tenant داشته باشی که ثابت کند chokepoint هزینه‌اش را برمی‌گرداند.** خودِ gateway می‌تواند premature-optimization باشد. `[Probable]` — این با گلوگاهِ اعلامیِ خودت هم‌راستاست.

**ضدِ توصیه‌ی دوم:** اگر هر tenantی قرار است کدِ untrusted/تولیدشده را در حجم اجرا کند (backtestِ کوانت/ماینینگ، code-execِ تحقیق)، آن‌وقت «isolation را رها کن، cgroups کافی است» *خطرناک* غلط است — از روزِ اول به sandboxِ واقعی (gVisor/E2B) نیاز داری، و CVEهای n8n/OpenClaw هزینه‌ی اشتباه را نشان می‌دهند. توصیه‌ی من فقط اگر درست است که agentهایت کدِ دلخواه اجرا **نمی‌کنند**.

**ضدِ توصیه‌ی سوم:** شرطِ DBOS-به‌جای-Temporal فرض می‌کند single-box می‌مانی. اگر contentionِ VPS زودتر از انتظار مجبورت کند tenantها را روی چند ماشین بشکنی، آرزو می‌کنی از اول Temporal/Restate رفته بودی. **کاهش‌دهنده:** durability را پشتِ یک interface (یک ماژول) فاکتور کن تا شعاعِ مهاجرت کوچک بماند — منابع هم دقیقاً همین را توصیه می‌کنند.

---

## Confidence

**Medium.** لَند‌سکیپِ frameworkها/toolها خوب مستند و به‌روز است (منابعِ متعددِ فوریه–ژوئنِ ۲۰۲۶)، ولی: (الف) انتخابِ بهینه به فاکت‌هایی که ندارم وابسته است — اینکه tenantهایت کدِ untrusted اجرا می‌کنند یا نه، پشتیبانیِ virtualizationِ دقیقِ VPSت، و حجمِ واقعیِ action؛ (ب) جدیدترین تکه‌ها (اسپکِ MCP ۲۰۲۶-۰۷-۲۸، بعضی نسخه‌ها) RC/emerging و بعد از cutoffِ من‌اند، فقط با search تأیید شده‌اند؛ (پ) نمره‌های جدولِ مقایسه قضاوتِ جهت‌دارند نه benchmark. پس: بالا روی «MCP استانداردِ interop است» و «governance-containment gap واقعی است»، پایین‌تر روی نمره‌های خاصِ toolها.

---

## Claims table

| Claim | Evidence | Confidence (H/M/L) | Source + date |
|---|---|---|---|
| MCP استانداردِ غالبِ agent-to-tool است؛ Anthropic نوامبر ۲۰۲۴ معرفی کرد | «USB-C for AI»؛ پذیرش در Claude/Cursor/VS Code/ChatGPT | H | webfuse MCP cheat-sheet, 2026-04 |
| اسپکِ MCP 2026-07-28 (stateless HTTP، MCP Apps، Tasks، OAuth/OIDC، W3C Trace Context) فعلاً RC است، نهایی ۲۸ ژوئیه | پستِ رسمیِ بلاگِ MCP | M (`uncertain` تا نهایی‌شدن) | blog.modelcontextprotocol.io, RC 2026-07 |
| MCP Registryِ رسمی برای self-host طراحی نشده؛ maintainerها ساپورت نمی‌کنند | مستنداتِ رسمی | H | modelcontextprotocol.io/registry/about |
| IBM Context Forge یک gateway/registry/proxyِ OSS است که MCP/A2A/REST/gRPC را federate می‌کند، با OTel؛ latency ~۱۰۰–۳۰۰ms، بدون ساپورتِ تجاری | GitHub + مرور | M (`verify` license/latencyِ فعلی) | github.com/IBM/mcp-context-forge؛ mcpmanager 2026-04 |
| gateway بدونِ per-user permission در معرضِ prompt-injection و شکستِ audit است؛ secrets باید بیرونِ context window و auditِ OTel به identity گره بخورد | تاکسونومیِ Registry/Gateway/Runtime | M | arcade.dev, 2026-04 |
| durable-execution در ۲۰۲۵ حول agentها repositionشد (Temporal, Restate, Inngest, Trigger.dev, DBOS) | «sandbox orchestration لایه‌ی گم‌شده است» (Temporal, ۷ مه ۲۰۲۶) | H | golem.cloud, ~2026-06؛ temporal.io 2026-05 |
| DBOS دیتا و state اجرا را در Postgres/SQLite نگه می‌دارد، in-process/library، صفر زیرساخت؛ Go SDK + Databricks Lakebase آوریل ۲۰۲۶ | «Postgres is enough» | H | tiarebalbi.com, 2026-05؛ zylos.ai 2026-02 |
| فراخوان‌های LLM غیرقطعی‌اند و باید در durable-replay به‌شکلِ activityِ ژورنال‌شده wrap شوند؛ رایج‌ترین اشتباهِ تازه‌کارها | قراردادِ replay-safety | H | zylos.ai 2026-02؛ appscale.blog 2026-06 |
| durability این‌ها را حل نمی‌کند: hallucination، runaway loop، eval-drift، store-level DR؛ سربار ۵–۲۰٪ در ۱۰۰k/روز؛ HITL-signal هزینه‌ی idle را ۶۰–۸۰٪ کم می‌کند | معماریِ مرجع | M | appscale.blog, 2026-06 |
| برای کدِ untrusted، Docker/runc کافی نیست؛ چهار primitive: container/gVisor/Firecracker(Kata)/WASM؛ Firecracker بوت ~۱۲۵–۲۰۰ms، gVisor سربارِ I/O ~۱۰–۳۰٪ | اجماعِ فوریه ۲۰۲۶ | H | northflank؛ zylos.ai 2026-04؛ manveerc 2026-02 |
| E2B پرمصرف‌ترین sandbox، مبتنی بر Firecracker، sub-200ms، قابلِ self-host؛ Daytona sub-90ms | مرورِ ارائه‌دهنده‌ها | H | firecrawl.dev 2026-03؛ spheron 2026-04 |
| Google Agent Sandbox در KubeCon NA ۲۰۲۵ (CNCF/K8s SIG)، ولی Kubernetes لازم دارد | معرفیِ پروژه | M | manveerc 2026-02؛ zylos.ai 2026-04 |
| n8n CVE-2026-25049 (CVSS 10.0، sandbox-escape، دسامبر ۲۰۲۵)؛ بحرانِ گزارش‌شده‌ی «OpenClaw» با ۲۱٬۰۰۰+ نمونه‌ی افشاشده اوایل ۲۰۲۶ | نمونه‌های production | M (OpenClaw تک‌منبع، `verify`) | zylos.ai, 2026-04 |
| governance-containment gap: ~۵۸–۵۹٪ oversight ولی فقط ~۳۷–۴۰٪ containment (purpose-binding/kill-switch)؛ audit-trail قوی‌ترین پیش‌بینِ بلوغ | گزارش‌های صنعتی | M | MintMCP 2026-01؛ Kiteworks 2026-03 |
| الگوی «Agent Control Plane»: OAuth-scoped accounts + deterministic router + OPA gates + WORM audit + kill-switchِ تست‌شده؛ طبقه‌بندی با permission نه هوش؛ OSWorld سقفِ ~۶۶.۳٪ | بلوپرینتِ بانکی | M (`emerging` best-practice) | sebastienrousseau.com, 2026-06 |
| HITL باید انتخابی باشد نه روی هر action (وگرنه گلوگاه/غرقِ reviewer) | راهنمای enforcement | H | prefactor 2026-04؛ rasa 2026-05 |
| OpenLLMetry/OTel امن‌ترین انتخابِ instrumentation برای portability است (Langfuse/Phoenix/Laminar/LangSmith همه ingest می‌کنند) | مقایسه‌ی observability | H | laminar.sh, 2026-04 |
| Langfuse هسته‌ی MIT (ژوئن ۲۰۲۵)، self-host با PG+ClickHouse+Redis+S3؛ ابری $0/50k، $29، $199، $2,499 + $8/100k؛ ClickHouse بارِ opsِ واقعی | teardownِ pricing | H | dev.to 2026-05؛ cekura 2026-03؛ langfuse.com |
| Microsoft Agent Framework به GA 1.0 رسید ~آوریل ۲۰۲۶ (ادغامِ AutoGen + Semantic Kernel)؛ OpenAI Agents SDK مارس ۲۰۲۵؛ Google ADK آوریل ۲۰۲۵ | لَند‌سکیپِ framework | H | rasa 2026-05؛ langchain 2026-06؛ gurusup 2026-05 |
| Gartner: تا ۴۰٪ اپ‌های enterprise تا ۲۰۲۶ agentِ task-specific دارند (از <۵٪ در ۲۰۲۵)؛ تا ۴۰٪ پروژه‌های agentic ممکن است تا ۲۰۲۷ کنسل شوند | نقلِ Gartner در چند منبع | M | truefoundry 2026-06؛ agentmarketcap 2026-04 |
| EU AI Act ماده‌ی ۱۴ نظارتِ انسانی می‌خواهد؛ اجرای کامل ۲ اوت ۲۰۲۶ | چارچوبِ رگولاتوری | H | strata.io 2026-05؛ medium 2026-04 |

---

*فایل: `05-research-shared-engineering-lane.md` — شماره را با کنوانسیونِ فایلینگِ خودت تنظیم کن. آماده‌ی merge با خروجیِ سایرِ laneها طبقِ همین ۸ سرفصلِ ثابت.*
