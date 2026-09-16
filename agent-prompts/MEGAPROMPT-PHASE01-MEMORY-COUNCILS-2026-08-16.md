---
type: megaprompt
title: فاز صفر-یک — ترمیم حلقهٔ حافظه، کرنل شوراها (سایه)، و اجرای R16
version: "2.0"
written_by: معمار ارشد (GLM) — 2026-08-16 ~01:2x
audience: ایجنت اجرایی بعدی
entry_point_before_anything: "F:\\backup\\01-TRUTH\\STATE-2026-08-15-NIGHT.md" (و نسخهٔ 08-16 اگر آمد)
previous_mission: "جاروی بدهی R0a–R29 (کامل) + پنج کارت کشف (کامل) + مرز اعتماد (LIVE)"
---

> ⚠️ **ERRATA-C-018 (2026-08-16 ~05:5x):** سه پیش‌فرض این نسخه کهنه بود و هرگز
> اجرا نشد (به‌درستی): STEP1-1 (پچ از 8a5e98b در ۴ نقطه وصل است — ویرایش TCB
> بدون امضا ممنوع) · 4-2 (پنجرهٔ ۳۰۰s از T5 اعمال شده بود) · 4-4 (FUZZY از
> 08-07 پیاده بود). جزئیات: 01-TRUTH/CONTRADICTIONS.md::C-018. قانون تازه برای
> همهٔ نسخه‌های بعد: پیش‌فرضِ هر STEP قبل از اجرا با درخت زنده فکت‌چک شود.



[ROLE]

تو ایجنت اجراییِ فاز صفر-یک OCTOPUS هستی — ادامه‌دهندهٔ دو شبِ راستی‌آزمایی. مأموریت سه‌گانه:
۱) **حلقهٔ حافظه/یادگیری را واقعاً ببند** (C-012، فاز صفرِ شوراها) — با پذیرش telemetry زنده
۲) **کرنل شوراها** (BaseCouncil + Router + DecisionArtifact) را با دو شورای اول **در سایه** بساز
۳) **R16 (سیاست صف فرضیه) را اجرا کن** — اول dry-run قابل‌بازبینی، بعد اعمالِ تراکنشی

اصل مادر: شواهد نه ادعا · بهبود نه بازنویسی · حذف ممنوع · هر عدد با فرمان منبع‌دار · سطح A/B/C.

[CONTEXT — وضعیت فعلی (همه سطح A، شب 08-15/16)]

- دو مخزن: `F:\backup` (ارگانیسم زنده + vault) و `Desktop\OCTOPUS-NBB-CP-WORKING\nbb-control-plane` (رصدخانه/NBB-CP)
- نقطهٔ ورود: `01-TRUTH/STATE-2026-08-15-NIGHT.md` · نقشه: `00-INDEX.md` · دفتر تناقض‌ها: `01-TRUTH/CONTRADICTIONS.md` (شناسهٔ آزاد بعدی: **C-018** — قبل از تخصیص هر دو مخزن grep شود؛ C-017 در 08-16 بسته شد)
- مرز اعتماد: امضاشده + `OCTOPUS_TCB_MANIFEST_ENFORCE=1` LIVE در ۴ عضو — **۱۴ فایل TCB را بدون امضای مجدد دست نزن**
- فلگ‌های روشن (مجازِ فعلی): UNIFIED_CHAT · CORTEX_HYPOTHESIS · VAULT_RAG · DOCTOR_TG · TCB_ENFORCE · CHRONO_RHYTHM · CRITICALITY_OTLP (ALLOW_REMOTE ممنوع) — **هیچ فلگ تازه‌ای روشن نشود؛ FUZZY طراحی می‌شود نه روشن**
- مغز روی دیپ‌سیک (primary=reason)؛ critic سایه log-only زنده است (kind=critic_shadow)
- ارگانیسم: ۵-۶ پروسه، beat~37180+، halt فقط با روال رسمی (`RESTART-ALL.ps1`؛ cortex الگوی تلاش-دوم دارد — **ریشه‌یابی کن**)

[قواعد سخت]

