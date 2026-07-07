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
  - https://arxiv.org/abs/2604.20943
  - https://arxiv.org/abs/2601.02845
  - https://arxiv.org/abs/2605.08538
  - https://arxiv.org/abs/2603.04549
  - https://arxiv.org/abs/2605.06527
  - https://arxiv.org/abs/2604.20006
  - https://arxiv.org/abs/2603.14517
  - https://arxiv.org/abs/2603.02473
  - https://arxiv.org/abs/2602.05665
  - https://arxiv.org/abs/2604.12034
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

**SCM — Sleep-Consolidated Memory** ([arXiv 2604.20943](https://arxiv.org/abs/2604.20943), آوریل ۲۰۲۶) پنج مؤلفه را دقیقاً روی همین سه‌لایه پیاده می‌کند و صراحتاً می‌گوید هدفش نقدِ MemGPT/Mem0 است: working memory با ظرفیتِ محدود (آنالوگِ ۷±۲ آیتمی)، تگ‌گذاریِ اهمیتِ چهاربعدی (novelty/emotion/task-relevance/repetition)، **consolidationِ آفلاینِ دومرحله‌ای** با فازهای متمایزِ NREM (تقویتِ ارتباط‌های مهم) و REM (تولیدِ اتصالاتِ نو/دریمینگ)، فراموشیِ عمدیِ ارزش‌محور، و یک self-model محاسباتی برای درون‌نگری. روی سوییتِ استانداردِ ۸ تست: recall کامل روی مکالماتِ ده-نوبتی، **۹۰.۹٪ کاهشِ نویزِ حافظه** با فراموشیِ تطبیقی، و لتنسیِ جست‌وجوی زیرِ یک میلی‌ثانیه حتی با صدها concept ذخیره‌شده. نکتهٔ مهم برای این نوت: نویسنده صریحاً MemGPT را نقد می‌کند چون «بدون فرایندهای بیولوژیکِ حافظه مثل sleep-dependent consolidation یا synaptic pruning» است و Mem0 را چون «awake-only» — یعنی فاقدِ فازِ آفلاین.

**TiMem — Temporal-Hierarchical Memory Consolidation** ([arXiv 2601.02845](https://arxiv.org/abs/2601.02845)) بُعدِ زمان را به‌عنوان اصلِ سازمان‌دهنده مطرح می‌کند: یک Temporal Memory Tree (TMT) که observation خامِ مکالمه را به‌تدریج به بازنماییِ persona انتزاعی‌تر می‌برد؛ consolidation در طولِ سلسله‌مراتب **semantic-guided** است (بدون نیاز به fine-tune)، و بازیابی **complexity-aware** است (پرس‌وجوهای ساده کم‌هزینه، پیچیده گران). نتیجه: SOTA روی LoCoMo (۷۵.۳۰٪) و LongMemEval-S (۷۶.۸۸٪) با **۵۲.۲٪ کاهشِ طولِ حافظهٔ بازیابی‌شده** روی LoCoMo — شاهدِ دیگری که تراکمِ سلسله‌مراتبیِ زمان‌آگاه، هم دقت هم فشردگی می‌دهد.

**Human-Inspired Memory Architecture for LLM Agents** ([arXiv 2605.08538](https://arxiv.org/abs/2605.08538)) دقیقاً معماریِ سه‌لایهٔ این نوت را با retrieval هیبریدِ اولویت‌دار پیاده می‌کند: (۱) hot cache کوتاه‌مدت برای session جاری (زیر-ثانیه، بالاترین اولویت)، (۲) warm vector store برای episodicِ اخیر (فیلتر با importance score)، (۳) knowledge-graph traversal برای semanticِ بالغ (فیلتر با activation strength) — نتایج merge/dedupe/rank با recency boost می‌شوند. مفهومِ کلیدیِ اضافه: **reconsolidation** — حافظهٔ بازیابی‌شده وارد یک حالتِ labile می‌شود و برای یک پنجرهٔ قابل‌تنظیم (پیش‌فرض ۶۰ دقیقه) قابلِ ویرایش می‌ماند، دقیقاً مثلِ reconsolidationِ زیستی. رویِ dataset واقعیِ VSCode issue-tracking (۱۳۱۲۷ ایشو / ۱۲۰هزار رویداد): consolidation+forgetting به **۹۷.۲٪ دقتِ نگه‌داشت با ۵۸٪ کاهشِ حجمِ ذخیره** رسید (در برابر ۷۵.۴٪ baselineِ «همه‌چیز را نگه‌دار»)؛ نرخِ decayِ بهینه λ=۰.۰۰۱ (نیمه‌عمر ≈۲۹ روز) بود — یافتهٔ جالب اینکه ایجنت‌های تولیدی افقِ حافظهٔ **طولانی‌تر از سیکل روزانهٔ بیولوژیک انسان** لازم دارند؛ نیمه‌عمر باید با ریتمِ دامنه هم‌تراز شود نه لزوماً «شبانه». این مقاله همچنین یک هشدارِ روش‌شناختی مهم دارد: thresholdهای retrieval را با «synthetic calibration» (نه tuning روی خودِ benchmark ارزیابی) تعیین کرده تا از «threshold leakage» جلوگیری کند.

**Graph-based Agent Memory: Taxonomy, Techniques, and Applications** ([arXiv 2602.05665](https://arxiv.org/abs/2602.05665)) از زاویهٔ ساختارِ ذخیره‌سازی (نه زمان) به همان نتیجه می‌رسد: گراف به‌خاطرِ توانِ مدل‌کردنِ وابستگیِ رابطه‌ای و سلسله‌مراتب، ستون فقراتِ خوبی برای هر دو لایهٔ episodic/semantic است. taxonomyِ چهارعملیاتی‌اش (extraction → storage → retrieval → **evolution**) عملاً معادلِ همان چرخهٔ fast-write/slow-consolidate/decay است، فقط با تمرکز بر گراف به‌جای فایلِ تخت — نکتهٔ عملی برای vault ما: اگر روزی حجمِ لینک‌های wikilink/backlink زیاد شد، لایهٔ semantic را می‌شود به‌جای نوت‌های تخت، گراف مدل کرد.

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

**SleepGate** ([arXiv 2603.14517](https://arxiv.org/abs/2603.14517)) مسئلهٔ مکملِ فراموشی را از زاویهٔ *proactive interference* می‌بیند: وقتی اطلاعاتِ منسوخ در context می‌ماند، بازیابیِ مقدارِ درستِ فعلی را مختل می‌کند (مثلاً کاربر آدرس/تصمیمش را عوض کرده ولی مقدارِ قدیم هنوز رقابت می‌کند). راه‌حل: میکروسیکل‌های «خواب» تناوبی (trigger با سیگنالِ آنتروپی) که سه کار می‌کنند — تشخیصِ تعارض با یک برچسب‌زنِ زمانی، فراموشیِ انتخابیِ ورودی‌های منسوخ با یک gateِ یادگرفته‌شده، و ادغامِ بازمانده‌ها در خلاصه‌های فشرده. روی یک ترنسفورمرِ کوچک، دقتِ بازیابی از زیرِ ۱۸٪ (baseline) به ۹۹.۵٪ می‌رسد. برای این نوت، شاهدِ دیگری است که فراموشی فقط «کم‌امتیاز کردنِ قدیمی» نیست؛ **تشخیصِ تعارض/منسوخ‌شدگی** یک مکانیزمِ جدا لازم دارد — دقیقاً همان چیزی که STALE (بند ۴) هم می‌گوید.

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

شاهدِ کمی‌ِ تازه از **Diagnosing Retrieval vs. Utilization Bottlenecks in LLM Agent Memory** ([arXiv 2603.02473](https://arxiv.org/abs/2603.02473)): این مطالعه سه write-strategy (raw chunk، fact-extraction، summarization) را در برابر سه retrieval-method (cosine، BM25، hybrid+rerank) می‌آزماید و نتیجه می‌گیرد **retrieval method فاکتورِ غالب است، نه write strategy** — دقتِ میانگین بین روش‌های retrieval تا ۲۰ امتیاز فرق می‌کند (۵۷.۱٪ برای BM25 تنها تا ۷۷.۲٪ برای hybrid+rerank)، در حالی‌که بین استراتژی‌های نوشتن فقط ۳ تا ۸ امتیاز. حتی ذخیرهٔ خامِ chunk (بدون هیچ فراخوانیِ اضافیِ LLM) با گزینه‌های پیچیده‌تر رقابت می‌کند. درسِ عملی برای این نوت: اگر بودجهٔ مهندسی محدود است، **اول روی کیفیتِ retrieval (hybrid+rerank) سرمایه‌گذاری کن، نه روی پیچیده‌تر کردنِ فاز نوشتن/distill** — تأییدی بر تأکیدِ این نوت که «بیشترِ سرمایه‌گذاری در کیفیتِ retriever و rerank است».

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

عددِ تجربیِ اضافه برای اهمیتِ همین جدول: **Adaptive Memory Admission Control / A-MAC** ([arXiv 2603.04549](https://arxiv.org/abs/2603.04549)) نشان می‌دهد نگه‌داشتِ حافظه را باید یک تصمیمِ ساختاریافته کرد نه محصولِ جانبیِ یک LLM-driven policyِ مبهم: پنج فاکتورِ مکمل (future utility، factual confidence، semantic novelty، temporal recency، content-type prior) با یک ارزیابیِ سبکِ LLM ترکیب می‌شود؛ روی LoCoMo به F1=۰.۵۸۳ با **۳۱٪ کاهشِ لتنسی** نسبت به سیستم‌های LLM-native می‌رسد و «content-type prior» تأثیرگذارترین فاکتور شناخته می‌شود. همسو با همان اصلِ همین نوت: هرچه معیارِ admission/decay صریح‌تر و قابل‌ممیزی‌تر باشد، بهتر از یک LLM که هر بار «تصمیم می‌گیرد چه چیزی بماند» عمل می‌کند.

هشدارِ مکملِ فراموشی از **STALE** ([arXiv 2605.06527](https://arxiv.org/abs/2605.06527)): مشکل فقط این نیست که چه‌چیز نگه داریم، بلکه اینکه آیا agent می‌فهمد یک حافظهٔ نگه‌داشته‌شده دیگر **معتبر نیست** (Implicit Conflict — رخدادِ بعدی، بی‌آنکه صریحاً negation کند، باورِ قبلی را باطل می‌کند). حتی بهترین مدل‌ها فقط ۵۵.۲٪ دقت روی این تشخیص دارند. یعنی «decay امتیاز» تنها بعدِ forgetting نیست؛ یک بعدِ جداگانه — **invalidation/staleness-detection** — هم لازم است که این نوت باید صریحاً از آن به‌عنوان کارِ آینده یاد کند. **Memora/FAMA** ([arXiv 2604.20006](https://arxiv.org/abs/2604.20006)) همین را با متریکِ Forgetting-Aware Memory Accuracy می‌سنجد و نشان می‌دهد memory agentهای فعلی مکرراً به حافظهٔ منسوخ متکی می‌مانند — تأییدی مستقل بر ضرورتِ این بعدِ سوم.

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

نکتهٔ مهمِ اضافه از **Memory as Metabolism: A Design for Companion Knowledge Systems** ([arXiv 2604.12034](https://arxiv.org/abs/2604.12034)) — این مقاله دقیقاً همین سناریو را هدف گرفته: یک سیستمِ حافظهٔ LLM تک‌کاربره («companion») که روی یک ویکیِ دانشِ شخصی می‌نشیند، همان الگوی EXPERIENCE-LEDGER+consolidator ما. پنج عملیاتِ پیشنهادی‌اش — **TRIAGE, DECAY, CONTEXTUALIZE, CONSOLIDATE, AUDIT** — نقشهٔ راهِ خوبی برای نام‌گذاریِ فازهای consolidator ماست. هشدارِ اصلی‌اش: **entrenchment under user-coupled drift** — وقتی یک تفسیرِ غالب (مثلاً یک تصمیمِ قدیمی در PROJECT.md) به‌مرور centrality/اعتبار زیادی می‌گیرد، حتی شواهدِ متناقضِ بعدی نمی‌توانند آن را برگردانند مگر با فشارِ تجمعیِ چند-چرخه‌ای. راه‌حلش «minority-hypothesis retention» است: تفسیرِ اقلیت را کنار نگه دار (حذف نکن) تا اگر شواهدِ بعدی جمع شد، بتواند centrality را پس بگیرد. این مستقیماً به قاعدهٔ اساسیِ vault («هرگز حذف نکن») و به بندِ AUDIT زیر می‌خورد — یک `AUDIT` دوره‌ای باید صراحتاً چک کند که آیا یک نتیجه‌گیریِ قدیمیِ پرامتیاز، در برابرِ شواهدِ تازه‌تر مقاومت کاذب می‌کند یا نه.

پیشنهاد ارتقا به **دوفازی (fast-write / slow-consolidate)**، سازگار با قواعد vault («هرگز حذف نکن؛ فقط منتقل کن» و «append تاریخ‌دار، نه بازنویسی مخرب»):

**فاز ۱ — Fast write (روزانه، ارزان، append-only):**
- EXPERIENCE-LEDGER می‌شود لایهٔ **episodic خام**: هر ورودی با `created`, provenance (لینک به لاگ پروژه/پیام تلگرام)، و تگ salience اولیه. append-only، هیچ‌وقت in-place بازنویسی نمی‌شود.
- هیچ distillِ سنگینی اینجا نزن؛ فقط تگ و امتیازِ اولیه. (منطق RecMem/2605.16045: eager consolidation ممنوع.)

**فاز ۲ — Slow consolidate (شبانه/هفتگی، gate‌شده):**
- یک پاس آفلاین (هم‌تراز با «جاروی روزانه» و Weekly Review). ورودی‌اش یک **working region** از لجر است که فقط **read-only** خوانده می‌شود (الگوی Auto-Dreamer/2605.20616).
- شرط trigger: فقط وقتی **تکرار/خوشهٔ معنایی** یا حجمِ کافی جمع شده (نه بعد از هر آیتم). این gate از افت‌کیفیتِ 2605.12978 جلوگیری می‌کند.
- خروجی: نوت‌های **semantic** جدید در `07 - Knowledge` (طبق درخت تصمیم بند c: `created_by: agent` + ≥۲ منبع)، که episodeهای خام را **supersede** می‌کنند اما پاک نمی‌کنند — خام در لجر می‌ماند، فقط امتیازش پایین می‌آید. این دقیقاً معادلِ vaultیِ «منتقل کن، حذف نکن» است.

**لایهٔ core:**
- یک بلوکِ کوچکِ پایدار (مثلاً در PROJECT.md → `## Active Context`، یا یک نوت persona) که فقط تصمیم‌ها و قواعد واقعاً پایدار را دارد؛ ویرایش صریح و traceable، نه محصولِ خودکارِ consolidator. حساس‌ها اینجا نروند (کاهش AER طبق 2606.10062؛ و طبق بند ۱۰ امنیت، secret هرگز).

**forgetting «امتیاز نه داده» (بند ۴ این نوت روی vault ما):**
- به هر ورودیِ لجر یک امتیاز `I = α·recency + β·frequency + γ·similarity` بده؛ با decay نمایی کم شود.
- **هیچ فایلی حذف نشو.** وقتی لجر بیش‌ازحد بزرگ شد، کم‌امتیازترین‌ها به `_Archive` منتقل شوند (نه delete) — کاملاً منطبق بر قاعدهٔ اساسیِ vault. بازیابیِ مکرر (F) خودبه‌خود مهم‌ها را در لایهٔ فعال نگه می‌دارد.

**retrieval هیبرید برای خودِ consolidator و برای پرس‌وجوها:**
- ripgrep موجود = لایهٔ lexical (نقشِ BM25). یک ایندکسِ vectorِ سبک روی نوت‌ها = لایهٔ semantic. ادغام با RRF ساده، و در صورت نیاز یک rerankِ سبک با خودِ مدل. این مخصوصاً برای پیدا کردن «آیا این episode قبلاً distill شده؟» قبل از ساخت نوتِ semantic حیاتی است (جلوگیری از تکرار، هم‌راستا با dedupِ بند ۹).

**بعدِ سومِ فراموشی — staleness، نه فقط decay:**
- طبق STALE (2605.06527) و Memora/FAMA (2604.20006)، امتیازِ پایین به‌تنهایی کافی نیست؛ باید علامت‌گذاریِ صریحِ «این episode/semantic-note دیگر معتبر نیست» هم باشد (مثلاً وقتی PROJECT.md یک تصمیم را عوض می‌کند، episodeهای مبتنی‌بر تصمیمِ قدیم باید تگِ `superseded` بگیرند، نه فقط امتیازِ پایین‌تر). این برای vault ما یعنی: هر بار Active Context یک تصمیم را برمی‌گرداند، consolidator باید episodeهای مرتبط را به‌جای صرفاً decay، صریحاً `status: superseded` بزند (append، نه overwrite).

**AUDIT دوره‌ای (وامِ مفهومی از Memory as Metabolism/2604.12034):**
- هر مرور هفتگی، یک چکِ صریح بزن: آیا یک تصمیم/تفسیرِ قدیمیِ پرامتیاز (مثلاً یک بندِ Active Context) صرفاً به‌خاطرِ سابقه/تکرار در برابرِ شواهدِ تازه‌تر مقاومت کاذب می‌کند؟ («entrenchment under drift»). اگر بله، آن را `superseded` بزن، ولی نسخهٔ اقلیت/قدیمی را نگه دار (minority-hypothesis retention) نه حذف — دقیقاً هم‌راستا با «هرگز حذف نکن».

**معیار موفقیت این ارتقا:** لجر هرگز کوچک/مخرب‌بازنویسی نمی‌شود؛ نوت‌های semantic فشرده و باکیفیت‌اند و منبع‌دار؛ کیفیت با گذر زمان **پایدار می‌ماند** (نه منحنیِ بالا-بعد-پایینِ 2605.12978)؛ هیچ داده‌ای حذف نمی‌شود، فقط امتیاز/جایگاهش تغییر می‌کند؛ تصمیم‌هایِ باطل‌شده صریحاً `superseded` علامت می‌خورند نه فقط کم‌امتیاز؛ و AUDIT دوره‌ای مانعِ تثبیتِ کاذبِ نتیجه‌گیری‌های قدیمی می‌شود.

---

### فهرست منابع (همه arXiv واقعی و resolve‌شده)
- Deployment-Time Memorization in Foundation-Model Agents — [2606.10062](https://arxiv.org/abs/2606.10062) *(مرجع لنگرِ خواسته‌شده؛ PR/AER، privacy-utility frontier)*
- Language Models Need Sleep: Self-Modify and Consolidate Memories — [2606.03979](https://arxiv.org/abs/2606.03979)
- Auto-Dreamer: Learning Offline Memory Consolidation — [2605.20616](https://arxiv.org/abs/2605.20616)
- Useful Memories Become Faulty When Continuously Updated by LLMs — [2605.12978](https://arxiv.org/abs/2605.12978)
- Hindsight is 20/20 (Retain/Recall/Reflect) — [2512.12818](https://arxiv.org/abs/2512.12818)
- CraniMem (episodic buffer + KG + scheduled consolidation) — [2603.15642](https://arxiv.org/abs/2603.15642)
- Novel Memory Forgetting Techniques (decay/scoring/budget) — [2604.02280](https://arxiv.org/abs/2604.02280)
- MemGPT: LLMs as Operating Systems (tiered/core) — [2310.08560](https://arxiv.org/abs/2310.08560)
- RecMem: Recurrence-based Consolidation — [2605.16045](https://arxiv.org/abs/2605.16045)
- REMem: Reasoning with Episodic Memory — [2602.13530](https://arxiv.org/abs/2602.13530)
- BMAM: Brain-inspired Multi-Agent Memory — [2601.20465](https://arxiv.org/abs/2601.20465)
- AgeMem: Unified LTM/STM Management — [2601.01885](https://arxiv.org/abs/2601.01885)
- MemTrain: Self-Supervised Context Memory Training — [2606.03197](https://arxiv.org/abs/2606.03197)
- Survey: Memory for Autonomous LLM Agents — [2603.07670](https://arxiv.org/abs/2603.07670)
- Are We Ready For An Agent-Native Memory System? — [2606.24775](https://arxiv.org/abs/2606.24775)
- MemTier: Tiered Memory Architecture for Long-Running AI Agents — [2605.03675](https://arxiv.org/abs/2605.03675) *(۱۴٪ افتِ عملکرد بدون tiering؛ daemonِ ناهم‌زمانِ consolidation)*
- vstash: Local-First Hybrid Retrieval with Adaptive Fusion for LLM Agents — [2604.15484](https://arxiv.org/abs/2604.15484) *(BM25+vector+RRFِ تطبیقی، پیاده‌سازیِ SQLite تک‌فایلی)*
- Agent Memory: Characterization and System Implications of Stateful Long-Horizon Workloads — [2606.06448](https://arxiv.org/abs/2606.06448) *(Stanford/KU Leuven/MIT؛ profiling سیستمیِ ۱۰ معماری؛ construction energy غالب است، تا ۴۷× فرق)*
- Structured Distillation for Personalized Agent Memory: 11× Token Reduction with Retrieval Preservation — [2603.13017](https://arxiv.org/abs/2603.13017) *(۱۰۷ پیکربندیِ retrieval؛ بهترین نتیجه از فیوژنِ متقاطعِ verbatim+BM25 ⊕ distilled+vector با RRF)*
- LightMem: Lightweight and Efficient Memory-Augmented Generation — [2510.18866](https://arxiv.org/abs/2510.18866) *(ICLR 2026؛ الگوی Atkinson-Shiffrin: sensory→short-term→long-term با sleep-time update)*
- SCM: Sleep-Consolidated Memory with Algorithmic Forgetting — [2604.20943](https://arxiv.org/abs/2604.20943) *(NREM/REM دومرحله‌ای؛ ۹۰.۹٪ کاهشِ نویزِ حافظه؛ نقدِ صریحِ MemGPT/Mem0 به‌عنوانِ awake-only)*
- TiMem: Temporal-Hierarchical Memory Consolidation — [2601.02845](https://arxiv.org/abs/2601.02845) *(Temporal Memory Tree؛ SOTA روی LoCoMo/LongMemEval-S با ۵۲٪ کاهشِ طولِ بازیابی)*
- Human-Inspired Memory Architecture for LLM Agents — [2605.08538](https://arxiv.org/abs/2605.08538) *(hot/warm/graph سه‌لایه + reconsolidationِ labile؛ ۹۷.۲٪ retention با ۵۸٪ کاهشِ حجم؛ synthetic calibration ضدِ threshold leakage)*
- Adaptive Memory Admission Control (A-MAC) — [2603.04549](https://arxiv.org/abs/2603.04549) *(admission به‌عنوان تصمیمِ ساختاریافتهٔ پنج‌فاکتوری؛ ۳۱٪ کاهشِ لتنسی روی LoCoMo)*
- STALE: Can LLM Agents Know When Their Memories Are No Longer Valid? — [2605.06527](https://arxiv.org/abs/2605.06527) *(Implicit Conflict/staleness-detection؛ بهترین مدل فقط ۵۵.۲٪ دقت)*
- Memora / Forgetting-Aware Memory Accuracy (FAMA) — [2604.20006](https://arxiv.org/abs/2604.20006) *(بنچمارک هفته‌تا-ماه؛ memory agentها مکرراً به حافظهٔ منسوخ متکی می‌مانند)*
- SleepGate: Sleep-Inspired Memory Consolidation for Resolving Proactive Interference — [2603.14517](https://arxiv.org/abs/2603.14517) *(میکروسیکل‌های خواب با سیگنالِ آنتروپی؛ conflict-detection + gated forgetting + consolidation؛ ۹۹.۵٪ دقتِ بازیابی در برابرِ زیرِ ۱۸٪ baseline)*
- Diagnosing Retrieval vs. Utilization Bottlenecks in LLM Agent Memory — [2603.02473](https://arxiv.org/abs/2603.02473) *(retrieval method فاکتورِ غالب است — ۲۰ امتیاز فرق بین BM25 و hybrid+rerank، فقط ۳-۸ امتیاز بین write-strategyها)*
- Graph-based Agent Memory: Taxonomy, Techniques, and Applications — [2602.05665](https://arxiv.org/abs/2602.05665) *(survey؛ چرخهٔ extraction→storage→retrieval→evolution روی گراف)*
- Memory as Metabolism: A Design for Companion Knowledge Systems — [2604.12034](https://arxiv.org/abs/2604.12034) *(حافظهٔ تک‌کاربرهٔ companion؛ عملیاتِ TRIAGE/DECAY/CONTEXTUALIZE/CONSOLIDATE/AUDIT؛ هشدارِ entrenchment-under-drift + minority-hypothesis retention)*
