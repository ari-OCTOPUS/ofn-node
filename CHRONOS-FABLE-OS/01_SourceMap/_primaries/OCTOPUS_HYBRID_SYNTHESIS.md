---
type: comparative-analysis + hybrid-spec
project: "Octopus / fusion-mvp — سنتزِ هیبرید با استکِ ایجنتیِ ۲۰۲۶"
created: 2026-07-08
status: "پیش‌نویس برای وتوی Ari — هیچ نام‌گذاری‌ای نهایی نیست"
depends_on: "OCTOPUS_CHRONO_ARCHITECTURE.md (design locked)"
epistemics: "【E】 مستندِ منتشرشده/تثبیت‌شده · 【P】 استنتاجِ موجه · 【S】 گمانه"
---

# 🐙 اختاپوس × ده استکِ ایجنتیِ بزرگِ ۲۰۲۶ — تحلیل، مقایسه، طرحِ هیبرید

## ۰. چالش — قبل از هر چیز

**دو خطا در خودِ درخواست:**

1. **عدم‌تطابقِ لایه.** سندِ Chrono تو از قبل ۱۲ معماریِ مرجع دارد — اما همه از لایه‌ی **سیستم‌های توزیع‌شده** (HLC، Raft، SWIM، Temporal). استک‌های شرکت‌های بزرگ در ۲۰۲۶ لایه‌ی **orchestration/product** را حل می‌کنند: مدیریتِ context، توپولوژیِ ایجنت‌ها، حافظه، ایزولاسیون، interop. مقایسه‌ی مستقیمِ «معماری با معماری» گمراه‌کننده است؛ مقایسه‌ی درست **بُعد به بُعد** است (بخش ۳). 【P】
2. **ریسکِ meta-escalation.** «سیستمِ هیبریدی که آپدیتِ همه باشد» الگویِ شناخته‌شده‌ی planning-instead-of-doing است. سندِ Chrono الان code-ready است. اگر هیبرید یعنی بازطراحی قبل از shipping ِ P-Chrono-1، این سند ضدِ خودش عمل کرده. **قاعده‌ی این سند: هیچ ماژولِ هیبریدی جایگزینِ P-Chrono-1..4 نمی‌شود؛ همه بعد از آن سوار می‌شوند.** [قید سخت]

---

## ۱. ده استکِ مرجع — وضعیتِ ژوئیه‌ی ۲۰۲۶

