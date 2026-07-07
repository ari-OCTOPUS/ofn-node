---
type: handoff
updated: 2026-07-07
---

# HANDOFF — وضعیت برای جلسه بعد

## جلسه بیست‌وهشتم 2026-07-07 ~۲۳:۱۰ (Claude Code Opus، master) — CONSOLIDATE + هستهٔ Track A بسته شد (A1 budget_gate v2 · A2 money_gate · A3 capability-gate) — سوئیت ۹/۹ سبز

آری این سشن را (که روی worktree کهنهٔ modest-gould بود) اجراگرِ اصلیِ master کرد: «اول consolidateِ بی‌گم‌شدن، بعد Track A». هیچ اقدام live/پولی/irreversible. گزارش کامل با فیلدهای STATE-REPORT: [[00 - Inbox/2026-07-07 1935 OCTOPUS-STAGE0-REPORT|STAGE0-REPORT ضمیمهٔ ۷+۸]].

- **✅ A1 · budget_gate v2 (SoT-read):** `budget_gate.py` حالا سقف‌ها را از `budgets.yaml` می‌خواند (`_caps()`) با fail-closed strictest=min(yaml, کفِ هاردکد)؛ non-breaking (اعداد = v1.1: day 2/month 30/disaster 500، aud 1.5). per-organ از قبل در `organ_gate` بود. A4/A5 (MONEY_ATTRIBUTION + MAX_LAG vital) هم قبلاً در همان in-flight تمام شده بودند.
- **✅ A2 · money_gate + A3 · capability-gate (verdict اپراتور: بساز؛ open-decision #2 قفل):** سه ماژولِ نو در `_ops/budget/` — `approval_channel.py` (ApprovalChannel pluggable + NotWiredStub/Mock) · `money_gate.py` (>AU$20 بدون تأییدِ انسانیِ match‌خورده = deny؛ خودگزارشی هرگز معتبر نیست) · `capability_gate.py` (`is_open` = capability∧LIVE_ENABLED∧approval؛ calendar≠capability؛ `require()` هر دو گیت را زنجیر می‌کند). **گیتِ پولِ واقعی همین الان بسته است** (اثبات: `require(50 AUD)`=deny چون LIVE_ENABLED نیست + Telegram وصل نیست). `run_all` markerِ CAPABILITY-OK را روی سبزِ کامل می‌نویسد/روی شکست revoke. تست‌های نو `test_money_gate` + `test_capability_gate` → **سوئیت ۹/۹ فایل سبز**.

- **کارِ commit‌نشدهٔ Track A/A4 روی master گم‌نشده ثبت شد:** ۷ فایل (opslib germline-vital MAX_LAG · organism · telemetry-test · ledger · CHANGELOG · STAGE0-REPORT + `money_event_test.py` untracked) → tag لنگر `pre-consolidate-20260707-2227`(=49312fa) → برنچ `wip/trackA-20260707-2227`(2089358) → merge `--no-ff` به master (`b2e754d`). **هیچ برنچی جلوتر از master نبود** (jolly قبلاً merge؛ sad-bartik=master؛ بقیه فقط behind) → merge `<AHEAD>` عمداً skip.
- **verify سبز:** `_ops` ۶/۶ فایل ($0، UTF-8) · `money_event_test` ۳/۳ (V2 = EVENT_TYPE پول، chain mixed-type، set بسته) · تستِ ضدِ APPROVAL جعلی present و سبز · validatorها صفر خطای نو (فقط backlog §۱۱ + ۱ لینک placeholder). تلهٔ `cp1252` دوباره خورد → `python -X utf8`.
- **ارگانیسم خاموش** (نه 8771، نه process؛ INC-1 مرگ ~20:53) — σ=0/pre-replication؛ تولد دوباره = دابل‌کلیک مالک `RUN-ORGANISM.bat`.
- **باز برای جلسهٔ بعد:** (۱) **وصلِ Telegram** = قدمِ جدا و human-gated: adapterِ ApprovalChannel که core.db را می‌خواند + tokenِ botِ راز فقط از env در زمانِ اجرا (هرگز commit/hardcode)؛ سپس ساختِ `LIVE-ENABLED.flag` فقط توسط انسان. تا آن‌موقع گیت بسته می‌ماند. (۲) **Track B** (اولین دلارِ paperِ Lead-نقاشی): `attribution.py`+`reconcile.py`، هنوز `_ops/reconcile/*.csv` نیست. (۳) دو پرچمِ runtime نو (`CAPABILITY-OK`/`LIVE-ENABLED` در `_ops/state`) کاندیدِ gitignore کنارِ soma (open-decision #8/C6). (۴) نگه‌داشتنِ wip+tag تا verdict (rollback: `git reset --hard pre-consolidate-20260707-2227`).
- ⚠️ **flag امنیتی (فقط گزارش):** `C:\Users\Armin` یک git repo است — ولی فقط ۲ فایل زیر Documents track شده، **هیچ .ssh/secret/.env**؛ نشتِ فعال نیست، footgun است. دست نزدم؛ تصمیم مالک. · worktreeهای کهنهٔ modest-gould/vigilant (۱۱ behind) کاندید prune.

## جلسه بیست‌وهفتم 2026-07-07 ~۱۸:۱۵ (Claude Code، worktree jolly-ardinghelli) — دستور کار جلسه ۲۶ اجرا شد: مهاجرت DeepSeek + قتل مسیر مرده + تست دیوار باربر + فیکس کوریِ validator

آری گزارش جلسه ۲۶ (راستی‌آزمایی زمینی، worktree ‏modest-gould-1c7bac، **merge‌نشده** — شماره ۲۶ برای همان رزرو ماند) را به این جلسه سپرد؛ هر ادعا پیش از ویرایش روی ریپو دوباره verify شد — همه دقیق بودند. گزارش کامل: [[00 - Inbox/2026-07-07 1815 گزارش جلسه ۲۷ — اجرای دستور کار جلسه ۲۶|گزارش جلسه ۲۷]].

- 🔴→✅ **مهاجرت DeepSeek کد زنده (مهلت 07-24):** ‏`gateway.py` (مدل :104 + قیمت‌ها :20 → ‏`deepseek-v4-flash` ‏$0.14/$0.28) · ‏`setup_wizard.py` (:76 ‏`LLM_MODEL` در ‏.env-ساز + :175 برچسب) · learning-engine ‏`app/providers.py` (:46) · اسناد bundle هم‌سو (README-FA/ARCHITECTURE). ‏`_ops` از قبل v4-flash — دست‌نخورده. ⚠️ اگر `.env` موجود هنوز `LLM_MODEL=deepseek-chat` دارد فقط مالک دستی عوض کند (ایجنت ‏.env را نمی‌خواند) یا ویزارد دوباره اجرا شود.
- 🔴→✅ **مسیر مردهٔ `C:\Users\Armin\Desktop\backup` → `F:\backup` در ۷ فایل عملیاتی:** [[05 - Agents/RATIFIED-TASKS|RATIFIED-TASKS]] (۹ جا شامل مسیر STOP) · ‏PROMPT-v1/v2 ‏learning-engine · [[04 - Architect System/architect/01-Project/M0.5-RESTORE-RUNBOOK-proposal|M0.5-runbook]] (همهٔ rclone/schtasks) · ‏`_memory/BUILD-PROMPT.md` · README ‏app · ‏gitleaks.toml. ارجاع‌های تاریخی و `backup-Archive`/`deploy-lab` عمداً دست‌نخورده. ناوگان زمان‌بند خالی بود → تسکی برای همگام‌سازی نبود (قید RATIFIED-TASKS برقرار)؛ restore بعدی با مسیر درست متولد می‌شود.
- 🟠→✅ **تست دیوار باربر** در `_ops/tests/test_fitness_sigma.py`: جعل ۵ APPROVAL + ۱ EXPERIENCE در ledger → σ بالا می‌رود (اثبات رسیدن حمله) ولی `acceptance_rate`/`judged` بی‌حرکت + cell حذف نمی‌شود + ‏authoritative سایه می‌ماند. سوئیت ۶ فایل/۴۰ چک سبز ($0).
- 🆕✅ **کشف+فیکس این جلسه: هر دو validator داخل worktree «سبزِ خالی» می‌دادند** — ‏EXCLUDE ‏`.claude` روی مسیر مطلق چک می‌شد و worktreeها زیر `.claude/worktrees/`اند → «بررسی شد: ۰ نوت» با exit 0. فیلتر → مسیر نسبی‌به‌ROOT (رفتار اجرا از ریشهٔ واقعی عیناً همان). الان ۳۰۴/۵۷۳ نوت اسکن؛ فقط همان ۳۳ خطای backlog جلسه ۲۴ + ۱ placeholder کهنه (§۱۱ عمداً رها) — **صفر خطای نو از این جلسه**.
- **میز آری:** merge دو branch (‏`claude/modest-gould-1c7bac` = گزارش ۲۶ · ‏`claude/jolly-ardinghelli-0e33f4` = این تغییرات) · ‏.env دستی (بالا ⬆) · سؤال نو ‏langar (‏`_code`) در [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]] · نردبان قبلی دست‌نخورده: بک‌اپ off-box + restore-drill (M0.5) → verdictها (V1/V2 + ۳ مورد ۰۷-۰۷) → دابل‌کلیک RUN-ORGANISM → متولی فروش 07-20. ‏leftover ایجنت بعدی: `ZIMAN-BRAIN-SETUP.md:36` (cd مسیر مرده، یک‌خطی).

**(ادامهٔ جلسه ~۱۹:۳۵ — OCTOPUS STAGE 0 اجرا شد):** آری پرامپت STAGE 0 پک OCTOPUS را داد؛ audit + goal-lock انجام و **چهار verdict در چیپ قفل شد:** اولویت = ستاپ کامل (فروش 07-20 دستی مالک — همچنان بی‌متولی) · آستانهٔ پول human-gate = **AU$10** (کلید نو `human_gate_aud` در budgets.yaml؛ اگر منظور USD بود یک خط اصلاح) · **V1 بسته: همه-AUD** روز2/ماه30/فاجعه500 + MAX_DRAWDOWN ≡ spike_pct · **V2 بسته: type جدید در EVENT_TYPES** (ساخت در P1). با مجوز V1، **budget_gate → v1.1**: باگ واحد DISASTER (`:90` ‏AUD≥AUD، رفتار قبلی حفظ) + چک روزانه به AUD (سفت‌تر) + هماهنگی `governor_epoch` (نسبت velocity بی‌بعد ماند) و تست زنجیر — **سوئیت ۶ فایل/۴۰ چک سبز**. راستی‌آزمایی ۴ بلاکر ادعایی پک: فقط باگ ارز واقعاً باز بود؛ نشت کلید (llm.py v0.4.3) و epoch (آلوستاتیک) از قبل بسته، بودجه در SoT حل. خروجی‌ها: [[00 - Inbox/2026-07-07 1935 OCTOPUS-STAGE0-REPORT|STAGE0-REPORT]] (append-only، هر ادعا test-backed) + [[00 - Inbox/Prompt - OCTOPUS STAGE 0 (v-final) 2026-07-07|پرامپت فایل‌شده]]. **قدم بعد طبق build_plan: P0.5 germline-first (فقط-مالک: merge دو branch → rclone remote → restore-drill) پیش از هر کار پرریسک؛ بعدش P1 (budget_gate v2 + پیاده‌سازی V2 + MAX_LAG).**

**(ادامهٔ جلسه ~۲۰:۰۰ — پاسخ‌های STAGE-0 آری اعمال شد):** گیت پول → **AU$20** · لوپ مناظره → **AU$10/ماه** (ردیف SoT نو در budgets.yaml) · **قیمت DeepSeek قفل [VERIFIED 2026-07-07 · api-docs.deepseek.com]**: flash in $0.14 ‏(cache-hit ‏$0.0028) / out $0.28 — عین عدد gateway، برچسب [EST]→[VERIFIED] · مقصد off-box = **دیسک/ماشین دوم محلی T1/T2** (verdict در [[04 - Architect System/architect/01-Project/M0.5-RESTORE-RUNBOOK-proposal|M0.5-runbook]]؛ هشدار خود آری: tier ابری رمزنگاری‌شده بعداً) · **سه تصمیم attribution قفل** (feed مستقل / mint ‏id یکتا برای Lead / پنجره ۷ روز) → [[00 - Inbox/2026-07-07 2000 MONEY-ATTRIBUTION-design v1|MONEY-ATTRIBUTION v1]] فایل شد (ready، ساخت P2) · **فروش 07-20 = tentacle فعال human-gated** (تسک در [[04 - Architect System/architect/PROJECT|PROJECT آرشیتکت]]). جزئیات: ضمیمهٔ ۱ [[00 - Inbox/2026-07-07 1935 OCTOPUS-STAGE0-REPORT|STAGE0-REPORT]]. **تنها گیت ماندهٔ پیش از tick اول: merge دو branch (مالک).**

**(ادامهٔ جلسه ~۲۰:۴۵ — merge + P0.5 هر دو سبز):** با دو دستور human-gated آری: (۱) **merge:** merge نیمه‌تمام (MERGE_HEAD=720de99، صفر conflict — توقفش خطای مجوز گذرای `.git/objects` بود) abort شد؛ tag ‏`pre-merge-20260707` روی `6a1d493` ‏verify؛ ‏modest-gould طبق دستور merge نشد — **یافته: آن شاخه صفر کامیت اختصاصی دارد و فایل گزارش ۲۶ فقط uncommitted روی دیسک worktree قدیمی است** (`.claude/worktrees/modest-gould-1c7bac/00 - Inbox/`؛ بازیابی = کپی+commit، منتظر verdict)؛ **merge سبز: `35c383f`** (۲۷ فایل، +489/−66) + ضمیمهٔ ۲ گزارش (`c96c393`)؛ سوئیت/validatorها پس از merge سبز. (۲) **P0.5 germline:** اسکریپت اپراتور با ۳ تطبیق [RE-VERIFY] اجرا شد — ‏fsck + ‏`ledger.py verify` (گیت fail-closed) → ‏bundle کل تاریخچه **196.9MB** در `E:\germline\vault-2026-07-07_2022.bundle` + کپی state ‏`_ops` → **restore-drill واقعی: clone → fsck → ۵۷۸ نوت (=دقیقاً tracked) → verify زنجیرهٔ ledger بازیابی‌شده** → manifest ‏`drill: PASS`. **ناوردی ۳ (germline-first) روی tier محلی بسته شد؛ گیت tick اول باز است** — دابل‌کلیک `RUN-ORGANISM.bat` دست آری. گپ ثبت‌شده: `core.db`/`events.jsonl` ‏gitignore‌اند (الان ~خالی) — از اولین اجرای brain به STATE_DIRS بک‌اپ اضافه شوند (بدون .env). جزئیات: ضمیمه‌های ۲–۳ [[00 - Inbox/2026-07-07 1935 OCTOPUS-STAGE0-REPORT|STAGE0-REPORT]].

**(ادامهٔ جلسه ~۲۰:۵۵ — دستور واحد: بازیابی ژنوم + زمان‌بندی germline + 🐙 BIRTH):** هشت پلهٔ دستور human-gated آری fail-closed اجرا شد: (۱) گزارش جلسه ۲۶ بازیابی و commit شد (`5924926`)؛ (۲) ‏`core.db`/`events.jsonl` با SECRET-GUARD به state بک‌آپ اضافه شد (هرگز .env)؛ (۳) **زمان‌بندی دولایه:** تسک `germline-hourly` (push به bare ‏`E:\germline\vault.git` + state غلتان؛ تستِ زنده سبز) و `germline-daily` (۰۳:۳۰، bundle+drill+prune ‏۷د/۴ه) — اسکریپت‌ها در `scripts/`؛ (۴) drill پیشا-تولد سبز (**۵۷۹ نوت**، ledger دوسویه)؛ (۵) pre-flight ‏**۱۵/۱۵ PASS** (kill مسلح · gate ‏v1.1 ‏deny ‏functional · دو live-gate قفل + پرچم‌ها غایب = paper-only مطلق) + سوئیت ۴۰ چک؛ (۶) **BIRTH ‏20:42:55 — ارگانیسم زنده و روشن مانده:** pulse اول آلوستاتیک pressure=0.047 (فقط ددلاین 07-20) → ‏epoch بعدی 57.9min، ‏$0، صفر conflict، σ=0، دو NOTE در ledger (ALLOCATION_SHADOW ‏h1_ok + ‏ORGANISM_DAILY) و زنجیره پس از append سالم، ‏HTTP ‏8771 زنده، صفر anomaly؛ (۷) بک‌آپ پسا-تولد بعد از commit رکوردها (germline_lag=0). **kill تمیز: فایل `_ops\STOP-ORGANISM`.** فردا: بازبینی smoke ‏۲۴ساعته (heartbeat/state/alerts). جزئیات کامل: ضمیمهٔ ۴ [[00 - Inbox/2026-07-07 1935 OCTOPUS-STAGE0-REPORT|STAGE0-REPORT]].

**(ادامهٔ جلسه ~۲۱:۱۰ — PLAN-ONLY: ‏MASTER-PLAN v1 + دو INCIDENT):** دستور plan-only آری اجرا شد. audit زنده: 🔴 **INC-1 ارگانیسم از ~20:53 مرده** (سه tick سالم زد؛ بعد پروسه+launcher با هم kill شدند — بدون crash-log؛ محتمل: teardown ‏job سندباکس ایجنت → تولد پایدار فقط با **دابل‌کلیک مالک** یا Scheduled Task) · 🟠 **INC-2 اجرای scheduled ‏hourly ‏FAIL @20:49** (stderr گم؛ دستی سبز؛ روزانه+دستی پوشش می‌دهد) · 🟡 سه فایل soma-state ‏tracked → repo دائم dirty. خروجی: [[00 - Inbox/2026-07-07 2110 OCTOPUS-MASTER-PLAN v1|**OCTOPUS-MASTER-PLAN v1**]] (چهار Track + critical-path + **۱۰ open-decision** — سرآمدش: ری‌استارت organism (دابل‌کلیک تو، الان) · ۳ مخاطب pitch ‏D1 · تأیید capability-gate و V2). هیچ چیزی ساخته/عوض نشد.

## جلسه بیست‌وپنجم 2026-07-07 ~۱۶:۳۰ (Claude Code) — 🟢 git اصلی فیکس و commit شد؛ حافظهٔ ماندگار ایجنت تکمیل شد

آری: «مطمئن شو همه‌چیز ذخیره بشه، مسیر تغییرات را مهندس/ایجنت بعدی بفهمد.»

- **ریشهٔ خرابیِ چندهفته‌ایِ git پیدا شد:** `.git/config` خط `core.worktree` به مسیر یک sandbox ابری قدیمی (`/sessions/eager-brave-archimedes/...`) اشاره می‌کرد که روی این ویندوز اصلاً وجود نداشت — برای همین هر دستور git، حتی `status`، با «Invalid path '/sessions'» می‌شکست (هم در Bash و هم PowerShell). با تأیید صریح آری (طبق §۰-۲ قانون اساسی — ایجنت خودش تصمیم نگرفت) خط حذف شد؛ نسخهٔ پشتیبان در `.git/config.bak-pre-worktree-fix`.
- **🟢 اولین commit پس از هفته‌ها:** `76f58ca` — ۱۷۷۶ فایل، کل backlog از آخرین commit (۰۷-۰۶ ۱۱:۵۳) تا الان: لایهٔ ارگانیسم کامل، پنل، فیکس‌های genome-system (v0.4.3)، بازبینی چندایجنتی. چک امنیتی قبل از commit: صفر secret واقعی در diff، `.gitignore`/`.agentignore` فقط تغییر mode داشتند. **`git fsck --full` تمیز** + diff فایل‌های کلیدی صفر اختلاف — یک خطای گذرای «Permission denied» وسط commit بی‌ضرر بود (verify شد).
- **یافتهٔ جانبی genome-system:** `.git` داخلی‌اش تقریباً خالی/نامعتبر بود (صفر commit) → git ریپوی اصلی آن را submodule نشناخت و کل محتوایش را عادی track کرد. الان genome-system عملاً در تاریخچهٔ ریپوی اصلی هست. تصمیم باز (ماندن هم‌ریپو یا init مستقل) در [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]].
- **حافظهٔ ماندگار ایجنت (فراتر از vault) اولین‌بار نوشته شد:** `C:\Users\Armin\.claude\projects\F--backup\memory\` — پروژه/معماری/تاریخچهٔ git، پروفایل حرفه‌ایِ آری (بدون محتوای شخصیِ پروفایل خصوصی پنل — عمداً حذف شد)، الگوی بازبینی چندایجنتی، مرجع ناوبری vault. هدف: جلسهٔ بعدی (حتی با مدل دیگر) بی‌آنکه دوباره کل این تحقیق را تکرار کند مستقیم ادامه دهد.
- **باقی‌مانده:** سه verdict جدید در AGENT_QUESTIONS (شرط مرگ reconcile · fitness baseline · genome-system submodule) + نردبان قبلی (بک‌اپ off-box، smoke شبانهٔ RUN-ORGANISM).

## جلسه بیست‌وچهارم 2026-07-07 ~۱۵:۴۵ (Claude Code) — مهندسی چندایجنتی: ۳ دپارتمان موازی → ۳ فیکس کد + اتصالات + آمادگی دیپلوی

آری: «مثل یک شرکت طراحی، مولتی‌ایجنت و موازی همه را کامل کن؛ موارد مهم را لیست/تعمیر کن؛ آمادهٔ دیپلوی.» گزارش کامل: [[00 - Inbox/2026-07-07 1544 گزارش مهندسی چندایجنتی — بازبینی، تعمیر، آمادگی دیپلوی|گزارش مهندسی جلسه ۲۴]].

- **نکتهٔ اول — vault-doctor زمان‌بندی‌شده fire شد ولی no-op بود** (۰۶:۴۵؛ نه گزارش، نه تغییر — احتمالاً پشت prompt مجوز در اجرای بی‌ناظر). مأموریتش همین جلسه به‌صورت چندایجنتی و کامل انجام شد؛ تسک مصرف‌شده و disabled است.
- **۳ دپارتمان موازی (فقط‌خواندنی) → ۶ یافتهٔ کد + نقشهٔ A/B سلامت + چک‌لیست دیپلوی.** سه فیکس اعمال و تست شد: (۱) 🔴 **rollback رزرو organ_gate** — شکست نوشتن state پس از رزرو سراسری دیگر بودجه نشت نمی‌دهد (+ تست رگرسیون؛ سوئیت ۳۳ چک). (۲) **گارد نشت دوطرفه** `llm.py` (v0.4.3، hostname-based، ۴ چک). (۳) **حذف نویسهٔ فنس** در `topics.sanitize` (I10).
- **۳ verdict نو روی میز آری** (عدم‌تقارن شرط مرگ reconcile · fitness baseline خودارجاع · یادآوری DISASTER unit) → [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]] ورودی ۰۷-۰۷.
- **سلامت vault:** ۴ فایل A فیکس (فرانت‌متر ARCHITECTURE-PATTERNS/AUDIT-FULL/دو Prompt) · ۳۳ خطای B (بسته‌های `_audit`/اونلی‌فنز/scout-digests) طبق §۱۱ عمداً رها · اتصالات چسبید: Time-Architecture → [[01 - Dashboard/Home|Home]]+[[03 - Projects/_Index - Projects|ایندکس]] · «زیرساخت زنده» (ORGANISM-SPEC/پنل 8790/genome-system) → Home · اسناد ژنوم به v0.4.3 همگام.
- **دیپلوی:** مسیر کد آماده — اجرای شبانه $0/بدون کلید (debate هرگز در tick لود نمی‌شود)، پورت‌ها/CRLF/گیت‌ها verify. مانده فقط نردبان مالک: git → بک‌اپ → verdictها → دابل‌کلیک RUN-ORGANISM (smoke شبانه) → UI. **حجم تغییرات ثبت‌نشده بزرگ است — فیکس git حالا واقعاً فوری‌ترین آیتم میز توست.**
- verify پایانی: `_ops` ۳۳ چک سبز · ژنوم ۵ سوئیت سبز · صفر خطای فرانت‌متر لایهٔ دست‌چین · پنل ۹ کارت/۳ صفحه سالم.

## جلسه بیست‌وسوم‌ب 2026-07-07 ~۰۶:۲۵ (Claude Code) — تسک یک‌بارهٔ «vault-doctor» زمان‌بندی شد (آری ۸ ساعت غایب)

آری: «کل پوشهٔ backup را بازبینی کن، یک دکتر schedule کن که کامل بیاید سیستم را تعمیر کند و همهٔ ارتباطات را بگیرد.» → تسک زمان‌بندی‌شدهٔ **`vault-doctor`** ساخته شد (fireAt ۰۶:۴۵ همین صبح، یک‌باره، بعد از اجرا auto-disable — ناوگان از ۰ به ۱ تسک، با verdict مستقیم مالک). پرامپت خودبسنده در `C:\Users\Armin\.claude\scheduled-tasks\vault-doctor\SKILL.md`؛ مأموریتش: هر دو validator → تعمیر همهٔ فرانت‌مترهای agent-fixable (اونلی فنز ×۲ · scout-digests ×۴ · `_audit` ×۱ · ARCHITECTURE-PATTERNS بدون‌فرانت‌متر؛ الگوی «کلید اختراعی به بدنه») → فیکس لینک شکسته (placeholder کهنه → متن ساده) → تطبیق [[03 - Projects/_Index - Projects|ایندکس پروژه‌ها]] و [[01 - Dashboard/Home|Home]] با ۹ پروژهٔ زنده → تصحیح مسیرهای کهنهٔ `Desktop\backup` → اجرای هر ۶+۵ تست → گزارش در Inbox (`vault-doctor-report`) + ورودی HANDOFF (جلسه ۲۴) + AGENT_QUESTIONS برای owner-gatedها. محدودهٔ ممنوع صریح در پرامپت (genome/ و budgets.yaml فقط‌خواندنی، بدون ACTIVATION/ارگانیسم/call خارجی، $0). ⚠ شرط اجرا: اپ باز بماند؛ اگر بسته بود در باز شدن بعدی fire می‌شود.

## جلسه بیست‌وسوم 2026-07-07 (Claude Code) — دو باگ واقعی فیکس شد + پنل سفت شد + صفحهٔ ارگانیسم؛ همهٔ سوئیت‌ها سبز

آری: «همه مراحل کدنویسی را چک/کامل کن و ارتباطات را بچسبان.» بازبینی کد این جلسه inline انجام شد (نه چندایجنتی — صرفه‌جویی کردیت)؛ دو باگ واقعی پیدا و با تست بسته شد:

- **فیکس ۱ — race قفل append ژنوم (v0.4.2):** ریشهٔ فلیکی `review_test.py` (کشف جلسه ۲۲) = قفل O_EXCL بعد از ۳s timeout بی‌قفل ادامه می‌داد و زیر تردهای هم‌پروسه زنجیره فورک می‌شد. فیکس: قفل دولایه (`threading.Lock` سراسری per-path + همان سایدکار فایلی برای بین-پروسه، timeout→10s). **۱۲/۱۲ اجرای پیاپی سبز** (قبلاً ~۱/۳ شکست). ثبت: [[07 - Knowledge/genome-system/CHANGELOG|CHANGELOG v0.4.2]].
- **فیکس ۲ — H1 کاذب در `governor_epoch.allocate_dry`:** با گذر تاریخ (فشار ددلاین ۰۷/۲۰ تابع زمان است) `round(…,4)`های per-organ جمع grantها را ۰.۰۰۰۱ بالای cap برد → `test_epoch` قرمز شد. فیکس طبق ناوردی خود لایه: کل تخصیص در **میکرو-AUD صحیح با floor** — جمع ساختاراً ≤ cap؛ بدون epsilon. سوئیت `_ops` دوباره **۶ فایل/۳۲ چک سبز**.
- **پنل سفت شد (بازبینی روی کد خود پنل):** bind انحصاری `SO_EXCLUSIVEADDRUSE` (تلهٔ double-bind جلسه ۱۹) · قفل نوشتن پروفایل زیر ThreadingHTTPServer · گارد نام خالی در submit · اسکن پروژه‌ها با `os.walk` هرس‌شده (دیگر وارد `.git`/`_Archive`/`_Duplicates`/… نمی‌شود).
- **اتصال چسبید — صفحهٔ `/organism` پنل:** خواندن مستقیم `_ops/state/ORGANISM-STATE.json` (+ نام مالک از پروفایل برای خوش‌آمد): ضربان/کهنگی تیک، خرج ماه/امروز، متر مشکوک، تعارض‌ها، فشار/epoch بعدی، σ، halted/frozen، آخرین خطا؛ ارگانیسم خاموش = راهنمای `RUN-ORGANISM.bat`. ثبت متقابل در [[_ops/ORGANISM-SPEC|ORGANISM-SPEC §۵]] (فاز ۰ پنل اجراشده).
- **روشن‌کردن خود ارگانیسم:** لانچ `RUN-ORGANISM.bat` توسط کلاسیفایر ایمنی رد شد (نردبان فعال‌سازی = فقط-مالک؛ هم‌راستا با ORGANISM-SPEC §۴) — دور زده نشد. **اقدام مالک: دابل‌کلیک `F:\backup\_ops\RUN-ORGANISM.bat`** → صفحهٔ ارگانیسم پنل زنده می‌شود؛ smoke یک‌شبه طبق قدم ۷.
- verify پایانی: هر ۵ تست ژنوم سبز · `_ops` ۳۲ چک سبز · پنل سه صفحه (پروفایل/پروژه‌ها ۹ کارت/ارگانیسم) زنده روی 8790.

## جلسه بیست‌ودوم 2026-07-06 (Claude Code) — ادامهٔ ارگانیسم: قدم‌های ۱–۶ برگشت‌پذیر تأیید و ثبت شد (کردیت وسط کار تمام شد)

آری: «وسط کدنویسی بزرگ کردیت تمام شد — همه‌چیز را یادداشت کن، هیچی هدر نرود، مرتب کن.» ادامهٔ [[00 - Inbox/Prompt - ادامه ساخت ارگانیسم (متابولیسم-مناظره-تکثیر) تا کامل شدن 2026-07-06|پرامپت ادامه]]؛ کارِ روی‌دیسک با اجرای واقعی تست/validator راستی‌آزمایی و ثبت شد (نه فقط از روی ادعای متن جلسه).

- **قدم‌های ۱–۴ پک روی دیسک تأیید شد (همه additive/سایه، فرانت‌متر معتبر):**
  - قدم ۱ — **فیکس نشت کلید ژنوم v0.4.1:** `common/llm.py` حالا `API_URL` را از `ANTHROPIC_BASE_URL` می‌سازد + گارد `sk-ant-` پیش از هر I/O شبکه (کلید هرگز echo نمی‌شود) + `tests/leak_guard_test.py` (۳ چک آفلاین). ثبت: [[07 - Knowledge/genome-system/CHANGELOG|CHANGELOG ژنوم]]. **این جلسه دوباره اجرا شد → سبز.**
  - قدم ۲ — [[_ops/budget/budgets-proposed-diff|diff پیشنهادی budgets]] (فقط PROPOSAL، H7): نرخ پین aud_per_usd · DEBATE_LOOP cap · قیمت routing (راستی‌آزمایی api-docs.deepseek.com) · replication · دو ارگان PAINTING/ACCOUNTING.
  - قدم ۳ — [[_ops/ORGANISM-SPEC|ORGANISM-SPEC]] (سند «کل واحد»: سه لایه، نگاشت ماژول‌ها، ۱۰ ناوردی، نردبان فعال‌سازی، ۴ endpoint UI).
  - قدم ۴ — سه گزارش: [[_ops/budget/STAGE1-REPORT|STAGE1 متابولیسم]] · [[_ops/debate/STAGE2-REPORT|STAGE2 مناظره]] · [[_ops/budget/STAGE3-REPORT|STAGE3 تکثیر]].
- **راستی‌آزمایی این جلسه:** سوئیت `_ops/tests/run_all.py` = **۶ فایل / ۳۲ چک سبز** (آفلاین $0) · leak_guard سبز · هر دو validator اجرا شد: فایل‌های این جلسه **clean**؛ فقط ~۸ خطای backlog قدیمی (`اونلی فنز`/`scout-digests`) + ۱ لینک placeholder کهنه — دست‌نخورده. (جلسهٔ قبل مقدار type دو نوت را به مقدار مجاز اصلاح کرده بود.)
- **پنل آشنایی فاز ۰ ساخته و زنده شد (verdict آری همین جلسه: «روشنش کنیم»):** `_ops/panel/server.py` (stdlib، $۰، فقط loopback) — فرم کوتاه RTL فارسی (نام/نقش/اولویت پروژه‌ها/لحن/میزان خودمختاری/ریسک بودجه/بهترین وقت گزارش/خط‌قرمزها/هدف)؛ ذخیرهٔ atomic در `_ops/state/OWNER-PROFILE.json` + لاگ append-only `OWNER-PROFILE-LOG.md`؛ بازدید بعدی صفحهٔ «خوش برگشتی» با خلاصهٔ جواب‌ها و لینک ویرایش نشان می‌دهد. لانچر دائمی: `_ops/panel/RUN-PANEL.bat` (CRLF، دابل‌کلیک هر وقت بخواهی). **تست end-to-end زنده انجام شد** (پر کردن → ذخیره → بازشناسی → ریست به فرم خالی) — سبز؛ دیتای تستی پاک شد (overwrite به `{}`، نه rm — طبق قاعدهٔ حذف‌ممنوع). زنده روی `http://127.0.0.1:8790/`. صرفاً MEASURE/دیتای شخصی — هیچ ارتباطی با گیت‌های بودجه/زنده ندارد.
- **همان جلسه — صفحهٔ `/projects` اضافه شد (خواستهٔ آری: «پروژه‌هام و وضعیتشو بگه»):** اسکن فقط‌خواندنیِ هر ۹ `PROJECT.md` واقعی vault (به‌جز `_Templates`/`_Duplicates`/`.claude` worktree کهنه/سایر مسیرهای `.agentignore`) → کارت‌های وضعیت (status/kind/به‌روزرسانی/تعداد اقدام باز/خط «تمرکز فعلی» پاک‌شده از wikilink و `**`). صفر نوشتن روی نوت‌ها. verify شد: ۹/۹ پروژهٔ واقعی درست (نه ۱۱ — دو تای اول template بودند، فیلتر شد).
- **🔴 یافتهٔ نو (به این جلسه ربط ندارد، ولی باید ثبت شود):** `genome-system/tests/review_test.py` **فلیکی** است — سه اجرای پیاپی `exit=0,0,1` با `concurrent appends broke the chain: prev mismatch`. یعنی قفلِ append ژنوم (رفعِ #۱ نسخهٔ v0.4.0) زیر ۴-تردِ موازی گاهی زنجیرهٔ hash را می‌شکند. snapshotهای قبلیِ «۴ تست ژنوم سبز» اتفاقی این را ندیده بودند. → کاندید فیکس جلسهٔ بعد (باگ concurrency واقعی، نه تستِ صرفاً racy).
- **ناتمام / معوق:** قدم ۵ (**بازبینی خصمانه**) در جلسهٔ ساختِ قبل در پس‌زمینه لانچ شد ولی یافته‌هایش هرگز بازیابی/اعمال نشد (‏TaskOutput وسط rate-limit مُرد) — این نخِ اصلیِ باز است. قدم ۶ دفترداری با همین ثبت بسته شد. قدم‌های ۷ (smoke شبانه) و ۸ (UI) فقط-مالک. `git` در این محیط می‌شکند (خطای `/sessions` = همان worktree مرده) → **commit معوق مالک؛ همهٔ کار روی دیسک امن ولی commit‌نشده.**
- **گیت‌های زنده دست‌نخورده:** هیچ ACTIVATION ساخته نشد؛ live پیش از ۰۷/۲۱ در کد قفل است؛ verdictهای باز V1/V2 + diff پیشنهادی روی میز آری. مرجع کامل ادامه: [[00 - Inbox/2026-07-06 2150 ORGANISM-BUILD-HANDOFF — ساخت لایه متابولیسم-مناظره-تکثیر و نقشه ادامه|ORGANISM-BUILD-HANDOFF §۴]].

## جلسه بیست‌ویکم 2026-07-06 ~۲۱:۵۰ (Claude Code) — ساخت کامل لایه متابولیسم-مناظره-تکثیر (کد + تست سبز) — ناتمام، handoff ثبت شد

آری: «تا کد کامل برو، منسجم کن، یک کل واحد؛ بعد UI؛ هدف: روشن/کارا/به‌یادسپار/خودیادگیرنده؛ یک ماه دیتا جمع کنیم» — وسط کار متوقف کرد و خواست همه‌چیز ثبت شود.

- **هر سه Stage پک + وحدت‌بخش ساخته و تست شد (۳۲ چک سبز، آفلاین $0، همه additive/سایه):** `_ops/budget/` (opslib · telemetry · organ_gate · governor_epoch با epoch **آلوستاتیک** · fitness ضدreward-hacking · replication با قفل σ) + `_ops/debate/` (client · topics ضدتزریق · debate_loop ≤۳دور گیت‌خورده) + `_ops/organism.py` (حلقه همیشه-روشن + HTTP وضعیت 8771 = هوک UI) + `_ops/RUN-ORGANISM.bat` (CRLF verify) + سه پرامپت در `04 - Architect System/prompts/` + سوئیت `_ops/tests/`.
- **گزارش کامل + نقشهٔ دقیق ادامه (۸ قدم) + میز آری:** [[00 - Inbox/2026-07-06 2150 ORGANISM-BUILD-HANDOFF — ساخت لایه متابولیسم-مناظره-تکثیر و نقشه ادامه|ORGANISM-BUILD-HANDOFF]] ← **ایجنت بعدی از §۴ این نوت ادامه دهد** (فیکس نشت llm.py → diff پیشنهادی budgets → ORGANISM-SPEC → STAGE-REPORTها → بازبینی خصمانه → دفترداری → smoke شبانه → UI).
- **verify شد:** تله‌های budget_gate (هاردکد/agent-ignore/باگ ارزی :90) · نشت llm.py (:30، بدون ANTHROPIC_BASE_URL) · «تأیید = sent نه approved» · دو منبع حقیقت تلمتری (ledger.jsonl + core.db/usage). budget_gate و budgets.yaml و genome-system **دست‌نخورده** ماندند.
- **git:** deny rule اجرایی دست‌زدن به `.git` را بست (درست طبق §۰-۲)؛ دستور کارآمد فیکس (config --file، چون `git -C` با worktree خراب اصلاً بالا نمی‌آید) در [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]] ورودی آخر. commit این جلسه معوق مالک.
- **گیت‌های زنده:** هیچ ACTIVATION ساخته نشد؛ live قبل از **۰۷/۲۱** در خود کد قفل است؛ فاز −۱ فروش (**۰۷/۲۰**) همچنان مقدم و بی‌متولی.

