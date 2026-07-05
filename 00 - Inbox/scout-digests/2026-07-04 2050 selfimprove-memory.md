---
type: research
status: inbox
project: "[[04 - Architect System/architect/PROJECT]]"
created_by: agent
sources:
  - https://en.wikipedia.org/wiki/Testing_effect
  - https://en.wikipedia.org/wiki/Retrieval-induced_forgetting
  - https://pubmed.ncbi.nlm.nih.gov/11082860/
  - https://www.nature.com/articles/s41598-018-37089-2
  - https://arxiv.org/abs/2304.03442
  - https://www.alphaxiv.org/abs/2601.18642
  - https://www.alphaxiv.org/abs/2605.21768
  - https://www.alphaxiv.org/abs/2602.02007
tags: [research, ai]
created: 2026-07-04
updated: 2026-07-04
salience: 0.84
---

# selfimprove-memory — «Retrieval-Gated Reinforcement»: فعلِ گمشدهٔ `retrieve` — بازیابی به‌مثابهٔ رویدادِ نوشتن (reconsolidation) که سیگنالِ تقویتِ گمشدهٔ ۱۸۳۵ را تأمین می‌کند

> **این یک پیشنهاد است — اجرا نشده. propose-only: تنها خروجی، همین draft در `00 - Inbox/scout-digests/` است. هیچ نوتِ canonical (ARCHITECT_CHARTER، PROJECT.md، blueprint، Property Schema، _PROJECT_INSTRUCTIONS) و هیچ پرامپتِ عاملی تغییر نمی‌کند. ارتقای هر نوت به Knowledge یا تغییرِ قاعدهٔ evaporation، verdictِ آری می‌خواهد.**

## ۱. آیتم انتخابی و چرا مهم است (فعلِ گمشدهٔ حافظه = `retrieve`)

لِینِ MEMORY تا این لحظه **شش فعل** از چرخهٔ عمرِ حافظه را مکانیزه کرده — اما همه در سمتِ **write / maintain / push** اند:

- **deposit + rehydrate** (نوشتن و بازخوانیِ state پس از کرش) → [[00 - Inbox/scout-digests/2026-07-04 1906 selfimprove|Substrate-Memory / R-13]]
- **push-to-kin** (مادر→اسکات، رفعِ cold-start) → [[00 - Inbox/scout-digests/2026-07-04 1826 selfimprove|Kin-Provisioning]]
- **evaporate** (decay هنگام بی‌استفادگی) → [[00 - Inbox/scout-digests/2026-07-04 1835 selfimprove|Reinforcement-Weighted Evaporation]]
- **read/parse** (Trace Read-Contract) → [[00 - Inbox/scout-digests/2026-07-04 1922 selfimprove|Legible Pheromone Map]]
- **consolidate** (episodic→semantic، آفلاین) → [[00 - Inbox/scout-digests/2026-07-04 2031 selfimprove-memory|Slow-Wave Consolidation]]

**فعلِ گمشده = `retrieve` (سمتِ pull)**: هیچ دیجستی تعریف نکرده که یک عامل، *وسطِ یک task*، چطور اسلایسِ درستِ حافظه را از سابسترِیت **بیرون می‌کشد**. حافظه‌ای که در لحظهٔ تصمیم بازیابی نشود، بی‌فایده است — کلِ چرخه تاکنون write-only بوده.

**چرا بحرانی است — دو حلقهٔ نیمه‌کاره را می‌بندد.**

۱) **قاعدهٔ ۱۸۳۵ یک ورودیِ گمشده دارد.** ۱۸۳۵ می‌گوید salience با «re-depositِ ≥K دیجستِ متمایز» تقویت می‌شود. اما این تنها سیگنالِ تقویت است و **کُند** است (به نوشتنِ تازه نیاز دارد). یک نوت می‌تواند مدام **استفاده/بازیابی** شود ولی هرگز re-deposit نشود — و طبق ۱۸۳۵ اشتباهاً evaporate می‌شود. سیگنالِ تقویتِ گمشده دقیقاً **retrieval** است.

