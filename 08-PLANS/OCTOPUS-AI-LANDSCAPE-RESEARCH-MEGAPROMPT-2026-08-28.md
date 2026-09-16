# مگاپرامپت تحقیقاتی — پایش کامل اکوسیستم هوش مصنوعی برای OCTOPUS

نسخه: 2.0 · 2026-08-28
نقش: Research Scout — مرورگر اینترنت، کشف تکنولوژی‌های جدید، به‌روزرسانی self-awareness
اصل: هر یافته با منبع (URL + تاریخ) · بدون منبع = حذف

---

## [MISSION]

اینترنت را عمیق بگرد و جدیدترین تکنولوژی‌ها، مدل‌ها، فریم‌ورک‌ها، بنچمارک‌ها، اخبار و تغییرات قیمتی APIهای هوش مصنوعی را پیدا کن. خروجی: یک گزارش کامل که مالک بتواند از آن تصمیم بگیرد چه چیزی را وارد OCTOPUS کند و چه چیزی را رد.

---

## [CONNECTOR BUDGET — مجاز و الزامی]

هر ۶ connector زیر باید حداقل یک بار استفاده شوند:

| # | Connector | هدف | حداقل |
|---|---|---|---|
| ۱ | Perplexity Similarweb | رتببندی ترافیک، رشد، geography رقبا | ۳ کوئری |
| ۲ | CB Insights (Perplexity) | funding، category، مارکت‌مپ | ۲ کوئری |
| ۳ | Hugging Face | مدل، benchmark، paper، dataset | ۵۰ نتیجه |
| ۴ | GitHub | مخزن، adoption، maturity | ۲۵ مخزن |
| ۵ | Web Reader (URL fetch) | صفحات رسمی provider، pricing، changelog | ۵ صفحه |
| ۶ | Academic (Semantic Scholar / arXiv) | paperهای بنیادی ۲۰۲۵-۲۰۲۶ | ۱۰ paper |

---

## [SECTION 1 — مدل‌های زبانی]

### ۱.۱ frontier models

| جستجو | هدف |
|---|---|
| "best LLM 2026" | جدیدترین frontier از هر vendor |
| "GPT-5.6 Sol Terra Luna pricing" | قیمت‌گذاری فعلی OpenAI |
| "Claude Opus 5 Sonnet 5 Haiku 4.5 pricing 2026" | قیمت‌گذاری فعلی Anthropic |
| "DeepSeek V4 Flash Pro pricing August 2026" | قیمت‌گذاری فعلی DeepSeek |
| "Gemini 3.0 3.1 Pro Flash pricing 2026" | قیمت‌گذاری فعلی Google |
| "Grok 4 pricing xAI 2026" | قیمت‌گذاری فعلی xAI |
| "Mistral Large Medium Small 3 2026" | قیمت‌گذاری فعلی Mistral |
| "Qwen 3.5 3.6 4.0 pricing Alibaba 2026" | قیمت‌گذاری فعلی Alibaba |

خروجی برای هر مدل:
- نام دقیق · vendor · قیمت‌گذاری (in/out/cache) · context window · tool calling · structured output · JSON schema support · best use case · تاریخ مشاهده · منبع

### ۱.۲ small models برای edge

| جستجو | هدف |
|---|---|
| "best small LLM under 1B 2026" | مدل‌های ۰.۵-۱B |
| "Qwen 3.5 0.8B benchmark" | چالش‌گر فعلی T0 |
| "SmolLM3 3B benchmark edge" | چالش‌گر سنگین‌تر |
| "Phi 4 mini benchmark" | مایکروسافت |
| "Gemma 3 2B benchmark edge 2026" | گوگل |
| "best 0.5B 1B model RK3588 Orange Pi 2026" | بهینه برای ARM |

خروجی: مقایسه با qwen3-0.6b فعلی روی ۱۸۰ — آیا جایگزین بهتر هست؟

### ۱.۳ embedding و reranker

