---
type: report
status: draft
tags: [strategy, revenue, coherence-audit, outreach]
created: 2026-07-08
updated: 2026-07-08
created_by: agent
language: bilingual
---

# Track D — Coherence-Audit: shortlist مخاطب + drafts (ورودی ۰۷/۲۰)

> هدف: پرکردن §۶ خالیِ [[00 - Inbox/2026-07-06 1410 COHERENCE-AUDIT-PITCH-draft|COHERENCE-AUDIT-PITCH]] («۳ مخاطب هدف»). چون آری مخاطب فروش آماده ندارد، این نوت به‌جای اسمِ اشخاص، **۱۱ پروفایلِ خریدار** می‌سازد (۱۰ خریدار مستقیم + ۱ کانال/شراکت). هر پروفایل: چرا فیت است · زاویهٔ دقیقِ coherence-audit · یک draft پیامِ شخصی‌سازی‌شده به لحن §۷ پیچ.
>
> **آفر قفل‌شده (از پیچ):** Coherence Audit دو‌هفته‌ای، قیمت ثابت **$3k–5k**، ظرفیت ۱ پروژه در پنجره. هفتهٔ ۱ کشف → نقشهٔ ناسازگاری با شواهد؛ هفتهٔ ۲ نقشهٔ فیکس + ۲–۳ فیکسِ نمونهٔ اجراشده. **گارانتی:** اگر هفتهٔ اول ≥۵ ناسازگاریِ واقعی پیدا نشد، رایگان.
>
> **زبان drafts عمداً انگلیسی است** — خریدارها بین‌المللی و انگلیسی‌زبان‌اند (X/LinkedIn/Discord). `⟨…⟩` را آری per-person پر می‌کند. هیچ‌چیز اینجا ارسال نشده؛ فقط draft است.
>
> **نکته حریم:** این سرویسِ خودِ آری است (ممیزیِ انسجامِ سیستم‌های AI/دانش). ربطی به Project-F ندارد و هیچ اشاره‌ای به آن نیست.

---

## چطور از این لیست به ۳ نفر برسیم (توصیه)

سه بُعد برای انتخاب: (۱) **درد قابل‌مشاهده** — علناً از ناسازگاری/drift/هالوسینیشن شکایت کرده؟ (۲) **بودجه** — سیستم زنده و درآمدزا دارد که $3–5k برایش ناچیز است؟ (۳) **دسترسی** — کانال گرم (DM باز، معرفی، جواب‌دادن به cold). توصیهٔ پیش‌فرض من: **۱ خریدار مستقیمِ high-pain (پروفایل ۱ یا ۳)، ۱ ریسک‌بالا/بودجه‌بالا (پروفایل ۴)، و ۱ کانالِ تکثیرشونده (پروفایل ۱۱)** — تا هم یک قرارداد سریع، هم یک قرارداد بزرگ، هم یک مسیر تکرارشونده تست شود.

---

## پروفایل‌های خریدار

### ۱. بنیان‌گذار تنها با ۳+ ایجنت و صفر observability
- **چرا فیت:** چند ایجنت مستقل (support/sales/research) که هیچ لاگِ intent و حافظهٔ مشترک ندارند؛ خروجی‌های متناقض می‌گیرد و نمی‌تواند ردش را بزند. (گزارش‌های ۲۰۲۶ می‌گویند شایع‌ترین حفره در ۱۰ از ۱۲ سیستمِ solo-founder دقیقاً همین نبودِ intent-logging است.)
- **زاویهٔ audit:** نقشهٔ تعارضِ بین‌ایجنتی — کجا دو ایجنت تصمیم متضاد می‌گیرند، کجا intent اولیه گم می‌شود، کجا حافظهٔ مشترک وجود ندارد. خروجی: جدول «کدام ایجنت، کدام تعارض، چه هزینه».
- **کجا پیدا می‌شود:** IndieHackers، build-in-public در X، DEV Community.
- **draft:**
  > Hey ⟨name⟩ — saw you're running ⟨3+ agents / your one-person stack⟩ solo. Quick question: when two of your agents give conflicting answers, or one "forgets" a decision from last week, how do you actually trace *why*? I run a fixed-price, 2-week **Coherence Audit** — I map the costly contradictions across your agents/memory, hand you a prioritized fix-map, and ship 2–3 real fixes as proof. If I don't surface at least 5 genuine inconsistencies in week one, it's free. Worth 15 min this week to take a look?

