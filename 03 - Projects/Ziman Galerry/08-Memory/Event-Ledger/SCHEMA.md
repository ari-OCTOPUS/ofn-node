---
type: event
schema: ziman.event.v1
tenant_id: ZIMAN
---

# Event schema (append-only ledger)

Required fields:
```yaml
event_id: ""
schema_version: "ziman.event.v1"
idempotency_key: ""
content_hash: ""
occurred_at: ""
recorded_at: ""
actor_type: "human|agent|system"
actor_id: ""
tenant_id: "ZIMAN"
entity_id: ""
event_type: ""
evidence_pointer: ""
confidence: 0.0
privacy_class: "public|internal|restricted"
status: "provisional|active|retracted"
correlation_id: ""
causation_id: ""
```

## Example event types
- `inventory.owner_reported`
- `product.card_drafted`
- `experiment.planned`
- `experiment.outcome_recorded`
- `content.draft_created`
- `approval.granted`
- `capacity.ceiling_updated`
- `incident.raised`

Ledger path: `08-Memory/Event-Ledger/` (one JSONL or dated md files — curator decides format later).
No secrets/PII in events.
