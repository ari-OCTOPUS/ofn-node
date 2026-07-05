---
type: handoff
updated: 2026-07-06
---

# HANDOFF — وضعیت برای جلسه بعد

## جلسه هفدهم 2026-07-06 (Cowork) — 🟢 گیت LIFTED + throttle دستی ناوگان + لغو killswitch

سه verdict آری در یک پیام: throttle دستی · گیت را ببند («جمعش کن») · backlog غیر-md را خودت مهندسی کن.

- **🟢 Security Gate رسماً برداشته شد:** ریشهٔ برگشت‌های مکرر پیدا شد — §۲ [[04 - Architect System/architect/ARCHITECT_CHARTER|CHARTER]] دو خط متناقض diff-مانند داشت (بسته 07-03 / باز 07-05) و بقیهٔ فایل‌ها از خط کهنه می‌خواندند. حالا یک خط canonical «LIFTED 2026-07-06» + هدر [[ROTATION_CHECKLIST]] هماهنگ + ثبت در [[_memory/EXPERIENCE-LEDGER|ledger]]. ۱۴ ردیف HIGH/MEDIUM = backlog چرخش، **گیت نیستند**. این داستان بسته است — دوباره بازش نکن.
- **Throttle دستی (به‌جای killswitch):** `doctor-research` هر ۲ ساعت · `learning-engine-loop` هر ۶ ساعت (:35) · trio ‏pulse/consolidator/focus-board هر ۶ ساعت · ۱۹ اسکات روزانه دست‌نخورده · **`fleet-killswitch-1day` (فردا ۱۷:۰۰) disabled شد.** بار: ~۲۱۲ → ~۴۵ اجرا/روز.
- **backlog غیر-md:** پلن triage در [[00 - Inbox/NONMD-TRIAGE-PLAN-2026-07-06|NONMD-TRIAGE-PLAN]] — propose-only، اجرای انتقال با verdict.
- **معوق آری:** git init ویندوزی (runbook 04) · «Run now» روی تسک‌های تازه‌throttle‌شده اگر روی pre-approve مکث کردند.

## جلسه شانزدهم 2026-07-06 (Claude Code) — دو مغز: verdictها بسته شد + FRANKENSTEIN-BUILD-PLAN + deploy-lab

verdict آری: «پیشنهاد تو پیش برویم» → هر ۴ تصمیم باز §۷ [[_memory/TWO-BRAIN-CONTROL-BLUEPRINT|TWO-BRAIN-CONTROL-BLUEPRINT]] با توصیهٔ ایجنت بسته شد (status → active): فاز ۲ اول · موتور ستون۳ = Claude پلکانی (Fugu فقط escalation پشت سقف بودجه — راستی‌آزمایی وب: ضریب پنهان ۵–۱۵×) · ریتم = burst کران‌دار · برازندگی کیفی تا ~۴ هفته دادهٔ [[_memory/EXPERIENCE-LEDGER|ledger]].

- **رکن ساخت:** [[_memory/FRANKENSTEIN-BUILD-PLAN|FRANKENSTEIN-BUILD-PLAN]] — ۸ اندام با معیار پذیرش، قرارداد رسمی حذف/ساخت/تست، spec پچ ارتیفکت `fleet-live-dashboard`، ترتیب اجرا برای Fable 5.
- **اتصال رسمی کابین:** بخش «🎛 کابین کنترل (two-brain)» به هر ۸ PROJECT.md افزوده شد (افزایشی، `updated` بروز).
- **اندام ۱ زنده شد:** تسک `perception-refresh` (هر ۲ ساعت، propose-only) → بازتولید `_memory/SYSTEM-STATE.md` از زمان‌بند زنده/git/Inbox/validatorها.
- **مسیر موازی deploy-lab (جلسهٔ قبل‌تر امروز):** clone کامل vault در `Desktop\backup-deploy-lab` + تسک `deploy-lab-loop` (هر ۱۵ دقیقه، ۷ چک آمادگی، خاموشی خودکار بعد از DONE) + یک پاس بزرگ ۸-ایجنتی در حال اجرا (routing کل Inbox کپی + فیکس فرانت‌متر/لینک). کلید توقف: فایل `_deploy/STOP` در کپی.
- **برای آری:** (۱) **URL ارتیفکت `fleet-live-dashboard` را بده** — تنها ورودیِ لازم برای پچ پنل پروژه‌ها (BUILD-PLAN §۳؛ URL هیچ‌جای vault ثبت نیست) · (۲) «Run now» روی `perception-refresh` و `deploy-lab-loop` برای pre-approve · (۳) verdict سقف بودجهٔ روزانهٔ ستون۳ (پیشنهاد: AU$1/روز).

## جلسه پانزدهم 2026-07-06 (Cowork) — Replication Kit: کپی دقیق قابلیت‌ها + Architect

خواستهٔ آری: کپی دقیق تمام قابلیت‌ها/featureهای ساختار، مخصوصاً Architect — template قابل‌اجرا، مقصد Inbox.

- **ساخته شد (تماماً additive، ۵۳+۱ فایل):** پوشهٔ `00 - Inbox/replication-kit/` — `BLUEPRINT.md` (spec ۸ لایه؛ §۶ = Architect کامل: P1–P11، ۵ core، autonomy ladder، kill-switch، حلقهٔ gated، بودجهٔ دو-mode، دو مغز) + `scaffold.py` (بدون هیچ overwrite) + `seed/` (کپی دقیق قانون اساسی/[[06 - Architecture Maps/Property Schema|Property Schema]]/۶ template/هر دو validator/gitleaks/.agentignore/.claude + اسکلت‌های sanitized رجیستری/RATIFIED-TASKS/ROTATION/دشبورد/_memory).
- **تست:** scaffold در sandbox اجرا شد؛ هر دو validator روی vault تولیدشده سبز (۱۵/۰ · ۳۰/۰). اسکن secret روی kit: صفر مقدار محرمانه؛ دو مسیر secret شخصی settings.json با الگوی generic جایگزین شد.
- **گزارش کامل:** [[00 - Inbox/2026-07-06 0159 replication-kit-final-report|گزارش نهایی replication-kit]].
- **⚠️ checkpoint نشد:** vault هنوز git repo نیست (verdict قبلی آری: نه به init — human-only). دستهٔ این جلسه هم مثل جلسهٔ ۹ بدون rollback ماند.
- **برای آری:** (۱) verdict روی git init یا پذیرش بدون checkpoint · (۲) اگر SYSTEM-BLUEPRINT-v3 ratify شد، sync شدن kit را بخواه · (۳) جای دائمی kit (ماندن در Inbox یا انتقال به 04) — تصمیم تو.

### ادامه جلسه ۱۵ — verdict «maximum risk» + bootstrap مربی Learning Engine

- **verdict آری: max risk** → تفسیر و مرز در [[_memory/EXPERIENCE-LEDGER|ledger]] (آخرین ردیف): سقف مجاز منشور، نه دور زدن گیت. Engine در **shadow** روشن شد: `04 - Architect System/learning-engine/` (STATE + CONTRACT) · ردیف در [[05 - Agents/AGENT_REGISTRY|رجیستری]] · سطر در [[_memory/HEARTBEAT|HEARTBEAT]] · گسترش [[06 - Architecture Maps/Property Schema|schema]] با `trigger: loop`. specهای MASTER v1.3 و LEARNING-ENGINE v1.1 (با verdictهای ۱–۸) در Inbox.
- **قفل‌های باقی‌مانده (فقط دست آری):** rotation ۴ CRITICAL · ثبت کلید Fugu در [[ROTATION_CHECKLIST]] · عددکردن `budget_ceiling_daily` · git init · ذخیره `SELF-LEARNING-LOOP-SPEC` در vault. تا آن موقع Engine هیچ call خارجی نمی‌زند.

### ادامه ۳ جلسه ۱۵ — STARTUP-PROTOCOL + اولین boot + MASTER v1.4/GAP-ANALYSIS

