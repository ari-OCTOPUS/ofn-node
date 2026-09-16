# SESSION-HANDOFF — 2026-07-23 (مسیر تا فعال‌سازیِ اصولیِ اختاپوس)

> برای ایجنتِ بعدی. **منبعِ حقیقتِ ماشین‌خوان: `EXECUTION-STATE.json` (همین پوشه).** این سند
> «چرا/چطور»ی است که JSON نمی‌گوید. هر خط یا `[FACT]` (اجراشده/commit‌شده) است یا `[OPEN]`. هیچ green-lie.

---

## ★ به‌روزرسانیِ پایانِ جلسه (2026-07-23): PHASE-0 CANDIDATE کامل شد

کلِ مأموریتِ Phase-0 در همین جلسه تا مرزِ مالک رفت. HEAD نهایی سریِ `895c452`+ روی
`blocker-fixes-2026-07-22`؛ live `F:\backup` هنوز دست‌نخورده روی `05d2b5a`.

- **[FACT] C5** `7dfe991` · **C6** `c28a810` · **C7 money caller-migration** `bd908f3`
  (مسیرِ approve تلگرام حالا با bindingِ دقیقِ C4 پول را release می‌کند؛
  `test_telegram_channel`/`test_telegram_rfc_router`/`test_lead_effect_gate` بدونِ تغییر سبز).
- **[FACT] D1/D2** merged `8f417f3` · **D3/D4/D5** `07859f5` (halt سراسری هر provider/effector/
  writeback/launcher را رد می‌کند؛ سناریوی زمانِ مجازی: settled-count بایت‌به‌بایت یکسان، بدونِ duplicate).
- **[FACT] PRE-0** `fdfb58e`: ۱۰ invariant از نقاطِ ورودِ واقعی (`test_pre0_real_entry` 27/27).
- **[FACT] full-C-gate**: `run_sandbox_suite.py --full` → **263/263**، barrier: 0 live-write، 0 network
  (GATE-2 حل شد؛ دیگر ریسکِ live-boundary نیست).
- **[FACT] red-team** `1110b94`: ۱۴ ایجنتِ خصمانه → ۴ تأییدشده (۱ P1: owner-gate روی
  `/panic /resume /stop`؛ ۳ P2) همه fix‌شده؛ ۳ رد؛ ۳ suspect در Owner Packet ثبت.
- **[FACT] Owner Packet** `895c452`: `OCTOPUS-PRIME/phase-0/OWNER-PACKET-2026-07-23.md`.

**قدمِ بعدی دیگر کدنویسی نیست — تصمیمِ مالک است** (Owner Packet §12: merge؟ · GST/LEAD-REV · سخت‌سازیِ
capability_gate halt برای Phase-1A). هیچ merge/DB/flag/restart/effect انجام نشد. باقیِ این سند
تاریخچهٔ C1–C5 است (برای زمینه)، ولی وضعِ فعلی همین بخشِ ★ است.

---

## ۰. تصویرِ کلان — دو لایه که هرگز قاطی نشوند

| لایه | مکان | وضع |
|---|---|---|
| **اختاپوسِ زنده** | `F:\backup` (master `05d2b5a`) | زنده و در حالِ اجرا (organism/cortex/live-server + مرکزِ تلگرام). **یک بایت تغییر نکرده.** |
| **جراحیِ ایمنیِ Phase-0** | `F:\octopus-phase0-isolated` (branch `blocker-fixes-2026-07-22`) | candidate — **merge‌نشده، فعال‌نشده.** اینجا جراحی می‌شود. |

**فعال‌سازیِ اصولیِ جدید = وقتی Phase-0 کامل شود → Owner Packet → رأیِ merge مالک → deploy.** نه زودتر.
درختِ زنده دست‌نخورده و امن است؛ همهٔ جراحی در اتاقِ عملِ ایزوله انجام می‌شود.

---

## ۱. مأموریتِ اصلی — Phase-0 C→D→PRE-0 (جایی که باید ادامه دهی)

