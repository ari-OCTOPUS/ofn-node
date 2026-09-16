# 32 — self_improve_auto + replicate wiring (DR-001 follow-up)

Owner instruction (chat, 2026-08-04, same session as the `code_autonomy` wiring): "wire
self_improve_auto and replicate too."

## Method

Given the stakes (self-modification/replication gating) and the genuine uncertainty about
where these capabilities actually execute, this was investigated with a parallel research
workflow before any code was touched: 3 independent investigate agents (one per candidate
subsystem) followed by adversarial verify agents that tried to *refute* each proposed
insertion point (bypass check: is there another path to the same effect that skips the
proposed gate? ordering check: does the gate sit downstream of every existing safety check
without skipping any unconditional logging?). Full agent transcripts are in this session's
workflow journal; findings are summarized below and were independently re-confirmed by
reading the actual source before editing anything.

## self_improve_auto — wired at BOTH of its two real write sites

The investigation found something the initial grep-based scan missed: **there are two
structurally independent places where "self_improve_auto" becomes a real write**, not one.

### Site 1 (mandatory — this is the live gap): `_ops/cortex/auto_approve.py`, `run()`

Confirmed live call chain: `cortex/cortex.py`'s always-on daemon (127.0.0.1:8772) →
`run_cycle()` → `self_improve()` → `improve.run()` → `improve.maybe_auto_apply()` →
`auto_approve.run()` → (inside the `if d["action"] == "auto" and has_permission and not
applied:` block) → `apply_knob()`, which writes `state/cortex/auto-knobs.json`, mutates
`os.environ[knob]` immediately, and writes an `AUTO_APPROVE_APPLY` ledger entry.

`arm_gate.guard("self_improve_auto")` was added as an early-continue **inside that `if`
block, before `apply_knob()` is called**:
```python
if d["action"] == "auto" and has_permission and not applied:
    _arm_ok, _arm_why = arm_gate.guard("self_improve_auto")
    if not _arm_ok:
        reason = f"arm-gate-denied:{_arm_why}"
        escalated.append({"title": p.get("title"), "risk": d["risk"], "why": reason})
        _log({"decision": "escalated", ...})
        continue
    r = apply_knob(d["knob"], d["bounds"])
    ...
```
A deny is treated exactly like the codebase's existing "couldn't apply right now" cases:
appended to `escalated` and logged — never silently dropped.

**Deliberately NOT gated:** `apply_knob()` itself, because it has a second caller —
`doctor.py:695` inside `DoctorLoop.apply_merge()` — which only fires after a real owner
Telegram button tap (an independently-authenticated human approval, gated by its own
separate flag `OCTOPUS_WIRE_MERGE_APPLIES_KNOB`, verified default-off in production).
Gating `apply_knob()` itself would have imposed an autonomous-capability arm-token
requirement onto an already-owner-approved manual action — scope creep, not a fix. The
adversarial verify agent independently confirmed both the bypass check (no other caller of
`apply_knob()` reaches it without going through `auto_approve.run()` or the owner-approved
doctor path) and the ordering check (nothing unconditional is skipped by an early return
here) by reading source directly, not by trusting the investigator's summary.

**11 existing gates already run before this point** (ACTIVATION flag, observability
freshness, 24h refractory, risk classification, autonomy_matrix importance, goal alignment,
autonomy_grant, knob whitelist, self-test composite, permission re-check, one-apply-per-run
throttle) — full list in the workflow journal. `arm_gate` is added as gate #12, strictly
narrowing.

### Site 2 (defense-in-depth — currently orphaned): `_ops/vault_updater_apply.py`, `apply()`

This module never imports `cortex/improve.py` — it is a genuinely separate write path
(own `apply()` function, own idempotent disk write, own `ledger_note("VAULT_AUTO_WRITE",
...)` call) that duplicates the same `ACTIVATION-SELF-IMPROVE-AUTO.flag` check rather than
calling into site 1. `arm_gate.py`'s own `DANGEROUS` table already lists `self_improve_auto`
as the capability governing this flag, so this module has always been in scope for
arm_gate — nothing called it.

```python
if content in prev:
    return {"ok": True, "applied": False, "reason": "idempotent-noop", "path": rel}
_arm_ok, _arm_why = arm_gate.guard("self_improve_auto")
if not _arm_ok:
    return _refuse(f"arm-gate-denied:{_arm_why}")
block = (prev + ...
```
Placed **after** the idempotent-no-op check (a no-op that changes nothing on disk doesn't
need an arm-token) and **before** the real write — the 8th of this module's own numbered
gates.

