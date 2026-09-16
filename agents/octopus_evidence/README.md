# octopus_evidence

Library stub for connector Evidence Store rules + CONNECTOR-GAP loader.

- Runtime mirrors: `_ops/evidence_plane/connector_*.py`
- Related existing: `shadow_homeostasis/evidence_store.py`, `epistemics/schemas.py` EvidenceLink
- Rule: missing `evidence_id` OR invalid `source_type` => `unverified=true`
- Estimates require `confidence` + `valid_for`
- No secrets. No OAuth automation. No WAVE0 unlock. No mining.