۲) **نیمهٔ گمشدهٔ stigmergy.** دیجستِ mycelium (§Finding 5) گفت مورچه‌ها ردِ **استفاده‌شده** را تقویت می‌کنند و ردِ بی‌استفاده evaporate می‌شود. ۱۸۳۵ فقط نیمهٔ **evaporate-on-disuse** را ساخت؛ نیمهٔ **reinforce-on-traversal** ساخته نشد. هر بار که consolidator یک نوت را واقعاً *می‌پیماید/استناد می‌کند*، باید فرمونِ آن پررنگ‌تر شود. retrieval همان رویدادِ پیمایش است.

**de-riskِ چندگانه (پنج خواهر):** ۱۸۳۵ (ورودیِ تقویتِ سریع)، ۲۰۳۱ (نوتِ semantic بدونِ مسیرِ بازیابی write-only است؛ و شمارشِ retrieval یک اوراکلِ دومِ consolidation است)، ۱۸۲۶ (به push، فعلِ pull را می‌افزاید — اسکاتِ کم‌کانتکست می‌تواند *بپرسد*، نه فقط منتظرِ تغذیه بماند)، ۱۹۲۲ (این «یافتنِ ردِ درست» است، پیش از «خواندنِ رد»)، ۱۹۰۶ (retrieval = rehydrateِ ریزدانه و cue-triggered).

## ۲. یافته‌ها و prior-art

**لنگرِ زیستی — بازیابی یک عملِ نوشتن است، نه خواندن.**

