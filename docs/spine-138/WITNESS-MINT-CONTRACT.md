# WITNESS MINT CONTRACT (2026-08-28)
- Sole minter: 138 (ofn/adapters/witness_mint.py). 180/182 never self-mint.
- Binding (all recorded in request): run_id, artifact_sha256 (exact bytes), payload_sha256, policy_version, schema_version, created_at.
- request_id = sha256(canonical binding tuple) — deterministic → duplicate mint = same id, single JSONL line (idempotent by construction).
- Ledger: state witness_requests.jsonl append-only at minter.
- Verdict routing: 182 witness_response returns to the ORIGINAL run_id correlation; 138 settler consumes once (--no-reply).
- STRUCTURAL_PASS ≠ EXECUTABLE_PASS: mint produces structural verification only. An executable action card additionally requires a valid OwnerDecision approval with exact payload/artifact/verdict hashes — mint refuses to imply executability.
