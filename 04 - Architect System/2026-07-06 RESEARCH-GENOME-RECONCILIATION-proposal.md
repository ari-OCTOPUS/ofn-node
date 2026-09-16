---
type: proposal
status: proposal            # propose-only — هیچ فایل ژنوم تغییر نکرد. اعمال فقط با verdict آری.
role: Researcher-Designer   # منشور §۱: تحقیق/تحلیل/پیشنهاد؛ اعمال هرگز بدون verdict
created: 2026-07-06
verdict: pending-آری
scope: تطبیق «خروجی تحقیق ژنوم» با فایل‌های واقعی genome/learning-engine
sources_read: [ARCHITECT_CHARTER.md, architect/PROJECT.md, learning-engine/LEARNING-CONTRACT.yaml, learning-engine/LEARNING-STATE.json, learning-engine/ENGINE-PROMPT.md, learning-engine/MUTATION-WHITELIST.md, learning-engine/MUTATION-LEDGER.md, learning-engine/STARTUP-PROTOCOL.md, learning-engine/STARTUP-CHECKLIST.yaml, scripts/DOCTOR-BLUEPRINT-v1.md, LAPTOP-RUNTIME.md]
tags: [reconciliation, genome, learning-engine, propose-only]
---

# تطبیق تحقیق ↔ ژنوم واقعی — Propose-Only

> **این سند کد/ژنوم را تغییر نمی‌دهد.** طبق منشور §۱ (propose → تأیید آری → اعمال) و §۷ (پیشنهاد با شناسهٔ ledger)، خروجی این‌جا فقط دیفِ پیشنهادی است. هیچ فایل genome/learning-engine ویرایش نشد.

---

## ۰. TL;DR (یافتهٔ اصلی)

خروجی تحقیق عمدتاً یک **بازآفرینیِ مستقلِ** همان چیزی است که در `ARCHITECT_CHARTER.md` و `learning-engine/` **از قبل قانون است**. یعنی تحقیق ایمنیِ تازه‌ای اضافه نمی‌کند — همان معماریِ propose→approve، evaluator منجمد، سقفِ per-run، و حافظهٔ append-only را دوباره استنتاج می‌کند. ارزش واقعیِ تطبیق در سه چیز است:

1. **۳ دریفتِ داخلیِ زنده** بین فایل‌های خودت که تحقیق کمک می‌کند ببینیم (CONTRACT در برابر STATE در برابر CHARTER). این‌ها مهم‌ترند از هر توصیهٔ تحقیق.
2. **۲ سخت‌سازیِ واقعاً جدید** که تحقیق درست می‌گوید (read-only فنی + رادار آینده).
3. **۳ ادعای تحقیق که باید دور ریخته شوند** چون پروژه‌ات از آن‌ها **باهوش‌تر** است (مثلاً «دکتر هفتگی Opus» در برابر دکترِ zero-LLM قطعیِ موجود).

جمع‌بندی: از ~۱۵ توصیهٔ تحقیق، **۹ مورد از قبل قانون‌اند**، **۳ دلتای واقعی**، **۳ مردود**. هیچ‌کدام «جهش خودکار» نیستند؛ همه verdict آری می‌خواهند.

---

## ۱. نقشهٔ تطبیق (هر توصیهٔ تحقیق → فایل واقعی → حکم)

