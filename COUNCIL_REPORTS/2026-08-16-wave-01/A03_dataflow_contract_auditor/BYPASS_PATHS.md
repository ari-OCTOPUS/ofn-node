# BYPASS_PATHS — A03 Dataflow & Contract Audit (2026-08-16)

Paths that bypass one or more of: intent creation, Policy Gate, receipt generation,
capability restriction, budget reservation, postcondition verification.

Classifications used: BENIGN_INTERNAL · LEGACY · TEST_ONLY · UNCONTROLLED_SIDE_EFFECT · UNKNOWN.

---

## BP-01 — `/sh` raw shell handler in telegram_center
- **Path:** owner Telegram message `/sh <cmd>` → `center.py` handler (commands dict ~line 3213) → subprocess shell execution.
- **Bypasses:** action_bridge classification (A4 `run_external_command` equivalent), receipts, policy ladder, postcondition verification.
- **Mitigation present:** behind `_is_owner` fail-closed chat_id allowlist (center.py:2657-2674); non-owner silently dropped.
- **Classification:** BENIGN_INTERNAL (owner-only console) — but it is the widest single authority surface in the organism: one compromised owner Telegram session = arbitrary shell. No double-confirm, no audit trail equivalent to action receipts (only disposition log).
- **Recommended action:** route `/sh` through a double-confirm card + append to action-audit.jsonl with command hash.

## BP-02 — 4d_system control_plane policy ladder is not in any execution path
- **Path:** `control_plane/policy.py::evaluate` defines the Level 0–5 ladder, but grep shows callers are only inside `control_plane/` itself (killswitch.py, shadow.py, supervisor.py, approvals.py) plus tests. No brain, executor, or _ops module calls it.
- **Bypasses:** nothing — there is nothing to bypass; the ladder observes a shadow event stream (shadow.py) and its own approvals/killswitch flows, all flag-gated default-off (`control_plane/flags.py`: all live flags default-off).
- **Classification:** BENIGN_INTERNAL (by design — "v1 enforce نمی‌کند" per policy.py:14-16; enforcement live only for flag-gated self_code approvals).
- **Note:** two parallel policy vocabularies coexist (4d `ACTION_POLICY` levels vs `_ops/action_bridge` A0–A6). Schema drift risk when reading docs that mention "Policy Gate" without saying which one.

## BP-03 — 4d dashboard approval resolves "latest pending" without action binding
- **Path:** `events.resolve_latest_approval(new_state)` (4d_system/brain/events.py:280-300) flips the newest `approval_state='pending'` row to approved/rejected. Nothing binds the decision to a specific action/payload.
- **Bypasses:** approval-to-action binding (contrast: `_ops` approval_store binds `id`+`action_sha256`+HMAC token; action_bridge owner_gate binds `action_id`+`payload_hash`+nonce).
- **Mitigation:** the live approval lane is `_ops`; this 4d path serves the deprecated 4d bot and control_plane approvals (`resolve_bus_approval`), both flag-gated.
- **Classification:** LEGACY.

## BP-04 — 4d telegram_bot single-click code apply (deprecated)
- **Path:** `route_callback("approve:<pid>")` → `self_code.approve(pid)` (4d_system/brain/telegram_bot.py:358-367) — one button press applies a code proposal; no double-confirm step (doctrine in control_plane/approvals.py requires `confirmed=True`).
- **Mitigation:** `self_code.approve` itself re-runs the full gate at apply time (enabled flag, status check, TCB `assert_code_target_allowed`, stale comparison, static rescan, sandbox execution, tamper detection — self_code.py:403+); module is deprecated behind `OCTOPUS_4D_TELEGRAM_BOT_OPT_IN` fail-closed exit 3 (telegram_bot.py:40-89) due to the 409 second-poller hazard.
- **Classification:** LEGACY (dormant; revival requires explicit owner vote per DEPRECATED.md).

