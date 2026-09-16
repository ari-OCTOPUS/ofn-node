---
type: research
status: draft
tags: [research, agent-orchestration, durable-execution, checkpointing, recovery, saga, build-loop, propose-only]
created: 2026-07-05
updated: 2026-07-05
sources: "[[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]], [[BUILD-BACKLOG]], [[04 - Architect System/architect/04-Docs/AUTONOMOUS-RUN-2026-07-05|AUTONOMOUS-RUN]], [[_memory/EXPERIENCE-LEDGER|ledger]]"
---

# digestِ تحقیق — Agent-Orchestration: durable execution / checkpointing / recovery (۲۰۲۶) + پیشنهادِ P-08

> **این چیست؟** اولین خروجیِ **حالتِ تحقیقِ پیوستهٔ** حلقهٔ خودکارِ `build-planner-loop` (صفِ کار در آیتمِ ۷ تمام شد). موضوعِ این چرخه = **agent-orchestration patterns**، ولی با **زاویهٔ تازه** نسبت به آیتمِ ۵: آنجا *توپولوژی* (supervisor/mesh/token-economics) پوشش داده شد؛ اینجا **بُعدِ بقای اجرا** — durable execution، checkpointing، replay/idempotency، و saga/self-healing. این زاویه عمداً انتخاب شد چون مستقیماً روی دردِ مستندِ همین vault می‌نشیند: **حفرهٔ bootstrap / reset‌های مکرر** ([[_memory/EXPERIENCE-LEDGER|ledger]]).
>
> یک digestِ منبع‌دار → نگاشت به [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] (تأیید/گپ) → یک خطِ **Cross-domain** → **یک پیشنهادِ عملیِ اتصال به پلن (P-08)** به‌صورتِ diffِ قبل→بعد. **هیچ‌چیز اعمال نشد؛ spec دست‌نخورده؛ منتظرِ verdictِ آری.**
>
> **Problem / Goal / Constraints / Risks (طبقِ قاعده):** Problem = fleet روی زمان‌بندِ OS و «اپ باید باز باشد» اجرا می‌شود؛ وقتی session/اپ می‌میرد، **همهٔ تسک‌ها هم‌زمان می‌میرند** و چیزی durable نمی‌ماند که ناوگان را restart کند (حفرهٔ bootstrap، ۳+ بار در یک روز). Goal = نامیدنِ این گپ با واژگانِ استانداردِ ۲۰۲۶ و بستنِ امنِ آن + آماده‌سازیِ idempotency پیش از هر auto-effect. Constraints = propose-only، AU$30/ماه، تک‌میزبانِ لوکالِ Windows. Risk = biomimicry/theory-drift → مهار با نگاشتِ صریح به بخش‌های spec + منبعِ هر ادعا.

---

## ۱. یافته‌های کلیدی (۵ محور، هرکدام منبع‌دار)

### محور ۱ — Durable Execution: الگوی هستهٔ «harnessing» در ۲۰۲۶
- الگوی مشترکِ همهٔ پلتفرم‌های durable-execution: کد state خود را در **checkpointهای تعریف‌شده** بیرونی persist می‌کند و پس از هر شکست از آخرین checkpoint **resume** می‌شود — نه restart از صفر. [1][2]
- چرا برای ایجنت‌ها بحرانی است: ایجنت‌ها چند نقطهٔ شکست دارند (ارکستراسیون، رفتارِ احتمالاتیِ LLM، tool-call، human-in-the-loop) که **retryِ سنتی از پسِ آن‌ها برنمی‌آید**؛ durable execution = persistِ خودکارِ state + retryِ خودکار + resumeِ workflow. روندِ نام‌گذاری‌شدهٔ ۲۰۲۶ = **«AI Agent Harnessing»**. [1][2]
- حرکتِ پلتفرم‌ها (آوریلِ ۲۰۲۶): **OpenAI Agents SDK** → externalized state + snapshotting + rehydration به کانتینرِ تازه؛ **Microsoft Durable Task for AI agents** → زیرساختِ checkpointing/coordination؛ + Temporal، DBOS، Inngest، LangGraph به‌عنوان runtimeهای durable. [1][2]

