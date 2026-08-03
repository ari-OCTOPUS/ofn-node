# RESEARCH LANE — Memory architecture
# معماری memory برای عامل‌های long-running و چند-پروژه‌ای

> **DOMAIN:** سیستم‌های multi-agent خودمیزبان برای اپراتور تک‌نفره.
> **LANE (قفل‌شده):** فقط معماری memory برای عامل‌های long-running و چند-پروژه‌ای — نه framework، نه orchestration، نه RAG عمومی.
> **CONSTRAINTS:** یک VPS مشترک + لپ‌تاپ؛ تک‌نفره، operable/maintainable؛ export-first، no vendor lock-in؛ per-action cap + kill switch + audit log غیرقابل‌حذف.
> **تاریخِ ساخت:** ۲۰۲۶-۰۷-۰۱. منابع از web search زنده. برچسب: `[established] / [emerging] / [speculative]`. هرجا بعد از knowledge-cutoff → `uncertain` + راهِ verify.

---

## Summary

۱. **حقیقتِ ناخوشایند اول:** اکثر دموهای agent-memory اشتباهِ بنیادین دارند: «memory = vector DB». برای agentهای long-running، بنچمارک‌های مستقلِ ۲۰۲۶ نشان می‌دهد سیستم‌های multi-strategy روی Postgres از سیستم‌های vector-first بالاتر می‌زنند — Hindsight: 91.4٪ در برابر Mem0: 49.0٪ روی LongMemEval. `[established]`

۲. **برای تیمِ تک‌نفره روی VPS مشترک: ساده‌ترین stackِ ۸۰٪:** همان Postgres که داری + pgvector + Mem0 OSS (Apache 2.0). project_id را به‌عنوان user_id بگذار تا ایزولاسیون بین tenantها بدهی. هیچ سرویسِ جدایی لازم نیست. `[Probable]`

۳. **زمانِ نیاز به graph:** فقط اگر factهایت *در طول زمان تغییر می‌کنند* (مثل: قیمتِ دارایی، وضعیتِ پروژه، سرمایه‌گذاریِ فعال). آن‌وقت Graphiti (Apache 2.0) + FalkorDB یا pgvectorِ خودت با temporal‌indexing. Zep Cloud = vendor lock-in، Community Edition دیپرکیت شده. `[established]`

۴. **ایزولاسیونِ memory بین پروژه‌ها پیش‌فرض نیست.** هیچ frameworkِ معروفی به‌طور built-in isolation اجبار نمی‌کند — مسئولیتِ اپلیکیشن‌لایه است. user_id/project_id scoping + schema-level separation = تنها راهِ عملی. `[established]`

۵. **مدیریتِ context overflow:** یک cascade سه‌مرحله‌ای: (۱) compress/truncate tool-output اول، (۲) sliding window برای تاریخِ مکالمه، (۳) LLM summarization فقط به‌عنوانِ آخرین راه‌حل — سنگین‌ترین و گران‌ترین است. `[established]`

---

## Landscape

**۱) تاکسونومیِ استاندارد: چهار نوعِ memory.** `[established]` ریشه در CoALA (Cognitive Architectures for Language Agents، Princeton/CMU، arXiv:2309.02427) که مدل‌هایِ بزرگ مثل Letta، Mem0، و LangChain از آن به‌عنوانِ پایه استفاده کردند. در ۲۰۲۵–۲۰۲۶، اجماعِ صنعتی روی چهار نوع ثابت شد:

- **Working memory (in-context):** همان context-window. هر چه الان در پنجره است. سریع‌ترین، گران‌ترین (توکن)، ناپایدار.
- **Episodic memory:** لاگِ تعاملاتِ خاص — «چه اتفاقی افتاد در session قبلی». time-bound، instance-specific. backend: معمولاً یک DB با جستجوی متنی + تاریخ.
- **Semantic memory:** factهای انتزاعی و abstractشده — ترجیحات، دانشِ domain، entityها. atemporal (نمایندهٔ «حالِ حاضر»). backend: vector store یا knowledge graph.
- **Procedural memory:** مهارت‌ها، workflow، دستورالعمل‌های آموخته‌شده که agent می‌داند «چطور» کار کند — در ۲۰۲۶ شاملِ agents که system-promptِ خود را بازنویسی می‌کنند (LangMem). `[emerging]`