## BP-05 — lead outbound email lane executes outside action_bridge
- **Path:** proposal → owner verdict authorizes specific `effect_id` (allowlist default empty, lead_effect_gate.py:15,95) → `release_and_settle` (STOP/consent/authorization/idempotent) → outbound_worker → SMTP transport. Real network side effect; armed by owner vote 2026-07-31 (vote 17, TG-UI charter).
- **Bypasses:** action_bridge A4 (which has *no* executor function by design) — this is a separate lane with its own gate stack rather than a hole in action_bridge.
- **Mitigation present:** per-effect owner authorization, consent_gate may_draft/may_release, daily cap 10 (two layers; env-overridable, ≤0 = uncapped since owner request 2026-08-12), staleness gate (24h default, hard ceiling 72h, missing release_ts = refuse), GAP-2 price must come from recorded quote, NOT_ARMED honest status.
- **Classification:** BENIGN_INTERNAL (owner-armed lane), with one flag: `OCTOPUS_LEAD_DAILY_SEND_CAP<=0` removes the numeric cap by owner instruction — remaining gates are consent/authorization/STOP only.

## BP-06 — state_guard.py rewrites "append-only" state files
- **Path:** `_ops/state_guard.py` `_atomic_rewrite` (line ~297) strips null/invalid lines from REPAIR_TARGETS (`reach/ledger.jsonl`, `action-audit.jsonl`, `events.jsonl`, `intervention-ledger.jsonl`, …) and rewrites the file; quarantined lines moved to sidecar (evidence: `state/reach/ledger.jsonl.quarantined.20260808T165341`, removed_null: 1).
- **Bypasses:** append-only ledger semantics (not hash-chain integrity — affected files are unchained JSONL).
- **Classification:** BENIGN_INTERNAL (repair tool) — but it means several files named "ledger" are not immutable in practice; the hash-chained ledgers (genome, chord, octopus_v3 IntentLedger) are not in REPAIR_TARGETS.

## BP-07 — events.clear_events() deletes the 4d dashboard event log
- **Path:** `clear_events()` (4d_system/brain/events.py:303-313) `DELETE FROM dashboard_events` — full log wipe callable by any code importing the module (used in `__main__` self-test).
- **Classification:** LEGACY / TEST_ONLY-ish (self-test path), no owner gate; if the 4d brain's event history is ever treated as evidence, this is a delete path.

## BP-08 — LLM output written to ungated 4d memory store
- **Path:** `generate_hypothesis` tool (4d_system/brain/tools.py:118-156): LLM reply → `save_hypothesis(domain, hypothesis)` directly; no admission gate (contrast: `_ops` MemoryGate FSM). Hypotheses later feed prompts (`get_pending_hypotheses` → auto_experiment).
- **Bypasses:** memory admission control (4d side has none); poisoning vector for future prompts, not for execution.
- **Classification:** BENIGN_INTERNAL today (research sandbox; worst case = polluted research prompts), but it violates the invariant "model output is untrusted input" at the persistence layer.

## BP-09 — supervisor.py spawns processes (restart paths)
- **Path:** `control_plane/supervisor.py` (v5 self-healing) can spawn/restart known commands; flagged `self_heal_restart` = SHADOW_LOG in the 4d policy ladder, and policy.py:79-80 keeps `restart_after_halt` owner-only.
- **Classification:** BENIGN_INTERNAL (flag-gated, restart of same known commands after crash; halt-recovery remains owner-only).

---

## Summary table

| ID | Path | Bypasses | Classification | Severity |
|----|------|----------|----------------|----------|
| BP-01 | `/sh` owner shell | everything except owner auth | BENIGN_INTERNAL | MEDIUM (owner-console blast radius) |
| BP-02 | 4d policy ladder unwired | n/a (parallel observe-only plane) | BENIGN_INTERNAL | LOW |
| BP-03 | latest-pending approval flip | approval-action binding | LEGACY | LOW |
| BP-04 | single-click code apply (4d bot) | double-confirm doctrine | LEGACY | LOW |
| BP-05 | lead email lane | action_bridge A4 (own gates instead) | BENIGN_INTERNAL | MEDIUM (real external effect; cap now env-removable) |
| BP-06 | state_guard ledger rewrite | append-only semantics | BENIGN_INTERNAL | LOW-MEDIUM |
| BP-07 | clear_events() | evidence retention | LEGACY | LOW |
| BP-08 | ungated LLM→memory write (4d) | memory admission | BENIGN_INTERNAL | MEDIUM (poisoning vector) |
| BP-09 | supervisor restart spawns | restart authority | BENIGN_INTERNAL | LOW |

No UNCONTROLLED_SIDE_EFFECT path was found: every external-effect lane located (BP-05, BP-09, self_code apply, agi2027 ops actions) carries an owner gate, a flag armed by a recorded owner vote, or both.
