---
type: architecture
status: draft
tags: [replication, vault, architect, governance]
created: 2026-07-06
updated: 2026-07-06
language: bilingual
---

# VAULT REPLICATION BLUEPRINT — کپی دقیق قابلیت‌ها و featureهای سیستم

> این سند + پوشه `seed/` + اسکریپت `scaffold.py` = هر چیزی که برای بازسازی این سیستم در یک vault جدید لازم است.
> **شامل هیچ دیتای شخصی، secret، یا کدی از `_code` نیست** — فقط معماری، قوانین، قراردادها و اسکلت‌ها.
> منابع: `_PROJECT_INSTRUCTIONS.md` v2.0 · `SYSTEM-BLUEPRINT-v2.md` · `TWO-BRAIN-CONTROL-BLUEPRINT.md` · `AGENT_REGISTRY.md` · `SYSTEM_MAP.md` · `Property Schema.md`

---

## ۰. سیستم در یک پاراگراف

یک **vault ابسیدینِ agent-first** برای یک اپراتور تک‌نفره: انسان (رئیس کل) verdict می‌دهد، ایجنت‌ها می‌خوانند/تشخیص می‌دهند/پیشنهاد می‌کنند. روی vault یک **لایه مادر (architect)** سوار است — سیستم agentic همیشه‌روشن با کنترل از Telegram — و یک **ناوگان scout زمان‌بندی‌شده** که تحقیق و خودبهبودی propose-only انجام می‌دهد. سه مکانیزم ایمنی روی همه‌چیز حاکم است: **HITL (human-in-the-loop)**، **Kill-switch**، **§Security Gate**.

---

## ۱. لایه ۰ — ساختار فیزیکی (folder contract)

```
00 - Inbox/                ورودی تازه + AGENT_QUESTIONS.md + scout-digests/ + build-proposals/
01 - Dashboard/            Home.md · HANDOFF.md · Brain.md · فایل‌های .base · پنل‌های .html
02 - Life OS/              برنامه زندگی، Weekly Review
03 - Projects/             هر پروژه: PROJECT.md + لاگ تلگرام + اسناد
04 - Architect System/     لایه مادر: architect/ (01-Project…04-Docs, _meta, _code) + scripts/
05 - Agents/               شناسنامه ایجنت‌ها + AGENT_REGISTRY + RATIFIED-TASKS
06 - Architecture Maps/    ECOSYSTEM · SYSTEM_MAP · Property Schema
07 - Knowledge/            دانش ماندگار موضوعی
08 - Assets/Photos/        عکس/پیوست (<منبع-سال>)
09 - People/               نوت اشخاص
10 - Telegram processing/  Raw/YYYY-MM-DD.md + SOP + ROUTING
_Archive/  _Duplicates/    فقط مقصد انتقال — هرگز باز نمی‌شوند
_Templates/                ۶ قالب: project/knowledge/log/person/agent/handoff
_memory/                   حافظه مغز زنده: HEARTBEAT · EXPERIENCE-LEDGER · بلوپرینت‌ها
.claude/                   settings.json (deny) + rules/ (قواعد per-path)
.agentignore               مسیرهای ممنوع ماشین‌خوان
```

قواعد شماره‌گذاری: 00/01 رزرو سیستمی؛ شماره‌ها هرگز بازیافت نمی‌شوند؛ بخش جدید فقط به انتها (11، 12، …).

---

## ۲. لایه ۱ — قانون اساسی (governance core)

فایل `_PROJECT_INSTRUCTIONS.md` — برای ایجنت‌ها **فقط‌خواندنی**. قواعد به ترتیب اولویت:

1. **هرگز حذف نکن؛ فقط منتقل کن** (تکراری → `_Duplicates`؛ بازنشسته → `_Archive`).
2. **دست نزدن به `.git`، `_code`، secretها** — هم متنی (§۱۰) هم ماشین‌خوان (`.agentignore`) هم enforced (`.claude/settings.json` deny).
3. **Inbox-first:** هر ورودی اول به `00 - Inbox` یا `10 - Telegram processing`، بعد طبق درخت تصمیم مسیریابی.
4. **قاعده راه را بست → توقف + سوال در `AGENT_QUESTIONS.md`** — هرگز دور زدن.
5. **batch > ~۵ فایل → اول `agent-checkpoint:` commit** (برگشت‌پذیری یک‌فرمانه).

مکانیزم‌های کلیدی:

- **درخت تصمیم Inbox:** (a) کار پروژه شناخته‌شده → Next actions همان PROJECT.md · (b) ونچر جدید → اسکلت از template · (c) دانش بازمصرف → 07 با `created_by: agent` + ≥۲ منبع · (d) شخص → 09 · (e) مبهم → `status: idea` + سوال.
- **نام‌گذاری:** capture ماشینی = `YYYY-MM-DD HHmm <slug>.md` (تصادم ساختاراً غیرممکن)؛ ممنوع: « - Copy» و «(1)»؛ نسخه جدید = suffix تاریخ یا v2.
- **dedup:** فقط byte-identical تکراری است؛ پیشگیری تلگرام با grep روی `message_id` (پایپ‌لاین idempotent).
- **محتوای ایجنت‌ساخته:** append-only به نوت انسانی؛ هرگز بازنویسی مخرب؛ synthesis با `created_by: agent + sources ≥۲`.
- **خود-نگهداری قانون:** وقتی ایجنتی اشتباهی را تکرار کرد یک خط قاعده اضافه می‌شود؛ قواعد همیشه-رعایت‌شده حذف؛ سقف ~۲۰۰ خط.

---

## ۳. لایه ۲ — زبان داده (Property Schema)

فایل `06 - Architecture Maps/Property Schema.md` = تک‌منبع حقیقت. **هر کلید خارج از schema خطاست؛ ایجنت هرگز کلید اختراع نمی‌کند** (کلید جدید = ویرایش schema + `.obsidian/types.json` با تأیید مالک).

- هسته هر نوت: `type / project / status / tags / created / updated`.
- `status`: فقط `idea|active|paused|done|archived|inbox|draft|ready|superseded` (حروف کوچک — Bases حساس است).
- typeهای مهم و کلیدهای اضافی‌شان: `project` (kind: project|area، autonomy_level)، `agent` (model/trigger/code)، `log` (append-only + متادیتای dedup)، `proposal` (چرخه draft→ready→پذیرش، superseded_by)، `handoff` (فقط updated — مصرفی).
- کلیدهای رابطه: `parent / aligns_to / extends / supersedes / superseded_by`؛ عملیاتی: `depends-on / closes / target / audits / result / salience`.
- گارد معرفت‌شناختی: نوت‌های حوزه هیپنوتیزم `epistemic_status: peer-reviewed|speculative|fiction-canon` اجباری — **fiction-canon هرگز evidence تصمیم بیزنسی نیست.**

هر نوت جدید فقط از `_Templates/` ساخته می‌شود (۶ قالب در seed کپی شده‌اند).

---

## ۴. لایه ۳ — حافظه، handoff، مغز زنده

- هر `PROJECT.md` دو بخش **فرار** دارد: `## Active Context` (تمرکز فعلی / تغییرات اخیر / ۳ قدم بعدی / تصمیم‌های باز) و `## Progress` — پایان هر جلسه تازه می‌شوند.
- `01 - Dashboard/HANDOFF.md` = تنها نوت overwrite-مجاز؛ فقط wikilink، نه کپی محتوا، نه secret. شروع هر جلسه از همین‌جا.
- استثناهای overwrite ثبت‌شده: `Brain.md` (نبض مغز، بازنویسی هر ۳ ساعت) و `_memory/HEARTBEAT.md` (هر تسک فقط سطر خودش).
- `_memory/EXPERIENCE-LEDGER.md` = **append-only ledger** درس‌ها/verdictها (پایه چرخه خودبهبودی).
- عبارت جادویی «حافظه را به‌روز کن» = بازبینی Active Context/Progress همه پروژه‌های active.
- نوت‌های ایندکس < ۲۰۰ خط؛ سرریز → نوت خواهر.

---

## ۵. لایه ۴ — امنیت (defense in depth)

| لایه | مکانیزم |
|---|---|
| متن | §۱۰ قانون اساسی: secret هرگز در چت/نوت/HANDOFF/لاگ |
| ماشین‌خوان | `.agentignore`: `.git/`، `**/_code/`، `_Archive/`، `_Duplicates/`، `secrets-export/`، الگوها: `*.env*`، `*wallet*`، `*seed*`، `*key*`، `*.pem`، `*secret*` |
| enforced | `.claude/settings.json`: deny روی rm/del/Remove-Item، Write/Edit روی .git و _code و _Archive، Read روی الگوهای secret |
| per-path | `.claude/rules/*.md`: قواعد جدا برای architect / projects / telegram |
| فرآیندی | **§Security Gate**: تا وقتی حتی یک CRITICAL در `ROTATION_CHECKLIST.md` باز است → autonomy مؤثر همه ایجنت‌ها = read-only، فارغ از سطح ثبت‌شده |
| repo | gitleaks (config در `scripts/gitleaks.toml`) در CI؛ کلید رمزنگاری بکاپ (age) هرگز روی همان ماشین |

