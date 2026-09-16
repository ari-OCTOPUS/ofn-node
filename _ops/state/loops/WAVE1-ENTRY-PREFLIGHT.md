# Wave 1 Entry Reconciliation

Generated: 2026-08-20

Wave 1 artifacts are internally inconsistent and must not be flattened into a single PASS:

- `_ops/state/wave1/lock.json`: `wave1_unlocked=true`, activation `canary-sidecar`.
- `WAVE1-ENTRY-GATES.json`: `all_pass=true` but records `wave1_unlocked=false` and only authorizes a canary proposal.
- `WAVE1-VERIFIER.json`: `confirmed=false`, failed check `entry_gates_all_pass`, with gate failure `wave1_unlocked_false_before`.
- `WAVE1-CLOSEOUT.json`: later records `verifier_confirmed=true`, `wave1_api_unlocked=true`, while the Wave 0 governor remains locked.

Conservative state used by this work: **read-only canary-sidecar authorized; full Wave 1 rollout not independently reconciled**. No memory writes, prompt injection, process restart, or Wave flag mutation were performed.
