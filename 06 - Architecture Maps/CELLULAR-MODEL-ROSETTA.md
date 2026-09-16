---
type: architecture
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [cellular, rosetta, architecture, metaphor]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "[[06 - Architecture Maps/ECOSYSTEM]]"
  - "[[06 - Architecture Maps/SPEC-OCTOPUS-2027-v0]]"
---

# Cellular Model Rosetta — نگاشتِ استعارهٔ سلولی به ارگانیسمِ *موجودِ* اختاپوس

> ⚠️ **این سند توصیفی است، نه دستورِ ساخت.** هدفش **نامیدن و نگاشتِ** آنچه از قبل در
> `_ops/` زنده است — نه ساختِ یک لایهٔ سلولیِ موازی. **هیچ ماژول/ایجنت/ledgerِ نو
> ساخته نشود.** ضدالگوی «دو-ledger موازی» (هشدارِ جلسهٔ ۴۲) اینجا هم صدق می‌کند:
> اگر جایی نگاشت مبهم بود، **کدِ موجود مرجع است**، نه این استعاره.

## چرا این سند؟

الهامِ Spudcell/سلولِ مصنوعی مفید است چون سیستم **از قبل** یک ارگانیسمِ مولتی‌ایجنتیِ
سلولی است (متابولیسم، تقسیم، جهش، مرگ، ایمنی، نسب). این نقشه استعاره را به مکانیزمِ
واقعی می‌بندد تا هر ایجنتِ تازه‌واردی با «zero prior context» بفهمد کجای بدن ایستاده.

## جدولِ نگاشت (استعاره → مکانیزمِ واقعیِ موجود)

| استعارهٔ سلولی | ماژول/مکانیزمِ زندهٔ موجود |
|---|---|
| سلول / Agent | `_ops/doctor/box/` (`agent_state, dynamics, warden, topology, archivist, sensors, primitive, null_dreamer`) |
| غذا (nutrients) | `_ops/afferent/` (`sensory_bus, ingest_raw, school_bridge`) + `_ops/budget/telemetry.py` |
| پروتئین (خروجی) | `doctor.propose_rfc` → RFC + صفِ survivors |
| تحقیق/ورودیِ دانش | `_ops/cortex/web_research.py` ($0 وب) + `_ops/cortex/self_model.py` (خواندنِ خود) |
| فشار → تقسیم | `_ops/budget/governor_epoch.py` → `_ops/budget/replication.py` (`σ_effective`, `MAX_CELLS`, `SPAWN_PROPOSAL` human-gated, آلارمِ سرطان σ>1) |
| جهش (mutation، sandbox-only) | `_ops/doctor/evolution.py` + `doctor.run_sandbox` + `_ops/doctor/chamber.py` + `temperature.py` |
| مرگ / apoptosis | `_ops/budget/fitness.py` (حذفِ cell روی mismatch) + `λ_persist` منفی |
| سیستمِ ایمنی / منتقد | `_ops/doctor/chamber.py` (۴ صدا) + `box/warden.py` + protective-halt + `capability_gate.py` |
| غشا / حریمِ خصوصی | `.agentignore` + `organ_gate.py` + `money_gate.py` + redaction + human-append guard |
| نسب (lineage) | ledgerِ هش-زنجیرهٔ ژنوم + `_ops/idea_graph.py` + `RFCArchive` (MAP-Elites) |
| مغزِ مرکزی | `_ops/cortex/` (`registry, cortex, self_audit, improve, model_router, synthesis`) |
| قلب / ضربان | `_ops/heart/` (`sog_math, producers, autoregulation, control_law, doctor_setpoint, work_pump`) |
| متابولیسم / بودجه | `_ops/budget/` (`budgets.yaml` سقفِ AU$30، `budget_gate`, `organ_gate`) |

## «چه چیزی از قبل هست» در مقابلِ «چه چیزی صرفاً استعاره است»

- **واقعی و کد‌شده:** همهٔ ردیف‌های بالا به فایلِ اجراییِ موجود اشاره دارند.
- **صرفاً استعاره (بدونِ معادلِ مستقیم — عمداً):** «تمایزِ سلولی به بافت» (سیستم
  organ دارد نه بافتِ چندلایه)؛ «مرگِ برنامه‌ریزی‌شدهٔ کاملِ ارگانیسم» (سیستم mortal
  age دارد ولی خودکشیِ کامل ندارد — عمدی).

## چرخهٔ‌عمرِ سلول → اجزای واقعی (propose-only، فقط توصیف)

| حالت | نگاشتِ واقعی |
|---|---|
| Dormant / Hungry | phi-accrual در `_ops/chrono.py` (`alive/suspected`) + `idle_epochs` |
| Active / Productive | حلقهٔ `run_cycle` دکتر + پمپِ کارِ قلب |
| Stressed | `σ_effective` بالا → autoregulation ترمز |
| Dividing / Mutating | `replication.SPAWN_PROPOSAL` (human-gated) / `evolution` sandbox |
| Quarantined | `capability_gate` / `FREEZE` / protective-halt |
| Archived | `fitness` cell-removal + `λ_persist` |

## پیوندها

نقشهٔ کلان: [[06 - Architecture Maps/ECOSYSTEM|ECOSYSTEM]] · قراردادِ ۲۰۲۷:
[[06 - Architecture Maps/SPEC-OCTOPUS-2027-v0|SPEC-OCTOPUS-2027-v0]] · دانشِ سلولی:
[[07 - Knowledge/cellular-systems/spudcell-notes|spudcell-notes]] ·
[[07 - Knowledge/cellular-systems/synthetic-cell-to-agent-metaphor|نگاشتِ مفهومی]].