### محور ۲ — تاکسونومیِ «۷ الگوی بازیابی» + نردبانِ recovery
- الگوهای بازیابیِ multi-agent در ۲۰۲۶ در یک فهرستِ صریح جمع‌بندی شده: **retries · circuit breakers · validation gates · sagas · checkpoints · budget guardrails · human escalation.** [3]
- نردبانِ کاملِ recovery (به‌ترتیب): طبقه‌بندیِ شکست → retry با backoff+jitter → tripِ circuit-breaker → fallbackِ باوقار → **checkpoint & resume** → escalateِ تمیز → **یادگیری از هر خطا** (نوشتنِ درس به حافظه). [3][4]
- self-healing به‌عنوان قابلیتِ محصولی ظاهر شده: تشخیصِ خودکارِ حادثه + **restartِ خودترمیمِ ماشین** بدونِ دخالتِ انسانی (نمونه‌های enterprise). [4]

### محور ۳ — «Checkpoint ≠ Durable Execution» (تمایزِ تیز و پرخطر)
- snapshotِ state بین nodeها (LangGraph checkpointer و مشابه) **کافی نیست**؛ یک **journalِ durable** باید تصمیم بگیرد چه چیزی می‌تواند replay/skip/compensate/resume شود. checkpoint = «state کجاست»؛ durable execution = «چه‌طور امن جلو/عقب می‌رویم». [5]
- در production، `InMemorySaver` **restart-durable نیست** (با مرگِ process/کانتینر می‌پرد)؛ باید checkpointerِ ماندگار (DB/external) باشد. گذار از prototype به production = عوض‌کردنِ checkpointer. [6][7]
- الگوی interrupt/resumeِ HITL: تابعِ `interrupt` اجرا را **pause** و state را ذخیره می‌کند؛ resume «دقیقاً از همان‌جا» ادامه می‌دهد، نه replayِ کامل — **مشروط به وجودِ checkpointerِ durable + thread-id.** [6][5]

### محور ۴ — replay / idempotency / non-determinism (footقِ پنهان)
- ورک‌فلوهای ایجنتی پر از **non-determinism**اند: خروجیِ LLM، timestamp، رندم، نتایجِ retrieval، پاسخِ شبکه، تصمیمِ policy. هر عملیاتِ non-deterministic و هر side-effect باید داخلِ یک **task/step** wrap شود تا replay نتیجهٔ **ثبت‌شده** را بازاستفاده کند، نه اجرای دوباره. [8][9]
- **الزامِ idempotency:** «یک branch-push، تماسِ پرداخت، ارسالِ ایمیل، آپدیتِ تیکت، یا نوشتنِ DB می‌تواند تکرار شود و دنیا را **دوبار** عوض کند.» retry فقط وقتی امن است که عملیات **idempotent** باشد یا نتیجهٔ ثبت‌شده‌ای برای بازاستفاده باشد → تضمینِ **exactly-once**. [8][10]
- «ریسکِ پنهانِ replay»: خودِ durable-execution می‌تواند اگر side-effectها به‌درستی recorded/idempotent نباشند، تو را بسوزاند (اجرای دوبارهٔ همان side-effect حین replay). [10]

### محور ۵ — Saga / compensation + خودترمیمی
- استانداردِ ورک‌فلوهای پیچیده = **Saga Orchestration**: برای هر nodeِ رو‌به‌جلو یک **nodeِ جبرانیِ** رو‌به‌عقب map کن؛ در شکستِ جبران‌ناپذیر، ارکستریتور **زنجیرهٔ جبران را به ترتیبِ معکوس** اجرا می‌کند و workspace را تمیز می‌کند + لاگِ تشخیصیِ تمیز می‌نویسد. [11][12]
- Saga = شکستنِ تراکنشِ توزیع‌شده به تراکنش‌های محلی، هرکدام با یک actionِ جبرانی برای rollback. [11][13]
- لایهٔ self-healing: وقتی pipeline خراب/ناسازگار شد، **rollback به آخرین snapshotِ سازگار** — با **reverse-replayِ write-ahead-log** یا عملیاتِ جبرانی. [12]

