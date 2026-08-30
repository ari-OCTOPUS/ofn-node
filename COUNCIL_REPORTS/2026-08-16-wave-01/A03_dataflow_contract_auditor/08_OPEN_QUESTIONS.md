# 08_OPEN_QUESTIONS — A03 (2026-08-16)

Questions A03 could not close read-only; each is assigned a status of UNKNOWN with the
evidence that would resolve it.

## Q-1 · Is the runtime environment identical to the flag snapshots? (UNKNOWN — T0 needed)
`flags-loaded-cortex.json` and AEB bundles say ~150 WIRE flags =1 (incl. ACTION_BRIDGE,
MEMORY_DECISION, MEMORY_GATE, SCHOOL, INGEST). Is the *running* center/organism process
environment the same right now? → A02: live `os.environ` capture / process inspection.

## Q-2 · Is `OCTOPUS_TCB_MANIFEST_ENFORCE=1` actually set in the live runtime? (UNKNOWN)
4d trust-boundary enforcement is env-gated and default shadow (guardrails.py:211). The
manifest exists and is owner-signed per docs; the enforce flag's live state decides whether
TCB tamper = halt or report. → A02.

## Q-3 · What is the current value of `OCTOPUS_LEAD_DAILY_SEND_CAP` in the live env? (UNKNOWN)
Code default 10; owner said "don't want a limit" (2026-08-12) and ≤0 = uncapped. If the
env is set ≤0, the numeric belt is gone and only consent/authorization/STOP remain. → A02.

## Q-4 · Has any lead email actually been sent to date? (UNKNOWN — state needed)
Lane is armed; A03 did not open counter/state files (`state/legs/lead-send-counter.json`,
events) to avoid touching operational state semantics; a read-only check of counter value
and `events.jsonl` for `communication.*` would settle actual external effects to date. → A02.

## Q-5 · VQ-SELFGOAL-002 preconditions — how many of the four mechanical gates are closed?
The A2→auto flip is a pending owner decision; A03 found the vote reference but not the
checklist status. → owner/council records (04-SYSTEMS / 02-DECISIONS).

## Q-6 · Are spine/outcomes DBs receiving rows in production? (UNKNOWN)
Schema exists; row counts unknown (DBs not opened). If empty, "structurally bitemporal"
degrades further to "schema-only". → A02 read-only SELECT COUNT(*) (permitted for runtime
observation tier).

## Q-7 · Does the paid-LLM budget ceiling hold on every client? (partially out of A03 scope)
Router/budget modules exist and `paid_api_call`=A5 in the ladder, but A03 did not line-audit
`llm/router.py`/`glm_client.py`/`fugu_client.py` enforcement against bypassing imports.
→ A04 (authority) or later A03 wave.

## Q-8 · Intended semantics of forbidden-marker substrings? (design question)
`scope_guard.FORBIDDEN_MARKERS` includes broad substrings ("kill", "ledger", "seed",
"budget/", ".env", "token"). A legitimate artifact path containing any marker is
unconditionally forbidden (conservative). Confirm this is intended over-reach, since e.g.
a note file named "ledger-notes.md" inside an allowed scope cannot be written by A1.
→ owner confirmation (no code change implied).

## Q-9 · Who owns the `/sh` console decision? (owner decision)
REC-1 proposes double-confirm; whether the owner *wants* the friction is an owner-value
call, not an engineering one.

## Q-10 · Is the deprecated 4d telegram bot scheduled for deletion or permanent dormancy?
Vault rule says never delete, only close — confirm the same applies here, so nobody
"cleans up" the fail-closed guard away. → owner confirmation.
