---
id: mem_...
type: run
brain_owner: B6
status: raw            # raw → episodic → semantic → canonical_candidate → (approval) → canonical
risk_level: low
sensitivity: internal
source: { kind: model, ref: "" }
confidence: 0.0
created_at: 2026-07-11
updated_at: 2026-07-11
---

# Memory Write — <subject>

- **Stage:** raw | episodic | semantic | canonical_candidate | canonical
- **Provenance:** where it came from (source.kind + ref + trace/run id)
- **Payload:** the content being written
- **Promotion:** the next stage requires an evidence-backed `approval-packet` through B6.

> No brain writes `canonical` directly (spec §15). Promotion is a gated action.
