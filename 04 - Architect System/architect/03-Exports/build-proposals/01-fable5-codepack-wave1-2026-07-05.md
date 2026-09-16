---
type: proposal
status: draft
tags: [build-proposal, codegen, fable5]
created: 2026-07-05
updated: 2026-07-05
sources: "[[BUILD-BACKLOG]], [[MYCELIAL-MASTER-SPEC]]"
---

# پکِ کدنویسِ Fable 5 — موج ۱ (M0 → M1 → M2 → M3)

> **این چیست؟** بسته‌ی آماده‌ی تحویل به سازنده (**Fable 5**) برای **موجِ ۱** پلنِ ساخت: چهار milestoneِ کم‌ریسکِ هستهٔ `fusion-mvp`. خروجیِ آیتمِ ۱ صفِ حلقهٔ خودکارِ `build-planner-loop`. **فقط-پیشنهاد (propose-only)** — هیچ کدی اینجا اجرا یا اعمال نشده؛ منتظرِ verdictِ آری.
>
> منابع: [[BUILD-BACKLOG]] (متنِ کانونیِ prompt‌ها؛ M0–M3) · [[MYCELIAL-MASTER-SPEC]] §۴ پلنِ ساخت، §۵ چرخهٔ امن، §۶ انتخابِ مدل، §۱۰ handoff · صف/لاگ: [[04 - Architect System/architect/04-Docs/AUTONOMOUS-RUN-2026-07-05|AUTONOMOUS-RUN]].

## خلاصهٔ سریع (Quick Summary)

چهار پرامپتِ **مستقلِ آماده‌کپی** برای Fable 5 که هستهٔ ایمنی/بقای `fusion-mvp` را سفت می‌کنند — بدونِ لمسِ باتِ زندهٔ `langar`، بدونِ شبکه/پول/کلید، همه در **MOCK**. هرکدام «آخرش می‌ایستد» تا آری مرور کند. بعد از هر تکه: تست‌های سبز = گیتِ CI؛ سپس verdictِ آری → APPLY طبق ماشینِ حالتِ §۵. این پک چیزِ نویی «تصمیم» نمی‌گیرد؛ فقط متنِ کانونیِ [[BUILD-BACKLOG]] را در قالبِ handoffِ آماده‌ی‌اجرا با گاردهای سراسری، ترتیب، و معیارِ پذیرش بسته‌بندی می‌کند.

**چرا این چهار تا اول؟** موجِ ۱ = بی‌ریسک‌ترین و مستقل از rotation/git/پول. M0 پیش‌پروازِ سبزکردنِ سوئیت است؛ M1–M3 سه حفرهٔ fail-safe را می‌بندند (fallbackِ بی‌صدا، گیتِ side-effect، جعلِ خروجی).

## ۰. نحوهٔ استفاده (برای آری)

1. **یکی‌یکی.** هر بلوکِ پرامپت را جداگانه به Fable 5 بده — نه هر چهار را با هم. هر milestone «آخرش می‌ایستد».
2. **مرور بین تکه‌ها.** بعد از هر اجرا، diff و شمارشِ تست را ببین. طبق §۵: `PROPOSE → DRY-RUN → [verdictِ تو] → APPLY(MOCK) → TEST → PROMOTE`؛ `STOP` در هر لحظه = fail-closed.
3. **verdict.** خروجیِ Fable 5 تا تأییدِ تو فقط proposal است. اگر سبز و درست بود → APPLY؛ اگر نه → یک خط بازخورد و دوباره.
4. **ترتیبِ پیشنهادی:** M0 → M1 → M2 (زنجیره‌ای؛ M1 روی M0، M2 روی M1) سپس M3 (مستقل، هر زمان). جزئیات در بخشِ «ترتیب و وابستگی».

## قواعدِ سختِ سراسری (روی هر ۴ تکه اعمال می‌شود)

این قیود بالای هر پرامپت برای Fable 5 تکرار شده‌اند؛ اینجا یک‌جا:

- **فقط کدِ لوکال، فقط MOCK.** بدونِ اتصالِ شبکه/بیرونی، بدونِ کلیدِ واقعی، بدونِ هیچ اقدامِ مالی. (قیدِ سراسریِ تا rotationِ G-01.)
- **یک milestone در هر نوبت، آخرش بایست.** هیچ تکه‌ای به تکهٔ بعد نپرد.
- **دامنهٔ فایلِ محدود.** فقط فایل‌هایی که هر milestone صریحاً نام می‌برد تغییر کنند؛ باقیِ درخت دست‌نخورده.
- **fail-closed پیش‌فرض.** در شک → توقف/رد، نه ادامهٔ بی‌صدا. رگرسیونِ امنیتی نگیر (گاردهای injection باید سبز بمانند).
- **خروجی = proposal تا verdict.** کدنویس diff و نتیجهٔ تست را نشان می‌دهد؛ اعمالِ نهایی با آری.
- **هیچ ویرایشِ خارج از دامنه:** نه charter، نه PROJECT.md، نه اسکریپت‌های زمان‌بند، نه رمز/محرمانه.

## مدل و هزینه (Model & Cost)

استراتژیِ مدل از [[MYCELIAL-MASTER-SPEC]] §۶:

| نقش | مدل | چرا |
|---|---|---|
| **Builder** (این پک) | **Fable 5** | ساختِ کد و رفعِ باگ؛ lock-inِ کم چون spec قابل‌حمل است |
| Runtimeِ روتین | Claude Haiku | ارزان؛ ادراک/روتین |
| تحلیلِ سخت | Claude Sonnet/Opus | نقدِ معماری، تصمیمِ جهش |
| Escalation | Fugu — فقط پشتِ budget-gate | ضریبِ پنهانِ ~۵–۱۵× توکن؛ پیش‌فرض نه |

**برآوردِ هزینه:** موجِ ۱ کارِ کدنویسیِ محلی روی سوئیتِ MOCK است؛ مصرفِ توکنِ آن هزینهٔ **build-time** روی اشتراکِ Fable است، نه runtimeِ باتِ زنده — پس در سقفِ عملیاتیِ **AU$30/ماه** (D-25) نمی‌نشیند. هزینهٔ واقعی ≈ ۴ نشستِ کدنویسیِ کوتاه + اجرای تست‌ها. قیمتِ مدل را build-time از vendor بخوان، hard-code نکن.

---

## M0 — سبز کردنِ مجدد سوئیت (رفعِ regression N-01) 🟢 خیلی‌کم‌ریسک

- **حفره:** گیتِ allowlistِ G-26 پرامپتِ بی‌خطرِ «…و خوب کار می‌کنی» را رد می‌کند → `t_prompt_guardrail` قرمز؛ ادعای «همه سبز» stale است.
- **فایلِ مجاز:** `fusion-mvp/src/evals.py` (`ALLOWED_SENTENCE_PATTERNS`) و/یا `fusion-mvp/test_phase3.py`.
- **DoD:** `python test_phase3.py` → ۸/۸؛ کلِ سوئیت **۴۰/۴۰**؛ و injection (`ignore previous`) و حذفِ نقش همچنان رد شوند.
- **تست:** موردِ موجود سبز شود + یک assert که ثابت کند injection هنوز رد است (رگرسیونِ امنیتی نگیریم).

```text
فقط همین تکه را بساز و بایست. کدِ لوکال، تست در MOCK، هیچ فایلِ دیگری تغییر نکند.
مشکل: در fusion-mvp، تابعِ validate_prompt_allowlist در src/evals.py پرامپتِ بی‌خطرِ
«تو ایجنت Researcher هستی و خوب کار می‌کنی» را رد می‌کند و test_phase3.py::t_prompt_guardrail را قرمز کرده.
کار: یک الگوی allowlistِ محدود برای «توصیفِ خنثیِ کیفیت» اضافه کن که جمله‌های بی‌خطر را عبور دهد
ولی injection («ignore previous»/«نادیده بگیر»/خنثی‌سازیِ محافظ) و حذفِ نشانهٔ نقش را همچنان رد کند.
تعریفِ تمام‌شده: python test_phase3.py = ۸/۸ و کلِ سوئیت ۴۰/۴۰؛ یک assert اضافه کن که injection هنوز رد می‌شود.
آخرش: هر شش فایلِ تست را اجرا کن، شمارشِ سبز/قرمز را چاپ کن، بایست.
```

---

## M1 — بستنِ fallbackِ بی‌صدای IGK (fail-closed) 🟢 کم‌ریسک · وابسته به M0