| # | استک | هسته‌ی معماری | چه چیزی را واقعاً حل می‌کند | مبنا |
|---|---|---|---|---|
| 1 | **Anthropic** (Research system + Claude Agent SDK) | orchestrator-worker: ایجنتِ lead برنامه می‌ریزد، subagentهای موازی با contextِ جدا spawn می‌کند؛ plan قبل از پرشدنِ context به memory بیرونی می‌رود؛ pass جداگانه‌ی citation. workerها با هم حرف نمی‌زنند — کلِ تصمیمِ توپولوژی در orchestrator | **مقیاس‌پذیریِ token**: مصرفِ token به‌تنهایی ~۸۰٪ واریانسِ کارایی را توضیح می‌دهد؛ context windowهای مستقل = ظرفیتِ موازی. ۹۰٪+ بهبود بر تک‌ایجنت در evalهای پژوهشی | 【E】 |
| 2 | **OpenAI** (Agents SDK + harness) | primitiveهای مینیمال: Agent / Handoff / Guardrail / Tracing. ۲۰۲۶: sandbox execution + model-native harness برای long-horizon؛ Agent Builder ِ بصری در حالِ برچیده‌شدن — بازگشت به code-first | ارکستراسیونِ سبک + ایمنیِ ماژولار (guardrail به‌مثابه‌ی لایه‌ی جدا) + اجرای ایزوله | 【E】 |
| 3 | **Google** (ADK 1.0 + A2A) | درختِ سلسله‌مراتبیِ ایجنت‌ها (root → sub → sub-sub)؛ A2A v1.x زیرِ Linux Foundation: Agent Card امضاشده، delegation بینِ فریم‌ورک‌های ناهمگون؛ +۱۵۰ سازمان در production | **interop**: ایجنتِ ساخته‌شده با هر فریم‌ورکی به ایجنتِ دیگر کار واگذار کند — «HTTP ِ ایجنت‌ها» | 【E】 |
| 4 | **Microsoft** (Agent Framework 1.0، آوریل ۲۰۲۶) | ادغامِ AutoGen (ارکستراسیونِ چندایجنتی، GroupChat/debate) + Semantic Kernel (state ِ session، type-safety، middleware، telemetry)؛ gateهای تأییدِ انسانی first-class؛ MCP/A2A بومی | enterprise-grade بودن: state + observability + human approval در یک SDK | 【E】 |
| 5 | **Amazon** (Bedrock AgentCore) | framework-agnostic: Runtime (ایزولاسیونِ session با microVM ِ اختصاصی)، Memory (رویدادِ کوتاه‌مدت + استخراجِ async ِ حافظه‌ی بلندمدت با استراتژی‌های semantic/preference/summary)، Gateway/Identity، Harness ِ configurationی، و حلقه‌ی «recommendations»: تحلیلِ trace ِ production → پیشنهادِ اصلاحِ prompt/tool | **عملیات در مقیاس**: ایزولاسیون، حافظه‌ی مدیریت‌شده، بهبودِ مبتنی بر trace | 【E】 |
| 6 | **LangGraph** | گرافِ حالت با checkpointing ِ پایدار، crash recovery، time-travel debugging؛ durable execution روی هر node | تنها فریم‌ورکی که «قدمِ ۷ شکست خورد، حالا چه؟» را first-class جواب می‌دهد | 【E】 |
| 7 | **CrewAI** | ایجنتِ role-based با تعریفِ زبانِ طبیعی؛ backendهای pluggable ِ memory/RAG (v1.14) | سرعتِ prototyping؛ ارگونومی | 【E】 |
| 8 | **Temporal** | durable execution ِ صنعتی: replay ِ event-sourced، ممنوعیتِ خواندنِ مستقیمِ ساعت، worker heartbeat | (از قبل در سندِ Chrono — مرجعِ TINV-5) | 【E】 |
| 9 | **لایه‌ی پروتکل: MCP + A2A** | MCP = ایجنت↔ابزار؛ A2A = ایجنت↔ایجنت؛ هر دو زیرِ Linux Foundation؛ MCP بالای ۲۰۰ پیاده‌سازیِ سرور | استانداردِ مرزها؛ حذفِ lock-in | 【E】 |
| 10 | **LlamaIndex Workflows 1.0** | workflow ِ event-driven با stepهای typed؛ stable از ژوئنِ ۲۰۲۶ | pipelineهای دانش‌محور | 【E】 |

**الگوی مشترکِ کلِ صنعت در ۲۰۲۶ 【P】:** چهار primitive همگرا شده‌اند — (۱) subagent با context ِ ایزوله، (۲) حافظه‌ی دولایه (رویدادِ خام + استخراجِ بلندمدت)، (۳) durable state/checkpoint، (۴) حلقه‌ی بهبودِ مبتنی بر trace. آنچه **هیچ‌کدام** ندارند: مدلِ زمان، میرایی، و هزینه‌ی متابولیک.

---

## ۲. کجا اختاپوس جلوتر است (خوبی‌های معماریِ تو)

