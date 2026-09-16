# LEG P0-1 — `speed_to_lead` (response half of P0 ResponseQuoteLeg)
**Version:** 1.1 · **Priority:** P0 · **Pattern source:** Upscale Painting ("get a reply within minutes") + Premium Trust-and-Response playbook (first responder wins)
**Type:** propose-only Leg (Octopus invariant-compliant; no autonomous sends)

## I7 compatibility note (v1.1, explicit)
Nothing in this leg sends autonomously — "speed" means **card latency plus human action**,
never an ungated send. The external SMS/email leaves only after: owner verdict → LANGAR append
→ EffectorGate release. If a pre-approved transactional-reply policy is ever wanted, that is a
future explicit change to I7/TINV-7 by the Owner — not something this leg may assume.

## Mission
Every inbound `consented_inbound` lead produces an owner card **within 10 seconds** using the
two-stage card pattern: stage 1 = instant card with raw lead facts (name/suburb/text/urgency
placeholder); stage 2 = the LLM draft appended into the same card via `editMessageText` as soon
as it's ready (seconds later). Target: owner-approved reply reaches the lead in ≤ 2 minutes
from card during business hours.

## Integration contract *(verify names against repo before wiring)*
- Registered under `_ops/legs/speed_to_lead.*`; discovered by `live_loop.route_leg_proposals()`.
- Consumes event `lead.created` from the Lead Inbox (see `lead_inbox/LEAD_INBOX_SPEC.md`).
- Emits `LegProposal` → Telegram approval card → on **Approve**: LANGAR append → EffectorGate releases the SMS/email send → `record_proposal_outcome()`.
- Never sends anything itself. Ever.

## Input event schema (`lead.created`)
```json
{
  "lead_id": "uuid",
  "received_at": "ISO8601",
  "channel": "phone_missed|web_form|sms|email|facebook|airtasker|hipages|referral|manual",
  "name": "string|null",
  "phone": "string|null",
  "email": "string|null",
  "suburb": "string|null",
  "service_hint": "string|null",
  "raw_text": "string",
  "source_meta": {},
  "consent_basis": "inbound_inquiry"
}
```

## Processing steps
1. **Guard checks** (hard-coded, not LLM):
   - Dedupe: same phone/email active in last 14 days → attach to existing thread, propose follow-up instead of first-touch.
   - Quiet hours: if local time outside 07:30–20:30 AEST → draft now, propose **scheduled send at next window open** (card states the scheduled time).
   - Channel rule: reply on the channel the lead used (missed call → SMS; email → email).
2. **LLM draft** (prompt below) → first-response message + 1-line internal summary + urgency flag.
3. **Assemble proposal card** and route to Telegram.

## LLM prompt template (system)
```
You are the first-response drafter for {{BUSINESS_NAME}}, a licensed painting & maintenance
business in Sydney (NSW Lic {{NSW_LICENCE_NO}}). Owner: {{OWNER_NAME}}.

Draft ONE reply to a brand-new inbound lead. Rules:
- Voice: warm, competent Australian tradesperson-professional. No corporate filler, no emojis,
  no exclamation stacking. Sound like a busy professional who answers fast — that IS the brand.
- Always: greet by name if known, confirm you received their inquiry, show you read the
  specifics (mirror ONE concrete detail from their message), offer the next step.
- Next step = propose a concrete inspection window ("this arvo on my way past {{suburb}}
  around 5pm, or tomorrow 8am") OR a video-quote option for small jobs.
- SMS: max 320 chars, must start with "{{OWNER_NAME}} from {{BUSINESS_NAME}} here —" and
  end with "Reply STOP to opt out." (Spam Act identification + unsubscribe).
- Email: subject + max 120 words, signature block with licence no + insurance line.
- If the message signals urgency (water damage, mould, end-of-lease date, pre-sale/auction),
  acknowledge the deadline explicitly and offer the earliest slot.
- NEVER quote a price. NEVER promise a start date. NEVER claim availability you can't know.
Output JSON: {"message": str, "channel": "sms|email", "summary": str,
"urgency": "urgent|standard", "reasoning": str}
```

## Telegram approval card
```
⚡ NEW LEAD ({{channel}}) — {{elapsed}}s ago
{{name|Unknown}} · {{suburb|?}} · {{service_hint|?}}
"{{raw_text | truncate 200}}"
Urgency: {{urgency}} | Send: {{now | scheduled 07:30}}
── Draft ({{sms|email}}) ──
{{message}}
[✅ Send] [✏️ Edit] [📞 I'll call instead] [🗑 Junk]
```
- **Send** → EffectorGate releases via SMS/email effector; outcome `sent`.
- **Edit** → owner's edited text is what gets sent; store diff for learning.
- **I'll call** → no send; log `owner_called`; schedule follow-up check card at T+4h.
- **Junk** → outcome `rejected_junk`; feeds source-quality scoring.

## SMS effector config (Day-0 decision, from Verification Report §4.2)
- ACMA Sender ID Register is in force since 1 Jul 2026: **either** register the alphanumeric
  sender ID through the SMS provider **or** send from a dedicated virtual mobile number.
  Config: `SMS_SENDER_MODE = registered_alpha | dedicated_number`. Default: `dedicated_number`
  (leads can reply/call back — better for conversion anyway).

## Outcome recording
`record_proposal_outcome(proposal_id, outcome ∈ {sent, edited_sent, owner_called, rejected_junk, expired}, meta: {elapsed_to_card_s, elapsed_to_send_s, lead_id, channel})`
Downstream: `lead.first_response_at` set → feeds KPI + Governor.

## KPIs (v1.1 split: system latency vs human latency, never conflated)
- `lead_to_card_p50` ≤ 10s (stage-1 instant card) · `draft_appended_p50` ≤ 30s
- `card_to_send_p50` ≤ 2min business hours (owner action — a human metric, reported separately)
- approval rate ≥ 70% unedited after week 2 (else prompt needs tuning)
- lead → booked-inspection rate per channel (the market number that matters)

## Failure modes & guards
- LLM timeout > 30s → send fallback template card (pre-written generic reply) instead of nothing.
- Missing contact info → card becomes "task: find contact" not a send proposal.
- Duplicate cards for one lead: idempotency key = `lead_id` (one open first-touch proposal max).
- Never auto-expire silently: unactioned cards re-ping owner once at T+15min, then mark `expired`.

## Compliance notes
- Replying to an inbound inquiry is not unsolicited (consent basis: `inbound_inquiry`), but every
  SMS still carries identification + STOP line. STOP replies → `contacts.do_not_contact = true`
  enforced by the Lead Inbox before any future proposal.
