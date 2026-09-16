---
type: knowledge
status: active
created_by: agent
created: 2026-07-06
updated: 2026-07-06
tags: [doctor, mutation-ledger, memory]
sources:
  - https://arxiv.org/abs/2605.25338
  - https://arxiv.org/abs/2504.19413
  - https://arxiv.org/abs/2509.25140
  - https://arxiv.org/abs/2605.26252
  - https://arxiv.org/abs/2605.12978
  - https://arxiv.org/abs/2601.18642
  - https://arxiv.org/abs/2606.00619
  - https://arxiv.org/abs/2602.02474
  - https://arxiv.org/abs/2508.19828
  - https://arxiv.org/abs/2605.07242
  - https://arxiv.org/abs/2605.28732
  - https://arxiv.org/abs/2603.11768
  - https://arxiv.org/abs/2512.06749
  - https://arxiv.org/abs/2509.25370
  - https://arxiv.org/abs/2604.11641
  - https://arxiv.org/abs/2606.04990
  - https://arxiv.org/abs/2603.21522
  - https://arxiv.org/abs/2601.07190
  - https://arxiv.org/abs/2606.06240
  - https://arxiv.org/abs/2509.25238
---

# Active Mutation Ledger — از لاگ منفعل شکست تا منبع ترمیم فعال

> پرسش مرکزی: چطور یک ledgerِ شکست را از یک **passive log** («فقط ثبت شد که این trace fail شد») به یک **active repair source** («از همین شکست، یک اصلاح مینیمال و یک دادهٔ supervision می‌سازیم») تبدیل کنیم — بدون اینکه ledger بی‌مرز رشد کند.

این نوت برای طراحی «جهش‌نامهٔ دکتر» (mutation-ledger دکتر) نوشته شده. سه محور: (۱) CausalFlow و counterfactual repair، (۲) تبدیل failure-trace به supervision، (۳) تفاوت append-only log با memoryِ دارای lifecycle سبک Mem0 و مهار رشد.

---

## ۱. مسئله: چرا لاگ خام شکست کافی نیست؟

