# Cycle-1 Painting pack
run_id: revenue-cycle-1-20260827
claim_message_id: 6b5a0753-464e-4808-b572-f77a93ae782a
lane: A
HOLD_EXTERNAL=yes | may_authorize=false | NO send/publish/pay/ads/customer message
claim_level: OBSERVED (embedded leads) + PROPOSAL (questions/quote/cadence)
B2: do not reopen

## 1. Lead scores (directive formula as ranges)

Formula: P(cash) x expected_verified_net x urgency x evidence_quality / minutes / risk

All 8 cited leads are cold, follow_up_count=0, suburb/job_type/rooms/budget = empty.
Evidence quality is uniformly low. Scores below are ranges, not point truths.

| lead_id | cited_score | status | source | P(cash) | net AUD | urgency | evidence | minutes | risk | formula range | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| lead:pilot-pilot-2-2026-08-10T12-15-03Z | 44 | quoted | pilot | 0.15-0.35 | UNKNOWN | 0.4-0.6 | 0.25 | 20-40 | 1.4 | LOW-MID | furthest along |
| lead:pilot-pilot-2-2026-08-10T10-51-38Z | 44 | review | pilot | 0.12-0.30 | UNKNOWN | 0.4-0.6 | 0.20 | 25-45 | 1.5 | LOW-MID | same score, earlier stage |
| lead:pilot-pilot-1-2026-08-10T12-15-03Z | 38 | new | pilot | 0.08-0.22 | UNKNOWN | 0.3-0.5 | 0.15 | 25-45 | 1.6 | LOW | |
| lead:pilot-pilot-1-2026-08-10T10-51-38Z | 38 | new | pilot | 0.08-0.22 | UNKNOWN | 0.3-0.5 | 0.15 | 25-45 | 1.6 | LOW | |
| lead:manual-2026-08-10T11-02-24Z | 37 | contacted | manual | 0.08-0.20 | UNKNOWN | 0.3-0.5 | 0.15 | 20-40 | 1.5 | LOW | already contacted |
| lead:manual-2026-08-10T12-18-58Z | 37 | new | manual | 0.05-0.18 | UNKNOWN | 0.2-0.4 | 0.10 | 30-50 | 1.7 | LOW | empty fields |
| lead:manual-2026-08-10T11-02-50Z | 37 | new | manual | 0.05-0.18 | UNKNOWN | 0.2-0.4 | 0.10 | 30-50 | 1.7 | LOW | |
| lead:manual-2026-08-10T11-02-38Z | 37 | new | manual | 0.05-0.18 | UNKNOWN | 0.2-0.4 | 0.10 | 30-50 | 1.7 | LOW | |

Net value is UNKNOWN on every row (no rooms, suburb, job_type, budget_text).
Do not treat cited 37/38/44 as cash probability.

## 2. Top pick

**lead:pilot-pilot-2-2026-08-10T12-15-03Z**
Why (cited only): highest cited score 44 AND status=quoted. Twin score-44 is status=review, one step behind.
Why not others: empty geography/scope on all; quoted is the only extra cited signal.
Caveat: still cold, idle since 2026-08-10, no suburb. Qualify-first, not bid-ready.

Memory read (not a new claim): Board2 painting-lead GO 2026-08-22 was PASS on wiring; outbox lead rows were manual_completed only. Adds no job facts.

## 3. Qualification questions (do not send)

Ask in this order. Stop if any hard no.

1. Suburb / postcode (travel + parking)?
2. Interior, exterior, or both? Rooms / walls / metres if known?
3. Surface: new build, repaint, damage, render?
4. Timing window (week starting)?
5. Access: occupied, vacant, heights, colours already chosen?
6. Budget band (or need a range from us)?
7. Who decides / who pays?
8. Photos of 2-3 surfaces — yes/no (do not request off-channel upload this cycle)?
9. Any other quotes already?

Hard stops: no suburb, no job type, no access, or still shopping with no date after two touches.

## 4. Quote skeleton (NOT a quote)

Header: Master Painting (Sydney) / run revenue-cycle-1-20260827 / lead_id above / may_authorize=false
Scope: UNKNOWN — fill after Q1-Q3
Labour hours: UNKNOWN
Materials: UNKNOWN
Travel: UNKNOWN until suburb
GST: UNKNOWN for this job; do not invent
Validity: 14 days after numbers exist
Total: UNKNOWN
Line items later: prep, coat 1, coat 2, extras, waste, travel.

No dollar figure this cycle. A number without rooms/suburb would be fake.

## 5. Follow-up cadence (internal only)

Day 0: 138/owner reviews this pack (no customer send).
Day 1: if GO, one qualify call using questions 1-7.
Day 3: if no answer, one follow-up (still needs READY_FOR_OWNER_SEND).
Day 7: close as cold if still empty.

HOLD_EXTERNAL until 138/owner policy or READY_FOR_OWNER_SEND batch.

## 6. Missing facts

suburb, job_type, rooms, budget, contact channel, partner availability, GST treatment, prior quote text (status=quoted but text not cited).
