---
type: research
status: draft
tags: [research, memory, rag, retrieval, consolidation, context-rot, build-loop, propose-only]
created: 2026-07-05
updated: 2026-07-05
sources: "[[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]], [[BUILD-BACKLOG]], [[00 - Inbox/AUTONOMOUS-RUN-2026-07-05|AUTONOMOUS-RUN]], [[_memory/EXPERIENCE-LEDGER|ledger]]"
---

# digestِ تحقیق — Memory / RAG systems (۲۰۲۶): انواعِ حافظه · بازیابیِ هیبرید · consolidation/forgetting · context-rot + پیشنهادِ P-09

> **این چیست؟** دومین خروجیِ **حالتِ تحقیقِ پیوستهٔ** حلقهٔ خودکارِ `build-planner-loop` (صفِ کار در آیتمِ ۷ تمام شد؛ آیتم۸ idle دست‌نخورده). موضوعِ این چرخه = **memory / RAG systems** — چرخه‌ای که هنوز به‌صورتِ standalone زده نشده. زاویه عمداً از دو نوتِ قبلی جدا انتخاب شده تا **dedup** رعایت شود:
> - نوتِ [[00 - Inbox/build-proposals/05-ai-agent-eng-2026-2026-07-05|05]] حافظه را فقط از دریچهٔ **حمله** دید (indirect injection از حافظهٔ مسموم).
> - نوتِ [[00 - Inbox/build-proposals/08-agent-orchestration-durability-2026-07-05|08]] حافظه را از دریچهٔ **بقایِ اجرا** دید (durable execution = state-of-**execution**).
> - **این نوت (۰۹)** حافظه را از دریچهٔ **کیفیتِ دانش و بازیابی** می‌بیند: انواعِ حافظه، مسیرِ retrieval، چرخهٔ عمر (نوشتن/consolidate/forget)، و افتِ context = state-of-**data** و state-of-**retrieval**. مرز تمیز است.
>
> یک digestِ منبع‌دار (۵ محور) → نگاشت به §۶ [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] (تأیید/گپ) → یک خطِ **Cross-domain** → **یک پیشنهادِ عملیِ اتصال به پلن (P-09)** به‌صورتِ diffِ قبل→بعد. **هیچ‌چیز اعمال نشد؛ spec دست‌نخورده؛ منتظرِ verdictِ آری.**
>
> **Problem / Goal / Constraints / Risks (طبقِ قاعده):** Problem = خودِ این vault یک **سیستمِ حافظه** است (ledgerِ append-only که رشدِ بی‌مرز دارد + digestهای تبخیرشونده + مسیرِ FTS5→وکتور)، ولی §۶ فقط یک مدلِ **دوزمانه**ی حداقلی دارد؛ نه consolidation روی لایهٔ durable، نه fusion/rerank در بازیابی، نه متریکِ کیفیتِ retrieval — و خودِ حلقهٔ orientation هر اجرا **کلِ ledger** را می‌بلعد (سطحِ زندهٔ context-rot). Goal = نامیدنِ این گپ‌ها با واژگانِ استانداردِ ۲۰۲۶ و بستنِ **کم‌هزینه و برگشت‌پذیرِ** آن‌ها. Constraints = propose-only · AU$30/ماه (D-25) · تک‌میزبانِ لوکالِ Windows · CHARTER/Property Schema حاکم. Risk = biomimicry/theory-drift → مهار با نگاشتِ صریح به بخش‌های spec + منبعِ هر ادعا + برچسبِ [G]/[J].

---

## ۱. یافته‌های کلیدی (۵ محور، هرکدام منبع‌دار)

