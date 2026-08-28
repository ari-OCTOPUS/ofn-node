# TRANSPORT CONTRACT — 138→180 business spine (2026-08-28)
- Transport: EXISTING SSH mesh only (octomesh_send → peer receiver). No new broker/port.
- Envelope: standard mesh message + payload carries business_source.v1 snapshot reference.
- ACK semantics: ACK proves RECEIVE only (envelope accepted by peer receiver). ACK != processed != proposal.
- Idempotency: event_id = snapshot_id + lane; resend with same idempotency_key returns duplicate, no second effect.
- Wake binding: one wake task binds exactly one snapshot_id + row_count + source_row_hash set; 180 must echo binding in proposal.
- Receipts: mesh audit seq + queue counts recorded at send; age tracked until claim.
- Labels: source_kind=fake|live_masked carried in payload; live masked rows have may_contact=false, pii_redacted=true.
- Retry: bounded (max 2), same payload bytes, same idempotency key; MODEL_RERUNS=0 (frozen replay on peer).
