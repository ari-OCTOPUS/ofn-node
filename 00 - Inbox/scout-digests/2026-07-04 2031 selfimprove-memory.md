---
type: research
status: inbox
project: "[[04 - Architect System/architect/PROJECT]]"
created_by: agent
sources:
  - https://www.alphaxiv.org/abs/2607.01988
  - https://www.alphaxiv.org/abs/2605.20616
  - https://www.alphaxiv.org/abs/2512.23343
  - https://arxiv.org/abs/2304.03442
  - https://arxiv.org/abs/2309.02427
tags: [research, ai]
created: 2026-07-04
updated: 2026-07-04
salience: 0.82
---

# selfimprove-memory — «Slow-Wave Consolidation»: پاسِ آفلاینِ episodic→semantic (استخراجِ schema پیش از evaporation)

> **این یک پیشنهاد است — اجرا نشده. طرحِ یک مکانیزم برای consolidatorِ شبانه است؛ بدونِ verdictِ آری پیاده نشود. propose-only: تنها خروجی، همین draft در `00 - Inbox/scout-digests/` است. هیچ نوتِ canonical (ARCHITECT_CHARTER، PROJECT.md، blueprint، Property Schema) و هیچ پرامپتِ عامل تغییر نمی‌کند.**

## ۱. آیتم انتخابی و چرا مهم است (فعلِ گمشدهٔ حافظه)

لِینِ MEMORY تا امروز **پنج فعل** از چرخهٔ عمرِ حافظه را پوشش داده:

- **deposit** (نوشتنِ دیجست) و **rehydrate** (بازخوانیِ state بعد از کرش) → [[00 - Inbox/scout-digests/2026-07-04 1906 selfimprove|Substrate-Memory]]
- **push-to-kin** (مادر→اسکات، رفعِ cold-start) → [[00 - Inbox/scout-digests/2026-07-04 1826 selfimprove|Kin-Provisioning]]
- **evaporate** (decay هنگام بی‌استفادگی، salienceِ اسکالر) → [[00 - Inbox/scout-digests/2026-07-04 1835 selfimprove|Reinforcement-Weighted Evaporation]]
- **read/parse** (trace read-contract + برچسبِ ماشین‌خوان) → [[00 - Inbox/scout-digests/2026-07-04 1922 selfimprove|Legible Pheromone Map]]

**فعلِ گمشده = `consolidate`**: تبدیلِ سیگنالِ episodicِ تکرارشونده به دانشِ semanticِ ماندگار. این تنها فعلی است که هیچ دیجستی مکانیزمش را نداده.

**چرا بحرانی است — evaporation بدونِ آن lossy است.** قاعدهٔ ۱۸۳۵ می‌گوید salienceِ HIGH (تقویت در ≥K=۳ دیجستِ متمایز) → «پیشنهادِ promote به Knowledge». ولی این فقط **trigger** را تعریف می‌کند، نه **transform** را. بینِ «۳ دیجست الگوی X را تقویت کردند» و «یک نوتِ Knowledgeِ ماندگار وجود دارد» چه اتفاقی می‌افتد؟ تعریف‌نشده. نتیجهٔ امروز: یا دیجست‌ها انباشته می‌شوند (noise)، یا با age-out محو می‌شوند و **الگویِ آموخته‌شده از دست می‌رود**. consolidation همان گامِ **extract-before-forget** است که evaporation را امن می‌کند.

**de-riskِ چندگانه:** ۱۸۳۵ (evaporationِ غیر-lossy)، ۱۸۲۶ (نوتِ consolidate‌شده دقیقاً همان spore-packetِ پرارزشی است که مادر push می‌کند)، ۱۹۲۲ (از trace-index و `epistemic_status` استفاده می‌کند)، Adversarial v3 §۵ (تقویتِ oracle-gated)، §۶ (مکانیزه‌کردنِ لایهٔ long-termِ CoALA)، و [[05 - Agents/Mycelium Scout|Mycelium Scout]] §۴ (قاعدهٔ «۳+ دیجست → Knowledge» یک transformِ واقعی می‌گیرد).

## ۲. یافته‌ها و prior-art