پیپرِ دسامبر ۲۰۲۵ «Memory in the Age of AI Agents» (arXiv:2512.13564) این taxonomy را ناکافی دانست و یک تاکسونومیِ تجدیدنظرشده پیشنهاد داد (Factual / Experiential / Working). در عمل، همچنان مدلِ سه/چهارتایی بیشتر در production استفاده می‌شود. `[emerging]`

---

**۲) سه الگوی غالبِ production در ۲۰۲۶.** `[established]`

**(A) Vector-first extraction (Mem0):** رایج‌ترین الگو. agent turn → extraction pipeline (LLM استخراج factها) → vector embedding → ذخیره در vector store → retrieval semantic. سریع برای deploy، ولی temporal reasoning ضعیف (fact قدیمی و جدید هر دو در store می‌مانند). Mem0 بزرگ‌ترین community دارد (~۴۸k stars، funding $24M در اکتبر ۲۰۲۵).

**(B) Graph-native temporal (Zep/Graphiti):** هر fact یک validity-window دارد (`valid_at`/`invalid_at`). وقتی fact تغییر می‌کند، قدیمی invalidate می‌شود (نه حذف). retrieval: vector + full-text + graph traversal در یک call. قوی‌ترین temporal reasoning؛ ولی Zep Community Edition از آوریل ۲۰۲۵ دیپرکیت شده (feature retirementهای بیشتر فوریه ۲۰۲۶) — self-host الان یعنی Graphiti (Apache 2.0) + یک graph DB (Neo4j/FalkorDB/Kuzu) که بار عملیاتیِ واقعی است.

**(C) OS-style tiered (Letta / MemGPT):** agent خودش memory را مدیریت می‌کند (مثلِ OS): Core memory = RAM (همیشه in-context)، Recall memory = DB تعاملات (قابلِ جستجو، out-of-context by default)، Archival memory = long-term semantic (agent به‌صورتِ ابزار دسترسی می‌زند). Letta کاملاً self-hostable است ولی framework lock-in دارد — agentها باید داخلِ Letta runtime اجرا شوند. مناسبِ agentهایی که ساعت‌ها یا روزها بدون توقف اجرا می‌شوند.

**(D) Local-first verbatim (MemPalace — emerging):** جدیدترین breakout (v3.4.0، ۶ ژوئن ۲۰۲۶، ~54.1k GitHub stars، MIT). به‌جای extraction/summarization، ذخیره‌ی verbatim؛ retrieval با hybrid (semantic + BM25 + entity matching). ادعا: 96.6٪ R@5 روی LongMemEval با zero API call. `[emerging / uncertain]` — verify با اجرای evals روی workloadِ خودت، چون vendor-reported scores با هم تضاد دارند.

**(E) Declarative memory injection (CLAUDE.md / AGENTS.md):** `[established, underrated]` ساده‌ترین روشِ procedural memory که اکثر بررسی‌ها نادیده می‌گیرند. یک فایلِ markdown که agent در هر session می‌خواند — قانون‌ها، context، style. هیچ DB، هیچ embedding، هیچ سرویسی لازم ندارد. بنچمارکِ مستقلِ Letta نشان داد یک plain filesystem 74٪ روی memory taskها می‌زند و بعضی vector-store libraryهای تخصصی را شکست می‌دهد.

**(F) Multi-strategy روی Postgres (Hindsight / emerging pattern):** `[emerging]` تمامِ retrieval modes (semantic، keyword، entity matching، graph edges) روی یک Postgres با pgvector + graph tables + temporal indexes. یک container، یک backup. Hindsight با همین معماری 91.4٪ روی LongMemEval گزارش می‌دهد در برابرِ 49.0٪ Mem0 — ولی این vendor-self-reported است؛ `uncertain` تا اجرای مستقل.

---

**۳) مدیریتِ context overflow وقتی >۲۰۰k توکن.** `[established]`