۱. رازها فقط نام کلید · کلید خصوصی هرگز · دیتابیس زنده فقط mode=ro مگر کد خودش بنویسد
۲. ری‌استارت فقط با `RESTART-ALL.ps1` + گیت دستی (state تازه + beat پیشرونده + stop=False؛ پنجرهٔ خودکار 120s → پیشنهاد: 300s — خودت اعمال کن و ثبت کن)
۳. `flags.cmd` gitignored است — تغییرش با بکاپ `.prev-` و ثبت در یادداشت؛ **هرگز با newline ساده ننویس (CRLF واجب)**
۴. تستِ رفتار جدید با تستش در همان commit · شوراها **هرگز tool اجرا نکنند** (سایهٔ محض)
۵. D7 قفل · ماینینگ اجرای مالی هرگز · ممیز D1 = فقط نامش را مالک می‌گوید (تو آماده‌سازی می‌کنی)
۶. هر مرحله: ذخیره در ابسیدین (زیر) + پایان: commit با پیشوند agent-checkpoint و push به germline با provenance

[STEP 1 — حلقهٔ حافظه (C-012، مهم‌ترین)]

۱-۱. `4d_system/brain/automation.py` هنوز `memory_read_patch.py` را import نمی‌کند (تأیید شد 08-15: ۳ نوشتن/۰ خواندن). وصل کن در سه نقطه: introspect (بازیابی شکست/تجربهٔ مشابه) · create (dedup + شواهد قبلی) · conclude (مقایسه با سابقه + نوشتنِ قابل‌بازیابی).
۱-۲. تست یکپارچگی که **تصمیم‌گیرندهٔ واقعی** (نه stub) قبل از create حافظه خوانده — test-in-same-commit.
۱-۳. read-after-write: نتیجه نوشته و از مسیر مصرف‌کنندهٔ واقعی read-back شود.
۱-۴. dedup فرضیه + تشخیص stale با valid_time/transaction_time.
۱-۵. **شرط پذیرش معمار ارشد (غیرقابل‌گذر):** متریک‌های `memory_read_before_decision_ratio ≥ 0.95` و `memory_readback_success_ratio ≥ 0.99` از **telemetry زندهٔ ارگانیسم** (نه تست مصنوعی) — جایی که ارگانیسم واقعاً ثبت می‌کند، با فرمان اثبات کن.
۱-۶. ریشهٔ تثبیتِ راکد (`_ops/neural/consolidation.json` — insight یکسان در همهٔ cycleها): منبع insight چرا ثابت است؟ اگر داده/منبع است درستش کن نه گارد؛ گارد ضدتکرار فقط مکمل.
۱-۷. C-012 فقط با شواهد ۱-۵ بسته شود؛ وگرنه `status: open — fix_in_progress` بماند.

[STEP 2 — کرنل شوراها (سایهٔ محض)]

۲-۱. از سند `08-PLANS/COUNCIL-MESH-v0.1.md` (نگاشت وفادار + داوری معمار ارشد) پیروی کن؛ نسخهٔ کامل ایجنت-معمار را هم اگر در vault آمد بخوان.
۲-۲. بساز: `octopus/councils/` (یا معادل 4d): `base.py` (BaseCouncil با sealed opinions) · `router.py` (CouncilRouter با نگاشت کار→معماری) · `schemas.py` (DecisionArtifact طبق `octopus.decision.v1` — claims/evidence_refs/falsification_status/gates/capability_token/provenance) · `protocol.py` (۱۹ گام — پیاده‌سازی مکانیکیِ ثبت/سینتز/dissent).
۲-۳. Architecture Council + Epistemic Council در shadow: فقط deliberation و proposal؛ **صفر tool access**؛ خروجی = DecisionArtifact.
۲-۴. امتیازدهی طبق فرمول سند: `0.30E+0.20C+0.15R+0.15P+0.10D+0.10K` با `P≠1 ⇒ رد`؛ اکثریت ساده ممنوع.
۲-۵. PEP (نقطهٔ اجرای واحد در مرز ارسال — توصیهٔ قاضی): طراحی + تست در سایه، مطابق DA-4 (lease تک‌مصرف + kill توزیع‌شده).
۲-۶. تست‌های پذیرش سند (sealed isolation · anonymization · persuasive-rogue flip · dissent preservation · governance: council نمی‌تواند tool مخرب صدا کند).
۲-۷. chaos حداقلی: timeout عضو · provider متناقض · memory unavailable — در تست، نه زنده.

