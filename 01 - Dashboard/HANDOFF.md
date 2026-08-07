---
type: handoff
updated: 2026-08-07
---

# HANDOFF — وضعیت برای جلسه بعد

> قاعده: این فایل ایندکسِ wikilink است، زیرِ ۲۰۰ خط — نه آرشیو. تاریخچهٔ کاملِ قبلی: `_Archive/Logs/HANDOFF-archive-2026-07-16.md` (۲۶۳KB، قرنطینه‌شده 2026-07-16). سرریزِ 2026-07-29 (ورودی‌های ≤ 07-24): `_Archive/Logs/HANDOFF-archive-2026-07-29.md`. سرریزِ 2026-08-01 (ورودی‌های ≤ 07-27): `_Archive/Logs/HANDOFF-archive-2026-08-01.md`. سرریزِ 2026-08-04 (ورودی‌های ≤ 08-02): `_Archive/Logs/HANDOFF-archive-2026-08-04.md`. سرریزِ 2026-08-05 (ورودی‌های ≤ 08-04): `_Archive/Logs/HANDOFF-archive-2026-08-05.md`. سرریزِ 2026-08-06 (ورودی‌های 08-05): `_Archive/Logs/HANDOFF-archive-2026-08-06.md`. سرریزِ 2026-08-07 (ورودی‌های 08-06): `_Archive/Logs/HANDOFF-archive-2026-08-07.md`.
> 🧭 **ایجنتِ جدید؟** خلاصهٔ کاملِ کارِ 2026-08-02 + honest boundaries + قواعدی که این سشن رعایت کرد: [[00 - Inbox/SESSION-NOTES-2026-08-02|SESSION-NOTES-2026-08-02]]. درس‌های این سشن در [[../_memory/EXPERIENCE-LEDGER|ledger]] (§ 2026-08-02).

## 🔒 WORKLOCK — قفلِ کارِ موازی

<!-- WORKLOCK: بخشِ زندهٔ هماهنگی. ورودی‌های تاریخ‌دارِ پایین را دست نزن.
     lane که کارش تمام شد، ردیفِ خودش را به «آزاد» ببرد — ردیف را پاک نکند. -->

**چرا هست:** ۲۰۲۶-۰۸-۰۲ چهار deploy روی تصادمِ فایلِ مشترک سقط شد — نه باگِ منطقی، هر بار دو lane یک فایل. شاهد: `8af1924`/`b61d75c`/`5ff1119` (هر سه «union … registrations» روی `run_all.py`)، `6099de4` (`wiring.py`)، `b3fb9a5` (`orphan_scan.py`)، `f51a3dc` (`center.py`).
**و بدتر:** `.gitattributes` = `*.md merge=union` ⇒ تصادمِ markdown اصلاً conflict نمی‌دهد، **بلوکِ تکراری** می‌دهد. خطا ساکت است — بعد از merge روی `HANDOFF.md`/`PROJECT.md`ها چشمی چک کن.

**کی فعال است (2026-08-07 — سنجیده، نه از بریف):** خالی. سه ردیفِ ۰۸-۰۴
(`tg-ui-phases`/`cockpit-brain` ✅ تمام؛ `intel-spine` 🟡 سه روز بی‌به‌روزرسانی)
بازنشسته شدند — همان قاعدهٔ خودِ این بخش («lane ای که تمام شده ولی ✅ نخورده
بدتر از نبودِ جدول است»).

**همیشه رزرو:** `_ops/tests/run_all.py` (ثبتِ تست **مرکزی**؛ سه تصادم در یک روز — نامِ فایلِ تستت را **گزارش کن**، خودت ثبتش نکن) · `_ops/wiring.py` (فلگِ نو **بیرونِ** `PAPER_FULL_FLAGS` و خاموش) · `_ops/telegram_center/center.py` · `_ops/orphan_scan.py`.

