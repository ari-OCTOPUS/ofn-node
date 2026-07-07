---
type: reference
status: done
tags: [fusion-audit]
created: 2026-07-03
updated: 2026-07-03
---

# REFACTOR_PLAN — Fusion MVP (plan only, no code changes)

One item per fix. Ranked by risk-reduction per hour. Effort: S ≤1h / M ≤4h / L >4h.
`HUMAN-APPROVAL-REQUIRED` marks any item touching IGK kernel, HITL gate, kill-switch, or the
audit/Anchor Ledger. **Only R-01…R-05 are approved for the next work session.** Everything else is
backlog until a re-audit confirms the top fixes landed.

---

## APPROVED FOR NEXT SESSION (Top 5)

### R-01 — Make IGK unavailability fail-CLOSED  ·  Sev High  ·  Effort S  ·  HUMAN-APPROVAL-REQUIRED
- **Findings:** P1-01, P4-02, P6-02.
- **Change:** When `use_igk` is requested (config `USE_IGK=True`) and the kernel fails to spawn,
  **halt the run** instead of setting `self.use_igk=False`. Downgrade to cooperative mode must be an
  explicit, logged, opt-in flag (e.g. `ALLOW_COOPERATIVE_FALLBACK`, default False) — never the
  silent default. Narrow the `except Exception` to the specific spawn/IO errors and re-raise
  otherwise.
- **Files touched:** `src/orchestrator.py` (42-49; also the `PermitDenied` import stub 26-30),
  `config.py` (new flag).
- **Verification:** add a test that forces `KernelClient.__init__` to raise and asserts the run ends
  `halted`/`interrupted` (mirroring `test_igk_integration.py` case 2), and that `run_done` is never
  emitted. Existing `igk/test_redteam.py` and `test_igk_integration.py` must stay green.
- **Dependencies:** none. Do first — it is the single highest risk-reduction-per-hour item.

### R-02 — Human verdicts become a signed, tamper-evident root of trust  ·  Sev High  ·  Effort M  ·  HUMAN-APPROVAL-REQUIRED
- **Findings:** P2-01, P2-02, P2-03.
- **Change:** Route every `hitl_request`/`hitl_decision` through the **kernel's signed audit**
  (`KernelClient.audit`, HMAC) in addition to (or instead of) the unsigned `AuditLog`, so the human
  verdict itself is cryptographically anchored. Bind the verdict record to something stronger than
  the literal `"human-gate"` (at minimum a per-run verdict nonce issued by the kernel; ideally an
  operator identity). This is the concrete "Anchor Ledger for human verdicts" the system is missing.
- **Files touched:** `src/hitl.py` (27-32), `src/orchestrator.py` (wire kernel handle into HITLGate),
  `igk/kernel.py`/`igk/client.py` only if a new signed verb is needed (keep the frozen-invariant
  property — do **not** add any key/invariant-mutating verb).
- **Verification:** test that a post-hoc edit of a verdict in the signed log fails `verify()`; test
  that a forged unsigned-log approval is detectable by cross-checking the signed record. Keep the
  frozen-verb red-team test (`igk/test_redteam.py:55-59`) green.
- **Dependencies:** touches the kernel protocol surface — sequence after R-01, review together.

### R-03 — Wire (or explicitly retire) the judge panel's LLM verdict  ·  Sev High  ·  Effort M
- **Findings:** P4-01, P6-07.
- **Change:** Decide the panel's contract and make it honest. Either (a) parse `res.text` (e.g.
  `startswith("APPROVE")`) and combine it with the stance heuristic, so real model verdicts and
  provider diversity actually drive the vote and a model refusal is surfaced as a failure; or
  (b) if deterministic voting is intended for the MVP, **remove the paid `provider.complete` call**
  from `Judge.vote` and rename/document the panel as a deterministic policy check (not an LLM panel).
  Do not leave a paid call whose result is discarded.