مسیر: `C1→C6 → full-C-gate → D1→D5 → PRE-0 reachability → adversarial red-team → OWNER PACKET`.
هیچ live-action تا مرزِ مالک.

### وضعِ دقیقِ C-block (این جلسه پیش رفت)
| مرحله | commit | وضع | مدرک |
|---|---|---|---|
| C1 schema-migration framework | `32db70b` | `[FACT] VERIFIED` | `test_chrono_schema_migration` 7/7 |
| C2 v1→v2 binding columns | `9776c02` | `[FACT] VERIFIED` | همان تست |
| C3 idempotent request | `1f3ebae` | `[FACT] VERIFIED` | `test_effector_idempotency` |
| **C4 exact per-effect auth** | **`82fd1f6`** | `[FACT] VERIFIED` | `test_c4_exact_authorization` 18/18 |
| **C4.1 close E4 id-only bypass** | **`9f9a6dd`** | `[FACT] VERIFIED` | `test_c41_e4_id_only` 10/10 |
| **C5 CAS execution** | **`7dfe991`** | `[FACT] VERIFIED (2026-07-23)` | `test_c5_cas_execution` 33/33 + regression cluster green |
| C6 receipt/reconciliation | — | `[OPEN] ← active` | — |
| full-C-gate · D1-D5 · PRE-0 · red-team · owner-packet | — | `[OPEN]` | — |

### C4/C4.1 چه کردند (money-safety، مهم)
- **C4:** `_BATCH_RELEASE_KINDS` دیگر `"pay"` را ندارد (`_E4_MONEY_KINDS={"pay"}`). تابعِ نو
  `EffectorGate.release_effect(effect_id, approval)` = تک‌UPDATEِ اتمیک با bindingِ کامل در WHERE
  (id + content_hash + action_kind + target_ref + approval_idِ تک‌مصرفه/anti-replay + expiry + kill).
  یک approvalِ عمومی (بدونِ effect_id) **صفر پول** آزاد می‌کند.
- **C4.1 (سوراخی که معمار گرفت):** batch بسته بود ولی یک **bypassِ تک‌اثری** ماند —
  `release_one(effect_id)` می‌توانست یک effectِ پول را فقط با id (بدونِ binding) آزاد کند.
  حالا `release_one` **پول را رد می‌کند** (پول فقط از `release_effect`)؛ money-rowِ legacyِ بدونِ binding
  → `NEEDS_OWNER_REVIEW`؛ و `release_effect` مرجعِ لجرِ انسانی (`release_ref`) را **اجباری** می‌کند
  (approval_id به‌تنهایی authority نیست). **درسِ کلیدی: کدِ effectorِ پول سوراخ‌های ظریف دارد که فقط
  با پاسِ سلایس‌به‌سلایسِ مرورشده پیدا می‌شوند — هرگز C4-C6 را یک‌نوبته cram نکن.**

### C5 — قدمِ بعدی (طرحِ آماده)
`settle` الان `SELECT→blind-UPDATE` است (TOCTOU). C5:
- migration v4 (additive، fixture-only): `execution_id, execution_started_at, execution_finished_at,
  execution_worker_ref, external_receipt_ref, failure_reason` + statusِ `EXECUTING` به CHECK.
- state machine: `pending(=PENDING) → releasable(=AUTHORIZED) → EXECUTING → settled(=SUCCEEDED)`
  (+ REFUSED/EXPIRED/LEGACY_UNBOUND/NEEDS_OWNER_REVIEW/FAILED_SAFE/RECONCILE_REQUIRED).
- claim اتمیک: `UPDATE ... SET status='EXECUTING', execution_id=? WHERE effect_id=? AND status='releasable'` → rowcount==1.
- commit: `UPDATE ... SET status='settled', external_receipt_ref=? WHERE ... AND status='EXECUTING' AND execution_id=?`.
- هیچ SELECT-then-blind-UPDATE؛ هیچ `PENDING→SUCCEEDED`؛ دو executor یک برنده؛ workerِ stale نمی‌تواند finalize کند.
- تست‌ها: two-executors-one-winner · stale-worker · duplicate-claim · wrong-execution-id · duplicate-completion
  idempotent · no-direct-pending→succeeded · halt-before/during · migration v4 twice · rollback→v3 · future-fails-closed.