بهترین سیستم‌های production یک cascade سه‌لایه استفاده می‌کنند — به‌ترتیبِ اولویت:
1. **compress tool-output اول:** خروجیِ ابزارها معمولاً طولانی‌ترین بخشِ context‌اند. قبل از افزودن به context آن‌ها را truncate/compress کن.
2. **sliding window برای تاریخ:** پیام‌های قدیمی‌تر را truncate کن (نه حذف از DB).
3. **LLM summarization به‌عنوانِ آخرین راه‌حل:** گران‌ترین (یک call اضافه) ولی کیفیت بالاتر از truncate. تنها وقتی دو روشِ قبلی کافی نبودند.

«سیستم هرگز نباید crash کند یا response خالی بدهد وقتی به context limit می‌رسد.» `[established]`

**پیامدِ مستقیم برای پروژه‌ی multi-project:** هر tenant memory scopeِ جداگانه دارد = overflow هر پروژه مستقل است. خطرِ cross-contamination زمانی است که یک agent نتواند ببیند «کجا» هست.

---

**۴) ایزولاسیونِ memory در محیطِ multi-project/multi-tenant.** `[established]`

پیپرِ MemTrust (arXiv:2601.07004) به‌طور صریح نوشته که سیستم‌های فعلیِ memory «systematic security deficiencies» دارند: PII leakage، insufficient tenant isolation، memory-decision opaque، و پیاده‌سازیِ ناهمخوانِ «right-to-be-forgotten». به‌طورِ خاص: «Zep's graph structures may allow cross-tenant inference through shared entities، and Mem0's proprietary implementations leave tenant isolation mechanisms unverified.»

**راه‌حلِ عملی (تک‌نفره روی VPS مشترک):**
- user_id = project_name برای scoping کلِ memory reads/writes
- schema-level separation در Postgres (هر project یک schema جدا)
- metadata filtering (`{"project": "mining"}`) در queries
- هیچ shared-entity در knowledge graph بین پروژه‌ها (خطرِ cross-inference)

---

## Comparison table

> **جهتِ نمره:** ۱۰ = بهترین برای تک‌نفره/VPS مشترک/export-first. برچسب‌ها `[Probable]` جز جایی که explicit benchmark داریم.

| Solution (نقش) | Cost | Complexity | Scalability | Maintainability | Isolation | Maturity |
|---|---|---|---|---|---|---|
| **pgvector (Postgres extension)** | 10 | 9 | 7 | 9 | 8* | 10 |
| **Mem0 OSS + pgvector** (self-host, Apache 2.0) | 9 | 7 | 7 | 7 | 7† | 7 |
| **Mem0 OSS + Qdrant** (self-host) | 8 | 5 | 8 | 6 | 7† | 7 |
| **LangMem** (MIT, LangGraph-native) | 10 | 7 | 6 | 7 | 6† | 6 |
| **Letta / MemGPT** (self-host, Apache 2.0) | 7 | 4 | 6 | 5 | 7 | 7 |
| **Graphiti OSS** + FalkorDB (self-host, Apache 2.0) | 7 | 3 | 6 | 4 | 6† | 6 |
| **Zep Cloud** (managed SaaS) | 4 | 8 | 9 | 9 | 8 | 7 |
| **MemPalace** (MIT, local-first) | 10 | 7 | 5 | 7 | 7† | 4‡ |
| **Chroma (embedded mode)** (Apache 2.0) | 10 | 9 | 4 | 8 | 5 | 7 |
| **Qdrant standalone** (Apache 2.0) | 8 | 6 | 9 | 6 | 7 | 8 |
| **CLAUDE.md / AGENTS.md** (declarative) | 10 | 10 | 3 | 9 | 10 | 9 |

\* isolation با schema-per-project در Postgres — نیازِ کدنویسی دارد ولی قابلِ اجرا.
† isolation application-layer — هر کدام به scoping صریح (user_id/project_id) نیاز دارند؛ پیش‌فرض isolation اجبار نمی‌کند.
‡ MemPalace v3.4.0 جدید است (ژوئن ۲۰۲۶)، هنوز battle-tested نیست.

---

## Blind spots

- **«Memory = vector DB» یک خطای پیش‌فرض است.** `[established]` برای low-to-medium volume agent memory، یک سرویسِ vector DB جدا اغلب ارزشِ عملیاتی‌اش را ندارد. latency یک hop شبکه‌ای به managed vector DB (100–400ms) در loop agent بدتر از 3ms جستجوی local pgvector است.