- **Files touched:** `src/panel.py` (33-53), and doc/README claims about "multi-judge LLM panel."
- **Verification:** test that a provider returning `REJECT` flips a would-be approve (option a), or
  that no provider call is made (option b); a model exception must surface, not be ignored.
- **Dependencies:** none. Not a kernel/HITL surface, so no approval flag — but it is a #5-control fix.

### R-04 — Delete false-assurance controls or implement them  ·  Sev Medium  ·  Effort S
- **Findings:** P4-03 (`MAX_STEPS`), P2-05 (`external_write`), P4-04 (dead `Supervisor.review`).
- **Change:** (1) Enforce `MAX_STEPS` with a real step counter in `Orchestrator.run` that halts on
  exceed, **or** delete the constant and its README claim. (2) Either add a real `external_write`
  actuation that goes through the HITL gate + IGK `gate.act`, **or** remove `external_write` from
  `HITL_REQUIRED_FOR` until such an action exists. (3) Remove `Supervisor.review` (and stop
  constructing the `Supervisor` agent) **or** re-integrate it and update docs — no dead decider.
- **Files touched:** `config.py` (27, 40), `src/orchestrator.py` (81-137, 68), `src/agents.py`
  (72-86), `README.md`/`CHECKLIST.md` claims.
- **Verification:** if enforcing `MAX_STEPS`, a test that a synthetic over-limit run halts; grep
  confirms no dangling references after deletions; full suite green.
- **Dependencies:** none. Note: the `external_write`+HITL sub-item is HITL-adjacent — if you choose
  the *implement* path, that sub-item becomes `HUMAN-APPROVAL-REQUIRED`; the *delete* path is not.

### R-05 — Timeout / watchdog on kernel IPC  ·  Sev Medium  ·  Effort M  ·  HUMAN-APPROVAL-REQUIRED
- **Findings:** P6-01 (and it improves P1-06 kill-switch latency).
- **Change:** Give `KernelClient._call` a bounded read (timeout on `readline`, e.g. via a reader
  thread + `queue.get(timeout=...)` or non-blocking IO). On timeout, treat the kernel as failed →
  fail-closed halt (consistent with R-01). This removes the indefinite-hang path and lets STOP be
  observed within a bounded window even if the daemon stalls.
- **Files touched:** `igk/client.py` (22-26, 37-41).
- **Verification:** test with a stub daemon that never responds; assert `_call` raises within the
  timeout and the run halts fail-closed rather than hanging.
- **Dependencies:** pairs with R-01 (shared fail-closed halt path). Touches the kernel client →
  approval flag.

---

## BACKLOG (ranked; do not start until R-01…R-05 land and are re-audited)

### R-06 — Fix / gate the grounding control  ·  Sev Medium  ·  Effort M  ·  HUMAN-APPROVAL-REQUIRED
P1-04. Ground the **analysis/claims that actually correspond to the held-out domain**, not raw
Researcher findings; or replace the geography/science `held_out.json` with a domain-matched anchor;
then decide whether `GROUNDING_REQUIRED` can be safely enabled. Files: `src/orchestrator.py:114-120`,
`igk/held_out.json`, `config.py:59`. Verify: with the fix, a normal run does not score ratio 0.0 and
`GROUNDING_REQUIRED=True` no longer halts every run. Kernel-adjacent → approval flag.

### R-07 — Single canonical held-out anchor  ·  Sev Medium  ·  Effort S  ·  HUMAN-APPROVAL-REQUIRED
P5-03. One source of truth for `held_out.json` with a single loader; remove the duplicate or make one
a generated copy. Files: `igk/kernel.py:56-60`, both `held_out.json` locations, tests that copy it.
Kernel-adjacent → approval flag.

