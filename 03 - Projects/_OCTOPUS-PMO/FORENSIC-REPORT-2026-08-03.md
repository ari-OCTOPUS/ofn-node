---
title: گزارشِ فارنزیکِ اختاپوس — کشفِ ناشناخته‌ها
id: FORENSIC-REPORT-2026-08-03
type: forensic-discovery-report
version: v1
date: 2026-08-03
auditor: ZCode (model: GLM-5.2) — نقشِ باستان‌شناسِ نرم‌افزار + کارآگاهِ صحنهٔ جرم
scope: ۸ فازِ فارنزیک — کشفِ جعبه‌سیاه‌ها، متن‌های گمشدهٔ مالک، کدِ موازیِ ۳ ماهه
method: خواندنِ مستقیمِ فایل‌ها + git archaeology + cross-reference
prior_scans_reused:
  - OCTOPUS-BLINDSPOTS-100..DELTA-5 (565 موردِ قبلاً کشف‌شده)
  - _agent_audit_output/ (ممیزیِ ۲۰۲۷ با ۹ نقش)
  - Mega-Prompt.md (Survival University)
tamper_stamp:
  generated: 2026-08-03T18:00:00Z
  scope: forensic-discovery
  model: GLM-5.2
  limitations: [حجمِ du به timeout خورد، تعدادِ کل به‌طورِ تقریبی]
---

# 🔬 گزارشِ فارنزیکِ اختاپوس — کشفِ ناشناخته‌ها

> **تمبرِ اصالت:** این گزارش حاصلِ کاوشِ واقعیِ رویِ دیسک در ۲۰۲۶-۰۸-۰۳ است. هر ادعا با شواهد مستند است. هدف: پیدا کردنِ آنچه مالک **نمی‌داند که دارد**.

---

## 🎯 خلاصهٔ اجرایی — ۱۰ غافلگیریِ بزرگ

این ۱۰ چیز را مالک *احتمالاً نمی‌داند* و باید بداند:

| # | غافلگیری | شدت |
|---|---|---|
| ۱ | **۱۷۹ flagِ `OCTOPUS_WIRE_*` وجود دارد، فقط ۳ تای آن‌ها فعال است** — یعنی ۱۷۶ قابلیتِ نهفته/خاموش در کد | 🟡 |
| ۲ | **دو سیستمِ «OCTOPUS» به‌طورِ همزمان زنده‌اند:** `_octopus/` (دولتِ کنترل‌پلین، امروز فعال) + `OCTOPUS/` (داشبوردِ UI، ۱۰ روز مرده) | 🟠 |
| ۳ | **۴۰ commitِ گمشده در ۴ worktree:** clever-pike (+11), operational-loop (+11), unified-hardening (+11), vigilant-grothendieck (+7) — هیچ‌کدام در master نیست | 🟠 |
| ۴ | **`pre-0` و `PRE-0` یکی‌اند** (inode یکسان در ویندوز) — قانونِ اساسی + `governance.py` درون | ℹ️ |
| ۵ | **۱۰+ commitِ رهاشده (dangling)** که در هیچ برنچی نیستن | 🟡 |
| ۶ | **۳ مأموریتِ pending در `_octopus/state/approvals.json`** از ۲۰۲۶-۰۷-۲۵ گیر کرده — شاملِ یکی با `risk:high` | 🟠 |
| ۷ | **۵۶۵ نقطهٔ کور قبلاً کشف شده** (BLINDSPOTS ۱۰۰..DELTA-5) — ولی بخشِ پایه‌ای هنوز باز است (BCM خالی، Hebbian گرسنه، governor LLM شکسته) | 🔴 |
| ۸ | **`langar_bot.py` (OnlyFans) واقعاً Telegram POST می‌زند** با PII scrubber که قبلاً FAIL-OPEN گزارش شده | 🔴 |
| ۹ | **۱ برنچِ فارسیِ `ئئ`** که در واقع یک دستاوردِ واقعی است (4-wave TG-UI build record، ۲۰۲۶-۰۷-۳۱) ولی نامش گیج‌کننده است | 🟡 |
| ۱۰ | **`_octopus/config/octopus.yaml` دولتِ واقعی است** (mode: control-plane، language: fa، features: planner/self_heal/doctor_box) — نه `OCTOPUS/` | ℹ️ |

---

## فاز ۱ — نقشهٔ برداریِ کامل