**لنگرِ زیستی — sleep-dependent systems consolidation.** در خوابِ موج-آهسته (SWS)، ripplesِ هیپوکامپ ردهای episodic را **replay** می‌کنند؛ نئوکورتکس **schema/gist** را استخراج می‌کند؛ و آنگاه ردِ اختصاصیِ episodic می‌تواند decay کند. دو خاصیتِ قابل‌کپی: (الف) consolidation **آفلاین و batched** است (در «خواب»، نه وسطِ task) — منطبق بر consolidatorِ شبانهٔ ما؛ (ب) ترتیبِ **extract-then-decay** — gist پیش از محوِ رد بیرون کشیده می‌شود. آنالوگِ مادر-درخت: تجربهٔ فشرده‌به‌schemaِ چنددهه‌ایِ hub = حافظهٔ semantic که از صدها فصلِ episodic ساخته شده، و دقیقاً همان چیزی است که به kin route می‌شود (۱۸۲۶). ([AI Meets Brain: Memory Systems from Cognitive Neuroscience to Autonomous Agents](https://www.alphaxiv.org/abs/2512.23343))

**Prior-artِ AI:**
- **Generative Agents «reflection»:** به‌صورت دوره‌ای observationهای episodic را به insightهای سطح‌بالا (semantic) سنتز می‌کند؛ سه‌لایه: observation → reflection → retrieval. الگوی بنیادی. ([arXiv:2304.03442](https://arxiv.org/abs/2304.03442))
- **Mem0 / Memory-R1 / Mem-α:** چرخهٔ صریحِ extract → consolidate → forget؛ consolidation معمولاً هر N episode (۵۰–۲۰۰)، با **background daemon** ترجیح‌داده‌شده بر on-request (اجتناب از latency-spike). عددِ صنعتیِ هشدار: **summarizationِ ساده ~۲۰٪ از factهای encode‌شده را می‌بازد**.
- **Auto-Dreamer (۲۰۲۶-۰۵): «offline memory consolidation for language agents»** — عملاً همان آنالوگِ خواب/رؤیا — تجربهٔ انباشته را به دانشِ قابل‌استفادهٔ مجدد تبدیل می‌کند. ([alphaXiv:2605.20616](https://www.alphaxiv.org/abs/2605.20616))
- **Episodic-to-Semantic Consolidation Without Identity Drift (۲۰۲۶-۰۷-۰۲، ۲ روز پیش):** خطرِ اصلی را برجسته می‌کند — consolidation به‌طورِ متعارف یک عملِ **agent-changing** است؛ consolidationِ ساده هویت/رفتارِ عامل را drift می‌دهد. لنگرِ adversarialِ من. ([alphaXiv:2607.01988](https://www.alphaxiv.org/abs/2607.01988))
- **CoALA:** لایه‌های working/episodic/semantic/procedural را نام می‌برد ولی transformِ episodic→semantic را **مکانیزه نمی‌کند** — این پیشنهاد همان شکاف را پر می‌کند. ([arXiv:2309.02427](https://arxiv.org/abs/2309.02427))

## ۳. پیشنهاد — «Slow-Wave Consolidation» (proposal — needs Ari's verdict)

یک transformِ **شبانه و آفلاین** که consolidatorِ موجود اجرا می‌کند و **بینِ** salience-scoring (۱۸۳۵) و evaporation می‌نشیند. شش قاعده:

1. **Trigger (از salienceِ ۱۸۳۵ استفاده کن، سیگنالِ نو اختراع نکن):** یک خوشه وقتی consolidate می‌شود که **≥K=۳ دیجستِ متمایز** به‌طورِ مستقل همان الگویِ `covers`/tag را تقویت کرده باشند (salience HIGH). نوشتنِ episodicِ سریع، consolidationِ semanticِ کند و batched — همان عدم‌تقارنِ زیستی.
2. **Transform = schema extraction، نه summarization.** **invariantِ مشترکِ خوشه** را استخراج کن (آنچه تکرار می‌شود)، نه خلاصهٔ هر دیجست. خروجی: **یک** نوتِ semanticِ candidate.
3. **Pointerِ lossless برای provenance (پاسخ به ~۲۰٪ fact-loss).** نوتِ semantic یک gistِ lossy است ولی **backlinkِ wikilinkِ verbatim** به هر دیجستِ منبع دارد. زیست‌شناسی: نئوکورتکس schema را نگه می‌دارد، هیپوکامپ ردِ خام را تا لحظهٔ consolidation حفظ می‌کند — backlink همان ردِ ایمنی است. هیچ‌چیز واقعاً حذف نمی‌شود؛ منبعِ episodic **archive** می‌شود نه shred.
4. **تناقض surface می‌شود، نه smooth.** اگر دیجست‌های خوشه اختلاف داشتند (مثلاً دو run قاعدهٔ decayِ متضاد پیشنهاد دهند)، **میانگین نگیر** → `epistemic_status: contested` با هر دو backlink (منطبق بر برچسبِ ۱۹۲۲ + الگویِ ۵ synthesis: verified≠speculative). schema extraction که episodeهای متناقض را نادیده بگیرد = confabulation/false-memory.
5. **تقویت را oracle-gate کن (importِ §۵ ضد-echo).** یک الگو را فقط با **سیگنالِ عینیِ تکرار** تقویت کن — **K≥۳ deposit مستقل خودش oracle است** — هرگز چون مدل «حس می‌کند» یافته‌ای مهم است. این دقیقاً درسِ Reflexionِ §۵ (تزریق فقط با سیگنالِ عینیِ شکست/موفقیت) است که به لایهٔ consolidation منتقل می‌شود.
6. **جفت‌شدنِ safe-evaporation (de-riskِ ۱۸۳۵).** یک دیجستِ episodic فقط وقتی evaporate/archive می‌شود که **یا** (الف) محتوایِ salientش در یک candidateِ semantic consolidate شده باشد (extract-before-forget)، **یا** (ب) هرگز از آستانهٔ salience رد نشده باشد (واقعاً کم‌ارزش). شکافِ evaporationِ lossy بسته می‌شود.

خروجی به‌صورتِ **candidate** در Inbox / نوتِ Knowledge-candidate می‌نشیند — propose-only، gated توسطِ آری. هرگز نوتِ canonicalِ هویت را بازنویسی نمی‌کند → این پاسخِ سطح-مکانیزم به failure-modeِ identity-drift است ([2607.01988](https://www.alphaxiv.org/abs/2607.01988)) و همین حالا هم توسطِ Security Gate اجباری است.

**گام ۰ (فقط قاعده، در scopeِ نوشتنِ scout-digests/synthesis — نه پشتِ گیتِ canonical):** افزودنِ یک بخشِ «Consolidation candidates» به خروجیِ consolidator که خوشه‌های K≥۳ را با gistِ استخراج‌شده + backlinkها + `epistemic_status` فهرست کند. ارتقا به `07 - Knowledge` همچنان verdictِ آری می‌خواهد.

## ۴. ریسک‌ها و trade-offها

- **Identity drift ([2607.01988]):** consolidation می‌تواند رفتار/هویتِ عامل را عوض کند. مهار: propose-only + هرگز بازنویسیِ نوتِ canonical؛ خروجی فقط candidate.
- **Lossy gist (~۲۰٪ fact-loss صنعتی):** مهار با backlinkِ verbatim — extract-before-forget، **archive نه delete**.
- **Confabulation از smoothingِ تناقض:** مهار با `epistemic_status: contested`، نه میانگین‌گیری.
- **Echo / تقویتِ یک خطای اولیه (درسِ oracleِ §۵):** مهار با گیتِ K≥۳ depositِ مستقل؛ سیگنالِ عینی نه «حسِ مدل».
- **Over-consolidation (schemaِ زودرس):** K و آستانهٔ salience محافظه‌کار بمانند؛ خوشهٔ ۲تایی consolidate نشود.
- **هزینه:** یک passِ LLM شبانه فقط روی خوشه‌های HIGH — batched/offline، پس بدونِ latency-spike؛ هم‌راستا با «background daemon»ِ صنعت.

## ۵. لینک‌های مایکورایزال
- [[00 - Inbox/scout-digests/2026-07-04 1835 selfimprove|Reinforcement-Weighted Evaporation]] — این پاس دقیقاً بالادستِ evaporation می‌نشیند و آن را non-lossy می‌کند (extract-before-forget).
- [[05 - Agents/Mycelium Scout]] §۴ («۳+ دیجست → Knowledge») — این پیشنهاد به آن قاعده یک **transformِ واقعی** می‌دهد، نه فقط شمارشِ دستی.