- commit: `c5-cas-effect-execution`.

---

## ۲. پروتکل‌های اجرا (این‌ها را رعایت کن وگرنه خراب می‌کنی)

### Single-writer lease
`WRITER-LEASE.json` (همین پوشه). **قبل از هر edit:** ثابت کن هیچ writerِ دیگری فعال نیست —
`git worktree list` (فقط یک worktree)، بی‌قفل (`.git/index.lock`)، صفر پروسهٔ python روی این repo،
آخرین commit کهنه. اگر writerِ دیگری بود → `BLOCKED-CONCURRENT-WRITER`، به branch مشترک commit نزن.
lease را ACTIVE کن؛ در پایان RELEASED. (تاریخِ jsonها را با `date` بگیر — نه Date.now در workflow.)

### اجرای امنِ تست (حیاتی — وگرنه به درختِ زنده می‌زنی)
```bash
cd "F:/octopus-phase0-isolated/_ops/tests"
export REAL_VAULT="F:\octopus-phase0-isolated"   # حتی خواندنِ read-only به isolated برود، نه F:\backup
export PYTHONIOENCODING=utf-8
python -X utf8 <test>.py
```
`harness.setup()` خودش `ORG_ROOT`/`OPS_DIR` را `tempfile.mkdtemp` می‌کند (hermetic، بی‌DBِ زنده).
**بدونِ REAL_VAULT-pin، `opslib.ORG_ROOT` پیش‌فرض = literal `F:\backup`** → خطرِ نوشتن روی درختِ زنده.
⚠️ **full-C-gate blocker:** یک launcherِ ایزولهٔ امن برای کلِ ۲۵۱ تست هنوز `[OPEN]` است؛ `run_all`ِ خام
ریسک دارد. ساختِ آن launcher بخشی از C-gate است.

### commit
فقط فایل‌های همان سلایس را `git add` کن (نه `_ops/state/school-awareness.json` که runtime-churnِ از-پیش‌موجود است).
⚠️ **AV lockِ روی `.git/objects`** → `git add/commit` گاهی «Permission denied» می‌دهد → `sleep 3` و retry.

### گوچاهای دیگر
- **worktreeِ کاری از master عقب است** (~۵۷۴ خط) — همیشه روی `master 05d2b5a` / repoِ فعلی verify کن، نه HEADِ worktree. (اسکنِ روی درختِ عقب‌مانده شواهدِ کهنه می‌دهد — درسِ genome-scan.)
- `harness.setup()` یک dict برمی‌گرداند، نه os.environ.

---

## ۳. سایر رشته‌های این جلسه (context کامل)

### الف) آشتیِ بیانِ ژنوم — `FROZEN_NON_OPERATIONAL_APPENDIX`
دیپ‌اسکنِ ۱۹-ایجنته ادعا کرد اختاپوس «بیشتر می‌نویسد تا بخواند». آشتیِ فقط‌خواندنیِ ۱۷-ایجنته روی master:
**۱۰ از ۱۷ ادعا رد/تصحیح شد.** سه تصحیحِ کلیدی: عصبِ پاداش ازقبل سیم است (کامیت `484bafd`)؛ رفلکسِ سلامت
L3-control است نه read-only؛ لجرِ ژنوم write-only نیست (هر ضربان توسط `telemetry.read_genome` خوانده می‌شود).
ژن‌های واقعاً خفته (کاندیدِ Phase-1B): email (C-06)، ingest (C-04)، code_autonomy (C-09). کدِ مرده: `values.yaml` governance، Hebbian query API.
اسناد (candidate، منتظرِ owner-approved merge — **در F:\backup مستقیم اصلاح نشد**): `scratchpad/candidate/genome-expression/`
(RECONCILIATION.md + REGISTER.csv + CLAIMS.json + INTEGRITY.json + `test_analysis_artifact_encoding` 6/6).
⚠️ `TIMESTAMP-CONSISTENCY-RISK = OPEN/P2` (کلِ جلسه 07-17 مهر خورد ولی ساعت 07-23 است؛ بازنویسیِ انبوهِ retro **مجاز نیست**).

