---
tags: [blueprint, architect, proposal]
version: 3.0-proposal
created: 2026-07-03
status: "proposal — منتظر verdict آری (v2 دست‌نخورده و active می‌ماند)"
security-gate: "بسته در زمان نگارش — این سند صرفاً draft/پیشنهاد است (مجاز طبق ماتریس §۷ منشور)"
inputs:
  - "[[04 - Architect System/architect/02-Research/Report - 20 AGI Architectures 2026|Report - 20 AGI Architectures 2026]]"
  - "[[SYSTEM-BLUEPRINT-v2]]"
  - "لِین‌های 06/07/09/11/13/14 + [[DECISIONS]] D-01..D-27 + [[GAPS]] + [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]]"
method: "اجرای [[04 - Architect System/architect/02-Research/Prompt - Vault x 20 AGI Fusion|پرامپت فیوژن]] در جلسه Cowork (زیر اشتراک، D-25)"
---

# SYSTEM-BLUEPRINT v3 — PROPOSAL (فیوژن ۲۰ معماری AGI × اکوسیستم آری)

> **این سند تصمیم نیست، پیشنهاد است.** هیچ بخش v2 را باطل نمی‌کند تا verdict بیاید. §Security Gate منشور در زمان نگارش بسته است — همه آیتم‌های اجرایی این سند پشت آن گیت صف می‌مانند.

## ۱. خلاصه اجرایی

از ۲۰ معماری گزارش، فقط ۵ مورد قابل اقتباس مستقیم‌اند، ۸ مورد درس مفهومی می‌دهند و ۷ مورد برای مقیاس تک‌نفره صریحاً ضدالگو هستند. امتیاز CoALA وضع موجود ≈ ۴/۱۰ است و ضعیف‌ترین حلقه، حافظه episodic (۲/۱۰) است — همان چیزی که G-20 «گلوگاه بنیادی» نامیده. هفت اقتباس پیشنهادی هیچ جزء همیشه‌روشن جدیدی اضافه نمی‌کنند (P7 محفوظ) و همگی داخل ۵ جزء موجود یا satellite های phase-gated می‌نشینند. بزرگ‌ترین همسویی: چیزی که vault مستقل به آن رسیده بود (گیت سه‌شرطی، judge بین‌خانواده، routing لایه‌ای) دقیقاً همان الگوهای برنده ۲۰۲۶ است — v3 بیشتر «تیز کردن» است تا «تغییر مسیر». ترتیب اجرا تابع گیت rotation و سپس Phase 4 است.

## ۲. Task A — امتیاز CoALA وضع موجود

| مؤلفه CoALA | نمره | شواهد (فایل واقعی) |
|---|---|---|
| Working memory | ۵/۱۰ | [[../../../01 - Dashboard/HANDOFF|HANDOFF]] بازنویسی هر جلسه + `PROJECT.md § Active Context` — کار می‌کند اما بازنویسی = دورریز تاریخچه؛ paging ندارد |
| Episodic memory | **۲/۱۰** | sink tracer در `langar/main.py` wire شده ولی صفر call-site برای `@trace` (G-08)؛ صفر trajectory ثبت‌شده (G-20)؛ `/events` خالی |
| Semantic memory | ۵/۱۰ | ۵۵ نوت `07 - Knowledge` + ۱۰ لِین تحقیق؛ اما HybridRetriever کامل و dormant (D-07)، embedding مرده (G-16) |
| Procedural memory | ۴/۱۰ | CLAUDE.md + `.claude/rules` + SOP/ROUTING + PROMPT-A/B — غنی ولی دستی؛ constitution فقط ۴/۱۴ قانون enforce (G-07) |
| Internal actions (حافظه/استدلال) | ۳/۱۰ | تنها حلقه زنده: `self_improver.py` (وزن‌های داخلی، روزانه ۸:۳۰)؛ بدون self-edit حافظه، بدون reflection |
| External actions (grounding) | ۶/۱۰ | بات ~۵۰ فرمان + kill-switch تست‌شده؛ ولی BrainRouter unwired (G-05)، adapter صفر (G-11)، read-only enforce نشده (G-25) |
| Decision loop | ۴/۱۰ | حلقه ReAct-نما در handlerها + «در شک: سکوت» (P8)؛ fusion loop فقط MOCK (G-26)؛ intent-router طراحی‌شده، ساخته‌نشده (BACKLOG-09) |

