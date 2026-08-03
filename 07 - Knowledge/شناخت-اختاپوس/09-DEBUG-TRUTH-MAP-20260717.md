# 🐛 Truth Map — Debug Diagnostic Report

> **تاریخ:** 2026-07-17 شب (probe window ~22:15–22:45 AEST) | **ایجنت:** OCTOPUS DEBUG & DIAGNOSTIC AGENT (طبق `08-DEBUG-AGENT-MEGAPROMPT.md` v1.1)
> **روش:** ۶ حسگرِ موازیِ فقط‌خواندنی (فرضیه→محرک→مشاهده)، ۱۹۵ probe، صفر mutation، صفر اجرای اسکریپت، `.env` هرگز باز نشد.
> **دامنه:** T1..T12 + U1..U13. همه‌چیز propose-only — هیچ patchی اعمال نشده.

---

## A) Executive State

**وضعیت کلی: `DEGRADED-but-honest`** — ارگانیسم زنده و تازه است (beat 7706، ts 22:15:24، halted=null) ولی روی **کدِ کهنه** می‌چرخد، چند رفلکسِ حفاظتی‌اش **کور** است، و یک لایهٔ گاورنر **خراب-باز** است.

### ۳ ریسکِ با اولویتِ بالا

| # | ریسک | severity | شاهد |
|---|---|---|---|
| R1 | **secret در فایلِ «غیرمحرمانه»**: `OCTOPUS-flags.cmd:111-112` مقدارِ واقعیِ `TG_CENTER_BOT_TOKEN` + `TG_CENTER_CHAT_ID` را دارد، در حالی که headerِ خودش (خط ۲) می‌گوید non-secret؛ ۷ لانچرِ `.bat` صدایش می‌زنند. untracked در git (فقط روی دیسک، نه تاریخچه) | **HIGH** | `_ops/OCTOPUS-flags.cmd:2` vs `:111-112` |
| R2 | **بوتِ کهنه + کاکپیتِ کور**: پروسهٔ در حالِ اجرا (بوت 19:12:57) از `organism.py`ِ دورهٔ `abbd2d5` است؛ ۳ کامیتِ بعدی (`4976005`/`2250ab0`/`eeed04e` — شاملِ فیکسِ state-clobber و حسگرِ نسخه) روی دیسک‌اند ولی **لود نشده‌اند**. تنها سطحی که این کهنگی را نشان می‌داد (کاکپیتِ 8773) هم **DOWN** است — کهنگی الان از هیچ‌جا دیده نمی‌شود | **HIGH** | `git log -- _ops/organism.py` + `started` + curl 8773 → exit 7 |
| R3 | **رفلکسِ دردِ کور**: `organism.py:367-368` به عصبِ درد `spectral={}` و `sensory={}` می‌دهد و `neural_driver` هم error_rate/partner_stress را forward نمی‌کند → ۴ از ۶ ورودیِ pain همیشه صفر؛ `protective_halt` (pain>0.7) عملاً غیرقابل‌وصول مگر با اضافه‌خرجِ بزرگِ پولی. تیترِ «رفلکسِ سرکوب‌ناپذیر» در سیم‌کشیِ زنده واقعی نیست | **HIGH** | `organism.py:367-368` · `neural_driver.py:69-74` · `nociceptor.py:59-62` |

**آمار:** ۵۲ FACT · ۹ INFERENCE · ۴ BLOCKED (policy) · ۱۲ contradiction (۲ high) · ۱۳/۱۳ Unknown → **۱۱ حل‌شده، ۲ نیمه‌حل** · ۲ ابطالِ Knowledge Pack.

---

## B) Evidence Table (گزیدهٔ بار-بَر؛ ارجاعِ کامل در متنِ C/D)

