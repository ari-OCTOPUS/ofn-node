# 📋 بک‌لاگ پیشنهادی 4d_system — propose-only

> تاریخ: ۲۰۲۶-۰۷-۱۱ · روش: ممیزی دوگانهٔ مستقل (۲ ایجنت + راستی‌آزمایی دستی هر یافته) + مقایسه با استانداردهای multi-agent ۲۰۲۶–۲۰۲۷
> مرجعِ استاندارد: `4D-Vault/07-تحلیل-پژوهش/MAS-Audit-2027-Checklist.md` (Microsoft MARA، control-plane patterns، governance)
> **قاعدهٔ حاکم: هیچ موردی از این سند بدون تأیید مالک اجرا نمی‌شود. همهٔ تغییرها additive و flag-خاموش خواهند بود.**

---

## ✅ آنچه در همین جلسه اصلاح شد (برای تاریخچه)

هر ۱۴ فیکس کوچک، additive، راستی‌آزمایی‌شده با تست (سوییت: ۲۳/۲۳ سبز، ایمپورت ۲۸/۲۸):

| # | فایل | ایراد واقعی | شدت |
|---|---|---|---|
| ۱ | `brain/autoloop.py` | dedup دو کمیتِ بی‌ربط را مقایسه می‌کرد (MI ↔ E_shadow ذخیره‌شده) → کشف واقعی گاهی دور ریخته می‌شد | 🔴 بالا |
| ۲ | `brain/notify.py` | توکن تلگرام در خطای شبکه‌ای به `system.log` نشت می‌کرد | 🔴 بالا |
| ۳ | `run.py` | self-test همیشه exit 0 — شکستِ RAG/LLM/Pipeline بلعیده می‌شد | 🔴 بالا |
| ۴ | `agents/orchestrator.py` + `reporter.py` | شکستِ W1 به «NULL RESULT با اطمینان بالا» تبدیل می‌شد (منفیِ کاذبِ مطمئن) | 🔴 بالا |
| ۵ | `brain/graph.py` | `delta_self` کپیِ `e_shadow` ذخیره می‌شد → آمار DB بی‌معنا | 🔴 بالا |
| ۶ | `brain/frontier.py` | `abs()` روی کشیدگی → باند زیرگوسی دست‌نیافتنی، محورِ تنوعِ مرزِ دانش نصفه | 🟠 متوسط |
| ۷ | `ui/tab_meta.py` | خروجی LLM بدون escape داخل `unsafe_allow_html` (تزریق HTML) | 🟠 متوسط |
| ۸ | `brain/housekeeping.py` | `decision_packets.jsonl` و `autonomous_ideas.md` بی‌سقف (رشد ابدی) → `trim_textfile` با آرشیو | 🟠 متوسط |
| ۹ | `memory/store.py` | نبود WAL/busy_timeout (خطر database is locked بین Streamlit و CLI) + ایندکس‌های timestamp | 🟠 متوسط |
| ۱۰ | `data/synthetic.py` | نویزِ مشاهدهٔ `ar1_plus_noise` کپیِ مقیاس‌شدهٔ نوآوری‌های سیگنال بود (نقض مدل SOG) — corr از ~۰٫۷ به ~۰ | 🟠 متوسط (علمی) |
| ۱۱ | `data/real_api.py` | `log(0)` روی قیمت‌های Yahoo بدون گارد | 🟡 کم |
| ۱۲ | `core/scores.py` | پارامتر منحط → `math domain error` بی‌پیام | 🟡 کم |
| ۱۳ | `brain/vault_sync.py` | مسیر vault قفل به `Desktop` (شکننده با OneDrive) → env override `VAULT_DIR` | 🟡 کم |
| ۱۴ | `brain/web_research.py` | خطاها با `print` گم می‌شدند → logger | 🟡 کم |

اجرای تست روی ماشین خودت: `python tests/run_all.py` (یا `pytest tests/`).

---

## 🔍 مقایسهٔ ۲۷ جنبه با استانداردها و الگوهای قوی‌تر