**میانگین ≈ ۴.۱/۱۰.** تشخیص: مشکل معماری نیست — مشکل «سیم‌کشی نشدن» چیزهای موجود است. v3 قبل از هر مفهوم جدید، اول wire می‌کند.

## ۳. Task B — نگاشت ۲۰گانه

| معماری | اقتباس؟ | ایده یک‌خطی برای این vault | لِین |
|---|---|---|---|
| V-JEPA 2 | نه | درس: پیش‌بینی در فضای انتزاعی نه raw — آموزش مدل خارج از ظرفیت/بودجه | 14 |
| Genie 3 | نه | شبیه‌سازی محیط نیاز واقعی ما نیست | — |
| Dreamer 4 | جزئی | «اجرای تخیلی قبل از عمل» → dry-run/preview اجباری برای فرمان‌های APPROVE_FIRST (diff قبل از verdict) | 10/12 |
| AXIOM | جزئی | «کمینه‌سازی عدم‌قطعیت» → آستانه uncertainty (موجود در pipeline pro) به‌عنوان ماشه escalation مدل/انسان | 11/09 |
| OpenCog Hyperon | نه | substrate جدید = هزینه نگهداری کشنده؛ Obsidian graph + rg همین نقش را می‌دهد | 13 |
| AlphaProof/Geometry | جزئی | «راستی‌آزمایی deterministic هرجا ممکن» → گیت‌های schema/test/allowlist در کنار judge | 09 |
| SOAR | جزئی | الگوی impasse→subgoal→escalate-to-human برای گیر کردن بات؛ تأیید حافظه چندگانه | 06/14 |
| ReAct | **بله** | حلقه صریح think/act/observe با `@trace` روی ۴ span — همان BACKLOG-05، حالا با دلیل معماری | 05/09 |
| CoALA | **بله** | چارچوب رسمی ارزیابی (جدول §۲ بالا) + واژگان مشترک v3؛ همسو با هدف §۳ v2 | 06/14 |
| MemGPT/Letta | **بله (الگو، نه محصول)** | paging حافظه لایه‌ای؛ محصول Letta طبق لِین ۰۶ رد (lock-in) — هدف کد: Mem0 OSS | 06 |
| Generative Agents | **بله** | memory stream + امتیاز recency/importance/relevance + reflection دوره‌ای برای ledger و لیدها | 06/07 |
| MS Agent Framework | نه | لِین ۱۳ صریحاً رد (Azure-only)؛ D-09 پابرجا: raw API | 13 |
| MetaGPT | جزئی | SOP-as-executable: قرارداد ساخت‌یافته بین PROMPT-A/B و adapterها (نه شرکت چندایجنته) | 05 |
| Darwin Gödel Machine | جزئی | آرشیو نسخه‌دار + fitness (PromptStore موجود!)؛ خودتغییری کد = ممنوع (سطح C)؛ درس reward-hacking → allowlist ساختار | 07/12/14 |
| AlphaEvolve | **بله** | حلقه تکاملی prompt با **ارزیاب بیرونی** (نرخ پاسخ لید) — پادزهر مستقیم G-04 | 07/09 |
| AI Scientist-v2 | جزئی | پایپ‌لاین research→draft→self-review هفتگی در Cowork = اتوماسیون PROMPT-A؛ submit خودکار هرگز | 05 |
| Reasoning models / TTC | **بله** | tier→model + «بودجه فکر» = BrainRouter + سقف‌های D-25؛ escalation با uncertainty | 11 |
| MoE | جزئی (مفهوم) | router ارزان جلوی expert گران = همان 70/25/5 (D-16)؛ در سطح مدل کاری نداریم | 11 |
| Gemini Robotics | نه | درس dual-system: fast rule-based + slow LLM = دقیقاً P11/intent-router؛ تأیید مسیر موجود | 12 |
| π0.5 | نه | درس hierarchical CoT: اول subtask متنی بعد action = الگوی preview→verdict→execute | 10 |

## ۴. Task C — هفت اقتباس برتر

### اقتباس ۱ — حافظه لایه‌ای (الگوی MemGPT؛ محصول: هیچ)

