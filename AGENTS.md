# OCTOPUS — Agent Operating Contract

Every agent working in this repository (Cursor Agent, Cursor CLI, cloud agent, Tab) is bound by this file.
Nested `AGENTS.md` files in subdirectories add constraints; they never remove them.

## 1. Truth hierarchy (strongest to weakest)
1. Runtime output: real `pytest` run, execution receipt, `git log`
2. Repository file: ledger, MANIFEST, registry
3. Fresh CHECKPOINT / HANDOFF / DECISIONS
4. Older notes, megaplans
5. FORBIDDEN as evidence: chat summaries, agent memory, guesses

If a claim cannot be confirmed from level 1 or 2, write `status: unverified`. Never write it as fact.

## 2. Evidence grades (attach to every capability claim)
- E0 claimed, no code found
- E1 code exists, no test
- E2 unit test green on designed input
- E3 negative and boundary cases green
- E4 works on held-out (unseen) input
- E5 works under fault injection and scaffold variation

Hard rule: no capability rises above E3 without a scaffold-variation measurement.
Lowering a grade is a successful outcome, not a failure.

## 3. Number discipline
- Number without a source = `unverified`
- Small n = `UNDERPOWERED`, never "improved"
- Contradiction: record both values with `resolution: null, status: open`. Never silently pick one.
- Never generate synthetic or "illustrative" data.

## 4. Output boundaries (non-negotiable)
- Do not enable any flag matching `OCTOPUS_WIRE_*`, `OFN_WIRE_*`, `OBSERVATORY`, `CORTEX_HYPOTHESIS`
- `auto_email` stays closed. No email, message, or post leaves the machine.
- Do not open blocked gates: `secret_rotation`, `partner_precondition`, `miner_isolation`, `D1`, `D7`, `OWNER_KEY`
- Blocked is a decision, not a defect.

## 5. Self-elevation ban
Never raise your own authority. Do not edit your own gate, quota, or approval threshold.
Do not change a scoring formula mid-cycle. An attempt to self-elevate is an incident and gets logged.

## 6. Owner decisions
Do not decide on the owner's behalf, even when the answer looks obvious.
List it in `07-HANDOFF/` as `status: open, requires: owner_decision` and continue.

## 7. Deletion and naming
- `rm -rf` is forbidden. Stale files move to `99-ARCHIVE/` with an `archive_` prefix.
- No file named "brain v2" or "replacement orchestrator".
- Secrets: key names only, never values. Redact emails and names in logs and fixtures.

## 8. Lane discipline
Each agent works in exactly one lane, declared at session start, in its own git worktree.
Touching a file owned by another lane is a stop condition: log it and halt.

## 9. Exit requirement
Every session ends with `09-LANES/<LANE>/LANE-REPORT.md` containing: what was done, what
remains, what failed, evidence paths, rollback steps. No report, no completion.
