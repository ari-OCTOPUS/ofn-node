---
type: proposal
status: draft
created: 2026-07-05
updated: 2026-07-05
extends: "[[MYCOLEDGER-REBUILD-CHARTER-proposal-v2]]"
tags: [prompts, parallel, repair, architecture, mock-to-live, propose-only]
---

> [!warning] propose-only · پشتِ گیت
> ۱۰ پرامپتِ موازی برای **ادامهٔ آپدیتِ معماری + ترمیمِ آن به واقعی**. هر عامل فقط **می‌خوانَد و پیشنهاد می‌دهد** — هیچ کدی ساخته/اجرا/ویرایش نمی‌شود (منشورِ v2 §۱۰: تا M0+M0.5 سبز نشود، read-only/propose-only). خروجیِ هر عامل یک سندِ `proposal` جداست → صفر تداخلِ فایل → واقعاً موازی.

# ۱۰ پرامپتِ موازی — ترمیمِ معماری به «واقعی»

**چرا این‌ها propose-only‌اند، نه کدنویس:** [[BUILD-BACKLOG]] (M0–M8) پرامپت‌های ساختِ **ترتیبی** با هم‌پوشانیِ فایل‌اند (M1/M2→`orchestrator.py`، M1/M2/M3/M8→`config.py`) و پشتِ گیت‌اند. این ۱۰ عامل به‌جایش **بلوپرینتِ ترمیم** را موازی می‌سازند: census/spec/mapِ هر زیرسیستم. لحظه‌ای که آری گیت را باز کند، این بلوپرینت‌ها به پرامپت‌های ساختِ M0–M8 تغذیه می‌شوند — بی‌دوباره‌کاری، بی‌حدس.

**هستهٔ «ترمیم به واقعی»:** بستنِ شکافِ MOCK↔LIVE و کد-مرده که در GAPS مستند است — G-04 (eval خودارجاع)، G-08 (observability خاموش)، G-10 (EffectorGate تهی/fail-open)، G-15 (پنلِ نمایشی)، G-16 (schema مرده)، G-26 (صفر اجرای LIVE).

---

## هدرِ مشترک — **پیش از هر بلوکِ زیر paste شود**

```
تو یک عاملِ propose-only از ناوگانِ MycoLedger هستی. منشورِ حاکم:
04 - Architect System/architect/01-Project/MYCOLEDGER-REBUILD-CHARTER-proposal-v2.md

قواعدِ سخت (نقض = توقفِ فوری):
- §Security Gate بسته است → فقط READ و PROPOSE. هیچ کدی اجرا/ویرایش نکن؛ هیچ فایلِ کد را تغییر نده.
- هرگز secret/credential را نخوان/نقل/لمس نکن. اگر به رازی رسیدی، فقط مسیرش را به‌عنوان یافته گزارش کن — بدونِ مقدار.
- MOCK ≠ LIVE: هیچ ادعای «کار می‌کند» را از اجرای MOCK نپذیر. هر ادعا برچسب بخورد: [proven-in-field]/[plausible]/[guess].
- انضباطِ ضدِّاستعاره: هر آنالوژیِ زیستی باید یک مکانیزمِ نرم‌افزاریِ واقعی + فایل:خط نام ببرد، وگرنه حذف.
- خروجی‌ات فقط **یک سندِ proposal** در مسیرِ تعیین‌شده است (frontmatter: type: proposal, status: draft).
  فایلِ هیچ عاملِ دیگری را دست نزن. کدِ هیچ‌جا را تغییر نده.
- ترتیبِ حقیقت: کدِ واقعی > charter > blueprint v2 > این پرامپت > سندِ قدیمی‌تر.
- آخرِ کار: «یافته‌های کلیدی + گلوگاهِ باز + قدمِ بعدیِ پیشنهادی» بنویس و **بایست**. تصمیم و اجرا با آری.
کدِ واقعی زیرِ: 04 - Architect System/architect/_code/ai-farm/  (AI-sume/langar · AI-sume/langar-pro · fusion-mvp[+igk] · fusion-creative · fusion-safety)
```

---

## P1 — نقشهٔ کد → ژنوم (INDEX · §۹ گام ۱-۲) · foundation
- **بخوان:** کلِ درختِ `_code/ai-farm` (ساختار + فایل‌های سرِ هر ماژول) + charter-v2 + [[SYSTEM-BLUEPRINT-v2]].
- **کار:** هر فایل/جزءِ واقعی را به ژنوم (germline / soma / EffectorGate) و به یک milestone (M0–M8) نسبت بده. نقشهٔ «وضعِ فعلی → هدف».
- **سند باید داشته باشد:** جدولِ `فایل → لایهٔ ژنوم → milestone → وضعیت (زنده/mock/مرده)`؛ فهرستِ کد-مرده؛ گراف وابستگیِ ماژول‌ها.
- **خروجی:** `01-Project/repair-specs/01-code-genome-map.md`

