---
type: prompt
status: ready
tags: [doctor, evolution, research, self-improvement, prompts]
created: 2026-07-06
updated: 2026-07-06
related: "[[04 - Architect System/architect/04-Docs/Prompt - دکتر مغز تکاملی (Evolutionary Doctor) 2026-07-05]] · [[04 - Architect System/architect/04-Docs/2026-07-06 0237 DEEP-GAP-ANALYSIS-v2]]"
---

# بسته پرامپت تحقیقاتی — هوشمندسازی دکتر تکاملی

> خواسته آری: «خودِ هوشمندسازی می‌خواهم — وظیفه دکتر تکاملی.» این ۸ پرامپت **کپی-پیست‌آماده** هر کدام روی یک ستون دکتر یا یک تصمیم باز §۹ کار می‌کنند و **دیتای واقعی** برای مغز جمع می‌کنند.
>
> **طرز کار (یاد بگیر):**
> ۱. یک پرامپت را کپی کن، در یک چت تازه Cowork بچسبان.
> ۲. کوورک تحقیق می‌کند + نتیجه را در `07 - Knowledge/_doctor-research/` ذخیره می‌کند (هر پرامپت خودش مسیر و نام فایل را می‌گوید).
> ۳. هر نوت `created_by: agent` + `sources ≥۲` می‌گیرد → دکتر بعداً از همین recall می‌کند.
> ۴. بعد از هر تحقیق، یک خط verdict بده (مفید/نه) → همین verdict غذای ستون ۲ است.
>
> ترتیب پیشنهادی: P1→P2 (پایه ارزیابی) اول، بعد بقیه به هر ترتیب. یکی در روز کافی است — پخش‌شدن بهتر از هجوم.

---

## P1 — تابع برازندگی (تصمیم باز §۹.۲ — مهم‌ترین)

```
تحقیق عمیق کن: چطور سیستم‌های self-improving agent در ۲۰۲۶ «جهش خوب» را از «metric-gaming» تشخیص می‌دهند؟ روی این‌ها تمرکز کن: تابع fitness چندبُعدی، held-out set، reference runner مستقل، evaluator locking، و ترکیب سیگنال عینی (درآمد/سرعت/خطا) با قضاوت انسانی.

منابع اصلی arXiv/paper را مبنا بگیر نه بلاگ. حداقل ۵ منبع. برای هر رویکرد بنویس: چطور کار می‌کند، هزینه/overhead، و آیا روی یک vault مبتنی-markdown با LLM-tasks قابل‌پیاده‌سازی است.

خروجی را به‌صورت یک نوت markdown ذخیره کن در:
"C:\Users\Armin\Desktop\backup\07 - Knowledge\_doctor-research\fitness-function-design.md"
با frontmatter: type: knowledge, status: active, created_by: agent, tags: [doctor, fitness, evolution], و sources: با همه لینک‌ها. آخرش یک بخش «۳ پیشنهاد مشخص برای تابع برازندگی دکتر ما» اضافه کن.
```

## P2 — ارزیاب مستقل / canary (ستون ۲ + DEEP-GAP شکاف ۲/۸)

```
تحقیق کن: معماری «adversarial evaluator» و «canary evaluation» در agentهای خودبهبود ۲۰۲۶ چطور پیاده می‌شود؟ چطور یک generator را از evaluator جدا می‌کنند تا سیستم داور جهش خودش نباشد؟ مکانیزم‌ها: context تازه per-review، system-prompt بدبین، mini-anchor-set از سناریوهای واقعی، معیارهای dimensioned.

مرجع کن به Darwin Gödel Machine (arxiv 2505.22954) و RewardHackingAgents (arxiv 2603.11337). حداقل ۵ منبع. برای هر مکانیزم: overhead، false-positive risk، و نسخه سبک قابل‌اجرا روی لپ‌تاپ.

ذخیره در:
"C:\Users\Armin\Desktop\backup\07 - Knowledge\_doctor-research\canary-adversarial-evaluator.md"
frontmatter مثل بالا، tags: [doctor, evaluator, canary]. آخرش «طرح canary مینیمال برای learning-engine-loop ما: ۳-۵ سناریوی ثابت + معیار pass/fail».
```

## P3 — مرز invariant ↔ mutable (تصمیم باز §۹.۱)

```
تحقیق کن: در سیستم‌های self-modifying (Darwin Gödel Machine، Promptbreeder، AutoML-Zero و مشابه)، چطور «بخش قابل‌جهش» را از «هسته محافظت‌شده» جدا می‌کنند؟ استعاره ژن حفاظت‌شده vs پرتغییر در عمل چطور کد می‌شود؟ مکانیزم‌های enforcement: allowlist، sandbox، سطح‌بندی دسترسی write.

حداقل ۴ منبع. برای هر رویکرد: چطور نقض مرز را می‌گیرند، و چطور مرز را با تجربه گسترش می‌دهند بدون بازکردن هسته.

ذخیره در:
"C:\Users\Armin\Desktop\backup\07 - Knowledge\_doctor-research\invariant-mutable-boundary.md"
tags: [doctor, invariant, mutation-surface]. آخرش «نقشه مرز پیشنهادی برای vault ما: چه چیز هرگز، چه چیز میدان خلاقیت».
```

## P4 — جهش‌نامه فعال (Mutation Ledger → ترمیم، DEEP-GAP شکاف ۴)