| مزیت | صنعت چه دارد | ارزیابی |
|---|---|---|
| **گیتِ اثرِ برگشت‌ناپذیر (TINV-7)** — هیچ send/publish بدونِ append به قلب settle نمی‌شود | تقریباً هیچ. «human approval gate» ِ Microsoft/OpenAI اختیاری و per-workflow است، نه قانونِ فیزیکیِ سیستم | 【P】 قوی‌ترین وجهِ تمایز. صنعت این را در ۲۰۲۷–۲۰۲۸ کشف خواهد کرد |
| **ترتیبِ کلیِ واحد + hash-chain (TINV-2/3)** | LangGraph/Temporal لاگِ replay دارند اما نه لاگِ **معتبرِ ضدجعل** با فلشِ زمانِ انسانی | 【P】 |
| **قضاوتِ انسانی به‌مثابه‌ی root-of-trust** (نه checkbox) — لنگرِ ضدِ drift | حلقه‌های بهبودِ صنعت (trace grader ِ OpenAI، recommendations ِ AgentCore) **خود-ارجاع‌اند**: مدل، خروجیِ مدل را می‌سنجد → ریسکِ agreement spiral. Anchor Ledger دقیقاً همین حفره را می‌بندد | 【P】 |
| **قیدِ متابولیک (TINV-6)** — نرخِ تجربه کران‌دار، سریع‌تر = پیرتر | صنعت فقط budget guard و loop/timeout protection دارد — حسابداریِ هزینه، نه فیزیکِ هزینه | 【P】 |
| **liveness ِ تدریجی (phi-accrual, suspected)** | اکثر فریم‌ورک‌ها retry ِ ساده یا timeout ِ باینری | 【E】 |
| **تعیّن‌گراییِ زمان (TINV-5)** | فقط Temporal و LangGraph معادل دارند؛ بقیه wall-clock می‌خوانند و replay ندارند | 【E】 |

---

## ۳. کجا اختاپوس عقب است (بدی‌ها — بی‌تعارف)

| ضعف | صنعت چه کرده | شدت |
|---|---|---|
| **توپولوژیِ ایستا: ۶ پای ثابت.** یافته‌ی Anthropic: کارایی تابعِ ظرفیتِ token ِ موازی است. پای ثابت یعنی سقفِ موازی‌سازیِ ثابت — کارِ سنگینِ پژوهشی/lead-gen زیرِ ظرفیت می‌ماند | spawn ِ پویا: lead agent به‌قدرِ نیاز subagent می‌سازد و می‌کُشد | 🔴 بالا |
| **بدونِ استراتژیِ context/حافظه.** لاگ، رویداد ذخیره می‌کند اما هیچ مکانیزمی برای compaction، خلاصه‌سازی، یا استخراجِ حافظه‌ی بلندمدت پیش از سرریزِ context ِ LLM نیست. پای Research بعد از ۵۰ چرخه چه چیزی «به یاد می‌آورد»؟ | Anthropic: externalize ِ plan قبل از ۲۰۰k؛ AgentCore: استخراجِ async ِ semantic/summary از رویدادهای خام | 🔴 بالا |
| **حلقه‌ی بهبودِ ناقص.** دکتر restart می‌کند (OTP) اما «evolve» فعلاً نامش هست، مکانیزمش نیست: هیچ مسیرِ trace → پیشنهادِ اصلاحِ prompt/tool → اعمال وجود ندارد | AgentCore recommendations؛ trace grader ِ OpenAI | 🟠 متوسط |
| **checkpoint ِ رسمی نیست.** known-good restore هست، اما نه checkpoint ِ per-beat با قابلیتِ time-travel. debugging ِ گذشته‌ی اختاپوس الان یعنی خواندنِ دستیِ لاگ | LangGraph: checkpoint + time-travel first-class | 🟠 متوسط |
| **ایزولاسیونِ صفر.** تک‌process، پاها حافظه‌ی مشترک. پای compromised (مثلاً prompt injection از leadِ ورودی) کلِ بدن را می‌آلاید | microVM (AgentCore)، sandbox (OpenAI) — روی Orange Pi ناممکن، اما process-level ممکن است | 🟠 متوسط |
| **قفل‌شدگی/interop صفر.** نه MCP ِ رسمی در مرزِ ابزار، نه A2A. تا وقتی تک‌نفره‌ای مشکل نیست؛ روزی که leg ِ خارجی بخواهی، بازنویسی است | MCP/A2A استانداردِ de facto با +۱۵۰ سازمان | 🟡 پایین (فعلاً) |
| **bus factor = 1 روی قلب.** توقفِ human-append → stasis طراحی‌شده و canon-سازگار است؛ اما عملیاتاً یعنی تعطیلاتِ تو = کمای سیستمِ کسب‌وکار. برای مأموریتِ «۲۴/۷ روی lead» تناقضِ عملیاتی دارد | صنعت اصلاً انسان را الزامی نکرده (ضعفِ آن‌ها، اما راحتیِ عملیاتی‌شان) | 🟡 طراحی‌شده، ولی باید صریح پذیرفته شود |

---

