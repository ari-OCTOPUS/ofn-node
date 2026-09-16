# 🧬 پرامپتِ جامعِ ارتقای مهندسی — «ایده‌یاب شخصی»

> **دستورالعملِ اجرا:** این سند یه ممیزیِ مهندسی از ۴۵ دیدگاه مختلف است. هر بخش رو با دقت بخون، وضعیت فعلی رو بررسی کن، و **فقط چیزی که واقعاً نیازه** رو تقویت کن. قانون طلایی: **هیچ کد موجودی رو حذف نکن مگر اینکه دلیل فنی قوی داشته باشی.** همه‌چیز backwards-compatible.

---

## 📋 مشخصاتِ پروژه

```
پروژه:    ایده‌یاب شخصی (Personal Idea Discovery Engine)
مسیر:     C:\Users\Armin\Desktop\4d_system
حجم:      ~۸۵۰۰ خط Python در ۵۱ ماژول
مدل:      SOG (Self-Other Gradient) linear-Gaussian
هدف:      کشف خودکار «نشانه‌های بُعد چهارم» در داده‌های سری‌زمانی
زبان‌ها:   Python 3.13، Streamlit، Plotly، SQLite، ChromaDB
LLM:      Fugu (مغز اصلی، کند)، GLM-4.6 (کمکی، سریع)
```

### ساختار فایل‌ها:
```
4d_system/
├── core/          ← مدل ریاضی SOG (نباید دست بخوره)
│   ├── model.py        (276 خط) — P_closed, DARE, Delta_self, E_shadow
│   ├── metrics.py      (217 خط) — empirical_shadow, fit_shadow_parameters
│   ├── scores.py       (192 خط) — SMS, SLS, PCAI, MSC
│   └── simulator.py    (144 خط) — Monte-Carlo
├── brain/         ← هوشمندی سیستم
│   ├── autoloop.py     (453 خط) — موتور پژوهش خودمختار
│   ├── graph.py        (276 خط) — LangGraph 8-node pipeline
│   ├── nodes.py        (384 خط) — node‌های گراف
│   ├── meta_research.py(690 خط) — تحقیق فراشناختی + وب
│   ├── vault_sync.py   (418 خط) — همگام‌سازی Obsidian
│   ├── web_research.py (269 خط) — جستجوی وب رایگان
│   ├── self_model.py   (253 خط) — خودآگاهی ساختاری
│   ├── patterns.py     (352 خط) — الگوهای معماری
│   ├── hypotheses.py   (215 خط) — فرضیه‌های قابل‌آزمون
│   ├── tools.py        (213 خط) — LangChain @tool
│   ├── reflection.py   (149 خط) — خودارزیابی
│   ├── auto_experiment.py(114) — صف آزمایش
│   └── state.py        (65 خط) — state definition
├── data/          ← منابع داده
│   ├── rhythm_store.py (238 خط) — حافظه‌ی ریتم‌های خام (.npy)
│   ├── physical.py     (130 خط) — Brownian, Lorenz, pendulum
│   ├── synthetic.py    (111 خط) — AR(1), Gaussian, logistic
│   └── real_api.py     (128 خط) — Yahoo Finance, NOAA
├── memory/        ← حافظه‌ی پایدار
│   ├── research_store.py(542) — patterns, architectures, proposals
│   ├── store.py        (261 خط) — experiments, rhythms, conversations
│   ├── vectorstore.py  (133 خط) — ChromaDB RAG
│   └── embeddings.py   (48 خط) — multilingual MiniLM
├── ui/            ← رابط کاربری
│   ├── visuals.py      (666 خط) — Plotly: tesseract, graph, gauges
│   ├── app.py          (246 خط) — 3 تب: loop, graph, meta
│   ├── tab_graph.py    (233 خط) — گراف Obsidian + معادلات
│   ├── tab_meta.py     (338 خط) — خودآگاهی + پروپوزال
│   ├── tab_laboratory.py(212) — آزمایشگاه تعاملی (غیرفعول)
│   └── tab_research.py (272 خط) — پژوهش (غیرفعول)
├── llm/           ← کلاینت‌های LLM
│   ├── router.py       (188 خط) — Fugu→GLM→Mock routing
│   ├── langchain_models.py(172)— adapter LangChain
│   ├── glm_client.py   (61 خط) — Z.ai endpoint
│   ├── fugu_client.py  (56 خط) — Sakana AI
│   └── base_client.py  (47 خط) — base class
├── agents/        ← ایجنت‌های تخصصی
│   ├── orchestrator.py (139 خط)
│   ├── detector.py     (88 خط) — W1 shadow detector
│   ├── analyst.py      (72 خط) — W2 geometric analyst
│   ├── reporter.py     (109 خط) — W3 reporter
│   ├── verifier.py     (81 خط) — W0 verifier
│   └── base.py         (75 خط)
├── config/
│   └── settings.py     (128 خط) — LLMConfig, ANCHORS
└── knowledge/
    └── ledger.py       (160 خط) — immutable 4D/ reference
```

