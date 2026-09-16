---
type: architecture
status: superseded
tags: [governance, architecture, learning-engine, fugu-integration]
created: 2026-07-06
updated: 2026-07-06
superseded_by: "[[04 - Architect System/architect/04-Docs/2026-07-06 0245 MASTER-ARCHITECTURE-SPEC-v1.4-draft]]"
---

> [!note] ثبت ایجنت (Inbox-first)
> متن آری، آپلود 2026-07-06. نرمال‌سازی هنگام ثبت: frontmatter با [[06 - Architecture Maps/Property Schema|Property Schema]] سازگار شد (کلیدهای اصلی: type: architecture-spec · revision: v1.3 · owner: آری)؛ wikilink به نوت‌های غایب (`SELF-LEARNING-LOOP-SPEC` — در vault نیست) به متن ساده تبدیل شد؛ ۴ خطای تایپی مدل مبدأ اصلاح شد. تا verdict آری: **proposal، نه canonical.**


# MASTER-ARCHITECTURE-SPEC — نقشهٔ نهایی معماری یکپارچه

> این سند مقدمهٔ canonical معماری است. ترتیب برتری مرجعیت:
> `PROJECT_INSTRUCTIONS` (قانون اساسی) > locked rules > domain-governing docs (مثل `ACQUISITION-ENGINE`) > master-build/playbook > proposals (این سند، `TWO-BRAIN`، `PHASE-0A` تا ratify) > templates > memory-synthesis.
> هر ادعای فراتر از فایل‌های آپلودشده با برچسب «استنباط» یا «VERIFIED/UNVERIFIED» مشخص شده. هیچ تضاد یا ریسک امنیتی نرم‌سازی نشده.

---

## ۰. خلاصهٔ اجرایی

این مجموعه یک **سیستم‌عامل شخصی agent-first و vault-based** برای یک اپراتور تنها (آری، سیدنی، فارسی‌زبان) است؛ یک Vault ابسیدین که به‌جای ذخیره‌سازی صرف، چرخهٔ عملیاتی زنده با حاکمیت، حافظه، کنترل و امنیت است. ساختار سه‌خازنه است: (۱) حاکمیت (`PROJECT_INSTRUCTIONS`)، (۲) کنترل دو‌مغزی پیشنهادی (`TWO-BRAIN`)، (۳) بازبینی و اصلاح ingest (`REVIEW` + `PHASE-0A`)؛ در کنار پنج قالب زنده و یک نمونهٔ حافظهٔ پروژهٔ واقعی (Project-F).

سیستم در حال گذار است: لایهٔ governance کامل و canonical است؛ لایهٔ control در حال شکل‌گیری (`status: draft`)؛ لایهٔ memory/ingest در حال سخت‌شدن. **نسخهٔ v1 این سند یک لایهٔ جدید اضافه می‌کند: یکپارچه‌سازی Sakana Fugu API به‌عنوان موتور ستون ۳ (حلقهٔ فکری خودمختار)**، که در چندین نقطهٔ معماری برای تقویت هوشمندی فراتر از حد به‌کار گرفته می‌شود — اما همیشه پشت گیت‌های امنیتی خودِ سیستم.

---

## ۱. نقشهٔ لایه‌ها

