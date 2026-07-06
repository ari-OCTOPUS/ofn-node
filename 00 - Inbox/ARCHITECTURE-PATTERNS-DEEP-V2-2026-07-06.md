---
type: report
status: final
tags: [architecture, patterns, hybrids, phase-4, phase-5]
created: 2026-07-06
language: persian
---

# 🧬 الگوهای معماری — پاسخ گسترش‌یافته V2 (Composite & Hybrid Focus)

> **دومین پاسخ:** آری با بیان «پاس قبلی آنها را مِس کرد» خواست کاوش عمیق‌تر. این سند **فقط الگوهای نو و ترکیبی‌های آری خودش طراحی‌شده** را نشانه می‌گیرد — نه تکرار Mycelial Topology و دوست‌های معروف.

---

## الگوهای جدید (10+1 نو در Pass 2)

### 1. **Allowlist-by-Content + Checklist Quarantine (PHASE-0A)**
- **نام فارسی:** قاعدهٔ سفیدفهرست‌سازی محتوایی + ربات قرنطینه
- **منبع:** `_memory/PHASE-0A-EXCLUSION-SPEC.md` (۲۰۲۶-۰۷-۰۴) + `00 - Inbox/GAP-ANALYSIS-2026`
- **مکانیزم:** ۴ درپورت سری: (۱) محدودهٔ مسیر (resolved absolute paths، نه glob)؛ (۲) قرنطینهٔ unconditional اگر نام فایل/مسیر در ROTATION_CHECKLIST ظاهر شود (gate بدون override)؛ (۳) gitleaks host-side (SCAN-UNAVAILABLE = توقف کامل، نه fallback regex)؛ (۴) سنجش کدینگ UTF-8. **نقض glob:** RTL Persian reordering (راهنمای_۰۵ vs ۰۵_راهنمای) glob را می‌شکند — حل: حتی تطبیق substring normalized NFC.
- **چرا قوی‌تر:** سه شکست‌نامهٔ سابق (checklist-named secret urldecoding، RTL glob fragility، SCAN-UNAVAILABLE downgrade) را در یک جایگاه حل می‌کند. ordered gates تضمین می‌کند: quarantine monotonic است، دنیا رزرو‌شدهٔ ۲ بر ۳.
- **نگاشت v2:** فاز ۴ (PHASE-0A نهایی‌سازی + gitleaks on Windows)؛ فاز ۵ (memory-layer خالص‌شده روی ingest-manifest).
- **نقش دقیق:** جایگزینی `BUILD-PROMPT § Phase 0a` که دنیل-گلب بود (شکست رایج).

### 2. **Dual-Manifest Ingest (Allowlist + Quarantine + Skipped-Encoding)**
- **نام فارسی:** سه‌پشتی Manifest (سبز، زردپیچیده، خاکستری)
- **منبع:** `PHASE-0A-EXCLUSION-SPEC.md §Outputs`
- **مکانیزم:** سه فایل JSON append-only در `_memory/`: (الف) `ingest-manifest` = فقط پاس‌یافتگان (sha256+mtime)؛ (ب) `quarantine-manifest` = gate۲ یا gate۳ catch‌شدگان (ردیف checklist ref یا regex ID، محتوا هرگز نه)؛ (پ) `skipped-encoding` = UTF-8 decode ناپذیرها. downstream (مرحلهٔ ۱+) فقط manifest سبز می‌خواند.
- **چرا قوی‌تر:** filesystem مجوز‌دهنده نیست (فایل حاضر=شامل؛ حاضر نیست=شامل نیست). Manifest = تنها منبع حقیقت. Re-derive ممنوع (drift ریسک). Append-only = تاریخچهٔ ثابت.
- **نگاشت v2:** فاز ۴ (Phase-0a manifests درست‌شده)؛ فاز ۵ (downstream از manifest تغذیه می‌شود).