| ID | گزاره | برچسب | شاهد (file:line) |
|---|---|---|---|
| B1 | ارگانیسم زنده: beat 7706، profile paper-full، halted=null، ۴ بوتِ امروز (09:02، 12:24، 18:07، 19:12) | FACT | `state/ORGANISM-STATE.json` · `_memory/HEARTBEAT.md` |
| B2 | فقط 8771+8772 گوش می‌دهند؛ 8773 (کاکپیتِ زنده) و 8770 مرده | FACT | curl + TCP listen table |
| B3 | organism.py در حالِ اجرا کهنه است (پیش-`4976005`)؛ wiring.py و live_loop.py کهنه **نیستند** (قبل از بوت آخرین‌بار عوض شده‌اند) | FACT | `git log -1 -- <file>` × ۳ + mtime |
| B4 | سایدکارِ نسخه فقط یک‌بار **در بوت** نوشته می‌شود (`organism.py:213`)؛ غیبتش = بوتِ پیش-کد، نه باگِ نوشتن | FACT | `organism.py:66,77-94,213` + `git log -S CODE_SIDECAR` |
| B5 | ترس الان **اجرایی** است نه فقط گزارشی: `auto_approve.self_test` بلاک، `code_autonomy` → freeze؛ و همین الان engaged (`in_fear=['legs']`, stress=1.0) | FACT | `auto_approve.py:86-92,154-159` · `code_autonomy.py:63-84,249-251` · `stress-latest.json` |
| B6 | دامنهٔ ترس محدود است: حلقهٔ اصلیِ tick/پول/لگ‌ها ترس را مصرف نمی‌کنند — فقط لِین‌های خود-تغییری | FACT | grep `in_fear` سراسر `_ops` + `organism.py:350-721` |
| B7 | واحدِ بودجهٔ cardiac = beat (نه دلار)؛ امروز depleted: spent 327 > cap 288؛ `spend("active")` بی‌قیدوشرط حتی بعد از depletion؛ `resting` هرگز خرج نمی‌شود | FACT | `cardiac.py:43,137-152` · `organism.py:704-705` · `cardiac-budget.json` |
| B8 | اثرِ خوابِ depletion توسط قلبِ هیبرید **mask** می‌شود: بلاکِ heart (`organism.py:711-718`) دو خط بعدْ `_sleep_s` را با 900s بازنویسی می‌کند | FACT | `organism.py:699-718` + state `heart.period_shadow_s=900` |
| B9 | گاورنرِ زنده = `governor_epoch.run_epoch` درون-پروسه، هر epochِ آلوستاتیک؛ shadow/propose-only؛ ۲۸۴ فایلِ epoch | FACT | `organism.py:386-391` · `governor_epoch.py:3,241,284-379` |
| B10 | گاورنرِ LLM «خراب-باز»: گیتِ دوقفله باز (هر دو flag-file موجود) ولی هر epoch با `PriceNotLocked` می‌میرد → سقوطِ بی‌صدا به dry؛ ۹۵ تکرار، آخری 22:15:22 | FACT | `governor_epoch.py:245-281` · `debate/client.py:72-74` · `governor-alerts.md` |
| B11 | `governor_shadow.py` هرگز اجرا نشده: هدفِ اولین-نوشتنش (`04 - Architect System\_memory\HEARTBEAT.md`) اصلاً وجود ندارد | INFERENCE | `governor_shadow.py:11-34` + Test-Path=False |
| B12 | box روی مسیرِ tick هست ولی سه-قفله (epochِ دکتر + bottleneck-یافت‌شده + attention) و به‌احتمالِ قوی هرگز step نکرده (rfcs.json خالی، صفر ردِ دیسکی به‌طراحی) | FACT+INFERENCE | `doctor.py:735-740,776-777,794` · `state/doctor/rfcs.json` |
| B13 | `octopus_core` سایدکارِ یتیم: صفر import از `_ops`؛ گزارشِ rebuild خودش آن را adaptor می‌داند که attach-هایش «راهنما برای ایجنتِ بعد» ماند | FACT | grep + `OCTOPUS-v2-REBUILD-REPORT.md:94-127` |
| B14 | جدولِ حقیقتِ فلگ‌ها: **23 LIVE · 15 ENABLED-NO-EVIDENCE · 1 ENABLED-SKELETON (mining) · 8 DORMANT · 1 ON-BRANCH (PROPOSAL_BUTTONS) · 1 DEAD** | FACT | `_ops/OCTOPUS-flags.cmd` (۲۰×=1، ۲×=0) + `wiring.py:82-128` + `/api/organism` |
| B15 | فلگِ مرده: `OCTOPUS_WIRE_SELF_IMPROVE_AUTO=1` را **هیچ کدی نمی‌خواند**؛ گیتِ واقعیِ آن لایه = فایلِ `ACTIVATION-SELF-IMPROVE-AUTO.flag` (که هست → لایه روشن است، از راهِ دیگر) | FACT | grep تک-hit در خودِ `.cmd` · `cortex/improve.py:41` |
| B16 | مسیرِ ایمیل→کارت روی **شاخه** است نه master: `prop:` روی live صفر رخداد؛ `OCTOPUS_WIRE_EMAIL/INGEST` روی live اعلان‌شده ولی هیچ‌جا set نشده (DORMANT) | FACT | grep live vs `git show claude/ollama-fugu-brain-54c897` |
| B17 | مصرفِ پولیِ واقعی این بوت صفر است با وجودِ گیتِ باز (genome ledger ۰ رویداد، core.db ۰ ردیف)؛ آخرین هشدارِ بی‌کلیدی 2026-07-15 | FACT | `telemetry-latest.json` · `governor-alerts.md` |
| B18 | `lead-inbox` روی live وجود ندارد — سرِ لولهٔ خشک هنوز هرگز ننوشته (همه‌ی producerها flag-off) | FACT | listing `state/legs` |

