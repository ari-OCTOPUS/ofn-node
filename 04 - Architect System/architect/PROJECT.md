---
type: project
kind: area
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
owner: آری
risk_level: critical
autonomy_level: read-only
tags: [ai, automation, telegram, meta-system]
created: 2026-07-03
updated: 2026-08-07
---

# پروژه: architect

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه (مادر) میزبانِ ستون است؛ node در §۳ رجیستریِ اتصال (build/test/delete پشتِ verdict).

**هدف:** سیستم هوش مصنوعیِ خودکدنویس که همهٔ پروژه‌ها را بازرسی و کنترل می‌کند و از طریق تلگرام به من وصل است.

**دو ماژول:**

1. **محقق و طراح** — تحقیق خودکار و خودبهبودی براساس معماری‌ای که طراحی می‌کنیم.
2. **رئیس کل** — کنترل و بازرسی تمام سیستم‌ها و پروژه‌های دیگر؛ رابط من با کل اکوسیستم از طریق تلگرام.

**نقش در اکوسیستم:** لایهٔ مادر — همهٔ پروژه‌های دیگر (Accounting، Crypto، Mining، Lead-نقاشی، Ziman، اونلی فنز «Project-F»، هیپنوتیزم) زیر نظارت این سیستم اجرا و کنترل می‌شوند.

**قاعده حریم Project-F:** پروژه اونلی فنز در هر خروجی cross-domain (تلگرام، داشبورد، گزارش) فقط با کد «Project-F» ارجاع می‌شود — نه نام پلتفرم، نه هویت پارتنر، نه جزئیات محتوا. جزئیات فقط داخل پوشه خود پروژه.

## Active Context