### لنگرهای ریاضی (نباید تغییر کنن):
```
E_shadow  = 0.012553  nat/گام
Δ_self    = 0.122520  nat/گام
I_pred    = 0.0144179 nat
اتحاد:    ½log(σ²_z/S) = E_shadow + Δ_self = 0.135073
نقطه‌ی کار: ρ=0.5, λ=0.5, σ_ε=0.1, σ_ζ=0.05, σ_d=0.1
```

---

## 🔍 ممیزیِ ۴۵‌گانه

برای هر دیدگاه، این چک‌لیست رو طی کن:
1. وضعیت فعلی چیست؟ (بخوان/بررسی کن)
2. مشکل یا ضعف چیست؟
3. چه تقویتی نیاز است؟
4. پیاده‌سازی کن (اگه لازمه)

### 🏗️ الف) معماری و ساختار (۱–۸)

**۱. یکپارچگی ماژول‌ها** — آیا همه‌ی ماژول‌ها به‌درستی import میشن؟ circular import نیست؟ `tab_laboratory.py` و `tab_research.py` ساخته شدن ولی به `app.py` وصل نیستن — آیا باید وصل بشن یا حذف؟

**۲. جدول‌های SQLite** — ۳ فایل جداگانه schema می‌سازن (`store.py`، `research_store.py`). آیا migration مدیریت میشه؟ اگه ستون عوض بشه چه؟

**۳. لایه‌بندی** — آیا separation of concerns رعایت شده؟ `brain/` باید logic داشته باشه، `ui/` فقط display. چک کن هیچ business logic‌ای تو UI نیست.

**۴. مدیریت خطا** — هر `except Exception: pass` یه مشکل بالقوه‌ست. پیدا کن همه رو و logging اضافه کن.

**۵. Type hints** — آیا تابع‌ها type annotation دارن؟ مهم‌ترین فایل‌ها (autoloop, model, graph) رو چک کن.

**۶. Constants و Magic Numbers** — آیا اعداد hardcode شده باید constant بشن؟ (مثلاً timeout‌ها، threshold‌ها)

**۷. Dependency injection** — آیا `get_router()` singleton درست کار می‌کنه؟ تو test‌ها قابل mock کردن هست؟

**۸. Configuration management** — آیا `.env` به‌درستی load میشه؟ `settings.py` central هست؟

### 🔒 ب) امنیت و پایداری (۹–۱۶)

**۹. API key مدیریت** — کلیدها تو `.env` هستن. آیا leak نمیشن تو log؟ `st.caption` کلید رو نشون نمیده؟

**۱۰. SQL Injection** — آیا همه‌ی query‌ها parameterized هستن؟ `f"SELECT ... {var}"` نیست؟

**۱۱. Path traversal** — `vault_sync.py` مسیر فایل می‌سازه. آیا safe هست؟

**۱۲. File handling** — آیا `open()` ها `with` استفاده می‌کنن؟ `np.save` و `np.load` safe هستن؟

**۱۳. Network timeout‌ها** — httpx timeout‌ها مناسب هستن؟ Fugu: 300s، GLM: 45s، web: 15s — منطقی؟

**۱۴. Memory leaks** — autoloop `history` بی‌نهایت رشد می‌کنه. `session_state.results` هم. آیا limit دارن؟

**۱۵. Process safety** — Streamlit rerun تو loop. آیا race condition ممکنه؟

**۱۶. Error recovery** — اگه DB corrupt بشه، اگه ChromaDB fail بشه، اگه vault unreachable باشه — graceful fallback هست؟

### ⚡ ج) کارایی و بهینه‌سازی (۱۷–۲۴)

**۱۷. Graph computation** — `_force_directed_layout` O(n²) است با ۸۰ node = ۶۴۰۰ operations در هر iteration × 150 iteration. آیا باید numpy-vectorized بشه یا کاهش iteration؟

**۱۸. RAG indexing** — `index_vault` هر بار همه‌ی vault رو re-index می‌کنه. incremental indexing؟

**۱۹. SQLite query‌ها** — آیا index‌ها کافی هستن؟ `EXPLAIN QUERY PLAN` چک کن.

**۲۰. ChromaDB singleton** — آیا یکبار ساخته میشه یا هر tab؟

**۲۱. Plotly performance** — گراف ۸۰-node + ۴۴۰-edge سنگینه. آیا `Scattergl` بهتر از `Scatter`؟

**۲۲. Streamlit rerun** — آیا `@st.cache_data` و `@st.cache_resource` استفاده شده؟ کجا باید اضافه بشه؟

**۲۳. numpy در loops** — آیا vectorization ممکنه تو `autoloop` یا `metrics`؟

**۲۴. Lazy loading** — آیا imports سنگین (ChromaDB، embeddings) فقط موقع نیاز load میشن؟

### 🧠 د) هوشمندی و خودمختاری (۲۵–۳۲)

