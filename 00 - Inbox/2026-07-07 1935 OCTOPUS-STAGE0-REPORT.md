---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: done
tags: [octopus, organism, audit]
created: 2026-07-07
updated: 2026-07-07
created_by: agent
---

# OCTOPUS · STAGE-REPORT-0 — GOAL-LOCK + REALITY-AUDIT (اجرا: 2026-07-07، جلسه ۲۷-ادامه)

> append-only — Stage بعدی اولین کارش خواندن همین بلوک است. پرامپت منبع: [[00 - Inbox/Prompt - OCTOPUS STAGE 0 (v-final) 2026-07-07|Prompt STAGE 0]].
> قرارداد صداقت (دستور کار جلسه ۲۶): **هر ادعای این گزارش یا شاهد runnable دارد یا برچسب [EST]/[OPEN]** — جلسهٔ بعد شاهدها را اجرا کند، گزارش را باور نکند.
> شاهدهای runnable: `python -X utf8 _ops/tests/run_all.py` (۶ فایل/۴۰ چک) · `genome-system/tests/leak_guard_test.py` · دو validator ‏`scripts/` · CLI ‏`python budget_gate.py`.

## STAGE-REPORT-0

```yaml
goals_restated: >
  Octopus = ارگانیسم چندایجنتهٔ درآمدزا روی همین vault: هر tentacle یک بیزنس واقعی اپراتور،
  تنها سیگنال نهایی fitness «دلار AUD محقق‌شده در حساب» (نه پیش‌بینی، نه self-report)،
  یادگیری از آزمون‌وخطا/خاطره (ledger append-only)، رشد فقط پشت گیت انسانی و سقف سخت.
  isomorphism-first: این سیستم از صفر ساخته نمی‌شود — لایهٔ ارگانیسم `_ops/` + genome-system +
  control-brain موجودند؛ Octopus «تکمیل بُعدهای گمشده» است: پول واقعی (attribution)، trust-ramp، رابط‌ها.

value_produced: >
  کوتاه‌مدت: بریف/پیام تحقیق‌شدهٔ approve-first برای بیزنس‌ها (زمان اپراتور آزاد می‌شود).
  میان‌مدت: لید→فاکتور→پول نشسته با attribution قابل‌اندازه‌گیری per-tentacle.
  سنجش: AUD ‏CONFIRMED در reconciliation + acceptance_rate انسانی (فعلاً تنها متریک زنده).

priority_confirmed: >
  ✅ verdict آری 2026-07-07 (همین جلسه، چهارگزینه‌ای): «ستاپ کامل مقدم» —
  فروش فاز −۱ (ددلاین 2026-07-20) دستی/موازی توسط خود اپراتور؛ در سیستم همچنان بی‌متولی [OPEN].

tentacle_candidates:
  - {name: Lead-نقاشی,  مسیر_درآمد: لید→کوت→فاکتور پرداخت‌شده, خروجی_سنجش‌پذیر: "رسید بانکی با carrier=شماره فاکتور", mode: paper}
  - {name: Ziman Galerry, مسیر_درآمد: فروش گالری/محتوا, خروجی_سنجش‌پذیر: "فروش منتسب به UTM/کد تخفیف (فازی)", mode: paper}
  - {name: Crypto-eToro,  مسیر_درآمد: "P&L محقق per-position (BUY انسانی، SELL طبق exit_rules)", خروجی_سنجش‌پذیر: position_id در صورت eToro, mode: paper}
  - {name: Accounting,    نقش: "organ پشتیبان روی floor — درآمد مستقیم ندارد، خارج از لوپ داروینی", mode: floor}
  - {name: Mining,        نقش: "INFORM-only، خارج از لوپ", mode: floor}
  - {name: Project-F,     نقش: "🔒 walled — EXCLUDED_ORGANS تا GATE 0؛ هرگز به Fugu", mode: excluded}

repo_map:   # [VERIFIED روی ریپو در همین جلسه؛ تست‌ها اجرا شدند]
  آناتومی(germline/soma):
    - "07 - Knowledge/genome-system/ — ledger hash-chain (ledger/ledger.py) + Guardian/Creativity/Doctor + gates.yaml"
    - "vault markdown + git (دو branch merge‌نشده: modest-gould گزارش ۲۶ · jolly-ardinghelli تغییرات ۲۷/این گزارش)"
    - "_ops/ORGANISM-SPEC.md = سند کل واحد؛ RATIFIED-TASKS = تک‌منبع بازسازی ناوگان (مسیرها از ۲۷ درست)"
  فیزیولوژی(pulse/HRV/dormancy):
    - "_ops/organism.py — حلقهٔ tick ۵دقیقه‌ای + HTTP وضعیت 8771؛ ⚠ هرگز tick نخورده (ORGANISM-STATE.json غایب [VERIFIED])"
    - "_ops/budget/governor_epoch.py — epoch آلوستاتیک: clamp(base·(1−k·pressure), base/4..base·2)؛ pressure=max(velocity,deadline,anomaly)"
    - "_ops/budget/replication.py — σ از ledger؛ STOP/FREEZE فلگ‌ها در opslib (fail-closed)"
    - "بک‌اپ off-box: scripts/backup-offbox.ps1 + restore-drill.ps1 فقط اسکریپت — هرگز اجرا نشده [VERIFIED جلسه ۲۶]"
  متابولیسم(budget/enforce):
    - "scripts/budget_gate.py = تنها enforcer (v1.1 از امروز — همه-AUD)"
    - "_ops/budget/budgets.yaml = SoT اعداد (cap 30 AUD · human_gate_aud 10 · spike_pct 25 ≡ MAX_DRAWDOWN)"
    - "_ops/budget/organ_gate.py (per-organ روی budget_gate، جایگزین نه) · telemetry.py (دو منبع حقیقت + STOP-METABOLIC) · fitness.py (پذیرش فقط انسانی)"
  رابط‌ها(اولویت پک Web→TG→WA):
    - "Web: _ops/panel/server.py ‏loopback:8790 (پروفایل/پروژه‌ها/organism) ✅ زنده‌شدنی؛ صفحهٔ tentacle/attribution ندارد"
    - "Telegram: _launchpad/second-brain-live/control-brain (approve-first، مهاجرت v4-flash در ۲۷) — ساخته، خاموش"
    - "WhatsApp: فقط interface ‏Channel در core/contracts.py — ساخته نشده"

dual_core_map:   # isomorphism: دو-هسته از قبل به‌شکل رکن A/B وجود دارد — ماژول موازی نساز
  - {module: "هر بیزنس (adapters/business/*)", self_core: "رکن A تحقیق/یادگیری وزن‌دار", outreach_core: "رکن B پیام/compose ‏approve-first", weight: "وزن‌های SoT ‏budgets.yaml: value .30/urgency .25/efficiency .20/human .20/waste .05"}
  - {module: "لایهٔ ارگانیسم", self_core: "genome Guardian/Doctor + fitness/σ", outreach_core: "debate→PROPOSAL→صف انسانی", weight: "داوری تعارض = verdict انسانی (تنها arbiter)؛ کمی‌سازی رقابت دو-هسته [OPEN — Stage 1]"}

reward_loop_design: >
  طبق طرح MONEY-ATTRIBUTION (فعلاً artifact چت — [OPEN: فایل شود]): attribution_id حامل از
  PROPOSAL→CLAIMED(گزارش انسان)→CONFIRMED(فقط reconcile با core.db/بانک/eToro)→ATTRIBUTED؛
  fitness هرگز زیر CONFIRMED نمی‌خواند؛ mismatch → [CONFLICT] freeze. گارد Goodhart همین امروز
  test-backed است: «APPROVAL جعلی در ledger → σ بالا می‌رود ولی acceptance_rate بی‌حرکت» (چک ۴۰م سوئیت).
  رویدادهای MONEY_* طبق verdict V2 امروز = type جدید در EVENT_TYPES (آیتم ساخت P1، با تست زنجیره).
  attribution_coverage باید vital درجه‌یک شود (کنار σ/drawdown).

autonomy_ramp_init: >
  ✅ verdict آری 2026-07-07: آستانهٔ پول human-gate = 10 (ثبت‌شده AU$10 در budgets.yaml:human_gate_aud؛
  اگر منظور USD بود ≈AU$15 — اصلاحش یک خط است [CONFIRM ارز]). trust-score هنوز ساخته نشده؛
  init: همهٔ tentacleها trust=0 و mode=paper؛ فرمول = f(paper→live پاس‌شده، AUD ‏CONFIRMED مثبت،
  صفر نقض ناوردی) — منحنی رشد [OPEN]. پرعواقب‌ها (پول>آستانه، کلید، حذف floor، spawn بین‌پروژه،
  kill/rollback) همیشه human-gated. live_gate دوقفله (تاریخ ≥2026-07-21 + پرچم فقط-مالک) [VERIFIED در opslib + تست].

sigma_control_law: >
  σ هرگز به ۱ servo نمی‌شود؛ ایمنی روی cap+gate: MAX_CELLS=6 (سقف سخت)، spawn_depth=1،
  accept_threshold=0.40، spawn همیشه PROPOSAL پشت گیت دوقفله + verdict انسانی (seed دستی)،
  EXCLUDED: PROJECT_F. ‏σ_effective فقط از ledger (APPROVAL با origin.loop=replication) شمرده
  می‌شود؛ σ>1 → آلارم cancer-axis [test-backed]. نرخ ذاتی فعلاً subcritical-با-seed-دستی
  (محافظه‌کارترین گزینهٔ خود پک) تا اولین ماه دیتای واقعی.

gaps:
  - "قلب هرگز نزده: ORGANISM-STATE.json غایب — اولین tick فقط-مالک (RUN-ORGANISM.bat)"
  - "ناوردی ۳ باز: off-box + restore-drill اجرانشده (M0.5) — گیت هر کار پرریسک"
  - "لایهٔ پول (attribution/MONEY events/reconcile.py) ساخته نشده — فقط طرح"
  - "trust-score و منحنی رشد: وجود ندارد"
  - "budget_gate v2 (خواندن سقف‌ها از budgets.yaml به‌جای هاردکد): ساخته نشده"
  - "germline_lag بدون MAX_LAG عددی (vital تعریف‌نشده)"
  - "Fugu: base_url ‏TBD + دسترسی AU تأییدنشده [OPEN]؛ قیمت DeepSeek از platform قفل نهایی نشده"
  - "پنل صفحهٔ tentacle/attribution ندارد؛ WhatsApp ساخته نشده"
  - "دو branch ‏git ‏merge‌نشده؛ فروش 07-20 بی‌متولی (دستی مالک)"

blockers:   # چهار بلاکر ادعایی پک، RE-VERIFY شده روی ریپو
  - {name: "نشت کلید (ANTHROPIC_API_KEY حامل DeepSeek → api.anthropic.com)", status: VERIFIED, fix: "از قبل بسته — llm.py v0.4.3: API_URL از ANTHROPIC_BASE_URL + گارد دوطرفهٔ hostname (:44-55)؛ شاهد: leak_guard_test.py"}
  - {name: "ریاضی بودجه ($2/روز ≫ AU$30/ماه)", status: VERIFIED, fix: "SoT از ۰۷-۰۶: cap_monthly=30 AUD؛ daily=سقف burst نه نرخ پایدار؛ امروز V1 اعداد را قفل کرد (همه-AUD)"}
  - {name: "باگ ارز budget_gate (AUD vs ثابت USD)", status: VERIFIED, fix: "✅ فیکس شد همین جلسه (v1.1 پشت verdict V1): DISASTER_AUD=500 (رفتار قبلی حفظ)، CEIL_DAY_AUD=2 (چک ×نرخ پین — سفت‌تر از قبل)، governor_epoch و تست زنجیر هماهنگ؛ سوئیت ۴۰/۴۰ سبز"}
  - {name: "epoch به‌شکل clock", status: VERIFIED, fix: "از قبل آلوستاتیک بود — governor_epoch.py:76 ‏clamp(base·(1−k·pressure))؛ نقض منشور وجود ندارد"}
  - {name: "مسیر vault (Desktop\\backup مرده)", status: VERIFIED, fix: "جلسه ۲۷ در ۷ فایل عملیاتی فیکس شد؛ vault = F:\\backup"}
  - {name: "مهاجرت DeepSeek کد زنده (aliasها تا 07-24)", status: VERIFIED, fix: "جلسه ۲۷: gateway/setup_wizard/providers → deepseek-v4-flash"}

build_plan:   # ordered by dependency — P0 ≺ P0.5 ≺ P1 ≺ P2 ≺ P3 ≺ P4
  - "P0 ✅ (این گزارش): goal-lock + audit + چهار verdict قفل (اولویت/گیت‌پول/V1/V2) + فیکس بلاکر ارز"
  - "P0.5 germline-first (فقط-مالک — ناوردی ۳، گیت هر کار پرریسک): merge دو branch → rclone remote → اولین sync → restore-drill سبز با شمارش (اسکریپت‌ها آماده‌اند)"
  - "P1 frozen core (agent، ارزان): budget_gate v2 (سقف‌ها از budgets.yaml؛ همان تست‌ها) · پیاده‌سازی V2 (type جدید EVENT_TYPES + تست زنجیره/سازگاری) · MAX_LAG عددی germline_lag (پیشنهاد→verdict)"
  - "P2 metabolism+pulse زنده (Stage 1 پک): اولین tick ارگانیسم (مالک: RUN-ORGANISM) → telemetry واقعی · trust-score skeleton (MEASURE-only) · attribution skeleton (MONEY events shadow — ۳ تصمیم carrier باز)"
  - "P3 debate: موجود و تست‌شده (سایه)؛ فقط اتصال بودجهٔ لوپ (پیش‌فرض AU$5/ماه) پس از P2"
  - "P4 replication: موجود (propose-only)؛ پشت live_gate دوقفله + σ-law بالا؛ هیچ کار جدید تا دیتای paper"

open_questions:   # سه ورودی گمشده + باقی‌مانده
  - "ارزش/carrier (ورودی ۱): سه تصمیم MONEY-ATTRIBUTION — feed مستقل reconcile (CSV بانک/حسابداری یا API؟) · حامل عملی Lead (شماره فاکتور موجود است؟) · پنجرهٔ attribution/grace چند روز؟"
  - "وضعیت کد (ورودی ۲): ✅ پاسخ داده شد (همین audit)؛ فقط: کی merge دو branch؟"
  - "محیط اجرا (ورودی ۳): مقصد off-box (B2/Drive/OneDrive؟) · دابل‌کلیک RUN-ORGANISM کی؟ · دسترسی AU ‏Sakana + base_url از کنسول [OPEN]"
  - "V1 ✅ بسته (همه-AUD: روز2/ماه30/فاجعه500 + MAX_DRAWDOWN≡spike_pct)؛ باقی‌ماندهٔ بسته: قفل قیمت DeepSeek از platform + عدد لوپ مناظره (پیش‌فرض AU$5 برقرار)"
  - "V2 ✅ بسته: type جدید در EVENT_TYPES (اجرا در P1)"
  - "ارز human_gate: «$10» به‌عنوان AU$10 ثبت شد — اگر USD منظور بود بگو (یک خط اصلاح)"
  - "متولی فروش 07-20: طبق verdict امروز دستی/مالک — چه کسی/کی؟"

invariants_touched:
  - "I6 تک-enforcer: فیکس داخل خود budget_gate؛ هیچ enforcer موازی ساخته نشد"
  - "I11 صداقت عددی: همهٔ قیمت‌ها [EST]/[FACT] با منبع؛ هیچ عددی جعل نشد"
  - "ناوردی ۳ (germline-first): ⚠ هنوز باز — P0.5 را gate می‌کند؛ هیچ کار پرریسکی پیش از drill"
  - "I13 (انسان رئیس): چهار تصمیم امروز با verdict صریح اپراتور قفل شد، نه فرض ایجنت"

epoch_mode: "allostatic — تابعِ فشار [VERIFIED در governor_epoch.py + تست سبز]"
```

