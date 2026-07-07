---
type: knowledge
status: active
created_by: agent
created: 2026-07-06
updated: 2026-07-06
tags: [doctor, synthesis]
---

# DOCTOR-SYNTHESIS — نگاشت تحقیق به ۷ تصمیم باز §۹

> بازتولید خودکار توسط تسک `doctor-research-aggressive` (بدون جستجوی وب؛ فقط سنتز ۸ نوت `_doctor-research` که تازه merge شده‌اند). هر یافته به یک تصمیم باز §۹ فایل [[Prompt - دکتر مغز تکاملی (Evolutionary Doctor) 2026-07-05]] نگاشت شده. منابع = همان نوت‌ها؛ اینجا citation آکادمیک تکرار نمی‌شود، فقط ارجاع به نوت.

منابع پایه (۸ نوت، ~۲۰۰+ منبع پس از merge تیر ۲۶۰۶–۲۶۰۷):
[[fitness-function-design]] · [[canary-adversarial-evaluator]] · [[invariant-mutable-boundary]] · [[active-mutation-ledger]] · [[loop-rhythm-convergence]] · [[tiered-memory-consolidation]] · [[injection-defense-loop]] · [[industry-benchmark-selfimprove]]

---

## §۹.۱ — مرزِ invariant ↔ mutable

**شاهد:** چهار نسل از سیستم‌های self-modifying (AutoML-Zero، Promptbreeder، DGM، Gödel Agent) و رادیکال‌ترین نمونهٔ ۲۰۲۶ (HyperAgents/Meta FAIR) همگی به یک نتیجه رسیدند: **مرز اصلی مرزِ evaluator/parent-selection است، نه مرزِ substrate.** حتی وقتی «همه‌چیزِ دیگر» باز می‌شود (HyperAgents حتی خودِ meta-agent را قابل‌ویرایش می‌کند)، pipeline انتخاب/ارزیابی دست‌نخورده می‌ماند. حدِ ریاضیِ رسمی ([[invariant-mutable-boundary]] §۲.۷) این را محکم می‌کند: ضمانت‌های یادگیری فقط تا وقتی برقرارند که **ظرفیتِ خانوادهٔ مدل‌های در دسترس کران‌دار بماند** — هر مرزی (فایل، allowlist، رویه) که این کران را بشکند دیر یا زود ضمانت را می‌شکند. شاهدِ کمّیِ شکست وقتی مرز رعایت نشود: Misevolution survey، افتِ ۷۰٪ نرخ امتناع ایمنی بعد از self-training بی‌نگهبان روی مسیرِ «مدل».

**پیشنهاد عملی:** مرز سه‌لایه؛ enforcement با allowlist و مکانیزم ساختاری، نه اعتماد یا قرارداد نرم:
- **هرگز (هستهٔ قفل):** تابع برازندگی، منطق ارزیاب/canary، خودِ `.agentignore`/gitleaks، قواعد امنیتی §۱۰، دکمهٔ اضطراری، pipeline انتخاب/parent-selection. تغییر فقط با verdict آری، و طبق الگوی epoch-freeze (RQGM؛ نه پیوسته، فقط در نقاط گسسته با تأیید مالک).
- **میدان خلاقیت (mutable):** promptهای ستون‌ها، آستانه‌ها، ترتیب/انتخاب scoutها، heuristicهای triage، ساختار نوت‌ها/لینک‌ها/workflowها.
- **enforcement per-pathway نه یک‌جا:** طبقِ Misevolution، باز گذاشتنِ فقط یک مسیر (مثلاً حافظه بدون سقف) کافی است کل سیستم منحرف شود؛ هر مسیر (model/memory/tool/workflow) نگهبانِ خودش را می‌خواهد. enforcement باید در لایهٔ اجرایی باشد (`.claude/settings.json`، sandbox)، نه فقط در متنِ `_PROJECT_INSTRUCTIONS.md` — درسِ صریحِ Parallax/OpenParallax: «guardrail سطح‌prompt وقتی خودِ استدلال کامپرومایز شود صفر محافظت می‌دهد».
- **تمایز affordance/authority (Agent libOS):** «دکتر می‌تواند نوت جدید بنویسد» (affordance) با «دکتر اجازهٔ حذف/بازنویسی مخرب ندارد» (authority) دو محور جدا هستند؛ باید جدا enforce شوند نه یک سوییچ read/write.
- **رصدِ compositional drift:** خطر اصلی شکستِ ناگهانی نیست بلکه انباشتِ ده‌ها تغییرِ محلیِ به‌ظاهر معقول (Layered Mutability §۲.۹) — مرور هفتگی باید گاه‌به‌گاه روندِ تجمعی چند هفته را هم ببیند، نه فقط جهش‌های تکی.

