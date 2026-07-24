---
type: handoff
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
session: claude/octopus-beat-parallel (ZCode, 2026-07-24)
supersedes: HANDOFF-NEXT-AGENT.md (2026-07-12), ARCHITECTURE-COMPLETE-2026-07-20/10_HANDOFF_NEXT.md
created: 2026-07-24
updated: 2026-07-24
created_by: agent (ZCode)
tags: [project-f, handoff, reorg, governance]
---

# 🤝 HANDOFF — ایجنت بعدی Project-F (پس از بازآرایی 2026-07-24)

> **این سند را اول بخوان.** خودکفاست — کل وضعیت پروژه + کاری که این جلسه شد + قدم بعدی، همه اینجا.
> **خلاصه یک‌خطی:** این جلسه فقط **بازآرایی ساختار فایل (Obsidian)** بود. هیچ محتوای استراتژیک، تصمیم، یا gate تغییر نکرد. پروژه هنوز **GATE 0 = NO-GO**، **ZERO اجرای بیرونی**.

---

## ۰. چطور این پوشه را پیدا کنی (مهم — تلهٔ encoding)

نام پوشهٔ پروژه فارسی است: `03 - Projects/اونلی فنز/`. در **Git Bash این نام هش می‌شود** و `cd`/`git mv` مستقیم با خطای «No such file or directory» شکست می‌خورد. **راه‌حل اثبات‌شده:** از Python استفاده کن:

```python
import glob, os
proj = [c for c in glob.glob("03 - Projects/*/") if os.path.exists(c+"PROJECT-F-CONTROL-MANIFEST.json")][0]
# حالا proj رشتهٔ صحیحِ مسیر است؛ همهٔ عملیات فایل را با آن انجام بده
```

اگر بخواهی از CLI مستقیم بری، فقط دستورات داخلِ پوشه (`ls`, `pytest`) کار می‌کنند، نه path-as-argument با نام فارسی.

---

## ۱. وضعیت پروژه (تغییر نکرده — فقط مرور)

| شاخص | مقدار |
|---|---|
| **کسب‌وکار** | محتوای faceless فقط‌پا (فقط پا، بدون صورت/بدن/explicit)، legal adult، از استرالیا |
| **تیم** | دونفره ۵۰/۵۰: آری (Operator، ~۸-۱۰h/هفته) + صبا (Creator، ~۳h/هفته) |
| **فاز** | validation — **ZERO اجرای بیرونی**: هیچ اکانت، پست، DM، درآمد، مشتری، ترافیک واقعی |
| **GATE 0** | 🟡 **OPEN** (محل اقامت صبا ثبت‌نشده + تأیید مکتوب صبا روی توافق + سؤال آخر پرسشنامه) |
| **PAGE_SETUP** | 🔴 **NO-GO** (stamped 2026-07-20) |
| **PF_V5** | REVOKED (برنامهٔ تهاجمی لانچ باطل) |
| **BODY expansion** | ❄️ FROZEN (صبا رد کرد ۲۰۲۶-۰۷-۰۳؛ باز شدن فقط با dual consent) |
| **STOP-ORGANISM** | ❌ **وجود ندارد** در زمان این جلسه |
| **OCTOPUS** | زنده و در حال اجرا (port 8771، heartbeat امروز ok) اما پل PF→OCTOPUS flag-gated OFF |

### سه مسدودکنندهٔ اصلی GATE 0 (همه نیاز به تصمیم انسانی دارند):
1. **محل اقامت صبا** — ثبت Branch A/B با source-type (آری «A» attest کرده ولی فیلد نوع منبع خالی)
2. **تأیید مکتوب صبا** روی توافق ۱۲-بنده‌ای (آری امضا کرده، صبا هنوز نه)
3. **سؤال آخر پرسشنامه** — از سوی صبا اشتباه فهمیده شد، باز OPEN

> **هیچ ایجنتی حق ندارد GATE-STAMP را GO کند** بدون آن سه امضا. این قاعده در خود فایل stamp قید شده.

---

## ۲. این جلسه چه شد — بازآرایی ساختار (Reorg)

**مرجع حاکمیتی:** `SOURCE-OF-TRUTH-MATRIX.md` (تؤیید مالک ۲۰۲۶-۰۷-۱۲): «ریشهٔ canonical؛ docs/research آینهٔ stale». این بازآرایی فقط *اجرای آن حکم* بود — هیچ تصمیم جدیدی گرفته نشد.

### ۶ کامیت (هرکدام قابل revert):
```
62d2d4e  test(pf): REORG-LOG pytest — 366 passed/0 failed
a615263  docs(pf): MANIFEST files_registry + INDEX/HOME + REORG-LOG
fa042a0  reorg(pf): import 3 scattered files + sync _memory
6e8f952  reorg(pf): move 35 files to numbered folders (step 4)
57f5138  archive(pf): superseded v1 code → 09 - Archive
c9dabaa  cleanup(pf): remove junk + stale mirrors (step 1-2)
```