### محور ۱ — تاکسونومیِ ۴گانهٔ حافظه + الگویِ tiered (استانداردِ production ۲۰۲۶)
- ایجنتِ production در ۲۰۲۶ چهار نوع حافظه دارد: **working** (context فعال، cacheِ کوتاه‌عمر، با پایانِ session تخلیه) · **episodic** (تاریخچهٔ زمان‌ایندکسِ رویدادها: چه شد، کِی، با چه نتیجه) · **semantic** (فکت‌ها/مفاهیم/روابط — اغلب knowledge-graph با اعتبارِ زمانی) · **procedural** (ورک‌فلوها و الگوهای ابزارِ آموخته‌شده که مؤثر بوده‌اند). [1][2]
- الگویِ غالبِ production = **tiered**: یک **هستهٔ کوچکِ همیشه-در-context** + یک **لایهٔ بازیابیِ vector-backed** + یک **سیاستِ صریحِ forgetting**. مدلِ لایه‌ایِ کامل از پایدارترین به فوری‌ترین: organizational (آنچه سازمان رسماً تعریف/governance کرده) → semantic → episodic → working. [1][3]
- نکتهٔ تیز: بیشترِ تیم‌ها فقط working + episodic دارند؛ **semantic و procedural** لایه‌های «فراموش‌شده»اند که تفاوتِ ایجنتِ «باهوش‌تر با تکرار» را می‌سازند. [2][4]

### محور ۲ — Agentic RAG: بازیابیِ هیبرید + fusion + rerank (بالاترین ROI)
- **«اول retrieval را درست کن، بعد agent را رویش بگذار.»** پرهزینه‌ترین اشتباهِ ۲۰۲۶ = رفتن به‌سراغِ ارکستراسیونِ ایجنتی پیش از سالم‌بودنِ retriever؛ ایجنتی که روی یک retrieverِ ضعیف loop می‌زند «فقط پولِ بیشتری خرج می‌کند تا **مفصّل‌تر اشتباه** کند». [5][6]
- **بازیابیِ هیبرید = baselineِ production**: dense (وکتور، معنا) و sparse (BM25/لغوی، نام/کد/اختصار/عددِ دقیق) را **موازی** بزن و با **RRF (Reciprocal Rank Fusion)** یا score-combinerِ آموخته fuse کن — هر دو mode شکست را هم‌زمان می‌پوشاند. [7][8]
- **Reranking = بالاترین‌ROI بهبود**: بعد از retrieveِ اولیه (top-۲۰/۵۰)، یک **cross-encoder** هر سند را با کوئری دوباره امتیاز می‌دهد → top-۵. الگوی رایج: هیبرید top-۵۰ → rerank به top-۵ → LLM، که کیفیتِ پاسخ را **~۱۵–۳۰٪ (RAGAS)** بالا می‌برد. [7][9]

### محور ۳ — Context Rot: افتِ کیفیت با رشدِ context (پدیدهٔ سنجش‌شده)
- تحقیقِ «Context Rot» (Chroma): کیفیتِ خروجی با **افزایشِ توکنِ ورودی** افت می‌کند — در **همهٔ** مدل‌های بزرگ. مهم: افت **بسیار پیش از پُرشدنِ پنجره** شروع می‌شود؛ مدلِ ۲۰۰K توکنی در **~۵۰K** افتِ معنادار نشان می‌دهد. [10][11]
- روی ۱۸ مدلِ frontier (GPT-4.1، خانوادهٔ Claude 4، Gemini 2.5، Qwen3): دقت **غیریکنواخت** و گاهی **۳۰–۵۰٪** پیش از حدِ مستند افت می‌کند؛ و عجیب: **ورودیِ منسجم و ساخت‌یافته attention را بیشتر از ورودیِ درهم افت می‌دهد** — «ساختار در مقیاس، هزینهٔ دقت دارد». [10][12]
- «Context Engineering» جانشینِ «Prompt Engineering» شد: طراحیِ عامدانهٔ **هرچه مدل در هر inference می‌بیند**. گفت‌وگویِ مهندسیِ ۲۰۲۶ دربارهٔ **context-budget، دقتِ retrieval، و لایه‌های حافظه** است؛ default = «۵۰K–۲۰۰K توکنِ **مرتبط** را retrieve کن، بعد long-context روی همان reason کن» — نه dumpِ همه‌چیز. [12][13][14]