## لاگ تغییرات کد این Stage (فقط بلاکر — طبق حکم پک)

| فایل | تغییر | شاهد |
|---|---|---|
| `04 - Architect System/scripts/budget_gate.py` | v1.1: ثابت‌ها → ‏`CEIL_DAY_AUD/CEIL_MONTH_AUD/DISASTER_AUD` (همه AUD طبق V1)؛ چک روزانه ×نرخ پین؛ خط فاجعه AUD≥AUD | سوئیت ۴۰ چک سبز |
| `_ops/budget/governor_epoch.py` | ‏burst_cap = ‏CEIL_DAY_AUD/AUD (نسبت velocity بی‌بعد ماند) | چک‌های epoch سبز |
| `_ops/tests/test_organ_gate.py` | اعداد تست زنجیر روزانه به semantics ‏AUD نو | «زنجیر به budget_gate» سبز |
| `_ops/budget/organ_gate.py` + `_ops/budget/budgets.yaml` | فقط کامنت/SoT: بستن [OPEN] قدیمی + کلید نو `human_gate_aud: 10` + نگاشت MAX_DRAWDOWN≡spike_pct | validatorها صفر خطای نو |

## ضمیمهٔ ۱ (append-only) — پاسخ‌های اپراتور + اعمال (2026-07-07 ~۲۰:۰۰)

