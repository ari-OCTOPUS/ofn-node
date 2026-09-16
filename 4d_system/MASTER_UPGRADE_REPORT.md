# 🧬 گزارش اجرای پرامپت جامع ارتقا — ایده‌یاب شخصی

> اجراشده در ۲۰۲۶-۰۷-۱۱ بر اساس `MASTER_UPGRADE_PROMPT.md`
> روش: ممیزی ۴۵دیدگاهی با ۴۴ agent موازی (۷ گروه + ریشه‌یابی صفحه سفید) + راستی‌آزمایی خصمانه‌ی هر یافته‌ی critical/high + اجرای اصلاحات به ترتیب اولویت + تست بعد از هر تغییر.
> نتیجه‌ی ممیزی: **۱۳۹ یافته → ۵ رد شده در راستی‌آزمایی → ۱۳۴ تأیید** (۳ بحرانی، ۱۹ بالا، ۷۵ متوسط، ۳۷ کم)

---

## 🔴 بحرانی — ریشه‌ی «صفحه سفید» (هر سه رفع شد)

### ۱. باگ نقطه‌ی ورود `run.py` — علت اصلی صفحه سفید ✅
- **فایل:** `run.py:124-128`
- **مشکل:** با `streamlit run run.py`، اسکریپت در هر rerun دوباره اجرا می‌شود ولی پایتون ماژول `ui.app` را cache می‌کند؛ `from ui.app import *` فقط بار اول UI را می‌سازد. **از اجرای دوم به بعد صفر element رندر می‌شود → صفحه‌ی کاملاً سفید، بدون هیچ خطایی در لاگ** (با AppTest بازتولید شد: run1 = UI کامل، run2 = صفر element).
- **راه‌حل:** `importlib.reload(sys.modules["ui.app"])` در rerunهای بعدی.
- **تأیید:** سه اجرای متوالی، هر سه UI کامل (۵ تب، ۰ exception).

### ۲. لوپ بی‌نهایتِ تماس LLM در چت ✅
- **فایل:** `ui/app.py:224-229`
- **مشکل:** `if q := st.text_input(...)` — مقدار ویجت بین rerunها می‌ماند و هرگز پاک نمی‌شود؛ بعد از یک سؤال، هر rerun همان سؤال را دوباره به Fugu (تا ۳۰۰ ثانیه) می‌فرستد + `st.rerun()` → **برای همیشه**. تاریخچه هم هر بار duplicate می‌شد.
- **راه‌حل:** گارد `chat_last_q` + spinner + سقف ۱۰۰ پیام برای حافظه‌ی چت.

### ۳. رندر سنگین همه‌ی تب‌ها در هر rerun ✅
- **فایل:** `ui/app.py` + `ui/tab_graph.py` + `ui/tab_meta.py` + `ui/visuals.py`
- **مشکل:** `st.tabs` بدنه‌ی همه‌ی تب‌ها را در هر اجرا می‌سازد؛ هر گام لوپ (یک rerun کامل + تماس GLM تا ۶۰ ثانیه بدون spinner) دوباره: ۳× `parse_vault_graph()`، layout با پایتون خالص O(n²)×۱۵۰، اسکن AST کل پروژه (`build_self_map`)، و کوئری‌های DB.
- **راه‌حل:**
  - layout با **numpy برداری** شد: ~۲–۴ ثانیه → **۷۸ms** (۸۰ node / ۴۴۰ edge / ۱۵۰ iteration)
  - `@st.cache_data` با امضای vault (تعداد فایل + آخرین mtime) → invalidation خودکار؛ یک parse مشترک برای گراف + آمار + کاوش
  - `build_self_map` هم cache شد (TTL ۱۰ دقیقه)
  - تب‌های سنگین **حین لوپ فعال رندر نمی‌شوند** + spinner با شماره‌ی گام برای هر iteration
- **سنجش:** rerun گرم: **~۱.۰s → ~۰.۱s** (۱۰×)؛ cold: ۳.۴ → ۲.۹s.

---

## 🟠 اولویت بالا (همه اجرا شد)