### ۲. آژانس اتوماسیون AI با استکِ درهم‌ریختهٔ n8n/Make/Zapier
- **چرا فیت:** ده‌ها workflow برای چند کلاینت؛ پرامپت‌ها کپی‌شده و بین سناریوها drift کرده؛ منطق تکراری؛ هیچ single-source-of-truth. (منابع ۲۰۲۶: نگه‌داری و debug استکِ رشد‌کرده هزینهٔ عملیاتیِ اصلیِ این آژانس‌هاست.)
- **زاویهٔ audit:** ممیزیِ sprawl — پرامپت‌های تکراری/متضاد بین سناریوها، sub-flowهای کهنه/یتیم، جاهایی که یک تغییر باید همه‌جا اعمال می‌شد و نشد.
- **کجا پیدا می‌شود:** انجمن n8n، Make community، r/automation، AI-agency Twitter/LinkedIn.
- **draft:**
  > Hi ⟨name⟩ — ⟨your agency⟩ is clearly running a lot of automations across n8n/Make/Zapier. The question I keep hearing from agencies your size: when the same prompt logic is copy-pasted across 40 scenarios and one of them silently drifts, how do you catch it before a client does? I do a fixed-price, 2-week **Coherence Audit** of the whole stack — duplicated/conflicting prompts, stale sub-flows, no-source-of-truth gaps — with a ranked fix-map and 2–3 fixes shipped. Week one finds 5+ real issues or you pay nothing. Open to a 15-min look?

### ۳. اپراتور بات پشتیبانی/هلپ‌دسک روی یک KB
- **چرا فیت:** بات پشتیبانیِ AI روی help-center؛ مقالات کهنه‌اند و بات پاسخ‌هایی می‌دهد که با سند/پالیسی فعلی می‌جنگد — مستقیماً به churn و تیکت وصل است.
- **زاویهٔ audit:** انسجامِ KB↔bot — مقالات stale، پاسخ‌های متناقض دربارهٔ پالیسی/قیمت، retrieval که سند محصولِ اشتباه را می‌کشد.
- **کجا پیدا می‌شود:** جوامع Intercom/Zendesk AI، support-ops Slack، LinkedIn (Head of CX/Support).
- **draft:**
  > Hi ⟨name⟩ — I noticed ⟨company⟩ runs an AI support agent on top of your help center. One pattern I see a lot: the bot confidently answers with a policy that your docs quietly changed three months ago, and nobody notices until a customer escalates. I run a 2-week, fixed-price **Coherence Audit** that maps exactly where your knowledge base and your bot disagree — stale articles, contradictory policy answers, retrieval pulling the wrong product — plus a fix-map and 2–3 fixes done. If week one doesn't turn up 5 real contradictions, it's free. 15 minutes to see if it's worth it?

### ۴. استارتاپ SaaS عمودیِ RAG-محور (حقوقی/پزشکی/مالی «چت با اسنادت»)
- **چرا فیت:** کوئری‌های multi-hop/زمان‌حساس هالوسینیشنِ بااعتمادبه‌نفس تولید می‌کنند؛ مسئولیت حقوقی بالا؛ منابع نسخه‌های متضاد دارند. (بودجه بالا، ریسک بالا — قرارداد بزرگ‌تر.)
- **زاویهٔ audit:** grounding و citation-integrity — نسخه‌های متضادِ منبع، بازیابیِ سند منسوخ، جاهایی که هیچ گاردی جلوی ادعای بی‌منبع را نمی‌گیرد.
- **کجا پیدا می‌شود:** AI Engineer World's Fair، Towards AI، LangChain/LlamaIndex Discord، LinkedIn (founding engineer).
- **draft:**
  > Hi ⟨name⟩ — ⟨product⟩ lets people chat with ⟨legal/clinical/financial⟩ documents, which means a confidently-wrong, unsourced answer isn't a bug, it's liability. When your retrieval pulls an outdated version of a doc, or two source documents contradict each other, what stops the model from just picking one and sounding certain? I run a 2-week, fixed-price **Coherence Audit** focused on grounding integrity — conflicting source versions, stale retrieval, missing guardrails — delivered as an evidence-backed report, a fix-map, and 2–3 fixes shipped. Guaranteed 5+ real findings in week one or it's free. Worth 15 minutes?