---

## C) Unknowns Resolved (U1..U13)

| U | حکم | خلاصهٔ شاهد |
|---|---|---|
| **U1 pacemaker** | ✅ حل — **ARTIFACT است، نه عضوِ مرده.** عضوِ «pacemaker» در جدولِ innervation همان spine است که با تازگیِ `ORGANISM-STATE.json` و **SLA=5min** نمره می‌گیرد (`innervation.py:30`)؛ ولی cadenceِ واقعیِ tick الان **900s** است (heart wire_open → `organism.py:711-718`). آستانهٔ قرمز 3×SLA=15.0min و سنِ اندازه‌گیری‌شده 15.1min — هر tick با **~۶ ثانیه** اختلاف قرمز می‌شود. دو منبعِ beat خلط شده‌اند: chrono-pacemakerِ واقعی هر 60s در `chrono.db` می‌تپد (`chrono.py:34,706-717`) ولی innervation هرگز chrono.db را نمی‌خواند. بدتر: `innervation.persist` در **همان tick و ~۶۰ms قبل از** بازنویسیِ state اجرا می‌شود (`organism.py:651` قبل از `:661`) پس سنِ measured همیشه بدترین-حالت است. |
| **U2 stale boot** | ✅ حل — **بله، کهنه است، و فقط organism.py.** بوت 19:12:57؛ commits `4976005` (20:09)، `2250ab0` (20:18)، `eeed04e` (20:46) بعد از بوت. wiring/live_loop skew ندارند. سایدکار غایب چون کدِ نوشتنش ۵۷ دقیقه بعدِ بوت متولد شد؛ **در restartِ بعدی خودش ظاهر می‌شود** (falsifier: اگر بعد از restart هم غایب بود → باگِ واقعیِ مسیرِ نوشتن). K17 تأیید+تدقیق. |
| **U3 epistemics** | ✅ حل — **خطای دسته‌بندی در صورت‌سؤال:** `make_epistemics()` هیچ‌جا وجود ندارد؛ سیم = `wiring.epistemics_beat` (`wiring.py:770`، فراخوان `organism.py:629`) با ۳ قفلِ داخلی (flag → STOP/halted → epoch هر 720). در runtime فلگ **روشن** است (K7 حل: README کهنه است، mtime 9/07، دو روز قبل از unlockِ مالک 2026-07-11). اما خروجی‌ها ساختاراً پوچ‌اند: upstreamها خالی/TODO و `wire_reconcile/fitness=false`. |
| **U4 nociceptor** | ✅ حل — مسیر وجود دارد و **enforce می‌شود** (`protective_override` → `_protective_skip=True` که epoch/fitness/replication را skip می‌کند، `organism.py:364-377,386,405`) **ولی ورودی‌هایش گرسنه‌اند** (R3). سپرهای sigma که واقعاً زنده‌اند جای دیگرند: `code_autonomy` sigma≥1→freeze، `stress` sigma≥0.75→fear، doctor→RFC. |
| **U5 model_router** | ✅ حل — `ask()` **هیچ** ورودیِ گاورنر/بودجه‌ای قبل از انتخاب نمی‌خواند: نقشهٔ ثابتِ tier + `CORTEX_LOCAL_FIRST=1` (فقط برای secondary؛ primary هرگز local-first نمی‌شود) + کلید-موجودی + flag-fileهای paid + `organ_gate.reserve` فقط در لحظهٔ اجرا. `CORTEX_ROUTE_SCORER` تنظیم نیست → scorer خفته. گیتِ paid **امروز باز** است (سه فایلِ ACTIVATION موجود). |
| **U6 daily_cap 288** | ✅ حل — **عقلانی**: 288 = 86400s ÷ 300s (یک beat در هر tickِ ۵ دقیقه‌ای؛ کامنت در `cardiac.py:43`، تولد `14f94f4` 2026-07-09). ولی در عمل «جیرهٔ ۲۴ساعته» نیست: bio_rhythm با pace «mice» (42s) در ~۳٫۴ ساعت خرجش می‌کند؛ و چون `spend("active")` بی‌شرط است و resting هرگز خرج نمی‌شود، شمارنده از سقف رد می‌شود (327>288) — نیمه-سیم‌کشی. |
| **U7 box tick** | ✅ حل — روی مسیرِ زنده هست: tick → `doctor_beat` (epochِ روزانه 1440) → `run_cycle` → `_run_box_cycle` پشتِ `OCTOPUS_WIRE_BOX=1` (`doctor.py:776-777`). ولی **سه‌قفله** و مدرکِ اجرا صفر (rfcs خالی؛ box هیچ ردِ دیسکی نمی‌گذارد) → «armed اما احتمالاً هرگز step نکرده». |
| **U8 octopus_core** | ✅ حل — **سایدکارِ یتیم می‌ماند**: صفر import از `_ops`؛ گزارشِ rebuild خودش آن را integration-guide برای «ایجنتِ بعدی» گذاشته (attachها vapor). جایگزینِ `_ops` نیست. |
| **U9 governor** | ✅ حل — گاورنرِ واقعی درون-پروسه است (`governor_epoch.run_epoch`، هر epoch، ۲۸۴ رکورد، shadow/propose-only). حالتِ LLMاش **خراب-باز** (B10). `governor_shadow.py` (اسکریپتِ جدا) **هرگز اجرا نشده** (B11) — مستنداتِ SETUP-README سرپرستی را توصیف می‌کنند که وجود ندارد. |
| **U10 digest generic** | ✅ حل — حلقهٔ digest روی **کلید**ها generic است و `render_leg_digest` روی `{status, detail, next}` generic؛ افزودنِ pseudo-legِ «demands» صرفاً additive است. **اما هنوز هیچ producerِ demands[] در کلِ `_ops` وجود ندارد** — یک producer کم داریم، نه یک renderer. |
| **U11 wiring vs cortex** | ✅ حل — **هیچ‌کس دروغ نمی‌گوید؛ دو سنجهٔ متفاوت با یک اسم**: بلاکِ wiring فلگِ env را گزارش می‌کند، registryِ کورتکس تازگیِ فایل با SLA چندروزه را. `fitness-latest.json` را یک `fitness.compute()`ِ **بی‌قید** روزانه می‌نویسد (`organism.py:406`) که فلگِ `wire_fitness` را نادیده می‌گیرد (فلگ فقط A2-outbox را می‌بندد)؛ `reconcile-latest` از یک اجرای دستیِ پیش از بوت است. |
| **U12 alignment** | ✅ حل — **کلیدِ بدنام**: journal فیلدِ `aligned` را از `alignment.get('changed')` پر می‌کند (`cortex.py:360`)؛ `changed=false` + دلیلِ «هم‌راستا بود» حالتِ سالمِ no-op است. یافتهٔ جانبی: مسیرهای blocked/error هم دقیقاً همین را ثبت می‌کنند و `reason` هرگز journal نمی‌شود — journal سالم/blocked را تفکیک نمی‌تواند. |
| **U13 cockpit 8773** | ⚠️ نیمه‌حل — **مرگِ کنسولی، بدونِ سرپرست**: لانچر فقط foreground است (`RUN-LIVE.bat`)، هیچ scheduled task/pidfile/logی نیست؛ آخرین heartbeat «live-cockpit=START» 10:30:51 در برابرِ ری‌بوتِ ارگانیسم 19:12:57. فرضیهٔ برتر: پنجرهٔ کنسول بسته شده. باز: مالک 8773 را always-on می‌خواهد یا on-demand؟ |

