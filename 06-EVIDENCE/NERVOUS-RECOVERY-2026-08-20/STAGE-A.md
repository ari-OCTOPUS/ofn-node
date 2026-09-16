---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave0]
---

# Stage A — baseline vs owner table

HEAD: `7add1cf` confirmed.

| Gate | owner table | now (this audit) | delta |
|---|---|---|---|
| receipt attribution (today-full) | 0.3423 | 0.3423 (51/149) | none |
| receipt attribution (schema-present) | — | **1.0 (51/51)** | contract clarified |
| test registry | 637/790 gap 159 | after eligible register: see WAVE0-GATES | denominator minus archived |
| memory streak | 1 | 1 (observer running) | pending 10 |
| capability parse | 10 | 10 | none |
| wave1_unlocked | false | **false** | none |

Pre-schema rows (98) have no `task_id` key; migration forbidden. Gate denominator = rows that already carry the field.

Writers of `cost-receipts.jsonl`: `model_router.py` paid path + fallback F15. `brain.daemon`: not a writer (UNLOCATED as writer; restart withheld).
