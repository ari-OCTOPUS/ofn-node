---
type: research
status: inbox
project: "[[04 - Architect System/architect/PROJECT]]"
created_by: agent
sources:
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC2785478/
  - https://pubmed.ncbi.nlm.nih.gov/28871661/
  - https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3805967/
  - https://www.aiqnahub.com/agentic-workflow-loop-forever/
  - https://datricon.com/blog/security-theater-the-illusion-of-safety-in-a-world-of-checkboxes
  - http://panarchy.org/ashby/variety.1956.html
tags: [research, ai]
created: 2026-07-05
updated: 2026-07-05
salience: 0.8
---

# selfimprove-safety — «AIRE Self-Test» (خودآزمونِ نگاتیو-سلکشن): هر کنترلِ ایمنیِ *اعلام‌شده* باید یک آزمونِ «اثباتِ شلیک» داشته باشد وگرنه inert است — پاسخِ طراحی به R-04 (کنترل‌های false-assurance)، با تمرکز بر بندِ `MAX_STEPS`ِ اجرانشده

> لِینِ SAFETY. **PROPOSE-ONLY** — این یک design sketch است، اعمال نشده؛ `_code`/`orchestrator.py`/`agents.py`/`config.py`/README/constitution لمس نشد. سطح: audit/trust surface؛ فازِ enforcement kernel-adjacent → **HUMAN-APPROVAL-REQUIRED**. verdict نهایی با آری.

**dedup (rotation):** grep روی همهٔ `*selfimprove*` digestها برای `AIRE / thymic / negative-selection / central-tolerance / APECED / inert-control / declared-vs-enforced / security-theater` → **NONE** (لنگرِ AIRE کاملاً آزاد). دو digestِ حاویِ «runaway/step-limit» ([[00 - Inbox/scout-digests/2026-07-05 1219 selfimprove|1219 Decay-Reinforcement]] و [[00 - Inbox/scout-digests/2026-07-04 2050 selfimprove-memory|2050 Retrieval-Gated]]) هر دو دربارهٔ runaway-ِ **حافظه/فرمون** (hoard/echo) هستند، نه کنترلِ **MAX_STEPS**ِ ارکستریتور. آیتمِ من genuinely نو است.
- پوششِ خانوادهٔ SAFETY تا کنون: R-01 ([[00 - Inbox/scout-digests/2026-07-04 2054 selfimprove-safety|Anoikis 2054]])، R-02 ([[00 - Inbox/scout-digests/2026-07-04 2023 selfimprove-safety|Costimulation 2023]])، R-05 (تاشده در Anoikis)، R-06+R-07 ([[00 - Inbox/scout-digests/2026-07-04 2041 selfimprove-safety|Germline 2041]])، R-08 (1655)، R-09 ([[00 - Inbox/scout-digests/2026-07-04 1911 selfimprove|Apoptosis 1911]])، §4 kappa ([[00 - Inbox/scout-digests/2026-07-04 1744 selfimprove|Quorum 1744]])، GAP 8 ([[00 - Inbox/scout-digests/2026-07-04 2008 selfimprove|Calibrated 2008]]).
- **R-03** (پنلِ داور) در لِینِ general توسط [[00 - Inbox/scout-digests/2026-07-04 2128 selfimprove|Vestigial Costly Signal 2128]] پوشش داده شد (تصمیم: prune). **R-04** (کنترل‌های false-assurance) تنها آیتمِ نام‌بردهٔ خانوادهٔ SAFETY است که هرگز به‌عنوان یک آیتمِ **طراحی‌شده** نوشته نشده — فقط حاشیه‌ای ارجاع شد. → انتخابِ غیرِ-forced.

---

## ۱) آیتم و چرا مهم است