### ۵. تیم knowledge-ops روی Notion / مشاور «مغز دوم» با لایهٔ AI Q&A
- **چرا فیت:** ویکیِ داخلیِ بزرگ + لایهٔ پرسش‌وپاسخ AI؛ SOPهای تکراری/متناقض، صفحات کهنه که به پاسخ AI خوراک می‌دهند.
- **زاویهٔ audit:** انسجامِ ویکی — SOPهای تکراری/متضاد، صفحات یتیم، محتوای stale که AI به‌عنوان حقیقت cite می‌کند.
- **کجا پیدا می‌شود:** Notion community، حلقه‌های PKM/Ness Labs، ops-Slackها، LinkedIn (Head of Ops/Knowledge).
- **draft:**
  > Hi ⟨name⟩ — with a Notion workspace as deep as ⟨company/your clients'⟩, the AI answer layer is only as coherent as the wiki underneath it. My guess is you've got the same SOP written three slightly-different ways, and the AI cites whichever it hits first. I do a 2-week, fixed-price **Coherence Audit** of the knowledge base feeding your AI — duplicate/conflicting SOPs, orphaned and stale pages, contradictions the assistant quietly repeats — with a ranked fix-map and 2–3 fixes done. 5+ real issues in week one or you don't pay. Up for a 15-min look?

### ۶. استارتاپ ایجنتِ فروش/SDR خودکار (outbound autonomous)
- **چرا فیت:** ایجنت‌ها پیام‌های ناسازگار می‌فرستند، تماس‌های قبلی را «فراموش» می‌کنند، با CRM تناقض دارند — مستقیماً به reputation و deal وصل.
- **زاویهٔ audit:** انسجامِ حافظهٔ ایجنت↔CRM — outreach تکراری، ادعاهای متناقض دربارهٔ محصول، context قبلیِ گم‌شده.
- **کجا پیدا می‌شود:** sales-tech Twitter، GTM-engineering Slack، LinkedIn (founder GTM tooling).
- **draft:**
  > Hey ⟨name⟩ — autonomous outbound is great until two of your agents email the same prospect with contradictory claims, or one forgets a call already happened. How are you catching that today? I run a 2-week, fixed-price **Coherence Audit** of your agent memory and CRM sync — duplicate outreach, conflicting product claims, dropped prior context — delivered as a prioritized fix-map plus 2–3 fixes shipped. If week one doesn't surface 5 real inconsistencies, it's free. 15 minutes this week?

### ۷. micro-SaaS از جنس prompt-chain / GPT-wrapper که ارگانیک رشد کرده
- **چرا فیت:** پرامپت‌ها hard-code شده در ده جای کد، بدون versioning؛ کیفیت بی‌سروصدا افت کرده (model/prompt drift) و هیچ گاردی رگرسیون را نمی‌گیرد.
- **زاویهٔ audit:** فهرست‌برداری پرامپت — پرامپت‌های پراکنده/تکراری، نبودِ version control، رگرسیونِ drift بدون گارد.
- **کجا پیدا می‌شود:** IndieHackers، r/SaaS، build-in-public X.
- **draft:**
  > Hi ⟨name⟩ — ⟨product⟩ has clearly grown fast, which usually means the prompts are scattered across the codebase with no version history and the output quietly got worse without anyone changing a line. When quality drifts, can you point to *which* prompt and *when*? I run a 2-week, fixed-price **Coherence Audit** — a full prompt inventory, duplicated/conflicting instructions, and the drift regressions no guard is catching — with a fix-map and 2–3 fixes done. 5+ real findings in week one or it's free. Worth a 15-min look?