**همیشه امن موازی:** سندِ نو در `06`/`07`/`00` (نه بخشِ دیگران در HANDOFF و PROJECT.mdها) · **فایلِ تستِ نو** با نامِ یکتا در `_ops/tests/` · ممیزیِ ایستا (grep، `git log`، اجرای read-only، هر دو validator).

**ثابت:** فقط داخلِ worktree بنویس — **`F:\backup` درختِ زندهٔ در حالِ اجراست** · `git add -A` هرگز · >~۵ فایل ⇒ اول `agent-checkpoint:` · «fatal: stash failed»/قفلِ `.git/objects` = قفلِ AV ⇒ **retry** نه دورزدن · lane که تمام کرد ردیفش را ✅ کند (پاک نکند).

## وضعِ لحظه‌ای

- 🛡️✅ **2026-08-07 (شب — ممیزیِ امنیتیِ وب‌اپ: ۶ فیکس + سخت‌سازیِ ARIA/CSP + برخوردِ دو ایجنت روی یک فایل).** commit `5c161d2`.
  گزارشِ بیرونی (audit) روی miniapp gateway/app.js/live/dashboard verify شد (۴ یافته
  تأییدشده، همه فیکس+test+mutation-test): toast() XSS (اسکیپِ شرطیِ فارسی)، فهرستِ
  «چیزِ سالم» در viewHome (برعکسِ همان باگ)، `str(e)` خامِ live/server.py، leak ِ
  کلیدهایِ unmanaged در `/api/flags` ِ dashboard. **سیبلینگِ کشف‌شده:** همان کلاسِ
  نشتِ `str(e)` در `cortex.py`'s `/ask` (به providerهای پولی می‌رسد — FUGU/GLM/DEEPSEEK
  key) — فیکس شد. **سخت‌سازیِ اضافه** (طبقِ درخواستِ دیپ‌اسکن): نوارِ تب
  role=tablist/tab/tabpanel+roving tabindex+کیبورد، CSP بسته (بدونِ script
  unsafe-inline)، بازگشت‌به‌تب با `visibilitychange` هم بیرونِ Telegram — با
  پیش‌نمایشِ واقعیِ مرورگر تأیید شد (کلیک+کیبورد+CSP بدونِ violation).
  **⚠️ یافتهٔ عملیاتی:** حینِ این کار، یک ایجنتِ دیگر (احتمالاً GLM worker یا یکی از
  سه ایجنتِ (۲)/(۳) بالا) هم‌زمان روی همان `app.js`/`live/server.py` می‌نوشت — ۵ فیکسِ
  مستقل با برچسبِ `FIX (deep-scan 2026-08-07)` (stale-fetch guard، null-guard، ارورِ
  `el` تعریف‌نشده در `render()`، و نسخهٔ دیگری از همین دو فیکس). فقط toast() واقعاً
  تصادم داشت (innerHTML vs textContent — دومی span ِ `ltr()` را متن خام نشان می‌داد)؛
  دستی حل و هر دو نگرانی حفظ شد. کارِ آن‌ها verify شد و در همین commit نگه داشته شد.
  **یادآوریِ خودم:** این جلسه هم مثلِ آن ایجنت مستقیم روی `F:\backup` (درختِ زنده)
  می‌نوشت، نه worktree — طبقِ WORKLOCK بالا («ثابت: فقط داخلِ worktree»).
  ۳ یافتهٔ کم‌اولویتِ باقی‌ماندهٔ گزارش (deferred قبلاً) همین جلسه implement شدند،
  چیزی معلق نماند.

