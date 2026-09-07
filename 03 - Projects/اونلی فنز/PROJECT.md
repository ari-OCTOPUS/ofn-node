---
type: project
kind: project
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
owner: آری
risk_level: high
autonomy_level: read-only
tags: [creator-business, faceless]
created: 2026-07-03
updated: 2026-09-07
aliases: ["Project-F", "پروژه اونلی فنز", "Active Context"]
---

# پروژه: اونلی فنز

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه یک node در §۳ رجیستریِ اتصال است (build/test/delete پشتِ verdict).

**وضعیت:** creator brand با مدل faceless (فقط پا در فاز فعلی) — تیم دونفره ۵۰/۵۰، فاز validation. سند کامل: [[03 - Projects/اونلی فنز/project-master-reference|master-reference]].

**نقش در اکوسیستم:** درآمد آزمایشی؛ زیر نظارت architect (رئیس کل). کد ارجاع در خروجی‌های cross-domain: **«Project-F»**.

> 🆕 **HANDOFF پس از بازآرایی (۲۰۲۴-۰۷-۲۴):** ساختار مرتب شد + pf_os کامل شد. اول [[00 - Control/HANDOFF-NEXT-AGENT-2026-07-24-REORG|این سند]] را بخوان.

## 🎛 رابطِ کنترلِ ایجنتِ مادر (Architect) — cross-domain
- قراردادِ ماشین‌خوان: `PROJECT-F-CONTROL-MANIFEST.json` (صفر-PII، کدِ A/C) · روایت: [[03 - Projects/اونلی فنز/AGENT-CONTROL-INTERFACE|AGENT-CONTROL-INTERFACE]].
- مدلِ کنترلِ مادر: **رصد + صف‌بندیِ verdict + قطعِ اضطراری** — اجرای هیچ اکشنِ بیرونی، بدونِ دورزدنِ GATE 0/Hard-Gated، بدونِ تغییرِ قاعدهٔ قفل‌شده. مجریِ نهاییِ کارِ پرمخاطره = انسان (A).

## Agent interface (تا پیش از ARCHITECT_CHARTER — نسخه حداقلی)

- **خواندن مجاز:** PROJECT.md، master-reference، نوت‌های validation و لاگ آزمایش‌ها.
- **نوشتن مجاز:** فقط پیشنهاد (proposal)، گزارش و draft داخل همین پوشه؛ هیچ اکشن خارجی (پست، پیام، ساخت اکانت، پرداخت) بدون verdict انسانی.
- **ممنوع مطلق:** echo هویت پارتنر، عکس/محتوا، یا هر جزئیات شناسایی‌پذیر در تلگرام، داشبورد یا هر خروجی خارج از این پوشه — فقط کد «Project-F».
- **Security Gate:** تا وقتی ردیف‌های CRITICAL در [[ROTATION_CHECKLIST]] باز است، همه ایجنت‌ها روی این پروژه read-only هستند.

## KPIs (فاز validation)

delivery-rate پارتنر در trial sprint `[To measure]` · engagement روی teaserها `[To measure]` · نتیجه Track B (payment/banking پایدار: بله/خیر) — متریک درآمد از ابتدا به صبا گزارش شود (شرط تعهد او).

## Open blockers

