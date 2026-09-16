---
type: structural-analysis
status: evidence-backed
date: 2026-08-21
session_id: SESSION-20260820-21
scope: four uploaded docs as one multi-layer Vault-based OS
documents:
  1: "CHATBOX-MEGAPROMPT 2026-08-12 — Chat Box to brain/memory/equations/architecture"
  2: "TYPED-EVENTS-RUNBOOK 2026-08-12 — instrument → stream → migrate"
  3: "GAP-ANALYSIS 2026-07-06 — 10 structural flaws"
  4: "MASTER-SPEC v1.4 2026-07-06 — vault-based agent-first OS"
analysis_rules: "only from uploaded files; inference labeled; conflicts recorded; missing requirements listed"
---

# A) Executive Structure Summary

این چهار سند مجموعاً یک **سیستم‌عامل شخصی vault-based و agent-first** را توصیف می‌کنند که در گذار از «ذخیره‌سازی نوت» به «چرخهٔ عملیاتی زنده» است: حاکمیت انسانی (L1)، کنترل دومغزی با نردبان استقلال L0–L3 و حلقهٔ ۶گامی (L2)، هوش خارجی Fugu (L2b، خریداری‌شده، propose-only پشت گیت)، ingest/امنیت چندگیتی (L3)، حافظه/دانش (L4)، پروژه/عملیات (L5) و لایه‌های people/log/handoff/agent (L6–L9). دو سند ۰۸-۱۲ یک **مأموریت اجرایی مجزا** می‌سازند: اتصال Chat Box به اندام‌های موجود (نه مغز جدید) با قراردادهای عرضی Typed Event + Run ID + Context Engine + Truth Layer/Verifier، و گیت پذیرش فناوری مبتنی بر شواهد runtime (TDR). سند ۰۷-۰۶ (Gap Analysis) ده نقص ساختاری با رفرنس بیرونی ثبت می‌کند که سه‌تایشان (ارزیاب، observability تفویض، edge execution) پیش‌شرط L2 هستند. کل ساختار حول اصول «Improve don't rewrite»، «propose-only مگر پشت گیت انسانی»، «شاهد قبل از ادعا» و «حقیقت بر ظاهر» یکپارچه است.

# B) Layer Map

| لایه | نقش | فایل‌های پشتیبان (از اسناد) | ورودی | خروجی | وابستگی | گلوگاه |
|---|---|---|---|---|---|---|
| L1 Governance | قانون اساسی، قواعد، مسیر ممنوع، چرخهٔ عمر | PROJECT_INSTRUCTIONS.md | تصمیمات مالک | قواعد جهانی | Property Schema، .agentignore، .claude/settings.json | سقف ۲۰۰ خط (ادعای سند) |
| L2 Control | دومغزی، حلقهٔ ۶گامی، نردبان L0–L3 | TWO-BRAIN-CONTROL-BLUEPRINT.md | SYSTEM-STATE، verdict انسانی | پیشنهاد، mutation ledger، فاز بعد | §Security Gate (باز)، git init (باز) | گیت باز، git نبود (در زمان سند) |
| L2b External Intelligence | موتور ستون ۳؛ Fugu/Ultra | Sakana Fugu API [VERIFIED/ACQUIRED] | سیگنال ستون ۱/۲، دستور انسان | سنتز/پیشنهاد | کلید+rotation+budget+Gate+git | کلید OPEN، budget باز، Ultra pool ثابت (C17) |
| L3 Ingest/Security | مجوز ورود، قرنطینه، اسکن | PHASE-0A-EXCLUSION-SPEC + REVIEW.md | کاندیداهای .md | ingest/quarantine/skip manifests | gitleaks (host)، ROTATION_CHECKLIST | gitleaks روی host اجرا نشده؛ RTL شکننده |
| L4 Memory/Knowledge | حافظهٔ پایدار، سنتز، دانش | knowledge.md، *-memory.md، _memory/ | نوت‌ها، منابع | نوت created_by:agent + sources≥2 | templates، MOC، _memory/ | _memory/ mount پایدار نیست |
| L5 Project/Ops | چرخهٔ عمر، Active Context، G0–G4 | project.md، *-project-memory | Inbox، تصمیمات | PROJECT.md، DecisionLog | templates، لاگ | GATE 0 باز |
| L6–L9 People/Log/Handoff/Agent | موجودیت، لاگ، انتقال، ربات | person/log/handoff/agent.md | تعامل، پایان جلسه | نوت person، HANDOFF | templates، Architect | ریسک حریم خصوصی |
| Chat Box (مأموریت ۰۸-۱۲) | «دهان» واحد | gateway موجود + Collaborator + /api/ask | متن مالک | پاسخ + facts + events | owner_recall، cortex، business_brain، vault، explainerها | intent router، context budget، truth layer |