---

## ۲. نگاشت به ستون (تأیید / گپ) — grounded، نه تزئینی

**الف) ممیزیِ «۷ الگوی بازیابی» [3] روی این سیستم:**

| الگوی بازیابی (۷گانهٔ ۲۰۲۶) | اندامِ معادل در این vault | حکم |
|---|---|---|
| retries (backoff+jitter) | — (غیررسمی؛ در spec نیست) | ⚠️ گپ |
| circuit breakers | §۲ سِپتا/bulkhead میان دامنه‌ها [J] | ✅ طراحی‌شده (پیاده‌سازی 🟡) |
| validation gates | Doctor + validators + rubric ≥۱۲/۱۶ (§۵/§۹) | ✅ قوی |
| sagas (compensation) | §۵ فلشِ `ROLLBACK/REVERT` — ولی بدونِ زنجیرهٔ جبرانِ per-step | ⚠️ نیمه |
| **checkpoints (durable)** | — (زمان‌بندِ OS، «اپ باید باز باشد») | 🔴 **گپِ بزرگ = حفرهٔ bootstrap** |
| budget guardrails | §۶ budget guard AU$30 + alert ۵۰/۸۰٪ | ✅ |
| human escalation | verdict gate (کلِ طراحیِ propose-only) | ✅ قوی |

> **نتیجه:** سیستم **۴.۵ از ۷** الگو را دارد (۳ کامل + septa/saga نیمه). گمشدهٔ اصلی و پرخطر = **durable checkpoint** و **saga-compensationِ صریح**.

**ب) نگاشتِ مفهومیِ سایر یافته‌ها:**

| یافته | بخشِ spec | حکم |
|---|---|---|
| durable execution = resume نه restart | §۲ «خودترمیمیِ بی‌امان» [J] · §۵ | ⚠️ **گپ** — self-heal هست ولی substrateِ durable نیست |
| checkpoint ≠ durable execution | §۲ bootstrap-watchdog | ⚠️ **تأییدِ گپ** — RATIFIED-TASKS متن را نگه می‌دارد، ولی journalِ اجرا نیست |
| exactly-once / idempotent side-effect | §۳ EffectorGate · Anchor Ledger | 🔶 **پیش‌شرطِ بحرانی** — گیت permit می‌گیرد ولی idempotency-key ندارد |
| saga: هر forward یک compensating | §۵ ماشینِ `PROPOSE→…→PROMOTE` | ⚠️ ماشین هست، ستونِ جبرانِ per-step نیست |
| WAL-checkpoint + reverse-replay rollback | §۴ M5 (backup) · §۶ memory | 🔶 M5 نزدیک است ولی **at-rest** است نه **in-flight** (پایین) |
| «learn from every error» = درس به حافظه | §۷ Reflexion (LOG به ledger) | ✅ **تأییدِ مستقل** — حلقهٔ §۷ دقیقاً همین است |

**ج) گروندینگِ کلیدی — چرا این محور دقیقاً دردِ همین vault است:**
- **حفرهٔ bootstrap ابزارِ آکادمیک نیست؛ مستند است:** [[01 - Dashboard/HANDOFF|HANDOFF]] هشدار می‌دهد تسک‌ها فقط وقتی **اپ باز است** اجرا می‌شوند؛ [[_memory/EXPERIENCE-LEDGER|ledger]] «reset دوم/سوم» را در یک روز ثبت کرده (کلِ ناوگان صفر شد → هیچ تسکی برای خودترمیمیِ §۳.۳ نماند). مهارِ فعلی = **RATIFIED-TASKS** (متنِ پرامپت داخلِ vault) + آشتیِ شروعِ جلسه (لنگرِ HANDOFF). این عملاً یک **جایگزینِ دستی و انسان‌محورِ durable-execution** است — ولی **بدونِ journal/checkpointِ خودکار.** ۲۰۲۶ این گپ را دقیقاً «durable execution» می‌نامد [1][5].
- **حلقهٔ propose-only خودش سطحِ idempotency دارد:** هر اجرا یک نوتِ `NN-<slug>-DATE` + یک ردیفِ ledger + یک خطِ log می‌نویسد. [[_memory/EXPERIENCE-LEDGER|ledger]] **قبلاً** یک «اجرای جبرانی پس از بیداریِ host» را ثبت کرده — پس replay در همین سیستم **فرضی نیست، رخ داده.** نام‌گذاریِ `NN-<slug>-DATE` + قاعدهٔ «یک آیتم، آخرش بایست» یک **گاردِ idempotencyِ ad-hoc** است [8][10].