## ۴. طرحِ هیبرید — Chrono هسته می‌ماند، چهار primitive ِ صنعت پیوند می‌خورد

**اصلِ پیوند:** هر ماژولِ واردشده باید (الف) زیرِ invariantهای TINV بنشیند، (ب) هزینه‌ی متابولیکِ صریح داشته باشد. ماژولی که هزینه ندارد وارد نمی‌شود.

### H-1 · پاهای زایا (dynamic sub-legs) — از Anthropic
هر پا مجاز است زیرِ خودش subagentهای **فانی و موقت** spawn کند (context ِ جدا، مأموریتِ self-contained، بدونِ ارتباطِ افقی — دقیقاً قیدِ Anthropic).
- **قیدهای TINV:** sub-leg از HLC ِ والد fork می‌شود؛ **حقِ نوشتن به LANGAR ندارد** — خروجی فقط از راهِ والد بالا می‌رود (no core fragmentation حفظ می‌شود). عمرش حداکثر N ضربان؛ بعدش kill ِ اجباری.
- **هزینه:** tokenهای sub-leg در `experience_rate` ِ والد حساب می‌شوند → پایی که زیاد spawn کند سریع‌تر پیر می‌شود. spawn ِ بی‌کران = خودکشیِ متابولیک. [این قید را صنعت ندارد و مزیتِ توست]
- **ریسک:** پیچیدگیِ scheduling روی تک‌process؛ سقفِ سختِ همزمانی لازم است (پیشنهاد: ۲–۳ sub-leg ِ فعال کل، نه per leg). 【P】

### H-2 · نردبانِ حافظه — از AgentCore/Anthropic
دولایه: (۱) رویدادِ خام = همان لاگِ موجود؛ (۲) job ِ استخراجِ بلندمدت که هر K ضربان (نه wall-clock — سازگار با TINV-5) رویدادهای پا را به حافظه‌ی فشرده (خلاصه/semantic) تبدیل می‌کند و در جدولِ `leg_memory` می‌نویسد. پا در شروعِ هر چرخه memory ِ خودش را بارگذاری می‌کند، نه کلِ تاریخچه.
- **قید:** حافظه‌ی استخراج‌شده **غیرمعتبر (non-authoritative)** است — تنها منبعِ حقیقت LANGAR است؛ حافظه فقط cache ِ شناختی است و بازتولیدپذیر از لاگ.
- **هزینه:** استخراج خودش رویداد است، experience مصرف می‌کند؛ فراموشی (eviction ِ حافظه‌ی قدیمی) اجباری است — حافظه‌ی بی‌کران ممنوع، همان قیدِ ضدِ AI-god. 【P】

### H-3 · checkpoint ِ per-beat + time-travel — از LangGraph
تو ۸۰٪ راه را رفته‌ای: TINV-5 + HLC + لاگ یعنی replay ممکن است؛ فقط رسمی‌اش کن. در هر write-barrier ِ ضربان، snapshot ِ سبکِ state ِ هر پا (چند KB) ذخیره شود؛ ابزارِ `replay(from_beat, to_beat)` برای debugging.
- **هزینه:** storage روی SQLite؛ retention ِ چرخشی (مثلاً ۱۰۰۰ ضربانِ آخر full، قبل‌تر فقط لاگ).
- **چرا اول این:** ارزان‌ترین ماژول، بیشترین اهرم برای دیباگِ H-1/H-2 ِ بعدی. 【P】

### H-4 · دکترِ trace-grader ِ لنگردار — از AgentCore + Anchor Ledger ِ خودت
دکتر از restart-only به حلقه‌ی کامل ارتقا می‌یابد: تحلیلِ traceهای production → پیشنهادِ مشخصِ اصلاحِ prompt/tool-description → **اما اعمالِ هیچ اصلاحی بدونِ human-append به LANGAR settle نمی‌شود** (TINV-7 روی خود-تغییری). این دقیقاً ترکیبِ الگوی صنعت با حفره‌ای است که صنعت باز گذاشته: حلقه‌ی بهبودِ آن‌ها self-referential است؛ حلقه‌ی تو لنگرِ انسانی دارد. Anchor Ledger ِ موجود همین‌جا integrate می‌شود.
- **هزینه:** هر چرخه‌ی evolve یک قضاوتِ انسانی می‌خواهد → نرخِ تکامل با نرخِ حضورِ تو کران‌دار است. این feature است، نه bug — تکاملِ بی‌لنگر همان drift است. 【P】