اصل طلایی: **Constraints خارج از context مدل** (allowlist/deny در config و kernel)، نه داخل prompt (P3).

---

## ۶. لایه ۵ — ARCHITECT (لایه مادر) — عمیق

### ۶.۱ هویت و pipeline

`04 - Architect System/architect/` = مغز. پوشه‌بندی pipeline:
`01-Project` (BLUEPRINT نسخه‌دار، DECISIONS، GAPS، BACKLOG، CHANGELOG، پرامپت‌های PROMPT-A/B) → `02-Research` (نوت‌های تحقیق شماره‌دار) → `03-Exports` → `04-Docs` (آدیت‌ها، schemaها) + `_meta` (inventory، manifest حذف) + `_code` (runtime — برای ایجنت‌ها ممنوع).

دو نقش: **محقق/طراح** (خودبهبودی سطح prompt/skill — هرگز weight مدل) و **کنترل‌پلین** (بازرسی همه tenantها از Telegram).

### ۶.۲ اصول غیرقابل مذاکره (P1–P11)

P1 human-gate روی هر action برگشت‌ناپذیر؛ `final = max(autonomy_floor, safety_result)` · P2 **fail-closed**: kill-switch قبل از هر action و هر round حلقه؛ timeout=DENY · P3 constraints خارج از prompt · P4 هر self-edit = git commit + eval gate + rollback <۵ دقیقه · P5 isolation per-tenant (schema + credential جدا) · P6 measure-first · P7 **بودجه پیچیدگی: فقط ۵ جزء core همیشه‌روشن** · P8 «در شک: سکوت» · P9 دیوار داده شخصی · P10 هیچ private key روی ماشین agentic؛ signer off-box · P11 **هیچ LLM در مسیر فرمان** — نگاشت متن→فرمان rule-based (regex router).

### ۶.۳ پنج کامپوننت core + دو satellite

1. **Telegram Bot** — تنها رابط انسان↔سیستم. `owner_only` (غریبه=سکوت)؛ Intent-Router rule-based؛ **step-up passphrase** برای فرمان‌های مخرب (deploy/kill/budget)؛ `/halt /resume /status /verdict`.
2. **Brain + Router** — rule-based: ساده→Haiku، متوسط→Sonnet، پیچیده→Opus (هدف 70/25/5)؛ fallback زنجیره‌ای provider.
3. **Research Engine** — پایپ‌لاین search → source_quality (۰–۱۵) → uncertainty → synthesis → constitution gate؛ **دو checkpoint میانی** ضد error-compounding.
4. **Memory** — سه‌لایه (working/episodic/semantic → هدف CoALA + pgvector)؛ هر رکورد فیلد `origin: user|web|self_generated`؛ محتوای وب در بازیابی هم داخل `<external_data>` (دفاع persistence-poisoning).
5. **Safety Kernel** — constitution + kill-switch + PatchManager (سطح ۳ عمداً NotImplementedError) + جدول `action_policy(tenant, domain, max_amount, requires_approval, hard_stop)`.

Satellites (phase-gated): **Self-Improvement Lab** و **Tenant Adapters**.

### ۶.۴ قرارداد Tenant Adapter

هر پروژه در `projects.yaml`: `name / repo / autonomy_floor / budget_subcap / adapter`. Adapter فقط interface خواندنی: `status() / logs(n) / report(period) / audit()` — **با credential جداگانه read-only (enforced، نه قراردادی)**. هر write فقط از deploy pipeline گیت‌شده. Crypto/Mining: فقط داده عمومی؛ کلید هیچ‌جا.

### ۶.۵ نردبان استقلال (Autonomy Ladder)

`L0 گزارش → L1 پیشنهاد → L2 bounded-auto (فقط whitelist منشور) → L3 مشتق idempotent`. ورود به L2/L3 فقط پشت Gate + git. **لیست سیاه همیشه human-only:** تغییر charter، secret، پول، پیام خارجی، تغییر git. سطوح اکشن: `AUTONOMOUS / INFORM / APPROVE_FIRST / HARD_STOP` (مالی = HARD_STOP).

### ۶.۶ Kill-switch (سه‌سطحی، fail-closed)