### ابطال‌های Knowledge Pack (مهم‌ترین خروجی)

| # | ادعای قبلی | حکمِ امروز |
|---|---|---|
| ✗ K11/K12 | «fear فقط گزارش می‌شود؛ حلقهٔ آلوستاتیک وجود ندارد» | **REFUTED (بخشاً):** ترس الان ≥۳ مصرف‌کنندهٔ رفتاری دارد و همین لحظه engaged است (B5) — ولی فقط در لِین‌های خود-تغییری؛ tick/پول هنوز مصرفش نمی‌کنند (B6). مصرف‌کنندهٔ `cardiac.depleted` هم الان هست (`cardiac.py:236-237`) ولی توسط heart مسک می‌شود (B8). |
| ✗ K9 | «سایدکار غایب → شاید بوت stale» | **تدقیق:** غیبت = بوتِ پیش-کد؛ خودِ stale-بودن مستقلاً **اثبات** شد (U2) و با restart هر دو حل می‌شوند. |
| ✓ K4، K15، K7 (با توضیح)، K10 | تأیید شدند | B13، B7، U3، B7 |

---

## D) Anomaly & Contradiction Table

| تناقض | شاهد | severity |
|---|---|---|
| فایلِ «non-secret» با دو secretِ واقعی | `OCTOPUS-flags.cmd:2` vs `:111-112` | **high** |
| تیترِ رفلکسِ درد («unsuppressible, enforced») vs ورودی‌های گرسنه → غیرقابل‌وصول | `organism.py:367-368` · `neural_driver.py:69-74` | **high** |
| گیتِ گاورنر-LLM «باز» vs رفتارِ ۱۰۰٪ dry (PriceNotLocked ×۹۵، ساعتی) | `governor_epoch.py:245-281` · alerts | medium |
| heartbeat ساعتی «organism=ok/healthy» vs همان ساعت‌ها خطای تکرارشونده + بودجهٔ over-cap | `HEARTBEAT.md` vs `governor-alerts.md` | medium |
| `wire_box=true` خوانده می‌شود «box روشن» vs سه‌قفله و صفر مدرکِ اجرا | `doctor.py:735-777` | medium |
| بلاکِ wiring خودش را جدولِ حقیقت جا می‌زند ولی ~۱۰ لایهٔ روشن را کم‌شماری می‌کند (heart/bio/ziman/cartographer/pulse/selfheal/…) | `/api/organism` vs flags | medium |
| GO-LIVE comment فلگِ مرده را «سیمِ لایه» معرفی می‌کند | `flags.cmd:29-36` vs grep | medium |
| مستنداتِ governor_shadow سرپرستی‌ای را توصیف می‌کنند که هرگز نبوده | `SETUP-README.md:44` vs Test-Path | medium |
| README کهنهٔ epistemics («off») vs runtime روشن | mtime 9/07 vs unlock 11/07 | low |
| docstringِ router «قفل تا 21/07» vs گیتِ الان-باز با overrideها | `model_router.py` vs flag-files | low |
| journal `aligned` ≠ معنای aligned (کلیدِ بدنام) | `cortex.py:358-362` | low |
| `chrono.legs` فقط lead-naghshi را می‌شمارد؛ ۴ اندامِ فعالِ دیگر غایب | state | low |
| مسیرهای اشتباه در خودِ مگاپرامپت: flags در `_ops\` است (نه ریشه)، cardiac در `_ops\cardiac.py` (نه `cortex\`) | probe errors | low |

---

## E) Patch Proposals (Phase 2 — بدونِ اعمال؛ همه propose-only)

> ترتیب = اثرْبخشی/ریسک. 🔑 = فقط-مالک.

**P1 🔑 — restartِ ارگانیسم (تعمیرِ صفر-خطی).**
هدف: R2. لودِ `4976005..eeed04e` (فیکسِ state-clobber + حسگرِ نسخه + ledger-verify) و تولدِ خودکارِ سایدکار. فایل: هیچ (اکشنِ مالک). baseline: `ORGANISM-STATE.code` غایب. انتظار: موجود، و `_code_freshness` سبز. shadow: ندارد (خودِ restart). rollback: `git checkout abbd2d5 -- _ops/organism.py` + restart (بعید). پذیرش: تستِ AT-1.

**P2 🔑 — کوچ + چرخشِ secretهای flags.cmd.**
هدف: R1. مالک دو خطِ 111-112 را به مخزنِ env منتقل و توکن را از BotFather بچرخاند (این توکن قبلاً هم در لیستِ چرخش بود). ریسک: اگر ترتیبِ بوت env را قبل از `.bat` لود نکند، باتِ مرکز بی‌توکن می‌شود — اول ترتیبِ لود verify شود. rollback: بازگرداندنِ دو خط (با مقادیرِ چرخیده).

**P3 — بینا-کردنِ عصبِ درد.**
هدف: R3. فایل: `_ops/organism.py:367-368` — به‌جای `{}`، snapshotِ واقعیِ spectral/sensory از همان tick پاس شود؛ و `neural_driver.py:69-74` دو ورودیِ error_rate/partner_stress را forward کند. کوچک‌ترین تغییرِ امن: فقط پرکردنِ dictها، بدون تغییرِ آستانه‌ها. baseline: pain همیشه ≤0.58. انتظار: pain در سناریوی RED+sigma بالا >0.7. shadow: یک tick با logِ مقدارِ pain قبل/بعد. rollback: برگرداندنِ دو خط. تست: AT-3.

**P4 🔑 — قفلِ قیمت یا بستنِ صادقانهٔ گاورنر-LLM.**
هدف: توقفِ ۹۵×خطای ساعتی + هم‌خوانیِ گیت/رفتار. دو راه: (الف) مالک `price_in/price_out` را در `budgets.yaml` قفل کند (فایلِ owner-voted)؛ یا (ب) تا آن موقع `ACTIVATION-GOVERNOR-LLM.flag` برداشته شود تا گیت «بسته» را صادقانه بگوید. rollback: برگرداندنِ flag-file.

**P5 — صادق‌سازیِ بودجهٔ ضربان.**
فایل: `_ops/organism.py:704-705` — بعد از depletion، `spend("resting")` به‌جای `"active"`. اثر: شمارنده دیگر از سقف رد نمی‌شود و `resting` معنا پیدا می‌کند. rollback: یک خط. تست: AT-5. (جداگانه: تقدمِ صریح بینِ resting-clampِ cardiac و heart-override به‌جای last-writer-wins فعلی — تصمیمِ طراحی، پیشنهاد فقط ثبت.)

**P6 — کالیبرهٔ SLAی pacemaker (رفعِ آرتیفکتِ U1).**
فایل: `_ops/cortex/innervation.py:30` — یا SLA پویا از `heart.period_shadow_s` (مثلاً `ceil(period*2/60)`)، یا سنجشِ spine از `chrono.db` (منبعِ ۶۰ثانیه‌ای واقعی). کوچک‌ترین: SLA=20. baseline: dead_spots=[pacemaker] هر tick. انتظار: [] پایدار. rollback: عدد قبلی. تست: AT-6.

**P7 — خوانا-سازیِ journalِ کورتکس.**
فایل: `_ops/cortex/cortex.py:358-362` — افزودنِ `align_changed` + `align_reason` (نگه‌داشتنِ `aligned` یک نسخه برای سازگاری). rollback: حذفِ دو کلید.

**P8 — نام‌گذاریِ صادقِ اعضای registry.**
فایل: `_ops/cortex/registry.py:28,30` — `fitness_report`/`reconcile_report` یا فیلدِ `source: file-freshness` تا /api/cortex خود-توصیف شود و U11 برای همیشه بسته بماند. ریسک: مصرف‌کننده‌های string-match — اول grep.

**P9 🔑 — سرنوشتِ کاکپیتِ 8773.**
تصمیمِ مالک: always-on (→ ثبتِ scheduled task که خودِ `.bat` مستند کرده + `heartbeat('live-cockpit=STOP')` در `finally` دورِ serve_forever تا مرگ visible شود) یا on-demand (→ سطح‌های وضعیت دیگر 8773 را جزوِ «مجموعهٔ زنده» جا نزنند). ملاحظه: autostart یک سرورِ با-اکشنِ‌مالک را بی‌مراقب بالا می‌آورد — صراحتاً owner-call.

**P10 — پاک‌سازیِ فلگِ مرده.**
فایل: `_ops/OCTOPUS-flags.cmd:36` — حذفِ `SET OCTOPUS_WIRE_SELF_IMPROVE_AUTO=1` + اصلاحِ کامنتِ GO-LIVE به نامِ گیتِ واقعی (`ACTIVATION-SELF-IMPROVE-AUTO.flag`). امروز no-op است؛ فقط حقیقت‌رسانی.

**P11 — کامل‌سازیِ بلاکِ wiring در state.**
فایل: `_ops/wiring.py:523-547` — افزودنِ `wire_heart/bio/pulse/selfheal/pocketsmith/web_research/ziman/cartographer/fisher/mining` تا داشبورد/آدیت یک بلاک را بخواند. additive؛ rollback: حذفِ خطوط.

**P12 — رفرشِ READMEِ epistemics + docstringِ router.**
دو سندِ کهنه که K7/L-contradiction را بازتولید می‌کنند. یک پاراگراف هرکدام.

**P13 (blocked-on-producer) — pseudo-legِ demands در digest.**
`render.py` آماده است؛ تا وقتی producerِ demands[] ساخته نشود (طرحِ `07-ALLOSTATIC-DEMAND-LOOP-DESIGN.md`)، این patch معلق بماند.

---

## F) Acceptance Tests

| # | برای | تست |
|---|---|---|
| AT-1 | P1 | بعد از restart: `Test-Path _ops/state/ORGANISM-STATE.code` = True **و** `started` جدید **و** curl 8771 سالم. اگر سایدکار باز غایب → باگِ مسیرِ نوشتن (falsifierِ K17-3). |
| AT-2 | P2 | `grep -c "TG_CENTER" _ops/OCTOPUS-flags.cmd` = 0 **و** باتِ مرکز بعد از restart پاسخ می‌دهد (توکنِ چرخیده از env). |
| AT-3 | P3 | تستِ واحد: snapshot با sigma=0.9 + freeze=RED → `evaluate().pain > 0.7` و `protective_override.action=='protective_halt'`؛ regression: snapshotِ سالم → pain < 0.3. |
| AT-5 | P5 | شبیه‌سازی: spend تا cap، سپس ۳ tick — `spent==cap` ثابت و `resting==3`. |
| AT-6 | P6 | سه tickِ متوالی با period 900s → `dead_spots == []` در هر سه؛ و با killِ عمدیِ writer (تستی) → spine قرمز (حساسیت حفظ شود). |
| AT-7 | P7 | خطِ journalِ جدید هر دو کلید را دارد؛ سناریوی blocked (`plan غایب`) از سالم قابلِ تفکیک است. |

---

## G) Reflection JSON

```json
{
  "outcome": "success",
  "facts": [
    {"claim": "Running organism.py is pre-4976005; 3 newer commits on disk not loaded", "evidence_refs": ["git log -- _ops/organism.py", "ORGANISM-STATE.started=19:12:57"]},
    {"claim": "fear is enforced in self-change lanes and engaged now", "evidence_refs": ["auto_approve.py:86-92", "code_autonomy.py:249-251", "stress-latest.json"]},
    {"claim": "nociceptor inputs starved: spectral={} sensory={} at call site", "evidence_refs": ["organism.py:367-368", "neural_driver.py:69-74"]},
    {"claim": "pacemaker dead-spot is a cadence-calibration artifact (SLA 5min vs 900s tick, red at 15.0 vs age 15.1)", "evidence_refs": ["innervation.py:30,69-74", "organism.py:651,661,711-718"]},
    {"claim": "governor LLM gate open but 100% dry via PriceNotLocked x95", "evidence_refs": ["governor_epoch.py:245-281", "governor-alerts.md"]},
    {"claim": "real secrets inside non-secret flags file", "evidence_refs": ["_ops/OCTOPUS-flags.cmd:2,111-112"]}
  ],
  "inferences": [
    {"claim": "box never stepped in production", "basis": ["rfcs.json empty across 4 boots", "no error alerts", "no disk trace by design"]},
    {"claim": "governor_shadow.py never ran", "basis": ["mandatory first-write dir absent"]},
    {"claim": "sidecar will self-materialize on next restart", "basis": ["written once at boot, organism.py:213", "code postdates boot"]}
  ],
  "hypotheses": [
    {"claim": "8773 died by console close", "test": "start via RUN-LIVE.bat and watch heartbeat", "falsifier": "a crash trace in a python error log at ~10:30-19:12 window"},
    {"claim": "spent>cap overshoot came from ~42s mice-pace ticks before heart wire opened", "test": "correlate 4 boot times with cardiac spend curve", "falsifier": "spend increments during confirmed 900s-period windows"}
  ],
  "unknowns": [
    "paid keys present now (BLOCKED: .env off-limits)",
    "epistemics_beat actually fired (advisory is memory-only by design)",
    "C:\\ops governor_shadow twin registered in Task Scheduler",
    "which tier answered llm_learn syntheses (ledger lacks tier field)",
    "box-ever-stepped ground truth (needs a persistent box trace)",
    "owner intent for 8773: always-on vs on-demand"
  ],
  "gap": "Expected a broken pacemaker organ and a missing allostatic loop; found instead a mis-calibrated SLA artifact and a partially-built fear circuit that IS enforced in self-change lanes — the организm is more honest than its dashboards and less protected than its headlines.",
  "critique": "Read-only discipline prevented proving in-memory-only paths (epistemics fire, box step); two megaprompt path errors (flags location, cardiac location) cost probe time and are now corrected in the map; .env rule honored at the cost of 4 BLOCKED items.",
  "candidate_lesson": {
    "context": "auditing a live organism with flag-gated layers",
    "lesson": "Grade 'wired' claims on three independent axes — env flag, call-site reachability, and persistent side-effect — because each axis alone produced a false verdict somewhere in this audit (SELF_IMPROVE_AUTO, wire_box, wire_fitness).",
    "confidence": "high",
    "expiry_days": 7
  },
  "smallest_next_action": {
    "kind": "propose_patch",
    "description": "Owner restarts the organism (P1) — zero-line patch that activates 3 already-committed honesty fixes and materializes the version sidecar",
    "expected_signal": "ORGANISM-STATE.code exists; new started ts; wiring unchanged",
    "rollback": "git checkout abbd2d5 -- _ops/organism.py + restart",
    "requires_human_approval": true
  },
  "risk": "low"
}
```

---

## H) Open UNKNOWNs (صادقانه)

1. حضورِ فعلیِ کلیدهای paid (FUGU/GLM/DEEPSEEK) — **BLOCKED** (نیازمندِ `.env`؛ قاعده مقدم است). آخرین شواهدِ منفی 07-15، آخرین تکمیلِ موفقِ llm_learn 07-17 با tier=local.
2. آیا `epistemics_beat` در این پروسه واقعاً fire کرده — خروجی عمداً فقط-حافظه است؛ اثباتِ read-only ناممکن (INFERENCE: بله).
3. دوقلوی `C:\ops\governor_shadow.py` و taskِ «GovernorShadow» در Task Scheduler — شمارشِ taskها بیرون از scope ماند (گوچا: از PowerShell بپرس، نه Bash).
4. کدام tier به سنتزهای `llm_learn` جواب داده (ledger فیلدِ tier ندارد — ایدهٔ patchِ آینده).
5. آیا box هرگز در production قدم زده (نیازمندِ ردِ ماندگار — P-idea در D).
6. مقصودِ مالک برای 8773 (always-on یا on-demand) — پیش‌نیازِ P9.
7. آیا `OCTOPUS_SYNTH_EVENT_DRIVEN=1` واقعاً سنتزِ paid را event-driven کرده (probe نشده؛ مرتبط با اصلِ «کورتیزول نه تایمر»).
8. importِ `octopus_core` بیرون از `_ops` (درخت‌های langar/saba/ziman بررسی نشد — K4 فقط `_ops` را پوشش داد).

---

*تولیدشده طبق قراردادِ §۶ مگاپرامپت — فایلِ نو، بدونِ overwrite. workspace: فقط همین پوشه. هیچ patchی اعمال نشد؛ هیچ secretی echo نشد؛ `.env` باز نشد. ۶ حسگرِ read-only، ۱۹۵ probe، ~600k tokenِ تشخیصی.*

---

# ضمیمهٔ ساخت — 2026-07-17 نیمه‌شب (فازِ «همه را دیباگ کن»، دستورِ مالک)

مالک دستور داد همهٔ تعمیرها ساخته شوند. **همهٔ patchهای غیر-🔑 روی master ساخته، تست و commit شدند** — دو کامیت: `37cebf2` (تعمیرهای P) + `35c505e` (فیکس‌های بازبینیِ خصمانه). چون پروسهٔ زنده importها را در حافظه دارد، **اثرِ همه با restart (P1) می‌آید**.

| Patch | وضعیت | کجا |
|---|---|---|
| P3 عصبِ دردِ بینا | ✅ ساخته+تست | `organism.py` (sigma/afferent/error_rate واقعی) + `neural_driver.py` (forward) |
| P5 بودجهٔ صادق | ✅ | `organism.py` (resting بعد از depletion) + `cardiac.py` (rollover در status) |
| P6 آرتیفکتِ pacemaker | ✅ | `innervation.py` (SLAی پویا، clamp ۰..۱۸۰۰s، سقف ۳۲min) |
| P7 journal خوانا | ✅ | `cortex.py` (`align_changed`+`align_reason`) |
| P8 registry خود-توصیف | ✅ | `registry.py` (`source`+`watches`) |
| P10 فلگِ مرده | ✅ (بیرونِ git) | `flags.cmd` — خطِ SET بازنشسته؛ secretها دست‌نخورده |
| P11 بلاکِ wiring کامل | ✅ | `wiring.py` (+۱۴ کلیدِ `wire_*`) |
| P12 سندهای کهنه | ✅ | epistemics README + docstringِ router |
| box-trace | ✅ | `doctor.py` → `state/doctor/box-latest.json` |
| P13 demands digest | ⏸ معلق | producerِ demands[] هنوز وجود ندارد (طرحِ ۰۷) |
| P1/P2/P4/P9 | 🔑 مالک | restart · چرخشِ secret · قفلِ قیمت · سرنوشتِ 8773 |

**بازبینیِ خصمانهٔ ثانویه (۳ اسکپتیک روی 37cebf2):** هر سه حملهٔ اصلی REFUTED (بی‌crash/هنگ؛ تشخیصِ مرگ حفظ — قرمز حداکثر ۵۱–۹۶min؛ طوفانِ haltِ روزِ اول رد — دردِ امروز ≈۰٫۲۵). ولی ۵ نقصِ واقعی پیدا و **همه بسته شد** (`35c505e`)، از جمله:

- **🔴 مینِ HIGHِ از-قبل-موجود:** `budget_pct` در دو سایت میکرو-دلار را بر سقفِ دلاری تقسیم می‌کرد (خطای ۱۰⁶×) — اولین خرجِ paidِ ماه (>۲۶ میکرودلار) درد=۱٫۰ و protective_halt تا آخرِ ماه. فقط به این دلیل نخورده بود که خرجِ ماه دقیقاً $0 است. حالا `opslib.usd()`.
- گاردِ inf/OverflowError در innervation؛ نجاتِ دیمنِ کورتکس از period آلوده (`cortex.py:471`)؛ KeyError نهفتهٔ cardiac؛ خنثی‌سازیِ NaN/inf حسی.
- یادداشتِ صادق: `partner_stress` حالا forward می‌شود ولی هنوز هیچ producerی ندارد (۱ از ۶ محورِ درد ساختاراً صفر — نقصِ شناخته، producer قلابی اختراع نشد).

تست: `test_truthmap_fixes.py` **۱۸/۱۸** + رگرسیونِ neural/frontier/innervation/cardiac/cortex-shadow همه exit 0. ثبت در `run_all.py`.

**قدمِ بعدیِ مالک (به‌ترتیبِ اثر):** ① restart (همهٔ این‌ها + سایدکار + فیکس‌های صداقتِ عصر زنده می‌شوند) ② چرخش/کوچِ secretِ flags.cmd ③ قفلِ price در budgets.yaml یا برداشتنِ flagِ گاورنر-LLM ④ verdictِ 8773.