---

## ۳. Cross-domain

> مرزِ **exactly-once / idempotency** مستقیماً به **Crypto** (اندامِ ۳ — تنها نامزدِ *bounded-auto SELL*؛ یک SELLِ retry/replay-شدهٔ غیرِ idempotent می‌تواند تریدِ دوباره بزند = همان footقِ «payment call تکرارشده» [8][10]) و **Lead-نقاشی** (اندامِ ۲ — نوشتنِ pipeline/weekly-report؛ replay = دوباره‌ارسال/دوباره‌ثبت) وصل می‌شود. اندامِ افقیِ مسئولِ هر دو = **EffectorGate + Anchor Ledger** (§۳): یک `idempotency_key`ِ واحد در گیت، exactly-once را **هم‌زمان** به هر دو دامنه می‌دهد — همان «یک رشته، چند node»یِ *Armillaria* [J]. (Project-F طبقِ قاعده ماسک؛ نوشتن‌های آن نیز مشمولِ همین گیت‌اند.)

---

## ۴. پیشنهادِ عملیِ اتصال به پلن (P-08) — «EffectorGate با idempotency-key + run-journalِ durable»

**چرا این یکی (نه بقیه):** بالاترین blast-radius برای سیستمی که (الف) fleet-اش روی زمان‌بندِ **غیرdurable** است (حفرهٔ bootstrapِ تکرارشونده) و (ب) قرار است روزی **auto-effect** بزند (سطحِ footقِ double-effect). یک مکانیزم (idempotency-key در گیت) + یک سند (run-journal) هر دو را می‌بندد. کم‌هزینه، برگشت‌پذیر، بدونِ فعال‌سازیِ کد.

**این diffها پیشنهاد‌اند — اعمال نشد. spec دست‌نخورده.**

### diff الف — §۳ (EffectorGate / Anchor Ledger): افزودنِ `idempotency_key`
- **قبل:** «EffectorGate = تنها دروازهٔ side-effect؛ هر `ToolGateway.call` قبل از اجرا permit می‌گیرد و مصرف می‌کند (fail-closed).»
- **بعد (افزوده):** «هر `ToolGateway.call` یک `idempotency_key` حمل می‌کند = هَشِ (intent + target + run-id). **Anchor Ledger پیش از finalize، جفتِ (key → result) را ثبت می‌کند؛ کلیدِ تکراری نتیجهٔ ثبت‌شده را برمی‌گرداند، نه اجرای دوباره** (exactly-once). این پیش‌شرطِ ایمنیِ **هر** auto-effectِ آینده است — به‌ویژه bounded-auto SELLِ Crypto و نوشتنِ pipelineِ Lead. مهارِ replay-double-effect [8][10].»

### diff ب — §۵ (Build/Test/Delete): ستونِ جبران (saga) + checkpointِ durable
- **قبل:** ماشینِ حالتِ `PROPOSE→DRY-RUN→VERDICT→APPLY(MOCK)→TEST→PROMOTE` با فلشِ `ROLLBACK/REVERT` و `STOP=fail-closed`.
- **بعد (افزوده):** «این ماشین یک **saga** است: برای هر گامِ رو‌به‌جلو یک **actionِ جبرانیِ** معکوس تعریف کن (`APPLY`→`revert-mv`، `PROMOTE`→`demote`)، و ترتیبِ جبران = **معکوسِ اجرا** [11]. + یک **run-journalِ سبک** (یک خطِ JSON per گذارِ حالت در `audit.jsonl`/Anchor Ledger) تا milestoneِ نیمه‌ساخته پس از قطعِ session **resume/rollbackِ قطعی** شود، نه restart از صفر [1][5]. **تبصرهٔ صریح:** run-journal آنالوگِ **durable-execution** و **مکملِ** M5 است، نه جایگزینش — **M5 وضعیتِ at-rest (مرگِ دیسک) را نگه می‌دارد؛ run-journal وضعیتِ in-flight (مرگِ session وسطِ اجرا) را.**»

