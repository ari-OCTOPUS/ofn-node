# OpenQuestions — decisions only the owner can make (research-spec-compiler organ)

These are the ORANGE/gated decisions the OPTIMIZE verdict cannot make for you.
The kernel proposes; you decide. Nothing below is executed autonomously.

## Q1 — Activate the shadow attachment? (ORANGE) — ✅ ANSWERED 2026-07-14: A
Owner authorized "A: yes, shadow-only" ("بیا اینو کامل کنیم"). DONE: one
additive `PROJECT.md` written into `F:\backup\03 - Projects\research-spec-compiler\`
registering the organ in URCP (`autonomy_level: read-only`, `risk_level: low`,
off-flag true). Verified: only that new folder was added, zero existing body
files modified, organ now visible to `registry_scan`. Fully reversible (delete
the folder → germline intact). The organ is registered + read-only + propose-only;
it takes NO outward action. Later effect-upgrades remain separate ORANGE gates
(see Q2/Q5).

## Q2 — Fresh replication data? — TOOLING READY 2026-07-14 (owner runs the trigger)
The verdict is scoped to a single frozen snapshot (body's research daemon
stopped 2026-07-11). To upgrade OPTIMIZE→INTEGRATE honestly, the body needs to
run again and produce new events. **The coding is complete and read-only:**
- `tools/preflight_reactivation.py` — READ-ONLY GO/NO-GO safety gate (currently
  reports GO: no flags, daemon stopped, budget 998/1000, anchor 0.135073 healthy).
- `experiments/organism_bridge.py::live_refresh_and_reevaluate()` — notices fresh
  events and re-runs the hybrid self-model on them, READ-ONLY, propose-only.
- `attach-proposal/REACTIVATION-RUNBOOK.md` — the exact owner steps + rollback.
**I do NOT start the daemon** — the body's Risk Ladder marks 4d_system
"owner-approved run only" (self-modifying, spends LLM budget, no OS sandbox). You
run `F:\backup\4d_system\start.bat`; the kernel tooling handles the rest read-only.

## Q3 — Which experiment next? (queue order, per the ADR-007 firewall)
Economy may reorder this, never the verdicts. Candidates:
- **H-OWN-01** (social-mirror self-model) — highest revenue potential in your table.
- **H-OWN-07** (causal self-model) — BCI-adjacent.
- A v3 hybrid with a compositional (non-cyclic) target so the fancy mechanisms
  can actually earn their keep (the current stream is too trivially predictable).

## Q4 — Financial parameters (still [EST] plans, need your numbers)
Monthly compute cap, pricing for C0 products, the "30% brain-data fund" split.
I execute none of these without concrete owner-set numbers/accounts.

## Q5 — Production authority
Should `apply_merge` (L5 production change) ever be wired for this organ? Default
and recommendation: **no** — stays unwired; every production effect keeps needing
your Telegram verdict.
