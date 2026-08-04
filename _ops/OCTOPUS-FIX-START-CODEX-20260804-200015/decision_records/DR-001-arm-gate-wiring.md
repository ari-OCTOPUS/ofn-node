# DR-001 — arm_gate wiring decision needed

**Status:** ✅ **`code_autonomy` wired** (owner instruction, same day) · ✅ **`self_improve_auto`
wired at both real write sites** (owner instruction, same day: "wire self_improve_auto and
replicate too") · ⛔ **`replicate` NOT wired — no real execution path exists to gate** (see
`32-SELF-IMPROVE-AND-REPLICATE-WIRING.md`).
**Raised:** 2026-08-04, verification run.
**Related:** blindspot #30, `12-ARM-GATE-CURRENT-TRUTH.md`, `14-ARM-GATE-PATCH-REPORT.md`,
`31-ARM-GATE-WIRING-VERIFY.md`, `32-SELF-IMPROVE-AND-REPLICATE-WIRING.md`.

## The decision

Should `arm_gate.guard('code_autonomy')` (and, as follow-up, `self_improve_auto` /
`replicate`) be wired into their real execution paths, given `OCTOPUS_ARM_SENSITIVE_
DEFAULT=1` is already armed in `OCTOPUS-flags.cmd` but currently has no effect?

## Options

1. **Wire it** (recommended by this run) — one new `arm_gate.guard()` check added as gate
   #8 in `self_patch.py`'s `_offer_patch_to_owner`, strictly after the existing 7 gates.
   Makes the owner's already-armed flag actually do something. Requires a fresh two-key
   arm-token before a self-patch can reach the owner's approval card at all.
2. **Leave it as-is** — module stays a tested-but-unconsumed library. No behavior change,
   no new friction, but the owner's `OCTOPUS_ARM_SENSITIVE_DEFAULT=1` decision stays inert
   and blindspot #30 stays open in practice even though the module exists.
3. **Turn the flag back off** until wiring is ready, to avoid the flags file implying a
   protection that isn't active. Not recommended — the flag is harmless either way (it's a
   no-op today), and turning it off doesn't reduce any risk, it just removes a forward
   signal of intent.

## This run's recommendation

Option 1, as a separate, small, independently-reviewable commit — not bundled into this
report/harness commit, and not applied automatically by any future agent without an
explicit owner go-ahead, per the master instruction's D5/D6 boundary.

## Update — self_improve_auto and replicate (same day, third instruction)

Owner: "wire self_improve_auto and replicate too." A parallel research workflow (3
investigate + 2 adversarial-verify agents, see `32-SELF-IMPROVE-AND-REPLICATE-WIRING.md`
for the full record) found:

- **self_improve_auto has TWO independent real write sites**, not one: `cortex/
  auto_approve.py`'s `run()` (live, reached every cycle by the cortex.py daemon —
  mandatory) and `vault_updater_apply.py`'s `apply()` (currently orphaned/uncalled in
  production, but shares the exact same capability name in `arm_gate.DANGEROUS` —
  wired anyway as cheap, harmless defense-in-depth for whenever it does get wired up).
  Both are now wired, both tested (4 new tests each, all pre-existing tests still pass).
- **replicate has NO real execution path yet** — `budget/replication.py` only ever writes
  a `SPAWN_PROPOSAL` ledger note for a human to read; there is no spawn/fork/execute
  function anywhere in the codebase. Wiring `arm_gate.guard('replicate')` today would gate
  a log-write with nothing dangerous downstream — not a real hardening, just theater. **Not
  wired.** When a real spawn function is eventually written, that is where the guard
  belongs, not before.