### diffهایِ ثانویه (کاندیدا؛ این اجرا اعمال/بسته نشد)
- **§۲ — نامیدنِ اندامِ گمشده:** کنارِ «bootstrap-watchdog» یک ردیفِ **durable checkpoint / run-journal** [J→G] اضافه شود؛ چون خودترمیمیِ §۳.۳ فعلاً **دستی/تعاملی** است ([[_memory/EXPERIENCE-LEDGER|ledger]]: تنزل به propose-only چون L2/git-init پشتِ گیت) دقیقاً به‌خاطرِ نبودِ همین journal. **نامیدنِ گپ = گامِ اول.**
- **§۲ — ممیزیِ ۷گانه:** جدولِ «۴.۵/۷» بالا به‌عنوان یک self-assessmentِ استاندارد به spec افزوده شود (retries و durable-checkpoint و saga-compensation = بک‌لاگِ صریح).
- **§۶ Memory:** یک خط که ledgerِ append-only «durable substrate» است ولی **journalِ اجرا نیست** (state-of-data ≠ state-of-execution) — رفعِ ابهامِ رایج.

---

## ۵. Trade-off پیشنهادِ P-08 (نمرهٔ ۱–۱۰)

| بعد | نمره | توضیح |
|---|---|---|
| Cost | ۸ | متنِ spec + یک خطِ JSON per گذار؛ صفر هزینهٔ APIِ افزوده |
| Complexity | ۴ | یک idempotency-key + یک journalِ append؛ ستونِ saga سند است نه کدِ نو |
| Scalability | ۹ | با فعال‌سازیِ هر auto-effectِ حیاتی اهمیتش بیشتر می‌شود |
| Maintainability | ۸ | سند-محور، روی Anchor Ledgerِ **موجود** سوار می‌شود |
| Security | ۸ | double-effect (تریدِ/ارسالِ دوباره) و resume-از-وسطِ ناامن را می‌بندد |
| Time-to-Impl | ۷ | diff §۳/§۵ (verdict) + یک helperِ idempotency در گیت (کارِ Fable، MOCK) |

**ROI: بالا** — کم‌ترین هزینه، مستقیماً حفرهٔ bootstrap + footقِ double-effect را هدف می‌گیرد. هم‌راستا با §۵ (برگشت‌پذیری) و «در شک read-only» (§۰.۳).

---

## ۶. سؤالِ باز برای verdictِ آری
- diff الف/ب روی spec اعمال شود (نسخه → v0.2 طبقِ §۷)، یا فعلاً فقط به‌عنوانِ ریسک/بک‌لاگِ ثبت‌شده در §۱/§۲ بماند؟
- `idempotency_key` + run-journal **پیش‌نیازِ کدام milestone** شوند؟ پیشنهاد: **قبل از هر فعال‌سازیِ auto-effect (Crypto/Lead)**، یا به‌عنوان یک **M-نو** یا الحاق به **M2 (EffectorGate)** / **M6 (observability)**. — verdict.
- آیا M5 باید WAL-checkpointِ `langar.db` را با run-journal **یکی** کند یا **جدا**؟ (M5 = at-rest؛ journal = in-flight — پیشنهاد: جدا ولی هم‌مقصد.) — verdict.
- (میان‌بخشی، برای thread قبلی) این پیشنهاد با P-05 (مرزِ اعتماد/provenance) و P-06 (runbookِ چرخش) هم‌خانواده است؛ هر سه در یک بستهٔ v0.2 قابلِ همگرایی‌اند — به [[04 - Architect System/architect/03-Exports/build-proposals/07-review-packet-2026-07-05|REVIEW-PACKET]] اضافه شود؟