## P2 — spec واقعی‌سازیِ EffectorGate (G-10) · می‌خورد به M1+M2
- **بخوان:** `fusion-mvp/src/orchestrator.py`، `src/tools.py`، `fusion-mvp/igk/`، `config.py`، THREAT-MODEL.
- **کار:** طراحیِ بستنِ سه خلأ G-10: (۱) `GROUNDING_REQUIRED` واقعی، (۲) عبورِ `ToolGateway.call`+finalize از permit (نه فقط no-op)، (۳) حذفِ fallbackِ بی‌صدا به cooperative (fail-closed با پرچمِ `IGK_REQUIRED`).
- **سند باید داشته باشد:** دیاگرامِ choke-point؛ محلِ دقیقِ hookها (فایل:خط)؛ قراردادِ permit؛ پلنِ تستِ `PermitDenied`/`STOP`.
- **خروجی:** `01-Project/repair-specs/02-effectorgate-spec.md`

## P3 — spec پوششِ کاملِ بودجه (G-06) · می‌خورد به M4
- **بخوان:** `langar/budget.py` + همهٔ call-siteهای LLM در `langar/`.
- **کار:** فهرستِ **هر** call-site که از `BudgetManager` رد نمی‌شود؛ طراحیِ سیم‌کشیِ سراسری؛ hard-stop AU$30/ماه (D-25) + alert ۵۰/۸۰٪ + گاردِ اندازهٔ `langar.db-wal`/audit.
- **سند باید داشته باشد:** جدولِ call-site (فایل:خط، پوشش‌داده‌شده؟)؛ نقطهٔ enforcement واحد؛ پلنِ تستِ عبور-از-سقف.
- **خروجی:** `01-Project/repair-specs/03-budget-coverage-spec.md`

## P4 — spec سیم‌کشیِ observability (G-08) · می‌خورد به M6
- **بخوان:** `langar/observability/tracer.py` + `main.py` (sink) + جای چهار span.
- **کار:** محلِ اتصالِ `@trace` روی چهار span (model_call/tool_call/reasoning/handoff)؛ کامل‌کردنِ `/delete_all_data` برای جداولِ event/trace (نقصِ GDPR-style).
- **سند باید داشته باشد:** چهار محلِ دقیقِ call-site (فایل:خط)؛ schemaِ رویداد؛ پلنِ تستِ «≥۴ رکورد بعد از یک تعامل، صفر بعد از delete».
- **خروجی:** `01-Project/repair-specs/04-observability-spec.md`

## P5 — spec eval/held-outِ بیرونی (G-04، D-21) · می‌خورد به M7/حلقه
- **بخوان:** `fusion-mvp/src/optimizer.py`، `src/evals.py`، `src/panel.py`، `self_update.py`.
- **کار:** طراحیِ گیتِ بیرونیِ ارتقا: held-out **واقعی** (نه rubric کیواژه‌ای)، judge بین‌خانواده (D-09)، گیتِ سه‌شرطی promotion. رفعِ Goodhart-by-construction.
- **سند باید داشته باشد:** طرحِ ساختِ held-out از trajectoryهای واقعی (وابسته به G-20)؛ قراردادِ judge؛ شرایطِ سه‌گانهٔ promote؛ چه چیزی الان خودارجاع است (فایل:خط).
- **خروجی:** `01-Project/repair-specs/05-eval-heldout-spec.md`

## P6 — سرشماریِ MOCK↔LIVE و کد-مرده (G-15/G-16/G-26) · قلبِ «ترمیم به واقعی»
- **بخوان:** `fusion-mvp/src/panel.py`+`orchestrator.py`؛ `langar-pro/db/schema.sql`+کدِ نوشتنِ آن؛ `langar/core/ace.py`+`retrieval.py`؛ `langar/brain/brain_router.py`.
- **کار:** census هر جای نمایشی/مرده: رأیِ هیوریستیکِ پنل، `synthesizer.py` مرده، vector-1536 مرده، `confidence` همیشه NULL، ۱۴جدول→۶جدول، ACE بی‌producer، BrainRouter بی‌سیم، «صفر اجرای LIVE».
- **سند باید داشته باشد:** جدولِ `مؤلفه → ادعا → واقعیت (فایل:خط) → چک‌لیستِ واقعی‌سازی`؛ اولویتِ نزولی.
- **خروجی:** `01-Project/repair-specs/06-mock-vs-live-census.md`

## P7 — spec راستی‌آزماییِ kill-switch + fail-closed (D-06/D-13) · می‌خورد به M1
- **بخوان:** `langar/bot.py`، `fusion-mvp/src/killswitch.py`، `orchestrator.py`.
- **کار:** یکسان‌سازیِ kill-switch (`halted` DB = حقیقت + mirrorِ فایلِ `STOP`)؛ DENY-on-timeout (D-13)؛ پلنِ تستِ halt→سکوت→resume.
- **سند باید داشته باشد:** ماشینِ حالتِ halt؛ نقاطِ چکِ `halted`/`STOP` (فایل:خط)؛ سناریوهای تستِ fail-closed؛ شکافِ فعلی بینِ دو مکانیزم.
- **خروجی:** `01-Project/repair-specs/07-killswitch-verify-spec.md`

