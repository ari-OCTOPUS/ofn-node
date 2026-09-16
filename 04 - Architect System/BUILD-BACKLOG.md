---
tags: [backlog, build, milestones, proposal, architect]
created: 2026-07-04
status: proposal — پلنِ ساخت (چیزی ساخته نشد)
spine: survival
constraint: "تا rotation → فقط کدِ لوکالِ read-only، بدونِ اتصالِ مالی/بیرونی، تست در MOCK"
sources: "[[SURVIVAL-ARCHITECTURE]], [[LAPTOP-RUNTIME]], PHASE1-INVENTORY.md, [[GAPS]]"
---

# BUILD BACKLOG — از حفره تا کدِ اجراشده (M0..M8)

> هر milestone **مستقل** است: فقط همان تکه ساخته می‌شود و می‌ایستد. هر کدام نگاشت به **فایلِ واقعی** + **تعریفِ تمام‌شده (DoD)** + **تست** + **پرامپتِ آمادهٔ کدنویس** (کدکس/کلودکد).
>
> **قیدِ سراسری (تا rotationِ G-01):** فقط کدِ لوکال، read-only، **بدونِ اتصالِ مالی/بیرونی**. همه در **MOCK** تست می‌شوند — نه کلیدِ واقعی، نه شبکه.
>
> **خارج از scope این backlog (عمداً):** چرخشِ کلید (G-01، دستِ اپراتور) · اثباتِ LIVEِ حلقه (G-26، بعد از rotation و held-out واقعی) · L1-توزیع‌شده و holobiont-ISR (over-engineering فعلی — SURVIVAL §۶).

---

## نقشهٔ کلی

| M | عنوان | فایل هدف | حفره | ریسک | وابستگی |
|---|-------|----------|------|------|---------|
| **M0** | سبز کردنِ مجدد سوئیت | `fusion-mvp/src/evals.py` + `test_phase3.py` | N-01 | 🟢 خیلی کم | — |
| **M1** | بستنِ fallbackِ بی‌صدای IGK | `fusion-mvp/src/orchestrator.py` + `config.py` | کارت +۱ / G-10§3 | 🟢 کم | M0 |
| **M2** | EffectorGateِ یکپارچه | `fusion-mvp/src/orchestrator.py` + `src/tools.py` | G-10§1-2 | 🟡 متوسط | M1 |
| **M3** | تنزلِ امن به‌جای جعل | `fusion-mvp/src/llm.py` + `config.py` | کلاس شبکه/API | 🟢 کم | — |
| **M4** | گاردِ بودجهٔ سراسری + دیسک | `langar/budget.py` + call-sites | G-06 | 🟡 متوسط | — |
| **M5** | بکاپِ off-box محلی + restore تستی | `_ops/backup/` (نو) | BACKLOG-10 | 🟢 کم | — |
| **M6** | سیم‌کشیِ observability | `langar/observability/tracer.py` | G-08 | 🟢 کم | — |
| **M7** | پنلِ واقعی به‌جای نمایشی | `fusion-mvp/src/panel.py` | G-15 | 🟡 متوسط | M0 |
| **M8** | L1.5 stress-gated promotion | `fusion-mvp/self_update.py` + `config.py` | L1.5 نیمه | 🟡 متوسط | M6 (سیگنال) |

> **چرا M0 عوض شد؟** قبلاً گفتم «M0 = بستنِ fallback + EffectorGate». اما قیدِ فاز ۴ = «اولین milestone بی‌ریسک‌ترین». سوئیتِ قرمز (۳۹/۴۰) نباید مبنای جراحیِ ایمنی باشد؛ پس **M0 = سبز کردنِ سوئیت** (pre-flight)، و fallback/EffectorGate شدند M1/M2 (هنوز خیلی زودند).

---

## M0 — سبز کردنِ مجدد سوئیت (رفعِ regression N-01)

- **حفره:** گیتِ allowlistِ G-26 پرامپتِ بی‌خطرِ «…و خوب کار می‌کنی» را رد می‌کند → `t_prompt_guardrail` قرمز؛ ادعای «همه سبز» stale است.
- **فایل:** `fusion-mvp/src/evals.py` (`ALLOWED_SENTENCE_PATTERNS`) و/یا `fusion-mvp/test_phase3.py`.
- **DoD:** `python test_phase3.py` → ۸/۸؛ کلِ سوئیت **۴۰/۴۰**؛ و injection (`ignore previous`) و حذفِ نقش همچنان رد می‌شوند.
- **تست:** موردِ موجود سبز شود + یک assert که ثابت کند injection هنوز رد است (رگرسیونِ امنیتی نگیریم).

