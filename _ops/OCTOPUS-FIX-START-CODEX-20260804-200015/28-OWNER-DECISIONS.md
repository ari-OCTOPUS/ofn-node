# 28 — Owner decisions still needed

1. **arm_gate wiring — DONE for `code_autonomy`** (owner instructed this in chat later the
   same day: "wire arm_gate into self_patch.py per DR-001"). `_offer_patch_to_owner` now
   calls `arm_gate.guard('code_autonomy')` as gate #8; 39/39 tests pass including 4 new
   ones proving no regression. See `31-ARM-GATE-WIRING-VERIFY.md`. **Still open:**
   `self_improve_auto` and `replicate` would need
   their own call-site audits (not done this session — `_ops/cortex/auto_approve.py` /
   `_ops/cortex/improve.py` / `_ops/budget/replication.py` are where those capabilities
   actually live, per grep, but exact insertion points were not traced).
2. **Full `OCTOPUS_REQUIRE_ARM=1` enforcement** — separate, broader decision from #1; not
   requested by the owner's 7-flag list and not recommended by this run without more
   analysis of every one of the 5 `DANGEROUS` capabilities' current call sites.
3. **Organism restart timing** — the 7 newly-armed flags are on disk and startup correctly
   sources them (confirmed), but the *running* process won't see them until restarted. This
   run recommends waiting until decision #1 is made first, so a restart doesn't create a
   false impression that arm-gating is now live (see `10-SAFE-RESTART-PLAN.md`).
4. **doctor-pulse merge** — mentioned in the source scan docs as an 8-day-stuck mission
   (`awaiting-merge` since 2026-07-29). Not touched this session (out of scope: it's a
   mission-approval action in the live/main tree, not a P0 code fix, and this run stayed
   inside the isolated worktree). Still open per the scan docs; re-check its current state
   before acting, since the scan is now hours old and the organism has kept running.
5. **OWNER-PROFILE PII in git history** — still open (untracked now, but history retains
   it). Only urgent if/when the repo becomes public; not touched this session (destructive
   history rewrite is explicitly out of scope for a D0-D4 run).
6. **whisper-medium (1.4GB) cleanup** — still open, low urgency, not touched this session.

None of the above were acted on. All are documented here for the owner to decide, per the
master instruction's Phase G requirement that anything needing a decision gets recorded, not
silently done or silently dropped.