### R-08 — Link/consolidate the two audit chains  ·  Sev Medium  ·  Effort M  ·  HUMAN-APPROVAL-REQUIRED
P5-01. Cross-reference the unsigned main chain and the signed kernel chain (e.g. main-log records
carry the kernel seq/sig for the same event), so a full timeline is authenticated end to end. Files:
`src/tracing.py`, `igk/kernel.py`, `src/orchestrator.py`. Audit-ledger surface → approval flag.

### R-09 — Unify the two kill-switch paths  ·  Sev Medium  ·  Effort S  ·  HUMAN-APPROVAL-REQUIRED
P1-05. Have `_kguard` also honor the in-process `KillSwitch` (and/or route programmatic trips to
create the external STOP file) so both stop mechanisms are coherent under IGK. Files:
`src/orchestrator.py:73-79`, `src/killswitch.py`. Kill-switch surface → approval flag.

### R-10 — Treat configuration as immutable settings  ·  Sev Medium  ·  Effort M
P1-07, P6-04. Load config once into a frozen object / settings instance passed explicitly, instead of
mutating module globals; adjust tests to use fixtures/overrides rather than reassigning `config.*`.
Files: `config.py`, `src/*`, tests. Reduces the kernel-relocation and test-contamination risks.

### R-11 — Typed interfaces between components  ·  Sev Medium  ·  Effort L
P6-03. Introduce TypedDict/dataclass (or pydantic) for the kernel protocol responses and a structured
claim/handoff type between agents; fail loudly on shape mismatch instead of silent `None`. Files:
`igk/kernel.py`, `igk/daemon.py`, `igk/client.py`, `src/agents.py`.

### R-12 — Escalate selected halts to HITL  ·  Sev Low/Medium  ·  Effort S
P4-05. Optionally route guardrail/grounding failures through the human gate rather than a bare halt,
if the owner wants human-in-the-loop on those (currently safe-but-silent). Files:
`src/orchestrator.py:93-120`.

### R-13 — Crash-reconcilable per-run state  ·  Sev Low/Medium  ·  Effort M
P5-04. Persist nonce/budget checkpoints (or accept and document the 30s-expiry bound) so post-crash
state is reconcilable. Files: `igk/kernel.py`, `src/budget.py`.

### R-14 — De-duplicate `_load_env`  ·  Sev Low  ·  Effort S
P6-05. One shared loader with consistent quote-stripping. Files: `run.py`, `self_update.py`,
`smoke_live.py`.

### R-15 — Widen audit hash from 64-bit  ·  Sev Low  ·  Effort S  ·  HUMAN-APPROVAL-REQUIRED
P6-06. Use the full SHA-256 digest in the chain. Files: `src/tracing.py:54`, `dashboard.py:46`
(verifier must match). Audit-ledger surface → approval flag. (Largely moot once R-02/R-08 sign the
chain, but cheap.)

### R-16 — Prompt rollback floor validation  ·  Sev Low  ·  Effort S
P5-05. Validate the reverted prompt version against the allow-list on rollback. Files:
`src/prompt_store.py:74-81`.

### R-17 — (scope) Audit LANGAR  ·  Sev n/a  ·  Effort L
Pass 3. Request a read exception for `.../ai-farm/AI-sume/langar-pro/` and run Passes 1–6 against it;
Priority-3 is otherwise unmet.

### R-18 — (scope) Verify git history for pre-move secrets  ·  Sev unknown  ·  Effort S
Pass 7 gap. From an environment where the vault git repo is reachable, scan history for
previously-committed `.env`/`.kernel_key`/`*.key`; if found, rotate (per `ROTATION_CHECKLIST`) —
current `.gitignore` only prevents *future* commits.

---

## Sequencing notes
- R-01 first (unblocks the fail-closed contract that R-05, R-06, R-09 all rely on).
- R-02 and R-08/R-15 are the "signed ledger" cluster — review them together with the owner.
- Do **not** batch kernel/HITL/kill-switch/ledger items with unrelated hygiene items in one commit;
  each approval-flagged item should land in its own reviewed change.
- Re-audit after R-01…R-05 before promoting any backlog item.
