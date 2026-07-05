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

یک نکتهٔ محتاطانه از بیرونِ خانوادهٔ repair: [«Where LLM Agents Fail and How They Can Learn From Failures» (۲۰۲۵/۲۰۲۶)](https://arxiv.org/abs/2509.25370) پیش از هر ادعای «یادگیری از شکست»، تأکید می‌کند که خودِ **failure attribution** باید در سطحِ step دقیق باشد وگرنه درسِ استخراج‌شده نویزی خواهد بود — یعنی محور ۲ (CausalFlow) و محور ۳ (ReasoningBank/MemSkill/MemPro) به‌هم وابسته‌اند: بدون attributionِ دقیق، تبدیلِ شکست به supervision صرفاً نویز را به لایهٔ حافظه منتقل می‌کند.

جمع‌بندی محور ۳: **ledgerِ فعال = ledgerی که خروجی‌اش خوراک آموزش/تکامل است، نه فقط بایگانی — و این فقط وقتی درست کار می‌کند که attribution زیرش دقیق باشد.**

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

اصل حاکم: **رشد باید تابع ارزشِ اطلاعاتی باشد، نه تابعِ زمان.** یک ledgerِ فعالِ سالم، در حالت پایدار **همگرا**