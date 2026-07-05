---
type: knowledge
status: active
created_by: agent
created: 2026-07-06
updated: 2026-07-06
tags: [doctor, memory, consolidation]
sources:
  - https://arxiv.org/abs/2606.10062
  - https://arxiv.org/abs/2606.03979
  - https://arxiv.org/abs/2605.20616
  - https://arxiv.org/abs/2605.12978
  - https://arxiv.org/abs/2512.12818
  - https://arxiv.org/abs/2603.15642
  - https://arxiv.org/abs/2604.02280
  - https://arxiv.org/abs/2310.08560
  - https://arxiv.org/abs/2606.03197
  - https://arxiv.org/abs/2601.01885
  - https://arxiv.org/abs/2601.20465
  - https://arxiv.org/abs/2602.13530
  - https://arxiv.org/abs/2605.16045
  - https://arxiv.org/abs/2603.07670
  - https://arxiv.org/abs/2606.24775
  - https://arxiv.org/abs/2605.03675
  - https://arxiv.org/abs/2604.15484
  - https://arxiv.org/abs/2606.06448
  - https://arxiv.org/abs/2603.13017
  - https://arxiv.org/abs/2510.18866
---

# حافظهٔ لایه‌ای agent: جدا کردن working / long-term / core و فاز consolidation شبانه

> خلاصهٔ یک‌خطی: بهترین معماری‌های حافظهٔ ۲۰۲۶ حافظه را به لایه‌های زمانی جدا می‌کنند، اکتساب سریع (fast) را از تثبیت کند (slow) می‌شکنند، خام episode را به‌عنوان مدرکِ درجه‌یک نگه می‌دارند، و به‌جای «حذف داده» فقط «امتیاز بازیابی را decay» می‌کنند.

این نوت سنتز agent است روی paperهای ۲۰۲۶ حوزهٔ agent-memory. مرجع لنگر: **Deployment-Time Memorization in Foundation-Model Agents** (arXiv 2606.10062) که همان شناسهٔ خواسته‌شده است و resolve می‌شود.

---

## ۱. چرا سه لایه؟ (working / long-term / core)

