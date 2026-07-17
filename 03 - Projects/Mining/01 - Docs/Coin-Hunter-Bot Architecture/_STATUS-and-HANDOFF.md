---
type: handoff
project: "[[03 - Projects/Mining/PROJECT]]"
status: active
tags: [mining, architecture, coin-hunter, handoff]
created: 2026-07-14
updated: 2026-07-18
---

# 🧭 CONTINUATION BRIEF — معماری Coin Hunter Bot (برای ایجنت بعدی)

> **این نوت خودبسنده است.** اگر تازه واردی و حافظهٔ جلسهٔ قبل را نداری: کلِ آنچه لازم داری برای «دقیق ادامه‌دادن» همین‌جاست. **اول این را کامل بخوان، بعد `00 - MASTER-ARCHITECTURE`.**

---

## ۱. مأموریت (یک‌خطی)

تکمیلِ **کلِ معماریِ یک «coin hunter bot» حرفه‌ای** برای پروژهٔ Mining، با سنتزِ همهٔ قطعاتِ پراکنده (PDFها، SCOUT-B، هابِ OPI، منشور) در یک بلوپرینتِ واحدِ **قابل‌ساخت**. سیستم = **Coin Hunter Bot / Autonomous Accumulator**: حلقهٔ `SENSE → SCORE → ACT` + مغزِ چندلایهٔ LLM، روی ناوگانِ Orange Pi 5، survival-first، با ایزولاسیونِ سختِ باینری/کیف‌پول.

## ۲. وضعیتِ فعلی — چه چیزی ✅ تمام شده

**۱۳ سندِ معماری نوشته و در ۳ مکان ذخیره شد** (پوشهٔ `01 - Docs/Coin-Hunter-Bot Architecture/`):

| فایلِ واقعی (نامِ canonical) | وضعیت |
|---|---|
| `00 - MASTER-ARCHITECTURE.md` | ✅ دستیِ من — نقشهٔ کل + آشتیِ دو واقعیت + محورِ Regime + ماتریسِ اتوماسیون + فهرست |
| `01 - GOVERNANCE-and-SAFETY.md` | ✅ ایجنت + بازبینیِ خصمانه |
| `02 - SENSE-Discovery-Layer.md` | ✅ ایجنت |
| `03 - SCORE-Screening-and-Forensics.md` | ✅ ایجنت |
| `04 - Adversarial-Defense-and-Antifragility.md` | ✅ ایجنت |
| `05 - AGENT-BRAIN-Decision-Layer.md` | ✅ **دستیِ من** (ایجنتش mid-stream stall کرد) |
| `06 - ACT-Fleet-Execution-and-Orchestration.md` | ✅ ایجنت |
| `07 - SUBSTRATE-Fleet-Hub-and-Infra.md` | ✅ ایجنت |
| `08 - MONITORING-Telemetry-and-Deathwatch.md` | ✅ ایجنت |
| `09 - EXIT-Liquidity-and-Accounting.md` | ✅ ایجنت |
| `10 - DATA-STATE-and-SCHEMA.md` | ✅ ایجنت |
| `11 - BUILD-ROADMAP-and-Sequencing.md` | ✅ ایجنت |
| `_STATUS-and-HANDOFF.md` | ✅ همین نوت |

**سه مکانِ ذخیره (تکراری، برای ایمنی):**
1. worktree: `…/.claude/worktrees/coin-hunter-bot-arch-d49739/03 - Projects/Mining/01 - Docs/Coin-Hunter-Bot Architecture/` ← نسخهٔ canonical برای git
2. **vault زنده** (قابل‌دیدن در Obsidian): `03 - Projects/Mining/01 - Docs/Coin-Hunter-Bot Architecture/`
3. scratchpad backup: `…/scratchpad/arch-specs/` + `journal-backup.jsonl`

---

## ۳. ✅ نقصِ اصلیِ شناخته‌شده — «واگراییِ تجزیهٔ لایه‌ها» (حل شد 2026-07-14 — جزئیات در §۴ بند ۲؛ این بخش برای سابقه نگه داشته شد)