| جستجو | هدف |
|---|---|
| "best embedding model 2026 small efficient" | جایگزین/تکمیلی qwen3-embedding |
| "Qwen3 Embedding 0.6B vs 4B vs 8B" | خانواده کامل |
| "best reranker model 2026 free local" | جایگزین reranker (Anthropic key کار نمی‌کرد) |
| "Nomic embed v2 benchmark" | رقیب |
| "BGE M3 embedding 2026" | رقیب |
| "voyage AI embedding pricing 2026" | رقیب API |

خروجی: آیا qwen3-embedding:0.6b بهترین انتخاب است یا باید عوض شود؟ آیا reranker رایگان جدید وجود دارد؟

### ۱.۴ vision و multimodal

| جستجو | هدف |
|---|---|
| "best vision model API 2026 pricing" | برای تحلیل تصویر املاک |
| "GPT-5.6 vision capability" | |
| "Claude vision pricing 2026" | |
| "Gemini vision pricing 2026" | |
| "best open source vision model 2026" | برای آفلاین |

---

## [SECTION 2 — فریم‌ورک و orchestration]

| جستجو | هدف |
|---|---|
| "best AI agent framework 2026 production" |LangGraph، CrewAI، AutoGen، OpenAI Swarm، Anthropic tool use |
| "durable execution AI agent 2026" | ‏DBOS، ‏Temporal، ‏Inngest، ‏Trigger.dev |
| "AI agent observability 2026" | ‏LangSmith، ‏Langfuse، ‏Arize، ‏Phoenix |
| "structured output LLM 2026 best" | ‏Instructor، ‏Outlines، ‏llama.cpp grammar |
| "AI agent memory 2026 production" | ‏Mem0، ‏Zep، ‏Letta، ‏MemGPT |
| "multi-agent orchestration 2026" | ‏AG2، ‏MetaGPT، ‏ChatDev |
| "AI coding agent 2026 best" | ‏Cursor، ‏Copilot، ‏Devin، ‏OpenHands |
| "RAG framework 2026 best production" | ‏LlamaIndex، ‏Haystack، ‏txtai |

خروجی برای هر فریم‌ورک:
- نام · گیت‌هاب stars · آخرین commit · زبان · production-ready؟ · آیا با OCTOPUS سازگار است؟ · verdict: ADOPT / TRIAL / ASSESS / HOLD / REJECT

---

## [SECTION 3 — زیرساخت و deployment]

| جستجو | هدف |
|---|---|
| "llama.cpp latest release 2026" | نسخه جدید و قابلیت‌های جدید |
| "vLLM latest 2026" | برای serving سنگین‌تر |
| "Ollama vs vLLM vs llama.cpp 2026" | مقایسه |
| "RK3588 RK3588S NPU inference 2026" | بهینه‌سازی برای Orange Pi |
| "best ARM SBC AI inference 2026" | سخت‌افزار جدید |
| "Orange Pi 5 Pro alternatives 2026" | برد بهتر؟ |
| "Raspberry Pi 5 AI inference 2026" | مقایسه |

---

## [SECTION 4 — اخبار و رویدادهای ۲۰۲۶]

| جستجو | هدف |
|---|---|
| "AI news August 2026" | اخبار مهم ماه |
| "OpenAI news August 2026" | GPT-5.6، ‏Astra، تغییرات |
| "Anthropic news August 2026" | ‏Claude، قیمت‌گذاری، محصولات |
| "DeepSeek news August 2026" | تغییرات قیمت/مدل |
| "Google Gemini news August 2026" | ‏Gemini، ‏Astra |
| "Meta AI news August 2026" | ‏Llama، ‏open source |
| "AI agent deployment production 2026" | مطالعهٔ موردی واقعی |
| "AI startup funding August 2026" | CB Insights |

خروجی: ۱۰ خبر مهم که بر OCTOPUS تأثیر می‌گذارد.

---

## [SECTION 5 — امنیت و reliability]

