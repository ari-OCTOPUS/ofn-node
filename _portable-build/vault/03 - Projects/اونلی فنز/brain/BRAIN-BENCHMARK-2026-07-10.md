---
type: benchmark
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: complete (learning layer strengthened + verified)
created: 2026-07-10
created_by: agent (Claude Fable 5)
relates_to: "brain/ (project_f_brain, acquisition, ab_tracker, dual_brain_v3, learning) · [[PROJECT-F-BRAIN-SPEC]] · [[langar/LANGAR-SPEC]]"
tags: [project-f, brain, multi-agent, benchmark, learning, bandit]
aliases: ["Brain Benchmark", "بنچمارک مغز"]
---

# مغزِ Project-F — راستی‌آزمایی یادگیری + بنچمارک با معماری رقبا (2026-07-10)

> دو سؤال: (۱) آیا مغزِ یادگیرندهٔ مستقل واقعاً کار می‌کند؟ (۲) در برابر معماریِ شرکت‌های مولتی‌ایجنتِ ۲۰۲۶ کجا ایستاده و چطور قوی‌تر شد؟

## §۱ — آیا کار می‌کند؟ (تستِ تجربی، نه ادعا)
| مؤلفه | فایل | نتیجهٔ تست |
|---|---|---|
| مغزِ یادگیرندهٔ جذب | `acquisition.py` | ✅ رتبهٔ tag را از دادهٔ واقعی یاد می‌گیرد (nylon>oil)، بهترین روز را یاد می‌گیرد (Saturday)، و **از restart جان‌به‌در می‌برد** — تست تجربی سبز |
| A/B tracker آماری | `ab_tracker.py` | ✅ برنده را با آستانهٔ significance تشخیص می‌دهد |
| ۷ زیرعامل + دو Guard | `project_f_brain.py` | ✅ Compliance/Ethics-Guard قواعد را drop می‌کنند؛ route‌ی tiered (قیمت→آری) کار می‌کند؛ archive persist می‌شود |
| control-plane | `dual_brain_v3.py` / `orchestrator.py` | ✅ import و اجرا؛ `think_and_communicate` خروجی می‌دهد |
| **لایهٔ یادگیریِ قوی (جدید)** | `learning.py` | ✅ ۱۰/۱۰ تست + eval: Thompson از greedy **۴۹٪ بهتر (ایستا)** و **۳۳٪ بهتر (شیفتِ ترند)** روی میانگینِ ۴۰ seed |

**نتیجه:** بله کار می‌کند. اما یک ضعفِ جدی داشت (پایین) که رفع شد.

## §۲ — بنچمارک با معماریِ رقبا (۲۰۲۶)
منابع: Anthropic multi-agent research system · OpenAI Agents SDK · LangGraph · CrewAI/AutoGen · ادبیاتِ contextual bandit/Reflexion/DGM. `[FACT — منابع در §۶]`

| بُعدِ معماری | الگویِ قویِ رقبا `[FACT]` | مغزِ Project-F (قبل) | بعد از تقویت |
|---|---|---|---|
| **Orchestrator-worker** | lead + subagentهای موازی با قراردادِ صریح (Anthropic) | ✅ control-plane + ۷ زیرعامل با نقشِ شفاف | ✅ (بدون تغییر) |
| **Guardrails موازی/fail-fast** | validatorها قبل از generation، tripwire (OpenAI) | ✅ Compliance+Ethics-Guard قبل از route | ✅ |
| **HITL به‌صورت interrupt** | auto برای روتین، escalate فقط high-risk (~95/5) | ✅ tiered: low→صبا، high(قیمت/انتشار)→آری | ✅ |
| **Memory تفکیک‌شده** | short/long/entity/episodic جدا (CrewAI/LangGraph Store) | ⚠️ تخت: archive.json + acquisition_memory | ✅ recency-weighted posterior (episodic-مانند) اضافه شد |
| **Durable execution / persistence** | checkpoint هر گام، resume (LangGraph) | ✅ همهٔ stateها JSON persist (restart-safe) | ✅ |
| **اکتشاف (exploration)** | **contextual bandit: Thompson/UCB؛ pure-greedy = باگ** | ❌ **greedy خام** (میانگین؛ روی برندهٔ نویزی قفل) | ✅ **ThompsonBandit + UCB1 + فلورِ اکتشاف + min-pull** |
| **سازگاری با non-stationarity** | recency/decay (ترندِ متغیر) | ❌ همهٔ دادهٔ قدیم وزنِ برابر | ✅ recency نیمه‌عمرِ ۲۱ روزه |
| **Archive of what worked** | DGM/MAP-Elites: نگه‌داریِ برنده‌ها + context | ⚠️ archive بود ولی pricer از آن **نمی‌خواند** | ✅ LearningBridge دادهٔ واقعی → سیاستِ اکتشاف را تغذیه می‌کند |
| **Approval-gated learning** | reflection/قاعده = proposal تا تأیید (ضدِّ self-reinforcing error) | ✅ فقط از نتایجِ ثبت‌شده | ✅ `approved` flag صریح؛ دادهٔ رد‌شده وارد نمی‌شود |
| **Eval harness (offline)** | ~۲۰ کیس، LLM-judge، regression | ❌ نبود | ✅ `regret_eval_avg`: Thompson vs greedy روی seedها |
| **Transparency/observability** | trace هر call (Langfuse-class) | ⚠️ لاگِ محدود | ✅ `explain()`: mean/pulls/uncertainty/explore_rate هر arm |
| **Cost cap + kill-switch** | budget + halt خودکار | ✅ ۲٪-cap (brain) + سقفِ AUD 15 (لنگر) + kill | ✅ |
| **λ_persist<0 (ضدِّ engagement-at-any-cost)** | — (خاصِّ ما، فراتر از رقبا) | ✅ Ethics-Guard | ✅ (بندیت فقط ساعتِ تولیدِ سبک‌های compliant را تخصیص می‌دهد، نه دستکاریِ فن) |

