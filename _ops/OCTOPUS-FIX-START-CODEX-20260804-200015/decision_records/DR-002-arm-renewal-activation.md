# DR-002 — arm-token auto-renewal (`arm_renewal.py`) activation decision

**Status:** ✅ **Activated** (`OCTOPUS_WIRE_ARM_RENEWAL=1`, `OCTOPUS-flags.cmd`) — both
`code_autonomy` and `self_improve_auto`, after a second, more-informed owner confirmation.
**Raised:** 2026-08-05, continuation of DR-001 (`arm_gate` wiring).
**Related:** `arm_gate.py` (DANGEROUS registry, DR-001), `arm_renewal.py`,
`tests/test_arm_renewal.py`, `07 - Knowledge/شناخت-اختاپوس/11-USABILITY-AUDIT-AND-ARMING-2026-08-05.md`.

## The decision

DR-001 wired `arm_gate.guard()` into `code_autonomy`'s and `self_improve_auto`'s real
write paths, but left the two-key arm-token itself unminted — `state/arm/` did not exist,
so both capabilities were fail-closed-dead regardless of the `ACTIVATION-*.flag` files
present since 2026-07-22. `arm_renewal.py` closes that gap: on its own flag, it mints a
fresh 24h token every ~10 minutes for any capability whose `ACTIVATION-*.flag` exists and
whose `STOP-*` marker does not — never opening anything ACTIVATION itself has not already
allowed.

## Timeline (why this needed a second, sharper confirmation)

1. Owner, broad grant (2026-08-05 night): *"مجوزِ کامل داری کامل خودترمیمیی کنه همیشه با
   ضربانِ قلب سهمِ توکن بگیره... همشو بیا"* — build and wire it all.
2. A 3-lane build produced `arm_renewal.py`, tested (20/20) on a session worktree branch,
   but **not** merged to `master` — an adversarial review at the time found both
   `ACTIVATION-*.flag` files already present (since 2026-07-22) and `self_improve_auto`'s
   apply path genuinely zero-click, meaning the renewal tool would be equivalent to
   opening the lock outright, not a neutral maintenance action. Held for explicit re-
   confirmation with the mechanism spelled out. See `feedback-a-ready-lock-plus-a-preset-
   key-unlocks-itself.md` (agent memory).
3. Owner, same session, after that explanation: *"تموم جزییات رو دیدم و موافقم همه اجازه
   هارو بهش بدم."*
4. Before acting on (3), a dedicated research workflow independently re-derived the exact
   mechanics (not trusted from step 2's summary):
   - `code_autonomy`: gate opens → `propose_to_owner()` only posts a Telegram card;
     `apply_approved()` (the only function that writes) requires `_owner_approved(aid)`.
     Real, per-capability instant kill exists: `_ops/STOP-CODE-AUTONOMY`, polled ~5s.
   - `self_improve_auto`: gate opens → `apply_knob()` runs **synchronously in the same
     call**, zero owner-facing step. Scope: 3 whitelisted, bounded, $0, reversible timing
     knobs (`CORTEX_THINK_EVERY_N`, `CHRONO_NUDGE_EVERY_N_BEATS`, `HEART_SAMPLE_INTERVAL_S`).
     **No dedicated STOP marker exists for it anywhere in the codebase** — the module's
     own docstring reference to a `STOP-SELF-IMPROVE-AUTO` convention is aspirational, not
     implemented; `auto_approve.py`/`improve.py` never check for it. The real, confirmed
     instant kill is deleting `ACTIVATION-SELF-IMPROVE-AUTO.flag` itself.
   - The code was ported to `master` as new files (no merge-collision risk — `arm_gate.py`
     itself was NOT touched, avoiding the class of risk that would have silently deleted
     the 2026-08-04 `sensitive_enforced()` P0 tightening had it been raw-copied).
   - 20/20 unit tests + 3/3 mutation tests (STOP-marker bypass, ACTIVATION bypass,
     kill-marker-name derivation) all caught cleanly on `master`.
5. A full adversarial safety review (fresh agent, no prior context) of the merged code
   found the code itself mechanically sound, but raised two points step 3's consent had
   not actually been shown: (a) **both `ACTIVATION-*.flag` files carry the identical
   generic line "owner-resurrection ... all paid gates ON" from 2026-07-22** — a bulk
   reactivation, not a decision specific to these two capabilities; (b) `arm_renewal.py`'s
   own docstring claims heart-dependence ("با ضربانِ قلب") that `capability_active()` does
   not implement — it only checks file existence, never heart/stress state. This made it
   likely that the owner's original "با ضربانِ قلب سهمِ توکن بگیره" phrasing actually
   described `self_patch`'s Fugu-share quota (a separate, already-activated change, which
   genuinely is heartbeat-cadenced), not this module.
6. Owner was asked directly, with both (a) and (b) spelled out, and three concrete options
   (code_autonomy only / both / neither, code left inert either way). **Answer: "هر دو
   مسلح شوند، همان طرحِ اول"** — arm both, as originally planned, with the fuller picture
   now in hand.

## Options considered at step 6

1. **Arm `code_autonomy` only** — leaves the genuinely zero-click `self_improve_auto` path
   dormant (delete `ACTIVATION-SELF-IMPROVE-AUTO.flag`, keep `ACTIVATION-CODE-AUTONOMY.flag`);
   would have let the code_autonomy patch-card flow (dead since 08-04, including the
   shadow-green race-condition fix sitting since 08-01) resume without waking the
   auto-knob-tuning path.
2. **Arm both, as designed** — chosen. code_autonomy stays human-gated via Telegram tap
   regardless; self_improve_auto's blast radius is 3 bounded numeric knobs, $0, reversible.
3. **Arm neither, leave code built-but-inert** — most conservative; rejected by owner.

## Outcome

`OCTOPUS_WIRE_ARM_RENEWAL=1` set 2026-08-05; organism restarted to load it. Real, confirmed
kill switches going forward: `_ops/STOP-CODE-AUTONOMY` (instant, polled ~5s) for
code_autonomy; deleting `_ops/ACTIVATION-SELF-IMPROVE-AUTO.flag` (instant, checked at every
call site) for self_improve_auto — **not** a `STOP-SELF-IMPROVE-AUTO` file, which would only
stop future token *renewal*, not revoke an already-minted (up to 24h) token.
