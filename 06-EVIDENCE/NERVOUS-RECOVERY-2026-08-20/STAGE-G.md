---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave0, ledger]
---

# Stage G — merge and verdict

Reality Ledger: `reality-ledger.jsonl` (append-only, dedupe on finding_id + evidence hash).

Merged artifact classes: REALITY_SNAPSHOT, TEST_REGISTRY, RECEIPT_ATTRIBUTION_AUDIT, CAPABILITY_INVENTORY, MEMORY_READ_GATE, NERVOUS_RECOVERY, DEEP_SCAN, SEAM_HUNT, CANARY_CORTEX, STAGE_A/B/C.

Conflicts recorded, not deleted:

- `CONFLICT-ATTR-DENOMINATOR` — today-full 0.3423 vs schema-present 1.0
- `CONFLICT-C048-NUMBER` — S-B01 vs S-A14 both labelled C-048
- `CONFLICT-BCM-CONSUMER` — EFFECTORS display-only vs DEEP-SEAMS readers

C-048..C-053 remain **candidates**. Zero writes to `01-TRUTH/CONTRADICTIONS.md`.

`wave1_unlocked` remains false even if WAVE0_PASS is confirmed. Wave 1 needs a separate owner command.