- **Zep Community Edition دیگر وجود ندارد.** `[established]` دیپرکیت از آوریل ۲۰۲۵، feature retirementهای بیشتر فوریه ۲۰۲۶. self-host الان = Graphiti + Neo4j/FalkorDB/Kuzu = سه سرویس جدا + بارِ عملیاتیِ واقعی. این در بسیاری از مقایسه‌ها ذکر نمی‌شود.

- **Benchmark disputeها جدی‌اند.** `[established]` Zep ادعای 84٪ روی LoCoMo کرد؛ Mem0 این را به 58.44٪ تصحیح کرد (allegation: adversarial category inclusion errors)؛ Zep 75.14٪ counter-claim کرد. vendor-reported scores را بدون اجرای eval روی workloadِ خودت باور نکن.

- **Letta framework lock-in.** `[established]` استفاده از tiered memory مدلِ Letta یعنی agentها باید داخل Letta runtime اجرا شوند. خروج بعداً گران است. اگر Cowork را می‌خواهی نگه داری، Letta نمی‌چسبد.

- **تضادِ fact در Mem0 base.** `[established]` Mem0 پایه (بدون graph) fact قدیمی و جدید را هر دو نگه می‌دارد. اگر آدرسِ سرمایه‌گذاری تغییر کند، ممکن است fact قدیمی با semantic query بالاتر score بزند. گرفتن این مشکل بدونِ Mem0g (Pro, $249/ماه) یا Graphiti ممکن نیست.

- **Consolidation pipeline خودکار نیست در Letta.** `[established]` Letta agentها خودشان باید تصمیم بگیرند چه موقع از Recall به Archival منتقل کنند — یعنی بیشتر deploymentها این را پیاده نمی‌کنند و Recall memory بی‌نهایت رشد می‌کند.

- **CLAUDE.md به‌عنوانِ روشِ procedural memory دست‌کم گرفته می‌شود.** `[established]` بنچمارکِ مستقلِ Letta نشان داد یک plain filesystem 74٪ روی memory taskها می‌زند. برای پروژه‌هایی که قوانین و context ثابت دارند، این کافی است و هیچ سرویسِ اضافه‌ای نمی‌خواهد.

- **داده‌ی از دست رفته در extraction pipeline.** `[Probable]` همه‌ی frameworkها در extraction از مکالمه fact استخراج می‌کنند؛ این عمداً اطلاعات را از دست می‌دهد (خلاصه‌سازی = از دست دادن نویانس). برای tenantِ «دفترچه‌ی شخصی» که باید verbatim retrieval داشته باشد، MemPalace یا یک episodic log ساده مناسب‌تر است.

- **هزینه‌ی extraction LLM در write path.** `[established]` هر turn در Mem0/Zep یک call اضافه به LLM (برای استخراجِ fact) ایجاد می‌کند. در ترافیکِ بالا می‌چرخد، ولی برای multi-project تک‌نفره با volume کم، این هزینه ناچیز است — تا زمانی که از API مدلِ گران استفاده کنی.

- **Right-to-be-forgotten ناهمخوان است.** `[established]` GDPR/right-to-delete در اکثر frameworkها کامل پیاده نشده. اگر projectهای تجاری داری، این یک حفره‌ی compliance است. pgvector + Mem0 + schema-per-project بهترین کنترل را می‌دهد.

- **MemPalace جدید است.** `[uncertain]` 54.1k stars جذاب است ولی v3.4.0 ژوئن ۲۰۲۶ هنوز در edge cases آزمایش‌نشده است. برای production financial data (ماینینگ/سرمایه‌گذاری)، صبر تا v4 یا داشتنِ یک fallback عاقلانه است.

---

## Recommendation

**بالاترین ROI برای تک‌نفره روی VPS مشترک — سه مرحله:**

### مرحله‌ی ۱ (الان): همانِ Postgres + pgvector + Mem0 OSS