- **boot interview دائمی شد:** [[04 - Architect System/learning-engine/STARTUP-PROTOCOL|STARTUP-PROTOCOL]] + بانک سوال YAML؛ گام صفرِ «جلسه بعد باید» شد. boot#1 اجرا شد — جواب‌ها در LEARNING-STATE + [[_memory/EXPERIENCE-LEDGER|ledger]].
- **⚠️ git:** verdict آری «تو بزن» ولی mount سندباکس git-metadata را خراب کرد → **اقدام دستی آری:** حذف `.git` ناقص + اجرای runbook [[00 - Inbox/build-proposals/04-git-init-runbook-2026-07-05|04]] در PowerShell.
- **ثبت‌های نو:** [[00 - Inbox/2026-07-06 0245 MASTER-ARCHITECTURE-SPEC-v1.4-draft|MASTER v1.4]] (v1.3 → superseded) · [[00 - Inbox/2026-07-06 0245 GAP-ANALYSIS-2026|GAP-ANALYSIS]] (۱۰ ایراد؛ رفرنس‌ها verify-نشده) · ردیف #24 کلید Fugu در [[ROTATION_CHECKLIST]] (OPEN، تکمیل مالک).
- **حلقه self-mutation زنده شد:** تسک `learning-engine-loop` (هر ساعت :44، بی‌صدا) — جهش bounded-auto فقط روی [[04 - Architect System/learning-engine/MUTATION-WHITELIST|whitelist]]، anchor در [[05 - Agents/RATIFIED-TASKS|RATIFIED-TASKS]]، ۱ جهش/روز، kill=فایل STOP. **آری: یک‌بار «Run now» بزن تا ابزارها pre-approve شوند.**
- **معوق آری:** lift رسمی گیت (دو ویرایش دستی) · تکمیل ردیف #24 · git init ویندوزی · ذخیره SELF-LEARNING-LOOP-SPEC.

### ادامه ۴ جلسه ۱۵ — 🟢 LAPTOP-PILOT روز صفر: «زنده کن کل ساختارو»

- **۲۶ تسک زنده شد:** ۵ ratified + ۱۹ اسکات + survival-heartbeat + learning-engine-loop. تاریک (تنها استثنا): لاین‌های پرفرکانس selfimprove (محافظ سهمیه). طرح: [[00 - Inbox/2026-07-06 0350 LAPTOP-PILOT-30D-DESIGN|LAPTOP-PILOT-30D]] · تحقیق‌ها: [[00 - Inbox/2026-07-06 0330 research-self-mutation-architecture|خودجهش/DGM]] + [[00 - Inbox/2026-07-06 0345 research-corporate-mycelial-patterns|الگوهای شرکتی]].
- **جلسه بعد (bootstrap-watchdog):** تطبیق زمان‌بند↔ratified طبق معمول + چک اولین جهش learning-engine-loop (دقیقه ۳۵ هر ساعت؛ سقف ۱/روز) + شمارش beat اسکات‌ها.
- **معوق آری (بلاکرهای پایلوت):** P1 ستون‌های ROTATION+lift charter · P2 تأیید `git log` ویندوزی · «Run now» روی تسک‌های تازه‌enable برای pre-approve · اپ باز بماند · P5–P7 تا هفته ۳.

## جلسه چهاردهم 2026-07-05 (Cowork) — رکنِ ساخت: MYCELIAL-MASTER-SPEC v0.1 + اتصالِ ۸ پروژه

خواستهٔ آری: سندِ حرفه‌ایِ معماریِ قارچی (*Armillaria*/کیلومترها) که هر ایجنت با آن خودش را بهتر کند، **رکنِ اصلیِ ساخت** باشد، به **همهٔ پروژه‌ها** وصل شود، ~۸۰٪ طراحی را برای **Fable 5** آماده کند، و چرخهٔ **build/test/delete** بدهد. تحقیقِ SDD + Reflexion + orchestration انجام شد.

- **ساخته شد:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] (v0.1) — ستونِ SDD با ۱۱ بخش: META/CHARTER/معماریِ مایسیلیایی(+Mermaid)/رجیستریِ اتصالِ ۸ پروژه/پلنِ M0–M8 با برچسبِ `[→F5]`/چرخهٔ امنِ build-test-delete/طراحیِ مدل-حافظه-ابزار/پروتکلِ Reflexion/trade-offs(۱–۱۰)/DoD/handoff/changelog. **بر پایهٔ اندام‌های موجود ساخته شد نه تکراری** ([[MYCELIAL-ARCHITECTURE-vfinal]]، [[BUILD-BACKLOG]]، [[SURVIVAL-ARCHITECTURE]]، [[LAPTOP-RUNTIME]]).
- **اتصالِ رسمی (§۳):** هر ۸ پروژه node شد + اندام‌های افقی (EffectorGate/Anchor Ledger/Budget/Kill-switch/Fleet/Doctor). لینک از [[01 - Dashboard/Home|Home]] بخش «رکنِ ساخت».
- **استراتژیِ مدل (تحقیق):** Fable 5=سازنده · Claude (Haiku→Sonnet/Opus)=runtime · **Fugu فقط escalationِ پشتِ budget-gate** (ضریبِ پنهانِ ۵–۱۵× توکن با سقفِ AU$30 خطرناک).
- **گاردِ delete:** hard-delete ممنوع → `mv` به `_Duplicates` + dry-run + verdict؛ و **فعال‌سازیِ delete مشروط به M5 (بکاپِ off-box)** چون vault خارج از git است (تنها rollback).
- **اعتبارسنجی:** هر دو validator سبز برای فایل‌های این جلسه؛ صفر مقدارِ محرمانه در spec (اسکن شد). spec در `04 - Architect System/` است → خارج از دامنهٔ frontmatter-validator (مثل بقیهٔ فایل‌های آن پوشه).
- **برای آری — verdictهای باز (§۱۰ spec):** (۱) lift رسمیِ Security Gate · (۲) `git init` (پیش‌شرطِ SDD/L2) · (۳) DNA/PII · (۴) ✅ بک‌لینکِ ستون در هر ۸ PROJECT.md اعمال شد (اتصالِ دوطرفهٔ §۳؛ افزایشی، `updated` بروز شد) · (۵) اجرای handoff به Fable 5 (موج۱: M0→M1→M2→M3).

### افزودهٔ همین جلسه (آری موقتاً غایب — «حلقهٔ دایره‌وار، پلن را جلو ببر، توکن دارم»)

- **کنترل‌پنلِ تعاملی ساخته شد:** `01 - Dashboard/CONTROL-PANEL.html` + آرتیفکتِ Cowork `system-control-panel` — ادغامِ `BRAIN-FOCUS-BOARD` + `SYSTEM-DASHBOARD` در یک کاکپیت + **کنسولِ Doctor** (askClaude/sendPrompt) + لنزِ **🏗️ Build Spine** (§۳ + M0–M8 + verdictها) + Scout Intelligence. تسکِ `system-dashboard` **disabled** (reversible؛ ادغام‌شد؛ بنرِ جانشین روی HTMLش).
- **حلقهٔ خودکار راه افتاد:** تسکِ `build-planner-loop` (`*/30 * * * *`، بی‌صدا، **فقط-پیشنهاد**) — هر ۳۰دقیقه یک آیتم از صفِ [[00 - Inbox/AUTONOMOUS-RUN-2026-07-05|AUTONOMOUS-RUN]] را جلو می‌برد و به [[00 - Inbox/build-proposals/_README - Build Proposals|build-proposals]] می‌نویسد. صف: پکِ کدجنِ Fable موج۱–۳ · Reflexion روی spec · runbookِ git-init · تحقیقِ AI-eng و opsec · REVIEW-PACKET · idle. قواعدِ سخت در پرامپتِ تسک: propose-only، بدونِ charter/PROJECT/spec/task/کد/رمز/git، فقط نوشتن در build-proposals + AUTONOMOUS-RUN + append ledger.
- **⚠️ مهم برای آری وقتی برگشتی:** (۱) تسکِ نو ممکن است روی **pre-approve ابزار** مکث کند — یک‌بار **«Run now»** روی `build-planner-loop` بزن تا WebSearch/Write تأیید شوند، وگرنه اجراها می‌ایستند. (۲) تسک‌ها فقط وقتی **اپ باز است** اجرا می‌شوند. (۳) وقتی برگشتی: `build-proposals/` را مرور و verdict بده، بعد `build-planner-loop` را **disable** کن.