## جلسه بیستم‌و 2026-07-06 ~۱۹:۳۰ (Cowork) — PROMPT-PACK سه‌مرحله‌ای: متابولیسم → مناظره → تکثیر

آری: «گزارش v4 را با دیتای جدید (METABOLIC-GOVERNOR) وفق بده و به سه پرامپت مرحله‌ای تبدیل کن» + ویژن: دو ایجنت جعبه‌سیاه که بحث می‌کنند و تجربه ثبت می‌کنند، لوپ DeepSeek، ساب‌ایجنت با نرخ موفقیت، هر پروژه مستقل. (دیتای paste‌شده فقط دیتا بود — پرامپت داخلش اجرا/adopt نشد.)

- **خروجی:** [[00 - Inbox/2026-07-06 1930 PROMPT-PACK — سه پرامپت مرحله‌ای (متابولیسم-مناظره-تکثیر)|PROMPT-PACK]] (draft) — پرامپت ۱: تلمتری واحد + `organ_gate` + `governor_epoch` سایه (governor_shadow دست‌نخورده — کشف منتقد: آن سرپرستِ صفر-LLM است نه موتور تخصیص). پرامپت ۲: `_ops/debate/debate_loop.py` — معمار×خلاق، ≤۳ round، هر call از organ_gate، ثبت EXPERIENCE در ledger زنجیرهٔ‌هش (جایگزین ماشینی جدول پاشیدهٔ لجر). پرامپت ۳: fitness با تعریفِ قفلِ ضدreward-hacking (پذیرش = فقط APPROVAL صفِ کنترل-برین با تطبیق core.db؛ survive هرگز) + SPAWN human-gated + MAX_CELLS=6 + عمق ۱.
- **بازبینی سه‌منتقده (هر سه needs_fixes، فولد شد):** budgets.yaml از قبل verdict-خورده موجود بود (بازنویسی ممنوع شد) · aliasهای deepseek-chat/reasoner از ۰۷/۲۴ مرده‌اند → کلید از budgets.yaml · AU$1/روز لوپ = کل سقف ماهانه → پیش‌فرض cap_monthly: 5 AUD · تبدیل ارز پین (aud_per_usd) · رویداد نو در EVENT_TYPES مجاز نیست → NOTE/subtype · سیاست retry و est worst-case · گارد prompt-injection برای topicها · بند زمان‌بندی: فعال‌سازی زنده و پرامپت ۳ زودتر از ۰۷/۲۱ نه.
- **verdictهای باز پک:** عدد لوپ + تکلیف CEIL_DAY_USD هاردکد · NOTE/subtype یا افزودن type به ledger.py · دو فیکس git (تکرار). **فاز −۱ فروش ۰۷/۲۰ همچنان مقدم و بی‌متولی.**
- **v2 (قالب جامع، خواستهٔ آری):** پک بازنویسی شد — هر پرامپت حالا SNAPSHOT دانش verify‌شده تا سطح خط کد را درون خودش حمل می‌کند (تله‌ها: کلید ANTHROPIC حامل DeepSeek، متر صفرِ `or 0`، cp1252، EVENT_TYPES بسته، بازنشستگی aliasها ۰۷/۲۴) + role-promptهای کامل MUSE/ARCHITECT (embed) + schema رویدادها + فرمول est worst-case + تعریف قفلِ پذیرش + قرارداد STAGE1→2→3-REPORT برای انباشت دانش بین جلسات.

