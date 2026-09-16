# Painting Day1 — lead path (no live send)
Canonical intake: drop JSON matching lead.schema.json into painting/inbox/
Scoring: deterministic rules in score_lead.py (to be added) — model only explains/drafts
Outbox: quote draft + SoW + followups D0/D1/D3 — HUMAN send gate
Invoice/deposit: prepare link template READY_NOT_APPLIED until GO
Approval: only APPROVE_QUOTE:<id> bound command — plain chat is NOT approval
Idempotency: one quote/invoice per lead_id
