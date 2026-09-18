# L8 PASS CRITERION (written before scanning outputs)
Lane: L8 Ledger topology diagnosis
Written: 2026-09-01T23:50:00+10:00
Read-only: yes except 09-LANES/L8/
Forbidden: src/ writes, ledger/ writes
Depends on: L1 (log-mining findings exist)

This lane PASSES iff all of:
1. PASS-CRITERION.md hashed before extracting chains from ledgers.
2. One real causal chain is extracted from EXISTING files (e.g. .cursor/hook-ledger.jsonl hash chain and/or 07-HANDOFF/contradictions.csv). Each hop has a source path.
3. Information loss points are named from those files (missing fields, broken prev_hash, truncated rows, dual values without winner). No invented hops.
4. Graph build is deferred as a proposal only (not implemented, no ledger/ writes).
5. No flags, no network, no rm, no git push, no Telegram.

Baselines: persistence (existing jsonl chain), prior-only (L1 findings are context not a new chain), random (not used).
Every number needs a source path or the token unverified.
