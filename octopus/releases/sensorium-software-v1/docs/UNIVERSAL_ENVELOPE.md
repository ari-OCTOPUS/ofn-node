# UNIVERSAL_ENVELOPE

Required fields: event_id, schema_version, sequence_number, sensorium_board_id, sensor_id,
subsensor_id, sensor_agent_id, observation_type, observed_property, subject, result, time,
location, quality, uncertainty, provenance, evidence, security, routing, policy.

Rules:
- provenance, evidence, and policy are mandatory
- time_unverified is explicit
- signature_verified is false unless a real verify set verified_by
- confidence is clamped to [0,1]
- canonical JSON + SHA-256 content hash
- malformed events append to quarantine jsonl; originals are not rewritten