# C) Canonical Documents

- **حاکمیت/مرجع نهایی**: PROJECT_INSTRUCTIONS.md (فقط‌خواندنی برای ایجنت) — بالاترین.
- **Spec مرجع اجرایی ingest**: PHASE-0A-EXCLUSION-SPEC (proposed، در حال supersede کردن BUILD-PROMPT).
- **مرجع ریسک/گپ**: REVIEW.md.
- **مرجع مفهومی کنترل**: TWO-BRAIN-CONTROL-BLUEPRINT (draft/proposal).
- **مرجع یکپارچه**: Master Architecture Spec (draft v1.4؛ پس از ratify → v2 canonical).
- **حافظه/مرور/proposal**: *-memory.md، templates، handoff، gap analysis، دو سند مأموریتی ۰۸-۱۲ (اجرایی).
- **رقابت مرجعیت باز (ثبت‌شده در سند)**: دو master doc در Project-F؛ ACQUISITION-ENGINE vs MASTER-BUILD/Playbook؛ PHASE-0A supersede BUILD-PROMPT. Master Spec خودش می‌گوید تا ratify، PROJECT_INSTRUCTIONS مرجع می‌ماند (استنباط: ترتیب برتری اعلامی سند معتبر است).

# D) Operational Flow

① Capture (تلگرام/Inbox/cron) → 00-Inbox → ② Decision Tree → پروژه/دانش/شخص → ③ Read-before-write → ④ Ingest Eligibility (Gate1 مسیر → Gate2 قرنطینه → Gate3 اسکن secret → Gate4 encoding) → manifest → ⑤ Memory Synthesis (created_by:agent + sources≥2) → ⑥ Control Loop ۶گامی (ادراک → تشخیص → پیشنهاد [Fugu propose-only] → verdict انسانی → اعمال [L2/L3 پشت Gate+git+budget] → سنجش) → ⑦ Handoff.

- **read-only**: نوت‌ها برای ایجنت، manifest برای پایین‌دست.
- **propose-only**: پیشنهاد دکتر/Fugu، memory synthesis، equation/architecture explainerها، Chat Box effect requests، F2–F5.
- **human-approved**: verdictها، semantic/core memory write، گیت، پول، پیام خارجی، secret rotation.
- **execution-blocked**: لیست سیاه همیشه human-only (charter، secret، پول، پیام خارجی، تغییر گیت).

# E) Security and Boundary Model

- گیت‌ها: Secret boundary (§۱۰، فعال)؛ مسیر ممنوع .agentignore+.claude/settings.json؛ تلگرام whitelist؛ Ingest Gate1–4 (proposed، Gate3 با gitleaks+regex+[F4]، SCAN-UNAVAILABLE=full stop)؛ §Security Gate (باز)؛ git rollback (باز)؛ kill-switch ۳سطحی (proposed)؛ human approval gate (فعال)؛ agent-checkpoint قبل از >۵ فایل؛ dry-run validators؛ rotation checklist (۴ سطر CRITICAL+OPEN)؛ Fugu gate (کلید+budget باز).
- **آسیب‌پذیری‌های صریح ثبت‌شده (نرم‌سازی نشده)**: نشت secret از .md checklist-named؛ RTL glob fragility؛ SCAN-UNAVAILABLE downplay؛ gate فقط DB را محافظت می‌کند نه vault/Desktop؛ encoding fragility؛ orphan metric قاطی با island cluster؛ relation extraction بدون precision audit؛ _Archive غایب با backup gate تأییدنشده؛ کلید Fugu در صورت عدم rotation؛ budget بدون ceiling. Gap #1 (ارزیاب self-judge، ~۵۰٪ tamper در natural runs) و #۲ (تفویض بدون attribution).

# F) State and Control Architecture

- dashboard (fleet-live-dashboard ✅)؛ watchdog (بازسازی فاز ۰)؛ Mutation Ledger (فاز ۳)؛ ledger append-only (✅ ref)؛ autonomy L0–L3 (ratified؛ L2/L3 قفل)؛ mutation flow (propose→verdict→whitelist-apply)؛ rollback git (نبود)؛ kill-switch ۳سطحی (proposed)؛ Gateهای G0–G4 (فعال، G0 باز)؛ Fugu L2b (proposed).
- حلقهٔ ۶گامی: ادراک → تشخیص → پیشنهاد → verdict → اعمال → سنجش. متریک: شاخص استقلال >۵۰٪ applied بدون لمس انسانی در ۴ هفته.
- مأموریت ۰۸-۱۲ اضافه می‌کند: Run ID + Typed Events (RUN_CREATED…RUN_COMPLETED، sequence صعودی، idempotent، append-only)، run store (create/append/get/list/mark_terminal)، SSE بعد از TDR، Truth/Verifier (CLAIM_CREATED/VERIFIED با evidence خارجی)، control events (PAUSE/RESUME/CANCEL/APPROVAL = درخواست، نه authorization).