| جستجو | هدف |
|---|---|
| "AI agent security best practices 2026" | ‏prompt injection، ‏jailbreak، ‏exfiltration |
| "LLM hallucination mitigation 2026" | کاهش توهم |
| "AI reliability benchmark 2026" | ‏AgentBench، ‏SWE-bench |
| "LLM cost optimization 2026" | بهینه‌سازی هزینه |
| "prompt injection defense 2026" | دفاع عملی |
| "AI red teaming 2026" | red team عملی |

---

## [SECTION 6 — رقبا و بازار]

| جستجو (Similarweb) | هدف |
|---|---|
| "perplexity.ai traffic growth 2026" | ترافیک و رشد رقیب |
| "character.ai traffic 2026" | رقیب ‏chat |
| "poe.com traffic 2026" | رقیب ‏chat |
| "chatgpt.com traffic growth 2026" | غول بازار |
| "claude.ai traffic growth 2026" | رقیب |

| جستجو (CB Insights) | هدف |
|---|---|
| "AI agent startup funding 2026" | سرمایه‌گذاری‌ها |
| "AI infrastructure funding 2026" | زیرساخت |
| "AI automation real estate 2026" | مرتبط با Painting/Ziman |

---

## [OUTPUT FORMAT]

### بخش ۱ — مدل‌های جدید کشف‌شده

برای هر مدل جدید که قبلاً در OCTOPUS نبود:
- نام · ‏vendor · قیمت · ‏context · ‏tool calling · ‏structured output · منبع · تاریخ
- پیشنهاد: ‏ADOPT / TRIAL / ASSESS / HOLD / REJECT + دلیل

### بخش ۲ — مدل‌های موجود که باید به‌روز شوند

آیا ‏qwen3-0.6b، ‏qwen3-embedding، ‏deepseek-v4-flash هنوز بهترین انتخاب‌اند؟ یا چیز بهتر آمده؟

### بخش ۳ — فریم‌ورک‌های جدید

آیا فریم‌ورکی هست که با فلسفهٔ ‏OCTOPUS (بدون framework موازی، ‏reuse-first) سازگار باشد؟

### بخش ۴ — تغییرات قیمتی

آیا قیمت‌گذاری ‏DeepSeek/OpenAI/Anthropic تغییر کرده؟ جدول مقایسه با قیمت‌های فعلی.

### بخش ۵ — اخبار بحرانی

آیا خبری هست که بر ‏OCTOPUS تأثیر فوری داشته باشد؟ (تغییر API، ‏deprecation، امنیت)

### بخش ۶ — پیشنهادهای عملیاتی

- ۳ اقدام فوری (با معیار اجرا)
- ۳ اقدام میان‌مدت (این هفته)
- ۳ اقدام بلندمدت (این ماه)
- ۳ چیز که نباید انجام داد (با دلیل)

### بخش ۷ — سطوح شواهد

هر یافته با یکی از این برچسب‌ها:
- `LIVE_API` — خودم تست کردم
- `OFFICIAL_DOCS` — از مستندات رسمی
- `GITHUB_STARS` — از مخزن عمومی
- `NEWS_ARTICLE` — از خبر معتبر
- `BLOG_POST` — از بلاگ (کم‌اعتبارتر)
- `UNKNOWN` — بدون منبع کافی (حذف شود)

---

## [DEFINITION OF DONE]

- [ ] حداقل ۵۰ منبع نام‌برده‌شده
- [ ] حداقل ۳ connector مختلف استفاده شده
- [ ] هر مدل/فریم‌ورک با قیمت/تاریخ/منبع
- [ ] حداقل ۵ یافتهٔ جدید که OCTOPUS قبلاً نمی‌دانست
- [ ] حداقل ۳ پیشنهاد عملیاتی با معیار اجرا
- [ ] هیچ ادعایی بدون منبع
- [ ] هیچ secret یا credential چاپ نشده
- [ ] گزارش به فارسی + انگلیسی (دوزبانه)