**علت:** هر ایجنتِ طراح فقط شمارهٔ لایهٔ خودش را داشت، نه فهرستِ کاملِ نام‌فایل‌ها. در نتیجه هر کدام یک **تجزیهٔ لایه‌ایِ متفاوت** را در ذهنش فرض کرد و wikilinkها را با آن ساخت. مثال: لایهٔ «دفاعِ خصمانه» با ۵ نام/شمارهٔ مختلف ارجاع داده شده (`[[04 - Adversarial-Defense-and-Antifragility]]`، `[[05 - ADVERSARIAL-DEFENSES]]`، `[[06 - ADVERSARIAL-DEFENSES]]`، `[[08 - ADVERSARIAL-DEFENSES]]`، …).

> **محتوای هر سند سالم و باکیفیت است.** فقط **برچسبِ لینک‌های متقابل** ناهماهنگ است (و گاهی یک سند فرض کرده مفهومی در سندِ خواهرِ دیگری است). `00 - MASTER` و `05` لینکِ درست دارند.

**تجزیهٔ canonical (۱۲ فایلِ واقعی — مرجعِ نهایی همین است).** جدولِ نگاشتِ **مفهوم → فایلِ واقعی** برای پاکسازی:

| مفهوم در لینکِ draft (هر شماره‌ای) | → فایلِ واقعی |
|---|---|
| OVERVIEW / COST-REGIME / CONTROL-LOOP | `00 - MASTER-ARCHITECTURE` |
| GOVERNANCE / SIX-DESIGN-PRINCIPLES / OPERATOR-VISION | `01 - GOVERNANCE-and-SAFETY` |
| SENSE / discovery / sources | `02 - SENSE-Discovery-Layer` |
| SCORE-Screening / Forensics / scorecard / gates | `03 - SCORE-Screening-and-Forensics` |
| ADVERSARIAL / DEFENSES / STRUCTURAL-FLAWS(-MITIGATION) | `04 - Adversarial-Defense-and-Antifragility` |
| BRAIN / TIERS / multi-tier / SCORE-brain / MENTOR / GOVERN-META-drift | `05 - AGENT-BRAIN-Decision-Layer` |
| ACT / fleet-execution / SCOUT-B-FLEET-MINING | `06 - ACT-Fleet-Execution-and-Orchestration` |
| SUBSTRATE / OPI-hub / OPI-AUTOMATION-HUB | `07 - SUBSTRATE-Fleet-Hub-and-Infra` |
| MONITORING / DEATHWATCH | `08 - MONITORING-Telemetry-and-Deathwatch` |
| EXIT / LIQUIDITY / SIZING / PORTFOLIO / accounting | `09 - EXIT-Liquidity-and-Accounting` |
| DATA / SCHEMA / SECURITY-and-STORAGE / encryption | `10 - DATA-STATE-and-SCHEMA` |
| BUILD / ROADMAP / sequencing | `11 - BUILD-ROADMAP-and-Sequencing` |

**ابهام‌هایی که باید با خواندنِ متن حل شوند (نه مکانیکی):** «SCORE» گاهی = غربالگری (۰۳) و گاهی = مغز (۰۵)؛ «OPERATOR-VISION» متن‌اش در ۰۱ ولی Tier5 mentor در ۰۵؛ «SECURITY-STORAGE» و «SIZING-PORTFOLIO» به‌عنوان سندِ مستقل وجود ندارند و در ۱۰ و ۰۹ ادغام شده‌اند.

**رویهٔ پاکسازیِ پیشنهادی:** برای هر یک از ۱۱ سند: (۱) `grep -oE '\[\[[^]]+\]\]'` بگیر، (۲) هر لینک را با جدولِ بالا به فایلِ واقعی نگاشت کن (بر اساس **مفهوم**، نه شماره)، (۳) با Edit تصحیح کن، (۴) چک کن محتوای سند مفهومی را که به سندِ خواهرِ ناموجود واگذار کرده، گم نکرده باشد. **این یک تسکِ خوش‌تعریف است؛ مکانیکیِ صرف نیست — متن را بخوان.**