- 💰🔍 **2026-08-07 (عصر — گزارشِ ایجنتِ (۳) جارویِ عملیات/پول: ۳ فیکس، صفر آرم‌کردن، صفر ری‌استارت).**
  بکاپِ خام: `C:\Users\Armin\Desktop\OCTOPUS-SCAN-OPERATIONS-2026-08-07\` (run_all + AUDIT-REPORT).
  جوابِ صادقانه به «همه‌چیز واقعاً کار می‌کند یا فقط شبیهِ فعالیت؟»: lead امروز **صفر** است
  ولی این درست است (propose_only:true، credential ِ SMTP نیست)؛ arbiter اکنون 🟢 سبز است
  (نه قرمز). **سه فیکس در دامنهٔ بنده (budget/heart/tests):**
  `de2af9c` — تلهٔ `UnboundLocalError: PriceNotLocked` در `heart/doctor_setpoint.py:175-242`
  (مسیرِ پولی): import درونِ tryِ اصلی بود و `except PriceNotLocked` نامِ bind‌نشده را می‌زد؛
  خودِ مسیرِ fail-softِ یک درِ پولی خراب بود. الگویِ `governor_epoch` (import جدا/تحمل‌پذیر).
  `828b607` — `test_token_meter` شکننده: `read_window` بدونِ `now=NOW` به دیوارِ واقعی
  می‌افتاد (کد سالم بود). `585f137` — `phantom_guards` رچت: ۲ فلگِ مسلح‌شده از دفتر پایین،
  ۵ فلگِ production-reader اعلان (comment-only). **باگِ کلاسِ نوشتنِ غیراتمیک:** فایلِ متخف
  (`budget_gate.py`) از قبل حذف شده؛ همهٔ stateهای پولی/ارگانی الگویِ امنِ `opslib.LockedJson`
  دارند — صفر فیکسِ نو لازم. **۶ شکستِ خارج از دامنه** (render_legs/tg_send_audit/
  c6_trigger/vault_hygiene/obsidian_index/miniapp) در `AGENT_QUESTIONS` ثبت شد. یک typo
  (`CORTEX_THINK_RICH` در test_cortex_rich_think_heart.py:67) هم ثبت شد (دامنهٔ مغز).

- 🚪🔍 **2026-08-07 (عصر — گزارشِ ایجنتِ (۲) سطحِ تعامل: دو ریشهٔ «نمی‌شه حرف زد» فیکس شد).**
  ممیزیِ کاملِ شواهدمحور در [[../07 - Knowledge/شناخت-اختاپوس/25-INTERACTION-SURFACE-AND-QUOTA-DEAD-END-2026-08-07|نوتِ ۲۵]].
  بکاپِ خام: `C:\Users\Armin\Desktop\OCTOPUS-SCAN-INTERACTION-2026-08-07\`. **دو فیکس:**
  `972a1e7` — `ask_vault` (مسیرِ RAG ِ vault) به‌طور سیستماتیک با `rg-error` (timeout)
  می‌مرد؛ `.claude/worktrees/*` (۱۲٬۷۴۶ md، ۵ کپیِ `Lead-نقاشی.md`ِ ۹۴۰KB) + `_build` +
  `_archive-binaries` + `_portable-build` به `_BUILD_EXCLUDE` اضافه شد → 0.3s (was >20s)،
  جوابِ مستند با ۴ منبع. `9e06a1f` — وقتی سهمیهٔ روزانهٔ فوگو پر می‌شود (هر روزِ اخیر
  به ۶۰/۶۰ می‌رسد)، `mirror_room` بن‌بست می‌شود و پیامِ گمراه‌کننده «چند دقیقه دیگر»
  می‌داد؛ حالا صادقانه می‌گوید سهمیه‌ست، فردا ریست می‌شود. **مینی‌اپ سالم بود** (هر ۷ تب
  دادهٔ زنده، beat=28210=live). **افکارِ cortex قابلِ دیدن‌اند** (تبِ سیستم/brain).
  **توصیه:** `notif_inbox`/`restart_control` امن برای آرم (۱۴+۱۶+۳+۱۰ تست سبز) ولی فلگ‌ها
  هنوز در `OCTOPUS-flags.cmd` نیستند — تصمیمِ مالک. سؤالِ باز: آیا `FUGU_DAILY_CALL_CAP=60`
  باید بالاتر برود (هر روز پر می‌شود و چتِ عمیق را می‌بندد)؟

- 🐙🔍 **2026-08-07 (عصر — گزارشِ ایجنتِ (۱) سینکِ آگاهی-حافظه: ناقص ولی صادقانه).**
  ممیزیِ کاملِ شواهدمحور در [[../07 - Knowledge/شناخت-اختاپوس/24-COGNITION-SYNC-AUDIT-2026-08-07|نوتِ ۲۴]].
  بکاپِ خام: `C:\Users\Armin\Desktop\OCTOPUS-SCAN-COGNITION-2026-08-07\`. خلاصه:
  ۵ منبعِ زنده (BCM×۲، self-model، C6، vault_bridge)، ۳ «sensor-rich/actuator-poor»
  (Hebbian، latent vectors، consolidation ضعیف). **یک یافتهٔ تشخیصیِ نو:**
  فیلدِ `applied` در `effect-shadow.jsonl` همیشه `False` هاردکد است (`wiring.py:1730`) —
  شکافِ observability (نه باگ)، سؤال در `AGENT_QUESTIONS.md`. vault_whole = ۱۰۹٬۲۲۰
  chunk وصل شد و کار می‌کند (9/9 سبز). نرخِ واقعیِ trip بعدِ ری‌استارت = ۰٪
  (pain=0.207، زیرِ آستانه — رفتارِ درستِ ترمز). هیچ فلگی دست نخورد؛ هیچ
  فیکسی کامیت نشد (hebbian.json از null خودش heal شد).

- 🚀🔍 **2026-08-07 (شب — سه مگاپرامپتِ اسکنِ موازیِ کاملِ اختاپوس dispatch شد؛ منتظرِ گزارش).**
  مالک: «لایه‌های آگاهی و معادلاتِ ریاضیِ حافظه‌ها سینک‌اند؟ چرا نمی‌شه
  باهاش حرف زد با اینکه کنترل‌پنلم هست؟» سه مگاپرامپتِ متنیِ کاملاً
  ایزوله (بدونِ تصادمِ فایل، طبقِ الگویِ WORKLOCK) مستقیم در چت داده شد
  برای سه ایجنتِ موازیِ بیرونی که مالک خودش paste می‌کند:
  **(۱) همگرایی/سینکِ آگاهی-حافظه** (`_ops/cortex`, `_ops/memory`,
  BCM/Hebbian/consolidation/effect-shadow/self-model، آیا `CORTEX_RICH_THINK`
  واقعاً اثر کرد، اتصالِ `vault_bridge`→`vault_whole`). **(۲) سطحِ تعامل**
  (`_ops/telegram_center/*`، تستِ end-to-end ِ واقعیِ چت، هر ۷ تبِ مینی‌اپ،
  توصیهٔ آرم‌کردنِ `notif_inbox`/`restart_control`). **(۳) سلامتِ عملیاتی/پول**
  (جاروی کاملِ `run_all.py`، شکارِ باگِ کلاسِ نوشتنِ غیراتمیک — یافتهٔ
  امروزِ `budget_gate.py:171-173` — در کلِ `_ops/`، ممیزیِ فلگِ تاریک/مرده،
  آیا لید واقعاً از consent رد می‌شود). هر سه: فقط‌خواندنی روی `legs/**`
  و `wiring.py`، احتیاطِ بالا روی `center.py`، فیکس+تست+mutation-test
  در دامنهٔ خودشان، صفر آرم‌کردنِ فلگ/ری‌استارتِ خودسر، بکاپِ نهایی در
  `Desktop/OCTOPUS-SCAN-{COGNITION,INTERACTION,OPERATIONS}-2026-08-07/`،
  گزارشِ کاملِ بازگشتی برای من. **هنوز نتیجه‌ای نرسیده — جلسهٔ بعد این
  سه گزارش را می‌خواند و vault را طبقشان به‌روز می‌کند.**

- 🧩✅ **2026-08-06 (ورودی‌های این روز — mirror_room/4D-Vault/RAG-bridge/تلگرام-race/۷ فیکسِ دیگر) به آرشیو منتقل شد:** `_Archive/Logs/HANDOFF-archive-2026-08-07.md`.

- 🧩✅ **2026-08-07 (روز — ممیزیِ شناختی + فیکس‌های P1-P5 + مسیرِ ارسال باز شد).**
  مالک: «مغزها و حافظه‌ها واقعاً پیشرفت کردن؟ دیباگشون کن.» **ممیزیِ کاملِ ۱۶.۵ ساعتِ
  روشن‌ماندن:** مغزِ محلی (Ollama) یک فکر را ۱۶ ساعت تکرار کرد (۱۰۶ سیکل، ۱ فکرِ یکتا)؛
  مغزِ پولی (Fugu) ۶ ساعتِ واقعی کار کرد بعد سراش瑟 (۶۰/۶۰ daily-cap). حافظه‌ها: BCM
  واقعاً یاد گرفت (۷۸ کلید potentiated)، self-model ۱۹× رشد کرد (۴۷۷→۹۱۷۵ خط)، consolidation
  کار می‌کرد (ن_in=2) ولی effect-shadow ۱۵۷۷۵ بار محاسبه کرد و ۰ بار اعمال (sensor-rich،
  actuator-poor). **سه ریشهٔ مستقل پیدا شد.**
  **فیکس شد (commit `f9940e2`، با رأیِ مالک):**
  - **P1 — مسیرِ ارسال باز شد:** `lead_candidate_inbox.py` — بعد از پذیرشِ consent،
    `consent_current` مادیالایز می‌شود (تا امروز هرگز ساخته نمی‌شد → `no-record` → بسته).
    legs با رأیِ مالک باز شد. firewall حفظ (CHECK + derive + market_signal رد). ۴ تست +
    mutation-test سبز.
  - **P2 — مغزِ محلی از چرخش خارج شد:** `cortex.py:think()` پشتِ `OCTOPUS_WIRE_CORTEX_RICH_THINK`
    context را با آخرینِ reflection + سیگنالِ قلب غنی می‌کند. فلگ خاموش = byte-identical.
  - **P5 — کلِ vault ایندکس شد:** `vault_whole` collection (10922 chunks، جدا از 4d_vault).
  - **P3 — از قبل کار می‌کرد** (تصورِ اشتباهِ جلسهٔ قبل اصلاح شد: cursor n_in=2).
  - **P4 — فقط طرح** (effect-shadow اکچوئیتور، shadow 24-48h طبق یادداشتِ قبلی).
  **اصلاحیهٔ صادقانه:** دو تصورِ جلسهٔ قبل اشتباه بود — memory.db خالی نبود (مسیرِ اشتباه
  چک شده بود؛ واقعی در `_ops/state/memory/memory.db`، ۳۶ ردیف)، و consolidation no-op نبود.
  کدِ لمس‌شده: `_ops/legs/lead_candidate_inbox.py`، `_ops/cortex/cortex.py`،
  `_ops/tests/test_consent_materialize.py`.

  **⚠️ تأییدِ مستقل + تصحیح (بعدازظهرِ همان روز، ۵-ایجنته روی کدِ زنده):**
  P1/P2/P3 تأیید شدند (P1: ۴/۴ تست زنده سبز، `verdict` از خودِ firewall محاسبه
  می‌شود نه از تولیدکننده). P5 عددش غلط بود — شمارشِ زنده ۷۰٬۹۹۳ بود نه ۱۰۹۲۲ و
  هنوز ایندکس می‌شد. **مهم: «P4 فقط طرح» غلط بود** — اکچوئیتور از قبل در
  `wiring.protective_override()` ساخته/تست شده (فلگ `OCTOPUS_NEURAL_EFFECT_SHADOW`
  از ۰۷-۲۷ آرم است)؛ کارِ باقی‌مانده کدنویسی نیست، فقط تحلیلِ shadow-log + تصمیمِ
  آرم‌کردنِ فلگ. آرم‌کردنِ `CONSENT_FW`+`LEAD_OUTBOUND` هم تحلیل شد: **امن** —
  گیتِ فقط-رد + چک‌پوینتِ تأییدِ انسانیِ ازقبل‌موجود + هنوز credentialِ SMTP نیست.
  جزئیاتِ کامل + مگاپرامپتِ آمادهٔ کپی‌پیستِ جلسهٔ بعد:
  [[../07 - Knowledge/شناخت-اختاپوس/23-P1-P5-VERIFIED-AND-NEXT-MEGAPROMPT-2026-08-07|23-P1-P5-VERIFIED-AND-NEXT-MEGAPROMPT]].

- ✅ **2026-08-07 (شب — هر دو حل شد + ری‌استارتِ کامل با موفقیت: مالک «do both i agree»).**
  `budget-state.json` بازسازی شد (ریشه: `budget_gate.py:171-173` نوشتنِ
  غیراتمیک دارد؛ داده از `telemetry-latest.json` ِ مستقل که صفر هزینهٔ واقعی
  نشان می‌داد، نه حدس). `FREEZE.flag` پاک شد. ری‌استارت: ۴ از ۵ limb تمیز،
  **cortex zombie بود** (۲ ثانیه CPU روی ۸۰+ دقیقه) — `RESTART-PROCESS.ps1`
  عمداً fallbackِ اجباری برای cortex ندارد؛ بعدِ تأییدِ zombie‌بودن دستی
  `Stop-Process -Force` + ری‌استارتِ دوباره، موفق. **همهٔ ۵ پروسه الان با
  هر ۶ فلگ (۵ + `PAIN_THRESHOLD_CALIBRATED`) زنده‌اند**، تأیید شده از
  `flags-loaded-*.json` هر پنج‌تا. جزئیاتِ کامل: بخشِ «حل شد» در
  [[../07 - Knowledge/شناخت-اختاپوس/23-P1-P5-VERIFIED-AND-NEXT-MEGAPROMPT-2026-08-07|23-P1-P5-VERIFIED-AND-NEXT-MEGAPROMPT]].
  کارگر هر ۵ فلگِ توصیه‌شده را در `OCTOPUS-flags.cmd` آرم کرد (تأیید شد: مقدارها
  درست، CRLF سالم) و درخواستِ ری‌استارت کرد. تأییدِ مستقلِ ۴-ایجنتهٔ دیگر **دو
  مشکلِ واقعی** پیدا کرد که ری‌استارتِ فوری را نادرست می‌کرد:
  **(۱) توجیهِ ایمنیِ P4 غلط بود** — «pain ۰.۲۷۵ < ۰.۳۵» یک مثالِ حسابیِ تک‌نمونه
  با ورودیِ کهنه بود، نه تحلیلِ لاگِ کامل؛ محاسبهٔ واقعی روی ۱۵٬۸۹۷ ردیف: بیشینهٔ
  pain ِ ترکیبی ۰.۴۳۵، و **۵.۵٪ ردیف‌ها واقعاً از ۰.۳۵ رد می‌شدند**. و یک فلگِ
  ششمِ اعلام‌نشده هم آرم شده بود (`OCTOPUS_PAIN_THRESHOLD_CALIBRATED`) که خودِ
  آستانهٔ ۰.۳۵ را زنده می‌کند — بدونش آستانهٔ واقعی ۰.۷۰ است (صفر رد). **(۲)
  `_ops/budget/FREEZE.flag` همین الان زنده است** (از ۱۵:۰۷، چون `budget-state.json`
  خراب شده — ۲۵۶ بایتِ whitespace، JSON نامعتبر) — تا باز است، `organ_gate.reserve()`
  هر اقدامِ organ-gated (شاملِ فراخوانِ cortex و هر پایِ outbound) را رد می‌کند؛
  یعنی حتی بعدِ ری‌استارت اکثرِ این ۵ فلگ بی‌اثر می‌ماندند. طبقِ `OPS_RUNBOOK.md`
  این فقط‌مالک است. تست‌ها واقعاً سبز بودند (۶۵ نه ۶۱ — شمارش غلط بود نه شکست).
  **فلگ‌ها دست‌نخورده ماندند؛ ری‌استارت انجام نشد** — دو تصمیمِ مالک باز است:
  علتِ خرابیِ `budget-state.json` + آیا با نرخِ واقعیِ ۵.۵٪ هنوز می‌خواهد
  `LEARNED_APPLY`+`PAIN_THRESHOLD_CALIBRATED` با هم روشن بمانند.

- 🔁✅ **2026-08-07 (عصر — کنترلِ ری‌استارت از تلگرام + جعبهٔ اعلانِ مینی‌اپ).**
  مالک: پیام‌های تلگرام به‌جای شلوغ‌کردنِ چت، جای درست در کنترل‌پنلِ مینی‌اپ +
  «کل پروسهٔ ری‌استارت با تأییدِ من از تلگرام». **صندوقِ اعلان:** `notif_inbox.py`
  نو (صف‌محورِ JSON، همان الگویِ `approval_store`) با ۵ نقطهٔ قلاب پشتِ
  `OCTOPUS_WIRE_NOTIF_INBOX` (فلگ خاموش = رفتارِ امروز بایت‌به‌بایت): دایجست‌های
  مغز/قلب/دکتر، کارتِ RFC، پیشنهادِ پا، دو منبعِ کم‌فوریتِ event_bridge. تبِ
  هفتمِ مینی‌اپ («اعلان‌ها») + `notif.mark_read` اضافه شد. **طرحِ محدودِ خروجیِ
  HTTPS** (`outbound_https.py`) هم ساخته شد — فقط اسکلت، هیچ‌جا وصل نشده، پشتِ
  فلگِ جداگانه‌اش، allow-list-محورِ fail-closed.
  **کنترلِ ری‌استارت:** `/restart [scope]` مستقیم در `handlers` ِ `center.py` (نه
  پلِ دو-باتی) — کارتِ تأییدِ `ap:ok`/`ap:no` (از همان مکانیزمِ صفِ approval_store،
  صفر verbِ نو)؛ `restart_control.py` نو با `execute_restart` (پروسهٔ
  `CREATE_NEW_PROCESS_GROUP`ِ جداشده، تست‌شده در برابرِ مرگِ پروسهٔ مادر) و
  `check_restart_result` (گزارشِ نتیجه از `beat` ِ مرکز). یک باگِ واقعی پیدا/فیکس
  شد: `/restart` عضوِ `_CENTER_SLASH` نبود — همان دستهٔ اشکالِ outer-bot-4 که
  `/heart`/`/brain`/`/doctor` برایش قبلاً فیکس شدند. ۲۶ تستِ نو (هر شاخهٔ ایمنی
  mutation-tested)، یک اسکریپتِ دیباگِ بی‌احتیاط چند jobِ تستی در
  `approvals.json` ِ زنده نوشت که دستی پاک شد (درسِ ثبت‌شده در حافظه). **هنوز
  پشتِ `OCTOPUS_WIRE_RESTART_CONTROL` (خاموش)** — آرم‌کردن رأیِ جداگانه.
  کدِ لمس‌شده: `_ops/telegram_center/{notif_inbox,restart_control,center,
  miniapp_state,miniapp_gateway,miniapp/*}.py`، `_ops/integrations/outbound_https.py`،
  `_ops/{wiring,live_loop}.py`، `_ops/budget/approval_channel.py`،
  `_ops/agi2027_control/ops_actions.py`، ۱۰+ تستِ نو.