## جلسه سیزدهم 2026-07-05 (Cowork) — اجرای P0 + بازسازی ۲ تسک هسته + verdict گیت (همه creds فیک)

اجرای مستقل [[00 - Inbox/Prompt - خواندن کامل سیستم و آشتی زمان‌بند 2026-07-05|پرامپت مادر P0]] (read-only) → خروجی [[00 - Inbox/SYSTEM-STATE-2026-07-05|SYSTEM-STATE-2026-07-05]].

- **آشتیِ زمان‌بندِ زنده:** ۴۹ تسک / ۳۴ enabled (نه «۶»). وارونگی: ۲۶ اسکات/selfimprove که رجیستری «عمداً تاریک» می‌گوید enabled‌اند؛ ۳ تسک هسته غایب بودند (`brain-focus-board`,`system-dashboard`,`experience-review`)؛ [[_memory/HEARTBEAT|HEARTBEAT]] beat غیرواقعی داشت؛ ناوگان Research Radar + `radar-qa` مستندنشده. جزئیات + جدول ۴کلاسه: [[00 - Inbox/SYSTEM-STATE-2026-07-05|SYSTEM-STATE]].
- **verdict آری (Q1):** `brain-focus-board` (`50 */3 * * *`) و `experience-review` (`30 21 * * 0`) از [[05 - Agents/RATIFIED-TASKS|RATIFIED-TASKS]] **بازسازی شد** (focus-board هر ~۳س · review امشب ~۲۱:۳۵). `system-dashboard` عمداً بیرون — **تبصره:** self-heal §۳.۳ برمی‌گرداندش مگر از «جدول تسک‌های ratified» رجیستری حذف شود (verdict باز).
- **verdict آری (Q2):** تصمیم تاریک/روشنِ ۲۶ تسک → واگذار به `experience-review` هفتگی (پرامپتش برای پیشنهاد retire/keep آپدیت شد).
- **🔴 verdict آری (Security Gate):** «همه credentialها فیک → گیت را بردار». **۳ فایل `.env` زندهٔ داخل vault توسط آری حذف شد** (Lead/کاریابی‌bot · Ziman/control-brain · architect/langar) — verify: صفر `.env` باقی. **ولی lift رسمی معوقِ ویرایش دستی آری است** ([[04 - Architect System/architect/ARCHITECT_CHARTER|CHARTER]] برای ایجنت immutable · ستون وضعیت [[ROTATION_CHECKLIST]] فقط انسان). ثبت append در [[_memory/EXPERIENCE-LEDGER|ledger]].
- **git:** آری «نه» → بدون rollback؛ طبق منشور L2 هم بدون git روشن نمی‌شود → autonomy عملاً propose-only می‌ماند حتی با گیتِ باز. deploy دامنه‌ها هم‌چنان پشت rule 4 رجیستری (Phase 4 + verdict per-domain).
- **برای آری:** (۱) دو ویرایش دستی گیت (پایین) تا رسمی شود · (۲) «Run now» روی `brain-focus-board`+`experience-review` برای pre-approve ابزار · (۳) verdict حذف `system-dashboard` از جدول ratified یا پذیرش بازگشتش.

## جلسه دوازدهم 2026-07-05 (Cowork) — دکتر تکاملی: verdict §۹ + پرامپت لایهٔ شناخت (صفر اجرا)

دنبالهٔ سند اهداف دکتر تکاملی؛ طبق دستور آری همچنان **فقط پرامپت، هیچ اجرایی نه**.

- **۴ تصمیم §۹ قفل شد (verdict آری):** برازندگی = درآمد/خروجی پروژه‌ها + سادگی/سرعت workflow · استقلال = **L2 bounded-auto از ابتدا** (فعال‌سازی مشروط به Security Gate + `git init`؛ تا آن‌موقع عملاً L1) · دکمهٔ اضطراری = **سه‌سطحی** (Pause/Kill/Revert) · گام بعد = لایهٔ شناخت. سند: [[00 - Inbox/Prompt - اهداف دکتر مغز تکاملی (Evolutionary Doctor)|پرامپت اهداف دکتر]] (status → `partially-ratified`؛ ۳ تصمیم باز: مرز invariant↔mutable · بودجهٔ Fugu/سقف روزانه · ریتم حلقه).
- **پرامپت نو ساخته شد:** [[00 - Inbox/Prompt - لایه شناخت زمینه (Ground-Truth Perception Layer)|لایهٔ شناختِ زمینه]] — اسکنر قطعیِ فایل‌سیستم + زمان‌بند زنده → `SYSTEM-STATE` واحد (۹ بلوک شامل Task Reconciliation، Security/PII Flags، Gates، Fitness Proxies، Kill-Switch State، Delta). پیش‌نیاز ستون ۱؛ ۴ تصمیم باز در §۷ همان سند.
- **ترتیب مصوب ساخت:** Security Gate + git → لایهٔ شناخت → ستون ۱ → ستون ۲ → ستون ۳ (Fugu).
- **اعتبارسنجی:** هر دو validator اجرا شد؛ صفر خطا از فایل‌های این جلسه (خطاهای `07 - Knowledge/_audit` و ۱ لینک digest از قبل موجودند).
- **برای آری:** verdict سه تصمیم باز سند اهداف + ۴ تصمیم §۷ لایهٔ شناخت؛ و همچنان ⛔ گیت rotation بالاتر از همه‌چیز.

## جلسه یازدهم‌د 2026-07-05 (Cowork) — Project-F: verification + انطباق تحقیق بیرونی + ACQUISITION-ENGINE + اتصال vault

سه دستور آری روی [[03 - Projects/اونلی فنز/PROJECT|Project-F]]: راستی‌آزمایی → انطباق ۸ فایل AI بیرونی → بهینه‌سازی جذب مشتری. سپس «چک اتصال مغز دوم» → vault root وسط همین جلسه mount شد (تا قبلش فقط پوشه پروژه در دسترس بود).

- **Verification sprint (Prompt 3) اجرا شد:** [[03 - Projects/اونلی فنز/research-results/12-prelaunch-verification-2026-07-05|12-prelaunch-verification]] — همه اعداد Day-Zero معتبر؛ OF $10 همچنان [SPEC]؛ X ACC جعلی (fetch رسمی)؛ برند Anar Soles صفر collision؛ ⚠️ سیگنال quarantine ‏r/VerifiedFeet.
- **تحقیق بیرونی ingest شد:** [[03 - Projects/اونلی فنز/research-results/13-external-ai-research-integration-2026-07-05|13-external-integration]] + پوشه `external-research-2026-07-05/`؛ 🚨 تعارض با ۲ قاعده قفل‌شده («Persian/Sydney» در کپی عمومی — Playbook خودی هم آلوده) → verdict آری pending؛ نردبان قیمت حالا ۳ نسخه.
- **سند کانونی جذب ساخته شد:** [[03 - Projects/اونلی فنز/ACQUISITION-ENGINE-2026-07-05|ACQUISITION-ENGINE]] — قیف ۵لایه نیمه‌خودکار ToS-safe، هزینه sprint ~A$75–105، kill criteria=G1/G2.
- **Patch بلوپرینت §۱۱ روی PROJECT.md اعمال شد؛** OpenQuestions بازنویسی (۱۳ باز، ۶ بسته)؛ سنتز حافظه به `_memory/onlyfans-project-memory-2026-07-05.md` (ریشه vault) هم کپی شد.
- **برای آری — به ترتیب:** (۱) ⛔ ردیف‌های CRITICAL ‏[[ROTATION_CHECKLIST]] از 07-03 هنوز OPEN (کیف Monero + کلیدهای exchange افشاشده) — بالاتر از همه‌چیز؛ (۲) GATE 0 (اقامت پارتنر) — یک خط جواب؛ (۳) verdict سؤال ۹ (Persian/Sydney) قبل از هر bio/کپشن.
- فایل‌های غیر-Project-F آپلودی در `03 - Projects/اونلی فنز/_inbox-other-projects/` (Ziman DM Bot · self-improvement map) — مقصد نهایی = تصمیم آری. نوت: نوشتن‌های این جلسه همه با دستور مستقیم آری بود (L0 تعاملی)؛ Security Gate برای autonomy همچنان بسته.