**آیتم: R-04 — «کنترل‌های false-assurance را حذف کن یا واقعاً پیاده‌شان کن».** سه یافتهٔ audit:
- **P4-03 `MAX_STEPS`** — یک ثابتِ config + ادعای README، ولی **هیچ step-counterِ اجرایی‌ای در `Orchestrator.run` آن را چک/halt نمی‌کند** (`config.py:27`, `src/orchestrator.py:81-137`). یعنی هیچ سقفِ اجرا-شده‌ای روی رانِ runaway نیست.
- **P2-05 `external_write`** — در `HITL_REQUIRED_FOR` هست، ولی **هیچ actuationِ واقعیِ `external_write`** که از گیتِ HITL + `gate.act`ِ IGK عبور کند وجود ندارد (`config.py:40`). گیتی که درِ ناموجود را نگهبانی می‌کند.
- **P4-04 `Supervisor.review`** — یک deciderِ **مرده**: agentِ Supervisor ساخته می‌شود ولی `review` هرگز مشورت نمی‌شود (`src/agents.py:72-86`, `src/orchestrator.py:68`).

**چرا این keystone است — و چرا از R-03/2128 متمایز.** [[00 - Inbox/scout-digests/2026-07-04 2128 selfimprove|2128]] یک قاعدهٔ خوب داد («هیچ فراخوانِ هزینه‌دار نباید خروجی‌اش را دور بریزد») ولی این قاعده فقط سیگنال‌های **هزینه‌دارِ دورریخته** را می‌گیرد. `MAX_STEPS` اصلاً **هیچ فراخوانی نمی‌زند** — یک *چکِ نانوشته* است؛ CI-testِ 2128 هرگز آن را flag نمی‌کند. `external_write` یک *اکشنِ ناموجود* است؛ `Supervisor` یک *deciderِ صداشده‌نشده*. این‌ها کلاسِ **کنترلِ اعلام‌شده-ولی-تمرین‌نشده** هستند، نه کلاسِ خروجیِ دورریخته. جوهرِ مشترکِ ایمنی: **واگراییِ envelopeِ اعلام‌شده از envelopeِ اجرا-شده** — سطحِ ایمنی‌ای که سیستم (در config/README/HITL_REQUIRED_FOR) *ادعا* می‌کند بزرگ‌تر از سطحی است که واقعاً *شلیک* می‌کند.

از میانِ سه بند، **`MAX_STEPS` بحرانی‌ترین است**: نبودِ سقفِ اجرا-شده یعنی رانِ runaway/حلقه‌ای هیچ مرزی ندارد — و *همهٔ* گیت‌های دیگر (Quorum, Costimulation, Anoikis, Apoptosis) به‌طورِ نانوشته فرض می‌کنند که ران **کران‌دار** است. این آیتم آن فرضِ نانوشته را اجرایی می‌کند.

**بُعدِ متا (چرا این حلقهٔ self-improvement را de-risk می‌کند):** یک حلقهٔ خودبهبودده (من + لِین‌های خواهر) که با نرخِ ~۲۰ digest/روز **گیت‌های ایمنیِ جدید پیشنهاد می‌دهد**، ساختاراً مستعدِ انباشتِ کنترل‌های *اعلام‌شده* سریع‌تر از کنترل‌های *enforced+tested* است — یعنی تولیدِ **security-theater در مقیاس**. قاعدهٔ این digest دقیقاً پادزهرِ آن است و یک انضباط روی خودِ همین loop می‌گذارد.

## ۲) یافته‌ها / prior-art

