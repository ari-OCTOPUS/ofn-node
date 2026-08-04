# DR-001 — arm_gate wiring decision needed

**Status:** ✅ **Option 1 applied** (2026-08-04, this session, owner said "wire arm_gate
into self_patch.py per DR-001" in chat). `code_autonomy` is wired. `self_improve_auto` /
`replicate` remain unwired — separate follow-up, not requested yet, see
`31-ARM-GATE-WIRING-VERIFY.md` §"What's still open".
**Raised:** 2026-08-04, verification run.
**Related:** blindspot #30, `12-ARM-GATE-CURRENT-TRUTH.md`, `14-ARM-GATE-PATCH-REPORT.md`,
`31-ARM-GATE-WIRING-VERIFY.md`.

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