## جلسه یازدهم‌ج 2026-07-05 (Cowork) — منشور استقلال **ratified + اجرا** و restore ناوگان پس از reset دوم

دو دستور آری: «مغز مستقل‌تر» → [[00 - Inbox/Prompt - منشور استقلال مغز (Autonomy Ladder)|منشور استقلال مغز v1]] · سپس «اجرا کن پرامپت‌های خودتو» = **verdict آری → ratified، AUTONOMY: on، گام‌های §۸ اجرا شد.**

- **منشور:** نردبان L0–L3 · لیست سفید bounded-auto · HEARTBEAT دوطرفه · گزارش فقط-استثنا · شاخص استقلال · halt. + سه تکمیل: kill switch مالک (§۱۰) · سقف روزانهٔ L2=۳ · بلوک تزریق §۹. Risk-Governance کامل (cap · kill switch · audit=[[_memory/EXPERIENCE-LEDGER|ledger]]).
- **کشف حین اجرا — reset دوم همان روز:** زمان‌بند دوباره ۰ تسک بود (session قطع‌شده) → **حفرهٔ bootstrap**: وقتی کل ناوگان هم‌زمان می‌میرد، تسکی برای خودترمیمی نمی‌ماند و متن پرامپت‌ها هم می‌میرد. دو مهار: [[05 - Agents/RATIFIED-TASKS|RATIFIED-TASKS]] (متن کامل پرامپت‌ها داخل vault، تک‌منبع بازسازی) + چک شروعِ جلسه (پایین ↓). ledger: دو ردیف نو (regress + tune).
- **اجرا شد:** جدول ratified در [[05 - Agents/AGENT_REGISTRY|رجیستری]] (فقط ۶؛ اسکات‌های تاریک عمداً بیرون — خودترمیمی برنمی‌گرداندشان) · `_memory/HEARTBEAT.md` (استثنای overwrite ثبت شد) · **هر ۶ تسک با بلوک autonomy-protocol v1 از نو ساخته شد** (cronهای قبلی؛ فقط experience-review با notification) — اولین اجرای زندهٔ §۳.۳، از لنگر تعاملی.
- **برای آری:** یک‌بار «Run now» روی تسک‌ها (به‌خصوص brain-focus-board و experience-review) تا ابزارها pre-approve شوند؛ اجراهای نزدیک (ظهر امروز): pulse ~۱۲:۰۹ · dashboard ~۱۲:۲۹ · focus-board ~۱۲:۵۵ · **review امشب ~۲۱:۳۵ (شاخص استقلال + pendingها را می‌آورد)** · consolidator ~۲۲:۰۲ · fleet ~۲۳:۰۱. تست پذیرش §۸.۶ (حذف عمدی یک تسک) معوق تا ۲ beat موفق.

## جلسه یازدهم‌ب 2026-07-05 (Cowork، بامداد) — ناوگان تاریک + تک‌منبع سرکوب (verdict آری)

verdict آری روی سؤال باز: «self-improve live prompt · self run» → اعمال شد.

- **کشف CRITICAL:** زمان‌بندِ زنده صفر تسک داشت درحالی‌که [[05 - Agents/AGENT_REGISTRY|رجیستری]] ۳۲ ادعا می‌کرد؛ آخرین دیجست خودکار 2026-07-04 21:29 (سکوت ~۲۴س)؛ مانیفست آرتیفکت هم خالی — reset state جلسه. قاعدهٔ نو در [[_memory/EXPERIENCE-LEDGER|ledger]]: منبع حقیقت fleet = خروجی زندهٔ زمان‌بند، نه markdown.
- **re-arm دو تسک هسته با پرامپت بهبودیافته:** `brain-focus-board` (`50 */3 * * *`، بی‌صدا) — پرامپت نو: تک‌منبع سرکوب (مصرف مستقیم raw/effective/suppressed/needs_source_verify از دکتر)، قاعدهٔ fresh-inode، fleet از زمان‌بند زنده · `experience-review` (`30 21 * * 0`، notification) — امشب ۲۱:۳۵ اجرا می‌شود و pending «re-arm بقیهٔ ناوگان» را برای verdict می‌آورد.
- **تابلو v10 (hash `434cd36c…`):** سرکوب محلی تابلو حذف شد؛ دکتر از inode تازه: raw=۶۶ → effective=۹۳ (۲ utf8 + ۶ index-drift دیشب بعد از remount خودشان محو شدند — تأیید تجربی کلاس stale-view؛ utf8-suspect باقی‌مانده هم ویندوز-verify تمیز بود). آرتیفکت نو `brain-focus-board-v2`. validatorها سبز (۱۶۴/۰ · ۴۱۶/۰).
- **verdict تکمیلی («هستهٔ کم‌مصرف»):** ۴ تسک زیرساختی هم re-arm شد — `brain-pulse` (`0 */3`) · `system-dashboard` (`20 */6`؛ پرامپت تسک، تک‌منبع سرکوب را بر متن کهنهٔ قرارداد حاکم می‌کند) · `mycelial-consolidator` (`0 22` بازگشتی؛ بدون دیجست نو = خروج بی‌صدا) · `fleet-selection` (`0 23 * * 0`) → **۶ تسک زنده**. ۱۹ اسکات + ۶ لاین selfimprove عمداً تاریک (سنجش جدای اثر چرخه + پلن).
- **باز:** نوت پرامپت [[00 - Inbox/Prompt - System Dashboard Artifact|تابلوی سیستم]] هنوز سرکوب موازی توصیف می‌کند (اصلاح متن canonical = verdict آری) · اجرای اولِ تسک‌ها را تماشا کن تا ابزارها pre-approve شوند (اولین: brain-focus-board همین ساعت).

## جلسه یازدهم 2026-07-05 (Cowork، بامداد) — چرخهٔ بستهٔ خودبهبودی (دستور آری)

خواستهٔ آری: «consistent circle of self improvement» → «yes go for it». مشکل: درس‌ها در سه جای جدا (لاگ HTML تابلو · حلقهٔ بهبود پرامپت · دیجست‌های ناوگان) بدون بازگشت به هم.

