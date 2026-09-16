---
type: prompt
status: ready
target: "Claude Code (Windows، اجرا در F:\\backup)"
depends-on: "[[01 - Dashboard/HANDOFF]] · [[00 - Inbox/2026-07-06 1821 STATE-MAP — چهار جریان موازی و آشتی با طرح قبلی]]"
tags: [codebase, engineering, multi-agent, build, test]
created: 2026-07-06
updated: 2026-07-06
language: persian
---

# پرامپت مادر — مهندسی کامل کدبیس vault (max-load، چندایجنتی)

> برای Claude Code روی ویندوز، cwd = `F:\backup`. کل پرامپت زیر را کپی‌پیست کن.

```text
تو مهندس ارشد ساخت (Build Engineer) این vault هستی. مأموریت: یک پاس کاملِ باحوصله روی
«تمام» سطوح مهندسی مستقل و مرتبط این پوشه — چک، تکمیل، ساخت، تست — با حداکثر موازی‌سازی
(subagentهای Task tool) و استفادهٔ فعال از پلاگین‌ها/skillهای نصب‌شده. هیچ عجله‌ای نیست؛
کیفیت > سرعت. هر ادعای «درست شد» باید تستِ اثبات‌کننده داشته باشد وگرنه [UNVERIFIED] تگ بخورد.

## ۰) اول بخوان (به همین ترتیب، بعد شروع کن)
1. `CLAUDE.md` (ریشه) و `.agentignore`
2. `01 - Dashboard/HANDOFF.md` — فقط بلوک‌های جلسات ۲۰ (د/ج/ب) و ۱۷–۱۹
3. `00 - Inbox/2026-07-06 1821 STATE-MAP….md` — جدول تعارض‌ها (§۴)
4. قبل از دست‌زدن به هر پروژه: PROJECT.md همان پروژه
5. `06 - Architecture Maps/Property Schema.md` — هر نوت جدید فقط با کلیدها/typeهای مجاز

## ۱) قواعد سخت (نقض هرکدام = توقف همان خط و flag)
- مسیرهای `.agentignore` را هرگز نخوان/ننویس/echo نکن: `_code/`، `_Archive/`، `_Duplicates/`
  (فقط مقصد mv)، `secrets-export/`، و الگوهای `*.env`، `*.env.*`، `*key*`، `*seed*`، `*wallet*`،
  `*secret*`، `*.pem`. محتوای `.git` را هم مستقیم نخوان — فقط از CLI گیت استفاده کن (مجاز، §۲).
- هیچ call خارجی LLM/API نزن؛ هیچ فایل env را باز نکن؛ تست‌ها فقط آفلاین/mock (الگوی موجود:
  genome_selftest با gateway/memory فیک). راه‌اندازی زندهٔ ربات‌ها کار مالک است.
- پروژهٔ «اونلی فنز» فقط با کد «Project-F» ارجاع می‌شود؛ صفر echo هویت/محتوا خارج از پوشه‌اش؛
  دیتای Project-F هرگز به هیچ سرویس بیرونی (مخصوصاً Fugu) نمی‌رود؛ ژنومش config-only و قفل می‌ماند.
- `07 - Knowledge/genome-system/genome/` read-only است (invariant core). هر نیاز به تغییرش را
  فقط به‌شکل رویداد PROPOSAL با kill_criteria در ledger خودش پیشنهاد بده؛ اعمال نکن.
- charterها برای ایجنت immutable؛ قواعد قفل‌شده را overwrite نکن — تضاد را با تگ منبع flag کن.
- آیتم‌های فقط‌مالک را شبیه‌سازی/جعل نکن: `genome_guard --init`، مقصد بک‌اپ off-site، کلید واقعی،
  `owner_confirmed` در gates.yaml، Task Scheduler، هر پرداخت/اشتراک.
- کلید فرانت‌متر نو اختراع نکن (تعارض #۸ فعال است)؛ ۴۰ خطای backlog قدیمی validator را دست نزن —
  فقط فایل‌های خودت باید صفر خطا باشند.
- kill-switch: اگر فایل `04 - Architect System/STOP` وجود داشت، فقط گزارش بنویس و بایست.

## ۲) فاز ۰ — substrate (اول از همه، سریال)
verdict قبلی مالک برای git init داده شده («تو بزن»، جلسه ۱۵)؛ فقط سندباکس خرابش می‌کرد — تو
روی fs واقعی ویندوزی، پس مجازی:
- vault: `git -C "F:\backup" config --unset core.worktree` → `git status` سالم؟ اگر repo
  بی‌نجات بود: `.git` خراب → mv به `_Duplicates/broken-dot-git-<date>` و `git init` + کامیت
  snapshot (طبق runbook: `00 - Inbox/build-proposals/04-git-init-runbook-2026-07-05`).
  `.gitignore` موجود (قرنطینهٔ PHASE-0A و `_launchpad`) دست‌نخورده بماند.
- `07 - Knowledge/genome-system/.git` مرده‌زاد است (صفر object، config.lock جامانده) → mv به
  `_Duplicates/` و `git init` + کامیت اولیه داخل خودش.
- چون `_launchpad` عمداً gitignore است (env محلی دارد): قبل از هر ویرایش آن‌جا یک
  `tar.gz` از `_launchpad/second-brain-live/` بدون فایل‌های env/secret در
  `07 - Knowledge/_backups/` بساز (rollback تنها همین است).
- از این‌جا به بعد: پایان هر فاز = `git commit -m "agent-checkpoint: <فاز>"`.

## ۳) جبهه‌های مهندسی (بعد از فاز ۰، حداکثر موازی — هر جبهه یک subagent مالکِ فایل‌های خودش؛
##    هیچ دو ایجنتی روی یک فایل نمی‌نویسند؛ هماهنگی فقط از راه `_ops/SESSION-REPORT-<date>.md`)

### جبههٔ A — `_launchpad/second-brain-live/` (مغز دوم v2؛ سنگین‌ترین)
1. `python run_tests.py` (سوئیت ۴۷تایی — روی ویندوز کامل اجرا می‌شود) + `python genome_selftest.py`؛
   هر قرمز را ریشه‌یابی و رفع کن (۱ قرمز شناختهٔ قبلی = stale-copy تست فاز۲، نه منطق).
2. تکمیل «فاز ۵» معوق: README غیرفنی فارسی + smoke نهایی آفلاین (import-level همهٔ ماژول‌ها،
   py_compile همه‌جا، بوت خشک بدون شبکه با DictSecrets فیک).
3. 🔴 مهاجرت DeepSeek قبل از 2026-07-24: aliasهای `deepseek-chat`/`deepseek-reasoner` بازنشسته
   می‌شوند. بدون بازکردن env: default/fallbackهای کد → `deepseek-v4-flash`؛ هشدار بوت اگر مقدار
   env هنوز alias کهنه بود (چک runtime مجاز است، خواندن فایل نه)؛ فیلد پیش‌فرض setup_wizard هم.
4. رگرسیون درس‌های قبلی: همهٔ `.bat`ها CRLF + بدون `(`/`)` در echo داخل بلوک if؛ قفل تک‌نمونهٔ
   8768 (`SO_EXCLUSIVEADDRUSE`)؛ گارد پورت 8770 در wizard؛ error-handler تلگرام (نمونه‌گیری Conflict).
5. `/api/genomes` و `/genomes` و کارت‌های RTL: تست offline با رجیستری ۴ ژنوم (قفل Project-F=
   status_only/sensitive/بدون engine باید در تست assert شود).
6. evolution/: مسیر TTL ۳۰روزهٔ fail-closed + kill سه‌سطحی + گارد privacy (رکن‌های sensitive
   هرگز به tier بیرونی) — برای هرکدام تست بنویس اگر ندارد.

### جبههٔ B — `07 - Knowledge/genome-system/` (v0.4.0)
1. کل تست‌سوئیت خودش را اجرا کن؛ سبز نگه دار.
2. تست‌های تکمیلی برای ادعاهای v0.4.0: ledger hash-chain زیر همزمانی (append قفل‌دار، تحمل خط
   نیمه‌نوشته)، tamper-detect در حلقه، boundary test ژنوم، «دکتر خودش را داوری نمی‌کند».
3. فقط `agents/` `perception/` `ledger/` قابل ویرایش‌اند؛ `genome/` و `plan.yaml` نه (plan-gated
   loop زنده است — برخورد نوشتاری نکن). سه milestone فقط‌مالک را لیست کن، انجام نده.

### جبههٔ C — `04 - Architect System/scripts/` + ساخت budget_gate v2
1. اسکریپت‌های موجود (budget_gate/genome_guard/governor_shadow/dashboard_doctor) را py_compile +
   تست واحد. semantics فعلی حفظ شود: fail-closed، قفل با steal بعد ۳۰s، rollover.
2. **ساخت v2 (آیتم مصوب جلسه ۲۰د):** `budget_gate.py` بخوانَد از
   `_ops/budget/budgets.yaml` (تک‌منبع؛ `cap_monthly: 30 AUD` = verdict مالک) به‌جای هاردکد
   `CEIL_*`؛ + per-organ buckets (الان پارامتر `agent` در حسابداری بی‌اثر است):
   floor/quota هر ارگان از بخش `projects` همان yaml؛ daily = سقف burst نه نرخ پایدار؛
   backward-compatible (بدون yaml → همان رفتار فعلی). تست: همزمانی ۲۰موازی، rollover،
   per-organ isolation، fail-closed وقتی yaml خراب است.
3. `governor_shadow.py`: فقط اضافه‌شدن خواندن budgets.yaml به گزارشش (shadow، صفر اعمال).
4. هر دو validator (`validate_frontmatter.py` + `find_broken_links.py`) آخرِ کار سبز برای
   فایل‌های لمس‌شدهٔ خودت.

### جبههٔ D — عرضی (cross-cutting، ایجنت جدا)
- اسکن secret با `scripts/gitleaks.toml` روی کل تغییرات خودت (گزارش-فقط)؛ اگر چیزی پیدا شد:
  توقف همان خط + flag، نه فیکس خودسر.
- ممیزی CRLF همهٔ `.bat`/`.ps1` vault؛ py_compile سراسری فایل‌های py خارج از مسیرهای ممنوع؛
  گزارش importهای مرده/وابستگی‌های غایب (requirements)؛ هیچ refactor سلیقه‌ای.

## ۴) روش چندایجنتی (مکزیمم لود، ولی منضبط)
- الگو: ۱ ایجنت inventory (read-only، نقشهٔ فایل/تست هر جبهه) → ۴ ایجنت جبهه (A/B/C/D موازی)
  → روی هر diff مهم یک ایجنت بازبین خصمانه (skill های code-review/debug/testing-strategy/
  security-review اگر نصب‌اند — اول `/plugins` و skillهای در دسترس را لیست کن و فعالانه به‌کار بگیر)
  → ایجنت integrator (اجرای مجدد کل تست‌ها + کامیت‌ها).
- قانون مالکیت: هر فایل فقط مال یک ایجنت در هر لحظه؛ ادعای هر ایجنت بدون خروجی تست پذیرفته نشود.
- اگر ابزار/پلاگینی وسط کار لازم شد که نیست، جایگزین محلی بساز و در گزارش [OPEN] کن.

## ۵) Definition of Done + گزارش پایانی
- همهٔ تست‌ها سبز (عدد بده: قبل/بعد)؛ کامیت per-phase؛ صفر خطای validator از فایل‌های خودت؛
  صفر یافتهٔ secret در تغییرات.
- گزارش نهایی: `00 - Inbox/2026-07-06 CODE-ENGINEERING-REPORT.md` با فرانت‌متر دقیقاً:
  type: report / status: draft / created_by: agent / tags + created/updated — هیچ کلید دیگر.
  محتوا: per-جبهه (چه سبز بود، چه شکست، چه ساختی، چه [UNVERIFIED] ماند، چه فقط‌مالک است) +
  جدول کامیت‌ها.
- بلوک کوتاه به بالای `01 - Dashboard/HANDOFF.md` (فقط wikilink، بدون secret) + Active Context
  هر PROJECT.md لمس‌شده.
- صادق باش: «قابلیت ادعاشده ولی مرده» بدترین خروجی این vault بوده — پیدا کردی، جار بزن.
```

## یادداشت ثبت (خارج از پرامپت)
- مبنای مجوز git: verdict «تو بزن» جلسه ۱۵ + قاعدهٔ جلسه ۱۷ (commit فقط Windows-side) — Claude Code ویندوزی است، پس بلاکر سندباکس موضوعیت ندارد.
- هزینهٔ اجرا: صفر call خارجی — سازگار با سقف AU$30 (`_ops/budget/budgets.yaml`).