```
پرامپتِ کدنویس — M0:
فقط همین تکه را بساز و بایست. کدِ لوکال، تست در MOCK، هیچ فایلِ دیگری تغییر نکند.
مشکل: در fusion-mvp، تابعِ validate_prompt_allowlist در src/evals.py پرامپتِ بی‌خطرِ
«تو ایجنت Researcher هستی و خوب کار می‌کنی» را رد می‌کند و test_phase3.py::t_prompt_guardrail را قرمز کرده.
کار: یک الگوی allowlistِ محدود برای «توصیفِ خنثیِ کیفیت» اضافه کن که جمله‌های بی‌خطر را عبور دهد
ولی injection («ignore previous»/«نادیده بگیر»/خنثی‌سازیِ محافظ) و حذفِ نشانهٔ نقش را همچنان رد کند.
تعریفِ تمام‌شده: python test_phase3.py = ۸/۸ و کلِ سوئیت ۴۰/۴۰؛ یک assert اضافه کن که injection هنوز رد می‌شود.
آخرش: هر شش فایلِ تست را اجرا کن، شمارشِ سبز/قرمز را چاپ کن، بایست.
```

---

## M1 — بستنِ fallbackِ بی‌صدای IGK (fail-closed)

- **حفره (خطرناک‌ترین):** `orchestrator.py` خط ۴۹ — اگر کرنلِ IGK بالا نیاید، `self.use_igk = False` و بی‌صدا به cooperative برمی‌گردد. عکسِ fail-closed (کارت +۱ / G-10 بند ۳).
- **فایل:** `fusion-mvp/src/orchestrator.py` + `fusion-mvp/config.py` (پرچمِ نو `IGK_REQUIRED`).
- **DoD:** با `IGK_REQUIRED=True`، اگر کرنل بالا نیاید → orchestrator با خطای **صریح** halt می‌کند (نه ادامهٔ cooperative) و در audit ثبت می‌شود. با `IGK_REQUIRED=False` رفتارِ فعلی برای dev می‌ماند.
- **تست:** مسیرِ daemon را عمداً خراب کن (مسیرِ غلط) → run با `IGK_REQUIRED=True` باید halt/raise شود، نه finalize.

```
پرامپتِ کدنویس — M1:
فقط همین تکه را بساز و بایست. کدِ لوکال، تست در MOCK، فقط orchestrator.py و config.py.
مشکل: در src/orchestrator.py وقتی ساختِ KernelClient استثنا می‌دهد، کد بی‌صدا use_igk=False می‌کند
و به حالتِ cooperative می‌افتد — این خلافِ fail-closed است.
کار: یک پرچمِ IGK_REQUIRED (پیش‌فرض True) به config.py اضافه کن. اگر True بود و کرنل بالا نیامد،
به‌جای fallbackِ بی‌صدا، یک استثنای صریح بده که اجرا را halt کند و رویداد را در audit ثبت کند.
اگر False بود، رفتارِ فعلی (fallback) برای توسعه بماند.
تعریفِ تمام‌شده: یک تستِ جدید که با daemonِ عمداً‌خراب و IGK_REQUIRED=True اثبات کند run هرگز finalize نمی‌شود.
آخرش: تستِ جدید + test_igk_integration.py را اجرا کن، نتیجه را نشان بده، بایست.
```

---

## M2 — EffectorGateِ یکپارچه (choke-pointِ واقعی)

- **حفره:** `ActuationGate` فقط `finalize`ِ no-op را می‌بندد؛ callهای واقعیِ ابزار/side-effect از permit نمی‌گذرند (G-10 بند ۱-۲).
- **فایل:** `fusion-mvp/src/orchestrator.py` + `fusion-mvp/src/tools.py` (`ToolGateway.call`).
- **دامنه (bounded):** فقط **side-effectها** (اجرای ابزار در `ToolGateway` + finalize) از گیت عبور کنند — نه هر فراخوانیِ داخلیِ LLM (اصلِ صفحهٔ effector در v3).
- **DoD:** هر `ToolGateway.call` قبل از اجرا یک permit می‌گیرد و مصرف می‌کند؛ «فراموشیِ گیت» → رد (نه اجرا). finalize دیگر تنها no-op نیست.
- **تست:** یک اقدامِ ابزاری بدونِ permitِ معتبر → `PermitDenied`؛ مسیرِ سالم همچنان کار کند؛ با STOP همه‌چیز fail-closed.