### 3. **Budget Dual-Mode (Normal + Growth Escalation)**
- **نام فارسی:** بودجهٔ دوماهواره با escalation‌گیت
- **منبع:** `MASTER-ARCHITECTURE-SPEC-v1.4 §۳.۸` (D-25) + `MYCELIAL-MASTER-SPEC §۶.۸`
- **مکانیزم:** دو mode ترکیبی: (۱) Normal: $0.50/run · $2/روز (alert ۵۰/۸۰٪) · $60 hard-stop (halt)؛ (۲) Growth: $1/run · $10/روز · $300/ماه — entry = فرمان صریح انسانی + passphrase step-up. Logic خارج از prompt (config/db، نه پرامپت). سقفِ عادیِ پایین برای اجازه دادن به سناریوی سنگین تا **عمداً ناموفق شود** (fail-closed).
- **چرا قوی‌تر:** رشدِ مصرف = تصمیمِ آگاهانهٔ انسانی، نه خزشِ خاموش. Escalation عمداً موانع می‌سازد (passphrase) — رفتار ریسک‌پذیری را دیر کند.
- **نگاشت v2:** فاز ۴ (budget-gate gated روی autonomy L2); فاز ۵ (Fugu call = checked علیهِ growth-mode).

### 4. **Learned-Mutation Bounded Loop with 1/Day Cap + STOP-File Mirror**
- **نام فارسی:** حلقهٔ جهش‌یادگیری محدود با سقف روزانه + انعکاس فایلی
- **منبع:** `04 - Architect System/learning-engine/` contract + `RATIFIED-TASKS §learning-engine-loop` + `_memory/LEARNING-STATE.json`
- **مکانیزم:** (۱) MUTATION-WHITELIST = فقط 5 فیلد prompt (scaffold-specific، نه سیگنال/policy/secret)؛ (۲) هر mutant = commit PROMPT-v{N+1} در تاریخ/diff/ledger-ref؛ (۳) خط کشی: یک جهش/روز ماکسیمم، ledger_cursor = آخرین ردیف پردازش‌شده؛ (۴) اگر `STOP` فایل وجود دارد یا state.last_mutation_date == امروز → no-op + beat و exit؛ (۵) rollback: اگر ۲ اجرا متوالی خطا ثبت شود → بازگردان به v1 (anchor) و log revert.
- **چرا قوی‌تر:** ۴ مکانیسم جدا هم‌عمل: whitelist تنگ‌دستی، capping کاپِ روزانه (drift prevent)، STOP-file synchronous (human halt بی‌latency)، v1 anchor (rollback deterministic).
- **نگاشت v2:** فاز ۴ (learning-loop + MUTATION-WHITELIST ratified)؛ فاز ۵ (autonomous mutation applied).

### 5. **Anchor Ledger Hash-Chain (Append-Only Audit Log)**
- **نام فارسی:** دفتریِ لنگرِ زنجیری (رکورد تغییر ثابت)
- **منبع:** `MYCELIAL-MASTER-SPEC §۶.۷` (kill-switch + verdictها) + architecture docs (Anchor Ledger = رگ انتقال اعلام)
- **مکانیزم:** هر اقدامِ مالی/deploy/kill/promote = یک ردیف in `audit.jsonl`: {timestamp, actor, action, target, hash_of_prev_line, signature}. هیچ ویرایش/حذف; فقط append. Hash-chain (هر ردیف تاریخچهٔ قبلیِ checksum می‌دهد) ضد-tampering.
- **چرا قوی‌تر:** Blockchain-lite accountability بدون heavyweight؛ هر revert/promote/escalation قابل audit؛ صدور سند مالی.
- **نگاشت v2:** فاز ۴ (migration to Postgres journaling); فاز ۵ (صفر fallback موقعیت‌گیری).

### 6. **Stale-View Verification Protocol (Windows-Host Double-Check)**
- **نام فارسی:** پروتکلِ تأیید دیدِ کهنه (sandbox/host sync)
- **منبع:** `RATIFIED-TASKS §brain-focus-board` — dashboard_doctor.py fresh-inode check + Windows-side verify
- **مکانیزم:** (۱) Doctor (Python C:\Armin\…) نتیجهٔ raw/effective/suppressed می‌دهد؛ (۲) Brain-Pulse agent هر needs_source_verify (UTF-8 drift، index mismatch) را **Windows host side می‌خواند** قبل استفاده (stale-view sandbox FP ثابت شده در ledger); (۳) تنها منبع سرکوب = Doctor output، نه محلی override.
- **چرا قوی‌تر:** sandbox/host sync را حل می‌کند — معروف ترین صحنهٔ قضاوت‌شاهی در vault-based agentic. FP ledger‌شده (قابل نقض).
- **نگاشت v2:** فاز ۴ (doctor صریح); فاز ۵ (verify میانگام).