**۲۵. Novelty detection** — آیا `_compute_novelty` z-score درست محاسبه میشه با sample size کوچک؟

**۲۶. Autoloop autonomy** — آیا loop واقعاً خودمختاره؟ چه تصمیمی بدون LLM می‌گیره؟

**۲۷. Learning from experience** — آیا سیستم از reflection‌های قبلی استفاده می‌کنه؟ `load_context_node` رو چک کن.

**۲۸. Meta-research quality** — آیا proposal‌های تولیدشده واقعاً مفید هستن یا generic؟

**۲۹. Web research relevance** — آیا نتایج arXiv/Wikipedia مرتبط هستن با direction فارسی؟ `_optimize_search_query` چقدر خوب ترجمه می‌کنه؟

**۳۰. Self-model accuracy** — آیا `build_self_map` ساختار واقعی رو درست می‌بینه؟ limitation‌ها واقعی هستن؟

**۳۱. Decision making** — `_should_ask_user` چه معیاری داره؟ آیا threshold مناسب هست؟

**۳۲. Pattern deduplication** — آیا الگوهای تکراری ذخیره نمیشن؟ منطق `_save_pattern` رو چک کن.

### 📊 ه) داده و حافظه (۳۳–۳۸)

**۳۳. Rhythm persistence** — آیا `.npy` فایل‌ها قابل recovery هستن؟ corruption detection؟

**۳۴. Obsidian sync** — آیا `create_discovery_note` frontmatter درست تولید می‌کنه؟ wikilink‌ها valid هستن؟

**۳۵. Data provenance** — آیا هر rhythm/experiment منبعش ثبت میشه؟ traceability؟

**۳۶. Memory hierarchy** — آیا short-term (session)، medium-term (DB)، long-term (vault) درست تفکیک شدن؟

**۳۷. Backup strategy** — آیا DB و rhythms قابل backup هستن؟ export/import؟

**۳۸. Data validation** — آیا سری‌های زمانی قبل از ذخیره validate میشن؟ NaN، infinite، short series؟

### 🎨 و) رابط کاربری و تجربه‌ی کاربری (۳۹–۴۴)

**۳۹. صفحه سفید مشکل** — آیا گراف force-directed یا Plotly سنگین باعث hang میشه؟ lazy load یا pagination؟

**۴۰. Feedback loops** — آیا کاربر نتیجه‌ی action‌ها رو سریع می‌بینه؟ loading spinner؟

**۴۱. Mobile responsiveness** — آیا app روی موبایل کار می‌کنه؟ `max-width: 1000px` محدودیت ایجاد می‌کنه؟

**۴۲. Accessibility** — آیا contrast کافی هست؟ RTL درست کار می‌کنه؟ screen reader؟

**۴۳. Error display** — آیا خطاها user-friendly هستن؟ tracebacک خام به کاربر نشون داده نمیشه؟

**۴۴. Navigation** — ۳ تب. آیا کاربر همیشه می‌دونه کجاست؟ breadcrumb؟ status bar؟

### 🔗 ز) اتصال و یکپارچگی (۴۵)

**۴۵. End-to-end flow** — آیا مسیر کامل کار می‌کنه؟
```
direction کاربر → meta_research → web_research → LLM synthesis
→ proposal ذخیره → Obsidian note → wikilink‌گذاری → graph update
→ rhythm‌ها ذخیره → autoloop استفاده → pattern کشف → ذخیره
```

---

## 🎯 خروجیِ مورد انتظار

برای هر دیدگاه که issue پیدا می‌کنی:

1. **فایل:** مسیر دقیق
2. **خط:** شماره یا محدوده
3. **مشکل:** توصیف دقیق
4. **راه‌حل:** code snippet یا action مشخص
5. **اولویت:** critical / high / medium / low
6. **تلاش:** trivial / small / medium / large

سپس تقویت‌ها رو با این ترتیب اجرا کن:
1. First: Critical bugs (صفحه سفید، crash، data loss)
2. Then: High priority (security، stability)
3. Then: Medium (performance، UX)
4. Finally: Low (style، docs)

---

## 📝 قوانین

- ❌ **هیچ کد موجودی رو حذف نکن** مگر اینکه دلیل فنی قوی داشته باشی و تو گزارش ذکر کنی
- ✅ **فقط اضافه کن یا بهتر کن** — backwards-compatible همیشه
- ✅ **تغییر کوچک و متمرکز** — یه چیز رو درست کن، تست کن، بعدی
- ✅ **قبل از تغییر، بخوان** — context رو کامل فهمیده باش
- ✅ **match style کد موجود** — naming، indentation، docstring‌های فارسی
- ✅ **Test after each change** — `python -c "from module import ..."` بعد از هر edit
- ❌ **هیچ تغییری در `4D/` یا `4D-Vault/` یا `core/`** (immutable reference)

---

**شروع کن. از دیدگاه ۱ شروع کن و ترتیب با اولویت.**
