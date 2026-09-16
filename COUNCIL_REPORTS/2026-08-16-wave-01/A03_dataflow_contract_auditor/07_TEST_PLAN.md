# 07_TEST_PLAN — A03 (2026-08-16)

Read-only-verifiable tests (T1) that would upgrade this report's statuses. A03 did not
execute tests; existing suites observed on disk: `_ops/action_bridge/tests/` (test_flow,
test_classifier, test_scope_guard, test_claimed_fixture, bridge_harness),
`4d_system/tests/test_control_plane_*.py`, `tests/test_goal_action_bridge.py` (14/14 green
per component registry — not re-run by A03).

## Proposed tests

### TP-1 · Text cannot de-escalate (classifier property)
For every action_type in BASE: for adversarial `intent`/`expected_effect` texts (Persian +
English fabrication pairs, scope-escape phrases, "read-only", "just observing"),
`classify(req)["classification"] >= BASE[req["action_type"]]`. Status upgrade: F-02 → T1.

### TP-2 · A2/A4/A5 executor-path absence (structural)
Assert `executor.EXECUTABLE == {"A0","A1"}` and that no function in action_bridge performs
network/subprocess/SMTP (grep-based import-lint as a test). Guards against drift adding an
A4 executor silently. Upgrade: F-03/F-04 → T1.

### TP-3 · Approval binding & replay (owner_gate)
approve-for-action-A must not authorize action-B (payload_hash mismatch); expired approval
rejected; nonce reuse rejected; missing signing key ⇒ grant fails closed; non-ASCII
signature rejected without exception. Upgrade: F-06 → T1.

### TP-4 · Receipt-failure downgrade (receipt.finalize)
Simulate receipts_dir write failure → status EXECUTED must come back FAILED with
`status-downgraded` error; ledger append failure same. Upgrade: F-07 → T1.

### TP-5 · Idempotency conflict detection
Same action_id + different target ⇒ CONFLICT (rsplit(":") path — the historically dead
branch); no-ledger ⇒ CONFLICT. Upgrade: F-08 → T1.

### TP-6 · Memory veto polarity
With router returning veto=true: mission blocked + ledger row; with router raising:
pipeline continues (fail-soft); plan bytes identical with/without `_recall_for_goal`
(invariant `t_memory_is_never_authority_over_the_plan`). Upgrade: F-09 → T1.

### TP-7 · Callback token TOCTOU
`ap:approve:<jid>:<token>` with token minted for different action/owner/expiry must fail
`compare_digest`; expired epoch fails; second use of same jid `_move` returns False.
Upgrade: F-11 → T1.

### TP-8 · `/sh` absence-of-confirm probe (red test documenting current behavior)
Document expected current behavior (executes after owner gate without confirm) and the
post-REC-1 target (requires pw/pwc). Prevents silent regression in either direction.

### TP-9 · Lead lane gate stack
Per-effect authorization: send_one without owner-authorized effect_id ⇒ refuse; stale
release_ts (25h default) ⇒ `effect.refused(stale_refused)`; missing release_ts ⇒ refuse;
cap counter increments only on confirmed sent; GAP-2: email body amount == recorded
`total_incl_gst` else skip with `no-price` receipt. Upgrade: F-13 → T1.

### TP-10 · Temporal invariants
New spine/outcomes rows: `occurred_at <= recorded_at` and (until REC-3b) equal — make the
current equality an explicit, asserted property so the first true backdated event flips a
visible test; receipts parse with offset or are rejected; genome ledger chain verifies over
last N rows (verify_chain exists for chord; add for genome). Upgrade: F-14/F-15/F-29 → T1.

### TP-11 · MemoryGate authority rules
Candidate with source=agent, namespace=owner_fact ⇒ verb ∈ {propose, reject}, never commit;
self_knowledge stays ADVISORY; secret-shaped content rejected (regex battery); TTL expiry
changes search results. Upgrade: F-17 → T1.

### TP-12 · Scope-guard traversal battery
`..`, junction/symlink escapes, drive letters, UNC, NUL, `sandbox-evil` vs `sandbox`
prefix, forbidden markers on resolved path only (e.g., a file literally named
"ledger-notes.txt" *inside* an allowed scope is still forbidden by marker "ledger" —
confirm intended). Upgrade: F-23 → T1.

### TP-13 · state_guard quarantine preserves evidence
After repair, quarantined lines exist in sidecar; original file line count = before −
removed; a chained ledger in REPAIR_TARGETS would fail verification (currently none — add
guard test that REPAIR_TARGETS ∩ chained-ledgers = ∅). Upgrade: F-26 → T1.