### ۸. شرکت متوسط با پایلوت AI که گیر کرده («agentic AI برای ما جواب نداد»)
- **چرا فیت:** پایلوتی که خروجی متناقض داد و اعتماد مدیریت را فرسود؛ الان سرِ دوراهیِ کشتن یا relaunch است. (Forbes ۲۰۲۶: چرا agentic AI برای بعضی کار می‌کند و برای بعضی شکست می‌خورد.) audit مستقل = ابزار تصمیمِ اجرایی.
- **زاویهٔ audit:** یک ممیزیِ مستقلِ بی‌طرف به‌عنوان تشخیصِ پیش از تصمیم — نقشهٔ ناسازگاریِ شواهد-محور برای ارائه به مدیر، نه یک بازسازیِ کور.
- **کجا پیدا می‌شود:** LinkedIn (VP Eng / Head of AI / fractional CTO)، Forbes councils، شبکه‌های fractional-CTO.
- **draft:**
  > Hi ⟨name⟩ — I gather ⟨company⟩'s agentic pilot didn't land the way you hoped. Before you write it off (or rebuild it), it's usually worth knowing *why* it produced contradictory outputs — often it's stale context and conflicting sources, not the model. I run a 2-week, fixed-price **Coherence Audit**: an independent, evidence-backed map of exactly where the system is incoherent, with a prioritized fix-map you can take to the exec table, plus 2–3 fixes shipped as proof. If I can't surface 5 real inconsistencies in week one, there's no charge. Worth 15 minutes?

### ۹. تیم dev-tool/framework که خودش swarm ایجنتی روی LangGraph/CrewAI/AutoGen می‌سازد
- **چرا فیت:** dogfooding چند ایجنت؛ drift بین دستورهای ایجنت‌ها، تناقضِ حافظهٔ مشترک، پوششِ ناقصِ گارد.
- **زاویهٔ audit:** انسجامِ دستورِ بین‌ایجنتی + تناقض حافظهٔ مشترک + پوشش گارد؛ خروجی برای‌شان هم proof-point محصول است.
- **کجا پیدا می‌شود:** LangChain/CrewAI Discord، GitHub، AI Engineer World's Fair.
- **draft:**
  > Hey ⟨name⟩ — you're building the framework *and* dogfooding a swarm of agents on it, so you feel incoherence before your users do: agent instructions that contradict, shared memory that disagrees with itself, guards with gaps. Want an outside pass on it? I run a 2-week, fixed-price **Coherence Audit** — inter-agent instruction conflicts, shared-memory contradictions, guard coverage — as a report + fix-map + 2–3 fixes. Doubles as a proof-point you can point customers at. 5+ real findings in week one or it's free. 15 minutes?

### ۱۰. برند e-commerce/DTC با دستیار خرید AI + خلاصهٔ ریویو
- **چرا فیت:** دستیار با مشخصات محصول تناقض دارد، موجودی/پالیسی stale است — مستقیماً به conversion و برگشتِ کالا وصل.
- **زاویهٔ audit:** انسجامِ دادهٔ محصول↔دستیار — منابعِ اسپکِ متضاد، پاسخ‌های پالیسیِ کهنه، dedupe.
- **کجا پیدا می‌شود:** جوامع Shopify/DTC، ecommerce-ops Slack، LinkedIn (Head of Ecom).
- **draft:**
  > Hi ⟨name⟩ — an AI shopping assistant is a conversion machine right up until it tells a customer something your product page contradicts, or quotes a return policy you changed last quarter. How do you keep the assistant and the source-of-truth product data in sync today? I run a 2-week, fixed-price **Coherence Audit** — conflicting spec sources, stale policy answers, duplicate/contradictory product data feeding the assistant — with a fix-map and 2–3 fixes shipped. Guaranteed 5+ real findings in week one or it's free. Worth 15 min?

### ۱۱. (کانال، نه خریدار مستقیم) مشاور/fractional AI engineer یا آژانس با کلاینت‌های دارای همین درد
- **چرا فیت:** خودش لزوماً نمی‌خرد، ولی **کانالِ تکثیر** است — کلاینت‌هایش دقیقاً درد انسجام دارند. یک قراردادِ white-label/معرفی می‌تواند چند پروژه بیاورد.
- **زاویهٔ audit:** بسته‌بندیِ Coherence Audit به‌عنوان یک offer قابل‌فروشِ مجدد (white-label یا rev-share معرفی) که او به کلاینت‌هایش می‌فروشد.
- **کجا پیدا می‌شود:** AI-consultant Twitter، MLOps/LLMOps community، شبکه‌های آژانسی، AI Engineer World's Fair.
- **draft:**
  > Hi ⟨name⟩ — you're close to a lot of teams shipping AI features, which means you keep seeing the same mess: contradictory agent outputs, stale knowledge, prompts drifting with no guard. I've productized the fix as a 2-week, fixed-price **Coherence Audit** ($3–5k, evidence-backed report + fix-map + 2–3 fixes, 5-findings-or-free guarantee). Rather than pitch your clients directly, I'd love to explore white-labeling or a referral split so it's *your* offer. Worth 15 minutes to see if it fits your book?