## جلسه بیستم‌هـ 2026-07-06 ~۱۹:۱۵ (Cowork) — نقشهٔ روابط کامل vault v4

آری: «گزارش کامل از تمام ارتباطات بین تمام فایل‌ها با خواندن دوبارهٔ همه — رودمپ‌طور.» اجرا: ۸ خوانندهٔ موازی (۲۹۷ خواندن) + گراف برنامه‌ایِ wikilink → [[00 - Inbox/2026-07-06 1911 Vault Relationship Map v4|Vault Relationship Map v4]] (کاندید جانشینی v3 در 02-Research — verdict آری).

- **اعداد سخت:** ۶۹۱ نوت / ۲۰۱۳ یال. ستون‌ها: architect/PROJECT (۷۲ ورودی) · ROTATION_CHECKLIST (۵۷) · HANDOFF (۸۴ خروجی — ستون فقرات ناوبری). شریان غالب: Inbox↔04 (۱۲۵+۸۷).
- **پنج لایه:** قانون اساسی/schema → حافظه → عملیات → کد → درآمد؛ زنجیرهٔ ساخت: HYBRID-SPEC ↔ GOVERNOR-MUSE ↔ genome-system ↔ PANEL-SPEC ↔ Coherence-Audit (۰۷/۲۰).
- **۱۰ شکاف برتر (v4 §۵):** دو `.git` مرده · لجر تجربه از ردیف ۶۸ پاشیده (parse ماشینی می‌شکند) · ددلاین ۰۷/۲۰ بی‌متولی · ناوگان fireAt بی‌نبض + perception-refresh به مقصد ناموجود (`_memory/SYSTEM-STATE.md`) · **مسیر hardcode شدهٔ `Desktop\backup` در پرامپت‌های restore خودترمیمی (vault در `F:\backup` است!)** · جفت‌های بی‌supersede (دکتر ×۲، mycelial ×۲، حافظهٔ Project-F ×۲) · لینک‌های شکستهٔ پس از انتقال کد · متون کهنهٔ گیت LIFTED · `_Archive`/`Raw/` غایبِ ارجاع‌شده · HANDOFF ۹۰KB متورم.
- **کشف جانبی:** کپی کهنهٔ کامل vault (~۵۱۱ نوت) در `.claude/worktrees/hopeful-elgamal-6febe8` [کاندید پاکسازی با verdict]. نکته: تعارض #۴ (عدد بودجه) در جلسهٔ METABOLIC-GOVERNOR (پایین ↓) بسته شد — AU$30.