آری به سؤال‌های باز جواب داد (بلوک OPERATOR ANSWERS، چت). حکم‌ها و اعمال:

| سؤال باز | verdict اپراتور | اعمال |
|---|---|---|
| carrier/ارزش (ورودی ۱) | feed مستقل (بانک/Stripe/فاکتور) = ground-truth؛ Lead شماره‌فاکتور ندارد → سیستم **id یکتا mint کند**؛ پنجرهٔ attribution = **۷ روز** | ✅ سه تصمیم قفل → [[00 - Inbox/2026-07-07 2000 MONEY-ATTRIBUTION-design v1|MONEY-ATTRIBUTION v1]] فایل شد (status: ready، ساخت P2) |
| کد (ورودی ۲) | فقط merge مانده؛ ترتیب: **merge → tick اول** | — فقط-مالک |
| محیط (ورودی ۳) | off-box = **دیسک/ماشین دوم محلی (T1/T2)**؛ هشدار خود اپراتور: از آتش/سرقت محافظت نمی‌کند → tier ابری رمزنگاری‌شده بعداً؛ برای drill کافی است | ✅ verdict در [[04 - Architect System/architect/01-Project/M0.5-RESTORE-RUNBOOK-proposal|M0.5-runbook]] ثبت شد |
| گیت پول | **AU$20** (جایگزین $10؛ enforcer سفت می‌ماند) | ✅ `budgets.yaml: human_gate_aud: 20` |
| V1 باقی‌مانده | لوپ مناظره = **AU$10/ماه**؛ قیمت DeepSeek از platform قفل شود، [VERIFIED]، تخمین ممنوع | ✅ `DEBATE_LOOP: {cap_monthly: 10}` در SoT · قیمت‌ها **[VERIFIED 2026-07-07 · api-docs.deepseek.com/quick_start/pricing]**: flash in $0.14 (cache-hit $0.0028) / out $0.28 — عین عدد موجود gateway، برچسب ارتقا یافت؛ pro $0.435 (hit $0.003625) / $0.87؛ بازنشستگی aliasها 07-24 15:59 UTC روی صفحه تأیید |
| متولی فروش 07-20 | **tentacle فعالِ human-gated موازی** (نه منتفی، نه خودکار)؛ اولویت کلی ستاپ | ✅ تسک در Next actions ‏[[04 - Architect System/architect/PROJECT|PROJECT آرشیتکت]]؛ سیستم پس از merge+tick فقط draft/تحقیق؛ هر اقدام واقعی دست آری |
| حاکمیت | ✅ تأیید: فقط فیکس verdict-دار اعمال شد؛ شل‌کردن ترمز رد شد | — |