```
پرامپتِ کدنویس — M2:
فقط همین تکه را بساز و بایست. کدِ لوکال، تست در MOCK، فقط orchestrator.py و tools.py.
هدف: EffectorGate را واقعی کن. الان ActuationGate فقط finalize (یک no-op) را می‌بندد.
کار: اجرای ابزار در ToolGateway.call را از ActuationGate عبور بده تا هر side-effect پیش از اجرا
permit بگیرد و مصرف کند (fail-closed). فقط side-effectها را گیت کن، نه فراخوانیِ داخلیِ LLM/reasoning را.
قیود: STOP همچنان همه را fail-closed کند؛ رفتارِ سالم نشکند.
تعریفِ تمام‌شده: تستی که (۱) اقدامِ ابزاری بدونِ permit → PermitDenied، (۲) مسیرِ سالم finalize،
(۳) با STOP رد. آخرش: test_igk_integration.py + redteam را اجرا کن، بایست.
```

---

## M3 — تنزلِ امن به‌جای جعل (کلاسِ شبکه/API)

- **حفره:** در نبودِ کلید/در outage، `llm.py` به متنِ MOCKِ **جعلی** می‌افتد؛ در production یعنی پاسخِ ساختگیِ بی‌صدا (تعارض با P8 «در شک: سکوت»).
- **فایل:** `fusion-mvp/src/llm.py` + `config.py` (پرچمِ `SAFE_DEGRADE`).
- **DoD:** با `SAFE_DEGRADE=True`، خروجیِ mock به‌جای تظاهر به پاسخِ واقعی، **برچسبِ صریحِ `[DEGRADED]`** می‌گیرد و مسیرِ finalize آن را گیت می‌کند (بدونِ تأییدِ صریح، نهایی نمی‌شود).
- **تست:** در MOCK، خروجی برچسبِ degraded دارد؛ finalize بدونِ علامتِ صریح رخ نمی‌دهد.

```
پرامپتِ کدنویس — M3:
فقط همین تکه را بساز و بایست. کدِ لوکال، تست در MOCK، فقط llm.py و config.py.
مشکل: وقتی کلید نیست، LLMClient خروجیِ mockِ جعلی می‌دهد که در production گمراه‌کننده است.
کار: پرچمِ SAFE_DEGRADE (پیش‌فرض True) اضافه کن. در حالتِ mock/تنزل، خروجی را با پیشوندِ صریحِ
[DEGRADED] و پرچمِ degraded=True برگردان؛ در orchestrator مطمئن شو خروجیِ degraded بدونِ
تأییدِ صریح finalize نمی‌شود (سکوت/read-only به‌جای جعل).
تعریفِ تمام‌شده: تستی که (۱) خروجیِ mock برچسبِ [DEGRADED] دارد، (۲) finalize روی خروجیِ degraded گیت می‌شود.
آخرش: تست‌های مرتبط را اجرا کن، بایست.
```

---

## M4 — گاردِ بودجهٔ سراسری + دیسک (کلاسِ منابع)

- **حفره:** `langar/budget.py` فقط AILab را می‌پوشد؛ سقفِ کلِ سیستم enforce نمی‌شود (G-06). گاردِ اندازهٔ دیسک/WAL هم نیست.
- **فایل:** `langar/budget.py` + call-siteهای LLM در `langar/` + یک چکِ اندازهٔ فایل.
- **DoD:** همهٔ callهای LLM از `BudgetManager` عبور می‌کنند؛ alert پلکانیِ ۵۰٪/۸۰٪؛ halt خودکار در سقفِ ماهانه (AU$30، D-25)؛ هشدارِ اندازهٔ `langar.db-wal`/`audit`.
- **تست:** شبیه‌سازیِ عبور از سقف → halt؛ WALِ بزرگِ ساختگی → هشدار.