روال معمول با شکست agent این است: outcome-level feedback («جواب نهایی غلط بود») + یک retry کور یا rewrite کامل. مشکل: این feedback نمی‌گوید **کدام step** مقصر بوده (ambiguous credit assignment). روش‌هایی مثل Reflexion / Self-Refine / Self-Reflection کل trajectory را نقد و بازتولید می‌کنند؛ یعنی رد ذهنی «کجا و چرا شکست» را ایزوله نمی‌کنند و اصلاح‌شان مینیمال نیست ([CausalFlow](https://arxiv.org/abs/2605.25338)).

یک لاگ append-only از این جنس، در بهترین حالت یک **archive** است: خواندنی، ولی نه actionable. برای اینکه ledger «فعال» شود باید سه کار انجام دهد:

1. **attribution:** بگوید کدام stepِ مشخص، cause شکست بوده (نه اینکه فقط بگوید شکست شد).
2. **repair:** یک minimal edit بسازد که همان trace را از fail به success flip کند.
3. **supervision:** آن جفتِ (step غلط → step درست) را به دادهٔ قابل‌آموزش تبدیل کند.

---

## ۲. CausalFlow — ledger به‌مثابهٔ interventional engine

[CausalFlow (Bonagiri و همکاران، UC Davis، ۲۰۲۶)](https://arxiv.org/abs/2605.25338) دقیقاً همین سه‌گانه را پیاده می‌کند. ایدهٔ محوری: به‌جای همبستگی، از **counterfactual intervention** واقعی استفاده کن.

### مدل trace
هر اجرا یک زنجیرهٔ وابسته است: `τ = (s₁, …, s_T)`. هر step به همهٔ stepهای قبل وابسته است (sequential dependency). یک verifier باینری `V(y(τ), x) ∈ {0,1}` می‌گوید trace موفق شد یا نه.

### Causal Responsibility Score (CRS) — قلب attribution
برای هر stepِ کاندید `sᵢ`:
1. مدل `K` جایگزینِ minimally-edited پیشنهاد می‌دهد (`K=3` در آزمایش‌ها؛ بیشتر از این diminishing returns).
2. هر جایگزین را می‌گذارد و **همهٔ stepهای بعدی را re-execute می‌کند** تا اثر propagate شود.
3. `CRS(sᵢ) = 1` اگر **حداقل یک** جایگزین، outcome را از fail به success flip کند.

یعنی CRS یک تست علّیِ واقعی است، نه یک حدسِ log-based. این نکته CausalFlow را از رقیب هم‌زمانش ([DoVer](https://arxiv.org/abs/2512.06749) — Intervention-Driven Auto Debugging، که checkpointing و re-planning در سطح framework می‌خواهد) و از failure-taxonomyها (MAST، Who&When) جدا می‌کند: بدون تغییر framework، فقط با intervention روی trace. DoVer از زاویهٔ دیگری همین حرف را می‌زند: به‌جای اتکا به log ثابت، عمداً یک state/message/route/tool-call را حذف یا perturb می‌کند و رفتار حاصل را می‌بیند — یعنی تأییدِ مستقل بر این‌که «مداخلهٔ counterfactual» در ۲۰۲۶ به یک الگوی مشترک برای attribution در چند تیمِ مستقل تبدیل شده، نه ایدهٔ منحصر یک مقاله.

### تولید اصلاح مینیمال (counterfactual repair)
از میان جایگزین‌هایی که flip کرده‌اند، آنکه **کمترین تغییر** را دارد انتخاب می‌شود. معیار minimality:

```
Minimality(sᵢ, s'ᵢ) = (m / L) · (1 − ½ · (||x|−|y|| / L))
```
که `m` تعداد token-matchهای موقعیتی، `L = max(|x|,|y|)`. اصلاح بهینه:
```
s*ᵢ = argmax Minimality(sᵢ, s'ᵢ)  s.t.  V(y(τ[i←s'ᵢ]), x) = 1
```
نتیجه: minimality score بین **۰.۷۹ تا ۰.۸۷** — یعنی repair یک ویرایش token-level است، نه بازنویسی کل جواب. (روش‌های refine در بعضی benchmarkها minimality تا ۰.۰۱ داشتند، یعنی عملاً کل جواب را دوباره تولید کرده بودند.)

### validation چندعاملی
برای کم‌کردن نویزِ attributionِ LLM-ساخته، سه agent: A پیشنهاد می‌دهد، B نقد می‌کند، C متانقد. یک **Consensus Score** محاسبه می‌شود و فقط stepهایی با `Consensus ≥ 0.5` به‌عنوان causal تأیید می‌شوند. این همان gateای است که مانع ورود هر ادعای ترمیمِ تأییدنشده به ledger می‌شود.

### دو مصرف — همان‌جا که ledger «فعال» می‌شود
- **test-time repair:** همان لحظه، با کمترین behavioral drift، شکست را recover کن. بیشترین سود در taskهای retrieval-heavy: MedBrowseComp ‏**+۳۰.۸ واحد** accuracy، SealQA Hard ‏**+۱۲.۶ واحد**. (Self-Refine/Self-Reflection روی MedBrowseComp حتی **منفی** شدند — نقد سراسری در taskهای پیچیده تخریب می‌کند.)
- **training-time supervision:** هر جفتِ `(sᵢ, s*ᵢ)` یک **contrastive pair** است، آمادهٔ offline preference optimization (مثل DPO) یا reward modeling.

نکتهٔ کلیدی برای ما: در مجموع **۴۲.۷٪** از trailهای شکست‌خورده به repairِ معتبر تبدیل شدند. یعنی «شکست» دیگر یک بن‌بست نیست، یک **feedstock** است.

---

## ۳. Failure-trace → داده supervision (فراتر از CausalFlow)

CausalFlow جفت contrastive می‌سازد؛ اما یک الگوی وسیع‌تر هست: **شکست را مثل موفقیت، شهروند درجه‌یکِ حافظه بدان.**

[ReasoningBank (Google Cloud AI + UIUC، ۲۰۲۵)](https://arxiv.org/abs/2509.25140) دقیقاً این کار را می‌کند. اکثر memory systemها فقط trajectoryهای موفق را ذخیره می‌کنند و درسِ شکست‌ها را دور می‌ریزند. ReasoningBank از هر trajectory — موفق **و** شکست‌خورده — یک memory item ساخت‌یافته (Title / Description / Content) استخراج می‌کند:
- از موفقیت: strategyهای معتبر.
- از شکست: **counterfactual pitfalls و درس‌های پیشگیرانه** («این کار را نکن چون قبلاً fail شد»).

سیگنالِ درست/غلط را یک LLM-as-a-judge می‌دهد (بدون ground-truth). نتیجه: با گنجاندن شکست‌ها، success rate از ۴۶.۵٪ به ۴۹.۷٪ رسید — درحالی‌که baselineها با افزودن شکست‌ها **بدتر** شدند. این تفاوت بین «شکست به‌عنوان نویز» و «شکست به‌عنوان supervision» است.

الگوهای هم‌خانواده که همین جهت را تأیید می‌کنند:
- **MemSkill** ([2602.02474](https://arxiv.org/abs/2602.02474)): یک *designer* دوره‌ای hard caseها (جایی که مهارت فعلی حافظهٔ غلط تولید کرد) را بازبینی و skillها را تکامل می‌دهد — closed loop روی شکست.
- **MemPro** ([2606.00619](https://arxiv.org/abs/2606.00619)): کل pipelineِ حافظه را یک *evolvable program* با version tree می‌بیند؛ یک Evolving Agent شکست‌های تکرارشونده را diagnose و نسخهٔ بهترِ فرزند می‌سازد (failure-mode-guided edit-debug).

### ۳-۰) رقیبِ retrieval-based در برابر generative-repair — PALADIN
[PALADIN (۲۰۲۵)](https://arxiv.org/abs/2509.25238) از زاویهٔ دیگری همان مسئلهٔ محور ۳ را حل می‌کند: به‌جای اینکه هر بار یک LLM را برای ساختنِ اصلاح صدا بزند (مسیر CausalFlow)، اول با **systematic failure injection** روی ToolBench بیش از ۵۰هزار trajectoryِ «recovery-annotated» ساخته (Error-Trajectory Dataset)، بعد در inference یک بانکِ ۵۵+ نمونهٔ شکستِ برچسب‌خورده (طبق taxonomy ToolScan) نگه می‌دارد: هر خطای runtime به نزدیک‌ترین نمونه match می‌شود و **اکشنِ ترمیمِ متناظر** اجرا می‌شود — یعنی repair از طریق retrieval، نه تولید از صفر. مدل با LoRA روی همین دیتاست fine-tune می‌شود تا fault-tolerance را بدون افتِ توانِ پایه یاد بگیرد. برای جهش‌نامهٔ دکتر یعنی: مرحلهٔ ۳ (REPAIR) دو گزینهٔ معماری دارد — «تولید مینیمالِ per-case» (CausalFlow، دقیق‌تر ولی گران‌تر) در برابر «تطبیق با بانکِ exemplar از پیش validated» (PALADIN، ارزان‌تر و قابل‌مقیاس‌تر وقتی الگوهای شکست تکراری‌اند). دوتایی مکمل‌اند: بانکِ exemplarِ PALADIN می‌تواند دقیقاً همان چیزی باشد که از repair-ledgerِ ما، بعد از عبور از VALIDATE، بیرون می‌آید.

یک نکتهٔ محتاطانه از بیرونِ خانوادهٔ repair: [«Where LLM Agents Fail and How They Can Learn From Failures» (۲۰۲۵/۲۰۲۶)](https://arxiv.org/abs/2509.25370) پیش از هر ادعای «یادگیری از شکست»، تأکید می‌کند که خودِ **failure attribution** باید در سطحِ step دقیق باشد وگرنه درسِ استخراج‌شده نویزی خواهد بود — یعنی محور ۲ (CausalFlow) و محور ۳ (ReasoningBank/MemSkill/MemPro) به‌هم وابسته‌اند: بدون attributionِ دقیق، تبدیلِ شکست به supervision صرفاً نویز را به لایهٔ حافظه منتقل می‌کند.

جمع‌بندی محور ۳: **ledgerِ فعال = ledgerی که خروجی‌اش خوراک آموزش/تکامل است، نه فقط بایگانی — و این فقط وقتی درست کار می‌کند که attribution زیرش دقیق باشد.**

### ۳-۱) سه تأییدِ تازهٔ ۲۰۲۶ روی همین ایده (trace → dataset ساخت‌یافته)

- **CodeTracer** ([2604.11641](https://arxiv.org/abs/2604.11641)، آوریل ۲۰۲۶): برای failureهای code-agent، کل تاریخچهٔ state-transition را به یک **trace tree سلسله‌مراتبی** با حافظهٔ پایدار بازسازی می‌کند و «failure onset localization» انجام می‌دهد — یعنی نه‌فقط اینکه کجا fail شد، بلکه زنجیرهٔ downstream را هم مشخص می‌کند. از این کار، **CodeTraceBench** ساخته شده: دیتاستی با supervision هم در سطح stage و هم در سطح step، مستقیماً از trajectoryهای واقعیِ چهار framework کد-agent (bug-fixing، refactoring، terminal interaction). این دقیقاً همان الگوی «failure-trace → دادهٔ supervision ساخت‌یافته» است که محور ۳ ادعا می‌کند، اما این‌بار در دامنهٔ کد و با benchmark عمومی.
- **EAGER** ([2603.21522](https://arxiv.org/abs/2603.21522)، مارس ۲۰۲۶): برای سیستم‌های چندعاملی، یک Representation Model با **Reasoning-Scoped Contrastive Learning** الگوهای reasoning درون‌عامل و بین‌عامل را به یک فضای نهفتهٔ مشترک می‌برد تا تجربه‌های مشابهِ گذشته سریع بازیابی شوند. نکتهٔ مرتبط با ledger: وقتی خروجیِ نهایی توسط کاربر «غلط» تأیید شد، یک چرخهٔ «Expert Inspect + Agent RCA» هم دانشِ شکستِ سطح-عامل و هم سطح-سیستم را **به‌روزرسانی** می‌کند — یعنی یک نمونهٔ دیگر از lifecycle-write (نه صرفاً append) روی دانشِ شکست.
- **«From Agent Traces to Trust» (سروِی)** ([2606.04990](https://arxiv.org/abs/2606.04990)، ژوئن ۲۰۲۶): این سروِی یک taxonomy برای کل میدان می‌سازد — trace source، evidence/execution unit، و جهت‌های روشیِ provenance representation / evidence attribution / failure diagnosis. برای جهش‌نامهٔ دکتر مفید است چون واژگان مشترکِ CausalFlow/CodeTracer/MemTrace/EAGER را در یک framework می‌گذارد و تأیید می‌کند که «تبدیل trace به دادهٔ قابل‌اعتماد» در ۲۰۲۶ به یک زیرحوزهٔ مستقل تبدیل شده، نه یک ترفندِ تک‌مقاله‌ای.

---

## ۴. Append-only log در برابر memory دارای lifecycle (سبک Mem0)

اینجا هستهٔ تصمیم معماری برای جهش‌نامهٔ دکتر است.

### الف) append-only log
- **مزیت:** ساده، idempotent، audit-friendly، بدون تخریب مخرب.
- **عیب:** بی‌مرز رشد می‌کند؛ ورودی‌های کهنه/متناقض کنار هم می‌مانند؛ retrieval پرنویز می‌شود.

[«Is Agent Memory a Database?» (Orogat & Mansour، ۲۰۲۶)](https://arxiv.org/abs/2605.26252) چهار **failure mode** حافظهٔ record-level را نام می‌برد که مستقیماً بیماری‌های append-only log هستند:
1. **unregulated growth** (رشد بی‌مهار)
2. **missing semantic revision** (نبود بازنگری معنایی)
3. **capacity-driven forgetting** (فراموشیِ ظرفیت‌محور، نه ارزش‌محور)
4. **read-only retrieval** (بازیابیِ فقط‌خواندنی)

پیشنهادشان **Governed Evolving Memory (GEM)** با چهار operatorِ سطح-state است: `ingestion / revision / forgetting / retrieval`. نکتهٔ فلسفیِ مهم: **درستیِ حافظه، خاصیتِ trajectoryِ state است، نه خاصیتِ تک‌رکورد.** یعنی یک log که فقط رکورد اضافه می‌کند، ذاتاً نمی‌تواند این شش شرطِ درستی را برآورده کند.

### ب) memory دارای lifecycle — مدل Mem0
[Mem0 (Chhikara و همکاران، ۲۰۲۵)](https://arxiv.org/abs/2504.19413) به‌جای append، در **Update Phase** برای هر factِ کاندید، top-s حافظهٔ مشابه را می‌کشد و خودِ LLM از طریق یک tool-call یکی از این چهار عمل را انتخاب می‌کند:

| عمل | چه وقت | اثر روی ledger |
|---|---|---|
| **ADD** | factِ نو و مجزا | رشد کنترل‌شده |
| **UPDATE** | مکمل حافظهٔ موجود | ادغام، نه تکثیر |
| **DELETE** | متناقض با فکت جدید | حذف/ابطالِ کهنه |
| **NOOP** | چیزی برای تغییر نیست | صفر رشد |

نتیجهٔ عملی Mem0: مصرف حافظه ~۷k توکن در هر مکالمه در برابر ۲۶k توکنِ کل متن خام و ۶۰۰k توکنِ یک رقیب (Zep) — یعنی lifecycle عملاً رشد را **دو مرتبه‌ای** مهار می‌کند، به‌علاوهٔ ۹۱٪ کاهش p95 latency نسبت به full-context. در نسخهٔ گرافی، رابطه‌های کهنه به‌جای حذف فیزیکی **invalid mark می‌شوند** تا temporal reasoning حفظ شود — نکته‌ای که با قاعدهٔ «هرگز حذف نکن، فقط منتقل/ابطال کن» vaultِ ما هم‌راستاست.

### ب-۱) وقتی تصمیمِ lifecycle خودش learned می‌شود — Memory-R1
[Memory-R1 (۲۰۲۵)](https://arxiv.org/abs/2508.19828) همان چهارتاییِ Mem0 (`ADD/UPDATE/DELETE/NOOP`) را نگه می‌دارد اما انتخاب عمل را به‌جای heuristic ثابت، به یک **Memory Manager آموزش‌دیده با RL** (PPO/GRPO، outcome-driven reward) می‌سپارد؛ یک Answer Agent جدا هم فقط رکوردهای مرتبط را برای پاسخ انتخاب می‌کند. نکتهٔ مهم برای ما: انتخاب ADD در برابر UPDATE در برابر DELETE می‌تواند خودش یک **سیاستِ قابل‌یادگیری از بازخورد outcome** باشد، نه فقط یک قاعدهٔ دستی — یعنی مرحلهٔ ۵ پایپ‌لاین ما (LIFECYCLE-WRITE) در بلندمدت کاندید تبدیل‌شدن به یک policy آموزش‌دیده است، نه صرفاً یک if/else.

### ب-۰.۵) وقتی خطا در خودِ لایهٔ حافظه رخ داده — MemTrace
اگر CausalFlow روی attributionِ شکستِ reasoning/action تمرکز دارد، [MemTrace (Deng, Zhong, Zhang و همکاران، مه ۲۰۲۶)](https://arxiv.org/abs/2605.28732) یک لایهٔ مکمل و باریک‌تر را هدف می‌گیرد: خطاهایی که ریشه‌شان **خودِ سیستم حافظه** است — یعنی storage، retrieval، یا integration معیوب. این کار trace‌های اجراییِ annotate‌شده با faulty-operation-id، نوع خطا و توضیح می‌سازد تا خطا را دقیقاً به فاز مقصر (نوشتن غلط؟ بازیابیِ نامرتبط؟ ادغامِ اشتباه؟) نسبت دهد. برای جهش‌نامهٔ دکتر یعنی: وقتی شکست از خودِ ledger/lifecycle-writer می‌آید (نه از تصمیمِ اصلیِ agent)، باید attributionِ جدا داشته باشیم — «باگ در حافظه» با «باگ در reasoning» یک نوع repair نمی‌خواهند.

### ب-۱.۵) قراردادِ صریح برای «حذف» — TOKI
[TOKI (Wang، HKUST، ژوئن ۲۰۲۶)](https://arxiv.org/abs/2606.06240) دقیقاً روی نقطه‌ای انگشت می‌گذارد که Mem0/GEM آن را صریح نمی‌کنند: وقتی یک فکتِ نو با یک فکتِ ذخیره‌شده تناقض دارد، **کدام قاعده برنده می‌شود و چرا؟** این مقاله چهار heuristic رایجِ صنعتی را نام می‌برد — last-writer-wins، evidence-weighted merge، await-confirmation، per-rule policy — و نشان می‌دهد هیچ‌کدام سطح ایزولاسیون یا anomalyِ زمانِ نوشتن را که می‌پذیرند اعلام نمی‌کنند. راه‌حل: یک جبرِ عملگرِ **bitemporal** (transaction-time × valid-time) روی یک schemaِ dual-row، به‌طوری‌که فکتِ بازنده هرگز physically حذف نمی‌شود بلکه در یک **audit row** با provenance نگه داشته می‌شود — دقیقاً معادلِ «ابطال به‌جای حذف فیزیکی» که در Mem0 گرافی و در قانون خودِ vault دیدیم. نکتهٔ اضافه‌ای که TOKI می‌آورد: DELETE در پایپ‌لاین ما (مرحلهٔ ۵) باید بگوید **کدام heuristicِ تناقض‌حل‌کنی** را اجرا می‌کند (مثلاً: آخرین repairِ تأییدشده برنده است، مگر consensus-score قدیمی بالاتر باشد) — یعنی DELETE/UPDATE را از یک تصمیمِ ضمنی به یک قراردادِ صریح و قابل‌بازرسی تبدیل کند.

### ب-۲) وقتی خودِ ledger نیاز به repair دارد — cascade invalidation
مشکلی که Mem0/GEM کمتر به آن می‌پردازند: وقتی یک رکوردِ منبع (source fact) بعداً **باطل یا اصلاح** شود، هر چیزی که از آن مشتق شده (خلاصه، skill آموخته‌شده، رکورد repair مشتق) ممکن است stale بماند و دیده شود. [MemoRepair (۲۰۲۶)](https://arxiv.org/abs/2605.07242) این را «**cascade update problem**» می‌نامد و یک قرارداد barrier-first پیشنهاد می‌دهد: اول همهٔ فرزندانِ متأثر از سرویس خارج (withdraw) می‌شوند، بعد جانشین‌ها فقط از میانِ support معتبرِ پس‌رویداد و پیشینیانِ ترمیم‌شده ساخته می‌شوند، و **انتشارِ مجدد فقط برای جانشینِ کاملاً predecessor-closed مجاز است.** برای جهش‌نامهٔ دکتر یعنی: اگر یک درسِ پایه (root lesson) در repair-ledger باطل شد، هر جفتِ contrastive یا skill مشتق‌شده از آن هم باید به‌جای ماندنِ خاموش، صراحتاً withdraw و بازسازی شود — وگرنه ledger پر از derived-artifactهای یتیم می‌ماند که هیچ‌کس دیگر منبعشان را چک نمی‌کند.

### هشدار مهم: UPDATE بی‌گیت، حافظه را فاسد می‌کند
[«Useful Memories Become Faulty When Continuously Updated by LLMs» (Zhang و همکاران، ۲۰۲۶)](https://arxiv.org/abs/2605.12978): اگر consolidation/UPDATE بعد از **هر** تعامل شلیک شود، utility اول بالا می‌رود بعد **پایین‌تر از baselineِ بی‌حافظه** می‌افتد. در یک آزمایش، ۵۴٪ از مسائلی که قبلاً حل شده بودند بعد از consolidation دوباره fail شدند. توصیهٔ صریح مقاله: **raw episodes را first-class evidence نگه‌دار و consolidation را explicitly gate کن، نه اینکه خودکار بعد از هر رویداد اجرا شود.**

پیامد برای معماری دکتر: **hybrid**. یک لایهٔ append-only از episodeهای خام (شواهد دست‌نخورده، برگشت‌پذیر) + یک لایهٔ consolidatedِ گیت‌دار با lifecycle. نه فقط append، نه UPDATEِ حریص.

### ب-۳) تأییدِ مستقل معماری hybrid — SSGM
[SSGM — Stability and Safety Governed Memory (Lam, Li, Zhang, Zhao، دانشگاه Jinan، مارس ۲۰۲۶)](https://arxiv.org/abs/2603.11768) از زاویهٔ ریسک به همین جمع‌بندی می‌رسد. این مقاله چهار دستهٔ شکستِ حافظهٔ evolving را نام می‌برد: **Stability** (semantic/procedural/goal drift از تکرارِ summarization)، **Validity** (hallucination + temporal obsolescence — فکت‌های کهنهٔ متناقض)، **Efficiency** (retrieval latency و index bloat — همان چیزی که رشدِ بی‌مرز تولید می‌کند)، و **Safety** (memory poisoning، نشتِ حریم خصوصی در چندعاملی).

راه‌حل پیشنهادیِ SSGM چهار اصل است که با طرح ما هم‌پوشانیِ مستقیم دارد:
1. **Pre-Consolidation Validation:** یک Truth Maintenance System پیش از ذخیره چک می‌کند آیا آپدیت با فکت‌های هسته تناقض دارد — معادلِ VALIDATE/consensus-gate ما.
2. **Temporal & Provenance Grounding:** decay تابع Weibull + اثبات provenance رمزنگاری‌شده برای فیلترکردن داده‌های کهنه — معادلِ DECAY/CONSOLIDATE ما.
3. **Access-Scoped Retrieval:** کنترل دسترسیِ هویت‌محور، مانعِ آلودگیِ متقابل بین عامل‌ها.
4. **Reversible Reconciliation:** جفت‌کردنِ یک گراف فعالِ mutable با یک لاگِ اپیزودیکِ immutable، به‌طوری‌که drift به‌صورت دوره‌ای در برابر منبع اصلی اصلاح شود.

نکتهٔ مهم: اصل ۴ (Reversible Reconciliation) دقیقاً همان معماری دو-لایه‌ای است که ما از تقابل Mem0 در برابر «Useful Memories Become Faulty» استخراج کردیم — این‌جا از یک تیم کاملاً مستقل، با انگیزهٔ ریسک/safety (نه performance)، به همان نتیجه رسیده‌اند: **حافظهٔ mutable هرگز نباید تنها نسخهٔ حقیقت باشد؛ همیشه یک لنگرِ immutable لازم است که بشود به آن reconcile کرد.**

---

## ۵. مهار رشد بی‌مرز ledger — جعبه‌ابزار

جمع رویکردها برای اینکه ledger منفجر نشود:

1. **Minimality-first repair (CausalFlow):** هر ورودیِ اصلاح یک token-level diff است، نه یک بازنویسی کامل → حجمِ هر رکورد کوچک.
2. **Consensus-gate (CausalFlow):** فقط repairهای validated (Consensus ≥ 0.5) وارد ledger می‌شوند → نرخ ورود کنترل می‌شود.
3. **Lifecycle operators (Mem0 / GEM):** DELETE + UPDATE + NOOP رشد را از خطی به sub-linear می‌آورند.
4. **Gated consolidation (Zhang و همکاران):** consolidation را زمان‌بندی‌شده و مشروط اجرا کن، نه هر تعامل.
5. **Biologically-inspired forgetting (FadeMem، [2601.18642](https://arxiv.org/abs/2601.18642)):** decayِ نمایی تطبیقی + salience (relevance، فرکانس دسترسی، الگوی زمانی) + consolidation با conflict-resolution → **۴۵٪ کاهش storage** بدون افت روی multi-hop. یعنی «فراموشیِ ارزش‌محور» جایگزین «فراموشیِ ظرفیت‌محورِ» بد می‌شود.
6. **Version-tree pruning (MemPro):** به‌جای انباشتِ خطی، نسخه‌های ضعیف هرس می‌شوند و فقط شاخهٔ برنده می‌ماند.
7. **Sawtooth consolidate-and-collapse (Active Context Compression، [2601.07190](https://arxiv.org/abs/2601.07190)):** یک الگوی تازهٔ ژانویهٔ ۲۰۲۶، الهام‌گرفته از استراتژیِ کاوشِ کپک-لجنیِ *Physarum polycephalum*. خودِ agent (نه یک summarizer بیرونی) تصمیم می‌گیرد کِی sub-task تمام شده یا به بن‌بست خورده؛ آن‌وقت یک خلاصه به بلوکِ پایدارِ «Knowledge» اضافه می‌کند و **همهٔ پیام‌های بینِ آن checkpoint و اکنون را حذف می‌کند**. نتیجه: به‌جای لاگِ یکنواخت رو-به-رشد، یک الگوی «دندانه‌اره‌ای» (رشد حین کاوش، فروریزش حین consolidation). تفاوت کلیدی با Mem0/GEM: کنترلِ pruning دستِ خودِ عامل است، نه یک فرایند بیرونیِ heuristic — نکته‌ای که برای مرحلهٔ ۷ پایپ‌لاین ما (DECAY/CONSOLIDATE) گزینهٔ جایگزین «self-triggered checkpoint» را مطرح می‌کند، در کنارِ زمان‌بندیِ دوره‌ایِ بیرونی.

اصل حاکم: **رشد باید تابع ارزشِ اطلاعاتی باشد، نه تابعِ زمان.** یک ledgerِ فعالِ سالم، در حالت پایدار **همگرا** می‌شود، نه اینکه بی‌نهایت رشد کند.

---

## ۶. طرح FAILURE→REPAIR برای جهش‌نامهٔ دکتر ما

خلاصهٔ اجرایی؛ ترکیبِ CausalFlow (attribution+repair) + Mem0-lifecycle (مهار رشد) + گیتِ consolidation (ضدفساد).

**پایپ‌لاین هفت‌مرحله‌ای (هر شکستِ دکتر از این تسمه‌نقاله رد می‌شود):**

1. **CAPTURE (append-only, idempotent):** هر شکست به‌صورت یک episodeِ خامِ تاریخ‌دار ثبت می‌شود. این لایه دست‌نخورده و برگشت‌پذیر است — «first-class evidence». پیش از ثبت، dedup با شناسهٔ یکتا (سبک `message_id`).
2. **ATTRIBUTE (CRS):** با counterfactual intervention، stepِ مقصر پیدا می‌شود. اگر هیچ intervention آن را flip نکرد → این شکست **غیرقابل‌ترمیمِ محلی** است (مثلاً اطلاعات لازم اصلاً وجود ندارد) → فقط به‌عنوان episode می‌ماند، وارد repair-ledger نمی‌شود. attribution باید تشخیص دهد شکست از **reasoning عامل** آمده یا از **خودِ لایهٔ حافظه** (سبک MemTrace) — دو مسیر repair متفاوت می‌خواهند.
3. **REPAIR (minimal):** کوچک‌ترین editای که outcome را flip کند تولید و انتخاب می‌شود → جفتِ `(step غلط → step درست)`. دو مسیر ممکن: تولید per-case (CausalFlow) یا تطبیق با بانکِ exemplarِ از‌پیش‌validated (PALADIN) — دومی برای الگوهای شکستِ تکراری ارزان‌تر است.
4. **VALIDATE (consensus-gate):** repair با re-execution و اجماع چندعاملی تأیید می‌شود. زیر آستانه → دور ریخته می‌شود، وارد ledger نمی‌شود.
5. **LIFECYCLE-WRITE (ADD/UPDATE/DELETE/NOOP):** جفتِ تأییدشده در برابر ledger موجود سنجیده می‌شود:
   - نو و مجزا → **ADD**
   - مکملِ یک درسِ موجود → **UPDATE**
   - نقض‌کنندهٔ یک درسِ کهنه → **DELETE/invalidate** (ابطال، نه حذف فیزیکی — همسو با قاعدهٔ vault؛ طبق TOKI باید مشخص شود کدام heuristicِ تناقض‌حل‌کنی برنده تعیین می‌کند، و فکتِ بازنده در یک audit row با provenance می‌ماند)
   - تکراری → **NOOP**
   - (مسیر بلندمدت: این تصمیم می‌تواند مثل Memory-R1 به یک policyِ آموزش‌دیده با outcome-reward تبدیل شود، نه فقط heuristic.)
   - **اگر یک درسِ ریشه باطل شد:** طبق الگوی barrier-first MemoRepair، هر رکورد/skillِ مشتق‌شده از آن باید صراحتاً withdraw و سپس از support معتبرِ پس‌رویداد بازسازی شود — نه اینکه صامت stale بماند.
6. **SUPERVISE:** جفت‌های تأییدشده به‌صورت دسته‌ای (نه بعد از هر رویداد — gated) به دو کانال می‌روند: (الف) contrastive dataset برای preference optimization/reward، (ب) درس‌های failure-aware سبک ReasoningBank برای تزریق در promptِ آینده.
7. **DECAY/CONSOLIDATE (زمان‌بندی‌شده):** به‌صورت دوره‌ای — نه پیوسته — forgettingِ ارزش‌محور (salience × decay) اجرا می‌شود و درس‌های هم‌خانواده fuse می‌شوند. این مرحله رشد را همگرا نگه می‌دارد.

**پنج قاعدهٔ طلایی طرح:**
- **شکست = feedstock، نه بن‌بست.** هر fail یا repair می‌شود یا (اگر غیرقابل‌ترمیم) به‌عنوان درسِ پیشگیرانه می‌ماند.
- **دو لایه:** episodeِ خامِ append-only (شاهد) + repair-ledgerِ دارای lifecycle (دانش فعال). هرگز فقط یکی.
- **هر ورودی minimal و validated.** بدون consensus-gate، ledger پر از نویز می‌شود.
- **UPDATE/consolidation همیشه gated.** پیوسته‌سازیِ حریص، حافظهٔ خوب را فاسد می‌کند (شواهد: ۵۴٪ regression).
- **رشد تابع ارزش است، نه زمان.** DELETE/invalidate + forgettingِ salience-محور تضمین می‌کنند ledger همگرا شود.

**معیارهای سلامت که باید پایش شوند:** repair-rate (چند درصد شکست‌ها ترمیم شد؟)، minimality-score (اصلاح‌ها کوچک‌اند؟)، growth-rate ledger (خطی است یا sub-linear؟)، و post-consolidation utility (آیا utility بعد از هر consolidation بالا ماند یا افتاد؟).

---

*منابع کلیدی: CausalFlow ([2605.25338](https://arxiv.org/abs/2605.25338)) · DoVer ([2512.06749](https://arxiv.org/abs/2512.06749)) · «Where LLM Agents Fail…» ([2509.25370](https://arxiv.org/abs/2509.25370)) · PALADIN ([2509.25238](https://arxiv.org/abs/2509.25238)) · Mem0 ([2504.19413](https://arxiv.org/abs/2504.19413)) · ReasoningBank ([2509.25140](https://arxiv.org/abs/2509.25140)) · GEM/«Is Agent Memory a Database?» ([2605.26252](https://arxiv.org/abs/2605.26252)) · TOKI ([2606.06240](https://arxiv.org/abs/2606.06240)) · «Useful Memories Become Faulty…» ([2605.12978](https://arxiv.org/abs/2605.12978)) · FadeMem ([2601.18642](https://arxiv.org/abs/2601.18642)) · MemPro ([2606.00619](https://arxiv.org/abs/2606.00619)) · MemSkill ([2602.02474](https://arxiv.org/abs/2602.02474)) · Memory-R1 ([2508.19828](https://arxiv.org/abs/2508.19828)) · MemoRepair ([2605.07242](https://arxiv.org/abs/2605.07242)) · MemTrace ([2605.28732](https://arxiv.org/abs/2605.28732)) · SSGM ([2603.11768](https://arxiv.org/abs/2603.11768)) · CodeTracer ([2604.11641](https://arxiv.org/abs/2604.11641)) · EAGER ([2603.21522](https://arxiv.org/abs/2603.21522)) · «From Agent Traces to Trust» ([2606.04990](https://arxiv.org/abs/2606.04990)) · Active Context Compression ([2601.07190](https://arxiv.org/abs/2601.07190)).*