---

## کجا این خریدارها جمع‌اند (watering holes — گراند‌شده با research)

- **بنیان‌گذارهای تنها/micro-SaaS:** IndieHackers، build-in-public در X، DEV Community (مثال: مقالهٔ ۲۰۲۶ «I Audited 12 Solo Founders' AI Agents» — دقیقاً همین سرویس، اعتبارسنجیِ تقاضا).
- **آژانس‌های اتوماسیون:** انجمن n8n، Make community، r/automation، LinkedInِ AI-agency.
- **RAG/vertical SaaS و framework teams:** AI Engineer World's Fair (SF، ژوئن–ژوئیه)، Towards AI، LangChain/LlamaIndex/CrewAI Discord، رویدادهای Temporal («reliable agents in production»).
- **eval/observability-aware buyers:** مخاطبِ محتوای Confident AI / MLflow / JetBrains دربارهٔ LLM observability و prompt-drift — کسانی که درد را نام‌گذاری کرده‌اند و آمادهٔ خریدِ راه‌حل‌اند.
- **enterprise pilot که گیر کرده:** LinkedIn، Forbes business councils، شبکه‌های fractional-CTO.

## ریسک‌ها / یادداشت صداقت

- هیچ اسم/شرکتِ واقعیِ مشخصی fabricate نشد — همه پروفایل‌اند؛ آری اسم واقعی را از watering-holeها پر می‌کند (`⟨…⟩`).
- drafts هنوز ارسال‌نشدنی‌اند تا آری per-person شخصی‌شان کند (خطِ اولِ «دیدم … را ساختی» باید واقعی و دقیق باشد وگرنه cold می‌ماند).
- گارانتیِ «۵ ناسازگاری یا رایگان» فقط وقتی امن است که آری مطمئن باشد در سیستمِ هدف واقعاً ≥۵ مورد هست — برای سیستم‌های خیلی کوچک/تمیز، پروفایل را رد کن.
- زبان: اگر مخاطبی فارسی‌زبان بود، draft قابل‌بومی‌سازی است (لحن §۷ پیچ آماده است).

## سؤال‌های تصمیمِ آری (verdict)

1. **کدام ۳ پروفایل؟** پیشنهاد پیش‌فرض: **۱ (solo، سریع) + ۴ (RAG عمودی، بزرگ) + ۱۱ (کانال، تکرارشونده)**. موافقی یا ترکیب دیگر (مثلاً ۳ پشتیبانی به‌جای ۱)؟
2. **زاویهٔ positioning:** روی کدام درد بیشتر مانور بدهیم — «تصمیم‌های متناقض ایجنت‌ها» یا «KB/دانشِ کهنه که AI cite می‌کند»؟ (draftها را به آن سمت تیز می‌کنم.)
3. **گارانتی:** «۵ ناسازگاری یا رایگان» را نگه داریم یا برای مخاطبِ enterprise به «audit پولی، بدون گارانتیِ رایگان» تبدیل کنیم؟
4. **کانال (پروفایل ۱۱):** آری حاضر است white-label/rev-share را روی میز بگذارد یا فقط مستقیم‌فروشی؟
5. آیا نیچ ثابت است (audit انسجام سیستم AI/دانش) یا §۵ پیچ باید عوض شود؟

## منابع

- [[00 - Inbox/2026-07-06 1410 COHERENCE-AUDIT-PITCH-draft]] · [[00 - Inbox/2026-07-06 PROBE-MERGE]]
- research (read-only، ۰۷/۰۸): DEV Community — "I Audited 12 Solo Founders' AI Agents in 2026"؛ Forbes — "Why Agentic AI Works For Some Companies And Fails For Others" (2026-07-06)؛ Confident AI — LLM observability / prompt-drift 2026؛ n8n/Make/Zapier 2026 comparison (workflow sprawl/maintenance)؛ AI Engineer World's Fair 2026.