### 7. **Reflexion-Driven Self-Improvement (Evaluator-Optimizer Loop)**
- **نام فارسی:** حلقهٔ تأملی خودبهبودی (ارزیاب↔بهینه‌کننده)
- **منبع:** `MYCELIAL-MASTER-SPEC §۷` (نقد + diff + ledger + version بالا) + `EXPERIENCE-LEDGER` append-only درسها
- **مکانیزم:** (۱) ایجنت spec را می‌خواند (proposal)؛ (۲) نقدِ adversarial ۳ ضعفِ بالا (blast radius)؛ (۳) diff مشخص + دلیل = propose-only (implement نکند)؛ (۴) ردیف تکی ledger: | تاریخ | agent | critique | 3-diffs | ledger_entry |؛ (۵) version بالا (v0.1→v0.2); (۶) سپس انسان verdict = accept/reject.
- **چرا قوی‌تر:** هر عبور بهترِ سند را گوش می‌کند (نه خود‌اصلاحی). Adversarial = anti-Goodhart. Ledger proof.
- **نگاشت v2:** فاز ۴ (spec + reflex prompt); فاز ۵ (consensus روی improve).

### 8. **Typed-Frontmatter-as-Contract (Property Schema + .obsidian/types.json)**
- **نام فارسی:** فرانت‌متر تایپ‌دار به‌عنوان قرارداد
- **منبع:** `06 - Architecture Maps/Property Schema.md` + `.obsidian/types.json` enforcement
- **مکانیزم:** (۱) نوت frontmatter = شناسنامهٔ قرارداد (type, status, tags, created, updated، plus type-specific)؛ (۲) هر کلید خارج schema = خطا (ایجنت اختراع نمی‌کند)؛ (۳) status enum قفل‌شده (idea|active|paused|done|archived|inbox|draft|ready|superseded)؛ (۴) رابطه multitext: parent/aligns_to/extends/supersedes/created_by/sources (knowledge only ≥۲)؛ (۵) Obsidian-side enforcement `.obsidian/types.json` (Bases حساس حروف + enum validation).
- **چرا قوی‌تر:** frontmatter = machine-readable governance (نه توصیهٔ متن). Bases query روی schema. Drift غیرممکن (نوت invalid=detected فوری).
- **نگاشت v2:** فاز ۴ (schema enforcement strict); فاز ۵ (graph-query روی typed-frontmatter).

### 9. **EXPERIENCE-LEDGER Append-Only Verdicts (Self-Healing Log)**
- **نام فارسی:** لاگِ append-only درسها (خودترمیمی شفاف)
- **منبع:** `_memory/EXPERIENCE-LEDGER.md` (۱۵+ ستون) + تمام ratified tasks
- **مکانیزم:** هر ردیف: | تاریخ | task | kind (auto/propose/revert/observe/regress) | شرح | applied/pending | ledger_ref |. Append-only (هرگز edit). درس جدید (regress/observe) = dismiss/accept/escalate من انسان. شاخص استقلال = سهم applied/auto ÷ reset.
- **چرا قوی‌تر:** **تک** اثبات اجرا. Drift گیره (قابل و query). Verdict delay ممنوع (آنی ثبت یا nothing). Ledger = source-of-truth replay.
- **نگاشت v2:** فاز ۴ (EXPERIENCE-LEDGER متحد); فاز ۵ (decision-support روی ledger query).

### 10. **Fugu Integration 5-Point (F1–F5 Escalation Stack)**
- **نام فارسی:** ۵ نقطهٔ تلفیقِ Fugu (escalation‌سطحی)
- **منبع:** `MASTER-ARCHITECTURE-SPEC-v1.4 §۳.۲` + decision D-25
- **مکانیزم:** (۱) F1 = ستون ۳ خودمختار (TWO-BRAIN فاز ۴، پشت Gate+git+budget); (۲) F2 = memory synthesis/relation extract (propose-only); (۳) F3 = orphan rescue per-subtree (propose-only); (۴) F4 = ingest risk-class دومین (Gate ۳ second-net، propose-only); (۵) F5 = project decision support (propose-only). **بحرانی:** Fugu Ultra pool ثابت است (خریداری شد) → Project-F data **ممنوع** فیلتریت (C17) — فقط Fugu استاندارد opt-out provider یا محلی Claude.
- **چرا قوی‌تر:** escalation تدریجی (cheap اول) + explicitly gated (F1 alone require full L2/L3). Budget isolation (F1 vs F2–F5).
- **نگاشت v2:** فاز ۴ (F5 propose-only + budget-gate); فاز ۵ (F1 autonomous pشت L3).