**تنها گیت باقی‌مانده پیش از P2: merge دو branch (فقط-مالک) → اولین tick.** سؤال‌های هنوز باز: Fugu ‏base_url/دسترسی AU [OPEN] · MAX_LAG عددی (P1) · منحنی رشد trust (P2).

## ضمیمهٔ ۲ (append-only) — اجرای دستور merge اپراتور + سبزی پس از ادغام (2026-07-07 ~۲۰:۴۵)

دستور human-gated اپراتور («فقط همین کار») اجرا شد:

1. merge نیمه‌تمام موجود بود (MERGE_HEAD=`720de99`، **صفر conflict** — توقف تلاش قبلی = خطای مجوز گذرای `.git/objects`، نه تعارض) → `git merge --abort` تمیز.
2. tag ‏`pre-merge-20260707` از قبل وجود داشت؛ verify شد → دقیقاً `6a1d493` ✅ (واگرد اضطراری: `git reset --hard pre-merge-20260707`).
3. ‏modest-gould طبق دستور merge نشد. ⚠ **یافتهٔ دقیق برای مالک:** tip آن شاخه = `5356cd7` یعنی **صفر کامیت اختصاصی** — «در master بودن» فقط ancestor بودن است؛ **فایل گزارش جلسه ۲۶ («…1745 گزارش راستی‌آزمایی زمینی….md») در master نیست** (نه tracked، نه روی دیسک Inbox اصلی) و تنها نسخه‌اش uncommitted روی دیسک worktree قدیمی است: `F:\backup\.claude\worktrees\modest-gould-1c7bac\00 - Inbox\`. HANDOFF ‏master هم ورودی جلسه ۲۶ ندارد. بازیابی = کپی همان فایل به Inbox اصلی + commit (یک‌دقیقه‌ای؛ خارج از mandate این دستور — انجام نشد).
4. **merge انجام شد: `35c383f`** — ۲۷ فایل، +489/−66، **صفر conflict**، تلاش اول، بدون خطای مجوز، درخت کار تمیز (SYSTEM-OVERVIEW فقط سمت master تغییر کرده بود و HANDOFF فقط سمت شاخهٔ ما → تداخلی نبود).
5. **سبزی پس از merge روی F:\backup:** سوئیت `_ops` ۶ فایل/۴۰ چک سبز · فرانت‌متر: ۳۳۲ نوت، همان ۳۳ خطای backlog شناختهٔ §۱۱ · لینک‌ها: ۶۱۹ نوت، همان ۱ placeholder کهنه — **صفر خطای نو**. (اختلاف شمارش با worktree = فایل‌های ignored/محلیِ روی دیسک master که در git نیستند.)

master اکنون = جلسه ۲۷ کامل + STAGE 0 + پاسخ‌های اپراتور + SYSTEM-OVERVIEW. گیت بعدی: **P0.5** (rclone به دیسک دوم → restore-drill) → tick اول.

## ضمیمهٔ ۳ (append-only) — P0.5 اجرا شد: germline off-box + restore-drill سبز (2026-07-07 ~۲۰:۲۲)

اسکریپت P0.5 اپراتور اجرا شد با سه تطبیق [RE-VERIFY]شده: (۱) گیت `ledger.py verify` فعال شد — CLI واقعاً موجود بود (exit 0/1)؛ (۲) حذف `2>$null` از ‏git clone — تلهٔ PS5.1 با ‏EAP=Stop روی stderr پیشرفت؛ (۳) manifest با utf8. پیش‌فرض‌ها verify شد: درایو E ‏(«Game»، ۷۲GB آزاد) ≠ F ✅ · ۵۷۸ نوت tracked ≥ آستانهٔ ۳۰۰ ✅ · ‏ledger.jsonl ژنوم tracked (داخل bundle) ✅ · در `_ops` فقط `__pycache__` ‏ignored ✅.

زنجیرهٔ fail-closed (هر پله شکست = توقف کل):

1. `git fsck --full` روی vault ✅ · `ledger.py verify` زنجیرهٔ hash ژنوم ✅
2. bundle کل تاریخچه → `E:\germline\vault-2026-07-07_2022.bundle` (**196.9MB**) + robocopy ‏`_ops` → ‏`state-2026-07-07_2022\`
3. **restore-drill واقعی (هرگز روی vault ‏live):** clone از bundle به scratch → ‏fsck ✅ → **۵۷۸ نوت بازیابی** (= دقیقاً شمار tracked) → **verify زنجیرهٔ ledger «بازیابی‌شده»** ✅ (round-trip کامل) → scratch پاک
4. manifest: ‏`drill: PASS`، ‏`germline_lag = 0`

**ناوردی ۳ (germline-first) روی tier محلی بسته شد** — «بک‌آپ تست‌نشده = بک‌آپ نامعلوم» دیگر برقرار نیست؛ مسیر restore اثبات‌شده موجود است. **🟢 گیت tick اول باز است** (دابل‌کلیک `RUN-ORGANISM.bat` — فقط-مالک).

باقی‌مانده/گپ ثبت‌شده: tier ابری رمزنگاری‌شده (هشدار خود اپراتور: آتش/سرقت) · زمان‌بندی تکرار بک‌اپ (کاندید: schtasks با همین اسکریپت bundle) · `core.db` و `_launchpad/**/events.jsonl` ‏gitignore‌اند و در bundle نیستند — الان تقریباً خالی؛ از اولین اجرای واقعی brain باید جداگانه (بدون `.env`!) به STATE_DIRS اضافه شوند.

## ضمیمهٔ ۴ (append-only) — دستور واحد اجرا شد: بازیابی ژنوم + زمان‌بندی germline + BIRTH (2026-07-07 ~۲۰:۵۵)

هشت پلهٔ دستور human-gated آری، fail-closed و به ترتیب اجرا شد (جابه‌جایی اعلام‌شده: ثبتِ پلهٔ ۸ پیش از بک‌آپِ پلهٔ ۷ تا خود رکوردها هم داخل bundle بیفتند و germline_lag واقعاً صفر شود):

1. **ژنوم:** گزارش جلسه ۲۶ از worktree قدیمی → Inbox اصلی (append-only، بدون overwrite) — commit ‏**`5924926`** ‏(`592492653c3ce2f468001d29baec0010c865ebd4`).
2. **اسکوپ state:** ‏`core.db` + ‏`events.jsonl` به هر دو لایهٔ بک‌آپ اضافه شد — SECRET-GUARD دولایه: whitelist دقیق نام فایل + رد الگوی `env/secret/wallet/seed`؛ هرگز `.env`.
3. **زمان‌بندی germline دولایه** (Register-ScheduledTask — بدون نیاز به elevation، هر دو Ready): ‏`germline-hourly` هر ۱ ساعت = push افزایشی همهٔ شاخه‌ها/tagها به bare repo ‏`E:\germline\vault.git` + کپی state غلتان (تستِ زنده: سبز، refs verify شد) · ‏`germline-daily` ‏۰۳:۳۰ = bundle کامل + restore-drill + prune با retention ‏۷ روزانه/۴ هفتگی. اسکریپت‌ها داخل خود vault: `04 - Architect System/scripts/germline-backup.ps1` و `germline-hourly.ps1` (خودشان هم بک‌آپ می‌شوند).
4. **drill پیشا-تولد سبز:** ‏`vault-2026-07-07_2040.bundle` — **۵۷۹ نوت** بازیابی (+۱ = گزارش ۲۶) · زنجیرهٔ ledger دوسویه OK · ‏core.db در state گرفته شد.
5. **pre-flight ‏۱۵/۱۵ ‏PASS** + سوئیت ۴۰ چک سبز: kill مسلح و نپریده (STOP-ORGANISM غایب، halted/frozen false) · ‏budget_gate v1.1 با deny ‏functional روی رزرو بزرگ (reason=daily) · ‏SoT: ‏human_gate_aud=20 / لوپ=10 / ماه=30 AUD · **هر دو live-gate قفل تا 2026-07-21 + هر دو پرچم فعال‌سازی غایب = صفر مسیر پول واقعی (paper-only مطلق)**. نکتهٔ صداقتی: ماژول enforcement آستانهٔ AU$20 = P2؛ الان خاصیت اکیداً قوی‌تر برقرار است.
6. **BIRTH ✅ (observed) — 2026-07-07 20:42:55:** ‏`RUN-ORGANISM.bat` لانچ مستقل؛ tick اول در همان ثانیه: **اولین pulse آلوستاتیک: pressure=0.047** (تماماً deadline_proximity ‏= ‏PROJECT_F@2026-07-20، ‏۱۳ روز؛ spend_velocity=0، anomaly=0) → ‏next_epoch=**57.9min** · organs/telemetry خوانده شد ($0، صفر conflict، صفر suspect) · σ=0.0 ‏(pre-replication) · fitness در سایه (authoritative=false) · **دو NOTE به ledger ژنوم نشست: ‏ALLOCATION_SHADOW ‏(h1_ok=true) + ‏ORGANISM_DAILY — و زنجیرهٔ hash پس از append دوباره verify شد** · ‏HTTP ‏`127.0.0.1:8771` زنده (‏/api/organism ‏۲۰۰) · هیچ alert/anomaly/تلاش irreversible — halt لازم نشد. debate طبق طراحی در tick لود نمی‌شود؛ وقتی human-triggered اجرا شود هر call از ‏organ_gate با سقف AU$10/ماه می‌گذرد.
7. **post-birth backup:** بلافاصله پس از commit همین رکورد اجرا (germline_lag=0)؛ manifest در `E:\germline\last_backup_manifest.json`.
8. همین ضمیمه + HANDOFF + PROJECT.

**گپ‌های باز:** tier ابری رمزنگاری‌شده · محتوای واقعی core.db پس از اولین اجرای brain · enforcement آستانهٔ AU$20 (ماژول trust/ramp — P2) · بازبینی smoke ‏۲۴ساعته فردا (organism روشن مانده؛ kill تمیز = فایل `_ops\STOP-ORGANISM`).

## ضمیمهٔ ۵ (append-only) — PLAN-ONLY: ‏MASTER-PLAN v1 + دو INCIDENT از audit زنده (2026-07-07 ~۲۱:۱۰)

دستور plan-only اپراتور اجرا شد — هیچ ساختی، هیچ تغییر live، فقط audit + پلن + ثبت:

## ضمیمهٔ ۶ (append-only) — BUILD ‏Track 0: پایدارسازی ✅ (2026-07-07 ~۲۱:۵۰ — commit ‏`49312fa`)

- **C6 ✅** سه فایل soma ‏untrack (`git rm --cached` — فایل‌ها روی دیسک) + ‏.gitignore (شامل الگوی `telemetry/` برای فایل‌های dated فردا)؛ حضورشان در بک‌آپ verify شد؛ repo تمیز. ‏follow-up کوچک: ‏fitness/replication-latest هم daily-churn دارند (سؤال باز).
- **C2 ✅** ‏`scripts/organism-watchdog.ps1` + تسک ‏`organism-watchdog` ‏(Ready): هر ۱۵ دقیقه از +2h؛ اول تسلیم به STOP/STOP-ORGANISM؛ **فقط revive** (تولد اول همیشه دست مالک). انحراف: trigger ‏AtLogOn ‏Access-denied (الویشن) → پوشش ری‌بوت با همان تکرار ‏۱۵دقیقه‌ای.
- **INC-2 ✅ ریشه:** با مهار stderr پیدا شد — «`remote: unable to write .../vault.git/objects/tmp_... Permission denied`» یعنی **git.exe زیر توکن task روی E: نمی‌نویسد ولی PowerShell می‌نویسد** (ACL سالم بود، CFA=0، ‏RunLevel Highest هم ثبت‌نشدنی). فیکس معماری: **git → ‏TEMP محلی، ‏Move با PowerShell به E:** · ‏hourly: push سبک مسیر اول + ‏fallback غلتان تک‌فایلی `hourly-latest.bundle` (‏~196MB ثابت — انباشته نمی‌شود، سازگار با نگرانی دیسک verdict) · ‏daily هم TEMP→Move. **verify در context واقعی زمان‌بند: hourly ‏`OK bundle-fallback` ✅ · ‏daily ‏result=0، ‏manifest ‏`2026-07-07_2144` ✅.** ‏[OPEN-DIAG غیرباربر: چراییِ دقیق رفتار git زیر task.]
- **🟢 اقدام مالک: دابل‌کلیک `F:\backup\_ops\RUN-ORGANISM.bat`** → تولد پایدار + شروع کلاک smoke ‏۲۴h؛ watchdog از این پس مرگ ناخواسته را ≤۱۵min جبران می‌کند.

## ضمیمهٔ ۵ → یادداشت زمینه (audit پیش از BUILD):

- **audit زنده سه یافتهٔ نو داد:** 🔴 ‏INC-1: ارگانیسم پس از ۳ tick سالم از ~20:53 مرده (پورت refused؛ هیچ python/cmd؛ هیچ crash-log/heartbeat خروج → ‏kill خارجی پروسه+launcher؛ محتمل: teardown ‏job سندباکس ایجنت — **درس: تولد پایدار فقط با لانچ مالک یا Scheduled Task**) · 🟠 ‏INC-2: اولین اجرای scheduled ‏germline-hourly ‏FAIL ‏(20:49، ‏exit 1؛ stderr در log نیست؛ اجرای دستی سبز بود) — لایهٔ روزانه+دستی پوشش می‌دهد؛ [RE-VERIFY @21:49] · 🟡 سه فایل soma-state ناخواسته tracked → repo با هر tick دائم dirty (تصمیم gitignore = C6).
- **خروجی:** [[00 - Inbox/2026-07-07 2110 OCTOPUS-MASTER-PLAN v1|OCTOPUS-MASTER-PLAN v1]] — چهار Track ‏(A ایمنی پول: bg-v2/money_gate/capability-gate/V2/MAX_LAG · ‏B اولین tentacle ‏paper = Lead-نقاشی تا اولین دلار CONFIRMED · ‏C سخت‌سازی/رصد: فیکس دو INCIDENT، smoke ‏۲۴h، tier ابری، داشبورد 8771، ‏gitignore ‏soma · ‏D فروش 07-20 ‏human-gated مستقل) + گراف وابستگی/critical-path + ‏۱۰ ‏open-decision + ‏[RE-VERIFY]ها. **هیچ فرضی به‌جای verdict گذاشته نشد.**

## ضمیمهٔ ۷ (append-only) — CONSOLIDATE: کارِ in-flightِ Track A گم‌نشده به master + verify سبز (2026-07-07 ~۲۲:۲۷ — merge `b2e754d`)

اجراگرِ نو (همین سشن، Opus 4.8) طبق verdict اپراتور «تو اجراگرِ اصلیِ masterی؛ اول consolidateِ بی‌گم‌شدن، بعد Track A» اجرا شد. **هیچ اقدام live/پولی/irreversible.**

```yaml
built: >
  کارِ commit‌نشدهٔ Track A/A4 روی master (۷ فایل incl. money_event_test.py untracked) گم‌نشده
  ثبت شد: (۱) tag لنگر pre-consolidate-20260707-2227 = 49312fa · (۲) برنچ wip/trackA-20260707-2227
  (commit 2089358) کل tree in-flight را گرفت · (۳) merge --no-ff به master = b2e754d.
  merge برنچِ <AHEAD> عمداً skip شد چون هیچ برنچی جلوتر از master نیست (توپولوژی زیر).