- Postgres که DBOS/LANGAR رویش نشسته → extension pgvector را فعال کن → Mem0 را self-host کن (Docker، Apache 2.0، هیچ چیزِ جدیدی نمی‌خواهد).
- **ایزولاسیون:** `user_id = "project_mining"` / `user_id = "project_accounting"` / ... — هر خواندن/نوشتن scoped است.
- **declarative memory:** یک `CLAUDE.md` (یا معادلِ آن) per-project برای قوانینِ ثابت — هیچ embedding، هیچ سرویس، هیچ هزینه.
- **export:** Mem0 یک CRUD API دارد؛ backup = همان Postgres dump که همیشه داری. ۱۰۰٪ export-first.
- **context overflow:** cascade سه‌لایه (compress tool-output → sliding window → LLM summarization) پیاده کن. اجازه نده سیستم crash کند.
- `[Probable]` — این برای ۸۰٪ ارزشِ memory با کمترین بارِ عملیاتی کافی است.

### مرحله‌ی ۲ (وقتی temporal reasoning لازم شد): Graphiti + FalkorDB

- اگر و فقط اگر: factهایی داری که در طول زمان تغییر می‌کنند و از «چه چیزی الان درست است» باید جواب دقیق بدهی (مثلاً: قیمتِ سرمایه‌گذاری، وضعیتِ پروژه، یک lead که تبدیل به customer شده).
- FalkorDB به‌جای Neo4j: سبک‌تر، Redis-compatible، self-host راحت‌تر. `[Probable]` — ولی `uncertain`، verify با ops مقایسه‌ای.
- Graphiti Apache 2.0 است — data ownership داری.

### مرحله‌ی ۳ (فقط اگر agentهایت روزها بدون توقف اجرا می‌شوند): Letta

- برای agentهایی که ساعت‌ها یا روزها autonomous اجرا می‌کنند و باید context window خود را مدیریت کنند.
- هزینه: framework lock-in. آگاهانه انتخاب کن.

### دقیقاً چه چیزی را **نساز** (پرچمِ over-engineering)

- ❌ **Qdrant یا Chroma به‌عنوانِ سرویسِ جدا** — تا زمانی که روی pgvector هستی و >50M vector نداری.
- ❌ **Zep Community Edition** — دیگر وجود ندارد.
- ❌ **Zep Cloud** — vendor lock-in و SaaS بیرونی. مخالفِ export-first.
- ❌ **Neo4j برای self-host** — سنگین، پیچیده؛ FalkorDB یا pgvectorِ خودت را ترجیح بده.
- ❌ **Letta برای همه‌ی projectها** — framework lock-in + over-engineered برای projectهایی که session-based‌اند.
- ❌ **extraction pipeline برای همه‌ی memory** — برای دفترچه‌ی شخصی و log تحقیق، episodic verbatim بهتر است.
- ❌ **یک memory stack مشترک برای همه‌ی tenantها** — خطرِ cross-project leakage مستقیم.
- ❌ **MemPalace در production مالی (هنوز)** — v3.4.0 ژوئن ۲۰۲۶، battle-tested نیست.
- ❌ **summarization به‌عنوانِ اولین واکنش به overflow** — compress و sliding window اول.

---

## TOOLING

| Tool | Pricing model | Best alternative | Lock-in (۱–۱۰) |
|---|---|---|---|
| **pgvector** (Postgres extension) | رایگان/OSS (PostgreSQL license) | Qdrant اگر pgvector کافی نباشد | **1** — خودِ Postgres |
| **Mem0 OSS** (server) | Apache 2.0 self-host رایگان؛ Cloud: Free/10k req، Starter $19، Pro $249 (با graph)، Enterprise | MemPalace / LangMem | **3** — API خودشون ولی export کامل |
| **Graphiti** | Apache 2.0 OSS رایگان؛ Zep Cloud: Flex $25/20k credits، Plus $475/300k credits | pgvector + temporal indexingِ دستی | **2** — OSS ولی graph DB وابستگی دارد |
| **Letta / MemGPT** | Apache 2.0 self-host رایگان؛ Cloud managed (`verify` pricing) | Mem0 + agentِ سبک‌تر | **5** — framework lock-in |
| **LangMem** | MIT OSS رایگان | Mem0 | **4** — نیازِ LangGraph |
| **MemPalace** | MIT OSS رایگان؛ 29 MCP tools | Mem0 / episodic log ساده | **1** — MIT + local |
| **Qdrant** | Apache 2.0 self-host رایگان؛ Cloud free-tier + managed | pgvector / Weaviate | **2** — format portable |
| **Chroma** | Apache 2.0 (embedded رایگان) | pgvector | **2** — local file |
| **FalkorDB** | BSL 1.1 / Community OSS (`verify` license) | Neo4j / pgvector + graph tables | **3** (`verify` license) |
| **Neo4j** | Community OSS محدود؛ Enterprise پولی | FalkorDB / Kuzu | **6** — Enterprise lockَin |
| **Zep Cloud** | Credit-based SaaS ($25–$475/ماه) | Graphiti + FalkorDB self-host | **8** — داده بیرون از VPS |