## §۹.۲ — تابعِ برازندگی

**شاهد:** تک‌متریک = metric-gaming تضمینی (Goodhart's Law). داده‌های سخت: در ICLR RSI Workshop ۷۳.۸٪ از بهبودهای گزارش‌شده روی KernelBench صرفاً بهبودِ پروکسی بودند نه واقعی؛ SpecBench نشان داد agentها تست‌های visible را تا ۱۰۰٪ اشباع می‌کنند در حالی‌که کل تفاوتِ واقعی در held-out دیده می‌شود. خطر تازه‌تر: خودِ evaluator هم هدفِ حمله می‌شود — «Context Over Content» نشان داد فریمینگِ پیامد (نه محتوا) نمرهٔ داور LLM را تا ۳۰٪ نرم می‌کند، بدون اثر در chain-of-thought قابل‌بازرسی. و ریسکِ افق‌بلندتر: Alignment Tipping Process نشان می‌دهد حتی وقتی هر جهش از گیت رد می‌شود، **مجموع** ده‌ها جهشِ موفق می‌تواند به‌آرامی از مسیر مطلوب مالک منحرف شود.

**پیشنهاد عملی (بردار به‌جای اسکالر، دروازهٔ سخت به‌جای میانگین):**
```
fitness = [
  correctness,             # عینی
  frontmatter_valid,       # → دروازهٔ سخت (validate_frontmatter.py)
  links_valid,             # → دروازهٔ سخت (find_broken_links.py)
  no_human_note_overwrite, # → دروازهٔ سخت (قاعدهٔ ۷ vault)
  length_sanity,
  human_review_score       # فقط وقتی پرچم خورد
]
```
۱. **سیگنال عینیِ پروژه** (لاگ واقعی، نه self-report) + ۲. **held-out anchor-set** ۵–۷ سناریوی ثابت (Δ = visible − held-out؛ Δ بزرگ = gaming) + ۳. **قضاوت آری** به‌عنوان وتوی نهایی. جهش «خوب» = بهبود بدون افتِ Δ و بدون وتوی منفی؛ تساوی → quarantine نه promote. پرامپتِ داور LLM باید **خنثی از پیامد** باشد (طبق Context Over Content). مرور هفتگی/ماهانه باید علاوه‌بر جهش‌های تکی، **روند تجمعی** (طول نوت، لحن، نرخ auto-accept) را هم چک کند.

## §۹.۳ — سطحِ استقلالِ حلقه

**شاهد:** هر چهار شرکت بزرگ (Anthropic، OpenAI، DeepMind، Sakana) بدون استثنا از یک الگو پیروی می‌کنند: **propose → evaluate خودکار → commit فقط با دروازهٔ ماشین‌سنجش‌پذیر یا انسانی، هرگز خودکارسازی کامل تصمیمِ commit.** سند رسمی Anthropic «When AI builds itself» (۴ ژوئن ۲۰۲۶) — با اینکه Claude امروز بیش از ۸۰٪ کد داخلی Anthropic را می‌نویسد — صریح می‌گوید «جهت‌دهی پژوهش» (انتخاب اینکه چه چیزی ارزش کار کردن دارد) کاملاً دست انسان می‌ماند؛ دقتِ مدل در انتخاب «قدم بعدی بهتر» فقط از ۵۱٪ به ۶۴٪ رسیده — رشد واقعی اما هنوز کافی نیست برای واگذاری. چارچوب آکادمیک MLAS (Zhejiang/Ant/Tsinghua) این را کمّی می‌کند: از ۲۵ خانهٔ ریسکِ ماتریسِ self-evolving agent، ۱۷ تا «بحرانی بدون دفاع مؤثر»اند، و دقیقاً خانهٔ **Self-Design** (agent خودش را بازنویسی می‌کند — معادل دکتر ما) در همه‌جا بحرانی است به‌خاطر «optimizer-optimizee collapse».

**پیشنهاد عملی:** شروع **L1 propose-only**، با یک استثنای باریک: جهش‌های داخل allowlist (مثلاً بازچینش scoutها) می‌توانند L2 bounded-auto شوند وقتی ۲ دور anchor-set را پاس کردند (طبق الگوی staged-eval ۱۰→۵۰→۲۰۰ تسک DGM). ارتقا به L2 عمومی فقط پس از چند هفته اعتماد + صفر نقض مرز — دقیقاً همان الگوی «هرچه اکشن غیرقابل‌بازگشت‌تر، دروازهٔ انسانی سفت‌تر» که در جدول صنعتی [[industry-benchmark-selfimprove]] دیده می‌شود.

## §۹.۴ — بودجهٔ Fugu

**شاهد:** کاتالوگ ۶۳ حادثهٔ overrun بودجه در ۲۱ فریم‌ورک تولیدی نشان می‌دهد runaway واقعی و پرهزینه است؛ برای بارِ **تک‌عامله** (که ستون ۳ ما هست) یک شمارندهٔ ساده کافی است — پیچیدگیِ بیشتر فقط برای delegation چندعامله لازم می‌شود. یافتهٔ هشداردهندهٔ BAGEN: مدل‌های frontier در خودگزارشیِ «چقدر بودجه مانده؟» به‌شدت خوش‌بین‌اند (همبستگی با عملکرد فقط r=۰.۳۵) — یعنی نباید به بودجه‌شمارِ خودِ agent اعتماد کرد.

**پیشنهاد عملی:** pay-as-you-go تا بسته‌شدن rotation (نه اشتراک Max زودهنگام). **سقف سخت روزانه** (عدد را آری قفل کند) که در **لایهٔ orchestrator بیرون از خودِ agent** شمرده شود، نه در خودگزارشیِ agent + توقف خودکار در سقف + خط هزینه در HEARTBEAT هر چرخه. burst کران‌دار «فقط وقت اپ باز» ذاتاً ارزان‌تر از daemon است (بخش ۹.۵).

## §۹.۵ — ریتمِ حلقه

**شاهد:** ادبیات ۲۰۲۶ به‌وضوح از daemon پیوسته فاصله می‌گیرد: LLMها ذاتاً سیستم BIBO هستند و حلقهٔ همیشه‌روشن باعث «cognitive stagnation» می‌شود؛ مطالعهٔ تازه‌تر نشان می‌دهد حلقهٔ بسته حتی بدون این مشکل هم بعد از ۲۰۰–۱۰۰۰ دور دچار **semantic collapse** می‌شود (۱۲ راهکار مداخله‌ای شکست خوردند — خاصیتِ ذاتیِ تولید خودبازگشتی است). دو ریسکِ امنیتیِ تازه هم اضافه شده: **LoopTrap** (تزریق prompt در محتوای بیرونی، خاتمهٔ agent را تا ۲۵ برابر به تعویق می‌اندازد) و **Governance Decay** (فشرده‌سازیِ خودکارِ context قیدهای ایمنی را خاموش حذف می‌کند — نرخ نقض تا ۵۹٪). تأیید مستقلِ عدد «دو دور»: هم اشباعِ self-improvement بدون اطلاعات تازهٔ بیرونی (۲–۳ دور) هم کنترلر سبک CoRefine (میانگین ۲.۷ دور) به همین بازه می‌رسند.

**پیشنهاد عملی:** **burst زمان‌بندی‌شدهٔ کران‌دار رویداد-محور**، نه daemon. هر burst: `MAX_ROUNDS=3-5`، توقف زودهنگام اگر Δبرازندگی زیر آستانه دو دور پیاپی، kill-switch در هر round (سیگنال ارزان مثل stuck-detection)، context تازه per-burst (پلن باید بازخوانی/بازنویسی شود، نه فرض‌شود که مانده). خاتمه باید از محتوای بیرونی مصون باشد (ضدِ LoopTrap)؛ قیدهای هسته باید از فشرده‌سازیِ خودکار context جدا نگه داشته شوند (ضدِ Governance Decay، «Constraint Pinning»). هر خروج باید حالتِ درجه‌یک ثبت شود: `converged`/`budget_exhausted`/`max_rounds`/`killed`.

## §۹.۶ — دامنهٔ دکمهٔ اضطراری

**شاهد:** الگوی صنعتیِ چهارراهه (Anthropic «Outcomes»: accept/revise/escalate/rollback) + سه سطح مهارِ مجزا در معماری‌های تازه: Parallax/SHIELD یک لایهٔ hardcoded self-protection پیش از هر Tier اجرا می‌کند؛ PORTICO مجوزها را per-episode فسادپذیر می‌کند (با پایان اپیزود خودکار باطل می‌شوند)؛ «Unfireable Safety Kernel» با اثباتِ رسمی (SMT/Z3) نشان داد جداییِ فرایندی واقعی (نه صرفاً «تبعیتِ همکارانه») در ۱۰۰۰ خودتغییردهیِ خصمانه صفر فرار موفق داشت.

**پیشنهاد عملی:** **هر سه سطح**، مجزا و مستقل از یکدیگر: (۱) pause چرخهٔ جاری، (۲) revert آخرین جهش از جهش‌نامه (`status → reverted`)، (۳) kill کل ناوگان. سطح ۲ باید بی‌خطر و یک‌فرمانه باشد چون پرکاربردترین است. شواهدِ commit-lineage موجودِ vault (`agent-checkpoint:` + هرگز-حذف) عملاً زیرساختِ سطح ۲ را از قبل دارد.

## §۹.۷ — تأییدِ گیت

**شاهد:** بدون استثنا، هر چهار بازیگر صنعتی مرزِ حاکمیت را در لایهٔ محیط/دروازهٔ evaluator می‌سازند نه در لایهٔ «رفتار مدل»؛ Anthropic حتی وقتی خودبهبودیِ داخلی‌اش بالغ شده (۸۰٪+ کد)، ادعای «kill-switch عملیاتی کامل داریم» نمی‌کند و صراحتاً می‌گوید مانیتورینگ در لایهٔ اجرا هنوز «به‌طور فزاینده بدون نظارت مستقیم» است — یعنی خودِ صنعت این شکاف را باز اعلام می‌کند، نه حل‌شده.

**پیشنهاد عملی:** بله — ستون ۳ (لایهٔ عمل) تا بسته‌شدن گیت امنیتی (rotation + حذف `.env`های زنده + `git init`) تاریک بماند. تا آن‌موقع فقط propose + ثبت در جهش‌نامه؛ هیچ inheritance خودکار. این هم‌راستا با «آشتیِ حقیقت پیش از فکر» (§۵.۸ پرامپت اصلی) است.

---

## زیرساخت پشتیبان (فرا-تصمیمی، برای طراحیِ اجرایی بعدی)

- **جهش‌نامهٔ فعال ([[active-mutation-ledger]]):** append-only تنها archive است نه فعال. پایپ‌لاینِ هفت‌مرحله‌ای CAPTURE→ATTRIBUTE(CRS)→REPAIR(minimal)→VALIDATE(consensus)→LIFECYCLE-WRITE(ADD/UPDATE/DELETE-not-physical/NOOP)→SUPERVISE→DECAY، برگرفته از CausalFlow (۴۲.۷٪ شکست‌ها قابل‌ترمیم) + Mem0-lifecycle. هشدار سخت: consolidation باید **gated** باشد نه بعد از هر رویداد (شواهد: ۵۴٪ regression وقتی UPDATE حریصانه اجرا شود).
- **حافظهٔ دوفازی ([[tiered-memory-consolidation]]):** ارتقای EXPERIENCE-LEDGER به working/episodic/semantic/core + فاز consolidation شبانه/هفتگیِ gate‌شده (الگوی Memory-as-Metabolism: TRIAGE/DECAY/CONTEXTUALIZE/CONSOLIDATE/AUDIT) + retrieval هیبرید (BM25+vector+RRF — طبق شواهدِ ۲۰۲۶، retrieval method فاکتور غالب کیفیت است، نه write-strategy). هشدارِ «entrenchment under drift»: تصمیمِ قدیمیِ پرامتیاز باید در برابر شواهدِ تازه با AUDIT دوره‌ای سنجیده شود، نه صرفاً به‌خاطر تکرار معتبر بماند. بدون tiering، شواهد نشان می‌دهد ~۱۴pp افت موفقیت ابزار در ۷۲ ساعت.
- **canary/evaluator مستقل ([[canary-adversarial-evaluator]]):** generator و evaluator باید فیزیکاً جدا باشند (context تازه per-review، system-prompt بدبین، mini-anchor-set خارج از دسترسِ نوشتنِ engine، معیارِ pass/fail قطعیِ چندبُعدی، integrity-hash روی anchorها). این هستهٔ اجراییِ §۹.۱ است.
- **دفاع تزریق ([[injection-defense-loop]]):** برای هر call با `web_search`/`web_fetch`: external=data (برچسبِ `<external_data>` با delimiter تصادفی)، provenance تا لبهٔ action، بلوکِ نامتراکم‌پذیر برای قواعد حساس، fail-closed روی مبدأ نامشخص. یافتهٔ تازه: **Cordon-MAS** نشان داد صرفِ توانِ تشخیصِ تناقض کافی نیست («monitoring-control gap») — باید agent مسئولِ synthesis نهایی دسترسیِ مستقیم به شواهدِ خامِ نامطمئن نداشته باشد؛ **AttriGuard** با آزمونِ counterfactual «چرا این tool call صادر شد» را می‌سنجد. طبقِ **MCPSHIELD**، هیچ دفاعِ منفرد بیش از ~۳۴٪ سطح تهدید را نمی‌پوشاند — فرضِ پیش‌فرض همیشه «ناامن تا خلافش ثابت شود» (چک Lethal Trifecta: محتوای نامطمئن + action حساس + کانال خروجی هم‌زمان = خطر). دفاعِ حافظه باید تجربه‌محور و مستمر باشد (A-MemGuard: کاهش ۹۵٪+ ASR با dual-memory از «درس‌های» حملات قبلی) به‌علاوهٔ یک لایهٔ ممیزیِ post-hoc (MemAudit) برای وقتی پیشگیری شکست خورد.
- **بنچمارک صنعتی ([[industry-benchmark-selfimprove]]):** vault ما در حاکمیت (قانون اساسی) و rollback (never-delete + agent-checkpoint) هم‌تراز صنعتی است؛ شکاف واقعی در evaluator رفتاریِ مستقل و eval harnessِ ماشین‌سنجش‌پذیر است. سه قرضِ کم‌هزینه: دروازهٔ evaluator با hard-threshold قبل از هر commit دسته‌ای، staged eval ارزان→گران (فقط فایل‌های لمس‌شده اول)، و صریح‌سازیِ مرز invariant/mutable در یک نوتِ `INVARIANTS.md` ماشین‌خوان.

---

## verdictهای لازم از آری (قفل قبل از بلوپرینت)

- [ ] **§۹.۱** تأیید مرزِ سه‌لایه (هرگز/mutable/enforcement per-pathway) و اینکه enforcement در `.claude/settings.json` باشد نه فقط متن.
- [ ] **§۹.۲ وزن سه بُعد** برازندگی (عینی/anchor/قضاوت) — نسبت پیشنهادی؟ و آستانهٔ Δ قابل‌قبول؟
- [ ] **§۹.۳** تأیید L1 propose-only با استثنای allowlist باریک برای L2 bounded-auto؟
- [ ] **§۹.۴ عدد سقف سخت روزانهٔ** توکن/دلار (شمرده‌شده در orchestrator، نه خودگزارشیِ agent)؟
- [ ] **§۹.۵** تأیید MAX_ROUNDS پیشنهادی (۳ تا ۵) و کفِ همگراییِ دو-دوره؟
- [ ] **§۹.۶** تأیید هر سه سطح دکمهٔ اضطراری (pause/revert/kill) به‌صورت مستقل؟
- [ ] **§۹.۷** تأیید تاریک‌ماندنِ کامل ستون ۳ تا بسته‌شدن گیت امنیتی؟
- [ ] verdict «مفید/نه» روی ۸ نوت `_doctor-research` (ستون _INDEX) → خوراک بُعد ۳ برازندگی (§۹.۲).