| # | جنبه | وضع فعلی | استاندارد ۲۰۲۷ / الگوی مرجع | شکاف |
|---|---|---|---|---|
| ۱ | لایه‌بندی معماری | core/data/brain/agents/ui تفکیک تمیز | MARA: ingestion→cognition→memory→governance | ✅ کم |
| ۲ | Agent registry | نقش‌ها در کد (W0–W3) ولی registry رسمی نیست | registry با id/owner/permission/status | 🟠 متوسط |
| ۳ | Orchestration | LangGraph + دروازهٔ W0 (و حالا W1) | حلقهٔ reflect کران‌دار + خروج تمیز | 🟠 (مورد B1) |
| ۴ | ایمنی خودتغییری | guardrails fail-closed، فقط strategy.json، clamp + rate-limit | change-contract با تست قبل از اعمال — دارد ✅ | ✅ کم |
| ۵ | Human-in-the-loop | دروازهٔ anchor-violation انسانی؛ evolve خودکار با اطلاعِ پسینی | promotion-gate اختیاری (تو خودمختاری را ترجیح داده‌ای) | 🟡 (مورد B9، فلگ خاموش) |
| ۶ | حافظهٔ اپیزودیک | SQLite + archive جدول‌ها | WAL ✅ (این جلسه) · migration ندارد | 🟠 (مورد B6) |
| ۷ | حافظهٔ معنایی (RAG) | Chroma + ID قطعی | ID مستقل از ایندکسِ سراسری + حذفِ کهنه‌ها | 🟠 (مورد B3) |
| ۸ | هزینه | APIهای رایگان + Ollama محلی + mock mode | $0 پایه — عالی | ✅ |
| ۹ | سرعت UI | cache امضادار + numpy layout (~۰٫۱s گرم) | لوپ در fragment/thread جدا از render | 🟠 (مورد B8) |
| ۱۰ | UX | RTL + ۵ تب + spinner گام‌دار | جداسازی مسیر ذخیرهٔ UI/موتور | 🟠 (مورد B2) |
| ۱۱ | Observability | logger مرکزی + events + heartbeat | خطاهای web_research هم به log ✅ (این جلسه) | ✅ کم |
| ۱۲ | تست/CI | **این جلسه ساخته شد:** ۲۳ تست + exit-code واقعی self-test | CI خودکار (pre-commit / task scheduler) | 🟠 (مورد B10) |
| ۱۳ | بازتولیدپذیری | seedها در verifier/self-test کنترل‌شده | `simulate()` پیش‌فرض seed=None | 🟡 (مورد B14) |
| ۱۴ | صحت آماری | استقلال نویز-سیگنال ✅ (این جلسه) · گارد NaN ✅ | تخمین‌گر MI فقط خطی-گاوسی است (برای آشوب حساس نیست) | 🟡 (مورد B12) |
| ۱۵ | Exploration/تنوع | MAP-Elites (frontier) — الگوی quality-diversity معتبر | هر دو محور حالا کار می‌کنند ✅ (این جلسه) | ✅ |
| ۱۶ | Novelty/dedup | z-score + dedup هم‌جنس ✅ (این جلسه) | ذخیرهٔ MI در schema برای dedup دقیق‌تر | 🟡 (مورد B6) |
| ۱۷ | خودمدل | `self_model` با AST — فقط‌خواندنی، امن | گزارش خودمدل → registry رسمی | 🟡 |
| ۱۸ | فراشناخت | `ReflectionGate` طراحی شده ولی **وصل نیست** | حلقهٔ بازتاب کران‌دار متصل | 🟠 (مورد B1) |
| ۱۹ | Secretها | `.gitignore` ✅ · نشت لاگ بسته شد ✅ (این جلسه) · `_safe_err` ✅ | اسکن دوره‌ای secret در outputs | 🟡 |
| ۲۰ | تحمل خطای شبکه | timeout همه‌جا ✅ ولی retry/backoff ندارد | ۲–۳ تلاش با backoff | 🟠 (مورد B7) |
| ۲۱ | یکپارچگی DB | WAL+busy_timeout+index ✅ (این جلسه) | try/finally همهٔ اتصال‌ها + migration | 🟠 (موارد B5,B6) |
| ۲۲ | مهار رشد داده | housekeeping کامل شد ✅ (این جلسه — ۶ سقف) | ✅ | ✅ |
| ۲۳ | امنیت UI | escape خروجی LLM ✅ (این جلسه) + escape وب از قبل | ✅ | ✅ |
| ۲۴ | Vendor lock-in | ۳ ارائه‌دهنده + mock — جابه‌جایی آسان | ۳ پشتهٔ LLM موازی → یک interface | 🟠 (مورد B11) |
| ۲۵ | Alerting | Telegram + صف پایدار + throttle | ✅ (نشت بسته شد) | ✅ |
| ۲۶ | نسخه‌بندی | داخل ریپوی والدِ خانگی — تاریخچهٔ مستقل ندارد | git مستقل + تگ قبل از هر evolve | 🟠 (مورد B10) |
| ۲۷ | داده‌ی fallback | fallback مصنوعی با seed ثابت وارد آمار می‌شود | برچسب‌گذاری و حذف از aggregateها | 🟠 (مورد B4) |