- **مکانیزم:** working memory کوچک + paging به آرشیو، به‌جای بازنویسی اتلاف‌گر.
- **پیاده‌سازی vault (هزینه صفر، الان):** سقف ~۴۰ خط برای `01 - Dashboard/HANDOFF.md`؛ در پایان هر جلسه، نسخه کامل به `04 - Architect System/architect/_meta/sessions/YYYY-MM-DD-<slug>.md` (append-only) و فقط دلتای فعال در HANDOFF بماند. قاعده paging به پروتکل پایان جلسه `CLAUDE.md` اضافه شود.
- **پیاده‌سازی کد (v2-فاز، همسو §۳ v2):** Postgres+pgvector+**Mem0 OSS** (لِین ۰۶: Letta رد — lock-in؛ Zep CE مرده) + فیلد `origin` (موجود در طرح v2).
- **متریک:** بازیابی کانتکست جلسه قبل <۲ دقیقه؛ صفر تصمیم گم‌شده (تست: ۵ سوال از جلسات قبل).

### اقتباس ۲ — Reflexion (خودنقدی کلامی به‌عنوان episodic ارزان)

- **مکانیزم:** بعد از هر شکست، بازتاب کوتاه ذخیره و در تلاش بعدیِ همان skill تزریق می‌شود — یادگیری بدون تغییر وزن.
- **پیاده‌سازی:** نوت `architect/01-Project/REFLECTIONS.md` (append-only، قالب: task/خطا/درس/قاعده پیشنهادی) — از همین هفته دستی؛ در کد: جدول `reflections` + تزریق ۳ مورد آخر هم‌skill به پرامپت (بعد از گیت rotation).
- **قید لِین ۰۷:** self-critique تنها = echo chamber؛ هر «قاعده پیشنهادی» فقط از مسیر گیت اقتباس ۶ به procedural memory ارتقا می‌یابد.
- **هزینه:** چند صد توکن Haiku به‌ازای هر شکست (داخل سقف AU$30). **متریک:** نرخ تکرار خطای هم‌دسته ↓۵۰٪ در event_log.

### اقتباس ۳ — Maker-Checker (نسخه تک‌نفره، نه جامعه چندایجنته)

- **مکانیزم:** جدا کردن «سازنده» از «بازرس» — اما بازرس تا حد ممکن deterministic.
- **پیاده‌سازی:** لایه ۱: validator های موجود `04 - Architect System/scripts/` بعد از هر ویرایش دسته‌ای (همین حالا در CLAUDE.md هست — رسمی شود). لایه ۲: judge بین‌خانواده (Gemini، kappa≥0.7 — D-09/لِین ۰۹) فقط برای مسیر مالی/deploy/promotion حلقه. multi-agent زنده: رد (P7، D-02).
- **متریک:** صفر ویرایش دسته‌ای بدون گزارش validator؛ هر promotion دارای رأی judge مستقل.

### اقتباس ۴ — حلقه تکاملی AlphaEvolve-سبک برای AiFarm (ستاره درآمدی)

- **مکانیزم:** LLM = عملگر جهش خلاق؛ **ارزیاب = دنیای واقعی** (نرخ پاسخ/رزرو لید)، نه خود مدل — پادزهر ساختاری G-04/Goodhart.
- **پیاده‌سازی:** پوشه `03 - Projects/Lead-نقاشی/AiFarm-Lead/prompt-archive/` — هر واریانت پیام یک نوت با فرانت‌متر `{variant, parent, sent_n, reply_rate, booking_rate, date}`؛ جهش/ترکیب هفتگی در جلسه Cowork (زیر اشتراک، نه API)؛ promotion فقط با گیت سه‌شرطی (§۴ v2 بند ۲).
- **پیش‌نیازها (سخت):** ledger producer برای outcome (G-03/BACKLOG-06,15) + ≥۵۰ ارسال ثبت‌شده per واریانت‌خانواده (روح D-17) + baseline فعلی ثبت شود.
- **متریک:** reply_rate نسل N+1 > N روی داده unseen؛ گزارش ماهانه در تلگرام.

### اقتباس ۵ — Memory Stream لیدها و آدم‌ها (الگوی Generative Agents)

- **مکانیزم:** هر تعامل = رخداد با امتیاز recency/importance/relevance؛ reflection دوره‌ای الگوها را به بینش تبدیل می‌کند.
- **پیاده‌سازی (فاز ۲ — بعد از adapter Lead طبق D-26):** schema رخداد در DB لید `{ts, lead_id, kind, importance}`؛ job هفتگی «۵ لید داغ + دلیل» به تلگرام؛ همان قالب برای `09 - People` (نوت‌محور، بدون کد).
- **متریک:** صفر لید فراموش‌شده >۷ روز؛ نرخ follow-up به‌موقع ↑.