- **حفره (خطرناک‌ترین کلاس):** `orchestrator.py` — اگر کرنلِ IGK بالا نیاید، بی‌صدا `use_igk = False` و به cooperative برمی‌گردد. عکسِ fail-closed.
- **فایلِ مجاز:** `fusion-mvp/src/orchestrator.py` + `fusion-mvp/config.py` (پرچمِ نو `IGK_REQUIRED`).
- **DoD:** با `IGK_REQUIRED=True`، اگر کرنل بالا نیاید → orchestrator با خطای **صریح** halt می‌کند و در audit ثبت می‌شود. با `IGK_REQUIRED=False` رفتارِ فعلیِ dev می‌ماند.
- **تست:** مسیرِ daemon را عمداً خراب کن → run با `IGK_REQUIRED=True` باید halt/raise شود، نه finalize.

```text
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

## M2 — EffectorGateِ یکپارچه (choke-pointِ واقعی) 🟡 متوسط · وابسته به M1

- **حفره:** `ActuationGate` فقط `finalize`ِ no-op را می‌بندد؛ callهای واقعیِ ابزار/side-effect از permit نمی‌گذرند.
- **فایلِ مجاز:** `fusion-mvp/src/orchestrator.py` + `fusion-mvp/src/tools.py` (`ToolGateway.call`).
- **دامنهٔ محدود:** فقط **side-effectها** (اجرای ابزار + finalize) گیت شوند — نه هر فراخوانیِ داخلیِ LLM (اصلِ صفحهٔ effector).
- **DoD:** هر `ToolGateway.call` قبل از اجرا permit می‌گیرد و مصرف می‌کند؛ «فراموشیِ گیت» → رد. finalize دیگر تنها no-op نیست.
- **تست:** اقدامِ ابزاری بدونِ permitِ معتبر → `PermitDenied`؛ مسیرِ سالم کار کند؛ با STOP همه fail-closed.

```text
فقط همین تکه را بساز و بایست. کدِ لوکال، تست در MOCK، فقط orchestrator.py و tools.py.
هدف: EffectorGate را واقعی کن. الان ActuationGate فقط finalize (یک no-op) را می‌بندد.
کار: اجرای ابزار در ToolGateway.call را از ActuationGate عبور بده تا هر side-effect پیش از اجرا
permit بگیرد و مصرف کند (fail-closed). فقط side-effectها را گیت کن، نه فراخوانیِ داخلیِ LLM/reasoning را.
قیود: STOP همچنان همه را fail-closed کند؛ رفتارِ سالم نشکند.
تعریفِ تمام‌شده: تستی که (۱) اقدامِ ابزاری بدونِ permit → PermitDenied، (۲) مسیرِ سالم finalize،
(۳) با STOP رد. آخرش: test_igk_integration.py + redteam را اجرا کن، بایست.
```

---

## M3 — تنزلِ امن به‌جای جعل (کلاسِ شبکه/API) 🟢 کم‌ریسک · مستقل

- **حفره:** در نبودِ کلید/در outage، `llm.py` به متنِ MOCKِ **جعلی** می‌افتد؛ در production یعنی پاسخِ ساختگیِ بی‌صدا (تعارض با P8 «در شک: سکوت»).
- **فایلِ مجاز:** `fusion-mvp/src/llm.py` + `fusion-mvp/config.py` (پرچمِ `SAFE_DEGRADE`).
- **DoD:** با `SAFE_DEGRADE=True`، خروجیِ mock برچسبِ صریحِ `[DEGRADED]` می‌گیرد و مسیرِ finalize بدونِ تأییدِ صریح آن را نهایی نمی‌کند.
- **تست:** در MOCK خروجی برچسبِ degraded دارد؛ finalize بدونِ علامتِ صریح رخ نمی‌دهد.

```text
فقط همین تکه را بساز و بایست. کدِ لوکال، تست در MOCK، فقط llm.py و config.py.
مشکل: وقتی کلید نیست، LLMClient خروجیِ mockِ جعلی می‌دهد که در production گمراه‌کننده است.
کار: پرچمِ SAFE_DEGRADE (پیش‌فرض True) اضافه کن. در حالتِ mock/تنزل، خروجی را با پیشوندِ صریحِ
[DEGRADED] و پرچمِ degraded=True برگردان؛ در orchestrator مطمئن شو خروجیِ degraded بدونِ
تأییدِ صریح finalize نمی‌شود (سکوت/read-only به‌جای جعل).
تعریفِ تمام‌شده: تستی که (۱) خروجیِ mock برچسبِ [DEGRADED] دارد، (۲) finalize روی خروجیِ degraded گیت می‌شود.
آخرش: تست‌های مرتبط را اجرا کن، بایست.
```

---

## ترتیب و وابستگی

```
M0 (سبز کردنِ سوئیت) ──► M1 (fail-closedِ IGK) ──► M2 (EffectorGate)
                                                        
