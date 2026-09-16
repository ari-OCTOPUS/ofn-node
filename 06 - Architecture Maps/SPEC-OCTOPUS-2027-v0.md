---
type: architecture
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [spec, governance, autonomy, 2027]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "[[06 - Architecture Maps/AUDIT-MATRIX-self-improvement-2026-07-10]]"
  - "[[01 - Dashboard/HANDOFF]]"
---

# SPEC — Octopus 2027 v0 (چک‌لیستِ ۲۲-بخشیِ مالک → نقشهٔ اجراییِ grounded)

> ورودی: چک‌لیستِ 2027-gradeِ مالک (control plane · autonomy ladder · handoff · GAAT-telemetry
> · learning contract · artifacts اجباری). روش: **هیچ بندی روی کاغذ نمی‌ماند** — هر بند یا به
> فایلِ موجود نگاشت می‌شود، یا probeِ ماشین‌خوان در `self_audit.py` می‌گیرد، یا واردِ صفِ
> `/upgrades` می‌شود. نسخهٔ زندهٔ وضعیت: `state/cortex/audit-matrix.json`.

## §۱ هویتِ سیستم (یک‌خطی، سنجش‌پذیر)

**Octopus = ارگانیسمِ عملیاتِ شخصیِ خودبهبودگر**: بدنِ همیشه-روشنِ $0 (متابولیسم/قلب/پمپ)
+ مغزِ کنترل‌گرِ جدا (کورتکس) + دکترِ تکاملیِ propose-only + سطحِ انسانیِ تلگرام.
- **mission سنجش‌پذیر:** velocityِ تأییدشدهٔ شناختی/پولی ↑ در حالی که σ≤1، spend≤سقفِ ماهانه، و هیچ اقدامِ برگشت‌ناپذیر بدونِ human-append.
- **non-goals تا 2027:** multi-tenant/VPS (O-01 باز)، بازنویسیِ ژنومِ Anthropic-tier، جایگزینیِ قضاوتِ مالک.
- **ارزش vs single-agent:** هنوز اثبات نشده — probeِ باز (§۲۱-۴).

## §۲/§۳ control plane + registry

| لایه | واقعیت |
|---|---|
| orchestration plane | cortex (8772) — جدا از execution (organism 8771) ✅ |
| registry | `cortex/registry.py` (اعضای state-محور) + `budgets.yaml routing` (مغزها) — **گپ:** ایجنت‌های تصمیم‌گیر (doctor/legs/box/debate) عضو نیستند |
| policy | قانونِ اساسی + `.agentignore` + live_gateها ✅ |
| memory | ledger (canon) + consolidation/BCM + school ✅ |
| observability | live 8773 + cockpit + audit-matrix ✅ |

## §۴ نردبانِ خودمختاری (رسمی — از این پس مرجعِ همهٔ ماژول‌ها)

| سطح | معنا | نگاشتِ واقعی | گیت |
|---|---|---|---|
| **L0** observe | فقط می‌خواند/گزارش می‌دهد | cortex sweep، self_audit، producers | همیشه مجاز |
| **L1** propose | پیشنهاد به مالک | doctor RFC، improve digest، needs | همیشه مجاز (propose-only پیش‌فرضِ کلِ سیستم) |
| **L2** auto-tune | knobهای $0 برگشت‌پذیرِ whitelist | improve.AUTO_KNOBS | `ACTIVATION-SELF-IMPROVE-AUTO` + refractory + observability-ok |
| **L3** auto-reconfig | ترتیب/فاصلهٔ کارِ $0 درون‌کران | cortex.align_work_plan | `OCTOPUS_WIRE_HEART_WORK` + کران‌های تست‌شده |
| **L4** sandboxed patch | تغییرِ کد فقط در sandbox | doctor.run_sandbox | همیشه ایزوله؛ هرگز production |
| **L5** production change | اعمالِ واقعی | apply_merge (**فعلاً unwired — P0**) | human-append + verdictِ تلگرام + rollback-tag |
| degrade | هر سطح → L1 | خودکار وقتی observability بمیرد (گاردِ نو در improve) | — |

## §۷ handoff — تصمیمِ معماری (صادقانه)

این سیستم agent-to-agent chat-handoff ندارد و **عمداً** state-file-handoff است: هر تولیدکننده
یک فایلِ schema-دار می‌نویسد (`schema: X.v1` — heart-signals.v1، cortex-state.v1،
work-plan.v1، audit-matrix.v1، upgrades-digest.v1) و مصرف‌کننده fail-soft می‌خواند.
**قرارداد:** هر state-file جدید باید `ts` + `schema` نسخه‌دار داشته باشد + خواندنِ fail-soft.
raw pointer همیشه کنارِ خلاصه (ledger/journal append-only). حدِ handoff = عمقِ ۱ (فایل)،
پس context-collapse زنجیره‌ای ساختاراً ممکن نیست.