### 11. **Two-Brain Control: Durable Split (Perception + Verdict) with Async Heartbeat**
- **نام فارسی:** کنترل دومغزی با دقّ‌ضربان غیرهمگام
- **منبع:** `TWO-BRAIN-CONTROL-BLUEPRINT.md` + `RATIFIED-TASKS §HEARTBEAT`
- **مکانیزم:** (۱) ادراک (SYSTEM-STATE از روز): دکتر health + fleet status + gates + ledger digest؛ (۲) Verdict (انسان): فقط آری (نه LLM)، فقط پس از read HANDOFF + Brain؛ (۳) اعمال (پشت gate+git)؛ (۴) سنجش: fitness + reconciliation؛ (۵) دقّ‌ضربان: هر ratified task در `_memory/HEARTBEAT.md` یک سطر (timestamp سیدنی + نتیجهٔ یک‌خطی). سکوت >۲×دوره = regress ledger. دکتر از Heartbeat می‌خواند: beat غایب = monitor (تسک pre-approve نشده‌اند).
- **چرا قوی‌تر:** دو مغز **هم‌زمان** می‌بینند (dashboard زنده). Verdict latency کاپ‌شده (ادراک → verdictbotch → timeout=DENY). Heartbeat = لایهٔ صحت‌آزمایی fleet.
- **نگاشت v2:** فاز ۴ (دکتر + دقّ‌ضربان مستقل); فاز ۵ (Two-Brain runningمکمل).

---

## هایبریدهای شناخت‌شده (5 Composite Patterns)

### Hybrid #1: **Inbox-First × Allowlist-Scan × Quarantine-Gate**
- **کامپوزیشن:** قانون اساسی Inbox-first (routing تصمیم) + PHASE-0A allowlist (qualified candidates فقط) + Gate۲ قرنطینهٔ unconditional (نام لیست شده = **بدون condition** bypass)
- **اجزا:** 
  - (الف) Inbox تمام ورودی گرفت (00-Inbox یا 10-Telegram)
  - (ب) درخت تصمیم routing: پروژه شناسان‌شده → PROJECT.md · نو → template · دانش → 07 · person → 09 · مبهم → idea
  - (پ) ingest eligibility = PHASE-0A Gate۱–۴
  - (ت) اگر fail۲ (یا ۳)→ quarantine manifest (نه delete/ignore)
  - (ث) downstream پس از شروع memory-layer فقط از ingest-manifest می‌خواند
- **چرا این ترکیب قوی:** Inbox = واحد single-funnel (بدون پاشنده‌های موازی). allowlist = صریح (نه فرضی). Gate۲ = hard-gate = **نهایی بدون appeal** تا rotation. سه لایه جدای اقدام (دریافت، screening، filtering) بدون entanglement.
- **کجای v2:** فاز ۴ (PHASE-0A ratified)؛ فاز ۵ (Inbox purity).

### Hybrid #2: **Mutation-Whitelist × Ledger-Ref × Rollback-Anchor (Learning-Loop Safe-Mutation)**
- **کامپوزیشن:** MUTATION-WHITELIST = کدام فیلدها (۵ تنها scaffold-target) × LEARNING-STATE ledger-cursor (کجا می‌خوانیم درسها) × PROMPT-v1 anchor (rollback deterministic)
- **اجزا:**
  - (الف) whitelist = 5 فیلد فقط (نه سیگنال، policy، secret، model-weight)
  - (ب) loop جهش: ledger-cursor → بخوان ردیفهای نو → یک درس واقعی (شاهد) یا skip
  - (پ) mutant = PROMPT-v{N+1} = v{N} copy + یک edit + {timestamp, diff, ledger-ref, reason}
  - (ت) state = last_mutation_date, mutation_count, version, ledger_cursor
  - (ث) rollback if ۲ consecutive fails → بازگرد به v۱
- **چرا این ترکیب قوی:** whitelist = anti-scope-creep. ledger-ref = drift-proof (هر جهش از کدام درس؟ چرا؟). v۱ anchor = **replay-able** rollback (نه "last seen version").
- **کجای v2:** فاز ۴ (learning-engine blueprint + ratified); فاز ۵ (autonomous 1/day application).