منبع حقیقت = flag `halted` در DB + mirror فایل `STOP`. چک می‌شود: اول هر handler، هر call مدل، **ابتدای هر round حلقه خودبهبودی، قبل از هر git commit**. تست ماهانه. timeout = DENY.

### ۶.۷ حلقه خودبهبودی (gated)

- گیت سه‌شرطی کمّی: regression روی anchor set (۵۰–۱۰۰ case) ≤۵٪ + بهبود روی held-out **unseen** + صفر failure category جدید.
- pass → git commit (هرگز main)؛ fail → rejected-buffer؛ توقف: max ۴ round یا دو دور بهبود <۰.۵.
- Judge بین‌خانواده‌ای (مدل خانواده دیگر قضاوت می‌کند)؛ kappa ≥ 0.7.
- شروع فقط با ≥۵۰ trajectory واقعی (cold-start rule)؛ هیچ دور LIVE بدون held-out واقعی.
- ~۲۵٪ anchor set هر فصل refresh (ضد Goodhart/overfit).
- مرز مطلق: policy gate / kill-switch / secrets / مسیر مالی دست‌نخوردنی.

### ۶.۸ مدل بودجه (دو mode، خارج از prompt)

| پارامتر | Normal | Growth (فرمان صریح + passphrase) |
|---|---|---|
| هر run | $0.50 | $1 |
| روزانه | $2 (alert در ۵۰٪/۸۰٪) | $10 |
| ماهانه | $60 hard-stop → halt + پیام | $300 |
| حلقه خودبهبودی | ۰ (خاموش) | $2/روز |

فلسفه: سناریوی سنگین در Normal **عمداً fail می‌شود** — رشد مصرف = تصمیم آگاهانه انسان، نه خزش خاموش.

### ۶.۹ ارزیابی و observability

eval سه‌لایه + چهار span trace؛ sampling تا ۲۰٪ runها + ۱۰۰٪ production failureها؛ drift هفتگی ≥۵٪ → investigate؛ judge سبک روی خروجی روزمره (نه فقط مالی)؛ monitoring: Uptime Kuma + Dozzle + alert تلگرام + گزارش هفتگی هزینه.

### ۶.۱۰ چرخه سند و red-team

BLUEPRINT نسخه‌دار (v1→v2→v3-proposal)؛ هر نسخه با **PROMPT-B (red-team)** نمره می‌گیرد و نسخه بعد یافته‌ها را اعمال می‌کند؛ v قبلی دست‌نخورده می‌ماند. قانون حل تناقض: **کد واقعی > سند جدیدتر > سند قدیمی‌تر**. کنار آن: `DECISIONS.md` (D-xx)، `GAPS.md` (G-xx)، `BACKLOG.md` (BACKLOG-xx)، `CHANGELOG.md` — هر ادعا/حفره/تصمیم شناسه‌دار و قابل‌ارجاع.

### ۶.۱۱ مدل دو مغز (کنترل‌لوپ مشترک)

```
① ادراک (SYSTEM-STATE) → ② تشخیص (Doctor) → ③ پیشنهاد (propose-only)
→ ④ verdict (انسان) → ⑤ اعمال (فقط whitelist) → ⑥ سنجش (fitness+ledger) → ①
```

- **مغز انسانی:** تابع برازندگی، invariantها، §Gate و charter (human-only)، بودجه، kill-switch — کم‌فرکانس، اقتدار نهایی.
- **مغز دکتر (Evolutionary Doctor):** ۳ ستون — نگهبان سلامت (قطعی، صفر-LLM؛ `dashboard_doctor.py`)، کاشف جهش (Mutation Ledger)، حلقه فکری — پرفرکانس، اقتدار محدود.
- کابین مشترک = artifact زنده (dashboard) که هر دو مغز هم‌زمان می‌بینند و عمل می‌کنند.
- متریک: شاخص استقلال (>۵۰٪ درس کم‌ریسک applied بدون لمس انسان در ۴ هفته) · صفر نقض invariant · نسبت promote÷revert.

---

## ۷. لایه ۶ — ناوگان ایجنت‌ها

### ۷.۱ رجیستری (`05 - Agents/AGENT_REGISTRY.md`)

هر ایجنت یک ردیف: `دامنه / هدف / autonomy هدف / می‌خواند / می‌نویسد / ممنوع`. **هر ردیف وارث §Security Gate است.** الگوی autonomy: تقریباً همه propose-only؛ فقط watcher مالی execute-with-verdict → bounded-auto پشت گیت.

