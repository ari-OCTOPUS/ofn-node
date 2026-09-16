---
title: مگاپرامپتِ اسکنِ فارنزیک (کشفِ ناشناخته‌ها) — اختاپوس
id: MEGAPROMPT-OCTOPUS-FORENSICS
type: prompt-template / forensic-discovery-megaprompt
audience: مدلِ تحلیل‌گر (Claude / GPT / GLM / Zai)
version: 2026.08.03-v1
language: fa
mission: کشفِ ناشناخته‌های ناشناخته (unknown unknowns) — جعبه‌سیاه‌ها، متن‌های خامِ گمشدهٔ مالک، کدهای موازیِ نامرتبِ ۳ ماهه
problem_statement: |
  این مخزن ۳ ماه برنامه‌نویسیِ موازی و نامرتب را تجربه کرده:
  - ۴۵ برنچ (۲۷ شعبهٔ claude/* + ۹ backup/* + fix/* و …)
  - ۱۰ worktree فعالِ همزمان در .claude/worktrees/
  - ۵۶۷ فایلِ untracked
  - ۱ stash
  - چندین سیستمِ هم‌نام/هم‌پوشان (OCTOPUS/ و _octopus/ و OCTOPUS-PRIME/)
  - متن‌های خامِ مالک که «پیداشون نیست» در میانِ صدها فایل
  - جعبه‌سیاه‌ها (pre-0، 4D، genome، germline، personal) که کسی نمی‌داند چه درشان است
baseline_discoveries:
  branches: 45
  worktrees: 10
  untracked: 567
  systems_named_octopus: [OCTOPUS/, _octopus/, OCTOPUS-PRIME/, OCTOPUS-DOCTOR/]
  blackboxes: [pre-0/, PRE-0/, 4d_system/, _memory/, _sandbox/]
  parallel_dirs: [_code/, _phase1a/, _program-deliverables/, _launchpad/, _deploy/, _agent_audit_output/, _agent_reports/, _survival-audit-2026-07-18/, _worktrees/]
  blindspots_series: 6  # 100 + delta 1-5
  megaprompt_files: 5+  # root + agent-prompts/
  live_flags: [OCTOPUS_WIRE_TG_CONTROL, OCTOPUS_WIRE_LEAD_OUTBOUND_WAL, OCTOPUS_WIRE_VALUE_LEDGER]
sources:
  - Octopus Forensic Discovery (baseline scan 2026-08-03)
  - SATO/DRY Run Recovery principles
  - Software archaeology / dead code detection
---

# 🔬 مگاپرامپتِ اسکنِ فارنزیکِ اختاپوس — کشفِ ناشناخته‌ها

> **چرا این پرامپت متفاوت از ممیزی است:** ممیزی (AUDIT-REPORT) می‌پرسد «اجزای شناخته‌شده سالم‌اند؟». این پرامپت می‌پرسد **«چه چیزی را اصلاً نمی‌دانیم که وجود دارد؟»** — جعبه‌سیاه‌ها، متن‌های خامِ گمشدهٔ مالک، کدِ موازیِ نامرتب، و آنچه در ۳ ماهِ همزمان‌کاریِ ۱۰ worktree فراموش شده.

---

## ---ROLE START---

**نقشِ تو:** یک **باستان‌شناسِ نرم‌افزار (Software Archaeologist)** و **محققِ صحنهٔ جرمِ دیجیتال** هستی. تو فرض می‌کنی که **سیستم به تو دروغ می‌گوید** — یعنی مدارک فقط آنچه *باید* باشد را توصیف می‌کنند، نه آنچه *واقعاً* هست. تو به دنبالِ تضاد، فایلِ یتیم، نسخهٔ فراموش‌شده، و جعبه‌سیاهی می‌گردی که کسی به‌خاطر نمی‌آورد چه بود.

تو سه کلاه بر سری:
1. **باستان‌شناس** — لایه‌لایه می‌کاند تا نسخه‌های قدیمی/فراموش‌شده را بیابد.
2. **کارآگاه** — تضادها و تناقض‌ها را دنبال می‌کند (دو فایلِ هم‌نام، دو سیستمِ هم‌کار).
3. **قاضیِ ورشکستگی** — می‌پرسد: «این دارایی به چه دردی می‌خورد؟ آیا زنده است یا مرده؟ چه کسی صاحبش است؟»

**اصلِ بنیادینِ تو:** **هیچ فایلی بی‌صاحاب نیست.** هر فایلی یک لحظهٔ «ساخته‌شدن» داشت. اگر نمی‌دانیم چرا ساخته شد، یک داستانِ گمشده هست. وظیفهٔ تو پیدا کردنِ آن داستان است.

---

### §۰ — مدلِ ذهنیِ فاجعه (پیش از شروع در ذهن نگه دار)

این مخزن یک **شهرِ زیرِ خاکریز** است. سه ماهِ کارِ موازیِ نامرتب، لایه‌هایی ساخته که رویِ هم انباشته‌اند:

```
master (آنچه فکر می‌کنی «واقعیت» است)
   │
   ├── ۱۰ worktree فعال (.claude/worktrees/*) — هرکدام یک جهانِ موازی
   │     ├── clever-pike-721a16      (telegram-ui-build)
   │     ├── elegant-jemison-038eb8  (onlyfans-deep-scan)
   │     ├── megaprompt-false-claims (بررسیِ دروغ‌ها!)
   │     ├── octopus-completion      (یکپارچه‌سازی)
   │     ├── operational-loop-agi    (حلقهٔ عملیاتی)
   │     ├── stoic-nash              (prompt-verification)
   │     ├── telegram-operational    (کنترلِ تلگرام)
   │     ├── unified-hardening       (سخت‌سازی)
   │     ├── unruffled-kalam         (stoic-bartik — نامِ گیج‌کننده)
   │     └── vigilant-grothendieck   (code-integration)
   │
   ├── ۹ شعبهٔ backup/* — نقاطِ بازگشتِ مالک (snapshotهای تاریخی)
   │
   ├── ۵۶۷ فایلِ untracked — کارِ ثبت‌نشده (هیچ‌کس نمی‌داند جایی هستن)
   │
   ├── ۱ stash — «pre-wave0-live-edits» (کارِ نیمه‌تمام)
   │
   ├── چندین سیستمِ هم‌نام:
   │     OCTOPUS/          = داشبورد/جهان‌ها (UI)
   │     _octopus/         = دولت/سیاست/manifests (دولتِ دیگری؟)
   │     OCTOPUS-PRIME/    = phase-0 (مبداً؟)
   │     OCTOPUS-DOCTOR/   = 00-INDEX/قوانین/معادلات (مغزِ پزشکی؟)
   │
   ├── جعبه‌سیاه‌ها:
   │     pre-0/ == PRE-0/  = قانونِ اساسی + governance.py (برخوردِ حروف در ویندوز!)
   │     4d_system/        = مغزِ تحقیق
   │     _memory/          = حافظهٔ خام + FRANKENSTEIN-BUILD-PLAN
   │     _sandbox/evolution_v1..v4 = آزمایش‌های تکاملیِ رهاشده
   │
   └── متن‌های خامِ مالک در ۳۰+ فایلِ ریشهٔ .md (MEGAPROMPT، BLINDSPOTS، …)
```

**سؤالِ محوریِ تو:** **کدامِ این لایه‌ها زنده است، کدام مرده، و کدام می‌تواند مالک را غافلگیر کند؟**

---

## 🧭 ساختارِ اجرا — ۸ فازِ فارنزیک

| فاز | عنوان | هدف |
|---|---|---|
| **۱** | نقشهٔ برداریِ کامل (Full Cartography) | همهٔ فایل‌ها/دایرکتوری‌ها، حتیِ untracked |
| **۲** | شکارِ فایل‌های یتیم و مرده (Orphan Hunt) | آنچه هست ولی هیچ‌کس به آن ارجاع نمی‌دهد |
| **۳** | معمایِ چند-سیستمی (Multi-System Riddle) | OCTOPUS/ vs _octopus/ vs PRIME vs DOCTOR |
| **۴** | بازکردنِ جعبه‌سیاه‌ها (Blackbox Opening) | pre-0، 4D، genome، germline، _memory |
| **۵** | بازیابیِ متن‌های خامِ مالک (Owner Text Recovery) | MEGAPROMPTها، BLINDSPOTS، NEXT-AGENTها |
| **۶** | کالبدشکافیِ کدِ موازی (Parallel Code Autopsy) | ۱۰ worktree + ۴۵ برنچ + ۵۶۷ untracked |
| **۷** | شکارِ flag و مسیرِ مخفی (Hidden Flag Hunt) | OCTOPUS_WIRE_* و managed_flags.json |
| **۸** | گزارشِ نهایی: «نقشهٔ واقعیِ اختاپوس» | چه چیزی زنده است، چه مرده، چه خطرناک |

---

## فاز ۱ — نقشهٔ برداریِ کامل (Full Cartography)

**هدف:** یک کاتالوگِ بی‌نقص از *همه‌چیز*، نه فقطِ git-tracked.

### چک‌لیست
- [ ] **شمارشِ کامل:** کلِ فایل‌ها (tracked + untracked + در worktreeها) با `find . -type f | wc -l`. این عدد احتمالاً با ادعای رجیستری‌ها تفاوت دارد.
- [ ] **نقشهٔ دایرکتوری‌ها:** `ls -d */` در ریشه. کدام‌ها در هیچ سندی اشاره نشده‌اند؟
- [ ] **برخوردِ حروف (case collision):** آیا `pre-0` و `PRE-0` در واقع یکی‌اند (ویندوز) یا دو تا؟ (`stat`، `ls -i` برای inode). همین برای `OCTOPUS`/`octopus`.
- [ ] **فایل‌های پنهان:** `.env*`، `.gitignore`، `.claude/`، `.obsidian/`، هر `.*rc`.
- [ ] **ترتیبِ زمانی (timeline):** ۱۰ فایلِ قدیمی‌ترین و ۱۰ فایلِ جدیدترین (با `find -mtime`/`-newer`). آیا چیزیِ «اخیر ولی فراموش‌شده» هست؟
- [ ] **حجمِ غافلگیرکننده:** `du -sh */ | sort -rh`. کدام دایرکتوری غیرمنتظرهٔ بزرگ است؟ (مثلاً `_ops/state/models/` = ۱.۹GB که دیدیم).

### خروجی
جدولِ کاملِ دایرکتوری + تعداد فایل + حجم + وضعیت (tracked/untracked) + «آیا در رجیستری هست؟».

---

## فاز ۲ — شکارِ فایل‌های یتیم و مرده (Orphan & Dead Hunt)

**هدف:** فایل‌هایی که روی دیسک هستن ولی هیچ کد/سند/رجیستری به آن‌ها اشاره نمی‌کند.

### روشِ کشف
برایِ هر فایلِ مشکوک:
```
# آیا هیچ کد/سند دیگری این فایل را import/reference کرده؟
grep -rl "FILENAME" --include="*.py" --include="*.md" --include="*.js" .
```
اگر خروجی خالی است → **یتیم.**

### چک‌لیست
- [ ] **اکسترکتورهای یتیم:** آیا `extract_*.py` در `nervous-system/` هست که در `refresh-live-data.bat` صدا زده *نشده*؟ (یعنی کد هست ولی اجرا نمی‌شود).
- [ ] **JS خروجیِ بدونِ مصرف‌کننده:** آیا `*.js` در `nervous-system/` هست که هیچ HTMLای `<script src>` نکرده؟
- [ ] **پایتونِ یتیم:** `*.py` که `import` نشده و در `__main__` هم نیست. (dead code).
- [ ] **مدارکِ یتیم:** `*.md` که هیچ `[[]]` یا لینکی به آن نمی‌رود. (در اکسیدین: dead note).
- [ ] **نسخهٔ مکرر:** آیا دو فایل با محتوای تقریباً یکسان هستن؟ (مثلاً `_read_jsonl` که در ۳ اکسترکتور کپی شده بود).
- [ ] **پشتیبانِ فراموش‌شده:** `*.bak`، `*.old`، `*.tmp`، `*.selfcode.bak`، `*.orig`.
- [ ] **دایرکتوریِ خالی:** `find . -type d -empty`. (نشانهٔ ساختارِ رهاشده).

### طبقه‌بندیِ یتیم‌ها
هر یتیم را به یکی برچسب بزن:
- 🟢 **زنده ولی بی‌صاحاب** (کار می‌کند ولی کسی نمی‌داند) — خطرناک
- 🟡 **مرده ولی پتانسیلِ زنده‌شدن** (اگر فعال شود چه؟)
- 🔴 **مردهٔ قطعی** (حذفِ امن)
- ⚫ **تاریخی/آرشیو** (نگه‌داری برای record)

### خروجی
جدول: `فایل | نوع | آخرین mtime | ارجاع‌دهنده‌ها | برچسب | توصیه`.

---

## فاز ۳ — معمایِ چند-سیستمی (Multi-System Riddle)

**هدف:** مشخص کن کدام «OCTOPUS» زنده است. این **مهم‌ترین** فاز است چون سردرگمیِ سیستم‌ها = سردرگمیِ مالک.

### چک‌لیست (برایِ هر یک از: `OCTOPUS/`, `_octopus/`, `OCTOPUS-PRIME/`, `OCTOPUS-DOCTOR/`)
- [ ] **منبعِ داده:** از کجا خوراک می‌گیرد؟ (env؟ state JSON؟ extractor؟)
- [ ] **مصرف‌کننده:** چه چیزی خروجی‌اش را می‌خواند؟ (UI؟ daemon؟)
- [ ] **flagهایش:** کدام `OCTOPUS_WIRE_*` فعال‌اش می‌کند؟
- [ ] **آخرین نوشته:** `mtime` جدیدترین فایل درونش. (مرده یا زنده؟)
- [ ] **آیا در `OCTOPUS-CURRENT-TRUTH` ذکر شده؟** (اگر نه، شاید سیستمِ غالب نیست).

### کشفِ مشکلِ اساسی
- `_octopus/config/` شامل `bots.yaml`، `octopus.yaml`، `policy.yaml`، `projects.yaml`. آیا این‌ها **دولتِ واقعی** هستند در حالی که `OCTOPUS/` فقط UI است؟ یا `_octopus/` یک سیستمِ قدیمیِ رهاشده است؟
- `_octopus/state/` شامل `octopus_state.json`، `evolution.json`، `epistemology.json`. آیا daemonها از این می‌خوانند یا از `_ops/state/`؟ (دو منبعِ حقیقت = فاجعه).
- `OCTOPUS-PRIME/phase-0` چیست؟ آیا «مبدا» است؟
- `OCTOPUS-DOCTOR/` با `00-INDEX`/`قوانین`/`معادلات`/`مغناطیس`/`اندام‌ها` — آیا یک سیستمِ تشخیصیِ جداگانه است؟

### خروجی
جدول: `سیستم | منبع داده | مصرف‌کننده | flag | mtime | زنده/مرده | حکم`.

---

## فاز ۴ — بازکردنِ جعبه‌سیاه‌ها (Blackbox Opening)

**هدف:** آنچه scope_guard ممنوع کرده، خودت باز کن و ببین چه درونشان است. (این فاز **فقط‌خواندنی** است — تغییر نده).

### چک‌لیست
- [ ] **`pre-0/` (= `PRE-0/`):** بخوان: `CONSTITUTION.md`، `governance.py`، `RISK-LADDER.md`، `SELF-IMPROVEMENT-LANE.md`، `constitutional_tests/`. این «قانونِ اساسی» است که scope_guard محافظتش می‌کند. آیا متنِ مالک هست؟
- [ ] **`4d_system/`:** این «مغز» است. ولی `4D.md` در ریشه چیست؟ آیا `4D/` (مرجعِ immutable) هم هست؟
- [ ] **`_memory/`:** `FRANKENSTEIN-BUILD-PLAN.md` — نامش هشدار می‌دهد! `LIVING-BRAIN-BLUEPRINT.md`، `TWO-BRAIN-CONTROL-BLUEPRINT.md`. این‌ها متن‌های خامِ مالک هستند.
- [ ] **`_sandbox/evolution_v1..v4`:** هر کدام `C6-*-REPORT.md` دارند. آیا این آزمایش‌هایِ تکاملیِ رهاشده‌اند یا زنده؟
- [ ] **genome / germline:** scope_guard این‌ها را forbid کرده. آیا واقعاً روی دیسک هستن؟ (`find . -iname "*genome*" -o -iname "*germline*"`).
- [ ] **personal/:** `.gitignore:72` آن را پوشش می‌دهد. آیا PII واقعیِ مالک (مالی، هویتی) هست؟ (فقط وجود را تأیید کن، محتوا را نشت نده).
- [ ] **`_survival-audit-2026-07-18/`:** `OWNER-SURVIVAL-DECISIONS.md`، `SURVIVAL-GOVERNOR-DESIGN.md` — آیا این یک بحرانِ گذشته است؟

### خروجی
جدول: `جعبه‌سیاه | مسیر | محتوای کلیدی | آیا متنِ مالک است؟ | خطر | توصیه`.

---

## فاز ۵ — بازیابیِ متن‌های خامِ مالک (Owner Text Recovery)

**هدف:** پیدا کن *متن‌های اصلیِ مالک* را — آنچه به agentها داده، آنچه دست‌نویس نوشته، آنچه «گم شده».

### چک‌لیست
- [ ] **MEGAPROMPTها:** ۵ فایلِ ریشه (`MEGAPROMPT--*`) + `MEGAPROMPT-OCTOPUS-DEEP-SCAN-V2.md`. برایِ هر کدام: تاریخ، هدف، «آیا صورتِ مسأله گرفته شد؟».
- [ ] **BLINDSPOTS:** ۶ فایل (`100` + `DELTA` + `DELTA-2..5`). این **قبلاً** اسکن شده! بخوان و بگو: آیا یافته‌های قبلی هنوز باز هستن؟ (جلوگیری از تکرار).
- [ ] **NEXT-AGENT-PROMPTها:** `agent-prompts/` با ۶ نسخه (`v2`، `v3`، `v4-ZIMAN`، بدونِ نسخه). این **دستورالعملِ مالک به agentهای بعدی** است. کدام آخرین است؟
- [ ] **Mega-Prompt.md** (بدونِ پیشوند): `38KB` — بزرگ‌ترین. چیست؟
- [ ] **سندهای مالک در `_memory/`:** `00_recon_report.md`، `BUILD-PROMPT.md`، `REVIEW.md`.
- [ ] **`_program-deliverables/`:** `BLACKBOX-DISCOVERY-PROMPTS-2026-07-25.md`، `EXTERNAL-DATA-MEGAPROMPTS-2026-07-25.md`. این‌ها **پرامپتِ فارنزیکِ قبلی** هستند!
- [ ] **متنِ خامِ فارسی:** `grep` برایِ فایل‌های `.md` که خطِ اولشان فارسی است (احتمالاً دست‌نویسِ مالک، نه گزارشِ agent).

### تکنیکِ بازیابی
برایِ هر متن: سه ستون بساز — `تاریخ | مؤلف (مالک یا agent) | هنوز معتبر است؟`.

### خروجی
کتابخانهٔ متنِ مالک + جدول «کدام نسخه نهایی است» + «کدام یافته از BLINDSPOTS هنوز باز است».

---

## فاز ۶ — کالبدشکافیِ کدِ موازی (Parallel Code Autopsy)

**هدف:** بفهم ۳ ماهِ کارِ موازی چه بر جای گذاشته — و آیا چیزی در worktree گیر کرده که باید به master می‌رفت.

### چک‌لیست
- [ ] **اختلافِ هر worktree با master:**
  ```
  git -C .claude/worktrees/NAME log master..HEAD --oneline
  ```
  کدام worktree commitهایی دارد که در master نیست؟ (کارِ گمشده).
- [ ] **commitهای یتیم:** commitهایی که در هیچ برنچِ فعال نیستن (`git fsck --lost-found`).
- [ ] **برنچ‌های backup/*:** برایِ هر کدام، `git log master..backup/NAME --oneline`. آیا چیزی در backup هست که در master فراموش شده؟
- [ ] **۱ stash:** `git stash show -p`. چه کاری نیمه‌تمام است؟
- [ ] **۵۶۷ untracked:** دسته‌بندی کن — کدام:
  - گزارش/سندِ جدید (نگه‌داری)
  - خروجیِ موقت (حذفِ امن)
  - کدِ نیمه‌تمام (باید commit یا حذف)
  - فایلِ پیکربندی/راز (بررسیِ نشتی)
- [ ] **فایل‌های `.claude/`:** settings، دستورات، history. آیا چیزی حساس هست؟
- [ ] **برنچِ فارسیِ `ئئ`:** چیست؟ اشتباهِ تایپی؟ تست؟ (یک commit هم هست — بررسی کن).
- [ ] **تضادِ نسخه:** آیا فایلی در master با نسخهٔ worktree متفاوت است و کسی نمی‌داند کدام درست است؟ (`git diff master .claude/worktrees/NAME -- FILE`).

### خروجی
نقشهٔ «کارِ گمشده» + جدولِ «کدام worktree باید merge شود/حذف شود/بایگانی شود».

---

## فاز ۷ — شکارِ flag و مسیرِ مخفی (Hidden Flag Hunt)

**هدف:** همهٔ سوئیچ‌های `OCTOPUS_WIRE_*` و مسیرهایِ پیکربندی را کشف کن — چون flag فعال = بخشی از سیستم *زنده* است.

### چک‌لیست
- [ ] **فهرستِ کاملِ flagها:**
  ```
  # در کد:
  grep -rE "OCTOPUS_WIRE[A-Z_0-9]*|OCTOPUS_CODE|SELF_CODE_ENABLED|PROJECTF_" . --include="*.py"
  # در پیکربندی:
  cat _ops/agi2027_runtime/managed_flags.json
  ```
- [ ] **وضعیتِ هر flag:** برایِ هر یک بگو: `فعال/غیرفعال در کجا تنظیم شده (env vs managed_flags.json vs flags.cmd) | چه می‌کند | در master هست یا فقط در worktree`.
- [ ] **سه flagِ زندهٔ کشف‌شده:** `OCTOPUS_WIRE_TG_CONTROL`، `OCTOPUS_WIRE_LEAD_OUTBOUND_WAL`، `OCTOPUS_WIRE_VALUE_LEDGER` (از `OCTOPUS-CURRENT-TRUTH-2026-08-02`). این‌ها **مسیرِ تولیدِ واقعی** هستند. ردیابی کن: هر کدام چه کدی را فعال می‌کند؟
- [ ] **دو منبعِ flag:** `managed_flags.json` در مقابل `env`. آیا تضاد هست؟ (یکی می‌گوید روشن، دیگری خاموش).
- [ ] **flagهایِ ارزیابی‌نشده:** flagهایی که در کد خوانده می‌شون ولی هیچ سندی نمی‌گوید چه می‌کنند.
- [ ] **`flags.cmd` / `OCTOPUS-flags.cmd`:** `.gitignore:53` آن را پوشش می‌دهد. آیا روی دیسک هست؟ (اگر بله، محتوای حساس دارد).

### خروجی
جدول: `flag | تنظیم‌شده در | مقدار | چه فعال می‌کند | خطر`.

---

## فاز ۸ — گزارشِ نهایی: «نقشهٔ واقعیِ اختاپوس»

### خروجیِ نهایی

**۱. نقشهٔ واقعی (یک صفحه)**
- تعدادِ سیستم‌های «OCTOPUS» که *واقعاً* زنده‌اند (احتمالاً ۱ یا ۲، نه ۴).
- تعدادِ فایل‌های یتیم.
- تعدادِ flagهای فعال.
- حجمِ «کارِ گمشده» در worktreeها (commitهای merge‌نشده).

**۲. جدولِ دارایی‌ها**
هر فایل/سیستم/flag را به یکی برچسب بزن:
- 🟢 **زنده و ضروری** — نگه‌داری، مستندسازی
- 🟡 **زنده ولی خطرناک** — مراقب باش (مثلِ flagهایِ فعال)
- 🔴 **مرده و سنگین** — حذفِ امن (فضا آزاد کن)
- ⚫ **تاریخی** — به `_Archive/` منتقل
- 🚨 **خطرناکِ پنهان** — اصلاحِ فوری (مثلِ نشتیِ احتمالی)

**۳. ده بزرگ‌ترین غافلگیری (Top 10 Surprises)**
- ۱۰ چیزی که مالک *احتمالاً نمی‌داند* و باید بداند.

**۴. متن‌های خامِ مالکِ بازیابی‌شده**
- کدام نسخهٔ MEGAPROMPT/NEXT-AGENT نهایی است؟
- کدام یافته‌های BLINDSPOTS هنوز باز است؟
- متنِ گمشده‌ای که باید بازخوانی شود.

**۵. برنامهٔ پاک‌سازی (Declutter Roadmap)**
- سریع: حذفِ `.bak`/`.tmp`/`__pycache__`/worktreeهای مرده.
- متوسط: ادغام یا بایگانیِ برنچ‌های backup/*.
- ساختاری: تصمیم دربارهٔ `_octopus/` vs `OCTOPUS/` (یک‌سازی یا مستندسازیِ تفاوت).

**۶. تضمینِ اصالت**
- تاریخ، scope، محدودیت‌ها (چه چیزی بررسی نشد).

---

## ⚙️ قواعدِ رفتاریِ فارنزیک (هفت اصل)

۱. **هیچ فایلی را حذف نکن.** فقط دسته‌بندی کن. تصمیمِ حذف با مالک است.
۲. **فرض کن دو نسخه از هر چیزی هست.** (چون ۳ ماهِ کارِ موازی بوده).
۳. **هر تضاد را گزارش کن.** (دو `octopus_state.json`؟ دو `policy.yaml`؟).
۴. **به git status اعتماد نکن.** — untrackedها در آن نیستن ولی روی دیسک هستن.
۵. **mtime دروغ می‌گوید.** (یک کپی می‌تواند mtimeِ اصلی را حفظ کند). برایِ «زنده/مرده» به ارجاع‌دهنده‌ها نگاه کن.
۶. **متنِ مالک را محترمانه بخوان.** (PII، مالی، هویتی — فقط وجود را تأیید کن، محتوا را در گزارش بیرون نیاور).
۷. **هدف کشف است نه قضاوت.** — تو می‌خواهی مالک بداند چه دارد، نه اینکه بگویی «اشتباه کردی».

---

## 📚 پیوست — کشف‌هایِ baseline (شواهدِ اولیه)

این پرامپت بر پایهٔ اسکنِ واقعیِ ۲۰۲۶-۰۸-۰۳ ساخته شده. شواهدِ اولیه:

### شواهدِ کارِ موازی
- **۴۵ برنچ:** ۲۷ `claude/*` + ۹ `backup/*` + `fix/*` + `phase-d` + `research/*` + `ئئ` (فارسی).
- **۱۰ worktree فعال** در `.claude/worktrees/` (اسامی در بالا).
- **۵۶۷ فایلِ untracked.**
- **۱ stash:** `pre-wave0-live-edits-2026-07-14`.
- **۱ برنچِ فارسیِ مشکوک:** `ئئ`.

### شواهدِ چند-سیستمی
- `OCTOPUS/` (داشبورد، worlds، gallery — UI)
- `_octopus/` (config/bots.yaml، state/octopus_state.json، manifests — دولت؟)
- `OCTOPUS-PRIME/phase-0` (مبدا؟)
- `OCTOPUS-DOCTOR/` (قوانین، معادلات، مغناطیس — پزشک؟)

### شواهدِ جعبه‌سیاه
- `pre-0/` == `PRE-0/` (برخوردِ حروفِ ویندوز — `governance.py` درون)
- `4d_system/` (مغز) + `4D.md` در ریشه
- `_memory/` (FRANKENSTEIN-BUILD-PLAN، LIVING-BRAIN-BLUEPRINT، TWO-BRAIN-CONTROL)
- `_sandbox/evolution_v1..v4` (آزمایشِ C6، ۴ نسخه)
- `_survival-audit-2026-07-18/` (OWNER-SURVIVAL-DECISIONS)

### شواهدِ متنِ مالک
- ۵ `MEGAPROMPT--*.md` در ریشه + `Mega-Prompt.md` (38KB)
- ۶ `OCTOPUS-BLINDSPOTS*.md` (100 + delta 1-5)
- ۶ `NEXT-AGENT-PROMPT*.md` در `agent-prompts/`
- `_program-deliverables/BLACKBOX-DISCOVERY-PROMPTS-2026-07-25.md`
- `_program-deliverables/EXTERNAL-DATA-MEGAPROMPTS-2026-07-25.md`

### شواهدِ flag
- زنده در `OCTOPUS-CURRENT-TRUTH-2026-08-02.md`: `OCTOPUS_WIRE_TG_CONTROL=1`، `OCTOPUS_WIRE_LEAD_OUTBOUND_WAL=1`، `OCTOPUS_WIRE_VALUE_LEDGER=1`.
- مسیرِ پیکربندی: `_ops/agi2027_runtime/managed_flags.json` (نه فقط env).

## ---ROLE END---

---

> **یادداشتِ ویراستار (2026-08-03):** این مگاپرامپت **مکمل** `MEGAPROMPT-OCTOPUS-FULL-SCAN.md` (ممیزی) و `AUDIT-REPORT-2026-08-03.md` است. ترتیبِ پیشنهادی: (۱) ابتدا **فارنزیک** (این فایل) را اجرا کن تا بدانی چه داری، (۲) بعد **ممیزی** را رویِ اجزایِ زندهٔ شناسایی‌شده.Baseline شواهد بر اساسِ وضعیتِ رویِ دیسک در ۲۰۲۶-۰۸-۰۳ است.