الگوی OS-محورِ MemGPT ([arXiv 2310.08560](https://arxiv.org/abs/2310.08560)) هنوز اسکلت مرجع است: حافظه مثل سلسله‌مراتب حافظهٔ سیستم‌عامل مدیریت می‌شود — یک لایهٔ سریع و کوچک داخل context، و لایه‌های کند و بزرگ بیرون، با جابه‌جایی داده بین‌شان (paging). paperهای ۲۰۲۶ این ایده را پخته‌تر کرده‌اند و معمولاً سه لایهٔ کارکردی تفکیک می‌کنند:

| لایه | معادل شناختی | چه نگه می‌دارد | چطور فراموش می‌کند |
|---|---|---|---|
| **Working / short-term** | حافظهٔ کاری، in-trial | فقط زمینهٔ همین task/session جاری؛ action-observation جاری، subgoal فعال | با پایان session تخلیه یا خلاصه می‌شود؛ چیزی که به long-term نرود، می‌رود |
| **Long-term (episodic + semantic)** | هیپوکامپ → نئوکورتکس | episodic: ردِ خام «چه اتفاقی افتاد»؛ semantic: درسِ distill‌شدهٔ بازمصرف‌پذیر | با decay امتیاز + pruning بودجه‌ای؛ نه با حذف فوری |
| **Core** | persona / خودانگاره | چند بلوک ثابتِ همیشه-در-context: کیستی کاربر، قواعد پایدار، تنظیمات | تقریباً هرگز؛ فقط ویرایش صریح و traceable |

نکتهٔ کلیدی که چند survey ۲۰۲۶ تأکید می‌کنند (survey جامع [arXiv 2603.07670](https://arxiv.org/abs/2603.07670)، و مطالعهٔ سیستمیِ agent-native [arXiv 2606.24775](https://arxiv.org/abs/2606.24775)): **هیچ معماری‌ای در همهٔ سناریوها برنده نیست**؛ اثربخشی به این بستگی دارد که ساختار حافظه با گلوگاهِ workload هم‌تراز باشد، و **maintenance محلی (localized) ارزان‌تر از بازسازماندهی سراسری (global reorganization) است**. این دقیقاً منطق فاز شبانه را توجیه می‌کند: کارِ سنگینِ سازماندهی را از مسیر داغِ پاسخ‌دهی جدا کن.

عددِ ملموسی که هزینهٔ نبودِ این جداسازی را نشان می‌دهد: **MemTier** ([arXiv 2605.03675](https://arxiv.org/abs/2605.03675)) گزارش می‌دهد نرخ موفقیتِ اجرای ابزار در agentهای طولانی‌مدت با حافظهٔ تخت (flat-file) طیِ یک پنجرهٔ ۷۲ ساعته **۱۴ واحدِ درصد افت** می‌کند. راه‌حلش هم‌راستا با این نوت است: episodic storage ساختاریافته (JSONL) + بازیابیِ وزن‌دارِ پنج‌سیگنالی + یک **daemonِ ناهم‌زمان** برای semantic consolidation (ترفیعِ factهای مهم) + policyِ تطبیقی با RL روی وزن‌های بازیابی. حتی روی سخت‌افزار مصرفی (GPU ۶ گیگ) روی LongMemEval-S حدود ۳۳ امتیاز بهبود نسبت به baseline می‌گیرد — شاهدی مستقل بر اینکه «تخت نگه‌داشتنِ حافظه + فقدان daemonِ ناهم‌زمان» دقیقاً همان الگوی معیوبی است که این نوت توصیه به اجتنابش می‌کند.

**LightMem** ([arXiv 2510.18866](https://arxiv.org/abs/2510.18866), ICLR 2026) الهام‌گرفته از مدلِ Atkinson-Shiffrin (روان‌شناسیِ حافظهٔ انسانی)، دقیقاً همین سه‌لایه را با نام‌های شناختی می‌سازد: **sensory memory** (فیلترِ سبکِ اطلاعاتِ نامربوط با فشرده‌سازیِ ارزان + گروه‌بندیِ موضوعی) → **topic-aware short-term memory** (تثبیتِ گروه‌های موضوعی، خلاصه‌سازیِ ساختاریافته) → **long-term memory با sleep-time update** (پروسهٔ آفلاینی که consolidation را کاملاً از inferenceِ آنلاین جدا می‌کند). نتیجه روی LongMemEval/LoCoMo: تا ۷.۷٪/۲۹.۳٪ بهبودِ دقتِ QA، تا ۳۸×/۲۰.۹× کاهشِ کلِ توکن، و تا ۳۰×/۵۵.۵× کاهشِ تعداد فراخوانیِ API — رگرسیونِ مستقل دیگری که نشان می‌دهد نامِ لایه‌ها فرقی نمی‌کند (sensory/short-term/long-term یا working/episodic/semantic)، تا وقتی که **جداییِ fast-acquire از slow-consolidate** رعایت شود، هزینه به‌شدت پایین می‌آید.

عددِ سیستمیِ مکمل از **Agent Memory: Characterization and System Implications** ([arXiv 2606.06448](https://arxiv.org/abs/2606.06448), Stanford/KU Leuven/MIT، اولین profiling سیستمیِ agent memory روی ۱۰ سیستمِ واقعی): هزینهٔ **construction** (نوشتنِ/ساختِ حافظه) نه هزینهٔ query-time، غالبِ چرخهٔ عمرِ agent است — روی ۱.۸ میلیون توکنِ تاریخچه، construction wall-time از زیرِ یک دقیقه (BM25، EmbedRAG) تا بیش از ۱۳ ساعت (Letta) متغیر است، و انرژی-به-ازای-پاسخِ-درست تا ۴۷× بین سیستم‌های هم‌دقت فرق می‌کند. این مقاله یک taxonomyِ چهارمحوره هم می‌دهد که مستقیماً با لایه‌بندیِ این نوت هم‌پوشانی دارد: Paradigm I (long-context، بدون ساخت حافظه)، II (flat RAG append-only — BM25/EmbedRAG)، III (structure-augmented RAG که به append-only مثل GraphRAG/HippoRAG-v2 در برابر consolidating مثل Mem0/SimpleMem تقسیم می‌شود)، IV (agentic control flow — MemGPT/Letta/A-Mem که خودِ LLM تصمیم به نوشتن/بازیابی می‌گیرد). درسِ عملی: **زمان‌بندیِ consolidation را از مسیرِ پاسخ‌دهیِ حساس-به-تأخیر جدا کن** (admission control روی construction به‌عنوان یک workloadِ پس‌زمینه)، دقیقاً همان چیزی که فاز شبانه در این نوت پیشنهاد می‌دهد.

### working چه نگه می‌دارد / چطور فراموش می‌کند
لایهٔ کاری فقط باید «آنچه برای قدم بعدی لازم است» را داشته باشد. الگوی HiAgent و کارهای مشابه: subgoal را به‌عنوان chunk نگه دار، و به‌محض بستن subgoal، جفت‌های action-observationِ مربوط را با یک خلاصه جایگزین کن. فراموشیِ لایهٔ کاری = **خلاصه‌سازیِ فشرده در پایان هر واحد کار**، نه انباشت خام تا انفجار context.

### long-term چه نگه می‌دارد / چطور فراموش می‌کند
اینجا هستهٔ بحث است. long-term خودش دولایه است:
- **episodic**: ترجکتوریِ خام، تایم‌استمپ‌دار، با provenance. «چه شد، کِی، در چه زمینه‌ای».
- **semantic**: schemaها/درس‌های عمومیِ distill‌شده روی چند episode. «قاعدهٔ بازمصرف».

REMem ([arXiv 2602.13530](https://arxiv.org/abs/2602.13530)) نشان می‌دهد حافظهٔ agentها بیش‌ازحد semantic است و episodicity را گم می‌کند؛ راه‌حلش گراف حافظهٔ هیبریدی است که gistهای زمان‌آگاه و factها را به هم لینک می‌کند. BMAM ([arXiv 2601.20465](https://arxiv.org/abs/2601.20465)) همین جداسازی episodic/semantic/salience/control را زیرسیستم‌های تخصصی با مقیاس‌های زمانی مکمل می‌کند.

### core چه نگه می‌دارد / چطور فراموش می‌کند
core همان بلوک‌های همیشه-حاضر است (در ادبیات MemGPT: persona/human block). این لایه **عمداً کوچک و پایدار** است؛ به‌ندرت و فقط با ویرایش صریحِ ثبت‌شده تغییر می‌کند. Deployment-Time Memorization ([arXiv 2606.10062](https://arxiv.org/abs/2606.10062)) یادآوری می‌کند که هرچه بیشتر در این لایه نگه داری، Personalization Recall (PR) بالاتر می‌رود ولی Adversarial Extraction Rate (AER) هم بالا می‌رود — پس core باید فقط چیزهای واقعاً هویتی/پایدار را بگیرد، نه هر factِ حساس.

---

## ۲. فاز consolidation شبانه (sleep-cycle) و distill کردن episodic→semantic

ایدهٔ محوری ۲۰۲۶: **اکتساب سریع را از تثبیت کند جدا کن** (complementary learning systems). در طول روز/session، فقط سریع بنویس؛ کارِ فکریِ سازماندهی را به یک پاسِ آفلاین (شبانه/دوره‌ای) بسپار.

- **Language Models Need Sleep** ([arXiv 2606.03979](https://arxiv.org/abs/2606.03979)): پارادایم «Sleep» دو مرحله دارد — (۱) **Memory Consolidation / Knowledge Seeding**: distillِ رو-به-بالای حافظه‌های شکنندهٔ کوتاه‌مدت به دانش پایدار بلندمدت با **replay**؛ (۲) **Dreaming**: تولید curriculum از دادهٔ سنتتیک برای rehearse و پالایش قابلیت‌ها بدون نظارت انسانی. پیام کلیدی: مدل باید «بخوابد» تا حافظهٔ فرار به دانش تثبیت‌شده تبدیل شود.
- **Auto-Dreamer** ([arXiv 2605.20616](https://arxiv.org/abs/2605.20616)): consolidatorِ آفلاینِ *یادگرفته‌شده*. per-session را سریع می‌گیرد، سپس در یک پاس کندِ cross-session یک «working region» از memory bankِ typed را به‌عنوان **read-only evidence** برمی‌دارد، با tool-use محدود entryها و **ترجکتوری‌های منبعِ provenance-linked** را بازرسی می‌کند، و یک مجموعهٔ فشردهٔ تازه می‌سازد که جای ناحیهٔ قبلی را می‌گیرد. با GRPO و پاداشِ کارایی end-to-end آموزش می‌بیند. نتیجه: روی ScienceWorld ۷ امتیاز بهتر با memory bankِ فعالِ **۱۲ برابر کوچک‌تر**، و تعمیم به ALFWorld/WebArena بدون بازآموزش.
- **RecMem** ([arXiv 2605.16045](https://arxiv.org/abs/2605.16045)): consolidation را **recurrence-based** می‌کند. ورودی‌ها اول در یک «subconscious layer» با embeddingِ سبک ذخیره می‌شوند؛ LLM فقط وقتی برای استخراج episodic/semantic صدا زده می‌شود که **تکرارِ پایدارِ تعاملاتِ معنایی‌مشابه** دیده شود (یعنی خوشهٔ باارزش). تا ۸۷٪ کاهش هزینهٔ توکنِ ساخت حافظه با دقتِ بالاتر. درس: consolidation را eager (پس از هر تعامل) نزن؛ آن را **رویداد-محور / تکرار-محور** trigger کن.
- **CraniMem** ([arXiv 2603.15642](https://arxiv.org/abs/2603.15642)): بافرِ episodicِ کران‌دار برای پیوستگیِ نزدیک + گرافِ دانشِ long-term برای recall معناییِ پایدار؛ یک **حلقهٔ consolidation زمان‌بندی‌شده** ردهای پرارزش را در گراف replay می‌کند و آیتم‌های کم‌ارزش را prune می‌کند تا رشدِ حافظه مهار شود.

### هشدار بحرانی: consolidation را gate کن، evidence را overwrite نکن
**Useful Memories Become Faulty When Continuously Updated by LLMs** ([arXiv 2605.12978](https://arxiv.org/abs/2605.12978)) یافتهٔ مهمی دارد: اگر بعد از *هر* تعامل consolidation بزنی، منفعتِ حافظه اول بالا می‌رود، بعد افت می‌کند و می‌تواند **زیرِ baselineِ بدون‌حافظه** برود. حتی از روی راه‌حل‌های ground-truth، مدل روی ۵۴٪ مسائلی که قبلاً بدون حافظه حل کرده بود شکست خورد — و مقصر **مرحلهٔ consolidation** است، نه خودِ تجربه. نتیجهٔ عملی طلایی:

> **episode خام را به‌عنوان مدرکِ درجه‌یک نگه دار، و consolidation را صراحتاً gate کن — نه اینکه بعد از هر تعامل شلیک کنی. کنترلِ episodic-only اغلب با consolidatorها رقابت می‌کند.**

این با Auto-Dreamer هم‌خوان است: ناحیه read-only است، خامْ سرِ جایش می‌ماند، فقط یک لایهٔ فشردهٔ تازه *روی* آن می‌نشیند و supersede می‌کند — نه اینکه مدرک را پاک کند.

---

## ۳. retrieval هیبرید: BM25 + vector + rerank با RRF

الگوی بالغ ۲۰۲۶ برای مسیر خواندن:

1. **دو retriever مکملِ مرحله‌اول به‌صورت موازی**: BM25 (lexical/keyword — برای تطبیق دقیق نام، شناسه، اصطلاح) و dense vector (semantic — برای مفهومِ هم‌معنا با واژه‌های متفاوت).
2. **fusion با RRF (Reciprocal Rank Fusion)**: نتایج دو منبع را روی **rank** ادغام می‌کند نه روی امتیاز خام، پس نیازی به هم‌مقیاس کردن امتیازهای ناسازگار نیست. فرمول سادهٔ `score = Σ 1/(k + rank_i)` (معمولاً k حدود ۱۰ تا ۶۰). قوی و «zero-shot».
3. **rerank با cross-encoder** روی چند-ده کاندیدای برتر: مرحلهٔ دومِ گران ولی دقیق که واقعاً بالای Pareto می‌نشیند.

بیشترِ سرمایه‌گذاریِ مهندسی در خودِ fusion نیست (RRF چند خط کد است)، بلکه در کیفیتِ دو retriever و rerankِ نهایی. برای حافظهٔ agent، این مسیر روی هر دو لایهٔ episodic و semantic اجرا می‌شود و می‌تواند سیگنال‌های مکمل (زمان، provenance، salience) را هم به fusion تزریق کند — همان کاری که BMAM با «fusing multiple complementary signals» و REMem با گرافِ حافظه می‌کنند. AgeMem ([arXiv 2601.01885](https://arxiv.org/abs/2601.01885)) کلِ read/write/update/summarize/discard را به‌صورت actionهای tool-based به policyِ خود agent می‌سپارد تا خودش تصمیم بگیرد چه‌وقت و چه‌چیز بازیابی کند.

پیاده‌سازیِ عملیِ این الگو را **vstash** ([arXiv 2604.15484](https://arxiv.org/abs/2604.15484)) نشان می‌دهد: یک فایل SQLiteِ واحد که هم vector similarity و هم full-text (BM25-مانند) را نگه می‌دارد، با **RRFِ تطبیقی** (وزن‌دهیِ per-query بر اساس IDF) که تا ۲۱٪+ بهبود روی بنچمارک‌های BEIR می‌دهد؛ و یک ترفندِ مهم برای نگه‌داشتنِ کیفیت بدون برچسبِ انسانی: هرجا vector-heavy و FTS-heavy retriever با هم اختلاف نظر دارند، همان اختلاف را سیگنالِ self-supervised برای fine-tuneِ embeddingِ سبک می‌گیرد. لتنسیِ میانه ۲۰.۹ میلی‌ثانیه روی +۵۰هزار کوئریِ برچسب‌خورده — یعنی این معماری در مقیاسِ واقعی و روی سخت‌افزارِ محلی هم عملی است، نه فقط تئوری.

شواهدِ تجربیِ اضافه از **Structured Distillation for Personalized Agent Memory** ([arXiv 2603.13017](https://arxiv.org/abs/2603.13017)): روی ۶ ماه سشنِ کدنویسیِ واقعی، مقاله ۱۰۷ پیکربندیِ retrieval را می‌آزماید (pure، cross-layer، hybrid) و نشان می‌دهد بهترین نتیجه از **fusionِ چندسیگنالی روی دو لایهٔ متن** می‌آید: BM25 روی متنِ خام (verbatim) + HNSW-vector روی متنِ distill‌شده، ترکیب‌شده با RRF. یعنی حتی خودِ «کدام لایه را با کدام retriever بخوانیم» یک بعدِ طراحیِ مجزاست — distillِ semantic لزوماً نباید جایگزینِ کاملِ ایندکسِ خام شود؛ فیوژنِ متقاطعِ لایه‌ها (raw+BM25 ⊕ distilled+vector) با **۱۱× کاهشِ توکن** و حفظِ کیفیتِ بازیابی به نتیجه می‌رسد — تأییدی دیگر بر اصل «خام را نگه دار، رویش لایهٔ فشرده بساز، نه به‌جایش».

---

## ۴. «امتیاز را decay کن، نه داده را»

اصل مرکزیِ forgetting در ۲۰۲۶ (منبع دقیق: **Novel Memory Forgetting Techniques** [arXiv 2604.02280](https://arxiv.org/abs/2604.02280)):

- تابع امتیازِ نگه‌داشت:  `I(mᵢ, t) = α·R(mᵢ,t) + β·F(mᵢ) + γ·S(mᵢ, qₜ)`
  - **R** = recency زمانی (تازگی)
  - **F** = frequency استفاده/بازیابی (هرچه بیشتر بازیابی شود، تقویت)
  - **S** = similarity معنایی با کوئری/زمینهٔ فعلی
- **decay نمایی روی امتیاز**: `exp(−λ(t − tᵢ))` — λ کوچک‌تر یعنی نگه‌داشتِ طولانی‌تر، λ بزرگ‌تر یعنی فراموشیِ تهاجمی‌تر. مهم: این **امتیاز** را کم می‌کند، دادهٔ زیرین دست‌نخورده می‌ماند.
- **prune فقط وقتی از بودجه رد شدی**: `argmax_{M'⊆M} Σ I(mᵢ,t)  s.t. |M'| ≤ B`. یعنی تا وقتی جا هست هیچ‌چیز حذف نمی‌شود؛ فقط وقتی سقفِ context/بودجه شکست، کم‌امتیازترین‌ها کنار می‌روند.

چرا این «decay امتیاز نه داده» درست است:
- episodeِ خامْ مدرک است (طبق 2605.12978)؛ اگر امتیازش صفر شود دیگر بالا نمی‌آید ولی اگر بعداً لازم شد قابل احیا است.
- بازیابیِ مکرر خودبه‌خود چیزهای مهم را زنده نگه می‌دارد (F بالا)، و چیزهای بی‌مصرف طبیعتاً به ته صف می‌روند — «فراموشیِ نرم».
- با Deployment-Time Memorization ([arXiv 2606.10062](https://arxiv.org/abs/2606.10062)) هم‌راستاست: پایین بردنِ امتیازِ factهای حساسِ کم‌مصرف، سطحِ AER (نشتِ استخراجی) را کم می‌کند بدون قربانی‌کردنِ کاملِ PR.

---

## ۵. جمع‌بندیِ الگوی مرجع ۲۰۲۶

```
[ورودی] → working (خام، همین session)
      │  (پایان واحد کار: خلاصهٔ فشرده)
      ▼
episodic (خام + provenance + تایم‌استمپ)  ← مدرکِ درجه‌یک، هرگز مخرب overwrite نشو
      │  (فاز شبانه/رویداد-محور: replay + distill، gate‌شده)
      ▼
semantic (درسِ بازمصرف‌پذیر، فشرده، supersede‌کننده نه پاک‌کننده)
      ▲
core (چند بلوک هویتیِ پایدار، همیشه در context)

read: BM25 ⊕ vector → RRF → rerank(cross-encoder)
forget: decay نماییِ امتیاز (R,F,S) ؛ prune فقط زیر فشار بودجه
```

---

## طرح ارتقای EXPERIENCE-LEDGER + consolidator ما به حافظهٔ دوفازی

وضع فعلی ما (به‌فهم من از vault): یک **EXPERIENCE-LEDGER** تخت که رخدادها/درس‌ها را append می‌کند، و یک consolidator که احتمالاً روی همین لجر می‌نویسد/بازنویسی می‌کند. مشکل الگوییِ این طرح دقیقاً همان چیزی است که 2605.12978 هشدار می‌دهد: اگر consolidator مکرراً روی لجر بازنویسی کند، کیفیت اول بالا و بعد پایین می‌رود.

پیشنهاد ارتقا به **دوفازی (fast-write / slow-consolidate)**، سازگار با قواعد vault («هرگز حذف نکن؛ فقط منتقل کن» و «append تاریخ‌دار، نه بازنویسی مخرب»):

**فاز ۱ — Fast write (روزانه، ارزان، append-only):**
- EXPERIENCE-LEDGER می‌شود لایهٔ **episodic خام**: هر ورودی با `created`, provenance (لینک به لاگ پروژه/پیام تلگرام)، و تگ salience اولیه. append-only، هیچ‌وقت in-place بازنویسی نمی‌شود.
- هیچ distillِ سنگینی اینجا نزن؛ فقط تگ و امتیازِ اولیه. (منطق RecMem/2605.16045: eager consolidation ممنوع.)

**فاز ۲ — Slow consolidate (شبانه/هفتگی، gate‌شده):**
- یک پاس آفلاین (هم‌تراز با «جاروی روزانه» و Weekly Review). ورودی‌اش یک **working region** از لجر است که فقط **read-only** خوانده می‌شود (الگوی Auto-Dreamer/2605.20616).
- شرط trigger: فقط وقتی **تکرار/خوشهٔ معنایی** یا حجمِ کافی جمع شده (نه بعد از هر آیتم). این gate از افت‌کیفیتِ 2605.12978 جلوگیری می‌کند.
- خروجی: نوت‌های **semantic** جدید در `07 - Knowledge` (طبق درخت تصمیم بند c: `created_by: agent` + ≥۲ منبع)، که episodeهای خام را **supersede** می‌کنند اما پاک نمی‌کنند — خام در لجر می‌ماند، فقط امتیازش پایین می‌آید. این دقیقاً معادلِ vaultیِ «منتقل کن، حذف نکن» است.

**لایهٔ core:**
- یک بلوکِ کوچکِ 