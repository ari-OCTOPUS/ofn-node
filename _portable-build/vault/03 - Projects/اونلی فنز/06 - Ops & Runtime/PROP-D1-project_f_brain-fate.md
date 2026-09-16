---
type: report
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: idea
created: 2026-07-12
updated: 2026-07-12
created_by: agent
sources:
  - "[[PROJECT-F-BRAIN-SPEC]]"
  - "[[brain/BRAIN-BENCHMARK-2026-07-10]]"
  - "[[00 - Control/SOURCE-OF-TRUTH-MATRIX]]"
  - "[[00 - Control/HANDOFF-NEXT-AGENT]]"
tags: [project-f, brain, orchestration, hitl, runtime, decision, propose-only]
aliases: ["PROP-D1", "سرنوشت project_f_brain", "Brain Fate Decision"]
---

# PROP-D1 — سرنوشتِ `brain/project_f_brain.py` (spec-canonical ولی runtime-dead)

> **این یک PROPOSAL است، نه تصمیم.** PLAN ≠ APPROVAL ≠ EXECUTION. هیچ کد/انتقال/اجرا اینجا دستور داده نمی‌شود. سه گزینه با فرمتِ PMO (Current / Delta / Preserved / Rollback) آمده؛ یک گزینه با استدلال توصیه شده و صریحاً **در انتظارِ رأیِ مالک** علامت خورده.
> نام‌گذاری: **C = the creator** (استودیوی محتوا)، **A = the operator** (کاکپیت). لِیبل‌های مسیرِ داخلِ کد به‌جای اکو، با anchor ذکر شده‌اند.

---

## ۱. مسئله در یک خط `[FACT]`

`PROJECT-F-BRAIN-SPEC.md` حول یک شیء نوشته شده — `ProjectFBrain` (۷ زیرعامل، routingِ tiered HITL: low→C / high→A، و `archive()` برای «چه چیزی کار کرد») — که **در هیچ نقطه‌ای از runtime نمونه‌سازی نمی‌شود**. حلقهٔ زنده (`orchestrator.py`) از `DualBrainV3` استفاده می‌کند (۱۰ زیرعاملِ فکر + ۷ خروجیِ متنی، **بدون** routingِ tiered، **بدون** `archive()`). مرکزِ ثقلِ اسپک، مرده است.

---

## ۲. شواهدِ فایل‌محور (چه چیزی زنده است، چه چیزی مرده)

### ۲.۱ شیءِ مرده
| مؤلفهٔ اسپک | anchor | وضعیت |
|---|---|---|
| کلاس `ProjectFBrain` | `brain/project_f_brain.py:81` | تعریف شده، هرگز instantiate نمی‌شود |
| `process_draft()` — HITLِ tiered | `brain/project_f_brain.py:177` | فقط تعریف |
| routing: low→creator / high→operator | `brain/project_f_brain.py:199-207` | لِیبل‌های مسیر hard-coded؛ فقط `kind=="price"` = high-risk |
| `archive()` + persist به `archive.json` | `brain/project_f_brain.py:213-222`، مسیر `:33-34`، I/O `:91-108` | تعریف؛ خروجیِ آن (`brain/archive.json`) فقط ۳ ردیفِ **تستی** دارد (۲ approved + ۱ rejected) |
| گواهِ عدم‌اتصال | grep سراسری روی `*.py` | تنها ارجاع به `ProjectFBrain`/`project_f_brain` = خودِ فایل + یک کامنت در `brain/dual_brain.py:47` |

