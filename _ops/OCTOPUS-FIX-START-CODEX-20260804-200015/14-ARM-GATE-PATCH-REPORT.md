# 14 — arm_gate patch report

> **UPDATE 2026-08-04 (same day, later in the session):** the owner explicitly instructed
> "wire arm_gate into self_patch.py per DR-001" in chat. The `code_autonomy` half of this
> proposal below was implemented exactly as scoped, tested (4 new + 35 regression, 39/39),
> and committed. See `31-ARM-GATE-WIRING-VERIFY.md` for the verification record and
> `DR-001` for the updated decision-record status. The `self_improve_auto`/`replicate`
> half described below is **still** just a proposal — not requested, not applied.

## Why this stayed a proposal until the owner's explicit go-ahead

Wiring `arm_gate.guard()` into the actual `code_autonomy` write path means touching code
that governs self-modification of the live tree — a D5/D6-adjacent capability. The master
instruction is explicit: "اگر patch زنده ریسک دارد: فقط implementation پشت flag / default-
off / owner decision بساز / commit نکن." Even though the change described below is designed
to be strictly-tightening and default-safe (arm_gate's own two knobs are both off today), a
change to the self-patch apply path is exactly the category this run is required to leave as
a reviewable proposal, not a live edit.

## Where it would go

`_ops/self_patch.py`, function `_offer_patch_to_owner(res)` — this is the real
`code_autonomy`-adjacent write path (it is what turns a shadow-green self-patch into an
owner-facing button-card, per the flags.cmd comment: "این تنها مسیری است که به نوشتنِ کد
روی درختِ زنده ختم می‌شود"). It already has a 7-gate chain:
`active() + ACTIVATION | heart mood | _owner_approved | allowed_target(target_guard) |
shadow_green | non-empty content | refractory + dedup + 48h staleness`.

Proposed insertion point: immediately after the existing
`if not (res or {}).get("shadow_green") or not (res or {}).get("content"): return {"ok":
False, "reason": "not-offerable"}` check and before `_authorization_shadow(res)` is called —
i.e. as gate #8, strictly after all seven existing gates have already passed, never before
them (so it can only narrow, never widen, what currently gets through).

## Proposed diff shape (illustrative — not written to any file)

```python
import arm_gate  # new import, top of self_patch.py

def _offer_patch_to_owner(res: dict) -> dict:
    ...
    if not (res or {}).get("shadow_green") or not (res or {}).get("content"):
        return {"ok": False, "reason": "not-offerable"}
    # NEW — gate #8, defense-in-depth on top of the existing 7:
    ok, why = arm_gate.guard("code_autonomy")
    if not ok:
        return {"ok": False, "reason": f"arm-gate-denied:{why}"}
    _authorization_shadow(res)
    ...
```

## Why this is safe to propose (but still not to apply unreviewed)

- `arm_gate.guard()` today returns `(True, "arm-gate-not-enforced")` for `code_autonomy`
  whenever both `OCTOPUS_REQUIRE_ARM` and `OCTOPUS_ARM_SENSITIVE_DEFAULT` are unset — so
  wiring it in with *both* flags at their current values (`REQUIRE_ARM` unset,
  `ARM_SENSITIVE_DEFAULT=1`) would immediately start requiring a real two-key arm-token for
  `code_autonomy`, since the owner already flipped `ARM_SENSITIVE_DEFAULT=1` in
  `OCTOPUS-flags.cmd`. **This is the behavior change the owner actually asked for when they
  armed that flag** — right now arming it does nothing; wiring it in is what makes the
  owner's own decision take effect.
- It cannot loosen anything: `arm_gate.guard()` only ever returns `True` (pass) or denies;
  it never grants a capability the existing 7 gates would have refused.
- Same wiring pattern would apply to wherever `self_improve_auto` and `replicate` actually
  execute (`_ops/cortex/auto_approve.py` / `_ops/cortex/improve.py` for the former,
  `_ops/budget/replication.py` for the latter) — this run did not trace those two to a
  specific insertion line; that is follow-up scope, not done here.

## What this run recommends

1. Owner reviews this proposal (and ideally the two follow-up call sites for
   `self_improve_auto`/`replicate`).
2. A future session implements it as its own isolated, tested, reviewable commit — with its
   own regression test proving the existing 7-gate behavior is unchanged when arm_gate is
   not enforced, and a new test proving `code_autonomy` is denied without a fresh arm-token
   once `OCTOPUS_ARM_SENSITIVE_DEFAULT=1` is both set *and* wired.
3. Until then, `OCTOPUS_ARM_SENSITIVE_DEFAULT=1` staying on in `OCTOPUS-flags.cmd` is
   harmless (it is a no-op today) — no need to turn it back off while waiting for the
   wiring decision.