### محور ۴ — Consolidation / Forgetting / Write-Policy / Conflict-Resolution
- **الگویِ دوفازی** (LightMem، MOOM): نوشتنِ **آنلاینِ سریع** (اطلاعاتِ نو فوراً پذیرفته می‌شود) + **consolidationِ آفلاینِ کند** در پس‌زمینه که **تناقض‌ها را حل و ورودی‌های مرتبط را merge می‌کند**. «یا consolidation، یا حافظه **بی‌مرز رشد می‌کند**.» [15][16]
- سه سیگنالِ **forgetting**: (۱) time-decay (نمائی، الهام از منحنیِ فراموشیِ Ebbinghaus) · (۲) بسامدِ دسترسی (LRU/LFU) · (۳) اهمیتِ معنایی (LLM-judged). (FadeMem: decayِ نمائیِ تطبیقی + fusionِ حافظه.) [15][17]
- **حلِ تعارض روی نوشتن (self-editing)**: وقتی اطلاعِ نو با کهنه می‌جنگد، رکوردِ **موجود** به‌روز شود نه رکوردِ **تکراری** (Mem0). برای حافظهٔ append-only، جبهه‌ی تحقیقاتیِ نو = **جبرِ عملگرِ bitemporal** برای حلِ تناقض بدونِ از دست‌رفتنِ تاریخچه (TOKI). [16][17][18]

### محور ۵ — سنجشِ حافظه/RAG + سمّی‌سازیِ بازیابی (Eval + Security)
- **متریک‌های کیفیتِ retrieval (نه فقط پاسخ):** Context Relevance با Precision@k · Recall@k · **nDCG@k** · **MRR** · Hit@K. کیفیتِ generation: faithfulness، citation-accuracy، refusal-correctness، hallucination-rate. «retrieval نقطهٔ ورودِ دانش است و **تأثیرِ تعیین‌کننده** بر کلِ سیستم دارد.» [19][20]
- **PoisonedRAG** (USENIX Security 2025): تعدادِ **اندکی** سندِ ساختگیِ دقیق در corpusِ میلیونی می‌تواند نرخِ پاسخِ غلط را به **>۹۰٪** برساند. → دفاع: corpus باید **curate/sign/filter** شود، هم در ingest هم در serve. [21][22]
- این محور، محورِ «حملهٔ حافظه»یِ نوتِ [[00 - Inbox/build-proposals/05-ai-agent-eng-2026-2026-07-05|05]] را **کمّی و از سمتِ retrieval** تکمیل می‌کند (نه تکرار): ۰۵ گفت «حافظهٔ مسموم = سطحِ حمله»؛ اینجا نرخِ >۹۰٪ و نقطهٔ دفاع (ingest+serve) اضافه می‌شود. [21][23]

---

## ۲. نگاشت به ستون (§۶ Memory strategy) — grounded، نه تزئینی

**متنِ فعلیِ §۶ (نقلِ دقیق):** «durable = append-only EXPERIENCE-LEDGER + Anchor Ledger؛ volatile = scout-digestهای تبخیرشونده (TTL). مسیرِ بازیابی: FTS5 اول، بعد لایهٔ وکتور. این قطبِ دوگانهٔ BIO-SYNTHESIS-MAP edge #13 است.»

**الف) ممیزیِ تاکسونومیِ ۴گانه [1][2] روی این سیستم:**