### ۲.۲ شیءِ زنده
| مؤلفه | anchor | نکته |
|---|---|---|
| `DualBrainV3` (مغزِ حلقهٔ زنده) | `orchestrator.py:17` (import)، `orchestrator.py:53` (`self.brain = brain or DualBrainV3()`) | control-plane واقعی |
| `think_and_communicate()` | `brain/dual_brain_v3.py:389` | خروجی: thoughts + messages؛ **همه** `human_gated=True` به‌صورت **flat** |
| گیتِ compliance/ethics | `brain/dual_brain_v3.py:75-76` (`_checks_pass`) + `:245-247` | **all-or-nothing**: یا همه thoughts تولید می‌شوند یا یک `[blocked]` واحد — نه drop/route به‌ازای هر پیشنهاد |
| فیلترِ متن | `brain/dual_brain_v3.py:69-72` (`_guard_text`) | فقط forbidden-terms روی متنِ خروجی |
| checks در حلقه | `orchestrator.py:104-105` | همهٔ قواعد **True** فرض می‌شوند → گاردها در حلقهٔ زنده عملاً تهی‌اند |
| حافظهٔ تطبیقیِ واقعی | `brain/learning.py` + `brain/acquisition.py` (طبق `PROJECT-F-CONTROL-MANIFEST.json:68,123`) | «چه چیزی کار کرد» در واقع اینجا زندگی می‌کند (bandit/recency)، **نه** در `archive.json` |
| گواهِ اجرای واقعیِ حلقه | `brain/hebb_orch.json` (۲۱۶ co-occurrence، `last_seen≈2026-07-11`) | orchestrator با `DualBrainV3` واقعاً tick خورده |
| مصرف‌کننده‌های زندهٔ دیگرِ `DualBrainV3` | `langar/langar_bot.py:263`، `studio/studio_telegram_v3.py:70,154` | (studio_telegram_v3 خودش deprecated است — matrix:66) |

**خلاصهٔ واگرایی:** `DualBrainV3` غنی‌تر است (۱۰ vs ۴ زیرعاملِ فعال در `process_draft`) و پیام‌های واقعی‌ای می‌سازد که پایین‌دست (`/brief` کاکپیت و استودیو) مصرف می‌کنند؛ ولی مدلِ حاکمیتیِ آن **تخت** است (همه‌چیز gated، بدونِ tieringِ ~۹۵/۵ و بدونِ archiveِ approval-gated). `ProjectFBrain` مدلِ حاکمیتیِ قوی‌تر (tiered + archive، هم‌ترازِ الگوهای ۲۰۲۷ طبق بنچمارک §۲) را دارد ولی پیاده‌سازی‌اش کم‌عمق است (رشته‌های hard-coded؛ گاردها محتوا را بازرسی نمی‌کنند، فقط وجودِ ۱۲ کلیدِ قاعده را چک می‌کنند) و به هیچ‌جا وصل نیست.

### ۲.۳ هازاردِ جانبی — اسنادِ کنترلی به ماژولِ مرده اشاره می‌کنند `[FACT]`
این مستقل از هر گزینه‌ای باید اصلاح شود، چون سطحِ کنترلِ agentِ مادر را به کدِ مرده می‌بندد:

| فایل:خط | ادعا | واقعیت |
|---|---|---|
| `PROJECT-F-CONTROL-MANIFEST.json:67` | capability `brain_hitl` → `"runtime": "brain/project_f_brain.py"` | runtime واقعی = `dual_brain_v3.py` + `orchestrator.py` |
| `PROJECT-F-CONTROL-MANIFEST.json:121` | `programmatic_api.ProjectFBrain` با `process_draft/archive/...` | این API زنده نیست |
| `AGENT-CONTROL-INTERFACE.md:66` | «سپردنِ تحلیل → مغز `process_draft()`» | متدِ مرده |
| `README.md:36` | `project_f_brain` را جزوِ «کد زنده» فهرست می‌کند | مرده |
| `brain/BRAIN-BENCHMARK-2026-07-10.md:21` | «route tiered (قیمت→A) کار می‌کند؛ archive persist می‌شود» | فقط در تستِ ایزوله، نه در حلقه |
| `PROJECT-F-FULL-REPORT-2026-07-09.md:74` | «test-green، وصل نیست» | ✅ این یکی صادق است |
| `SOURCE-OF-TRUTH-MATRIX.md:67` | «spec-canonical ولی runtime-dead / هیچ‌جا instantiate نمی‌شود» | ✅ صادق — نقطهٔ مرجعِ این PROP |