- **Testing effect / retrieval practice.** خودِ عملِ بازیابی، اتصالاتِ نگه‌دارندهٔ حافظه را **تقویت** می‌کند — قوی‌تر از مطالعهٔ مجدد (Roediger & Karpicke 2006؛ >۱۰۰ سال شواهد). یعنی «استفاده» = تقویت. ([Testing effect — Wikipedia](https://en.wikipedia.org/wiki/Testing_effect))
- **Retrieval-Induced Forgetting (RIF) — تقویتِ گزینشی + سرکوبِ رقبا.** بازیابیِ یک آیتم نه‌تنها آن را تقویت می‌کند (Rp+ ≈ **۸۱٪**)، بلکه **رقبای هم‌نشانه** (آیتم‌های مرتبط که همان cue را share می‌کنند ولی بازیابی نشدند) را **سرکوب** می‌کند (Rp- ≈ **۵۵٪**) نسبت به خنثی (NRp ≈ **۶۸٪**) — اثرِ ~۱۳٪. و این سرکوب یک **مکانیزمِ مهارِ recall-specific** است، نه صرفاً رقابتِ ناشی از تقویت (Anderson, Bjork & Bjork 1994؛ اثباتِ recall-specific: [PubMed 11082860](https://pubmed.ncbi.nlm.nih.gov/11082860/) · جدولِ ۸۱/۶۸/۵۵: [RIF — Wikipedia](https://en.wikipedia.org/wiki/Retrieval-induced_forgetting)). → این دقیقاً یک سیگنالِ **decayِ گزینشیِ اصولی** است: بازیابیِ برندهٔ یک خوشه باید بازنده‌های هم‌cue را کم‌وزن کند.
- **Reconsolidation — پنجرهٔ labile.** حافظهٔ بازفعال‌شده وارد دورهٔ **ناپایداری (labilization)** و سپس بازتثبیت می‌شود؛ بسته به reactivation می‌تواند **تقویت، تضعیف یا به‌روزرسانی** شود. مهم: تنها **reminderِ ناقص/incongruent** (یک «prediction error») labilization را trigger می‌کند. یعنی بازیابی = فرصتی برای *نوشتنِ دوباره* — اما فقط وقتی تناقض هست. ([Nature Sci Rep 2019](https://www.nature.com/articles/s41598-018-37089-2))
- **لنگرِ مادر-درخت/ممریستور:** rehydrationِ شبکهٔ قارچی با **ولتاژِ درست (cue)** بازفعال می‌شود؛ نهالِ در تنش با **سیگنالِ درماندگی (cue)** کربن را از مادر *pull* می‌کند. هر دو = cue→بازفعال‌سازی، یعنی همان retrieval.

**Prior-artِ AI (تازه، ۲۰۲۶):**
- **Generative Agents — تابعِ بازیابیِ کانونی:** score = ترکیبِ نرمال‌شدهٔ **recency (decay) + importance + relevance (شباهت)**. الگویِ مرجعِ ranking. ([arXiv:2304.03442](https://arxiv.org/abs/2304.03442))
- **FadeMem (۲۰۲۶-۰۱): فراموشیِ زیست‌الهام برای حافظهٔ عامل** — دقیقاً هم‌خانواده؛ فراموشیِ گزینشی به‌جای catastrophic-forgetting یا انباشتِ بی‌پایان. ([alphaXiv:2601.18642](https://www.alphaxiv.org/abs/2601.18642))
- **Memory-R2 (۲۰۲۶-۰۵): Fair Credit Assignment** — کدام حافظه سزاوارِ اعتبار/تقویت است؟ همان مسئلهٔ «reinforce به کدام رد». ([alphaXiv:2605.21768](https://www.alphaxiv.org/abs/2605.21768))
- **Beyond RAG for Agent Memory (۲۰۲۶-۰۲):** RAGِ خام برای حافظهٔ عامل بد است — حافظهٔ عامل یک استریمِ **کراندار و منسجم** است، نه کورپوسِ بزرگِ ناهمگون؛ retrieval باید decouple+aggregate کند. → هشدار: روی scout-digests سراغِ vector-RAGِ ساده نرو. ([alphaXiv:2602.02007](https://www.alphaxiv.org/abs/2602.02007))

## ۳. پیشنهاد — «Retrieval-Gated Reinforcement» (proposal — needs Ari's verdict)

تعریفِ فعلِ `retrieve` به‌گونه‌ای که **رویدادِ بازیابی، خودش رویدادِ نوشتنِ سبک** باشد و ورودیِ گمشدهٔ ۱۸۳۵ را تأمین کند. شش قاعده:

1. **عملِ pull (cue→ranked recall).** وقتی عامل کانتکست می‌خواهد، یک **cue** صادر می‌کند (tagها + covers + کلیدواژهٔ task). candidateها با اسکورِ سبکِ Generative-Agents رتبه می‌گیرند: `score = w_r·relevance(cue∩covers/tags) + w_s·salience(۱۸۳۵) + w_t·recency`. خروجی = top-K **رفرنسِ سبک (wikilink)**، نه محتوایِ inline (رعایتِ درسِ reference-first و context-rotِ ۱۸۲۶). این یک **توسعهٔ read-contract** است، نه تغییرِ canonical.

2. **بازیابی = نوشتن (reconsolidation): پالسِ تقویت به salienceِ ۱۸۳۵.** با هر بازیابیِ *استفاده‌شده*، یک پالسِ تقویتِ کوچک به salience تزریق شود. → این همان ورودیِ گمشدهٔ قاعدهٔ decay است و نیمهٔ **reinforce-on-traversal**ِ stigmergy را کامل می‌کند.

3. **گیتِ عینیِ ضدِ echo (importِ درسِ اوراکلِ §۵ / ۲۰۳۱).** «استفاده» را **تنگ** تعریف کن: نوت فقط وقتی تقویت می‌شود که در یک depositِ پایین‌دستی واقعاً **استناد/لینک** شده باشد — نه صرفاً چون ranker آن را برگرداند، و هرگز چون «مدل حس کرد مرتبط است». سیگنالِ عینیِ استناد = اوراکل.

4. **RIF — decayِ گزینشی و cue-scoped.** وقتی برندهٔ یک خوشهٔ هم‌cue بازیابی-و-استفاده شد، **رقبای هم‌cueِ بازیابی‌نشده** (همان tag/covers، بدونِ استناد) یک nudgeِ decayِ کوچک می‌گیرند (آنالوگِ مهارِ RIF: Rp- < NRp). نقشهٔ فرمون خودتیزشونده می‌شود. **گاردِ pattern-separation:** فقط رقبای بالای یک آستانهٔ شباهت، با decrementِ **کراندار + کف (floor)**، تا نوتِ متمایزی که صرفاً tag را share می‌کند سرکوب نشود.

5. **پنجرهٔ reconsolidation = لحظهٔ امنِ به‌روزرسانی.** چون بازیابی حافظه را labile می‌کند، همان لحظه consolidator می‌تواند یک **candidateِ به‌روزرسانی** پیشنهاد دهد — اما فقط با **prediction-error gate**: تنها وقتی محتوایِ بازیابی‌شده با کانتکستِ فعلی **تناقض/ناسازگاری** دارد (reminderِ ناقص). خروجی همچنان candidate است، هرگز auto-rewrite (مهارِ identity-drift از ۲۰۳۱ / [2607.01988]).

6. **retrieval-count = اوراکلِ دومِ consolidation (de-riskِ ۲۰۳۱).** یک دیجستِ خام که با **≥K cueِ متمایز** بازیابی-و-استفاده شده، candidateِ promote است — مکملِ قاعدهٔ «≥K depositِ متمایز»ِ ۲۰۳۱. دو اوراکلِ مستقل (deposit-frequency و retrieval-frequency) → سیگنالِ قوی‌تر، promoteِ کاذبِ کمتر.

**گام ۰ (فقط مشاهده، در scopeِ نگه‌داریِ scout-digests — نه پشتِ گیتِ canonical):** consolidator برای هر دیجست یک `retrieval_used_count` و `last_used` را در یک بخشِ «Retrieval ledger» لاگ کند. صرفاً داده‌جمع‌کردن، بدونِ تغییرِ رفتار — تا بعداً w_r/w_s/w_t و K روی دادهٔ واقعی کالیبره شوند، نه با حدس. **measurement before mechanism.**

## ۴. ریسک‌ها و trade-offها

- **Echo / خود-تقویتِ runaway** (نوت تقویت می‌شود → بالاتر رتبه می‌گیرد → باز بازیابی می‌شود): مهار با گیتِ عینیِ «استناد‌شده» (قاعدهٔ ۳) + تقویتِ **اشباع‌شونده/لگاریتمی** + خودِ RIF (قاعدهٔ ۴) به‌عنوان نرمالایزر (winner-take-most ولی کراندار).
- **Over-suppressionِ RIF** (سرکوبِ نوتِ متمایزِ هم‌tag): مهار با cue-scoping + آستانهٔ شباهت + کفِ decrement + propose-only (آری خطا را می‌گیرد).
- **Popularity bias / rich-get-richer** (نوتِ پرتکرار غالب، نوتِ نادرِ حیاتی گرسنه): مهار با بونوسِ recency/novelty + کفِ salience؛ اسکورِ retrieval هرگز به‌تنهایی eviction را تعیین نکند.
- **Identity drift از به‌روزرسانیِ reconsolidation** (درسِ [2607.01988]): update فقط candidate، prediction-error-gated، هرگز auto-apply.
- **RAGِ خام نامناسب است** ([2602.02007]): سابسترِیتِ ما استریمِ کراندار است؛ retrieval روی tag/covers/wikilinkِ موجود، نه embeddingِ کورِ کل vault.
- **هزینه:** پالسِ تقویت یک نوشتنِ **اسکالر** است (ارزان، بدونِ LLM)؛ تنها candidateِ به‌روزرسانی یک passِ LLMِ batched — آن هم فقط روی تناقض‌ها.

## ۵. لینک‌های مایکورایزال
- [[00 - Inbox/scout-digests/2026-07-04 1835 selfimprove|Reinforcement-Weighted Evaporation]] — این پیشنهاد **ورودیِ تقویتِ گمشدهٔ** قاعدهٔ decayِ آن را تأمین می‌کند؛ با هم حلقهٔ stigmergy را کامل می‌کنند (reinforce-on-use + evaporate-on-disuse).
- [[00 - Inbox/scout-digests/2026-07-04 2031 selfimprove-memory|Slow-Wave Consolidation]] — retrieval-count یک اوراکلِ دومِ consolidation است و پنجرهٔ reconsolidation لحظهٔ امنِ update را می‌دهد.
