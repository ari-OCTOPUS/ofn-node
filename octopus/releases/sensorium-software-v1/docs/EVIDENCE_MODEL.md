# EVIDENCE_MODEL

Append-only `/var/lib/octopus/state/evidence/observations.jsonl`.
Indexes: event_id, sequence, timestamp, sensor_id, subject, observed_property.
last_*.json files are latest pointers, not the historical store.
Duplicates are detected by event_id. Hash mismatch fails verify_jsonl.
Retention policy: 14 days for derived indexes; jsonl is not rewritten.
No independent JetStream EVIDENCE stream is live.
