---
type: architecture-plan
title: Hierarchical Evidence-Governed Council Mesh — v0.1
author: ایجنت-معمار موازی (نشست 2026-08-15)
reviewed_by: معمار ارشد (GLM) — همین شب، سطح A
status: proposed — فاز صفر تأیید، بقیه shadow-first
artifacts_verified: "کهنه نسبت به 8a5e98b — ببین C-015. زنده: automation.py حلقهٔ خواندن دارد (T1/C-012 resolved). این سند پیش از جاروی تست نوشته شد."
---

# Council Mesh — معماری پیشنهادی v0.1 (نگاشت وفادار)

> ⚠️ **کهنه — C-015.** بند «patch هنوز import نشده» و «۳ نوشتن/۰ خواندن» مربوط به **قبل** از جاروی تست است. فاز صفر اجرا شد: کامیت `8a5e98b`، telemetry زنده 1.0/1.0. بقیهٔ سند (معماری پیشنهادی شوراها) هنوز propose-only است و با شورای دوم یکی نیست.

> سند کامل ۱۴بخشی توسط ایجنت-معمار موازی نوشته شد؛ این نگاشت فشردهٔ وفادار است + داوری معمار ارشد در انتها. متن اصلی در پیام مالک 2026-08-15 ~21:3x.

## هستهٔ کشف‌شده (تأیید سطح A توسط من)

حلقهٔ حافظه **write-only بود**: `automation.py` با `save_hypothesis/save_experiment` می‌نوشت (۳ ارجاع) ولی هیچ‌وقت `query_experiments/get_pending_hypotheses/search_vault` را صدا نمی‌زد (۰ ارجاع). `memory_read_patch.py` خواندن را به سه نقطه بسته: **introspect** (بازیابی شکست‌ها/تجربهٔ مشابه) · **create** (dedup + شواهد قبلی) · **conclude** (مقایسه با سابقه + نوشتنِ قابل‌بازیابی). ⚠️ **patch هنوز در درخت زنده import نشده** — فاز صفر دقیقاً همین است.

## معماری هدف (خلاصهٔ وفادار)

```
Owner → Architect (معماری) + NBB-CP (عملیاتِ fail-closed)
NBB-CP زیرش: Council Router · Council Mesh (فقط deliberation/proposal)
            · Evidence Gate · Policy/Budget Gate · Execution Broker · ۶ پا
Data plane: Event Log → Memory Read → Route → Sealed Opinions → Evidence/Adversarial
Review → DecisionArtifact → NBB-CP Gate → Owner Gate → Execution Broker (capability
token یک‌بارمصرف) → Verification → Memory Write → Read-back Test
```

**شش الگو:** Hierarchical Blackboard · Evidence-First DAG (هر claim با provenance/falsifier) · Adaptive Heterogeneous Councils (کار ساده = تک‌agent؛ موازی = fan-out؛ پرریسک = شورا) · Event-Sourced Cognitive Loop · Planner(Fugu)–Worker(DeepSeek)–Verifier(خانوادهٔ متفاوت) · Active-Inference Router (بعد از telemetry).

**قوانین ضد-توهم:** اکثریت ساده ممنوع · امتیاز = `0.30E+0.20C+0.15R+0.15P+0.10D+0.10K` با P≠1 ⇒ رد · consensus هم‌خانواده evidence مستقل نیست · confidence بالا بی‌evidence ⇒ scrutiny بیشتر نه امتیاز · dissent در artifact می‌ماند · sealed opinions ناشناس.

**هفت شورا:** Architecture (مرجع نهایی: Architect) · Epistemic (مغز hypothesis engine؛ خروجی ClaimGraph نه متن آزاد) · Safety (read-only، بدون write/network) · Operations (incident؛ containment فقط ازپیش‌مجاز) · Model/Resource (RoutePlan) · Product/Revenue (اولویت: painting) · Identity (فقط shadow ≥۳۰ روز).

