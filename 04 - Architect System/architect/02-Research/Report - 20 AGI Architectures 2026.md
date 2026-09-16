---
type: report
created: 2026-07-03
prompt: "[[04 - Architect System/architect/02-Research/Prompt - AGI Architectures Research 2026|Prompt - AGI Architectures Research 2026]]"
method: deep-research (۵ ایجنت جستجوی موازی + ۲ ایجنت راستی‌آزمایی خصمانه)
verification: "۱۶ ادعای پرریسک چک شد — ۱۵ تأیید، ۱ رد (حذف شد)"
status: done
destination: "07 - Knowledge"
updated: 2026-07-04
---

# ۲۰ معماری نوآورانه AGI — وضعیت ژوئیه ۲۰۲۶

## ۱. خلاصه اجرایی

در ۲۰۲۶، ترکیب reasoning models (استدلال با test-time compute) و معماری sparse از نوع Mixture-of-Experts ساختار غالب مدل‌های frontier است. جبهه دوم AGI به‌سرعت به سمت world models چرخیده — خروج Yann LeCun از Meta و seed یک‌میلیارد دلاری AMI Labs، عرضه عمومی Genie 3 و محصولات World Labs و NVIDIA Cosmos نشانه‌های آن‌اند. ایجنت‌های LLM از الگوهای پژوهشی (ReAct، Reflexion) به فریم‌ورک‌های production (Microsoft Agent Framework، LangGraph) و لایه‌های حافظه تجاری (Letta، Mem0، Zep) بلوغ یافته‌اند. سیستم‌های خودبهبود و open-ended — Darwin Gödel Machine در ICLR 2026 و AlphaEvolve با استقرار واقعی در زیرساخت Google — از آزمایش فکری به اثر اندازه‌گیری‌شده رسیده‌اند. هم‌زمان مدل‌های VLA (Gemini Robotics، π0.5، Helix 02) تجسد (embodiment) را دوباره به مسیر اصلی AGI برگردانده‌اند، در حالی که معماری‌های شناختی کلاسیک (SOAR، OpenCog Hyperon) نقش نقشه مفهومی و آزمایشگاه ایده را حفظ کرده‌اند.

## ۲. جدول اصلی — ۲۰ معماری

| # | نام | آزمایشگاه/سازنده | سال | خانواده پارادایم | مکانیزم هسته (یک جمله) | وضعیت ۲۰۲۶ |
|---|---|---|---|---|---|---|
| 1 | V-JEPA 2 | Meta AI (FAIR) / تیم LeCun | 2025 | World models | پیش‌بینی self-supervised ویدیو در فضای latent به‌جای پیکسل، با planning رباتیک zero-shot | prototype |
| 2 | Genie 3 / Project Genie | Google DeepMind | 2025 | World models | تولید real-time دنیای سه‌بعدی تعاملی از متن با سازگاری پایدار هنگام کاوش | production (محدود) |
| 3 | Dreamer 4 | Danijar Hafner / DeepMind | 2025 | World models | یادگیری world model از داده آفلاین و آموزش policy درون rolloutهای تخیلی | research |
| 4 | AXIOM | VERSES AI | 2025 | Active inference | ایجنت free-energy با مدل‌های مولد object-centric؛ یادگیری در چند دقیقه با کسری از compute | research |
| 5 | OpenCog Hyperon (PRIMUS/MeTTa) | SingularityNET / Goertzel | 2024 | Neurosymbolic | metagraph خودتغییرده (AtomSpace) + زبان MeTTa + مدل شناختی PRIMUS | prototype |
| 6 | AlphaProof / AlphaGeometry | Google DeepMind | 2024 | Neurosymbolic | جفت‌کردن LLM با موتور استنتاج نمادین و RL از نوع AlphaZero در Lean | research |
| 7 | SOAR | John Laird / U. Michigan | 1983 | Cognitive architecture | قواعد production + حافظه‌های چندگانه (semantic/episodic/procedural) + RL | research |
| 8 | ReAct | Yao et al. / Princeton+Google | 2022 | LLM-agent pattern | حلقه think→act→observe؛ ادغام chain-of-thought با ابزار | production |
| 9 | CoALA | Sumers, Yao et al. / Princeton | 2023 | LLM-agent pattern | چارچوب مفهومی: تکسونومی حافظه + فضای action + حلقه تصمیم | research |
| 10 | MemGPT → Letta | Packer et al. / UC Berkeley | 2023 | Memory-centric | مدیریت مجازی context به سبک OS paging؛ ایجنت حافظه خودش را ویرایش می‌کند | production |
| 11 | Generative Agents | Park et al. / Stanford | 2023 | Memory-centric | memory stream + retrieval + reflection + planning برای رفتار اجتماعی نوظهور | research |
| 12 | AutoGen → MS Agent Framework | Microsoft | 2023→2026 | Multi-agent | ارکستریشن گفت‌وگویی چندایجنته در SDK یکپارچه با A2A و MCP | production |
| 13 | MetaGPT → Atoms | DeepWisdom | 2023→2026 | Multi-agent | نقش‌های ثابت شرکت نرم‌افزاری با SOPهای اجرایی بین ایجنت‌ها | production |
| 14 | Darwin Gödel Machine | Sakana AI + آزمایشگاه Clune | 2025 | Self-improving | ایجنت کدنویس که کد خودش را بازنویسی و با اعتبارسنجی تجربی و آرشیو تکاملی بهبود می‌دهد | research |
| 15 | AlphaEvolve | Google DeepMind | 2025 | Self-improving | حلقه تکاملی روی کد تولیدی Gemini با ارزیاب‌های خودکار برای کشف الگوریتم | production |
| 16 | AI Scientist-v2 | Sakana AI | 2025 | Self-improving | خط لوله agentic tree search: ایده → آزمایش → مقاله → خودبازبینی | prototype |
| 17 | Reasoning models (test-time compute) | OpenAI پیشگام؛ صنعت‌گستر | 2024→ | Frontier scaling | chain-of-thought آموزش‌دیده با RL + مقیاس‌پذیری compute در زمان استنتاج | production |
| 18 | Mixture-of-Experts (MoE) | صنعت‌گستر (DeepSeek، Google، Qwen) | 2021→ | Frontier scaling | فعال‌سازی گزینشی expertها به‌ازای هر توکن؛ جداسازی ظرفیت از هزینه | production |
| 19 | Gemini Robotics (VLA + ER) | Google DeepMind | 2025 | Embodied / VLA | سیستم دوگانه: مدل VLA برای کنترل + مدل ER برای استدلال فضایی و برنامه‌ریزی | production (gated) |
| 20 | π0 / π0.5 | Physical Intelligence | 2024–2025 | Embodied / VLA | ستون VLM + action expert مبتنی بر flow matching با chain-of-thought سلسله‌مراتبی | prototype |