> **دو نسخهٔ اسپک وجود دارد:** `PROJECT-F-BRAIN-SPEC.md` (root) **و** `docs/PROJECT-F-BRAIN-SPEC.md`. هر گزینه‌ای که اسپک را لمس کند باید **هر دو** را در نظر بگیرد.

---

## ۳. سه گزینه (فرمتِ PMO)

### گزینهٔ A — WIRE: اتصالِ `project_f_brain` به orchestrator (فعال‌سازیِ tiered HITL + archive)

- **Current:** `orchestrator.py:53` مستقیماً `DualBrainV3()` می‌سازد؛ `ProjectFBrain` بی‌مصرف؛ `archive.json` فقط fixture. `langar_bot.py:263` هم مستقلاً `DualBrainV3()` می‌سازد.
- **Delta (چه تغییر می‌کند):**
  - سواپِ خام غیرممکن است — `ProjectFBrain.process_draft` فقط ۴ `Proposal` با رشته‌های hard-coded می‌سازد (`:113,133,141,147`) و متنِ واقعیِ پیام‌ها را تولید نمی‌کند؛ جایگزینیِ کاملِ `DualBrainV3` یعنی از دست‌رفتنِ ۶ زیرعاملِ فکر + کلِ لایهٔ CommBrain که `/brief` و استودیو مصرف می‌کنند.
  - مسیرِ عملی = نوشتنِ یک **adapter**: خروجیِ `DualBrainV3` (thoughts/messages) را از `compliance_guard`/`ethics_guard`/route + archiveِ `ProjectFBrain` عبور دهد (کدِ glueِ جدید، نه صرفاً «wiring»).
  - callbackِ verdict→archive: پس از رأیِ A در صفِ verdict (`VERDICT_QUEUE.md`, `THREAD-CLOSURE-D §9`)، فراخوانیِ `brain.archive(kind, outcome)`. پلامبینگِ جدید.
  - لمسِ ۲ فایلِ canonicalِ زنده (`orchestrator.py`, `langar_bot.py`) + احتمالاً TickResult contract.
- **Preserved:** خطوطِ قرمز (propose-only، دوکلیده، ۲٪-cap، λ_persist<0)؛ لایهٔ learning (`learning.py`/`acquisition.py`) دست‌نخورده؛ شکلِ پیام‌های `DualBrainV3` اگر adapter آن‌ها را pass-through کند.
- **What breaks:** اگر مسیرِ سواپ (نه adapter) انتخاب شود → شکلِ `TickResult.messages` عوض می‌شود و `/brief` کاکپیت + فیدهای استودیو می‌شکنند؛ آلودگیِ `archive.json` (ردیف‌های واقعی روی fixtureهای تست)؛ گاردهای `orchestrator.py:104-105` که همه‌چیز را True فرض می‌کنند با گیتِ سختِ `ProjectFBrain` تناقض پیدا می‌کنند.
- **Effort:** `[EST]` **Medium-High** — adapter + verdict-archive callback + ۲ call-site + تست‌های جدید.
- **Risk:** `[EST]` **High** — تنها حلقهٔ کاریِ سیستم را برای فیچری به خطر می‌اندازد که پیاده‌سازیِ فعلی‌اش کم‌عمق است (فقط `price` = high؛ گاردها محتوا نمی‌خوانند). ceremony زیاد، ایمنیِ واقعیِ افزوده کم.
- **Rollback:** پشتِ یک flag (پیش‌فرض off) → `git revert` تمیز؛ ولی ردیف‌های واقعیِ archive باید دستی پاک شوند (state pollution). بدونِ flag، rollback = revert دو فایل + پاک‌سازیِ state.

