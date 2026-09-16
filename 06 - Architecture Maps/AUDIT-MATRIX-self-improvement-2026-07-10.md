---
type: architecture
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [audit, self-improvement, governance]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "[[01 - Dashboard/HANDOFF]]"
  - "_ops/cortex/self_audit.py"
  - "_ops/cortex/improve.py"
---

# Audit Matrix — چک‌لیستِ ۲۰-بخشیِ مالک مقابلِ کدِ واقعی (2026-07-10)

> ورودی: چک‌لیستِ حاکمیتِ multi-agentِ production-grade که مالک داد. روش: ممیزیِ موازیِ
> ۱۲-ایجنتی مقابلِ `_ops` واقعی (۱.۵M توکن) + verifyِ خصمانهٔ Doneها + موتورِ ماشین‌خوانِ
> `self_audit.py` که این ماتریس را **در لوپ** بازتولید می‌کند (`state/cortex/audit-matrix.json`).

## بلوغِ فعلی: **~۶۹٪** (۱۹ Done · ۱۲ Partial · ۵ Missing از ۳۶ probeِ ماشین‌خوان)

نسخهٔ زندهٔ همیشه‌تازه: `state/cortex/audit-matrix.json` + دایجستِ owner-facing:
`state/cortex/upgrades-digest.json` (در تلگرام `/upgrades`، در اتاقِ زنده چیپِ 🧬).

## ستون‌فقراتِ ایمنی — محکم (Done، داده‌زنده)

- **kill-switch مطلق:** STOP در صدرِ هر حلقه (organism/cortex/هر *_beat). §13
- **propose-only + $0:** هر call از organ_gate→budget_gate (تنها enforcer). §1
- **هویتِ تک‌مالک:** allowlistِ chat_id تلگرام؛ first-birth فقط مالک. §1
- **منبعِ حقیقت:** ledgerِ hash-chainedِ ژنوم (tamper-evident)؛ chrono.db فقط cache؛ replay موجود. §5
- **secrets:** `.agentignore` + env_loader بدونِ echo + keys_present فقط bool. §14
- **redaction:** هر خروجیِ تلگرام/زنده از `contains_secret/redact`. §14
- **sim/shadow قبل از هر اقدام:** sim_heart + allocate_dry + sandbox + shadow-mode. §18
- **ریاضیِ قفل‌شده:** PULSE-EQUATIONS-LOCKED (MC-validated، sha256). §3/§17
- **regression suite:** ۸۸ فایل تست + capability marker + held-out canaries. §11

## گاف‌های P0 — یافته‌های سختِ ممیزی (که probeهای اولیه زیادی سخاوتمند دیده بودند)

| # | گاف | یافته | بخش |
|---|---|---|---|
| 🔴 | **human-append جعل‌پذیر** | `human_append_guard._default_guard` **کدمردهٔ غیرفعال** است؛ configure/authorize هرگز در production صدا زده نمی‌شوند → `is_human=True` قابلِ‌جعل. | §15 |
| 🔴 | **verdictِ مالک بی‌اثر** | `apply_merge` تعریف‌شده ولی **هرگز در runtime صدا زده نمی‌شود** → «merge-approved» فقط برچسب است، نه اعمال. | §15 |
| 🟠 | **حلقهٔ خودتحلیل ناقص** | دکتر mine/rfc/sandbox می‌کند ولی eval واقعی (`measured_lift`) stub است + db تا این جلسه تزریق نمی‌شد (calibration داده‌مرده). **db در این جلسه فیکس شد.** | §9/§10 |
| 🟠 | **سطح‌بندیِ تغییر غایب** | tune/reconfig/rewrite/code بدونِ change-contract. **`improve.py` این را اضافه کرد.** | §10 |

## گاف‌های P1/P2 (دسته‌بندی‌شده — رأی مالک «هر چه پیدا کرد، دسته‌بندی‌شده»)

- **governance:** autonomy-level در OWNER-PROFILE خوانده نمی‌شود · memory-poisoning مانیتورِ خودکار ندارد · owner-mapping per-agent صریح نیست.
- **architecture:** registryِ coherence فایل‌ها را می‌بیند نه ایجنت‌های تصمیم‌گیر (doctor/legs/box/debate غایب از MEMBERS) · debate_loop off · simplify-governance برای زیرسیستم‌های unwired نیست.
- **observability:** epistemic-signals (off) · cost/latency-trace واحد نیست · drift-metric نیست.
- **theory:** single-agent baseline justification نیست.
- **implementation:** registryِ RFC in-memory (با restart گم) · pipelineِ design-doc→doctor نیست (idea_graph جدا).

## چه در این جلسه ساخته شد (حلقهٔ خودارتقاییِ owner-facing — لایهٔ غایب)

1. **`_ops/cortex/self_audit.py`** — ۳۶ probeِ ماشین‌خوان؛ ماتریسِ زنده در لوپ (honest Missing/Partial، نه سبزِ دروغ).
2. **`_ops/cortex/improve.py`** — از audit + RFCهای دکتر + idea_graph + coherence → پیشنهادهای **دسته‌بندی‌شدهٔ** اولویت‌دار؛ سطح‌بندیِ تغییر؛ propose-only مگر پرچمِ `ACTIVATION-SELF-IMPROVE-AUTO` (فقط knobهای $0 برگشت‌پذیرِ whitelist)؛ یادگیری از verdict؛ مغزِ محلیِ $0.
3. **وایرینگ:** در چرخهٔ cortex هر ۱۰ چرخه؛ `/upgrades` تلگرام؛ چیپِ 🧬 اتاقِ زنده.
4. **فیکسِ زندهٔ db دکتر** (organism.py) — اولین پیشنهادِ خودِ حلقه به خودش (calibration زنده شد).
5. **اهرمِ `ACTIVATION-RESEARCH-EARLY`** — مالک می‌تواند سپرِ تاریخِ تحقیقِ پولی را زودتر باز کند.

## قدمِ بعد (که حلقه حالا خودش به مالک پیشنهاد می‌دهد)

دو P0 امنیتی — **enforceِ human_append_guard** و **وایرینگِ apply_merge** — چون هستهٔ خود-تغییردهی و امنیت‌اند، عمداً auto نشدند؛ در دایجستِ `/upgrades` صدرِ صف‌اند تا با تأییدِ صریحِ مالک (یا ایجنتِ بعدی با احتیاط) اعمال شوند. بقیهٔ گاف‌ها در دایجست، دسته‌بندی‌شده.