```
پرامپتِ کدنویس — M4:
فقط همین تکه را بساز و بایست. کدِ لوکال، تست در MOCK، بدونِ اتصالِ مالی/بیرونی، دامنه = پوشهٔ langar/.
مشکل: BudgetManager فقط هزینهٔ AI-Lab را می‌شمارد؛ سایرِ callهای LLM خارج از حساب‌اند (G-06).
کار: BudgetManager را به همهٔ مسیرهای callِ LLM در langar وصل کن؛ alert در ۵۰٪ و ۸۰٪ سقفِ ماهانه؛
halt خودکار در سقف (پیش‌فرض معادلِ AU$30/ماه). یک گاردِ ساده هم اضافه کن که اگر langar.db-wal یا
فایلِ audit از یک آستانه بزرگ‌تر شد هشدار دهد.
تعریفِ تمام‌شده: تست‌هایی که (۱) عبور از سقفِ ماهانه → halt، (۲) رسیدن به ۵۰/۸۰٪ → alert، (۳) WALِ بزرگ → هشدار.
آخرش: تست‌ها را اجرا کن، بایست.
```

---

## M5 — بکاپِ off-box محلی + restore تستی (کلاسِ سخت‌افزار)

- **حفره:** بزرگ‌ترین حفرهٔ بقا — بکاپِ off-box نیست؛ مرگِ دیسک = نابودیِ کامل (BACKLOG-10).
- **فایل:** `_ops/backup/backup.ps1` + `_ops/backup/restore.ps1` (نو، اسکریپتِ لوکال).
- **قید:** فقط کپیِ **لوکالِ off-box** (USB/دیسکِ دوم). rclone-به-cloud فقط comment/رزرو می‌ماند تا rotation (چون credential/شبکه لازم دارد).
- **DoD:** کپیِ اتمیکِ `langar.db` (+ WAL checkpoint) و `audit.jsonl` و `prompts.json` به مقصدِ لوکال؛ اسکریپتِ restore که به یک پوشهٔ موقت بازمی‌گرداند و صحت را ثابت می‌کند.
- **تست:** backup → restore به temp → `PRAGMA integrity_check` سبز.

```
پرامپتِ کدنویس — M5:
فقط همین تکه را بساز و بایست. کدِ لوکال، بدونِ شبکه/cloud. فقط پوشهٔ _ops/backup/ را بساز.
هدف: بکاپِ off-box محلی برای بقا در برابر مرگِ دیسک.
کار: دو اسکریپتِ PowerShell بنویس: backup.ps1 که langar.db (با WAL checkpoint)، audit.jsonl و
prompts.json را اتمیک به یک مقصدِ لوکالِ پارامتری (USB/دیسکِ دوم) کپی می‌کند؛ و restore.ps1 که به یک
پوشهٔ موقت بازمی‌گرداند و PRAGMA integrity_check می‌زند. کپیِ cloud/rclone را فقط به‌صورت comment/رزرو بگذار
(پیاده نکن — تا rotation).
تعریفِ تمام‌شده: اجرای backup سپس restore روی داده‌ی نمونه، integrity_check سبز.
آخرش: یک run نمونه روی داده‌ی ساختگی نشان بده، بایست.
```

---

## M6 — سیم‌کشیِ observability (G-08)

- **حفره:** دکوریتورِ `@trace` هیچ call-site ندارد → `/events` خالی؛ `/delete_all_data` جداولِ event را پاک نمی‌کند.
- **فایل:** `langar/observability/tracer.py` + چهار call-site (`model_call`, `tool_call`, `reasoning`, `handoff`).
- **DoD:** چهار span واقعاً trace می‌شوند و در `event_log` می‌نشینند؛ `/delete_all_data` جداولِ event را هم شامل شود.
- **تست:** یک تعاملِ نمونه → `event_log` ≥ ۴ رکورد؛ بعد از delete_all → خالی.

```
پرامپتِ کدنویس — M6:
فقط همین تکه را بساز و بایست. کدِ لوکال، تست در MOCK، دامنه = langar/.
مشکل: tracer/@trace call-site ندارد → /events خالی است (G-08).
کار: چهار span کلیدی (model_call, tool_call, reasoning, handoff) را با tracer سیم‌کشی کن
(sink از قبل در main.py وصل است)؛ و /delete_all_data را کامل کن که جداولِ event/trace را هم پاک کند.
تعریفِ تمام‌شده: تستی که بعد از یک تعاملِ نمونه event_log ≥۴ رکورد دارد و delete_all آن را خالی می‌کند.
آخرش: تست را اجرا کن، بایست.
```

---

## M7 — پنلِ واقعی به‌جای نمایشی (G-15)