| نوعِ حافظه (۲۰۲۶) | اندامِ معادل در این vault | حکم |
|---|---|---|
| working (context فعال، TTL) | scout-digestهای تبخیرشونده (§۶ volatile) | ✅ هست |
| episodic (رویدادِ زمان‌ایندکس) | [[_memory/EXPERIENCE-LEDGER|EXPERIENCE-LEDGER]] append-only + Anchor Ledger | ✅ قوی |
| **semantic** (فکت/گراف/رابطه) | **کلِ گرافِ Obsidian** (MOCها + wikilink + Property Schema) — **ولی در §۶ به‌عنوانِ «حافظه» نام‌گذاری نشده** | 🔶 اندام هست، در مدلِ حافظه غایب |
| **procedural** (ورک‌فلوِ آموخته) | [[05 - Agents/RATIFIED-TASKS|RATIFIED-TASKS]] (متنِ پرامپتِ تسک‌ها) + اسکریپت‌های §۴ — **باز هم در §۶ نام‌گذاری نشده** | 🔶 اندام هست، در مدلِ حافظه غایب |

> **نتیجهٔ الف:** سیستم **هر ۴ نوع را عملاً دارد** ولی §۶ فقط ۲ را (working/episodic) به‌عنوانِ «حافظه» می‌نامد. semantic (گرافِ vault) و procedural (RATIFIED-TASKS) **اندامِ موجود**اند که فقط **برچسبِ حافظه ندارند** — این یک گپِ **نام‌گذاری/نگاشت** است، نه اندامِ گمشده. (دقیقاً همان صداقتِ ضدِّاستعارهٔ §۰.۴: اندام هست، باید درست نامیده شود.)

**ب) نگاشتِ مفهومیِ سایر یافته‌ها:**

| یافته | بخشِ spec | حکم |
|---|---|---|
| الگویِ tiered = هسته + retrieval + forgetting | §۶ (durable + FTS5/وکتور + TTL) | ✅ **تأییدِ مستقل** — قطبِ دوزمانهٔ §۶ **دقیقاً** baselineِ ۲۰۲۶ است |
| هیبرید **موازی** + RRF + **rerank** | §۶ «FTS5 اول، **بعد** وکتور» = **ترتیبی، بدونِ fusion، بدونِ reranker** | 🔴 **گپِ high-ROI** — الگوی فعلی fallbackِ ترتیبی است نه fusionِ موازی؛ reranker (بالاترین‌ROI) اصلاً نیست |
| context-rot: افت پیش از overflow | orientationِ حلقه **کلِ ledger** (۶۴+ ردیف، رو‌به‌رشد) + spec + backlog + HANDOFF را هر اجرا می‌خواند | 🔴 **ریسکِ زنده و خودارجاع** — هرچه ledger رشد کند، contextِ هر اجرای خودکار bloat و افت می‌کند |
| دوفازی: نوشتنِ سریع + consolidationِ کندِ حل‌تعارض | ledger **append-only، بدونِ consolidation/حل‌تعارض** روی لایهٔ durable؛ تسکِ `mycelial-consolidator` هست ولی خروجی‌اش لایهٔ مصرفیِ orientation نیست | 🔶 **تنشِ طراحی** (پایین) |
| forgetting = decay+LFU+salience | §۶ TTL فقط روی volatile؛ لایهٔ durable **هیچ سیاستِ فراموشی/خلاصه‌سازی ندارد** | ⚠️ گپ — رشدِ بی‌مرزِ append-only |
| متریکِ retrieval (Recall@k/nDCG/MRR) | §۶ Eval = rubric ≥۱۲/۱۶ + judge + DoD — **هیچ متریکِ کیفیتِ retrieval نیست** | ⚠️ گپ — نمی‌دانیم FTS5→وکتور واقعاً کار می‌کند یا نه |
| PoisonedRAG >۹۰٪ · curate/sign/filter | §۰.۴ صداقت + P-05 (مرزِ اعتماد/provenance) | 🔶 **مکمّلِ P-05** — نقطهٔ دفاع = ingest حافظه (scout→ledger) + serve (retrieval) |