| # | توصیهٔ تحقیق | وضعیت واقعی در پروژه (فایل·خط) | حکم |
|---|---|---|---|
| Q1 | مرز invariant↔mutable = «آنچه معیار قضاوت را تعیین می‌کند» | `MUTATION-WHITELIST.md` §۰ + `ENGINE-PROMPT.md` §۰.۳ + منشور «immutable برای ایجنت‌ها» | ✅ **از قبل قانون** |
| Q1 | ژنوم read-only **فنی**، نه فقط قراردادی | فعلاً فقط prompt/contract: «حلقه هرگز whitelist را جهش نمی‌دهد» (WHITELIST §۰، DEEP-GAP شکاف ۸) — هیچ enforce فایل‌سیستمی نیست | → **دلتای واقعی D4** |
| Q1 | پروتکل تغییر ژنوم: ۷۲h + کلید دوم | منشور §۱: propose→approve، timeout=DENY (D-13) — کلید دوم/۷۲h نیست | 🟡 **اختیاری D5** |
| Q2 | متریک‌های سلامت perception | `dashboard_doctor.py`: raw/effective/counts/findings + `ENGINE-PROMPT` §۲ (نسبت جهش ماندگار:revert >۳:۱، صفر نقض invariant) | ✅ **از قبل قانون** |
| Q2 | درسِ Recall = scope باید allowlist مالک باشد | منشور §۶ Privacy + `LEARNING-CONTRACT` L3_ingest «بدون manifest سبز، یادگیری ممنوع» | ✅ **از قبل قانون** |
| Q2 | کالبدشکافی‌های بیرونی (AutoGPT/Rewind/Recall) | context مفید — ولی ledger خودت (row-27/37/40/47 stale-view) کالبدشکافیِ زنده‌ترِ خودت است | ℹ️ فقط context |
| Q3 | رادار ۲۴ماهه + سناریو ۳–۵ساله + اصول ۱۰ساله | چنین artifactی نداری؛ فعلاً `DECISIONS D-xx` + `BUILD-BACKLOG` (لاگ تصمیم، نه پیش‌نگری) | 🟢 **دلتای جدید D-radar (کم‌فوریت)** |
| Q4 | evaluator منجمد بیرون از دسترسِ نوشتن | WHITELIST: «جهشی که whitelist/گاردها را لمس کند = نقض → halt» | ✅ **از قبل قانون** |
| Q4 | monitor جدا از متریکِ بهینه‌شونده | دکتر (zero-LLM) جدا از حلقهٔ جهش (LLM) — تفکیک ساختاری موجود | ✅ **از قبل قانون** |
| Q4 | سقف per-run + گیت انسانی | WHITELIST: «۱ جهش/روز، evidence-based، ۲ خطا→rollback، STOP» + منشور propose→approve | ✅ **از قبل قانون** |
| Q5 | حذف polling دقیقه‌ای → event-driven + batch شبانه | حلقه **ساعتی** است (`loop_task @ 35 * * * *`)، نه دقیقه‌ای؛ لاین‌های `*/3,*/15,*/5` عمداً **dark** (STATE.pilot.scope_dark) | ⚠️ **بخشاً مردود** (strawman) — اما اقتصادِ Q5 پشتیبانِ «dark ماندن» است |
| Q5 | «کش گرم» = incremental index محلی | پروژه از ledger + دکتر استفاده می‌کند، نه prompt-cache API | ❌ **مردود** (استفاده نمی‌شود) |
| Q6 | دکتر گرانِ کم‌تکرار + کارگر ارزان | دکترِ **zero-LLM قطعی** (از «هفتگی Opus» ارزان‌تر و بهتر) | ✅ **از قبل قانون + باهوش‌تر** |
| Q6 | حافظهٔ مشترک = JSONL/ledger + git، نه vector-DB/Kafka | `EXPERIENCE-LEDGER` + `MUTATION-LEDGER` append-only + git-target | ✅ **از قبل قانون** |
| Q6 | model routing (RouteLLM/FrugalGPT) | فعلاً «Claude داخلی»؛ حجم = ۱ جهش/روز → ROI مسیریابی پایین | ℹ️ اختیاریِ کم‌اولویت |
| MERGE-3 | «دکتر هفتگی Opus-tier» | متناقض با دکترِ zero-LLM موجود = **پس‌رفت** | ❌ **مردود** |

---

## ۲. سه دریفتِ داخلیِ زنده — مهم‌ترین خروجی (دیف propose-only)

این‌ها تعارض بین فایل‌های خودِ توست که تطبیق آشکار کرد. اولویتِ اول، چون سیستمِ «تک‌منبعِ حقیقت» با سه صدای متناقض کار می‌کند.