```
┌──────────────────────────────────────────────────────────────────┐
│  L1 GOVERNANCE          PROJECT_INSTRUCTIONS.md (constitution)     │
│  (human-only edit)      rules · folders · lifecycle · security      │
├──────────────────────────────────────────────────────────────────┤
│  L2 CONTROL (draft)     TWO-BRAIN-CONTROL-BLUEPRINT.md              │
│  human + دکتر           L0–L3 ladder · 6-step loop · phases         │
│         ↑ Gate + git (BOTH OPEN) ↑                                  │
├──────────────────────────────────────────────────────────────────┤
│  L2b EXTERNAL INTELLIGENCE   Sakana Fugu API (Tokyo) [VERIFIED]     │
│  (engine of ستون ۳)        multi-agent orchestration, OpenAI-comp. │
│         ↑ human-only external + budget + Gate + git ↑              │
├──────────────────────────────────────────────────────────────────┤
│  L3 INGEST/SECURITY     PHASE-0A-EXCLUSION-SPEC + REVIEW.md         │
│  (proposed)             4 gates → ingest/quarantine/skip manifests  │
├──────────────────────────────────────────────────────────────────┤
│  L4 MEMORY/KNOWLEDGE    knowledge.md (tpl) + onlyfans-memory        │
│                         _memory/ · 07-Knowledge · manifests         │
├──────────────────────────────────────────────────────────────────┤
│  L5 PROJECT/OPS         project.md (tpl) + Project-F (live)         │
│                         G0–G4 gates · GATE 0 BLOCKED                 │
├──────────────────────────────────────────────────────────────────┤
│  L6–L9 PEOPLE/LOG/      person.md · log.md · handoff.md · agent.md  │
│       HANDOFF/AGENT     (templates)                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## ۲. جدول لایه‌ها (نقش / ورودی / خروجی / وابستگی / گلوگاه)

| لایه | نقش | فایل‌های پشتیبان | ورودی | خروجی | وابستگی | گلوگاه |
|---|---|---|---|---|---|---|
| L1 Governance | قانون اساسی، قواعد، مسیر ممنوع، چرخهٔ عمر | `PROJECT_INSTRUCTIONS.md` | تصمیمات مالک | قواعد جهانی | Property Schema، `.agentignore`، `.claude/settings.json` | سقف ۲۰۰ خط |
| L2 Control | دو‌مغزی، حلقهٔ ۶ گامی، نردبان L0–L3 | `TWO-BRAIN-CONTROL-BLUEPRINT.md` | SYSTEM-STATE، verdict انسان | پیشنهاد، mutation ledger، فاز بعد | §Security Gate (باز)، `git init` (باز)، ارتیفکت dashboard، watchdogها | گیت باز، git نبود |
| **L2b External Intelligence** | **موتور ستون ۳؛ ارکستراسیون چند‌ایجنتی فراتر از حد** | **Sakana Fugu API (Tokyo)** | سیگنال‌های ستون ۱/۲، دستور انسان | سنتز تصمیم، delegate، synthesize | **کلید API در `.agentignore` + rotation checklist**، budget ceiling، Gate+git | کلید secret، budget، human-only external |
| L3 Ingest/Security | مجوز ورود، قرنطینه، اسکن | `PHASE-0A-EXCLUSION-SPEC.md` + `REVIEW.md` | `.md` کاندیدا | `ingest/quarantine/skipped-encoding` manifests | gitleaks (host)، ROTATION_CHECKLIST، `.agentignore` | gitleaks در sandbox نیست؛ RTL شکننده |
| L4 Memory/Knowledge | حافظهٔ پایدار، سنتز، دانش | `knowledge.md`، `onlyfans-...-memory.md` | نوت‌ها، منابع، تحقیقات خارجی | نوت `created_by: agent` + `sources ≥2` | templates، MOC، `_memory/` | `_memory/` mount پایدار نیست |
| L5 Project/Ops | چرخهٔ عمر، Active Context، gates | `project.md`، `onlyfans-...` | ورودی Inbox، تصمیمات | PROJECT.md، DecisionLog، G0–G4 | templates، چرخهٔ عمر، لاگ | GATE 0 باز |
| L6–L9 People/Log/Handoff/Agent | موجودیت‌ها، لاگ، انتقال، ربات | `person/log/handoff/agent.md` | تعامل، پایان جلسه | نوت person، HANDOFF، runbook | templates، Architect System | ریسک حریم خصوصی (vault به ایجنت داده می‌شود) |

---

## ۳. یکپارچه‌سازی Sakana Fugu API — لایهٔ L2b «هوشمندی فراتر از حد»

### ۳.۱ هویت و تأیید

| فیلد | مقدار | منبع |
|---|---|---|
| شرکت | **Sakana AI**، تأسیس Tokyo، July ۲۰۲۳ | RuntimeWire |
| محصول | **Fugu** + **Fugu Ultra** — API ارکستراسیون چند‌ایجنتی، رفتار تک‌مدلی، OpenAI-compatible | RuntimeWire |
| مدل Ultra | `fugu-ultra-20260615`؛ $5/1M input · $30/1M output · $0.50/1M cached input | RuntimeWire |
| **وضعیت خرید** | **ACQUIRED 2026-07-06** — اشتراک Ultra فعال؛ **auto-renew روشن** تا منقضی نشود | خبر آری (2026-07-06) |
| اشتراک | Standard $20 · Pro $100 · Max $200 در ماه (شامل هر دو مدل) | RuntimeWire |
| قابلیت‌ها | تصمیم answer/delegate · انتخاب مدل دیگر · نحوهٔ ارتباط ایجنت‌ها · سنتز · فراخوانی بازگشتی خود | RuntimeWire |
| پایهٔ پژوهشی | TRINITY + Conductor (arXiv، Dec ۲۰۲۵) | RuntimeWire |
| حاکمیت/حریم خصوصی | در Fugu استاندارد می‌توان provider/model خاص را برای data/privacy/compliance حذف کرد؛ pool در Fugu Ultra ثابت است | RuntimeWire |
| قید وابستگی | Fugu وابستگی به مدل‌های خارجی را **حذف نمی‌کند، بلکه انتزاع و مدیریت می‌کند** | RuntimeWire |
| وضعیت تأیید | **[VERIFIED 2026-07-06]** —web-search §۷.۳ Blueprint انجام شد | این سند |

### ۳.۲ نقاط استفاده در ساختار (در جاهای مختلف — تقویت هوشمندی فراتر از حد)

Fugu در **پنج نقطهٔ معماری** به‌کار گرفته می‌شود. هر نقطه یک سطح استقلال و گیت مخصوص دارد:

| # | نقطهٔ استفاده | نقش هوشمندانه | سطح استقلال | گیت |
|---|---|---|---|---|
| F1 | **ستون ۳ — حلقهٔ فکری خودمختار** (`TWO-BRAIN` فاز ۴) | موتور فکری دکتر: وقتی answer/delegate/synthesize | **L3** (پشت Gate+git+سقف بودجه) | human-only تا ratify |
| F2 | **Memory synthesis / relation extraction** (فاز ۳/۴ memory-layer) | استنباط entity/edge با precision audit | **L1 propose-only** | human verifies قبل commit |
| F3 | **Per-subtree orphan rescue** (فاز ۴/۵) | تفکیک island cluster از true orphan | **L1 propose-only** | human approves link |
| F4 | **Ingest eligibility assist** (PHASE-0A Gate 3 second net) | طبقه‌بندی ریسک secret به‌عنوان دومین تور بعد از gitleaks+regex | **L1 propose-only** | Gate 2/3 سخت همچنان حاکم |
| F5 | **Project decision support** (Project-F و سایر پروژه‌ها) | سنتز تصمیم چندوجهی (مثلاً reconciliation master docs، pricing ladder) | **L1 propose-only** | human verdict (GATE 0 و غیره) |

> اصل کلیدی: Fugu در **هیچ نقطه‌ای** مستقیماً اعمال نمی‌کند مگر پشت L2/L3 و Gate+git. در F2–F5 همیشه propose-only است؛ انسان verdict می‌دهد. این با حاکمیت `PROJECT_INSTRUCTIONS` §۱۰ (پیام خارجی = human-only) و `TWO-BRAIN` §۳ (لیست سیاه: پول/پیام خارجی همیشه human-only) سازگار است.

### ۳.۳ مدل امنیتی Fugu

| ریسک | کنترل |
|---|---|
| کلید API = secret | هرگز در چت/نوت/HANDOFF/لاگ؛ مسیر ممنوع `.agentignore` + `.claude/settings.json` (deny+hooks)؛ ردیف در `SECRETS-ROTATION-CHECKLIST.md` با status OPEN تا rotated |
| پرداخت اشتراک | human-only (لیست سیاه: پول)؛ **auto-renew روشن** تا سرویس قطع نشود — اما هزینهٔ ماهانه در ledger budget ثبت شود |
| نشت داده به مدل خارجی | **🔴 CRITICAL (شدت‌گرفته):** چون Ultra خریداری شد و pool آن ثابت است، دادهٔ حساس Project-F (Iran geo-block، KYC، هویت صبا) **به‌هیچ‌وجه** نباید به Fugu Ultra برود. فقط Fugu استاندارد (opt-out provider) برای کارهای حساس؛ Ultra فقط برای کارهای عمومی/غیرهویتی (memory synthesis عمومی، orphan rescue، relation extraction روی نوت‌های non-sensitive) |
| وابستگی تک‌provider | Fugu وابستگی را انتزاع می‌کند نه حذف؛ به‌عنوان hedge، نه جانشین Claude/محلی |
| هزینهٔ بی‌کنترل | **سقف بودجهٔ روزانه** (مثلاً ≤AUD X/day)؛ توقف خودکار هنگام عبور؛ ledger append-only |
| hallucination orchestration | F2: precision audit نمونه‌ای قبل commit edge؛ هر claim `[FACT]/[INFERENCE]/[UNVERIFIED]` |
| Edge جعلی در مرز عمدی | F3: per-subtree scoping؛ Fugu فقط پیشنهاد می‌دهد، انسان تأیید |

### ۳.۴ فازبندی ساخت لایهٔ L2b

- **فاز ۰ (اکنون):** کلید API ثبت در rotation checklist (OPEN) + `.agentignore`؛ هیچ فراخوانی واقعی.
- **فاز ۱ (human-only):** بستن §Security Gate + `git init` → rollback ممکن.
- **فاز ۲:** ادراک زمان‌بندی‌شده (SYSTEM-STATE) — F5 می‌تواند activate شود (propose-only).
- **فاز ۳:** Mutation Ledger — F2/F3/F4 propose-only فعال.
- **فاز ۴:** ستون ۳ خودمختار — F1 پشت Gate+git+سقف بودجه (L2/L3).

---

## ۴. اسناد canonical و رقابت مرجعیت

| فایل | نقش | سطح |
|---|---|---|
| `PROJECT_INSTRUCTIONS.md` | حاکمیت نهایی، فقط‌خواندنی برای ایجنت | بالاترین |
| `PHASE-0A-EXCLUSION-SPEC.md` | spec جایگزین ingest (proposed) | مرجع اجرایی ingest |
| `REVIEW.md` | مرور grounded (final) | مرجع ریسک/گپ |
| `TWO-BRAIN-CONTROL-BLUEPRINT.md` | proposal (draft) | مرجع مفهومی کنترل |
| `project/person/log/knowledge/handoff/agent.md` | templates | قالب ساخت |
| `onlyfans-...-memory.md` | memory-synthesis زنده | حافظهٔ پروژه |
| **این سند** | **Master Architecture Spec (draft)** | **مرجع یکپارچه** |

**رقابت‌های باز:** دو master doc در Project-F (#5)؛ ACQUISITION-ENGINE vs MASTER-BUILD/Playbook (#15)؛ `PHASE-0A` در حال supersede کردن `BUILD-PROMPT` که در آپلودها نیست (#13). [استنباط: تا ratify، `PROJECT_INSTRUCTIONS` مرجع باقی است.]

---

## ۵. گردش عملیاتی

```
① Capture (تلگرام/Inbox/cron) → 00-Inbox
② Decision Tree (§4 PROJECT_INSTRUCTIONS) → پروژه/دانش/شخص/مبهم
③ Read-before-write (§8) → ایجنت اول PROJECT.md را می‌خواند
④ Ingest Eligibility (PHASE-0A: Gate1 Path → Gate2 Checklist Quarantine → Gate3 Secret Scan (gitleaks+regex+[F4 Fugu second-net]) → Gate4 Encoding) → manifest
⑤ Memory Synthesis → created_by: agent + sources ≥2 → _memory/ (یا پوشهٔ پروژه اگر mount نباشد)
⑥ Control Loop (TWO-BRAIN) → ① ادراک → ② تشخیص → ③ پیشنهاد [F5/F2 Fugu propose-only] → ④ verdict انسان → ⑤ اعمال (L2/L3، F1 پشت Gate+git+budget) → ⑥ سنجش
⑦ Handoff → Active Context/Progress آپدیت + HANDOFF بازنویسی (wikilink فقط) + لاگ پروژه
```

**سطوح دسترسی:** قانون اساسی/charter/secret/پول/پیام خارجی/تغییر گیت = **human-only همیشه**. Next actions/HANDOFF/append تلگرام = **agent-executable**. پیشنهاد دکتر/Fugu = **propose-only (L1)**. اعمال whitelist = **L2 پشت Gate+git (قفل)**. مشتق idempotent/F1 = **L3 پشت Gate+git+budget (قفل)**. فایل خارج از manifest = **وجود ندارد** برای پایین‌دست.

---

## ۶. مدل امنیت و مرز

| گیت | منبع | وضعیت | شرط توقف |
|---|---|---|---|
| Secret boundary | §۱۰، §۲ | فعال | — |
| مسیر ممنوع `.agentignore` + `.claude/settings.json` | §۲، §۱۰ | فعال | توقف + AGENT_QUESTIONS |
| تلگرام whitelist (user ID مالک) | §۱۰ | فعال | — |
| Ingest Gate 1 — Path Scope (resolved paths) | PHASE-0A | proposed | skip |
| Ingest Gate 2 — Checklist Quarantine (Gate2 > Gate3) | PHASE-0A | proposed | quarantine تا ROTATED |
| Ingest Gate 3 — Secret Scan (gitleaks+regex، Fugu second-net) | PHASE-0A + REVIEW | proposed، ناتمام | SCAN-UNAVAILABLE = full stop |
| Ingest Gate 4 — Encoding Sanity | PHASE-0A | proposed | skipped-encoding |
| §Security Gate (charter) | TWO-BRAIN §۳ | **باز** | پیش‌شرط L2 |
| git rollback | TWO-BRAIN §۲ | **باز** | پیش‌شرط اعمال |
| kill-switch ۳سطحی | TWO-BRAIN §۲ | proposed | — |
| Human approval gate (verdict) | TWO-BRAIN گام ④ | فعال | — |
| agent-checkpoint commit (پیش از >۵ فایل) | §۰ | فعال | — |
| اعتبارسنجی dry-run (validate_frontmatter + find_broken_links) | §۱۱ | فعال | پایان = هر دو پاس |
| rotation checklist (23 سطر، 4 CRITICAL+OPEN) | REVIEW | فعال، 4 باز | 4 سطر باز |
| **Fugu API key gate** (rotation + budget + human-external) | **این سند §۳** | **proposed** | **کلید rotated + budget set تا activate** |
| **Fugu budget ceiling** (سقف روزانه + توقف خودکار) | **این سند §۳** | **proposed** | **عبور = kill + AGENT_QUESTIONS** |

**آسیب‌پذیری‌های ثبت‌شده (بدون نرم‌سازی):** secret leakage از `.md` checklist-named (REVIEW #2)؛ RTL glob fragility (REVIEW #3)؛ SCAN-UNAVAILABLE downplay (REVIEW #1)؛ gate فقط DB را حفظ می‌کند نه vault/Desktop (REVIEW #4)؛ encoding fragility (REVIEW #6)؛ orphan metric با island cluster قاطی (REVIEW #5)؛ relation extraction بدون precision audit (REVIEW #6)؛ `_Archive` غایب با backup gate تأییدنشده (REVIEW #8). **جدید:** کلید Fugu اگر rotated نشود، نشت API = هزینه/دسترسی غیرمجاز؛ budget بدون ceiling = خروج از کنترل مالی (human-only پول).

---

## ۷. معماری کنترل و وضعیت

**نردبان استقلال L0–L3:** L0 گزارش · L1 پیشنهاد (propose-only) · L2 bounded-auto (whitelist §۳، پشت Gate+git) · L3 مشتق idempotent (پشت Gate+git+budget). **لیست سیاه همیشه human-only:** charter، secret، پول، پیام خارجی، تغییر گیت.

**حلقهٔ کنترل ۶ گامی:** ادراک → تشخیص → پیشنهاد (Fugu propose-only) → verdict (آری) → اعمال (L2/L3 + F1 پشت Gate+git+budget) → سنجش (برازندگی + استقلال + health).

**مؤلفه‌ها:** dashboard `fleet-live-dashboard` (✅)؛ watchdog (بازسازی فاز ۰)؛ Mutation Ledger (فاز ۳)؛ ledger append-only (✅ ref)؛ autonomy levels (ratified، L2/L3 قفل)؛ mutation flow (propose→verdict→whitelist-apply)؛ rollback git (**نبود**)؛ kill-switch ۳سطحی (proposed)؛ Gateهای G0–G4 پروژه (فعال، GATE 0 باز)؛ **Fugu L2b (proposed، proposed، کلید+budget باز)**.

**متریک موفقیت:** شاخص استقلال >۵۰٪ applied بدون لمس انسانی در ۴ هفته؛ صفر نقض invariant؛ health پایدار؛ نسبت promote÷revert؛ هزینه به‌ازای چرخه (شامل مصرف Fugu).

---

## ۸. معماری حافظه و دانش

| نوع حافظه | محل | نقش |
|---|---|---|
| پایدار (durable) | `07 - Knowledge` + `*-memory.md` (memory-synthesis) | حقایق ماندگار، load-before-session |
| عملیاتی (active) | `## Active Context` + `## Progress` در PROJECT.md + `HANDOFF.md` | تمرکز فعلی، ۳ قدم بعدی، تصمیم‌های باز |
| تصمیم‌گیری | لاگ پروژه + DecisionLog | تصمیمات، open questions |
| سنتز ایجنت | `created_by: agent` + `sources ≥2` | دانش تولیدشده با هویت متمایز |
| ingest manifest | `_memory/ingest-manifest.json` | منبع یکتای پایین‌دست |
| memory layer | `_memory/` (FTS5-first، سپس bge-m3) | recall، اتصال |
| entities | `09 - People`، `03 - Projects`، `05 - Agents` | موجودیت‌های زنده |
| handoff | `01 - Dashboard/HANDOFF.md` | انتقال جلسه |