### H-5 · مرزِ interop (deferred)
MCP در مرزِ ابزارها هر جا ابزارِ نو اضافه می‌شود؛ A2A Agent Card فقط اگر روزی leg ِ بیرونی خواستی. **الان نساز.** 【S】

**آنچه عمداً وارد نمی‌شود:** microVM (سخت‌افزار ندارد)، visual builder (خودِ OpenAI دارد جمعش می‌کند — code-first برنده شد)، مهاجرت به هیچ فریم‌ورکی (لایه‌ی Chrono ِ تو را هیچ‌کدام ندارند؛ مهاجرت یعنی حذفِ تنها مزیت).

---

## ۵. نقشه‌ی راه

| فاز | محتوا | پیش‌نیاز | معیارِ خروج |
|---|---|---|---|
| **۰ (الان)** | **P-Chrono-1..4 بدونِ تغییر ship شود.** هیچ کارِ هیبرید قبل از این | — | heartbeat زنده؛ HLC روی هر رویداد؛ `age_tick` فقط human-append |
| **۱** | H-3: checkpoint ِ per-beat + `replay()` | P-Chrono-1..4 | بازسازیِ state ِ هر پا در ضربانِ دلخواه < ۵s |
| **۲** | H-2: نردبانِ حافظه + eviction | فاز ۱ | پای Research بعد از ۱۰۰+ چرخه context overflow نگیرد؛ حافظه از لاگ بازتولیدپذیر باشد |
| **۳** | H-1: sub-legهای فانی + حسابداریِ متابولیکِ spawn | فاز ۲ + TINV-6 فعال | یک کارِ breadth-first (lead-gen ِ چند-منبعی) با ≥۲ sub-leg موازی، بدونِ نقضِ TINV-2/3 |
| **۴** | H-4: دکترِ trace-grader ِ لنگردار (ادغامِ Anchor Ledger) | فاز ۳ + eval harness | ≥۱ اصلاحِ پیشنهادیِ دکتر که با قضاوتِ انسانی settle و اعمال شده، با بهبودِ قابلِ‌اندازه‌گیری در eval |
| **۵ (معلق)** | H-5: A2A/MCP ِ رسمی در مرز | نیازِ واقعیِ بیرونی | — |

**شاخصِ موفقیتِ کل:** (۱) هیچ اثرِ برگشت‌ناپذیری بدونِ LANGAR settle نشده (audit صفر-نقض)؛ (۲) throughput ِ کارِ breadth-first ≥۲× نسبت به ۶ پای ثابت؛ (۳) هر چرخه‌ی خود-اصلاحی traceable به یک قضاوتِ انسانیِ مشخص.

---

## ۶. سؤالِ باز (فقط یکی، واقعاً blocking)
**سیاستِ stasis:** وقتی human-append نیست (سفر/بیماری)، sub-legها و job ِ استخراجِ حافظه هم باید freeze شوند یا فقط اثرهای برگشت‌ناپذیر gate بمانند و شناختِ داخلی ادامه یابد؟ گزینه‌ی دوم عملیاتی‌تر است اما یعنی «رؤیادیدن در کما» — باید تصمیمِ canon بگیری، چون بر تعریفِ stasis در Fusion World هم اثر می‌گذارد.

---

## منابع (وضعیتِ ۲۰۲۶)
- anthropic.com/engineering/multi-agent-research-system
- openai.com/index/introducing-agentkit · openai.com/index/the-next-evolution-of-the-agents-sdk
- rapidclaw.dev/blog/a2a-protocol-complete-guide-2026 (A2A v1.x، Linux Foundation)
- alicelabs.ai/en/insights/best-ai-agent-frameworks-2026 (Microsoft Agent Framework 1.0)
- docs.aws.amazon.com/bedrock-agentcore (Runtime/Memory/recommendations)
- morphllm.com/ai-agent-framework (LangGraph checkpointing/time-travel)