### Hybrid #3: **Dual-Mode-Budget × Escalation-Gate × Anchor-Ledger (Financial Governance)**
- **کامپوزیشن:** Mode-select (Normal vs Growth + passphrase) × alert/ceiling + halt خودکار × Anchor Ledger signing per spend
- **اجزا:**
  - (الف) Normal = $0.50/run · $2/day alert · $60 hard-stop
  - (ب) Growth = entry via human command + passphrase; $1/run · $10/day · $300/month
  - (پ) Both logged: Anchor Ledger ← {timestamp, mode, spend, cumulative, action}
  - (ت) Over-cap = halt + AGENT_QUESTIONS + صفر automatic resume
- **چرا این ترکیب قوی:** Mode escalation = تصمیم آگاه (نه خزش). Ledger = تاریخچهٔ اعتبار (مالی). Halt hard (نه warning) = fail-closed.
- **کجای v2:** فاز ۴ (budget-gate اجرای Fugu); فاز ۵ (حسابرسی ledger).

### Hybrid #4: **Schema-Frontmatter × Live-Dashboard × Query-Driven Graph (Knowledge Contract)**
- **کامپوزیشن:** Property Schema = typed frontmatter + `.obsidian/types.json` enforcement × Brain/Brain-Focus-Board (real-time HTML render) × dashboard_doctor.py zero-LLM
- **اجزا:**
  - (الف) Schema فقط entity types + status enum + رابطه fieldها
  - (ب) Types.json در Obsidian = enum validation + Bases query روی frontmatter
  - (پ) Brain.md = html render از Active Contexts + vault metric (doctor raw_score)
  - (ت) Dashboard_Doctor = Python zero-LLM = validator pass + metric compute + hash-diff = نوشتن؟
- **چرا این ترکیب قوی:** frontmatter = machine-readable (نه متنی). typed = validation خودکار. graph query = صفر دستی extraction (نه wikilink regex‌گردانی). dashboard realtime (refresh ۶ ساعت).
- **کجای v2:** فاز ۴ (schema strict enforcement); فاز ۵ (query-driven).

### Hybrid #5: **HEARTBEAT-Check × Fleet-Selection × Evaporation-TTL (Fleet Health Loop)**
- **کامپوزیشن:** HEARTBEAT.md per-task (timestamp ۳ ساعت ۲۴ beat = alive؟) × fleet-selection (quality evaluate) × mycelial-consolidator (evaporation scouts >14 روز)
- **اجزا:**
  - (الف) HEARTBEAT: ۱۵+ ratified task, هرکدام سطر = [timestamp sydney + result line]
  - (ب) Silence >2×period = regress ledger
  - (پ) Fleet-selection weekly: دیجسته‌های تازه کیفیت‌سنجی کن + retire/re-arm recommend
  - (ت) Mycelial-consolidator nightly: >14d scout → archive (evaporation)
- **چرا این ترکیب قوی:** Heartbeat = synchronous health (بی دیجست پولی). Fleet-select = async quality (هفتگی). Evaporation = TTL مستقل (۱۴d default). تثلیث سطحهای نمایش‌دهی: instant (beat)، weekly (quality)، auto (TTL).
- **کجای v2:** فاز ۴ (HEARTBEAT + fleet-eval ratified); فاز ۵ (retire/spawn decisions).

---

## جدول DECISIONS (استخراج D-01..D-29 از DECISIONS.md)

| ID | تصمیم | قاعدهٔ v2 Portable |
|---|---|---|
| D-01 | رئیس‌کل = انسان (یا نرم‌افزار propose فقط) | هیچ autonomy بدون verdict انسانی |
| D-02 | 5 اجزای core (نه 15) | معماری capacity ~۵ = تک اپراتور |
| D-03 | حذف Wilson score، execution-rings، FUSION از MVP | MVP-first = governance گیم‌نباز ندارد |
| D-04 | Observability = OpenLLMetry+MLflow (نه Langfuse) | ClickHouse acquisition = migrate |
| D-06 | Kill-switch = `halted` DB flag + STOP file mirror | fail-closed: دو منبع حقیقت sync |
| D-07 | HybridRetriever BM25+TF-IDF موجود (dormant) | کد > سند: code-as-spec |
| D-08 | مدل = `claude-haiku-4-5-20251001` | کد > جدول قیمت |
| D-09 | Raw API الان → SDK cautious → LangGraph exit-only | Lock-in < portability |
| D-10 | Crypto mining: analysis free، exec hard-stop | Autonomous analysis، human financial |
| D-11 | کلید کریپتو = off-box مکمل | صفر LLM near-signing |
| D-13 | Approval timeout = DENY (نه suspend) | Fail-closed > suspend |
| D-14 | Policy engine = allowlist table (نه OPA) | Simplicity > formalism (P7) |
| D-16 | نسبت routing = 70/25/5 | Cost vs quality ratio |
| D-17 | حلقهٔ خودبهبودی ≥50 trajectory | Cold-start threshold |
| D-18 | Eval set = anchor ثابت + رشد ماهانه | Anti-Goodhart: anchor lock |
| D-21 | Fusion loop = الگوی مرجع (نه ACE) | Code > proposal |
| D-25 | بودجهٔ hard-stop = AU$30/ماه API | Cost cap قطع نشدنی |
| D-28 | مغز upgradable با gated model-swap | Model selection = human verdict + canary |
| D-29 | Vault sync = Obsidian+Syncthing (نه git) | E2E+privacy |