---

## If-I'm-wrong

**قوی‌ترین ضدِ توصیه‌ی اصلی (pgvector + Mem0):** اگر ماینینگ/سرمایه‌گذاری واقعاً temporal-heavy باشد — یعنی agentهایت باید بدانند «قیمتِ BTC در زمانِ تصمیمِ من چقدر بود» یا «این دارایی کِی خریداری شد و به کِی فروخته شد» — آن‌وقت Mem0 base نه‌تنها ناکافی بلکه *گمراه‌کننده* است. یک temporal knowledge graph (Graphiti) از روزِ اول بهتر است، حتی با بارِ عملیاتیِ بیشترش.

**ضدِ توصیه‌ی دوم:** اگر «export-first» را مطلق بگیری و بنچمارکِ Hindsight (91.4٪ multi-strategy روی Postgres) را جدی بدانی، ممکن است بخواهی از اول یک Hindsight-like architecture بسازی (Postgres + graph tables + temporal indexes + app-layer retrieval). این بدونِ vendor وابستگی است و بالاترین recall را می‌دهد — ولی هزینه‌ی ساختش (نه خریدنش) بالاست. اگر Hindsight یا MemPalace mature شوند، ممکن است این ماهیانه بهترین انتخاب باشد؛ الان زودتر از موعد است.

**ضدِ توصیه‌ی سوم:** بنچمارکِ مشهورِ Letta نشان داد filesystem ساده 74٪ می‌زند. اگر این را جدی بگیری، ممکن است نتیجه بگیری که هیچ memory framework خاصی لازم نیست — فقط یک دایرکتوریِ ساختاریافته از فایل‌های markdown (per-project) + یک جستجوی full-text روی Postgres. این نه over-engineered است نه vendor lock-in دارد. پاسخِ من: این برای procedural/declarative memory درست است، ولی برای episodic و semantic که پویا تغییر می‌کنند، نیازِ به extraction pipeline واقعی است.

---

## Confidence

**Medium.** landscape تثبیت‌شده است (CoALA، Mem0، Letta، Graphiti همه مستند‌اند)؛ ولی: (الف) بنچمارک‌ها vendor-reported هستند و با هم تضاد دارند — تنها run روی workloadِ خودت اعتماد می‌سازد؛ (ب) MemPalace جدید است (`emerging`)؛ (پ) وضعیتِ Zep CE deprecation و FalkorDB licensing را `verify` کن — این‌ها ممکن است تغییر کرده باشند؛ (ت) Letta runtime-locking را قبل از commit تست کن.

---

## Claims table