- **[[_memory/EXPERIENCE-LEDGER|EXPERIENCE-LEDGER]] ساخته شد:** حافظهٔ canonical و append-only چرخه؛ بذر ۱۰ درس → اکنون **۱۳ ردیف (۱۲ applied · ۱ info · ۰ pending)**. verdict باز (whitelist دکتر) همین جلسه accept و پیاده شد ↓.
- **بازوها:** انباشت خودکار — پرامپت تسک `brain-focus-board` (هر ۳ ساعت) حالا ledger را می‌خواند/append می‌کند · verdict — تسک نو `experience-review` (یکشنبه ۲۱:۳۰، با notification) · اعمال — فقط تعاملی · سنجش — بخش «🔁» تابلو (v8) با قاعدهٔ تفکیک اثر چرخه از گیت انسانی rotation.
- **تابلو v8→v9 (hash `f367687f…`)، vault و آرتیفکت یکسان:** بخش «🔁 چرخهٔ خودبهبودی» + fleet=۳۲. گارد فاز ۵ حین ساخت v8 یک واژهٔ هم‌الگو در متن diff گرفت → نویسه‌گردانی (قاعدهٔ ledger ردیف ۳ دوباره تأیید شد — گارد زنده است).
- **رجیستری ۳۰→۳۲:** دو تسک چرخه هم‌زمان با ساختشان ثبت شدند؛ قاعدهٔ نو در چرخه: «هر تسک زمان‌بندی نو = ثبت هم‌زمان در AGENT_REGISTRY» (ضد تکرار درس v5/v7).
- **verdict دکتر حل شد (این جلسه، دستور آری «Option B»):** `04 - Architect System/scripts/dashboard_doctor.py` بازطراحی → دو نمره `raw_score`/`effective_score`؛ لایهٔ `SUPPRESS_RULES` (by-design، با `ledger_ref`) + `VERIFY_RULES` (utf8/index-drift → `needs_source_verify`، خارج از گیت CRITICAL). detection خام دست‌نخورده، هیچ سیگنالی پنهان نشد. اجرای زنده: **raw=۲۳ → effective=۸۶** (۸ verify · ۱ suppress · ۲ واقعی). تصمیم: heuristic بایتی رد شد (DecisionLog وسط‌فایل بود) → verify-at-source. جزئیات: [[_memory/EXPERIENCE-LEDGER|ledger]] ردیف‌های ۳۳ و ۱۱–۱۳.
- **درسِ حین‌کار (regress، ثبت‌شده):** stale-view روی خودِ اسکریپتِ تازه‌ویرایش‌شده هم زد (مِنت سندباکس نمای ناسازگار/بریده، size منجمد) → قاعده: فایلِ همین‌جا-Windows-ویرایش‌شده را از همان مِنت اجرا نکن؛ inode تازه یا Windows-side. تعمیمِ row-27 — چرخه باز روی خودش کار کرد.
- **برای آری (۲ دقیقه):** یک‌بار «Run now» روی `brain-focus-board` و `experience-review` برای پیش‌تأیید ابزارها. (verdict دکتر دیگر باز نیست.)

> در پایان هر جلسه ایجنت **بازنویسی** می‌شود (تنها نوتی که overwrite مجاز است). فقط wikilink — نه کپی محتوا، نه secret.

## جلسه بعد باید:

- **گام صفر — boot interview:** طبق [[04 - Architect System/learning-engine/STARTUP-PROTOCOL|STARTUP-PROTOCOL]] اطلاعات حیاتی باز/کهنه را از آری بگیر (حداکثر ۴ سوال، skip-logic از [[04 - Architect System/learning-engine/STARTUP-CHECKLIST.yaml|STARTUP-CHECKLIST]])، جواب‌ها را در LEARNING-STATE + ledger بنویس، سطح جلسه را اعلام کن.
- اول [[_PROJECT_INSTRUCTIONS|قانون اساسی v2.0]] را بخوان و طبق پروتکل جلسه در `CLAUDE.md` کار کن.
- **bootstrap-watchdog (منشور §۵، درس reset دوم):** همان اول، فهرست زندهٔ زمان‌بند را با جدول ratified در [[05 - Agents/AGENT_REGISTRY|رجیستری]] تطبیق بده؛ تسک ratified غایب → از [[05 - Agents/RATIFIED-TASKS|RATIFIED-TASKS]] بازبساز (L2، ثبت در ledger) و `_memory/HEARTBEAT.md` را چک کن.
- **🟢 گیت rotation: LIFTED 2026-07-06 (verdict آری) — بسته و تمام‌شده؛ دوباره طرحش نکن.** تک‌منبع: §۲ [[04 - Architect System/architect/ARCHITECT_CHARTER|charter]]. ۱۴ ردیف HIGH/MEDIUM ‏[[ROTATION_CHECKLIST]] = backlog (مرور هفتگی experience-review).
- گام بعد از گیت: TOP-5 آدیت fusion ([[04 - Architect System/architect/04-Docs/fusion-audit/REFACTOR_PLAN|REFACTOR_PLAN]]) → [[00 - Inbox/Prompt - Phase 4 Real Integration|پرامپت Phase 4]].
- **فرانت‌متر/schema حالا تمیز است (جلسه ۷):** validator صفرخطا؛ کارِ باز فقط بک‌لاگ ساختاری در [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]] (کد/باینری، کهنگی PROJECT، لینک `[[INDEX]]`).
- **تابلو → منبع واحد سرکوب: برای تابلوی تمرکز انجام شد (جلسهٔ ۱۱ب، verdict آری — v10).** باقی‌مانده: نوت پرامپت [[00 - Inbox/Prompt - System Dashboard Artifact|تابلوی سیستم]] و تسک `system-dashboard` (فعلاً در زمان‌بند موجود نیست) هنوز لایهٔ سرکوب موازی توصیف می‌کنند — اصلاح با verdict آری.
- **قبل از هر اجرای BUILD-PROMPT حافظه:** اول [[_memory/REVIEW|REVIEW]] (بازبینی grounded، ۸ یافته) و [[_memory/PHASE-0A-EXCLUSION-SPEC|PHASE-0A-EXCLUSION-SPEC]] (منطق اصلاح‌شدهٔ ورود به ingest) خوانده شود؛ اسپک جایگزین بخش exclusion فعلی BUILD-PROMPT است و هنوز منتظر ratify آری.
- **بلوپرینت مغز زنده ratify شد (جلسه ۹)** — گام‌های ۲ و ۳ نقشهٔ راه اجرا شده؛ گام ۴ (memory-layer) همچنان پشت گیت rotation/gitleaks. verdict باز: Brain.md به‌عنوان دومین نوت overwrite-مجاز ([[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]]).

## جلسه دهم‌ب 2026-07-04 (Cowork) — تعمیر و v4 تابلوی تمرکز

خواستهٔ آری: «تعمیرات و بهبود» تابلو براساس پرامپت قرارداد ([[00 - Inbox/Prompt - System Dashboard Artifact|Prompt - System Dashboard Artifact]]). چرخهٔ کامل اسکن→مدل→hash-diff→رندر→گاردها اجرا شد؛ hash عوض شد (54928625… → 5a5a0c1f…) → بازرندر `01 - Dashboard/BRAIN-FOCUS-BOARD.html`.

- **دو تعمیر اسکن (در حلقهٔ بهبود پرامپت ثبت شد):** کیت فیوژن در `00_Knowledge_Base` چک می‌شود (۱/۴ → ۴/۴ واقعی) · آمار خام دایرکتوری‌ها حالا `.agentignore` را رعایت می‌کند (04: غیر-md ‏3132→8).
- **متریک‌ها (اجرای زندهٔ هر دو validator، سبز):** فرانت‌متر ۱۶۴/۰ خطا · لینک ۴۱۵/۰ شکسته · notes=۴۱۳ (تعریف یکسان: md خارج از محدودهٔ منفی، بدون `_code`) · Doctor خام ۴۸ / پس از سرکوب ۵۱ — یافته‌ها همان (۱ CRITICAL بایت خراب DecisionLog فیوژن).
- **تعمیرات UI:** جستجوی case-insensitive · برچسب کامل ۵ گام roadmap از [[_memory/LIVING-BRAIN-BLUEPRINT|بلوپرینت]] (قبلاً بریده) · نمایش امتیاز خام Doctor.
- **پابرجا:** گیت rotation (۴ CRITICAL) · هر دو گارد فاز ۵ سبز · قاعدهٔ Project-F برقرار.
- **ادامهٔ جلسه (v5، دو verdict آری):** حالت اجرا = **دستی** («تابلو را اجرا کن» → چرخهٔ کامل + سینک آرتیفکت؛ تسک زمان‌بندی ساخته نشد) · **ناهم‌خوانی رجیستری بسته شد:** brain-pulse (`0 */3 * * *`) و system-dashboard (`20 */6 * * *`، cron تأیید زنده) به [[05 - Agents/AGENT_REGISTRY|رجیستری]] افزوده شد → ۲۴ تسک. تابلو v5 (hash `7e9555dd…`) در vault و آرتیفکت Cowork یکسان.
- **FP نو ثبت‌شده در تابلو:** `utf8-corrupt` روی AGENT_REGISTRY بعد از ویرایش ویندوزی = stale-view سندباکس (دُم‌بریده، mtime منجمد)؛ تأیید مستقیم ویندوزی: فایل سالم. الگوی `utf8-corrupt-after-windows-edit` به سرکوب تابلو افزوده شد — اگر در اجرای زمان‌بندی system-dashboard هم دیده شد، اول از ویندوز verify شود.
- **v6 (اجرای دستی «run and improve»):** بهبود کارت‌ها — متن بلاکرهای باز از Open blockers هر PROJECT.md رندر می‌شود (Accounting ×۲ · brushline ×۱). stale-view رجیستری پس از ~۲۰ دقیقه پابرجا (observe ثبت شد). hash `6083e227…` — vault و آرتیفکت یکسان؛ گاردها سبز.
- **v7 («faster self improvement»، بامداد ۰۵):** regress شکار شد — v5 فقط رجیستری را می‌خواند و scale-up 10x ساعت ۱۹:۲۲ ([[00 - Inbox/2026-07-04 1922 Scale-up ناوگان خودبهبودی (aggressive 10x)|runbook]]) را ندیده بود. سه اقدام: (۱) [[05 - Agents/AGENT_REGISTRY|رجیستری]] با 10x سینک شد — ۶ لاین selfimprove + cron های `*/3` و `0 */3` → **۳۰ تسک**؛ (۲) تابلو v7 (hash `8cc035b3…`) با fleet=۳۰ و selfimprove_runs_day≈۱۰۰۸ و درسِ «منبع fleet = رجیستری + runbookهای Inbox»؛ (۳) تسک نو `brain-focus-board` هر ۳ ساعت دقیقهٔ ۵۰ (این scope؛ propose-only جز پارامترهای نمایشی؛ بی‌صدا) — توصیه به آری: یک‌بار «Run now» برای پیش‌تأیید ابزارها.

