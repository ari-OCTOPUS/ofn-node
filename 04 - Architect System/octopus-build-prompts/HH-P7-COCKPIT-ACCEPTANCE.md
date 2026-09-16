---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [pulse, cockpit, acceptance]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "[[04 - Architect System/octopus-build-prompts/HYBRID-HEART-MASTER-PLAN]]"
  - "[[04 - Architect System/octopus-build-prompts/TELEGRAM-BRAIN-COCKPIT-v2-FULL-BODY]]"
aligns_to: "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
---

# HH-P7 — سطحِ کابین + پذیرشِ نهایی (suite-green)

> gate خروج: **suite-green** — قلبِ سایه در کابینِ تلگرام دیده می‌شود و کلِ سوییتِ ارگانیسم سبز است.

## تحویل‌دادنی‌ها

1. **کارتِ قلب در `cockpit_readmodel.py`** (additive — تب/بخشِ موجودِ مربوط به بدن): از state-fileهای heart (`heart-shadow-latest.json`, `heart-setpoint-latest.json`, `heart-signals-latest.json`, `PULSE-EQUATIONS-LOCKED.json`, `HEART-SIM-REPORT.json`) فقط‌خواندنی:
   - velocity_now + باندِ هدف (setpoint) + گپ؛ Internal-CPI؛ Δ_self_live (+authoritative)؛ σ/zone؛ periodِ سایه vs `TICK_SECONDS` واقعی؛ وضعیتِ قفل‌ها (`e_shadow: locked|excluded`, `i_pred`)؛ `production_wire_open` با دلایلِ باز/بسته (شفافیتِ ۸ شرط)؛ epoch_seqِ setpoint.
   - fail-soft: فایلِ غایب → «—» (کابین هرگز کرش نمی‌کند)؛ redaction-safe (از `redact/contains_secret` موجود عبور).
2. **پذیرش**: هر ۴ فایلِ تستِ heart در `run_all.py` ثبت و **کلِ سوییت سبز** با `REAL_VAULT=<worktree>` (تا کدِ همین شاخه سنجیده شود، نه live-tree). گزارشِ عددی در HANDOFF.
3. **تست** (`test_heart_loop.py` یا فایلِ کابین): با state-fileهای ساختگی در mini-vault، کارت مقادیرِ درست را نشان می‌دهد؛ فایلِ غایب → کرش نه؛ هیچ secret در خروجی.

## خطوطِ قرمز

کابین فقط‌خواندنی است — هیچ دکمهٔ فعال‌سازیِ قلبِ زنده در تلگرام (فعال‌سازی = فایلِ flag که فقط مالک از فایل‌سیستم می‌سازد؛ ضدِ فعال‌سازیِ تصادفی/جعلی) · وضعیتِ «سبز» بدونِ ownerAck برای exclusionها render نمی‌شود · مسیرِ پول (`app:*`) بایت‌به‌بایت دست‌نخورده.
