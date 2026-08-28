# SAFETY PROOFS (non-destructive; suite-cited, run 2026-08-28T00:14:00Z)
| # | Claim | Proof | Result |
|---|---|---|---|
| 1 | 180 cannot customer-send directly | mesh policy roles + may_authorize=false everywhere; 180 has no egress besides mesh transport; no_public_surface tests (no anonymous business writes) | PASS (structural) |
| 2 | 182 has no executor handle | 182 role=lab-witness; effects only on 138; witness CLI verification-only | PASS (structural) |
| 3 | 138 builds no executable card without pass | action_tiers gate: YELLOW→needs approval, RED→disabled (octopus_common.action_check; tests/test_runtime.py executor cases) | PASS |
| 4 | structural PASS ≠ EXECUTABLE_PASS | EXECUTABLE_PASS concept absent in ofn runtime (vocabulary from newer directives, unmapped) → coverage gap GAP-1, not a bypass | NOTED |
| 5 | UNKNOWN mandatory-payload reject | mesh receiver schema/policy rejects malformed; envelope truth=UNKNOWN surfaced, never silently accepted | PASS |
| 6 | approval without exact payload hash rejected | approval_create binds payload_hash; approval_validate rejects payload_changed | PASS (unit) |
| 7 | expired/superseded/wrong-user/duplicate approval rejected | TestApprovalLifecycle (expired→reject, replay→reject, decision binding) | PASS (unit) |
| 8 | changed payload after approval rejected | approval_validate 'payload_changed' | PASS (unit) |
| 9 | same idempotency key → no second effect | transport 'duplicate' status + worker duplicate_blocked (live-proven 2026-08-26/27 canaries) + tests | PASS (live+unit) |
| 10 | Telegram/policy unavailable → DENY not allow | telegram bridge fail-closed (BLOCKED_CONFIG, no sends); owner-control identity fail-closed; no-response=deny/hold standing rule | PASS (structural) |
All probes fake/sandbox; zero live effects; zero secrets read.