verified_numbers:
  - {what: "_ops suite", value: "۶/۶ فایل سبز (هدر: ۴۰ چک)", source: "python -X utf8 _ops/tests/run_all.py", tag: RUNNABLE}
  - {what: "money EVENT_TYPE (V2)", value: "۳/۳ چک سبز؛ chain mixed-type verified + set بسته می‌ماند", source: "genome-system/tests/money_event_test.py", tag: RUNNABLE}
  - {what: "سفت‌کاری ضدِ APPROVAL جعلی", value: "تست present و سبز: acceptance_rate بی‌حرکت", source: "_ops/tests (test_fitness_sigma)", tag: RUNNABLE}
  - {what: "validatorها", value: "فقط backlog شناختهٔ §۱۱ (_audit/اونلی‌فنز/scout-digests) + ۱ لینک placeholder؛ صفر خطای نو", source: "scripts/validate_frontmatter.py + find_broken_links.py (621 نوت)", tag: RUNNABLE}
  - {what: "توپولوژی برنچ‌ها", value: "master جلوترین؛ behind: jolly8/nifty11/vigilant11/modest11؛ sad-bartik 0/0 (=master)؛ هیچ‌کدام ahead نیست", source: "git rev-list --left-right --count master...<b>", tag: RUNNABLE}
