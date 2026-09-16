---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
source: "[[06 - Architecture Maps/CELLULAR-MODEL-ROSETTA]]"
tags: [cellular, lifecycle]
created: 2026-01-01
updated: 2026-01-01
---

# چرخهٔ‌عمر — <نامِ سلول/ایجنت>

> ۹ حالت + شرطِ گذار. نگاشت روی مکانیزمِ واقعی (نه رفتارِ نو).

| حالت | یعنی چه | شرطِ ورود | مکانیزمِ واقعی |
|---|---|---|---|
| Dormant | خواب، بی‌سیگنال | idle_epochs | phi-accrual `chrono` |
| Hungry | منتظرِ غذا | ورودیِ ناکافی | `afferent` |
| Active | در حالِ کار | سیگنال رسید | `run_cycle` |
| Productive | خروجی می‌دهد | کار موفق | `propose_rfc` |
| Stressed | زیرِ فشار | σ بالا | autoregulation |
| Dividing | تقسیم پیشنهاد | فشار+منبع | `replication` (human-gate) |
| Mutating | جهشِ آزمایشی | فرضیه | `sandbox`/`chamber` |
| Quarantined | قرنطینه | خطا/ریسک | `capability_gate`/FREEZE |
| Archived | بایگانی | بی‌فایدگی | `fitness`/λ_persist |
