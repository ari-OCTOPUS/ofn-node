# نگاشت چک‌لیست ۷گانه‌ی فیوژن ۲۰۲۶ → پیاده‌سازی (فاز ۱ MVP)

وضعیت: ✅ پیاده‌شده و تست‌شده · 🟡 پیاده‌ی پایه (قابل ارتقا در فاز ۲/۳) · ⬜ هنوز نه

هدف فاز ۱ این بود که حداقل ۴ مورد را «واقعی و قابل‌اجرا» پیاده کنیم. در عمل ۴ مورد کامل
و ۲ مورد به‌صورت پایه پیاده شد (مورد ۵ و ۷ پایه). جزئیات:

---

## ✅ ۱) متابولیسم → بودجه و حسابداری منابع
**کجا:** `config.py`، `src/budget.py`، `src/llm.py`
- هر فراخوانی مدل توکن مصرفی را برمی‌گرداند و در `BudgetLedger` ثبت می‌شود (cost-accounting لایه‌ای).
- سقف per-agent و سقف کل (`PER_AGENT_BUDGET_USD`, `GLOBAL_BUDGET_USD`) + سقف تعداد فراخوانی (`MAX_CALLS_PER_AGENT`) = همان rate-limit.
- **قطع خودکار:** اگر هزینه از سقف عبور کند، `BudgetExceeded` پرتاب و کل اجرا متوقف می‌شود (budget hook).
- **تست:** `run_tests.py` → «ثبت هزینه» و «قطع خودکار بودجه». سناریوی واقعی ۴ در README.

## ✅ ۲) مالکیت گرادیان → کنترل انسانی و کلید قطع
**کجا:** `src/killswitch.py`، `src/hitl.py`، `src/agents.py` (Supervisor)
- **kill-switch دوگانه:** نرم‌افزاری (`ks.trip`) و انسانیِ بیرونی (ساختن فایل `logs/STOP`). قبل از هر گام `ks.check()` اجرا می‌شود = circuit breaker.
- **HITL approval gate:** اقدام حساس `finalize` بدون تأیید انسان اجرا نمی‌شود.
- **Supervisor** قبل از نهایی‌سازی مجوز صادر/رد می‌کند.
- **تست:** kill-switch (۲ تست) + HITL (۲ تست) سبز. سناریوهای ۲ و ۳ در README.

## ✅ ۳) شفافیت مکث → رصد، ممیزی، مکث‌وبازرسی
**کجا:** `src/tracing.py`
- هر رویداد (`agent_call`, `tool_call`, `hitl_request`, `halt`, ...) در `logs/audit.jsonl` ثبت و هم‌زمان روی کنسول چاپ می‌شود (شفافیت لحظه‌ای).
- **audit log غیرقابل‌دستکاری:** زنجیره‌ی هش (هر رکورد به هش رکورد قبلی گره می‌خورد). `verify_chain()` دستکاری را لو می‌دهد.
- نقطه‌ی مکث (`HITLGate`) همان «inspect & pause» است.
- **تست:** «صحت زنجیره‌ی audit» (دستکاری یک خط → زنجیره می‌شکند).
- **فاز ۲ افزوده شد:** داشبورد محلی `dashboard.py` (هزینه‌ی هر ایجنت + خط‌زمانی + وضعیت اجراها) و قلاب اختیاری Langfuse (`src/langfuse_sink.py`) برای tracing ابری.

## ✅ ۴) گذرگاه ابزار + least-privilege → دسترسی مقیّد
**کجا:** `src/tools.py`، `config.AGENT_ALLOWED_TOOLS`
- همه‌ی ابزارها فقط از `ToolGateway` عبور می‌کنند؛ هر ایجنت فقط به ابزارهای scoped خودش دسترسی دارد.
- درخواست ابزار خارج از حوزه → `ToolPermissionError` (هیچ کنش بی‌مجوز).
- هر `tool_call` به ایجنت منشأ گره می‌خورد (no anonymous reach).
- **تست:** «least-privilege رد ابزار» (Analyst نمی‌تواند جستجو کند) + «ابزار مجاز».
- 🟡 ارتقا فاز ۲: گذرگاه واقعی MCP + policy layer + scoped API keys + sandbox برای اجرای کد.