traps_hit:
  - {trap: "cp1252: چاپِ '─' در run_all.py روی کنسول ویندوز می‌ترکد (UnicodeEncodeError) — تلهٔ شناخته", fix: "PYTHONUTF8=1 / python -X utf8 (مطابق هدر همین گزارش)"}
invariants_touched: >
  هیچ ناوردی تضعیف نشد. append-only حفظ شد (هیچ hard-delete؛ برنچ wip + tag نگه داشته شد).
  budget_gate/budgets.yaml دست‌نخورده. live_gate دوقفله سالم (تست سبز). هیچ مسیر پولی/live لمس نشد.
  دست‌نزدن به C:\Users\Armin رعایت شد.
sigma_epoch_state: >
  ارگانیسم خاموش است (نه 8771 listen، نه پروسهٔ python) — مطابق INC-1 (مرگ ~20:53).
  σ=0 / pre-replication (تست). epoch آلوستاتیک، هیچ epoch زنده‌ای نمی‌چرخد.
  تولدِ دوباره = دابل‌کلیک مالک `F:\backup\_ops\RUN-ORGANISM.bat` (watchdog فقط revive، تولد اول دستِ مالک).
open_for_next: >
  Track A: budget_gate v2 (خواندن از budgets.yaml SoT + fail-closed) → money_gate (AU$20 با token انسانی)
  → A3 capability-gate (07-21). همه offline/paper. · reconcile plumbing `_ops/reconcile/*.csv` هنوز ساخته نشده
  (بلاکر Track B). · worktreeهای کهنه modest-gould/vigilant-williamson روی 5356cd7 (۱۱ behind)؛ modest-gould یک
  نسخهٔ dupِ گزارش جلسه ۲۶ دارد که فقط روی همان برنچ است (master معادلش را دارد) — کاندید prune با verdict.