> ⚠️ **خط زیر خالی = GATE 0 باز = هر اکشن بیرونی ممنوع.** «temporary-A» (07-16) فقط مجوز آماده‌سازی propose-only بود، نه بستن G0. ثبت رسمی فقط با امضای [[03 - Projects/اونلی فنز/DecisionLog#DL-2026-07-20-G0 — حقیقتِ GATE 0|DL-2026-07-20-G0]].

**GATE 0: محل اقامت پارتنر ثبت و شاخه A/B انتخاب شود** — «محل اقامت پارتنر: ___ · تاریخ: ___ · پیامد: Branch A/B» ([[03 - Projects/اونلی فنز/architecture-blueprint-2026-07-04|بلوپرینت §۱]])

بلاکرهای باز (به‌روز 2026-07-20 عصر، بعد از ballot — [[03 - Projects/اونلی فنز/00 - Control/SCAN-LOCK-2026-07-20|SCAN-LOCK]]):
- **PAGE_SETUP = NO-GO** ([[03 - Projects/اونلی فنز/00 - Control/GATE-STAMP-2026-07-20|GATE-STAMP]]) — تا بسته‌شدن P0های باز [[03 - Projects/اونلی فنز/00 - Control/ARCHITECTURE-COMPLETE-2026-07-20/09_NOGO_PAGE_SETUP|NOGO]]
- ✅ PF-V5 = **REVOKED** (‏`APPROVED: REVOKE` — ‏DL-2026-07-20-PF-V5) · ✅ body-freeze **امضا شد** · ✅ Fansly قفل شد · ✅ remote=NO
- G0: ‏Branch A ‏**attested** (اظهار A) ولی باز — نوع منبع + تاریخ تأیید C خالی؛ سؤال آخر پرسشنامه حل‌نشده
- توافق: **A-SIGNED** — تأیید مکتوب C مانده (قبل از Day-Zero)
- PII در فایل‌های tracked (دو سند/۸ عکس `test/`) — انتقال R10 با رأی مالک؛ **الزامی قبل از هر remote آینده**
- Security Gate بسته (R11) · «Sydney» در کپی عمومی (R9) · ریسک #۱ (consistency زیر friction) تست‌نشده

## Active Context


- تمرکز فعلی: استودیو LEGAL_CLEAR با رسید ۰۹-۰۵؛ سند اجرایی v4.1 دارایی‌ها را با assets_ref فهرست می‌کند.
- تغییرات اخیر: export واترمارک‌دار SoT؛ آثار به رضایت‌نامهٔ per-asset وابسته‌اند (عنوان LEGAL_CLEAR ≠ مجوز عام انتشار).
- ۳ قدم بعدی: (۱) تصمیم مالک دربارهٔ کانال انتشار؛ (۲) نگاشت هر اثر به رضایت‌نامه؛ (۳) تعریف outcome_verifier پای.
- تصمیم‌های باز: کانال/زمان‌بندی انتشار.

## Progress

- 2026-09-07: v4.1 قواعد per-asset consent را در دستور اجرایی تثبیت کرد.
- **۲۰۲۶-۰۸-۰۱ — چه کار می‌کند:** بی‌تغییر از ۰۷-۲۰ — ۲۰۹/۲۰۹ تستِ سبز، دو کاکپیتِ propose-only، ۹/۹ safety net، حاکمیت روی DecisionLog قفل. این هفته نه کدِ تازه‌ای اضافه شد نه ادعای تازه‌ای ساخته شد.
- **۲۰۲۶-۰۸-۰۱ — چه مانده:** بی‌تغییر — سه امضای انسانیِ A + پر کردنِ ballot + بک‌لاگِ `R-*` (‏R9 ‏Sydney · R10 ‏PII ِ tracked · R11 ‏OpSec · R3 · merge ِ برنچِ sprint).
- **۲۰۲۶-۰۸-۰۱ — مشکلات شناخته:** بی‌تغییر، و یکی افزوده: این پا در `ORGANISM-STATE.business_legs` **غایب** است، پس رکودش را هیچ سنجه‌ای فریاد نمی‌زند — دوازده روز سکوتِ کامل بدونِ حتی یک آلارم.
- چه کار می‌کند: دوکاکپیت propose-only کامل و سخت‌شده (لنگر + استودیوی Creator با نام‌های neutral) · ۹/۹ safety net واقعی با اثبات ([[03 - Projects/اونلی فنز/00 - Control/ARCHITECTURE-COMPLETE-2026-07-20/03_SAFETY_NETS|03_SAFETY_NETS]]) · compliance ‏tick از manifest ‏fail-closed · زنجیرهٔ کامل C→vault→pipeline→payload دستی با کد tracking · KPI+funnel قابل‌سنجش (‏/kpi_import) · audit ‏HITL ‏(approvals.jsonl) · **209/209 تست سبز با runner مستند** · حاکمیت روی DecisionLog قفل (NO-GO stamp)
- چه مانده: **۳ امضای انسانی A** (G0 · REVOKE|RATIFY · توافق) + پر کردن [[03 - Projects/اونلی فنز/00 - Control/OWNER-BALLOT-2026-07-20|ballot]] · backlog ‏R-* ([[03 - Projects/اونلی فنز/00 - Control/ARCHITECTURE-COMPLETE-2026-07-20/07_BACKLOG_REMAINING|07_BACKLOG]]): scrub ‏Sydney از کپی عمومی (R9، پیش‌نیاز bio) · انتقال PII ‏tracked (R10، رأی مالک) · چک‌لیست OpSec ۲۴بندی (R11) · scrub مشترک (R3) · merge برنچ sprint با رأی Q10/Q11
- مشکلات شناخته: تعهد پارتنر مشروط به دیدن مسیر پول‌دهی · تاریخچهٔ git حاوی PII است تا مالک دربارهٔ remote جواب دهد (ballot ‏Q8) · pf_os فقط در درخت زندهٔ untracked (ریسک تک‌نسخه — R5) · `_global_stop` روی exception ‏fail-open (R2) · نوت‌های top-level ‏۱۳۵ خطای frontmatter ‏pre-existing (پاکسازی جدا)

## Next actions

- [x] 📱 **[[03 - Projects/اونلی فنز/06 - Ops & Runtime/PROP-D5-MINIAPP-SOCIAL-COCKPIT|PROP-D5]] فاز ۱ ساخته شد** (GO مالک ۰۸-۰۳) — روشن‌کردن با `OCTOPUS_PF_MINIAPP=1` + ری‌استارت
- [x] 🧠 **ADOPT ِ growth-archaeologist + دوزبانه‌سازی denylistها** (GO مالک ۰۸-۰۳)؛ REJECT ِ مغز دوم پابرجا
- [ ] 🔐 **رأی: هشت مسیر read-only ِ مینی‌اپ (`/api/state`,`/api/legs`,…) بدون احراز initData سرو می‌شوند** — روی تونل عمومی قابل‌دیدن‌اند (اسکراب‌شده ولی بی‌احراز)؛ مسیرهای PF عمداً پشت HMAC رفتند. هم‌ترازکردنشان = تصمیم مالک
- [ ] 🧪 **رأی: سوییت `pf_os` در state ِ زنده می‌نویسد** (`_ops/state/saba-bridge.jsonl`) — نیازمند redirect در `conftest.py`؛ همان کلاسِ باگی که conftest برای `approvals.jsonl` حل کرده بود
- [ ] 👁 **رأی: آیا متنِ درفت هم در مینی‌اپ دیده شود؟** فاز ۱ فقط شمار می‌دهد؛ نمایش متن = پهن‌کردن مرز قاعدهٔ #۷
- [ ] 🗺 **دستورالعملِ اجرا = [[03 - Projects/اونلی فنز/00 - Control/ROADMAP-10-STAGES-2026-07-12|ROADMAP ۱۰-مرحله]]** — مرحلهٔ ۱ (بستنِ GATE 0) کلِ زنجیره را باز می‌کند
- [ ] **۱۱ verdict منتظر تو** (THREAD-CLOSURE §۹): G0 · Playbook+M3-a · قاعدهٔ بالانس >$100 · سقف مغز AUD 15 · نردبان EXT-04 · برند Anar Soles · Fansly discovery-first · حالت labeling X · بلاک AU · فعال‌سازی لنگر · انجماد body
- [ ] **G0** — ثبت محل اقامت پارتنر + انتخاب Branch A/B (بلوپرینت §۱)
- [ ] ارسال پیام آماده به صبا (بازپرسیدن سؤال آخر + انتظارات — بلوپرینت §۴.۲) و ثبت جواب
- [ ] توافق مکتوب دونفره (بلوپرینت §۴.۱) — فقط بعد از Branch A
- [x] انجماد «expansion به body» — پیش‌فرض اعمال شد 2026-07-20 (DL-2026-07-20-BODY-FREEZE؛ ratify با امضای A) · hours واقعی از 07-10 بسته: ~۳h/هفته
- [ ] روز صفر زیرساخت (بلوپرینت §۵، ~۴–۵ ساعت) → شروع warm-up هفته ۱
- [x] Track B + C (desk research) — انجام شد 2026-07-04: GO conditional / GO limited
- [x] 2026-07-17: UI Creator hardening + VaultBank wiring + 22-asset seed (commits f72a83e/0a871e0) — ۱۵۵ تست سبز
- [ ] **مرحلهٔ ۵ (باقی‌مانده، بی‌نیاز به گیت):** `LearningBridge` را در `pf_admin._default_pipe()` پیش‌فرض کن (الان `AcquisitionBrain.with_bandit()` وجود دارد ولی به‌صورتِ اختیاری فعال نیست)؛ تستِ regression بنویس

## نوت‌های مرتبط

- [[03 - Projects/اونلی فنز/پرسشنامه پارتنر - پاسخ‌های صبا|پرسشنامه پارتنر — پاسخ‌های صبا]]
- [[03 - Projects/اونلی فنز/اونلی فنز|لاگ پیام‌های تلگرام — اونلی فنز]]
- [[03 - Projects/اونلی فنز/Knowledge_Base_Memory_Synthesis|Knowledge_Base_Memory_Synthesis]]
- [[03 - Projects/اونلی فنز/project-master-reference|project-master-reference]]

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]]

## 🎛 کابین کنترل (two-brain)

- کابین مشترک: ارتیفکت `fleet-live-dashboard` · نقشه (بایگانی‌شده/superseded): [[07 - Knowledge/_memory-blueprints/TWO-BRAIN-CONTROL-BLUEPRINT|TWO-BRAIN]] · نقشهٔ ساخت (بایگانی‌شده/superseded): [[07 - Knowledge/_memory-blueprints/FRANKENSTEIN-BUILD-PLAN|FRANKENSTEIN-BUILD-PLAN]]
- عملیات استاندارد از کابین (intent → sendPrompt): «تست <پروژه>» = validators + چک کد + تست قرارداد · «بساز» = اسکلت از `_Templates` + ثبت همین‌جا · «آرشیو» = فقط انتقال به `_Archive`/`_Duplicates` (هرگز حذف واقعی).
- تست قرارداد این پروژه: هنوز تعریف نشده — طبق BUILD-PLAN §۲ تعریف شود.