## جلسه دهم 2026-07-04 (Cowork) — تابلوی تمرکز مغزها (live artifact)

خواستهٔ آری: ساخت live artifact در Cowork از پرامپت «Brain Focus Board» + گسترش منابع داده (v2/v3).

- **خروجی:** `01 - Dashboard/BRAIN-FOCUS-BOARD.html` (مشتق، overwrite-مجاز) + آرتیفکت Cowork با شناسهٔ `brain-focus-board`. تازه‌سازی **دستی** (idempotent با model_hash)؛ HTML آپلودی قبلی دادهٔ نمونه بود و فقط بذر خودبهبودی از آن منتقل شد.
- **منابع live (v2/v3):** گیت‌ها از [[ROTATION_CHECKLIST]] (۴ CRITICAL باز) · ناوگان از [[05 - Agents/AGENT_REGISTRY|رجیستری]] + شمار دیجست‌های امروز · سیگنال هر مغز از [[01 - Dashboard/Brain|Brain]] · متریک‌ها از اجرای زندهٔ هر دو اسکریپت اعتبارسنجی (سبز: فرانت‌متر ۱۶۴ ✓ · لینک ۴۱۵، صفر شکسته) · roadmap از [[_memory/LIVING-BRAIN-BLUEPRINT|بلوپرینت]] · دادهٔ خام دایرکتوری‌ها از فایل‌سیستم.
- **Doctor (سلامت ۵۱):** ۱ CRITICAL همان بایت خراب UTF-8 در DecisionLog فیوژن (باز/ذخیره در Obsidian) + index-drift کریپتو **واقعی است** (INDEX آن فایل‌ها را ندارد — نه stale-view).
- **مشاهدهٔ ثبت‌شده:** ناهم‌خوانی شمار تسک — رجیستری ۲۲ ولی جلسهٔ ۹ج ۲۴ (brain-pulse و system-dashboard در رجیستری ثبت نشده‌اند) → رجیستری به‌روز شود.
- قاعدهٔ Project-F رعایت شد (فقط فاز/Track، بدون نام/مسیر/لینک). هر دو گارد فاز ۵ (secret-grep و صفر ارجاع خارجی) سبز.

## جلسه نهم‌ب 2026-07-04 (Cowork) — داشبورد زندهٔ کل سیستم

خواستهٔ آری: ارتیفکت کامل ماژول‌ها/قابلیت‌ها که با هر تغییر خودش را وفق دهد. سه verdict: کل سیستم · HTML تعاملی در vault · تسک زمان‌بندی.

- **پرامپت استاندارد:** [[00 - Inbox/Prompt - System Dashboard Artifact|Prompt - System Dashboard Artifact]] — چرخهٔ اسکن → مدل JSON → hash-diff (اگر تغییری نبود، هیچ نوشتنی) → رندر → گاردهای parse/secret. قاعدهٔ Project-F و محدودهٔ منفی داخل قرارداد.
- **خروجی:** `01 - Dashboard/SYSTEM-DASHBOARD.html` (v1 ساخته شد — هرم سه‌طبقه، کارت ۸ مغز با درصد کیت و فیلتر risk، نقشهٔ راه، متریک‌ها، مدل embedded). مشتق و overwrite-مجاز (owner-directed)؛ نوت canonical نیست.
- **تسک `system-dashboard`:** هر ۶ ساعت (دقیقهٔ ۲۰، ضد تصادم با brain-pulse) → **جمع ۲۴ تسک.** توصیه به آری: یک‌بار «Run now» برای پیش‌تأیید ابزارها.
- **ماژول Doctor اضافه شد (نهم‌ج):** اسکریپت سوم `04 - Architect System/scripts/dashboard_doctor.py` (چک‌های قطعی: کیت، index-drift، UTF-8، dup-basename، کهنگی، سلامت HTML/secret) + فاز ۶ در نوت پرامپت + بخش «🩺 Doctor» در داشبورد (v2، health=۶۶). زمان‌بندی propose-only؛ اعمال با verdict. **تکمیل‌شده با verdict آری:** ۹ index-drift (۷ کریپتو + ۲ ماینینگ). **یافتهٔ نو CRITICAL:** `فیوژن هیپنوتیزم/00_Knowledge_Base/DecisionLog.md` بایت خراب UTF-8 دارد (مثل architecture-blueprint اونلی) — یک‌بار در Obsidian باز/ذخیره شود. دو false-positive در حلقهٔ بهبود پرامپت ثبت شد (stale-view سندباکس · pointerهای MOVED).

## جلسه نهم 2026-07-04 (Cowork) — زنده‌سازی: ratify بلوپرینت + اعمال Tier A + کیت ۴فایلی

verdict مستقیم آری (هر ۴ مورد: بازبینی · ratify · Tier A · کیت). بازبینی grounded پیش از تصویب → ۴ یافته در بخش «ثبت تصویب» [[_memory/LIVING-BRAIN-BLUEPRINT|بلوپرینت]] (status: `active`؛ «accepted» در schema نیست).

- **Tier A اعمال شد:** ۳۹ لینک روی ۲۶ نوت منبع، طبق فاز ۵ [[_memory/LINK-DISCOVERY-PROMPT|پروتکل]] — بخش `## مرتبط` انتهای منبع، متن اصلی دست‌نخورده. نمونه‌گیری پیش‌اعمال (۵/~۴۰): همه شاهد متنی مستقیم؛ هیچ منبعی در کلاس قرنطینهٔ [[ROTATION_CHECKLIST]].
- **کیت مغز پروژه ساخته شد (۱۷ فایل):** INDEX ×۵ (Mining از قبل داشت) + DecisionLog ×۶ (`type: log`) + OpenQuestions ×۶ برای Accounting · Crypto · Lead-نقاشی · Mining · Ziman · اونلی فنز — همه seeded از PROJECT.md خودشان، با `project:` binding. Ziman: [[03 - Projects/Ziman Galerry/Strategy-DecisionLog|Strategy-DecisionLog]] به‌عنوان لاگ پیشین لینک شد (مکمل، نه تکراری — قاعدهٔ ۴).
- **Active Context هر ۶ PROJECT.md** با خط «کیت مغز پروژه» تازه شد + `updated: 2026-07-04`.
- **اعتبارسنجی:** هر دو اسکریپت بعد از هر دو دسته سبز — فرانت‌متر ۱۶۳ نوت ✓ · لینک ۴۱۴ نوت، صفر شکسته ✓ (اجرای سندباکس؛ اجرای تاییدی ویندوزی طبق سابقهٔ stale-view توصیه می‌شود).
- **commit نشد:** vault هنوز git repo نیست (تصمیم باز init با آری) — دستهٔ >۵ فایل بدون checkpoint ماند.
- **متریک گام ۵ (پایهٔ امروز):** رفع ناسازگاری متریک در ثبت تصویب: ≥۱ لینک hub برای هر خوشهٔ جزیره‌ای · ≥۳ لینک hub برای هر ۸ مغز پروژه. سنجش Δorphan واقعی بعد از ایندکس مجدد گراف.