ledger_events_written: >
  هیچ — این Stage فقط git است (capture/merge)، هیچ tick ارگانیسم و هیچ append به ledger نشد.
human_verdicts_open: >
  ⚠️ امنیت: C:\Users\Armin یک git repo است (فقط ۲ فایل زیر Documents track شده؛ هیچ .ssh/secret/.env)
  — نشتِ فعال نیست ولی footgun است؛ فقط flag شد، تصمیم با مالک. · prune دو worktree کهنه. · نگه‌داشتنِ
  wip/trackA-20260707-2227 + tag pre-consolidate تا تأیید مالک (rollback: git reset --hard pre-consolidate-20260707-2227).
  · [OPEN] base_url/دسترسی AU سakana · منحنی trust-ramp · هر قیمت/آفر/مخاطبِ نو = بپرس.
```

- **تصحیح یک ادعای کهنه:** گزارشِ راستی‌آزماییِ ۱۷:۴۵ (روی worktree کهنهٔ modest-gould) چند آیتم را «باز» دید که در واقع روی master بسته‌اند (money-gate AU$20، loop AU$10، DeepSeek [VERIFIED]، DISASTER فیکس، MAX_DRAWDOWN≡spike_pct، germline اثبات‌شده). علتش صرفاً کهنه‌بودنِ آن worktree بود — نه خطای master. سند صحیح = همین STAGE0-REPORT.

## ضمیمهٔ ۸ (append-only) — Track A · A1 budget_gate v2 (SoT-read) ساخته و تست شد (2026-07-07 ~۲۲:۴۰ — commit بعدی)

اجراگرِ نو (Opus، master) پس از consolidate، اولین آیتمِ باقی‌ماندهٔ Track A را ساخت. **offline/paper، هیچ مسیر پول واقعی، non-breaking.**

```yaml
built: >
  budget_gate.py حالا سقف‌ها را از budgets.yaml (SoT) می‌خواند (`_caps()`) به‌جای ثابتِ هاردکد.
  fail-closed = strictest: cap مؤثر = min(yaml, کفِ هاردکد)؛ yaml ناخوانا/غایب/بی‌PyYAML → کفِ هاردکد.
  نرخ ارز آینهٔ opslib (yaml.aud_per_usd یا 1.5) تا دو لایه واگرا نشوند. امضای reserve/settle/release دست‌نخورد.
  به‌روزرسانی: `04 - Architect System/scripts/budget_gate.py` + کامنتِ زنجیر `_ops/budget/organ_gate.py`
  (per-organ از قبل آنجا enforce می‌شد — گپِ A1 فقط سقفِ سراسریِ خودِ budget_gate بود) +
  تستِ نو `_ops/tests/test_budget_gate_v2.py` (۷ چک) در run_all.
verified_numbers:
  - {what: "تستِ A1", value: "۷/۷ سبز (SoT-read · strictest-min · fail-closed · non-breaking · daily/disaster از SoT)", source: "python -X utf8 _ops/tests/test_budget_gate_v2.py", tag: RUNNABLE}
  - {what: "کلِ سوئیت", value: "۷/۷ فایل سبز (۶ قبلی + A1)", source: "python -X utf8 _ops/tests/run_all.py", tag: RUNNABLE}
  - {what: "CLI روی budgets.yaml واقعی", value: "caps_effective = day 2 · month 30 · disaster 500 · aud 1.5؛ src='budgets.yaml ∧ hardcode-floor' (= v1.1، non-breaking)", source: "python -X utf8 budget_gate.py", tag: RUNNABLE}
traps_hit:
  - {trap: "cp1252 (باز هم) روی run_all/print", fix: "python -X utf8"}
invariants_touched: >
  I2 (تک-enforcer) حفظ شد — budget_gate همچنان تنها نقطهٔ enforce؛ فقط منبعِ اعدادش SoT شد.
  fail-closed سخت‌تر شد (min → هرگز شل‌تر از هاردکد). budgets.yaml دست‌نخورده (I6). هیچ مسیر live/پول لمس نشد.