**الگوی زیستی — نگاتیو-سلکشنِ تیموسی و «بیانِ بی‌بندوبارِ ژن» با هدایتِ AIRE:**
- تیموس تحمّلِ خودی را **فرض نمی‌کند — آن را می‌آزماید**. سلول‌های اپیتلیالِ مدولاریِ تیموس (mTEC) هزاران آنتی‌ژنِ بافتیِ محیطی (PTA) را که «هیچ کاری با بیانشان ندارند» به‌طورِ ectopic بیان می‌کنند (**promiscuous gene expression**، با تنظیمِ فاکتورِ رونویسیِ AIRE) — **فقط برای اینکه** تیموسیت‌های خام در برابرِ آن self-antigenها *آزموده* شوند و کلونِ high-affinity حذف شود (**negative selection**). یعنی خودِ ارگانیسم **شرطِ آزمون را عامدانه می‌سازد** و آزمون را روی هر کلون *اجرا* می‌کند. ([Transcriptional regulation by AIRE — central tolerance, PMC2785478](https://pmc.ncbi.nlm.nih.gov/articles/PMC2785478/)؛ [Update on Aire and thymic negative selection, Passos 2018](https://pubmed.ncbi.nlm.nih.gov/28871661/))
- **شکستِ آزمون = بیماری (APECED):** جهشِ AIRE یعنی تحمّل به بافت‌های خاصی *اعلام* شده (ماشینِ تیموس هست، selection برای اکثرِ آنتی‌ژن‌ها کار می‌کند) ولی در برابرِ آنتی‌ژن‌های وابسته-به-AIRE **هرگز تمرین نمی‌شود** → کلونِ خودواکنش‌گر **فرار می‌کند** → autoimmunityِ چنداندامی. ([APECED, PMC3805967](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3805967/))

> **بازقاب‌گیریِ کلیدی — باگِ R-04 دقیقاً APECED است.** کنترلِ اعلام‌شده-ولی-تمرین‌نشده (`MAX_STEPS`ِ چک‌نشده، گیتِ `external_write`ِ بی‌اکشن، `Supervisor`ِ صداشده‌نشده) = **آنتی‌ژنی که در تیموس هرگز presented نمی‌شود**؛ رانِ runaway/اکشنِ ممنوعی که باید می‌گرفت = **کلونِ خودواکنش‌گرِ فراری**. درمان از خودِ زیست‌شناسی می‌آید: مثلِ AIRE، **شرطِ چالش را بساز و آزمون را اجرا کن** — برای هر کنترل یک تستِ negative-selection که *اثبات کند شلیک می‌کند*.

**prior-art امنیتی / AI:**
- **runaway agent یک هزینهٔ واقعیِ ۲۰۲۶ است:** یک ران بدونِ شرطِ خروجِ معتبر می‌تواند بی‌نهایت تکرار کند؛ یک موردِ مستند **۱۲٬۰۰۰ دلار** در یک نشستِ runaway پیش از کشف سوزاند. سه مکانیزمِ خروجِ اجباری لازم است: **سقفِ سختِ iteration**، detectorِ تکرارِ tool-call، و چکِ اتمامِ domain-aware — و نکتهٔ کلیدی: «**خودِ LLM نمی‌تواند به‌اعتماد تصمیم بگیرد کِی تمام است؛ گاردریلِ deterministicِ اجرا-شده در کد لازم است**». این دقیقاً توجیهِ enforceِ `MAX_STEPS` است، نه صرفاً declare کردنش. ([Agentic Workflow Loop Forever — aiqnahub 2026](https://www.aiqnahub.com/agentic-workflow-loop-forever/))
- **Security Theater / false assurance:** «پیاده‌سازیِ تدابیرِ امنیتی که حسِ کاذبِ ایمنی می‌سازند بدونِ محافظتِ واقعی»؛ نمونه‌ها: «سیاستِ رمزِ عبورِ enforced-نشده، checkbox compliance». مهم‌ترین نکته برای ما: false-assurance **بدتر از نبودِ کنترل است**، چون «فوریتِ پیاده‌سازیِ تدابیرِ مؤثرتر را کم می‌کند» — یک بمبِ ساعتی. ([Security Theater — Datricon](https://datricon.com/blog/security-theater-the-illusion-of-safety-in-a-world-of-checkboxes))
- **through-line به requisite variety (Ashby):** false-assurance یعنی سطحِ کنترلِ *اعلام‌شده* واریتهٔ تنظیمی‌ای را ادعا می‌کند که سطحِ *اجرا-شده* ندارد → **واریتهٔ ادعایی > واریتهٔ مؤثر** → تنظیم‌گر دقیقاً نسبت به همان اختلالی که تبلیغ می‌کند مدیریتش می‌کند، کور است. این آیتم را به [[00 - Inbox/scout-digests/2026-07-04 1850 selfimprove|Requisite-Variety Gate 1850]] وصل می‌کند بدونِ تکرارِ آن (1850 = واریتهٔ *ترکیبِ ناوگان*؛ این = واریتهٔ *کنترل‌های اعلام‌شده-در-برابر-اجرا-شده*). ([Ashby, Requisite Variety 1956](http://panarchy.org/ashby/variety.1956.html))

**همگرایی:** زیست‌شناسی (AIRE: تحمّل باید *تمرین* شود نه *اعلام*؛ شکست → APECED) و امنیت (کنترلِ آزموده‌نشده = theater؛ گاردریلِ deterministic لازم) **یک فیکسِ واحد** برای R-04 می‌سازند — اعتبارِ متقاطع، نه قیاسِ تزئینی.

## ۳) PROPOSAL — «AIRE Self-Test Rule» (proposal — needs Ari's verdict)

قاعدهٔ عمومی، سپس تصمیمِ سه بندِ R-04:

1. **قاعدهٔ AIRE (constitution-adjacent — نیازمندِ verdictِ آری):** هر کنترلی که در سطحِ اعلام‌شده ظاهر می‌شود — هر `*_REQUIRED*`, `MAX_*`, گیت، یا decider که در `config`/README/HITL_REQUIRED_FOR/blueprint نام برده شده — باید یک **تستِ negative-selection** داشته باشد که **شرطِ چالش را عامدانه بسازد** و *اثبات کند کنترل رفتار را عوض می‌کند* (halt/deny/escalate). کنترلی با هیچ تستِ passing = **INERT** → یا wire شود یا حذف. حالتِ سومِ «اعلام‌شده ولی تمرین‌نشده» یک نقصِ auditable است (سوپرست از قاعدهٔ Vestigial-Signalِ 2128؛ آن بندِ ۱ را می‌گیرد، این کلاسی که آن نمی‌بیند را هم).

2. **`MAX_STEPS` (بندِ داغ) — enforce، نه delete.** یک step-counterِ واقعی در `Orchestrator.run` که روی exceed **halt fail-closed** می‌کند (هم‌راستا با R-01/Anoikis). تستِ negative-selection: یک رانِ مصنوعیِ over-limit → assert که `halted` و `run_done` هرگز emit نشد. (زیستی: کلونِ high-affinity ارائه و *حذف* می‌شود.) این تنها بندِ side-effect-critical است؛ فازِ enforcement → `HUMAN-APPROVAL-REQUIRED`.

3. **`external_write` — تصمیمِ صریح.** یا (a) یک actuationِ واقعی که از HITL + `gate.act`ِ IGK عبور کند اضافه شود (آنگاه این بند خودش `HUMAN-APPROVAL-REQUIRED` است و باید با [[00 - Inbox/scout-digests/2026-07-04 2023 selfimprove-safety|Costimulation]]ِ دو-سیگنالی جفت شود)، یا (b) `external_write` از `HITL_REQUIRED_FOR` **برداشته** شود تا گیت درِ ناموجود را نگهبانی نکند. پیشنهادِ من: (b) برای الان (کمینه، بی‌ریسک)، چون هیچ actuationی وجود ندارد که گیت واقعاً محافظتش کند.

4. **`Supervisor.review` — حذفِ deciderِ مرده.** یا حذفِ `review` + توقفِ ساختِ Supervisor، یا re-integrate + آپدیتِ داک. deciderِ مرده = mTECی که آنتی‌ژن را ارائه نمی‌دهد؛ توهّمِ نظارت بدونِ نظارت. پیشنهاد: حذف (کمینه) مگر آری بخواهد نقشِ Supervisor زنده شود.

5. **گامِ صفرِ بی‌ریسک (فقط تست، پشتِ گیت نمی‌ماند):** قاعدهٔ ۱ را ابتدا به‌صورتِ یک **اسکنِ auditِ فقط-خواندنی** بنویس — فهرستِ هر کنترلِ اعلام‌شده در برابرِ وجود/عدمِ تستِ enforcement — و خروجی را به‌عنوانِ گزارش بده (نه تغییرِ رفتار). این «نقشهٔ APECED» است: کدام کنترل‌ها آنتی‌ژنِ presented-نشده‌اند. سپس فازِ enforcement (بندهای ۲–۴) پشتِ approval.

**کمینه/دامنه:** فقط کنترل‌های پرپیامد آزمونِ negative-selectionِ سخت‌گیرانه می‌گیرند؛ منطبق با اصلِ AIRE که همهٔ آنتی‌ژن‌ها را با شدتِ برابر ارائه نمی‌کند بلکه high-affinity/خطرناک‌ها را trim می‌کند. ترجیحِ **enforce+test** بر «حذفِ صرف» فقط وقتی کنترل واقعاً لازم است (مثلِ `MAX_STEPS`)؛ وگرنه حذف بهتر از تئاتر است.

## ۴) ریسک‌ها / trade-offها

- **autoinflammation (قرینهٔ 2041):** step-counterِ خیلی تنگ → haltِ رانِ سالمِ طولانی. کاهش: سقف با graceِ کالیبره‌شده از substratِ conformalِ [[00 - Inbox/scout-digests/2026-07-04 2008 selfimprove|Calibrated 2008]]، نه عددِ جادویی؛ + مسیرِ escalate-to-HITL (R-12) به‌جای haltِ خام.
- **هزینهٔ نگهداریِ قاعدهٔ AIRE:** «هر کنترل یک تست» بار می‌گذارد و می‌تواند خودش به checkbox تبدیل شود (تستِ تهیِ همیشه-سبز). کاهش: تست باید *شرطِ چالش را واقعاً بسازد و شکست را ببیند* (mutation-style)، نه یک assertِ صوری؛ این خودش یک meta-invariant است.
- **حذفِ نابه‌جا:** حذفِ `Supervisor`/`external_write` ممکن است قابلیتی را ببندد که آری بعداً بخواهد. کاهش: تصمیمِ delete-vs-wire صریحاً به verdictِ آری واگذار شد؛ این digest فقط دو مسیر را روشن می‌کند.
- **اشتباه‌گرفتن با 2128:** نباید یکی شوند — 2128 = خروجیِ هزینه‌دارِ دورریخته (honest signaling)؛ این = کنترلِ اعلام‌شده-ولی-تمرین‌نشده (negative-selection)، به‌علاوهٔ بندِ `MAX_STEPS` که هیچ فراخوانی ندارد و 2128 اصلاً نمی‌بیندش. (همان درسِ «origin ≠ integrity»ِ 2023.)
- **سطحِ approval:** قاعدهٔ ۱ constitution-adjacent؛ بندهای ۲–۴ enforcement روی `_code` → **HUMAN-APPROVAL-REQUIRED**. این digest فقط design sketch است، بدونِ لمسِ `_code`/config/README، بدونِ verbِ جدیدِ kernel، بدونِ mutationِ invariant.

## ۵) mycorrhizal links

- [[00 - Inbox/scout-digests/2026-07-04 2128 selfimprove]] — Vestigial Costly Signal (R-03): **خواهرِ مکمل** — آن خروجیِ دورریخته را می‌گیرد؛ این کنترلِ تمرین‌نشده را. با هم کلِ آنتی‌پترنِ false-assurance را می‌پوشانند.
- [[00 - Inbox/scout-digests/2026-07-04 2054 selfimprove-safety]] — Anoikis (R-01): سقفِ `MAX_STEPS` روی همان مسیرِ **fail-closed halt** می‌نشیند که Anoikis ساخت.
- [[00 - Inbox/scout-digests/2026-07-04 1850 selfimprove]] — Requisite-Variety Gate: through-line «واریتهٔ ادعایی > واریتهٔ مؤثر»؛ آنجا برای ناوگان، اینجا برای کنترل‌ها.
- مرجع: [[04 - Architect System/architect/04-Docs/fusion-audit/REFACTOR_PLAN]] R-04 (خانه؛ P4-03/P2-05/P4-04) + R-12 (escalate→HITL).

<!-- proposal — needs Ari's verdict · propose-only · SAFETY lane · AIRE Self-Test / R-04 -->
