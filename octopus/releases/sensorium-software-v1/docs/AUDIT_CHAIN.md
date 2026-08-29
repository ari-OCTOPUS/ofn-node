# AUDIT_CHAIN

Fields: previous_hash, payload_hash, record_hash, sequence, head.hash.
verify_chain walks the jsonl. Concurrent delayed forks from a seen parent are accepted.
GAP-002 remains OPEN until an offline-signed checkpoint verifies.
audit_integrity=HASH_CHAIN_ONLY until that happens.