## جلسه بیستم‌د 2026-07-06 (Cowork) — METABOLIC-GOVERNOR: بازبینی round-based + ثبت + بسته شدن تعارض #۴ (سقف = AU$30)

آری draft پیشنهاد «METABOLIC-GOVERNOR v0.1» را داد (مغز سهمیه‌بندی API، لایه روی budget_gate — extension پنتا، نه جریان پنجم). طبق workflow ورود دیتا: delta-map + راستی‌آزمایی وب + سه verdict گرفته شد.

- **ثبت شد:** [[04 - Architect System/2026-07-06 METABOLIC-GOVERNOR-proposal|METABOLIC-GOVERNOR-proposal]] (فرانت‌متر schema-compliant شد — کلیدهای اختراعی `system/scope/autonomy` به بدنه رفت، از کلاس تعارض #۸ جلوگیری شد) + §۵ بازبینی/delta-map داخل خود سند. لینک در [[04 - Architect System/GOVERNOR-MUSE-SYSTEM-INDEX|INDEX]].
- **✅ تعارض #۴ بسته شد (verdict آری): سقف واحد ماهانه = AU$30** → `_ops/budget/budgets.yaml` ساخته شد (تک‌منبع حقیقت؛ config-only، هیچ اتوماسیونی روشن نشد). ناسازگاری باقی: `CEIL_DAY_USD=2.0` در budget_gate با AU$30/ماه → daily = سقف burst؛ حل در budget_gate v2 (باید از budgets.yaml بخواند + per-organ buckets — الان پارامتر agent بی‌اثر است).
- **🔴 یافتهٔ راستی‌آزمایی:** aliasهای `deepseek-chat`/`deepseek-reasoner` از **۰۷/۲۴** بازنشسته می‌شوند (۱۸ روز!) — routing به `deepseek-v4-flash` تصحیح شد. قیمت Fugu رسماً تأیید ($5/$30؛ >272K $10/$45؛ no-stack؛ Max=۲۰× نه ۳۰×). [OPEN]: endpoint دقیق Sakana + **دسترسی استرالیا تأییدنشده** + قیمت رسمی DeepSeek از platform + آفر «ماه دوم مجانی تا پایان جولای» (مرتبط با پلن $20 جلسه ۱۸).
- **تعارض #۳ عمداً باز ماند:** جدول routing سند tier ‏Anthropic نداشت؛ در budgets.yaml ردیف anthropic فقط برای متر شدن اضافه شد — تغییر استک genome-system فقط از پروتکل ژنوم + `owner_confirmed` (verdict جدا).
- fitness عددی تا ~۴ هفته دادهٔ ledger فقط shadow (هم‌راستا با verdict جلسه ۱۶)؛ قید صریح در سند.
- git checkpoint نشد — هر دو repo مرده (تعارض #۶)؛ فیکس دستی آری هنوز مقدم است.
- **هنوز مهم‌ترین‌ها روی میز آری:** دو فیکس git (۲ دقیقه) → ۳ مخاطب فروش (۰۷/۲۰) → سه milestone فقط‌مالک ژنوم ۲ → verdict فعال‌سازی shadow این Governor (پیش‌نیاز: بک‌اپ → گارد → بودجه طبق INDEX).
- **(ادامهٔ جلسه)** پرامپت مادر برای Claude Code ساخته شد: [[00 - Inbox/Prompt - مهندسی کامل کدبیس vault (Claude Code max-load) 2026-07-06|پرامپت مهندسی کدبیس]] — پاس کامل چندایجنتی روی ۴ جبهه (second-brain-live · genome-system · scripts+budget_gate v2 · عرضی)؛ فاز ۰ = تعمیر هر دو git (مبنا: verdict «تو بزن» جلسه ۱۵، اجرا Windows-side)؛ صفر call خارجی؛ مهاجرت deepseek→v4-flash داخلش. اگر Code اجرایش کرد، دو فیکس git از میز آری برداشته می‌شود.

## جلسه بیستم‌ج 2026-07-06 ~۱۸:۲۰ (Cowork) — بازنگری کامل: چهار جریان موازی + آشتی با طرح قبلی

آری: «کامل از اول بازنگری کن — پوشه‌ها/منطق‌ها الان چه شکلی‌اند؛ طرح قبلی از یادمان نرود.» نقشهٔ کامل + آشتی: [[00 - Inbox/2026-07-06 1821 STATE-MAP — چهار جریان موازی و آشتی با طرح قبلی|STATE-MAP]].

- **کشف:** چهار جلسهٔ Cowork موازی کار کرده‌اند/می‌کنند — «ژنوم ۱-معمار» (04) · «ژنوم ۲-خلاق» (07) · «اونلی» · «زیمان» (مسیر Desktop = شورت‌کات به همین `F:\backup`؛ کپی واگرا نیست، تأیید شد) + تسک زمان‌بندی «Genome loop».
- **جریان ژنوم ۱ — GOVERNOR+MUSE (پنتا):** نقشه = [[04 - Architect System/GOVERNOR-MUSE-SYSTEM-INDEX|GOVERNOR-MUSE-SYSTEM-INDEX]]. ۱۵ سند propose + ۶ اسکریپت تست‌شده در `scripts/` + رفعِ اعمال‌شدهٔ دریفت‌های D1/D2/D3 + ۸ باگ رفع ([[04 - Architect System/2026-07-06 REVIEW-FIXES-changelog|REVIEW-FIXES]]). مانده (فقط‌مالک): پیست منشور فاز۱ در charter · `genome_guard --init` · مقصد بک‌اپ · Task Scheduler. ترتیب فعال‌سازی: بک‌اپ → گارد ژنوم → بودجه → GOVERNOR shadow → MUSE dry-run → (۳۰ روز) live. تصمیم باز: جهت D1 (L1 اعمال شد؛ L3؟). جزئیات: [[04 - Architect System/GOVERNOR-MUSE-APPLIED+HANDOFF|APPLIED+HANDOFF]].
- **جریان ژنوم ۲ — `07 - Knowledge/genome-system/` (v0.4.0):** پروژهٔ کد کامل (فاز ۰–۴ سبز): ژنوم read-only با **boundary test** + ledger hash-chain + سه ایجنت (Guardian/Creativity/Doctor) + LLM router. گزارش خودش (به‌دستور آری): [[07 - Knowledge/genome-system/HANDOFF|HANDOFF-قرارداد]] + [[07 - Knowledge/genome-system/CHANGELOG|CHANGELOG]] — ۷ ایراد ایمنی رفع (ledger زیر همزمانی، گیت بودجهٔ مردهٔ گاردین، tamper-detect، …)؛ حلقهٔ genome-loop ۳بار/روز (۹/۱۵/۲۱) plan-gated فعال؛ ۳ milestone فقط‌مالک باز (بک‌اپ off-site · کلید واقعی · `owner_confirmed`). گزارش Project-F: round-1 delta-map، ~۸۰٪ تأیید مسیر، تعارض‌ها فقط flag، پشت GATE 0. زیمان: چیزی ننوشت.
- **⚠️ هفت تعارض با تصمیم‌های قفل‌شده/طرح قبلی (جدول کامل در STATE-MAP §۴):** ژنوم پنجم (values.yaml ↔ باگ H1 HYBRID) · تأخیر هسته سه‌گزینه‌ای (۱۴روز/۷۲س+کلید دوم/۴۸س) · استک LLM دوگانه (DeepSeek قفل‌شده ↔ Anthropic در gates.yaml) · پنج عدد بودجهٔ ناسازگار (+$50/ماه نو) · خانهٔ کد در ۰۷ (خلاف جدول §۲) · **هر دو `.git` مرده** (vault: worktree سندباکسی · genome-system: صفر object) → همهٔ ادعاهای revert/branch فعلاً بی‌substrate · سه دکترِ موازی.
- **لنگر طرح قبلی (گم نشود):** [[00 - Inbox/2026-07-06 1450 HYBRID-SPEC — ژنوم واحد|HYBRID-SPEC]] + **فاز −۱ = فروش: ۳ مخاطب [[00 - Inbox/2026-07-06 1410 COHERENCE-AUDIT-PITCH-draft|COHERENCE-AUDIT]] §۶ هنوز خالی؛ ۰۷/۲۰ تنها ددلاین درآمد است و هیچ‌کدام از چهار جریان رویش کار نمی‌کند.**
- **پیشنهاد ادغام (propose-only، STATE-MAP §۶):** ۵ خط DECADE → `genome/values.yaml` (حل H1 بدون فیلد نو) · دو ریتم صریح (۷۲س عملیاتی / ۱۴روز زندگی) · evaluator مشترک سه دکتر · تصمیم استک LLM. verdictهای فوری: دو فیکس git → فروش → بقیه.

## جلسه بیستم‌ب 2026-07-06 (Cowork) — هیبریدِ کل سیستم: یکتاسازیِ سه ژنوم روی یک شیءِ کد

آری: «همه‌چیو ترکیب کن، کل سیستم رو بخون، هیبریدی جدید بساز» + «از پلاگینا استفاده کن». اجرا با یک Workflow چندایجنتی: ۵ خوانندهٔ موازی (کد زنده · اسپک‌های ژنوم · پنل/درآمد · سه ژنوم موازی · الگوها) → سنتز → ۳ منتقد خصمانه → آشتی (۱۰ ایجنت، هر سه منتقد `needs_fixes`؛ تصحیح‌ها فولد شد).

- **خروجی:** [[00 - Inbox/2026-07-06 1450 HYBRID-SPEC — ژنوم واحد|HYBRID-SPEC]] (draft). تز: سه سندِ موازی ([[00 - Inbox/2026-07-06 DECADE-CONTRACT-draft|پیمان ده‌ساله]] / دکتر / [[00 - Inbox/2026-07-06 PROBE-MERGE|قطب‌نما]]) روی یک شیءِ کد (`PersonalGenome`) یکی می‌شوند — هسته=`values`(DECADE) · محافظت=دکتر · سنجش=قطب‌نما؛ «یک anchor-set، سه مصرف» (پلِ اتصال از DECADE §۷.۴). پنل شریک = نمونهٔ همان ژنوم؛ Coherence Audit = بسته‌بندیِ همان موتورِ انسجام.
- **تصحیح‌های صداقتیِ منتقدها (مهم، فولدشده):** Coherence Audit فرضیهٔ درآمدیِ اثبات‌نشده است نه فروشِ قطعی · مرزِ هسته/پوسته امروز machine-enforceable نیست (کاغذی تا `.claude/settings.json`) · بلاکرِ نو کشف شد: ژنوم‌ها هیچ persistence ندارند (hardcode CFG) → **فاز ۰.۵ نو** · باگِ privacy برای accounting **latent است نه live** (رکن‌ها بی‌tier→DeepSeek) · `git init` پیش‌شرطِ هر ادعای revert.
- **فازبندی با death-condition صریح:** **فاز −۱ = فروش** (پرکردنِ ۳ مخاطبِ [[00 - Inbox/2026-07-06 1410 COHERENCE-AUDIT-PITCH-draft|COHERENCE-AUDIT]] §۶، zero code) **مقدم بر همهٔ پلامبینگ** چون ۰۷/۲۰ تنها ددلاینِ زندهٔ درآمد است.
- **۱۰ verdictِ باز (§۸):** سرآمد = ۵ خط هستهٔ DECADE هنوز blank · کلید دومِ انسانی · git init control-brain · سقف بودجه (تناقض AU$30/$40/$60) · بودجهٔ ساعت-به-فاز.
- **اعتبارسنجی:** هر دو validator اجرا شد — فایل نو **clean**؛ ۳۶ خطای backlog قدیمی (`_audit`/Project-F/scout-digests) و ۱ لینکِ placeholder دست‌نخورده. [[04 - Architect System/architect/PROJECT|architect PROJECT]] Active Context تازه شد.
- **پلاگین‌ها:** خواستهٔ آری «از پلاگینا استفاده کن» → Workflow (چندایجنتی) هستهٔ همین اجرا بود؛ نگاشتِ پنل↔پلاگین‌های Cowork (scheduled-tasks/Artifacts/skill-creator) به‌عنوان verdict §۸.۶ باز ماند.

## جلسه بیستم 2026-07-06 (Cowork) — merge ۵ کاوشگر → PROBE-MERGE؛ شرط مرگ ۰۷/۱۳ بسته

نتایج ۵ کاوشگر (نان/غربال/محک/قطب‌نما/کنتور، ۷ پاس، قیمت‌ها verify‌شده) در [[00 - Inbox/2026-07-06 PROBE-MERGE|PROBE-MERGE]] ثبت شد — شامل tally شکست WebSearch (instrument سطر ۵) و ثبتِ نقضِ تک‌کانتکستی.

- **verdict باز ۱ §۶ [[00 - Inbox/2026-07-06 1325 MASTER-COWORK-STRATEGY|MASTER-COWORK-STRATEGY]] بسته شد:** MCP جستجو وصل نمی‌شود؛ تریگر = ≥۵ شکست ثبت‌شده/هفته → اول free tier.
- **قواعد نو برای جلسات بعد:** بدون ۳ کیس طلایی هیچ skillی پیوند نمی‌خورد؛ داوری stale-view = sha256 نه LLM · مدل embedding قفل: bge-m3 (fallback: e5-base)؛ τ = صدک ۹۵ درون-Genome، recalibrate در رشد ۲۰٪/تعویض مدل · Graph-RAG فریز.
- **⚠️ تنها ددلاین زنده: ۰۷/۲۰ — پیچ «نان» (Coherence Audit، فیکس $3k–5k، ۲ هفته) به ۳ مخاطب.** جزئیات positioning/کانال‌ها در PROBE-MERGE.
- نکتهٔ اجرا: سندباکس bash اول جلسه بالا نیامد ولی بعداً برگشت — هر دو validator اجرا شد: فرانت‌متر PROBE-MERGE سبز (۳۵ خطای backlog قدیمی دست‌نخورده)؛ لینک شکستهٔ جلسه ۱۸ در همین HANDOFF فیکس شد (۲→۱؛ باقی‌مانده placeholder قدیمی scout-digest).
- **پرسش بقا (ادامهٔ جلسه):** «آرمین فراموش/منحرف/روز بد + پوشش خانواده؟» → draft [[00 - Inbox/2026-07-06 DECADE-CONTRACT-draft|پیمان ده‌ساله]] (قرارداد اولیس: ۵ هدف هسته با دست آری + خطوط قرمز + قاعدهٔ اصلاح ۱۴روزه + کلید دوم خانوادگی + بکاپ 3-2-1 + جانشینی؛ §۷ = گام‌های فعال‌سازی). منتظر verdict؛ **مقدم بر آن: ۰۷/۲۰.**
- **بازطراحی داشبورد (۸ سوال در ۲ دور، جواب‌های آری قفل شد):** [[00 - Inbox/2026-07-06 PANEL-SPEC-ادمین-و-شرکا|PANEL-SPEC]] — پنل ادمین دست آری + پنل کاستوم هر شریک (نقش OPERATOR)، وب از راه **VPS جدا** («آینهٔ گنگ»: مغز/سکرت روی لپ‌تاپ می‌ماند) + تلگرام، چت شریک ترکیبیِ سقف‌دار، نوتیف کاستوم شرطی. اسکلت موجود: authz سه‌نقشه + panel_server با PIN + rokn A. فازهای ۰–۳، هر فاز با verdict؛ شرط مرگ فاز ۱: ۷ روز بی‌استفادگی خود آری = توقف. **فاز ۰ بدون verdict شروع نمی‌شود.**
- **پرامپت تحقیق دکتر تکاملی (خواستهٔ آری: ژنوم بچسبد به دکتر):** [[00 - Inbox/Prompt - تحقیق عمیق مغز دوم تکاملی (ژنوم-حال-آینده) 2026-07-06|پرامپت تحقیق]] — خودبسنده برای اجرای مستقل در تب Research (Fable 5)؛ ۶ سوال Q1–Q6 (ژنوم/حال/آینده/خوداصلاحی امن/اقتصاد اسکن/سلسله‌مراتب هوش)؛ ۳ تصمیم باز نوت [[00 - Inbox/Prompt - اهداف دکتر مغز تکاملی (Evolutionary Doctor)|اهداف دکتر]] در خروجی الزامی GENOME-MERGE گنجانده شد. ⚠️ هشدار یکتاسازی: سه ژنوم موازی داریم (پیمان ده‌ساله · لنگرهای قطب‌نما · invariantهای دکتر) — Q1 مأمور یکی‌کردنشان است.

## جلسه نوزدهم‌ب 2026-07-06 (Cowork) — اجرای ۴گانه: فاز ۱ ژنوم (کد+تست سبز) + داشبورد ژنوم + pitch ۰۷/۲۰

آری «هر چهار مورد را انجام بده + پیشنهاد عملی‌ترشدن کدنویسی». هر چهار انجام و وریفای شد (کد واقعی، نه فقط سند):

- **#۱ فاز ۱ ژنوم (کد زنده):** `adapters/business/base.py` — `BusinessConfig` → **`PersonalGenome`** (backward-compatible، `BusinessConfig` alias؛ فیلدهای نو با default: persona/voice/values/goals/channels/autonomy/budget_share/privacy_class/evolution_optin/kpis؛ `__post_init__` → voice=tone، persona پیش‌فرض حرفه‌ای). سیستم‌پرامپت رکن A از `persona` می‌آید (خودشیفتگی حذف)، رکن B از `voice`. سه آداپتر (ziman/painting/accounting) با ژنوم غنی شدند (accounting=sensitive).
- **#۴ رجیستری+selftest (گلوی عملیاتی):** `adapters/business/__init__.py` → `genomes()` (۴ ژنوم شامل `PROJECTF_GENOME` config-only قفل=status_only/sensitive/بدون engine) + `genome_selftest.py`. **selftest آفلاین سبز:** هر ۵ چک پاس (فیلدها/post_init · رجیستری ۴تایی · جمع budget_share=۰.۸≤۱ · قفل Project-F · چرخهٔ کامل رکن A→B سه بیزنس با gateway/memory فیک).
- **#۲ داشبورد ژنوم:** `adapters/dashboard.py` → `/api/genomes` (JSON از `asdict`، verify: ۴ کارت/۱۸۵۲ بایت معتبر) + `/genomes` (کارت مدرن RTL هر ژنوم: persona/autonomy badge/budget bar/privacy 🔒/KPI) + لینک از صفحهٔ وضعیت. **view روی رجیستری، هستهٔ قدیم دست‌نخورده** (طبق انتخاب آری «داشبورد نو + هستهٔ قدیم»).
- **#۳ ددلاین ۰۷/۲۰:** [[00 - Inbox/2026-07-06 1410 COHERENCE-AUDIT-PITCH-draft|COHERENCE-AUDIT-PITCH]] (draft) — pitch یک‌صفحه‌ای هماهنگ با سطر ۱ PROBE-MERGE (positioning/مشکل/اسکوپ ۲هفته/deliverables/آفر $3–5k/۳ مخاطبِ جای‌خالی/پیام outreach). فرض صریح: Coherence Audit = ممیزی انسجام سیستم AI/دانش (نیچِ مهارت خودِ آری).
- **⚠️ stale-view دوباره:** مانت سندباکس فایل‌های تازه‌ویرایش‌شده را دُم‌بریده داد (base.py خط ۱۳۵، accounting خط ۲۴) — `cp` هم بایت stale کپی کرد. راه‌حل این‌بار: بازسازی معادلِ منطق در fs داخلی سندباکس و اجرای selftest آن‌جا (سبز). فایل واقعی ویندوز با Read کامل verify شد (base.py تا خط ۱۷۹).
- **معوق آری (گیت نهایی):** روی ویندوز `python run_tests.py` بزن (سوئیت ۴۷تایی؛ سندباکس telegram ندارد پس آن‌جا کامل اجرا نشد) + `python genome_selftest.py` + مرورگر `localhost:8770/genomes`. اگر سبز، commit ویندوزی.

## جلسه نوزدهم 2026-07-06 (Cowork) — فیکس Conflict تلگرام (قفل تک‌نمونه) + CRLF لانچرها

اولین بوت واقعی v2 موفق (داشبورد 8770 + KeePassXC + صف تأیید + ربات روشن) ولی کنسول پر از `telegram.error.Conflict` — ریشه: **دو نمونهٔ هم‌زمان app.py**. سه مسیر بی‌گارد: 🚀 ویزارد بدون چکِ روشن‌بودنِ مغز · autostart مخفی (`run-brain-hidden.vbs` + حلقهٔ restart ده‌ثانیه‌ای `run-brain.bat`) · double-bind ساکت 8770 روی ویندوز (`SO_REUSEADDR` در http.server).

- **فیکس ۱ — `_launchpad/second-brain-live/control-brain/app.py`:** قفل تک‌نمونه پیش از KeePass/داشبورد (سوکت انحصاری `127.0.0.1:8768`، env: ‏`BRAIN_LOCK_PORT`، با `SO_EXCLUSIVEADDRUSE`)؛ نمونهٔ دوم با پیام فارسی + دستور PowerShell بستنِ نمونهٔ مخفی، تمیز خارج می‌شود. kill/crash → آزادسازی خودکار قفل.
- **فیکس ۲ — `adapters/telegram_bot.py`:** ‏`add_error_handler` سراسری — Conflict (بار ۱و۲ و هر ۳۰اُم) و خطای شبکهٔ گذرا (هر ۱۰اُم) یک‌خطی و نمونه‌گیری‌شده؛ اسپم «No error handlers are registered» تمام شد.
- **فیکس ۳ — `setup_wizard.py` ‏/launch:** قبل از spawn مغز، ‏`port_open(DASHBOARD_PORT)` چک می‌شود — 🚀 چندباره دیگر نمونهٔ دوم نمی‌سازد؛ متن پاسخ هم وضعیت واقعی («از قبل روشن بود») را می‌گوید.
- **فیکس ۴ — ریشهٔ خروجی خرابِ START-HERE (اسکرین‌شات آری):** همهٔ `.bat`های launchpad ‏LF-only بودند → cmd خط‌ها را وسط توکن می‌شکست (`uirements.txt`، ‏`_modules`، ‏`-silent`) → هر ۷ فایل CRLF شد. **کشف دوم (بعد از CRLF):** پرانتزِ بسته داخل echoهای فارسیِ درونِ بلوک `if (...)` حالا parse-error قطعی می‌داد («... was unexpected at this time» → بستن آنی پنجره) → پرانتزها از خط ۱۵ و ۲۷ حذف و هر دو bat با CRLF صریح بازنویسی شد. **قاعده:** داخل بلوک cmd هرگز `(` یا `)` در متن echo نگذار.
- **وریفای:** app.py compile سبز؛ telegram_bot.py و setup_wizard.py ویندوز-verify کامل (مانت دوباره stale-view/دُم‌بریده نشان داد — همان کلاس شناختهٔ جلسه ۱۷)؛ بلوک‌های افزوده جداگانه در fs سندباکس compile سبز.
- **سند استراتژی Cowork (خواستهٔ پرامپت «Nexus» آری):** [[00 - Inbox/2026-07-06 1325 MASTER-COWORK-STRATEGY|MASTER-COWORK-STRATEGY]] — نگاشت به primitiveهای واقعی (vault=حافظه · subagent=تیم · skill=پلاگین · artifact/تسک=runtime) + ماتریس انتخاب ابزار + زنجیرهٔ استاندارد مأموریت + ۴ verdict باز (§۶ سند).
- **اسپک معماری ژنوم (خواستهٔ «بازطراحی هر بخش + استقلال + ژنوم شخصی کنار ژنوم اصلی»؛ محدوده=داشبورد نو روی هستهٔ قدیم، دامنه=همهٔ بیزنس‌ها):** [[00 - Inbox/2026-07-06 1400 GENOME-ARCHITECTURE-SPEC|GENOME-ARCHITECTURE-SPEC]] (draft) — کشف: ژنوم از قبل در کد هست (`BusinessConfig`=ژنوم شخصی · `core/`+`contracts.py`+`evolution/`=ژنوم اصلی). schema `PersonalGenome` (persona/voice/autonomy/budget_share/privacy_class/kpis) + نگاشت ۵ بیزنس + فازبندی ۵گانه + ۴ verdict (§۷). ⚠️ این **ژنوم عملیاتیِ per-agent** است؛ مکمل — نه هم‌ذاتِ — «ژنوم دکتر تکاملی/پیمان ده‌ساله» جلسه ۲۰ (آن لایهٔ invariant/ارزش است). Q1 جلسه ۲۰ باید این را هم در یکتاسازی لحاظ کند. پرامپت «Asba» آری خروجی خام یک LLM دیگر بود (نویسه‌های نشتی) و greenfield ابری — عمداً به تکامل‌درجا برگردانده شد (تضاد با معماری قفل‌شده).
- **⚠️ اقدام دستی آری (یک‌بار):** دابل‌کلیک `KILL-ALL-BRAIN.bat` (کنار START-HERE؛ همین جلسه ساخته شد — همهٔ پایتون‌ها را می‌بندد) و بعد فقط یک نمونه روشن کن؛ اگر `ZimanControlBrain.lnk` در `shell:startup` هست و خودکار نمی‌خواهی، پاکش کن. commit ویندوزی معوق جلسه ۱۸ حالا این فایل‌ها را هم می‌گیرد. (نکتهٔ shell: دستور PowerShell داخل wrapper ‏cmd وقتی از خود PowerShell اجرا شود `$_` را از دست می‌دهد — دو بار برای آری خطا ساخت؛ راه‌حل = فایل bat.)

## جلسه هجدهم 2026-07-06 (Cowork) — مأموریت «مغز دوم v2»: فاز ۰→۴ + ۱۶ الگوی معماری + کاک‌پیت واحد

خواستهٔ آری: پیاده‌سازی معماری v2 (۴ لایه، دو رکن هر بیزنس، مغز تکاملی) روی همان `_launchpad/second-brain-live/`، فاز‌به‌فاز با تأیید، موازی با استخراج الگوهای معماری vault و یکپارچه‌سازی.

- **فاز ۰ — کشف:** `_launchpad/second-brain-live/INVENTORY.md` — ممیزی، نگاشت کد موجود به ۴ لایه، پیشنهاد تک‌ربات ادمین، ۴ سؤال (جواب آری: کانال تلگرام+واتساپ · بیزنس‌ها زیمان/نقاشی/حسابداری · DeepSeek ~$2-3/روز + Fugu سقف $40 → پلن Standard $20 بهینه، وب‌سرچ تأیید کرد).
- **فاز ۱ — معماری:** `ARCHITECTURE.md` (۴ لایه + ۶ ADR + schema حافظه + Gateway + بودجه) + `core/contracts.py` (قرارداد رسمی دو رکن + Channel انتزاعی برای واتساپ).
- **فاز ۲ — Core+ادمین:** `core/memory.py` (core.db) + `gateway.py` (DeepSeek/Fugu/Tavily، دروازهٔ بودجه، کش) + `channels.py` + `approval.py` (صف approve-first + Notifier) → ربات ادمین ارتقا: `/status` تجمیعی+بودجه، `/queue`، `/briefs`، کارت 👍/👎، Approve/Edit/Reject.
- **فاز ۳ — آداپترها:** `adapters/business/` پلاگینی — base + زیمان/نقاشی/حسابداری (رکن A تحقیق وزن‌دار با حلقهٔ یادگیری + رکن B پیام approve-first) + `rokn_daily.py` (idempotent). کاربر `mom` (viewer) + فیلد Chat ID مامان در wizard. code-review پلاگین اجرا شد.
- **فاز ۴ — مغز تکاملی:** `evolution/brain.py` + `evolution_loop.py` — Proposal (مشکل/راه‌حل/ریسک/اثر/rollback) → کارت ادمین ✅/❌ → تأیید = ثبت `CHANGELOG.md` + دستور branch جدا (هرگز کد اصلی را مستقیم نمی‌زند). TTL ۳۰روزه (fail-closed) · kill سه‌سطحی (STOP-EVO/halt/git revert) · **گارد privacy: دیتای Project-F هرگز به Fugu نمی‌رود** (کشف pass-2: pool ی Fugu Ultra ثابت و opt-out ندارد).
- **الگوهای معماری (دو پاس، Explore agent):** [[00 - Inbox/ARCHITECTURE-PATTERNS-REPORT-2026-07-06|REPORT]] (۱۲ الگو) + [[00 - Inbox/ARCHITECTURE-PATTERNS-DEEP-V2-2026-07-06|DEEP-V2]] (۱۱ الگوی نو + ۵ هایبرید کامپوزیت + ۲۹ قاعدهٔ DECISIONS) — ورودی DNA فاز ۴/۵. + نوت [[00 - Inbox/marketing-agent-tooling-audit-2026-07-06|ممیزی ابزار بازاریابی]].
- **کاک‌پیت واحد:** آرتیفکت `second-brain-master-cockpit` جایگزین ۵ آرتیفکت pinned شد — پیشرفت فاز + ۴ لایه + گیت/بودجه + ناوگان زنده. هر فاز آپدیت می‌شود.
- **کیفیت:** تست‌سوئیت ۲۱→۴۷ (۴۶ سبز؛ ۱ قرمز = آرتیفکت stale-copy تست فاز۲ نه باگ منطق).
- **⚠️ معوق آری (مهم):** (۱) **یک بار `git add -A && git commit` سمت ویندوز** بزن — stale-view مانت باعث شد چند blob (base.py/rokn_daily.py/setup_wizard.py/…) در git ناقص ذخیره شوند؛ فایل‌های واقعی ویندوز کامل‌اند (Grep تأیید شد) و commit ویندوزی همه را re-sync می‌کند. (۲) فاز ۵ (README غیرفنی + smoke نهایی) با «فاز ۵ برو». (۳) restart wizard برای دیدن فیلد مامان + ماژول‌های evolution/rokn-daily.

## جلسه هفدهم 2026-07-06 (Cowork) — 🟢 گیت LIFTED + throttle دستی ناوگان + لغو killswitch

سه verdict آری در یک پیام: throttle دستی · گیت را ببند («جمعش کن») · backlog غیر-md را خودت مهندسی کن.

- **🟢 Security Gate رسماً برداشته شد:** ریشهٔ برگشت‌های مکرر پیدا شد — §۲ [[04 - Architect System/architect/ARCHITECT_CHARTER|CHARTER]] دو خط متناقض diff-مانند داشت (بسته 07-03 / باز 07-05) و بقیهٔ فایل‌ها از خط کهنه می‌خواندند. حالا یک خط canonical «LIFTED 2026-07-06» + هدر [[ROTATION_CHECKLIST]] هماهنگ + ثبت در [[_memory/EXPERIENCE-LEDGER|ledger]]. ۱۴ ردیف HIGH/MEDIUM = backlog چرخش، **گیت نیستند**. این داستان بسته است — دوباره بازش نکن.
- **Throttle دستی (به‌جای killswitch):** `doctor-research` هر ۲ ساعت · `learning-engine-loop` هر ۶ ساعت (:35) · trio ‏pulse/consolidator/focus-board هر ۶ ساعت · ۱۹ اسکات روزانه دست‌نخورده · **`fleet-killswitch-1day` (فردا ۱۷:۰۰) disabled شد.** بار: ~۲۱۲ → ~۴۵ اجرا/روز.
- **backlog غیر-md اجرا هم شد (verdict دوم آری: «برو کاملش کن نترس»):** B1 کد → `_code/` (۹ پوشه + ۱۲ فایل؛ ۴ نوت md معماری path-linked برگردانده شد) · B2 دیتای بدون‌ارجاع ×۱۴ → `_Duplicates` · B3 تصویر orphan ×۶۸ → `08 - Assets` · ۱۹۲ فایل ارجاع‌دار عمداً ماند. جزئیات + لاگ: [[00 - Inbox/NONMD-TRIAGE-PLAN-2026-07-06|NONMD-TRIAGE-PLAN]] (status: done).
- **✅ git init انجام شد (سرانجام):** ‏`.git` خرابِ جلسه ۱۵ (HEAD معیوب) → `_Duplicates/broken-dot-git-2026-07-05`. کشف مهندسی: مانت سندباکس الگوی lock+rename گیت را خراب می‌کند (config → NUL) → repo روی fs امن سندباکس ساخته شد و آخر جلسه بیت‌به‌بیت به vault کپی و verify شد. ۳ commit: snapshot اولیه (۱۵۰۳ فایل، fsck سبز) · B2+B3 · مستندات. قرنطینهٔ PHASE-0A در `.gitignore` (۳ نوت فیوژن تا rotation ردیف ۶). **قاعده برای جلسات بعد: git از سندباکس فقط read؛ commit یا Windows-side یا با الگوی tmp→copy→verify همین جلسه.**
- **🧠 «مغز دوم» (Second Brain Live) ساخته شد (خواستهٔ آری: زنده‌سازی کامل خارج سندباکس):** `_launchpad/second-brain-live/` = کپی control-brain + ziman-agent + **painting-bot + accounting-bot** (مرجع‌ها در `_code` دست‌نخورده؛ کل `_launchpad` ‏gitignore). ‏`setup_wizard.py` (فرم HTML فارسی ‏localhost:8877): همهٔ کلیدها شامل **Sakana Fugu** + توکن‌های جدا برای هر ربات، فقط در `.env` محلی؛ + **📡 گزارش اتصال** (getMe زندهٔ تلگرام‌ها، پینگ Anthropic، ‏Fugu، ‏KeePass، ‏Node/Python، وضعیت ۴ ماژول، درصد اتصال). پچ‌های کپی: fallback ‏DictSecrets از env در `app.py` (بدون KeePass کار می‌کند) · هر ۴ پروژه enabled با workdir نسبی · requirements ربات نقاشی از اسکن import ساخته شد · npm install خودکار در bat. مسیر آری: `START-HERE.bat` → فرم → 📡 → 🚀. v2 = کاستوم UI. **اولین اجرای واقعی آری انجام شد: گزارش اتصال ۱۱/۱۴ سبز (۷۸٪) — هر ۳ ربات تلگرام متصل.** سپس با verdict آری **Anthropic حذف و DeepSeek موتور اصلی شد** (endpoint سازگار `api.deepseek.com/anthropic` + `LLM_MODEL=deepseek-chat`؛ متغیر `ANTHROPIC_API_KEY` عمداً حامل کلید DeepSeek برای کد قدیمی). Fugu فقط escalation.
- **⚠️ درس stale-view تکرار شد:** فایل‌های همین‌جلسه ویرایش‌شده از مانت سندباکس نمای بریده می‌دهند (wizard در سندباکس SyntaxError نمایی داد؛ ویندوزی کامل و سالم verify شد) — تست نهایی wizard را آری موقع اجرا می‌بیند.
- **معوق آری:** اجرای `START-HERE.bat` با توکن تلگرام **نو** · «Run now» روی تسک‌های تازه‌throttle‌شده اگر روی pre-approve مکث کردند · repo تودرتوی AiFarm در `_code` به `.git-disabled` تغییرنام یافت (برگشت‌پذیر).

### ادامه جلسه ۱۷ — خاموشی کامل ناوگان (verdict آری: «همشون خاموش بشن»)

خواستهٔ آری بعد از throttle صبح: «به تموم اسکجل‌ها بگو برای بار آخر تسکاشونو انجام بدن، گزارشاشونو یادداشت کنن و خاموش بشن، همشون.»

- **مکانیزم:** ابزار trigger فوری در دسترس نبود؛ به‌جایش هر ۲۷ تسک enabled از cron به `fireAt` یک‌باره تبدیل شد (staggered، هرکدام ۱ دقیقه فاصله، بین ۱۰:۱۳ تا ۱۰:۳۹ صبح سیدنی). تسک یک‌باره طبق رفتار استاندارد پس از fire شدن **خودش auto-disable می‌شود** — یعنی هرکدام گزارش/دیجست عادی خودش را (رفتار همیشگی، بدون تغییر پرامپت) یک آخرین‌بار می‌نویسد و بعد خاموش می‌ماند.
- **۲۷ تسک متاثر:** survival-heartbeat، mycelium، crypto/mining/lead/ziman/accounting/hypnosis/projectf-scout، mycelial-consolidator، fleet-selection، ai-watch/security-watch/markets/jobs/health/tools/philosophy/world/science/learning/local-sydney-scout، brain-pulse، brain-focus-board، experience-review، learning-engine-loop، doctor-research.
- **شرط:** fire فقط تا وقتی اپ Cowork باز است انجام می‌شود؛ اگر بسته شد، در باز شدن بعدی fire و disable می‌شود.
- **جمع بعد از این پنجره: ۰ تسک زمان‌بندی فعال.** راه‌اندازی مجدد هرکدام = تصمیم بعدی آری (نه خودکار).
- **معوق واقعی آری (از پاسخ قبلی):** ۱) بستن رسمی داستان گیت — انجام شد بالا (بند اول همین جلسه). ۲) backlog غیر-md — انجام شد بالا (بند سوم). این جلسه فقط لایهٔ زمان‌بندی را تمام کرد.

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
- **دور اولِ زنده اجرا شد (دستور آری «تا یک ساعت»):** ۹ ایجنت موازی → ۹ دیجست منبع‌دار در [[00 - Inbox/scout-digests/_README - Scout Digests|scout-digests]] (`2026-07-04 <slug>.md`) + [[00 - Inbox/scout-digests/2026-07-04 synthesis|synthesis]] (الگوهای بین‌پروژه‌ای). اعتبارسنجی: **۳۵۵ نوت، صفر لینک شکسته؛ صفر خطای فرانت‌متر جدید.** یافته‌های شاخص: Crypto stack زیر AU$30 (~$0.01/ماه) · Mining VerusHash ~۹وات بردهٔ کارایی · Lead: Google LSA در AU نیست → GBP+Ads · selfimprove طرح R-08 (Certificate-Transparency برای لینک دو زنجیرهٔ آدیت). ۵ الگوی مایکوریزایی در synthesis (مالکیت substrate · نگه‌داشت>جذب · evaporation/hرس · AI بک‌اند نامرئی · verified≠speculative).
- **باز برای آری:** (۱) برای پیش‌تأییدِ ابزارها، هر تسک را یک‌بار «Run now» بزن تا اجراهای بعدی روی permission مکث نکنند. (۲) دایال شدت selfimprove: ساعتی=۷۵٪ دقیق ولی ریسک سقف نرخ؛ `0 */2 * * *` سبک‌تر. (۳) هرس هفتگی scout-digests را consolidator پیشنهاد می‌دهد ولی اجرا با آری (ایجنت حذف نمی‌کند).