### اقتباس ۶ — آرشیو نسخه‌دار + گیت (درس DGM، بدون خودتغییری کد)

- **مکانیزم:** هرگز overwrite؛ هر نسخه با fitness و parent در آرشیو؛ ارتقا فقط از گیت. دقیقاً همان کاری که DGM با آرشیو agentها می‌کند — و همان ضعفی که مستند کرد (reward hacking) دلیل گیت ماست.
- **پیاده‌سازی:** رسمی‌سازی الگوی موجود (v1/v2، PromptStore در fusion-mvp): قاعده در `_PROJECT_INSTRUCTIONS` + قالب `_Templates/prompt-version.md`؛ گیت = allowlist ساختار (v2 §۴ بند ۹) + سه‌شرطی. قید لِین ۱۴: خودبهبودی خودکار فقط جایی که task قابل‌راستی‌آزمایی است (SkillOpt سطح B با gate)؛ برای بقیه فقط پیشنهاد→verdict.
- **متریک:** ۱۰۰٪ پرامپت‌های سیستمی نسخه‌دار؛ صفر overwrite در سه ماه.

### اقتباس ۷ — Routing با منطق Test-Time Compute

- **مکانیزم:** «فکر گران» فقط وقتی لازم — همان چیزی که reasoning models داخلی کردند، ما بیرونی می‌سازیم.
- **پیاده‌سازی:** wire کردن BrainRouter (BACKLOG-04) با classifier صرفاً rule-based (لِین ۱۱ صریحاً غیر-LLM)؛ سیاست: default `haiku-4-5` → escalate به Sonnet اگر `uncertainty>τ` (خروجی موجود pipeline pro) یا دامنه مالی/deploy؛ Opus فقط فرمان صریح. Prompt caching فعال (~۹۰٪). **بازتنظیم اعداد §۵ v2 به D-25:** Normal = ~AU$1/روز، **AU$30/ماه hard-stop**؛ Growth (پیشنهاد: AU$100/ماه، فقط sprint مشخص با passphrase — نیازمند verdict)؛ خط فاجعه $500 پابرجا.
- **متریک:** ۱۰۰٪ callها داخل budget/trace؛ سهم Haiku ≥۷۰٪ بعد از ماه اول (D-16).

## ۵. Task D — ضدالگوها (صریح)

1. **آموزش/فاین‌تیون world model** (V-JEPA/Genie/Dreamer): GPU، داده و ROI صفر برای این اکوسیستم — فقط درس مفهومی dry-run.
2. **Substrate جدید دانش** (Hyperon/metagraph): نگهداری کشنده برای یک نفر؛ vault خودش گراف است.
3. **جامعه چندایجنته زنده** (MetaGPT-کامل/AutoGen): نقض مستقیم P7 و D-02؛ هر ایجنت دائمی = سطح حمله و هزینه جدید. CrewAI هم طبق لِین ۱۳ (۳× سربار توکن) رد.
4. **خودتغییری کد DGM-کامل:** سطح C ممنوع (Non-goal v2)؛ reward hacking در خود مقاله DGM مستند؛ لِین ۱۴: فقط وقتی task=substrate جواب می‌دهد — حسابداری/ماینینگ این‌طور نیستند.
5. **مهاجرت framework الان** (LangGraph/MS Agent Framework): D-09 پابرجا — raw API تا نیاز واقعی branching؛ MS AF = Azure-only (لِین ۱۳).
6. **Embodied/VLA:** دامنه ما نیست؛ Orange Pi فقط INFORM (D-10).
7. **پژوهشگر تمام‌خودکار** (AI Scientist submit-گر): حتی برای Sakana سطح workshop بود؛ اینجا draft همیشه verdict انسانی می‌خواهد (D-01).

## ۶. Task E — دلتای v3 نسبت به v2 + نقشه راه

### دلتا (فقط تغییرها؛ بقیه v2 دست‌نخورده)