**ج) گروندینگِ کلیدی — چرا این محور دقیقاً دردِ همین vault است:**
- **این vault خودش یک RAG store است.** append-only بودنِ [[_memory/EXPERIENCE-LEDGER|ledger]] یک انتخابِ **صحیحِ integrity** است (canonical، tamper-evident — §۷ LOG). ولی همان append-only با best-practiceِ consolidation/forgetting **تنش** دارد: ledger فقط **رشد** می‌کند و ستونِ «وضعیت» به‌روز می‌شود، اما ردیف‌ها **merge/حل‌تعارض نمی‌شوند**. مصداقِ زنده: ردیف‌های «reset دوم/سوم» بعداً **خطای مثبت** از آب درآمدند (ردیف ۵۴/۶۲) ولی هنوز در ledger‌اند و در هر orientation **دوباره خوانده** می‌شوند. این یعنی تناقض‌ها **انباشته و بازخوانده** می‌شوند — دقیقاً چیزی که الگوی دوفازی [15][16] حل می‌کند.
- **حلقهٔ orientation قربانیِ context-rotِ خودش است.** طبقِ گامِ ۱ پرامپتِ تسک، هر اجرا `AUTONOMOUS-RUN` + `HANDOFF` + `MYCELIAL-MASTER-SPEC` + `BUILD-BACKLOG` را می‌خواند، و ledger هم مرجعِ دائمی است. با رشدِ ledger و نوت‌های build-proposals (۸→۹→…)، توکنِ orientation یکنواخت بالا می‌رود — و [10][12] می‌گویند افت **well before overflow** است. راه‌حلِ ۲۰۲۶ = **retrieve، نه dump**: یک لایهٔ خلاصهٔ consolidated به‌جای بلعِ خامِ کلِ ledger.
- **بودجه = چراغِ قرمزِ retrieval-first [5][6].** با سقفِ **AU$30/ماه** (D-25)، «agent روی retrieverِ ضعیف = پولِ بیشتر برای اشتباهِ مفصّل‌تر» یک هشدارِ مستقیمِ اقتصادی است: قبل از هر ارکستراسیونِ گران‌ترِ ناوگان، **کفِ retrieval (هیبرید+rerank)** باید سالم شود.

---

## ۳. Cross-domain

> **حافظه/بازیابی یک اندامِ افقیِ مشترک است** ([[04 - Architect System/MYCELIAL-MASTER-SPEC|spec]] §۲: «Anchor Ledger + EXPERIENCE-LEDGER = durable substrate»). یک ارتقایِ واحدِ retrieval (هیبریدِ موازی + rerank) و یک لایهٔ consolidated، **recall را برای هر ۸ node هم‌زمان** بالا می‌برد — همان «یک موجودِ کلونالِ واحد، چند node» [J]. بیشترین اثر روی دامنه‌های با **ردِّ حافظه‌ی بزرگ‌تر**: **Crypto** (اندامِ ۳ — Portfolio Registry + exit_rules + alerts؛ بازیابیِ دقیقِ عددِ قیمت/قانون جایی است که وکتورِ تنها می‌لغزد و BMِ لغوی نجات می‌دهد [7]) · **Accounting** (اندامِ ۱ — رجیستر انطباق) · **Lead-نقاشی** (اندامِ ۲ — pipeline/weekly-report). سطحِ **سمّی‌سازی** [21] هر دامنه‌ای است که scout-digest‌اش به ledger می‌ریزد → نقطهٔ دفاع = همان مرزِ اعتمادِ P-05، حالا با نرخِ کمّیِ >۹۰٪ به‌عنوانِ توجیه. (Project-F طبقِ قاعده ماسک؛ حافظه/گزارشِ کدشده‌اش نیز مشمولِ همین لایه.)

---

## ۴. پیشنهادِ عملیِ اتصال به پلن (P-09) — «حافظهٔ دوفازی + کفِ retrievalِ هیبرید»