---

## 🗂 بک‌لاگ — وضعیت: **همه اجرا شد** (دستور مالک ۲۰۲۶-۰۷-۱۱: «همرو کامل کن»)

> سوییت پس از اجرا: **۶۳/۶۳ سبز** · ایمپورت ۲۹/۲۹ · فلگ‌های رفتاریِ جدید همه **خاموش**اند.

| # | وضعیت | نحوه‌ی اجرا / فلگ |
|---|---|---|
| B1 | ✅ | گیتِ بازتاب وصل شد (`patterns.reflect_should_revise` + شمارنده در state/nodes) — فلگ `REFLECT_GATE=1`، سقف `REFLECT_MAX` (پیش‌فرض ۳). گاردِ GraphRecursionError در هر دو مسیرِ graph **بی‌قیدوشرط** فعال (کرش → state با error). |
| B2 | ✅ | دکمه‌ی «تایید و ذخیره» حالا از `engine._save_pattern` می‌گذرد — dedup/تگ/MI یکسان با موتور. |
| B3 | ✅ | `memory/chunk_ids.py` (ID مستقل از ترتیب) + حذفِ per-source قبل از افزودن در `index_vault` با fallback امن. IDهای طرحِ قدیم در اولین ایندکس پاک می‌شوند. |
| B4 | ✅ | throttle per-source (`_throttled`) + فاصله‌ی سراسریِ ۱ ثانیه؛ fallback با seed مشتق از reason+زمان و `info.fallback=True`. |
| B5 | ✅ **کامل** | `_conn`/`_rconn` context-manager + try/finally روی **همه‌ی** توابعِ store (۸) و research_store (۲۰) و rhythm_store (۴، +پاک‌سازیِ npy یتیم) و nodes/auto_experiment/research_agenda؛ حتی `_ensure_db`/`_ensure_research_tables`. هیچ اتصالِ بی‌محافظی نماند. |
| B6 | ✅ | `PRAGMA user_version=2` + ستونِ `temporal_mi` (CREATE برای DB نو، ALTER برای قدیمی) + dedup دومرحله‌ای MI-اول. |
| B7 | ✅ | `_requests_get` با ۳ تلاش/backoff نمایی روی هر ۵ fetcher (env: `NET_RETRY_ATTEMPTS`). |
| B8 | ✅ | `brain/bg_loop.py` (خالص، تست‌دار) + سیمِ ui/app.py — فلگ `LOOP_BG_THREAD=1`؛ خاموش = مسیرِ قبلی بایت‌به‌بایت. |
| B9 | ✅ | `evolve(apply=False)` + فلگ `EVOLVE_REQUIRE_APPROVAL=1` → پیشنهاد در `strategy_proposed.json` + رویدادِ approval.required + پکتِ تلگرام. پیش‌فرض: خاموش (خودمختار، انتخابِ خودت). |
| B10 | ✅ | `scripts/init_git.bat` + hook `scripts/hooks/pre-commit` (سوییت قرمز = commit مسدود). **باید خودت یک‌بار روی ویندوز اجرایش کنی.** |
| B11 | ✅ (فاز ۱: shadow + ابزارِ تصمیمِ فاز ۲) | جمع‌آوری: `llm/shadow_compare.py` + `scripts\run_shadow_compare.bat`. تحلیل/تصمیم: `llm/shadow_analyze.py` + یک‌کلیک `scripts\run_shadow_analyze.bat` — کلِ `outputs/llm_shadow.jsonl`ِ تجمیع‌شده را می‌خواند و طبقِ معیارِ زیر یک حکم (`decide()`) صادر می‌کند؛ فقط-خواندنی، هیچ سوئیچِ زنده/ویرایشِ سورس/فلگی. **معیارِ تصمیمِ فاز ۲** (پس از ≥۳۰ رکورد): اگر یک پشته error_rate و تأخیرِ میانگینِ **هر دو** بدتر دارد و mean_similarity>۰٫۷ → `MIGRATE` به برنده پشتِ فلگ؛ اگر similarity<۰٫۵ → `HOLD_INVESTIGATE_DIVERGENCE` (سوییچ ممنوع)؛ بندِ خاکستریِ [۰٫۵،۰٫۷] و تساوی/split → `HOLD_*` (بدونِ سوییچ). احکام: INSUFFICIENT_DATA · NO_SIMILARITY_DATA · HOLD_INVESTIGATE_DIVERGENCE · HOLD_SIMILARITY_INCONCLUSIVE · HOLD_NO_CLEAR_LOSER · MIGRATE. |
| B12 | ✅ | `core/nonlinear_mi.py` (باندهای هم‌احتمال + Miller–Madow) — روی آشوب: MI=۲٫۰۳ در برابرِ ۰٫۱۵ خطی (۱۳×). فلگِ detector: `NONLINEAR_MI=1` کلیدِ `mi_nonlinear` را می‌افزاید. |
| B13 | ✅ | scipy از requirements حذف؛ beautifulsoup4 صریح شد. |
| B14 | ✅ | `simulate(seed=0)` پیش‌فرضِ بازتولیدپذیر + گاردِ مخرجِ `var_e` در model. |
| B15 | ✅ | `brain/backup.py` — snapshot روزانه‌ی DB (با sqlite backup API) + strategy/frontier، روتیشنِ ۵تایی؛ در housekeeping سیم شد. env: `HK_BACKUP`, `HK_BACKUP_KEEP`. |