- **حفره:** پنل کالِ LLM می‌زند و هزینه ثبت می‌کند ولی رأی از **هیوریستیکِ طول/کیورد** می‌آید؛ خروجیِ مدل بی‌اثر است.
- **فایل:** `fusion-mvp/src/panel.py` (`Judge.vote`).
- **DoD:** رأیِ هر داور از **خروجیِ providerِ خودش** استخراج شود (APPROVE/REJECT)، نه از `_decide` هیوریستیک. در MOCK با providerهای برچسب‌دار قابل‌تست بماند (اثباتِ LIVE در G-26 معوق).
- **تست:** providerی که REJECT می‌دهد → رأیِ منفی؛ رأی مستقل از طولِ متن.

```
پرامپتِ کدنویس — M7:
فقط همین تکه را بساز و بایست. کدِ لوکال، تست در MOCK، فقط panel.py.
مشکل: Judge.vote رأی را از هیوریستیکِ طول/کیورد می‌گیرد و خروجیِ واقعیِ provider را نادیده می‌گیرد (G-15).
کار: رأی را از متنِ پاسخِ provider استخراج کن (شروع با APPROVE/REJECT)؛ هیوریستیک فقط fallback باشد.
ساختار را طوری نگه دار که در MOCK با providerهای برچسب‌دار (که APPROVE یا REJECT می‌دهند) قابل‌تست باشد.
تعریفِ تمام‌شده: تستی که (۱) providerِ REJECT → رأیِ منفی، (۲) رأی مستقل از طولِ متن، (۳) حدنصاب هنوز کار کند.
آخرش: test_phase3.py (بخشِ پنل) را اجرا کن، بایست.
```

---

## M8 — L1.5 stress-gated promotion (LOH-analog، رزرو → پایه)

- **حفره:** در `self_update.py` ارتقاء فقط **امتیازی** است؛ ذخیرهٔ نسخهٔ دوم بدونِ گیتِ استرس promote می‌شود (L1.5 نیمه).
- **فایل:** `fusion-mvp/self_update.py` + `config.py`.
- **وابستگی:** سیگنالِ anomaly/استرس (از M6/observability یا یک ورودیِ ساده).
- **DoD:** promote فقط وقتی **هم** بهبودِ نمره هست **و هم** سیگنالِ استرس اجازه دهد؛ در نبودِ استرس، نسخهٔ جدید ساخته ولی **masked** می‌ماند (نه active) — دقیقاً LOHِ استرس‌القا.
- **تست:** بدونِ سیگنالِ استرس → با نمرهٔ بهتر هم active نمی‌شود؛ با سیگنال → promote.

```
پرامپتِ کدنویس — M8:
فقط همین تکه را بساز و بایست. کدِ لوکال، تست در MOCK، فقط self_update.py و config.py.
هدف: L1.5 stress-gated promotion (آنالوگِ LOHِ استرس‌القا).
کار: can_keep/حلقهٔ promote را طوری تغییر بده که نسخهٔ جدید فقط وقتی active شود که هم نمره بهتر شده باشد
و هم یک سیگنالِ استرس/anomaly (پارامترِ ورودی، پیش‌فرض غیرفعال) اجازه دهد. در نبودِ استرس نسخه ساخته
ولی masked بماند (در PromptStore ذخیره، ولی active عوض نشود).
تعریفِ تمام‌شده: تستی که (۱) بدونِ استرس، نسخهٔ بهتر masked می‌ماند، (۲) با استرس promote می‌شود، (۳) rollback سالم.
آخرش: تست‌های self_update را اجرا کن، بایست.
```

---

## ترتیبِ اجرا و منطق

**موجِ ۱ (fusion-mvp، کم‌ریسک، مستقل):** M0 → M1 → M2 → M3. هستهٔ ایمنی/بقا را سفت می‌کند بدونِ لمسِ langarِ زنده.
**موجِ ۲ (langar/بدنه):** M4، M6 — گاردِ منابع و شفافیت روی باتِ زنده.
**موجِ ۳ (تابِ بقا):** M5 (بکاپ)، M7 (پنل)، M8 (stress-gate).

هر milestone «آخرش می‌ایستد» تا مرور کنی. هیچ‌کدام به کلیدِ چرخانده‌نشده، پول، یا شبکه وابسته نیست → همه **قبل از rotation** ایمن‌اند.

## Next (آخرش بایست)

این پلن proposal بود؛ هیچ فایلِ کد تغییر نکرد. برای شروع، پرامپتِ **M0** را به کدنویس بده — کم‌ریسک‌ترین، و سوئیت را دوباره سبز می‌کند.