**قواعد:** «حافظه را به‌روز کن» = بازبینی Active Context/Progress همهٔ activeها. نوت‌های ایندکس زیر ۲۰۰ خط. ~۲۴٪ نوت‌ها report/handoff → از recall خارج. `_memory/` mount پایدار نیست (گلوگاه). **جديد:** Fugu (F2) می‌تواند در memory synthesis کمک کند اما propose-only + precision audit.

---

## ۹. تضادها و تصمیم‌های باز

| # | تناقض/تصمیم باز | چرا مهم | آسیب اگر حل نشود |
|---|---|---|---|
| C1 | §Security Gate + `git init` باز | پیش‌شرط L2/rollback/F1 | مغز دوم و Fugu همیشه L0–L1 |
| C2 | gitleaks روی host اجرا نشده | قلب gate ingest | نشت secret به DB |
| C3 | دو master doc در Project-F | مرجعیت مبهم | اقدام اشتباه |
| C4 | سه نسخهٔ pricing ladder | تصمیم مالی باز | seeding اشتباه |
| C5 | «Persian»/«Sydney» در copy vs locked rules | نقض مرز LOCKED | ریسک حریم خصوصی/geo |
| C6 | GATE 0 (محل سکونت صبا) ثبت‌نشده | ممکن است داخل ایران | کل Project-F block |
| C7 | `_memory/` mount پایدار نیست | سنتز در محل non-canonical | پراکندگی حافظه |
| C8 | `_Archive` غایب + backup gate تأییدنشده | no-safety-net | از دست رفتن داده |
| C9 | ۴ سطر CRITICAL rotation باز | rotated نشده | نشت |
| C10 | موتور ستون ۳ | — | **RESOLVED 2026-07-06: Fugu انتخاب شد [VERIFIED]** |
| C11 | orphan با island cluster قاطی | مرز عمدی | لینک جعلی |
| C12 | relation extraction بدون precision audit | edge جعلی | دانش آلوده |
| C13 | PHASE-0A supersede BUILD-PROMPT | مرجعیت دوگانه | اجرای نسخهٔ قدیمی |
| C14 | Fansly mirror vs equal-weight | استراتژی باز | اجرای اشتباه |
| C15 | ACQUISITION-ENGINE vs MASTER-BUILD/Playbook | سلسله‌مراتب مبهم | تداخل |
| **C16 (جدید)** | **کلید Fugu + budget ceiling تنظیم‌نشده** | **activate Fugu خطرناک** | **نشت/هزینه غیرمجاز** — **جزئی حل: Ultra خریداری شد + auto-renew؛ سقف روزانه و tier همچنان باز** |
| **C17 (جدید، بحرانی‌تر)** | **Fugu Ultra pool ثابت + خریداری شد** | **دادهٔ حساس Project-F به pool ثابت برود** | **نقض survival filter (Iran geo-block/KYC)** — سیاست segregate داده الزامی |