## 🟡 ۵) بدون نقطه‌ی تصرف واحد → تنوع و تفکیک
**کجا:** `src/agents.py`، `src/orchestrator.py`
- **separation of duties** پیاده شد: سه نقش جدا با ابزار جدا؛ هیچ ایجنتی کنترل کامل ندارد.
- بودجه و kill-switch مستقل از ایجنت‌ها می‌توانند اجرا را قطع کنند (چند مسیر توقف مستقل).
- ⬜ باقی‌مانده: تنوع provider/مدل (multi-provider) و چند داورِ هم‌زمان (multi-judge) برای حذف تک‌نقطه‌ی تصمیم. فعلاً تک‌مدل.

## 🟡 ۶) قید متقابل → تقسیم نقش و چک‌وبالانس
**کجا:** `src/agents.py` (Supervisor/worker)، `src/hitl.py`
- الگوی **supervisor/worker** با راستی‌آزمایی متقابل: Supervisor خروجی Analyst را تأیید/رد می‌کند.
- **انسان همیشه بالاتر از ایجنت** (override در دروازه‌ی HITL) = escalation اجباری در آستانه.
- 🟡 ارتقا فاز ۳: capability‌های مجاز با نظارت متناظر، و escalation چندسطحی.

## 🟡 ۷) مانیتورینگ، شبیه‌سازی شکست، eval → آزمون‌پذیری
**کجا:** `src/guardrails.py`، `run_tests.py`، سناریوهای README
- **guardrail خروجی** پایه: ادعای نامطمئنِ بدون هشدار را رد می‌کند.
- **شبیه‌سازی شکست:** سناریوی «بودجه‌ی بیش از حد» و «STOP بیرونی» عملاً تست شکست‌اند.
- **فاز ۲:** داشبورد `dashboard.py` مانیتورینگ بصریِ هزینه/فعالیت را اضافه کرد.
- ⬜ باقی‌مانده: eval-harness خودکار (promptfoo/DeepEval) + گاردریل جدی‌تر (NeMo/Guardrails AI) + هشدار آنومالیِ خودکار هزینه/مجوز. هدف فاز ۳.

---

### جمع‌بندی
| مورد | وضعیت |
|---|---|
| ۱ بودجه/هزینه | ✅ کامل |
| ۲ HITL + kill-switch | ✅ کامل |
| ۳ شفافیت/audit | ✅ کامل |
| ۴ least-privilege | ✅ کامل |
| ۵ تنوع/تفکیک | ✅ کامل (پنل چندداور + رجیستری provider) |
| ۶ چک‌وبالانس | ✅ کامل (پنل + escalation + گاردریل پرامپت) |
| ۷ eval/guardrail | ✅ کامل (eval-harness + خوداپدیتی + سناریوی شکست) |

**هر ۷ مورد پیاده و تست شد (۱۷ تست سبز: ۹ فاز۱ + ۸ فاز۳).**

---

## فاز ۴ — تنوع و حذف تک‌نقطه‌ی تصمیم (مورد ۵، انجام‌شده)
**کجا:** `src/panel.py`، `src/providers.py`، `config.JUDGES`/`PANEL_QUORUM`

- **پنل چندداورِ مستقل** جای ناظرِ تنها را گرفت: سه داور با نگرش‌های متفاوت (strict/lenient/balanced) رأی می‌دهند؛ تأیید نیازمند **حد نصاب** (۲ از ۳) است — **هیچ داوری به‌تنهایی نمی‌تواند تأیید کند** (پرهیز از تک‌نقطه‌ی تصمیم).
- **رجیستری provider** (`providers.py`): داوران به‌صورت round-robin بین providerها پخش می‌شوند؛ معماری آماده‌ی چند provider واقعی (Anthropic + …) است. در حالت MOCK سه provider مستقل برای تنوع.
- **separation of duties:** Researcher/Analyst/داوران نقش و ابزارِ جدا دارند؛ بودجه و kill-switch مستقل می‌توانند قطع کنند.
- **escalation (مورد ۶):** اگر آرا نصفه‌نیمه شد (نه تأیید، نه ردِ کامل) → ارجاع به انسان از طریق HITL.
- هر رأی و تصمیمِ پنل در audit log ثبت می‌شود.

---

## فاز ۳ — آزمون‌پذیری، ایمن‌سازی و خوداپدیتی (انجام‌شده)
**کجا:** `src/evals.py`، `src/prompt_store.py`، `src/optimizer.py`، `self_update.py`، `test_phase3.py`