---

## ۴. کارهای باقی‌مانده (به ترتیبِ اولویت)

1. ~~**[owner-decision] تصمیمِ Regime هزینه.**~~ ✅ **حل شد (2026-07-18): رأی مالک = Regime A (AUD-0) قطعی — D-006 در DecisionLog.** Regime B همچنان owner-gated خاموش؛ فعال‌سازی = verdict جدید. (توجه: ‏OpenQuestions ‏#۶ ربطی به رژیم ندارد — آن شمارشِ سخت‌افزار است، D-007.)
2. ~~**[پاکسازی] نرمال‌سازیِ wikilink/تجزیه** طبق §۳ بالا.~~ ✅ **انجام شد (2026-07-14):** همهٔ لینک‌های لایه‌ای در ۱۲ سند به نام‌های canonical نگاشت شدند (بر اساس مفهوم، نه شماره؛ موارد مبهم با خواندن متن حل شد — SCORE تفکیک شد به ۰۳=گیت/scorecard و ۰۵=مغز/Tier-meta؛ MENTOR/OPERATOR-VISION → ۰۵+۰۱). نودهای Mermaid و مثال‌های backtick همین سند عمداً دست‌نخورده ماندند. verify با grep کامل: صفر لینکِ غیر-canonical باقی مانده.
3. ~~**[state] به‌روزرسانیِ فایل‌های مغزِ پروژه**~~ ✅ **کامل شد (2026-07-14):** `PROJECT.md` (Active Context + Next actions)، `DecisionLog.md` (D-005/D-006 با رأی)، `OpenQuestions.md` (#۶ بسته)، `INDEX.md` (بخشِ ⭐ Coin-Hunter-Bot Architecture اضافه شد). هر دو validator اجرا شد؛ فایل‌های این کار پاک‌اند (۷ گزارشِ این پوشه false-positiveاند: ۴ نودِ Mermaid در ۰۳/۰۹ + ۳ مثالِ backtick در §۳ همین سند — عمداً دست‌نخورده).
4. **[git] commit مسدود است.** خطا: `Permission denied` روی `F:/backup/.git/objects` — قفلِ AV/هندلِ باز روی `.git`. **فایل‌ها روی دیسک امن‌اند.** رفع (سمتِ مالک): پروسهٔ قفل‌کننده/AV را ببند، سپس در worktree `git add "03 - Projects/Mining/01 - Docs/Coin-Hunter-Bot Architecture"` + commit. پیامِ آمادهٔ commit در §۶.
5. **[اختیاری] بازتولیدِ دو ایجنتِ ناموفق** برای غنای بیشتر: `design:05` (stall — دستی جبران شد) و `ingest:roadmap-v3` (خطای usage-policy — محتوایش از `data.txt` + COWORK prompt پوشش داده شد). روشِ resume در §۵.

---

## ۵. آرتیفکت‌های workflow (برای resume یا بازرسی)

- **runId:** `wf_371daf58-8f1` — نتیجه: ۲۳/۲۵ ایجنت موفق (۲ خطا: `ingest:roadmap-v3` usage-policy، `design:05` stall).
- **scriptPath (برای resume با کش):** `C:\Users\Armin\.claude\projects\F--backup-03---Projects-Mining--claude-worktrees-coin-hunter-bot-arch-d49739-03---Projects-Mining-01---Docs\dd70d31f-dc7f-402f-a629-50abe8f5fde5\workflows\scripts\coin-hunter-architecture-wf_371daf58-8f1.js`
  - resume: `Workflow({scriptPath: "…", resumeFromRunId: "wf_371daf58-8f1"})` — ایجنت‌های بدون‌تغییر از کش برمی‌گردند؛ فقط تغییریافته‌ها دوباره اجرا می‌شوند.
- **journal (خروجیِ خامِ هر ایجنت + completeness-critic):** `…/subagents/workflows/wf_371daf58-8f1/journal.jsonl` و کپیِ پایدار در `scratchpad/journal-backup.jsonl`. یافته‌های completeness آنجاست.
- **اسکریپتِ استخراج (journal → فایل):** `scratchpad/extract_specs.py`.

## ۶. پیامِ آمادهٔ commit
```
feat(mining): coin-hunter-bot architecture — 13-doc consolidated blueprint

MASTER + 11 layer specs (governance, SENSE, SCORE, adversarial, agent-brain,
ACT, substrate, monitoring, exit/accounting, data/schema, build-roadmap) + handoff.
Regime A (AUD-0) default; Regime B (paid) owner-gated OFF. Additive only.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

---

## ۷. مواد خام (منابعِ سنتز — همه read-only)

- **PDFهای استخراج‌شده به متن** (در scratchpad `pdftext/`): `README.txt` (معماریِ ۴-tier)، `CORE PRINCIPLES.txt` (قانون اساسیِ تغییرناپذیر)، `tier2 forensics prompt.txt` (ابعادِ ۱۰-گانه)، `COWORK OPERATOR PROMPT.txt` (شش اصل + guardrail)، `CRITIQUE DEEP.txt` (۷ نقص)، `roadmap-v3-jame.txt`، `SUMMARY.txt`، `handoff context.txt`، `CPU Mining Quantum Resistance Plan.txt`. (PDFها با `pdftotext -enc UTF-8` قابلِ استخراج‌اند؛ pdftoppm نصب نیست.)
- **مخزن:** `01 - Docs/Bot System/*.pdf`، `01 - Docs/Strategy & Roadmap/*.pdf` + `data.txt`، `01 - Docs/Orange Pi Automation System - 20 Projects/ARCHITECTURE_v2_Hybrid_Final.md`، [[03 - Projects/Mining/04 - Research/SCOUT-B|SCOUT-B]] (B1–B25)، `CLAUDE.md` (منشورِ Mining)، [[03 - Projects/Mining/PROJECT|PROJECT]]، Coin Scouting Framework، Hardware Registry.

## ۸. حقایقِ لنگر (که نباید دوباره کشف شوند)

- **ناوگان:** ۱۶–۵۰× Orange Pi 5 (RK3588: ۴×A76+۴×A55) + ۵۰–۲۰۰× ESP32؛ FPGAهای Artix-7 **پارک** (ماین نمی‌کنند). لبه = برق `<$0.05/kWh` یا solar. `[OPEN]` تعدادِ واقعیِ ناوگان (config قدیمیِ Hcash = ۶ نود).
- **CORE_PRINCIPLES (تغییرناپذیر):** عمر ≤۹۰d؛ mcap `$50k–$50M`؛ CPU-mineable؛ ماینر open-source؛ default=REJECT؛ «average-miner-unprofitable ولی operator-profitable» = **سیگنالِ مثبت (edge-zone)**.
- **۷ نقصِ ساختاری** (نقدِ عمیق) → هر کدام mitigation در `04`.
- **قواعدِ قفل R1–R8** در `01`؛ سه zoneِ ایزوله (ماشین اصلی ⟂ ناوگان ⟂ امضاکنندهٔ air-gapped).

## ۹. یادآوریِ حاکمیتی (این‌ها را نقض نکن)

- **additive-only:** هیچ فایلِ موجودی حذف/بازنویسی/جابه‌جا نشود بدون git commit + verdict آری (`git mv` فقط). به‌روزرسانیِ PROJECT/DecisionLog/OpenQuestions مجاز است.
- **هیچ باینری اجرا نشود، هیچ کیف/کلید لمس نشود، هیچ خروجِ نقدی.** ربات فقط پیشنهاد می‌دهد؛ ورودِ کوین/spend/delete = گیتِ انسانی.
- زبانِ اسناد فارسی با اصطلاحاتِ انگلیسی؛ frontmatter + تگ‌های epistemic `[FACT]/[EST]/[SPEC]/[OPEN]`.