---

## ۱۰. نیازمندی‌های ناقص (به ترتیب اولویت)

| اولویت | نیازمندی | منبع |
|---|---|---|
| P0 | rotation ۴ سطر CRITICAL (انسانی) | REVIEW |
| P0 | بستن GATE 0 (صبا → Branch A/B) | onlyfans-memory |
| P0 | تأیید `_Archive` + backup رمزشده | REVIEW #8 |
| **P0** | **ثبت کلید Fugu در rotation checklist + `.agentignore` (OPEN تا rotated)** | **این سند §۳** |
| **P0** | **تعیین سقف بودجهٔ روزانهٔ Fugu + kill خودکار** | **این سند §۳** |
| P1 | gitleaks روی host + re-baseline Phase 0b | REVIEW |
| P1 | قرنطینه checklist-named `.md` | REVIEW #2 |
| P1 | ratify PHASE-0A (allowlist-by-scan) | PHASE-0A |
| P1 | `git init` + تاریخچه commit | TWO-BRAIN فاز ۱ |
| P1 | بستن §Security Gate (charter) | TWO-BRAIN فاز ۱ |
| **P1** | **فعال‌سازی F5 (Project decision support، propose-only) بعد از Gate+git** | **این سند §۳.4** |
| P2 | mount پایدار `_memory/` | onlyfans-memory |
| P2 | حل چندمرجعیتی Project-F | onlyfans-memory |
| P2 | precision audit relation extraction (F2) | REVIEW #6 |
| P2 | per-subtree orphan scoping (F3) | REVIEW #5 |
| **P2** | **ratify سیاست Fugu Ultra: فقط برای کارهای غیرحساس؛ Project-F داده به pool ثابت نرود (C17)** | **این سند §۳** |
| P3 | ratify TWO-BRAIN §۷ (تابع برازندگی عددی، ریتم حلقه) | TWO-BRAIN §۷ |
| P3 | ساخت Mutation Ledger + watchdog | TWO-BRAIN فاز ۳/۰ |
| **P3** | **فعال‌سازی F1 (ستون ۳ خودمختار) پشت Gate+git+budget (L3)** | **این سند §۳.4** |
| P3 | تدوین این Master Spec → ratified | این سند |

