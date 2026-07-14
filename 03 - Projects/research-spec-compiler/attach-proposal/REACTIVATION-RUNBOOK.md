# RUNBOOK — reactivating the body's research daemon for fresh data

**Who acts:** the OWNER. The kernel does NOT start the daemon (the body's own
Risk Ladder marks `4d_system` = *owner-approved run only*: it is a
self-modifying, LLM-budget-spending autonomous loop with no OS sandbox). The
kernel provides only READ-ONLY tooling around it. Everything below is reversible.

## Why reactivate
H-HYBRID-01 (ADR-008, OPTIMIZE) was scoped to a SINGLE frozen snapshot — the 4d
daemon has been stopped since 2026-07-11, so the 5 "temporal cuts" are
correlated, not independent replications. To upgrade the shadow cortex's verdict
honestly (OPTIMIZE → possibly INTEGRATE), the body needs to run again and
produce FRESH events. That is the only thing reactivation buys.

## Steps

### 1. Preflight (kernel, READ-ONLY — safe to run any time)
```
cd C:\Users\Armin\Desktop\121212121212121212\research-spec-compiler
python tools/preflight_reactivation.py
```
Expect `VERDICT: GO` (checks: no STOP/FREEZE flag · daemon stopped · budget not
exhausted · identity anchor 0.135073 healthy · DB reachable). If NO-GO, resolve
the flagged item first. This touches nothing writable.

### 2. Reactivate (OWNER, on the body — this is the ORANGE act)
```
cd /d F:\backup\4d_system
start.bat            REM  the body's own launcher (or: python run.py)
```
Watch the body's own RUNBOOK.md / AUTONOMOUS_RUN.md for its budget cap
(1000 cloud calls/day) and its telegram/owner gates. The daemon appends to
`dashboard_events` as it runs the 9-phase cycle.

### 3. Let the shadow cortex re-evaluate (kernel, READ-ONLY)
Once fresh rows exist, the kernel notices and re-runs the frozen hybrid
self-model on the new data — no body write, propose-only:
```
python -c "from experiments.organism_bridge import live_refresh_and_reevaluate as r; import json; print(json.dumps(r(), ensure_ascii=False, indent=1))"
```
- If `action: no_op` → no fresh events yet (daemon still warming up).
- If `action: reevaluated` → prints the fresh `hybrid_selfpred` +
  `bottleneck_advantage` on the NEW data. Compare to ADR-008's 0.946 / 0.036;
  a genuinely independent replication is what lets a follow-up ADR raise the
  verdict.

### 4. (Optional) stop the daemon again
The body's own STOP mechanism (a STOP flag / its dashboard control) — the OWNER,
per the body's controls. The kernel never stops it.

## Rollback / safety
- The kernel writes NOTHING to the body in any of these steps (mode=ro reads
  only). The one body write already made — `03 - Projects/research-spec-compiler/`
  — is deletable to fully un-register the organ.
- The daemon's own kill-switch/STOP is out-of-band and owner-controlled.
- Effect-upgrades (propose → shadow-run, `apply_merge`) remain SEPARATE ORANGE
  gates (Q5 in OpenQuestions.md); reactivation does not enable them.
