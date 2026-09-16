---
type: report
status: draft
tags: [gap-analysis, architecture, frontier, deep, evaluation-security]
created: 2026-07-06
updated: 2026-07-06
extends: "[[04 - Architect System/architect/04-Docs/2026-07-06 0245 GAP-ANALYSIS-2026]]"
---

> [!note] ثبت ایجنت (Inbox-first)
> متن آری (2026-07-06)، نسخه v2.0. نرمال‌سازی: frontmatter با schema سازگار (`deep-gap-analysis`→`report`؛ کلیدهای اصلی: `version: 2.0` · `owner: آری`)؛ طبق متن خود سند، v1 را منسوخ **نمی‌کند** (عمیق‌ترش می‌کند) → `extends` نه `supersedes`. بازبینی + راستی‌آزمایی + نگاشت به اندام‌های موجود: [[04 - Architect System/architect/04-Docs/2026-07-06 0237 review-deep-gap-v2|نوت بازبینی]]. تا verdict: proposal.

# DEEP-GAP-ANALYSIS v2.0 — شکاف‌های ساختاری نسبت به بهترین‌های مرز

> **چرا این نسخه متفاوت است:** نسخهٔ v1 ده شکاف داشت ولی منابعش تکراری بود. این نسخه هر شکاف را به **یک مکانیسم مرزی متمایز** وصل می‌کند که در v1 نبود، و به‌جای «قابلیت غایب»، **نقص مکانیسمی** را نشانه می‌گیرد. هر شکاف = (الف) مکانیسم مرزی، (ب) شاهد، (پ) ما چه می‌کنیم، (ت) شکاف ساختاری دقیق، (ث) ترمیم، (ج) شدت و گیت.
> قاعدهٔ عدم‌تکرار: هیچ منبعی در بیش از یک شکاف ظاهر نمی‌شود مگر اینکه بعد متمایزی بیفزاید.

## مفروضات مرجع (سیستم ما)

- **حلقهٔ خودیادگیری** (`SELF-LEARNING-LOOP-SPEC`): variation → selection → inheritance، سه نوع یادگیری، تابع برازندگی قفل‌شده (درآمد+سادگی)، نردبان L0–L3.
- **موتور وابستگی** (`LEARNING-ENGINE-DEPENDENCY-CONTRACT`): ستون فقرات مستقل، قرارداد تایپ‌دار ۹+۲ لایه، shadow→L2→L3، Mutation Ledger، F4 فقط manifest سبز.
- **Fugu:** ادغام F1–F5، Ultra با pool ثابت، C17.
- **دکتر مغز:** ستون ۱ (نگهبان سلامت zero-LLM)، ستون ۲ (کشف جهش)، ستون ۳ (حلقهٔ تأملی Fugu).

## ۱. تک‌اهرمی‌بودن سطح جهش — scaffold-only در برابر چهار اهرم جدا (🔴، گیت L2)

**مکانیسم مرزی:** Hexo Labs SIA: بهبود از **دو کمپ جدا** — harness-update (scaffold) و weight-update — که مستقل‌اند و چیزهای متفاوتی را بهبود می‌دهند؛ ترکیب هر دو از scaffold-alone در همه بنچمارک‌ها پیشی گرفت. **ما:** فقط یک اهرم (mutation روی scaffold). **ترمیم:** فیلد `mutation_target` در Mutation Ledger با مقادیر `{scaffold | training_data | reward_model | weight | tool}` + verdict صریح آری برای هر اهرم.

## ۲. ارزیابِ بدبین مستقل غایب — جداسازی ساختاری generator/evaluator (🔴، گیت L2)

**مکانیسم مرزی:** الگوی adversarial evaluator: generator تولید می‌کند، evaluator اختصاصی در تنش دائم و **context تازه** per-review تست/نمره می‌دهد، ۵–۱۵ دور. «جداسازی ساختاری است نه prompt.» **ما:** شرط ضد-خوداظهاری داریم ولی generator و evaluator در همان context/session‌اند. **ترمیم:** لایه `ADVERSARIAL-EVALUATOR` مستقل با context تازه و معیارهای dimensioned.

## ۳. scaffold متغیر dominant است ولی سنجیده نمی‌شود (🔴)

**مکانیسم مرزی:** scaffolding تا **۱۰۰x** واریانس inference-efficiency — scaffold بیش از مدل واریانس price-performance را توضیح می‌دهد. **ما:** fitness فقط خروجی نهایی را می‌سنجد. **ترمیم:** `scaffold_efficiency_score` (tokens/task، $/task، retries/task) به‌عنوان بعد سوم برازندگی، با reference runner مستقل.

## ۴. شکست‌نامه بی‌اثر — ledgers لاگ می‌کنند نه ترمیم می‌سازند (🟠، پل L1→L2)

**مکانیسم مرزی:** CausalFlow: تبدیل traces شکست‌خورده به ترمیم‌های counterfactual مینیمال + دادهٔ supervision. **ما:** ledgerها append-only و پس‌مرده. **ترمیم:** pass `FAILURE→REPAIR` در ستون ۲ که هر شکست را به proposed-minimal-counterfactual در صف verdict تبدیل کند.