---

## ۱۱. فهرست نهایی فایل‌ها/ماژول‌های نیازمند

- **فنی:** اجرای gitleaks روی host؛ `git init`؛ بستن §Security Gate؛ rotation ۴ سطر؛ تأیید `_Archive`+backup؛ watchdog بازسازی؛ Mutation Ledger؛ precision audit؛ per-subtree orphan؛ mount پایدار `_memory/`؛ تزریق‌دفاع spec؛ kill-switch ۳سطحی spec؛ تابع برازندگی عددی.
- **Fugu:** کلید در rotation checklist + `.agentignore`؛ budget ceiling + kill خودکار؛ سیاست opt-out provider در Fugu استاندارد؛ ممنوعیت Fugu Ultra برای دادهٔ حساس Project-F؛ OpenAI-compatible client با fallback محلی.
- **معماری:** این Master Spec → ratified؛ حل چندمرجعیتی Project-F؛ سلسله‌مراتب مرجعیت صریح؛ Property Schema + `.obsidian/types.json`؛ مسیر واقعی `_Templates`؛ `.agentignore` موجود.
- **عملیاتی:** runbook ساخت Gate (فاز ۱ human-only)؛ manifest orchestration (فاز ۱+ فقط manifest بخواند)؛ acceptance tests فاز ۰a؛ enforcing کلید ممنوع در زمان اجرا؛ idempotency pipeline تلگرام.