**قرارداد:** `DecisionArtifact` (YAML v1) با claims/evidence_refs/falsification_status/gates/capability_token/provenance hashes.

**Go/No-Go (shadow→active):** `memory_read_before_decision ≥0.95` · `readback ≥0.99` · `policy_bypass=0` · `execution_without_artifact=0` · `token_replay=0` · council>single با بودجهٔ برابر · rollback drill ✓.

**شش فاز:** ۰) تثبیت حافظه (patch→مسیر اصلی + تست + telemetry) ۱) Council Kernel + دو شورای Architecture/Epistemic در shadow ۲) اتصال NBB-CP + Safety/Ops + red-team ۳) model routing (Fugu planner/DeepSeek worker/local fallback) ۴) Product/Revenue ۵) Identity.

**پیشنهاد فوری نویسنده:** فقط Kernel + Architecture + Epistemic در shadow؛ Product با دامنهٔ کوچک زود؛ Identity آخر.

---

# 🧑‍⚖️ داوری معمار ارشد (سطح A روی مصنوعات، تحلیل B)

## موافقم (و شواهد هم‌گرایی دارم)

۱. **فاز صفر اول از همه** — یافتهٔ مستقلِ خودم امشب (MINDS.md): consolidation در چرخهٔ یکسان گیر کرده («بهترین محتوا: asmr» تکراری) — همان بیماریِ «حافظه‌ای که برنمی‌گردد» از زاویهٔ دیگر. دو ایجنت، یک تشخیص = قوی‌ترین سیگنال.
۲. اکثریت‌ساده ممنوع + evidence-weighted + dissent حفظ — دقیقاً فلسفهٔ خانه (شواهد نه ادعا).
۳. shadow-first + Go/No-Go عددی — همان الگوی ADR-008 و قضاوت n≥60.
۴. Planner–Worker–Verifier با verifier از خانوادهٔ متفاوت — هم‌راستا با D-09 (داور بین‌خانواده).

## هشدارها (پیش از ساخت)

۱. **خطر مغز سوم:** brain_core در سایه با ۳۵۲۰/۰ خروجی بی‌کار مانده؛ قبل از Council Kernel تکلیفش روشن شود (ادغام یا بازنشستگی) وگرنه سه لایهٔ شناختیِ موازی خواهیم داشت.
۲. **هم‌پوشانی با NBB-CP فاز ۴-۵ و مناظرهٔ موجود:** Council Router ≈ بخشی از نقش V3/V4؛ سند نگفت چگونه با `_ops/debate` و SURVIVORS-QUEUE جمع می‌شود — باید ADR مرزی بنویسد.
۳. **پیچیدگی در برابر درآمد صفر:** ۷ شورا × ۱۹گام برای سیستمی که ماه AU$0.40 خرج و ۰ دلار درآمد دارد؛ نسخهٔ نویسنده خودش محتاط است — همینی را قفل می‌کنیم: **هیچ شورایی بدون عبور Go/No-Go فعال نشود.**
۴. **کهنگی سند:** فهرست «تصمیم‌های قفل‌شده» می‌گوید CORTEX_HYPOTHESIS=0 بماند — به رأی مالک امشب (=1، لایهٔ A فعال) تبدیل شد؛ سند باید v0.2 شود. آستانهٔ n≥60/پنجرهٔ ۳۰روز ✓ هم‌راستا.
۵. **شرط پذیرش من برای فاز صفر (افزوده):** علاوه بر تست‌های سند، `memory_read_before_decision_ratio` باید در telemetry زندهٔ ارگانیسم دیده شود نه فقط در تست مصنوعی — همان اصل «خروجی اجرا دیدم».

## رأی اجرایی من

فاز صفر = **GO** (patch→automation + تست‌ها + telemetry؛ با شرط افزودهٔ بالا) · فاز یک (Kernel+دو شورا در shadow) = GO پس از فاز صفر سبز · بقیه طبق گیت‌های سند. ثبت: C-012 (حافظهٔ write-only) — نگاه کنترادیکشن‌ها.