# G) Knowledge and Memory Architecture

- پایدار (durable): 07-Knowledge + *-memory.md (memory-synthesis، created_by:agent + sources≥2).
- عملیاتی (active): ## Active Context + ## Progress در PROJECT.md + HANDOFF.md.
- تصمیم‌گیری: لاگ پروژه + DecisionLog.
- ingest manifest: _memory/ingest-manifest.json (منبع یکتای پایین‌دست).
- entities: 09-People، 03-Projects، 05-Agents.
- سیاست حافظه در مأموریت ۰۸-۱۲: session (مجاز/موقت) vs episodic candidate (may_authorize=false) vs semantic/core (write ممنوع بدون رأی). «یادت بماند» → پیشنهاد حافظه، نه write.
- گلوگاه: _memory/ mount پایدار نیست؛ ~۲۴٪ نوت‌ها report/handoff → خارج از recall.

# H) Conflicts / Unresolved

1. **Fugu در مسیر چت؟** Master Spec L2b (Fugu موتور، VERIFIED/ACQUIRED 07-06) در مگاپرامپت چت (08-12) ذکر نشده؛ مگاپرامپت فقط Cortex + Business Brain + «4d وصل نیست» را می‌خواهد. (استنباط: یا Fugu از مسیر چت کنار گذاشته شده یا سند چت قدیمی‌تر از تصمیم است؛ ثبت شد.)
2. **ارزیاب self-judge (Gap #1)** در برابر «متریک قطعی، نه خوداظهاری Fugu» (§۱۶): سند کنترل نیت دارد ولی reference runner جدا و holdout set را نداریم — Gap صریح می‌گوید غایب است.
3. **git init**: Master Spec C1 «باز» (پیش‌شرط L2/rollback) در حالی که پروتکل ۰۸-۱۲ می‌گوید «هیچ commit مگر دستور صریح» — ناسازگار نیست ولی git در زمان سند موجود نبود (در واقعیت امروز repo هست — STALE).
4. **run_all.py**: مگاپرامپت آن را LOCKED می‌کند (فقط برای ظاهر سبز نشود) — تعارض با هر تغییر registry بدون رأی.
5. **درجهٔ مرجعیت**: دو master doc در Project-F؛ ACQUISITION-ENGINE vs MASTER-BUILD؛ PHASE-0A supersede BUILD-PROMPT — همگی باز.
6. **Fugu Ultra (C17)**: pool ثابت + خریداری‌شده؛ سیاست جداسازی دادهٔ حساس هنوز ratify نشده — نقض survival filter در صورت خطا.
7. **budget تک‌عددی** (Gap #8) در برابر §۱۶ budget ceiling روزانه: چندبُعدی (per-workflow) غایب است.
8. **حافظهٔ فایل-محور به‌عنوان primitive** (Gap #3): EXPERIENCE-LEDGER ثبت‌کننده است، حافظهٔ خود-بهبوددهنده نیست — §۱۶ LEARNING-STATE.json فقط state حلقه است.

# I) Missing Requirements

فنی: reference runner/trusted evaluator جدا (Gap #1)؛ delegation-scoped observability gateway با delegation_id (Gap #2)؛ edge/local execution tier برای C17 (Gap #5)؛ memory scoping per-identity (Gap #6)؛ pre-launch permission gate برای زیرایجنت (Gap #7)؛ budget چندبُعدی با soft/hard + circuit breaker (Gap #8)؛ audit unified با requestor+verdict bind (Gap #9)؛ لایهٔ vision/multimodal (Gap #10).
معماری: event schema + run store adapter (مأموریت ۰۸-۱۲، ابتدا reuse)؛ equation explainer و architecture explainer (verify موجودی)؛ Truth Layer/Verifier با evidence خارجی؛ Technology Decision Records برای ۹ candidate؛ runtime baseline (۲۰ درخواست)؛ کنترل events؛ SSE trial (فقط بعد از TDR).
عملیاتی: بستن §Security Gate؛ git init (در زمان سند)؛ rotation ۴ سطر CRITICAL؛ تأیید _Archive+backup؛ mount پایدار _memory/؛ gitleaks روی host؛ ratify PHASE-0A؛ تعیین budget ceiling Fugu؛ سیاست جداسازی Fugu Ultra (C17).

# J) Final Deliverables

## 1) نقشهٔ نهایی لایه‌ها
L1 Governance (انسانی) → L2 Control (دومغزی، L0–L3) → L2b Fugu (propose-only پشت گیت) → L3 Ingest/Security (چهارگیت) → L4 Memory/Knowledge → L5 Project/Ops (G0–G4) → L6–L9 People/Log/Handoff/Agent؛ روی همه: مأموریت چت ۰۸-۱۲ (Chat Box بهعنوان façade یکپارچه) + شریان Typed Events/Run ID + Truth Layer/Verifier.

## 2) جدول وابستگی کلیدی
PROJECT_INSTRUCTIONS → همه (قانون)؛ §Security Gate + git → L2/L3/F1؛ ROTATION_CHECKLIST + gitleaks → Gate3؛ PHASE-0A manifest → پایین‌دست؛ _memory/ → L4؛ Fugu (کلید+budget) → L2b/F2–F5؛ PolicyGate + owner verdicts → هر effect؛ /api/ask + Collaborator + owner_recall → Chat Box؛ run store + event schema → مأموریت ۰۸-۱۲.

## 3) نیازمندی‌ها به ترتیب اولویت
P0: rotation ۴ سطر CRITICAL؛ بستن GATE 0؛ تأیید _Archive+backup؛ ثبت کلید Fugu + budget ceiling؛ سیاست Fugu Ultra/C17.
P0 (مأموریت ۰۸-۱۲): discovery ضدتکرار؛ runtime baseline؛ event schema v1 + run store؛ instrumentation بدون تغییر رفتار.
P1: gitleaks روی host؛ ratify PHASE-0A؛ git init + §Security Gate؛ فعال‌سازی F5؛ Gap #1 (reference runner) و #۲ (delegation observability) قبل از L2.
P2: mount پایدار _memory/؛ حل چندمرجعیتی Project-F؛ precision audit؛ per-subtree orphan؛ Chat Box integration (R)؛ SSE (بعد از TDR).
P3: F1 پشت Gate+git+budget؛ ratify Master Spec v2؛ Gap #5/#6/#7/#8/#9/#10.

## 4) پیشنهاد بازطراحی (استنباط)
حفظ L1–L9 و اعمال اصول مادر؛ افزودن سه قرارداد عرضی از مأموریت ۰۸-۱۲ (Typed Events، Context Engine، Truth Layer) بدون اندام جدید؛ حل ارزیاب با reference runner مستقل (Gap #1) قبل از هر L2؛ تفکیک Fugu به دو مسیر (چت: اندام‌های موجود؛ پشت‌صحنه: F2–F5 propose-only)؛ باند کردن budget چندبُعدی؛ حافظهٔ کاری فایل-محور به‌عنوان primitive خواندنی/قابل‌بازنویسی با origin+source.

## 5) ده سؤال دقیق از صاحب سیستم
1. آیا Fugu در مسیر پاسخ چت حضور دارد یا فقط پشت‌صحنه (F2–F5)؟ (Conflict H1)
2. آیا git repo فعلی مرجع rollback برای L2 است؟ (C1)
3. budget روزانه/چندبُعدی Fugu: چه سقف‌هایی و کدام tier؟ (C16)
4. سیاست Fugu Ultra برای Project-F: فقط استاندارد opt-out؟ (C17)
5. reference runner/ارزیاب مستقل (Gap #1): چه شکلی؟ (هولداوت/فایل/تست)
6. آیا «یادت بماند» باید به memory candidate برود (propose) یا مسیر تأیید مشخصی دارد؟
7. دو master doc Project-F: کدام canonical؟ (C3)
8. run_all.py: تغییرات registry فقط با رأی مالک؟ (قفل مگاپرامپت)
9. rollback path برای event/run store: چه سطح durability ادعا شود (NON_DURABLE تا اثبات)؟
10. SSE/WebSocket: آیا دوطرفهٔ واقعی (pause/approval زنده) لازم است یا HTTP کافی است؟

## محدودیت‌های تحلیل
- فقط بر اساس چهار فایل آپلودشده؛ برچسب‌های [استنباط] جدا شده‌اند.
- همهٔ conflictها و ریسک‌های امنیتی بدون نرم‌سازی ثبت شدند.
- اسناد ۰۷-۰۶ و ۰۸-۱۲ از دو نقطهٔ زمانی‌اند؛ وضعیت اجرای امروزِ repo خارج از scope این تحلیل است.