### فلگ‌های جدید (همه پیش‌فرض خاموش مگر ذکر شود)
`REFLECT_GATE` · `REFLECT_MAX=3` · `LOOP_BG_THREAD` · `EVOLVE_REQUIRE_APPROVAL` · `NONLINEAR_MI` · `NET_RETRY_ATTEMPTS=3` (فعال) · `HK_BACKUP=1` (فعال — فقط فایل می‌سازد، رفتار را عوض نمی‌کند) · `HK_BACKUP_KEEP=5` · `HK_MAX_PACKET_LINES` · `HK_MAX_IDEA_LINES`

---

## 🗂 بک‌لاگِ اولیه (برای تاریخچه — متنِ پیشنهادیِ پیش از اجرا)

| # | پیشنهاد | چرا | ریسک | تلاش | تست جلوگیری از خرابی |
|---|---|---|---|---|---|
| B1 | وصل‌کردن `ReflectionGate` به `graph.py` (سقف بازتاب در state) | حلقهٔ report↔reflect فقط با recursion-limit (خطای ناگرفته) می‌ایستد؛ ابزارش ساخته شده و بلااستفاده است | کم (flag خاموش) | S | تست حلقه با reflect اجباری REVISE |
| B2 | مسیر ذخیرهٔ دکمهٔ تأیید UI ← موتور (`engine._save_pattern`) | کدِ مرده و واگرا: تگ‌ها/ریتم/یادداشت با مسیر اصلی فرق دارد؛ با هر تغییر آستانه فعال می‌شود | کم | S | تست برابری خروجی دو مسیر |
| B3 | vectorstore: ID پایدار per-source + حذف chunkهای کهنهٔ همان source | ویرایش هر یادداشت vault → chunkهای یتیم و نتایج RAG کهنه، رشد بی‌پایان chroma | متوسط (rebuild یک‌باره) | M | ایندکس دوباره روی vault آزمایشی: شمارش ثابت |
| B4 | real_api: throttle per-source + seed متغیر fallback + پرچم `synthetic_fallback` در aggregateها | الان یک سریِ مصنوعیِ یکسان بارها وارد آمار «داده‌ی واقعی» می‌شود | متوسط (نرخ تماس API بالا می‌رود — سقف کلی بماند) | M | تست: دو source پشت‌سرهم، هر دو واقعی |
| B5 | sweep تدریجی `try/finally` روی همهٔ اتصال‌های sqlite (اولویت: research_store) | نشت اتصال در مسیر خطا؛ با WAL کم‌اثرتر ولی همچنان واقعی | کم | M | تست خطای وسط تراکنش |
| B6 | مهاجرت schema با `PRAGMA user_version` + ستون `temporal_mi` در patterns | تغییر ستون الان خطای خاموش است؛ MI هم persist نمی‌شود (dedup را محدود می‌کند) | متوسط | M | migration روی کپی DB واقعی |
| B7 | retry/backoff (۲–۳ تلاش) روی همهٔ تماس‌های شبکه | یک blip → جایگزینی خاموش با دادهٔ مصنوعی | کم | S | mock شکست اول، موفقیت دوم |
| B8 | اجرای لوپ در `st.fragment`/thread جدا | هر گام render-thread را تا پایان تماس LLM نگه می‌دارد | متوسط-بالا (state هم‌روند) | L | AppTest سه rerun زیر لوپ فعال |
| B9 | فلگ اختیاری `EVOLVE_REQUIRE_APPROVAL` (پیش‌فرض: خاموش = رفتار فعلی) | تو خودمختاری را انتخاب کرده‌ای — این فقط دستگیرهٔ اختیاری برای آینده است، نه fail-closed | صفر (فلگ خاموش) | S | تست هر دو حالت فلگ |
| B10 | `git init` مستقل برای 4d_system + اجرای `tests/run_all.py` قبل از هر commit/evolve | تاریخچهٔ مستقل + تور ایمنی خودکار؛ الان گیر ریپوی والد خانگی است | کم | S | خود سوییت |
| B11 | یکی‌سازی ۳ پشتهٔ LLM (router/langchain/httpx خام) پشت یک interface | سه مسیر خطا/timeout/log متفاوت | بالا (رفتاری) — **فقط با shadow-run** | L | مقایسهٔ خروجی دو پشته روی ۲۰ پرامپت ثابت |
| B12 | تخمین‌گر MI مکمل غیرخطی (مثلاً KSG یا binned MI) کنار خطی-گاوسی | logistic map ساختار دارد ولی MI خطی نمی‌بیندش — نقطهٔ کور علمی | متوسط | M | سری آشوبی: MI غیرخطی > 0 |
| B13 | حذف `scipy` از requirements (هیچ importی ندارد) یا استفادهٔ واقعی | وابستگی سنگین بلااستفاده = هزینهٔ نصب/سطح حمله | صفر | XS | نصب تمیز + سوییت |
| B14 | پیش‌فرض seed در `simulate()` (`seed=0`) | MC غیرقابل‌بازتولید وقتی caller فراموش کند | کم (تغییر پیش‌فرض) | XS | تست بازتولید |
| B15 | export/backup دوره‌ای DBها و ریتم‌ها (در housekeeping) | دادهٔ پژوهشی تک‌نسخه است | کم | S | restore روی کپی |

**خط قرمزها (تغییرناپذیر):** `4D/` فقط‌خواندنی می‌ماند · نوشتن در vault فقط additive · هیچ فلگی بدون تأیید تو روشن نمی‌شود · هیچ بازنویسیِ کامل ساختار.

---

## 📝 یادداشت فنی جلسه

- پوشهٔ `tests/_shadow_tails/` زیرساختِ دورزدنِ یک باگِ محیطی است (mount ایجنت اندازهٔ کهنهٔ فایل‌های رشدکرده را cache می‌کند). روی ویندوزِ خودت لازم نیست — مستقیم `python tests/run_all.py` را اجرا کن.
- یک خرابیِ historicalِ متن (حروف چینی وسط توضیح فارسی در `data/synthetic.py`) هم در همین جلسه اصلاح شد.