```
تحقیق کن: چطور ledger شکست را از یک لاگ منفعل به یک منبع ترمیم فعال تبدیل می‌کنند؟ روی CausalFlow، counterfactual repair، و تبدیل failure-trace به داده supervision تمرکز کن. تفاوت append-only log با یک memory دارای lifecycle (ADD/UPDATE/DELETE/NOOP سبک Mem0).

حداقل ۵ منبع. برای هر رویکرد: چطور از یک شکست، یک اصلاح مینیمال می‌سازند، و چطور جلوی رشد بی‌مرز ledger را می‌گیرند.

ذخیره در:
"C:\Users\Armin\Desktop\backup\07 - Knowledge\_doctor-research\active-mutation-ledger.md"
tags: [doctor, mutation-ledger, memory]. آخرش «طرح FAILURE→REPAIR برای جهش‌نامه دکتر ما».
```

## P5 — ریتم و همگرایی حلقه فکری (تصمیم باز §۹.۵ + ستون ۳)

```
تحقیق کن: agentهای خودمختار ۲۰۲۶ حلقه فکری‌شان را daemon پیوسته می‌سازند یا burst زمان‌بندی‌شده کران‌دار؟ چطور از حلقه فراری (runaway) و از context-rot در حلقه‌های طولانی جلوگیری می‌کنند؟ مکانیزم‌های همگرایی: MAX_ROUNDS، دو دور بهبود زیر آستانه، budget-per-cycle، kill-switch در هر round.

حداقل ۴ منبع. برای هر رویکرد: هزینه، ریسک، و مناسب‌بودن برای اجرای «فقط وقتی اپ باز است» (نه daemon واقعی).

ذخیره در:
"C:\Users\Armin\Desktop\backup\07 - Knowledge\_doctor-research\loop-rhythm-convergence.md"
tags: [doctor, control-loop, cost]. آخرش «ریتم پیشنهادی برای ستون ۳ دکتر ما با توجه به محدودیت اپ-باز».
```

## P6 — حافظه tiered / consolidation (DEEP-GAP شکاف ۱۱/۱۲ + §۶ دکتر)

```
تحقیق کن: بهترین معماری‌های حافظه agent در ۲۰۲۶ چطور working / long-term / core را جدا می‌کنند؟ فاز consolidation شبانه (sleep-cycle)، episodic→semantic distill، و retrieval هیبرید (BM25+vector+rerank با RRF). چطور «امتیاز را decay کن نه داده را».

مرجع کن به Deployment-Time Memorization (arxiv 2606.10062) و paperهای agent-memory ۲۰۲۶. حداقل ۵ منبع. برای هر لایه: چه چیزی نگه می‌دارد، چطور فراموش می‌کند.

ذخیره در:
"C:\Users\Armin\Desktop\backup\07 - Knowledge\_doctor-research\tiered-memory-consolidation.md"
tags: [doctor, memory, consolidation]. آخرش «طرح ارتقای EXPERIENCE-LEDGER + consolidator ما به حافظه دوفازی».
```

## P7 — دفاع تزریق برای حلقه با web_search (ستون ۳ + §۵.۵ دکتر)

```
تحقیق کن: وقتی یک حلقه agentic از web_search محتوای بیرونی می‌بلعد، چطور جلوی prompt-injection غیرمستقیم و memory-poisoning را می‌گیرند؟ مکانیزم‌ها: مرز اعتماد provenance (external = data نه instruction)، sanitize، برچسب <external_data>، و بلوک نامتراکم‌پذیر برای دستورهای حساس.

مرجع کن به paperهای indirect prompt injection و PoisonedRAG ۲۰۲۶. حداقل ۴ منبع. برای هر دفاع: چطور کار می‌کند و نقطه‌ضعفش.

ذخیره در:
"C:\Users\Armin\Desktop\backup\07 - Knowledge\_doctor-research\injection-defense-loop.md"
tags: [doctor, security, injection]. آخرش «قواعد سخت دفاع تزریق برای callهای Fugu دکتر ما».
```

## P8 — بنچمارک شرکت‌های بزرگ (چطور در مقیاس زنده کرده‌اند)

```
تحقیق کن: شرکت‌های بزرگ (Anthropic, OpenAI, Google DeepMind, Sakana AI) سیستم‌های self-improving/agentic خودشان را در production چطور اداره می‌کنند؟ روی این‌ها: eval harness، human-in-the-loop gate، rollback، observability، و مدل حاکمیت. چه چیزی را عمداً خودکار نکرده‌اند و چرا.

حداقل ۶ منبع رسمی/فنی. یک جدول مقایسه «آن‌ها چه می‌کنند vs vault ما چه دارد» بساز.

ذخیره در:
"C:\Users\Armin\Desktop\backup\07 - Knowledge\_doctor-research\industry-benchmark-selfimprove.md"
tags: [doctor, benchmark, industry]. آخرش «۳ چیزی که می‌توانیم از آن‌ها قرض بگیریم بدون شکستن P7 بودجه پیچیدگی».
```

---

## بعد از جمع‌شدن دیتا (وقتی ۴+ نوت آماده شد)

یک چت تازه باز کن و این را بده تا سنتز شود و به تصمیم‌های باز §۹ دکتر وصل شود:

```
همه نوت‌های داخل "C:\Users\Armin\Desktop\backup\07 - Knowledge\_doctor-research\" را بخوان و یک سند سنتز بساز که هر یافته را به یکی از ۷ تصمیم باز §۹ فایل «Prompt - دکتر مغز تکاملی» نگاشت کند و برای هر تصمیم یک پیشنهاد عملی با شاهد بدهد. ذخیره در "00 - Inbox" با نام DOCTOR-SYNTHESIS. verdictهای لازم من را در انتها لیست کن.
```

> نکته: این ۸ پرامپت را می‌شود دستی زد (کنترل کامل، یادگیری بیشتر) یا به‌عنوان تسک زمان‌بندی گذاشت (خودکار، دیتای مداوم). اگر خواستی خودکارشان کنم، بگو — یک تسک هفتگی «doctor-research» می‌سازم که هفته‌ای یکی را می‌زند.
