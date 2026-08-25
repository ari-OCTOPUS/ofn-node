# Phase 3 P4 — Memory Gate proof

Tests: `python3 -m unittest ofn.organism.tests.test_memory_gate ...` from `/opt/octopus/lab`

- Ran 65 organism tests: OK
- OFN-L4 shadow tests: 4 OK
- Databases: tempfile only
- Live organism.db: not opened via `db.connect()`
- After tests, PID 12748 still alive; no :8091

Invariants asserted in `test_named_decision_paths_emit_receipts_and_evidence` and tick/ask tests:

- memory_reads_per_cycle >= 1
- memory_future_use_total == 0
- decision_evidence.executable == 0
- named purposes present: introspect, create, conclude, curiosity, school, inner_speech, learning, proposal, utterance
- live path connect without env raises `live_schema_mutation_blocked`
- live sqlite_master still lacks `memory_read_receipts` and `wan_fetches`

`test_past_episode_is_evidence_future_episode_is_not` proves bitemporal filter: future episode_id excluded; past included.

Live GET /api/v1/organism was not used for this proof.