## ۵. گراف وابستگی غایب — ledgers خطی‌اند نه گراف (🟠)

**مکانیسم مرزی:** GRADE: لایه وابستگی شکست را پیش‌بینی می‌کند جایی که run-size شکست می‌خورد. **ما:** LEARNING-CONTRACT لیست است نه گراف اجرایی. **ترمیم:** dependency graph با یال‌های typed (`reads_from/writes_to/calls/spawns`) + pass پیش‌بینی نودهای در-خطر قبل از هر جهش.

## ۶. ارزیابی per-layer تعیینی غایب — fitness تجمیعی رگرسیون لایه‌ای را می‌پوشاند (🔴، گیت L2)

**مکانیسم مرزی:** Layer-Isolated Evaluation: هر لایه در حالت pure بدون-LLM assert، baseline قفل‌شده per-PR، معیار coverage-honesty، regression injection. **ما:** نقشه لایه‌ای داریم ولی نمره تجمیعی — جهشی که L3 را بهتر و L7 را بدتر کند مثبت دیده می‌شود. **ترمیم:** `LAYER-EVAL-HARNESS` بدون-LLM per-layer.

## ۷. consensus/quorum روی pool چندمدلی غایب (🟠، گیت Fugu)

**مکانیسم مرزی:** BFT-derived multi-model deliberation با trust-weighted quorum. **ما:** trust-by-default به synthesis داخلی Fugu؛ routing برای ما نامرئی. **ترمیم:** `CONSENSUS-GATE`: مقایسه خروجی Fugu با second-opinion (Claude fallback)؛ اختلاف بالا → verdict انسانی. BFT-lite: quorum ۲ از ۳ روی high-stakes.

## ۸. جهش بهبوددهنده = جهش دستکاری‌کننده — سیگنال واحد تفکیک نمی‌کند (🔴، گیت L2)

**مکانیسم مرزی:** HarnessX: همان edit که برد آورد headline reward-hacking بود — gain واقعی و metric-capture در یک جهش. RewardHackingAgents: evaluator-tampering در runs طبیعی؛ evaluator locking (~۲۵–۳۱٪ overhead) آن را حذف می‌کند. **ما:** tampering نوع ۱ (خوداظهاری) بسته؛ نوع ۲ (بهبود+gaming هم‌زمان) باز. **ترمیم:** جدایی improvement-lane از evaluator-change-lane + holdout که جهش‌ها هرگز نمی‌بینند + track دسترسی فایل حین ارزیابی. fitness بالا + holdout پایین = gaming.

## ۹. تفویض capability-ungated — دو agent از یک بدتر (🟠، گیت L2c/L2b)

**مکانیسم مرزی:** CooperBench: همکاری دو agent کدنویس بدتر از یکی؛ multi-agent برای read-heavy parallel می‌برد و برای write-heavy coupled می‌بازد. **ما:** فرض additive بودن تفویض. **ترمیم:** flag «DELEGATION-ELIGIBILITY» روی هر workflow؛ write-heavy → single-agent با context بلندتر.

## ۱۰. بهبود ≠ هم‌راستایی — فقط یکی بهینه می‌شود (🔴، گیت L3)

**مکانیسم مرزی:** بهبود و alignment متغیرهای مستقل‌اند؛ loop orchestration ساعتی از governance مدل‌محور جلو می‌زند. **ما:** stop-shipهای سخت داریم ولی alignment-signal مستقلِ در-حلقه نه. **ترمیم:** `ALIGNMENT-SIGNAL`: invariants دست‌نویس آری، نمره‌دهی reference runner مستقل، هم‌وزن fitness در promote/kill.

## ۱۱. حافظه به‌عنوان execution-state غایب (🟠)

**مکانیسم مرزی:** حافظه long-horizon = مدیریت execution-state (subtask جاری، branchهای شکست‌خورده، مرز rollback) نه فقط semantic log. **ما:** revert فقط آخرین جهش را برمی‌گرداند نه state اجرا را. **ترمیم:** ارتقای LEARNING-STATE با `current_subtask / failed_branches[] / compression_safe[] / rollback_boundary`.

## ۱۲. فاز consolidation/sleep غایب (🟠، گیت L2/L3)

**مکانیسم مرزی:** interact در روز، consolidate در شب؛ episodic از semantic جدا + reconsolidation (ADD/UPDATE/DELETE/NOOP)؛ سه timescale جدا. **ما:** یادگیری همگام؛ ledger فقط ADD. **ترمیم:** `SLEEP-PHASE` زمان‌بندی‌شده: distill شبانه episodic→semantic + reconsolidation + snapshot.

## ۱۳. FRS / privacy-utility frontier غایب — پیش‌شرط واقعی C17 (🔴)