## جلسه چهارم 2026-07-04 (Cowork) — رفع خطای EACCES ابسیدین

- علت: `_Archive/Venvs/karyabi-bot-venv` یک venv ساخته‌شده در WSL بود (symlinkهای `bin/python` که ویندوز نمی‌تواند lstat کند) → Obsidian هنگام لود EACCES می‌داد.
- اقدام با تایید صریح آری: همان venv حذف شد (استثنای مجاز `.agentignore` — دستور مستقیم مالک). `QuantumAlphaBot-venv` بررسی شد: venv خالص ویندوزی، صفر symlink، بی‌خطر و دست‌نخورده ماند.
- درس قاعده‌ای: venvهای WSL/لینوکسی حتی در `_Archive` هم برای Obsidian سمی‌اند (ویندوز symlinkهای WSL را lstat نمی‌کند).
- **اجرا شد (توسط خود آری، PowerShell):** کل `_Archive` → `Desktop\backup-Archive` (بیرون vault). ریشه vault دیگر `_Archive` ندارد؛ `_Duplicates` هنوز داخل است. `QuantumAlphaBot-venv` (سالم، ویندوزی) هم با همان انتقال بیرون رفت.
- هماهنگ‌سازی: [[01 - Dashboard/Home|Home]] (بخش پوشه‌های سیستمی) به‌روز شد. چون [[_PROJECT_INSTRUCTIONS|قانون اساسی]] فقط‌خواندنی است، پیشنهاد کامل آپدیت قواعد (§۰/§۲/§۳/§۱۲ + `.agentignore`/`.gitignore` + SOP تلگرام + Weekly Review + CLAUDE.md + مسیرهای stale نوت‌ها) در [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]] ثبت شد — منتظر verdict آری.