### D1 — `mode: active/L3` در قرارداد ✗ در برابر واقعیتِ `L0-shadow/L1` در STATE
- **قرارداد** (`LEARNING-CONTRACT.yaml:9`): `mode: active   # L3 — call خارجی فعال … ← تغییر از shadow` و hard_rule «active بعد از Gate+git ← تغییر از propose-only» و L2b/L2c `status: active`.
- **واقعیت** (`LEARNING-STATE.json`): `autonomy_level: "L0-shadow"`، `external_calls_scope: "L1-propose-only … L2/L3 همچنان قفل"`، `runtime: "interactive-sessions-only (هنوز پروسه مستقل ندارد)"`.
- **منشور** §۱: حلقه = propose→approve، بدون میان‌بر.
- **تشخیص:** فایلِ قرارداد به‌صورت آرزویی به L3/active جهش داده شده، ولی وضعیتِ عملیاتی هنوز L1-propose-only است. STATE محافظه‌کار و درست است؛ قرارداد جلوتر از واقعیت است. تحقیق Q4 دقیقاً همین را هشدار می‌دهد: autonomy را جلوتر از گاردها باز نکن.
- **دیف پیشنهادی (گزینهٔ محافظه‌کار، هم‌راستا با منشور fail-closed):**
```diff
# learning-engine/LEARNING-CONTRACT.yaml
-  mode: active              # L3 — call خارجی فعال؛ کلید در ROTATION + budget_ceiling_daily عددی     ← تغییر از shadow
+  mode: propose-only        # عملیاتی = L1 (منبع: STATE.autonomy_level=L0-shadow، external_calls_scope=L1-propose-only)
+  mode_target: active-L3    # هدف، نه وضعیت فعلی؛ ارتقا فقط با: ردیف‌های ۱–۴ سبز + git_ready + verdict صریح
```
- **verdict آری لازم:** آیا واقعاً می‌خواهی الان L3/active باشی (که آن‌وقت STATE باید ارتقا یابد و پیش‌شرط‌ها تأیید شوند)، یا STATE درست است و قرارداد باید به عقب هماهنگ شود؟ **توصیه: دومی** (قرارداد را با واقعیت هماهنگ کن).

### D2 — `security_gate_status: "OPEN"` در STATE ✗ در برابر `LIFTED` در منشور
- **منشور** §۲ (تک‌منبعِ رسمیِ وضعیت گیت): «🟢 گیت برداشته شد — LIFTED … هر ۴ ردیف CRITICAL ROTATED … verdict صریح آری «جمعش کن» ۲۰۲۶-۰۷-۰۶».
- **STATE**: `"security_gate_status": "OPEN"` + note «lift رسمی معوقِ ویرایش دستی مالک».
- **تشخیص:** liftی که STATE منتظرش بود، در منشور **انجام شده**؛ STATE صرفاً sync نشده = کهنه. عارضهٔ جانبی: `STARTUP-CHECKLIST` سوال `rotation_status` را تا وقتی STATE=OPEN است هر boot می‌پرسد → نویزِ بی‌مورد.
- **دیف پیشنهادی:**
```diff
# learning-engine/LEARNING-STATE.json
-  "security_gate_status": "OPEN",
+  "security_gate_status": "LIFTED",   // sync با ARCHITECT_CHARTER §۲ (LIFTED، verdict «جمعش کن» 2026-07-06)
```
- **verdict آری لازم:** تأیید کن منشورِ LIFTED حقیقت است → STATE را sync کن (سوالِ boot تکراری خودش خاموش می‌شود).