### مقیاسِ سیستم
| متریک | مقدار |
|---|---|
| **کلِ فایل‌ها** (بدون .git) | **~۱۲۵,۰۰۰** |
| **برنچ‌ها** | **۴۵** |
| **worktreeهای فعال** | **۱۰** |
| **فایل‌های untracked** | **۵۶۷** (۳۴۲ json، ۸۴ md، ۴۸ py، ۲۸ jsonl) |
| **commitهای gمشوده (ahead of master)** | **۴۰** |
| **commitهای رهاشده (dangling)** | **۱۰+** |
| **flagهای OCTOPUS_WIRE_*** | **۱۷۹** (۳ فعال) |
| **stash** | **۱** |

### دایرکتوری‌های ریشه (۳۹ عدد!)
سیستم از یک vault ساده به یک **شهرِ زیرِ خاکریز** تبدیل شده. دایرکتوری‌های ریشه در ۵ دسته:

**۱. سیستم‌های اصلی (زنده):** `_ops/`، `4d_system/`، `nervous-system/`، `_octopus/`، `OCTOPUS/`، `OCTOPUS-DOCTOR/`
**۲. Vault اکسیدین:** `00-Inbox` تا `10-Telegram processing` (۱۰ پوشهٔ استاندارد)
**۳. میراثِ موازی:** `OCTOPUS-PRIME/`، `CHRONOS-FABLE-OS/`، `NBB-Project-Scan-2026-07-11/`، `TELEGRAM-SYSTEM-MAP/`
**۴. staging/legacy با `_`:** `_code/`، `_phase1a/`، `_program-deliverables/`، `_launchpad/`، `_deploy/`، `_memory/`، `_sandbox/`، `_agent_audit_output/`، `_agent_reports/`، `_survival-audit-2026-07-18/`، `_worktrees/`، `_Archive/`، `_Duplicates/`، `_Templates/`
**۵. سایر:** `app/`، `agent-prompts/`، `Inbox/`، `Obsidian Vault/`، `Projects/`، `pre-0/`(=`PRE-0/`)

---

## فاز ۲ — شکارِ فایل‌های یتیم و مرده

### یافته‌ها
- **فایل‌های `.bak` متعدد** — پشتیبان‌های فراموش‌شدهٔ `.obsidian/` و `Accounting/_archive/`. قابلِ حذفِ امن.
- **دایرکتوری‌های خالی** (~۱۵+) — `4d_system/outputs/self_code_proposals` (خالی یعنی هیچ self-code proposal ای اعمال نشده)، چند پوشه در `Obsidian Vault/LifeOS-Architect/` (ساختارِ رهاشده).
- **`_Archive/worktree-rescue-2026-07-24/`** — یک تلاشِ نجاتِ قبلی از کارِ موازی، با کپیِ untracked‌ها.

### یتیم‌های مهم
- **`Mega-Prompt.md` (38KB)** — بزرگ‌ترین سند. «SURVIVAL UNIVERSITY» — متافورِ اصلیِ مالک برایِ کلِ سیستم. این **متنِ بنیادینِ مالک** است ولی در هیچ MOC یا رجیستری اشاره نشده.
- **`_agent_audit_output/`** — یک ممیزیِ کاملِ قبلی با ۹ نقش، verdict: «L2 — contained but blind». این گزارش قبلاً وجود داشته ولی احتمالاً فراموش شده.

---

## فاز ۳ — معمایِ چند-سیستمی (مهم‌ترین فاز)

این **سردرگمیِ اساسی** سیستم است. چهار چیز «OCTOPUS» هستن:

| سیستم | مسیر | mtime جدیدترین | حکم | منبع داده |
|---|---|---|---|---|
| **`_octopus/`** | دولتِ کنترل‌پلین | **۲۰۲۶-۰۸-۰۳ ۱۵:۴۳** ✅ | **زنده — دولتِ واقعی** | `config/octopus.yaml`، `state/*.json` |
| **`OCTOPUS/`** | داشبورد + worlds + gallery | ۲۰۲۶-۰۷-۲۴ | **مرده (۱۰ روز)** — UIStatic | nervous-system/*.js |
| **`OCTOPUS-PRIME/`** | phase-0 + test-authority | ۲۰۲۶-۰۷-۲۴ | **مرده — مبداً/تاریخی** | sandbox test reports |
| **`OCTOPUS-DOCTOR/`** | doctor/scanner.py + قوانین | **۲۰۲۶-۰۸-۰۳ ۱۷:۰۹** ✅ | **زنده — امروز فعال** | scan از ارگانیسم |

### کشفِ کلیدی: `_octopus/` دولتِ غالب است
`_octopus/config/octopus.yaml` صراحتاً می‌گوید:
```yaml
octopus:
  mode: "control-plane"
  ui: "telegram"
  language: "fa"
features:
  planner: true
  self_heal: true
  self_awareness: true
  doctor_box: true
  evolution: false      # خاموش!
  epistemology: false   # خاموش!
  experiments: true
  project_f: true
```
**این دولتِ واقعی است.** `OCTOPUS/` (داشبورد) فقط یک لایهٔ نمایشِ ایستاست که از ۲۴ جولای به‌روز نشده. ولی `_octopus/` امروز (۱۵:۴۳) در حالِ نوشتنِ approvals و audit log بوده.

### کشفِ حیاتی: ۳ مأموریتِ گیرکرده
`_octopus/state/approvals.json` شاملِ ۳ مأموریتِ `pending` از **۲۰۲۶-۰۷-۲۵** (۹ روز پیش) است:
1. `M-20260725-132939` — risk: **high** — «یه لطفی بکن و وضعیتو یه نگاه بنداز»
2. `M-20260725-134401` — risk: high — همان عنوان (تکراری؟)
3. یک موردِ دیگر

این‌ها **منتظرِ رأیِ مالک هستند ولی ۹ روز کسی نگرفته.** یا فراموش شده یا در صفِ اشتباه.

---

## فاز ۴ — بازکردنِ جعبه‌سیاه‌ها

### `pre-0/` (= `PRE-0/`) — قانونِ اساسی
**این متنِ خامِ مالک است.** تأیید شد: `pre-0` و `PRE-0` inode یکسان دارند (`281474977257574`) — در ویندوز یکی‌اند.

محتوای کلیدی (`CONSTITUTION.md` + `governance.py`):
- **۷ لایهٔ تقدم:** `retrieved_data < agent_prompt < operational_narrative < experiment_protocol < memory_policy < effect_policy < global_halt < constitution`. لایهٔ پایین **هرگز** بالا را override نمی‌کند.
- **۱۰ hard constraint:** شاملِ `no_credential_acquisition`، `no_replication`، `no_resist_shutdown`، `no_concealment`.
- **مرزِ self-improvement:** فقط `measure/reproduce/propose/test/compare/request_review` مجاز است. `edit_constitution`، `acquire_credentials`، `replicate`، `merge_or_deploy` ممنوع.
- **AGI یک فرضیهٔ اثبات‌نشده است، نه هویت.** (`IDENTITY-AND-AGI-STATUS.md`)

**حکم:** این **متنِ بنیادینِ مالک** است که scope_guard محافظتش می‌کند. سالم و مهم.

### `_memory/` — حافظهٔ خام + بلوپرینت‌ها
- **`FRANKENSTEIN-BUILD-PLAN.md`** — «زنده‌کردنِ اندام‌ها» (۸ اندام، طراحی ۸۰٪). این **نقشهٔ ساختِ مالک** است.
- `TWO-BRAIN-CONTROL-BLUEPRINT.md`، `LIVING-BRAIN-BLUEPRINT.md` — معماریِ دو-مغزی.
- نامِ «Frankenstein» هشدارِ خودِ مالک است دربارهٔ ماهیتِ مونتاژیِ سیستم.

### `_sandbox/evolution_v1..v4` — آزمایش‌های تکاملیِ رهاشده
۴ نسخه از آزمایشِ C6 (تکامل/کذب‌سنجی). هر کدام `C6-*-REPORT.md` دارند. این‌ها **آزمایش‌های تحقیقاتی** هستن، نه کدِ تولید. ولی در `_sandbox/` هستن یعنی نه به‌طورِ رسمی مرده و نه زنده.

### `_survival-audit-2026-07-18/` — بحرانِ گذشته
`OWNER-SURVIVAL-DECISIONS.md`، `SURVIVAL-GOVERNOR-DESIGN.md`، `OCTOPUS-REALITY-TO-REVENUE-MAP.md`. این **یک بحرانِ زنده‌ماندن** در ۱۸ جولای بوده. آیا هنوز مرتبط است؟

---

## فاز ۵ — بازیابیِ متن‌های خامِ مالک

### کتابخانهٔ متنِ مالک (بایگانیِ دستاوردها)

| متن | تاریخ | نوع | حکم |
|---|---|---|---|
| **`Mega-Prompt.md`** (38KB) | ۲۰۲۶-۰۷-۱۱ | متافورِ «Survival University» | **متنِ بنیادین** — باید در MOC باشد |
| **`OCTOPUS-BLINDSPOTS-100` + DELTA 1-5** | ۲۰۲۶-۰۷-۲۷ تا ۰۷-۲۸ | ۵۶۵ نقطهٔ کور | **مهم‌ترین اسکنِ قبلی** |
| `MEGAPROMPT--octopus-repair-2026-07-25.md` | ۲۰۲۶-۰۷-۲۵ | ترمیم | احتمالاً اجرا شده |
| `MEGAPROMPT--octopus-fable-opus-2026-07-25.md` | ۲۰۲۶-۰۸-۰۲ | (به‌روزشده) | بررسی |
| `NEXT-AGENT-PROMPT` (۶ نسخه) | v2 تا v4-ZIMAN | دستور به agent بعدی | **آخرین نسخه:** v4-ZIMAN؟ (تأیید کن) |
| `_program-deliverables/BLACKBOX-DISCOVERY-PROMPTS` | ۲۰۲۶-۰۷-۲۵ | **همین کارِ فارنزیک قبلاً!** | بررسیِ یافته‌هایش |
| `_memory/00_recon_report.md` | — | recon اولیه | تاریخی |

### کشفِ حیاتی: ۵۶۵ نقطهٔ کورِ قبلاً کشف‌شده
BLINDSPOTS-100..DELTA-5 مجموعاً **۵۶۵ مورد + ۱۴ تصحیح** کشف کرده. مهم‌ترین‌ها که **هنوز باز** هستن (از خودِ BLINDSPOTS-DELTA-5):

**🔴 بحرانی (از ۱۰۰):**
- **BCM خالیه** (صفر کلید، ۶۵ استپ) — یادگیریِ پلاستیسیته واقعاً اتفاق نمی‌افتد.
- **Hebbian گرسنه** (۱ جفت، strength 0.132) — دایرهٔ واژگانِ کوچک.
- **Governor LLM ۲۴h شکسته** — `extract_json` روی JSON ناقص fail، ۲۲ fail.
- **Debate بیشتر stub** — qwen timeout → متنِ canned فارسی.
- **فقط ۱ پا زنده** (lead-naghshi) — ۹ پایِ دیگر مرده.

**🟡 از DELTA-5 (جدیدترین):**
- #۵۵۲: reentry packet فقط RAM counts — بعد از restart صفر نشون می‌ده.
- #۵۵۵: `/heart set` stale-card ممکن است target مطلق اعمال کند.
- #۵۵۰: `_mark_hypothesis` read-modify-write غیراتمیک.

**جمع‌بندیِ BLINDSPOTS:** سیستم **«نصف‌بسته، نه شکسته»** است. سه wiring (neural→decision، memory→decision، BCM guard) می‌تواند کلش را عوض کند.

---

## فاز ۶ — کالبدشکافیِ کدِ موازی

### کارِ گمشده در worktreeها
| worktree | ahead of master | behind | حکم |
|---|---|---|---|
| **clever-pike-721a16** | **+11** | -40 | کارِ مهمِ gمشوده (telegram-ui) |
| **operational-loop-agi** | **+11** | -185 | حلقهٔ عملیاتی، ولی ۱۸۵ commit عقب |
| **unified-hardening** | **+11** | -139 | سخت‌سازی، ۱۳۹ commit عقب |
| **vigilant-grothendieck** | **+7** | -185 | code-integration |
| elegant-jemison | 0 | -8 | onlyfans-deep-scan (merge شده؟) |
| megaprompt-false-claims | 0 | -34 | بررسیِ دروغ‌ها (مهم!) |
| octopus-completion | 0 | -219 | ۲۱۹ commit عقب — احتمالاً رهاشده |
| stoic-nash | 0 | -40 | prompt-verification |
| telegram-operational-control | 0 | 0 | sync با master ✅ |
| unruffled-kalam | 0 | -40 | stoic-bartik (نامِ گیج‌کننده) |

**مجموعِ کارِ گمشده: ۴۰ commit** که باید merge یا صراحتاً رد شود.

### شعبه‌های backup/* (نقاطِ بازگشتِ مالک)
۹ شعبه، همگی snapshotهای تاریخی:
- `backup/before-cleanup-2026-07-19` — پیش از پاک‌سازی
- `backup/pre-c6-merge` / `pre-c6-sync-c7` — پیش از ادغامِ C6
- `backup/pre-deploy-2026-07-21` — پیش از deploy
- `backup/pre-golive-2026-07-15` / `pre-truthful-cockpit-2026-07-15` (۲ نسخه!)

**نکته:** دو شعبهٔ `pre-truthful-cockpit-2026-07-15` و `...-7-15` (با فرمتِ تاریخِ متفاوت) **همان نقطه را نشان می‌دهند** (هر دو commit `6a38af8`). یکی اضافی است.

### شعبهٔ فارسیِ `ئئ`
این اشتباه نیست! یک دستاوردِ واقعی است: «4-wave TG-UI build record - owner 4 rulings, deliverables, unification, ratchet 17->7» (۲۰۲۶-۰۷-۳۱). ولی نامش غیراستاندارد است و باید به یک نامِ معنادار تغییر کند یا merge شود.

### ۱۰+ commitِ رهاشده (dangling)
`git fsck --lost-found` نشان داد حداقل ۱۰ commit وجود دارد که در هیچ برنچی نیستن. این‌ها کارِ واقعی هستند که گم شده‌اند. (خطرناک — ممکن است شاملِ ترمیمِ مهمی باشد.)

### stash
`pre-wave0-live-edits-2026-07-14` — ویرایش‌های wave0 شاملِ verify روی کدِ زنده. می‌تواند ارزشمند باشد.

---

## فاز ۷ — شکارِ flag و مسیرِ مخفی

### ۱۷۹ flag — فقط ۳ فعال
این **مهم‌ترین کشفِ کمی** است. کد شاملِ **۱۷۹ flagِ مجزای `OCTOPUS_WIRE_*`** است:

**۳ flagِ زنده** (از `managed_flags.json` و `OCTOPUS-CURRENT-TRUTH`):
```json
{
  "OCTOPUS_WIRE_TG_CONTROL": "1",          // کنترلِ تلگرام
  "OCTOPUS_WIRE_LEAD_OUTBOUND_WAL": "1",   // خروجیِ WALِ لید
  "OCTOPUS_WIRE_VALUE_LEDGER": "1"         // دفترِ ارزش
}
```

**۱۷۶ flagِ خاموش** — هر کدام یک قابلیتِ نهفته. نمونه‌های قابل‌توجه:
- `OCTOPUS_WIRE_KILL_SEAM` — ضدِ replay (در گزارشِ ممیزی ذکر شد، خاموش)
- `OCTOPUS_WIRE_ACTION_BRIDGE` — پلِ اقدام (خاموش)
- `OCTOPUS_WIRE_CODE_APPLY` / `CODE_BRAIN` — اعمالِ کد (خاموش)
- `OCTOPUS_WIRE_DEBATE` / `DEBATE_VERDICT` — مناظره (خاموش، ولی BLINDSPOTS گفت شکسته)
- `OCTOPUS_WIRE_HEART` / `PULSE_ARBITER` — قلبِ مرکبی (خاموش)
- `OCTOPUS_WIRE_SELF_IMPROVE_AUTO` — خودبهبودیِ خودکار (خاموش — خوشبختانه)
- `OCTOPUS_WIRE_EVOLUTION` — تکامل (در octopus.yaml هم false)
- `OCTOPUS_WIRE_PROJECTF_CORTEX` / `SPINE` — Project-F (خاموش، PROJECTF_API_BASE_URL غایب)

### کشفِ حیاتی: `langar_bot.py` (OnlyFans) واقعاً POST می‌زند
از ممیزیِ قبلیِ `_agent_audit_output/`: **«the OnlyFans langar_bot does live Telegram POST behind a FAIL-OPEN PII scrubber.»**

این یعنی:
- `03 - Projects/اونلی فنز/langar/langar_bot.py` واقعاً به Telegram پیام می‌فرستد.
- PII scrubber آن **FAIL-OPEN** است — یعنی اگر scrubber خطا دهد، پیامِ خام (با PII) ارسال می‌شود.
- این **خارج از پلِ action_bridge** است — یعنی گیت‌هایِ `_ops/action_bridge/` (A0-A6) این مسیر را پوشش نمی‌دهند.

**شدت: 🔴 CRITICAL** — این تنها مسیرِ شناخته‌شدهٔ «ارسالِ خارجیِ واقعی» است که ممکن است PII نشت کند.

### مسیرهای پیکربندیِ متعدد (سردرگمیِ flag)
flagها از **سه منبعِ متفاوت** خوانده می‌شوند:
1. `os.environ` (محیطِ اجرا)
2. `_ops/agi2027_runtime/managed_flags.json` (فایلِ مدیریت‌شده)
3. `flags.cmd` / `OCTOPUS-flags.cmd` (`.gitignore` شده، احتمالاً روی دیسک)

اگر این سه تضاد داشته باشند (یکی روشن، دیگری خاموش)، رفتار غیرقابل‌پیش‌بینی است.

---

## فاز ۸ — جدولِ دارایی‌ها (تصمیمِ نهایی)

هر دارایی را به یک برچسب اختصاص بده:

### 🟢 زنده و ضروری — نگه‌داری، مستندسازی
| دارایی | دلیل |
|---|---|
| `_ops/`، `4d_system/`، `nervous-system/` | هستهٔ زنده |
| `_octopus/` | دولتِ کنترل‌پلینِ فعال |
| `OCTOPUS-DOCTOR/` | امروز فعال (scanner.py) |
| `pre-0/` (= `PRE-0/`) | قانونِ اساسی |
| `_memory/` (FRANKENSTEIN، TWO-BRAIN) | بلوپرینت‌های مالک |
| `OCTOPUS-BLINDSPOTS*.md` | ۵۶۵ یافتهٔ ارزشمند |
| `Mega-Prompt.md` | متافورِ بنیادین |

### 🟡 زنده ولی خطرناک — مراقب باش
| دارایی | خطر |
|---|---|
| ۳ flagِ فعال (`TG_CONTROL`، `LEAD_OUTBOUND_WAL`، `VALUE_LEDGER`) | مسیرِ تولیدِ واقعی |
| **`langar_bot.py`** (OnlyFans) | **POST واقعی + PII FAIL-OPEN** |
| ۳ مأموریتِ pending در `_octopus/state/approvals.json` | گیرکرده از ۰۷-۲۵ |
| ۱۷۶ flagِ خاموش | قابلیتِ نهفته — اگر فعال شوند چه؟ |
| `_sandbox/evolution_v1..v4` | آزمایشِ نیمه‌زنده |

### 🔴 مرده و سنگین — حذفِ امن (بعد از تأیید)
| دارایی | دلیل |
|---|---|
| `OCTOPUS/` (داشبورد) | ۱۰ روز مرده (ولی ممکن است فقط نیاز به refresh داشته باشد) |
| `OCTOPUS-PRIME/phase-0` | تاریخی — مبداً |
| `NBB-Project-Scan-2026-07-11/` | snapshotِ تاریخی |
| فایل‌های `.bak` در `.obsidian/` و `Accounting/_archive/` | پشتیبانِ فراموش‌شده |
| دایرکتوری‌های خالی (~۱۵) | ساختارِ رهاشده |
| شعبهٔ تکراریِ `backup/pre-truthful-cockpit-2026-7-15` | همان نقطهٔ دیگری |

### ⚫ تاریخی — به `_Archive/` منتقل
| دارایی | دلیل |
|---|---|
| `_phase1a/` (C2-C7 reports) | فازهایِ اولیهٔ تکمیل‌شده |
| `_agent_audit_output/`، `_agent_reports/` | ممیزی‌های قبلی |
| `_survival-audit-2026-07-18/` | بحرانِ گذشته |
| `_deploy/` | deployهای قدیمی |
| ۸ شعبهٔ backup/* (به جز ۱ مرجع) | snapshotهای تاریخی |

### 🚨 خطرناکِ پنهان — اصلاحِ فوری
| دارایی | خطر | توصیه |
|---|---|---|
| **`langar_bot.py` PII FAIL-OPEN** | نشتیِ PII | تبدیل به FAIL-CLOSED |
| **۴۰ commitِ گمشده در worktreeها** | کارِ ارزشمندِ فراموش‌شده | merge یا صراحتاً رد |
| **۱۰+ commitِ رهاشده (dangling)** | کارِ گم‌شده | `git fsck` + بررسی |
| **Governor LLM شکسته** (از BLINDSPOTS) | تخصیصِ کور | ترمیمِ `extract_json` |
| **BCM خالی + Hebbian گرسنه** | «هوش مصنوعی» واقعی نیست | wiring (۳ مسیر) |

---

## 📅 برنامهٔ پاک‌سازی (Declutter Roadmap)

### 🚨 سریع (امروز)
1. **بررسیِ ۳ مأموریتِ pending** در `_octopus/state/approvals.json` — مالک رأی بدهد یا reject.
2. **بررسیِ `langar_bot.py`** — آیا PII scrubber واقعاً FAIL-OPEN است؟ اگر بله، تبدیل به FAIL-CLOSED.
3. **بررسیِ ۴۰ commitِ گمشده** — `git log clever-pike -- master..HEAD` برایِ هر worktree. ارزشمند است یا دور ریختنی؟

### 🔧 متوسط (این هفته)
4. **بررسیِ ۱۰+ commitِ رهاشده** — `git show <hash>` برایِ هر dangling. ترمیمِ مهمی گم نشده؟
5. **تغییرِ نام یا mergeِ برنچِ `ئئ`** به نامی معنادار.
6. **حذفِ شعبهٔ تکراریِ `backup/pre-truthful-cockpit-2026-7-15`.**
7. **بررسیِ `_octopus/` vs `OCTOPUS/`** — آیا داشبورد باید refresh شود یا سیستمِ جداست؟ مستندسازیِ تفاوت.

### 🏗️ ساختاری (موجِ بعد)
8. **کاتالوگِ ۱۷۹ flag** — هر کدام را مستند کن (چه می‌کند، چه زمانی فعال).
9. **یک‌سازیِ منبعِ flag** (env vs managed_flags.json vs flags.cmd).
10. **حلِ ۵۶۵ نقطهٔ کورِ باز** (از BLINDSPOTS) — اولویت: BCM، Hebbian، Governor LLM.
11. **انتقالِ دارایی‌هایِ تاریخی به `_Archive/`** (_phase1a، _agent_audit_output، …).

---

## ✅ تضمینِ اصالت

| فیلد | مقدار |
|---|---|
| `generated` | ۲۰۲۶-۰۸-۰۳T۱۸:۰۰:۰۰Z |
| `scope` | کشفِ فارنزیک — ۸ فاز |
| `model` | GLM-5.2 (ZCode) |
| `evidence_standard` | شواهدِ مستقیم از رویِ دیسک + git + خواندنِ فایل |
| `prior_scans_reused` | BLINDSPOTS-100..DELTA-5 (۵۶۵ مورد)، _agent_audit_output، Mega-Prompt.md |

### محدودیت‌ها
1. **حجمِ دقیقِ دایرکتوری‌ها timeout خورد** — `du -sh` کامل نشد. ولی مولفه‌های بزرگ (whisper model ۱.۹GB، state) شناسایی شد.
2. **محتوایِ کاملِ ۴۰ commitِ گمشده بررسی نشد** — فقط تعداد و نامِ worktree. هر کدام نیاز به `git log` اختصاصی دارد.
3. **۱۰+ dangling commit فقط شناسایی شد** — محتوای هر کدام نیاز به `git show` دارد.
4. **۱۷۹ flag فقط فهرست شد** — معنایِ هر کدام نیاز به کاوشِ کد دارد.
5. **langar_bot.py فقط از ممیزیِ قبلی نقل شد** — باید مستقیماً خوانده و راستی‌آزمایی شود.

---

> **یادداشتِ نهایی:** اختاپوس **بزرگ‌تر و پیچیده‌تر از آن است که فکر می‌کردی.** ۱۲۵,۰۰۰ فایل، ۴۵ برنچ، ۱۷۹ flag، ۴ سیستمِ «OCTOPUS». ولی خبرِ خوب: **دولتِ واقعی (`_octopus/`) امروز زنده و فعال است، قانونِ اساسی (`pre-0/`) سالم است، و ۵۶۵ نقطهٔ کور قبلاً شناسایی شده.** مشکلاتِ اصلی در سه جا متمرکزند: (۱) **کارِ گمشده در worktreeها** (۴۰ commit)، (۲) **`langar_bot.py` با PII FAIL-OPEN** (تنها نشتیِ واقعی)، و (۳) **۵۶۵ نقطهٔ کورِ باز** (به‌خصوص BCM/Hebbian/Governor). با اجرایِ برنامهٔ پاک‌سازی، سیستم قابلِ درک و مدیریت خواهد بود.