---

## ۱۲. ۱۰ سوال دقیق برای صاحب سیستم

1. آیا `BUILD-PROMPT.md` هنوز canonical است یا `PHASE-0A` کاملاً جایگزینش می‌کند؟
2. آیا `TWO-BRAIN` §۷ ratify می‌شود؟ تابع برازندگی آستانهٔ عددی؟
3. فاز بعد از Gate: فاز ۲ (ادراک زمان‌بندی‌شده)؟ ریتم: daemon یا burst؟
4. **تأیید شد: موتور ستون ۳ = Sakana Fugu [VERIFIED 2026-07-06]. سقف بودجهٔ روزانهٔ Fugu چقدر؟ Standard/Pro/Max کدام اشتراک؟**
5. آیا `git init` + تاریخچه راه می‌افتد (پیش‌شرط rollback/L2/F1)؟
6. لیست کامل مسیرهای ممنوع `.agentignore` و deny rules `.claude/settings.json` چیست؟ همگام‌اند؟
7. آیا `_memory/` mount پایدار می‌شود یا قاعدهٔ توقف هنگام نبود mount اضافه شود؟
8. چه کسی ۴ سطر CRITICAL rotation را rotate می‌کند و تا کجا فازهای ≥۱ memory-layer متوقف بماند؟
9. در Project-F: کدام master canonical؟ قیمت‌گذاری نهایی؟ قانون «Persian/Sydney ممنوع» تغییر می‌کند یا Playbook bios اصلاح؟
10. **آیا سیاست Fugu Ultra (pool ثابت) برای دادهٔ حساس Project-F ممنوع می‌شود و فقط Fugu استاندارد (opt-out) مجاز است؟ (C17)**

---

## ۱۴. لایهٔ Architect — جزئیات عمیق (دادهٔ اضافه از Replication Kit)

> **منبع:** گزارش Replication Kit (2026-07-06، `type: report`، `created_by: agent`) که آری فرستاد. این داده در ۱۱ فایل آپلودی نبود و از اسناد `SYSTEM-BLUEPRINT-v2` + `TWO-BRAIN` + `AGENT_REGISTRY` + `Property Schema` + `SYSTEM_MAP` استخراج شده. **محدودیت:** BLUEPRINT از اسناد خوانده شده، نه از کد `_code` (طبق `.agentignore`) — جزئیات runtime ممکن است با سند فاصله داشته باشد (قانون خود vault: کد واقعی > سند).

### ۱۴.۱ خواسته و خروجی Replication Kit

- **خواستهٔ آری:** کپی‌برداری دقیق از تمام قابلیت‌ها و featureهای ساختار، مخصوصاً قسمت Architect — به‌صورت template قابل‌اجرا، مقصد `00 - Inbox`.
- **خروجی:** `04 - Architect System/architect/03-Exports/replication-kit/` — ۵۳ فایل، تماماً additive (هیچ فایل موجودی ویرایش/حذف/جابه‌جا نشد).
- **اجزا:** `BLUEPRINT.md` (spec کامل ۸ لایه) · `scaffold.py` (بازسازی اسکلت fail-closed) · `seed/` (۵۰ فایل کپی دقیق + اسکلت sanitized).

### ۱۴.۲ پوشش Architect (§۶ BLUEPRINT — عمیق‌ترین بخش)

