# Cycle-6 Painting — OCTOPUS reconnect runbook
run_id: revenue-cycle-6-20260827
task_id: C6-PAINT-RUNBOOK
idempotency_key: cycle6:painting:brainport-inbox
lane: A
claim_level: C1-C5 receipts + Fugu DAY1
HOLD_EXTERNAL=yes | HUMAN send gate | no Snapp contact

## Memory inputs (do not rebuild)

- C1 01-painting-pack.md — CRM pilots closed (not people)
- C3 01-painting.md / 01-painting-snapp.md — unsigned 0100-A + 0101-B A$1815
- C4 01-painting-snapp-contact.md — CONTACT_STATUS=UNKNOWN Stay HOLD
- C5 01-painting-capability.md — inbox JSON + BrainPort ALLOW painting
- Fugu: F:\\backup\\06-EVIDENCE\\FUGU-BIZ-SPRINT-2026-08-24\\painting\\DAY1.md
- Fugu: painting/INTAKE.json schema painting/schema/lead.schema.json
- Quotes: F:\\backup\\03 - Projects\\Lead-نقاشی\\Estimate 0100-A.pdf and Estimate 0101-B.pdf

## Bind (OCTOPUS, no external agent)

1) Intake store = existing Fugu painting/inbox/ (JSON matching lead.schema.json). Do not mint a second CRM.
2) Call ofn/helpers/brainport.py ask(business="painting", pipeline="quote_draft", prompt=<inbox text>, tier="default")
   default → LIVE 127.0.0.1:8895 hypno-fugu-mini (BRAIN_PROVIDER=fugu).
   local → 180 127.0.0.1:8081 octopus-llama-lab qwen3-0.6b-q4_0.
3) Write draft only to painting/outbox/ (quote / SoW / followup D0 D1 D3).
4) Send gate: APPROVE_QUOTE:<id> bound command only. Plain chat is not approval. No customer send.

## Do not

Contact Snapp. Invent a suburb from the Beecroft gym EFTPOS. Start hypno.service. Rebuild C1-C5.
