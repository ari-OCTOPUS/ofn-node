# EXECUTION-ORDER — Orange Pi CHG A+B+D

**Authorization:** `OCTOPUS-ORANGEPI-CHG-ABD-20260822`  
**Written (AEST):** 2026-08-22T16:53:45+10:00  
**Executor:** sensoriom @ sensorium-opi5pro (192.168.0.182)  
**Laptop:** plans + grant only

## Recommended sequence: **A → D → B**

| Step | CHG | Why this order |
|------|-----|----------------|
| 1 | **A** Sensorium watchdog / defer index | Stops the sensorium READY/watchdog storm (~1411 restarts). Frees CPU/IO so ledger repair and soaks are observable. Lowest coupling to ledger writers. |
| 2 | **D** Ledger append-only repair | Fixes duplicate seq=9024 / break_seq=9025 while WM thrash is still risky. Integrity before raising WM budget. May briefly mask WM writers as part of D freeze. |
| 3 | **B** WM/skill MemoryMax floor (or unmask+floor) | After ledger verify PASS, raise MemoryMax to 128–256M (still capped). If B2 mask was used during D, unmask here then apply floor. |

## Why not A→B→D

B thrash against a broken ledger can worsen duplicate/conflict appends while D is open. Raising MemoryMax before repair increases write pressure on a broken chain.

## Why not D first

D is safer with A already damping the board sensorium storm (IO/CPU noise). A does not require a healthy prediction ledger to succeed.

## Parallelism

- A soak can continue while D prep (backup/hash) runs.
- B2 **temporary mask** may start at D freeze (not a full B1 raise).
- **Do not** start C (NATS) or E (compaction) — not authorized.

## Gate checklist before declaring package done

1. A: sensorium READY stable; watchdog storm stopped; receipt.
2. D: verify_all_ledgers.py PASS; duplicate quarantined; receipt.
3. B: MemoryMax in [128M,256M] (or documented temporary mask cleared); OOM storm stopped; no torch; still capped; receipt.
4. Update TO-LAPTOP exchange + laptop evidence ack.
5. Wave0 actuators/MQTT/legs still locked.

## Abort

Any forbidden-surface touch, verify_all FAIL after claimed repair, or unconstrained MemoryMax → STOP package, rollback that CHG, report to owner via ari.