**چرا این یکی (نه بقیه):** بالاترین blast-radius چون (الف) خودِ حلقهٔ خودکار **همین‌حالا** قربانیِ رشدِ append-only + orientationِ خام است (context-rotِ زنده)، و (ب) هر ۸ node از یک substrateِ حافظهٔ واحد retrieve می‌کنند، پس یک ارتقا = بهبودِ کل. کم‌هزینه، برگشت‌پذیر، **بدونِ فعال‌سازیِ کد** (سند-محور + یک helperِ MOCK).

**این diffها پیشنهاد‌اند — اعمال نشد. spec دست‌نخورده.**

### diff الف — §۶ (Memory strategy): از «دوزمانه» به **tieredِ ۴گانه + لایهٔ consolidated**
- **قبل:** «durable = append-only EXPERIENCE-LEDGER + Anchor Ledger؛ volatile = scout-digestهای تبخیرشونده (TTL). مسیرِ بازیابی: FTS5 اول، بعد لایهٔ وکتور.»
- **بعد (افزوده):** «مدلِ حافظه **صریحاً tiered** است: **working** = scout-digestِ TTL · **episodic** = ledgerِ append-only (canonical/audit — دست‌نخورده می‌ماند) · **semantic** = گرافِ Obsidian (MOC/wikilink) · **procedural** = [[05 - Agents/RATIFIED-TASKS|RATIFIED-TASKS]]. + یک **لایهٔ consolidatedِ مشتق** (خروجیِ `mycelial-consolidator`): الگوی **دوفازی** [15] — نوشتنِ سریع در ledgerِ خام + **consolidationِ کندِ آفلاین** که تناقض‌ها را حل و درس‌های هم‌خانواده را merge می‌کند، **بدونِ ویرایشِ ledgerِ خام** (append-only محفوظ). orientation از این لایهٔ خلاصه می‌خواند، نه از خامِ کلِ ledger → مهارِ **context-rot** [10][12]. سیگنالِ forgetting برای لایهٔ مشتق: decay + LFU + salience [15].»

### diff ب — §۶ (Retrieval): از fallbackِ **ترتیبی** به هیبریدِ **موازی + rerank + متریک**
- **قبل:** «مسیرِ بازیابی: FTS5 اول، بعد لایهٔ وکتور.»
- **بعد (افزوده):** «بازیابی = **هیبریدِ موازی**: FTS5 (sparse/لغوی — نام/عدد/کدِ دقیق) و وکتور (dense/معنا) **هم‌زمان** اجرا و با **RRF** fuse شوند [7][8]؛ سپس یک **rerankِ سبک** (cross-encoderِ لوکال یا، اگر بودجه اجازه داد، یک فراخوانِ Haikuِ کوتاه پشتِ budget-gate) top-K را به top-۵ ببرد [7][9]. یک **probe-setِ ثابتِ کوچک** (۱۰–۲۰ کوئریِ طلایی روی همین vault) با **Recall@k / MRR** [19] کیفیتِ retrieval را قابل‌سنجش کند — این متریک به §۶ Eval افزوده شود (کنارِ rubric ≥۱۲/۱۶).»

### diffهایِ ثانویه (کاندیدا؛ این اجرا اعمال/بسته نشد)
- **§۶ Eval — متریکِ retrieval:** Recall@k/nDCG/MRR به‌عنوانِ DoDِ لایهٔ حافظه (الان فقط rubric کیفیتِ **پاسخ** را می‌سنجد، نه کیفیتِ **بازیابی**). [19][20]
- **§۰.۴ / §۶ — سختیِ سمّی‌سازی:** یک خط که «حافظه = corpusِ RAG؛ ingest (scout→ledger) و serve (retrieval) باید curate/filter شوند» — با نرخِ کمّیِ PoisonedRAG [21] به‌عنوانِ توجیه، هم‌خانواده با P-05 (مرزِ اعتماد/provenance).
- **§۲ — نامیدنِ اندام:** ردیفِ «حافظهٔ semantic = گرافِ vault [J]» و «procedural = RATIFIED-TASKS [J]» به جدولِ اندام‌ها افزوده شود تا مدلِ حافظه با معماری هم‌تراز شود.