**جمع‌بندی:** مغز از نظرِ orchestration/HITL/governance **هم‌ترازِ الگوهای قوی** بود، ولی **ضعفِ کلیدی = نبودِ اکتشاف** (مهم‌ترین تفاوتِ سیستمِ قوی با toy طبق هر سه منبعِ اصلی). این رفع شد.

## §۳ — ضعف‌هایی که پیدا و رفع شد
1. **greedy خام (بزرگ‌ترین):** `acquisition.analyze()` با میانگین رتبه می‌داد → روی برندهٔ نویزیِ اولیه قفل می‌شد و ترندِ جدید را نمی‌گرفت. **رفع:** `ThompsonBandit` (نمونه‌گیریِ posterior = اکتشافِ خودکارِ armهای کم‌داده) + `UCB1` قطعی. eval نشان داد greedy در ~۲۵٪ اجراها فاجعه‌بار قفل می‌شود (regret تا ۹۰–۱۰۵)، Thompson مهارشده (۳۷–۶۶).
2. **اشباعِ امتیاز:** `min(1, ...)` قدیمی برندگانِ قوی را به ۱٫۰ می‌چسباند و تفکیک را می‌کشت. **رفع:** `tanh` هموار و بی‌اشباع.
3. **بی‌حافظگیِ زمانی:** دادهٔ ۶۰روزه‌ی قدیمی وزنِ دادهٔ امروز. **رفع:** recency نیمه‌عمرِ ۲۱روزه (= پنجرهٔ آزمایشِ M3).
4. **آرشیوِ بی‌استفاده:** archive برنده‌ها را ذخیره می‌کرد ولی سیاست از آن نمی‌خواند. **رفع:** `LearningBridge` دادهٔ واقعیِ `AcquisitionMemory` را به سیاستِ اکتشاف وصل می‌کند (بدونِ کانِن دوم).
5. **نبودِ eval:** هیچ سنجهٔ کیفیتِ یادگیری نبود. **رفع:** `regret_eval_avg` (regret روی چند seed) — چیزی که سیستمِ قوی دارد و toy ندارد.

## §۴ — گاردریل‌های بندیت (governance، تا «قوی» به «رادیکال» تبدیل نشود)
- **مرزِ اخلاقی:** بندیت فقط بینِ سبک‌های محتواییِ **ازقبل-compliant** ساعتِ کمیابِ تولید را تخصیص می‌دهد؛ **هرگز چیزی رو به فن دستکاری نمی‌کند** (پاداش = عملکردِ پستِ عمومی، نه engagement-at-any-cost → سازگار با λ_persist<0 و Ethics-Guard).
- **فلور/سقفِ اکتشاف** hard-coded (۵٪–۴۰٪) → هرگز رفتارِ رادیکال یا کاملاً تصادفی نمی‌گیرد.
- **min-pull=۳** پیش از قضاوت → با نظمِ نمونهٔ کوچکِ round2 §۶.۲ (پنجرهٔ ≥۲هفته، یک متغیر) هم‌راستا؛ بندیت **weekly allocator** است نه per-post switcher.
- **propose-only:** خروجیِ بندیت پیشنهاد است؛ تصمیم با آری (دوکلیده).
- **approval-gated:** فقط دادهٔ تأییدشده وارد یادگیری.
- **transparency:** `explain()` برای هر تصمیم mean/uncertainty/explore_rate می‌دهد (responsible-AI سه‌ستونی).

## §۵ — آنچه هنوز gap است (صادقانه)
- **LLM-as-judge eval** نداریم (رقبا دارند)؛ eval فعلی synthetic-regret است. `[OPEN]` — بعد از دادهٔ واقعی + verdict V3 (فعال‌سازی LLM).
- **contextual** واقعی نیست: بندیت فعلی per-arm است، نه با feature-vectorِ زمینه (LinUCB کامل). برای مقیاسِ فعلی (چند tag) کافی است؛ ارتقا به LinUCB بعد از حجمِ داده. `[OPINION]`
- **pricer** هنوز از بندیت استفاده نمی‌کند (فقط tag-selection). گام بعدی: اتصالِ Pricer به همین سیاست پس از verdict قیمت (#۱۰). `[OPEN]`
- integration به‌صورت opt-in است؛ اتصالِ خودکار به `plan_week` نیاز به یک ویرایشِ کوچکِ `acquisition.py` دارد که عمداً پشتِ تصمیم گذاشته شد تا تست‌های موجود نشکند.

## §۶ — Sources
Anthropic «Building a multi-agent research system» (anthropic.com/engineering) · OpenAI Agents SDK docs (openai.github.io/openai-agents-python) · LangGraph persistence/HITL (docs.langchain.com) · CrewAI process types · contextual bandits (arXiv 2505.16918؛ Thompson/UCB) · Reflexion (episodic self-critique) · Darwin-Gödel Machine (arXiv 2505.22954) · HITL escalation design 2026. جزئیات و URLها: بنچمارکِ تحقیقاتیِ این راند (subagent research).

---
*همهٔ کد propose-only و ایزوله در پوشهٔ Project-F؛ هیچ اکشن بیرونی؛ اجرا پشتِ GATE 0. تست‌ها $0 و آفلاین.*