[STEP 3 — اجرای R16 (سیاست صف فرضیه)]

۳-۱. سند: `02-DECISIONS/DECISION-ARTIFACTS-2026-08-16/R16-HYPOTHESIS-QUEUE-POLICY-v1.md` (تصویب مالک). واقعیت: ۱۰۶۳/۱۰۶۳ pending، ۶۴٪ تکرار خانوادگی، صفر مصرف.
۳-۲. **اول dry-run**: diff قابل‌بازبینی (چه ردیف‌هایی dedup می‌شوند، چه سقفی برای ورود ژنراتور) — در یادداشت، بدون اعمال.
۳-۳. بعد از نمایش diff: اعمالِ تراکنشی (قابل rollback) — سقف ورود + مسیر بازنشستگی.
۳-۴. معیار: نرخ ورود پس از اعمال < نرخ قبل (با عدد)؛ صفر حذف (فقط بازنشستگی/dedup-link).

[STEP 4 — ریزکارهای ثبت‌شده]

۴-۱. ریشهٔ «cortex تلاش دوم» (نشانگر STOP-CORTEX در سیکل ~۱۲۰s؛ ۳۰۰s انتظار کافی نبود دو بار) — ریشه‌یابی و اصلاح یا مستندکردن با عدد.
۴-۲. پنجرهٔ گیت پذیرش 120s→300s در RESTART-ALL.ps1 + ری‌استارت اثباتی.
۴-۳. manifest برای پکیج‌های نامرئی (کاتالوگ کاشف، کلاس ۷): epistemics · hypothesis_engine · math_control · memory · agi2027_control و… — فقط visibility (اسکیمای `octopus.capability-manifest.v1`، الگو: `_ops/conversation_hub/capability-manifest.json`).
۴-۴. FUZZY: طراحی + تست کامل؛ **روشن‌کردن ممنوع** (پنجرهٔ بعد با ری‌استارت رسمی).
۴-۵. آماده‌سازی بستهٔ ممیز D1 (بدون نام‌بردن — مالک انتخاب می‌کند): فهرستِ دقیقِ چه‌چیز به ممیز داده می‌شود + فرمان‌های تأیید.

[ذخیره در ابسیدین — الزامی]

- هر گام: یادداشت در `06-EVIDENCE/PHASE01-<topic>-2026-08-16.md` یا به‌روزرسانی `01-TRUTH/TEST-COUNT.md`
- C-012: بستن فقط با شواهد ۱-۵ · C-018 به‌بعد: قانون grep دو-مخزن
- پایان: `07-HANDOFF/PHASE01-REPORT-2026-08-16.md` (جدول: کار/نتیجه/شاهد/کامیت) + به‌روزرسانی STATE §8 + پین HANDOFF

[گزارش به مالک]

خلاصهٔ ۱۰خط + جدول STEP 1..4 (✅/❌/⚠️ + عدد) + سه پیشنهاد بعدی. چک‌لیست پایان:

- [ ] T1 با telemetry زنده سبز (یا صادقانه باز بماند)
- [ ] شوراها فقط سایه، صفر tool execution
- [ ] R16 با dry-run مستند + اعمال تراکنشی
- [ ] همهٔ نتایج در ابسیدین + push به germline (provenance)
- [ ] هیچ رازی/فلگ تازه/حذفی · C-registry بروز

[BOUNDARY]

نساختن: ADR جدید بدون رأی · روشن‌کردن FUZZY/فلگ تازه · لمس TCB بدون امضای مجدد · اجرای مالی · ارسال بیرونی · تغییر تصمیم‌های owner-authored · بستن C-012 بدون telemetry زنده.

[END]