M3 (تنزلِ امن) ── مستقل، هر زمان بعد از M0 ──────────────┘
```

- **زنجیره:** M1 روی سوئیتِ سبزِ M0 می‌نشیند؛ M2 روی رفتارِ fail-closedِ M1. اگر M0 قرمز بماند، مبنای تستِ M1/M2 قابل‌اتکا نیست.
- **مستقل:** M3 به M0/M1/M2 وابسته نیست (فقط `llm.py`/`config.py`)، ولی چون `config.py` را هم لمس می‌کند، **بعد از M1** انجامش بده تا merge روی `config.py` تمیز بماند.
- **خارج از این موج (عمداً):** M4·M6 (موج۲) و M5·M7·M8 (موج۳) — آیتمِ ۲ صف.

## معیارِ پذیرشِ کلِ موج ۱ (Definition of Done)

- [ ] M0: سوئیت **۴۰/۴۰**؛ assertِ injection سبز.
- [ ] M1: با daemonِ خراب و `IGK_REQUIRED=True` هرگز finalize نمی‌شود (halt صریح + ثبت در audit).
- [ ] M2: اقدامِ ابزاری بدونِ permit → `PermitDenied`؛ مسیرِ سالم کار می‌کند؛ STOP → fail-closed.
- [ ] M3: خروجیِ MOCK برچسبِ `[DEGRADED]` دارد؛ finalizeِ خروجیِ degraded گیت می‌شود.
- [ ] گیتِ کیفیت (§۵/§۹): rubric ≥۱۲/۱۶ با judgeِ کورِ خانوادهٔ متفاوت + anti-Goodhart (گیت = کف، نه هدف).
- [ ] هیچ رگرسیونِ امنیتی: گاردهای injection/حذفِ نقش در کلِ سوئیت سبز بمانند.
- [ ] verdictِ آری برای هر تکه پیش از APPLY.

## راستی‌آزمایی و ثبت (این اجرا)

- **اسکنِ محرمانه:** این نوت صفر مقدارِ محرمانه/PII دارد؛ همهٔ ارجاع‌ها به «کلید» فارسی‌اند، الگوهای رمزِ انگلیسی نیامده.
- **stale-view (کشفِ همین اجرا):** نمای سندباکسِ [[MYCELIAL-MASTER-SPEC]] در §۶ برید (۱۸۹ خط)، ولی خواندنِ سمت‌ویندوز کاملِ ۱۱ بخش (۲۷۷ خط) را نشان داد → مِنتِ سندباکس کهنه بود، نه spec ناقص. طبق قاعدهٔ ledger، مبنا = خواندنِ ویندوزی. (این ردیف در [[_memory/EXPERIENCE-LEDGER|EXPERIENCE-LEDGER]] ثبت شد.)
- **validatorها:** هر دو اسکریپتِ `04 - Architect System/scripts/` اجرا شد؛ این نوتِ نو نباید خطای فرانت‌متر یا لینکِ شکستهٔ نو بسازد.

## سؤالاتِ بازِ آری (propose-only — اگر شک، اینجا)

1. **دانه‌بندیِ verdict:** موجِ ۱ را milestone-به-milestone با verdict بینِ هر تکه پیش ببریم، یا M0→M3 را یک‌جا به Fable بدهیم و آخرش یک‌بار مرور کنی؟ (پیش‌فرضِ امنِ من: یکی‌یکی.)
2. **`IGK_REQUIRED` پیش‌فرض:** True (fail-closed) درست است؟ در dev ممکن است اصطکاک بسازد؛ ولی امن‌تر است. تأیید می‌کنی؟
3. **دامنهٔ M2:** آیا «فقط side-effect گیت شود، نه فراخوانیِ داخلیِ LLM» با نیتِ تو می‌خواند، یا می‌خواهی هر reasoning-call هم شمرده شود؟ (پیش‌فرض: فقط side-effect — طبق اصلِ صفحهٔ effector.)