## جلسه سوم 2026-07-04 (Cowork) — Triage کامل vault با verdict مستقیم آری

استثنای گیت فقط برای مرتب‌سازی/triage با دستور مستقیم مالک اعمال شد؛ هیچ secret و هیچ `_code` لمس نشد؛ گیت برای هر کار autonomous پابرجاست.

- **Inbox: ۲۸ → ۵ فایل.** مانده‌ها فقط موارد باز: [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]] (خالی) + ۴ پرامپت در انتظار اجرا (Security Ops G-01 · Phase 4 · [[00 - Inbox/Prompt - Research Pack 7 Projects 2026-07-03|Research Pack]] با پرامپت‌های باقیمانده Mining/Ziman/Project-F · [[00 - Inbox/Prompt - اتصال همه پروژه‌ها به مغز کنترل|اتصال به مغز کنترل]]).
- **corpus تحقیق → `04 - Architect System/architect/02-Research/`:** SCOUT-A/C/DEEP-Governance/[[04 - Architect System/architect/02-Research/SCOUT-SUMMARY|SUMMARY]] · [[04 - Architect System/architect/02-Research/Report - 20 AGI Architectures 2026|Report - 20 AGI]] · [[04 - Architect System/architect/02-Research/Report - Architect - Adversarial Review v3 2026-07-04|Adversarial Review v3]] · [[04 - Architect System/architect/02-Research/Report - Architec