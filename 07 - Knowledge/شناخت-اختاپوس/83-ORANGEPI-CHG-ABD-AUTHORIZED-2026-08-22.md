# 83 — Orange Pi CHG A+B+D authorized (2026-08-22)

**AEST:** 2026-08-22T16:53:45+10:00  
**Auth ID:** `OCTOPUS-ORANGEPI-CHG-ABD-20260822`  
**Links:** [[82-EXPEDITED-BOUNDED-LIVE-ROLLOUT-2026-08-22]] · evidence `06-EVIDENCE/OCTOPUS-ORANGEPI-CHG-ABD-2026-08-22/`

## Decision

Owner authorized Orange Pi package **A + B + D** with **separate plans**. Executor: **sensoriom** on `sensorium-opi5pro` (192.168.0.182). Laptop files plans + OWNER-CHG grant only — does not SSH/mutate the Pi.

## Package

| CHG | Summary |
|-----|---------|
| A | WatchdogSec 120–300s and/or defer heavy `_save_index` until READY+pet; quarantine `TAINTED_WINDOW_sensorium-cpu.yaml` |
| B | MemoryMax floor 128–256M (capped) or temporary mask until ledger fixed; no torch; no unconstrained |
| D | Append-only repair duplicate seq=9024 / break_seq=9025; quarantine duplicate; new epoch if needed; never silent hash rewrite; `verify_all_ledgers.py` |

**Not authorized:** C NATS · E compaction (unless incidental to A)

## Execution order

**A → D → B** — A stops sensorium storm; D repairs ledger before WM write pressure rises; B then raises capped MemoryMax (or unmasks).

## Still forbidden (global)

private keys/make-root-v2 · MQTT/PWM/legs/root action_executor · arm reflex · planner · Doctor auto-patch on Pi · torch WM · open 9101 to LAN · zero-fill sensors · in-place hash rewrite · truncate observations casually · unconstrained WM on 3.8Gi

## Next

Paste `SENSORIOM-EXECUTE-BRIEF.txt` to sensoriom; collect receipts on TO-LAPTOP exchange; then Board2 wire remains queued after CHG execution evidence.


## Execution result (2026-08-22 ~17:02 AEST)
- A PASS WatchdogSec=180 NRestarts=0
- D PASS ledger verify ok prediction seq=9029
- B PASS MemoryMax=128M WM+skill NRestarts=0
- C/E deferred; WAVE0 actuators locked