### ب) `octopus-prime-labs` — اعصابِ unwired (اثبات‌شده GREEN)
بستهٔ مستقلِ ایجنتِ موازی در `F:\backup\03 - Projects\octopus-prime-labs`: Context Assembly (data/instruction fence)،
Knowledge Leg کاندید، Epistemic Reader، AST Reachability Analyzer (`EXISTS≠WIRED≠REACHABLE`)، verification/claims
contracts، experiment/lineage/fleet، shadow controller. **این جلسه اعتبارسنجی شد: pytest 43/43 + ruff clean +
`test_no_runtime_coupling` (صفر importِ `_ops`).** کتابخانهٔ خالص، **NO-GO برای runtime**، بنیادِ Phase-1B+.
inert است (روی درختِ زنده ولی صفر import به `_ops` → ارگانیسم را لمس نمی‌کند).

### ج) کارِ لایهٔ زندهٔ همین جلسه (روی F:\backup، از قبلِ Phase-0)
- **مرکزِ فرماندهیِ تلگرام** زنده شد (گروه، /menu، مکثِ تک‌پا، /budget، /revenue، دو-باتی، ترمزِ اضطراری آزاد).
- **قلبِ پول فاز ۱+۲**: resync پاکت‌اسمیت، `deposits_export` (۹۵ واریزی draft)، `claims_backfill`، تستِ e2e. فاز ۳ منتظرِ مالک.
- **Proposal Router** (G1/G3، commit `c4ed669`) + عصبِ پاداشِ سیم‌شده.
(این‌ها روی درختِ زنده‌اند؛ ربطی به جراحیِ ایزولهٔ Phase-0 ندارند.)

---

## ۴. مرزِ زندهٔ سخت (تا پایانِ Phase-0 ممنوع)
merge به `F:\backup` · باز/مهاجرتِ DBِ زنده · تغییرِ flag · restart · پاک‌کردنِ STOP/HALT · ارسالِ تلگرام ·
PocketSmith/provider · تغییرِ scheduled-task · **فعال‌سازیِ قابلیتِ خفته** · code self-apply · حذفِ backup/worktree.
پایان = فقط **Owner Packet** (repo/branch/HEAD، رنجِ commit، تست‌ها+شمارش، احکامِ C/D/PRE-0، رأیِ reviewerها،
شواهدِ zero-live/network، migration preview، backup/rollback، ترتیبِ deploy، downtime، smoke، canary/rollback trigger).

---

## ۵. قدمِ بعدیِ دقیق
```
1. lease بگیر (ثابت کن concurrent-writer نیست).
2. EXECUTION-STATE.json را بخوان → active_milestone = C5_CAS_EXECUTION.
3. C5 را طبق §1 بزن (migration v4 + CAS + تست‌های همزمانی) → commit c5-cas-effect-execution.
4. بی‌توقف C6 → full-C-gate (+ ساختِ safe launcher) → D → PRE-0 → red-team → Owner Packet.
5. هر سلایس: یک writer، تستِ هدف‌مند + regression، یک commit، EXECUTION-STATE آپدیت.
6. فقط BLOCKED (با repro دقیق) یا PHASE-0 CANDIDATE READY گزارش کن.
```
**مسیرِ اصولیِ فعال‌سازی: Phase-0 کامل → Owner Packet → رأیِ مالک → merge → deploy → سپس Phase-1B (بیانِ ژن‌های خفته با ladder).**
اختاپوس نه با افزودنِ مغزِ بیشتر، بلکه با **بستنِ امنِ اعصاب و عبورِ اثبات‌شده از دروازه‌های ایمنی** اصولی زنده می‌شود.