| # | فایل:خط | مشکل | راه‌حل | تلاش |
|---|---|---|---|---|
| ۴ | `data/rhythm_store.py:115` | `load_rhythm` مسیر را با یک `.parent` اضافه به Desktop resolve می‌کرد → **همه‌ی ریتم‌های ذخیره‌شده None برمی‌گشتند** | مسیر پایه = ریشه‌ی پروژه + fallback با نام فایل؛ با DB واقعی تست شد | trivial |
| ۵ | `.env` + نبود `.gitignore` | کلیدهای واقعی Fugu/GLM داخل ریپوی git والد (`C:/Users/Armin`) بدون محافظت — یک `git add .` = نشت کلید | `.gitignore` ساخته شد (.env، outputs/، __pycache__، لاگ‌ها) | trivial |
| ۶ | `ui/tab_meta.py:89-100` | هر سه دکمه‌ی پیشنهادی با `StreamlitAPIException` کرش می‌کردند (تخصیص به key ویجت بعد از ساختش) | الگوی `meta_direction_pending` — اعمال قبل از ساخت ویجت؛ با کلیک واقعی در AppTest تست شد | small |
| ۷ | `brain/meta_research.py:447` | import تابع ناموجود `get_experiments` → ImportError خاموش، فاز «آزمایش‌های گذشته» کلاً مرده | `query_experiments` (تابع واقعی) | trivial |
| ۸ | `brain/vault_sync.py:179` | frontmatter همه‌ی یادداشت‌های خودکار **YAML نامعتبر** (`#` داخل flow sequence = comment) | تگ‌ها بدون `#` و با quote؛ با `yaml.safe_load` تست شد | small |
| ۹ | `brain/vault_sync.py:118` | `autolink_vault` غیر idempotent — گارد فرم `[[t]]` را چک می‌کرد ولی خروجی همیشه `[[t\|alias]]` بود → هر اجرا ۵۴ لینک تکراری | گارد هر دو فرم؛ dry-run دوم الان **۰ لینک جدید** | trivial |
| ۱۰ | `memory/vectorstore.py:99` | هر پروسه کل vault را با UUID تصادفی دوباره index می‌کرد → ۱۰۰۶ chunk به‌جای ۴۳۰ (کیفیت RAG خراب) | ID قطعی (hash منبع+محتوا) → upsert؛ پاک‌سازی یک‌باره انجام شد: **۱۰۰۶ → ۴۳۰**، re-index دیگر رشد نمی‌کند | small |
| ۱۱ | `brain/nodes.py:81-87` | درس‌های آموخته آخرِ context بودند ولی پایین‌دست فقط `context[:300]` مصرف می‌کند → **حلقه‌ی یادگیری عملاً تزئینی بود** | درس‌ها اول context | trivial |
| ۱۲ | `brain/autoloop.py:326` | سری‌های NaN/inf بدون اعتبارسنجی وارد امتیازدهی می‌شدند (false positive تماشایی) | چک `np.isfinite` قبل از تحلیل در `run_step` و `run` — تست: سری NaN رد می‌شود | small |
| ۱۳ | `brain/graph.py:218-224` | کد ذخیره‌ی گفت‌وگو **بعد از return** — هرگز اجرا نمی‌شد | جابه‌جایی قبل از return | trivial |
| ۱۴ | `llm/router.py:176` | `get_router()` هر بار instance جدید می‌ساخت (singleton نبود) | singleton ماژول‌سطح + `fresh=True` برای تست/mock | trivial |
| ۱۵ | `config/settings.py:52-60` | مقادیر env در لحظه‌ی import منجمد می‌شدند → `load_dotenv(override=True)` بعدی بی‌اثر | `field(default_factory=...)` — تست شد | trivial |
| ۱۶ | `llm/fugu_client.py`, `glm_client.py` | بدنه‌ی خطای HTTP سرور verbatim برگردانده می‌شد (ریسک echo کلید در 401) | `_safe_err`: حذف کلید API از پیام + truncate | trivial |
| ۱۷ | `ui/app.py:24-51` | هیچ RTL‌ای برای UI تماماً فارسی + متن‌های نامرئی در تم تیره (باکس‌های روشن بدون `color`) | CSS راست‌چین برای markdown (کد/pre همچنان LTR) + رنگ متن تیره در باکس‌ها و کارت پروپوزال | small |
| ۱۸ | پروژه (۲۷ نقطه) | `except Exception: pass` بدون هیچ logging (هیچ framework لاگی وجود نداشت) | `setup_logging()` مرکزی (idempotent، فایل `outputs/system.log`) + logger در بدترین نقاط autoloop | medium |

