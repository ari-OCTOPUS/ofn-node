---
type: evidence
schema: octopus-heart-g4-genome-tip-blocker/1
status: PROMOTION_BLOCKED
created: 2026-08-25
scope: read-only-forensics
---

# G4 promotion blocker — genome tip count mismatch

## Gate result

```text
Ledger.verify()     = PASS (ok)
Ledger.verify_tip() = FAIL (length mismatch: file=14656 tip=14294)
```

No repair, `seal_tip()`, rewrite, append, or sidecar deletion was performed.

## Facts measured read-only

- Ledger: `07 - Knowledge/genome-system/ledger/ledger.jsonl`
- Parsed records: `14656`
- Non-empty physical lines: `14656`
- Malformed JSON records: `0`
- Hash-chain verification: `PASS`
- Current final ledger hash: `967b4688474e0e10771eb5af89d500af3fd9439c3bf9ea93851554c6d78f9292`
- Sidecar `tip_hash`: exactly the same final hash
- Sidecar `n`: `14294`
- Count delta: `362`
- Ledger and sidecar were both updated around `2026-08-25T00:33:38Z`.

The matching final hash means the sidecar points at the current chain head. The failing count means its length claim is not trustworthy. This is not evidence of a current tail truncation, but it still fails the explicitly approved `verify AND verify_tip` promotion gate.

## Records in the 362-row count gap

All 362 rows parse and are chain-linked. Actors include:

- debate: 137
- scheduler: 79
- governor: 59
- self-improve: 34
- heart-work-pump: 19
- auto-approve: 10
- organism: 6
- reconcile-beat: 6
- doctor: 4
- pacemaker: 3
- heart-doctor: 3
- cortex-synthesis: 2

Types: NOTE=322, PROPOSAL=37, HEARTBEAT=3.

The first physical row after sidecar count position has an earlier timestamp than the sidecar's current timestamp, while the sidecar's hash matches the final row. This is consistent with a historical count offset that later appends preserved via `prev_n + 1`, a backfill/reanchor/replacement, or a direct append path; it is not by itself proof of which mechanism occurred.

## Decision

G4 remains:

```text
PATCH_VERIFIED_NOT_PROMOTED
```

No live source patch and no organism restart will occur while this gate is red. A forensic review of ledger history/writers is in progress. The least-destructive next action will be chosen only after that review; blindly resealing would erase the mismatch evidence and is prohibited.
