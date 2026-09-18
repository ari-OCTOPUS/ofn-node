# OWNER-RULING-WAVE1-2026-09-18 — first outbound wave = FULL scope

- stamp: 2026-09-18T07:55Z (17:55 AEST)
- channel: owner chat with ZCode session (lane S2-OPEN-20260918). Question asked in chat
  (4 options: small batch / full wave / hot-only / path-B-first). Owner answered: **«همش کامل»**
  = option 2, **full wave**.
- scope ruled: the first outbound cycle contacts **all 68 email leads** of
  state/revenue-drive/lead-emails.jsonl (not a 10–15 pilot batch), plus every already-consumed
  card target (SMARTER-COMMUNITIES, BCS-PICA, INDEX batch — consumed earlier today per
  OWNER-RULING-GOB3-2026-09-18) and the DoE `needs_reply` thread (16 days pending).
- phone-only 29 leads stay gated on DIDWW (owner purchase action, call-channel.json
  PENDING_OWNER_PURCHASE) — unchanged by this ruling.

## Readiness verified live (07:50Z)
- locks all ABSENT: SEND-PAUSED, AUTH-REVOKED, CHANNEL-REVOKED, STOP-AUTONOMY, /etc/octopus-ops-halt
- cards 6/6 consumed (registry sha d34b6aea…)
- rate card PRICE_VALIDATED 07:08Z (owner-approved bands 5.5–8k / 8–15k / 15k+ AUD)
- staged quote packets present in send-queue/ (QP-20260913-*.json)
- next revenue-drive tick: 2026-09-18 12:00:36Z (≈22:00 AEST)

## NOTE for the runtime lane (cap reconciliation, NOT executed by this lane)
- channel-authorization.json envelope: daily_send_cap **60** ("raised from 10 per owner answer
  2026-09-18"), scope = painting funnel.
- i7-runtime.json standing_authorization: daily_cap **10** (granted 02:58Z).
- This ruling (full wave, all 68) postdates both. At cap 10 the full wave stretches ~7 days;
  at 60 it completes in ~2 cycles. The owner has ruled the WAVE is full — the runtime lane owns
  aligning the effective cap to the ruling using its own preimage + paired-test + receipt
  discipline (money-path files were not touched by this lane; two-writer collision avoided).

rollback: none needed (no state mutated by this ruling).