---

## 🟡 متوسط (اجراشده)

- **دو تب مرده وصل شدند** (`tab_laboratory`, `tab_research` — دیدگاه ۱): حالا ۵ تب. باگ تداخل کلید `lab_rho` بین expander تب لوپ و تب آزمایشگاه هم رفع شد (rename به `quick_*`).
- **`use_container_width` منسوخ** → `width='stretch'` در هر ۱۴ نقطه (۴ فایل) — پاک شدن warningهای لاگ.
- **ثابت‌های timeout مرکزی** در settings (`FUGU_TIMEOUT=300`, `GLM_TIMEOUT=60`, `WEB_TIMEOUT=20`، قابل‌تنظیم با env) — ناسازگاری ۱۸۰/۳۰۰ ثانیه‌ی Fugu رفع شد.
- **arXiv از https** (قبلاً plain HTTP).
- **escape محتوای وب نامطمئن** در tab_meta (title/snippet با `unsafe_allow_html` رندر می‌شدند) + اعتبارسنجی scheme لینک.
- **traceback خام به کاربر نمایش داده نمی‌شود** — داخل expander «جزئیات فنی» + ثبت در log.
- **novelty با نمونه‌ی < ۳** دیگر z-score بی‌معنا نمی‌سازد (مقدار خنثی ۰.۵).
- **رشد بی‌نهایت حافظه‌ی چت** → سقف ۱۰۰ پیام.

## ✅ راستی‌آزمایی نهایی

```
▸ import هر ۴۴ ماژول: موفق (۰ خطا)
▸ AppTest run.py: cold 3.4s، warm 0.24s، ۵ تب، ۰ exception در ۳ اجرای متوالی
▸ کلیک دکمه‌ی پیشنهادی: بدون کرش، text_area پر می‌شود
▸ python run.py (self-test در mock): ALL SYSTEMS GO — انکرها، حافظه، RAG، ابزارها، pipeline ۸مرحله‌ای
▸ لوپ ۲ گامه در mock: سالم، NaN رد می‌شود
▸ ChromaDB: 1006→430 chunk، re-index idempotent
▸ YAML frontmatter تولیدی: با yaml.safe_load معتبر
▸ core/ و 4D/ و 4D-Vault دست‌نخورده (فقط پاک‌سازی index خود سیستم)
```

## 📌 پیشنهادهای باقی‌مانده (اجرا نشده — نیازمند تصمیم/رِفکتور بزرگ‌تر)

1. **یکی‌سازی ۳ پشته‌ی LLM** (router + langchain + httpx خام در meta_research/autoloop) پشت یک interface — medium/large، ریسک رفتاری.
2. **مهاجرت schema برای SQLite** (`PRAGMA user_version` + جدول migration) — الان `CREATE TABLE IF NOT EXISTS` تنهاست؛ تغییر ستون = خطای خاموش.
3. **اجرای لوپ در thread پس‌زمینه** (یا `st.fragment`) به‌جای rerun-per-iteration — الان هر گام همچنان render-thread را تا پایان تماس LLM نگه می‌دارد (ولی با spinner و تب‌های سبک).
4. **دوگانگی منطق ذخیره‌ی کشف** بین `ui/app.py` (دکمه‌ی تایید) و `brain/autoloop.py` — انتقال به brain.
5. **معیار dedup الگوها** در `_save_pattern` مقدار MI را با فیلد `delta_self` مقایسه می‌کند — معناشناسی مشکوک ولی رفتار فعلی حفظ شد.
6. **context manager برای همه‌ی اتصال‌های sqlite** (بستن در مسیر خطا) — sweep بزرگ، پیشنهاد: تدریجی.
7. کیفیت ترجمه‌ی جستجوی فارسی→انگلیسی (`_optimize_search_query`) و امتیازدهی کیفیت پروپوزال‌ها.
8. پشتیبان‌گیری/export برای DBها و ریتم‌ها.

---
*پشتیبان کامل کد قبل از تغییرات: `4d_system_backup_pre_upgrade.zip` (در scratchpad جلسه). لاگ سیستم از این پس: `outputs/system.log`*
