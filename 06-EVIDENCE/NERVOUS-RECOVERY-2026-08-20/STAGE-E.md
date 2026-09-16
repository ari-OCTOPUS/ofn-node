---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave0, memory]
---

# Stage E — memory continuity (observe only)

No new memory writer. No Wave 1. Observer polls `_ops/state/pulse/memory-read-latest.json` and appends unique beats to `memory-continuity.jsonl`.

Contract:

- trailing consecutive healthy ticks, not a sum of reads
- `reads_per_cycle >= 3`, `readback=read_ok`, `status=OK`, `executable` is not true
- unique increasing `beat` (integer gaps allowed; live clock is not +1)
- cycle receipt = `memory-obs:{beat}:{observed_at}` (observation receipt, not a cost-receipt)
- first jsonl row without `observed_at` is excluded from the streak

Observer started 2026-08-20T12:20:21Z. At closeout: **15** trailing healthy observed ticks (beats 43390…43420). Gate threshold is 10.