| claim | evidence | confidence (H/M/L) | source + date |
|---|---|---|---|
| اجماعِ صنعت ۲۰۲۵–۲۰۲۶ روی سه/چهار نوعِ memory: working، episodic، semantic، procedural | CoALA (arXiv:2309.02427)؛ zylos.ai survey | H | zylos.ai 2026-04؛ atlan.com 2026-04 |
| Mem0 بزرگ‌ترین community: ~48k stars، $24M funding (اکتبر ۲۰۲۵) | گزارشِ funding و stars | H | agenticwire.news 2026-06؛ mem0.ai 2026-06 |
| MemPalace v3.4.0 (ژوئن ۲۰۲۶)، ~54.1k stars، 96.6٪ R@5 روی LongMemEval، zero API calls، MIT | vendor-reported (`uncertain` تا verify مستقل) | M | rohitraj.tech 2026-06 |
| Zep Community Edition دیپرکیت از آوریل ۲۰۲۵، feature retirement بیشترِ فوریه ۲۰۲۶؛ self-host = Graphiti + graph DB | مستنداتِ Zep و مرور مستقل | H | vectorize.io 2026-03؛ atlan.com 2026-04 |
| بنچمارکِ LongMemEval: Mem0 49.0٪، Zep 63.8٪، Hindsight 91.4٪ (vendor-reported) | اعداد از فروشندگان — با هم تضاد دارند | M | atlan.com 2026-04؛ hindsight 2026-05 (تضاد: verify با Zep counter-claim) |
| Zep ادعای 84٪ روی LoCoMo؛ Mem0 تصحیح به 58.44٪؛ Zep counter: 75.14٪ — dispute حل‌نشده | GitHub: getzep/zep-papers/issues/5 | H (dispute واقعی است) | atlan.com 2026-04 |
| Letta: agent خودش context را مدیریت می‌کند (core/recall/archival)؛ کاملاً self-hostable؛ framework lock-in | مستنداتِ Letta | H | jobsbyculture 2026-06؛ rohitraj.tech 2026-06 |
| LangMem MIT OSS، LangGraph-native، procedural memory (agent system-prompt خود را بازنویسی می‌کند) | مستنداتِ LangChain | H | atlan.com 2026-04 |
| بنچمارکِ Letta: plain filesystem 74٪ روی memory tasks و بعضی vector-library‌ها را شکست می‌دهد | Letta-published benchmark | M (vendor-reported) | gist.github.com |
| multi-strategy روی Postgres (Hindsight) از vector-primary در accuracy بالاتر می‌زند | architecture + benchmark argument | M (`uncertain` تا verify مستقل) | hindsight.vectorize.io 2026-05 |
| MemTrust: سیستم‌های فعلیِ memory systematic security deficiencies دارند؛ tenant isolation by default نیست | arXiv:2601.07004 | H | arxiv.org/pdf/2601.07004 |
| برای <50M vector، pgvector کافی است و dedicated vector DB را توجیه نمی‌کند | توافقِ مستقل در چند بررسی | H | layerbase.com 2026-05؛ hindsight.vectorize.io 2026-05 |
| Mem0 + pgvector: self-host با Docker، Apache 2.0، بدون نیاز به سرویسِ جدا | مستنداتِ Mem0 | H | mem0.ai؛ railway.com 2026-04 |
| Mem0 base (non-graph) temporal conflict ضعیف دارد؛ graph-enhanced (Mem0g) فقط Pro ($249/ماه) | مقایسه‌ی مستقل | H | vectorize.io 2026-03؛ atlan.com 2026-04 |
| Graphiti Apache 2.0، ~27k stars ژوئن ۲۰۲۶، MCP Server v1.0 نوامبر ۲۰۲۵، Neo4j/FalkorDB/Kuzu | GitHub گزارش | H | github.com/getzep/graphiti؛ agenticwire.news 2026-06 |
| cascade context management: compress tool-output → sliding window → LLM summarization (آخرین راه‌حل) | best-practice مستقل | H | medium.com 2026-01 |
| استخراجِ fact در write-path هر turn یک LLM call اضافه دارد | معماریِ Mem0/Zep | H | spheron.network 2026-04 |
| Cloudflare Agent Memory: private beta آوریل ۲۰۲۶، export-committed ولی closed-source (`uncertain`) | گزارشِ مستقل | M | fountaincity.tech 2026-05 |
| MemPalace MIT، 29 MCP tools، backends: ChromaDB/SQLite/Qdrant/pgvector، local models via Ollama | vendor page | M (جدید، `verify` production readiness) | rohitraj.tech 2026-06؛ callsphere.ai 2026-06 |
| Mem0 cloud: Free/10k req، Starter $19، Pro $249، Enterprise — Pro برای graph | مستنداتِ Mem0 | H (`verify` همین — ممکن است تغییر کرده باشد) | callsphere.ai 2026-06 |

---

*فایل: `06-research-memory-architecture.md` — آماده‌ی merge با سایرِ laneها با همین ۸ سرفصلِ ثابت.*
