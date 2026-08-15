# ماتریس نهایی R1 تا R29 — اولویت‌بندی ساختاری نهایی
# Final R1–R29 Matrix — Definitive Structural Prioritization

**نسخه / Version:** 2.0 (final — merged from Council 2 + owner fact-check + TCB attribution correction)  
**تاریخ / Date:** 15 August 2026  
**مبنای اولویت‌بندی / Prioritization basis:** Structural dependency (root cause → symptom), NOT operator convenience  
**منبع / Sources:** [Master Audit](file:///home/user/workspace/OCTOPUS-MASTER-AUDIT-FINAL.md) · [Council 2 Synthesis](file:///home/user/workspace/model-council-2-synthesis.md) · [GPT-5.6 Sol C2](file:///home/user/workspace/model-council-2-gpt_5_6_sol.md) · [Gemini 3.1 Pro C2](file:///home/user/workspace/model-council-2-gemini_3_1_pro.md)

---

## نردبان اولویت / Priority Ladder

**اصل / Principle:** هر آیتم فقط پس از تکمیل پیش‌نیازهای ساختاری‌اش قابل اجراست. «تیک زدن چک‌لیست» نیست — گذار از قصد به مکانیزم است.

Each item can only be executed after its structural prerequisites are complete. This is not checklist-ticking — it is the transition from intent to mechanism.

---

## فاز ۰ — مهار فوری / Phase 0 — Immediate Containment

| # | عنوان / Title | نوع / Type | دست / Owner | پیش‌نیاز / Prereq | V-item | توضیح / Notes |
|---|---|---|---|---|---|---|
| **R1** | چرخش GitHub PAT / Rotate GitHub PAT | Immediate containment | **مالک / Owner** | — | V5 (partial) | تنها نشت پرخطرِ زنده: `Mining/02-Code/Robo-data/scout_all_in_one.py:38`. چرخش = شما. Pair با pre-commit/CI scanning. |
| **R0a** | NO-GO تحت مالکیت محافظت‌شده / NO-GO under protected ownership | Structural prerequisite | **مالک / Owner** | — | V2 (closed) | ۹ ادعای `test_no_go_envelope.py` باید تحت ownership محافظت‌شده قرار گیرند — ایجنت نتواند تست را تغییر دهد. |

---

## فاز ۱ — ریشهٔ شواهد / Phase 1 — One Trustworthy Evidence Root (days)

| # | عنوان / Title | نوع / Type | دست / Owner | پیش‌نیاز / Prereq | V-item | توضیح / Notes |
|---|---|---|---|---|---|---|
| **R2** | Push به germline / Push to germline | Evidence prerequisite | **مالک / Owner** | R0a | — | ۱۹+ کامیت محلی جلوتر است. Push با provenance امضاشده + deployment digest. بدون این، هیچ حسابرسی بیرونی معتبر نیست. |
| **R19** | تولید AEB از درخت زنده / Generate Audit Evidence Bundle from live tree | Structural audit-integrity fix | ایجنت / Agent | R2 | — | تولید خودکار از revision منجمد + runtime attestations. هرگز دوباره بریفینگ انسان‌نوشته حسابرسی نشود. نردبان وضعیت: declared→implemented→tested→deployed→drilled→independently reproduced. |

---

## فاز ۲ — ترمیم هستهٔ اعتماد / Phase 2 — Repair the Trusted Core (1–2 weeks)

| # | عنوان / Title | نوع / Type | دست / Owner | پیش‌نیاز / Prereq | V-item | توضیح / Notes |
|---|---|---|---|---|---|---|
| **R13** | فیکس C-013: TCB مرز اعتماد امضاشده / Fix C-013: Signed trust-boundary manifest | **Structural — CRITICAL** | **رأی مالک / Owner vote** | R2 | C-013, V1, V6 | **بالاترین اولویت ساختاری.** `REFERENCE_DIR` به `SYSTEM_ROOT` فال‌بک می‌زند → همه‌چیز TCB می‌شود. فیکس: manifest امضاشده با digest و owner؛ fail-closed با diagnostic؛ hash-check نه فقط path membership. **اصلاح انتساب:** ایجنت خوش‌نیت زیر مأموریت مکتوب هم از کنار TCB رد شد — این استدلال شورا را قوی‌تر می‌کند. |
| **R3** | غیرفعال‌کردن یکی از دو تسک رصدخانه / Disable duplicate Observatory task | Symptom repair (C-014) | **رأی مالک / Owner vote** | — | C-014 | تسک قدیمی `OCTOPUS-Observatory` (PT1H) + تسک جدید 17:06 = fetch دوتایی. غیرفعال‌کردن فوری؛ ریشه‌سازی: single job registry + idempotency + coalescing. |
| **R4-R14a** | فیکس breaker بازِ orchestr + نقش unreachable از ask() | **Structural execution-path defect** | ایجنت / Agent | R13 | V1 | **مهم‌ترین در بلاک بدهی تست.** breaker باز = مسیر حاکمیتی غیرقابل‌دسترسی. |
| **R4-R14b** | به‌روزرسانی allowlist/فلگ‌ها/inventory به قرارداد امروز | Contract debt | ایجنت / Agent | R13 | — | اگر inventory‌های کهنه admission را کنترل می‌کنند → structural. |
| **R4-R14c** | API drift ×۴ | Contract debt | ایجنت / Agent | — | — | تست↔کد drift؛ ریشه‌یابی شده در T2. |
| **R26** | معافیت SMTP گیت / SMTP gate exemption | **High-risk policy exception — NOT cosmetic** | **رأی مالک / Owner vote** | R13 | V1 | استثنا می‌تواند complete mediation را سوراخ کند. نیاز: قاعدهٔ باریک، منقضی‌شونده، متصل به عمل، با تست‌های منفی. |

---

## فاز ۳ — چهار کنترل ساختاری / Phase 3 — Four Retained Structural Controls (4–8 weeks)

| # | عنوان / Title | نوع / Type | دست / Owner | پیش‌نیاز / Prereq | V-item | توضیح / Notes |
|---|---|---|---|---|---|---|
| **R20a** | شبکهٔ PEP + قرارداد ۱۵-فیلدی عمل / PEP mesh + canonical action contract | **Structural — CRITICAL** | ایجنت / Agent | R13 | V1, V4 | NIST reference monitor: always invoked, tamperproof, verifiable. 6 PEP: network egress, tool broker, persistent memory, code sandbox, budget debit, queue/transaction. |
| **R20b** | جداسازی حافظه به‌ازای هر پا / Per-leg memory isolation | **Structural — CRITICAL** | ایجنت / Agent | R20a | V3 | Per-leg namespaces, ACLs, provenance domains, taint labels. بدون این، یک پا شواهد همه را آلوده می‌کند (shared-fate risk). |
| **R20c** | مسیر محلی/خصوصی Fugu / Local/private Fugu route | **Structural — CRITICAL** | ایجنت / Agent | R20a | V5 | ۸ مرحله: classify/tokenize → redact → abstract → DLP → bind approval to hash → prevent retrieval → taint response → hard fallback. تبدیل «ارسال نکن» از سیاست به ویژگی ساختاری. |
| **R20d** | ارزیاب مستقل / Independent evaluator | **Structural — CRITICAL (binding constraint)** | **رأی مالک + ایجنت / Owner vote + Agent** | R20a | V11 | **بار-تحمل‌کننده‌ترین ریسک حل‌نشده.** ۵ محور استقلال: code ownership, identity/credentials, data/holdout secrecy, compute/telemetry, release authority. «داوری دقیقِ خود، همچنان داوری خود است.» بینش یگانه: حافظهٔ بهتر ممکن است gaming را ماندگار کند. |
| **R20e** | تأیید متصل به عمل + kill توزیع‌شده / Action-bound approval + distributed kill | **Structural** | ایجنت / Agent | R20a | V4, V6 | Single-use, signed, expiry-bound leases. بستن درز `OCTOPUS_WIRE_KILL_SEAM` پس از رأی مالک. تمرین تحت partition/backlog نه فقط engage/release سالم. |

---

## فاز ۴ — یادگیری محدود و کاهنده / Phase 4 — Bounded & Subtractive Learning (6–10 weeks)

| # | عنوان / Title | نوع / Type | دست / Owner | پیش‌نیاز / Prereq | V-item | توضیح / Notes |
|---|---|---|---|---|---|---|
| **R16** | سیاست صف ۱۰۶۲ فرضیه / 1,062-hypothesis queue policy | **Structural** | ایجنت / Agent | R20b | V8 | Scarcity, retirement, family dedup, bounded attention. صفِ ۱۰۶۲ فرضیهٔ pending = بدون سیاستِ حذف/انقضا. |
| **R18** | تحکیم دلتا به‌جای سطح / Delta-not-level consolidation | **Structural epistemic fix** | ایجنت / Agent | R20b | V7 | جلوگیری از انباشت تکراری به‌عنوان شواهد جدید. |
| **R15** | راه‌اندازی daemon 4d / Daemon 4d bring-up | **Structural operationalization** | **رأی مالک / Owner vote** | R20b, R20d | — | فقط در حالت سایه. **هشدار شورا:** پایش مسمومیت حافظه الزامی است — حافظهٔ بهتر ممکن است gaming را ماندگار کند (persistence of evaluator gaming). |
| **R17** | رأی فلگ FUZZY / FUZZY flag vote | Policy decision | **رأی مالک / Owner vote** | R16 | — | رأی = مکانیزم نیست. باید به policy نسخه‌بندی‌شده و runtime admission متصل شود. |

---

## فاز ۵ — اطمینان پیش از فعال‌سازی / Phase 5 — Assurance Before Activation (8–12+ weeks)

| # | عنوان / Title | نوع / Type | دست / Owner | پیش‌نیاز / Prereq | V-item | توضیح / Notes |
|---|---|---|---|---|---|---|
| **R4-R14d** | تکمیل بدهی‌های باقی‌ماندهٔ تست / Complete remaining test debt | Quality infrastructure | ایجنت / Agent | Phase 2-3 | — | ۱۵ شکست pre-existing، همگی ریشه‌یابی‌شده (۹ drift، ۴ API، ۲ live-env). |
| **R21** | حسابرسی بیرونی D1 / External D1 audit | **Structural assurance** | **مالک / Owner** | R19, Phase 3 | — | فقط پس از AEB امضاشده. انتخاب ممیز = مالک. |
| **R22** | README پاها / Leg READMEs | Cosmetic unless from manifest | ایجنت / Agent | R13 | — | اگر از manifest تولید شود = structural. در غیر‌صورت = مستندسازی. |
| **R23** | run_tests زیمان / Ziman run_tests | Quality infrastructure | ایجنت / Agent | — | — | برای evidence یکنواخت. |
| **R24** | sqlmodel کاریابی / Jobs sqlmodel | Implementation debt | ایجنت / Agent | — | — | Structural اگر schema constraints + idempotency ایجاد کند. |
| **R25** | کامیت hardtask در working repo / Commit hard-task work | Evidence hygiene | ایجنت / Agent | — | — | حفظ بازتولیدپذیری. |
| **R27** | باگ کیفیت ask / ask quality bug | Product-quality symptom | ایجنت / Agent | — | — | Escalate اگر governance role reachability را تحت تأثیر قرار دهد. |
| **R28** | brain_core: سایه←زنده / brain_core shadow→live | **Structural activation** | ایجنت / Agent | Phase 5 complete | — | از طریق ارزیاب مستقل، provenance، canary، rollback. |
| **R29** | 4d: سایه←زنده / 4d shadow→live | **Structural activation** | ایجنت / Agent | Phase 5 complete | — | نیازمند memory isolation, deletion/TTL, poisoning tests. **هرگز هم‌زمان با R28.** |

---

## خلاصهٔ وابستگی‌ها / Dependency Summary

```
R1 (PAT) ──────────────────────────────────────────────────────> فوری
R0a (NO-GO ownership) ──> R2 (push) ──> R19 (AEB) ──> R21 (audit)
                                      │
R13 (TCB manifest) <── R2 ────────────┘
  ├──> R3 (disable dup task)
  ├──> R4-R14a (orchestr breaker)
  ├──> R26 (SMTP = arch review)
  ├──> R20a (PEP mesh)
  │      ├──> R20b (per-leg memory)
  │      │      ├──> R16 (hypothesis queue)
  │      │      ├──> R18 (delta consolidation)
  │      │      └──> R15 (daemon 4d, shadow only)
  │      ├──> R20c (local Fugu)
  │      ├──> R20d (independent evaluator) ← binding constraint
  │      └──> R20e (action-bound approval + kill)
  └──> R22 (README from manifest)
R21 (external audit) ──> R28 (brain_core) ┉┉> R29 (4d) [NEVER simultaneous]
```

---

## جدول کلید / Key Table

| نماد / Symbol | معنا / Meaning |
|---|---|
| **مالک / Owner** | فقط مالک می‌تواند انجام دهد (رأی، چرخش، push، انتخاب ممیز) |
| **ایجنت / Agent** | ایجنت زیر مأموریت مکتوب می‌تواند انجام دهد |
| **رأی مالک + ایجنت / Owner vote + Agent** | رأی مالک پیش‌نیاز است، سپس ایجنت اجرا می‌کند |
| **Structural** | علت ریشه‌ای — بدون آن، کنترل‌های پایین‌دست بی‌معنا |
| **Cosmetic** | نشانه — مهم اما نه پیش‌نیاز ساختاری |
| **Binding constraint** | بار-تحمل‌کننده‌ترین ریسک — تا حل نشود، هیچ GO ممکن نیست |

---

## اصل حاکم / Governing Principle

> گذار از «قصد حاکمیتی» به «مکانیزم حاکمیتی» نیازمند آن است که هر ادعای امنیتی در سطح نثر را یک فرضیه بدانیم که باید مکانیکی تأیید شود، نه یک اصل بدیهی که فرض می‌شود.
>
> The transition from "governance intent" to "governance mechanism" requires treating every prose-level safety claim as a hypothesis to be mechanically verified, not an axiom to be assumed.

---

*بر اساس سنتز شورای دوم + فکت‌چک مالک + اصلاح انتساب TCB. منابع: [Master Audit](file:///home/user/workspace/OCTOPUS-MASTER-AUDIT-FINAL.md) · [Council 2 Synthesis](file:///home/user/workspace/model-council-2-synthesis.md) · [GPT-5.6 Sol C2](file:///home/user/workspace/model-council-2-gpt_5_6_sol.md) · [Gemini 3.1 Pro C2](file:///home/user/workspace/model-council-2-gemini_3_1_pro.md)*