### ۷.۲ ناوگان scout (تسک‌های زمان‌بندی‌شده)

- اسکات‌های موضوعی روزانه (هر دامنه یک cron، پوشش ~۲۴ساعته) — همه propose-only، خروجی فقط در `00 - Inbox/scout-digests/`.
- لایه ارکستراسیون: `mycelial-consolidator` (سنتز شبانه + evaporation)، `fleet-selection` (retire/spawn هفتگی)، `brain-pulse`، `system-dashboard`، `brain-focus-board`، `experience-review` (بازوی verdict هفتگی).
- هر اسکات گارد ویژه دامنه دارد (مثلاً: crypto بدون ترید؛ health بدون توصیه پزشکی؛ security هرگز secret واقعی تست نکند).

### ۷.۳ درس bootstrap (حیاتی برای replica)

وقتی همه تسک‌ها هم‌زمان بمیرند، هیچ تسکی نمی‌ماند که خودترمیمی را اجرا کند. دو مهار:
1. **`RATIFIED-TASKS.md`** = متن کامل پرامپت‌ها داخل vault (تک‌منبع بازسازی؛ restore فقط تسک‌های ratified — بقیه فقط با verdict).
2. چک تطبیق زمان‌بند ↔ جدول ratified در شروع هر جلسه تعاملی.
قاعده: **منبع حقیقت fleet = خروجی زنده زمان‌بند؛ جدول‌ها سندِ نیت‌اند، نه اثبات اجرا.**

### ۷.۴ قواعد سراسری fleet

خطای خاموش = باگ درجه‌یک · هر اکشن = ورودی Anchor Ledger (append-only، hash-chain برای مسیر مالی/deploy) · timeout تأیید = DENY · بودجه جمعی hard-stop.

---

## ۸. لایه ۷ — Dashboard

`Home.md` (جهت‌یابی، MOC) · `HANDOFF.md` (وضعیت جلسه‌به‌جلسه) · `Brain.md` (نبض زنده) · فایل‌های `.base` (viewهای Obsidian Bases روی frontmatter — به همین دلیل schema سخت‌گیر است) · پنل‌های `.html` (artifactهای زنده: SYSTEM-DASHBOARD، BRAIN-FOCUS-BOARD، CONTROL-PANEL).

---

## ۹. لایه ۸ — اعتبارسنجی (پوشه `scripts/` — در seed کپی شده)

> «ایجنت تصمیم می‌گیرد، اسکریپت verify می‌کند.» هر دو dry-run.

- `validate_frontmatter.py` — کلیدهای هسته، مقادیر بسته status/type، تاریخ ISO، کلید خارج از schema → exit≠0.
- `find_broken_links.py` — همه wikilinkها به سبک resolution ابسیدین.
- قاعده: بعد از هر ویرایش دسته‌ای + شروع مرور هفتگی؛ جلسه وقتی «تمام» است که هر دو پاس شوند.
- `dashboard_doctor.py` (ستون ۱ دکتر — قطعی، صفر-LLM) و `gitleaks.toml` مکمل‌اند.

---

## ۱۰. ترتیب بازسازی (پیشنهادی — هر فاز با verdict وارد بعدی می‌شود)

1. **فاز ۰ — اسکلت:** `python scaffold.py <target>` → ساختار + قانون اساسی + schema + templates + validators.
2. **فاز ۱ — حاکمیت (human-only):** پر کردن جدول پروژه‌ها در `_PROJECT_INSTRUCTIONS.md`؛ ساخت `ROTATION_CHECKLIST.md` واقعی؛ `git init` + اولین commit؛ تعیین وضعیت §Gate.
3. **فاز ۲ — داده:** ساخت PROJECT.md هر پروژه از template؛ مهاجرت ورودی‌ها Inbox-first؛ اجرای هر دو validator تا سبز.
4. **فاز ۳ — dashboard و حافظه:** Home/HANDOFF/Brain + `_memory` (HEARTBEAT، EXPERIENCE-LEDGER).
5. **فاز ۴ — fleet:** ثبت اسکات‌ها در AGENT_REGISTRY + RATIFIED-TASKS؛ فقط propose-only؛ خروجی فقط scout-digests.
6. **فاز ۵ — runtime architect:** طبق SYSTEM-BLUEPRINT (بیرون از scope این kit — کد در `_code` است و عمداً کپی نشده).

---

*ساخته‌شده 2026-07-06 توسط ایجنت (propose-only). این kit سند نیت است؛ اجرا و verdict با آری.*