## جلسه هشتم‌ب 2026-07-04 (Cowork) — کشف ارتباطات بین‌دایرکتوری + بلوپرینت مغز زنده

اسکن read-only کل vault (۳۸۵ نوت، خارج از محدودهٔ منفی): گراف wikilink + کشف unlinked-mention با نرمال‌سازی RTL. **هیچ نوتی ویرایش نشد — همه propose-only.**

- **خروجی‌ها (هر سه در `_memory/`):** [[_memory/CONNECTIONS-MAP|CONNECTIONS-MAP]] (~۴۰ لینک Tier A آمادهٔ اعمال + Tier B/C؛ یافتهٔ ساختاری: لایهٔ معماری ۰۴/۰۵/۰۶ پروژه‌ها را می‌بیند ولی لینک نمی‌دهد) · [[_memory/LINK-DISCOVERY-PROMPT|LINK-DISCOVERY-PROMPT]] (چرخهٔ کشف→verdict→اعمال؛ جایگزین بهبودیافتهٔ Phase 4/5) · [[_memory/LIVING-BRAIN-BLUEPRINT|LIVING-BRAIN-BLUEPRINT]] (ساختار هرمی: مغز مرکزی قابل‌گفتگو + کیت ۴فایلی مغز مستقل هر پروژه + رگ‌های عرضی).
- **آمار:** orphan=۱۴۱ (بخش بزرگی خوشهٔ جزیره‌ای عمدی) · میانگین out-degree=۲.۳۶ · کاندیدا ۲۳۶۳→۱۷۴ بین‌دایرکتوریِ curated.
- **منتظر verdict آری:** اعمال Tier A · پذیرش کیت ۴فایلی برای ۶ پروژه · ترتیب زنده‌سازی (اول rotation/gitleaks، بعد memory-layer). → **هر سه در جلسهٔ نهم حل شد.**

## جلسه هشتم 2026-07-04 (Cowork) — بازبینی BUILD-PROMPT لایهٔ حافظه

بازبینی فقط‌خواندنی و grounded روی `_memory/BUILD-PROMPT.md` + `_memory/00_recon_report.md` + `_memory/EXCLUDED.md`؛ ادعاهای کلیدی مقابل vault زنده چک شد (گیت rotation، اسکریپت‌ها، نبود `_Archive`، شمار نوت‌ها — همه تایید).

- **خروجی:** [[_memory/REVIEW|REVIEW]] (verdict + جدول verify + ۸ یافته با شدت) و [[_memory/PHASE-0A-EXCLUSION-SPEC|PHASE-0A-EXCLUSION-SPEC]] (drop-in: allowlist-by-scan به‌جای denylist-glob + قرنطینهٔ بی‌قیدوشرط هر `.md` نام‌برده در [[ROTATION_CHECKLIST]] تا ROTATED شدن ردیفش + توقف کامل وقتی gitleaks در دسترس نیست + تست‌های پذیرش).
- **یافته‌های CRITICAL:** اسکن secret فاز 0b فقط regex بود نه gitleaks → گیت تا اجرای gitleaks از ویندوز قابل اتکا نیست · فایل‌های md نام‌برده در checklist (قابل‌ingest) باید مستقل از نتیجهٔ اسکن قرنطینه شوند.
- **HIGH:** شکنندگی glob با نام‌های RTL (سابقهٔ باگ ترتیب واژهٔ فارسی) · گیت فقط DB حافظه را محافظت می‌کند نه ردیف‌های ۲۰–۲۳ بیرون از vault.
- **MEDIUM:** متر orphan خوشه‌های جزیره‌ایِ عمداً ایزوله را orphan می‌شمارد (باید per-subtree شود) · بدون audit دقت روی روابط استخراجی LLM · پیشنهاد FTS5-first قبل از لایهٔ وکتور.
- **نیازمند verdict آری:** پذیرش اسپک 0a اصلاح‌شده در BUILD-PROMPT، قبل از هر فاز ingest.

## جلسه هفتم 2026-07-04 (Cowork) — منسجم‌سازی کل vault

خواستهٔ آری «کل پوشهٔ backup را منسجم‌تر کن». آدیت موازیِ ۷-ایجنتی فقط‌خواندنی → ۹۴ یافته؛ اجرا با ۳ verdict آری (گسترش schema · تغییرنام نسخه‌های غیرریشه · بک‌لاگِ کد/باینری). **صفر حذف، همه افزایشی.**

- **گسترش [[06 - Architecture Maps/Property Schema|Property Schema]] (§۱ + §۲.۱ نو):** ۵ type نو (`architecture`/`design`/`proposal`/`runbook`/`tasks`) + status `superseded` + ۱۲ کلید رابطه/عملیاتی (`parent`/`aligns_to`/`extends`/`supersedes`/`superseded_by`/`canon_rank`/`depends-on`/`closes`/`target`/`audits`/`result`/`language`) — هماهنگ در `.obsidian/types.json` + `validate_frontmatter.py`. نرمال‌سازیِ تک‌مصرف‌ها: `index→moc` · `note→knowledge` · `master-prompt→prompt` · status `reference→active`/`draft-for-human-review→draft`.
- **فرانت‌متر ۴۵ → ۰ خطا** (۱۸ نوت: Ziman ×۶ · اونلی‌فنز ×۹ شامل ۴ فایلِ بی‌متادیتا · هیپنوتیزم ×۲ · Mining/Crypto).
- **رفع ابهام نام (verdict آری):** نسخهٔ هیپنوتیزمِ ROTATION → [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/ROTATION_CHECKLIST - هیپنوتیزم|ROTATION_CHECKLIST — هیپنوتیزم]] · architect HANDOFF (که در واقع سندِ «قلب و آگاهی» بود و فرانت‌متر نداشت) → [[04 - Architect System/architect/01-Project/HANDOFF - قلب و آگاهی|HANDOFF - قلب و آگاهی]] (+فرانت‌متر). لینک‌های ورودی اصلاح شد؛ حالا `[[ROTATION_CHECKLIST]]` و `[[HANDOFF]]` bare بی‌ابهام = نسخهٔ ریشه.
- **پسوند دوتایی:** `PROJECT_STRUCTURE.md.pdf→.pdf` (Accounting) · `MOVED - 05_راهنمای_API_keys.md.md→.md` (Lead/کاریابی). متن کهنهٔ دو ایندکس (۰۶ «فعلاً خالی» / ۰۷ لینک MAP) اصلاح شد.
- **بک‌لاگ (Q3=فقط ثبت):** جابه‌جایی کد لوز → `_code` · باینری Crypto → آرشیو بیرونی · کهنگی Ziman/اونلی PROJECT · لینک `[[INDEX]]` · تناقض epistemic_status · فیلد `project:` خودارجاع — همه در [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]].
- **گیت:** پوشهٔ backup در گیتِ خانه **untracked** است → commit نزدم (افزودنش کل درخت شامل باینری/الگوهای secret را stage می‌کرد). init کردنِ vault همچنان تصمیم بازِ آری.

## جلسه ششم 2026-07-04 (Cowork) — بازنگری/بهینه‌سازی ناوگان + گسترش

بازنگری انتقادی روی سیستم جلسه‌ٔ پنجم؛ ۴ گلوگاه رفع + ۲ اسکات نو (همه propose-only، فقط scout-digests).