---

## 5 توصیه تیز فاز ۴ (پیاده‌سازی)

### 1. **PHASE-0A Finalize + Gitleaks-on-Windows (P0 Blocker)**
- **دقت:** `_memory/PHASE-0A-EXCLUSION-SPEC.md` کامل است؛ اجرای gitleaks از Windows (نه sandbox) پیش‌شرط.
- **دلیل:** Quarantine-Gate۲ فقط کارکرد دارد تا ingest-manifest معتبر باشد. Sandbox gitleaks FP است.
- **کد:** Phase-0a runner → gitleaks host → triplet manifests → ingest-manifest = source-of-truth phase 1+.

### 2. **Learning-Loop Autonomy بندی (Cap ۱/day + STOP-file)**
- **دقت:** `learning-engine/MUTATION-WHITELIST` + `LEARNING-STATE.json` + anchor v1 PROMPT.
- **دلیل:** mutation unbounded = drift. ۱/day = prevent خزش ولی allow learning.
- **کد:** learning-engine-loop cron + ledger-ref check + version auto-increment.

### 3. **Anchor-Ledger Journaling (Phase-0a → Postgres DBOS-style)**
- **دقت:** اجازت دهید that `audit.jsonl` = source، append-only forever. هر action (ingest/deploy/promote/revert) = ledger row.
- **دلیل:** Accountability + rollback determinism.
- **کد:** Postgres INSERT audit trigger + hash-chain + signature verify on read.

### 4. **HEARTBEAT + Fleet-Selection Merge (Weekly Sanity)**
- **دقت:** `_memory/HEARTBEAT.md` = per-task beat؛ `fleet-eval.md` = quality + retire/arm recommendations.
- **دلیل:** Decouple صحت (instant beat) از کیفیت (async eval) از TTL (mycelial evaporation).
- **کد:** Brain-pulse (3h) beat-update → fleet-selection (weekly) quality → mycelial-consolidator (nightly evaporation).

### 5. **Fugu F5 Propose-Only + Budget Integration**
- **دقت:** F5 = project decision support, propose-only فقط. F1 (autonomous) = pشت L3 + budget-gate (Phase 5 فقط).
- **دلیل:** Escalation stack = security by layering.
- **کد:** Fugu client → budget-check → permit-check → call (با noop-on-quota).

---

## خلاصهٔ ۱۰ خطی

**الگوهای نو (Pass 2):** Allowlist-by-Content + Dual-Manifest · Dual-Mode Budget · Bounded-Mutation + Ledger · Anchor-Ledger Hash-Chain · Stale-View Verify · Reflexion Loop · Typed-Frontmatter Contract · EXPERIENCE-LEDGER Append · Fugu 5-Point.

**هایبریدهای بسته‌شده:** (۱) Inbox×Allowlist×Quarantine | (۲) Whitelist×Ledger×Anchor | (۳) Budget×Escalation×Ledger | (۴) Schema×Dashboard×ZeroLLM | (۵) Heartbeat×Fleet×TTL.

**معادل فاز ۴:** PHASE-0A + Learning-Loop نهایی + Anchor-Ledger · Fazy ۵: autonomy L2/L3 + Fugu F1.

**شمار:** 11 الگوی نو + 5 هایبرید = 16 نیمه‌ساختار معاصر.

---

**وضعیت:** درج مکمل بر اساس vault 2026-07-06 · آری‌دار یافتهٔ خاص (C17، D-25، gitleaks، learning-loop، فاز-بند‌سازی).

