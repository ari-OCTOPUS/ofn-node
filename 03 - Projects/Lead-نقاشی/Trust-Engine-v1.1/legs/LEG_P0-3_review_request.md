# LEG — `review_request`
**Version:** 1.1 · **Priority:** **P1** (re-sliced 2026-07-21: P0 is funnel-only. Pull-forward exception: this leg consumes `job.completed` from the EXISTING business, independent of the new funnel — the Owner may activate it early as an explicit config decision.)
**Pattern source:** all 5 reverse-engineered Sydney winners (review velocity is the #1 shared moat; Brushworks' Trustindex widget, Upscale's 3-platform review wall)
**Type:** propose-only Leg with **sequence-level approval** (policy noted below)

## Mission
Every completed job converts into (1) a Google review, (2) a referral seed, (3) a reactivation record. Review velocity — fresh reviews per month — is the single strongest Maps-ranking and trust input for a young painting business.

## Integration contract *(verify against repo)*
- Trigger: event `job.completed` (from `/done <job_id>` Telegram command or ServiceM8 webhook later).
- Emits ONE `LegProposal(kind="review_sequence")` covering the whole cadence.
- **Policy decision (explicit, Owner-visible):** approval is granted once for the whole
  sequence; subsequent messages in the cadence auto-release through EffectorGate **only** while
  kill-switch conditions are false. If strict per-message gating is required by Octopus
  invariants (I1–I10), set `REVIEW_SEQ_MODE=per_message` and each step becomes its own card.
  Default: `sequence` (otherwise the Owner drowns in cards and the cadence dies — the exact
  failure the prior research warned about).

## Input event schema (`job.completed`)
```json
{
  "job_id": "uuid", "client": {"name": "", "phone": "", "email": ""},
  "suburb": "", "service": "", "value": 0,
  "completed_at": "ISO8601",
  "satisfaction_signal": "explicit_happy|neutral|complaint|unknown",
  "photos_before_after": true
}
```

## Cadence (default)
| Step | When | Channel | Content | Kill-switch check before send |
|---|---|---|---|---|
| S1 | T+2h (or 09:00 next day if job ends after 17:00) | SMS | Thank-you + direct Google review link | complaint raised? STOP received? |
| S2 | T+3d | SMS | Gentle reminder (only if no review detected) | review already left? reply received? |
| S3 | T+10d | SMS or email | Referral seed: "know anyone in {{suburb}} thinking about painting? We look after friends of clients" + referral incentive if configured | reviewed-and-happy only |
| — | T+180d / T+365d | — | handoff: emit `reactivation.due` for future Reactivation Leg (P2) — recorded, not sent | — |

**Complaint branch:** `satisfaction_signal=complaint` → NO review ask. Proposal becomes a
service-recovery card ("call {{name}}, issue: …"). A review request on an unhappy client is
negative-review generation.

## LLM prompt template (system)
```
You draft post-job messages for {{BUSINESS_NAME}}. Owner: {{OWNER_NAME}}.
Given job context (client name, suburb, service, any detail the owner logged), draft the
requested step (S1 thank-you+review / S2 reminder / S3 referral).
Rules:
- Personal and specific: reference the actual work ("the hallway gyprock repair came up well").
  Generic review-beggar texts get ignored.
- S1 ≤ 300 chars: thanks + "if you were happy with the work, a Google review helps a small
  local business more than you'd think" + {{GOOGLE_REVIEW_LINK}} + "Reply STOP to opt out."
- S2 ≤ 240 chars, lighter touch, zero guilt, one link.
- S3: referral framing = looking after their people, not commission-speak. Include
  {{REFERRAL_OFFER}} only if provided.
- Never ask for "5 stars" explicitly; never offer payment/discount FOR a review (review-gating
  and incentivised reviews breach Google policy and risk ACL trouble). Referral incentive (S3)
  attaches to a referred JOB, never to the review.
Output JSON: {"message": str, "step": "S1|S2|S3"}
```

## Telegram approval card (sequence)
```
⭐ REVIEW SEQUENCE — {{client.name}} · {{suburb}} · ${{value}}
Satisfaction: {{satisfaction_signal}}
S1 (T+2h): "{{s1_preview}}"
S2 (T+3d, skipped if reviewed): "{{s2_preview}}"
S3 (T+10d, happy-only): "{{s3_preview}}"
[✅ Approve sequence] [✏️ Edit steps] [⏭ S1 only] [🚫 Skip client]
```

## Review detection
- MVO: GBP polling effector (or manual `/reviewed <job_id>` command) sets `review.received`,
  which cancels S2 and unlocks S3.
- Card to Owner on every new review: draft reply included (owner-approved reply → posts via
  GBP API effector). Replying to 100% of reviews is part of the moat.

## Outcome recording
`record_proposal_outcome(proposal_id, outcome ∈ {sequence_approved, partial, skipped}, meta:{job_id})`
Per-step effector log: `review_msg.sent{step}` · terminal events: `review.received{rating}`,
`referral.received{new_lead_id}` — **referral.received links the new lead to the referring job:
this is how the Governor learns which jobs/suburbs breed compounding work.**

## KPIs
- reviews/month (velocity) + rolling average rating · S1→review conversion %
- % reviews replied to (target 100%) · referral leads/quarter and their close rate

## Failure modes & guards
- Client already asked in last 90 days (repeat client) → S1 only, no reminder.
- STOP at any step → halt sequence, set do_not_contact, confirm card to Owner.
- No review link configured → block sequence with setup card (don't send a linkless ask).
- Timezone/quiet hours same rules as Leg P0-1.

## Compliance notes
- Existing customer = inferred consent under Spam Act; identification + STOP still mandatory.
- No incentivised reviews (Google policy + ACL "misleading testimonials" exposure).
- Review reply drafts must never disclose client address/job details beyond what the reviewer
  themselves made public.
