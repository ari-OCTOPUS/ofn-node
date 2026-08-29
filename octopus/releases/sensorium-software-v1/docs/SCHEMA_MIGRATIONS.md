# SCHEMA_MIGRATIONS

upgrade_observation fills location/evidence/policy and forces signature_verified=false.
Legacy records are not deleted. Malformed events go to quarantine jsonl.
