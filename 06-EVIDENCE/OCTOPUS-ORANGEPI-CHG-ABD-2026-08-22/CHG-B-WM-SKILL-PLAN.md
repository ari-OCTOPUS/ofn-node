# CHG-B — WM / skill MemoryMax floor (or temporary mask)

**Authorization:** `OCTOPUS-ORANGEPI-CHG-ABD-20260822` (package A+B+D)  
**Board:** sensorium-opi5pro @ 192.168.0.182  
**Executor:** sensoriom  
**Written (AEST):** 2026-08-22T16:53:45+10:00

## Problem (evidence)

- WM `MemoryMax` ≈ **48 MiB**; NRestarts wm ~**38906**, skill ~**35394** (OOM thrash).
- Board has ~3.8Gi class memory budget elsewhere — **unconstrained WM is forbidden**; torch WM forbidden.

## Goal

Stop OOM restart thrash with an **evidence-based MemoryMax floor (≥128–256M)** OR a **temporary mask** of the unit until ledger (CHG-D) is fixed — whichever is safer given current ledger break.

## Allowed change set

### Path B1 — Raise MemoryMax (preferred once D done or if mask not needed)

1. Before: `systemctl show` for wm + skill units → `MemoryMax`, `MemoryCurrent`, `NRestarts`, cgroup pressure if available.
2. Drop-in: set `MemoryMax=` to evidence-based floor:
   - Floor band: **128M–256M** (start 128M; raise toward 256M only if OOM continues with proof).
   - Never remove MemoryMax (no unconstrained); never approach full board RAM.
3. **No torch**; no GPU/torch WM path enablement.
4. Restart wm/skill only after drop-in; soak and watch OOM / NRestarts.

### Path B2 — Temporary mask until ledger fixed

1. If CHG-D not yet applied and WM writes against broken ledger worsen corruption risk: mask (stop+mask) the thrashing wm/skill units **temporarily**.
2. Record mask reason = waiting on CHG-D append-only repair.
3. Unmask only after D verify_all_ledgers PASS (or explicit owner note).
4. After unmask, apply B1 MemoryMax floor before leaving units running long.

## Dependency note

- Prefer **D before long-running B1** if WM appends to prediction ledger: thrash against duplicate seq=9024 / break_seq=9025 can worsen ledger pain.
- Short B2 mask is OK in parallel with D.

## Explicitly forbidden during B

- unconstrained WM / deleting MemoryMax; torch WM; open 9101; MQTT/PWM/legs; arm reflex; planner; Doctor auto-patch; private keys; C NATS changes; E compaction; in-place hash rewrite.

## Verification

- OOM kills stop or drop sharply; NRestarts plateau.
- MemoryCurrent stays under new MemoryMax with headroom.
- No torch processes; MemoryMax still set (not infinity).
- Receipt with before/after `MemoryMax` and NRestarts.

## Rollback

1. Restore previous MemoryMax drop-in (e.g. 48M) OR remove raise drop-in.
2. If masked: unmask only with owner/plan state; or keep masked if rollback target is safe silent.
3. Restart units; document return to pre-CHG memory settings.
4. If instability: remask and STOP — do not chase with unconstrained limits.

## Success criteria

- WM/skill stable under capped MemoryMax ≥128M (or intentional temporary mask with D in flight); no forbidden surfaces.