open_for_next: >
  A2 money_gate (ماژول نو `_ops/budget/money_gate.py`: check(amount_aud, approval_token) > AU$20 بدون token = deny؛
  هنوز مصرف‌کننده ندارد=paper) · سپس A3 capability-gate (⚠ open-decision #2 — تغییر تعریفِ live_gate = نیازمند verdict مالک،
  پیش از ساخت متوقف می‌شوم) · Track B هنوز به reconcile plumbing نیاز دارد.
human_verdicts_open: >
  A3 (open-decision #2): آیا live_gate از «تاریخ+پرچم» به «تاریخ+پرچم+marker سبزِ سوئیت» ارتقا یابد؟ (تغییر قفل = verdict).
  سایر open-decisionهای MASTER-PLAN v1 هنوز باز.
```

## ضمیمهٔ ۹ (append-only) — Track A · A2 money_gate + A3 capability-gate (open-decision #2 قفل‌شد) ساخته و سبز (2026-07-07 ~۲۳:۱۰ — commit بعدی)

verdict اپراتور: «A2 و A3 را همین حالا بساز؛ open-decision #2 قفل شد؛ کلیدِ انسانی = Telegram (فعلاً وصل‌نشده).» ساخته شد؛ **offline/paper، هیچ مسیرِ پولِ واقعی، هر دو گیت fail-closed.**

**تعریفِ قفل‌شدهٔ live_gate (طبق درخواستِ اپراتور برای ثبت):**
> `capability_gate.is_open(action)` = True فقط اگر **هر سه** با AND: (۱) **capability** — markerِ سبزِ کاملِ سوئیت (فقط `run_all` سبز می‌نویسدش؛ هر شکست revoke) · (۲) **LIVE_ENABLED** — پرچمی که فقط انسان از ApprovalChannel می‌سازد (نه ناوگان، نه تاریخ) · (۳) **per-action approval** — تأییدِ انسانیِ match‌خورده از ApprovalChannel. **calendar ≠ capability**: رسیدنِ 07-21 یا هر تاریخی به‌تنهایی هیچ باز نمی‌کند.
> `money_gate.check(amount, action, channel)`: ≤AU$20 → allow (زیرِ Autonomy Ramp؛ سقفِ کل با budget_gate)؛ >AU$20 → فقط با تأییدِ انسانیِ معتبرِ match‌خورده (status ∈ approved/sent). خودگزارشیِ ایجنت هرگز معتبر نیست.
> `require(action, amount, channel)` = هر اقدامِ پولِ واقعی باید **هم** از live_gate **هم** از money_gate رد شود.

**چرا الان بسته است (اثباتِ runnable، محیطِ واقعی):** `capability_ok=True` (سوئیت سبز) ولی `live_enabled=False` (پرچمِ انسانی نیست) + کانال = NotWiredStub (Telegram وصل نیست) → `require('LEAD-TEST', 50)` = **deny در live_gate**؛ `money_gate.check(50)` = **deny** مستقل. این حالتِ مطلوبِ فازِ paper است.

```yaml
built: >
  سه ماژولِ نو در _ops/budget: approval_channel.py (Approval/ApprovalChannel/NotWiredStub/MockApprovalChannel)،
  money_gate.py (A2)، capability_gate.py (A3، شاملِ require() که دو گیت را زنجیر می‌کند). ApprovalChannel
  pluggable؛ adapterِ عملیاتی=Telegram (وصل‌نشده→NotWiredStub، همیشه no-approval). run_all حالا markerِ
  CAPABILITY-OK را روی سبزِ کامل می‌نویسد و روی هر شکست revoke می‌کند (fail-closed).
verified_numbers:
  - {what: "A2 money_gate", value: "۶/۶ سبز", source: "python -X utf8 _ops/tests/test_money_gate.py", tag: RUNNABLE}
  - {what: "A3 capability_gate", value: "۶/۶ سبز", source: "python -X utf8 _ops/tests/test_capability_gate.py", tag: RUNNABLE}
  - {what: "کلِ سوئیت", value: "۹/۹ فایل سبز (۷ + A2 + A3)", source: "python -X utf8 _ops/tests/run_all.py", tag: RUNNABLE}
  - {what: "گیتِ پول بسته الان", value: "require(50 AUD)=deny(live_gate: LIVE_ENABLED off)؛ money_gate(50)=deny؛ human_gate_aud=20 از SoT", source: "python -c capability_gate.require/money_gate.check", tag: RUNNABLE}
traps_hit:
  - {trap: "cp1252 (باز)", fix: "python -X utf8"}
invariants_touched: >
  fail-closed سرتاسر (هر شرطِ غایب = بسته). «خودگزارشیِ ایجنت هرگز معتبر نیست» encode شد (فقط approved/sent
  از کانالِ مستقل). calendar ≠ capability. هیچ مسیرِ پولِ واقعی باز نشد. تک-دروازهٔ effector = require()
  (هم live هم money). opslib.live_gate_open (گیتِ فعال‌سازیِ لوپِ debate/replication، تاریخ+پرچم) عمداً
  دست‌نخورده ماند — نگرانیِ جداست؛ یکی‌سازیِ اختیاری در آینده. budget_gate/budgets.yaml دست‌نخورده.
open_for_next: >
  وصلِ Telegram (قدمِ جدا و human-gated): adapterِ ApprovalChannel که core.db را می‌خواند + tokenِ botِ راز فقط
  از env در زمانِ اجرا (هرگز commit/hardcode). سپس ساختِ LIVE-ENABLED فقط توسط انسان. · Track B: attribution.py +
  reconcile.py → اولین دلارِ paper-CONFIRMED. · دو پرچمِ runtime (CAPABILITY-OK/LIVE-ENABLED در _ops/state)
  کاندیدِ gitignore کنارِ soma (open-decision #8 / C6).
human_verdicts_open: >
  وصلِ Telegram (زمان + credential دستِ انسان). · gitignore دو پرچمِ نو (C6/#8). · فرمت/مسیرِ CSVِ reconcile (#5).
```
