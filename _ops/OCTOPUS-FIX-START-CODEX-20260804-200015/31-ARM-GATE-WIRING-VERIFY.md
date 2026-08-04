# 31 — arm_gate wiring verification (DR-001 applied)

Owner instruction (chat, 2026-08-04): "wire arm_gate into self_patch.py per DR-001." This
is Option 1 from `DR-001`, implemented exactly as scoped in `14-ARM-GATE-PATCH-REPORT.md` —
no more, no less.

## What changed

`_ops/self_patch.py`:
- `import arm_gate` added next to the existing `import opslib`.
- `_offer_patch_to_owner(res)` gained gate #8: immediately after the existing
  `shadow_green`/`content` check and **before** `_authorization_shadow(res)` is called:
  ```python
  _arm_ok, _arm_why = arm_gate.guard("code_autonomy")
  if not _arm_ok:
      return {"ok": False, "reason": f"arm-gate-denied:{_arm_why}"}
  ```
- Docstring updated from "هفت گیت" to "هشت گیت" with the new gate documented — code and
  its own comment no longer drift apart.

`_ops/tests/test_self_patch.py`: 4 new tests, `_ops/tests/run_p0_verify.py`: added
`test_self_patch.py` to the harness's SUITE list.

## Why this insertion point and not somewhere else

`_offer_patch_to_owner` is the exact function identified in `14-ARM-GATE-PATCH-REPORT.md`
as the real `code_autonomy` write-adjacent path (it turns a shadow-green patch into an
owner-facing button-card via `code_autonomy.propose_to_owner`). Placing the check
**after** all seven pre-existing gates (flag, shadow_green, content non-empty — the other
four gates from the docstring: heart mood/refractory/dedup/48h-staleness live inside
`drive()`'s caller chain upstream of this function) and **before** `_authorization_shadow`
guarantees arm_gate can only narrow what already got this far — it can never grant
something the existing chain would have refused. `t_arm_gate_only_narrows_never_widens`
proves this directly: a `shadow_green=False` patch stays `not-offerable` even with a fully
valid arm-token present.

## Test results — 4 new + 35 pre-existing = 39/39 pass, 0 regressions

Run directly this session (`PYTHONIOENCODING=utf-8 PYTHONUTF8=1`):

| Test | Proves |
|---|---|
| `t_arm_gate_default_off_is_byte_identical` | Both arm_gate knobs off (today's live default) → `guard()` returns pass-through, `_offer_patch_to_owner` reaches `ok:True` exactly as before this change existed |
| `t_arm_gate_sensitive_default_denies_without_a_fresh_token` | `OCTOPUS_ARM_SENSITIVE_DEFAULT=1` + no arm-token → denied at gate #8, **and** confirms no `pending-patches/*.json` was written (the deny happens before any side effect, not just before the owner card) |
| `t_arm_gate_sensitive_default_allows_with_a_fresh_two_key_token` | Same flag + ACTIVATION flag + both fresh arm-tokens present → passes gate #8, flow continues to `ok:True` |
| `t_arm_gate_only_narrows_never_widens` | A `shadow_green:False` patch, even with a fully valid arm-token, still returns `{"ok": False, "reason": "not-offerable"}` — arm_gate cannot rescue a patch the earlier gates rejected |

All 35 pre-existing `test_self_patch.py` tests still pass unmodified — this is the
regression proof that the byte-identical-when-default-off guarantee holds for the whole
existing self-patch loop (queue, daily cap, allowlist, transient-failure handling, etc.),
not just the one function that changed.

Full harness: `python _ops/tests/run_p0_verify.py` → **ALL GREEN**, 118 total checks
(79 from the original P0 verification + 39 from `test_self_patch.py`).

## What this means for the live process (not executed — informational only)

Read-only check of `F:\backup` main root (main root's runtime state, not touched):
- `_ops/ACTIVATION-CODE-AUTONOMY.flag` **already exists** on disk (created 2026-07-23).
- `_ops/state/arm/` **does not exist** — no arm-token has ever been minted.

So: once this commit reaches the live tree, `OCTOPUS_ARM_SENSITIVE_DEFAULT=1` becomes
effective, and the organism is restarted (none of which happened in this session — see
`10-SAFE-RESTART-PLAN.md`, still not recommended to rush), the practical effect is
immediate and real: `self_patch`'s owner-approval cards for `code_autonomy` **stop being
offered** until the owner mints a fresh two-key arm-token. That is exactly blindspot #30
closing for real, not just on paper. This is a genuine behavior change for the live
self-patch loop the owner should be aware of before restarting — it is not silent, it will
show up as `self_patch` defects going from "open" → "failed" with
`result_reason: arm-gate-denied:...` instead of producing owner cards, until tokens exist.

## What's still open

- `self_improve_auto` and `replicate`'s real call sites (`_ops/cortex/auto_approve.py` /
  `_ops/cortex/improve.py` / `_ops/budget/replication.py`) were **not** wired this session —
  the owner's instruction named `self_patch.py` specifically, matching DR-001's scoped
  Option 1. Wiring those two is a separate, not-yet-requested follow-up.
- No arm-token minting flow was built or changed — the owner still needs an existing (or
  future) mechanism to actually create `code_autonomy.arm.json` / `.arm2.json` when they
  want to arm a self-patch. This session did not audit whether one already exists.

## Rollback

`git revert <this-commit>` — pure change to one function + its docstring + new tests +
one harness entry; no other file touched, no data migration, nothing else depends on it.