## §۸/§۹ observability + governanceِ اجرایی — دو گاردِ نو (این جلسه کد شد)

- **گاردِ GAAT (§۲۱-۱):** اگر ORGANISM-STATE کهنه (>۶۰ دقیقه) یا sweep ناممکن باشد →
  improve حالتِ `observability_degraded` می‌گیرد: **auto-apply سخت‌قفل**، فقط L1، و یک
  آیتمِ P0 صدرِ digest. «مشاهده مُرد = خود-تغییری می‌ایستد.»
- **دورهٔ refractory (§۱۴):** بینِ دو auto-apply حداقل ۲۴h (`improve-auto-state.json`) —
  ایجنت پشتِ‌سرِهم به معماریِ خودش دست نمی‌زند؛ الهام از pulse→gate→refractory ِ chrono.

## §۲۲ — دوازده artifactِ اجباری: وضعیت

| artifact | وضعیت | مکان |
|---|---|---|
| Agent Registry | 🟡 Partial | cortex/registry.py + budgets routing (گپ: ایجنت‌های تصمیم‌گیر) |
| Handoff Schema | ✅ (به‌صورتِ state-file contract، §۷ بالا) | همین SPEC + فیلدهای schema |
| Log/Trace Schema | 🟡 Partial | ledger NOTE+subtype + journal + work-log (taxonomy واحد نیست) |
| Memory Contract | ✅ | قانونِ اساسی §۶–۹ + consolidation/BCM |
| Learning Contract | ✅ | LEARNING-CONTRACT (GOVERNOR+MUSE، propose-only mode) |
| Governance Ruleset | ✅ | _PROJECT_INSTRUCTIONS + ARCHITECT_CHARTER + live_gates |
| Autonomy Ladder Spec | ✅ (این سند §۴) | SPEC-OCTOPUS-2027 |
| Evaluation Harness | ✅ | run_all (۸۸) + sim_heart + sog_math + held-out |
| Shadow Promotion Workflow | ✅ (الگوی sim→shadow→flag→owner) | HH-P4/P5 + doctor sandbox |
| Rollback Playbook | 🟡 Partial | pre-merge tags + RESTART mechanism (سندِ واحد نیست) |
| Decision Ledger | 🟡 Partial | AGENT_QUESTIONS verdicts + ledger NOTEها (تجمیع نیست) |
| Vitals Dashboard | ✅ | live 8773 (هولوگرام) + cockpit v2 |

## ترتیبِ اجرا (تطبیقِ پیشنهادِ ۸-گامیِ مالک با واقعیت)

گام‌های ۱،۲،۴،۵ عملاً انجام‌شده‌اند (truth-source/observability/memory/shadow-loop). باقی به ترتیب:
1. **گام ۳ (فعال):** همین SPEC = autonomy ladder + دو گاردِ governance (کد شد).
2. **گام ۶:** validator/replay — دو P0ِ باز: enforceِ human_append_guard + سیمِ apply_merge (**رأی مالک، AGENT_QUESTIONS «22:30»**) + evalِ واقعیِ measured_lift.
3. **گام ۷:** ارتقایِ محدودِ L2 (auto-tune) فقط بعد از یک هفته دادهٔ سایه + رأی.
4. **گام ۸:** recursionِ سطحِ معماری — فقط بعد از ثباتِ ۶ و ۷ (refractory حاکم).

## پرسش‌های سختِ §۲۱ — پاسخِ ثبت‌شده

1. observability بمیرد؟ → گاردِ نو: خود-تغییری فوراً L1. ✅ کد شد.
2. critic خراب شود؟ → verdict-learning + سقفِ attention + سطحِ L5 همیشه انسانی. 🟡
3. canon آلوده شود؟ → ledger hash-chained + germline restore-drill + قرنطینهٔ created_by. 🟡 (recovery-runbook واحد نیست)
4. single-agent ارزان‌تر همان را بدهد؟ → صادقانه: هنوز نسنجیده‌ایم؛ probeِ باز، نگهِ backlog.
5. روایتِ قشنگ vs شواهدِ ضعیف؟ → قاعدهٔ خانه از قبل: فقط trace/ledger مرجع است.
6. geometry بدونِ سودِ عملی؟ → بله حاضریم ساده کنیم — معیار: هر لایهٔ ریاضی باید به تصمیم وصل باشد (قلب→cadence وصل است؛ epistemics هنوز decoration → کاندیدِ ساده‌سازی/فعال‌سازی).