- **بستن حلقهٔ طبیعت→معماری:** پرامپت [[05 - Agents/Research Scout Fleet|selfimprove]] حالا از `synthesis` + اسپورهای `mycelium` هم بک‌لاگ می‌گیرد → یافتهٔ زیستی به پیشنهاد معماری تبدیل می‌شود (همان «کپی طبیعت»).
- **Evaporation/TTL:** `consolidator` هر شب `status` دیجست‌های >۱۴ روز خودِ ناوگان را in-place به `archived` می‌برد (برگشت‌پذیر، نه حذف، فقط scout-digests) — پیاده‌سازی توصیهٔ stigmergy خودِ دیجست mycelium.
- **بهداشت نوتیف:** هر ۱۰ اسکات بی‌صدا؛ فقط `consolidator` شبانه نوتیف («synthesis آماده»).
- **۲ اسکات نو (پرکردن ساعات خالی بعدازظهر):** `ai-watch` (۱۴:۰۰ — قابلیت‌های نو AI، خوراک architect) · `security` (۱۶:۰۰ — opsec/چرخش secret/prompt-injection). fleet-eval یکشنبه اگر کم‌سیگنال بودند retire پیشنهاد می‌دهد (spawn-and-select).
- **حجم بالا (پلن Max 20x):** selfimprove → `*/15` (۹۶/روز)؛ + ۴ اسکات متنوع نو برای پرکردن روز: `markets` (۱۵) · `jobs` (۱۷) · `health` (۱۸) · `tools` (۱۹). منطق requisite variety (تنوع > کوبیدن یک حلقه).
- **متنوع‌تر (خواستهٔ آری):** ۵ اسکات شبانهٔ کاملاً متفاوت برای پرکردن شب + افزایش variety: `philosophy` (۲۰ — ریشهٔ «فلسفه»ی خواستهٔ اول) · `world` (۲۱) · `science` (۲۳) · `learning` (۲) · `local` سیدنی (۴).
- **جمع اکنون: ۲۲ تسک.** ۱۹ اسکات روزانه (پوشش ~۲۴ساعته ۶:۰۰–۰۴:۰۰) + selfimprove هر۱۵دقیقه + consolidator ۲۲ + fleet-selection یکشنبه. اسکات‌های شب در دور بعدی consolidator سنتز می‌شوند (lag ~۱ روز). fleet-eval یکشنبه کم‌سیگنال‌ها را retire پیشنهاد می‌دهد.
- **سقف واقعی = پنجرهٔ نرخ پلن** (مشترک با استفادهٔ تعاملی آری). فراتر از سقف: دورها صف→اجرا، خراب نمی‌شوند. اگر تعاملی خفه شد، دایال: selfimprove به `*/30` یا `0 * * * *`.

## جلسه هفتم‌ب 2026-07-04 (Cowork) — لایهٔ اتصال + مغز زنده

- **لایهٔ اتصال کامل شد (خواستهٔ «ارتباطات بینشون»):** [[00 - Inbox/scout-digests/_Mycorrhizal Map|نقشهٔ مایکوریزایی]] = حافظهٔ اتصالِ ماندگار (ماتریس تغذیهٔ ۱۹ اسکات × پروژه + لجر انباشتیِ ۵ الگو). قرارداد خروجی: هر دیجست خطِ **Cross-domain اجباری** دارد. `consolidator` هر شب نقشه را می‌خواند و اتصال نوِ پایدار را append می‌کند (dedup)؛ فایل‌های `_`-دار از evaporation معاف. برخلاف synthesisِ روزانه، اتصالات اینجا **انباشته** می‌شوند نه تبخیر.
- **مغز زنده (خواستهٔ «مغز زنده با همه پروژه‌ها»):** [[01 - Dashboard/Brain|Brain.md]] = نمای یک‌نگاهیِ زندهٔ کل سیستم (نبض ناوگان + وضعیت زندهٔ هر ۸ پروژه + الگوها + تصمیم‌های باز). تسک `brain-pulse` هر ۳ ساعت از روی Active Contextها + آخرین synthesis بازنویسی‌اش می‌کند (فقط لینک/state، نه secret). لینک از [[01 - Dashboard/Home|Home]]. عملاً پرامپت «اتصال همه پروژه‌ها به مغز کنترل» را محقق کرد.
- **نیازمند ratify آری:** Brain.md دومین نوتِ overwrite-مجاز است (تا حالا فقط HANDOFF) — به‌عنوان استثنای owner-directed عمل می‌کند؛ پیشنهاد اصلاح §۸ در [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]].
- **جمع اکنون: ۲۳ تسک** (۱۹ اسکات + selfimprove + consolidator + fleet-selection + brain-pulse).

## جلسه پنجم 2026-07-04 (Cowork) — Research Scout Fleet + حلقهٔ خودبهبودی

استثنای صریح گیت از آری: ناوگان اسکات زمان‌بندی با autonomy **propose-only، نوشتن فقط در `00 - Inbox/scout-digests/`**. هیچ secret/`_code`/نوت canonical لمس نشد. اجرا روی اشتراک Max آری (نه D-25).

- **طراحی زیست‌الگو:** [[05 - Agents/Mycelium Scout|Mycelium Scout]] (نگاشت میسیلیوم/قارچ/جنگل/بقا → معماری AGI چندایجنتی حافظه‌محور) + پروتکل مشترک [[05 - Agents/Research Scout Fleet|Research Scout Fleet]].
- **۸ اسکات پروژه‌ای روزانه (staggered، سیدنی):** crypto 06 · mycelium 07 · mining 08 · lead 09 · ziman 10 · accounting 11 · hypnosis 12 · projectf 13. هرکدام: PROJECT.md خودش را می‌خواند، از اسکیل `deep-research` سؤال روز را می‌زند، dedup می‌کند، دیجست تاریخ‌دار در scout-digests می‌گذارد. **اجرای اول: فردا صبح ۵-۰۷.**
- **حلقهٔ خودبهبودی — هر ۳۰ دقیقه** ([[05 - Agents/Research Scout Fleet|selfimprove]]): طبق دستور آری «۷۵٪ به خودبهبودی» و سپس «تندتر» — `architect-selfimprove` **هر ۳۰ دقیقه (۴۸/روز)** بک‌لاگ architect (REFACTOR_PLAN/Open Questions/Adversarial v3/Blueprint) را تحقیق و **پیشنهاد** می‌دهد؛ adaptive + propose-only. نسبت ≈ ۴۸⁄۵۷ ≈ **~۸۵٪**. دایال: `*/15` تندتر · `0 * * * *` ساعتی. سقف واقعی = نرخ پلن.
- **ثبت:** [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]] (بخش fleet + ردیف selfimprove) · [[05 - Agents/_Index - Agents|ایندکس Agents]] (active شد) · استیجینگ [[00 - Inbox/scout-digests/_README - Scout Digests|scout-digests]].
- **لایهٔ ارکستراسیون (بستن حلقه):** `mycelial-consolidator` شبانه (`0 22 * * *`) دیجست‌های روز را سنتز و الگوهای بین‌پروژه‌ای + promote/prune پیشنهاد می‌دهد → `synthesis.md` (خواندنی‌ترین، «مرتب‌کردنِ همه»). `fleet-selection` یکشنبه‌شب (`0 23 * * 0`) کیفیت ناوگان را ارزیابی و retire/spawn پیشنهاد می‌دهد → `fleet-eval.md`. هر دو propose-only.
- **جمع: ۱۱ تسک زمان‌بندی.** ۸ اسکات روزانه + selfimprove هر ۳۰دقیقه + consolidator شبانه + fleet-selection هفتگی.
- **دور اولِ زنده اجرا شد (دستور آری «تا یک ساعت»):** ۹ ایجنت موازی → ۹ دیجست منبع‌دار در [[00 - Inbox/scout-digests/_README - Scout Digests|scout-digests]] (`2026-07-04 <slug>.md`) + [[00 - Inbox/scout-digests/2026-07-04 synthesis|synthesis]] (الگوهای بین‌پروژه‌ای). اعتبارسنجی: **۳۵۵ نوت، صفر لینک شکسته؛ صفر خطای فرانت‌متر جدید.** یافته‌های شاخص: Crypto stack زیر AU$30 (~$0.01/ماه) · Mining VerusHash ~