### گزینهٔ B — REWRITE: بازنویسیِ اسپک تا با واقعیتِ `DualBrainV3` بخواند

- **Current:** اسپک (×۲ نسخه) + مانیفست + interface + README واقعیتِ نادرست را روایت می‌کنند (بخش ۲.۳).
- **Delta:**
  - `PROJECT-F-BRAIN-SPEC.md` **و** `docs/PROJECT-F-BRAIN-SPEC.md`: «۷ زیرعامل» → «۱۰ thinking + ۷ comm»؛ «tiered low→C/high→A» → «flat human-gated + گیتِ all-or-nothing + فیلترِ forbidden-terms»؛ «`archive()`» → «حافظهٔ bandit/recency در `learning.py`+`acquisition.py`».
  - `PROJECT-F-CONTROL-MANIFEST.json:67,121`: repoint `brain_hitl` → `dual_brain_v3.py`+`orchestrator.py`؛ جایگزینیِ ورودیِ `ProjectFBrain` با `DualBrainV3.think_and_communicate`.
  - `AGENT-CONTROL-INTERFACE.md:66` و `README.md:36`: repoint.
  - `BRAIN-BENCHMARK:21` را به «spec-target، نه live» annotate کن.
  - **حفظِ صریحِ tiered-HITL + approval-gated-archive به‌عنوان roadmap/north-star** (وگرنه یک طراحیِ قوی‌ترِ حاکمیتی از روایتِ «canonical» حذف می‌شود).
- **Preserved:** کلِ runtime (صفر تغییرِ کد)؛ `project_f_brain.py` به‌عنوان reference-implementation سرِ جای خود؛ همهٔ گاردها.
- **What breaks:** هیچ‌چیزِ runtime. تنها هزینه: مدلِ tiered/archive از «توصیفِ جاری» به «هدفِ آینده» تنزل می‌کند (باید صریح preserved شود تا گم نشود).
- **Effort:** `[EST]` **Low-Medium** — ویرایشِ سندی در ~۵-۶ فایل، بدونِ ریسکِ کد.
- **Risk:** `[EST]` **Low** — docs-only.
- **Rollback:** `git revert` ویرایش‌های سندی.

### گزینهٔ C — ARCHIVE: بازنشستگیِ `project_f_brain` به‌عنوان کدِ مرده

- **Current:** ماژول مرده ولی سرِ جای خود؛ اسناد به آن اشاره می‌کنند.
- **Delta:**
  - طبق قاعدهٔ #۱ منشور (**هرگز حذف، فقط انتقال**): `brain/project_f_brain.py` → `09 - Archive`؛ `brain/archive.json` (fixture) هم همراهش.
  - سپس **ناچاراً** همان اصلاحاتِ سندیِ بخش ۲.۳ (مانیفست:67،121؛ interface:66؛ README:36؛ benchmark:21) لازم است — وگرنه dangling reference. یعنی C ⊂ کارِ سندیِ B **به‌علاوهٔ** یک move.
  - اسپک همچنان دربارهٔ ماژولی حرف می‌زند که حالا در انباری است → بدنهٔ اسپک هم باید بازنویسی شود (دوباره کارِ B).
- **Preserved:** runtime؛ برگشت‌پذیریِ کامل (git + انتقالِ غیرمخرب).
- **What breaks:** هیچ‌چیزِ runtime. مرجعِ پیاده‌سازیِ tiered/archive از دسترسِ کاری خارج می‌شود؛ اگر بعداً A خواسته شود باید از archive/git احیا شود.
- **Effort:** `[EST]` **Low-Medium** — ۱ انتقال + همان اصلاحاتِ سندیِ B.
- **Risk:** `[EST]` **Medium** — حذفِ north-starِ طراحی از لایهٔ کدِ فعال؛ ادعای test-green بنچمارک تاریخی می‌شود.
- **Rollback:** انتقالِ معکوس از `09 - Archive` (منشور تضمینِ غیرمخرب می‌دهد).

---

