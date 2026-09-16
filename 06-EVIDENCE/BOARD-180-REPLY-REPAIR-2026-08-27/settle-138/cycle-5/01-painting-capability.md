# Cycle-5 A — Painting capability map
run_id: revenue-cycle-5-20260827
task_id: C5-PAINT-CAP
idempotency_key: cycle5:painting:capability-map-v2
lane: A
claim_level: OBSERVED C1-C4 stores + Fugu DAY1 + 138 LLM evidence
HOLD_EXTERNAL=yes | no Snapp contact | no send

## Internalize C1-C4 stores (do not mint a new lead store)

- C1: settle-138/cycle-1/01-painting-pack.md (CRM pilots — closed, not people)
- C3: 01-painting.md + 01-painting-snapp.md — unsigned 0100-A / 0101-B A$1815
- C4: 01-painting-snapp-contact.md — CONTACT_STATUS=UNKNOWN. Stay HOLD. Do not re-hunt.

Vault still holds the same files:
- Lead-نقاشی.md (Romeo 2023 STALE only)
- Estimate 0100-A.pdf + 0101-B.pdf

## Existing internal capability

- Fugu painting/DAY1.md + INTAKE.json: inbox JSON → BrainPort draft → HUMAN send gate. APPROVE_QUOTE:<id> only.
- tradequote_local repo exists. Not claimed as a live sender.
- Board2 ofn.service ACTIVE. telegram_production=false.

## Reconnect

Use LIVE route 1 (138 :8895 fugu) for draft/explain only, via ofn/helpers/brainport.py ask(business=painting).
Local fallback: 180 :8081 qwen3-0.6b-q4_0.
Do not contact Snapp. Do not start hypno.service.