---

## Sources
- [1] [Durable Execution: The Key to Harnessing AI Agents in Production — Inngest](https://www.inngest.com/blog/durable-execution-key-to-harnessing-ai-agents) · [Durable Task for AI Agents — Microsoft Learn](https://learn.microsoft.com/en-us/azure/durable-task/sdks/durable-task-for-ai-agents)
- [2] [Durable Execution for AI Agent Runtimes: Checkpointing, Replay, and Recovery — Zylos Research](https://zylos.ai/research/2026-04-24-durable-execution-agent-runtimes/) · [Durable Execution for Crashproof AI Agents — DBOS](https://www.dbos.dev/blog/durable-execution-crashproof-ai-agents)
- [3] [Multi-Agent Error Recovery Patterns — Naitive](https://blog.naitive.cloud/error-recovery-multi-agent-systems-key-patterns/) · [AI Agent Orchestration Patterns 2026 — JobsByCulture](https://jobsbyculture.com/blog/ai-agent-orchestration-patterns-2026)
- [4] [AI Agent Error Handling & Self-Healing Patterns (2026) — Taskade](https://www.taskade.com/blog/ai-agent-error-recovery) · [Introducing WorkHQ (self-healing restarts) — SS&C Blue Prism](https://www.blueprism.com/resources/blog/introducing-workhq-automation-coordination/)
- [5] [Why Checkpoints Aren't Durable Execution — Diagrid](https://www.diagrid.io/blog/checkpoints-are-not-durable-execution-why-langgraph-crewai-google-adk-and-others-fall-short-for-production-agent-workflows) · [Interrupts — LangChain Docs](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [6] [Your LangGraph agent works. Now make the workflow durable — ZenML](https://www.zenml.io/blog/langgraph-durable-runtime) · [Build durable AI agents with LangGraph and Amazon DynamoDB — AWS](https://aws.amazon.com/blogs/database/build-durable-ai-agents-with-langgraph-and-amazon-dynamodb/)
- [7] [The best AI agent frameworks in 2026 — LangChain](https://www.langchain.com/resources/ai-agent-frameworks)
- [8] [Durable execution — LangChain Docs](https://docs.langchain.com/oss/python/langgraph/durable-execution) · [Demystifying Determinism in Durable Execution — Jack Vanlightly](https://jack-vanlightly.com/blog/2025/11/24/demystifying-determinism-in-durable-execution)
- [9] [Determinism during replay — AWS Durable Execution SDK Guide](https://docs.aws.amazon.com/durable-execution/patterns/best-practices/determinism/) · [Agent Workflows Are Rediscovering Durable Execution — Medium/Koshy](https://nittikkin.medium.com/agent-workflows-are-rediscovering-durable-execution-be110661ed8c)
- [10] [The Hidden Replay Risk in LangGraph: How "Durable Execution" Can Burn You — Medium/Parmar](https://medium.com/@mehul_parmar/the-hidden-replay-risk-in-langgraph-how-durable-execution-can-burn-you-1d966141e71a)
- [11] [Beyond Try/Except: Implementing the Saga Pattern in 2026 AI Agents — Medium/Ponnusamy](https://medium.com/@rahulponnusamy/beyond-try-except-implementing-the-saga-pattern-in-2026-ai-agents-92dcb7c0bf48) · [Mastering Saga Patterns — Temporal](https://temporal.io/blog/mastering-saga-patterns-for-distributed-transactions-in-microservices)
- [12] [Async AI Agent Workflows Survive Failures — Augment Code](https://www.augmentcode.com/guides/async-ai-agent-workflows)
- [13] [Pattern: Saga — microservices.io](https://microservices.io/patterns/data/saga.html)

> **پایان.** فقط-پیشنهاد. اتصالِ اجرا = اولین اجرای **حالتِ تحقیقِ پیوسته**، صفِ [[04 - Architect System/architect/04-Docs/AUTONOMOUS-RUN-2026-07-05|AUTONOMOUS-RUN]]. طبقِ §۷، اعمالِ diffها منتظرِ verdictِ آری است.