| عنصر | توصیف (از گزارش) |
|---|---|
| اصول | **P1–P11** — مجموعهٔ اصول بنیادین Architect |
| کامپوننت‌های core (۵) | **Telegram bot** با Intent-Router rule-based و step-up passphrase · **Brain/Router** · **Research Engine** با دو checkpoint · **Memory** با origin و `<external_data>` · **Safety Kernel** |
| satellite‌ها (۲) | دو مؤلفهٔ satellite (جزئیات در گزارش) |
| Tenant Adapter | قرارداد read-only creds enforced |
| نردبان استقلال | **L0–L3** + لیست سیاه human-only (تطابق با TWO-BRAIN §۳) |
| kill-switch | **fail-closed** (DB flag + STOP؛ چک هر round/هر commit) |
| خودبهبودی | حلقهٔ خودبهبودی با گیت سه‌شرطی + judge بین‌خانواده + cold-start ≥۵۰ trajectory |
| مدل بودجه | **دو-mode:** $2/$60 Normal · $10/$300 Growth |
| eval/observability | چرخهٔ نسخه‌بندی blueprint با red-team (**PROMPT-B**) |
| مدل دو مغز | حلقهٔ کنترل ۶گامی (تطابق با TWO-BRAIN §۲) |

### ۱۴.۳ چه چیزی عیناً کپی شد (seed)

- قانون اساسی (جدول اکوسیستم → placeholder) · `Property Schema.md` کامل · هر ۶ template · `validate_frontmatter.py` + `find_broken_links.py` + `gitleaks.toml` + `scripts/README.md` · `.agentignore` · `CLAUDE.md` · هر ۳ فایل `.claude/rules/`.
- اسکلت‌های نو: `AGENT_REGISTRY` (با وراثت §Gate) · `RATIFIED-TASKS` (درس bootstrap) · `ROTATION_CHECKLIST` (گیت از روز اول بسته) · `SYSTEM_MAP`/`ECOSYSTEM` · `Home`/`HANDOFF`/`Brain` · `HEARTBEAT`/`EXPERIENCE-LEDGER` · SOP/ROUTING تلگرام · `DECISIONS`/`GAPS`/`BACKLOG`/`CHANGELOG`/`SYSTEM-BLUEPRINT-v1` · `Weekly Review` · `AGENT_QUESTIONS`.

### ۱۴.۴ Sanitization و تست

- **دو مسیر Read-deny شخصی** در `settings.json` اصلی → با الگوی generic (`**/*wallet*` و مشابه) جایگزین شد؛ هیچ نام فایل secret واقعی در kit نیست.
- **اسکن regex** روی کل kit (کلید/توکن/آدرس/پسورد): تنها match یک کامنت توضیحی در `.agentignore` بود — **صفر مقدار محرمانه**.
- محتوای `_code`، دیتای پروژه‌ها، عکس‌ها، لاگ‌ها، نوت‌های شخصی: عمداً کپی نشد (بازسازی runtime = فاز ۵ بلوپرینت).
- **تست:** `scaffold.py` در sandbox اجرا → ۵۰ فایل ساخته شد؛ مسیر خطای «مقصد ناخالی» و «overwrite» fail-closed است. validators روی vault تولیدشده: frontmatter ۱۵/۰ خطا · لینک ۳۰/۰ شکسته — سبز.

### ۱۴.۵ checkpoint باز — نیازمند verdict

> commit ممکن نیست: vault هنوز git repo نیست و آری قبلاً به `git init` «نه» گفته (HANDOFF جلسه ۱۳؛ تغییر git = human-only در منشور). دستهٔ ۵۳+۲ فایلی این جلسه بدون checkpoint ماند — مثل جلسه ۹.

- اگر نظرت عوض شده، `git init` + commit اول را خودت بزن یا verdict صریح بده.
- این با **C1** (§Security Gate + git باز) و **C8** (`_Archive` غایب + backup gate تأییدنشده) مرتبط است.

### ۱۴.۶ تأثیر روی یکپارچه‌سازی Fugu

- **مدل بودجهٔ دو-mode** ($2/$60 Normal · $10/$300 Growth) اکنون **سقف بودجهٔ Fugu** را مشخص می‌کند (C16): مصرف Fugu باید در همان پنجره‌های Normal/Growth قرار گیرد، نه فراتر.
- **kill-switch fail-closed** موجود در Architect، به‌طور طبیعی به‌عنوان کنترل توقف Fugu هنگام عبور از budget قابل استفاده است — یعنی مکانیزم kill از قبل در معماری هست.
- **Memory با origin و `<external_data>`** دقیقاً محل قرارگیری خروجی Fugu (F2 memory synthesis) است: هر خروجی Fugu باید با `origin: fugu` و `<external_data>` برچسب بخورد تا از نوت‌های انسانی متمایز شود.
- **Safety Kernel + لیست سیاه human-only** تقویت می‌کند که Fugu Ultra (pool ثابت) نباید دادهٔ Project-F ببیند (C17) — این یک کنترل ساختاری، نه فقط سیاست.

---

## ۱۵. منابع (به‌روز)