- **eval-harness (مورد ۷):** `score_prompt` کیفیت هر system prompt را با rubric نقش می‌سنجد؛ `evaluate_findings` خروجی بی‌منبع را به‌عنوان شکست لو می‌دهد.
- **سناریوهای شکست تست‌شده:** اطلاعات بی‌منبع، پرامپتِ injection، و تنزل نمره — همه در `test_phase3.py` (۵ تست سبز).
- **سیستم خوداپدیتیِ پرامپت (اعمال خودکار + rollback):** `self_update.py` با Optimizer نسخه‌ی بهترِ پرامپت را پیشنهاد و **خودکار اعمال** می‌کند، اما:
  - فقط اگر نمره‌ی eval بالاتر برود نگه می‌دارد؛ وگرنه **rollback خودکار** (سیستم نمی‌تواند خودش را بدتر کند).
  - **گاردریل امنیتی** پرامپتی که نقش را حذف کند یا injection باشد را رد می‌کند (مورد ۲/۷).
  - **kill-switch** و سقف دور و **تاریخچه‌ی کامل نسخه‌ها** برای بازگشت (مورد ۲/۳).
  - هر تغییر در audit log ثبت می‌شود (مورد ۳).

### وضعیت نهایی: ۶ مورد از ۷ کامل
تنها باقی‌مانده: مورد ۵ (تنوع provider/multi-judge) که نیازمند چند مدل/کلید است — هدف فاز بعد.

---

## فاز ۵ — IGK: از انطباقِ رفتاری به انطباقِ ساختاری
**کجا:** `igk/` (`kernel.py` · `daemon.py` · `client.py`) + اتصال در `src/orchestrator.py`

کانن (`v5-IGK`) می‌گوید کنترل‌ها باید **بیرونِ بسترِ ایجنت و مکانیکاً اجباری** باشند، نه cooperative. این فاز همان گذار را انجام داد. نگاشتِ ۴ معیار IGK:

| معیار | قبلاً (رفتاری) | حالا (ساختاری) | تست |
|---|---|---|---|
| **kill بیرونی** | `ks.check()` درون‌process؛ fail-open اگر صدا نشود | کرنلِ process-جدا؛ `_kguard`+permitِ **fail-closed**؛ STOP→هیچ کنش | redteam ۲ · integ ۲ |
| **grounding held-out** | فقط کلیدواژه‌ی پرامپت (internal-consistency) | گیتِ grounding-validity روی held-outِ ساختاریافته؛ contradicted/unverifiable رد | grounding ۵تست · failures الف |
| **audit امضا** | hash-chain بدونِ کلید (جعل‌پذیر) | HMAC با کلیدِ درون‌کرنل (`chmod 600`)؛ جعل بدونِ کلید ناممکن | redteam ۱ |
| **self_update قفل** | denylistِ نرم | شعاعِ اثر محدود به متنِ پرامپت + پروتکلِ کرنل هیچ verbِ تغییرِ invariant ندارد | redteam ۴ · failures ب |

**سناریوهای شکستِ واقعی (۳ مورد، `test_failures.py`):** الف) Researcherِ بی‌منبع/غلط (eval+guardrail+ground می‌گیرند)؛ ب) خوداپدیتیِ خنثی‌کننده‌ی محافظ (`validate_prompt` رد)؛ ج) replay/permitِ جعلی (کرنل رد).

**تست‌ها (همه سبز):** `run_tests.py` ۹ · `test_phase3.py` ۸ · `igk/test_redteam.py` ۸ · `igk/test_grounding.py` ۵ · `test_failures.py` ۷ · `test_igk_integration.py` ۳ → **۴۰ سبز**.

### چه چیزی هنوز باز است (صادقانه — جزئیات در `fusion-safety/THREAT-MODEL.md`)
- **ایزولاسیون در سطحِ process است، نه OS-user/TEE:** روی یک کاربر، `.kernel_key` خواندنی است. رفعِ واقعی = daemon زیر کاربرِ سیستمیِ جدا.
- **حالت LIVE اجرا نشده:** نیازمندِ کلیدِ Anthropic در `.env` توست (sandbox شبکه ندارد). با کلید، `MODEL`/cost-accounting واقعی فعال می‌شود.
- **گراندینگ هیوریستیکِ ساختاریافته است،** نه retrieval/NLI؛ و `held_out.json` نمونه است نه منبعِ واقعیِ زنده.
- **مورد ۵** (multi-provider واقعی) همچنان نیازمندِ چند کلید است.