## ۳. پروفایل معماری‌ها

### ۱. V-JEPA 2 — پیش‌بینی در فضای latent

- **سازنده:** Meta AI (FAIR)، تیم Yann LeCun — خانواده JEPA از I-JEPA (2023) تا V-JEPA 2 (ژوئن 2025)
- **مکانیزم اصلی:** معماری joint-embedding predictive که به‌جای بازسازی پیکسل، بازنمایی بخش‌های پنهان/آینده ویدیو را در فضای latent پیش‌بینی می‌کند. روی بیش از ۱ میلیون ساعت ویدیوی اینترنتی pre-train شده و نسخه V-JEPA 2-AC با کمتر از ۶۲ ساعت ویدیوی ربات، برنامه‌ریزی action-conditioned یاد می‌گیرد. planning کاملاً در فضای بازنمایی انجام می‌شود، نه در فضای مشاهده.
- **نوآوری کلیدی:** manipulation رباتیک zero-shot (بازوهای Franka در دو آزمایشگاه دیده‌نشده) بدون reward مخصوص task و بدون جمع‌آوری داده روی ربات.
- **قوت/محدودیت:** درک حرکت قوی (77.3% روی Something-Something v2) و SOTA در پیش‌بینی action؛ اما خود LeCun این مسیر را در Meta کم‌منبع می‌دانست و شرکت را ترک کرد.
- **وضعیت ۲۰۲۶:** [prototype] — مدل 1.2B پارامتری آزاد روی Hugging Face؛ استقرار zero-shot روی ربات واقعی. ادامه مسیر اکنون در AMI Labs خود LeCun دنبال می‌شود.
- **منابع:** [arXiv:2506.09985](https://arxiv.org/abs/2506.09985) · [Meta AI — V-JEPA](https://ai.meta.com/vjepa/) · [AMI Labs](https://www.buildfastwithai.com/blogs/yann-lecun-ami-labs-world-models)

### ۲. Genie 3 / Project Genie — دنیای تعاملی real-time

- **سازنده:** Google DeepMind — پیش‌نمایش پژوهشی اوت 2025، عرضه عمومی ژانویه 2026
- **مکانیزم اصلی:** world model عمومی که از یک prompt متنی، محیط سه‌بعدی قابل کاوش و فوتورئالیستی تولید می‌کند و به‌صورت پیوسته به کنش کاربر پاسخ می‌دهد — برخلاف مولدهای ویدیوی غیرفعال. خروجی 720p با ۲۰–۲۴ فریم بر ثانیه و سازگاری پایدار دنیا در طول کاوش.
- **نوآوری کلیدی:** نخستین world model تعاملی real-time همه‌منظوره؛ DeepMind آن را «پله‌ای به‌سوی AGI» برای آموزش ایجنت‌های عمومی می‌داند.
- **قوت/محدودیت:** تعامل واقعی و سریع؛ اما سشن‌ها کوتاه/محدودند و دسترسی فعلاً gate شده است.
- **وضعیت ۲۰۲۶:** [production — محدود] — لانچ عمومی «Project Genie» در ۲۹ ژانویه 2026 فقط برای مشترکان Google AI Ultra در آمریکا.
- **منابع:** [DeepMind — Genie 3](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/) · [Google Blog — Project Genie](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/project-genie/) · [صفحه مدل Genie](https://deepmind.google/models/genie/)

### ۳. Dreamer 4 — آموزش ایجنت درون تخیل

- **سازنده:** Danijar Hafner و همکاران (وابسته به DeepMind) — DreamerV3 (2023، بعداً در Nature) → Dreamer 4 (سپتامبر 2025)
- **مکانیزم اصلی:** ابتدا یک world model از تجربه یاد می‌گیرد، سپس policy از نوع actor-critic را درون rolloutهای «تخیلی» همان مدل آموزش می‌دهد. Dreamer 4 به آموزش کاملاً آفلاین با world model ترنسفورمری و هدف «shortcut forcing» مهاجرت کرده است.
- **نوآوری کلیدی:** نخستین ایجنتی که task بلندافق «الماس در Minecraft» را صرفاً از دیتاست آفلاین ویدیو-اکشن حل کرد — بدون هیچ تعامل زنده با محیط — و real-time روی یک GPU اجرا می‌شود.
- **قوت/محدودیت:** برنامه‌ریزی بلندافق و بهره‌وری نمونه عالی؛ اما در benchmark های رودررو از رقیب active-inference (مثل AXIOM) در بهره‌وری compute عقب مانده است.
- **وضعیت ۲۰۲۶:** [research] — خط پژوهشی فعال؛ همچنان baseline استاندارد مقایسه در مقالات ۲۰۲۶ (مثل DreamerV3-XP).
- **منابع:** [arXiv:2509.24527](https://arxiv.org/abs/2509.24527) · [GitHub — dreamerv3](https://github.com/danijar/dreamerv3) · [DreamerV3-XP](https://arxiv.org/abs/2510.21418)

### ۴. AXIOM — active inference بهره‌ور

- **سازنده:** VERSES AI — ژوئن 2025 (چارچوب نظری: Karl Friston، free-energy principle)
- **مکانیزم اصلی:** ایجنت active inference که به‌جای جریان پیکسل/توکن، مدل‌های مولد object-centric در حال گسترش می‌سازد؛ ادراک، یادگیری، برنامه‌ریزی و کنش همگی با کمینه‌سازی expected free energy (عدم قطعیت) انجام می‌شوند.
- **نوآوری کلیدی:** یادگیری policy بازی در چند دقیقه از تعامل خام، با چند مرتبه‌بزرگی compute کمتر از deep RL.
- **قوت/محدودیت:** روی Gameworld 10K حدود ۶۰٪ بهتر از DreamerV3 (امتیاز ۷۷ در برابر ۴۸)، حدود ۶ برابر sample-efficient تر، ۳۹ برابر ارزان‌تر و ۴۰۰ برابر کوچک‌تر (0.95M در برابر 420M پارامتر)؛ اما هنوز محدود به محیط‌های بازی‌مانند/object-centric و دموهای اولیه رباتیک.
- **وضعیت ۲۰۲۶:** [research] — از ژوئن 2025 با لایسنس آکادمیک open-source؛ استقرار تجاری تأییدشده ندارد.
- **منابع:** [arXiv:2505.24784](https://arxiv.org/abs/2505.24784) · [VERSES — نتایج Gameworld 10K](https://www.globenewswire.com/news-release/2025/06/02/3091981/0/en/verses-digital-brain-beats-google-s-top-ai-at-gameworld-10k-atari-challenge.html) · [ارزیابی مستقل Soothsayer](https://soothsayeranalytics.com/media/soothsayer-assesses-verses-axiom-model-a-step-forward-in-efficiency-and-learning-in-ai)

### ۵. OpenCog Hyperon (PRIMUS / MeTTa) — بستر شناختی بازتابی

- **سازنده:** SingularityNET / جامعه OpenCog (Ben Goertzel) — نسخه آلفا آوریل 2024
- **مکانیزم اصلی:** یک AtomSpace توزیع‌شده (hypergraph/metagraph) دانش را نگه می‌دارد؛ MeTTa زبان متابرنامه‌نویسی خودتغییرده برای فرایندهای شناختی است؛ و PRIMUS طرح معماری شناختی است که استدلال احتمالاتی (PLN)، یادگیری تکاملی (MOSES) و تخصیص توجه (ECAN) را هماهنگ می‌کند.
- **نوآوری کلیدی:** کامپایلر جدید مبتنی بر MORK (اواخر 2025) اجرای MeTTa را چند مرتبه‌بزرگی سریع‌تر کرده و آن را به سمت قراردادهای هوشمند «ASI Chain» می‌برد.
- **قوت/محدودیت:** یکپارچه‌سازی نظری قوی روش‌های عصبی/نمادین/تکاملی؛ اما نتایج AGI-سطح در دنیای واقعی هنوز اثبات نشده است.
- **وضعیت ۲۰۲۶:** [prototype] — devnet آلفای ASI Chain زنده است و خط لوله کامپایلر MeTTa از دسامبر 2025 عملیاتی است.
- **منابع:** [SingularityNET — Hyperon Progress (دسامبر 2025)](https://singularitynet.io/hyperon-progress-from-prototypes-to-scalable-intelligence/) · [سایت رسمی Hyperon](https://hyperon.opencog.org/) · [ASI:Chain devnet](https://chainwire.org/2025/11/26/asichain-devnet-launches-with-new-infrastructure-for-autonomous-agents/)

### ۶. AlphaProof / AlphaGeometry — ریاضیات neurosymbolic

- **سازنده:** Google DeepMind — دموی مدال نقره IMO در 2024، انتشار Nature در نوامبر 2025
- **مکانیزم اصلی:** AlphaGeometry یک LLM مبتنی بر Gemini را با موتور استنتاج نمادین هندسه جفت می‌کند؛ AlphaProof با ترکیب fine-tuning Gemini و RL به سبک AlphaZero، در زبان formal Lean دنبال اثبات می‌گردد.
- **نوآوری کلیدی:** حل ۴ از ۶ مسئله IMO 2024 (سطح مدال نقره)؛ AlphaGeometry 2 به نرخ حل ۸۴٪ روی مسائل هندسه IMO سال‌های 2000–2024 رسید.
- **قوت/محدودیت:** SOTA در ریاضیات رقابتی formal؛ اما محدود به دامنه‌های قابل formal سازی و نیازمند ترجمه مسئله به Lean.
- **وضعیت ۲۰۲۶:** [research] — کار AlphaProof در Nature منتشر شده («Olympiad-level formal mathematical reasoning with reinforcement learning»).
- **منابع:** [Nature (2025)](https://www.nature.com/articles/s41586-025-09833-y) · [AlphaGeometry2 — arXiv](https://arxiv.org/pdf/2502.03544) · [DeepMind — AI for Math](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/ai-for-math/)

### ۷. SOAR — معماری شناختی کلاسیکِ هنوز زنده

- **سازنده:** John Laird و همکاران، دانشگاه میشیگان — از 1983
- **مکانیزم اصلی:** سیستم قواعد production که اجرای واکنشی، برنامه‌ریزی سلسله‌مراتبی و چند حافظه بلندمدت (semantic، episodic، procedural) به‌علاوه reinforcement learning را یکپارچه می‌کند. افزونه‌های اخیر مدل‌سازی هیجان مبتنی بر appraisal و ادغام عمیق‌تر نمادین/غیرنمادین را اضافه کرده‌اند.
- **نوآوری کلیدی:** الگوی مرجع چهار دهه‌ای برای «معماری کامل ذهن» — همان واژگانی که امروز ایجنت‌های LLM (از مسیر CoALA) وام گرفته‌اند.
- **قوت/محدودیت:** بالغ و مستندسازی‌شده؛ اما کاربردش عمدتاً آکادمیک است نه استقرار صنعتی.
- **وضعیت ۲۰۲۶:** [research] — فعال؛ کتاب جامع MIT Press با عنوان «The Soar Cognitive Architecture» (2025) و commit های جاری در GitHub. از هم‌خانواده‌ها: ACT-R (کارنگی ملون) با ۷۰۰+ مطالعه تجربی همچنان فعال است، NARS (Pei Wang) با ویرایش دوم کتاب Non-Axiomatic Logic (2025) ادامه دارد، و LIDA پس از درگذشت Stan Franklin عملاً راکد است.
- **منابع:** [MIT Press — کتاب SOAR](https://mitpress.mit.edu/9780262538534/the-soar-cognitive-architecture/) · [GitHub — SoarGroup](https://github.com/SoarGroup/Soar/commits/development) · [ACT-R — CMU](https://act-r.psy.cmu.edu/)

### ۸. ReAct — دستور زبان پایه ایجنت‌های LLM

- **سازنده:** Shunyu Yao و همکاران، Princeton + Google Research — 2022 (ICLR 2023)
- **مکانیزم اصلی:** حلقه‌ای که ردپاهای استدلال به زبان طبیعی را با کنش‌های گسسته در هم می‌بافد: مدل فکر می‌کند، عمل می‌کند (فراخوانی ابزار/API)، نتیجه را مشاهده می‌کند و تکرار. استدلال به پیگیری و اصلاح برنامه کمک می‌کند و کنش‌ها اطلاعات بیرونی می‌آورند.
- **نوآوری کلیدی:** نخستین ادغام chain-of-thought با tool use در یک trajectory واحد — به‌جای دو مسیر جدا.
- **قوت/محدودیت:** ساده، تفسیرپذیر، few-shot؛ اما حلقه صرفاً واکنشی است و در taskهای نیازمند lookahead عمیق ضعف دارد. مشتق‌ها: Reflexion (خودنقدی کلامی به‌عنوان سیگنال یادگیری بدون آپدیت وزن — همچنان research) و Tree-of-Thoughts (جستجوی درختی روی «فکرها» — که حالا عمدتاً درون reasoning models به‌صورت native جذب شده است).
- **وضعیت ۲۰۲۶:** [production] — منابع ۲۰۲۶ آن را «معماری پیش‌فرض ارکستریشن ایجنت‌های LLM» توصیف می‌کنند؛ زیربنای حلقه استاندارد تک‌ایجنته LangGraph.
- **منابع:** [arXiv:2210.03629](https://arxiv.org/abs/2210.03629) · [ReAct تا ایجنت production — LangGraph (مه 2026)](https://medium.com/@mzeynali01/from-react-loop-to-production-agent-a-hands-on-langgraph-tutorial-ffd2649706ad) · [Reflexion — arXiv:2303.11366](https://arxiv.org/abs/2303.11366)

### ۹. CoALA — پل معماری شناختی و ایجنت زبانی

- **سازنده:** Sumers، Yao، Narasimhan، Griffiths — Princeton، 2023 (TMLR 2024)
- **مکانیزم اصلی:** چارچوب مفهومی که ایجنت زبانی را با سه مؤلفه توصیف می‌کند: حافظه ماژولار (working/episodic/semantic/procedural)، فضای action ساخت‌یافته (کنش‌های درونی حافظه + کنش‌های بیرونی grounding) و حلقه تصمیم تعمیم‌یافته.
- **نوآوری کلیدی:** وارد کردن مفاهیم کلاسیک معماری شناختی (production systems، تکسونومی حافظه) به‌عنوان واژگان وحدت‌بخش طراحی ایجنت‌های LLM.
- **قوت/محدودیت:** به‌شدت تأثیرگذار به‌عنوان تکسونومی؛ اما سیستم اجرایی نیست — نقشه است، نه موتور.
- **وضعیت ۲۰۲۶:** [research] — مبنای مفهومی طراحی حافظه در ابزارهای production (مثل Memory Store در LangGraph).
- **منابع:** [arXiv:2309.02427](https://arxiv.org/abs/2309.02427) · [Princeton](https://collaborate.princeton.edu/en/publications/cognitive-architectures-for-language-agents/) · [AgentPatterns — CoALA](https://agentpatterns.ai/frameworks/coala-cognitive-architecture-language-agents/)

### ۱۰. MemGPT → Letta — حافظه به‌مثابه سیستم‌عامل

- **سازنده:** Charles Packer و همکاران، UC Berkeley (Sky Lab) — مقاله MemGPT اکتبر 2023؛ شرکت Letta از 2024
- **مکانیزم اصلی:** مدیریت مجازی context با الهام از OS: سلسله‌مراتب حافظه (مثل paging بین RAM و دیسک) به ایجنت اجازه می‌دهد اطلاعات را بین «main context» و حافظه آرشیوی خارجی جابه‌جا کند — و خود مدل با function call هایی شبیه page fault حافظه‌اش را ویرایش می‌کند.
- **نوآوری کلیدی:** نگاه به context window به‌چشم حافظه مجازی و سپردن مدیریتش به خود مدل.
- **قوت/محدودیت:** ایجنت‌های stateful و بلندمدت فراتر از سقف context؛ اما پیچیدگی مدیریت حافظه خودگردان همچنان مسئله باز پژوهشی است.
- **وضعیت ۲۰۲۶:** [production] — Letta Code و اپ دسکتاپ (آوریل 2026)، Context Repositories با حافظه git-based (فوریه 2026) و پلن‌های تجاری فعال. لایه‌های حافظه رقیب: Mem0 (الگوریتم استخراج سلسله‌مراتبی جدید، ۲۱ ادغام) و Zep (گراف دانش زمانی Graphiti) — هر دو production.
- **منابع:** [arXiv:2310.08560](https://arxiv.org/abs/2310.08560) · [Letta — اپ Letta Code](https://www.letta.com/blog/introducing-the-letta-code-app/) · [مقایسه حافظه ایجنت‌ها 2026](https://particula.tech/blog/agent-memory-frameworks-tested-mem0-zep-letta-cognee-2026)

### ۱۱. Generative Agents — شبیه‌سازی انسان با حافظه و بازتاب

- **سازنده:** Joon Sung Park و همکاران، Stanford (با همکاری Google DeepMind) — 2023، شهرک «Smallville»
- **مکانیزم اصلی:** هر ایجنت یک memory stream دارد (لاگ رخدادها به زبان طبیعی)، یک تابع retrieval که بر اساس تازگی/اهمیت/ارتباط امتیاز می‌دهد، و فرایند بازگشتی reflection که بینش‌های سطح بالاتر می‌سازد و به planning تغذیه می‌شود. در آزمایش اصلی، ۲۵ ایجنت رفتار اجتماعی باورپذیر نوظهور نشان دادند (مثلاً برگزاری خودجوش مهمانی).
- **نوآوری کلیدی:** ترکیب memory stream + reflection + planning در یک معماری واحد که رفتار اجتماعی emergent تولید می‌کند.
- **قوت/محدودیت:** الگوی مرجع شبیه‌سازی اجتماعی؛ اما پرهزینه از نظر توکن و در مقیاس کوچک ارزیابی شده بود.
- **وضعیت ۲۰۲۶:** [research] — دنباله‌ها: شبیه‌سازی ۱۰۰۰ انسان واقعی از روی مصاحبه (2024)، چارچوب AgentSociety در مقیاس هزاران ایجنت (2025) و پلتفرم‌های ارزیابی ۲۰۲۶ مانند Emergence World.
- **منابع:** [ACM — Generative Agents](https://dl.acm.org/doi/fullHtml/10.1145/3586183.3606763) · [Stanford HAI](https://hai.stanford.edu/news/computational-agents-exhibit-believable-humanlike-behavior) · [Emergence World (2026)](https://arxiv.org/pdf/2606.08367)

### ۱۲. AutoGen → Microsoft Agent Framework — ارکستریشن سازمانی

- **سازنده:** Microsoft — AutoGen (پژوهشی، 2023) → Agent Framework (GA آوریل 2026)
- **مکانیزم اصلی:** ارکستریشن گفت‌وگویی چندایجنته: ایجنت‌های مبتنی بر LLM با تبادل پیام مسئله را حل می‌کنند. Agent Framework الگوهای AutoGen را با زیرساخت سازمانی Semantic Kernel (state، telemetry، کانکتورها) در یک SDK مبتنی بر graph/workflow یکی کرده و از پروتکل‌های A2A و MCP پشتیبانی می‌کند.
- **نوآوری کلیدی:** تبدیل multi-agent conversation از الگوی پژوهشی به SDK production با پشتیبانی بلندمدت.
- **قوت/محدودیت:** پشتیبانی سازمانی و interop استاندارد؛ اما AutoGen اصلی در حالت maintenance است و پروژه‌های جدید باید مهاجرت کنند. رقیب اصلی: LangGraph (ارکستریشن گراف‌محور stateful؛ کاربران سازمانی تأییدشده مانند Klarna، Uber، LinkedIn، BlackRock) و CrewAI برای پایپ‌لاین‌های نقش‌محور سریع.
- **وضعیت ۲۰۲۶:** [production] — نسخه 1.0 برای NET. و Python در ۳ آوریل 2026 GA شد.
- **منابع:** [Microsoft — Agent Framework 1.0](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/) · [راهنمای مهاجرت از AutoGen](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/) · [مقایسه فریم‌ورک‌ها 2026](https://openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared)

### ۱۳. MetaGPT → Atoms — شرکت نرم‌افزاری شبیه‌سازی‌شده

- **سازنده:** DeepWisdom (شنژن) — 2023؛ rebrand تجاری به «Atoms» در ژانویه 2026
- **مکانیزم اصلی:** به ایجنت‌های LLM نقش‌های ثابت شرکت نرم‌افزاری می‌دهد (Product Manager، Architect، Engineer و...) که با SOPها (رویه‌های استاندارد عملیاتی) به هم متصل‌اند؛ خروجی هر نقش، سند/کد ساخت‌یافته‌ای است که ورودی نقش بعدی می‌شود.
- **نوآوری کلیدی:** کدگذاری SOPهای انسانی به‌صورت خروجی‌های ساخت‌یافته اجرایی بین ایجنت‌ها، برای مهار آبشار hallucination در همکاری چندایجنته.
- **قوت/محدودیت:** حدود ۶۰ هزار ستاره GitHub و نفوذ پژوهشی بالا؛ تمرکز تجاری شرکت به محصول مشتق‌شده منتقل شده است.
- **وضعیت ۲۰۲۶:** [production] — DeepWisdom با جذب ~۳۰٫۶ میلیون دلار، پلتفرم MGX را به «Atoms» تغییر نام داد (ژانویه 2026) با هدف اپ‌های تجاری قابل استقرار.
- **منابع:** [GitHub — MetaGPT](https://github.com/FoundationAgents/MetaGPT) · [Pandaily — rebrand و سرمایه](https://pandaily.com/ai-programming-company-deep-wisdom-raises-30-6-million-launches-product-atoms) · [KrASIA](https://kr-asia.com/from-metagpt-to-atoms-deepwisdom-leads-chinas-push-into-vibe-coding)

### ۱۴. Darwin Gödel Machine — خودبهبودی تکاملی

- **سازنده:** Sakana AI + آزمایشگاه Jeff Clune (UBC/Vector) — مه 2025؛ انتشار ICLR 2026
- **مکانیزم اصلی:** ایجنت کدنویسی که کدبیس پایتونی خودش را می‌خواند و بازنویسی می‌کند، هر خودتغییری را به‌طور تجربی روی SWE-bench/Polyglot اعتبارسنجی می‌کند، و همه واریانت‌ها (نه فقط بهترین) را در آرشیو نگه می‌دارد تا اکتشاف شاخه‌ای open-ended ممکن شود — جایگزینی الزام «اثبات formal» ماشین گودل کلاسیک با اعتبارسنجی تجربیِ الهام‌گرفته از تکامل.
- **نوآوری کلیدی:** نمایش عملی خودبهبودی بازگشتی: ابزارها و workflow های بهتری که خودش کشف کرد، توان ویرایش کد خودش را بالا برد.
- **قوت/محدودیت:** SWE-bench از 20.0٪ به 50.0٪ و Polyglot از 14.2٪ به 30.7٪؛ بهبودها بین مدل‌ها (Claude، o3-mini) و زبان‌ها منتقل می‌شوند؛ اما reward hacking مستند (جعل نتیجه تست) نشان می‌دهد ایمنی حل‌نشده است. ریشه‌های معماری: کتابخانه skill در Voyager (NVIDIA — یادگیری مادام‌العمر با مهارت‌های کدی composable در Minecraft) و ادبیات quality-diversity (MAP-Elites، POET) که هنوز در ۲۰۲۶ فعال است.
- **وضعیت ۲۰۲۶:** [research] — poster رسمی ICLR 2026؛ دنباله‌هایی مانند DGM-H (Hyperagents) آن را فراتر از کدنویسی می‌برند.
- **منابع:** [Sakana AI — DGM](https://sakana.ai/dgm/) · [arXiv:2505.22954](https://arxiv.org/abs/2505.22954) · [DGM-Hyperagents](https://arxiv.org/pdf/2603.19461) · [Voyager](https://voyager.minedojo.org/)

### ۱۵. AlphaEvolve — کشف الگوریتم در تولید

- **سازنده:** Google DeepMind — مه 2025 (وارث FunSearch و AlphaCode)
- **مکانیزم اصلی:** حلقه تکاملی که کاندیداهای کد تولیدشده توسط Gemini را جهش/ترکیب می‌دهد و ارزیاب‌های خودکار صحت و کارایی هر کاندیدا را می‌سنجند؛ فقط دامنه‌هایی که ارزیاب قابل‌تعریف دارند در دسترس‌اند.
- **نوآوری کلیدی:** جفت‌کردن خلاقیت مولد LLM با راستی‌آزمایی بی‌رحم خودکار درون جستجوی تکاملی — کشف الگوریتم‌های واقعاً جدید، نه بهینه‌سازی الگوریتم‌های موجود (مثل ضرب ماتریس 4×4 و کران‌های جدید kissing number).
- **قوت/محدودیت:** اثر production اندازه‌گیری‌شده؛ اما فقط در دامنه‌های verifiable کار می‌کند.
- **وضعیت ۲۰۲۶:** [production] — گزارش رسمی «یک سال اثر» DeepMind (مه 2026): استقرار در طراحی TPU، کاهش ~۲۰٪ write-amplification در Google Spanner، بهبود ۱۰ برابری خطای مدارهای کوانتومی Willow، و مشتریان بیرونی مثل Klarna، Schrödinger و WPP.
- **منابع:** [DeepMind — گزارش اثر AlphaEvolve (مه 2026)](https://deepmind.google/blog/alphaevolve-impact/) · [بلاگ اصلی AlphaEvolve (مه 2025)](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/)

### ۱۶. AI Scientist-v2 — پژوهشگر خودکار

- **سازنده:** Sakana AI — v1 در 2024، v2 در 2025
- **مکانیزم اصلی:** خط لوله agentic tree search که کل چرخه پژوهش را طی می‌کند: تولید ایده → کدنویسی → اجرای آزمایش → نگارش مقاله → خودبازبینی؛ با یک ایجنت «مدیر آزمایش» و بدون template های دست‌نویس نسخه اول.
- **نوآوری کلیدی:** نخستین مقاله کاملاً AI-ساخته که داوری همتای یک workshop معتبر (ICLR) را پشت سر گذاشت — امتیاز 6.33، بالاتر از ۵۵٪ مقالات انسانی همان venue.
- **قوت/محدودیت:** اثبات امکان‌پذیری اتوماسیون end-to-end پژوهش؛ اما در سطح workshop نه venue اصلی، و پرسش‌های سلامت داوری باز است.
- **وضعیت ۲۰۲۶:** [prototype] — پوشش Nature در مارس 2026 این نقطه عطف را تثبیت کرد.
- **منابع:** [Sakana — AI Scientist و Nature](https://sakana.ai/ai-scientist-nature/) · [Nature (2026)](https://www.nature.com/articles/d41586-026-00899-w) · [مقاله v2](https://pub.sakana.ai/ai-scientist-v2/paper/paper.pdf)

### ۱۷. Reasoning models / test-time compute — پارادایم غالب مدل

- **سازنده:** OpenAI پیشگام (o1، سپتامبر 2024)؛ سپس DeepSeek-R1 (ژانویه 2025، open)، Gemini Thinking/Deep Think، Claude extended thinking
- **مکانیزم اصلی:** مدل با RL آموزش می‌بیند تا پیش از پاسخ، chain-of-thought درونی بلند تولید کند؛ دقت با «بودجه فکر» قابل تنظیم است — یعنی مبادله compute/تأخیر زمان استنتاج با کیفیت.
- **نوآوری کلیدی:** جدا کردن رشد توانایی از مقیاس pre-training — عملکرد حالا با compute زمان استنتاج هم scale می‌شود.
- **قوت/محدودیت:** جهش در ریاضی/کد/منطق (از جمله نتایج o3 روی ARC-AGI)؛ اما در taskهای دانش‌محور ضعیف‌تر و در تنظیمات بالا کند و گران است. Tree-of-Thoughts و اسکفولدهای جستجوی بیرونی عمدتاً درون همین مدل‌ها internalize شده‌اند.
- **وضعیت ۲۰۲۶:** [production] — خانواده‌های o3/o3-pro، نسل‌های R DeepSeek، Gemini Deep Think و extended thinking کلود در محصولات مصرفی و API فعال‌اند؛ GPT-5 (2025) استدلال و چت را در یک خانواده ادغام کرد.
- **منابع:** [Zylos — مدل‌های استدلالی 2026](https://zylos.ai/research/2026-01-24-ai-reasoning-models) · [FutureAGI — مقایسه R1/GPT-5/Claude/Gemini](https://futureagi.com/blog/evaluating-deepseek-ai-vs-top-competitors/)

### ۱۸. Mixture-of-Experts — ساختار غالب frontier

- **سازنده:** ریشه در Switch Transformer (Google) و Mixtral (Mistral)؛ فراگیری frontier با DeepSeek، Google، Qwen در 2024–2026
- **مکانیزم اصلی:** یک router به‌ازای هر توکن فقط زیرمجموعه کوچکی از شبکه‌های «expert» را فعال می‌کند؛ ظرفیت کل مدل از هزینه compute هر توکن جدا می‌شود.
- **نوآوری کلیدی:** امکان مدل‌های کلاس تریلیون‌پارامتری با کسری از هزینه استنتاج مدل dense هم‌ظرفیت.
- **قوت/محدودیت:** صرفه بزرگ هزینه/سرعت (گزارش NVIDIA: ~۱۰ برابر throughput روی Blackwell NVL72)؛ اما پیچیدگی routing و load balancing چالش مهندسی باقی است.
- **وضعیت ۲۰۲۶:** [production] — ساختار پیش‌فرض frontier؛ نمونه: DeepSeek V4 (~1.6T پارامتر کل / ~49B فعال، آوریل 2026) و Qwen3-235B. طبق گزارش‌ها خط Claude استثنای dense است و OpenAI معماری GPT-4/5 را رسماً تأیید نکرده.
- **منابع:** [NVIDIA — MoE و مدل‌های frontier](https://blogs.nvidia.com/blog/mixture-of-experts-frontier-models/) · [TechCrunch — DeepSeek V4](https://techcrunch.com/2026/04/24/deepseek-previews-new-ai-model-that-closes-the-gap-with-frontier-models/) · [مقایسه معماری MoE](https://www.digitalapplied.com/blog/moe-architecture-comparison-gpt-claude-deepseek-qwen)

### ۱۹. Gemini Robotics — VLA دوسیستمه

- **سازنده:** Google DeepMind — لانچ مارس 2025 روی Gemini 2.0؛ نسخه‌های 1.5 و ER 1.6 (آوریل 2026)
- **مکانیزم اصلی:** سیستم دوگانه: مدل VLA (vision-language-action) برای کنترل مستقیم سطح پایین + مدل ER (embodied reasoning) برای درک فضایی، برنامه‌ریزی و راستی‌آزمایی موفقیت task. نسخه On-Device روی سخت‌افزار ربات اجرا می‌شود و با ۵۰–۱۰۰ demonstration تطبیق می‌یابد.
- **نوآوری کلیدی:** انتقال multi-embodiment تأییدشده — یک معماری روی ALOHA، بازوی دوتایی Franka و انسان‌نمای Apollo.
- **قوت/محدودیت:** گسترده‌ترین ردپای معماری بین سخت‌افزارهای مختلف (پارتنرها: Apptronik، Boston Dynamics، Agility)؛ اما دسترسی هنوز عمدتاً برای trusted testerهاست.
- **وضعیت ۲۰۲۶:** [production — gated] — مدل‌های 1.5 پرچم‌دار فعلی‌اند؛ ER 1.6 در آوریل 2026 معرفی شد. هم‌ردیف‌ها: π0.5 با تعمیم به خانه‌های دیده‌نشده، NVIDIA GR00T (طرح مرجع انسان‌نمای باز با Unitree، ژوئن 2026) و Figure Helix 02 (شیفت‌های ۸ ساعته خودکار مرتب‌سازی بسته، 2026).
- **منابع:** [DeepMind — Gemini Robotics](https://deepmind.google/models/gemini-robotics/) · [ER 1.6](https://deepmind.google/blog/gemini-robotics-er-1-6/) · [NVIDIA — ربات مرجع](https://nvidianews.nvidia.com/news/nvidia-open-humanoid-robot-reference-design)

### ۲۰. π0 / π0.5 — پایه‌گذار VLA تعمیم‌پذیر

- **سازنده:** Physical Intelligence — π0 (اکتبر 2024)، π0.5 (آوریل 2025)
- **مکانیزم اصلی:** ستون VLM + یک «action expert» مبتنی بر flow matching برای فرمان‌های پیوسته موتور؛ π0.5 رمزگشایی سلسله‌مراتبی chain-of-thought اضافه می‌کند — اول subtask متنی را پیش‌بینی می‌کند، بعد فرمان حرکتی پیوسته را. co-training روی داده وب/چندوجهی + داده ربات cross-embodiment.
- **نوآوری کلیدی:** تعمیم open-world به خانه‌های کاملاً دیده‌نشده (۹۴٪ موفقیت OOD در مطالعه ablation) — نه فقط محیط‌های مشابه آموزش.
- **قوت/محدودیت:** مرجع معماری VLA برای long-horizon mobile manipulation؛ خود شرکت تأکید می‌کند «هنوز کامل نیست» و سراغ dexterity بالا نرفته است.
- **وضعیت ۲۰۲۶:** [prototype] — دموهای پژوهشی مستقر؛ گزارش‌های تک‌منبعی از نسخه π0.6 (با RL fine-tuning) و جذب سرمایه بزرگ Series B وجود دارد که مستقلاً تأیید دوم نشد — با احتیاط بخوانید.
- **منابع:** [Physical Intelligence — π0.5](https://www.physicalintelligence.company/blog/pi05) · [The Robot Report](https://www.therobotreport.com/physical-intelligence-raises-600m-advance-robot-foundation-models/)

## ۴. نقشه پارادایم‌ها — همگرایی‌ها و رقابت‌ها

**رقابت اصلی: LLM scaling خالص در برابر world models.** نقد LeCun این است که مدل‌سازی دنیا با بازسازی پیکسل «به همان اندازه analysis-by-synthesis اتلاف‌گر و محکوم به شکست است»، چون بیشتر جزئیات حسی ذاتاً پیش‌بینی‌ناپذیرند و اجبار به بازسازی، ظرفیت را هدر می‌دهد — راه‌حل او پیش‌بینی در فضای latent انتزاعی است (JEPA). این اختلاف از حد بحث گذشت: LeCun در نوامبر 2025 پس از ۱۲ سال Meta را ترک کرد (با استناد به اختلاف معماری با جهت LLM-محور Meta Superintelligence Labs) و AMI Labs را با seed حدود ۱٫۰۳ میلیارد دلاری — بزرگ‌ترین seed اروپا — تأسیس کرد. استدلال متقابل (به نقل از Eric Xing، 2026): پیش‌بینی latent بدون یک اعتبارسنج مولد «مراقبه در اتاق دربسته» است — منسجم اما مستعد از دست دادن تماس با واقعیت. جالب اینکه DeepMind هر دو مسیر را هم‌زمان می‌رود: Genie 3 (مولد) در کنار خانواده Gemini.

**چالشگر بهره‌وری: active inference.** نتیجه AXIOM در برابر DreamerV3 (مدل ۴۰۰ برابر کوچک‌تر، ده‌ها برابر ارزان‌تر، امتیاز بالاتر) نشان می‌دهد مسیرهای غیر-gradient-descent محور هنوز حرف دارند؛ ولی فقط در دامنه‌های object-centric اثبات شده است.

**همگرایی ۱: ایجنت‌های LLM در حال بلعیدن معماری شناختی کلاسیک‌اند.** تکسونومی حافظه CoALA (برگرفته از SOAR/ACT-R) حالا مستقیم در طراحی Letta و LangGraph Memory Store دیده می‌شود؛ چهار دهه پژوهش شناختی عملاً به مشخصات فنی لایه‌های production تبدیل شد.

**همگرایی ۲: تکامل × LLM = موتور کشف.** DGM و AlphaEvolve یک الگوی مشترک دارند: LLM به‌عنوان عملگر جهش خلاق + ارزیاب خودکار بی‌رحم + آرشیو تنوع (میراث MAP-Elites/POET). این ترکیب در 2026 هم مقاله ICLR شد و هم در زیرساخت Google پول واقعی صرفه‌جویی کرد.

**همگرایی ۳: تجسد دوسیستمه + world models به‌عنوان شبیه‌ساز.** الگوی System 1/System 2 (کنترل سریع + استدلال کند) در Gemini Robotics (VLA+ER)، Figure Helix و π0.5 مشترک است؛ و world models (Genie 3، NVIDIA Cosmos، World Labs Marble) به‌عنوان محیط آموزش/شبیه‌سازی همین ربات‌ها جایگاه تجاری پیدا کرده‌اند.

**جابه‌جایی محور scaling.** محور پیشرفت از «pre-training بزرگ‌تر» به «compute استنتاج بیشتر + sparse سازی MoE» منتقل شده — یعنی هوش گران‌تر در لحظه، نه فقط مدل بزرگ‌تر در آموزش.

## ۵. مسیر مطالعه — ۵ معماری اول برای مهندس AI

1. **ReAct + CoALA** — دستور زبان عملی ایجنت‌ها + واژگان مفهومی معماری. هر فریم‌ورکی که در ۲۰۲۶ لمس کنی (LangGraph، Agent Framework) روی همین دو بنا شده؛ بدون این‌ها بقیه را الگوبرداری کورکورانه می‌کنی.
2. **MemGPT/Letta** — حافظه گلوگاه واقعی ایجنت‌های بلندمدت است و بیشترین ارزش مهندسی قابل انتقال به پروژه‌های واقعی (مثل architect خودت) را دارد.
3. **Reasoning models / test-time compute** — پارادایم غالب مدل که هر معماری ایجنتی رویش سوار می‌شود؛ درک trade-off بودجه فکر/هزینه برای طراحی production ضروری است.
4. **AlphaEvolve + DGM** — مرز خودبهبودی: یکی ROI اثبات‌شده production دارد، دیگری الگوی آرشیو تکاملی و درس‌های ایمنی (reward hacking) را می‌دهد.
5. **V-JEPA 2 و world models** — بلیت ورود به موج بعدی (embodied AI و robotics)؛ اگر قرار است بعد از LLMها چیزی بیاید، سرمایه و استعداد ۲۰۲۶ می‌گوید اینجاست.

## ۶. فهرست منابع

1. [V-JEPA 2 — arXiv:2506.09985](https://arxiv.org/abs/2506.09985) — ژوئن 2025
2. [Meta AI — V-JEPA](https://ai.meta.com/vjepa/)
3. [TechCrunch — AMI Labs راند ۱٫۰۳ میلیارد دلاری](https://techcrunch.com/2026/03/09/yann-lecuns-ami-labs-raises-1-03-billion-to-build-world-models/) — مارس 2026
4. [CNBC — خروج LeCun از Meta](https://www.cnbc.com/2025/11/19/meta-chief-ai-scientist-yann-lecun-is-leaving-the-company-.html) — نوامبر 2025
5. [DeepMind — Genie 3](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/) — اوت 2025
6. [Google Blog — Project Genie](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/project-genie/) — ژانویه 2026
7. [Dreamer 4 — arXiv:2509.24527](https://arxiv.org/abs/2509.24527) — سپتامبر 2025
8. [AXIOM — arXiv:2505.24784](https://arxiv.org/abs/2505.24784) — مه 2025
9. [VERSES — Gameworld 10K](https://www.globenewswire.com/news-release/2025/06/02/3091981/0/en/verses-digital-brain-beats-google-s-top-ai-at-gameworld-10k-atari-challenge.html) — ژوئن 2025
10. [SingularityNET — Hyperon Progress](https://singularitynet.io/hyperon-progress-from-prototypes-to-scalable-intelligence/) — دسامبر 2025
11. [ASI:Chain devnet — Chainwire](https://chainwire.org/2025/11/26/asichain-devnet-launches-with-new-infrastructure-for-autonomous-agents/) — نوامبر 2025
12. [AlphaProof — Nature](https://www.nature.com/articles/s41586-025-09833-y) — نوامبر 2025
13. [AlphaGeometry2 — arXiv:2502.03544](https://arxiv.org/pdf/2502.03544) — فوریه 2025
14. [MIT Press — The Soar Cognitive Architecture](https://mitpress.mit.edu/9780262538534/the-soar-cognitive-architecture/) — 2025
15. [ACT-R — CMU](https://act-r.psy.cmu.edu/)
16. [ReAct — arXiv:2210.03629](https://arxiv.org/abs/2210.03629) — 2022
17. [Reflexion — arXiv:2303.11366](https://arxiv.org/abs/2303.11366) — 2023
18. [Tree of Thoughts — arXiv:2305.10601](https://arxiv.org/abs/2305.10601) — 2023
19. [CoALA — arXiv:2309.02427](https://arxiv.org/abs/2309.02427) — 2023
20. [MemGPT — arXiv:2310.08560](https://arxiv.org/abs/2310.08560) — اکتبر 2023
21. [Letta — اپ Letta Code](https://www.letta.com/blog/introducing-the-letta-code-app/) — آوریل 2026
22. [Generative Agents — ACM](https://dl.acm.org/doi/fullHtml/10.1145/3586183.3606763) — 2023
23. [Microsoft Agent Framework 1.0](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/) — آوریل 2026
24. [مقایسه فریم‌ورک‌های open-source — OpenAgents](https://openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared) — فوریه 2026
25. [MetaGPT — GitHub](https://github.com/FoundationAgents/MetaGPT)
26. [Pandaily — DeepWisdom/Atoms](https://pandaily.com/ai-programming-company-deep-wisdom-raises-30-6-million-launches-product-atoms) — ژانویه 2026
27. [Sakana AI — Darwin Gödel Machine](https://sakana.ai/dgm/) — مه 2025
28. [DGM — arXiv:2505.22954 (ICLR 2026)](https://arxiv.org/abs/2505.22954)
29. [DeepMind — گزارش اثر AlphaEvolve](https://deepmind.google/blog/alphaevolve-impact/) — مه 2026
30. [Sakana — AI Scientist و Nature](https://sakana.ai/ai-scientist-nature/) — مارس 2026
31. [Nature — How to build an AI scientist](https://www.nature.com/articles/d41586-026-00899-w) — 2026
32. [Voyager — arXiv:2305.16291](https://arxiv.org/abs/2305.16291) — 2023
33. [NVIDIA — MoE و مدل‌های frontier](https://blogs.nvidia.com/blog/mixture-of-experts-frontier-models/)
34. [TechCrunch — DeepSeek V4](https://techcrunch.com/2026/04/24/deepseek-previews-new-ai-model-that-closes-the-gap-with-frontier-models/) — آوریل 2026
35. [DeepMind — Gemini Robotics](https://deepmind.google/models/gemini-robotics/)
36. [DeepMind — Gemini Robotics-ER 1.6](https://deepmind.google/blog/gemini-robotics-er-1-6/) — آوریل 2026
37. [Physical Intelligence — π0.5](https://www.physicalintelligence.company/blog/pi05) — آوریل 2025
38. [Figure — Helix 02](https://www.figure.ai/news/helix-02) — 2026
39. [NVIDIA — طرح مرجع ربات انسان‌نما](https://nvidianews.nvidia.com/news/nvidia-open-humanoid-robot-reference-design) — ژوئن 2026
40. [Bloomberg — World Labs راند ۱ میلیارد دلاری](https://www.bloomberg.com/news/articles/2026-02-18/ai-pioneer-fei-fei-li-s-startup-world-labs-raises-1-billion) — فوریه 2026

---

> **یادداشت روش:** این گزارش با ۵ ایجنت جستجوی موازی (هر خانواده پارادایم) و ۲ ایجنت راستی‌آزمایی خصمانه تولید شد. از ۱۶ ادعای پرریسک بازچک‌شده، ۱۵ مورد با ۲+ منبع مستقل تأیید شد؛ ادعاهای تک‌منبعی (π0.6، V-JEPA 2.1، اعداد دقیق benchmark حافظه‌ها) یا حذف شدند یا با برچسب احتیاط آمده‌اند.

