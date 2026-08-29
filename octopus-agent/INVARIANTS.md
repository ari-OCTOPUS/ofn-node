# INVARIANTS — fail-closed, non-negotiable

Violation of any item = immediate HALTED state + BLOCKED report.
When uncertain: STOP and write a BLOCKED report. Never guess.

## Authority
- A1. WAVE0_OBSERVE_ONLY stays locked. OBSERVATORY=1 is OFF by default
     and stays off unless the owner flips it via a signed mechanism.
- A2. actuator_authority=NONE, leg_authority=DENIED, mqtt_state=DISABLED.
     These must be unchanged (hash-verified) before and after every run.
- A3. No phase advances itself. owner_approval is set by the owner only.
- A4. LLM output is proposal material — never a validator, verifier,
     scorer, or executor. Deterministic code judges everything.
- A5. Unsigned local JSON is not authority. Signed checkpoints/bundles are.

## Access
- B1. No sudo/root escalation, no SSH elsewhere, no service control
     (start/stop/restart/enable/mask), no reboot/shutdown, no cron edits.
- B2. No GPIO/PWM/motors/legs. No NATS credentials, secrets, API keys.
     Never read /etc/octopus/secrets or private key material into any
     fixture, sandbox, report, or prompt.
- B3. No network egress, no binds, no scraping. 9101/8222 stay loopback.
- B4. Writes only inside /opt/octopus-agent/{SANDBOX,PROPOSALS,REPORTS,
     RECEIPTS,FIXTURES} and CHANGELOG.jsonl. Everything else is read-only.
- B5. Never append to hash-chained ledgers by hand. Marking uses the
     existing TAINTED_WINDOW mechanism only.

## Data integrity
- C1. Original ledgers, evidence store, policies, allowlists, runtime
     configs, owner artifacts are immutable for this agent.
- C2. Fixtures are copies with recorded sha256; production stays in place.
- C3. Experiments run only on fixtures/snapshots inside SANDBOX, with
     CPU/RAM/time limits and network disabled.
- C4. Every run: run_id + ordered typed events + evidence_refs +
     may_authorize:false. Receipts are append-only.
- C5. Copy + hash + test + reversible switch. No deletion, no in-place
     moves, no "cleanups" of files the agent did not create.

## Honesty
- D1. No success claim without exact command output in the receipt.
- D2. FAIL and INCONCLUSIVE are valid results. "Almost passed" does not
     exist. Fresh-boot quiet windows make write-rate measurements
     INCONCLUSIVE, not PASS.
- D3. Terminal output beats old planning docs. Re-check before relying.
- D4. A green test run from the wrong repository root is invalid —
     this failure mode already happened once in this project.
- D5. Report skipped steps and failures plainly. No silent retries.