- Sakana AI Fugu API — جزئیات شرکت، مدل‌ها، قیمت، قابلیت‌ها، حاکمیت: RuntimeWire
- Replication Kit Report (2026-07-06) — جزئیات عمیق Architect، P1–P11، کامپوننت‌ها، مدل بودجه، kill-switch: دادهٔ آری (این سند §۱۴).
- پرامپت اهداف دکتر تکاملی + Checklist 150 (2026-07-06) — سه ستون، تابع برازندگی، safeguardها: دادهٔ آری (§۱۶).
- باقی منابع: فایل‌های آپلودشده (`PROJECT_INSTRUCTIONS`، `TWO-BRAIN-CONTROL-BLUEPRINT`، `REVIEW`، `PHASE-0A-EXCLUSION-SPEC`، `onlyfans-project-memory-2026-07-05`، و templates).

---

## ۱۶. حلقهٔ خودیادگیری تکاملی — نمای کلی

> جزئیات کامل در سند جداگانه: `SELF-LEARNING-LOOP-SPEC.md`.

سیستم «خودیادگیرنده» = سه نوع یادگیری هم‌زمان:

| نوع | مکانیزم | چی یاد می‌گیرد |
|---|---|---|
| تکاملی | ستون ۲ (کشف جهش → قرنطینه → ارزیابی → تثبیت/بازگردانی) | قواعد/heuristic بهتر → ژنوم canonical |
| تجربه‌ای | EXPERIENCE-LEDGER (append-only) | چه کار کرد/نشکد |
| فکری | ستون ۳ (Fugu: observe→think→conclude→decide) | فرضیه→آزمون→نتیجه→دستور بعدی |

**تابع برازندگی (قفل‌شده):** جهش خوب = (الف) کمک به درآمد/خروجی پروژه + (ب) سادگی/سرعت workflow — با شاهد مشخص و متریک قطعی، نه خوداظهاری Fugu.

**شرط بالفعل‌شدن:** ۶ گیت باید بسته شوند — Security Gate (rotation + ۳ `.env` + gitleaks واقعی)، `git init` + `.gitignore` سخت، آشتی حقیقت (sync drift)، budget ceiling روزانه، kill-switch سه‌سطحی، stale-view حل‌شده. تا آن‌ها، حلقه در **L1 propose-only** است: کشف و قرنطینه ممکن، تثبیت و اعمال خودکار نه.

**سafeguardهای stop-ship:** نشت به Fugu بدون فیلتر secret (#13)، L2 قبل از git (#31)، نبود حافظهٔ ایمنی برای reverted (#66)، خوداظهاری Fugu به‌عنوان شاهد (#78)، self-modification (#105)، تزریق web_search به‌عنوان دستور (#131).

**متریک کلیدی «خودیادگیرنده شدن»:** شاخص استقلال >۵۰٪ applied بدون لمس انسانی در ۴ هفته + سرعت رشد ژنوم (قواعد canonical جدید در زمان).

---

## ۱۷. Learning Engine — مستقل با وابستگی به کل ساختار

> جزئیات کامل در سند جداگانه: `LEARNING-ENGINE-DEPENDENCY-CONTRACT.md`.

Learning Engine یک **شریان عرضی (cross-cutting spine)** است که عمود بر لایه‌های L1–L9 می‌ایستد. «مستقل» یعنی encapsulated (state خود، lifecycle خود، قابل‌تست در sandbox جدا، قابل‌تعویض بدون دست‌زدن به لایه‌ها)؛ نه «جدای». Engine به هر لایه یک **قرارداد typed** دارد (خوردن/دادن).

**اصل کلیدی:** می‌توان Engine را یک‌تنها جایگزین کرد (نسخهٔ v2 یا موتور غیر-Fugu) بدون بازنویسی لایه‌ها — تا وقتی contract حفظ شود. و می‌توان یک لایه را تعویض کرد بدون دست‌زدن به Engine.

**قرارداد به ازای هر لایه:** L1 (قانون را می‌خواند، پیشنهاد تغییر فقط از طریق AGENT_QUESTIONS) · L2 (گزارش سطح استقلال + هزینه به dashboard) · L2b (prompt bundle با فیلتر secret/PII به Fugu، fallback اگر down) · L3 (فقط manifest می‌خواند، هرگز eligibility را دوباره محاسبه نمی‌کند) · L4 (جهش تثبیت‌شده → ژنوم canonical، خروجی با `origin: fugu`) · L5 (پیشنهاد next action، برازندگی per-project) · L6 (قرنطینهٔ پیش‌فرض) · L7 (لاگ + HEARTBEAT دوطرفه) · L8 (بخش Learning state در HANDOFF) · L9 (Engine خودش ایجنت ثبت‌شده با `trigger: loop`).

**حالت‌های اجرا:** shadow (L0، فقط خواندن + گزارش — **می‌تواند همین حالا قبل از Gate**) → gate-closed (L1 propose-only) → L2 bounded-auto → L3 autonomous.

**مرز استقلال:** contract فایل-محور (هیچ call مستقیم به کد لایه‌ها) · fail-degraded (خرابی لایه = fallback نه crash) · testable in isolation · swappable · state ownership در `LEARNING-STATE.json`.

---

> **وضعیت سند:** draft v1.3. Fugu Ultra ACQUIRED + auto-renew. Architect deep-detail + Self-Learning Loop + Learning Engine (مستقل + وابسته به کل ساختار) ادغام شد. پس از ratify آری روی §۳ (Fugu segregation)، §۷ (TWO-BRAIN)، §۱۶ (خودیادگیری)، §۱۷ (Engine: shadow-mode, fallback, contract source) و P0/P1 بالا، این سند canonical می‌شود و نسخهٔ v2 جایگزینش می‌کند.
