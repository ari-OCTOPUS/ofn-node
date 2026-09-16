---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave0, attribution]
---

# Stage B — attribution plumbing

Writers (code trace):

- `_ops/cortex/model_router.py` paid path (`CostReceiptAdapter().build` → append `cost-receipts.jsonl`)
- same file, F15 local-fallback path (now also passes resolver ids; datetime import was previously out of scope)
- `brain.daemon`: **not a writer** of this jsonl → restart withheld

Resolver: `_ops/nervous_recovery/task_context.py`

- caller `task` argument
- explicit `run_id→task` map
- `OCTOPUS_TASK_ID` only when `OCTOPUS_RUN_ID` matches
- else `task_id=null`

Original jsonl not rewritten. Pre-schema 98 rows remain UNATTRIBUTED in today-full forensic (0.3423). Gate uses schema-present rows: **51/51 = 1.0**.

Rollback: restore `_ops/cortex/model_router.py` from git parent of the Wave0 plumbing commit; do not rewrite receipts.