## P8 — طراحیِ گیتِ تست + red-team (M0-regression، G-26) · pre-flight
- **بخوان:** `fusion-mvp/tests/`، `test_phase3.py`، `src/evals.py` (`ALLOWED_SENTENCE_PATTERNS`).
- **کار:** پلنِ برگرداندنِ سوئیت به **۴۰/۴۰** بدونِ رگرسیونِ امنیتی (allowlistِ محدود برای جملهٔ بی‌خطر، ولی injection همچنان رد)؛ طراحیِ سوئیتِ red-teamِ گیتِ merge.
- **سند باید داشته باشد:** علتِ دقیقِ قرمزیِ فعلی (فایل:خط)؛ طرحِ fix؛ assertهای ضدِرگرسیون؛ فهرستِ سناریوهای red-team.
- **خروجی:** `01-Project/repair-specs/08-test-redteam-gate.md`

## P9 — آدیتِ سطحِ رازها/وابستگی/استقرار (G-01/G-02/D-27) · read-only
- **بخوان:** `langar-pro/requirements.txt`، compose-ها، `.env.example`، `scripts/gitleaks.toml`، `one-liner-vps-setup.sh`.
- **کار:** نقشهٔ سطحِ راز (فقط مسیرها، بی‌مقدار) + مرگِ مسیرِ LLM در Docker (نبودِ anthropic/openai در reqs → ImportError، تضادِ pg16/pg15) + پلنِ سخت‌سازیِ `.gitignore`/pre-commit/gitleaks. **چرخشِ راز دستِ آری می‌ماند — این عامل فقط آدیت می‌کند.**
- **سند باید داشته باشد:** جدولِ یافته‌ها (فایل، ریسک، اقدامِ پیشنهادی، «دستِ آری؟»)؛ پلنِ گیتلیکس.
- **خروجی:** `01-Project/repair-specs/09-security-surface-spec.md`

## P10 — spec enforcementِ قانون‌اساسی + policy (G-07/G-25/D-14) · read-only
- **بخوان:** `langar/core/constitution.py`، `langar-pro/app/research/constitution.py`، `core/self_improver.py`.
- **کار:** نگاشتِ «۱۴ قانونِ ادعا vs ۴ regexِ enforce‌شده»؛ طراحیِ enforcementِ read-only-tenant (G-25)؛ جدولِ allowlist policy در DB (D-14)؛ رفعِ ابهامِ واژهٔ «وزن» (G-24).
- **سند باید داشته باشد:** جدولِ `قانون → enforce‌شده؟ → مکانیزمِ پیشنهادی (فایل:خط)`؛ طرحِ policy table؛ مرزِ invariant↔mutable.
- **خروجی:** `01-Project/repair-specs/10-constitution-policy-spec.md`

---

## جدولِ dispatch (ایمنیِ موازی)

| عامل | زیرسیستم | GAP | فایلِ خروجی (یکتا) | می‌خورد به |
|---|---|---|---|---|
| P1 | نقشهٔ کل | §۹ | 01-code-genome-map | همه |
| P2 | EffectorGate | G-10 | 02-effectorgate-spec | M1,M2 |
| P3 | Budget | G-06 | 03-budget-coverage-spec | M4 |
| P4 | Observability | G-08 | 04-observability-spec | M6 |
| P5 | Eval/held-out | G-04,D-21 | 05-eval-heldout-spec | M7 |
| P6 | MOCK↔LIVE census | G-15/16/26 | 06-mock-vs-live-census | همه |
| P7 | Kill-switch | D-06,D-13 | 07-killswitch-verify-spec | M1 |
| P8 | Test/red-team | G-26 | 08-test-redteam-gate | M0 |
| P9 | سطحِ راز/deploy | G-01,G-02 | 09-security-surface-spec | M0(sec) |
| P10 | Constitution/policy | G-07,G-25 | 10-constitution-policy-spec | — |

**ایمنیِ موازی اثبات‌شده:** هر ۱۰ عامل فقط **می‌خوانند**؛ هرکدام دقیقاً **یک** فایلِ خروجیِ یکتا می‌نویسد → صفر تداخلِ نوشتن. هیچ‌کدام کد/راز/گیت را لمس نمی‌کند.

## بعد از این موج
۱۰ spec → آری verdict می‌دهد → لحظهٔ باز شدنِ گیت (M0+M0.5 سبز)، پرامپت‌های **ساختِ** [[BUILD-BACKLOG]] (M0–M8) از روی این بلوپرینت‌ها **ترتیبی** اجرا می‌شوند (چون فایل‌ها هم‌پوشان‌اند).

*propose-only. اجرا و verdict با آری. مشتق از GAPS (G-01..G-26) + DECISIONS (D-01..D-29) + BUILD-BACKLOG + کدِ واقعی.*