---

## ۵. Trade-off پیشنهادِ P-09 (نمرهٔ ۱–۱۰)

| بعد | نمره | توضیح |
|---|---|---|
| Cost | ۸ | diff سند + یک probe-set + خروجیِ consolidatorِ موجود؛ rerankِ لوکال = صفر API، یا Haikuِ کوتاه پشتِ budget-gate |
| Complexity | ۵ | RRF و cross-encoderِ لوکال کتابخانه‌های بالغ‌اند؛ لایهٔ consolidated روی تسکِ `mycelial-consolidator`ِ **موجود** سوار می‌شود |
| Scalability | ۹ | با رشدِ ledger و افزودنِ node، هم context-rot و هم recall بحرانی‌تر می‌شوند — این ارتقا دقیقاً همان‌جا اثر می‌گذارد |
| Maintainability | ۸ | سند-محور؛ append-only دست‌نخورده (integrity حفظ)، فقط یک لایهٔ مشتق افزوده |
| Security | ۷ | fusion/rerank سطحِ سمّی‌سازیِ retrieval را کم می‌کند؛ نقطهٔ دفاعِ ingest/serve مکمّلِ P-05 |
| Time-to-Impl | ۶ | diff §۶ (verdict) + helperِ RRF/rerank (کارِ Fable، MOCK) + probe-setِ دستیِ کوچک |

**ROI: بالا** — مستقیماً context-rotِ **زندهٔ همین حلقه** + recallِ هر ۸ node را هدف می‌گیرد، با کمترین هزینه و بدونِ لمسِ append-only. هم‌راستا با §۶ (دوزمانه‌ی موجود)، §۷ (consolidation = بازوی LOG)، و «retrieval-first» به‌عنوانِ مهارِ بودجهٔ AU$30.

---

## ۶. سؤالِ باز برای verdictِ آری
- diff الف/ب روی §۶ اعمال شود (نسخه → v0.2 طبقِ §۷)، یا فعلاً فقط ریسک/بک‌لاگِ ثبت‌شده در §۱/§۶ بماند؟
- لایهٔ **consolidated** خروجیِ همان تسکِ `mycelial-consolidator` باشد یا یک اندامِ نو؟ پیشنهاد: **همان تسک** (اجتناب از افزودنِ node؛ فقط قالبِ خروجی = «درس‌های merge/حل‌تعارض‌شده» که orientation از آن بخواند). — verdict.
- **rerank**: لوکالِ صفر-هزینه (cross-encoderِ کوچک) یا فراخوانِ کوتاهِ Haiku پشتِ budget-gate؟ (پیشنهاد: لوکال به‌عنوانِ default، Haiku فقط escalation — سازگار با §۶ استراتژیِ مدل.) — verdict.
- **پیش‌نیازِ کدام milestone؟** پیشنهاد: probe-set + متریکِ retrieval پیش از هر اتکای auto به بازیابی؛ الحاق به **M6 (observability)** یا یک **M-نو** برای لایهٔ حافظه. — verdict.
- (میان‌بخشی) P-09 با P-05 (مرزِ اعتماد/provenance) و P-08 (idempotency/journal) هم‌خانواده است — هر سه دربارهٔ **substrateِ حافظه/اثر**اند؛ به [[00 - Inbox/build-proposals/07-review-packet-2026-07-05|REVIEW-PACKET]] به‌عنوانِ بستهٔ v0.2 اضافه شود؟

---

