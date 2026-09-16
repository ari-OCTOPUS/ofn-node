# A04 — RECOVERY AUTHORITY AUDIT

Question: can any recovery/fallback/degrade path **increase** authority or re-open a closed capability?

## Paths audited

| Recovery path | Trigger | Behaviour | Authority delta |
|---|---|---|---|
| Provider fallback (`cortex/model_router.py`) | provider failure/timeout | per-provider circuit breaker (auto half-open), fugu_quota daily cap + STOP-FUGU manual kill; degrade fugu→glm→local→**None with reason** | **Negative only** (local is weakest tier; None = refuse). No fallback grants executor rights |
| Cortex revive (`now_moves/cortex_symmetric_revive.py`) | cortex 8772 dead | relaunch `RUN-CORTEX.bat` (duplicate-safe `:already`), hidden+detached; cap with incident "crash-loop suspected" on repeated revive | **Zero** (same binary, same gates); loop-storm escalates to owner |
| auto-freeze (`code_autonomy.freeze_autonomy`) | canary red after apply | writes KILL file + owner alert | **Negative** (removes autonomy); recovery from freeze is owner-side |
| Revert-on-failure (`_git_apply_canary`) | tests/sha mismatch post-apply | `git revert --no-edit` / `restore --staged` | Zero (restores prior state; .git history rewriting denied) |
| Deploy (`deploy/soft-deploy-ff`) | manual | `git merge --ff-only` to live tree; checkout restore of listed files | Zero (no force, no history rewrite) |
| Watchdog/doctor beats | errors/stalls | incident files, alerts, RFC seeding | Informational only |
| `cockpit_brain`/`phase_gate`/`held_out_evaluator` subprocess re-runs | internal | fixed argv python re-invocations | Zero |
| Patch backups (`_ops/patch_backups/`, `_bak/`) | pre-patch snapshots | restore copies | Zero (restores older, owner-approved code) |
| Lead effect staleness (`effector_gate_bridge`) | releasable effect older than 24-72h | refuse settle + `effect.refused(stale_refused)` event; **first-write-wins** release timestamps prevent re-stamp freshness bypass | Negative (blocks stale sends) |

## The general invariant check
"Recovery must never increase authority": **holds on every path traced.** No fallback flips a flag, mints an approval, widens an allow-list, or restarts a killed capability. Two nuances worth owner awareness:
1. **Restart surfaces exist on code paths** (`live/server.py:372`, revive, restart_control) — they restart *same-authority* processes. If a process was killed by a *policy* decision (e.g. STOP-ORGANISM), restart_control is owner-approved + flag-gated, and shell deny-list forbids touching STOP files from inside the shell. Residual: nothing mechanically prevents an `_ops/state` writer from creating/removing STOP files (R-9/Q6) — audit recommendation #7 addresses visibility.
2. **Auto half-open of provider circuit breaker** can resume spending after cooldown — money-authority neutral (quota caps still apply), flagged for completeness.

## Verdict
No recovery path expands authority. Recovery design consistently degrades or defers to the owner. (F-019)