## ۴. توصیه — **گزینهٔ B** (بازنویسیِ اسپک به واقعیت) `[PROPOSAL — در انتظارِ رأیِ مالک]`

**استدلال:**

1. **دو واقعیتِ مستقل، یک نتیجه.** (الف) سیستمِ زنده هم‌اکنون با مدلِ flat-gatedِ `DualBrainV3` کار می‌کند (`hebb_orch.json` اجرای واقعی را ثابت می‌کند) و پایین‌دست حولِ شکلِ پیام‌های همان مغز ساخته شده. (ب) اسناد دربارهٔ runtime **دروغ** می‌گویند (بخش ۲.۳). واقعیتِ (ب) صرف‌نظر از هر گزینه‌ای باید اصلاح شود؛ B این را با کمترین ریسک انجام می‌دهد.
2. **چرا A نه (حالا):** A فیچرِ حاکمیتی را تحویل می‌دهد ولی تنها حلقهٔ کاری را به خطر می‌اندازد، و پیاده‌سازیِ فعلیِ `ProjectFBrain` کم‌عمق است (فقط `price` high-risk؛ گاردها محتوا نمی‌خوانند — `:155,167`). A یک **فازِ آیندهٔ مشروط** است، منوط به رأیِ صریحِ مالک که «مدلِ tiered باید زنده شود»، و آنگاه باید **adapter (گیتِ `ProjectFBrain` روی خروجیِ `DualBrainV3`)** نوشته شود، نه سواپِ مغز.
3. **چرا C-خالص نه:** C از نظرِ کارِ سندی زیرمجموعهٔ B است **به‌علاوهٔ** یک انتقال، و مرجعِ پیاده‌سازیِ طراحیِ tiered/archive (که بنچمارک §۲ آن را هم‌ترازِ الگوهای ۲۰۲۷ می‌داند) را از لایهٔ فعال بیرون می‌برد. B همان کد را به‌عنوان reference/roadmap نگه می‌دارد و در عینِ حال اسناد را صادق می‌کند.

**شکلِ پیشنهادیِ B (اگر مالک تأیید کند):** اسپک را reconcile کن + tiered-HITL و approval-gated-archive را صریحاً به‌عنوان **north-starِ فازِ بعد** ثبت کن؛ انتقالِ فیزیکیِ `project_f_brain.py` (C) به‌عنوان add-onِ اختیاری باز بماند؛ A را به‌عنوان فازِ آیندهٔ مبتنی‌بر-adapter پشتِ رأیِ مالک نگه دار.

> این توصیه **PROPOSAL** است. تا رأیِ مالک، هیچ سند/کدی لمس نمی‌شود و هیچ سندی سندِ دیگر را overwrite نمی‌کند (هم‌راستا با `SOURCE-OF-TRUTH-MATRIX.md:72`).

---

## ۵. قلابِ verdict (برای صفِ تصمیم)

- **تصمیمِ لازم از مالک:** A / B / C — «آیا مدلِ tiered-HITL + approval-gated-archive باید زنده شود (A، فازِ آینده)، یا اسپک به واقعیتِ flat-gated بازنویسی شود (B، توصیه)، یا ماژول بازنشسته شود (C)؟»
- **منبعِ تسک:** `00 - Control/HANDOFF-NEXT-AGENT.md:57` (آیتم D1).
- **پیش‌شرطِ مشترکِ هر سه گزینه:** اصلاحِ ارجاعاتِ سندیِ بخش ۲.۳ (مانیفست/interface/README) — این خودش نیازمندِ رأی نیست چون فقط واقعیت را ثبت می‌کند، ولی چون بدنهٔ اسپک را لمس می‌کند در قلمروِ همین verdict قرار می‌گیرد.

---

*همهٔ محتوا propose-only و read-only تولید شده؛ صفر اکشنِ بیرونی؛ anchorها روی نسخهٔ worktreeِ `F:\backup` در `2026-07-12`.*