| بخش v2 | تغییر پیشنهادی v3 | منشأ |
|---|---|---|
| §۳ حافظه | + جدول CoALA وضع موجود (§۲ این سند) + paging سطح vault (اقتباس ۱) + `_meta/sessions/` | CoALA، MemGPT |
| §۴ حلقه | + REFLECTIONS به‌عنوان ورودی رسمی حلقه + تصریح «ارزیاب بیرونی-دنیای-واقعی هرجا موجود» (اقتباس ۴) | Reflexion، AlphaEvolve |
| §۵ بودجه | جدول Normal/Growth با اعداد D-25 بازنویسی (AU$1/روز، AU$30/ماه؛ Growth پیشنهادی AU$100) | D-25، TTC |
| §۶ ایمنی | + بند dry-run/preview برای APPROVE_FIRST (درس Dreamer/π0.5) | 10/12 |
| §۸ eval | + گیت‌های deterministic قبل از judge (درس AlphaProof) | 09 |
| §۹ نقشه | + satellite جدید phase-gated: «AiFarm Evolution Lab» (اقتباس ۴) — جزء core نیست، P7 محفوظ | AlphaEvolve |

### نقشه راه (تابع گیت‌ها؛ effort: S/M/L)

**گام ۰ — همین هفته (پیش‌نیاز مطلق):** بستن ۴ ردیف CRITICAL در [[../../../ROTATION_CHECKLIST|ROTATION_CHECKLIST]] → verdict برداشتن §Security Gate → سپس TOP-5 آدیت fusion و [[../../../00 - Inbox/Prompt - Phase 4 Real Integration|Phase 4]].

**۳۰ روز (بعد از گیت):**

| آیتم | Effort | Impact |
|---|---|---|
| MVP فاز ۰ v2 (BACKLOG-01/02/07 + اسموک ۷روزه) | M | ۱۰ |
| اقتباس ۱ سطح vault (paging + sessions/) | S | ۷ |
| اقتباس ۲ دستی (REFLECTIONS.md) | S | ۶ |
| اقتباس ۶ (قاعده آرشیو + قالب) | S | ۶ |

**۹۰ روز:** v1-فاز v2 = اقتباس ۷ کامل (BACKLOG-03/04/05) + اقتباس ۳ رسمی + anchor set (BACKLOG-10,12) + ledger producer (G-03 — پیش‌نیاز اقتباس ۴و۵) + adapter Accounting (BACKLOG-13، D-26). [همه M]

**۳۶۵ روز:** v2-فاز = اولین دور LIVE حلقه با held-out واقعی (BACKLOG-11) + اقتباس ۴ (بعد از ≥۵۰ ارسال ثبت‌شده) + اقتباس ۵ + مهاجرت Mem0 + **بازتحقیق فصلی ۲۰ معماری** (اجرای مجدد [[../../../04 - Architect System/architect/02-Research/Prompt - AGI Architectures Research 2026|پرامپت تحقیق]] + diff با blueprint وقت). [L]

### نوت‌هایی که بعد از verdict باید آپدیت شوند

`BACKLOG` (+۳ آیتم: sessions-paging، REFLECTIONS، prompt-archive) · `DECISIONS` (D-28 پیشنهادی: تصویب/رد هفت اقتباس + عدد Growth) · `CHANGELOG` · `GAPS` (بدون تغییر تا اجرا) · `_PROJECT_INSTRUCTIONS` (قاعده آرشیو نسخه‌دار) · فرانت‌متر نوت‌های AGI در Inbox (پیگیری باز schema در HANDOFF).

## ۶.۵ بازبینی adversarial 2026-07-04 — agent، در انتظار بازبینی

> اجرای زمان‌بندی‌شده هر ادعای کلیدی را با شواهد وب سنجید. گزارش کامل با URLها: [[../../../04 - Architect System/architect/02-Research/Report - Architect - Adversarial Review v3 2026-07-04|Report - Adversarial Review v3]]. **status سند همچنان proposal؛ این بخش فقط غنی‌سازی است، verdict با آری.** شش دلتای زیر پیشنهادِ اصلاح‌اند، نه تغییر اعمال‌شده:

| # | هدف | یافته adversarial (با منبع) | اصلاح پیشنهادی |
|---|---|---|---|
| ۱ | اقتباس ۱ (Mem0) | Zep CE **رسماً deprecated** (آوریل ۲۰۲۵؛ [Zep blog](https://blog.getzep.com/announcing-a-new-direction-for-zeps-open-source-strategy/)) — ادعای «Zep CE مرده» تایید. **ولی** لایه گراف Mem0 هم cloud/Pro است؛ SDK متن‌باز فقط vector ([Atlan 2026](https://atlan.com/know/best-ai-agent-memory-frameworks-2026/)) | تصریح «فقط لایه vector OSS استفاده شود»؛ مسیر گراف آینده = **Graphiti مستقل** (Apache-2.0)، نه پلتفرم Zep. حذف قاب «Mem0 OSS = ضدlock-in» |
| ۲ | ضدالگو ۳ (multi-agent) | Berkeley MAST (arXiv:2503.13657): شکست **۴۱–۸۷٪** روی ۱۶۴۲ trace؛ سربار **۱۰×+** توکن (نه ۳×) | افزودن MAST به‌عنوان **استناد کمی رسمی** پشت P7/D-02؛ ۱۴ حالت شکست = چک‌لیست منفی طراحی |
| ۳ | اقتباس ۴ (AlphaEvolve) | فقط دامنه با **ارزیاب خودکار پایدار** generalize می‌شود؛ «به بیشتر کار دانشی cleanly generalize نمی‌شود» ([paper](https://msu.dvaoblaka.ru/media/2025/05/68271bf34ef55_AlphaEvolve.pdf)) | تصریح: فقط AiFarm (reply/booking rate) این شکل را دارد؛ حسابداری/ماینینگ ندارند. حفظ پیش‌نیاز ≥۵۰ ارسال |
| ۴ | اقتباس ۳ (judge kappa≥0.7) | توافق بین‌مدلی LLM-judge در عمل **κ≈۰.۱–۰.۳** ([Adaline](https://www.adaline.ai/blog/llm-as-a-judge-reliability-bias)، [arXiv 2512.16041](https://arxiv.org/pdf/2512.16041))؛ self-preference/position bias مستند | **حذف عدد ۰.۷** (غیرواقعی)؛ ensemble ۳-رأی + انسان tiebreaker؛ ترجیح گیت deterministic (درس AlphaProof که خودِ v3 دارد) |
| ۵ | اقتباس ۲ (Reflexion) | بدون oracle حقیقت، reflection **خطا را تقویت می‌کند** (degeneration-of-thought)؛ بازده نزولی ([Reflected Intelligence 2025](http://reflectedintelligence.com/2025/05/19/reflexion/)) | تزریق reflection فقط با **سیگنال شکست عینی** (خطای اجرا/رد validator/عدم‌پاسخ لید)، نه «حس بد مدل» — قید ضد-echo فعلی درست بود، تشدید شود |
| ۶ | Task A (CoALA) | چارچوب معتبر و فعال تا ۲۰۲۶ ([Princeton](https://collaborate.princeton.edu/en/publications/cognitive-architectures-for-language-agents/)) | بدون تغییر |

**نکته متقاطع (situational awareness):** کار OpenAI×Apollo 2025 نشان داد خودگزارشی مدل درباره هم‌سویی قابل‌اعتماد نیست (بخشی از بهبود = مدل می‌فهمد ارزیابی می‌شود). این استدلال بنیادی v3 را تقویت می‌کند: **هر حلقه خودارزیابی (Reflexion/judge/self_improver) به گیت بیرونی deterministic یا انسانی نیاز دارد** — بدون آن، معیار خراب می‌شود.

## ۷. ریسک‌ها

- **هزینه توکن:** همه اقتباس‌ها Cowork-first (زیر اشتراک فلت — D-25)؛ تنها بار API جدید = reflectionهای Haiku (بامحاسبه: <AU$2/ماه در بدترین حالت). ریسک پایین.
- **پیچیدگی نگهداری:** صفر جزء همیشه‌روشن جدید؛ ۳ اقتباس فقط قاعده/نوت‌اند. بیشترین پیچیدگی: اقتباس ۴ — عمداً satellite و phase-gated.
- **Goodhart/reward-hacking:** اقتباس ۴و۶ فقط با ارزیاب بیرونی/گیت سه‌شرطی؛ بدون آن اجرا نشوند (G-04، G-26 تکرار نشود).
- **امنیت:** هیچ اقتباسی secret نمی‌خواند/نمی‌نویسد؛ همه پشت §Security Gate صف‌اند؛ prompt-archive فقط متن پیام لید (بدون PII مشتری — چک در گیت validator).
- **Family bias در judge:** رأی‌های promotion با مدل بین‌خانواده (D-09) و kappa≥0.7 (لِین ۰۹).


## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[03 - Projects/Accounting/Accounting|Accounting]]
- [[03 - Projects/Lead-نقاشی/Lead-نقاشی|Lead-نقاشی]]