**Important honesty note, found by the adversarial verify agent, not the initial
investigator:** `vault_updater_apply.py` currently has **no production caller at all** —
the vault's own `_agent_reports/ORPHAN-TRIAGE-2026-07-30.md` flags it as needing a separate
human-gated wiring vote before anything calls it. So this specific wiring, on its own,
protects nothing live *today*. It was implemented anyway because (a) it costs nothing —
strictly-tightening, default-off, zero behavior change to a path already unreachable, (b) it
closes the gap for the moment this module *does* get wired into production, and (c) the
real, live gap (Site 1) is separately and fully closed. This is explicitly **not** claimed
as closing a live risk by itself — see `29-RISKS-LEFT.md`.

### Tests

- `tests/test_auto_approve.py`: 4 new tests (`t_h`..`t_k`) — default-off byte-identical
  (regression of the existing `t_e` full-green-apply test), deny-without-token (and confirms
  `auto-knobs.json` is NOT written when denied), allow-with-fresh-two-key-token, and
  "arm_gate only narrows" (a high-risk proposal stays escalated even with a valid token).
  **11/11 pass**, all 7 pre-existing tests unmodified and still green.
- `tests/test_vault_updater_apply.py`: 4 new tests (`t_h`..`t_k`), same shape, plus one
  specific to this file's idempotent-check ordering: `t_k_arm_gate_does_not_block_the_
  idempotent_noop` proves a genuine no-op second write is never blocked by a missing
  arm-token (because the gate sits after the idempotent check, not before it).
  **11/11 pass**, all 7 pre-existing tests unmodified and still green.
- Regression cross-check: `tests/test_self_improve.py` (10/10) and `tests/test_improve_
  refractory.py` (5/5) — both depend on `auto_approve.py` transitively — still fully green.
- Full P0 harness (`_ops/tests/run_p0_verify.py`, now 9 files): **ALL GREEN**, 140 total
  checks (79 original + 39 self_patch + 11 auto_approve + 11 vault_updater_apply).

## replicate — deliberately NOT wired

`_ops/budget/replication.py` (135 lines, read in full) contains exactly four functions:
`_cfg()`, `_ledger_spawn_counts()`, `sigma_state()`, `evaluate()`. None of them spawn a
process, fork/copy the codebase, deploy an instance, or call `subprocess`/`os.exec`/docker/
git-clone. `evaluate()`'s entire "action," gated by six independent conditions (live-gate
flag+date, fitness authoritative, sigma not in alert zone, population cap, kill-switch,
exclusion list, per-cell acceptance-rate/judged-count thresholds), is appending a
`SPAWN_PROPOSAL` note to the genome ledger for a human to read later. Nothing in the
codebase consumes that note to actually create anything. The module's own docstring says so
explicitly: "spawn = side-effect ⇒ همیشه human-gated: این ماژول فقط PROPOSAL می‌سازد ...
هرگز چیزی اجرا/spawn نمی‌کند."

`budget/opslib.py`'s only reference is a path constant (`ACT_REPLICATION` flag path) with no
execution logic of its own. `action_bridge/classifier.py`'s only reference is a static
risk-tier lookup entry (`"replicate": "A6"`, which maps to a `REJECT` verdict elsewhere in
that same file) — pure classification metadata, not an enforcement point.

**Wiring `arm_gate.guard("replicate")` today would gate a ledger-note write with nothing
dangerous downstream of it — a hollow gesture, not real hardening.** Consistent with the
master instruction's "no capability created, nothing fabricated" ethos, this was left
unwired. **When a real spawn/execute function is eventually written** (none exists today),
that function is where `arm_gate.guard("replicate")` (with its two-key requirement) belongs
— most naturally replacing or wrapping the point that would call it, analogous to how this
session gated `apply_knob()`'s real callers rather than `decide()`'s classification step.

## Secret / outbound scan

Independent grep of the full diff (`cortex/auto_approve.py`, `vault_updater_apply.py`, both
test files, `run_p0_verify.py`): zero secret-pattern matches, zero
`requests./socket./smtplib/urllib.request/http.client` matches. Same discipline as every
prior phase of this run.

## Rollback

`git revert <this-commit>` — two production files changed (`auto_approve.py`,
`vault_updater_apply.py`), each with one new import + one new guarded block, both strictly
additive and behind arm_gate's own default-off knobs; two test files extended, one harness
entry added. Nothing else touched.