### D3 — دو whitelist ناسازگار + تعارضِ «call خارجی در حلقه»
- (الف) `ENGINE-PROMPT.md` §۰.۳ می‌گوید mutable = «`ENGINE-PROMPT.md` بخش‌های ۱+»؛ اما `MUTATION-WHITELIST.md` می‌گوید promptِ mutable = «`prompts/PROMPT-vN.md`» و `ENGINE-PROMPT` را اصلاً mutable نمی‌داند. خودِ هدرِ `ENGINE-PROMPT` هشدار می‌دهد: «منبع عملیاتی = MUTATION-WHITELIST + prompts/PROMPT-vN.md … دو منبع حقیقت نسازید (#108)».
- (ب) `ENGINE-PROMPT` §۰.۷ به حلقه اجازهٔ call خارجی می‌دهد؛ `MUTATION-WHITELIST` می‌گوید «هیچ call خارجی در این حلقه — فقط Claude داخلی».
- **تشخیص:** دقیقاً همان آنتی‌پترنِ «دو منبع حقیقت» که خودت برچسب زده‌ای. تحقیق Q1 (یک evaluator/مرزِ واحد، بدون منبع دومِ یتیم) اصلِ حلش را می‌دهد.
- **دیف پیشنهادی (تثبیت یک منبع):**
```diff
# learning-engine/ENGINE-PROMPT.md  (بالای §۰)
+ > [!warning] SUPERSEDED-FOR-OPS: منبعِ عملیاتیِ مرزِ جهش = MUTATION-WHITELIST.md (تنها).
+ > §۰.۳ و §۰.۷ این فایل فقط specِ نسل v2 است و برای حلقه اجرا نمی‌شود.
+ > حلِ تعارض: حلقه internal-Claude-only (طبق WHITELIST)؛ callهای خارجیِ Fugu/partner
+ > متعلق به لایه‌های L2b/L2c قراردادند، نه به حلقهٔ خودجهش.
```
- **verdict آری لازم:** تأیید کن `MUTATION-WHITELIST.md` تنها whitelist معتبر است (توصیه: بله). سپس مرزِ scope را صریح کن: «حلقهٔ جهش = داخلی؛ لایهٔ ingest/capability = خارجی مجاز زیر بودجه».

---

## ۳. دو سخت‌سازیِ واقعیِ تحقیق (دلتای جدید)

### D4 — enforce فنیِ read-only روی ژنوم (Q1 درست می‌گوید)
- **الان:** تغییرناپذیریِ منشور/قرارداد/whitelist فقط با **متنِ قرارداد/پرامپت** enforce می‌شود (منشور «immutable»، WHITELIST «حلقه هرگز whitelist را جهش نمی‌دهد»). هیچ گاردِ فایل‌سیستمی نیست → اگر حلقه دچار reward-hacking شود، از نظر فنی می‌تواند بنویسد (DEEP-GAP شکاف ۸ باز است).
- **قیدِ واقعیِ خودت (`DOCTOR-BLUEPRINT`):** vault یک mount نوع FUSE است و دکتر از آن می‌خواند؛ پس read-only باید فقط مسیرهای **نوشتنِ ژنوم** را ببندد، نه مسیر خواندنِ دکتر یا نوشتن‌های مجازِ حلقه (`LEARNING-STATE.json`، `prompts/`، `versions/`، `_memory/`).
- **پیشنهاد دو فازی:**
  - **حالا (کم‌هزینه، بدون پروسهٔ مستقل):** یک چکِ جدید به `dashboard_doctor.py` که «هر diff روی `ARCHITECT_CHARTER.md`/`LEARNING-CONTRACT.yaml`/`MUTATION-WHITELIST.md` بدون ردیفِ verdictِ مالک = CRITICAL». چون STATE می‌گوید `runtime: interactive-sessions-only`، این تنها enforceِ عملیِ ممکن الان است.
  - **فاز ۴ (وقتی حلقه پروسهٔ مستقل گرفت — NSSM در `LAPTOP-RUNTIME`):** آن ۳ فایل را در سطح OS برای هویتِ اجرایِ حلقه read-only کن؛ مسیرهای نوشتنِ مجاز writable بمانند.
- **verdict آری لازم:** چکِ دکتر را الان اضافه کنم (به‌صورت پیشنهاد کد جدا)؟ و read-only OS را به milestone فاز ۴ ببندم؟

### D-radar — رادار آیندهٔ ۲۴ماهه (Q3، کم‌فوریت، بدون تعارض)
- artifactِ پیش‌نگری نداری. تحقیق قالبِ سبک می‌دهد: هر آیتم = {نام، حلقهٔ Adopt/Trial/Assess/Hold، برچسب اطمینان، «چه شاهدی نظرم را عوض می‌کند»، تاریخ بازنگری}، مرور فصلی. تعارضی با ژنوم ندارد؛ صرفاً یک نوتِ جدید در `architect/` است. **پیشنهاد: بسازمش فقط اگر خواستی — اولویت پایین.**

---

## ۴. سه ادعای تحقیق که باید دور ریخته شوند (پروژه‌ات باهوش‌تر است)

1. **«دکتر هفتگی Opus-tier»** ❌ — دکترِ فعلی `zero-LLM` و قطعی است؛ جایگزینیِ آن با یک دکترِ LLMِ هفتگی هم گران‌تر است هم غیرقطعی = پس‌رفت. نگه‌دار.
2. **«اسکن دقیقه‌ای فاجعه است»** ⚠️ — سیستمِ تو دقیقه‌ای نیست؛ حلقه ساعتی است و لاین‌های `*/3,*/5` عمداً dark. (اما اقتصادِ Q5 را **نگه‌دار** به‌عنوان شاهدِ کمّی برای «dark ماندنِ» آن لاین‌ها.)
3. **«کش گرمِ API»** ❌ — استفاده نمی‌کنی؛ مسئلهٔ perceptionِ واقعیِ تو FUSE stale-view است (که با `stable_read` در `DOCTOR-BLUEPRINT` حل می‌شود، نه با batch).

---

## ۵. تصمیم‌هایی که فقط آری می‌تواند بدهد (verdict لازم)

1. **جهتِ D1:** واقعیت (L1-propose-only) درست است و قرارداد به عقب هماهنگ شود؟ یا واقعاً L3/active را الان می‌خواهی (با تأیید پیش‌شرط‌ها)؟ — *توصیه: هماهنگی با واقعیت.*
2. **D2:** تأیید LIFTED بودنِ گیت → sync کردنِ STATE.
3. **D3:** تثبیت `MUTATION-WHITELIST.md` به‌عنوان تنها whitelist + صریح‌کردنِ مرزِ scopeِ callِ خارجی.
4. **D4:** افزودن چکِ genome-diff به دکتر الان؟ + read-only OS در فاز ۴؟
5. **D5 (اختیاری):** برای تغییرِ ژنوم، نسخهٔ سبکِ «کلید دوم» (تأیید مجدد در boot بعدی — ماشینِ موجودِ STARTUP-PROTOCOL) کافی است، یا ۷۲h کاملِ تحقیق؟ — *توصیه: نسخهٔ سبک.*
6. **D-radar:** رادار آینده ساخته شود یا فعلاً نه؟

---

## ۶. ردیف‌های ledger پیشنهادی (اگر verdict داده شد — kind=propose)

> اگر تأیید کردی، این ردیف‌ها در `_memory/EXPERIENCE-LEDGER.md` / `MUTATION-LEDGER.md` append می‌شوند (من مسیر نوشتن مستقیم ندارم — طبق منشور §۴).

| تاریخ | kind | مبنا | تغییر پیشنهادی | وضعیت |
|---|---|---|---|---|
| 2026-07-06 | propose | این سند §۲ D1 | هماهنگیِ `LEARNING-CONTRACT.mode` با واقعیتِ STATE (L1) | pending-verdict |
| 2026-07-06 | propose | این سند §۲ D2 | sync `STATE.security_gate_status` → LIFTED (منشور §۲) | pending-verdict |
| 2026-07-06 | propose | این سند §۲ D3 | تثبیت WHITELIST به‌عنوان تک‌whitelist؛ annotate ENGINE-PROMPT §۰ | pending-verdict |
| 2026-07-06 | propose | این سند §۳ D4 | چکِ genome-diff در دکتر + read-only OS فاز ۴ | pending-verdict |

---

*این سند فقط پیشنهاد است. هیچ فایل ژنوم/کد تغییر نکرد. اعمالِ هر دیف = verdict صریح آری (منشور §۱/§۷).*