### نتیجهٔ کمی:
| | قبل | بعد |
|---|---|---|
| فایل پراکنده در ریشه | ۴۷ | **۱۲** |
| آینهٔ تکراری (docs/ + research/) | ۲۲ | **۰** |
| زبالهٔ دیسک | ~۳۷۴MB | **۰** |
| کد منسوخ در محل canonical | ۲ | **۰** |
| فایل گم‌شده بیرون از پروژه | ۴ | **۰** |
| تست pytest | — | **۳۶۶ passed / 0 failed** ✅ |

### جزئیات کامل در:
`[[00 - Control/REORG-LOG-2026-07-24|REORG-LOG-2026-07-24.md]]` — ردّ حاکمیتی کامل (چه حذف شد، چه جابه‌جا شد، چرا، با md5/transcript).

---

## ۳. ساختار جدید پوشه (نقشهٔ فعلی)

```
03 - Projects/اونلی فنز/
├── (۱۲ فایل در ریشه — code-coupled یا SoT؛ جابه‌جا نکن!)
│   ├── PROJECT.md            ← Active Context (کد langar_bot.py این را می‌خواند)
│   ├── OpenQuestions.md      ← (کد langar_bot.py می‌خواند)
│   ├── DecisionLog.md        ← (کد langar_bot.py می‌خواند)
│   ├── THREAD-CLOSURE-D-2026-07-10.md  ← (کد langar_bot.py می‌خواند)
│   ├── CLAUDE.md             ← منشور کاری (load_order)
│   ├── PROJECT-F-CONTROL-MANIFEST.json  ← قرارداد ماشین‌خوان (files_registry به‌روز شد)
│   ├── ACQUISITION-ENGINE-2026-07-05.md ← مرجع کانونی جذب (load_order)
│   ├── STATE-REPORT-2026-07-05.md       ← (load_order)
│   ├── HOME.md · INDEX.md · README.md   ← داشبورد/ناوبری ریشه
│   └── orchestrator.py       ← entrypoint کد
│
├── 00 - Control/      (۳۰ فایل) — gates، charter، handoffها، SoT-matrix، REORG-LOG، SCANها
├── 01 - Strategy/     (۱۴) — MASTER-BUILD، Playbook، blueprint، MONETIZATION، Fable5، master-reference، Identity/
├── 02 - Research/     (۱۳) — BASE-DATA-REPORT، RESEARCH-INTEGRATION ×۲، DECISION-MATRIX، COMPLIANT-PLAYBOOK، DECISIONLOG-ENTRIES، PROMPTS، research-prompts، research-track-BC، ARCHITECTURAL-SCAN، COMPETITOR-MARKET
├── 03 - Experiments/  (۱) — stub خالی
├── 04 - Content Studio/ (۳) — 30-Faceless-Clips، Content-Topics-Trends، _INDEX
├── 05 - Acquisition/  (۴) — AUTO-ACQUISITION-BLUEPRINT، Knowledge-Base-Memory، OCTOPUS-ACTUATION-ALIGNMENT، _INDEX
├── 06 - Ops & Runtime/ (۲۲) — LAUNCH-RUNBOOK، LAUNCH-SAFETY-NETS، LAYER2، AGENT-CONTROL-INTERFACE، PROMPT-NEXT، PROJECT-F-BRAIN-SPEC، PROJECT-F-FULL-REPORT، VERDICT_QUEUE، REGISTRY، RUNBOOK، KPI-DASHBOARD، props، logs، WEEKLY-BRIEF
├── 07 - Compliance & Privacy/ (۲) — OPSEC-ITEMS، _INDEX
├── 08 - Partner (PII)/ (۲) — 🔒 پرسشنامه صبا (PII — هرگز بیرون از پوشه)
├── 09 - Archive/      (۵) — superseded-code/ (dual_brain_v1، studio_telegram_v1، TELEGRAM-CONTENT-STUDIO v1+v2)
├── brain/  (۴۰) — پکیج پایتون: dual_brain_v3، learning، acquisition، store، guards، ab_tracker، kpi_dashboard، lifecycle، project_f_brain(runtime-dead)، content_engine، dm_pipeline، faq_engine، audit + tests
├── langar/ (۲۴) — پکیج پایتون: langar_bot، pf_admin، fan_admin، dm_admin، vault_admin، vault.json + specs
├── studio/ (۲۴) — پکیج پایتون: creator_studio، creator_brain، content_studio، affirm، studio_telegram_v3 + specs
├── pf_os/  (۳۹) — پکیج پایتون (incubating/قرنطینه، SHADOW_ONLY): api، brain، bridge، bridge_beat، config، cortex_client، events، learning_bus، loop، run_saba، saba_link، singleton + tests
├── tests/  (۱۹) — test_dm_hitl، test_langar_failclosed، test_layer2_integration، test_orchestrator_*، test_state_machines، test_store، test_warmup_guard، test_warning_kill
├── drafts-awaiting-gate/ (۶) — link-hub-copy، x-profile، tracking-link-design، ppv-ladder، kpi-dashboard-spec، msg-to-saba-question8
├── external-research-2026-07-05/ (۶) — reddit/x/content/of-funnel/opsec/100-topics
├── research-results/ (۱۴) — P1-P10 + 00/11/12/13 executive scans
├── _memory/ (۱) — onlyfans-project-memory-2026-07-05.md
├── _Archive/ (۳) — state snapshots
└── _inbox-other-projects/ (۲) — خارج scope (Ziman DM Bot، self-improvement)
```