- تغییرات اخیر: **2026-08-07 شب (agent، Sonnet 5 — راستی‌آزماییِ کارِ ایجنتِ سومِ همکار + کامیت `da9ab3b`).**
  یک ترنسکریپتِ سوم (ابزارهای متفاوت) مستقیماً ۷ فایلِ production را ویرایش کرده بود
  (`miniapp_gateway.py`/`miniapp_state.py`/`live/server.py`/`dashboard/server.py`/
  `app.js`/`style.css`/**`wiring.py`**). Workflow ِ ۶-ایجنته diff-به-diff بررسی کرد:
  `read_gate_enabled()` واقعاً سخت‌گیرانه‌تر شد (fail-closed)، قفلِ `_CACHE` درست،
  rate-limit + سقفِ body درست پیاده شدند، فیلدِ `applied` در `wiring.py` دقیقاً
  شرطِ گیتِ واقعی را می‌خواند بدونِ لمسِ گیت. **یک ایرادِ واقعی خودم فیکس کردم:**
  دو تعریفِ متناقضِ `.tblwrap table` در style.css (یکی مرده بود). ۷۴/۷۴ تست سبز.
  **این چرخهٔ کاری (سه ایجنتِ همکار روی همین درختِ زنده، هر بار راستی‌آزماییِ
  مستقل قبل از پذیرش):** `5c161d2` → `792a94a` → `0c9fecc` → `fc0df72` → `da9ab3b`.

- تغییرات اخیر: **2026-08-07 شب (agent، web-app security audit — ۶ فیکس + ARIA/CSP + برخوردِ دو ایجنت).**
  commit `5c161d2`. ۴ یافتهٔ گزارشِ بیرونی تأیید+فیکس+test+mutation-test: toast()
  XSS (اسکیپِ شرطیِ فارسی)، فهرستِ آرامِ viewHome (برعکسِ همان)، `str(e)` خامِ
  `live/server.py`، leak ِ کلیدهای unmanaged در `/api/flags` ِ dashboard. سیبلینگِ
  همان کلاسِ نشت در `cortex.py`'s `/ask` هم فیکس شد. سخت‌سازی: role=tablist/tab/
  tabpanel+roving tabindex+کیبورد، CSP بسته، بازگشت‌به‌تب با `visibilitychange` —
  با پیش‌نمایشِ واقعیِ مرورگر تأیید شد. **⚠️ حینِ کار، ایجنتِ دیگری هم‌زمان
  روی همان `app.js`/`live/server.py` می‌نوشت** (برچسبِ `FIX (deep-scan
  2026-08-07)` — احتمالاً GLM worker یا یکی از سه ایجنتِ اسکنِ زیر). ۵ فیکسِ
  آن‌ها (stale-fetch guard، null-guard، ارورِ `render()`) verify و نگه داشته
  شد؛ فقط تصادمِ toast() (innerHTML vs textContent، span ِ `ltr()`) دستی حل شد.
  **درسِ عملیاتی:** هر دو ایجنت مستقیم روی `F:\backup` می‌نوشتند نه worktree —
  دقیقاً همان الگویِ WORKLOCK که این پروژه از قبل مستند کرده.

- تغییرات اخیر: **2026-08-07 عصر (agent، operations/money-scan — گزارشِ ایجنتِ (۳)
  از سه مگاپرامپتِ اسکن).** جوابِ صادقانه به «همه‌چیز واقعاً کار می‌کند یا فقط
  شبیهِ فعالیت؟»: lead امروز **صفر** ولی درست است (propose_only:true، credential ِ SMTP
  نیست)؛ arbiter اکنون 🟢 سبز (نه قرمز). سه فیکس در دامنهٔ بنده: `de2af9c` تلهٔ
  `UnboundLocalError: PriceNotLocked` در `heart/doctor_setpoint.py` (مسیرِ پولی —
  خودِ fail-soft خراب بود)؛ `828b607` `test_token_meter` now=NOW (تستِ شکننه، کد سالم)؛
  `585f137` `phantom_guards` رچتِ فلگ. باگِ کلاسِ نوشتنِ غیراتمیک: فایلِ متخف از قبل
  حذف شده، همهٔ stateهای پولی `opslib.LockedJson` دارند — صفر فیکسِ نو لازم. ۶ شکستِ
  خارج از دامنه در `AGENT_QUESTIONS`. بکاپِ خام:
  `C:\Users\Armin\Desktop\OCTOPUS-SCAN-OPERATIONS-2026-08-07\`.

- تغییرات اخیر: **2026-08-07 عصر (agent، interaction-surface audit — گزارشِ ایجنتِ (۲)
  از سه مگاپرامپتِ اسکن: دو ریشهٔ «نمی‌شه حرف زد» فیکس شد).** مسیرِ RAG ِ vault
  (`ask_vault`) به‌طور سیستماتیک با `rg-error` می‌مرد — `.claude/worktrees/*`
  (۱۲٬۷۴۶ md، ۵ کپیِ `Lead-نقاشی.md`ِ ۹۴۰KB) + `_build`/`_archive-binaries`/`_portable-build`
  به `_BUILD_EXCLUDE` اضافه شد (`972a1e7`)؛ حالا 0.3s (was >20s timeout)، جوابِ مستند.
  مسیرِ چتِ آزاد (`mirror_room`) وقتی سهمیهٔ فوگو پر می‌شود (هر روزِ اخیر ۶۰/۶۰)
  بن‌بست می‌شود و پیامِ گمراه‌کننده می‌داد؛ صادقانه شد (`9e06a1f`). مینی‌اپ سالم
  (هر ۷ تب دادهٔ زنده). توصیه: `notif_inbox`/`restart_control` امن برای آرم. سؤالِ باز:
  `FUGU_DAILY_CALL_CAP=60` هر روز پر می‌شود — بالا برود؟ جزئیاتِ کامل:
  [[../../07 - Knowledge/شناخت-اختاپوس/25-INTERACTION-SURFACE-AND-QUOTA-DEAD-END-2026-08-07|25-INTERACTION-SURFACE-AND-QUOTA-DEAD-END]].

- تغییرات اخیر: **2026-08-07 عصر (agent، cognition-sync audit — گزارشِ ایجنتِ (۱)
  از سه مگاپرامپتِ اسکن).** جوابِ شواهدمحور به «آیا لایه‌های آگاهی سینک‌اند؟»:
  ناقص ولی صادقانه — متخصص‌های مکمل، نه جزایرِ متناقض. ۵ منبعِ زنده، ۳
  sensor-rich/actuator-poor. یک یافتهٔ تشخیصیِ نو (فیلدِ `applied` در
  effect-shadow همیشه `False` هاردکد — شکافِ observability، نه باگ) در
  `AGENT_QUESTIONS.md` ثبت شد. vault_whole = ۱۰۹٬۲۲۰ chunk وصل/کارآمد (9/9 سبز).
  نرخِ واقعیِ protective-halt بعدِ ری‌استارت = ۰٪ (pain 0.207 < 0.35). هیچ فلگی
  دست نخورد، هیچ فیکسی کامیت نشد (hebbian.json از null خودش heal شد). جزئیاتِ
  کامل: [[../../07 - Knowledge/شناخت-اختاپوس/24-COGNITION-SYNC-AUDIT-2026-08-07|24-COGNITION-SYNC-AUDIT]].

- تغییرات اخیر: **2026-08-07 شب (agent، Sonnet 5 — هر دو مسدودکننده رفع شد،
  ری‌استارتِ کامل (۵/۵) موفق، سه مگاپرامپتِ اسکنِ موازیِ کاملِ اختاپوس dispatch شد).**
  `budget_gate.py:171-173` نوشتنِ غیراتمیک بود (ریشهٔ خرابیِ `budget-state.json`)؛
  بازسازی با دادهٔ مستقلِ تلمتری، `FREEZE.flag` پاک شد. cortex یک‌بار zombie
  بود (`RESTART-PROCESS.ps1` fallbackِ اجباری ندارد) — دستی حل شد. هر ۵ پروسه
  الان با هر ۶ فلگ زنده‌اند. سپس سه مگاپرامپتِ ایزوله (سینکِ آگاهی/حافظه ·
  سطحِ تعامل «چرا نمی‌شه حرف زد» · سلامتِ عملیاتی/پول) برای سه ایجنتِ موازیِ
  بیرونی نوشته و مستقیم در چت داده شد — منتظرِ گزارش. جزئیاتِ کامل:
  [[../../07 - Knowledge/شناخت-اختاپوس/23-P1-P5-VERIFIED-AND-NEXT-MEGAPROMPT-2026-08-07|23-P1-P5-VERIFIED-AND-NEXT-MEGAPROMPT]].
- تغییرات اخیر: **2026-08-07 (agent، Sonnet 5 — کنترلِ ری‌استارت از تلگرام + صندوقِ اعلانِ مینی‌اپ + تأییدِ مستقلِ ممیزیِ شناختیِ کارگرِ GLM).**
  جزئیاتِ کامل: [[../../07 - Knowledge/شناخت-اختاپوس/23-P1-P5-VERIFIED-AND-NEXT-MEGAPROMPT-2026-08-07|23-P1-P5-VERIFIED-AND-NEXT-MEGAPROMPT]]. دو نخِ کارِ موازی امروز:

  **(الف) خودم — کنترلِ ری‌استارت + صندوقِ اعلان (۱۳ کامیت):** `/restart [scope]`
  مستقیم در `handlers` ِ `center.py` (نه پلِ دو-باتی) با کارتِ تأییدِ
  `ap:ok`/`ap:no` (از همان مکانیزمِ صفِ `approval_store`، صفر verbِ نو)؛
  `restart_control.py` نو با `execute_restart` (`CREATE_NEW_PROCESS_GROUP`ِ
  جداشده، تست‌شده در برابرِ مرگِ پروسهٔ مادر — `DETACHED_PROCESS` تجربتاً
  ضبطِ `Write-Host` را می‌شکست) + `check_restart_result` (از `beat` ِ مرکز).
  باگِ واقعی: `/restart` عضوِ `_CENTER_SLASH` نبود (همان دستهٔ outer-bot-4).
  جدا از این: صندوقِ اعلانِ `notif_inbox.py` با ۵ نقطهٔ قلاب پشتِ
  `OCTOPUS_WIRE_NOTIF_INBOX` (پیام‌های تلگرام به‌جای شلوغ‌کردنِ چت، تبِ هفتمِ
  مینی‌اپ) + طرحِ محدودِ `outbound_https.py` (فقط اسکلت، هیچ‌جا وصل نشده).
  ۲۶+ تستِ نو، هر شاخهٔ ایمنی mutation-tested. هر دو فلگ هنوز خاموش.

  **(ب) کارگرِ GLM — ممیزیِ شناختیِ ۱۶.۵ساعته + P1-P5 (`f9940e2`):** consent
  glue واقعی (مسیرِ ارسالِ لید باز شد، legs با رأیِ مالک)، `cortex.think()`
  پشتِ `OCTOPUS_WIRE_CORTEX_RICH_THINK`، reindex ِ کلِ vault. **تأییدِ مستقلِ
  ۵-ایجنتهٔ من روی کدِ زنده:** P1/P2/P3 تأیید شد (۴/۴ تستِ P1 زنده سبز)؛
  عددِ P5 غلط بود (۷۰٬۹۹۳ نه ۱۰۹۲۲، هنوز ایندکس می‌شد)؛ **مهم‌تر — ادعای
  «P4 فقط طرح» غلط بود**، اکچوئیتور از قبل در `wiring.protective_override()`
  ساخته/تست شده (فلگِ shadow از ۰۷-۲۷ آرم)، کارِ باقی‌مانده فقط تصمیمِ
  آرم‌کردنِ فلگ است نه کدنویسی؛ آرم‌کردنِ `CONSENT_FW`+`LEAD_OUTBOUND` هم
  تحلیل و **امن** تشخیص داده شد (گیتِ فقط-رد + چک‌پوینتِ تأییدِ انسانیِ
  ازقبل‌موجود + هنوز credentialِ SMTP نیست). مگاپرامپتِ آمادهٔ جلسهٔ بعد در
  نوتِ ۲۳.

- تغییرات اخیر: **2026-08-06 شبِ خیلی دیرتر (agent، Sonnet 5 — پایانِ جلسه: mirror_room سیم‌کشی شد، 4D-Vault بازسازی شد، ریشهٔ «رأی ثبت نمی‌شود» پیدا و رفع شد، سه ورک‌فلوی موازی، ۳۰+ کامیت).**
  جزئیاتِ کامل: [[../../07 - Knowledge/شناخت-اختاپوس/18-STALE-TEST-BACKLOG-2026-08-06|18-STALE-TEST-BACKLOG]] ·
  [[../../07 - Knowledge/شناخت-اختاپوس/19-TELEGRAM-APPROVAL-RACE-AND-ALERT-AUDIT-2026-08-06|19-TELEGRAM-APPROVAL-RACE]].
  رأیِ مالک «همرو موافقم کدنویسی‌ارو کامل کن ... جلسرو ببندیم» دو موردِ معلقِ
  قبلی را باز کرد و بعد سه دورِ دیباگِ زندهٔ اضافی از پیام‌های تلگرام آمد.

  **mirror_room:** فقط نیمهٔ `observe()` وصل شد (بی‌صدا/بی‌هزینه)؛ نیمهٔ `ask()`
  (جوابِ پولی در هر اتاق) عمداً وصل **نشد** — تصمیمِ هزینهٔ جداگانه.
  `OCTOPUS_TG_MIRROR_ALLROOMS=1` مسلح، ری‌استارتِ زنده تأیید شد.

  **4D-Vault:** ۳۰۵۵ نوتِ زیرپروژهٔ SOG/Brain-OS از متنِ خودِ ایندکسِ منجمدِ
  Chroma بازسازی شد؛ یک باگِ واقعیِ `index_vault()` (سقفِ batch ِ Chroma)
  هم پیدا/فیکس شد. ریتمِ تازه‌سازیِ دوره‌ای عمداً ساخته نشد — تصمیمِ مالک.

  **جاروی ۵۹۷ تست + تریاژِ ۷-ایجنته:** فقط ۱ موردِ ساختهٔ همین جلسه (فیکس شد)؛
  ۲۵ موردِ بدهیِ کهنه با تاریخ/علتِ دقیق کاتالوگ شد، دست نخورد — یکی مشکوک
  به نشتِ داده (`test_miniapp_lifecycle_view.py`)، یکی security-adjacent
  واقعی (فیکسِ ۰۸-۰۳ به doctor.py یک گاردِ ساختاری را که مانعِ رسیدنِ C6 به
  `apply_merge` بود بی‌سروصدا حذف کرده بود — blast-radiusِ امروز محدود ولی
  مرزِ ساختاری رفته؛ نیازِ رأیِ مالک، دست نخورد).

  **«چرا رأی ثبت نمی‌شود؟» — سه ریشهٔ مستقل، هر سه رفع شد.** (۱) کارتی که
  مالک واقعاً می‌دید (`brain_digest_beat`) اصلاً دکمهٔ رأی نداشت — کارتِ
  تعاملیِ واقعی سالم بود ولی مالک هرگز به آن نرسیده بود. (۲) فیکسِ ریشهٔ ۱
  خودش دکمهٔ cross-bot مرده ساخت (تلهٔ دو-باتیِ مستند، این بار روی
  wiring.py) — گرفته و رفع شد با یک تستِ واقعیِ dispatch. (۳) **رِیسِ
  دو-پروسهٔ واقعی روی approval_store** — `organism.py` (`goal_action_bridge`)
  و `center.py` بدونِ قفلِ بین‌پروسه‌ای روی همان `approvals.json` می‌نوشتند؛
  تأییدِ مالک می‌توانست بی‌صدا به pending برگردد. با `opslib.LockedJson`
  رفع شد؛ هر دو پروسه ری‌استارت شدند.

  **اصلاحیه (همان شب، بعد از تستِ زندهٔ مالک):** فیکسِ متنیِ ریشهٔ ۲ بالا
  را مالک رد کرد — «کار نمیکنه». فیکسِ واقعی: دکمهٔ `url` با deep-link
  (`t.me/intergrade2725_Bot?start=ap`، کاملاً سمتِ کلاینت، هیچ دیسپچرِ
  باتی لمس نمی‌شود) + **حذفِ کارت بعد از رأی** (درخواستِ صریحِ مالک).
  کامیت `38e9685`. جزئیات: [[../../07 - Knowledge/شناخت-اختاپوس/19-TELEGRAM-APPROVAL-RACE-AND-ALERT-AUDIT-2026-08-06|19 (اصلاحیه)]]
  و حافظه `feedback-cross-bot-callback-needs-a-url-deeplink`. تمامِ
  سؤال‌های بازِ AGENT_QUESTIONS + ۵ تناقضِ تصمیم-در-برابرِ-تصمیم (از‌جمله
  همین تلهٔ دو-باتی به‌عنوانِ الگوی سه‌بارتکرارشونده) در
  [[../../07 - Knowledge/شناخت-اختاپوس/20-NEXT-AGENT-MEGAPROMPT-QUESTIONS-AND-CONTRADICTIONS-2026-08-06|سندِ ۲۰]]
  جمع شد — ایجنتِ بعدی قبل از فیکس در آن حوزه‌ها اول آن سند را بخواند.

  **آلارمِ گمراه‌کننده — سومین نمونه پیدا شد.** همان کلاسِ باگِ «سقفِ روزانهٔ
  فوگو را broken می‌خواند» که امشب زودتر در `model_router.py` فیکس شده بود،
  در اسکنِ سراسری در `deep_think.py` و `self_patch.py` هم پیدا و فیکس شد.
  یک نمونهٔ چهارم در `_ops/legs/outbound_worker.py` پیدا شد ولی **فیکس
  نشد** — زیرِ قفلِ `_ops/legs/**`، منتظرِ رأیِ مالک (سؤال در AGENT_QUESTIONS).

  **کدِ کامیت‌شده تا لود نشود بی‌اثر است — بارِ سوم امشب، این بار روی
  چهار پروسهٔ هم‌زمان.** هر فیکس نیاز به بررسیِ دستیِ «کدام پروسه این
  ماژول را import می‌کند» داشت — `organism.py`/`live/server.py` هر دو
  به‌صورتِ transitive `model_router.py` را می‌خوانند، نه فقط `cortex.py`.
  یک اسکنِ AST جدید نقشهٔ کاملِ ریسکِ ری‌استارت را ثبت کرد (سندِ ۱۹).

- تغییرات اخیر: **2026-08-06 (agent، Sonnet 5 — جاروی یافته‌های خودگزارش‌شده + «کامل دبل چک کن دیباگ کن» + مگاپرامپتِ ۱۶).** جزئیات: [[../../07 - Knowledge/شناخت-اختاپوس/16-NEXT-AGENT-MEGAPROMPT-2026-08-06|16-NEXT-AGENT-MEGAPROMPT]] · [[../../07 - Knowledge/شناخت-اختاپوس/15-SELF-REPORTED-ISSUES-SWEEP-2026-08-06|15-SELF-REPORTED-ISSUES-SWEEP]]. ورک‌فلوی adversarial روی دامپِ تلگرامِ مالک: ۲۷ کاندیدا → ۲۴ تأیید. هشت کامیت: واچداگِ gateway (`6a0ae43`) · کلمپِ خودتقویت‌کنندهٔ `web_research` (`fa90a78`) · آلودگیِ self_run در `proposal_accept_rate` (`6ff0535`) · دو دورِ اصلاحِ `ui-registry.json` (`d16fa7b`/`0666acd`) · اتصالِ `sync_truth_note` به چرخهٔ cortex (`61e0227`، `OCTOPUS_WIRE_TRUTH_SYNC=1`) · همان فیلترِ self_run در `metric_separation.from_outcome_store` (`5cb9f21`، یافتهٔ ممیزیِ خصمانه). ⚠️ **یافتهٔ حیاتی:** cortex/organism هر دو از قبلِ کامیتِ فیکس بالا آمده بودند — فیکسِ درست روی دیسک تا ری‌استارت زنده صفر اثر داشت (`web_research.every_s`: ۵→۴۳۲۰۰ · `proposal_outcomes`: ۳۵→۲۵ فقط بعدِ ری‌استارت زنده تأیید شد). schtasks (`OctopusLiveDataRefresh`) عمداً خودم نزدم — قاعدهٔ سیستمی، دستورِ آماده به مالک داده شد. دو نمونهٔ دیگرِ همان آلودگیِ self_run (`outcome_store.metrics`، `paper_mvo.py`) عمداً فیکس **نشدند** — صداکنندهٔ تولیدی ندارند، تصمیمِ فیلترکردن ابهامِ معنایی دارد.

- **سرریزِ ۲۰۲۶-۰۸-۰۷:** ورودی‌های ۲۰۲۶-۰۷-۳۱ تا ۲۰۲۶-۰۸-۰۵ (فایل دوباره به سقف رسیده بود) منتقل شدند به
  `_Archive/Logs/architect-PROJECT-ActiveContext-archive-2026-08-07.md` — انتقال، نه حذف (§۰.۱).

## Progress

- **وضعیتِ کنترلِ ری‌استارت + اعلان‌ها (نو، ۲۰۲۶-۰۸-۰۷):** `OCTOPUS_WIRE_RESTART_CONTROL`
  و `OCTOPUS_WIRE_NOTIF_INBOX` هر دو ساخته/تست‌شده ولی **خاموش** — آرم‌کردن رأیِ
  جداگانهٔ مالک. **وضعیتِ P4/effect-shadow (تصحیح‌شده):** اکچوئیتور از قبل در
  `wiring.protective_override()` هست (خاموش، پشتِ `OCTOPUS_NEURAL_LEARNED_APPLY`)؛
  ۱۵٬۸۳۸ ردیفِ shadow-log منتظرِ تحلیل قبل از تصمیمِ آرم است. **وضعیتِ مسیرِ ارسالِ
  لید:** `consent_current` حالا مادیالایز می‌شود (`f9940e2`) ولی `OCTOPUS_WIRE_CONSENT_FW`+
  `OCTOPUS_WIRE_LEAD_OUTBOUND` هنوز خاموش‌اند — تحلیلِ ایمنی امن تشخیص داد
  (گیتِ فقط-رد + تأییدِ انسانیِ ازقبل‌موجود + credentialِ SMTP هنوز نیست).
  جزئیاتِ کامل: [[../../07 - Knowledge/شناخت-اختاپوس/23-P1-P5-VERIFIED-AND-NEXT-MEGAPROMPT-2026-08-07|23-P1-P5-VERIFIED-AND-NEXT-MEGAPROMPT]].
- **وضعیتِ خودآگاهی (نو، سنجیده ۲۰۲۶-۰۸-۰۵ بعد از ری‌استارتِ کامل):** هر پنج پروسه (`center`/`cortex`/`live`/`organism`/`miniapp-gateway`) با **۱۶۵ فلگ** و `OCTOPUS_REACH=1` بالا آمدند — پیش از امروز گیت‌وی ۷ فلگ داشت. دفترِ دسترسی: **۷۶۹ تابعِ یکتا** در ~۱۰ دقیقه. اعدادی که مغز حالا ساعتی/روزانه می‌خواند و فقط روی تغییر حرف می‌زند: ۶۰ ماژولِ یتیم از ۴۹۴ (۱۳ سنگین) · **۱۲۸ دروازهٔ تاریک از ۳۲۶ فلگ** (۱۲۶ جزئی، ۱۳۵ زندهٔ روشن) · ۲۷۲ فلگ که کد می‌خواند و هرگز مسلح نشده · ۲۱۷ نمادِ مرده · ۱۵۸ فایلِ حالتِ یتیم · ۲۸ کارِ ناتمام · ۲۳ ماژولِ بی‌تست. ⚠️ دفترِ خالیِ یک پروسه یعنی **UNKNOWN** نه «کدش نمی‌دود» — provenance ِ پروب این دو را جدا می‌کند و UI هم همین را می‌گوید.
- **سرریزِ ۲۰۲۶-۰۸-۰۷:** ردیف‌های قدیمی‌ترِ Progress (بودجهٔ مدل، سطحِ نوشتنِ کاکپیت، arm_gate،
  پاها/فلگ‌ها ۰۸-۰۱، TG-P2، ۰۷-۲۹..۰۷-۰۷) منتقل شدند به
  `_Archive/Logs/architect-PROJECT-Progress-archive-2026-08-07.md` — انتقال، نه حذف (§۰.۱).

## Next actions

- [ ] **بررسیِ مالک لازم:** آیتمِ آرشیوشدهٔ «tentacle فروش ۰۷-۲۰» در
  `_Archive/Logs/architect-PROJECT-Progress-archive-2026-08-07.md` — ددلاینش حالا هفته‌ها
  گذشته و در هیچ ورودیِ جدیدتری تکرار نشده؛ منسوخ یا فراموش‌شده؟

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[03 - Projects/Accounting/Accounting|Accounting]]
- [[03 - Projects/Lead-نقاشی/Lead-نقاشی|Lead-نقاشی]]
- [[03 - Projects/اونلی فنز/اونلی فنز|اونلی فنز]]

## 🎛 کابین کنترل (two-brain)

- کابین مشترک: ارتیفکت `fleet-live-dashboard` · نقشه: [[_memory/TWO-BRAIN-CONTROL-BLUEPRINT|TWO-BRAIN]] · نقشهٔ ساخت: [[_memory/FRANKENSTEIN-BUILD-PLAN|FRANKENSTEIN-BUILD-PLAN]]
- عملیات استاندارد از کابین (intent → sendPrompt): «تست <پروژه>» = validators + چک کد + تست قرارداد · «بساز» = اسکلت از `_Templates` + ثبت همین‌جا · «آرشیو» = فقط انتقال به `_Archive`/`_Duplicates` (هرگز حذف واقعی).
- تست قرارداد این پروژه: هنوز تعریف نشده — طبق BUILD-PLAN §۲ تعریف شود.