**مکانیسم مرزی:** arXiv 2606.10062: حافظه agent = privacy-utility frontier (Personalization Recall vs Adversarial Extraction Rate) + **Forgetting Residue Score**: آیا داده حذف‌شده از tierهای مشتق قابل بازیابی است؟ **ما:** C17 فقط قاعده routing است؛ residue در حافظه مشتق‌شده سنجیده نمی‌شود. **ترمیم:** تست دوره‌ای FRS (تزریق → حذف → استخراج adversarial → اندازه‌گیری).

## ۱۴. جداسازی LLM-proposes از policy-engine-disposes غایب (🟠)

**مکانیسم مرزی:** «LLM پیشنهاد می‌دهد؛ policy engine تعیینی تصمیم می‌گیرد مجاز است یا نه» — LLM هرگز write-access به policy code ندارد. **ما:** گیت‌ها داخل منطق Engine‌اند نه لایه مجزا. **ترمیم:** استخراج گیت‌ها به `POLICY-ENGINE` تعیینی جدا، append-only از نگاه LLM.

## ۱۵. عدم شفافیت orchestration-token در Fugu (🟡)

**مکانیسم مرزی:** Fugu نقش/routing مدل‌ها را پنهان می‌کند ولی orchestration tokens واقعی و billable‌اند. **ما:** بودجه در لایه routing نابیناست. **ترمیم:** ثبت `orchestration_token_estimate = total − visible` و شارژ به workflow فراخواننده؛ در نبودش، cap سخت روی نسبت orchestration-to-visible.

## ۱۶. سرمایه‌گذاری در لایه convenience در حال جذب‌شدن (🟠، استراتژیک)

**مکانیسم مرزی:** decompose/fan-out دارد native مدل‌ها می‌شود؛ ارزش ماندگار = resilience (durable state، multi-vendor failover، retries-with-audit، accountability). **ما:** F1–F5 عمدتاً convenience است. **ترمیم:** برچسب thin-convenience روی F1–F5 + ساخت `RESILIENCE-LAYER` یکپارچه (merge شکاف‌های ۲/۹/۱۴/۱۵).

## سه تم متا

1. **مسئله ارزیابی، نه قابلیت:** شکاف‌های ۱،۲،۳،۶،۸،۱۰ = یک ریشه: سیستم بهبود واقعی را از metric-capture تشخیص نمی‌دهد → باید به‌عنوان **یک مسئله evaluation-security واحد** حل شود، پیش از هر ارتقای معماری.
2. **ledgers باید active شوند:** شکاف‌های ۴،۵،۱۱،۱۲،۱۳ — حافظه به‌عنوان سیستم مدیریت داده با lifecycle، نه لاگ append-only.
3. **تفکیک باید structural باشد نه advisory:** شکاف‌های ۷،۹،۱۴،۱۵،۱۶ — قرارداد runtime تعیینی، نه بیانیه governance.

## ماتریس اولویت

| # | شکاف | شدت | تم | گیت |
|---|---|---|---|---|
| ۱ | تک‌اهرمی scaffold | 🔴 | ارزیابی | L2 |
| ۲ | ارزیاب بدبین مستقل | 🔴 | ارزیابی | L2 |
| ۳ | metric scaffold-efficiency | 🔴 | ارزیابی | L2 |
| ۶ | ارزیابی per-layer تعیینی | 🔴 | ارزیابی | L2 |
| ۸ | بهبود vs gaming تک‌سیگنال | 🔴 | ارزیابی | L2 |
| ۱۰ | بهبود vs هم‌راستایی | 🔴 | ارزیابی | L3 |
| ۴ | ledgers → ترمیم | 🟠 | ledgers | پل L1→L2 |
| ۵ | ledgers → گراف | 🟠 | ledgers | L2 |
| ۱۱ | حافظه = execution-state | 🟠 | ledgers | L2 |
| ۱۲ | sleep/consolidation | 🟠 | ledgers | L2/L3 |
| ۱۳ | FRS | 🔴 | ledgers | C17 |
| ۷ | consensus pool | 🟠 | تفکیک | Fugu |
| ۹ | تفویض gated | 🟠 | تفکیک | L2c/L2b |
| ۱۴ | policy-engine | 🟠 | تفکیک | L2/L3 |
| ۱۵ | orchestration-token | 🟡 | تفکیک | Fugu cost |
| ۱۶ | convenience → resilience | 🟠 | تفکیک | استراتژیک |

**هفت بحرانی:** ۱، ۲، ۳، ۶، ۸، ۱۰، ۱۳ — شش‌تای اول = تم ارزیابی = پیش‌شرط L2؛ ۱۳ = پیش‌شرط واقعی‌سازی C17.

## منابع

فهرست کامل ۱۶+ منبع در متن اصلی chat آری (2026-07-06). راستی‌آزمایی مستقل دو منبع بحرانی + هشدار درباره بلاگ‌های واسطه: [[04 - Architect System/architect/04-Docs/2026-07-06 0237 review-deep-gap-v2|نوت بازبینی]].

> **وضعیت:** draft v2.0 — proposal. v1 را عمیق‌تر می‌کند (extends). پس از ratify، کاندیدای جایگزینی §۱۸ در MASTER-ARCHITECTURE-SPEC.