---

## ۴. قواعد hard (نقض نکننی)

### ۴-۱. فایل‌های code-coupled (در ریشه بمانند — جابه‌جا نکن!)
این فایل‌ها توسط `langar/langar_bot.py` با مسیر نسبی `self.model.root / "FILE.md"` خوانده می‌شوند. اگر جابه‌جایشان کنی، تست‌ها می‌شکنند:
- `PROJECT.md` · `OpenQuestions.md` · `DecisionLog.md` · `THREAD-CLOSURE-D-2026-07-10.md`
- `drafts-awaiting-gate/kpi-dashboard-spec.md` (وجودش چک می‌شود)
- `drafts-awaiting-gate/` (کل پوشه)
- `Fable5/` (directory-existence check در langar_bot.py:298 — فعلاً وجود ندارد ولی چک می‌شود)
- `langar/upgrade_proposals/*.md` (glob در langar_bot.py:270)

### ۴-۲. قوانین قفل‌شدهٔ CLAUDE.md (تغییرناپذیر بدون verdict انسانی)
۱. فقط پا — بدون صورت/بدن/explicit
۲. geo-block کامل ایران در همه لایه‌ها
۳. پرداخت فقط داخل پلتفرم (نه P2P/crypto/PayPal)
۴. بدون نقض ToS
۵. privacy دوطرفه
۶. بدون fact جغرافیایی شهر-سطح در کپی عمومی (فقط «Aussie»؛ «Persian»/«Sydney» ممنوع تا حل سؤال #۹)
۷. کد Project-F بیرون از پوشه؛ صفر echo هویت/محتوا
۸. ۱۸+ و رضایت ثبت‌شده؛ محدودهٔ صبا بر همه حاکم
۹. body expansion FROZEN

### ۴-۳. autonomy level
- ✅ **خودکار تا حد ToS** (درون‌پوشه، برگشت‌پذیر): تحقیق، ساخت/ویرایش فایل، draft کپی، ثبت proposal در DecisionLog/OpenQuestions
- 🚫 **Hard-Gated (همیشه verdict انسانی + قفل GATE 0)**: ساخت اکانت، پست/DM، پرداخت، login واقعی، echo هویت صبا بیرون، تغییر قواعد قفل‌شده

---

## ۵. تناقض‌های باز (تصمیم مالک — این جلسه حل نشدند، عمداً)

| تناقض | وضعیت | مرجع |
|---|---|---|
| **نردبان قیمت** | ۳ نسخه (EXT-04 مرجح ولی owner-lock نشده) — tag CONFLICT باقی است | ACQUISITION-ENGINE §۴ vs Playbook §۴ |
| **نام برند** | OPEN — «Anar Soles» پیشنهاد #۱ ولی نهایی نشده | OpenQuestions #۶ |
| **«Persian»/«Sydney» در کپی** | opsec risk، حل‌نشده | OpenQuestions #۹ |
| **MASTER-BUILD ↔ Playbook** | دو سند master گاهی متفاوت | STATE-REPORT §۶ |
| **ساعت صبا** | SETTLED به ~۳h/هفته (۲۰۲۶-۰۷-۱۰) | — |
| **نقش Fansly** | SETTLED: mirror + discovery-first | OWNER-BALLOT Q7 |
| **block Australia geo** | OPEN | OpenQuestions #۱۹ |

> تا verdict، هیچ سندی سند دیگر را overwrite نکند — فقط reconcile-note.

---

## ۶. نکتهٔ مهم: تست‌ها (honesty discrepancy)

- **GATE-STAMP-2026-07-20** می‌گوید `TESTS_HONEST: 209/209` (عدد ثبت‌شده در forced-completion sprint).
- **اجرای من امروز (2026-07-24):** `python -m pytest brain/ langar/ studio/ pf_os/ tests/` → **۳۶۶ passed / 0 failed**.
- **دلیل اختلاف:** تست‌ها از ۲۰۲۰-۰۷-۲۰ تا امروز رشد کرده‌اند (زیرمجموعه‌های تستی c6 و دیگر اضافه شده).
- **من GATE-STAMP را به‌روز نکردم** (قاعدهٔ gate-abstention — هیچ ایجنتی حق تغییر stamp بدون امضا ندارد). اگر مالک عدد honest می‌خواهد، **او باید GATE-STAMP را با عدد جدید بازنویسی کند**، نه ایجنت.
- دستور اجرای تست از ریشهٔ پروژه با Python (به‌خاطر encoding نام پوشه):
```python
subprocess.run(['python','-m','pytest','brain/','langar/','studio/','pf_os/','tests/','-q'], cwd=proj)
```

---

## ۷. ادغام با OCTOPUS (وضعیت پیوند)

موجودیت OCTOPUS **زنده و فعال** است (port 8771، heartbeat امروز ok، ~۴۰ wiring beat). اما پل PF↔OCTOPUS **flag-gated OFF** است:

| نقطهٔ اتصال | وضعیت |
|---|---|
| Telegram → Langar bridge (`/pf_*` commands) | ✅ ACTIVE (تنها مسیر زنه) |
| pf_os → `saba-bridge.jsonl` (consumer) | 🟡 scaffold، consumer در wiring.py ساخته نشده |
| `pf_os/bridge_beat.py` | 🟡 آماده، flag OFF (`OCTOPUS_WIRE_SABA_BRIDGE`) |
| pf_os → Cortex HTTP | 🟡 آماده، flag OFF (`OCTOPUS_WIRE_PROJECTF_CORTEX`) |
| Budget organ PROJECT_F | 🟢 registered (floor $3/mo) |
| Business-brain observer | 🟢 propose-only |

**برای وصل کردن کامل:** (۱) یک خط import در wiring.py برای `saba_bridge_beat`، (۲) flip سه flag، (۳) ساخت Saba Studio bot token (BotFather). **همه نیازمند GO و Owner**.

---

## ۸. قدم‌های بعدی توصیه‌شده (به ترتیب اولویت)

1. 🔴 **(مالک، انسانی) بستن GATE 0:** با صبا تماس بگیر — (الف) محل اقامت/Branch، (ب) امضای توافق، (ج) پاسخ سؤال آخر. این تنها چیز واقعی است که پروژه را از NO-GO به GO می‌برد.
2. 🟡 اگر خواستی کد را وصل کنی: سه flag + یک خط wiring.py (مرحلهٔ OCTOPUS adapter). ولی هنوز `OCTOPUS_ADAPTER: SHADOW_ONLY` — ADR را ببین.
3. 🟢 اگر خواستی محتوا را فعال کنی: ۶ درفت آماده در `drafts-awaiting-gate/`، ۳۰ اسکریپت clip در `04 - Content Studio/`، ۲۲ دارایی در VaultBank. **همه نیازمند GO.**
4. ℹ️ اگر سند می‌خواهی: `LAUNCH-RUNBOOK-2026-07-16.md` در `06 - Ops & Runtime/` (مسیر جدید).

---

## ۹. فایل‌های مرجع (به این ترتیب لود کن)

```yaml
load_order:
  1: _memory/onlyfans-project-memory-2026-07-05.md   # حافظه فشرده
  2: STATE-REPORT-2026-07-05.md                        # وضعیت جامع
  3: CLAUDE.md                                         # منشور کاری (قواعد hard)
  4: PROJECT.md                                        # Active Context / Next actions
  # + این HANDOFF برای دانستن وضعیت پس از reorg
  # + REORG-LOG-2026-07-24.md برای ردّ کامل تغییرات
  # + GATE-STAMP-2026-07-20.md برای وضعیت gate
  # + SOURCE-OF-TRUTH-MATRIX.md برای اینکه بدانی کدام سند canonical است
```

---

## ۱۰. اگر خواستی بازآرایی را revert کنی

هر مرحله کامیت مستقل دارد. برای undo کامل:
```bash
git revert --no-commit 62d2d4e a615263 fa042a0 6e8f952 57f5138 c9dabaa
git commit -m "revert: full reorg rollback"
```
ولی **دلیل نمی‌بیند** — بازآرایی تست‌ها را نشکست (۳۶۶/۰) و هیچ محتوای واقعی را حذف نکرد.

---

*این سند supersede می‌کند: HANDOFF-NEXT-AGENT.md (2026-07-12)، ARCHITECTURE-COMPLETE-2026-07-20/10_HANDOFF_NEXT.md. آن دو قدیمی‌اند ولی برای تاریخچه در `00 - Control/` باقی می‌مانند.*