## Sources
- [1] [AI Agent Memory Systems: A 2026 Engineering Guide (Letta, LangMem, Mem0, Zep) — JobsByCulture](https://jobsbyculture.com/blog/ai-agent-memory-systems-guide-2026)
- [2] [Types of AI Agent Memory: Episodic, Semantic, Procedural and More — Atlan](https://atlan.com/know/types-of-ai-agent-memory/) · [Episodic Memory for AI Agents — Atlan](https://atlan.com/know/episodic-memory-ai-agents/)
- [3] [Agent Memory Architectures: Patterns and Trade-offs (2026) — Atlan](https://atlan.com/know/agent-memory-architectures/)
- [4] [Architecture and Orchestration of Memory Systems in AI Agents — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/04/memory-systems-in-ai-agents/)
- [5] [Agentic RAG in 2026: Five Production Retrieval Patterns — Brightter](https://www.brightter.com/articles/agentic-rag-five-retrieval-patterns-that-survive-production)
- [6] [RAG Production Guide 2026 — Lushbinary](https://lushbinary.com/blog/rag-retrieval-augmented-generation-production-guide/)
- [7] [Hybrid Search: BM25, Vector & Reranking Reference 2026 — DigitalApplied](https://www.digitalapplied.com/blog/hybrid-search-bm25-vector-reranking-reference-2026)
- [8] [Hybrid Search for RAG: Vector + Keyword + Reranking Guide 2026 — BuildMVPFast](https://www.buildmvpfast.com/blog/hybrid-search-rag-vector-keyword-reranking-2026)
- [9] [Advanced RAG: From Naive Retrieval to Hybrid Search and Re-ranking — DEV](https://dev.to/kuldeep_paul/advanced-rag-from-naive-retrieval-to-hybrid-search-and-re-ranking-4km3)
- [10] [Context Rot: Why LLMs Degrade as Context Grows — Morph](https://www.morphllm.com/context-rot)
- [11] [Context rot explained (& how to prevent it) — Redis](https://redis.io/blog/context-rot/)
- [12] [Context Rot, RAG, and Long Context: How to Architect LLM Systems in 2026 — Glasp](https://glasp.co/articles/context-rot-rag-long-context-hybrid)
- [13] [Context Engineering: Agent Reliability Playbook 2026 — DigitalApplied](https://www.digitalapplied.com/blog/context-engineering-agent-reliability-playbook-2026)
- [14] [Context Engineering Guide 2026: The Discipline That Replaced Prompt Engineering — JobsByCulture](https://jobsbyculture.com/blog/context-engineering-guide-2026)
- [15] [Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers — arXiv 2603.07670](https://arxiv.org/html/2603.07670v1)
- [16] [Memory Systems for AI Agents: What the Research Says — Steve Kinney](https://stevekinney.com/writing/agent-memory-systems)
- [17] [Best AI Agent Memory Frameworks in 2026: Compared and Ranked — Atlan](https://atlan.com/know/best-ai-agent-memory-frameworks-2026/)
- [18] [TOKI: A Bitemporal Operator Algebra for Contradiction Resolution in LLM-Agent Persistent Memory — arXiv 2606.06240](https://arxiv.org/pdf/2606.06240)
- [19] [RAG Evaluation 2026: Methods, Metrics, Frameworks — DataVLab](https://datavlab.ai/post/rag-evaluation-methods-metrics-2026-guide)
- [20] [Memory in Large Language Models: Mechanisms, Evaluation and Evolution — arXiv 2509.18868](https://arxiv.org/pdf/2509.18868)
- [21] [SafeRAG: Benchmarking Security in Retrieval-Augmented Generation — arXiv 2501.18636](https://arxiv.org/pdf/2501.18636)
- [22] [Security and Privacy in Retrieval-Augmented Generation — arXiv 2606.25533](https://arxiv.org/pdf/2606.25533)
- [23] [A Survey on Trustworthy LLM Agents: Threats and Countermeasures — arXiv 2503.09648](https://arxiv.org/pdf/2503.09648)

> **پایان.** فقط-پیشنهاد. اتصالِ اجرا = دومین اجرای **حالتِ تحقیقِ پیوسته**، صفِ [[00 - Inbox/AUTONOMOUS-RUN-2026-07-05|AUTONOMOUS-RUN]]. طبقِ §۷، اعمالِ diffها منتظرِ verdictِ آری است.
