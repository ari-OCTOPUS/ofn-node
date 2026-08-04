# 28 — Owner decisions still needed

1. **arm_gate wiring — DONE for all wireable capabilities.** `code_autonomy` (self_patch.py,
   gate #8, 39/39 tests) and `self_improve_auto` (two real write sites — `auto_approve.py`
   `run()`, live/mandatory, and `vault_updater_apply.py` `apply()`, defense-in-depth on a
   currently orphaned path — 22 new tests, 140/140 total in the P0 harness) are both wired,
   owner-instructed in chat, same session. See `31-ARM-GATE-WIRING-VERIFY.md` and
   `32-SELF-IMPROVE-AND-REPLICATE-WIRING.md`. **`replicate` deliberately left unwired** —
   `budget/replication.py` only ever writes a proposal note; there is no real spawn/execute
   function anywhere in the codebase yet to protect. Wiring it today would be theater, not
   hardening. Owner decision needed only if/when a real spawn function gets written — that
   is where the guard belongs.
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
